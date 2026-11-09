"""Revision 11-B / 11-C tuning (docs/current/REVISION_RULE_11.md Sec. 1.4, 3.3, 3.4, 4.2, 4.3, 2.6): room A, 15 cells x
the 30 tuning seeds = 450 runs per configuration; admissible <=> no failure (early stop at the first failure); score =
eval_v2.score (mean over cells of the 30-seed mean of (A1 + A2)/2), minimum selected, ties -> lowest index.

Stages (each: SHARD=0/2 and 1/2, single-threaded, environment C):
  B1  MFBLMS (6 steps) and its edge extension (one / two steps outward, Sec. 3.3); repeat 'run B1' until it prints
      'B1: nothing to run' (the extension points are defined only once the base grid is complete)
  B2  MFBLMS + det (7), switching FD-FxNLMS [6] (Z-A, 6), switching FD-FxNLMS + det (Z-B, 6); needs B1 selected
      (MFBLMS without an admissible step: the three groups are reported as inadmissible and B2 has no run; Rule 11a
      Sec. 4)
  C   RLS + det (cond.) (4), RLS + det + growth and RLS + det + growth (from start) (1 each, admissibility; Rule 11a
      Sec. 2.2), outer points of Sec. 4.2 (required RLS / VFF-RLS / SFTF-H first, then the optional points; second
      steps are added when a first step is better by > 0.01 dB; repeat 'run C' until 'C: nothing to run')
A group without an admissible configuration is listed in selected.json 'inadmissible' (reported, not evaluated) and
does not stop the selection (Rule 11a Sec. 4).
usage:
  RLS_FAST=1 OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 SHARD=0/2 python experiments/revision11_select.py run B1
  python experiments/revision11_select.py summary        # selection.md, selected.json (complete flag when all done)
  python experiments/revision11_select.py provenance B1|B2|C   # provenance_<stage>.json (never overwritten)
Output: results/protocol_r11_sel/ only (results/det_events/ is read; missing keys -> det_events_<shard>.jsonl here).
"""
import json
import os
import sys
import zlib

import numpy as np

import eval_v2 as ev
import revision11_methods as R

OUT = R.SEL_DIR
TOL = 0.01                                 # dB, Sec. 4.2 (equal within 0.01 dB)


def _records(mode='skip'):
    """All tuning records. A worker reads the other shard's file while it may be appending: a cut last line there is
    skipped (its owner drops it and redoes the run on its next start, review M-4); the summary reads strictly."""
    rs = []
    for f in sorted(OUT.glob('runs_*.jsonl')):
        rs.extend(R.read_jsonl(f, mode))
    seen = set()
    for r in rs:
        k = (r['group'], r['cfg'], r['noise'], r['scen'], r['seed'])
        if k in seen:
            raise ValueError(f'duplicate record {k}')
        seen.add(k)
    return rs


def _status(rs, group, idx, prm):
    """('fail', first failure) | ('done', score) | ('open', n) for one configuration."""
    rows = [r for r in rs if r['group'] == group and r['cfg'] == idx]
    if any(r['prm'] != prm for r in rows):
        raise ValueError(f'stale configuration {group} {idx}')
    bad = [r for r in rows if r['fail']]
    if bad:
        return 'fail', (bad[0]['noise'], bad[0]['scen'], bad[0]['seed'])
    need = {(nz, sc, sd) for nz, sc in R.COMBOS15 for sd in R.TUNE}
    if {(r['noise'], r['scen'], r['seed']) for r in rows} == need:
        return 'done', ev.score(rows)
    return 'open', len(rows)


def _select(rs, group, cfgs):
    """Selected index (min score, ties min index) among complete admissible configurations; None if any open or none."""
    st = [_status(rs, group, i, prm) for i, (_, prm) in enumerate(cfgs)]
    if any(s == 'open' for s, _ in st):
        return None, st
    ok = [(v, i) for i, (s, v) in enumerate(st) if s == 'done']
    return (min(ok)[1] if ok else 'none'), st


# ---------------------------------------------------------------- configuration lists (deterministic given the records)
def mfblms_cfgs(rs):
    kind, grid = R.GRID11['MFBLMS']
    cfgs = [(kind, p) for p in grid]
    for _ in range(2):                                      # at most two steps outward (Sec. 3.3 / 4.2)
        sel, _ = _select(rs, 'MFBLMS', cfgs)
        if sel in (None, 'none'):
            break
        mu = cfgs[sel][1]['mu']
        nxt = None
        for edge, steps in R.MU_EDGE.items():
            chain = (edge,) + steps
            if mu in chain[:-1] and mu == [c for c in chain if c in [p['mu'] for _, p in cfgs]][-1]:
                nxt = chain[chain.index(mu) + 1]
        if nxt is None or any(p['mu'] == nxt for _, p in cfgs):
            break
        cfgs.append((kind, {'mu': nxt, 'mod': True}))
    return cfgs


