from __future__ import annotations

from dataclasses import dataclass, field
import numpy as np


@dataclass
class PowerTracker:
    n_bins: int
    smoothing: float = 0.8
    regularization_ratio: float = 1e-3
    power: np.ndarray | None = field(default=None, init=False)
    update_count: int = field(default=0, init=False)
    weight_square_sum: float = field(default=1.0, init=False)

    def __post_init__(self) -> None:
        if self.n_bins <= 0:
            raise ValueError("n_bins must be positive")
        if not 0.0 <= self.smoothing < 1.0:
            raise ValueError("smoothing must satisfy 0 <= smoothing < 1")
        if self.regularization_ratio < 0.0:
            raise ValueError("regularization_ratio must be nonnegative")

    def update(self, filtered_reference_spectrum: np.ndarray) -> np.ndarray:
        x = np.asarray(filtered_reference_spectrum)
        if x.shape != (self.n_bins,):
            raise ValueError(f"expected shape {(self.n_bins,)}, got {x.shape}")

        instantaneous = np.abs(x) ** 2

        if self.power is None:
            # P_0 = I_0.  The squared sum of EMA weights is therefore one.
            self.power = instantaneous.astype(float, copy=True)
            self.weight_square_sum = 1.0
        else:
            a = self.smoothing
            self.power = a * self.power + (1.0 - a) * instantaneous
            # If P_b = a P_{b-1} + (1-a) I_b, and the periodograms are
            # independent, the variance multiplier is the squared sum of
            # the EMA weights.  This recursion retains the exact cold-start
            # transient caused by initializing with the first observation.
            self.weight_square_sum = (
                a * a * self.weight_square_sum + (1.0 - a) ** 2
            )

        self.update_count += 1
        return self.power.copy()

    def confidence_weight(self) -> float:
        """Estimate the optimal global/bin-wise shrinkage weight.

        The model is
            P_hat[k] = P[k] + eta[k],
        and
            P_tilde[k] = (1-lambda) P_bar + lambda P_hat[k].

        Under independent complex-Gaussian periodograms,
            Var(P_hat[k]) ~= s_b P[k]^2,
        where s_b is the squared sum of EMA weights.  The true between-bin
        spectral spread is estimated by debiasing the observed spread by the
        expected contribution of estimation noise.
        """
        if self.power is None:
            raise RuntimeError("update() must be called before confidence_weight()")

        p = np.asarray(self.power, dtype=float)
        pbar = float(np.mean(p))

        observed_between = float(np.sum((p - pbar) ** 2))
        uncertainty = float(self.weight_square_sum * np.sum(p**2))

        # Removing the sample mean removes 1/K of the expected independent
        # estimation-noise energy from the observed between-bin spread.
        noise_in_between = (1.0 - 1.0 / self.n_bins) * uncertainty
        signal_between = max(observed_between - noise_in_between, 0.0)

        denom = signal_between + uncertainty
        if denom <= 0.0:
            return 0.0
        return float(np.clip(signal_between / denom, 0.0, 1.0))

    def denominator(
        self,
        mode: str,
        block_index: int,
        switch_block: int | None = None,
        shrinkage_weight: float | None = None,
    ) -> np.ndarray:
        if self.power is None:
            raise RuntimeError("update() must be called before denominator()")

        mode = mode.lower()
        global_power = float(np.mean(self.power))

        # Relative diagonal loading. The numerical floor is only a zero-input guard.
        numerical_floor = np.finfo(float).eps * max(global_power, 1.0)
        loading = self.regularization_ratio * global_power + numerical_floor

        if mode == "global":
            return np.full(self.n_bins, global_power + loading)

        if mode == "binwise":
            return self.power + loading

        if mode == "switched":
            if switch_block is None:
                raise ValueError("switch_block is required for switched mode")
            if block_index < switch_block:
                return np.full(self.n_bins, global_power + loading)
            return self.power + loading

        if mode == "shrinkage":
            if shrinkage_weight is None:
                shrinkage_weight = self.confidence_weight()
            lam = float(np.clip(shrinkage_weight, 0.0, 1.0))
            shrunk_power = (1.0 - lam) * global_power + lam * self.power
            return shrunk_power + loading

        if mode == "uncertainty_floor":
            # Keep bin-wise normalization where the estimated PSD is reliable,
            # but prevent low-power / high-uncertainty bins from receiving a
            # large inverse gain.  The floor ratio is the current EMA variance
            # multiplier s_b, so it starts at one and approaches
            # (1-beta)/(1+beta) without an extra tuning parameter.
            floor_power = self.weight_square_sum * global_power
            return np.maximum(self.power, floor_power) + loading

        raise ValueError(f"unknown normalization mode: {mode}")
