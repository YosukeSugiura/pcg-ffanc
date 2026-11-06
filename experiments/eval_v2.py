"""Revision experiments after the strict TASLP review (2026-10-30; rule docs/current/REVISION_RULE.md, fixed before running).

Stages
  select : baseline (re)selection on the tuning seeds with an A1-aligned score, extended FD grids and two
           detector-equipped baselines (shared change events of the proposed method).
  final  : evaluation-seed runs of the selected baselines + the proposed methods (EVAL_SET = main | roomB | roomC | snr10),
           summarized with experiments/final_eval.py (same metrics, tests, figures).
Detector-equipped baselines ('... + det'): at every detection of the proposed method on the same run (stop sample and
localized change point tau, results/det_events/), RLS resets P and replays [tau, stop); 'FD-FxNLMS + det' (V-SCHED,
FD-FxNLMS with the circulant-RLS step schedule mu_b = scale N / (H b) floored at mu_min, cumulative bin power) restarts
its schedule at tau. Both therefore use exactly the detections of PCG-WLS (computed on PCG-WLS's own closed loop): same detections, but the
baselines restart naively (no Prop. 9 weighting, no growing controller length), so the comparison is 'same detector,
baseline-type restart' rather than an isolation of the estimator. det_reset_w: the restart
also sets the controller to zero (cold start) instead of keeping it (warm start); both variants are in the grids.
usage:
  RLS_FAST=1 SHARD=0/2 PART=_a python experiments/eval_v2.py select-run ; ... SHARD=1/2 PART=_b ... ;
  python experiments/eval_v2.py select-summary
  RLS_FAST=1 EVAL_SET=main SHARD=0/2 PART=_a python experiments/eval_v2.py final-run ; ... ; EVAL_SET=main python experiments/eval_v2.py final-summary
  EVAL_SET=main python experiments/eval_v2.py reuse      # copy unchanged-configuration records of results/final_eval
  SELOUT=_c python experiments/eval_v2.py select-summary ; EVAL_SET=main_c ... reuse / final-run / final-summary  (REVISION_RULE_4)
  UNCONTROLLED_FILL=1 EVAL_SET=roomC python experiments/eval_v2.py final-summary   # required for roomC (one run where
      every method stopped early; see uncontrolled_fill); a no-op elsewhere
Shards actually used (2026-10-30): selection PART _a/_b/_c; final main _p, _q; rooms shard 0/2 _a; shard 1/2 = SHARD 1/4
_x1 + 3/4 _x3 ([working branch], merged) and snr10 1/2 _z (duplicates of _x*, identical); rooms 'RLS + det' SHARD 0/2
_y0, 1/2 _y1 ([working branch], merged). Never run two processes with the same PART at the same time.
"""
import json, os, sys, time, zlib
from pathlib import Path
import numpy as np
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src')); sys.path.insert(0, str(ROOT / 'experiments'))
import final_eval as FE  # noqa: E402
SD = FE.SD; D = FE.D
M = 512; TT = 5.0; H = 128
TUNE = list(range(300, 310)) + list(range(600, 620)); EVAL = list(range(480, 520))
CELLS = FE.CELLS; NOISES = FE.NOISES; COMBOS15 = FE.COMBOS
MAIN = json.loads((ROOT / 'results/final_dev/final_config_core_main.json').read_text())['flags']
BANK = json.loads((ROOT / 'results/final_dev/final_config_core_final.json').read_text())['flags']

