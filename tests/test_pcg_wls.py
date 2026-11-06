import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from ffanc_norm.pcg_wls import PcgWls, PcgWlsConfig  # noqa: E402


def conv_matrix(xf, t0, stop, M):
    t = np.arange(t0, stop)[:, None] - np.arange(M)[None, :]
    return np.where(t >= 0, xf[np.clip(t, 0, None)], 0.0)


def _fed(M=16, H=8, n_hops=40, seed=0, **kw):
    rng = np.random.default_rng(seed)
    ep = PcgWls(PcgWlsConfig(M=M, H=H, **kw))
    xf = rng.standard_normal(n_hops * H); dh = rng.standard_normal(n_hops * H)
    return ep, xf, dh


def test_operator_exact_for_all_windows():
    M = 16
    ep, xf, _ = _fed(M=M)
    ep.xf = xf
    rng = np.random.default_rng(1)
    for a, b in [(0, 40), (0, 10), (5, 60), (30, 100), (100, 200), (150, 160), (3, 9)]:
        X = conv_matrix(xf, a, b, M)
        ep.stop = b; ep._ecache = {}
        r = np.array([sum(xf[n] * (xf[n - l] if n - l >= 0 else 0.0) for n in range(a, b)) for l in range(M)])
        Cf = ep._circ(r)
        u = rng.standard_normal(M)
        Gu = np.fft.irfft(ep._apply(Cf, a, np.fft.rfft(u, 2 * M)), 2 * M)[:M]
        assert np.allclose(Gu, X.T @ X @ u, atol=1e-10)


def test_incremental_statistics_match_direct():
    M, H, L = 16, 8, 5
    ep, xf, dh = _fed(M=M, H=H, L_hops=L, detect=False, k=2, k_first=2, k_steady=2)
    for b in range(40):
        ep.update(xf[b * H:(b + 1) * H], dh[b * H:(b + 1) * H])
        stop = (b + 1) * H; t0 = max(0, stop - L * H)
        X = conv_matrix(xf, t0, stop, M)
        assert ep.t0 == t0
        assert np.allclose(ep.p, X.T @ dh[t0:stop], atol=1e-9)
        assert np.allclose(ep.r, [sum(xf[n] * (xf[n - l] if n >= l else 0.0) for n in range(t0, stop)) for l in range(M)], atol=1e-9)
        assert np.isclose(ep.e0, dh[t0:stop] @ dh[t0:stop])
        assert len(ep.seg) <= L + 1


def test_converged_pcg_equals_ridge_ls():
    M, H, L = 16, 8, 6
    ep, xf, dh = _fed(M=M, H=H, L_hops=L, detect=False, k=60, k_first=60, k_steady=60)
    for b in range(20):
        w = ep.update(xf[b * H:(b + 1) * H], dh[b * H:(b + 1) * H])
    stop = 20 * H; t0 = stop - L * H
    X = conv_matrix(xf, t0, stop, M); G = X.T @ X
    w_ls = -np.linalg.solve(G + 1e-3 * ep.r[0] * np.eye(M), X.T @ dh[t0:stop])
    assert np.allclose(w, w_ls, atol=1e-8)


def test_truncated_pcg_score_is_conservative():
    """q_K = g^T z_K from PCG started at 0 is nondecreasing in K and <= g^T A^{-1} g."""
    M, H = 32, 16
    rng = np.random.default_rng(3)
    xf = np.zeros(400); e = rng.standard_normal(400)
    for n in range(400):
        xf[n] = 0.95 * (xf[n - 1] if n else 0.0) + e[n]
    ep = PcgWls(PcgWlsConfig(M=M, H=H)); ep.xf = xf; ep.stop = 400; ep._ecache = {}
    t0 = 400 - 4 * H
    X = conv_matrix(xf, t0, 400, M); G = X.T @ X
    r = np.array([sum(xf[n] * xf[n - l] for n in range(t0, 400)) for l in range(M)])
    rho = 1e-3 * r[0]
    g = rng.standard_normal(M)
    q = g @ np.linalg.solve(G + rho * np.eye(M), g)
    prev = 0.0
    for K in range(0, 40):
        qK = g @ ep._pcg(ep._circ(r), t0, rho, g, np.zeros(M), K)
        assert qK <= q * (1 + 1e-6)
        assert qK >= prev - 1e-6 * q
        prev = qK
    assert np.isclose(prev, q, rtol=1e-6)


