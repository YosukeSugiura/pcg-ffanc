from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
import sys
import time

import numpy as np
import optuna

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
sys.path.insert(0, str(ROOT / 'experiments'))

from ffanc_norm.conventional_baselines import (
    nlms_regularization,
    run_dct_sss,
    run_sss_kernel,
    run_vss2_kernel,
)
from ffanc_norm.fd_fxnlms import FDFxNLMS
from ffanc_norm.paths import synthetic_primary_path, synthetic_secondary_path
from ffanc_norm.simulation import run_ffanc
from ffanc_norm.theory import primary_variance, wiener_solution
from ffanc_norm.vss2_fxnlms import VSS2SafetyLimits
from ffanc_norm.benchmark_metrics import aggregate_heldout_hop_powers, classify_diagnostic_run
from ffanc_norm.runtime import (
    RunCount,
    ensure_compiled_kernels,
    estimate_total_seconds,
    format_duration,
)
from optimize_vss2_robust import SeedData, make_seed_data
from benchmark_transient_oracles import run_method as run_oracle_method

optuna.logging.set_verbosity(optuna.logging.WARNING)

CONVENTIONAL_METHODS = ('fixed_binwise', 'vss2', 'ad_vss2', 'sss', 'ad_sss', 'sss_dct')
ORACLE_METHODS = ('per_bin_oracle', 'full_vector_h4', 'known_from_start')

# Common safety limits for every compared method (conventional and oracle).
SAFETY_RESIDUAL_DB = 30.0
SAFETY_WEIGHT_NORM = 1e3
SAFETY_ABS_ERROR_FACTOR = 1e4

# Equal tuning budget for every method.  Earlier versions used 30-80 trials
# depending on the method, which can favor the more heavily tuned methods.
DEFAULT_TRIALS_PER_METHOD = 60
# Number of best training trials re-scored on the validation seeds.
VALIDATION_TOP_K = 10


def make_data(cfg: dict, seed: int, seconds: float) -> SeedData:
    return make_seed_data(cfg, seed, seconds)


def cumulative_db(error: np.ndarray, uncontrolled: np.ndarray, n: int | None = None) -> float:
    if n is None:
        n = len(error)
    num = float(np.dot(error[:n], error[:n]))
    den = float(np.dot(uncontrolled[:n], uncontrolled[:n]))
    return 10.0 * math.log10((num + 1e-30) / (den + 1e-30))


def run_fixed(data: SeedData, cfg: dict, mu: float) -> tuple[bool, np.ndarray]:
    alg = FDFxNLMS(
        fft_length=int(cfg['fft_length']),
        hop_length=int(cfg['hop_length']),
        controller_length=int(cfg['controller_length']),
        mu=float(mu), smoothing=float(cfg['power_smoothing']),
        regularization_ratio=float(cfg['regularization_ratio']), mode='binwise'
    )
    res = run_ffanc(
        data.x, synthetic_primary_path(), synthetic_secondary_path(), synthetic_secondary_path(),
        alg, secondary_noise=data.v, power_warmup_hops=0
    )
    e = res.error
    # Same three safety limits as the sample-wise conventional kernels
    # (hop residual ratio 30 dB, weight norm 1e3, |e| <= 1e4 * rms(d)), so that
    # the stability criterion does not differ between compared methods.
    stable = bool(np.all(np.isfinite(e)))
    if stable:
        pe, p0 = hop_curve_from_error(e, data.uncontrolled, int(cfg['hop_length']))
        wnorms = np.linalg.norm(res.controller_history, axis=1)
        stable, _failure = classify_diagnostic_run(
            pe, p0,
            max_weight_norm=float(np.max(wnorms)) if np.all(np.isfinite(wnorms)) else float('inf'),
            max_abs_error=float(np.max(np.abs(e))),
            disturbance_rms=data.disturbance_rms,
            max_residual_ratio_db=SAFETY_RESIDUAL_DB,
            max_weight_norm_limit=SAFETY_WEIGHT_NORM,
            max_abs_error_factor=SAFETY_ABS_ERROR_FACTOR,
        )
    return stable, e


