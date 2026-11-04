"""Tests for the new (flag-guarded) memory bank and the sid v2 profile check."""
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src')); sys.path.insert(0, str(ROOT / 'experiments'))
from ffanc_norm.epcg import EPCG, EPCGConfig  # noqa: E402
from ffanc_norm.epcg_bank import EPCGBank  # noqa: E402


def _data(M=16, H=8, n_hops=60, seed=0):
    rng = np.random.default_rng(seed)
    w = rng.standard_normal(M) * 0.5 ** np.arange(M)
    xf = rng.standard_normal(n_hops * H)
    dh = -np.convolve(xf, w)[:len(xf)] + 0.05 * rng.standard_normal(len(xf))
    return xf, dh


def test_bank_with_one_member_equals_epcg():
    M, H = 16, 8
    xf, dh = _data(M, H)
    a = EPCG(EPCGConfig(M=M, H=H, L_hops=12, detect=False))
    b = EPCGBank(EPCGConfig(M=M, H=H, detect=False), L_list=(12,))
    for i in range(0, len(xf), H):
        wa = a.update(xf[i:i + H], dh[i:i + H]); wb = b.update(xf[i:i + H], dh[i:i + H])
        assert np.allclose(wa, wb)


def test_bank_weights_are_a_distribution_and_follow_drift():
    M, H = 8, 16
    rng = np.random.default_rng(3)
    n = 400 * H
    xf = rng.standard_normal(n)
    # continuously rotating optimum (drift): short memory must win
    t = np.arange(n) / n
    w0 = rng.standard_normal(M); w1 = rng.standard_normal(M)
    dh = np.zeros(n)
    for i in range(0, n, H):
        c = np.cos(6 * np.pi * t[i]); s_ = np.sin(6 * np.pi * t[i])
        wt = c * w0 + s_ * w1
        seg = np.concatenate([np.zeros(M - 1), xf])[i:i + H + M - 1]
        dh[i:i + H] = -np.convolve(seg, wt)[M - 1:M - 1 + H]
    dh += 0.01 * rng.standard_normal(n)
    b = EPCGBank(EPCGConfig(M=M, H=H, detect=False), L_list=(4, 64))
    for i in range(0, n, H):
        b.update(xf[i:i + H], dh[i:i + H])
    P = np.array(b.pi_hist)
    assert np.allclose(P.sum(1), 1.0)
    assert P[100:, 0].mean() > 0.7          # the short memory dominates under drift


def test_sid_profile2_recovers_distance_and_rejects_edge():
    import prototype_new_algorithms as P
    rng = np.random.default_rng(0)
    fs, M, n = 8000, 32, 6000
    s = np.zeros(64); s[20] = 1.0; s[30:] = 0.1 * rng.standard_normal(34) * np.exp(-np.arange(34) / 8)
    u_true = 0.04
    s_true = P.shat_shift(s, u_true, 0.3, fs)
    x = rng.standard_normal(n)
    w_opt = 0.3 * rng.standard_normal(M) * 0.8 ** np.arange(M)
    # time-varying controller (re-adaptation): y is not an LTI filter of x
    y = np.zeros(n)
    for i in range(0, n, 128):
        wi = w_opt * (1 - np.exp(-i / 1500)) + 0.2 * rng.standard_normal(M) * np.exp(-i / 1500)
        seg = np.concatenate([np.zeros(M - 1), x])[i:i + 128 + M - 1]
        y[i:i + 128] = np.convolve(seg, wi)[M - 1:M - 1 + len(y[i:i + 128])]
    d = -np.convolve(np.convolve(x, s_true)[:n], w_opt)[:n]
    e = d + np.convolve(y, s_true)[:n] + 0.01 * rng.standard_normal(n)
    grid = np.round(np.arange(-0.06, 0.06 + 1e-9, 0.005), 4)
    u, info, nev = P.sid_profile2(x, y, e, s, 1000, 5000, M, grid, 0.3, fs, lrt=6.63, chow=6.63, edge=True)
    assert u is not None and abs(u - u_true) <= 0.0051
    u2, _, nev2 = P.sid_profile2(x, y, e, s, 1000, 5000, M, grid, 0.3, fs, c2f=0.02)
    assert abs(u2 - u_true) <= 0.0051 and nev2 < nev
    # true change outside the search range -> boundary -> rejected
    small = np.round(np.arange(-0.02, 0.02 + 1e-9, 0.005), 4)
    u3, info3, _ = P.sid_profile2(x, y, e, s, 1000, 5000, M, small, 0.3, fs, edge=True)
    assert u3 is None and info3['edge']


