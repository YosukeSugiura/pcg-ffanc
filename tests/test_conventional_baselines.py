import numpy as np
from ffanc_norm.conventional_baselines import run_sss_kernel


def test_sss_kernel_runs_and_selects_candidate():
    n = 512
    x = np.random.default_rng(0).standard_normal(n)
    s = np.array([0.0, 0.5])
    p = np.array([0.0, 0.8])
    d = np.convolve(x, p, mode='full')[:n]
    xf = np.convolve(x, s, mode='full')[:n]
    v = np.zeros(n)
    mus = np.array([0.4, 0.2, 0.1])
    stable, e, mu_hist, *_ = run_sss_kernel(
        x, d, xf, v, s, mus, 0.8, 1.0, 16, 1e-3, 64,
        60.0, 1e4, 1e6, 0, 0.0
    )
    assert stable
    assert np.all(np.isfinite(e))
    assert set(np.unique(mu_hist)).issubset(set(mus))


def test_ad_sss_kernel_runs():
    n = 512
    x = np.random.default_rng(1).standard_normal(n)
    s = np.array([0.0, 0.5])
    p = np.array([0.0, 0.8])
    d = np.convolve(x, p, mode='full')[:n]
    xf = np.convolve(x, s, mode='full')[:n]
    v = np.zeros(n)
    mus = np.array([0.4, 0.2, 0.1])
    stable, e, *_ = run_sss_kernel(
        x, d, xf, v, s, mus, 0.8, 1.0, 16, 1e-3, 64,
        60.0, 1e4, 1e6, 4, 1e-3
    )
    assert stable
    assert np.all(np.isfinite(e))
