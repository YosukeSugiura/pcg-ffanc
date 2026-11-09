"""Generate the Revision 11 manuscript quantities (tables/r11_values.tex) from the stored summaries and per-run
metrics of the Revision 11 runs, without new experiments.

Sources (results/):
  final_eval_holdout_r11/   11-B/11-C: 13 added baselines, room A holdout, family F1 (summary.md, metrics.jsonl)
  r11_ablation_holdout/     11-A: ablation G1-G5, family F2 (summary.md, metrics.jsonl)
  protocol_r11_sel/         tuning of the added baselines and outer grid points (selection.md, selected.json)
  eval_{roomB,roomC,snr10}_h/, final_eval_meas_{s,p}_h/   11-D: holdout re-evaluation, family F3 (summary.md, wiener.md)
  final_eval_holdout/       prespecified holdout records (Rule 9), read for paired differences only
The prespecified 390 family (139/195) and its macros stay in r9_values.tex (make_r9_values.py).
usage: python paper/v2/make_r11_values.py   (run inside the repository; writes paper/v2/tables/r11_values.tex)
"""
import collections
import json
import re
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
R = ROOT / 'results'
OUT = Path(__file__).resolve().parent / 'tables'

PRESPEC = ['FD-FxNLMS', 'leaky FD-FxNLMS', 'convex FD-FxNLMS', 'FDKF', 'RLS', 'VFF-RLS', 'FD-FxNLMS + det',
           'FD-FxNLMS + restart', 'RLS + det', 'SFTF + det', 'SFTF-H + det', 'CFTF + det', 'RLS + CUSUM']
ADDED = ['MFBLMS', 'MFBLMS + det', 'switching FD-FxNLMS [6]', 'switching FD-FxNLMS + det', 'RLS + det (cond.)',
         'RLS + det + growth', 'RLS + det + growth (from start)', 'RLS (extended grid)', 'VFF-RLS (extended grid)',
         'RLS + CUSUM (extended grid)', 'FD-FxNLMS (extended grid)', 'FDKF (extended grid)',
         'FD-FxNLMS + det (extended grid)']
EXACT = ['RLS + det', 'SFTF-H + det', 'CFTF + det']
FDTYPE = ['FD-FxNLMS', 'leaky FD-FxNLMS', 'convex FD-FxNLMS', 'FDKF', 'FD-FxNLMS + det', 'FD-FxNLMS + restart']
EXTENDED = {'RLS (extended grid)': 'RLS', 'VFF-RLS (extended grid)': 'VFF-RLS', 'RLS + CUSUM (extended grid)': 'RLS + CUSUM',
            'FD-FxNLMS (extended grid)': 'FD-FxNLMS', 'FDKF (extended grid)': 'FDKF',
            'FD-FxNLMS + det (extended grid)': 'FD-FxNLMS + det'}
ABLATION = ['PCG-WLS (fixed order)', 'PCG-WLS (restart)', 'PCG-WLS (no detector)', 'PCG-WLS (fixed order, restart)',
            'PCG-WLS (exact solver)']
CELLS = ['S8 stationary', 'S1 src 10cm', 'S2 src 30cm', 'S5 src 30cm cont', 'S7 rd abrupt', 'R1 rig 10cm',
         'R2 rig 30cm', 'R3 rig 30cm cont']
SHORT = {c: c.split()[0] for c in CELLS}
ROOMSETS = {'B': 'eval_roomB_h', 'C': 'eval_roomC_h', 'Snr': 'eval_snr10_h', 'Ms': 'final_eval_meas_s_h',
            'Mp': 'final_eval_meas_p_h'}


# ---------------------------------------------------------------- parsing
def tables(d):
    """{section heading: [row dict]} for every markdown table of results/<d>/summary.md (headings '## ' and '### ')."""
    out, head, cols = {}, None, None
    for line in (R / d / 'summary.md').read_text().splitlines():
        if line.startswith('#'):
            head, cols = line.lstrip('#').strip(), None
            out.setdefault(head, [])
        elif line.startswith('|') and head is not None:
            c = [x.strip() for x in line.strip().strip('|').split('|')]
            if cols is None:
                cols = c
            elif set(''.join(c)) <= set('-: '):
                continue
            else:
                out[head].append(dict(zip(cols, c)))
    return out


def section(d, prefix):
    t = tables(d)
    keys = [k for k in t if k.startswith(prefix)]
    assert len(keys) == 1, (d, prefix, keys)
    return t[keys[0]]


def counts_line(d, prefix):
    """'Counts: win a, loss b, mixed c, none d (of n)' after the section that starts with prefix."""
    lines = (R / d / 'summary.md').read_text().splitlines()
    i = next(i for i, l in enumerate(lines) if l.startswith('## ') and l[3:].startswith(prefix))
    for l in lines[i + 1:]:
        m = re.match(r'Counts: win (\d+), loss (\d+), mixed (\d+), none (\d+) \(of (\d+)\)', l)
        if m:
            return dict(zip(('win', 'loss', 'mixed', 'none', 'n'), map(int, m.groups())))
        assert not l.startswith('## '), (d, prefix)
    raise AssertionError((d, prefix))


def labels(rows):
    return {(r['baseline'], r['noise'], r['cell']): r for r in rows}


def num(s):
    return float(s.split()[0].replace('+', ''))