def sss_params_to_mus(params: dict) -> np.ndarray:
    K = int(params['K'])
    return np.asarray([float(params['mu_max']) * float(params['ratio'])**k for k in range(K)], dtype=np.float64)


def run_sss(data: SeedData, cfg: dict, params: dict, ad: bool) -> tuple[bool, np.ndarray, np.ndarray]:
    mus = sss_params_to_mus(params)
    max_abs = 1e4 * max(data.disturbance_rms, 1e-12)
    ad_order = int(params.get('ad_order', 0)) if ad else 0
    ad_mu = float(params.get('ad_mu', 0.0)) if ad else 0.0
    stable, e, mu_hist, _maxmu, _maxwn, _abort, _reason = run_sss_kernel(
        data.x, data.d, data.xf, data.v, np.ascontiguousarray(synthetic_secondary_path()),
        mus, float(params['lambda']), float(params['rho']),
        int(cfg['controller_length']), float(cfg['nlms_delta']), int(cfg['hop_length']),
        30.0, 1e3, max_abs, ad_order, ad_mu
    )
    return bool(stable), np.asarray(e), np.asarray(mu_hist)


def run_vss2(data: SeedData, cfg: dict, params: dict, ad: bool = False) -> tuple[bool, np.ndarray, np.ndarray]:
    safety = VSS2SafetyLimits(max_residual_ratio_db=30.0, max_weight_norm=1e3, max_abs_error_factor=1e4)
    max_abs = safety.max_abs_error_factor * max(data.disturbance_rms, 1e-12)
    ad_order = int(params.get('ad_order', 0)) if ad else 0
    ad_mu = float(params.get('ad_mu', 0.0)) if ad else 0.0
    stable, error, mu_hist, *_rest = run_vss2_kernel(
        data.x, data.d, data.xf, data.v, np.ascontiguousarray(synthetic_secondary_path()),
        float(params['beta']), float(params['gamma']), int(cfg['controller_length']),
        float(cfg['nlms_delta']), int(cfg['hop_length']),
        float(safety.max_residual_ratio_db), float(safety.max_weight_norm), float(max_abs),
        ad_order, ad_mu,
    )
    return bool(stable), np.asarray(error), np.asarray(mu_hist)


def run_sss_dct(data: SeedData, cfg: dict, params: dict) -> tuple[bool, np.ndarray, np.ndarray]:
    mus = sss_params_to_mus(params)
    max_abs = 1e4 * max(data.disturbance_rms, 1e-12)
    stable, error, mu_hist, *_ = run_dct_sss(
        data.x, data.d, data.xf, data.v, np.asarray(synthetic_secondary_path(), dtype=float),
        mus=mus,
        power_lambda=float(params['power_lambda']),
        q_correlation=float(params['q']),
        kappa=float(params['kappa']),
        rho=float(params['rho']),
        controller_length=int(cfg['controller_length']),
        regularization_ratio=float(cfg['regularization_ratio']),
        hop_length=int(cfg['hop_length']),
        max_residual_ratio_db=30.0, max_weight_norm_limit=1e3, max_abs_error=max_abs,
        normalization_floor=float(cfg['dct_normalization_floor']),
    )
    return bool(stable), np.asarray(error), np.asarray(mu_hist)