def mfblms_selected(rs):
    cfgs = mfblms_cfgs(rs)
    sel, st = _select(rs, 'MFBLMS', cfgs)
    if sel is None:
        return None
    if sel == 'none':
        return 'none'
    # selection final only when no further edge point is pending
    if len(mfblms_cfgs(rs)) != len(cfgs):
        return None
    return cfgs[sel][1]['mu']


def outer_groups():
    """[(base, [(kind, prm), ...] first-step points, [second steps] or None)]"""
    out = [(b, [pts[0]], [pts[1]]) for b, pts in R.OUTER.items()]
    out += [(b, pts, None) for b, pts in R.OUTER_OPT.items()]
    return out


def current_class():
    """Rule 11b Sec. 2.2 class of this machine's env_C.json (I or K; stops on F / missing / foreign)."""
    return R.env_class()


def reference_group(base):
    return f'{base} [reference]'


def outer_decision(rs, base, first, second, ref_bases=()):
    """Sec. 4.2 decision for one base; returns dict (status 'open' while runs are missing).

    Reference (Rule 11b Sec. 4 (b), (b')): for a base in ref_bases the existing selected configuration BASE13[base] is
    re-run in this environment (group '<base> [reference]', 450 runs) and its score replaces the recorded score as the
    reference; otherwise the recorded score (EXISTING_SCORE). The decision rules (failure / interior / better by
    > 0.01 dB / second step) are unchanged. A failing reference stops (Rule 11b Sec. 4, last item)."""
    g1 = f'{base} [outer 1]'
    s1 = [_status(rs, g1, i, p) for i, (_, p) in enumerate(first)]
    recorded = R.EXISTING_SCORE[base]
    if any(s == 'open' for s, _ in s1):
        return {'status': 'open', 'existing_score': recorded}   # first step not run yet (e.g. summary after B1)
    ok = [(v, i) for i, (s, v) in enumerate(s1) if s == 'done']
    d = {'existing_score': recorded}
    if base in ref_bases:
        st, val = _status(rs, reference_group(base), 0, R.BASE13[base][1])
        if st == 'open':
            d.update(status='open', waiting_reference=reference_group(base)); return d
        if st == 'fail':
            raise ValueError(f'reference re-run of the existing selection failed: {base} {val} '
                             '(environment mismatch beyond class K; stop, Rule 11b Sec. 4)')
        ref = val
        d.update(reference_score=ref, reference_source='rerun', reference_minus_recorded=ref - recorded)
    else:
        ref = recorded
        d.update(reference_score=ref, reference_source='recorded')
    d['first'] = [{'prm': p, 'result': s, 'value': v} for (_, p), (s, v) in zip(first, s1)]
    if not ok:
        d.update(status='done', decision='edge (outer point not admissible)', row=None); return d
    v, i = min(ok)
    if v >= ref - TOL:
        d.update(status='done', decision='interior (outer point not better by > 0.01 dB)', row=None); return d
    row = first[i]; d['decision'] = 'better: extended-grid row'
    if second is None:
        d.update(status='done', row={'kind': row[0], 'params': row[1], 'score': v},
                 note='Rule 11 defines no second step for this base: not run (report to the author)')
        return d
    g2 = f'{base} [outer 2]'
    s2 = [_status(rs, g2, j, p) for j, (_, p) in enumerate(second)]
    d['second'] = [{'prm': p, 'result': s, 'value': x} for (_, p), (s, x) in zip(second, s2)]
    if any(s == 'open' for s, _ in s2):
        d.update(status='open', pending=g2); return d
    ok2 = [(x, j) for j, (s, x) in enumerate(s2) if s == 'done']
    if ok2 and min(ok2)[0] < v - TOL:                       # second step better than the first by > 0.01 dB
        x, j = min(ok2); row = second[j]; v = x
        d['second_decision'] = 'better than the first step: row uses the second step (maximum two steps reached)'
    else:
        d['second_decision'] = 'failed' if not ok2 else 'not better than the first step'
    d.update(status='done', row={'kind': row[0], 'params': row[1], 'score': v})
    return d


