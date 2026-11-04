import numpy as np

from ffanc_norm.fd_fxnlms import FDFxNLMS
from ffanc_norm.simulation import run_ffanc


def test_past_controller_output_is_not_recomputed_after_updates():
    rng = np.random.default_rng(10)
    N, H, M = 64, 16, 32
    n_samples = 128

    x = rng.standard_normal(n_samples)
    p = np.array([0.0, 1.0])
    s = np.array([0.0, 0.5])

    alg = FDFxNLMS(
        fft_length=N,
        hop_length=H,
        controller_length=M,
        mu=0.02,
        smoothing=0.8,
        regularization_ratio=1e-3,
        mode="global",
    )

    result = run_ffanc(x, p, s, s.copy(), alg)

    # The first hop was generated with the initial zero controller and cannot
    # change when later coefficient updates occur.
    assert np.allclose(result.controller_output[:H], 0.0)
    assert not np.allclose(result.controller_history[-1], 0.0)


def test_transition_equivalent_error_replaces_only_legacy_secondary_response():
    from ffanc_norm.simulation import (
        causal_fir_block,
        transition_equivalent_error_block,
    )

    rng = np.random.default_rng(42)
    n = 96
    start, stop = 32, 48
    x = rng.standard_normal(n)
    s = np.array([0.5, -0.2, 0.1, 0.05])
    w_old = rng.standard_normal(8) * 0.1
    w_now = rng.standard_normal(8) * 0.1

    # Actual history was produced by w_old before the boundary and w_now after it.
    y = np.zeros(n)
    y[:start] = causal_fir_block(x, w_old, 0, start)
    y[start:stop] = causal_fir_block(x, w_now, start, stop)
    sec_actual = causal_fir_block(y, s, start, stop)
    d = rng.standard_normal(stop - start)
    e_physical = d + sec_actual

    e_virtual, correction = transition_equivalent_error_block(
        x=x,
        actual_controller_output=y,
        current_weights=w_now,
        secondary_path_model=s,
        physical_error_block=e_physical,
        start=start,
        stop=stop,
    )

    # Counterfactual reference: w_now had also generated the relevant legacy y.
    y_counterfactual = y.copy()
    hist_start = start - (len(s) - 1)
    y_counterfactual[hist_start:start] = causal_fir_block(x, w_now, hist_start, start)
    sec_counterfactual = causal_fir_block(y_counterfactual, s, start, stop)

    assert np.allclose(e_virtual, d + sec_counterfactual, atol=1e-12)
    assert np.allclose(correction, sec_counterfactual - sec_actual, atol=1e-12)
