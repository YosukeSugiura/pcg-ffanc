"""Numerical check 2 of [unpublished theory draft omitted] (Statement A, empirical gap), 2026-10-30. Analysis only.

Stationary cell S8, M = 512, tuning seeds 300-309, ar1 and harmonic. For each seed:
  - oracle floor: w_opt = LS controller on the whole 5 s run (non-causal); per-hop residual of w_opt = the
    irreducible part (uncontrollable residual + sensor noise);
  - excess(method, hop) = residual power(method) - residual power(w_opt), ensemble mean over seeds;
  - methods: exact growing-window LS (R-RLS lam = 1, the realizable optimum of Theorem 1 / Statement A), FD-FxNLMS
    (mu = 0.2 = the selected baseline, and 0.5), E-PCG (main configuration; window L = 48 hops).
Reported: excess ratios in dB (method / exact LS) over hop ranges, and the excess curves (results/gap_check2/).
usage: RLS_FAST=1 python experiments/gap_check2.py
"""
import json, sys
from pathlib import Path
import numpy as np
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src')); sys.path.insert(0, str(ROOT / 'experiments'))
import verify_protocol_defs as D  # noqa: E402
OUT = ROOT / 'results' / 'gap_check2'; OUT.mkdir(parents=True, exist_ok=True)
M = 512; SEEDS = list(range(300, 310)); TT = 5.0
MAIN = json.loads((ROOT / 'results/final_dev/final_config_core_main.json').read_text())['flags']
METHODS = {'exact LS (RLS lam 1)': ('R-RLS', {'lam': 1.0, 'delta': 1e-2}),
           'FD-FxNLMS mu 0.2': ('fixed_binwise', {'mu': 0.2}),
           'FD-FxNLMS mu 0.5': ('fixed_binwise', {'mu': 0.5}),
           'E-PCG (main)': ('E-PCG-F', MAIN)}
RANGES = [(1, 8), (8, 32), (32, 100), (100, 312)]          # hops


def cfg_of(nz):
    return dict(D.SCEN['S8 stationary'], controller_length=M, fft_length=2 * M, **({} if nz == 'ar1' else {'noise_type': nz}))


def floor_trace(nz, sd):
    D.P.RETURN_SIGNALS = True
    r = D.P.run(cfg_of(nz), sd, 'fixed_binwise', {'mu': 0.0}, TT, None)
    D.P.RETURN_SIGNALS = False
    xf = np.asarray(r['xf'], float); dh = np.asarray(r['dhat'], float); n = len(xf)
    nf = int(2 ** np.ceil(np.log2(2 * n)))
    X = np.fft.rfft(xf, nf); Dh = np.fft.rfft(dh, nf)
    ac = np.fft.irfft(np.abs(X) ** 2, nf)[:M]; cp = np.fft.irfft(np.conj(X) * Dh, nf)[:M]
    from scipy.linalg import solve_toeplitz
    w = solve_toeplitz(ac, -cp)                             # LS on the whole run (Toeplitz approx. of X^T X; n >> M)
    e = dh + np.fft.irfft(X * np.fft.rfft(w, nf), nf)[:n]
    H = int(cfg_of(nz)['hop_length'])
    return np.array([np.mean(e[b * H:(b + 1) * H] ** 2) for b in range(n // H)])


def main():
    out = ['# Gap check 2 (Statement A, empirical): excess over the oracle floor, S8, M = 512, tuning seeds 300-309', '',
           'excess = ensemble-mean residual power - ensemble-mean residual power of the whole-run LS controller (oracle floor);',
           'ratio = 10 log10(excess(method) / excess(exact growing-window LS)) over hop ranges (1 hop = 16 ms).', '']
    curves = {}
    for nz in ['ar1', 'harmonic']:
        fl = np.mean([floor_trace(nz, sd) for sd in SEEDS], 0)
        ex = {}
        for name, (meth, prm) in METHODS.items():
            tp = np.mean([np.asarray(D.P.run(cfg_of(nz), sd, meth, dict(prm), TT, None)['total_power'], float) for sd in SEEDS], 0)
            ex[name] = np.maximum(tp[:len(fl)] - fl[:len(tp)], 1e-12); curves[f'{nz}|{name}'] = ex[name]
            print(nz, name, 'done', flush=True)
        ref = ex['exact LS (RLS lam 1)']
        out += [f'## {nz}', '| method | ' + ' | '.join(f'hops {a}-{b}' for a, b in RANGES) + ' |', '|---' * (len(RANGES) + 1) + '|']
        for name in METHODS:
            out.append(f'| {name} | ' + ' | '.join(f'{10 * np.log10(ex[name][a:b].mean() / ref[a:b].mean()):+.2f} dB' for a, b in RANGES) + ' |')
        out += ['', f'oracle floor (mean NR of the whole-run LS controller relative to the uncontrolled power): see curves.npz', '']
    np.savez(OUT / 'curves.npz', **curves)
    (OUT / 'summary.md').write_text('\n'.join(out) + '\n'); print('\n'.join(out))


if __name__ == '__main__':
    main()
