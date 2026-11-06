"""Review N6 diagnostic (docs/current/REVISION_RULE_3.md): cold-restart 'RLS + det' (GRID cfg 0) in S7 AR(1) on the
evaluation seeds, against the selected warm configuration (v2b records) and PCG-WLS.
usage: RLS_FAST=1 python experiments/diag_s7_cold.py run ; python experiments/diag_s7_cold.py summary
"""
import json, sys
from pathlib import Path
import numpy as np
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'experiments')); sys.path.insert(0, str(ROOT / 'src'))
import eval_v2 as E  # noqa: E402
import final_eval as FE  # noqa: E402

OUT = ROOT / 'results' / 'revision3_diag'; OUT.mkdir(exist_ok=True)
FN = OUT / 's7_cold.jsonl'
NZ, SC, CFG = 'ar1', 'S7 rd abrupt', 0
PRM = E.GRID['RLS + det'][1][CFG]
assert PRM == {'lam': 0.9999, 'delta': 1e-2, 'det_reset_w': True}, PRM


def run():
    done = {json.loads(l)['seed'] for l in FN.read_text().splitlines()} if FN.exists() else set()
    with FN.open('a') as fh:
        for sd in E.EVAL:
            if sd in done:
                continue
            rec = E.simulate('RLS + det', PRM, 'A', NZ, SC, sd)
            mt = E.run_metrics(rec)
            fh.write(json.dumps(dict(rec, cfg=CFG, A1=mt['A1'], A2=mt['A2'], fail=mt['fail'])) + '\n'); fh.flush()
    print('runs done', flush=True)


def summary():
    cold = {r['seed']: r for r in map(json.loads, FN.read_text().splitlines())}
    assert sorted(cold) == E.EVAL, 'incomplete'
    MET, RUN = {}, {}
    for line in (ROOT / 'results/final_eval_v2b/metrics.jsonl').read_text().splitlines():
        r = json.loads(line)
        if r['noise'] == NZ and r['scen'] == SC:
            MET[(r['method'], r['seed'])] = r
    for f in sorted((ROOT / 'results/final_eval_v2b').glob('runs*.jsonl')):
        for r in FE.read_jsonl(f)[0]:
            if r['noise'] == NZ and r['scen'] == SC and r['method'] in ('E-PCG', 'RLS + det'):
                RUN.setdefault((r['method'], r['seed']), r)
    S = E.EVAL
    A = {'E-PCG': [MET[('E-PCG', s)] for s in S], 'RLS + det (warm, selected)': [MET[('RLS + det', s)] for s in S],
         'RLS + det (cold, cfg 0)': [cold[s] for s in S]}
    L = ['# Review N6 diagnostic: cold vs warm restart of RLS + det, S7 AR(1), evaluation seeds (REVISION_RULE_3.md)', '',
         '| method | median A1 (dB) | median A2 (dB) | failures |', '|---|---|---|---|']
    for m, rs in A.items():
        L.append(f"| {m} | {np.median([r['A1'] for r in rs]):.2f} | {np.median([r['A2'] for r in rs]):.2f} | "
                 f"{sum(int(r['fail']) for r in rs)} |")
    out = {}
    for m in ('RLS + det (warm, selected)', 'RLS + det (cold, cfg 0)'):
        d = np.array([a['A1'] - b['A1'] for a, b in zip(A['E-PCG'], A[m])])
        d2 = np.array([a['A2'] - b['A2'] for a, b in zip(A['E-PCG'], A[m])])
        out[m] = float(np.median(d))
        L.append(f'- E-PCG - {m}: A1 median paired {np.median(d):+.2f} dB (p {FE.pval(d):.2g}), '
                 f'A2 {np.median(d2):+.2f} dB (p {FE.pval(d2):.2g})')
    dc = out['RLS + det (cold, cfg 0)']
    row = 'row 1 (<= -3 dB)' if dc <= -3 else 'row 2 ((-3, -1] dB)' if dc <= -1 else 'row 3 (> -1 dB)'
    L += [f'- interpretation (REVISION_RULE_3): {row}', '']
    H = 128
    taus = {}
    for f in (ROOT / 'results/det_events').glob('*.jsonl'):
        for r in FE.read_jsonl(f)[0]:
            if r['room'] == 'A' and r['noise'] == NZ and r['scen'] == SC and r['events']:
                taus[r['seed']] = r['events'][0][1]
    L += ['| hop | median samples since tau | E-PCG NR | warm NR | cold NR |', '|---|---|---|---|---|']
    exc = {'warm': [], 'cold': []}
    for h in range(62, 80):
        nr = {}
        for k, get in (('E-PCG', lambda s: RUN[('E-PCG', s)]), ('warm', lambda s: RUN[('RLS + det', s)]),
                       ('cold', lambda s: cold[s])):
            tp = sum(get(s)['tp'][h] for s in S); up = sum(get(s)['up'][h] for s in S)
            nr[k] = (tp, up)
        for k in exc:
            exc[k].append(max(nr[k][0] - nr['E-PCG'][0], 0.0))
        since = np.median([(h + 1) * H - taus[s] for s in S])
        if h <= 72:
            L.append(f"| {h} | {since:.0f} | " + ' | '.join(f'{10 * np.log10(nr[k][0] / nr[k][1]):.2f}'
                                                          for k in ('E-PCG', 'warm', 'cold')) + ' |')
    # share of the excess residual energy over PCG-WLS (hops 62-79) by samples since tau (review n21)
    since = [np.median([(h + 1) * H - taus[s] for s in S]) for h in range(62, 80)]
    for k in exc:
        e = np.array(exc[k]); tot = e.sum()
        f1 = e[[i for i, n in enumerate(since) if n <= 512]].sum() / tot
        f2 = e[[i for i, n in enumerate(since) if n <= 580]].sum() / tot
        L.append(f'- {k}: share of the excess residual energy over E-PCG (hops 62-79) at n <= M: {f1:.0%}, n <= 580 '
                 f'(~1.1 M): {f2:.0%}')
    (OUT / 's7_cold.md').write_text('\n'.join(L) + '\n'); print('\n'.join(L))


if __name__ == '__main__':
    {'run': run, 'summary': summary}[sys.argv[1]]()
