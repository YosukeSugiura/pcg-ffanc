"""Revision 11 summaries (Rule 11 Sec. 1.3 metrics / tests / labels, unchanged; families F1, F2, F3).

  ablation      : 11-A, family F2 per variant: (i) variant - G0 (30 tests), (ii) variant vs the 13 baselines (390 tests),
                  (iii) descriptive (G1 - RLS + det) next to (G0 - RLS + det)  -> results/r11_ablation_holdout/
  new           : 11-B / 11-C, family F1 per proposal: 2 x 15 x n_new           -> results/final_eval_holdout_r11/
  rooms <set>   : 11-D roomB | roomC | snr10, family F3 per proposal: 2 x cells x (13 + n_new); bank - main; like-for-like
                  with the 480-519 record (10 common baselines, Holm 160 / 80)   -> results/eval_<set>_h/
  meas <set>    : 11-D meas_s | meas_p (12 common baselines, Holm 48 like-for-like)
Every cell also gets the paired median and the Hodges-Lehmann estimate (median of the Walsh averages) with a 95 %
seed-bootstrap CI (10 000 resamples, numpy default_rng(0) per cell); descriptive only. Existing records and metrics
(results/final_eval_holdout/, eval_*_x2/, final_eval_meas_*_8a/) are only read; the existing families are not recomputed
except for the like-for-like comparison, whose 480-519 labels are checked against the saved summary first.
"""
import json
import sys

import numpy as np

import eval_v2 as ev
import final_eval as fe
import revision11_methods as R

NH = int(R.TT * 8000) // R.H
LABELS = ('win', 'loss', 'mixed', '-')


# ---------------------------------------------------------------- loading
def load_runs(paths, methods, combos, seeds, extra_up=None):
    """Records of `methods` (name -> params must match) -> metrics {(m, nz, sc, sd): {...}}, with the strict checks of
    final_eval.summary (complete, no conflicting duplicates, method-independent uncontrolled power)."""
    by = {}
    for p in paths:
        for r in R.read_jsonl(p):                           # strict: a cut last line means the job did not finish
            m = r['method']
            if m not in methods:
                continue
            if r['prm'] != methods[m]:
                raise ValueError(f'stale record {m}')
            k = (m, r['noise'], r['scen'], r['seed'])
            if k in by:
                if any(by[k][x] != r[x] for x in ('tp', 'up', 'flag_stable')):
                    raise ValueError(f'conflicting duplicate {k}')
                continue
            by[k] = r
    need = {(m, nz, sc, sd) for m in methods for nz, sc in combos for sd in seeds}
    if set(by) != need:
        raise ValueError(f'incomplete records {len(set(by) & need)}/{len(need)}; extra {len(set(by) - need)}')
    full = dict(extra_up or {})
    for r in by.values():
        if len(r['up']) == NH:
            full.setdefault((r['noise'], r['scen'], r['seed']), np.asarray(r['up'], float))
    Mx = {}
    for k, r in by.items():
        u = full.get(k[1:])
        if u is None:
            raise ValueError(f'no full-length uncontrolled power for {k[1:]} (run the fill step)')
        if not np.array_equal(u[:len(r['up'])], np.asarray(r['up'], float)):
            raise ValueError(f'uncontrolled power differs {k}')
        rr = dict(r); rr['tp'] = np.nan_to_num(np.asarray(r['tp'], float), nan=1e30, posinf=1e30).tolist()
        rr['_up_full'] = u
        Mx[k] = fe.metrics(rr, NH)[0]
    return Mx, by


def saved_metrics(path, methods=None):
    out = {}
    for line in path.open():
        r = json.loads(line)
        if methods is None or r['method'] in methods:
            out[(r['method'], r['noise'], r['scen'], r['seed'])] = r
    return out


# ---------------------------------------------------------------- statistics
def hl_ci(d, nboot=10000):
    d = np.asarray(d, float); n = len(d)
    i, j = np.triu_indices(n)
    hl = float(np.median((d[i] + d[j]) / 2))
    rng = np.random.default_rng(0)
    idx = rng.integers(0, n, (nboot, n))
    s = d[idx]
    walsh = (s[:, i] + s[:, j]) / 2
    b = np.median(walsh, axis=1)
    lo, hi = np.quantile(b, [0.025, 0.975])
    return hl, float(lo), float(hi)