def stage_cfgs(stage, rs, cls=None):
    """[(group, idx, kind, prm)] currently defined for a stage (cls: env_C class, read when needed)."""
    out = []
    if stage == 'B1':
        out = [('MFBLMS', i, k, p) for i, (k, p) in enumerate(mfblms_cfgs(rs))]
    elif stage == 'B2':
        mu = mfblms_selected(rs)
        if mu is None:
            raise ValueError('B2 needs a final MFBLMS selection (finish B1)')
        if mu == 'none':                                    # Rule 11a Sec. 4: reported, not evaluated; B2 has no run
            return []
        for g, (k, grid) in R.dependent_grids(mu).items():
            out += [(g, i, k, p) for i, p in enumerate(grid)]
    elif stage == 'C':
        # order (Rule 11a Sec. 5.3): required (GRID11 groups, outer RLS / VFF-RLS / SFTF-H) -> optional outer points ->
        # second steps that a first step triggered
        for g in R.GROUPS_C:
            k, grid = R.GRID11[g]; out += [(g, i, k, p) for i, p in enumerate(grid)]
        for base, first, second in outer_groups():
            out += [(f'{base} [outer 1]', i, k, p) for i, (k, p) in enumerate(first)]
        # Rule 11b Sec. 4: references after the optional points (RLS + CUSUM always, the other 7 bases in class K)
        refs = R.reference_bases(cls or current_class())
        for base in refs:
            k, p = R.BASE13[base]; out.append((reference_group(base), 0, k, p))
        for base, first, second in outer_groups():          # second steps last: earlier positions stay fixed
            if second is not None:
                d = outer_decision(rs, base, first, second, refs)
                if d.get('pending') or 'second' in d:
                    out += [(f'{base} [outer 2]', j, k, p) for j, (k, p) in enumerate(second)]
    else:
        raise ValueError(stage)
    return out


def run_e0():
    """Rule 11b Sec. 4 (c), stage E0 (class K only): E-PCG main on the 450 tuning keys in this environment ->
    det_events_env_<shard>.jsonl; the tuning then reads only these events (tuning_events(source='env'))."""
    shard = int(os.environ['SHARD'].split('/')[0])
    if current_class() != 'K':
        print('E0: nothing to run (class I: the cached events are used)', flush=True); return
    path = R.out_path(OUT / f'det_events_env_{shard}.jsonl')
    have = {(r['noise'], r['scen'], r['seed']) for r in R.read_jsonl(path, 'repair')}
    keys = [(nz, sc, sd) for sd in R.TUNE for nz, sc in R.COMBOS15
            if zlib.crc32('|'.join(map(str, (nz, sc, sd))).encode()) % 2 == shard and (nz, sc, sd) not in have]
    if not keys:
        print('E0: nothing to run', flush=True); return
    with path.open('a') as fh:
        for nz, sc, sd in keys:
            _, own = R.run_record('E-PCG', *R.PROP['E-PCG'], 'A', nz, sc, sd)
            fh.write(json.dumps({'room': 'A', 'noise': nz, 'scen': sc, 'seed': sd, 'events': own}) + '\n'); fh.flush()
    print('E0', shard, 'complete', len(keys), flush=True)


def stage_events(stage, cls):
    """Events for a tuning stage: class K -> the complete E0 set (stop if incomplete); class I -> the cache."""
    if cls != 'K':
        return R.tuning_events(source='cache')
    ev_env = R.tuning_events(source='env')
    need = {(nz, sc, sd) for nz, sc in R.COMBOS15 for sd in R.TUNE}
    if set(ev_env) != need:
        raise ValueError(f'{stage}: stage E0 incomplete ({len(set(ev_env) & need)}/{len(need)}); run E0 first')
    return ev_env


# ---------------------------------------------------------------- run
COST = {'R-RLS': 1.0, 'R-VFF': 1.2, 'R-SFTF': 0.4, 'E-PCG-F': 0.1}


def assign(cfgs):
    """Greedy two-shard assignment by a rough cost per kind, in list order (lists only grow at the end, so earlier
    assignments never change)."""
    load = [0.0, 0.0]; owner = []
    for g, i, kind, prm in cfgs:
        s = 0 if load[0] <= load[1] else 1
        owner.append(s); load[s] += COST.get(kind, 0.05)
    return owner


