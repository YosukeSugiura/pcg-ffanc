"""Step 1 of docs/current/[planning reference omitted]: ablation of the frozen v6.5 towards the 'E-PCG core' (2026-10-28).

Variants (all E-PCG-F, M = 512; v6.5 = sweep_tradeoff.SWEEP['E-PCG-M v6.5'][2][2]):
  V0  v6.5 (reference)
  V1  V0 without the secondary-path re-identification (sid and every sid_* flag removed; the movement ridge stays,
      gated 'after_event', and is then never released)
  V2  V1 without the movement ridge (robust_bound_dx, reg_gamma, reg_gate removed)            = core candidate
  V3  V2 without the memory bank (mem_bank, mem_cheap, mem_primary removed: single window L_hops = 48)
  V4  V2 with adapt = 'restart' (no Prop. 9 weighting: restart the window at the located change)
  V5  V2 with detect = False and without 'doze' in mem_cheap (sliding-window LS only; localize / Prop. 9 inactive;
      'doze' removed because its wake-up relies on the detector's screen, review 2026-10-28)
  V6  V3 with adapt = 'restart' (Prop. 9 in a single window, without the bank that can mask it; compared to V3)
  V1 also removes the S_hat consistency detector (sid_consist_*, forced events). Kept in every variant: score_unreg
  (no effect without the movement ridge, i.e. in V2-V6) and cg_stat_exactJ (stopping-rule fix, [internal rationale omitted]
  #1). Note: V1 -> V2 also changes how the score solution is obtained (separate unregularized solve vs refined control
  filter); on S8 (no events) V1 and V2 differ by about +-0.1 dB. cg_auto (plan V6) is not implemented and was not
  adopted in PARAMETERS_v4 (R3): not run.

Cells (15 cell x noise): S8, S1, S2, S5, S7 (ar1 only), R1, R2, R3 x {ar1, harmonic}. Tuning seeds 300-309, 600-619.
T = 5 s, change at 1.0 s (S5 / R3: continuous 1.0-1.6 s).

Per run (16-hop windows, 1 hop = 16 ms):
  fail : S8 strict_div.evaluate(th = 0); others strict_div.evaluate_div (divergence)
  A    : NR over [1.0 s, end] (hops from int(1.0 fs) // H); S8: last 1 s (62 hops). Failed run: 0 dB
  A1   : NR over the first 0.5 s after the change (32 hops from ceil(1.0 fs / H)); S5 / R3: [1.0, 1.6] s; S8: none.
         Failed run: 0 dB (added 2026-10-28 before the runs: tau at -12 dB sits at its floor in S5 / R3 / S1)
  tau  : first window end k >= ceil(t_e fs / H) + 16 with window NR <= -12 dB (absolute level); tau = k H / fs - t_e;
         not reached: 4 s. t_e = 1.0 s (S5 / R3: 1.6 s; S8: 0). Failed run: 4 s
Decision rules (fixed before the runs; plan section 3.3):
  (i)   a variant with more failed runs than its reference (V1, V2 vs V0; V3-V5 vs V2) in any cell x noise:
        V1 / V2 -> not adopted; V3-V5 -> the removed component is kept
  (ii)  V2 becomes the core iff (i) holds and in all 15 cell x noise the median over seeds of A(V2) - A(V0) <= +0.3 dB
  (iii) V3-V5 vs V2 (and V6 vs V3): the component is kept iff in some cell x noise median dA >= +0.3 dB or
        median dA1 >= +0.5 dB or median dtau >= +0.05 s; otherwise it is dropped. Prop. 9 (V4, V6) is kept if either
        comparison keeps it. V1 is diagnostic only (rule (i) reported). V3-V6 are meaningful only if V2 is adopted.
  If (ii) fails because of failures in the rig cells, stop (fallback of the plan: rig bound, to be discussed).
usage:
  SHARD=0/2 PART=_a python experiments/ablation_core.py run ; SHARD=1/2 PART=_b ... ; python experiments/ablation_core.py summary
"""
import json, math, os, sys, time, zlib
from fractions import Fraction
from pathlib import Path
import numpy as np
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src')); sys.path.insert(0, str(ROOT / 'experiments'))
import strict_div as SD  # noqa: E402
S = SD.S; D = SD.D
ABL_SET = os.environ.get('ABL_SET', 'a')
assert ABL_SET in ('a', 'b', 'c', 'd'), ABL_SET
OUT = ROOT / 'results' / {'a': 'ablation_v6_5', 'b': 'ablation_core_b', 'c': 'ablation_core_c', 'd': 'ablation_core_d'}[ABL_SET]; OUT.mkdir(parents=True, exist_ok=True)
SEEDS = list(range(300, 310)) + list(range(600, 620))
CELLS = ['S8 stationary', 'S1 src 10cm', 'S2 src 30cm', 'S5 src 30cm cont', 'S7 rd abrupt',
         'R1 rig 10cm', 'R2 rig 30cm', 'R3 rig 30cm cont']