GRID = {
    'FD-FxNLMS': ('fixed_binwise', [{'mu': mu} for mu in (0.05, 0.1, 0.15, 0.2, 0.25, 0.3)]),
    'leaky FD-FxNLMS': ('leaky_binwise', [{'mu': mu, 'leak': lk} for mu in (0.1, 0.2, 0.35) for lk in (1e-3, 1e-2)]),
    'convex FD-FxNLMS': ('convex_binwise', [{'mu_fast': a, 'mu_slow': b, 'mu_a': 1.0} for a, b in
                                            ((0.9, 0.35), (0.8, 0.1), (0.5, 0.1), (0.5, 0.2), (0.35, 0.05), (0.35, 0.1))]),
    'FDKF': ('C-FDKF', [{'P0': p0, 'gain_scale': 4.0, 'A': a} for a in (0.998, 0.9995, 0.9999) for p0 in (10.0, 30.0)]),
    'RLS': ('R-RLS', [{'lam': lm, 'delta': 1e-2} for lm in (0.9995, 0.9998, 0.9999)]),
    'VFF-RLS': ('R-VFF', [{'N0': n0, 'lam_min': 0.9995, 'delta': 1e-3} for n0 in (500.0, 2000.0)]),
    'FD-FxNLMS + det': ('V-SCHED', [{'denom': 'cum', 'scale': 0.25, 'mu_min': 0.2, 'det_reset_w': True},
                                    {'denom': 'cum', 'scale': 0.25, 'mu_min': 0.2, 'det_reset_w': False},
                                    {'denom': 'cum', 'scale': 0.125, 'mu_min': 0.2, 'det_reset_w': True},
                                    {'denom': 'cum', 'scale': 0.25, 'mu_min': 0.1, 'det_reset_w': True},
                                    {'denom': 'rls', 'scale': 0.25, 'mu_min': 0.0, 'det_reset_w': True},
                                    {'denom': 'rls', 'scale': 0.25, 'mu_min': 0.0, 'det_reset_w': False},
                                    # appended 2026-10-30 after the review (before they ran): a moderate step boost after a
                                    # detection that decays to the FD-FxNLMS step 0.2 (mu_b = max(8 scale / (b + 1), 0.2))
                                    {'denom': 'cum', 'scale': 0.125, 'mu_min': 0.2, 'det_reset_w': False},
                                    {'denom': 'cum', 'scale': 0.0625, 'mu_min': 0.2, 'det_reset_w': False}]),
    'RLS + det': ('R-RLS', [{'lam': lm, 'delta': 1e-2, 'det_reset_w': rw} for lm in (0.9999, 1.0) for rw in (True, False)]
                  # appended 2026-10-30 (review N2, docs/current/REVISION_RULE_2.md, before they ran): regularization of the
                  # reset P ('det_delta'; initial delta unchanged), warm / cold
                  + [{'lam': 0.9999, 'delta': 1e-2, 'det_reset_w': rw, 'det_delta': dd} for dd in (0.1, 1.0) for rw in (False, True)]),
    # (2026-10-30, review N1, REVISION_RULE_2.md) the selected FD-FxNLMS (mu 0.3) + restart at PCG-WLS's detections: step boost
    # mu_b = max(0.3, s (N / H) / (b_since + 1)) (s = 1/16, 1/8, 1/4: 1, 3, 6 boosted hops), warm or cold; cold s = 0 is a
    # plain restart. Identical to FD-FxNLMS on runs without detections.
    'FD-FxNLMS + restart': ('fixed_binwise', [{'mu': 0.3, 'det_boost': sb, 'det_reset_w': False} for sb in (0.0625, 0.125, 0.25)]
                            + [{'mu': 0.3, 'det_boost': sb, 'det_reset_w': True} for sb in (0.0, 0.0625, 0.125, 0.25)]),
    # (2026-10-31, REVISION_RULE_4.md) stabilized FTF restarted at PCG-WLS's detections (prewindowed restart); mirrors
    # RLS + det configurations 0-3
    'SFTF + det': ('R-SFTF', [{'lam': lm, 'delta': 1e-2, 'det_reset_w': rw} for lm in (0.9999, 1.0) for rw in (True, False)]),
    # (2026-10-31, REVISION_RULE_6.md) exact covariance restart: RLS for T_h samples after a detection, then FTF
    'SFTF-H + det': ('R-SFTF', [{'lam': 0.9999, 'delta': 1e-2, 'det_reset_w': False, 'hybrid': th} for th in (512, 1024, 2048)]),
    # (2026-10-31, REVISION_RULE_7.md) covariance-window FTF restarted at the detections (O(M))
    'CFTF + det': ('R-SFTF', [{'lam': lm, 'delta': 1e-2, 'det_reset_w': rw, 'cov': True} for lm in (0.9999, 1.0) for rw in (True, False)]),
}
BASE = list(GRID)
DET = {'FD-FxNLMS + det', 'RLS + det', 'FD-FxNLMS + restart', 'SFTF + det', 'SFTF-H + det', 'CFTF + det'}


