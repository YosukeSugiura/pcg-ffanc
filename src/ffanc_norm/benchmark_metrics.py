from __future__ import annotations

import math
import numpy as np



def ensemble_power_ratio_db(pe_all: list[np.ndarray] | np.ndarray, p0_all: list[np.ndarray] | np.ndarray) -> np.ndarray:
    """Return an ensemble residual-ratio curve using linear-power averaging.

    Powers are averaged across runs before conversion to dB.  This avoids the
    geometric-mean bias introduced by averaging per-run dB values.
    """
    pe = np.asarray(pe_all, dtype=float)
    p0 = np.asarray(p0_all, dtype=float)
    if pe.shape != p0.shape or pe.ndim != 2 or pe.shape[0] == 0:
        raise ValueError("pe_all and p0_all must form nonempty equal 2-D arrays")
    if not np.all(np.isfinite(pe)) or not np.all(np.isfinite(p0)):
        raise ValueError("power arrays must be finite")
    if np.any(pe < 0.0) or np.any(p0 <= 0.0):
        raise ValueError("error power must be nonnegative and reference power positive")
    return 10.0 * np.log10((np.mean(pe, axis=0) + 1e-300) / np.mean(p0, axis=0))


def cumulative_power_ratio_db(pe_all: list[np.ndarray] | np.ndarray, p0_all: list[np.ndarray] | np.ndarray) -> float:
    """Return cumulative ensemble residual ratio in dB from linear powers."""
    pe = np.asarray(pe_all, dtype=float)
    p0 = np.asarray(p0_all, dtype=float)
    if pe.shape != p0.shape or pe.ndim != 2 or pe.shape[0] == 0:
        raise ValueError("pe_all and p0_all must form nonempty equal 2-D arrays")
    if not np.all(np.isfinite(pe)) or not np.all(np.isfinite(p0)):
        raise ValueError("power arrays must be finite")
    if np.any(pe < 0.0) or np.any(p0 <= 0.0):
        raise ValueError("error power must be nonnegative and reference power positive")
    return float(10.0 * np.log10((np.sum(np.mean(pe, axis=0)) + 1e-300) / np.sum(np.mean(p0, axis=0))))


def threshold_times_from_db_curve(
    db_curve: np.ndarray,
    hop_seconds: float,
    thresholds: tuple[float, ...] = (-3.0, -6.0, -10.0, -15.0, -18.0),
    smooth_hops: int = 1,
) -> dict[str, float | None]:
    """Return first threshold crossings for one ensemble dB curve.

    ``smooth_hops=1`` is the primary definition used for fair comparisons.
    Larger values are allowed only for explicitly labelled diagnostics.
    """
    db = np.asarray(db_curve, dtype=float)
    if db.ndim != 1 or hop_seconds <= 0.0 or smooth_hops <= 0:
        raise ValueError("invalid threshold-time arguments")
    if len(db) < smooth_hops:
        return {f"{th:g}": None for th in thresholds}
    if smooth_hops == 1:
        work = db
        times = (np.arange(len(work)) + 1) * hop_seconds
    else:
        work = np.convolve(db, np.ones(smooth_hops) / smooth_hops, mode="valid")
        times = (np.arange(len(work)) + smooth_hops) * hop_seconds
    out: dict[str, float | None] = {}
    for th in thresholds:
        idx = np.flatnonzero(work <= th)
        out[f"{th:g}"] = float(times[idx[0]]) if len(idx) else None
    return out