def family(Mx, prop, bases, combos, seeds, hl=True):
    """Paired two-sided Wilcoxon (Pratt), Holm over all 2 x len(bases) x len(combos) tests, labels of Sec. 1.3."""
    rows = []
    for b in bases:
        for nz, sc in combos:
            st = {}
            for key in ('A1', 'A2'):
                d = np.array([Mx[(prop, nz, sc, sd)][key] - Mx[(b, nz, sc, sd)][key] for sd in seeds])
                st[key] = {'med': float(np.median(d)), 'p': fe.pval(d), **(dict(zip(('hl', 'lo', 'hi'), hl_ci(d))) if hl else {})}
            fails = [sum(Mx[(m, nz, sc, sd)]['fail'] for sd in seeds) for m in (prop, b)]
            rows.append({'baseline': b, 'noise': nz, 'cell': sc, **{k: v for k, v in st.items()}, 'fail': fails})
    adj = iter(fe.holm([x for r in rows for x in (r['A1']['p'], r['A2']['p'])]))
    cnt = dict.fromkeys(LABELS, 0)
    for r in rows:
        r['A1']['p_holm'] = float(next(adj)); r['A2']['p_holm'] = float(next(adj))
        r['label'] = fe.label(r['A1']['med'], r['A1']['p_holm'], r['A2']['med'], r['A2']['p_holm'])
        cnt[r['label']] += 1
    return rows, cnt


def fam_md(title, rows, cnt):
    out = ['', f'## {title} (Holm over {2 * len(rows)})',
           '| baseline | noise | cell | med dA1 | HL dA1 [95% CI] | p_Holm A1 | med dA2 | HL dA2 [95% CI] | p_Holm A2 | label | fails prop/base |',
           '|---|---|---|---|---|---|---|---|---|---|---|']
    for r in rows:
        a, b = r['A1'], r['A2']
        hl = lambda x: f"{x['hl']:+.2f} [{x['lo']:+.2f}, {x['hi']:+.2f}]" if 'hl' in x else ''
        out.append(f"| {r['baseline']} | {r['noise']} | {r['cell']} | {a['med']:+.2f} | {hl(a)} | {a['p_holm']:.3g} | "
                   f"{b['med']:+.2f} | {hl(b)} | {b['p_holm']:.3g} | {r['label']} | {r['fail'][0]}/{r['fail'][1]} |")
    out += ['', f"Counts: win {cnt['win']}, loss {cnt['loss']}, mixed {cnt['mixed']}, none {cnt['-']} (of {len(rows)})"]
    return out


def diff_family(Mx, a, b, combos, seeds):
    """a - b over cells x {A1, A2} (Holm over 2 x cells), with 'worse' / 'better' flags at the label thresholds."""
    rows = []
    for nz, sc in combos:
        for key in ('A1', 'A2'):
            d = np.array([Mx[(a, nz, sc, sd)][key] - Mx[(b, nz, sc, sd)][key] for sd in seeds])
            h, lo, hi = hl_ci(d)
            rows.append({'noise': nz, 'cell': sc, 'key': key, 'med': float(np.median(d)), 'hl': h, 'lo': lo, 'hi': hi,
                         'p': fe.pval(d)})
    for r, p in zip(rows, fe.holm([r['p'] for r in rows])):
        thr = fe.THR_A1 if r['key'] == 'A1' else fe.THR_A2
        r['p_holm'] = float(p)
        r['flag'] = 'worse' if (p < 0.05 and r['med'] >= thr) else 'better' if (p < 0.05 and r['med'] <= -thr) else '-'
    return rows


def describe(Mx, methods, combos, seeds):
    q = lambda v: f'{np.median(v):.2f} ({np.quantile(v, .25):.2f}, {np.quantile(v, .75):.2f})' if len(v) else 'n/a'
    out = ['', '## A1 / A2 median (Q1, Q3) over seeds (failed runs A1 = A2 = 0 dB); failures; success-only medians',
           '| method | noise | cell | A1 | A2 | failures | A1 success-only | A2 success-only |', '|---|---|---|---|---|---|---|---|']
    for m in methods:
        for nz, sc in combos:
            v = [Mx[(m, nz, sc, sd)] for sd in seeds]; ok = [x for x in v if not x['fail']]
            out.append(f"| {m} | {nz} | {sc} | {q([x['A1'] for x in v])} | {q([x['A2'] for x in v])} | "
                       f"{sum(x['fail'] for x in v)}/{len(v)} | {q([x['A1'] for x in ok])} | {q([x['A2'] for x in ok])} |")
    return out


