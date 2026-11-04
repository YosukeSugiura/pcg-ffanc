import numpy as np

from ffanc_norm.paths import synthetic_secondary_path
from ffanc_norm.theory import (
    expected_fd_update_matrix,
    expected_rfft_power,
    filtered_autocovariance,
    toeplitz_from_autocov,
)


def test_global_fd_update_matrix_matches_block_covariance_formula():
    N, H, M = 64, 16, 24
    s = synthetic_secondary_path()[:12]
    r = filtered_autocovariance(s, max_lag=N + M + 2, pole=0.8)
    P = expected_rfft_power(r, N)
    denom_value = 1.001 * float(np.mean(P))
    denom = np.full(N // 2 + 1, denom_value)

    K_fd = expected_fd_update_matrix(r, N, H, M, denom)
    R = toeplitz_from_autocov(r, M)
    K_direct = H * R / denom_value

    assert np.allclose(K_fd, K_direct, rtol=1e-11, atol=1e-12)


def test_binwise_normalization_reduces_eigenvalue_spread():
    N, H, M = 128, 32, 64
    s = synthetic_secondary_path()
    r = filtered_autocovariance(s, max_lag=N + M + 2, pole=0.95)
    P = expected_rfft_power(r, N)
    pbar = float(np.mean(P))
    eps = 1e-3

    Kg = expected_fd_update_matrix(
        r, N, H, M, np.full(N // 2 + 1, (1.0 + eps) * pbar)
    )
    Kb = expected_fd_update_matrix(r, N, H, M, P + eps * pbar)

    eg = np.linalg.eigvals(Kg).real
    eb = np.linalg.eigvals(Kb).real
    cond_g = np.max(eg) / np.min(eg)
    cond_b = np.max(eb) / np.min(eb)

    assert cond_b < cond_g
