import math
import numpy as np

from ffanc_norm.benchmark_metrics import (
    aggregate_heldout_hop_powers,
    cumulative_power_ratio_db,
    ensemble_power_ratio_db,
    threshold_times_from_db_curve,
)
from ffanc_norm.conventional_baselines import (
    adaptive_decorrelation_step,
    dct_sss_msd_step,
    initialize_sss_diagonal,
    run_dct_sss,
    run_vss2_kernel,
    sss_msd_diagonal_step,
)
from ffanc_norm.vss2_fxnlms import vss2_step_size


def test_sss_initial_msd_rows_sum_to_rho():
    P = initialize_sss_diagonal(4, 16, rho=3.2)
    assert P.shape == (4, 16)
    np.testing.assert_allclose(P.sum(axis=1), 3.2, rtol=0, atol=1e-15)


def test_sss_eq25_one_step_matches_independent_expression():
    P = np.array([0.2, 0.3, 0.5])
    r = np.array([1.1, 0.4, 0.2])
    mu = 0.17
    sigma_e2 = 0.07
    power = 2.3
    got = sss_msd_diagonal_step(P, r, mu, sigma_e2, power)
    rp = np.dot(r, P)
    expected = np.empty_like(P)
    for j in range(len(P)):
        expected[j] = (
            (1 - 2 * mu * r[j] / power) * P[j]
            + mu**2 * sigma_e2 * r[j] / power**2
            + 2 * mu**2 * r[j] * P[j] * r[j] / power**2
            + mu**2 * r[j] * rp / power**2
        )
    np.testing.assert_allclose(got, expected, rtol=1e-14, atol=1e-15)


def test_ad_one_step_matches_direct_predictor_equations():
    xf_past = np.array([0.7, -0.2, 0.1])
    e_past = np.array([-0.4, 0.3, 0.2])
    q = np.array([0.1, -0.05, 0.02])
    xf = 0.9
    e = -0.8
    mu = 0.03
    xf_dec, e_dec, q_new = adaptive_decorrelation_step(xf, e, xf_past, e_past, q, mu)
    expected_x = xf - np.dot(q, xf_past)
    expected_e = e - np.dot(q, e_past)
    expected_q = q + mu * expected_x * xf_past / (np.dot(xf_past, xf_past) + 1e-12)
    assert np.isclose(xf_dec, expected_x)
    assert np.isclose(e_dec, expected_e)
    np.testing.assert_allclose(q_new, expected_q, rtol=1e-14, atol=1e-15)


def test_vss2_formula_has_gamma_inside_arctan_argument():
    beta, gamma, e = 0.36, 0.3, 0.05
    got = vss2_step_size(e, beta, gamma)
    correct = beta * math.atan(abs(e) ** gamma)
    wrong_gamma_outside = beta * (math.atan(abs(e)) ** gamma)
    assert np.isclose(got, correct, rtol=1e-14, atol=1e-15)
    assert not np.isclose(got, wrong_gamma_outside, rtol=1e-4, atol=1e-6)


def test_ad_vss2_kernel_runs_and_uses_finite_steps():
    n = 512
    rng = np.random.default_rng(4)
    x = rng.standard_normal(n)
    s = np.array([0.0, 0.5])
    p = np.array([0.0, 0.8])
    d = np.convolve(x, p, mode='full')[:n]
    xf = np.convolve(x, s, mode='full')[:n]
    v = np.zeros(n)
    stable, e, mu_hist, *_ = run_vss2_kernel(
        x, d, xf, v, s, 0.2, 1.0, 16, 1e-3, 64,
        60.0, 1e4, 1e6, 4, 1e-3,
    )
    assert stable
    assert np.all(np.isfinite(e))
    assert np.all(np.isfinite(mu_hist))
    assert np.all(mu_hist >= 0.0)


def test_dct_sss_eq35_one_step_matches_appendix_formula():
    xh = np.array([0.7, -0.4, 0.2])
    lam = np.array([1.2, 0.8, 0.5])
    J, mu, q, sigma = 2.4, 0.03, 5.0, 0.6
    got = dct_sss_msd_step(J, mu, q, xh, lam, sigma)
    a = np.sum(xh**2 / lam)
    b = np.sum(xh**2 / lam**2)
    expected = J - (2 * mu / q) * a * J + mu**2 * sigma * b
    assert np.isclose(got, expected, rtol=1e-14, atol=1e-15)


