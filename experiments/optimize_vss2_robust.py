from __future__ import annotations

import argparse
import csv
import json
import math
from pathlib import Path
import sys
import time
from dataclasses import asdict, dataclass

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from ffanc_norm.paths import synthetic_primary_path, synthetic_secondary_path
from ffanc_norm.signals import colored_noise
from ffanc_norm.simulation import secondary_noise_for_snr
from ffanc_norm.vss2_fxnlms import VSS2SafetyLimits

try:
    import optuna
except ImportError as exc:  # pragma: no cover
    raise SystemExit(
        "Optuna is required for this script. Install it with `pip install optuna`."
    ) from exc

from ffanc_norm.conventional_baselines import (
    KERNELS_COMPILED,
    _run_vss2_python,
    nlms_regularization,
    run_vss2_kernel,
)
from ffanc_norm.runtime import ensure_compiled_kernels


@dataclass(frozen=True)
class SeedData:
    seed: int
    x: np.ndarray
    d: np.ndarray
    xf: np.ndarray
    v: np.ndarray
    uncontrolled: np.ndarray
    disturbance_rms: float


@dataclass(frozen=True)
class EvalResult:
    stable: bool
    cumulative_total_residual_ratio: float
    cumulative_total_residual_db: float
    final_total_residual_db: float
    max_mu: float
    max_weight_norm: float
    abort_sample: int
    abort_reason: str


def run_vss2_seed(
    data: SeedData,
    secondary_path: np.ndarray,
    beta: float,
    gamma: float,
    controller_length: int,
    delta: float,
    hop_length: int,
    safety: VSS2SafetyLimits,
    use_numba: bool = True,
) -> EvalResult:
    max_abs_error = safety.max_abs_error_factor * max(data.disturbance_rms, 1e-12)
    # Use the single shared VSS2 implementation (also used by
    # benchmark_conventional_limit.py) instead of a private duplicate kernel.
    kernel = run_vss2_kernel if use_numba and KERNELS_COMPILED else _run_vss2_python
    stable, error, _mu_hist, max_mu, max_wnorm, abort_sample, reason_code = kernel(
        data.x,
        data.d,
        data.xf,
        data.v,
        secondary_path,
        float(beta),
        float(gamma),
        int(controller_length),
        float(delta),  # NLMS delta: denominator delta + ||x_f||^2
        int(hop_length),
        float(safety.max_residual_ratio_db),
        float(safety.max_weight_norm),
        float(max_abs_error),
        0,    # ad_order: plain VSS2 (no adaptive decorrelation)
        0.0,  # ad_mu
    )

    reason_map = {0: "", 1: "nonfinite_or_abs_error", 2: "weight_norm", 3: "residual_ratio"}
    reason = reason_map[int(reason_code)]

    if not stable:
        return EvalResult(
            stable=False,
            cumulative_total_residual_ratio=float("inf"),
            cumulative_total_residual_db=float("inf"),
            final_total_residual_db=float("inf"),
            max_mu=float(max_mu),
            max_weight_norm=float(max_wnorm),
            abort_sample=int(abort_sample),
            abort_reason=reason,
        )

    uncontrolled = data.uncontrolled
    cumulative_ratio = float(
        (float(np.dot(error, error)) + 1e-30)
        / (float(np.dot(uncontrolled, uncontrolled)) + 1e-30)
    )
    cum_db = float(10.0 * np.log10(cumulative_ratio))
    tail = min(len(error), 10 * hop_length)
    final_db = float(
        10.0
        * np.log10(
            (float(np.dot(error[-tail:], error[-tail:])) + 1e-30)
            / (float(np.dot(uncontrolled[-tail:], uncontrolled[-tail:])) + 1e-30)
        )
    )
    return EvalResult(
        stable=True,
        cumulative_total_residual_ratio=cumulative_ratio,
        cumulative_total_residual_db=cum_db,
        final_total_residual_db=final_db,
        max_mu=float(max_mu),
        max_weight_norm=float(max_wnorm),
        abort_sample=-1,
        abort_reason="",
    )


def make_seed_data(cfg: dict, seed: int, duration_seconds: float) -> SeedData:
    fs = int(cfg["sample_rate"])
    n_samples = int(round(duration_seconds * fs))
    rng_x = np.random.default_rng(seed)
    rng_v = np.random.default_rng(seed + 1000003)

    x = colored_noise(n_samples, rng_x, pole=float(cfg.get("ar_pole", 0.95)))
    p = synthetic_primary_path()
    s = synthetic_secondary_path()
    d = np.convolve(x, p, mode="full")[:n_samples]
    xf = np.convolve(x, s, mode="full")[:n_samples]
    v = secondary_noise_for_snr(d, cfg.get("secondary_noise_snr_db"), rng_v)
    uncontrolled = d + v
    return SeedData(
        seed=int(seed),
        x=np.ascontiguousarray(x, dtype=np.float64),
        d=np.ascontiguousarray(d, dtype=np.float64),
        xf=np.ascontiguousarray(xf, dtype=np.float64),
        v=np.ascontiguousarray(v, dtype=np.float64),
        uncontrolled=np.ascontiguousarray(uncontrolled, dtype=np.float64),
        disturbance_rms=float(np.sqrt(np.mean(d**2))),
    )