def score(rs):
    """Selection score (lower = better): mean over the cell x noise combinations of the mean over seeds of (A1 + A2) / 2."""
    by = {}
    for r in rs:
        by.setdefault((r['noise'], r['scen']), []).append(0.5 * (r['A1'] + r['A2']))
    return float(np.mean([np.mean(v) for v in by.values()]))


# ---------------------------------------------------------------- rooms / conditions
ROOMS = {'A': {}, 'B': {'ism_rt60': 0.15, 'ism_max_order': 30, 'len_p': 1200, 'len_s': 512},
         'C': {'ism_rt60': 0.3, 'ism_max_order': 30, 'len_p': 2400, 'len_s': 1024},
         'A_snr10': {'secondary_noise_snr_db': 10.0},
         'M': {'path_source': 'meshrir', 'len_p': 1200, 'len_s': 512, 'move_steps': 0},
         'M_8a': {'path_source': 'meshrir', 'len_p': 1200, 'len_s': 512, 'move_steps': 0, 'meshrir_d0': 5434}}
EVAL_SETS = {
    'meas_p_8a': ('M_8a', [(nz, 'S2 src 30cm') for nz in NOISES], ROOT / 'results/final_eval_meas_p_8a'),
    'meas_ps_8a': ('M_8a', [(nz, 'R2 rig 30cm') for nz in NOISES], ROOT / 'results/final_eval_meas_ps_8a'),
    'meas_p': ('M', [(nz, 'S2 src 30cm') for nz in NOISES], ROOT / 'results/final_eval_meas_p'),
    'meas_ps': ('M', [(nz, 'R2 rig 30cm') for nz in NOISES], ROOT / 'results/final_eval_meas_ps'),
    'main': ('A', COMBOS15, ROOT / 'results' / 'final_eval_v2'),
    'roomB': ('B', [(nz, sc) for nz in NOISES for sc in ('S8 stationary', 'S2 src 30cm', 'S5 src 30cm cont', 'R2 rig 30cm')], ROOT / 'results' / 'eval_roomB'),
    'roomC': ('C', [(nz, sc) for nz in NOISES for sc in ('S8 stationary', 'S2 src 30cm', 'S5 src 30cm cont', 'R2 rig 30cm')], ROOT / 'results' / 'eval_roomC'),
    # (2026-10-30, REVISION_RULE_2.md) main room with the N1 / N2 baselines (SELFILE=selected_b.json); records of
    # final_eval_v2 with an identical configuration are copied (EVAL_SET=main_b ... reuse)
    'main_b': ('A', COMBOS15, ROOT / 'results' / 'final_eval_v2b'),
    # (2026-10-31, REVISION_RULE_4.md) + SFTF + det (SELFILE default selected_c.json); v2b records copied
    'main_c': ('A', COMBOS15, ROOT / 'results' / 'final_eval_v2c'),
    'main_d': ('A', COMBOS15, ROOT / 'results' / 'final_eval_v2d'),   # (2026-10-31, REVISION_RULE_6.md)
    'main_e': ('A', COMBOS15, ROOT / 'results' / 'final_eval_v2e'),   # (2026-10-31, REVISION_RULE_7.md)
    'snr10': ('A_snr10', [(nz, sc) for nz in NOISES for sc in ('S8 stationary', 'S2 src 30cm')], ROOT / 'results' / 'eval_snr10'),
}


def cfg_of(room, nz, sc):
    cfg = dict(D.SCEN[sc], controller_length=M, fft_length=2 * M, **ROOMS[room], **({} if nz == 'ar1' else {'noise_type': nz}))
    if room in ('M', 'M_8a'):
        cfg['move_target'] = 'source' if sc.startswith('S2') else 'mic'
    return cfg


def read_jsonl(p):
    return FE.read_jsonl(p)[0] if p.exists() else []


# ---------------------------------------------------------------- shared detection events
EVD = ROOT / 'results' / 'det_events'; EVD.mkdir(parents=True, exist_ok=True)
_EV = None
# (M5) the cache key holds no configuration hash: the main configuration is frozen (final_config_core_main.json);
# delete results/det_events/ if it ever changes.


