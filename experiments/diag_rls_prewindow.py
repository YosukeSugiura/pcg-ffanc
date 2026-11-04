"""Review N8 diagnostic (docs/current/REVISION_RULE_5.md): RLS + det with a prewindowed restart, S2, evaluation seeds.
usage: RLS_FAST=1 SHARD=k/2 python experiments/diag_rls_prewindow.py run ; python experiments/diag_rls_prewindow.py summary"""
import json, os, sys
from pathlib import Path
import numpy as np
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'experiments')); sys.path.insert(0, str(ROOT / 'src'))
import eval_v2 as E  # noqa: E402
OUT = ROOT / 'results' / 'revision5_diag'; OUT.mkdir(exist_ok=True)
PRM = dict(E.GRID['RLS + det'][1][1], det_prewindow=True)
assert PRM == {'lam': 0.9999, 'delta': 1e-2, 'det_reset_w': False, 'det_prewindow': True}, PRM
JOBS = [(nz, 'S2 src 30cm', sd) for nz in ('ar1', 'harmonic') for sd in E.EVAL]


def run():
    k, n = map(int, os.environ.get('SHARD', '0/1').split('/'))
    fn = OUT / f'runs_{k}.jsonl'
    done = {(r['noise'], r['seed']) for r in map(json.loads, fn.read_text().splitlines())} if fn.exists() else set()
    with fn.open('a') as fh:
        for i, (nz, sc, sd) in enumerate(JOBS):
            if i % n != k or (nz, sd) in done:
                continue
            rec = E.simulate('RLS + det', PRM, 'A', nz, sc, sd); mt = E.run_metrics(rec)
            fh.write(json.dumps({'noise': nz, 'scen': sc, 'seed': sd, 'A1': mt['A1'], 'A2': mt['A2'], 'fail': mt['fail'],
                                 'n_restarts': rec['n_restarts']}) + '\n'); fh.flush()
    print('done', flush=True)


def summary():
    R = [json.loads(l) for f in OUT.glob('runs_*.jsonl') for l in f.read_text().splitlines()]
    V = [json.loads(l) for l in (ROOT / 'results/final_eval_v2c/metrics.jsonl').read_text().splitlines()]
    L = ['# N8: RLS + det with a prewindowed restart (REVISION_RULE_5.md), S2 src 30cm, evaluation seeds', '',
         '| noise | prewindowed RLS + det A1 | RLS + det A1 | SFTF + det A1 | failures (prewindowed) |', '|---|---|---|---|---|']
    rows = []
    for nz in ('ar1', 'harmonic'):
        a = np.median([r['A1'] for r in R if r['noise'] == nz])
        b, c = (np.median([r['A1'] for r in V if r['method'] == m and r['noise'] == nz and r['scen'] == 'S2 src 30cm'])
                for m in ('RLS + det', 'SFTF + det'))
        rows.append((a, b, c)); L.append(f'| {nz} | {a:.2f} | {b:.2f} | {c:.2f} | {sum(r["fail"] for r in R if r["noise"] == nz)} |')
    assert len(R) == 80, len(R)
    if all(abs(a - c) <= 1 for a, b, c in rows):
        v = 'row 1: deficit of SFTF + det attributed to the prewindowed restart'
    elif all(abs(a - b) <= 1 for a, b, c in rows):
        v = 'row 2: deficit attributed to the FTF implementation / numerics'
    else:
        v = 'row 3: numbers only; mechanism not isolated'
    L += ['', f'- interpretation: {v}']
    (OUT / 'rls_prewindow.md').write_text('\n'.join(L) + '\n'); print('\n'.join(L))


if __name__ == '__main__':
    {'run': run, 'summary': summary}[sys.argv[1]]()