def evaluate_candidate(
    beta: float,
    gamma: float,
    datasets: list[SeedData],
    cfg: dict,
    safety: VSS2SafetyLimits,
    std_weight: float,
    use_numba: bool,
    time_limit_s: float | None = None,
) -> dict:
    t0 = time.monotonic()
    secondary_path = np.ascontiguousarray(synthetic_secondary_path(), dtype=np.float64)
    rows = []
    for data in datasets:
        if time_limit_s is not None and time.monotonic() - t0 > time_limit_s:
            return {
                "stable": False,
                "objective": float("inf"),
                "failure": "trial_timeout",
                "seed_results": rows,
                "elapsed_s": time.monotonic() - t0,
            }
        r = run_vss2_seed(
            data=data,
            secondary_path=secondary_path,
            beta=beta,
            gamma=gamma,
            controller_length=int(cfg["controller_length"]),
            delta=float(cfg["nlms_delta"]),
            hop_length=int(cfg["hop_length"]),
            safety=safety,
            use_numba=use_numba,
        )
        row = {"seed": data.seed, **asdict(r)}
        rows.append(row)
        if not r.stable:
            return {
                "stable": False,
                "objective": float("inf"),
                "failure": f"seed_{data.seed}:{r.abort_reason}",
                "seed_results": rows,
                "elapsed_s": time.monotonic() - t0,
            }

    vals = np.array([r["cumulative_total_residual_db"] for r in rows], dtype=float)
    ratios = np.array([r["cumulative_total_residual_ratio"] for r in rows], dtype=float)
    ensemble_db = float(10.0 * np.log10(np.mean(ratios)))
    mean = float(np.mean(vals))
    std = float(np.std(vals, ddof=1)) if len(vals) > 1 else 0.0
    objective = ensemble_db + float(std_weight) * std
    return {
        "stable": True,
        "objective": float(objective),
        "ensemble_cumulative_total_residual_db": ensemble_db,
        "mean_cumulative_total_residual_db": mean,
        "std_cumulative_total_residual_db": std,
        "mean_final_total_residual_db": float(np.mean([r["final_total_residual_db"] for r in rows])),
        "max_mu": float(max(r["max_mu"] for r in rows)),
        "max_weight_norm": float(max(r["max_weight_norm"] for r in rows)),
        "seed_results": rows,
        "elapsed_s": time.monotonic() - t0,
    }



