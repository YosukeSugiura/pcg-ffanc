from __future__ import annotations

from dataclasses import dataclass
import math
import numpy as np


def vss2_step_size(error_magnitude: float, beta: float, gamma: float) -> float:
    """Numerically safe VSS2 step-size.

    Implements the arctangent VSS rule reproduced for VSS2-FxNLMS in later
    ANC literature (following Gomathi et al., 2016):

        mu(n) = beta * atan(|e(n)|**gamma).

    ``gamma`` is the exponent of the error magnitude *inside* atan.  This
    detail is regression-tested because moving gamma outside atan changes the
    algorithm materially.
    """
    if beta <= 0.0 or not np.isfinite(beta):
        raise ValueError("beta must be finite and positive")
    if gamma <= 0.0 or not np.isfinite(gamma):
        raise ValueError("gamma must be finite and positive")

    a = abs(float(error_magnitude))
    if not math.isfinite(a):
        return float(beta * (math.pi / 2.0))
    if a == 0.0:
        return 0.0

    z = gamma * math.log(a)
    if z >= 36.0:
        return float(beta * (math.pi / 2.0))
    if z <= -745.0:
        return 0.0
    return float(beta * math.atan(math.exp(z)))


@dataclass(frozen=True)
class VSS2SafetyLimits:
    """Early-abort thresholds for optimization-time robustness checks."""

    max_residual_ratio_db: float = 30.0
    max_weight_norm: float = 1.0e3
    max_abs_error_factor: float = 1.0e4

    def __post_init__(self) -> None:
        if self.max_residual_ratio_db <= 0.0:
            raise ValueError("max_residual_ratio_db must be positive")
        if self.max_weight_norm <= 0.0:
            raise ValueError("max_weight_norm must be positive")
        if self.max_abs_error_factor <= 0.0:
            raise ValueError("max_abs_error_factor must be positive")