def load(d, name='metrics.jsonl'):
    M = collections.defaultdict(dict)
    for line in (R / d / name).read_text().splitlines():
        r = json.loads(line)
        M[(r['method'], r['noise'], r['scen'])][r['seed']] = r
    return M


def paired(MA, a, MB, b, nz, sc, key):
    """Median over seeds of A minus B (paired by seed)."""
    A, B = MA[(a, nz, sc)], MB[(b, nz, sc)]
    assert sorted(A) == sorted(B)
    return float(np.median([A[s][key] - B[s][key] for s in A]))


def med(M, m, nz, sc, key):
    return float(np.median([r[key] for r in M[(m, nz, sc)].values()]))


def fails(M, m, nz, sc):
    return sum(r['fail'] for r in M[(m, nz, sc)].values())


def combos(M=None):
    return [(nz, sc) for nz in ('ar1', 'harmonic') for sc in CELLS if (nz, sc) != ('harmonic', 'S7 rd abrupt')]


def f1(x, nd=1):
    return f'{x:.{nd}f}'


def rng(vals, nd=1, absval=True):
    v = [abs(x) for x in vals] if absval else list(vals)
    lo, hi = f1(min(v), nd), f1(max(v), nd)
    return lo if lo == hi else f'{lo}--{hi}'


def hl_ci(d, nboot=10000):
    """Hodges-Lehmann estimate and 95 % seed-bootstrap interval; same procedure as experiments/revision11_summary.py."""
    d = np.asarray(d, float); n = len(d)
    i, j = np.triu_indices(n)
    hl = float(np.median((d[i] + d[j]) / 2))
    rng_ = np.random.default_rng(0)
    idx = rng_.integers(0, n, (nboot, n))
    s = d[idx]
    b = np.median((s[:, i] + s[:, j]) / 2, axis=1)
    lo, hi = np.quantile(b, [0.025, 0.975])
    return hl, float(lo), float(hi)