def _json_safe(value):
    """Recursively replace non-finite floats by None for strict JSON output."""
    if isinstance(value, float):
        return value if math.isfinite(value) else None
    if isinstance(value, dict):
        return {k: _json_safe(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_json_safe(v) for v in value]
    return value

def parse_seeds(text: str) -> list[int]:
    return [int(x) for x in text.split(",") if x.strip()]


def main() -> None:
    ap = argparse.ArgumentParser(
        description="Robust two-stage Optuna optimization for VSS2-FxNLMS."
    )
    ap.add_argument("--config", default=str(ROOT / "configs" / "oracle_2s.json"))
    ap.add_argument("--stage-a-seeds", default="0,1,2")
    ap.add_argument("--stage-b-seeds", default=",".join(str(i) for i in range(20)))
    ap.add_argument("--stage-a-duration", type=float, default=0.5)
    ap.add_argument("--stage-b-duration", type=float, default=2.0)
    ap.add_argument("--trials", type=int, default=80)
    ap.add_argument("--top-k", type=int, default=20)
    ap.add_argument("--beta-min", type=float, default=0.03)
    ap.add_argument("--beta-max", type=float, default=1.0)
    ap.add_argument("--gamma-min", type=float, default=0.10)
    ap.add_argument("--gamma-max", type=float, default=2.0)
    ap.add_argument("--std-weight", type=float, default=0.25)
    ap.add_argument("--trial-timeout", type=float, default=30.0)
    ap.add_argument("--max-residual-ratio-db", type=float, default=30.0)
    ap.add_argument("--max-weight-norm", type=float, default=1e3)
    ap.add_argument("--max-abs-error-factor", type=float, default=1e4)
    ap.add_argument("--seed", type=int, default=20261003, help="Optuna sampler seed")
    ap.add_argument("--no-numba", action="store_true",
                    help="force the pure-Python kernel (debugging only; very slow)")
    ap.add_argument("--allow-python-fallback", action="store_true",
                    help="run even if Numba is missing (100-300x slower)")
    ap.add_argument("--output-dir", default=str(ROOT / "results" / "vss2_robust_optuna"))
    args = ap.parse_args()

    cfg = json.loads(Path(args.config).read_text(encoding="utf-8"))
    stage_a_seeds = parse_seeds(args.stage_a_seeds)
    stage_b_seeds = parse_seeds(args.stage_b_seeds)
    if not stage_a_seeds or not stage_b_seeds:
        raise ValueError("both stage seed sets must be non-empty")
    if args.stage_a_duration <= 0 or args.stage_b_duration <= 0:
        raise ValueError("durations must be positive")

    safety = VSS2SafetyLimits(
        max_residual_ratio_db=args.max_residual_ratio_db,
        max_weight_norm=args.max_weight_norm,
        max_abs_error_factor=args.max_abs_error_factor,
    )
    if args.no_numba:
        use_numba = False
    else:
        use_numba = ensure_compiled_kernels(args.allow_python_fallback, "optimize_vss2_robust")

    # Cache deterministic signal/path realizations once. Optuna trials only run
    # the adaptive controller; no repeated signal generation/convolution.
    print("Preparing cached datasets ...", flush=True)
    stage_a_data = [make_seed_data(cfg, s, args.stage_a_duration) for s in stage_a_seeds]
    stage_b_data = [make_seed_data(cfg, s, args.stage_b_duration) for s in stage_b_seeds]
    # Fixed NLMS delta from the Stage-A (design) seeds only, same definition as
    # benchmark_conventional_limit.py.
    cfg = dict(cfg)
    cfg["nlms_delta"], _ = nlms_regularization(
        [d.xf for d in stage_a_data], int(cfg["controller_length"]), float(cfg["regularization_ratio"])
    )

    # Warm up Numba before timing individual trials.
    if use_numba:
        _ = run_vss2_seed(
            stage_a_data[0],
            np.ascontiguousarray(synthetic_secondary_path(), dtype=np.float64),
            beta=0.36,
            gamma=1.0,
            controller_length=int(cfg["controller_length"]),
            delta=float(cfg["nlms_delta"]),
            hop_length=int(cfg["hop_length"]),
            safety=safety,
            use_numba=True,
        )

    sampler = optuna.samplers.TPESampler(seed=args.seed, multivariate=True)
    pruner = optuna.pruners.MedianPruner(n_startup_trials=10, n_warmup_steps=1)
    study = optuna.create_study(direction="minimize", sampler=sampler, pruner=pruner)

    def objective(trial: optuna.Trial) -> float:
        beta = trial.suggest_float("beta", args.beta_min, args.beta_max, log=True)
        gamma = trial.suggest_float("gamma", args.gamma_min, args.gamma_max, log=True)
        t0 = time.monotonic()
        vals: list[float] = []
        ratios: list[float] = []
        for i, data in enumerate(stage_a_data):
            if time.monotonic() - t0 > args.trial_timeout:
                trial.set_user_attr("failure", "trial_timeout")
                raise optuna.TrialPruned("trial timeout")
            r = run_vss2_seed(
                data,
                np.ascontiguousarray(synthetic_secondary_path(), dtype=np.float64),
                beta,
                gamma,
                int(cfg["controller_length"]),
                float(cfg["nlms_delta"]),
                int(cfg["hop_length"]),
                safety,
                use_numba=use_numba,
            )
            if not r.stable:
                trial.set_user_attr("failure", f"seed_{data.seed}:{r.abort_reason}")
                trial.set_user_attr("abort_sample", r.abort_sample)
                raise optuna.TrialPruned("unstable candidate")
            vals.append(r.cumulative_total_residual_db)
            ratios.append(r.cumulative_total_residual_ratio)
            partial = float(10.0 * np.log10(np.mean(ratios)))
            if len(vals) > 1:
                partial += args.std_weight * float(np.std(vals, ddof=1))
            trial.report(partial, step=i)
            if trial.should_prune():
                raise optuna.TrialPruned("median pruner")
        ensemble_db = float(10.0 * np.log10(np.mean(ratios)))
        mean = float(np.mean(vals))
        std = float(np.std(vals, ddof=1)) if len(vals) > 1 else 0.0
        trial.set_user_attr("ensemble_db", ensemble_db)
        trial.set_user_attr("mean_db", mean)
        trial.set_user_attr("std_db", std)
        trial.set_user_attr("elapsed_s", time.monotonic() - t0)
        return ensemble_db + args.std_weight * std

    # Add literature setting explicitly so the search cannot miss it.
    study.enqueue_trial({"beta": 0.36, "gamma": 1.0})
    print("Stage A: broad Optuna search ...", flush=True)
    study.optimize(objective, n_trials=args.trials, gc_after_trial=True, show_progress_bar=False)

    complete = [t for t in study.trials if t.state == optuna.trial.TrialState.COMPLETE]
    complete.sort(key=lambda t: float(t.value))
    if not complete:
        raise RuntimeError("no stable Stage-A trial completed")

    top_trials = complete[: min(args.top_k, len(complete))]
    print(f"Stage B: robust re-evaluation of {len(top_trials)} candidates ...", flush=True)
    stage_b_rows = []
    for rank, trial in enumerate(top_trials, start=1):
        beta = float(trial.params["beta"])
        gamma = float(trial.params["gamma"])
        result = evaluate_candidate(
            beta=beta,
            gamma=gamma,
            datasets=stage_b_data,
            cfg=cfg,
            safety=safety,
            std_weight=args.std_weight,
            use_numba=use_numba,
            time_limit_s=args.trial_timeout * max(1.0, len(stage_b_data) / len(stage_a_data)),
        )
        stage_b_rows.append(
            {
                "stage_a_rank": rank,
                "stage_a_objective": float(trial.value),
                "beta": beta,
                "gamma": gamma,
                **result,
            }
        )
        status = "OK" if result["stable"] else f"FAIL({result['failure']})"
        obj = result["objective"]
        obj_text = f"{obj:.3f}" if np.isfinite(obj) else "inf"
        print(
            f"  #{rank:02d} beta={beta:.5g} gamma={gamma:.5g} "
            f"objective={obj_text} {status}",
            flush=True,
        )

    stable_b = [r for r in stage_b_rows if r["stable"]]
    stable_b.sort(key=lambda r: float(r["objective"]))
    best = stable_b[0] if stable_b else None

    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    payload = {
        "method": "VSS2-FxNLMS",
        "vss_rule": "mu(n) = beta * atan(|e(n)|**gamma)",
        "objective": "10*log10(mean linear cumulative residual ratio) + std_weight * std(per-seed dB); any unstable seed rejects candidate",
        "config": cfg,
        "safety": asdict(safety),
        "optimization": {
            "stage_a_seeds": stage_a_seeds,
            "stage_b_seeds": stage_b_seeds,
            "stage_a_duration_s": args.stage_a_duration,
            "stage_b_duration_s": args.stage_b_duration,
            "n_trials": args.trials,
            "top_k": args.top_k,
            "std_weight": args.std_weight,
            "trial_timeout_s": args.trial_timeout,
            "sampler": "Optuna TPESampler(multivariate=True)",
            "pruner": "MedianPruner + hard divergence abort",
            "numba": bool(use_numba),
        },
        "stage_a": [
            {
                "number": t.number,
                "state": t.state.name,
                "value": None if t.value is None else float(t.value),
                "params": dict(t.params),
                "user_attrs": dict(t.user_attrs),
            }
            for t in study.trials
        ],
        "stage_b": stage_b_rows,
        "best": best,
    }
    json_path = out_dir / "summary.json"
    json_path.write_text(json.dumps(_json_safe(payload), indent=2, allow_nan=False), encoding="utf-8")

    csv_path = out_dir / "stage_b_candidates.csv"
    with csv_path.open("w", newline="", encoding="utf-8") as f:
        fieldnames = [
            "stage_a_rank",
            "stage_a_objective",
            "beta",
            "gamma",
            "stable",
            "objective",
            "ensemble_cumulative_total_residual_db",
            "mean_cumulative_total_residual_db",
            "std_cumulative_total_residual_db",
            "mean_final_total_residual_db",
            "max_mu",
            "max_weight_norm",
            "failure",
            "elapsed_s",
        ]
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        for row in stage_b_rows:
            writer.writerow(row)

    if best is None:
        print("No Stage-B candidate was stable on every training seed.", flush=True)
    else:
        print(
            "BEST ROBUST: "
            f"beta={best['beta']:.6g}, gamma={best['gamma']:.6g}, "
            f"objective={best['objective']:.3f}, "
            f"ensemble={best['ensemble_cumulative_total_residual_db']:.3f} dB, "
            f"mean={best['mean_cumulative_total_residual_db']:.3f} dB, "
            f"std={best['std_cumulative_total_residual_db']:.3f} dB",
            flush=True,
        )
    print(f"saved: {json_path}", flush=True)
    print(f"saved: {csv_path}", flush=True)


if __name__ == "__main__":
    main()