def saved_labels(path, prop):
    """Labels in a saved final_eval summary.md section '## <prop> vs baselines'."""
    out = {}; on = False
    for line in path.read_text().splitlines():
        if line.startswith('## '):
            on = line.startswith(f'## {prop} vs baselines ')
            continue
        if on and line.startswith('| ') and not line.startswith('| baseline'):
            c = [x.strip() for x in line.strip('|').split('|')]
            if len(c) == 8:
                out[(c[0], c[1], c[2])] = c[7]
    return out


def like_for_like(Mx_new, seeds_new, old_dir, common, combos, old_seeds=tuple(range(480, 520))):
    """Holm over 2 x cells x len(common) in both seed sets (not paired across sets); old labels must equal the saved."""
    old = saved_metrics(old_dir / 'metrics.jsonl')
    out = ['', f'## Like-for-like with {old_dir.name} (seeds 480-519; {len(common)} common baselines; '
               f'Holm over {2 * len(combos) * len(common)})']
    res = {}
    for prop in ('E-PCG', 'E-PCG bank'):
        ro, _ = family(old, prop, common, combos, list(old_seeds), hl=False)
        rn, _ = family(Mx_new, prop, common, combos, list(seeds_new), hl=False)
        saved = saved_labels(old_dir / 'summary.md', prop)
        rec = {(r['baseline'], r['noise'], r['cell']): r['label'] for r in ro}
        if saved != rec:
            raise ValueError(f'recomputed 480-519 labels differ from {old_dir.name}/summary.md ({prop})')
        agree = sum(a['label'] == b['label'] for a, b in zip(ro, rn))
        out += ['', f'### {prop}: agreement {agree}/{len(ro)}',
                '| baseline | noise | cell | 480-519 label | holdout label | 480-519 dA1 / p / dA2 / p | holdout dA1 / p / dA2 / p | fails 480-519 | fails holdout |',
                '|---|---|---|---|---|---|---|---|---|']
        f = lambda r: f"{r['A1']['med']:+.3f} / {r['A1']['p_holm']:.3g} / {r['A2']['med']:+.3f} / {r['A2']['p_holm']:.3g}"
        for a, b in zip(ro, rn):
            if a['label'] != b['label']:
                out.append(f"| {a['baseline']} | {a['noise']} | {a['cell']} | {a['label']} | {b['label']} | {f(a)} | {f(b)} | "
                           f"{a['fail'][0]}/{a['fail'][1]} | {b['fail'][0]}/{b['fail'][1]} |")
        res[prop] = {'agreement': agree, 'total': len(ro)}
    return out, res


def write(out_dir, name, lines, data):
    R.out_path(out_dir)
    (out_dir / f'{name}.md').write_text('\n'.join(lines) + '\n')
    (out_dir / f'{name}.json').write_text(json.dumps(data, indent=1, default=str) + '\n')
    print('\n'.join(lines[:6]), '...', f'-> {out_dir}/{name}.md', flush=True)


# ---------------------------------------------------------------- Sec. 9 item 8 (b): environment-C holdout base
def base():
    if R.HOLDOUT_BASE != 'envC':
        raise ValueError('summary base only with R11_HOLDOUT_BASE=envC')
    meth = {m: v[1] for m, v in {**R.BASE13, **R.PROP}.items()}
    Mx, _ = load_runs(sorted(R.OLD_HOLD.glob('runs_*.jsonl')), meth, R.COMBOS15, R.HOLDOUT)
    R.out_path(R.OLD_HOLD / 'metrics.jsonl').write_text(''.join(json.dumps(v) + '\n' for v in Mx.values()))
    lines = ['# Room-A holdout re-run in environment C (Rule 11 Sec. 9 item 8 (b); the saved 390 family is unchanged)', '']
    data = {}
    for prop in ('E-PCG', 'E-PCG bank'):
        rows, cnt = family(Mx, prop, list(R.BASE13), R.COMBOS15, R.HOLDOUT)
        lines += fam_md(f'{prop} vs the 13 baselines (environment C re-run; reference for Rule 11 only)', rows, cnt)
        data[prop] = {'counts': cnt}
    write(R.OLD_HOLD, 'summary', lines, data)


def room_a_up():
    """Full-length uncontrolled power of the room-A holdout keys from the saved E-PCG main records (the holdout base),
    passed as extra_up so a key whose new rows all stopped early still has its reference (review L-2)."""
    from revision11_holdout import saved_up
    return saved_up()


