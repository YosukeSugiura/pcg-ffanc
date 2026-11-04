from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

import numpy as np
from scipy.signal import lfilter

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))

from ffanc_norm.benchmark_metrics import (
    classify_diagnostic_run,
    diagnostic_stability_summary,
    ensemble_power_ratio_db,
    threshold_times_from_db_curve,
)
from ffanc_norm.normalization import PowerTracker
from ffanc_norm.paths import synthetic_primary_path, synthetic_secondary_path
from ffanc_norm.signals import colored_noise
from ffanc_norm.simulation import causal_fir_block, right_aligned_history, secondary_noise_for_snr


def synthesis_basis(n_fft: int, controller_length: int) -> np.ndarray:
    """Real synthesis map for rFFT-bin-wise real multipliers.

    For a one-sided complex spectrum z and real per-bin vector mu,
        irfft(mu * z, n=N)[:M] = D(z) @ mu,
    where D(z) = real(S * z[None, :]).
    """
    k_bins = n_fft // 2 + 1
    m = np.arange(controller_length)[:, None]
    k = np.arange(k_bins)[None, :]
    weights = np.full(k_bins, 2.0 / n_fft)
    weights[0] = 1.0 / n_fft
    if n_fft % 2 == 0:
        weights[-1] = 1.0 / n_fft
    return np.exp(2j * np.pi * m * k / n_fft) * weights[None, :]


def future_controller_to_secondary_matrix(
    x: np.ndarray,
    secondary_path: np.ndarray,
    start: int,
    stop: int,
    controller_length: int,
) -> np.ndarray:
    """Map a controller coefficient vector to future secondary output change.

    The coefficient change is applied only from `start` onward. Therefore the
    returned matrix contains no fictitious modification of already-generated
    controller output and exactly preserves secondary-path legacy memory.
    """
    t = np.arange(start, stop)[:, None]
    m = np.arange(controller_length)[None, :]
    idx = t - m
    X = np.zeros(idx.shape, dtype=float)
    valid = (idx >= 0) & (idx < len(x))
    X[valid] = x[idx[valid]]
    return lfilter(secondary_path, [1.0], X, axis=0)


def per_bin_gradient_basis(
    filtered_reference_history: np.ndarray,
    new_error: np.ndarray,
    denominator: np.ndarray,
    synth: np.ndarray,
) -> np.ndarray:
    """Return D such that controller update is w_new = w - D @ mu_bins."""
    N = len(filtered_reference_history)
    H = len(new_error)
    e_frame = np.zeros(N, dtype=float)
    e_frame[-H:] = new_error
    Xf = np.fft.rfft(filtered_reference_history)
    E = np.fft.rfft(e_frame)
    z = np.conj(Xf) * E / denominator
    return np.real(synth * z[None, :])


def threshold_times(hop_db: np.ndarray, hop_seconds: float) -> dict[str, float | None]:
    k = 5
    out: dict[str, float | None] = {}
    if len(hop_db) < k:
        return {str(th): None for th in (-3, -6, -10, -15, -18)}
    smooth = np.convolve(hop_db, np.ones(k) / k, mode='valid')
    times = (np.arange(len(smooth)) + k) * hop_seconds
    for th in (-3, -6, -10, -15, -18):
        idx = np.flatnonzero(smooth <= th)
        out[str(th)] = float(times[idx[0]]) if len(idx) else None
    return out


def solve_box_ls(B: np.ndarray, a: np.ndarray, mu_cap: float, x0: np.ndarray | None = None) -> np.ndarray:
    """Minimum-norm box-constrained least squares via projected FISTA.

    The objective is convex quadratic. A tiny ridge selects the minimum-norm
    solution when the physical future-residual problem is non-unique.
    """
    K = B.shape[1]
    mean_col_energy = float(np.sum(B * B) / max(K, 1))
    ridge = 1e-10 * max(mean_col_energy, 1e-30)
    G = B.T @ B
    G.flat[::K + 1] += ridge
    c = B.T @ a

    # Deterministic power iteration for a safe Lipschitz constant.
    q = np.ones(K, dtype=float) / np.sqrt(K)
    for _ in range(20):
        z = G @ q
        nz = float(np.linalg.norm(z))
        if nz <= 1e-30:
            return np.zeros(K, dtype=float)
        q = z / nz
    L = float(q @ (G @ q)) * 1.001
    if L <= 1e-30:
        return np.zeros(K, dtype=float)

    if x0 is None or x0.shape != (K,):
        x = np.zeros(K, dtype=float)
    else:
        x = np.clip(x0, 0.0, mu_cap).astype(float, copy=True)
    y = x.copy()
    tk = 1.0

    for _ in range(250):
        x_new = np.clip(y - (G @ y - c) / L, 0.0, mu_cap)
        if np.linalg.norm(x_new - x) <= 1e-8 * max(1.0, np.linalg.norm(x)):
            x = x_new
            break
        tk_new = 0.5 * (1.0 + np.sqrt(1.0 + 4.0 * tk * tk))
        y = x_new + ((tk - 1.0) / tk_new) * (x_new - x)
        x = x_new
        tk = tk_new
    return x


