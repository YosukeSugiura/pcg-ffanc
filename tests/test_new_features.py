"""Tests for the 2026-10 additions (review item D16): movement bound (Prop. 13), score on the unregularized LS
(score_unreg), band-wise weights (band='tree'), proximal per-bin leakage, ISM causality margin and trajectories,
and smoke tests of the added baselines."""
import json
import sys
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src')); sys.path.insert(0, str(ROOT / 'experiments'))
import prototype_new_algorithms as P  # noqa: E402
from ffanc_norm.epcg import EPCG, EPCGConfig  # noqa: E402

FS = 8000


def _direct_path(r, M=64, Ls=128, fs=FS, c0=343.0):
    """fractional-delay direct path with 1/r amplitude (sinc interpolation)."""
    n = np.arange(Ls); d = 40.0 + r / c0 * fs          # constant offset as in pyroomacoustics' fractional delay
    win = np.where(np.abs(n - 40.0 - 0.3 / c0 * fs) <= 30, 0.5 + 0.5 * np.cos(np.pi * (n - 40.0 - 0.3 / c0 * fs) / 30), 0.0)
    return np.sinc(n - d) * win / r


def test_movement_bound_zero_displacement_is_zero():
    s = _direct_path(0.3)
    eps = P.movement_bound(s, 64, FS, 0.0, 0.3)
    assert np.max(np.abs(eps)) < 1e-9


def test_movement_bound_covers_direct_path_displacements():
    M, rs, D = 64, 0.3, 0.08
    s = _direct_path(rs)
    eps = P.movement_bound(s, M, FS, D, rs)
    Sk = np.fft.rfft(s, 2 * M * 2)[::2][:M + 1]
    rng = np.random.default_rng(0)
    for _ in range(50):
        u = rng.uniform(-D, D)
        s2 = _direct_path(rs + u)
        S2 = np.fft.rfft(s2, 2 * M * 2)[::2][:M + 1]
        lhs = -np.real((S2 - Sk) / Sk)
        # bins where the windowed fractional-delay response is not negligible (near Nyquist |S_k| -> 0 and the
        # filtered-reference power, hence the ridge and the stability condition, is irrelevant)
        band = np.abs(Sk) > 0.1 * np.max(np.abs(Sk))
        assert np.all(lhs[band] <= eps[band] + 0.05), float(np.max((lhs - eps)[band]))


def test_movement_bound_monotone_in_D():
    s = _direct_path(0.3)
    e1 = P.movement_bound(s, 64, FS, 0.03, 0.3); e2 = P.movement_bound(s, 64, FS, 0.10, 0.3)
    assert np.all(e2 >= e1 - 1e-12)


def _stationary_data(M=32, H=16, hops=120, seed=0):
    rng = np.random.default_rng(seed)
    from scipy.signal import lfilter
    x = lfilter([1.0], [1.0, -0.9], rng.standard_normal(hops * H))
    w0 = rng.standard_normal(M) * np.exp(-np.arange(M) / 6.0)
    d = -np.convolve(x, w0)[:len(x)] + 0.1 * rng.standard_normal(len(x))
    return x, d


