from __future__ import annotations

from dataclasses import dataclass
import numpy as np

from .blocking import FrameScheduler
from .fd_fxnlms import FDFxNLMS


def right_aligned_history(signal: np.ndarray, end: int, length: int) -> np.ndarray:
    """Return `length` samples ending at `end`, with left zero padding."""
    if end < 0 or end > len(signal):
        raise ValueError("invalid end")
    out = np.zeros(length, dtype=float)
    start = max(0, end - length)
    available = signal[start:end]
    if len(available):
        out[-len(available):] = available
    return out


def causal_fir_block(
    signal: np.ndarray,
    coeffs: np.ndarray,
    start: int,
    stop: int,
) -> np.ndarray:
    """Causal FIR outputs for [start, stop), assuming signal is known to stop-1."""
    signal = np.asarray(signal, dtype=float)
    coeffs = np.asarray(coeffs, dtype=float)
    if start < 0 or stop < start or stop > len(signal):
        raise ValueError("invalid block range")
    if len(coeffs) == 0:
        return np.zeros(stop - start, dtype=float)

    hist_start = max(0, start - len(coeffs) + 1)
    segment = signal[hist_start:stop]
    conv = np.convolve(segment, coeffs, mode="full")
    i0 = start - hist_start
    i1 = stop - hist_start
    return conv[i0:i1].copy()



def transition_equivalent_error_block(
    x: np.ndarray,
    actual_controller_output: np.ndarray,
    current_weights: np.ndarray,
    secondary_path_model: np.ndarray,
    physical_error_block: np.ndarray,
    start: int,
    stop: int,
) -> tuple[np.ndarray, np.ndarray]:
    """Return a current-filter-equivalent virtual error for one block.

    The physical error contains secondary-path memory generated before ``start``
    by older controller coefficients. This function replaces only that legacy
    controller-output history by the output that the *current* coefficients
    would have generated. Samples generated at or after ``start`` are untouched.

    Returns
    -------
    virtual_error:
        ``physical_error_block + transition_correction``.
    transition_correction:
        Secondary-path response of ``y_current - y_actual`` over the legacy
        controller-output samples that can still affect [start, stop).

    Notes
    -----
    This is an adaptation-domain counterfactual signal. It does not alter the
    physical ANC output or the performance metric. In a realizable algorithm,
    ``secondary_path_model`` would be the available secondary-path estimate.
    """
    x = np.asarray(x, dtype=float)
    y_actual = np.asarray(actual_controller_output, dtype=float)
    w = np.asarray(current_weights, dtype=float)
    shat = np.asarray(secondary_path_model, dtype=float)
    e_block = np.asarray(physical_error_block, dtype=float)

    if start < 0 or stop < start or stop > len(x):
        raise ValueError("invalid block range")
    if y_actual.shape != x.shape:
        raise ValueError("actual_controller_output must match x length")
    if e_block.shape != (stop - start,):
        raise ValueError("physical_error_block must match the block length")
    if len(shat) == 0 or start == 0:
        correction = np.zeros(stop - start, dtype=float)
        return e_block.copy(), correction

    memory = len(shat) - 1
    hist_start = max(0, start - memory)
    if hist_start == start:
        correction = np.zeros(stop - start, dtype=float)
        return e_block.copy(), correction

    # Recompute only the legacy controller-output samples that can still enter
    # the secondary path during the current block, using the current weights.
    y_current_hist = causal_fir_block(x, w, hist_start, start)
    delta = np.zeros(stop, dtype=float)
    delta[hist_start:start] = y_current_hist - y_actual[hist_start:start]
    correction = causal_fir_block(delta, shat, start, stop)
    return e_block + correction, correction

def secondary_noise_for_snr(
    disturbance: np.ndarray,
    snr_db: float | None,
    rng: np.random.Generator,
) -> np.ndarray:
    """Independent white secondary noise with SNR referenced to disturbance power."""
    disturbance = np.asarray(disturbance, dtype=float)
    if snr_db is None:
        return np.zeros_like(disturbance)

    pd = float(np.mean(disturbance**2))
    if pd <= 0.0:
        raise ValueError("disturbance power must be positive")

    pv = pd / (10.0 ** (float(snr_db) / 10.0))
    v = rng.standard_normal(len(disturbance))
    v -= float(np.mean(v))
    std = float(np.std(v))
    if std == 0.0:
        raise RuntimeError("failed to generate nonzero secondary noise")
    return v * (np.sqrt(pv) / std)