def objective_on_data(method: str, params: dict, datasets: list[SeedData], cfg: dict, objective_seconds: float) -> float:
    fs = int(cfg['sample_rate'])
    nobj = int(round(objective_seconds * fs))
    ratios = []
    for data in datasets:
        if method == 'fixed_binwise':
            stable, e = run_fixed(data, cfg, float(params['mu']))
        elif method == 'vss2':
            stable, e, _ = run_vss2(data, cfg, params, ad=False)
        elif method == 'ad_vss2':
            stable, e, _ = run_vss2(data, cfg, params, ad=True)
        elif method == 'sss':
            stable, e, _ = run_sss(data, cfg, params, ad=False)
        elif method == 'ad_sss':
            stable, e, _ = run_sss(data, cfg, params, ad=True)
        elif method == 'sss_dct':
            stable, e, _ = run_sss_dct(data, cfg, params)
        else:
            raise ValueError(method)
        if not stable:
            return 1e6
        ratio = (float(np.dot(e[:nobj], e[:nobj])) + 1e-30) / (float(np.dot(data.uncontrolled[:nobj], data.uncontrolled[:nobj])) + 1e-30)
        if not math.isfinite(ratio) or ratio > 100.0:
            return 1e6
        ratios.append(ratio)
    return 10.0 * math.log10(float(np.mean(ratios)))


def optimize_method(method: str, cfg: dict, train: list[SeedData], n_trials: int, objective_seconds: float, seed: int = 2026):
    sampler = optuna.samplers.TPESampler(seed=seed, multivariate=True)
    study = optuna.create_study(direction='minimize', sampler=sampler)

    # Every method gets exactly one enqueued reference point (literature or
    # project default), which counts toward the same trial budget.
    if method == 'fixed_binwise':
        study.enqueue_trial({'mu': float(cfg['mu_binwise'])})
    if method == 'vss2':
        study.enqueue_trial({'beta':0.36, 'gamma':1.0})
    if method == 'ad_vss2':
        study.enqueue_trial({'beta':0.36, 'gamma':1.0, 'ad_order':10, 'ad_mu':0.001})
    if method in ('sss', 'ad_sss'):
        base = {'K':4, 'mu_max':0.36, 'ratio':0.5, 'lambda':0.8, 'rho':1.0}
        if method == 'ad_sss':
            base.update({'ad_order':10, 'ad_mu':0.001})
        study.enqueue_trial(base)
    if method == 'sss_dct':
        # Li et al. (2026), Gaussian-reference example.
        study.enqueue_trial({'K':3, 'mu_max':0.03, 'ratio':0.5, 'power_lambda':0.9, 'q':5.0, 'kappa':0.8, 'rho':5.0})

    def obj(trial: optuna.Trial):
        if method == 'fixed_binwise':
            p = {'mu': trial.suggest_float('mu', 0.03, 1.2, log=True)}
        elif method in ('vss2', 'ad_vss2'):
            p = {
                'beta': trial.suggest_float('beta', 0.05, 0.8),
                'gamma': trial.suggest_float('gamma', 0.08, 2.0, log=True),
            }
            if method == 'ad_vss2':
                p['ad_order'] = trial.suggest_int('ad_order', 2, 12)
                p['ad_mu'] = trial.suggest_float('ad_mu', 1e-4, 3e-2, log=True)
        elif method in ('sss', 'ad_sss'):
            p = {
                'K': trial.suggest_int('K', 2, 4),
                'mu_max': trial.suggest_float('mu_max', 0.05, 1.2 if method=='sss' else 0.8, log=True),
                'ratio': trial.suggest_float('ratio', 0.25, 0.9),
                'lambda': trial.suggest_float('lambda', 0.5, 0.98),
                'rho': trial.suggest_float('rho', 0.1, 100.0, log=True),
            }
            if method == 'ad_sss':
                p['ad_order'] = trial.suggest_int('ad_order', 2, 12)
                p['ad_mu'] = trial.suggest_float('ad_mu', 1e-4, 3e-2, log=True)
        elif method == 'sss_dct':
            p = {
                'K': trial.suggest_int('K', 2, 4),
                'mu_max': trial.suggest_float('mu_max', 1e-4, 0.3, log=True),
                'ratio': trial.suggest_float('ratio', 0.25, 0.9),
                'power_lambda': trial.suggest_float('power_lambda', 0.7, 0.99),
                'q': trial.suggest_float('q', 1.0, 10.0),
                'kappa': trial.suggest_float('kappa', 0.51, 0.99),
                'rho': trial.suggest_float('rho', 0.1, 100.0, log=True),
            }
        else:
            raise ValueError(method)
        return objective_on_data(method, p, train, cfg, objective_seconds)

    study.optimize(obj, n_trials=n_trials, show_progress_bar=False)
    good = [t for t in study.trials if t.value is not None and math.isfinite(t.value) and t.value < 1e5]
    good.sort(key=lambda t: t.value)
    return study, good[: min(VALIDATION_TOP_K, len(good))]