CONT = {'S5 src 30cm cont', 'R3 rig 30cm cont'}
NOISES = ['ar1', 'harmonic']
COMBOS = [(nz, sc) for nz in NOISES for sc in CELLS if (nz, sc) != ('harmonic', 'S7 rd abrupt')]   # 15
M = 512; TT = 5.0; T_CAP = 4.0; WIN = 16; L_ABS = -12.0
THR_A = 0.3; THR_T = 0.05

V65 = dict(S.SWEEP['E-PCG-M v6.5'][2][2])
assert V65['robust_bound_dx'] == 0.1 and V65.get('sid') is True


def _drop(p, keys):
    return {k: v for k, v in p.items() if k not in keys}


_V1 = _drop(V65, {k for k in V65 if k == 'sid' or k.startswith('sid_')})
_V2 = _drop(_V1, {'robust_bound_dx', 'reg_gamma', 'reg_gate'})
VAR = {
    'V0': V65,
    'V1': _V1,
    'V2': _V2,
    'V3': _drop(_V2, {'mem_bank', 'mem_cheap', 'mem_primary'}),
    'V4': dict(_V2, adapt='restart'),
    'V5': dict(_V2, detect=False, mem_cheap=[c for c in _V2['mem_cheap'] if c != 'doze']),
}
VAR['V6'] = dict(VAR['V3'], adapt='restart')
REF = {'V1': 'V0', 'V2': 'V0', 'V3': 'V2', 'V4': 'V2', 'V5': 'V2', 'V6': 'V3'}
# ---- ABL_SET = 'b' (2026-10-28, after the code review; fixed before the runs) ----
# C1 = V2 + weight_consistent + fixes_1028 (bug fixes: [workflow reference omitted] 2e). The component ablation is repeated on
# C1 (rules (i)-(iii) unchanged): W2 = C1 vs V0 (rule (ii)); W3 -bank, W4 restart, W5 -detection (vs C1); W6 = W3 restart
# (vs W3). Detector options (review S1 / S2) vs C1: W7 loc_wide, W8 det_C_pre, W9 kd = 128, W10 all three. Rule (iv):
# an option is adopted iff no more failures, no cell x noise with median dA >= +0.3 dB or dA1 >= +0.5 dB, and some
# cell x noise with median dA <= -0.3 dB or dA1 <= -0.5 dB. If several are adopted, the adopted set is the final core
# only if W10 (all three) satisfies the same rule vs C1 (when all three are adopted); otherwise the single adopted
# option with the largest mean improvement of A1 (most negative mean dA1) is taken.
# usage (set b): ABL_SET=b for both run and summary.
# ---- ABL_SET = 'c' (2026-10-29, decisions recorded in [unpublished planning document omitted]; fixed before the runs) ----
# Prop. 9 removed from the algorithm (restart, kept as theory); detector option det_C_pre instead of kd = 128 (rule (iv)
# amended: cost tie-break). Confirmation of the combination never run: X1 = W4 (C1, restart) + det_C_pre vs W4, rule
# (v): confirmed iff no more failures and no cell x noise with median dA >= +0.3 dB or dA1 >= +0.5 dB. X2 = single window
# + Prop. 9 + det_C_pre (low-cost variant for the cost table, reported vs X1, no decision).
if ABL_SET in ('b', 'c', 'd'):
    _C1 = dict(_V2, weight_consistent=True, fixes_1028=True)
    _W3 = _drop(_C1, {'mem_bank', 'mem_cheap', 'mem_primary'})
    VAR = {'V0': V65, 'W2': _C1, 'W3': _W3, 'W4': dict(_C1, adapt='restart'),
           'W5': dict(_C1, detect=False, mem_cheap=[c for c in _C1['mem_cheap'] if c != 'doze']),
           'W6': dict(_W3, adapt='restart'), 'W7': dict(_C1, loc_wide=True), 'W8': dict(_C1, det_C_pre=True),
           'W9': dict(_C1, kd=128), 'W10': dict(_C1, loc_wide=True, det_C_pre=True, kd=128)}
    REF = {'W2': 'V0', 'W3': 'W2', 'W4': 'W2', 'W5': 'W2', 'W6': 'W3', 'W7': 'W2', 'W8': 'W2', 'W9': 'W2', 'W10': 'W2'}