# ---------------------------------------------------------------- 11-A (F2)
def ablation():
    var = {R.VARIANTS[g][0]: R.VARIANTS[g][1] for g in R.VARIANTS}
    paths = sorted(R.ABL_DIR.glob('runs_*.jsonl'))
    present = {r['method'] for p in paths for r in R.read_jsonl(p)}
    var = {m: v for m, v in var.items() if m in present}
    if 'PCG-WLS (fixed order)' not in var:
        raise ValueError('G1 (required) has no records')
    Mx, by = load_runs(paths, var, R.COMBOS15, R.HOLDOUT, room_a_up())
    old = saved_metrics(R.OLD_HOLD / 'metrics.jsonl')
    Mx.update(old)
    bases = list(R.BASE13)
    lines = ['# Revision 11-A: PCG-WLS ablation on the holdout seeds 800-839 (room A; family F2, Rule 11 Sec. 2.4)', '',
             f'Variants: {list(var)}. G0 = PCG-WLS main (saved holdout record, not re-run).']
    data = {}
    lines += describe(Mx, list(var) + ['E-PCG'], R.COMBOS15, R.HOLDOUT)
    for m in var:
        d0 = diff_family(Mx, m, 'E-PCG', R.COMBOS15, R.HOLDOUT)
        lines += ['', f'## (i) {m} - G0 (Holm over 30)', '| noise | cell | key | median d | HL [95% CI] | p_Holm | flag |', '|---|---|---|---|---|---|---|']
        lines += [f"| {r['noise']} | {r['cell']} | {r['key']} | {r['med']:+.2f} | {r['hl']:+.2f} [{r['lo']:+.2f}, {r['hi']:+.2f}] | {r['p_holm']:.3g} | {r['flag']} |" for r in d0]
        rows, cnt = family(Mx, m, bases, R.COMBOS15, R.HOLDOUT)
        lines += fam_md(f'(ii) {m} vs the 13 baselines', rows, cnt)
        det = [len(by[(m, nz, sc, sd)].get('detections', [])) for nz, sc in R.COMBOS15 for sd in R.HOLDOUT]
        lines += ['', f'Detections of {m}: total {sum(det)}, runs with >= 1: {sum(x > 0 for x in det)}/{len(det)}']
        data[m] = {'minus_G0': d0, 'vs13': rows, 'counts': cnt}
    if 'PCG-WLS (fixed order)' in var:
        lines += ['', '## (iii) G1 - RLS + det next to G0 - RLS + det (paired medians, dB)',
                  '| noise | cell | G1 dA1 | G0 dA1 | G1 dA2 | G0 dA2 |', '|---|---|---|---|---|---|']
        for nz, sc in R.COMBOS15:
            md = lambda a, k: float(np.median([Mx[(a, nz, sc, sd)][k] - Mx[('RLS + det', nz, sc, sd)][k] for sd in R.HOLDOUT]))
            lines.append(f"| {nz} | {sc} | {md('PCG-WLS (fixed order)', 'A1'):+.2f} | {md('E-PCG', 'A1'):+.2f} | "
                         f"{md('PCG-WLS (fixed order)', 'A2'):+.2f} | {md('E-PCG', 'A2'):+.2f} |")
    R.ABL_DIR.mkdir(parents=True, exist_ok=True)
    R.out_path(R.ABL_DIR / 'metrics.jsonl').write_text(''.join(json.dumps(v) + '\n' for k, v in Mx.items() if k[0] in var))
    write(R.ABL_DIR, 'summary', lines, data)