def events(room, nz, sc, sd):
    """[[stop, tau], ...] of the proposed method (main configuration) on this run; cached in results/det_events/."""
    global _EV
    if _EV is None:
        _EV = {}
        for f in EVD.glob('*.jsonl'):
            for r in read_jsonl(f):
                _EV[(r['room'], r['noise'], r['scen'], r['seed'])] = r['events']
    k = (room, nz, sc, sd)
    if k not in _EV:
        ch = not sc.startswith('S8')
        r = D.P.run(cfg_of(room, nz, sc), sd, 'PCG-WLS-F', dict(MAIN), TT, D.CH if ch else None)
        ev = [[(int(h) + 1) * H, int(t)] for h, t in zip(r['reset_hops'], r['loc_hist'])]
        assert len(r['reset_hops']) == len(r['loc_hist']), 'detections and localizations must be aligned'
        _EV[k] = ev
        with (EVD / f"ev{os.environ.get('PART', '')}.jsonl").open('a') as fh:
            fh.write(json.dumps({'room': room, 'noise': nz, 'scen': sc, 'seed': sd, 'events': ev}) + '\n')
    return _EV[k]


def simulate(m, prm, room, nz, sc, sd):
    meth = GRID[m][0] if m in GRID else 'PCG-WLS-F'
    p = dict(prm)
    if m in DET:
        p['det_events'] = events(room, nz, sc, sd)
    ch = not sc.startswith('S8'); t0 = time.time()
    r = D.P.run(cfg_of(room, nz, sc), sd, meth, p, TT, D.CH if ch else None)
    tp = np.array(r['total_power']); up = np.array(r['uncontrolled_power'])
    return {'method': m, 'prm': prm, 'room': room, 'noise': nz, 'scen': sc, 'seed': sd, 'flag_stable': bool(r['stable']),
            'tp': tp.tolist(), 'up': up[:len(tp)].tolist(), 'hops_full': len(up), 'wall_s': round(time.time() - t0, 2),
            'flops_hop': float(np.mean(r['flop_hist'])) if r.get('flop_hist') else None,
            'n_restarts': len(p.get('det_events', [])),
            **({'path_provenance': r['path_provenance']} if room in ('M', 'M_8a') else {})}


def run_metrics(rec):
    nh = int(TT * 8000) // H
    r = dict(rec)
    if len(r['tp']) < nh:                                   # stopped early = failed; padding only for the metric code
        r['_up_full'] = np.concatenate([np.asarray(r['up'], float), np.full(nh - len(r['up']), float(np.mean(r['up'])))])
    else:
        r['_up_full'] = np.asarray(r['up'], float)
    return FE.metrics(r, nh)[0]


# ---------------------------------------------------------------- stage 1: selection (tuning seeds, room A)
SEL = ROOT / 'results' / 'protocol_v2_sel'; SEL.mkdir(parents=True, exist_ok=True)


def select_run():
    done, dq = set(), set()
    for f in SEL.glob('runs*.jsonl'):
        for r in read_jsonl(f):
            if r['cfg'] < len(GRID[r['method']][1]) and r.get('prm') == GRID[r['method']][1][r['cfg']]:
                done.add((r['method'], r['cfg'], r['noise'], r['scen'], r['seed']))
                if r['fail']:
                    dq.add((r['method'], r['cfg']))
    si, sn = map(int, os.environ.get('SHARD', '0/1').split('/'))
    fn = SEL / f"runs{os.environ.get('PART', '')}.jsonl"
    torn = fn.exists() and fn.stat().st_size > 0 and not fn.read_bytes().endswith(b'\n')
    with fn.open('a') as fh:
        if torn:
            fh.write('\n')
        cfgs = [(m, ci, prm) for m in BASE for ci, prm in enumerate(GRID[m][1])]
        for idx, (m, ci, prm) in enumerate(cfgs):
            k = (m, ci)
            if idx % sn != si:                                     # round robin over configurations (balances the RLS family)
                continue
            if True:
                for sd in TUNE:                                   # seed-major: a failure is found early
                    if k in dq:
                        break
                    for nz, sc in COMBOS15:
                        if k + (nz, sc, sd) in done:
                            continue
                        rec = simulate(m, prm, 'A', nz, sc, sd); mt = run_metrics(rec)
                        fh.write(json.dumps({'method': m, 'cfg': ci, 'prm': prm, 'noise': nz, 'scen': sc, 'seed': sd,
                                             'fail': mt['fail'], 'A1': mt['A1'], 'A2': mt['A2'],
                                             'n_restarts': rec['n_restarts'], 'wall_s': rec['wall_s']}) + '\n'); fh.flush()
                        if mt['fail']:
                            dq.add(k); break
                print(m, ci, 'dropped' if k in dq else 'admissible', flush=True)