if ABL_SET == 'c':
    VAR = {'W4': VAR['W4'], 'X1': dict(VAR['W4'], det_C_pre=True), 'X2': dict(VAR['W3'], det_C_pre=True)}
    REF = {'X1': 'W4', 'X2': 'X1'}
# ---- ABL_SET = 'd' (2026-10-29, main method = X2 = single window + Prop. 9 + det_C_pre; diagnostics only, no decision)
# Y0 = W3 (single window + Prop. 9, kd 16, no det_C_pre): X2 vs Y0 = direct effect of det_C_pre in the single window.
# Window length L (the only design parameter of the main method): L_hops 24 / 96 / 192 vs 48 (X2); L = 48 is kept
# (declared before the runs); the table is the sensitivity report.
if ABL_SET == 'd':
    _X2 = dict(VAR['W3'], det_C_pre=True)
    VAR = {'Y0': VAR['W3'], 'X2': _X2, 'L24': dict(_X2, L_hops=24), 'L96': dict(_X2, L_hops=96),
           'L192': dict(_X2, L_hops=192)}
    REF = {'X2': 'Y0', 'L24': 'X2', 'L96': 'X2', 'L192': 'X2'}
LABEL = {'V0': 'v6.5', 'V1': '-sid', 'V2': '-sid -ridge (core)', 'V3': 'core -bank', 'V4': 'core restart (no Prop. 9)',
         'V5': 'core -detection', 'V6': 'core -bank, restart (no Prop. 9, single window)',
         'W2': 'C1 = core + fixes', 'W3': 'C1 -bank', 'W4': 'C1 restart (no Prop. 9)', 'W5': 'C1 -detection',
         'W6': 'C1 -bank, restart (single window)', 'W7': 'C1 + loc_wide', 'W8': 'C1 + det_C_pre', 'W9': 'C1 + kd 128',
         'W10': 'C1 + all three options', 'X1': 'final core = C1 restart + det_C_pre',
         'X2': 'low-cost: single window + Prop. 9 + det_C_pre', 'Y0': 'single window + Prop. 9 (no det_C_pre)',
         'L24': 'X2, L = 24 hops', 'L96': 'X2, L = 96 hops', 'L192': 'X2, L = 192 hops'}
THR_A1 = 0.5


def jobs():
    keep = os.environ.get('VARIANTS'); keep = keep.split(';') if keep else list(VAR)
    return [(v, nz, sc, sd) for v in keep for nz, sc in COMBOS for sd in SEEDS]