# ---------------------------------------------------------------- 11-B / 11-C (F1)
def new():
    rows_new = R.selected_new()
    Mx, by = load_runs(sorted(R.HOLD_DIR.glob('runs_*.jsonl')), {m: v[1] for m, v in rows_new.items()},
                       R.COMBOS15, R.HOLDOUT, room_a_up())
    Mx.update(saved_metrics(R.OLD_HOLD / 'metrics.jsonl'))
    n_new = len(rows_new)
    lines = ['# Revision 11-B / 11-C: new baselines on the holdout seeds 800-839 (room A; family F1, Rule 11 Sec. 3.5)', '',
             f'n_new = {n_new}: {list(rows_new)}. Proposals and the 13 prespecified baselines: saved holdout records (not re-run);',
             'the 390 family of the 13 baselines is unchanged and not recomputed here.']
    lines += describe(Mx, list(rows_new), R.COMBOS15, R.HOLDOUT)
    data = {'n_new': n_new, 'rows': rows_new}
    for prop in ('E-PCG', 'E-PCG bank'):
        rows, cnt = family(Mx, prop, list(rows_new), R.COMBOS15, R.HOLDOUT)
        lines += fam_md(f'F1: {prop} vs the {n_new} new baselines', rows, cnt)
        data[prop] = {'rows': rows, 'counts': cnt}
    lines += ['', '## New baselines minus RLS + det (paired medians, dB; descriptive)',
              '| baseline | noise | cell | dA1 | dA2 |', '|---|---|---|---|---|']
    for m in rows_new:
        for nz, sc in R.COMBOS15:
            md = lambda k: float(np.median([Mx[(m, nz, sc, sd)][k] - Mx[('RLS + det', nz, sc, sd)][k] for sd in R.HOLDOUT]))
            lines.append(f'| {m} | {nz} | {sc} | {md("A1"):+.2f} | {md("A2"):+.2f} |')
    rls = [m for m in ('RLS', 'RLS + det', 'RLS + CUSUM', 'RLS + det (cond.)') if any(k[0] == m for k in Mx)]
    lines += ['', f'## PCG-WLS minus the best RLS-family member per cell and metric ({rls}; best = lowest median; descriptive)',
              '| noise | cell | best A1 | PCG-WLS - best dA1 | best A2 | PCG-WLS - best dA2 |', '|---|---|---|---|---|---|']
    for nz, sc in R.COMBOS15:
        cells = []
        for k in ('A1', 'A2'):
            best = min(rls, key=lambda m: np.median([Mx[(m, nz, sc, sd)][k] for sd in R.HOLDOUT]))
            d = np.median([Mx[('E-PCG', nz, sc, sd)][k] - Mx[(best, nz, sc, sd)][k] for sd in R.HOLDOUT])
            cells += [best, f'{d:+.2f}']
        lines.append(f'| {nz} | {sc} | ' + ' | '.join(cells) + ' |')
    for m in rows_new:
        rs = [by[(m, nz, sc, sd)] for nz, sc in R.COMBOS15 for sd in R.HOLDOUT]
        if 'sw_log' in rs[0]:
            lines.append(f"- {m}: switches total {sum(len(r['sw_log']) for r in rs)}, mean hops in M "
                         f"{np.mean([r['sw_hops']['M'] for r in rs]):.1f} of {NH}")
        if 'cond_log' in rs[0]:
            n_ev = sum(len(r['cond_log']) for r in rs); n_rs = sum(sum(x[-1] for x in r['cond_log']) for r in rs)
            lines.append(f'- {m}: events {n_ev}, restarts applied {n_rs}')
    R.out_path(R.HOLD_DIR / 'metrics.jsonl').write_text(''.join(json.dumps(v) + '\n' for k, v in Mx.items() if k[0] in rows_new))
    write(R.HOLD_DIR, 'summary', lines, data)


# ---------------------------------------------------------------- 11-D (F3)
COMMON_X2 = ['FD-FxNLMS', 'leaky FD-FxNLMS', 'convex FD-FxNLMS', 'FDKF', 'RLS', 'VFF-RLS', 'FD-FxNLMS + det', 'RLS + det',
             'SFTF-H + det', 'CFTF + det']


def set_summary(out, combos, old_dir, common, title, extra_lines=(), wiener=None):
    from revision11_rooms import all_methods
    meth = {m: v[1] for m, v in all_methods().items()}
    extra = {(r['noise'], r['scen'], r['seed']): np.asarray(r['up'], float) for r in R.read_jsonl(out / 'uncontrolled.jsonl')}
    Mx, by = load_runs(sorted(out.glob('runs_*.jsonl')), meth, combos, R.HOLDOUT, extra)
    bases = [m for m in meth if m not in ('E-PCG', 'E-PCG bank')]
    lines = [f'# {title} (holdout seeds 800-839; family F3, Rule 11 Sec. 5.3)', '',
             f'Baselines ({len(bases)} = 13 + n_new): {bases}.']
    lines += describe(Mx, list(meth), combos, R.HOLDOUT)
    data = {'bases': bases}
    for prop in ('E-PCG', 'E-PCG bank'):
        rows, cnt = family(Mx, prop, bases, combos, R.HOLDOUT)
        lines += fam_md(f'F3: {prop} vs baselines', rows, cnt); data[prop] = {'rows': rows, 'counts': cnt}
    bm = diff_family(Mx, 'E-PCG bank', 'E-PCG', combos, R.HOLDOUT)
    lines += ['', f'## E-PCG bank - E-PCG (main) (Holm over {len(bm)})', '| noise | cell | key | median d | HL [95% CI] | p_Holm |', '|---|---|---|---|---|---|']
    lines += [f"| {r['noise']} | {r['cell']} | {r['key']} | {r['med']:+.2f} | {r['hl']:+.2f} [{r['lo']:+.2f}, {r['hi']:+.2f}] | {r['p_holm']:.3g} |" for r in bm]
    ll, res = like_for_like(Mx, R.HOLDOUT, old_dir, common, combos)
    lines += ll; data['like_for_like'] = res
    r2 = [(m, nz, sum(Mx[(m, nz, sc, sd)]['fail'] for sd in R.HOLDOUT)) for m in meth for nz, sc in combos if sc.startswith('R2')]
    if r2:
        lines += ['', '## R2 failures (runs out of 40)'] + [f'- {m} {nz}: {f}' for m, nz, f in r2]
    if wiener is not None:
        lines += wiener_lines(Mx, wiener, list(meth), combos, R.HOLDOUT)
    lines += list(extra_lines)
    R.out_path(out / 'metrics.jsonl').write_text(''.join(json.dumps(v) + '\n' for v in Mx.values()))
    write(out, 'summary', lines, data)


