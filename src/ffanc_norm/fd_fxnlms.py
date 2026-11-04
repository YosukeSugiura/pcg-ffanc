from __future__ import annotations

from dataclasses import dataclass
import numpy as np

from .normalization import PowerTracker


def fd_block_gradient(
    filtered_reference_history: np.ndarray,
    new_error: np.ndarray,
    denominator: np.ndarray,
    controller_length: int,
) -> np.ndarray:
    """Compute the causal block gradient using one FFT correlation.

    The new H error samples are right-aligned in an N-point zero-padded frame.
    If N >= M + H - 1, the first M IFFT samples equal the desired
    non-circular time-domain block gradient.
    """
    xf = np.asarray(filtered_reference_history, dtype=float)
    err = np.asarray(new_error, dtype=float)
    denom = np.asarray(denominator, dtype=float)

    N = xf.size
    H = err.size
    M = int(controller_length)

    if N <= 0 or H <= 0 or M <= 0:
        raise ValueError("N, H, and M must be positive")
    if H > N:
        raise ValueError("new_error must not be longer than the FFT frame")
    if M > N:
        raise ValueError("controller_length must not exceed FFT length")
    if N < M + H - 1:
        raise ValueError("need N >= M + H - 1 to avoid circular aliasing")
    if denom.shape != (N // 2 + 1,):
        raise ValueError("unexpected denominator shape")
    if np.any(denom <= 0.0):
        raise ValueError("denominator must be strictly positive")

    e_frame = np.zeros(N, dtype=float)
    e_frame[-H:] = err

    Xf = np.fft.rfft(xf)
    E = np.fft.rfft(e_frame)

    gradient_f = np.conj(Xf) * E / denom
    gradient_t = np.fft.irfft(gradient_f, n=N)

    # NumPy's inverse FFT already contains the 1/N factor.
    return gradient_t[:M].copy()


def direct_block_gradient(
    filtered_reference_history: np.ndarray,
    new_error: np.ndarray,
    controller_length: int,
) -> np.ndarray:
    """Unnormalized direct time-domain gradient for validation."""
    xf = np.asarray(filtered_reference_history, dtype=float)
    err = np.asarray(new_error, dtype=float)

    N = xf.size
    H = err.size
    M = int(controller_length)

    if N < M + H - 1:
        raise ValueError("need N >= M + H - 1")

    first_error_index = N - H
    out = np.zeros(M, dtype=float)

    for m in range(M):
        indices = np.arange(first_error_index, N) - m
        out[m] = np.dot(err, xf[indices])

    return out


@dataclass
class FDFxNLMS:
    fft_length: int
    hop_length: int
    controller_length: int
    mu: float
    smoothing: float
    regularization_ratio: float
    mode: str
    switch_block: int | None = None
    mu_global: float | None = None
    mu_binwise: float | None = None

    def __post_init__(self) -> None:
        N = self.fft_length
        H = self.hop_length
        M = self.controller_length

        if N <= 0:
            raise ValueError("fft_length must be positive")
        if H <= 0 or H > N:
            raise ValueError("invalid hop_length")
        if M <= 0 or M > N:
            raise ValueError("invalid controller_length")
        if N < M + H - 1:
            raise ValueError("need fft_length >= controller_length + hop_length - 1")
        if self.mu <= 0.0:
            raise ValueError("mu must be positive")
        if self.mode.lower() == "shrinkage":
            if self.mu_global is None or self.mu_binwise is None:
                raise ValueError("shrinkage mode requires mu_global and mu_binwise")
            if self.mu_global <= 0.0 or self.mu_binwise <= 0.0:
                raise ValueError("mu_global and mu_binwise must be positive")

        self.n_bins = N // 2 + 1
        self.w = np.zeros(M, dtype=float)
        self.power_tracker = PowerTracker(
            n_bins=self.n_bins,
            smoothing=self.smoothing,
            regularization_ratio=self.regularization_ratio,
        )
        self.block_index = 0
        self.shrinkage_weight_history: list[float] = []
        self.mu_history: list[float] = []

    def update(
        self,
        filtered_reference_history: np.ndarray,
        new_error: np.ndarray,
    ) -> np.ndarray:
        xf = np.asarray(filtered_reference_history, dtype=float)
        err = np.asarray(new_error, dtype=float)

        if xf.shape != (self.fft_length,):
            raise ValueError("filtered_reference_history must have fft_length samples")
        if err.shape != (self.hop_length,):
            raise ValueError("new_error must have hop_length samples")

        Xf = np.fft.rfft(xf)
        self.power_tracker.update(Xf)

        mode = self.mode.lower()
        if mode == "shrinkage":
            lam = self.power_tracker.confidence_weight()
            denom = self.power_tracker.denominator(
                mode=mode,
                block_index=self.block_index,
                shrinkage_weight=lam,
            )
            mu_eff = (1.0 - lam) * float(self.mu_global) + lam * float(self.mu_binwise)
            self.shrinkage_weight_history.append(lam)
        else:
            denom = self.power_tracker.denominator(
                mode=mode,
                block_index=self.block_index,
                switch_block=self.switch_block,
            )
            mu_eff = self.mu
            self.shrinkage_weight_history.append(float("nan"))

        self.mu_history.append(mu_eff)

        gradient = fd_block_gradient(
            filtered_reference_history=xf,
            new_error=err,
            denominator=denom,
            controller_length=self.controller_length,
        )

        # With e = d + s*y and y = w*x, descent uses a minus sign.
        self.w -= mu_eff * gradient
        self.block_index += 1
        return gradient