def select_by_validation(method: str, trials: list[optuna.trial.FrozenTrial], val: list[SeedData], cfg: dict, objective_seconds: float):
    rows = []
    for t in trials:
        score = objective_on_data(method, dict(t.params), val, cfg, objective_seconds)
        rows.append({'trial': t.number, 'train_db': float(t.value), 'val_db': float(score), 'params': dict(t.params)})
    if not rows:
        raise RuntimeError(f'{method}: no stable training trial; widen the search or check the implementation')
    rows.sort(key=lambda r: r['val_db'])
    best = dict(rows[0])
    # objective_on_data() returns 1e6 for any unstable validation seed.  Make an
    # all-unstable validation explicit instead of silently selecting it.
    best['validation_stable'] = bool(best['val_db'] < 1e5)
    return best, rows


def hop_curve_from_error(error: np.ndarray, uncontrolled: np.ndarray, H: int):
    n_hops = len(error) // H
    pe = np.empty(n_hops)
    p0 = np.empty(n_hops)
    for b in range(n_hops):
        sl = slice(b*H, (b+1)*H)
        pe[b] = np.mean(error[sl]**2)
        p0[b] = np.mean(uncontrolled[sl]**2)
    return pe, p0


def evaluate_heldout(method: str, params: dict, heldout: list[SeedData], cfg: dict, floor_db: float):
    H = int(cfg['hop_length']); fs = int(cfg['sample_rate'])
    pe_all=[]; p0_all=[]; stable_count=0; mu_stats=[]
    failures=[]
    for data in heldout:
        mu_hist = None
        if method == 'fixed_binwise':
            stable,e = run_fixed(data,cfg,float(params['mu']))
        elif method=='vss2':
            stable,e,mu_hist = run_vss2(data,cfg,params,False)
        elif method=='ad_vss2':
            stable,e,mu_hist = run_vss2(data,cfg,params,True)
        elif method=='sss':
            stable,e,mu_hist=run_sss(data,cfg,params,False)
        elif method=='ad_sss':
            stable,e,mu_hist=run_sss(data,cfg,params,True)
        elif method=='sss_dct':
            stable,e,mu_hist=run_sss_dct(data,cfg,params)
        else: raise ValueError(method)
        if not stable:
            failures.append(data.seed)
            continue
        stable_count += 1
        pe,p0=hop_curve_from_error(e,data.uncontrolled,H)
        pe_all.append(pe); p0_all.append(p0)
        if mu_hist is not None:
            mu_stats.append(mu_hist)
    out = aggregate_heldout_hop_powers(
        pe_all=pe_all, p0_all=p0_all, failures=failures, n_total=len(heldout),
        hop_length=H, sample_rate=fs, floor_db=floor_db,
    )
    if mu_stats:
        arr=np.asarray(mu_stats)
        out['mean_mu_first_10_samples_stable_only']=np.mean(arr[:,:10],axis=0).tolist()
    return out


def aggregate_oracle_runs(runs: list[dict], cfg: dict, floor_db: float) -> dict:
    """Aggregate oracle runs with the same survivor-bias rule as conventional methods.

    Earlier versions hard-coded ``primary_valid=True`` for oracles.  Oracle runs
    are now classified individually and an unstable oracle seed invalidates the
    primary curve exactly as it does for a conventional method.
    """
    H = int(cfg['hop_length']); fs = int(cfg['sample_rate'])
    pe_all = [np.asarray(r['total_power'], dtype=float) for r in runs if r.get('stable', False)]
    p0_all = [np.asarray(r['uncontrolled_power'], dtype=float) for r in runs if r.get('stable', False)]
    failures = [int(r['seed']) for r in runs if not r.get('stable', False)]
    return aggregate_heldout_hop_powers(
        pe_all=pe_all, p0_all=p0_all, failures=failures, n_total=len(runs),
        hop_length=H, sample_rate=fs, floor_db=floor_db,
    )