def select_summary():
    R = {}
    for f in sorted(SEL.glob('runs*.jsonl')):
        for r in read_jsonl(f):
            if r['cfg'] < len(GRID[r['method']][1]) and r.get('prm') == GRID[r['method']][1][r['cfg']]:
                R.setdefault((r['method'], r['cfg'], r['noise'], r['scen'], r['seed']), r)
    need = {(nz, sc, sd) for nz, sc in COMBOS15 for sd in TUNE}
    lines = ['| method | admissible (of grid) | selected | score (dB) | per-config score / first failure |', '|---|---|---|---|---|']
    out, inc = {}, []
    for m in BASE:
        grid = GRID[m][1]; sc_, notes = {}, []
        for ci in range(len(grid)):
            rs = [r for k, r in R.items() if k[0] == m and k[1] == ci]
            bad = [r for r in rs if r['fail']]
            if bad:
                notes.append(f"{ci}: fail ({bad[0]['noise']}, {bad[0]['scen'].split()[0]}, {bad[0]['seed']})")
            elif {(r['noise'], r['scen'], r['seed']) for r in rs} != need:
                inc.append((m, ci, len(rs)))
            else:
                sc_[ci] = score(rs); notes.append(f'{ci}: {sc_[ci]:.2f}')
        if sc_:
            best = min(sc_, key=sc_.get); out[m] = best
            lines.append(f'| {m} | {len(sc_)} of {len(grid)} | {best} {grid[best]} | {sc_[best]:.2f} | {"; ".join(notes)} |')
        else:
            out[m] = None; lines.append(f'| {m} | 0 of {len(grid)} | none | | {"; ".join(notes)} |')
    if inc and not os.environ.get('PARTIAL'):
        print('INCOMPLETE:', inc); sys.exit(1)
    if inc:                                   # PARTIAL=1: methods with an incomplete configuration are left out (None)
        for m in {m for m, _, _ in inc}:
            out[m] = None
        (SEL / 'selected_partial.json').write_text(json.dumps({'selected': out, 'grids': GRID, 'incomplete': inc}, indent=1))
        print('\n'.join(lines)); print('PARTIAL, incomplete:', inc); return
    sx = os.environ.get('SELOUT', '')        # (2026-10-30) e.g. '_b' -> selected_b.json / selection_b.md; default unchanged
    assert sx or not (SEL / 'selected.json').exists() or os.environ.get('SEL_OVERWRITE'), 'selected.json exists: use SELOUT'
    (SEL / f'selected{sx}.json').write_text(json.dumps({'selected': out, 'grids': GRID}, indent=1))
    (SEL / f'selection{sx}.md').write_text('\n'.join(lines) + '\n'); print('\n'.join(lines))


# ---------------------------------------------------------------- stage 2: evaluation-seed runs (FE machinery)
def _setup_final():
    global EVD, _EV
    es = os.environ.get('EVAL_SET', 'main'); assert es in EVAL_SETS, es
    room, combos, out = EVAL_SETS[es]
    sel = json.loads((SEL / os.environ.get('SELFILE', {'main_b': 'selected_b.json', 'main_c': 'selected_c.json', 'main_d': 'selected_d.json', 'main_e': 'selected_e.json', 'meas_p': 'selected_e.json', 'meas_ps': 'selected_e.json', 'meas_p_8a': 'selected_e.json', 'meas_ps_8a': 'selected_e.json'}.get(es, 'selected.json'))).read_text())
    if room in ('M', 'M_8a') and sel != json.loads((SEL / 'selected_e.json').read_text()):
        raise ValueError('Measured evaluation requires the frozen selected_e.json')
    meth = {m: (GRID[m][0], GRID[m][1][ci]) for m, ci in sel['selected'].items() if ci is not None}
    # record labels of PCG-WLS / PCG-WLS (multi-window) in results/ (former names, see ffanc_norm.naming)
    meth['E-PCG'] = ('PCG-WLS-F', MAIN); meth['E-PCG bank'] = ('PCG-WLS-F', BANK)
    base = [m for m in BASE if m in meth]
    FE.OUT = out; out.mkdir(parents=True, exist_ok=True)
    FE.METH = meth; FE.BASE = base; FE.ALL = base + FE.PROP; FE.COMBOS = combos; FE.SEEDS = EVAL
    FE.one = lambda m, nz, sc, sd: simulate(m, FE.METH[m][1], room, nz, sc, sd)
    if room in ('M', 'M_8a'):
        from measured_paths import write_provenance
        write_provenance(out, EVAL, es, ROOMS[room].get('meshrir_d0', 0))
        EVD = out / 'det_events'; EVD.mkdir(parents=True, exist_ok=True); _EV = None
    return es, room, out