def one(v, nz, sc, sd):
    cfg = dict(D.SCEN[sc], controller_length=M, fft_length=2 * M, **({} if nz == 'ar1' else {'noise_type': nz}))
    ch = not sc.startswith('S8')
    r = D.P.run(cfg, sd, 'E-PCG-F', dict(VAR[v]), TT, D.CH if ch else None)
    tp = np.array(r['total_power']); up = np.array(r['uncontrolled_power'])
    return {'variant': v, 'prm': VAR[v], 'noise': nz, 'scen': sc, 'seed': sd, 'flag_stable': bool(r['stable']),
            'tp': tp.tolist(), 'up': up[:len(tp)].tolist(), 'hops_full': len(up),
            'flops': float(np.mean(r['flop_hist'])) if r.get('flop_hist') else None}


def read_jsonl(path):
    recs, bad = [], 0
    for line in path.read_text().splitlines():
        try:
            recs.append(json.loads(line))
        except json.JSONDecodeError:
            bad += 1
    return recs, bad


def run():
    fn = OUT / f"runs{os.environ.get('PART', '')}.jsonl"
    done = set(); bad = 0
    for f in OUT.glob('runs*.jsonl'):
        recs, nb = read_jsonl(f); bad += nb
        done |= {(r['variant'], r['noise'], r['scen'], r['seed']) for r in recs if r.get('prm') == VAR.get(r['variant'])}
    si, sn = map(int, os.environ.get('SHARD', '0/1').split('/'))
    torn = fn.exists() and fn.stat().st_size > 0 and not fn.read_bytes().endswith(b'\n')
    t0 = time.time(); n = 0
    with fn.open('a') as fh:
        if torn:
            fh.write('\n')
        for j in jobs():
            if zlib.crc32('|'.join(map(str, j)).encode()) % sn != si or j in done:
                continue
            fh.write(json.dumps(one(*j)) + '\n'); fh.flush(); n += 1
    print(f'{n} runs in {time.time() - t0:.0f} s -> {fn} (resume skipped {bad} bad lines)', flush=True)


