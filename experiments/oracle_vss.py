from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))

from ffanc_norm.benchmark_metrics import (
    classify_diagnostic_run,
    cumulative_power_ratio_db,
    diagnostic_stability_summary,
    ensemble_power_ratio_db,
    threshold_times_from_db_curve,
)
from ffanc_norm.fd_fxnlms import fd_block_gradient
from ffanc_norm.normalization import PowerTracker
from ffanc_norm.paths import synthetic_primary_path, synthetic_secondary_path
from ffanc_norm.signals import colored_noise
from ffanc_norm.simulation import causal_fir_block, right_aligned_history, secondary_noise_for_snr


def _future_cost_and_mu(
    *, x, disturbance, secondary_path, y_history, w, gradient,
    start, horizon_stop, mu_max,
):
    """Exact receding-horizon scalar line search for one update direction.

    The candidate controller is w_new = w - mu * gradient and is held fixed
    over [start, horizon_stop).  Past controller output in y_history[:start]
    is kept exactly, so secondary-path memory is included.  The cost excludes
    independent sensor noise because its expected contribution is constant.
    """
    if horizon_stop <= start:
        return 0.0, 0.0

    # Candidate mu=0 future controller output.
    y0 = y_history.copy()
    y0[start:horizon_stop] = causal_fir_block(x, w, start, horizon_stop)
    sec0 = causal_fir_block(y0, secondary_path, start, horizon_stop)
    a = disturbance[start:horizon_stop] + sec0

    # Change in future controller output per unit mu. Past delta is zero.
    yg = np.zeros_like(y_history)
    yg[start:horizon_stop] = causal_fir_block(x, gradient, start, horizon_stop)
    secg = causal_fir_block(yg, secondary_path, start, horizon_stop)

    denom = float(secg @ secg)
    if denom <= 1e-30:
        mu = 0.0
    else:
        # residual(mu) = a - mu * secg
        mu = float((a @ secg) / denom)
        mu = float(np.clip(mu, 0.0, mu_max))

    r = a - mu * secg
    cost = float(r @ r)
    return mu, cost


