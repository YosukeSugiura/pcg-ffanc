"""Generalized Schur Cholesky of the lag Gram matrix (sid_fastchol): exactness against numpy and against the QR path."""
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src')); sys.path.insert(0, str(ROOT / 'experiments'))


def test_gschur_equals_cholesky():
    import prototype_new_algorithms as P
    rng = np.random.default_rng(1)
    x = np.zeros(5000); v = rng.standard_normal(5000)
    for t in range(1, 5000):
        x[t] = 0.9 * x[t - 1] + v[t]                      # coloured input (cond ~ 1e3)
    for lo, hi, L in ((3000, 4000, 120), (10, 900, 60), (2000, 4000, 7)):
        idx = np.arange(lo, hi)[:, None] - np.arange(L)[None, :]
        X = np.where(idx >= 0, x[np.clip(idx, 0, None)], 0.0)
        Lc = np.linalg.cholesky(X.T @ X)
        assert np.max(np.abs(P.gschur_chol(x, lo, hi, L) - Lc)) <= 1e-10 * np.max(np.abs(Lc))


def _closed_loop(seed=0):
    import prototype_new_algorithms as P
    rng = np.random.default_rng(seed)
    fs, M, n = 8000, 32, 6000
    s = np.zeros(64); s[20] = 1.0; s[30:] = 0.1 * rng.standard_normal(34) * np.exp(-np.arange(34) / 8)
    s_true = P.shat_shift(s, 0.04, 0.3, fs)
    x = rng.standard_normal(n)
    w_opt = 0.3 * rng.standard_normal(M) * 0.8 ** np.arange(M)
    y = np.zeros(n)
    for i in range(0, n, 128):
        wi = w_opt * (1 - np.exp(-i / 1500)) + 0.2 * rng.standard_normal(M) * np.exp(-i / 1500)
        seg = np.concatenate([np.zeros(M - 1), x])[i:i + 128 + M - 1]
        y[i:i + 128] = np.convolve(seg, wi)[M - 1:M - 1 + len(y[i:i + 128])]
    d = -np.convolve(np.convolve(x, s_true)[:n], w_opt)[:n]
    e = d + np.convolve(y, s_true)[:n] + 0.01 * rng.standard_normal(n)
    return x, y, e, s, M, fs


def test_fastchol_same_statistics_as_qr():
    import prototype_new_algorithms as P
    x, y, e, s, M, fs = _closed_loop()
    grid = np.round(np.arange(-0.06, 0.06 + 1e-9, 0.005), 4)
    kw = dict(lrt=6.63, chow=6.63, edge=True, c2f=0.02, wchow=0.01, xreg=len(s) + M, sig='profile')
    u0, i0, n0 = P.sid_profile2(x, y, e, s, 1000, 5000, M, grid, 0.3, fs, **kw)
    u1, i1, n1 = P.sid_profile2(x, y, e, s, 1000, 5000, M, grid, 0.3, fs, fastchol=True, **kw)
    assert u0 == u1 and n0 == n1 and abs(u1 - 0.04) <= 0.0051
    for k in ('chow', 'lrt', 'wchow', 'sig_u_crb', 'sig_u_hac'):
        assert np.isclose(i0[k], i1[k], rtol=1e-6, atol=1e-12), k
    assert i0['ci_set'] == i1['ci_set']