def test_dct_sss_reference_runner_smoke():
    n = 256
    rng = np.random.default_rng(5)
    x = rng.standard_normal(n)
    s = np.array([0.0, 0.4])
    p = np.array([0.0, 0.7])
    d = np.convolve(x, p, mode='full')[:n]
    xf = np.convolve(x, s, mode='full')[:n]
    stable, e, mu_hist, *_ = run_dct_sss(
        x, d, xf, np.zeros(n), s, np.array([0.03, 0.015, 0.0075]),
        power_lambda=0.9, q_correlation=5.0, kappa=0.8, rho=5.0,
        controller_length=16, regularization_ratio=1e-3, hop_length=64,
        max_residual_ratio_db=60.0, max_weight_norm_limit=1e5, max_abs_error=1e8,
    )
    assert stable
    assert np.all(np.isfinite(e))
    assert set(np.unique(mu_hist)).issubset({0.03, 0.015, 0.0075})


def test_heldout_aggregation_never_promotes_survivor_only_curve():
    pe = [np.array([1.0, 0.5]), np.array([0.9, 0.4])]
    p0 = [np.ones(2), np.ones(2)]
    result = aggregate_heldout_hop_powers(
        pe, p0, failures=[117], n_total=3, hop_length=128, sample_rate=8000, floor_db=-20.0
    )
    assert result['primary_valid'] is False
    assert result['status'] == 'unstable'
    assert 'points_db' not in result
    assert 'cumulative_2s_db' not in result
    assert 'stable_only_diagnostic' in result


def test_dct_sss_invalid_msd_candidates_abort_cleanly():
    # The paper's example step sizes can be too large when the controller is
    # much longer than in the paper.  Such candidates must invalidate the run
    # cleanly rather than producing a negative MSD and crashing one sample later.
    n = 128
    rng = np.random.default_rng(7)
    x = rng.standard_normal(n)
    s = np.array([0.0, 0.4])
    p = np.array([0.0, 0.7])
    d = np.convolve(x, p, mode='full')[:n]
    xf = np.convolve(x, s, mode='full')[:n]
    stable, e, mu_hist, _max_mu, _max_wnorm, abort_n, reason = run_dct_sss(
        x, d, xf, np.zeros(n), s, np.array([0.3, 0.2]),
        power_lambda=0.9, q_correlation=1.0, kappa=0.8, rho=1.0,
        controller_length=64, regularization_ratio=1e-3, hop_length=64,
        max_residual_ratio_db=60.0, max_weight_norm_limit=1e5, max_abs_error=1e8,
    )
    assert stable is False
    assert abort_n >= 0
    assert reason == 4
    assert np.all(np.isfinite(e[: abort_n + 1]))
    assert np.all(np.isfinite(mu_hist[: abort_n + 1]))


def test_heldout_aggregation_emits_primary_curve_when_all_runs_stable():
    pe = [np.array([1.0, 0.5]), np.array([0.9, 0.4])]
    p0 = [np.ones(2), np.ones(2)]
    result = aggregate_heldout_hop_powers(
        pe, p0, failures=[], n_total=2, hop_length=128, sample_rate=8000, floor_db=-20.0
    )
    assert result['primary_valid'] is True
    assert result['status'] == 'ok'
    assert 'points_db' in result
    assert 'curve_db' in result
    assert 'stable_only_diagnostic' not in result


def test_ensemble_metric_averages_linear_power_before_db():
    pe = np.array([[1.0, 0.01], [0.01, 1.0]])
    p0 = np.ones_like(pe)
    got = ensemble_power_ratio_db(pe, p0)
    expected = 10.0 * np.log10(np.array([0.505, 0.505]))
    np.testing.assert_allclose(got, expected, rtol=0, atol=1e-14)
    per_seed_db_mean = np.mean(10.0 * np.log10(pe / p0), axis=0)
    assert not np.allclose(got, per_seed_db_mean)
    expected_cum = 10.0 * np.log10(1.01 / 2.0)
    assert np.isclose(cumulative_power_ratio_db(pe, p0), expected_cum)


def test_primary_threshold_time_uses_unsmoothed_ensemble_curve():
    db = np.array([-1.0, -4.0, -7.0, -11.0])
    got = threshold_times_from_db_curve(db, 0.016, thresholds=(-3.0, -10.0))
    assert got['-3'] == 0.032
    assert got['-10'] == 0.064