def classify_diagnostic_run(
    hop_pe: list[float] | np.ndarray,
    hop_p0: list[float] | np.ndarray,
    *,
    max_weight_norm: float,
    max_abs_error: float,
    disturbance_rms: float,
    max_residual_ratio_db: float = 30.0,
    max_weight_norm_limit: float = 1.0e3,
    max_abs_error_factor: float = 1.0e4,
) -> tuple[bool, str | None]:
    """Classify one diagnostic run using the conventional safety limits.

    The residual-ratio limit is checked hop by hop.  Weight norm and absolute
    error limits mirror the conventional benchmark defaults.
    """
    pe = np.asarray(hop_pe, dtype=float)
    p0 = np.asarray(hop_p0, dtype=float)
    if pe.ndim != 1 or p0.ndim != 1 or pe.shape != p0.shape or pe.size == 0:
        return False, "invalid_power_shape"
    if not np.all(np.isfinite(pe)) or not np.all(np.isfinite(p0)):
        return False, "nonfinite_power"
    if np.any(pe < 0.0) or np.any(p0 <= 0.0):
        return False, "invalid_power"
    hop_db = 10.0 * np.log10((pe + 1e-300) / p0)
    if (not np.all(np.isfinite(hop_db))) or np.any(hop_db > max_residual_ratio_db):
        return False, "residual_ratio"
    if (not math.isfinite(max_weight_norm)) or max_weight_norm > max_weight_norm_limit:
        return False, "weight_norm"
    abs_limit = max_abs_error_factor * max(float(disturbance_rms), 1e-12)
    if (not math.isfinite(max_abs_error)) or max_abs_error > abs_limit:
        return False, "nonfinite_or_abs_error"
    return True, None


def diagnostic_stability_summary(runs: list[dict]) -> tuple[dict, list[dict]]:
    """Return explicit stability metadata and the stable subset.

    Primary metrics should be attached only when ``primary_valid`` is true.
    When it is false, stable-only metrics must be nested under a diagnostic key.
    """
    stable = [r for r in runs if bool(r.get("stable", False))]
    failures = [
        {"seed": int(r.get("seed", -1)), "reason": r.get("failure")}
        for r in runs
        if not bool(r.get("stable", False))
    ]
    return {
        "primary_valid": len(stable) == len(runs),
        "status": "ok" if len(stable) == len(runs) else "unstable",
        "stable": len(stable),
        "n": len(runs),
        "divergence_fraction": 0.0 if not runs else (len(runs) - len(stable)) / len(runs),
        "failures": failures,
    }, stable

def aggregate_heldout_hop_powers(
    pe_all: list[np.ndarray],
    p0_all: list[np.ndarray],
    failures: list[int],
    n_total: int,
    hop_length: int,
    sample_rate: int,
    floor_db: float,
) -> dict:
    """Aggregate held-out runs without survivor bias.

    Primary performance metrics are emitted only when *all* held-out runs are
    stable.  If any run fails, stable-run-only curves are retained strictly as
    diagnostics under ``stable_only_diagnostic`` and cannot be mistaken for the
    primary comparison.
    """
    stable_count = len(pe_all)
    base = {
        "primary_valid": stable_count == n_total,
        "status": "ok" if stable_count == n_total else "unstable",
        "stable": stable_count,
        "n": int(n_total),
        "failures": list(failures),
    }
    if stable_count == 0:
        return base
    pe = np.asarray(pe_all, dtype=float)
    p0 = np.asarray(p0_all, dtype=float)
    if pe.shape != p0.shape or pe.ndim != 2:
        raise ValueError("pe_all and p0_all must form equal 2-D arrays")

    db = 10.0 * np.log10(np.mean(pe, axis=0) / np.mean(p0, axis=0))
    times = (np.arange(len(db)) + 1) * hop_length / sample_rate
    points = {}
    for ts in (0.1, 0.25, 0.5, 1.0, 2.0):
        idx = min(len(db) - 1, max(0, int(math.ceil(ts * sample_rate / hop_length)) - 1))
        points[str(ts)] = float(db[idx])
    thresholds = {}
    for th in (-10, -15, -18):
        idx = np.flatnonzero(db <= th)
        thresholds[str(th)] = float(times[idx[0]]) if len(idx) else None
    idx = np.flatnonzero(db <= floor_db + 0.5)
    thresholds["floor_plus_0.5db"] = float(times[idx[0]]) if len(idx) else None
    cum = 10.0 * np.log10(np.sum(np.mean(pe, axis=0)) / np.sum(np.mean(p0, axis=0)))
    metrics = {
        "points_db": points,
        "threshold_s": thresholds,
        "cumulative_2s_db": float(cum),
        "curve_db": db.tolist(),
    }
    if base["primary_valid"]:
        base.update(metrics)
    else:
        base["stable_only_diagnostic"] = metrics
    return base