def uncontrolled_fill():
    """(2026-10-30, roomC) Where every method stopped early on a run, no stored record has the full-length uncontrolled
    power that final_eval.summary needs for the padding of failed runs. It does not depend on the method, so it is taken
    from a no-control run (FD-FxNLMS with mu = 0: the controller stays zero) and stored in <OUT>/uncontrolled.jsonl
    (not a runs*.jsonl file, so it is never read as a method record); final_eval.summary checks that its prefix equals the
    stored uncontrolled power of every record. No effect where some method ran to the end."""
    es, room, out = _setup_final()
    nh = int(TT * 8000) // H
    full, keys = set(), set()
    for f in out.glob('runs*.jsonl'):
        for r in read_jsonl(f):
            if r['method'] not in FE.METH or r.get('prm') != FE.METH[r['method']][1]:
                continue                                       # stale records are not used by the summary either
            k = (r['noise'], r['scen'], r['seed']); keys.add(k)
            if len(r['up']) == nh:
                full.add(k)
    fn = out / 'uncontrolled.jsonl'
    have = {(r['noise'], r['scen'], r['seed']): r['up'] for r in read_jsonl(fn)}
    for k in sorted(keys - full):
        if k not in have:
            rec = simulate('FD-FxNLMS', {'mu': 0.0}, room, *k)
            assert len(rec['up']) == nh and rec['flag_stable'], f'no-control run stopped early: {k}'
            with fn.open('a') as fh:
                fh.write(json.dumps({'noise': k[0], 'scen': k[1], 'seed': k[2], 'up': rec['up']}) + '\n')
            have[k] = rec['up']
        FE.EXTRA_UP[k] = have[k]
    print(f'uncontrolled fill: {len(keys - full)} run(s) without a full-length record', flush=True)


def reuse():
    es, room, out = _setup_final()
    assert es in ('main', 'main_b', 'main_c', 'main_d', 'main_e')
    fn = out / 'runs_reuse.jsonl'
    if fn.exists():
        print('exists', fn); return
    n = 0
    src = ROOT / 'results' / {'main': 'final_eval', 'main_b': 'final_eval_v2', 'main_c': 'final_eval_v2b', 'main_d': 'final_eval_v2c', 'main_e': 'final_eval_v2d'}[es]
    with fn.open('w') as fh:
        for f in sorted(src.glob('runs*.jsonl')):
            for r in read_jsonl(f):
                if r['method'] in FE.METH and r.get('prm') == FE.METH[r['method']][1]:
                    fh.write(json.dumps(dict(r, room='A')) + '\n'); n += 1
    print(f'{n} records reused (identical configuration) -> {fn}')


if __name__ == '__main__':
    cmd = sys.argv[1]
    if cmd == 'select-run':
        select_run()
    elif cmd == 'select-summary':
        select_summary()
    elif cmd == 'reuse':
        reuse()
    elif cmd == 'final-run':
        _setup_final(); FE.run()
    elif cmd == 'final-summary':
        es, room, out = _setup_final()
        if room in ('M', 'M_8a'):
            from measured_paths import validate_records
            validate_records(out, FE.METH, FE.COMBOS, EVAL)
        if os.environ.get('UNCONTROLLED_FILL'):        # flag (2026-10-30); default behaviour unchanged
            uncontrolled_fill()
        FE.summary()
        if room in ('M', 'M_8a'):
            from measured_paths import annotate_summary
            annotate_summary(out)
    else:
        raise SystemExit(cmd)
