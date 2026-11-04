import numpy as np

from ffanc_norm.theory import (
    misadjustment_metrics,
    secondary_noise_gradient_covariance,
    stationary_weight_error_covariance,
)


def test_secondary_noise_gradient_covariance_is_psd():
    N, H, M = 32, 8, 12
    r = 0.8 ** np.arange(N + 1)
    denom = np.ones(N // 2 + 1)
    Q = secondary_noise_gradient_covariance(r, N, H, M, denom, 0.1)
    assert np.allclose(Q, Q.T, atol=1e-12)
    assert np.min(np.linalg.eigvalsh(Q)) >= -1e-10


def test_scalar_lyapunov_matches_closed_form():
    K = np.array([[0.5]])
    mu = 0.2
    Q = np.array([[0.3]])
    A = 1.0 - mu * K[0, 0]
    expected = mu**2 * Q[0, 0] / (1.0 - A**2)
    C = stationary_weight_error_covariance(K, mu, Q)
    assert np.allclose(C[0, 0], expected)


def test_misadjustment_definition():
    R = np.eye(2)
    C = np.diag([0.01, 0.02])
    metrics = misadjustment_metrics(R, C, 0.0, 0.3)
    assert np.isclose(metrics["emse"], 0.03)
    assert np.isclose(metrics["misadjustment"], 0.1)