def run(stage):
    R.check_runtime_env('C')
    shard, total = map(int, os.environ['SHARD'].split('/'))
    if total != 2 or shard not in (0, 1):
        raise ValueError('expected SHARD 0/2 or 1/2')
    R.out_path(OUT).mkdir(parents=True, exist_ok=True)
    if stage == 'E0':
        return run_e0()
    cls = current_class()
    for f in [OUT / f'det_events_{shard}.jsonl', *sorted(OUT.glob(f'runs_*_{shard}.jsonl'))]:
        R.read_jsonl(f, 'repair')                           # own files: drop a cut last line (M-4)
    rs = _records()
    cfgs = stage_cfgs(stage, rs, cls)
    # shard by the position in the full (stable) configuration list, so both shards agree whatever has finished
    owner = assign(cfgs)
    todo = [(owner[pos], c) for pos, c in enumerate(cfgs) if _status(rs, c[0], c[1], c[3])[0] == 'open']
    if not todo:
        print(f'{stage}: nothing to run', flush=True); return
    events = stage_events(stage, cls)
    path = OUT / f'runs_{stage}_{shard}.jsonl'
    evpath = OUT / f'det_events_{shard}.jsonl'
    done = {(r['group'], r['cfg'], r['noise'], r['scen'], r['seed']) for r in rs}
    bad = {(r['group'], r['cfg']) for r in rs if r['fail']}
    with path.open('a') as out:
        for pos, (g, i, kind, prm) in todo:
            if pos != shard:
                continue
            for sd in R.TUNE:                                   # seed-major: a failure is found early
                if (g, i) in bad:
                    break
                for nz, sc in R.COMBOS15:
                    if (g, i, nz, sc, sd) in done:
                        continue
                    key = (nz, sc, sd); evs = None
                    if R.needs_events(g, kind, prm):
                        if key not in events:                   # class I, new key: E-PCG main, cached here only
                            r0, own = R.run_record('E-PCG', *R.PROP['E-PCG'], 'A', nz, sc, sd)
                            with evpath.open('a') as fh:
                                fh.write(json.dumps({'room': 'A', 'noise': nz, 'scen': sc, 'seed': sd, 'events': own}) + '\n')
                            events[key] = own
                        evs = events[key]
                    rec, _ = R.run_record(g, kind, prm, 'A', nz, sc, sd, evs)
                    m = R.metrics_of(rec)
                    small = {'group': g, 'cfg': i, 'kind': kind, 'prm': prm, 'noise': nz, 'scen': sc, 'seed': sd,
                             **m, 'n_events': rec.get('n_events'), 'n_restarts_applied': len(rec.get('restart_hops', [])),
                             'sw_switches': len(rec.get('sw_log', [])), 'wall_s': rec['wall_s']}
                    if not all(np.isfinite([m['A1'], m['A2']])):
                        raise ValueError(f'non-finite metric {g} {i} {key}')
                    out.write(json.dumps(small) + '\n'); out.flush()
                    if m['fail']:
                        bad.add((g, i)); break
            print(stage, shard, g, i, 'failed' if (g, i) in bad else 'complete', flush=True)


