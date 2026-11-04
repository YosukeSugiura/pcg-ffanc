import numpy as np

from ffanc_norm.fd_fxnlms import direct_block_gradient, fd_block_gradient


def test_fd_gradient_matches_direct_time_domain_gradient_without_normalization():
    rng = np.random.default_rng(1234)
    N, H, M = 512, 128, 256

    xf = rng.standard_normal(N)
    err = rng.standard_normal(H)
    denom = np.ones(N // 2 + 1)

    g_fd = fd_block_gradient(xf, err, denom, M)
    g_direct = direct_block_gradient(xf, err, M)

    assert np.allclose(g_fd, g_direct, rtol=1e-11, atol=1e-10)


def test_minus_gradient_reduces_local_block_squared_error():
    rng = np.random.default_rng(7)
    N, H, M = 512, 128, 64

    xf = rng.standard_normal(N)
    err = rng.standard_normal(H)

    # Block regression matrix X with X[h, m] = x_f[n_h - m].
    first_error_index = N - H
    X = np.empty((H, M))
    for m in range(M):
        X[:, m] = xf[first_error_index - m : N - m]

    g = X.T @ err
    eps = 1e-7

    j0 = 0.5 * np.dot(err, err)
    j_minus = 0.5 * np.dot(err - eps * (X @ g), err - eps * (X @ g))
    j_plus = 0.5 * np.dot(err + eps * (X @ g), err + eps * (X @ g))

    assert j_minus < j0
    assert j_plus > j0
