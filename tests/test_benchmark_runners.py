"""Regression tests for the restored benchmark / optimization runners.

These use tiny signals only; they check wiring and fairness rules, not
performance numbers.
"""
from pathlib import Path
import sys
import warnings

import numpy as np
import pytest

pytest.importorskip("optuna")

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "experiments"))

import benchmark_conventional_limit as bcl  # noqa: E402
import benchmark_transient_oracles as bto  # noqa: E402
import optimize_vss2_robust as ovr  # noqa: E402
from ffanc_norm import runtime  # noqa: E402
from ffanc_norm.conventional_baselines import run_vss2_kernel  # noqa: E402
from ffanc_norm.paths import synthetic_secondary_path  # noqa: E402
from ffanc_norm.vss2_fxnlms import VSS2SafetyLimits  # noqa: E402

CFG = {
    "fft_length": 512,
    "hop_length": 128,
    "controller_length": 256,
    "sample_rate": 8000,
    "mu_global": 0.055,
    "mu_binwise": 0.35,
    "power_smoothing": 0.8,
    "regularization_ratio": 0.001,
    "secondary_noise_snr_db": 20.0,
}


def test_oracle_and_conventional_heldout_signals_are_sample_identical():
    seed, seconds = 101, 0.064
    data = ovr.make_seed_data(CFG, seed, seconds)
    x, d, v, _p, _s, n_eval = bto._make_signals(CFG, seed, extra_hops=4, eval_seconds=seconds)
    assert n_eval == data.x.size
    np.testing.assert_allclose(x[:n_eval], data.x, rtol=1e-12, atol=1e-12)
    np.testing.assert_allclose(d[:n_eval], data.d, rtol=1e-12, atol=1e-12)
    np.testing.assert_allclose(v[:n_eval], data.v, rtol=1e-12, atol=1e-12)


def test_oracle_run_reports_stability_and_aggregation_respects_it():
    run = bto.run_method(CFG, 7, "known_from_start", 0.032, 1, 4.0)
    assert run["stable"] is True
    assert run["failure"] is None

    bad = dict(run, seed=8, stable=False, failure="weight_norm")
    agg = bcl.aggregate_oracle_runs([run, bad], CFG, floor_db=-20.0)
    assert agg["primary_valid"] is False
    assert agg["failures"] == [8]
    assert "points_db" not in agg
    assert "stable_only_diagnostic" in agg

    ok = bcl.aggregate_oracle_runs([run, dict(run, seed=9)], CFG, floor_db=-20.0)
    assert ok["primary_valid"] is True
    assert "points_db" in ok


def test_oracle_summary_never_promotes_survivor_curve():
    run = bto.run_method(CFG, 7, "known_from_start", 0.032, 1, 4.0)
    bad = dict(run, seed=8, stable=False, failure="residual_ratio")
    out = bto._ensemble_summary([run, bad], CFG, floor_db=-20.0)["known_from_start"]
    assert out["primary_valid"] is False
    assert "ensemble_total_db" not in out
    assert "ensemble_total_db" in out["stable_only_diagnostic"]


def test_trial_budget_is_equal_for_all_conventional_methods():
    plan = bcl.benchmark_plan(60, 6, 10, 20, 0.5, 2.0, include_oracles=False)
    secs = {item.method: item.signal_seconds for item in plan}
    assert set(secs) == set(bcl.CONVENTIONAL_METHODS)
    assert len(set(secs.values())) == 1
    assert secs["vss2"] == 60 * 6 * 0.5 + bcl.VALIDATION_TOP_K * 10 * 0.5 + 20 * 2.0


def _cfg_with_delta():
    design = [ovr.make_seed_data(CFG, k, 0.5) for k in range(2)]
    return bcl.with_nlms_regularization(CFG, design)


def test_nlms_regularization_matches_fixed_binwise_relative_loading():
    from ffanc_norm.conventional_baselines import nlms_regularization
    xf = [np.full(100, 2.0), np.full(50, 2.0)]
    delta, floor = nlms_regularization(xf, 256, 1e-3)
    assert np.isclose(delta, 1e-3 * 256 * 4.0)
    assert np.isclose(floor, 1e-3 * 4.0)
    with pytest.raises(ValueError):
        nlms_regularization([np.zeros(10)], 256, 1e-3)