def oracle_heldout(cfg: dict, seeds: list[int], floor_db: float, eval_seconds: float = 2.0):
    out = {}
    for method in ORACLE_METHODS:
        runs = [run_oracle_method(cfg, s, method, eval_seconds, 4, 4.0) for s in seeds]
        out[method] = aggregate_oracle_runs(runs, cfg, floor_db)
    return out


def with_nlms_regularization(cfg: dict, design: list[SeedData]) -> dict:
    """Return a cfg copy with fixed NLMS delta / DCT floor from design seeds only."""
    delta, floor = nlms_regularization(
        [d.xf for d in design], int(cfg['controller_length']), float(cfg['regularization_ratio'])
    )
    out = dict(cfg)
    out['nlms_delta'] = delta
    out['dct_normalization_floor'] = floor
    return out


def run_conventional_once(method: str, data: SeedData, cfg: dict, params: dict) -> bool:
    if method == 'fixed_binwise':
        stable, _ = run_fixed(data, cfg, float(params['mu']))
    elif method in ('vss2', 'ad_vss2'):
        stable, _, _ = run_vss2(data, cfg, params, ad=(method == 'ad_vss2'))
    elif method in ('sss', 'ad_sss'):
        stable, _, _ = run_sss(data, cfg, params, ad=(method == 'ad_sss'))
    elif method == 'sss_dct':
        stable, _, _ = run_sss_dct(data, cfg, params)
    else:
        raise ValueError(method)
    return bool(stable)


# Representative parameters used only to time each method (calibration).
CALIBRATION_PARAMS = {
    'fixed_binwise': {'mu': 0.35},
    'vss2': {'beta': 0.36, 'gamma': 1.0},
    'ad_vss2': {'beta': 0.36, 'gamma': 1.0, 'ad_order': 10, 'ad_mu': 0.001},
    'sss': {'K': 4, 'mu_max': 0.36, 'ratio': 0.5, 'lambda': 0.8, 'rho': 1.0},
    'ad_sss': {'K': 4, 'mu_max': 0.36, 'ratio': 0.5, 'lambda': 0.8, 'rho': 1.0, 'ad_order': 10, 'ad_mu': 0.001},
    # The paper's example mu_max=0.03 aborts within a few samples for M=256,
    # which would time an aborted run.  A stable value is used for timing only.
    'sss_dct': {'K': 4, 'mu_max': 0.003, 'ratio': 0.5, 'power_lambda': 0.9, 'q': 5.0, 'kappa': 0.8, 'rho': 5.0},
}


def calibrate_seconds_per_signal_second(cfg: dict, calib_seconds: float = 0.1, oracle: bool = True) -> dict[str, float]:
    """Time each method on one short signal (after a warm-up/JIT run).

    Cost is assumed linear in signal length; trials that diverge early abort
    sooner, so the estimate is an upper bound for the conventional methods.
    """
    data = make_seed_data(cfg, 999_999, calib_seconds)
    if 'nlms_delta' not in cfg:
        cfg = with_nlms_regularization(cfg, [make_seed_data(cfg, 0, 0.5)])
    out: dict[str, float] = {}
    for method in CONVENTIONAL_METHODS:
        params = CALIBRATION_PARAMS[method]
        run_conventional_once(method, data, cfg, params)  # warm-up / JIT compile
        t0 = time.perf_counter()
        stable = run_conventional_once(method, data, cfg, params)
        out[method] = (time.perf_counter() - t0) / calib_seconds
        if not stable:
            # An aborted run is shorter than a full run and would make the
            # estimate optimistic rather than an upper bound.
            raise RuntimeError(f'calibration run for {method} was unstable; fix CALIBRATION_PARAMS')
    if oracle:
        for method in ORACLE_METHODS:
            t0 = time.perf_counter()
            run_oracle_method(cfg, 999_999, method, calib_seconds, 4, 4.0)
            out[method] = (time.perf_counter() - t0) / calib_seconds
    return out