def run_one(cfg: dict, seed: int, mu_cap: float, horizon_hops: int, eval_seconds: float) -> dict:
    N = int(cfg['fft_length'])
    H = int(cfg['hop_length'])
    M = int(cfg['controller_length'])
    fs = int(cfg['sample_rate'])

    eval_samples = int(round(eval_seconds * fs))
    # Extra signal is needed for the final receding-horizon query.
    n_samples = eval_samples + horizon_hops * H

    rng_x = np.random.default_rng(seed)
    rng_v = np.random.default_rng(seed + 1000003)
    x = colored_noise(n_samples, rng_x, pole=0.95)
    p = synthetic_primary_path()
    s = synthetic_secondary_path()
    d = np.convolve(x, p, mode='full')[:n_samples]
    xf = np.convolve(x, s, mode='full')[:n_samples]
    v = secondary_noise_for_snr(d[:eval_samples], cfg.get('secondary_noise_snr_db'), rng_v)
    # Use the same target variance for the horizon extension.
    if n_samples > eval_samples:
        pd = float(np.mean(d[:eval_samples] ** 2))
        pv = pd / (10.0 ** (float(cfg['secondary_noise_snr_db']) / 10.0))
        v_ext = rng_v.standard_normal(n_samples - eval_samples) * np.sqrt(pv)
        v = np.concatenate([v, v_ext])

    power = PowerTracker(N // 2 + 1, float(cfg['power_smoothing']), float(cfg['regularization_ratio']))
    synth = synthesis_basis(N, M)

    w = np.zeros(M, dtype=float)
    y = np.zeros(n_samples, dtype=float)
    sec = np.zeros(n_samples, dtype=float)
    e = d + v
    anc = d.copy()

    hop_db = []
    hop_pe = []
    hop_p0 = []
    max_weight_norm_seen = 0.0
    max_abs_error_seen = 0.0
    mu_hist = []
    active_upper_fraction = []
    active_zero_fraction = []

    n_eval_hops = eval_samples // H
    for b in range(n_eval_hops):
        start = b * H
        stop = start + H

        y[start:stop] = causal_fir_block(x, w, start, stop)
        sec[start:stop] = causal_fir_block(y, s, start, stop)
        anc[start:stop] = d[start:stop] + sec[start:stop]
        e[start:stop] = anc[start:stop] + v[start:stop]
        max_abs_error_seen = max(max_abs_error_seen, float(np.max(np.abs(e[start:stop]))))

        xf_hist = right_aligned_history(xf, stop, N)
        Xf = np.fft.rfft(xf_hist)
        power.update(Xf)
        denominator = power.denominator('binwise', b)
        D = per_bin_gradient_basis(xf_hist, e[start:stop], denominator, synth)

        future_start = stop
        future_stop = min(n_samples, stop + horizon_hops * H)
        if future_stop > future_start:
            # Future residual with no update. Past y is kept exactly; future y is
            # generated by the current controller.
            y0 = y.copy()
            y0[future_start:future_stop] = causal_fir_block(x, w, future_start, future_stop)
            sec0 = causal_fir_block(y0, s, future_start, future_stop)
            a = d[future_start:future_stop] + sec0

            R = future_controller_to_secondary_matrix(x, s, future_start, future_stop, M)
            B = R @ D
            # residual(mu) = a - B mu. Independent sensor noise is omitted from
            # the oracle objective because its expected contribution is constant.
            mu_bins = solve_box_ls(B, a, mu_cap, mu_hist[-1] if mu_hist else None)
        else:
            mu_bins = np.zeros(N // 2 + 1)

        w = w - D @ mu_bins
        max_weight_norm_seen = max(max_weight_norm_seen, float(np.linalg.norm(w)))
        mu_hist.append(mu_bins)
        tol = max(1e-8, 1e-5 * mu_cap)
        active_upper_fraction.append(float(np.mean(mu_bins >= mu_cap - tol)))
        active_zero_fraction.append(float(np.mean(mu_bins <= tol)))

        pe = float(np.mean(e[start:stop] ** 2))
        p0 = float(np.mean((d[start:stop] + v[start:stop]) ** 2))
        hop_pe.append(pe)
        hop_p0.append(p0)
        hop_db.append(10.0 * np.log10((pe + 1e-15) / (p0 + 1e-15)))

    mu_hist = np.asarray(mu_hist)
    hop_db = np.asarray(hop_db)
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
        'seed': seed,
        'mu_cap': mu_cap,
        'hop_length': H,
        'sample_rate': fs,
        'threshold_times_s': threshold_times(hop_db, H / fs),
        'mu_mean_first_block': float(np.mean(mu_hist[0])) if len(mu_hist) else 0.0,
        'mu_max_first_block': float(np.max(mu_hist[0])) if len(mu_hist) else 0.0,
        'upper_fraction_first_block': float(active_upper_fraction[0]) if active_upper_fraction else 0.0,
        'zero_fraction_first_block': float(active_zero_fraction[0]) if active_zero_fraction else 0.0,
        'mu_mean_first_10': float(np.mean(mu_hist[:10])) if len(mu_hist) else 0.0,
        'upper_fraction_first_10': float(np.mean(active_upper_fraction[:10])) if active_upper_fraction else 0.0,
        'zero_fraction_first_10': float(np.mean(active_zero_fraction[:10])) if active_zero_fraction else 0.0,
        'hop_db': hop_db.tolist(),
        'hop_pe': list(map(float, hop_pe)),
        'hop_p0': list(map(float, hop_p0)),
        'mu_history_first_10': mu_hist[:10].tolist(),
    }


def summarize(runs: list[dict]) -> dict:
    out = {}
    caps = sorted({r['mu_cap'] for r in runs})
    for cap in caps:
        rr = [r for r in runs if r['mu_cap'] == cap]
        status, stable_rr = diagnostic_stability_summary(rr)
        d = {
            **status,
            'metric_definition': 'linear power averaged across seeds before conversion to dB; primary metrics require every seed to be stable; primary thresholds use no temporal smoothing',
        }
        if stable_rr:
            pe = np.asarray([r['hop_pe'] for r in stable_rr], dtype=float)
            p0 = np.asarray([r['hop_p0'] for r in stable_rr], dtype=float)
            curve = ensemble_power_ratio_db(pe, p0)
            metrics = {
                'mu_mean_first_block': float(np.mean([r['mu_mean_first_block'] for r in stable_rr])),
                'mu_max_first_block': float(np.mean([r['mu_max_first_block'] for r in stable_rr])),
                'upper_fraction_first_block': float(np.mean([r['upper_fraction_first_block'] for r in stable_rr])),
                'zero_fraction_first_block': float(np.mean([r['zero_fraction_first_block'] for r in stable_rr])),
                'mu_mean_first_10': float(np.mean([r['mu_mean_first_10'] for r in stable_rr])),
                'upper_fraction_first_10': float(np.mean([r['upper_fraction_first_10'] for r in stable_rr])),
                'zero_fraction_first_10': float(np.mean([r['zero_fraction_first_10'] for r in stable_rr])),
                'ensemble_hop_db': curve.tolist(),
                'ensemble_threshold_times_s': threshold_times_from_db_curve(curve, stable_rr[0]['hop_length'] / stable_rr[0]['sample_rate']),
                'per_seed_smoothed_threshold_diagnostic': {},
            }
            for th in ('-3', '-6', '-10', '-15', '-18'):
                vals = [r['threshold_times_s'][th] for r in stable_rr if r['threshold_times_s'][th] is not None]
                metrics['per_seed_smoothed_threshold_diagnostic'][th] = {
                    'mean_s': float(np.mean(vals)) if vals else None,
                    'success_fraction': len(vals) / len(stable_rr),
                }
            if status['primary_valid']:
                d.update(metrics)
            else:
                d['stable_only_diagnostic'] = metrics
        out[str(cap)] = d
    return out

def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument('--config', default=str(ROOT / 'configs' / 'oracle_2s.json'))
    ap.add_argument('--caps', nargs='+', type=float, default=[1.0, 2.0, 4.0, 8.0])
    ap.add_argument('--n-seeds', type=int, default=5)
    ap.add_argument('--seed-start', type=int, default=2000)
    ap.add_argument('--horizon-hops', type=int, default=4)
    ap.add_argument('--eval-seconds', type=float, default=0.75)
    args = ap.parse_args()

    cfg = json.loads(Path(args.config).read_text())
    runs = []
    for cap in args.caps:
        for seed in range(args.seed_start, args.seed_start + args.n_seeds):
            print(f'cap={cap:g}, seed={seed}', flush=True)
            runs.append(run_one(cfg, seed, cap, args.horizon_hops, args.eval_seconds))

    result = {
        'config': cfg,
        'caps': args.caps,
        'n_seeds': args.n_seeds,
        'seed_start': args.seed_start,
        'horizon_hops': args.horizon_hops,
        'eval_seconds': args.eval_seconds,
        'summary': summarize(runs),
    }
    out_dir = ROOT / 'results' / 'per_bin_oracle_cap_sweep'
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / 'summary.json').write_text(json.dumps(result, indent=2))
    (out_dir / 'runs.json').write_text(json.dumps(runs))
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