def test_heldout_seed_117_cold_start_is_bounded_with_delta():
    # Seed 117 has xf[3] = -1e-5: the unregularized denominator blew up the
    # first update for every sample-wise method in the 2026-10-17 run.
    cfg = _cfg_with_delta()
    data = ovr.make_seed_data(CFG, 117, 0.064)
    assert abs(data.xf[3]) < 1e-4
    params = {'beta': 0.3, 'gamma': 0.27}
    stable, _, _ = bcl.run_vss2(data, cfg, params, ad=False)
    assert stable
    unreg = dict(cfg, nlms_delta=0.0)
    stable0, _, _ = bcl.run_vss2(data, unreg, params, ad=False)
    assert not stable0
    sss = {'K': 2, 'mu_max': 0.21, 'ratio': 0.88, 'lambda': 0.64, 'rho': 0.31}
    assert bcl.run_sss(data, cfg, sss, ad=False)[0]


def test_fixed_binwise_uses_common_safety_limits():
    data = ovr.make_seed_data(CFG, 3, 0.064)
    stable, _ = bcl.run_fixed(data, CFG, 0.35)
    assert stable
    unstable, _ = bcl.run_fixed(data, CFG, 1e4)
    assert not unstable


def test_vss2_optimizer_uses_shared_kernel():
    data = ovr.make_seed_data(CFG, 5, 0.05)
    s = np.ascontiguousarray(synthetic_secondary_path(), dtype=np.float64)
    safety = VSS2SafetyLimits()
    r = ovr.run_vss2_seed(data, s, 0.36, 1.0, 256, 0.15, 128, safety, use_numba=False)
    stable, e, *_ = run_vss2_kernel(
        data.x, data.d, data.xf, data.v, s, 0.36, 1.0, 256, 0.15, 128,
        safety.max_residual_ratio_db, safety.max_weight_norm,
        safety.max_abs_error_factor * data.disturbance_rms, 0, 0.0,
    )
    assert r.stable == bool(stable)
    expected = 10.0 * np.log10((np.dot(e, e) + 1e-30) / (np.dot(data.uncontrolled, data.uncontrolled) + 1e-30))
    assert np.isclose(r.cumulative_total_residual_db, expected, rtol=1e-10)


def test_missing_numba_is_an_error_unless_fallback_is_explicit(monkeypatch):
    monkeypatch.setattr(runtime, "numba_available", lambda: False)
    with pytest.raises(RuntimeError, match="allow-python-fallback"):
        runtime.ensure_compiled_kernels(False, "test")
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        assert runtime.ensure_compiled_kernels(True, "test") is False
    assert any(issubclass(w.category, RuntimeWarning) for w in caught)


def test_runtime_estimate_arithmetic():
    est = runtime.estimate_total_seconds(
        {"a": 2.0, "b": 0.5},
        [runtime.RunCount("a", 10.0), runtime.RunCount("b", 4.0), runtime.RunCount("a", 1.0)],
    )
    assert est == {"a": 22.0, "b": 2.0, "total": 24.0}
    with pytest.raises(KeyError):
        runtime.estimate_total_seconds({}, [runtime.RunCount("x", 1.0)])
    assert runtime.format_duration(30) == "30.0 s"
    assert runtime.format_duration(600) == "10.0 min"


def test_validation_selection_flags_all_unstable_candidates():
    class T:
        def __init__(self, number, value, params):
            self.number, self.value, self.params = number, value, params

    data = ovr.make_seed_data(CFG, 21, 0.064)
    trials = [T(0, -5.0, {"mu": 1e4}), T(1, -4.0, {"mu": 2e4})]
    best, rows = bcl.select_by_validation("fixed_binwise", trials, [data], CFG, 0.064)
    assert best["validation_stable"] is False
    good, _ = bcl.select_by_validation("fixed_binwise", [T(2, -5.0, {"mu": 0.35})], [data], CFG, 0.064)
    assert good["validation_stable"] is True
    with pytest.raises(RuntimeError):
        bcl.select_by_validation("fixed_binwise", [], [data], CFG, 0.064)


def test_dct_floor_is_wired_into_runner():
    cfg = _cfg_with_delta()
    assert cfg['dct_normalization_floor'] > 0.0
    assert np.isclose(cfg['nlms_delta'], cfg['dct_normalization_floor'] * CFG['controller_length'])