def benchmark_plan(
    n_trials: int, n_train: int, n_val: int, n_heldout: int,
    objective_seconds: float, heldout_seconds: float, include_oracles: bool = True,
) -> list[RunCount]:
    """Signal-seconds simulated per method by main() (upper bound: no early aborts)."""
    plan = []
    for method in CONVENTIONAL_METHODS:
        sec = (
            n_trials * n_train * objective_seconds
            + min(VALIDATION_TOP_K, n_trials) * n_val * objective_seconds
            + n_heldout * heldout_seconds
        )
        plan.append(RunCount(method, sec))
    if include_oracles:
        for method in ORACLE_METHODS:
            plan.append(RunCount(method, n_heldout * heldout_seconds))
    return plan


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--config',default=str(ROOT/'configs'/'oracle_2s.json'))
    ap.add_argument('--train-seeds',type=int,default=6)
    ap.add_argument('--val-seeds',type=int,default=10)
    ap.add_argument('--heldout-seeds',type=int,default=20)
    ap.add_argument('--objective-seconds',type=float,default=0.5)
    ap.add_argument('--heldout-seconds',type=float,default=2.0)
    ap.add_argument('--trials',type=int,default=DEFAULT_TRIALS_PER_METHOD,
                    help='Optuna trials per method; identical for every method')
    ap.add_argument('--allow-python-fallback',action='store_true',
                    help='run even if Numba is missing (100-300x slower)')
    ap.add_argument('--estimate-only',action='store_true',
                    help='calibrate per-method cost, print the runtime estimate and exit')
    ap.add_argument('--max-estimated-hours',type=float,default=6.0,
                    help='refuse to start when the estimate exceeds this (use --force to override)')
    ap.add_argument('--force',action='store_true')
    args=ap.parse_args()
    if args.trials < 1:
        raise SystemExit('--trials must be >= 1')
    ensure_compiled_kernels(args.allow_python_fallback, 'benchmark_conventional_limit')
    cfg=json.loads(Path(args.config).read_text())

    # Optimize on 0.5-s datasets. Validation also uses 0.5 s objective.
    train=[make_data(cfg,s,args.objective_seconds) for s in range(args.train_seeds)]
    val=[make_data(cfg,20+s,args.objective_seconds) for s in range(args.val_seeds)]
    cfg = with_nlms_regularization(cfg, train)
    print(f"NLMS delta={cfg['nlms_delta']:.6g}, DCT bin floor={cfg['dct_normalization_floor']:.6g} "
          '(from training seeds only)', flush=True)

    # Bounded execution: estimate the wall-clock cost before any sweep starts.
    per_sec = calibrate_seconds_per_signal_second(cfg)
    plan = benchmark_plan(args.trials, args.train_seeds, args.val_seeds, args.heldout_seeds,
                          args.objective_seconds, args.heldout_seconds)
    estimate = estimate_total_seconds(per_sec, plan)
    print('RUNTIME ESTIMATE (upper bound, no early aborts):', flush=True)
    for k, v in estimate.items():
        print(f'  {k:>18s}: {format_duration(v)}', flush=True)
    if args.estimate_only:
        return
    if estimate['total'] > args.max_estimated_hours * 3600.0 and not args.force:
        raise SystemExit(
            f"estimated {format_duration(estimate['total'])} exceeds "
            f"--max-estimated-hours={args.max_estimated_hours}; reduce the plan or pass --force"
        )

    opt_summary={}; best={}
    for i,method in enumerate(CONVENTIONAL_METHODS):
        n=args.trials
        print(f'OPTIMIZE {method}: {n} trials',flush=True)
        study,top=optimize_method(method,cfg,train,n,args.objective_seconds,seed=2026+i)
        selected,rows=select_by_validation(method,top,val,cfg,args.objective_seconds)
        best[method]=selected['params']
        opt_summary[method]={'best_validation':selected,'top_validation':rows,'n_trials':n}
        print(method,selected,flush=True)
        if not selected['validation_stable']:
            print(f'WARNING {method}: every validation candidate was unstable; '
                  'held-out result will be reported as unstable', flush=True)

    # Held-out 2-s data, disjoint from both train and validation.
    heldout=[make_data(cfg,100+s,args.heldout_seconds) for s in range(args.heldout_seeds)]
    p=synthetic_primary_path(); s=synthetic_secondary_path(); M=int(cfg['controller_length'])
    _,_,_,jmin=wiener_solution(s,p,M,pole=0.95); vard=primary_variance(p,pole=0.95)
    varv=vard/(10**(float(cfg['secondary_noise_snr_db'])/10)); floor_db=10*np.log10((jmin+varv)/(vard+varv))
    final={}
    for method in CONVENTIONAL_METHODS:
        print('HELDOUT',method,flush=True)
        final[method]=evaluate_heldout(method,best[method],heldout,cfg,float(floor_db))
    print('HELDOUT oracles',flush=True)
    # Oracle held-out signals are sample-identical to the conventional ones
    # over the evaluation interval (see benchmark_transient_oracles._make_signals).
    final.update(oracle_heldout(cfg,[100+s for s in range(args.heldout_seeds)],float(floor_db),args.heldout_seconds))
    summary={'conditions':{
        'train_seeds':list(range(args.train_seeds)),
        'validation_seeds':list(range(20,20+args.val_seeds)),
        'heldout_seeds':list(range(100,100+args.heldout_seeds)),
        'objective_seconds':args.objective_seconds,
        'heldout_seconds':args.heldout_seconds,
        'physical_floor_db':float(floor_db),
        'trial_budget_policy':'equal',
        'trials_per_method':args.trials,
        'validation_top_k':VALIDATION_TOP_K,
        'nlms_delta':cfg['nlms_delta'],
        'dct_normalization_floor':cfg['dct_normalization_floor'],
        'nlms_regularization_definition':'delta = regularization_ratio * M * mean(xf^2) over training seeds; DCT floor = regularization_ratio * mean(xf^2)',
        'safety_limits':{'residual_ratio_db':SAFETY_RESIDUAL_DB,'weight_norm':SAFETY_WEIGHT_NORM,'abs_error_factor':SAFETY_ABS_ERROR_FACTOR},
        'runtime_estimate_s':estimate,
        'metric_definition':'linear power averaged across held-out seeds before dB; primary metrics only if every seed is stable',
    },'best_params':best,'optimization':opt_summary,'heldout':final}
    out=ROOT/'results'/'conventional_limit_benchmark'; out.mkdir(parents=True,exist_ok=True)
    (out/'summary.json').write_text(json.dumps(summary,indent=2))
    # Compact CSV.
    cols=['method','primary_valid','status','stable','n','db_0.1','db_0.25','db_0.5','db_1.0','db_2.0','cumulative_2s_db','t_m10','t_m15','t_m18','t_floor05']
    lines=[','.join(cols)]
    for method,r in final.items():
        pt=r.get('points_db',{}); th=r.get('threshold_s',{})
        vals=[method,str(r.get('primary_valid','')),str(r.get('status','')),str(r.get('stable','')),str(r.get('n','')),str(pt.get('0.1','')),str(pt.get('0.25','')),str(pt.get('0.5','')),str(pt.get('1.0','')),str(pt.get('2.0','')),str(r.get('cumulative_2s_db','')),str(th.get('-10','')),str(th.get('-15','')),str(th.get('-18','')),str(th.get('floor_plus_0.5db',''))]
        lines.append(','.join(vals))
    (out/'comparison.csv').write_text('\n'.join(lines)+'\n')
    print(json.dumps({'best_params':best,'heldout':final},indent=2),flush=True)

if __name__=='__main__': main()
