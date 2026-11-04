"""Numerical check 3 of [unpublished theory draft omitted] (windowed limit), 2026-10-30. Analysis only.

Question: does E-PCG (main, window L = 48 hops) reach the realizable limit of ITS OWN window, i.e. the excess of exact
LS on the same sliding window?  Same cell / seeds / floor as gap_check2 (S8, M = 512, tuning seeds 300-309).

Offline references (hop-wise, a priori: the controller applied on hop b is computed from the data before hop b;
virtual residual e = d_hat + X w, ridge delta = 1e-2 as in RLS):
  - 'offline growing LS'  : all data [0, bH)            (validates the offline evaluation against simulated RLS lam 1)
  - 'offline window LS'   : data [max(0, (b-L)H), bH)   (the windowed limit of E-PCG)
  - 'predicted window'    : sigma^2 tr(R G_win^-1), sigma^2 = oracle floor power, R = whole-run sample covariance.
Simulated curves (exact LS = RLS lam 1, E-PCG main) are read from results/gap_check2/curves.npz (same floor definition).
Pre-stated reading (before running): E-PCG reaches its windowed limit if its excess is within +-1 dB of
'offline window LS' over hops 48-312 (window full); hops < 48 are reported but E-PCG's growing controller length
(grow_len) makes it a different, biased estimator there.
usage: python experiments/gap_check3.py
"""
import sys
from pathlib import Path
import numpy as np
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'experiments'))
import gap_check2 as G2  # noqa: E402
D = G2.D
OUT = ROOT / 'results' / 'gap_check3'; OUT.mkdir(parents=True, exist_ok=True)
M = G2.M; SEEDS = G2.SEEDS; TT = G2.TT; L = 48; DELTA = 1e-2
RANGES = [(1, 8), (8, 48), (48, 100), (100, 200), (200, 312)]


def signals(nz, sd):
    D.P.RETURN_SIGNALS = True
    r = D.P.run(G2.cfg_of(nz), sd, 'fixed_binwise', {'mu': 0.0}, TT, None)
    D.P.RETURN_SIGNALS = False
    return np.asarray(r['xf'], float), np.asarray(r['dhat'], float), int(G2.cfg_of(nz)['hop_length'])


def offline(nz, sd):
    xf, dh, H = signals(nz, sd); n = len(xf); nb = n // H
    Xfull = np.lib.stride_tricks.sliding_window_view(np.concatenate([np.zeros(M - 1), xf]), M)[:, ::-1]  # row k = x_f[k..k-M+1]
    R = Xfull.T @ Xfull / n
    blk = lambda b: (Xfull[b * H:(b + 1) * H], dh[b * H:(b + 1) * H])
    Gg = np.zeros((M, M)); pg = np.zeros(M); Gw = np.zeros((M, M)); pw = np.zeros(M)
    res_g, res_w, tr_w = np.zeros(nb), np.zeros(nb), np.zeros(nb)
    for b in range(nb):
        Xb, db = blk(b)
        wg = np.linalg.solve(Gg + DELTA * np.eye(M), -pg); ww = np.linalg.solve(Gw + DELTA * np.eye(M), -pw)
        res_g[b] = np.mean((db + Xb @ wg) ** 2); res_w[b] = np.mean((db + Xb @ ww) ** 2)
        tr_w[b] = np.trace(np.linalg.solve(Gw + DELTA * np.eye(M), R)) if b > 0 else np.nan
        Gg += Xb.T @ Xb; pg += Xb.T @ db; Gw += Xb.T @ Xb; pw += Xb.T @ db
        if b - L + 1 >= 0:                                    # drop the hop leaving the window [b-L+1, b]
            Xo, do = blk(b - L + 1); Gw -= Xo.T @ Xo; pw -= Xo.T @ do
    return res_g, res_w, tr_w


def main():
    sim = np.load(ROOT / 'results/gap_check2/curves.npz')
    out = ['# Gap check 3: E-PCG vs exact LS on the same 48-hop window (S8, M = 512, tuning seeds 300-309)', '',
           'excess over the oracle floor (gap_check2 definition); ratios in dB relative to offline window LS', '']
    curves = {}
    for nz in ['ar1', 'harmonic']:
        fl = np.mean([G2.floor_trace(nz, sd) for sd in SEEDS], 0)
        rr = [offline(nz, sd) for sd in SEEDS]; print(nz, 'offline done', flush=True)
        nb = min(len(fl), *(len(r[0]) for r in rr))
        g = np.maximum(np.mean([r[0][:nb] for r in rr], 0) - fl[:nb], 1e-12)
        w = np.maximum(np.mean([r[1][:nb] for r in rr], 0) - fl[:nb], 1e-12)
        pred = np.nanmean([r[2][:nb] for r in rr], 0) * fl[:nb]
        ex = {'offline growing LS': g, 'offline window LS': w, 'predicted window (sigma^2 tr R G_win^-1)': pred,
              'sim exact LS (RLS lam 1)': sim[f'{nz}|exact LS (RLS lam 1)'][:nb], 'sim E-PCG (main)': sim[f'{nz}|E-PCG (main)'][:nb]}
        for k, v in ex.items():
            curves[f'{nz}|{k}'] = v
        out += [f'## {nz}', '| curve | ' + ' | '.join(f'hops {a}-{b}' for a, b in RANGES) + ' |', '|---' * (len(RANGES) + 1) + '|']
        for k, v in ex.items():
            out.append(f'| {k} | ' + ' | '.join(f'{10 * np.log10(np.nanmean(v[a:b]) / w[a:b].mean()):+.2f} dB' for a, b in RANGES) + ' |')
        out.append('')
    np.savez(OUT / 'curves.npz', **curves)
    (OUT / 'summary.md').write_text('\n'.join(out) + '\n'); print('\n'.join(out))


if __name__ == '__main__':
    main()