def test_cheap_bank_shared_statistics_are_exact():
    import dataclasses
    M, H = 16, 8
    xf, dh = _data(M, H, n_hops=80)
    base = EPCGConfig(M=M, H=H, k_hops=8)
    b = EPCGBank(base, L_list=(4, 16), cheap=True)
    ref = EPCG(dataclasses.replace(base, L_hops=4, detect=False, k_hops=2))
    for i in range(0, len(xf), H):
        b.update(xf[i:i + H], dh[i:i + H]); wr = ref.update(xf[i:i + H], dh[i:i + H])
        assert np.allclose(b.ws[0], wr, atol=1e-10)
    assert b.members[0].fft.flops() < ref.fft.flops()     # statistics not recomputed by the secondary member


def test_sid_profile2_xreg_recovers_distance():
    import prototype_new_algorithms as P
    rng = np.random.default_rng(0)
    fs, M, n = 8000, 32, 6000
    s = np.zeros(64); s[20] = 1.0; s[30:] = 0.1 * rng.standard_normal(34) * np.exp(-np.arange(34) / 8)
    u_true = 0.04
    s_true = P.shat_shift(s, u_true, 0.3, fs)
    x = rng.standard_normal(n)
    w_opt = 0.3 * rng.standard_normal(M) * 0.8 ** np.arange(M)
    y = np.zeros(n)
    for i in range(0, n, 128):
        wi = w_opt * (1 - np.exp(-i / 1500)) + 0.2 * rng.standard_normal(M) * np.exp(-i / 1500)
        seg = np.concatenate([np.zeros(M - 1), x])[i:i + 128 + M - 1]
        y[i:i + 128] = np.convolve(seg, wi)[M - 1:M - 1 + len(y[i:i + 128])]
    d = -np.convolve(np.convolve(x, s_true)[:n], w_opt)[:n]
    e = d + np.convolve(y, s_true)[:n] + 0.01 * rng.standard_normal(n)
    grid = np.round(np.arange(-0.06, 0.06 + 1e-9, 0.005), 4)
    u, info, _ = P.sid_profile2(x, y, e, s, 1000, 5000, M, grid, 0.3, fs, lrt=6.63, xreg=len(s) + M)
    assert u is not None and abs(u - u_true) <= 0.0051 and info['sig_u'] is not None


def test_sharescore_is_exact():
    M, H = 32, 16
    rng = np.random.default_rng(1)
    w0 = rng.standard_normal(M) * 0.7 ** np.arange(M)
    xf = rng.standard_normal(200 * H)
    dh = -np.convolve(xf, w0)[:len(xf)] + 0.1 * rng.standard_normal(len(xf))
    dh[100 * H:] = -np.convolve(xf, -w0)[100 * H:len(xf)] + 0.1 * rng.standard_normal(100 * H)
    a = EPCGBank(EPCGConfig(M=M, H=H), (4, 16), cheap=['share', 'nodetect', 'fftmin'])
    b = EPCGBank(EPCGConfig(M=M, H=H), (4, 16), cheap=['share', 'nodetect', 'fftmin', 'sharescore'])
    for i in range(0, len(xf), H):
        assert np.allclose(a.update(xf[i:i + H], dh[i:i + H]), b.update(xf[i:i + H], dh[i:i + H]), atol=1e-12)
    assert b.fft.flops() < a.fft.flops()


def test_doze_saves_cost_in_stationary_and_wakes_under_drift():
    rng = np.random.default_rng(2); M, H = 32, 16
    w0 = rng.standard_normal(M) * 0.7 ** np.arange(M); w1 = rng.standard_normal(M) * 0.7 ** np.arange(M)
    n = 400 * H; xf = rng.standard_normal(n); dh = np.zeros(n); wts = []
    for i in range(0, n, H):
        a = np.clip((i - 250 * H) / (100 * H), 0, 1); wt = (1 - a) * w0 + a * w1; wts.append(wt)
        seg = np.concatenate([np.zeros(M - 1), xf])[i:i + H + M - 1]; dh[i:i + H] = -np.convolve(seg, wt)[M - 1:M - 1 + H]
    dh += 0.05 * rng.standard_normal(n)
    cfg = EPCGConfig(M=M, H=H, screen_fa=0.01)
    res = {}
    for name, opts in (('ref', ['share', 'nodetect', 'fftmin', 'sharescore']),
                       ('doze', ['share', 'nodetect', 'fftmin', 'sharescore', 'doze'])):
        b = EPCGBank(cfg, (4, 32), cheap=opts); err = []
        for k, i in enumerate(range(0, n, H)):
            err.append(np.sum((b.update(xf[i:i + H], dh[i:i + H]) - wts[k]) ** 2))
        res[name] = (b.fft.flops(), np.mean(err[260:350]), b)
    dz = np.array([d[2] for d in res['doze'][2].doze_hist])
    assert res['doze'][0] < 0.7 * res['ref'][0]
    assert res['doze'][1] < 1.1 * res['ref'][1]            # drift tracking unchanged
    assert dz[100:250].mean() > 0.8 and dz[260:350].mean() < 0.1
