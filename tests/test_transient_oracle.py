import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'experiments'))

from per_bin_oracle_cap_sweep import future_controller_to_secondary_matrix
from ffanc_norm.simulation import causal_fir_block


def test_future_controller_matrix_preserves_legacy_secondary_state():
    rng = np.random.default_rng(123)
    n = 500
    M = 24
    start = 100
    stop = 260
    x = rng.standard_normal(n)
    s = rng.standard_normal(17) * 0.1
    w_old = rng.standard_normal(M)
    w_new = rng.standard_normal(M)

    # Generate immutable controller output before the switch.
    y = np.zeros(n)
    y[:start] = causal_fir_block(x, w_old, 0, start)

    # Exact switched future.
    y_exact = y.copy()
    y_exact[start:stop] = causal_fir_block(x, w_new, start, stop)
    sec_exact = causal_fir_block(y_exact, s, start, stop)

    # Legacy + linear map of the new coefficient vector.
    legacy = causal_fir_block(y, s, start, stop)
    R = future_controller_to_secondary_matrix(x, s, start, stop, M)
    sec_pred = legacy + R @ w_new

    assert np.allclose(sec_pred, sec_exact, rtol=1e-11, atol=1e-11)
