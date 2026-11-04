import math
import numpy as np

from ffanc_norm.vss2_fxnlms import VSS2SafetyLimits, vss2_step_size


def test_vss2_step_size_matches_direct_formula_in_normal_range():
    beta = 0.36
    gamma = 0.7
    for e in [0.0, 1e-3, 0.1, 1.0, 3.0, 10.0]:
        expected = beta * math.atan(abs(e) ** gamma)
        assert np.isclose(vss2_step_size(e, beta, gamma), expected, rtol=1e-13, atol=1e-15)


def test_vss2_step_size_saturates_without_overflow():
    beta = 0.36
    mu = vss2_step_size(1e308, beta, 100.0)
    assert np.isfinite(mu)
    assert np.isclose(mu, beta * math.pi / 2.0)


def test_vss2_step_size_is_even_and_bounded():
    beta = 0.5
    gamma = 1.2
    for e in [1e-8, 0.1, 1.0, 10.0, 1e30]:
        assert vss2_step_size(e, beta, gamma) == vss2_step_size(-e, beta, gamma)
        assert 0.0 <= vss2_step_size(e, beta, gamma) <= beta * math.pi / 2.0


def test_safety_limits_validate_positive_values():
    limits = VSS2SafetyLimits()
    assert limits.max_residual_ratio_db > 0
    assert limits.max_weight_norm > 0
    assert limits.max_abs_error_factor > 0
