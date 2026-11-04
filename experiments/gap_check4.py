"""Revision 10 (docs/current/REVISION_RULE_10.md): numerical check of Prop. rho with the pure 1/b schedule. Analysis only.

Same construction as gap_check2.py (S8, M = 512, tuning seeds 300-309, ar1 and harmonic; excess over the oracle floor
of the whole-run LS controller, ratio to exact growing-window LS over hop ranges) with the pure circulant-RLS step
schedule V-SCHED {denom: cum, scale: 1, mu_min: 0} added, plus the log-log slope of the excess over hops 100-312.
usage: RLS_FAST=1 OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 python experiments/gap_check4.py
"""
import hashlib, json, os, platform, subprocess, sys
from importlib.metadata import version
from pathlib import Path
import numpy as np
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'experiments'))
import gap_check2 as G2  # noqa: E402  (cfg_of, floor_trace, MAIN, constants)

RULE = ROOT / 'docs/current/REVISION_RULE_10.md'
OUT = ROOT / 'results' / 'gap_check4'
SEEDS = G2.SEEDS; TT = G2.TT
METHODS = {'exact LS (RLS lam 1)': ('R-RLS', {'lam': 1.0, 'delta': 1e-2}),
           'pure 1/b schedule (V-SCHED)': ('V-SCHED', {'denom': 'cum', 'scale': 1.0, 'mu_min': 0.0, 'avg': False}),
           'FD-FxNLMS mu 0.2': ('fixed_binwise', {'mu': 0.2}),
           'E-PCG (main)': ('E-PCG-F', G2.MAIN)}
RANGES = [(1, 8), (8, 32), (32, 100), (100, 312)]
SLOPE = (100, 312)


def predicted():
    rows = [l.split('|') for l in (ROOT / 'results/gap_check/summary.md').read_text().splitlines() if l.startswith('| ar1 |')]
    return float(np.median([float(r[9]) for r in rows]))       # rho_c (dB), median over the 10 seeds


def slope(ex):
    a, b = SLOPE; h = np.arange(a, b)
    return float(np.polyfit(np.log10(h), np.log10(ex[a:b]), 1)[0])


def main():
    if OUT.exists():
        raise FileExistsError(f'refusing to overwrite {OUT}')
    OUT.mkdir(parents=True)
    rho_ar1 = predicted()
    out = ['# Revision 10: Prop. rho check with the pure 1/b schedule (S8, M = 512, tuning seeds 300-309)', '',
           'excess = ensemble-mean residual power - ensemble-mean residual power of the whole-run LS controller (oracle floor);',
           'ratio = 10 log10(excess(method) / excess(exact growing-window LS)) over hop ranges (1 hop = 16 ms);',
           f'slope = least-squares slope of log10 excess vs log10 hop over hops {SLOPE[0]}-{SLOPE[1]} (exact 1/b decay = -1).',
           f'Prediction (results/gap_check/summary.md, rho_c median): ar1 {rho_ar1:+.2f} dB; harmonic infinite (eigenvalues < 1/2).', '']
    curves = {}; numeric = {}
    for nz in ['ar1', 'harmonic']:
        fl = np.mean([G2.floor_trace(nz, sd) for sd in SEEDS], 0)
        ex = {}
        for name, (meth, prm) in METHODS.items():
            tps = [np.asarray(G2.D.P.run(G2.cfg_of(nz), sd, meth, dict(prm), TT, None)['total_power'], float) for sd in SEEDS]
            if any(not np.all(np.isfinite(t)) for t in tps):
                raise FloatingPointError(f'non-finite power: {nz} {name}')
            tp = np.mean(tps, 0)
            ex[name] = np.maximum(tp[:len(fl)] - fl[:len(tp)], 1e-12); curves[f'{nz}|{name}'] = ex[name]
            print(nz, name, 'done', flush=True)
        ref = ex['exact LS (RLS lam 1)']
        out += [f'## {nz}', '| method | ' + ' | '.join(f'hops {a}-{b}' for a, b in RANGES) + ' | slope |',
                '|---' * (len(RANGES) + 2) + '|']
        numeric[nz] = {}
        for name in METHODS:
            r = {f'{a}-{b}': float(10 * np.log10(ex[name][a:b].mean() / ref[a:b].mean())) for a, b in RANGES}
            r['slope'] = slope(ex[name]); numeric[nz][name] = r
            out.append(f'| {name} | ' + ' | '.join(f'{r[f"{a}-{b}"]:+.2f} dB' for a, b in RANGES) + f' | {r["slope"]:+.3f} |')
        out.append('')
    p = numeric['ar1']['pure 1/b schedule (V-SCHED)']; diff = p['100-312'] - rho_ar1
    h = numeric['harmonic']['pure 1/b schedule (V-SCHED)']; hl = numeric['harmonic']['exact LS (RLS lam 1)']
    h_up = h['100-312'] > h['32-100']; h_slow = abs(h['slope']) < abs(hl['slope'])
    out += ['## Pre-registered interpretation (REVISION_RULE_10 section 2)',
            f'- ar1: ratio over hops 100-312 {p["100-312"]:+.2f} dB vs prediction {rho_ar1:+.2f} dB, difference {diff:+.2f} dB -> '
            + ('agreement (within 1 dB)' if abs(diff) <= 1.0 else 'departure (more than 1 dB)'),
            f'- harmonic: ratio 32-100 {h["32-100"]:+.2f} -> 100-312 {h["100-312"]:+.2f} dB (increase: {h_up}); slope {h["slope"]:+.3f} '
            f'vs exact LS {hl["slope"]:+.3f} (slower decay: {h_slow}) -> ' + ('agreement' if h_up and h_slow else 'departure'), '']
    np.savez(OUT / 'curves.npz', **curves)
    (OUT / 'summary.md').write_text('\n'.join(out) + '\n')
    (OUT / 'numeric.json').write_text(json.dumps({'prediction_ar1_db': rho_ar1, 'ratios': numeric}, indent=2) + '\n')
    (OUT / 'provenance.json').write_text(json.dumps({
        'commit': subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip(),
        'rule_sha256': hashlib.sha256(RULE.read_bytes()).hexdigest(), 'methods': {k: list(v) for k, v in METHODS.items()},
        'seeds': SEEDS, 'python': platform.python_version(),
        'software': {x: version(x) for x in ('numpy', 'scipy', 'pyroomacoustics')},
        'env': {x: os.environ.get(x) for x in ('RLS_FAST', 'OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'MKL_NUM_THREADS')}},
        indent=2) + '\n')
    print('\n'.join(out))


if __name__ == '__main__':
    main()