def test_restart_resets_both_windows():
    M, H = 16, 8
    ep, xf, dh = _fed(M=M, H=H, n_hops=30, J=2, threshold=0.0, localize=False, screen_fa=0.0, det_stat='score', adapt='restart')  # threshold 0: reset whenever tested
    for b in range(30):
        ep.update(xf[b * H:(b + 1) * H], dh[b * H:(b + 1) * H])
    assert ep.resets
    stop = 30 * H
    X = conv_matrix(xf, ep.t0, stop, M)
    assert np.allclose(ep.p, X.T @ dh[ep.t0:stop], atol=1e-9)
    XJ = conv_matrix(xf, ep.tJ, stop, M)
    assert np.allclose(ep.pJ, XJ.T @ dh[ep.tJ:stop], atol=1e-9)


def test_screen_residual_is_one_step_residual():
    M, H = 16, 8
    ep, xf, dh = _fed(M=M, H=H, n_hops=20, screen_fa=0.5, J=2, threshold=1e12, det_fa=0.0)
    for b in range(20):
        w_prev = ep.w.copy()
        ep.update(xf[b * H:(b + 1) * H], dh[b * H:(b + 1) * H])
        X = conv_matrix(xf, b * H, (b + 1) * H, M)
        en = float(np.sum((dh[b * H:(b + 1) * H] + X @ w_prev) ** 2)) / H
        assert np.isclose(ep.pe[-1][1], en)


def test_sandwich_pcg_matches_dense_and_is_conservative():
    M, H = 16, 8
    rng = np.random.default_rng(5)
    ep = PcgWls(PcgWlsConfig(M=M, H=H)); ep.xf = rng.standard_normal(300); ep.dh = rng.standard_normal(300)
    ep.t0, ep.tJ, ep.stop = 100, 268, 300
    gam = ep._residual_autocov(H)
    g = rng.standard_normal(M)
    q = ep._sandwich_dense(g, gam)
    CJ = ep._circ(np.array([sum(ep.xf[n] * ep.xf[n - l] for n in range(268, 300)) for l in range(M)]))
    prev = 0.0
    for K in (1, 2, 4, 8, 60):
        qK = ep._sandwich_q(g, gam, CJ, K)
        assert qK <= q * (1 + 1e-6) and qK >= prev - 1e-9
        prev = qK
    assert np.isclose(prev, q, rtol=1e-5)


def test_branch_rollback_on_noise_step_keeps_controller():
    """A forced detection on stationary data must roll back (no-restart branch predicts better)."""
    M, H = 16, 8
    rng = np.random.default_rng(7)
    n = 80 * H
    xf = rng.standard_normal(n); w_true = rng.standard_normal(M) * 0.5
    dh = -np.convolve(xf, w_true)[:n] + 0.05 * rng.standard_normal(n)
    ep = PcgWls(PcgWlsConfig(M=M, H=H, J=2, det_stat='score', det_fa=0.0, threshold=1e12, screen_fa=0.0,
                         localize=False, branch_hops=6, adapt='restart'))
    for b in range(80):
        if b == 40:
            ep.thr = 0.0                    # force one detection (false alarm)
        if b == 41:
            ep.thr = 1e12
        ep.update(xf[b * H:(b + 1) * H], dh[b * H:(b + 1) * H])
    assert ep.resets and ep.rollbacks
    assert ep.restart == 0                      # back on the original window
    assert np.linalg.norm(ep.w - w_true) < 0.05 * np.linalg.norm(w_true)


def test_weighted_operator_matches_dense():
    """alpha G_A + G_B with A = [t0, tau), B = [tau, stop) via circulants + three edge terms."""
    M = 16
    rng = np.random.default_rng(11)
    ep = PcgWls(PcgWlsConfig(M=M, H=8)); ep.xf = rng.standard_normal(300); ep.stop = 280; ep._ecache = {}
    t0, tau, stop, alpha = 60, 190, 280, 0.37
    corr = lambda a, b: np.array([sum(ep.xf[n] * (ep.xf[n - l] if n >= l else 0.0) for n in range(a, b)) for l in range(M)])
    r_main, r_B = corr(t0, stop), corr(tau, stop)
    Cw = alpha * ep._circ(r_main) + (1 - alpha) * ep._circ(r_B)
    u = rng.standard_normal(M)
    Gu = np.fft.irfft(ep._apply(Cw, [(alpha, t0), (1 - alpha, tau)], np.fft.rfft(u, 2 * M)), 2 * M)[:M]
    XA, XB = conv_matrix(ep.xf, t0, tau, M), conv_matrix(ep.xf, tau, stop, M)
    assert np.allclose(Gu, (alpha * XA.T @ XA + XB.T @ XB) @ u, atol=1e-9)