def rooms(name):
    from revision11_rooms import setup
    room, combos, out = setup(name)
    old = R.RES / {'roomB': 'eval_roomB_x2', 'roomC': 'eval_roomC_x2', 'snr10': 'eval_snr10_x2'}[name]
    set_summary(out, combos, old, COMMON_X2, f'Revision 11-D {name}')


def wiener_distance(Mx, bound, methods, combos, seeds):
    """Rule 11 Sec. 5.3 'distance to the Wiener lower bound (M-S)', descriptive (review L-7): per method and noise, the
    per-seed difference A2(method, seed) - total NR bound(seed, noise) in dB over the successful runs (A2 = NR of the
    last second of the stationary S8 run; the bound is the stationary causal Wiener expectation of Rule 9-D, not an
    adaptive-run guarantee). Returns {(method, noise): (median, Q1, Q3, n successful)}."""
    out = {}
    for m in methods:
        for nz, sc in combos:
            d = [Mx[(m, nz, sc, sd)]['A2'] - bound[(sd, nz)] for sd in seeds if not Mx[(m, nz, sc, sd)]['fail']]
            out[(m, nz)] = ((float(np.median(d)), float(np.quantile(d, .25)), float(np.quantile(d, .75)), len(d))
                            if d else (np.nan, np.nan, np.nan, 0))
    return out


def wiener_bound(out):
    rows = json.loads((out / 'wiener_per_seed.json').read_text())
    return {(r['seed'], nz): float(r['noise'][nz]['total_nr_db']) for r in rows for nz in r['noise']}


def wiener_lines(Mx, bound, methods, combos, seeds):
    wd = wiener_distance(Mx, bound, methods, combos, seeds)
    out = ['', '## Distance to the Wiener lower bound (Rule 11 Sec. 5.3; descriptive)',
           'Per seed: A2 (last 1 s NR) minus the total-NR Wiener bound of the same seed and noise, successful runs only;',
           'median (Q1, Q3) in dB (positive = above the bound).', '',
           '| method | noise | A2 - bound median (Q1, Q3) | successful runs |', '|---|---|---|---|']
    for (m, nz), (md, q1, q3, n) in wd.items():
        out.append(f'| {m} | {nz} | {md:+.2f} ({q1:+.2f}, {q3:+.2f}) | {n}/{len(seeds)} |' if n else f'| {m} | {nz} | n/a | 0/{len(seeds)} |')
    return out


def meas(name):
    from revision11_meas import SETS
    room, combos, out, label = SETS[name]
    old = R.RES / {'meas_s': 'final_eval_meas_s_8a', 'meas_p': 'final_eval_meas_p_8a'}[name]
    extra = []
    if name == 'meas_s' and (out / 'wiener.md').exists():
        extra = ['', (out / 'wiener.md').read_text()]
    bound = wiener_bound(out) if name == 'meas_s' else None
    set_summary(out, combos, old, list(ev.GRID), f'Revision 11-D {label} (MeshRIR, Rule 8a preprocessing)', extra, bound)


if __name__ == '__main__':
    cmd = sys.argv[1]
    if cmd == 'ablation':
        ablation()
    elif cmd == 'base':
        base()
    elif cmd == 'new':
        new()
    elif cmd == 'rooms':
        rooms(sys.argv[2])
    elif cmd == 'meas':
        meas(sys.argv[2])
    else:
        raise ValueError(sys.argv)