# ---------------------------------------------------------------- values
def generate():
    V = {}
    hold = load('final_eval_holdout')
    new = load('final_eval_holdout_r11')
    abl = load('r11_ablation_holdout')
    F1 = labels(section('final_eval_holdout_r11', 'F1: E-PCG vs'))
    F1b = labels(section('final_eval_holdout_r11', 'F1: E-PCG bank vs'))
    P = labels(section('final_eval_holdout', 'E-PCG vs baselines'))
    c1 = counts_line('final_eval_holdout_r11', 'F1: E-PCG vs'); c1b = counts_line('final_eval_holdout_r11', 'F1: E-PCG bank vs')
    assert len(F1) == 195 and c1['n'] == 195
    V.update(FoneWins=c1['win'], FoneLoss=c1['loss'], FoneMixed=c1['mixed'], FoneNone=c1['none'], FonePairs=c1['n'],
             FoneTests=2 * c1['n'], FoneBankWins=c1b['win'], FoneBankLoss=c1b['loss'], AddedN=len(ADDED))
    lab = collections.Counter(r['label'] for r in F1.values())
    assert (lab['win'], lab['loss'], lab['mixed'], lab['-']) == (c1['win'], c1['loss'], c1['mixed'], c1['none'])

    # --- wins of the prespecified family per baseline group (review M2)
    groups = {'Fd': FDTYPE, 'Rls': ['RLS', 'VFF-RLS'], 'Ex': EXACT, 'Sftf': ['SFTF + det'], 'Cusum': ['RLS + CUSUM']}
    assert sorted(sum(groups.values(), [])) == sorted(PRESPEC)
    for g_, members in groups.items():
        ls = [r['label'] for (b, _, _), r in P.items() if b in members]
        V[f'Pre{g_}Wins'], V[f'Pre{g_}Pairs'] = ls.count('win'), len(ls)
    # --- the four Must baselines (M3(a))
    four = ADDED[:4]
    w = {b: sum(F1[(b, nz, sc)]['label'] == 'win' for nz, sc in combos()) for b in four}
    V['FourWins'] = sum(w.values()); V['FourPairs'] = 15 * len(four)
    V['FourLoss'] = sum(F1[(b, nz, sc)]['label'] == 'loss' for b in four for nz, sc in combos())
    d = lambda b, nz, sc, k='A1': num(F1[(b, nz, sc)][f'med d{k}'])
    V['MfblmsAoneRange'] = rng([d('MFBLMS', nz, sc) for nz, sc in combos()])
    assert max(d('MFBLMS', nz, sc) for nz, sc in combos()) < 0
    sw, swd = 'switching FD-FxNLMS [6]', 'switching FD-FxNLMS + det'
    small = ['S1 src 10cm', 'S5 src 30cm cont', 'R1 rig 10cm', 'R3 rig 30cm cont']
    move = ['S2 src 30cm', 'R2 rig 30cm']
    V['SwSeight'] = f1(abs(d(sw, 'ar1', 'S8 stationary')))
    V['SwSmall'] = rng([d(sw, 'ar1', c) for c in small])
    V['SwMove'] = rng([d(sw, 'ar1', c) for c in move])
    V['SwSseven'] = f1(abs(d(sw, 'ar1', 'S7 rd abrupt')))
    V['SwHarm'] = rng([d(sw, 'harmonic', c) for c in CELLS if c != 'S7 rd abrupt'])
    V['SwdSeight'] = f1(abs(d(swd, 'ar1', 'S8 stationary')))
    V['SwdSmall'] = rng([d(swd, 'ar1', c) for c in small])
    V['SwdMove'] = rng([d(swd, 'ar1', c) for c in move])
    V['SwdSseven'] = f1(abs(d(swd, 'ar1', 'S7 rd abrupt')))
    V['SwdHarm'] = rng([d(swd, 'harmonic', c) for c in CELLS if c != 'S7 rd abrupt'])
    V['SwdNoneCells'] = ', '.join(SHORT[sc] + ('$^h$' if nz == 'harmonic' else '') for nz, sc in combos()
                                  if F1[(swd, nz, sc)]['label'] != 'win')
    diag = (R / 'final_eval_holdout_r11/summary.md').read_text()
    m = re.search(r'switching FD-FxNLMS \[6\]: switches total (\d+), mean hops in M ([0-9.]+) of (\d+)', diag)
    V['SwSwitches'] = m.group(1); V['SwHopsM'] = f'{float(m.group(2)):.0f}'; V['SwHops'] = m.group(3)
    m = re.search(r'switching FD-FxNLMS \+ det: switches total (\d+), mean hops in M ([0-9.]+) of (\d+)', diag)
    V['SwdSwitches'] = m.group(1); V['SwdHopsM'] = f'{float(m.group(2)):.0f}'
    m = re.search(r'RLS \+ det \(cond\.\): events (\d+), restarts applied (\d+)', diag)
    V['CondEvents'], V['CondRestarts'] = int(m.group(1)), int(m.group(2))
    V['CondKept'] = V['CondEvents'] - V['CondRestarts']
    # switching variants relative to FD-FxNLMS (prespecified records): A2 difference of medians, descriptive
    sw_a2 = [paired(new, b, hold, 'FD-FxNLMS', nz, 'S8 stationary', 'A2') for b in (sw, swd) for nz in ('ar1', 'harmonic')]
    sw_a1 = [paired(new, b, hold, 'FD-FxNLMS', nz, sc, 'A1') for b in (sw, swd) for nz, sc in combos()]
    V['SwAoneMaxGain'] = f'{max(0.0, -min(sw_a1)):.2f}'
    V['SwStatAtwo'] = rng(sw_a2, 1)
    V['SwStatAtwoSign'] = 'lower' if max(sw_a2) < 0 else 'mixed'
    # runs of RLS+det (cond.) that differ from RLS+det
    diff = sum(1 for (m_, nz, sc), runs in new.items() if m_ == 'RLS + det (cond.)' for s, r in runs.items()
               if (r['A1'], r['A2']) != (hold[('RLS + det', nz, sc)][s]['A1'], hold[('RLS + det', nz, sc)][s]['A2']))
    V['CondDiffRuns'] = diff; V['CondRuns'] = sum(len(v) for (m_, _, _), v in new.items() if m_ == 'RLS + det (cond.)')
    # paired median difference to RLS + det is 0.00 in every cell and metric (most runs identical); the cell medians
    # themselves differ by up to CondMedMax dB because the 25 changed runs move the order statistics
    cond_pair = max(abs(paired(new, 'RLS + det (cond.)', hold, 'RLS + det', nz, sc, k)) for nz, sc in combos() for k in ('A1', 'A2'))
    V['CondPairMax'] = f'{cond_pair:.2f}'
    V['CondMedMax'] = f"{max(abs(med(new, 'RLS + det (cond.)', nz, sc, k) - med(hold, 'RLS + det', nz, sc, k)) for nz, sc in combos() for k in ('A1', 'A2')):.2f}"
    cond_lab = all(F1[('RLS + det (cond.)', nz, sc)]['label'] == P[('RLS + det', nz, sc)]['label'] for nz, sc in combos())
    assert cond_lab, 'RLS + det (cond.) has a label different from RLS + det'

    # --- RLS+det vs RLS (S2 of the review) and the best RLS-family member
    rd = [paired(hold, 'RLS + det', hold, 'RLS', 'ar1', c, 'A1') for c in small]
    V['RlsdetMinusRls'] = rng(rd); V['RlsdetMinusRlsSign'] = 'worse' if min(rd) > 0 else 'mixed'
    V['RlsNoneSmall'] = 'yes' if all(P[('RLS', 'ar1', c)]['label'] == '-' for c in small) else 'no'
    best = {(r['noise'], r['cell']): r for r in section('final_eval_holdout_r11', 'PCG-WLS minus the best RLS-family')}
    V['BestRlsSoneRone'] = rng([num(best[('ar1', c)]['PCG-WLS - best dA1']) for c in ('S1 src 10cm', 'R1 rig 10cm')])
    V['BestRlsSfiveRthree'] = f"{max(abs(num(best[('ar1', c)]['PCG-WLS - best dA1'])) for c in ('S5 src 30cm cont', 'R3 rig 30cm cont')):.2f}"
    rls_win_cells = [SHORT[c] for c in CELLS if P[('RLS + det', 'ar1', c)]['label'] == 'win']
    V['RlsdetWinCells'] = ', '.join(rls_win_cells)

    # --- G1 and the RLS + det + growth variants (M3(b))
    g = {(r['noise'], r['cell']): r for r in section('r11_ablation_holdout', '(iii) G1 - RLS + det')}
    gd = lambda nz, c, k: num(g[(nz, c)][k])
    V['GzeroSseven'] = f1(abs(gd('ar1', 'S7 rd abrupt', 'G0 dA1')))
    V['GoneSseven'] = f1(gd('ar1', 'S7 rd abrupt', 'G1 dA1'))
    V['GzeroSeight'] = f1(abs(gd('ar1', 'S8 stationary', 'G0 dA1')))
    V['GoneSeight'] = f1(abs(gd('ar1', 'S8 stationary', 'G1 dA1')))
    V['GzeroHarmMove'] = rng([gd('harmonic', c, 'G0 dA1') for c in move])
    V['GoneHarmMove'] = rng([gd('harmonic', c, 'G1 dA1') for c in move])
    V['GzeroMove'] = ' and '.join(f1(abs(gd('ar1', c, 'G0 dA1'))) for c in move)
    V['GoneMove'] = ' and '.join(f1(abs(gd('ar1', c, 'G1 dA1'))) for c in move)
    ch = [abs(gd('ar1', c, 'G1 dA1') - gd('ar1', c, 'G0 dA1')) for c in small]
    V['GoneSmallChange'] = rng(ch, 2)
    gvr = labels(section('r11_ablation_holdout', '(ii) PCG-WLS (fixed order) vs'))
    gl = lambda nz, c: gvr[('RLS + det', nz, c)]['label']
    assert gl('ar1', 'S7 rd abrupt') == 'loss' and gl('ar1', 'S8 stationary') == 'win'
    assert all(gl('harmonic', c) == 'loss' for c in move) and all(gl('ar1', c) == '-' for c in move)
    V['GoneRlsdetWins'] = sum(gl(nz, c) == 'win' for nz, c in combos())
    V['GoneRlsdetLoss'] = sum(gl(nz, c) == 'loss' for nz, c in combos())
    V['GoneSmallLabels'] = ', '.join(f"{SHORT[c]} {gl('ar1', c) if gl('ar1', c) != '-' else 'no decision'}" for c in small)
    nm = {(r['baseline'], r['noise'], r['cell']): r for r in section('final_eval_holdout_r11', 'New baselines minus RLS + det')}
    gr, grs = 'RLS + det + growth', 'RLS + det + growth (from start)'
    V['GrowthSseven'] = f1(abs(num(nm[(gr, 'ar1', 'S7 rd abrupt')]['dA1'])))
    assert num(nm[(gr, 'ar1', 'S7 rd abrupt')]['dA1']) < 0
    V['GrowthStartSeight'] = f1(abs(num(nm[(grs, 'ar1', 'S8 stationary')]['dA1'])))
    assert num(nm[(grs, 'ar1', 'S8 stationary')]['dA1']) < 0
    arch = [c for c in CELLS if c not in ('S8 stationary', 'S7 rd abrupt')]
    V['GrowthArMoves'] = rng([num(nm[(b, 'ar1', c)]['dA1']) for b in (gr, grs) for c in arch])
    assert min(num(nm[(b, 'ar1', c)]['dA1']) for b in (gr, grs) for c in arch) > 0
    V['GrowthHarm'] = rng([num(nm[(b, 'harmonic', c)]['dA1']) for b in (gr, grs) for c in CELLS if c != 'S7 rd abrupt'])
    V['GrowthWins'] = sum(F1[(gr, nz, c)]['label'] == 'win' for nz, c in combos())
    V['GrowthStartWins'] = sum(F1[(grs, nz, c)]['label'] == 'win' for nz, c in combos())
    # ablation (F2)
    for tag, g_ in zip(('Gone', 'Gtwo', 'Gthree', 'Gfour', 'Gfive'), ABLATION):
        c = counts_line('r11_ablation_holdout', f'(ii) {g_} vs')
        V[tag + 'Wins'], V[tag + 'Loss'] = c['win'], c['loss']
        V[tag + 'WorseCells'] = len({(r['noise'], r['cell']) for r in section('r11_ablation_holdout', f'(i) {g_} - G0') if r['flag'] == 'worse'})
    s5 = [num(r['median d']) for r in section('r11_ablation_holdout', '(i) PCG-WLS (restart) - G0')
          if r['noise'] == 'harmonic' and r['cell'] in ('S5 src 30cm cont', 'R3 rig 30cm cont') and r['flag'] == 'worse']
    V['GtwoHarmCont'] = rng(s5)
    other = [num(r['median d']) for r in section('r11_ablation_holdout', '(i) PCG-WLS (restart) - G0') if r['flag'] != 'worse']
    V['GtwoOtherMax'] = f1(max(other))
    g5 = section('r11_ablation_holdout', '(i) PCG-WLS (exact solver) - G0')
    V['GfiveWorse'] = sum(r['flag'] == 'worse' for r in g5)
    V['GfiveMax'] = f1(max(abs(num(r['median d'])) for r in g5))
    g5l = labels(section('r11_ablation_holdout', '(ii) PCG-WLS (exact solver) vs'))
    V['GfiveLabelDiff'] = sum(g5l[k]['label'] != P[k]['label'] for k in P)
    V['GoneMinusGzeroSeight'] = f1(num(next(r['median d'] for r in section('r11_ablation_holdout', '(i) PCG-WLS (fixed order) - G0')
                                            if r['noise'] == 'ar1' and r['cell'] == 'S8 stationary' and r['key'] == 'A1')))
    V['GoneMinusGzeroSseven'] = f1(num(next(r['median d'] for r in section('r11_ablation_holdout', '(i) PCG-WLS (fixed order) - G0')
                                             if r['noise'] == 'ar1' and r['cell'] == 'S7 rd abrupt' and r['key'] == 'A1')))
    V['GrowthShareSeight'] = f1(abs(gd('ar1', 'S8 stationary', 'G0 dA1')) - abs(gd('ar1', 'S8 stationary', 'G1 dA1')))

    # --- outer grid (S1 of the review)
    sel = (R / 'protocol_r11_sel/selection.md').read_text()
    gains = []
    for base, ext in [(v, k) for k, v in EXTENDED.items()]:
        m = re.search(r'^- ' + re.escape(base) + r': (\{.*\})$', sel, re.M)
        info = json.loads(m.group(1))
        gains.append(info['reference_score'] - info['row']['score'])
    V['OuterGain'] = rng(gains, 2)
    ext_same = []
    for ext, base in EXTENDED.items():
        we = sum(F1[(ext, nz, c)]['label'] == 'win' for nz, c in combos())
        wb = sum(P[(base, nz, c)]['label'] == 'win' for nz, c in combos())
        ext_same.append(we == wb)
    V['OuterSameWins'] = 'all' if all(ext_same) else f'{sum(ext_same)} of {len(ext_same)}'
    assert all(ext_same), 'an extended-grid row has a different win count than its original selection'
    # outer points per base (final review S4): VFF-RLS improved at both steps; SFTF-H + det and leaky were not better
    outer = {b: json.loads(re.search(r'^- ' + re.escape(b) + r': (\{.*\})$', sel, re.M).group(1))
             for b in ('VFF-RLS', 'SFTF-H + det', 'leaky FD-FxNLMS')}
    vf = outer['VFF-RLS']
    assert vf['first'][0]['value'] < vf['reference_score'] and vf['second'][0]['value'] < vf['first'][0]['value']
    V['OuterVffRef'] = f"{vf['reference_score']:.2f}"
    V['OuterVffOne'] = f"{vf['first'][0]['value']:.2f}"; V['OuterVffOneN'] = f"{vf['first'][0]['prm']['N0']:.0f}"
    V['OuterVffTwo'] = f"{vf['second'][0]['value']:.2f}"; V['OuterVffTwoN'] = f"{vf['second'][0]['prm']['N0']:.0f}"
    sh = outer['SFTF-H + det']
    assert len(sh['first']) == 1 and sh['row'] is None
    V['OuterSftfhTh'] = sh['first'][0]['prm']['hybrid']
    V['OuterSftfh'] = f"{sh['first'][0]['value']:.3f}"; V['OuterSftfhRef'] = f"{sh['reference_score']:.2f}"
    lk = outer['leaky FD-FxNLMS']
    assert lk['row'] is None and [p['result'] for p in lk['first']] == ['done', 'fail']
    V['OuterLeakyOne'] = f"$\\mu={lk['first'][0]['prm']['mu']}$, leak {lk['first'][0]['prm']['leak']}: ${lk['first'][0]['value']:.2f}$ dB"
    V['OuterLeakyTwo'] = f"$\\mu={lk['first'][1]['prm']['mu']}$, leak {lk['first'][1]['prm']['leak']}"
    V['OuterLeakyRef'] = f"{lk['reference_score']:.2f}"
    # MFBLMS grid (final review S5): admissible only at the smallest-but-one step; larger steps failed
    mf = re.findall(r'^\| MFBLMS \| (\d+)[^|]*\| (\{[^|]*\}) \| ([^|]*) \|$', sel, re.M)
    mf = [(json.loads(p)['mu'], res.strip()) for _, p, res in mf]
    fail_s7 = sorted(mu for mu, res in mf if res.startswith('fail') and 'S7' in res)
    fail_other = sorted(mu for mu, res in mf if res.startswith('fail') and 'S7' not in res)
    ok = sorted(mu for mu, res in mf if not res.startswith('fail'))
    assert ok == [0.025, 0.05] and fail_s7 == [0.1, 0.15, 0.2, 0.25] and fail_other == [0.3], (ok, fail_s7, fail_other)
    V['MfblmsFailSseven'] = f'{fail_s7[0]}--{fail_s7[-1]}'; V['MfblmsFailOther'] = f'{fail_other[0]}'
    fd_mu = re.search(r"^\| FD-FxNLMS \| [^|]*\| \d+ \{'mu': ([0-9.]+)\}", (R / 'protocol_v2_sel/selection_e.md').read_text(), re.M)
    V['FdMu'] = fd_mu.group(1); V['MfblmsStepRatio'] = f"{float(fd_mu.group(1)) / 0.05:.0f}"

    # --- 11-D: holdout rooms, SNR 10 dB and measured paths (F3)
    total_agree = total_n = 0
    for tag, dset in ROOMSETS.items():
        F3 = labels(section(dset, 'F3: E-PCG vs'))
        c = counts_line(dset, 'F3: E-PCG vs')
        V[f'H{tag}Wins'], V[f'H{tag}Loss'], V[f'H{tag}Mixed'], V[f'H{tag}None'], V[f'H{tag}Pairs'] = \
            c['win'], c['loss'], c['mixed'], c['none'], c['n']
        V[f'H{tag}Tests'] = 2 * c['n']
        for part, group in (('Pre', PRESPEC), ('Add', ADDED)):
            ls = [r['label'] for (b, _, _), r in F3.items() if b in group]
            V[f'H{tag}{part}Wins'] = ls.count('win'); V[f'H{tag}{part}Loss'] = ls.count('loss')
            V[f'H{tag}{part}Pairs'] = len(ls)
        t = tables(dset)
        key = next(k for k in t if k.startswith('E-PCG: agreement'))
        a, n = map(int, re.search(r'agreement (\d+)/(\d+)', key).groups())
        V[f'H{tag}Agree'], V[f'H{tag}AgreeN'] = a, n
        total_agree += a; total_n += n
        cb = counts_line(dset, 'F3: E-PCG bank vs')
        V[f'H{tag}BankWins'], V[f'H{tag}BankLoss'] = cb['win'], cb['loss']
    V['HAgree'], V['HAgreeN'] = total_agree, total_n
    for tag in ('B', 'C'):
        dset = ROOMSETS[tag]
        F3 = labels(section(dset, 'F3: E-PCG vs'))
        M = load(dset)
        fdw = [r for (b, _, _), r in F3.items() if b in FDTYPE]
        wins_ = [r for r in fdw if r['label'] == 'win']
        a2ok = [r for r in wins_ if num(r['med dA2']) <= -0.5 and float(r['p_Holm A2']) < 0.05]
        a1ok = [r for r in wins_ if num(r['med dA1']) <= -1.0 and float(r['p_Holm A1']) < 0.05]
        V[f'H{tag}FdWins'], V[f'H{tag}FdPairs'] = len(wins_), len(fdw)
        V[f'H{tag}FdAtwo'], V[f'H{tag}FdAone'] = len(a2ok), len(a1ok)
        ex = {k: r for k, r in F3.items() if k[0] in EXACT}
        exw = [r for r in ex.values() if r['label'] == 'win']
        exl = [r for r in ex.values() if r['label'] == 'loss']
        V[f'H{tag}ExWinCells'] = ', '.join(sorted({SHORT[r['cell']] + ('$^h$' if r['noise'] == 'harmonic' else '') for r in exw}))
        V[f'H{tag}ExWinAone'] = rng([num(r['med dA1']) for r in exw])
        V[f'H{tag}ExLossCells'] = ', '.join(sorted({SHORT[r['cell']] + ('$^h$' if r['noise'] == 'harmonic' else '') for r in exl}))
        V[f'H{tag}ExLossCellN'] = len({(r['noise'], r['cell']) for r in exl})
        V[f'H{tag}ExLossN'] = len(exl)
        hs2 = [num(r['med dA1']) for r in exl if r['noise'] == 'harmonic' and r['cell'] == 'S2 src 30cm']
        ar2 = [num(r['med dA2']) for r in exl if r['noise'] == 'ar1' and r['cell'] == 'R2 rig 30cm']
        V[f'H{tag}ExHarmSAone'] = rng(hs2); V[f'H{tag}ExRtwoAtwo'] = rng(ar2)
        cu = [r for (b, _, _), r in F3.items() if b == 'RLS + CUSUM' and r['label'] == 'loss']
        V[f'H{tag}CusumLossCells'] = ', '.join(SHORT[r['cell']] + ('$^h$' if r['noise'] == 'harmonic' else '') for r in cu)
        V[f'H{tag}CusumLossAone'] = rng([num(r['med dA1']) for r in cu])
        V[f'H{tag}EharmRtwo'] = fails(M, 'E-PCG', 'harmonic', 'R2 rig 30cm')
        V[f'H{tag}EarRtwo'] = fails(M, 'E-PCG', 'ar1', 'R2 rig 30cm')
        V[f'H{tag}RlsharmRtwo'] = fails(M, 'RLS + det', 'harmonic', 'R2 rig 30cm')
        V[f'H{tag}RlsarRtwo'] = fails(M, 'RLS + det', 'ar1', 'R2 rig 30cm')
        for c, nm_ in (('S8 stationary', 'Szero'), ('S2 src 30cm', 'Stwo'), ('S5 src 30cm cont', 'Sfive')):
            V[f'H{tag}Bank{nm_}'] = fails(M, 'E-PCG bank', 'harmonic', c)
        ad = [r for (b, _, _), r in F3.items() if b in ADDED[:4] and r['label'] == 'loss']
        V[f'H{tag}FourLossN'] = len(ad)
        if ad:
            V[f'H{tag}FourLossNames'] = ', '.join(sorted({r['baseline'] for r in ad}))
            V[f'H{tag}FourLossAtwo'] = rng([num(r['med dA2']) for r in ad])
            V[f'H{tag}FourLossAone'] = rng([num(r['med dA1']) for r in ad])
            V[f'H{tag}FourLossFails'] = ', '.join(sorted({str(fails(M, r['baseline'], r['noise'], r['cell'])) for r in ad}))
            V[f'H{tag}FourLossCells'] = ', '.join(sorted({r['noise'] + ' ' + SHORT[r['cell']] for r in ad}))
        lossall = [r for r in F3.values() if r['label'] in ('loss', 'mixed')]
        V[f'H{tag}LossRtwo'] = sum(r['cell'] == 'R2 rig 30cm' for r in lossall if r['label'] == 'loss')
    # both rooms together, and consistency checks that the text relies on
    exw_all, cu_all = [], []
    for tag in ('B', 'C'):
        F3 = labels(section(ROOMSETS[tag], 'F3: E-PCG vs'))
        exw_all += [num(r['med dA1']) for (b, _, _), r in F3.items() if b in EXACT and r['label'] == 'win']
        cu_all += [num(r['med dA1']) for (b, _, _), r in F3.items() if b == 'RLS + CUSUM' and r['label'] == 'loss']
        assert V[f'H{tag}FdAtwo'] == V[f'H{tag}FdWins'], 'an FD-type win in a room does not meet the A2 criterion'
    V['HExWinAoneAll'] = rng(exw_all); V['HCusumLossAoneAll'] = rng(cu_all)
    # room C, AR(1) R2: failures of other methods (final review S7; descriptive, no mechanism claimed)
    MC_ = load(ROOMSETS['C'])
    fc = {m_: fails(MC_, m_, 'ar1', 'R2 rig 30cm') for (m_, nz, sc) in MC_ if nz == 'ar1' and sc == 'R2 rig 30cm'}
    V['HCRtwoFailFd'] = fc['FD-FxNLMS']; V['HCRtwoFailRls'] = fc['RLS']
    V['HCRtwoFailFdTypeRange'] = rng([fc[b] for b in FDTYPE], 0)
    low = sorted(m_ for m_, f in fc.items() if f <= 1)
    assert low == sorted(['MFBLMS', 'MFBLMS + det', 'switching FD-FxNLMS + det']), low
    # multi-window variant: stationary cost relative to PCG-WLS at M = 512 (extra_eval, seeds 480-519; Minor m11)
    ee = (R / 'extra_eval/summary.md').read_text()
    cst = {m_: int(v) for m_, v in re.findall(r'^\| (E-PCG(?: bank)?) \| 512 \| (\d+) / \d+ \| ar1 \|', ee, re.M)}
    V['MultiCostRatio'] = f"{cst['E-PCG bank'] / cst['E-PCG']:.1f}"
    assert V['HBExLossCellN'] == V['HCExLossCellN'], 'exact-restart loss cells differ between rooms B and C'
    assert V['GrowthWins'] == V['GrowthStartWins']
    # SNR 10 dB
    F3 = labels(section('eval_snr10_h', 'F3: E-PCG vs'))
    exw = [r for (b, _, _), r in F3.items() if b in EXACT and r['label'] == 'win']
    V['HSnrExWinCells'] = ', '.join(sorted({r['noise'] + ' ' + SHORT[r['cell']] for r in exw}))
    V['HSnrExWinAone'] = rng([num(r['med dA1']) for r in exw])
    V['HSnrExOther'] = 'none' if all(r['label'] in ('win', '-') for (b, _, _), r in F3.items() if b in EXACT) else 'some'
    # measured paths
    Fs = labels(section('final_eval_meas_s_h', 'F3: E-PCG vs'))
    Fp = labels(section('final_eval_meas_p_h', 'F3: E-PCG vs'))
    Mp, Ms = load('final_eval_meas_p_h'), load('final_eval_meas_s_h')
    V['HMpExNone'] = 'yes' if all(r['label'] == '-' for (b, _, _), r in Fp.items() if b in EXACT) else 'no'
    V['HMpWinsOutside'] = 'yes' if all(b not in EXACT for (b, _, _), r in Fp.items() if r['label'] == 'win') else 'no'
    fd_harm = [num(r['med dA1']) for (b, nz, _), r in Fp.items() if b in FDTYPE and nz == 'harmonic']
    V['HMpFdHarmAone'] = rng(fd_harm)
    V['HMpRlsAone'] = f"{num(Fp[('RLS + det', 'ar1', 'S2 src 30cm')]['med dA1']):.2f}"
    V['HMpRlsAonePsig'] = 'yes' if float(Fp[('RLS + det', 'ar1', 'S2 src 30cm')]['p_Holm A1']) < 0.05 else 'no'
    V['HMpRlsHarmAone'] = f"{num(Fp[('RLS + det', 'harmonic', 'S2 src 30cm')]['med dA1']):.2f}"
    V['HMpRlsHarmPsig'] = 'yes' if float(Fp[('RLS + det', 'harmonic', 'S2 src 30cm')]['p_Holm A1']) < 0.05 else 'no'
    V['HMpRlsAtwoMax'] = f"{max(abs(num(Fp[('RLS + det', nz, 'S2 src 30cm')]['med dA2'])) for nz in ('ar1', 'harmonic')):.2f}"
    V['HMpNoFail'] = 'yes' if all(fails(Mp, m, nz, sc) == 0 for (m, nz, sc) in Mp if m in EXACT + ['E-PCG', 'SFTF + det']) else 'no'
    msw = [r for (b, _, _), r in Fs.items() if r['label'] == 'win']
    V['HMsWinsAtwoAll'] = 'yes' if all(num(r['med dA2']) <= -0.5 and float(r['p_Holm A2']) < 0.05 for r in msw) else 'no'
    V['HMsWinsAtwoN'] = sum(num(r['med dA2']) <= -0.5 and float(r['p_Holm A2']) < 0.05 for r in msw)
    V['HMsWinsAoneOnly'] = ', '.join(sorted({r['baseline'] for r in msw if not (num(r['med dA2']) <= -0.5 and float(r['p_Holm A2']) < 0.05)}))
    V['HMsWinsAoneN'] = sum(num(r['med dA1']) <= -1.0 and float(r['p_Holm A1']) < 0.05 for r in msw)
    V['HMsFdAtwo'] = rng([num(r['med dA2']) for r in msw if r['baseline'] in FDTYPE])
    assert all(num(r['med dA2']) <= -0.5 and float(r['p_Holm A2']) < 0.05 for r in msw if r['baseline'] in FDTYPE)
    # M-S, AR(1): baselines whose A1 is significantly better than that of PCG-WLS (final review, Must 1).
    # The text names exactly these four FD-type baselines and states that the differences are below the 1 dB margin.
    ms_rev = [r for (b, nz, _), r in Fs.items() if nz == 'ar1' and num(r['med dA1']) > 0 and float(r['p_Holm A1']) < 0.05]
    assert sorted(r['baseline'] for r in ms_rev) == sorted(['FD-FxNLMS', 'convex FD-FxNLMS', 'FD-FxNLMS + det',
                                                            'FD-FxNLMS + restart']), [r['baseline'] for r in ms_rev]
    assert all(r['label'] == 'win' for r in ms_rev)
    assert not [r for (b, nz, _), r in Fs.items() if nz == 'harmonic' and num(r['med dA1']) > 0 and float(r['p_Holm A1']) < 0.05]
    ms_exact = [paired(Ms, 'E-PCG', Ms, r['baseline'], 'ar1', r['cell'], 'A1') for r in ms_rev]   # PCG-WLS minus baseline
    assert max(ms_exact) < 1.0, 'an A1 difference reaches the 1 dB margin (would be mixed)'
    V['HMsRevN'] = len(ms_rev)
    V['HMsRevMin'] = f'{min(ms_exact):.2f}'
    V['HMsRevMax'] = f'{max(ms_exact):.3f}'          # 0.999: two decimals would print 1.00 at the 1 dB margin
    V['HMsRevHl'] = rng([float(r['HL dA1 [95% CI]'].split()[0]) for r in ms_rev])
    ps = [float(r['p_Holm A1']) for r in ms_rev]
    V['HMsRevP'] = f'{min(ps):.4f}--{max(ps):.3f}'
    exh = [r for (b, nz, _), r in Fs.items() if b in EXACT + ['SFTF + det'] and nz == 'harmonic']
    V['HMsExHarmAone'] = rng([num(r['med dA1']) for r in exh], 2)
    V['HMsExHarmLabels'] = ','.join(sorted({r['label'] for r in exh}))
    V['HMsExHarmP'] = f"{min(float(r['p_Holm A1']) for r in exh):.2f}--{max(float(r['p_Holm A1']) for r in exh):.2f}"
    V['HMsExAr'] = ','.join(sorted({r['label'] for (b, nz, _), r in Fs.items() if b in EXACT + ['SFTF + det'] and nz == 'ar1'}))
    V['HMsConvexAr'] = Fs[('convex FD-FxNLMS', 'ar1', next(c for (b, nz, c) in Fs if b == 'convex FD-FxNLMS'))]['label']
    wd = {(r['method'], r['noise']): r for r in section('final_eval_meas_s_h', 'Distance to the Wiener')}
    V['HMsWienerE'] = '/'.join(f"{num(wd[('E-PCG', nz)]['A2 - bound median (Q1, Q3)']):.2f}" for nz in ('ar1', 'harmonic'))
    V['HMsWienerRls'] = '/'.join(f"{num(wd[('RLS + det', nz)]['A2 - bound median (Q1, Q3)']):.2f}" for nz in ('ar1', 'harmonic'))
    V['HMsWienerFd'] = '/'.join(f"{num(wd[('FD-FxNLMS', nz)]['A2 - bound median (Q1, Q3)']):.2f}" for nz in ('ar1', 'harmonic'))
    V['HMsWienerEone'] = f1(np.mean([num(wd[('E-PCG', nz)]['A2 - bound median (Q1, Q3)']) for nz in ('ar1', 'harmonic')]))
    V['HMsWienerRlsone'] = f1(np.mean([num(wd[('RLS + det', nz)]['A2 - bound median (Q1, Q3)']) for nz in ('ar1', 'harmonic')]))
    wl = [l for l in (R / 'final_eval_meas_s_h/wiener.md').read_text().splitlines() if l.startswith('| ar1 |') or l.startswith('| harmonic |')]
    V['HMsWienerRef'] = '/'.join(f'{float(l.split("|")[2].split()[0]):.1f}' for l in wl)
    # rooms: like-for-like mismatch counts per set
    V['HAgreeMismatch'] = ', '.join(f"{V[f'H{t}AgreeN'] - V[f'H{t}Agree']} ({n})" for t, n in
                                     (('B', 'room B'), ('C', 'room C'), ('Snr', 'SNR 10 dB'), ('Ms', 'M-S'), ('Mp', 'M-P')))
    assert V['HMsLoss'] == 0 and V['HMpLoss'] == 0 and V['HSnrLoss'] == 0
    return V


def macro_name(k):
    assert re.fullmatch(r'[A-Za-z]+', k), k
    return r'\Releven' + k


def main():
    V = generate()
    out = '% Generated from the Revision 11 result summaries by make_r11_values.py; do not edit.\n'
    out += '% Sources: final_eval_holdout_r11, r11_ablation_holdout, protocol_r11_sel, eval_{roomB,roomC,snr10}_h, final_eval_meas_{s,p}_h, final_eval_holdout.\n'
    out += ''.join('\\newcommand{' + macro_name(k) + '}{' + str(v) + '}\n' for k, v in V.items())
    (OUT / 'r11_values.tex').write_text(out)
    for k, v in V.items():
        print(f'{k:24s} {v}')
    print('generated', len(V), 'quantities')


if __name__ == '__main__':
    main()
