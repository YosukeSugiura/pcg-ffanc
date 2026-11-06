"""Diagnostic (2026-10-20): J(u) profiles of the closed-loop check for several nuisance regressor sets (x lags,
controller-based), on the checks of one run (captured from sid_profile2). usage: python experiments/diag_sid_nuisance.py 'S4 mic 10cm' 301"""
import json, os, sys, pickle
from pathlib import Path
import numpy as np
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src')); sys.path.insert(0, str(ROOT / 'experiments'))
import verify_protocol_defs as D
sel = json.loads((ROOT / 'results/protocol/selected_design.json').read_text())
L = D.GRID['E-PCG v2 light'][1][sel['E-PCG v2 light']]
_v3 = json.loads((ROOT / 'results/final_dev/final_config_v3.json').read_text())['flags']
PRM = dict(L, **dict(_v3, sid_xreg='ctrl'))
P = D.P
cap = []
_orig = P.sid_profile2
def spy(*a, **k):
    out = _orig(*a, **k)
    cap.append((a, k, out))
    return out
P.sid_profile2 = spy
scen, seed = sys.argv[1], int(sys.argv[2])
cfg = dict(D.SCEN[scen])
r = P.run(cfg, seed, 'PCG-WLS-F', PRM, D.T, D.CH)
x, y, e, sh, a, b, M, grid = cap[0][0][:8]
rs, fs = cap[0][0][8], cap[0][0][9]
yr = cap[0][1]['yreg']
print('u_true', r['geom']['u_true'], 'checks', [(c[0][4], c[0][5]) for c in cap])
def curve(Zfun, a, b, us):
    h = a + (b - a) // 2; out = []
    Qs = [np.linalg.qr(Zfun(lo, hi))[0] for lo, hi in ((a, h), (h, b))]
    for u in us:
        su = P.shat_shift(sh, u, rs, fs); dh = e[:b] - np.convolve(y[:b], su)[:b]
        J = []
        for Q, (lo, hi) in zip(Qs, ((a, h), (h, b))):
            r_ = dh[lo:hi] - Q @ (Q.T @ dh[lo:hi]); J.append(r_ @ r_)
        out.append(J)
    return np.array(out)
def xl(L):
    def f(lo, hi):
        idx = np.arange(lo, hi)[:, None] - np.arange(L)[None, :]
        return np.where(idx >= 0, x[np.clip(idx, 0, None)], 0.0)
    return f
us = np.round(np.arange(-0.12, 0.1201, 0.01), 3)
for ci in range(min(3, len(cap))):
    a, b = cap[ci][0][4], cap[ci][0][5]; yr = cap[ci][1]['yreg']; yr.hs = False
    print('check', ci, a, b)
    def comb(Lx, yr=yr):
        return lambda lo, hi: np.hstack([yr(lo, hi), xl(Lx)(lo, hi)])
    def zonly(lo, hi, yr=yr):
        return yr(lo, hi)[:, :1]
    for nm, Zf in (('xlag318', xl(P._sid_lg('direct', sh, M, 0.1, fs))), ('xlag256', xl(256)), ('xlag128', xl(128)),
                   ('z only', zonly), ('ctrlc', yr), ('ctrlc+x32', comb(32)), ('ctrlc+x64', comb(64)), ('ctrlc+x128', comb(128))):
        Jc = curve(Zf, a, b, us); t = Jc.sum(1)
        print(f'  {nm:8s} argmin tot {us[np.argmin(t)]:+.2f} h1 {us[np.argmin(Jc[:,0])]:+.2f} h2 {us[np.argmin(Jc[:,1])]:+.2f} '
              f'Jmin/n {t.min()/(b-a):.3e} depth (J(0)-Jmin)/Jmin {(t[us==0][0]-t.min())/t.min():.4f}')