@dataclass
class FFANCSimulationResult:
    error: np.ndarray
    anc_residual: np.ndarray
    disturbance: np.ndarray
    secondary_noise: np.ndarray
    controller_output: np.ndarray
    secondary_output: np.ndarray
    attenuation_db_per_hop: np.ndarray
    anc_residual_attenuation_db_per_hop: np.ndarray
    controller_history: np.ndarray


def run_ffanc(
    x: np.ndarray,
    primary_path: np.ndarray,
    secondary_path: np.ndarray,
    secondary_model: np.ndarray,
    algorithm: FDFxNLMS,
    secondary_noise: np.ndarray | None = None,
    power_warmup_hops: int = 0,
) -> FFANCSimulationResult:
    """Run causal FFANC with coefficients frozen within each H-sample hop.

    If power_warmup_hops > 0, the controller remains fixed during those hops
    while only the filtered-reference power tracker is updated. This is useful
    for stationary-theory validation without FFT-history startup transients.

    Sign convention:
        y = W*x
        y_s = S*y
        e_c = d + y_s
        e = e_c + v

    where v is independent secondary noise at the error sensor.
    """
    x = np.asarray(x, dtype=float)
    p = np.asarray(primary_path, dtype=float)
    s = np.asarray(secondary_path, dtype=float)
    shat = np.asarray(secondary_model, dtype=float)

    if x.ndim != 1:
        raise ValueError("x must be one-dimensional")

    n_samples = len(x)
    H = algorithm.hop_length
    N = algorithm.fft_length

    disturbance = np.convolve(x, p, mode="full")[:n_samples]
    filtered_reference = np.convolve(x, shat, mode="full")[:n_samples]

    if secondary_noise is None:
        v = np.zeros(n_samples, dtype=float)
    else:
        v = np.asarray(secondary_noise, dtype=float)
        if v.shape != (n_samples,):
            raise ValueError("secondary_noise must match x length")

    y = np.zeros(n_samples, dtype=float)
    sec = np.zeros(n_samples, dtype=float)
    anc_residual = disturbance.copy()
    error = disturbance + v

    scheduler = FrameScheduler(N, H)
    attenuation = []
    anc_residual_attenuation = []
    controller_history = [algorithm.w.copy()]

    if power_warmup_hops < 0:
        raise ValueError("power_warmup_hops must be nonnegative")

    for hop_index, (start, stop) in enumerate(scheduler.hop_ranges(n_samples)):
        # Freeze the controller during the entire H-sample hop.
        w_block = algorithm.w.copy()

        y[start:stop] = causal_fir_block(x, w_block, start, stop)
        sec[start:stop] = causal_fir_block(y, s, start, stop)
        anc_residual[start:stop] = disturbance[start:stop] + sec[start:stop]
        error[start:stop] = anc_residual[start:stop] + v[start:stop]

        xf_history = right_aligned_history(filtered_reference, stop, N)
        new_error = error[start:stop].copy()

        if hop_index < power_warmup_hops:
            # Estimate stationary filtered-reference power without adapting w.
            algorithm.power_tracker.update(np.fft.rfft(xf_history))
            controller_history.append(algorithm.w.copy())
            continue

        algorithm.update(xf_history, new_error)
        controller_history.append(algorithm.w.copy())

        # Total residual is normalized by the uncontrolled error-microphone signal d+v.
        pe = float(np.mean(new_error**2))
        p0 = float(np.mean((disturbance[start:stop] + v[start:stop]) ** 2))
        attenuation.append(10.0 * np.log10((pe + 1e-15) / (p0 + 1e-15)))

        # ANC-only metric excludes the independent secondary noise.
        pec = float(np.mean(anc_residual[start:stop] ** 2))
        pd = float(np.mean(disturbance[start:stop] ** 2))
        anc_residual_attenuation.append(
            10.0 * np.log10((pec + 1e-15) / (pd + 1e-15))
        )

    return FFANCSimulationResult(
        error=error,
        anc_residual=anc_residual,
        disturbance=disturbance,
        secondary_noise=v,
        controller_output=y,
        secondary_output=sec,
        attenuation_db_per_hop=np.asarray(attenuation),
        anc_residual_attenuation_db_per_hop=np.asarray(anc_residual_attenuation),
        controller_history=np.asarray(controller_history),
    )
