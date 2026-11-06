"""Analytic flop counts per hop (H samples) for the adaptation part of each algorithm.

Conventions: real FFT of length n = 2.5 n log2 n flops; complex multiply = 6,
complex add = 2, real multiply-add = 2. Filtering common to all filtered-x methods
(controller output y = w * x, x_f = S_hat * x, S_hat * y) is reported separately
by `common_filtering`. PCG-WLS is counted by instrumenting the implementation
(ffanc_norm.pcg_wls.FFTCounter); `pcg_wls_model` gives the closed form of the same count.
"""
from __future__ import annotations

import warnings

import numpy as np

from .pcg_wls import fft_flops


def _pow2(n: int) -> int:
    return int(2 ** np.ceil(np.log2(n)))


def common_filtering(M: int, H: int, Ls: int) -> float:
    """y = w * x (overlap-save, block H, new W each hop) + S_hat * x + S_hat * y (direct, length Ls). S_hat * y
    (for d_hat) is needed only by the virtual-residual methods (all except FD-FxNLMS and leaky FD-FxNLMS, which adapt
    on the measured error e): subtract 2 Ls H for those two."""
    n = _pow2(H + M - 1)
    return 3 * fft_flops(n) + 6.0 * (n // 2 + 1) + 2 * 2.0 * Ls * H


def fd_fxnlms(M: int, H: int) -> float:
    """Bin-normalized FD-FxNLMS, overlap-save frame N = 2M: X frame, error frame,
    gradient IFFT (+ causality constraint), power smoothing and normalization."""
    N = 2 * M
    bins = N // 2 + 1
    return 3 * fft_flops(N) + bins * (6.0 + 4.0 + 1.0 + 6.0 + 2.0) + 2.0 * M


def rls(M: int, H: int) -> float:
    """Conventional (MFx-)RLS: k = P x / (lam + x^T P x), P <- (P - k x^T P) / lam; counted as ~3 M^2 + 4 M
    multiply-adds per sample (P x, the rank-1 update and the scaling; exploiting the symmetry of P would give ~2 M^2,
    the implementation (dger + scale + matvec) ~2.5 M^2: same order)."""
    return H * 2.0 * (3.0 * M * M + 4.0 * M)


def sftf(M: int, H: int) -> float:
    """Stabilized fast transversal filter (Slock & Kailath 1991): 8 M multiplies + 8 M adds per sample. Same output as
    RLS except for the initial transient (initialization); numerical stability for lam close to 1 to be checked."""
    return H * 16.0 * M


def pcg_wls_model(M: int, H: int, kd: int, k_main: int, detect: bool = True) -> float:
    """Closed-form steady-state PCG-WLS count per hop (matches the instrumented implementation).
    FFT counts: statistics 5 (size >= H+M-1), boundary FFTs 3, circulant symbols 2,
    detector apply 9, detector PCG 2 + 8 kd, main PCG 2 + 8 k_main (sizes 2M)."""
    n2 = 2 * M
    nseg = _pow2(H + M - 1)
    f2 = fft_flops(n2)
    if detect:
        n_f2 = 3 + 2 + 9 + (2 + 8 * kd) + (2 + 8 * k_main)
    else:
        n_f2 = 2 + 1 + 6 + (2 + 8 * k_main)   # boundaries 2, symbol 1, G w 6
    vec = (M + 1) * (2 * 6.0 + 18.0 * (n_f2 // 2)) + 12.0 * M * (kd + k_main + 2)
    return 5 * fft_flops(nseg) + n_f2 * f2 + vec


def epcg_model(M: int, H: int, kd: int, k_main: int, detect: bool = True) -> float:
    """Deprecated alias of `pcg_wls_model` (the method was called E-PCG before v1.1.0)."""
    warnings.warn("cost.epcg_model is deprecated; use cost.pcg_wls_model", DeprecationWarning, stacklevel=2)
    return pcg_wls_model(M, H, kd, k_main, detect)


# ---- 2026-10-30: estimates for the remaining baselines of the final evaluation (adaptation part, per hop) ----
def leaky_fd_fxnlms(M: int, H: int) -> float:
    """FD-FxNLMS + leakage w <- (1 - mu leak) w (one multiply-add per tap)."""
    return fd_fxnlms(M, H) + 2.0 * M


def convex_fd_fxnlms(M: int, H: int) -> float:
    """Two FD-FxNLMS filters + the second filter's output (overlap-save, new W each hop) + mixing and the
    mixing-parameter update (~10 flops per sample)."""
    n = _pow2(H + M - 1)
    return 2 * fd_fxnlms(M, H) + 2 * fft_flops(n) + 6.0 * (n // 2 + 1) + 10.0 * H


def fdkf(M: int, H: int) -> float:
    """Frequency-domain Kalman filter (diagonal, C-FDKF): FD-FxNLMS-like frame transforms + the virtual residual
    r = d_hat + x_f * w (2 FFTs) + W = rfft(w) for the covariance update (1 FFT) + per-bin covariance and gain update
    (~40 real flops per bin). (Revised 2026-10-30 after review: the first estimate omitted the 3 FFTs.)"""
    N = 2 * M
    return fd_fxnlms(M, H) + 3 * fft_flops(N) + 40.0 * (M + 1)


def vff_rls(M: int, H: int) -> float:
    """RLS + variable forgetting factor (u^T k and the lambda update: ~2 M + 10 flops per sample)."""
    return rls(M, H) + H * (2.0 * M + 10.0)