def test_score_unreg_removes_ridge_induced_false_alarms():
    M, H = 32, 16
    x, d = _stationary_data(M, H)
    eps = np.full(M + 1, 3.0)                      # very large robust ridge
    det = {}
    for su in (False, True):
        ep = EPCG(EPCGConfig(M=M, H=H, L_hops=32, J=4, reg_eps=eps, reg_gamma=0.9, score_unreg=su, screen_fa=0.0))
        for b in range(len(x) // H):
            ep.update(x[b * H:(b + 1) * H], d[b * H:(b + 1) * H])
        det[su] = len(ep.resets)
    assert det[True] == 0
    assert det[True] <= det[False]


def test_band_tree_identical_blocks_returns_old_estimate():
    M = 32
    ep = EPCG(EPCGConfig(M=M, H=16, band='tree'))
    rng = np.random.default_rng(1)
    wA = rng.standard_normal(M)
    ev = {'wA': wA.copy(), 'wB': wA.copy()}
    CB = np.full(M + 1, 100.0 + 0j)
    w = ep._band_solve(ev, CB, 1.0, 1000, 200)
    assert np.allclose(w, wA, atol=1e-10)


def test_band_tree_large_change_returns_new_estimate():
    M = 32
    ep = EPCG(EPCGConfig(M=M, H=16, band='tree'))
    rng = np.random.default_rng(2)
    wA = rng.standard_normal(M); wB = wA + 50.0 * rng.standard_normal(M)
    ev = {'wA': wA.copy(), 'wB': wB.copy()}
    CB = np.full(M + 1, 1000.0 + 0j)
    w = ep._band_solve(ev, CB, 1.0, 1000, 200)
    assert np.linalg.norm(w - wB) < 0.05 * np.linalg.norm(wB - wA)


@pytest.fixture(scope='module')
def cab():
    return dict(json.loads((ROOT / 'configs/ism_cabin.json').read_text()), ism_causal_ms=1.0)


def test_ism_causality_margin(cab):
    for tgt in ('source', 'mic'):
        for sd in (300, 301, 302):
            cfg = dict(cab, move_dx=0.3, move_target=tgt)
            p, s, p2, s2 = P.ism_paths(cfg, sd)
            sp = s if s2 is None else s2
            # direct-path peaks: primary at least 1 ms (8 samples) later than secondary, before and after the move
            assert np.argmax(np.abs(p)) - np.argmax(np.abs(s)) >= 7
            assert np.argmax(np.abs(p2)) - np.argmax(np.abs(sp)) >= 7


def test_ism_trajectory_endpoints_match_abrupt(cab):
    for tgt in ('source', 'mic'):
        a = P.ism_paths(dict(cab, move_dx=0.1, move_target=tgt), 303)
        t = P.ism_paths(dict(cab, move_dx=0.1, move_target=tgt, move_steps=8), 303)
        assert np.allclose(a[0], t[0]) and np.allclose(a[2], t[2][-1], atol=1e-10)
        if tgt == 'mic':
            assert np.allclose(a[3], t[3][-1], atol=1e-10)


@pytest.mark.parametrize('meth,prm', [
    ('leaky_binwise', {'mu': 0.648, 'leak': 1e-2}),
    ('convex_binwise', {'mu_fast': 0.9, 'mu_slow': 0.2, 'mu_a': 1.0}),
    ('osp_binwise', {'mu': 0.648, 'mu_s': 1e-3, 'u_std': 0.1}),
    ('spec_binwise', {'mu': 1.0, 'robust_dx': 0.2, 'bound': True, 'proximal': True}),
])
def test_added_baselines_run_and_converge(meth, prm):
    cfg = json.loads((ROOT / 'configs/random_decay.json').read_text())
    r = P.run(cfg, 100, meth, prm, 1.0, None)
    tp = np.array(r['total_power']); up = np.array(r['uncontrolled_power'])
    assert r['stable'] and len(tp) == len(up)
    assert 10 * np.log10(tp[-10:].sum() / up[-10:].sum()) < -3.0


def test_shat_shift_zero_is_identity_and_recovers_direct_path_shift():
    s = _direct_path(0.3)
    assert np.allclose(P.shat_shift(s, 0.0, 0.3, FS), s, atol=1e-10)
    s2 = P.shat_shift(s, 0.05, 0.3, FS)
    # peak moves by about u/c*fs samples (0.05 m -> 1.17 samples) and scales by rs/(rs+u)
    assert abs(np.argmax(np.abs(s2)) - np.argmax(np.abs(s)) - 1) <= 1
    assert np.max(np.abs(s2)) < np.max(np.abs(s))


def test_sid_profile_recovers_u_in_closed_loop():
    rng = np.random.default_rng(3)
    M, n, rs = 32, 6000, 0.3
    s = _direct_path(rs, Ls=96)
    s_true = P.shat_shift(s, 0.04, rs, FS)
    from scipy.signal import lfilter
    x = lfilter([1.0], [1.0, -0.8], rng.standard_normal(n))
    p = rng.standard_normal(160) * np.exp(-np.arange(160) / 20.0)
    # time-varying controller (identifiability): two alternating filters
    W = [rng.standard_normal(M) * 0.1, rng.standard_normal(M) * 0.1]
    y = np.zeros(n)
    for k in range(0, n, 500):
        y[k:k + 500] = np.convolve(x, W[(k // 500) % 2])[k:k + 500]
    e = np.convolve(x, p)[:n] + np.convolve(y, s_true)[:n] + 1e-3 * rng.standard_normal(n)
    grid = np.round(np.arange(-0.1, 0.1001, 0.01), 3)
    u = P.sid_profile(x, y, e, s, 2000, n, M, grid, rs, FS)
    assert abs(u - 0.04) <= 0.011