# ---------------------------------------------------------------- summary
def summary():
    rs = _records('strict')
    lines = ['# Revision 11 tuning (room A, tuning seeds 300-309 + 600-619; Rule 11 Sec. 1.4)', '',
             '| group | config | params | result |', '|---|---|---|---|']
    data = {'groups': {}, 'outer': {}, 'new_rows': {}, 'inadmissible': [], 'complete': False, 'stages': {}}

    def table(g, cfgs):
        sel, st = _select(rs, g, cfgs)
        for i, ((k, p), (s, v)) in enumerate(zip(cfgs, st)):
            res = f'{v:.4f}' if s == 'done' else (f'fail {v}' if s == 'fail' else f'open ({v}/450)')
            lines.append(f'| {g} | {i}{" (selected)" if sel == i else ""} | {json.dumps(p)} | {res} |')
        data['groups'][g] = {'kind': cfgs[0][0], 'grid': [p for _, p in cfgs],
                             'status': [[s, v] for s, v in st], 'selected': sel,
                             'params': cfgs[sel][1] if isinstance(sel, int) else None,
                             'score': st[sel][1] if isinstance(sel, int) else None}
        return sel

    b1 = mfblms_cfgs(rs); table('MFBLMS', b1)
    mu = mfblms_selected(rs)
    data['stages']['B1'] = mu is not None
    if mu not in (None, 'none'):
        allb2 = True
        for g, (k, grid) in R.dependent_grids(mu).items():
            sel = table(g, [(k, p) for p in grid]); allb2 &= sel is not None
        data['stages']['B2'] = allb2
    elif mu == 'none':                                       # Rule 11a Sec. 4: B2 complete without runs
        data['stages']['B2'] = True
        for g in R.dependent_grids(0.1):
            data['inadmissible'].append({'group': g, 'reason': 'MFBLMS has no admissible step'})
    else:
        data['stages']['B2'] = False
    allc = True
    for g in R.GROUPS_C:
        k, grid = R.GRID11[g]; sel = table(g, [(k, p) for p in grid]); allc &= sel is not None
    cls = current_class(); refs = R.reference_bases(cls)
    data['env_class'] = cls; data['reference_bases'] = refs
    data['references'] = {}
    for base in refs:                                        # Rule 11b Sec. 4 (b), (b'): re-run existing selections
        k, p = R.BASE13[base]; table(reference_group(base), [(k, p)])
        data['references'][base] = data['groups'].pop(reference_group(base))   # not a new row, not inadmissible
    lines += ['', f'## Outer grid points (Sec. 4.2; reference = recorded score, or the re-run in this environment for '
                  f'{refs}; env_C class {cls}, Rule 11b Sec. 4)', '',
              '| base | recorded score | re-run score (this environment) | re-run - recorded | reference used | decision |',
              '|---|---|---|---|---|---|']
    details = []
    for base, first, second in outer_groups():
        d = outer_decision(rs, base, first, second, refs); data['outer'][base] = d
        allc &= d['status'] == 'done'
        rec = d.get('existing_score', R.EXISTING_SCORE[base])
        rr = d.get('reference_score') if d.get('reference_source') == 'rerun' else None
        rr_s = '' if rr is None else f'{rr:.4f}'
        df_s = '' if rr is None else f'{rr - rec:+.4f}'
        lines.append(f"| {base} | {rec:.4f} | {rr_s} | {df_s} | {d.get('reference_source', 'pending')} | "
                     f"{d.get('decision', d['status'])} |")
        details.append(f'- {base}: {json.dumps(d)}')
    lines += [''] + details
    data['stages']['C'] = allc
    # Rule 11b Sec. 4 (c): events of stage E0 against the cache (descriptive)
    ev_env = R.tuning_events(source='env')
    if ev_env:
        cache = R.tuning_events(source='cache')
        common = sorted(set(ev_env) & set(cache))
        diff = [k for k in common if ev_env[k] != cache[k]]
        data['e0'] = {'keys': len(ev_env), 'compared_with_cache': len(common), 'differing': [list(k) for k in diff]}
        lines += ['', '## Stage E0 events vs the cache (Rule 11b Sec. 4 (c); descriptive)', '',
                  f'- E0 keys {len(ev_env)}; compared with the cache {len(common)}; differing {len(diff)}: {diff}']
    # n_new rows (Sec. 3.5): admissible new baselines with their selected configuration
    for g, v in data['groups'].items():
        if isinstance(v['selected'], int):
            data['new_rows'][g] = {'kind': v['kind'], 'params': v['params'], 'score': v['score']}
    for base, d in data['outer'].items():
        if d.get('status') == 'done' and d.get('row'):
            data['new_rows'][f'{base} (extended grid)'] = d['row']
    # Rule 11a Sec. 4: a group without an admissible configuration is reported and not evaluated (not a stop)
    own = [{'group': g, 'reason': 'no admissible configuration',
            'failures': {str(i): v for i, (st, v) in enumerate(d['status']) if st == 'fail'}}
           for g, d in data['groups'].items() if d['selected'] == 'none']
    data['inadmissible'] = own + data['inadmissible']
    data['complete'] = all(data['stages'].get(s) for s in ('B1', 'B2', 'C'))
    if data['inadmissible']:
        lines += ['', '## Groups without an admissible configuration (reported, not evaluated; Rule 11a Sec. 4)', '']
        lines += [f"- {x['group']}: {x['reason']}" + (f" (first failure per configuration: {x['failures']})"
                                                       if x.get('failures') else '') for x in data['inadmissible']]
    lines += ['', f"Stages complete: {data['stages']}; n_new = {len(data['new_rows'])} rows: {list(data['new_rows'])}"]
    R.out_path(OUT).mkdir(parents=True, exist_ok=True)
    (OUT / 'selection.md').write_text('\n'.join(lines) + '\n')
    (OUT / 'selected.json').write_text(json.dumps(data, indent=1) + '\n')
    print('\n'.join(lines))


if __name__ == '__main__':
    if sys.argv[1] == 'run':
        run(sys.argv[2])
    elif sys.argv[1] == 'summary':
        summary()
    elif sys.argv[1] == 'provenance':                      # one file per stage (review L-3): provenance_<stage>.json
        stage = sys.argv[2]
        if stage not in ('B1', 'B2', 'C'):
            raise ValueError(stage)
        R.check_env('C')
        R.provenance(OUT, {'stage': f'tuning {stage}', 'seeds': R.TUNE}, [__file__], name=f'provenance_{stage}')
    else:
        raise ValueError(sys.argv)