def run_one(cfg: dict, seed: int, strategy: str, horizon_hops: int, mu_max: float):
    N = int(cfg['fft_length'])
    H = int(cfg['hop_length'])
    M = int(cfg['controller_length'])
    fs = int(cfg['sample_rate'])
    n_samples = int(round(float(cfg['duration_seconds']) * fs))

    rng_x = np.random.default_rng(seed)
    rng_v = np.random.default_rng(seed + 1000003)
    x = colored_noise(n_samples, rng_x, pole=0.95)
    p = synthetic_primary_path()
    s = synthetic_secondary_path()
    d = np.convolve(x, p, mode='full')[:n_samples]
    xf = np.convolve(x, s, mode='full')[:n_samples]
    v = secondary_noise_for_snr(d, cfg.get('secondary_noise_snr_db'), rng_v)

    power = PowerTracker(N // 2 + 1, float(cfg['power_smoothing']), float(cfg['regularization_ratio']))
    w = np.zeros(M)
    y = np.zeros(n_samples)
    sec = np.zeros(n_samples)
    e = d + v
    anc = d.copy()

    mu_hist = []
    mode_hist = []
    hop_db = []
    hop_pe = []
    hop_p0 = []
    max_weight_norm_seen = 0.0
    max_abs_error_seen = 0.0

    n_hops = n_samples // H
    for b in range(n_hops):
        start = b * H
        stop = start + H
        # Produce current hop with current controller.
        y[start:stop] = causal_fir_block(x, w, start, stop)
        sec[start:stop] = causal_fir_block(y, s, start, stop)
        anc[start:stop] = d[start:stop] + sec[start:stop]
        e[start:stop] = anc[start:stop] + v[start:stop]
        max_abs_error_seen = max(max_abs_error_seen, float(np.max(np.abs(e[start:stop]))))

        xf_hist = right_aligned_history(xf, stop, N)
        Xf = np.fft.rfft(xf_hist)
        power.update(Xf)

        if strategy == 'fixed_binwise':
            denom = power.denominator('binwise', b)
            g = fd_block_gradient(xf_hist, e[start:stop], denom, M)
            mu = float(cfg['mu_binwise'])
            chosen = 'binwise'
        elif strategy == 'fixed_global':
            denom = power.denominator('global', b)
            g = fd_block_gradient(xf_hist, e[start:stop], denom, M)
            mu = float(cfg['mu_global'])
            chosen = 'global'
        elif strategy in {'oracle_binwise', 'oracle_joint'}:
            horizon_stop = min(n_samples, stop + horizon_hops * H)
            denom_b = power.denominator('binwise', b)
            g_b = fd_block_gradient(xf_hist, e[start:stop], denom_b, M)
            mu_b, cost_b = _future_cost_and_mu(
                x=x, disturbance=d, secondary_path=s, y_history=y, w=w,
                gradient=g_b, start=stop, horizon_stop=horizon_stop, mu_max=mu_max,
            )
            if strategy == 'oracle_binwise':
                g, mu, chosen = g_b, mu_b, 'binwise'
            else:
                denom_g = power.denominator('global', b)
                g_g = fd_block_gradient(xf_hist, e[start:stop], denom_g, M)
                mu_g, cost_g = _future_cost_and_mu(
                    x=x, disturbance=d, secondary_path=s, y_history=y, w=w,
                    gradient=g_g, start=stop, horizon_stop=horizon_stop, mu_max=mu_max,
                )
                if cost_g < cost_b:
                    g, mu, chosen = g_g, mu_g, 'global'
                else:
                    g, mu, chosen = g_b, mu_b, 'binwise'
        else:
            raise ValueError(strategy)

        w = w - mu * g
        max_weight_norm_seen = max(max_weight_norm_seen, float(np.linalg.norm(w)))
        mu_hist.append(mu)
        mode_hist.append(chosen)

        pe = float(np.mean(e[start:stop] ** 2))
        p0 = float(np.mean((d[start:stop] + v[start:stop]) ** 2))
        hop_pe.append(pe)
        hop_p0.append(p0)
        hop_db.append(10.0 * np.log10((pe + 1e-15) / (p0 + 1e-15)))

    hop_db = np.asarray(hop_db)
    mu_hist = np.asarray(mu_hist)
    # Cumulative total-residual metric.
    cumulative_db = 10.0 * np.log10((np.sum(e**2) + 1e-15) / (np.sum((d + v) ** 2) + 1e-15))
    tail = min(5 * fs, n_samples)
    final_db = 10.0 * np.log10((np.sum(e[-tail:]**2)+1e-15) / (np.sum((d[-tail:]+v[-tail:])**2)+1e-15))

    thresholds = {}
    # Smooth only for threshold timing, 5-hop moving average.
    k = 5
    if len(hop_db) >= k:
        smooth = np.convolve(hop_db, np.ones(k)/k, mode='valid')
        times = (np.arange(len(smooth)) + k) * H / fs
        for th in (-3, -6, -10, -15, -18):
            idx = np.flatnonzero(smooth <= th)
            thresholds[str(th)] = float(times[idx[0]]) if len(idx) else None
    else:
        thresholds = {str(th): None for th in (-3,-6,-10,-15,-18)}

    stable, failure = classify_diagnostic_run(
        hop_pe, hop_p0,
        max_weight_norm=max_weight_norm_seen,
        max_abs_error=max_abs_error_seen,
        disturbance_rms=float(np.sqrt(np.mean(d[:len(e)] ** 2))),
    )

    return {
        'stable': stable,
        'failure': failure,
        'max_weight_norm': float(max_weight_norm_seen),
        'max_abs_error': float(max_abs_error_seen),
        'strategy': strategy,
        'seed': seed,
        'hop_length': H,
        'sample_rate': fs,
        'cumulative_db': float(cumulative_db),
        'final_5s_db': float(final_db),
        'threshold_times_s': thresholds,
        'mu_mean_first_10': float(np.mean(mu_hist[:10])),
        'mu_max': float(np.max(mu_hist)) if len(mu_hist) else 0.0,
        'mu_median': float(np.median(mu_hist)) if len(mu_hist) else 0.0,
        'global_fraction': float(np.mean(np.array(mode_hist) == 'global')),
        'mu_history': mu_hist.tolist(),
        'mode_history': mode_hist,
        'hop_db': hop_db.tolist(),
        'hop_pe': list(map(float, hop_pe)),
        'hop_p0': list(map(float, hop_p0)),
    }


def summarize(results):
    out = {}
    strategies = sorted({r['strategy'] for r in results})
    for strategy in strategies:
        rr = [r for r in results if r['strategy'] == strategy]
        status, stable_rr = diagnostic_stability_summary(rr)
        d = {
            **status,
            'metric_definition': 'linear power averaged across seeds before conversion to dB; primary metrics require every seed to be stable; primary thresholds use no temporal smoothing',
        }
        if stable_rr:
            pe = np.asarray([r['hop_pe'] for r in stable_rr], dtype=float)
            p0 = np.asarray([r['hop_p0'] for r in stable_rr], dtype=float)
            curve = ensemble_power_ratio_db(pe, p0)
            tail_hops = min(int(round(5.0 * stable_rr[0]['sample_rate'] / stable_rr[0]['hop_length'])), pe.shape[1])
            per_seed_cum = np.asarray([r['cumulative_db'] for r in stable_rr], dtype=float)
            per_seed_tail = np.asarray([r['final_5s_db'] for r in stable_rr], dtype=float)
            metrics = {
                'cumulative_db': cumulative_power_ratio_db(pe, p0),
                'final_5s_db': cumulative_power_ratio_db(pe[:, -tail_hops:], p0[:, -tail_hops:]),
                'ensemble_curve_db': curve.tolist(),
                'threshold_s': threshold_times_from_db_curve(curve, stable_rr[0]['hop_length'] / stable_rr[0]['sample_rate']),
                'per_seed_db_diagnostic': {
                    'cumulative_mean': float(np.mean(per_seed_cum)),
                    'cumulative_std': float(np.std(per_seed_cum, ddof=1)) if len(stable_rr) > 1 else 0.0,
                    'final_5s_mean': float(np.mean(per_seed_tail)),
                    'final_5s_std': float(np.std(per_seed_tail, ddof=1)) if len(stable_rr) > 1 else 0.0,
                },
                'mu_mean_first_10': float(np.mean([r['mu_mean_first_10'] for r in stable_rr])),
                'mu_max_mean': float(np.mean([r['mu_max'] for r in stable_rr])),
                'global_fraction_mean': float(np.mean([r['global_fraction'] for r in stable_rr])),
            }
            if status['primary_valid']:
                d.update(metrics)
            else:
                d['stable_only_diagnostic'] = metrics
        out[strategy] = d
    return out

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--config', default=str(ROOT / 'configs' / 'pilot.json'))
    ap.add_argument('--n-seeds', type=int, default=20)
    ap.add_argument('--seed-start', type=int, default=1000)
    ap.add_argument('--horizon-hops', type=int, default=4)
    ap.add_argument('--mu-max', type=float, default=8.0)
    args = ap.parse_args()

    cfg = json.loads(Path(args.config).read_text())
    results = []
    for seed in range(args.seed_start, args.seed_start + args.n_seeds):
        for strategy in ('fixed_global','fixed_binwise','oracle_binwise','oracle_joint'):
            results.append(run_one(cfg, seed, strategy, args.horizon_hops, args.mu_max))
    summary = {
        'config': cfg,
        'n_seeds': args.n_seeds,
        'horizon_hops': args.horizon_hops,
        'mu_max': args.mu_max,
        'summary': summarize(results),
    }
    out_dir = ROOT / 'results' / 'oracle_vss'
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / 'summary.json').write_text(json.dumps(summary, indent=2))
    (out_dir / 'runs.json').write_text(json.dumps(results))
    print(json.dumps(summary, indent=2))

if __name__ == '__main__':
    main()
