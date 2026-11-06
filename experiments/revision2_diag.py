"""Diagnostics of REVISION_RULE_2 sections 4-5 from stored records (no simulation; 2026-10-30).
  N1: 'FD-FxNLMS + restart' vs 'FD-FxNLMS' (evaluation v2b): paired Wilcoxon (pratt) per condition and metric, Holm over
      its 30 comparisons, win rule of FINAL_EVAL_RULE.md; count of conditions with |median A1 difference| <= 0.5 dB.
  N2: PCG-WLS - RLS + det, S7 AR(1) A1 (median paired difference) and the S7 hop table (hops 62-72: ensemble NR of the
      seed-summed powers, 40 evaluation seeds) with the samples since the localized change point tau of the first
      detection (n <= M = 512: the restarted RLS is under-determined).
usage: python experiments/revision2_diag.py   -> results/revision2_diag/n1_n2.md
"""
import json, sys
from pathlib import Path
import numpy as np
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'experiments')); sys.path.insert(0, str(ROOT / 'src'))
import final_eval as FE  # noqa: E402

OUT = ROOT / 'results' / 'revision2_diag'; OUT.mkdir(exist_ok=True)
MET = {}
for line in (ROOT / 'results/final_eval_v2b/metrics.jsonl').read_text().splitlines():
    r = json.loads(line); MET[(r['method'], r['noise'], r['scen'], r['seed'])] = r
CONDS = sorted({(k[1], k[2]) for k in MET})
SEEDS = sorted({k[3] for k in MET})
lines = ['# Revision 2 diagnostics N1 / N2 (REVISION_RULE_2.md sections 4-5; evaluation seeds, results/final_eval_v2b)', '']

# ---------------------------------------------------------------- N1
A, B = 'FD-FxNLMS + restart', 'FD-FxNLMS'
rows = []
for nz, sc in CONDS:
    d1 = np.array([MET[(A, nz, sc, s)]['A1'] - MET[(B, nz, sc, s)]['A1'] for s in SEEDS])
    d2 = np.array([MET[(A, nz, sc, s)]['A2'] - MET[(B, nz, sc, s)]['A2'] for s in SEEDS])
    m1 = float(np.median([MET[(A, nz, sc, s)]['A1'] for s in SEEDS]) - np.median([MET[(B, nz, sc, s)]['A1'] for s in SEEDS]))
    rows.append([nz, sc, float(np.median(d1)), FE.pval(d1), float(np.median(d2)), FE.pval(d2), m1])
adj = iter(FE.holm([x for r in rows for x in (r[3], r[5])]))
lines += ['## N1: FD-FxNLMS + restart minus FD-FxNLMS (negative = restart better); Holm over 30', '',
          '| noise | cell | med dA1 | p_Holm A1 | med dA2 | p_Holm A2 | diff of medians A1 | label (restart vs FD) |',
          '|---|---|---|---|---|---|---|---|']
win = within = 0
for r in rows:
    p1, p2 = next(adj), next(adj)
    lab = FE.label(r[2], p1, r[4], p2)
    win += lab in ('win', 'mixed'); within += abs(r[6]) <= 0.5
    lines.append(f'| {r[0]} | {r[1]} | {r[2]:+.2f} | {p1:.3g} | {r[4]:+.2f} | {p2:.3g} | {r[6]:+.2f} | {lab} |')
if within >= 12 and win == 0:
    v = "row 1: 'FD-FxNLMS does not profit from restarting at the detections'"
elif win >= 3:
    v = 'row 2: the detector also helps FD-FxNLMS; report E-PCG against FD + restart'
else:
    v = 'row 3: report the numbers without either statement'
lines += ['', f'- |diff of medians A1| <= 0.5 dB in {within} of {len(rows)}; wins of FD + restart over FD-FxNLMS: {win}',
          f'- interpretation (REVISION_RULE_2 section 4): {v}', '']

# ---------------------------------------------------------------- N2
nz, sc = 'ar1', 'S7 rd abrupt'
d = np.array([MET[('E-PCG', nz, sc, s)]['A1'] - MET[('RLS + det', nz, sc, s)]['A1'] for s in SEEDS])
lines += ['## N2: E-PCG - RLS + det, S7 AR(1)', '', f'- A1 median paired difference {np.median(d):+.2f} dB', '']
recs = {}
for f in sorted((ROOT / 'results/final_eval_v2b').glob('runs*.jsonl')):
    for r in FE.read_jsonl(f)[0]:
        if r['noise'] == nz and r['scen'] == sc and r['method'] in ('E-PCG', 'RLS + det'):
            recs.setdefault((r['method'], r['seed']), r)
ev = {}
for f in (ROOT / 'results/det_events').glob('*.jsonl'):
    for r in FE.read_jsonl(f)[0]:
        if r['room'] == 'A' and r['noise'] == nz and r['scen'] == sc:
            ev[r['seed']] = r['events']
taus = [ev[s][0][1] for s in SEEDS if ev.get(s)]
stops = [ev[s][0][0] for s in SEEDS if ev.get(s)]
H = 128
lines += [f'- first detection: stop sample median {np.median(stops):.0f} (hop {np.median(stops) / H:.1f}), localized tau '
          f'median {np.median(taus):.0f} (hop {np.median(taus) / H:.1f}); runs with a detection {len(taus)} of {len(SEEDS)}', '',
          '| hop | t (s) | median samples since tau | E-PCG NR (dB) | RLS + det NR (dB) | difference |', '|---|---|---|---|---|---|']
for h in range(62, 73):
    nr = {}
    for m in ('E-PCG', 'RLS + det'):
        tp = sum(recs[(m, s)]['tp'][h] for s in SEEDS); up = sum(recs[(m, s)]['up'][h] for s in SEEDS)
        nr[m] = 10 * np.log10(tp / up)
    since = np.median([(h + 1) * H - t for t in taus])
    lines.append(f'| {h} | {(h + 1) * H / 8000:.3f} | {since:.0f} | {nr["E-PCG"]:.2f} | {nr["RLS + det"]:.2f} | '
                 f'{nr["E-PCG"] - nr["RLS + det"]:+.2f} |')
(OUT / 'n1_n2.md').write_text('\n'.join(lines) + '\n'); print('\n'.join(lines))