def metrics(r):
    sc = r['scen']; cfg = D.SCEN[sc]; H = int(cfg['hop_length']); fs = int(cfg['sample_rate'])
    s8 = sc.startswith('S8')
    fail = SD.evaluate(r, 0.0)[0] if s8 else SD.evaluate_div(r)[0]
    if fail:
        return {'fail': 1, 'A': 0.0, 'A1': None if s8 else 0.0, 'tau': T_CAP}
    tp = np.asarray(r['tp'], float); up = np.asarray(r['up'], float); nh = len(tp)
    nr = lambda a, b: float(10 * np.log10(tp[a:b].sum() / up[a:b].sum()))
    n1 = int(1.0 * fs) // H
    A = nr(nh - n1, nh) if s8 else nr(int(1.0 * fs) // H, nh)
    t_e = 0.0 if s8 else (1.6 if sc in CONT else 1.0)
    a1 = math.ceil(Fraction('1.0') * fs / H)
    A1 = None if s8 else nr(a1, math.ceil(Fraction('1.6') * fs / H) if sc in CONT else a1 + 32)
    s = math.ceil(Fraction(str(t_e)) * fs / H)
    C = np.concatenate([[0.0], np.cumsum(tp)]); U = np.concatenate([[0.0], np.cumsum(up)])
    tau = T_CAP
    for k in range(s + WIN, nh + 1):
        if 10 * np.log10((C[k] - C[k - WIN]) / (U[k] - U[k - WIN])) <= L_ABS:
            tau = round(min(k * H / fs - t_e, T_CAP), 9); break
    return {'fail': 0, 'A': A, 'A1': A1, 'tau': tau}


def summary():
    recs, bad = [], 0
    for f in sorted(OUT.glob('runs*.jsonl')):
        rr, nb = read_jsonl(f); recs += rr; bad += nb
    by = {}; stale = 0; dup = 0; dup_diff = 0
    for r in recs:
        if r.get('prm') != VAR.get(r['variant']):
            stale += 1; continue
        k = (r['variant'], r['noise'], r['scen'], r['seed'])
        if k in by:
            dup += 1; dup_diff += by[k]['tp'] != r['tp']
        else:
            by[k] = r
    miss = [(v, nz, sc) for v in VAR for nz, sc in COMBOS
            if sum((v, nz, sc, sd) in by for sd in SEEDS) < len(SEEDS)]
    if miss:
        print('INCOMPLETE:', miss[:10], f'({len(miss)} groups)'); sys.exit(1)
    Mt = {k: metrics(r) for k, r in by.items()}
    fl = {}
    for (v, nz, sc, sd), r in by.items():
        if r.get('flops') is not None:
            fl.setdefault((v, sc.startswith('S8')), []).append(r['flops'])
    out = [f'# Ablation v6.5 -> core, set {ABL_SET} (tuning seeds 300-309, 600-619; M = 512; T = 5 s)',
           'Rules and metrics: experiments/ablation_core.py docstring (fixed before the runs). d = variant - reference, '
           'median over the 30 paired seeds; positive dA / dtau = the variant is worse. fail = failed runs (variant / reference).', '']
    dec = {}; meanA1 = {}
    if ABL_SET == 'a':
        order = ['V1', 'V2', 'V3', 'V4', 'V5', 'V6']; core, p9pair = 'V2', ('V4', 'V6')
        role = {'V1': 'diag', 'V2': 'core'}
    elif ABL_SET == 'c':
        order = ['X1', 'X2']; core, p9pair = None, None
        role = {'X1': 'conf', 'X2': 'diag'}
    elif ABL_SET == 'd':
        order = ['X2', 'L24', 'L96', 'L192']; core, p9pair = None, None
        role = {v: 'diag' for v in order}
    else:
        order = ['W2', 'W3', 'W4', 'W5', 'W6', 'W7', 'W8', 'W9', 'W10']; core, p9pair = 'W2', ('W4', 'W6')
        role = {'W2': 'core', 'W7': 'opt', 'W8': 'opt', 'W9': 'opt', 'W10': 'opt'}
    for v in order:
        ref = REF[v]
        out += [f'## {v} {LABEL[v]} vs {ref} {LABEL[ref]}',
                '| noise | cell | median A ref (dB) | median dA (dB) | median dA1 (dB) | median dtau (s) | fail |', '|---|---|---|---|---|---|---|']
        worse_fail = False; worse_A = False; worse_A1 = False; worse_T = False; maxdA = -1e9; rig_fail = False
        better = False; dA1s = []
        for nz, sc in COMBOS:
            a = [Mt[(v, nz, sc, sd)] for sd in SEEDS]; b = [Mt[(ref, nz, sc, sd)] for sd in SEEDS]
            dA = float(np.median([x['A'] - y['A'] for x, y in zip(a, b)]))
            dT = float(np.median([x['tau'] - y['tau'] for x, y in zip(a, b)]))
            dA1 = None if sc.startswith('S8') else float(np.median([x['A1'] - y['A1'] for x, y in zip(a, b)]))
            fa = sum(x['fail'] for x in a); fb = sum(y['fail'] for y in b)
            worse_fail |= fa > fb; worse_A |= dA >= THR_A; worse_T |= dT >= THR_T; maxdA = max(maxdA, dA)
            worse_A1 |= dA1 is not None and dA1 >= THR_A1; rig_fail |= fa > fb and sc.startswith('R')
            better |= dA <= -THR_A or (dA1 is not None and dA1 <= -THR_A1)
            if dA1 is not None:
                dA1s.append(dA1)
            mark = (' **' if dA >= THR_A or dT >= THR_T or fa > fb or (dA1 is not None and dA1 >= THR_A1) else '')
            s1 = '-' if dA1 is None else f'{dA1:+.2f}'
            out.append(f"| {nz} | {sc} | {np.median([y['A'] for y in b]):.2f} | {dA:+.2f} | {s1} | {dT:+.3f} | {fa} / {fb}{mark} |")
        meanA1[v] = float(np.mean(dA1s))
        if role.get(v) == 'diag':
            dec[v] = f'diagnostic (more failures than {ref}: {worse_fail}; max median dA {maxdA:+.2f} dB; mean dA1 {meanA1[v]:+.2f} dB)'
        elif role.get(v) == 'conf':
            ok = not (worse_fail or worse_A or worse_A1)
            dec[v] = ('CONFIRMED' if ok else 'NOT confirmed') + f' (more failures: {worse_fail}; worse: {worse_A or worse_A1}; max median dA {maxdA:+.2f} dB)'
        elif role.get(v) == 'opt':
            ok = not (worse_fail or worse_A or worse_A1) and better
            dec[v] = (('option ADOPTED' if ok else 'option not adopted') + f' (more failures: {worse_fail}; worse: '
                      f'{worse_A or worse_A1}; better somewhere: {better}; mean dA1 {meanA1[v]:+.2f} dB)')
        elif role.get(v) == 'core':
            ok = (not worse_fail) and maxdA <= THR_A
            dec[v] = (('adopted as core' if ok else 'NOT adopted') + f' (more failures: {worse_fail}'
                      f'{" (in rig cells: STOP, plan fallback to be discussed)" if rig_fail else ""}; max median dA {maxdA:+.2f} dB)')
        else:
            keep = worse_fail or worse_A or worse_A1 or worse_T
            dec[v] = (('component KEPT' if keep else 'component DROPPED') +
                      f' (more failures: {worse_fail}; dA >= {THR_A}: {worse_A}; dA1 >= {THR_A1}: {worse_A1}; dtau >= {THR_T}: {worse_T})')
        out += ['', f'Decision: {dec[v]}', '']
    p9 = ('Prop. 9 weighting: ' + ('KEPT' if ('KEPT' in dec[p9pair[0]] or 'KEPT' in dec[p9pair[1]]) else 'DROPPED') +
          f' (kept if {p9pair[0]} or {p9pair[1]} keeps it)') if p9pair else f'set {ABL_SET}: no component decision in this set'
    v2ok = dec[core].startswith('adopted') if core else True
    if ABL_SET == 'b':
        ad = [v for v in ('W7', 'W8', 'W9') if dec[v].startswith('option ADOPTED')]
        if len(ad) == 3 and dec['W10'].startswith('option ADOPTED'):
            fin = 'W10 (all three options)'
        elif ad:
            fin = max(ad, key=lambda v: -meanA1[v]) + ' (single option with the largest mean improvement of A1)'
        else:
            fin = 'none (C1 as is)'
        p9 += f'\n- detector options adopted for the final core: {fin}'
    out += ['## Cost (mean of flop_hist = flops per hop as logged by the simulator; S8 / change cells)',
            '| variant | S8 | change cells |', '|---|---|---|']
    out += [f"| {v} {LABEL[v]} | {np.mean(fl.get((v, True), [np.nan])):.0f} | {np.mean(fl.get((v, False), [np.nan])):.0f} |" for v in VAR]
    out += ['', '## Decisions', *[f'- {v} {LABEL[v]}: {dec[v]}' for v in dec], f'- {p9}',
            *([] if v2ok else [f'- {core} not adopted: the component decisions are not meaningful']),
            f'- unparsable lines skipped: {bad}; records: {len(by)}; stale (prm differs): {stale}; '
            f'duplicates: {dup} (differing: {dup_diff})']
    (OUT / 'stats.md').write_text('\n'.join(out) + '\n')
    print('\n'.join(['## Decisions', *[f'- {v} {LABEL[v]}: {dec[v]}' for v in dec], f'- {p9}',
                      *([] if v2ok else [f'- {core} not adopted: component decisions not meaningful'])]))


if __name__ == '__main__':
    {'run': run, 'summary': summary}[sys.argv[1]]()
