"""Revision 11 pre-run checks (Rule 11 Sec. 6.1-6.4). Evaluation seeds are never used for new records: Sec. 6.2 only
re-runs saved keys and compares bytes; the smoke runs use the tuning seed 300 only. Output: results/r11_preflight/.

  regress-dump <root> <out.pkl>   one side of Sec. 6.1 (run with the code tree <root>; separate processes per side)
  regress                         Sec. 6.1: base b3058bf (git archive in /tmp/r11_base) vs this tree -> regression.md
  envA                            Sec. 6.2 environment A: holdout E-PCG main 4 keys + RLS + det 1 key -> env_A.json
  envC                            Sec. 6.2 environment C: eval_roomB_x2 E-PCG 4 keys (Rule 9a keys)   -> env_C.json
  equiv                           Sec. 6.3 (a) MFBLMS gradient vs gap_check4a recursion A, (b) det_cond_db +-inf,
                                  (c1)-(c3) RLS + det + growth (Rule 11a Sec. 2.2)
  repeat                          Rule 11b m3: E-PCG room B ar1 S8 480 in two processes, byte-identical -> repeat.md
  ref-localize / localize         Rule 11b m5: reference values (this container, committed) / stage differences -> localize.md
  envA / envC write the class I / K / F of Rule 11b Sec. 2.2 and the machine fingerprint; PRA_NUM_THREADS 3 / 2.
  smoke A|B|C                     Sec. 6.4 seed 300 (A: three cells, B / C: timing of the 11-D method set) -> smoke_*.json
  smoke-md                        smoke.md from smoke_*.json
usage: RLS_FAST=1 OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 python experiments/revision11_preflight.py <cmd>
"""
import json
import os
import pickle
import struct
import subprocess
import sys
import time
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'results/r11_preflight'
BASE_COMMIT = 'b3058bf'
BASE_DIR = Path('/tmp/r11_base')
CASES = [('ar1', 'S2 src 30cm', 300), ('harmonic', 'R2 rig 30cm', 300)]
TIMING_KEYS = ('wall_s', 'elapsed', 'time')


def _bytes(v):
    if isinstance(v, np.ndarray):
        return ('nd', v.dtype.str, v.shape, v.tobytes())
    if isinstance(v, (float, np.floating)):
        return ('f', struct.pack('<d', float(v)))
    if isinstance(v, dict):
        return ('d', tuple((k, _bytes(v[k])) for k in sorted(v, key=str) if k not in TIMING_KEYS))
    if isinstance(v, (list, tuple)):
        return ('l', tuple(_bytes(x) for x in v))
    if isinstance(v, (np.integer, np.bool_)):
        return ('i', v.item())
    return ('o', v)


# ---------------------------------------------------------------- 6.1 regression
def regress_dump(root, out):
    """Run the 15 methods on CASES with the prototype of <root>; inputs (cfg, params, events) come from a pickled spec."""
    spec = pickle.loads(Path('/tmp/r11_regression_spec.pkl').read_bytes())
    sys.path[:0] = [str(Path(root) / 'src'), str(Path(root) / 'experiments')]
    import prototype_new_algorithms as P
    assert Path(P.__file__).resolve().is_relative_to(Path(root).resolve()), P.__file__
    P.RETURN_SIGNALS = True
    res = {}
    for item in spec:
        r = P.run(item['cfg'], item['seed'], item['kind'], item['params'], 5.0, item['change_at'])
        res[(item['name'], item['noise'], item['scen'])] = _bytes(r)
        print(root, item['name'], item['noise'], item['scen'], flush=True)
    Path(out).write_bytes(pickle.dumps(res))


def regress():
    import revision11_methods as R
    ev = R.ev
    OUT.mkdir(parents=True, exist_ok=True)
    if not (BASE_DIR / 'experiments/prototype_new_algorithms.py').exists():
        BASE_DIR.mkdir(parents=True, exist_ok=True)
        subprocess.run(f'git archive {BASE_COMMIT} src experiments | tar -x -C {BASE_DIR}', shell=True, check=True, cwd=ROOT)
    spec = []
    meth = dict(R.BASE13); meth.update(R.PROP)
    for nz, sc, sd in CASES:
        cfg = ev.cfg_of('A', nz, sc)
        r = ev.D.P.run(cfg, sd, 'E-PCG-F', dict(ev.MAIN), 5.0, ev.D.CH)
        events = R.epcg_events(r)
        for name, (kind, prm) in meth.items():
            p = dict(prm)
            if name in ev.DET:
                p['det_events'] = events
            spec.append({'name': name, 'noise': nz, 'scen': sc, 'seed': sd, 'cfg': cfg, 'kind': kind, 'params': p,
                         'change_at': ev.D.CH})
    Path('/tmp/r11_regression_spec.pkl').write_bytes(pickle.dumps(spec))      # exact Python objects (no JSON casts)
    env = dict(os.environ)
    procs = [subprocess.Popen([sys.executable, __file__, 'regress-dump', str(root), f'/tmp/r11_regress_{tag}.pkl'],
                              env=env) for tag, root in (('base', BASE_DIR), ('new', ROOT))]
    if any(p.wait() for p in procs):
        raise RuntimeError('regression dump failed')
    a = pickle.loads(Path('/tmp/r11_regress_base.pkl').read_bytes())
    b = pickle.loads(Path('/tmp/r11_regress_new.pkl').read_bytes())
    lines = [f'# Rule 11 Sec. 6.1 regression: new flags absent, this tree vs {BASE_COMMIT}', '',
             f'Methods: 12 selected baselines + RLS + CUSUM + E-PCG main + bank; cases {CASES}; T = 5 s;',
             'RETURN_SIGNALS = True (also x_f, d_hat, e, y, w_final); every returned value compared byte for byte',
             '(timing keys excluded); events of the '+'+ det baselines from this tree\'s E-PCG main run.', '',
             '| method | noise | cell | identical |', '|---|---|---|---|']
    ok = True
    for k in a:
        same = a[k] == b.get(k)
        ok &= same
        lines.append(f'| {k[0]} | {k[1]} | {k[2]} | {"yes" if same else "NO"} |')
    ok &= set(a) == set(b) and len(a) == 30
    lines += ['', f'Result: {"PASS" if ok else "FAIL"} ({len(a)} runs).']
    (OUT / 'regression.md').write_text('\n'.join(lines) + '\n')
    print(lines[-1])
    if not ok:
        sys.exit(1)


# ---------------------------------------------------------------- 6.2 environments
def _rel(new, old):
    new = np.asarray(new, float); old = np.asarray(old, float)
    if new.shape != old.shape:
        return float('inf'), float('inf')
    ab = np.abs(new - old)
    with np.errstate(divide='ignore', invalid='ignore'):
        rel = np.where(old != 0, ab / np.abs(old), np.where(ab == 0, 0.0, np.inf))
    return (float(np.max(rel)) if rel.size else 0.0), (float(np.max(ab)) if ab.size else 0.0)


def _compare(r, old, events_saved=None):
    """Byte checks (as before) and, for Rule 11b Sec. 2.3 m1, the size of the differences."""
    import revision11_methods as R
    tp = list(map(float, r['total_power'])); up = list(map(float, r['uncontrolled_power'][:len(tp)]))
    ab = lambda v: np.asarray(v, dtype='<f8').tobytes()
    c = {'tp': ab(tp) == ab(old['tp']), 'up': ab(up) == ab(old['up']),
         'flag_stable': bool(r['stable']) is bool(old['flag_stable']), 'hops_full': len(r['uncontrolled_power']) == old['hops_full']}
    upr, upa = _rel(up, old['up']); tpr, tpa = _rel(tp, old['tp'])
    with np.errstate(divide='ignore', invalid='ignore'):
        db = (float(np.max(np.abs(10 * np.log10(np.asarray(tp) / np.asarray(old['tp'], float)))))
              if len(tp) == len(old['tp']) and len(tp) else float('inf'))
    size = {'up_max_rel': upr, 'up_max_abs': upa, 'tp_max_rel': tpr, 'tp_max_abs': tpa, 'tp_max_db': db,
            'tp_finite': bool(np.all(np.isfinite(tp)))}
    if events_saved is not None:
        new_ev = R.epcg_events(r)
        c['events'] = json.dumps(new_ev) == json.dumps(events_saved)
        first = next((i for i, (a, b) in enumerate(zip(new_ev, events_saved)) if a != b),
                     None if len(new_ev) == len(events_saved) else min(len(new_ev), len(events_saved)))
        size['events_diff'] = {'n_new': len(new_ev), 'n_saved': len(events_saved), 'first_mismatch': first}
    return c, size


def classify(cases):
    """Rule 11b Sec. 2.2: 'I' all byte checks pass; 'K' events / flag_stable / hops_full equal for every key, max
    relative `up` difference <= UP_REL_TOL and tp finite; else 'F'."""
    import revision11_methods as R
    if all(all(x['checks'].values()) for x in cases):
        return 'I'
    ok = all(x['checks']['flag_stable'] and x['checks']['hops_full'] and x['checks'].get('events', True)
             and x['size']['up_max_rel'] <= R.UP_REL_TOL and x['size']['tp_finite'] for x in cases)
    return 'K' if ok else 'F'


def _env_info():
    import platform
    from importlib.metadata import version
    return {'python': platform.python_version(), 'executable': sys.executable,
            'software': {x: version(x) for x in ('numpy', 'scipy', 'pyroomacoustics')},
            'RLS_FAST': os.environ.get('RLS_FAST'),
            'threads': {x: os.environ.get(x) for x in ('OPENBLAS_NUM_THREADS', 'MKL_NUM_THREADS', 'OMP_NUM_THREADS',
                                                       'PRA_NUM_THREADS')},
            'commit': subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip()}


def _env_json(name, res):
    import revision11_methods as R
    cls = classify(res)
    d = {'environment': name, **_env_info(), 'machine': R.machine_fingerprint(), 'cases': res, 'class': cls,
         'pass': cls == 'I', 'up_rel_tol': R.UP_REL_TOL, 'rule11b_sha256': R.RULE11B_SHA256}
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / f'env_{name}.json').write_text(json.dumps(d, indent=2) + '\n')
    print(f'env {name}: class {cls}', 'PASS' if cls == 'I' else ('(K)' if cls == 'K' else 'FAIL'), flush=True)
    return d


SAVED_HOLD = ROOT / 'results/final_eval_holdout'      # 9-A records (environment A), whatever R11_HOLDOUT_BASE says


def _saved_holdout_events():
    out = {}
    for f in sorted(SAVED_HOLD.glob('det_events_*.jsonl')):
        for line in f.open():
            r = json.loads(line); out[(r['noise'], r['scen'], r['seed'])] = r['events']
    return out


def envA():
    import revision11_methods as R
    ev = R.ev
    R.check_runtime_env('A')                               # Rule 11b Sec. 3: PRA_NUM_THREADS=3
    keys = [(nz, sc, sd) for nz, sc in (R.COMBOS15[0], R.COMBOS15[-1]) for sd in (800, 839)]
    rkey = (R.COMBOS15[-1][0], R.COMBOS15[-1][1], 800)
    events = _saved_holdout_events()
    want = {('E-PCG',) + k for k in keys} | {('RLS + det',) + rkey}
    saved = {}
    for f in sorted(SAVED_HOLD.glob('runs_[01].jsonl')):
        for line in f.open():
            r = json.loads(line); k = (r['method'], r['noise'], r['scen'], r['seed'])
            if k in want:
                saved[k] = r
    if set(saved) != want:
        raise ValueError(f'saved keys missing {want - set(saved)}')
    res = []
    for k in sorted(want):
        m, nz, sc, sd = k
        kind, prm = (R.PROP['E-PCG'] if m == 'E-PCG' else R.BASE13['RLS + det'])
        p = dict(prm)
        if m == 'RLS + det':
            p['det_events'] = events[(nz, sc, sd)]
        if saved[k]['prm'] != prm:
            raise ValueError(f'saved configuration differs {k}')
        t = time.time()
        r = ev.D.P.run(ev.cfg_of('A', nz, sc), sd, kind, p, 5.0, None if sc.startswith('S8') else ev.D.CH)
        c, size = _compare(r, saved[k], events[(nz, sc, sd)] if m == 'E-PCG' else None)
        res.append({'method': m, 'noise': nz, 'scen': sc, 'seed': sd, 'checks': c, 'size': size,
                    'wall_s': round(time.time() - t, 2), 'n_events': len(events[(nz, sc, sd)])})
        print(res[-1], flush=True)
    _env_json('A', res)


def envC():
    import revision11_methods as R
    ev = R.ev
    R.check_runtime_env('C')                               # Rule 11b Sec. 3: PRA_NUM_THREADS=2
    combos = ev.EVAL_SETS['roomB'][1]
    keys = [(nz, sc, sd) for nz, sc in (combos[0], combos[-1]) for sd in (480, 519)]
    saved = {}
    for f in sorted((R.RES / 'eval_roomB').glob('runs*.jsonl')):
        for line in f.open():
            r = json.loads(line); k = (r['noise'], r['scen'], r['seed'])
            if r['method'] == 'E-PCG' and k in keys and r.get('prm') == ev.MAIN:
                if k in saved and any(saved[k][x] != r[x] for x in ('tp', 'up', 'flag_stable')):
                    raise ValueError(f'conflicting saved records {k}')
                saved[k] = r
    evs = {}
    for f in sorted((R.RES / 'det_events').glob('*.jsonl')):
        for line in f.open():
            r = json.loads(line)
            if r['room'] == 'B' and (r['noise'], r['scen'], r['seed']) in keys:
                evs[(r['noise'], r['scen'], r['seed'])] = r['events']
    if set(saved) != set(keys) or set(evs) != set(keys):
        raise ValueError('saved roomB keys or events missing')
    res = []
    for k in keys:
        nz, sc, sd = k
        t = time.time()
        r = ev.D.P.run(ev.cfg_of('B', nz, sc), sd, 'E-PCG-F', dict(ev.MAIN), 5.0, None if sc.startswith('S8') else ev.D.CH)
        c, size = _compare(r, saved[k], evs[k])
        res.append({'noise': nz, 'scen': sc, 'seed': sd, 'checks': c, 'size': size, 'wall_s': round(time.time() - t, 2)})
        print(res[-1], flush=True)
    d = _env_json('C', res)
    if d['class'] == 'F':
        sys.exit(1)


# ---------------------------------------------------------------- Rule 11b Sec. 2.3 m3 / m5
LOC_KEY = ('B', 'ar1', 'S8 stationary', 480)               # room B E-PCG key of envC (Rule 11b m3, m5)
LOC_REF = OUT / 'ref_localize_roomB_ar1_S8_480.npz'


def repeat_one(out):
    import revision11_methods as R
    ev = R.ev
    R.check_runtime_env('C')
    ev.D.P.RETURN_SIGNALS = True
    room, nz, sc, sd = LOC_KEY
    r = ev.D.P.run(ev.cfg_of(room, nz, sc), sd, 'E-PCG-F', dict(ev.MAIN), 5.0, None)
    Path(out).write_bytes(pickle.dumps(_bytes(r)))


def repeat():
    """Rule 11b m3: the same E-PCG run in two separate processes; every deterministic returned value byte-identical."""
    import revision11_methods as R
    R.check_runtime_env('C')
    outs = [Path(f'/tmp/r11_repeat_{i}.pkl') for i in (0, 1)]
    for o in outs:
        subprocess.run([sys.executable, __file__, 'repeat-one', str(o)], check=True)
    a, b = (pickle.loads(o.read_bytes()) for o in outs)
    ok = a == b
    keys = sorted(k for k, _ in a[1]) if a[0] == 'd' else []
    lines = ['# Rule 11b Sec. 2.3 m3: in-environment determinism (two processes)', '',
             f'- key: room {LOC_KEY[0]}, {LOC_KEY[1]} {LOC_KEY[2]}, seed {LOC_KEY[3]}, E-PCG main, 5 s, RETURN_SIGNALS',
             f'- PRA_NUM_THREADS {os.environ.get("PRA_NUM_THREADS")}; compared values: {keys}',
             f'- machine: {json.dumps({k: R.machine_fingerprint()[k] for k in R.MACHINE_KEYS})}', '',
             f'Result: {"PASS" if ok else "FAIL"}']
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / 'repeat.md').write_text('\n'.join(lines) + '\n')
    print(lines[-1])
    if not ok:
        sys.exit(1)


def _localize_values():
    import revision11_methods as R
    ev = R.ev
    P = ev.D.P
    room, nz, sc, sd = LOC_KEY
    cfg = ev.cfg_of(room, nz, sc)
    x, *_ = P._make_signals(cfg, sd, 1, 5.0)
    p, s, _, _ = P.ism_paths(cfg, sd, {})
    d = np.convolve(x, p, mode='full')[:len(x)]
    r = P.run(cfg, sd, 'E-PCG-F', dict(ev.MAIN), 5.0, None)
    return {'x': np.asarray(x, float), 'p': np.asarray(p, float), 's': np.asarray(s, float), 'd': d,
            'up': np.asarray(r['uncontrolled_power'], float)}


def ref_localize():
    """Reference values of the localize stages (this container, environment C, PRA_NUM_THREADS=2; committed)."""
    import revision11_methods as R
    R.check_runtime_env('C')
    v = _localize_values()
    OUT.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(LOC_REF, **v, machine=json.dumps(R.machine_fingerprint()))
    print('ref-localize ->', LOC_REF, {k: a.shape for k, a in v.items()})


def localize():
    """Rule 11b m5 (class K): the stage (x, RIR p / s, d = x * p, up) where this environment departs from the reference."""
    import revision11_methods as R
    R.check_runtime_env('C')
    ref = np.load(LOC_REF)
    v = _localize_values()
    lines = ['# Rule 11b Sec. 2.3 m5: where does `up` depart from the reference (descriptive, not a criterion)', '',
             f'- key: room {LOC_KEY[0]}, {LOC_KEY[1]} {LOC_KEY[2]}, seed {LOC_KEY[3]}; reference machine: '
             f'{json.loads(str(ref["machine"])).get("cpu_model")}; this machine: {R.machine_fingerprint()["cpu_model"]}',
             '', '| stage | identical | max relative difference | max absolute difference |', '|---|---|---|---|']
    for k in ('x', 'p', 's', 'd', 'up'):
        rel, ab = _rel(v[k], ref[k])
        lines.append(f'| {k} | {v[k].tobytes() == ref[k].tobytes()} | {rel:.3e} | {ab:.3e} |')
    (OUT / 'localize.md').write_text('\n'.join(lines) + '\n')
    print('\n'.join(lines))


# ---------------------------------------------------------------- 6.3 equivalences
def equiv():
    import revision11_methods as R
    ev = R.ev
    R.check_runtime_env('C')
    lines = ['# Rule 11 Sec. 6.3: equivalence of the new flags', '']
    ok_all = True
    # (a) MFBLMS gradient vs recursion A of gap_check4a (100 random frames, rel. 1e-12) and the recursion itself
    import gap_check4a as G
    from ffanc_norm.fd_fxnlms import fd_block_gradient_mod
    from ffanc_norm.simulation import right_aligned_history, causal_fir_block
    rng = np.random.default_rng(20261107)
    worst = 0.0
    for _ in range(100):
        xh = rng.standard_normal(G.N) * rng.uniform(0.1, 10.0); r = rng.standard_normal(G.H)
        den = rng.uniform(0.01, 5.0, G.N // 2 + 1)
        X = np.fft.rfft(xh); ef = np.zeros(G.N); ef[-G.H:] = r
        c = np.fft.irfft(np.conj(X) * np.fft.rfft(ef), G.N); c[G.M:] = 0.0          # gap_check4a.py lines 65-67
        ref = np.fft.irfft(np.fft.rfft(c) / den, G.N)[:G.M]
        worst = max(worst, float(np.max(np.abs(fd_block_gradient_mod(xh, r, den, G.M) - ref)) / np.max(np.abs(ref))))
    # whole recursion: G.recursion(kind='A') against the same loop with fd_block_gradient_mod
    n = 40 * G.H; xf = np.convolve(rng.standard_normal(n + 100), [1.0, 0.8])[100:100 + n]
    dh = np.convolve(xf, rng.standard_normal(32))[:n] * 0.5 + 0.01 * rng.standard_normal(n)
    Sx = G.bin_power(xf); w_ls = np.zeros(G.M); Rm = np.eye(G.M)
    ewA, tpA, _ = G.recursion(xf, dh, Sx, w_ls, Rm, 'A')
    w = np.zeros(G.M); tp2 = []
    for b in range(n // G.H):
        s0, s1 = b * G.H, (b + 1) * G.H
        rr = dh[s0:s1] + causal_fir_block(xf, w, s0, s1); tp2.append(float(np.mean(rr ** 2)))
        w = w - fd_block_gradient_mod(right_aligned_history(xf, s1, G.N), rr, (b + 1) * G.H * Sx, G.M)
    rel = float(np.max(np.abs(np.asarray(tp2) - tpA) / np.abs(tpA)))
    ok_a = worst <= 1e-12 and rel <= 1e-9
    ok_all &= ok_a
    lines += ['## (a) fd_block_gradient_mod vs recursion A (gap_check4a)',
              f'- 100 random frames (N 1024, H 128, M 512): max relative difference {worst:.3e} (criterion 1e-12)',
              f'- 40-hop recursion, gap_check4a.recursion(kind="A") vs the same loop with fd_block_gradient_mod: '
              f'max relative difference of the hop powers {rel:.3e}',
              f'- {"PASS" if ok_a else "FAIL"}', '']
    # (b) det_cond_db +-inf, seed 300, ar1 S2 and harmonic S5 (revision9_check_replay keys)
    ev.D.P.RETURN_SIGNALS = True
    keys = ('total_power', 'uncontrolled_power', 'stable', 'failure', 'reset_hops', 'e', 'y', 'w_final')
    evs = R.tuning_events()
    det = dict(R.BASE13['RLS + det'][1])
    lines += ['## (b) RLS + det (cond.): theta = -inf == RLS + det; theta = +inf == R-RLS lam 0.9999 without events',
              '| case | events | -inf vs RLS + det | +inf vs R-RLS | restarts (-inf / +inf) |', '|---|---|---|---|---|']
    for nz, sc in (('ar1', 'S2 src 30cm'), ('harmonic', 'S5 src 30cm cont')):
        e = evs[(nz, sc, 300)]
        cfg = ev.cfg_of('A', nz, sc)
        run = lambda p: ev.D.P.run(cfg, 300, 'R-RLS', p, 5.0, ev.D.CH)
        a = run(dict(det, det_events=e)); b = run(dict(det, det_events=e, det_cond_db=-np.inf, det_cond_k=32))
        c = run({'lam': 0.9999, 'delta': 0.01}); d = run(dict(det, det_events=e, det_cond_db=np.inf, det_cond_k=32))
        s1 = all(_bytes(a[k]) == _bytes(b[k]) for k in keys); s2 = all(_bytes(c[k]) == _bytes(d[k]) for k in keys)
        ok_all &= s1 and s2 and len(e) > 0
        lines.append(f'| {nz} {sc} | {len(e)} | {"identical" if s1 else "DIFFERENT"} | {"identical" if s2 else "DIFFERENT"} | '
                     f'{len(b["reset_hops"])} / {len(d["reset_hops"])} |')
    # (c1) Rule 11a Sec. 2.2: version (i) (growth after restarts only) without events == R-RLS lam 0.9999 delta 0.01
    cfg = ev.cfg_of('A', 'ar1', 'S8 stationary')
    grow_i = dict(R.GRID11['RLS + det + growth'][1][0]); grow_ii = dict(R.GRID11['RLS + det + growth (from start)'][1][0])
    a = ev.D.P.run(cfg, 300, 'R-RLS', dict(grow_i, det_events=[]), 5.0, None)
    c = ev.D.P.run(cfg, 300, 'R-RLS', {'lam': 0.9999, 'delta': 0.01}, 5.0, None)
    ok_c1 = all(_bytes(a[k]) == _bytes(c[k]) for k in keys)
    # (c2) run-level: the run ends n < 2M samples after the replay start -> taps >= max(n // 2, 1) are exactly 0
    # (w[1:] = 0 at the restart, zero gain outside the growing order); version (ii) likewise from the run start
    cfg2 = ev.cfg_of('A', 'ar1', 'S2 src 30cm'); Mc = int(cfg2['controller_length']); Hc = int(cfg2['hop_length'])
    T2 = 0.5; n_all = int(T2 * int(cfg2['sample_rate'])) // Hc * Hc; stop = (n_all // Hc - 2) * Hc; tau = stop - Hc // 2
    r1 = ev.D.P.run(cfg2, 300, 'R-RLS', dict(grow_i, det_events=[[stop, tau]]), T2, ev.D.CH)
    r0 = ev.D.P.run(cfg2, 300, 'R-RLS', {'lam': 0.9999, 'delta': 0.01, 'det_reset_w': False, 'det_events': [[stop, tau]]},
                    T2, ev.D.CH)
    n1 = n_all - tau; m1 = max(n1 // 2, 1)
    w1, w0 = np.asarray(r1['w_final']), np.asarray(r0['w_final'])
    ok_i = (len(r1['reset_hops']) == 1 and n1 < 2 * Mc and not np.any(w1[m1:]) and np.count_nonzero(w1[:m1]) == m1
            and np.count_nonzero(w0[m1:]) > 0)
    T3 = 0.1; n3 = int(T3 * int(cfg2['sample_rate'])) // Hc * Hc; m3 = max(n3 // 2, 1)
    r2 = ev.D.P.run(cfg2, 300, 'R-RLS', dict(grow_ii, det_events=[]), T3, ev.D.CH)
    r3 = ev.D.P.run(cfg2, 300, 'R-RLS', dict(grow_i, det_events=[]), T3, ev.D.CH)
    w2, w3 = np.asarray(r2['w_final']), np.asarray(r3['w_final'])
    ok_ii = n3 < 2 * Mc and not np.any(w2[m3:]) and np.count_nonzero(w2[:m3]) == m3 and np.count_nonzero(w3[m3:]) > 0
    ok_c2 = ok_i and ok_ii
    ev.D.P.RETURN_SIGNALS = False
    ok_all &= ok_c1 and ok_c2
    lines += ['', '## (c) RLS + det + growth (Rule 11a Sec. 2.2; replaces the former (c))',
              f'- (c1) version (i) `det_grow: half` with no event vs R-RLS lam 0.9999 delta 0.01 (seed 300, ar1 S8, 5 s, '
              f'signals and w_final): {"identical" if ok_c1 else "DIFFERENT"}',
              f'- (c2) version (i), one event (stop {stop}, tau {tau}) in a {T2} s run: the run ends n = {n1} < 2M = {2 * Mc} '
              f'samples after tau; w_final taps >= max(n // 2, 1) = {m1} are exactly 0 and the {m1} leading taps are '
              f'non-zero; RLS + det (same event, no growth) has {int(np.count_nonzero(w0[m1:]))} non-zero taps there: '
              f'{"PASS" if ok_i else "FAIL"}',
              f'- (c2) version (ii) `det_grow_start: True`, no event, {T3} s run (n = {n3} < 2M): taps >= {m3} exactly 0 and '
              f'the {m3} leading taps non-zero; version (i) on the same run has {int(np.count_nonzero(w3[m3:]))} non-zero '
              f'taps there (no growth at the start): {"PASS" if ok_ii else "FAIL"}',
              '- (c3) code review: for n = t - g0 + 1 >= 2M (or g0 = None) the regressor, gain, P update and w update are',
              '  the existing statements; the growth adds only the truncation `u[_grow_taps(n, M):] = 0` and, at a restart,',
              '  `w[_grow_taps(1, M):] = 0` (w[1:] = 0). det_grow absent: `_grow` is None and the loop is the existing one',
              '  (tests/test_revision11.py::test_rls_grow_none_is_the_existing_path and Sec. 6.1). PASS (review)', '',
              f'Result: {"PASS" if ok_all else "FAIL"}']
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / 'equivalence.md').write_text('\n'.join(lines) + '\n')
    print('\n'.join(lines))
    if not ok_all:
        sys.exit(1)


# ---------------------------------------------------------------- 6.4 smoke (seed 300 only)
def smoke(part):
    import revision11_methods as R
    R.check_runtime_env('C')
    sd = R.SMOKE_SEED
    rows = []
    mu_m = 0.1          # SW-FBLMS smoke: MFBLMS step not selected yet; 0.1 is one of the two smoke steps of Sec. 6.4

    def one(name, kind, prm, room, nz, sc, evs):
        rec, own = R.run_record(name, kind, prm, room, nz, sc, sd, evs)
        tp = np.asarray(rec['tp']); up = np.asarray(rec['up'])
        nr = float(10 * np.log10(np.sum(tp) / np.sum(up))) if np.all(np.isfinite(tp)) else float('nan')
        met = R.metrics_of(rec) if len(rec['tp']) == rec['hops_full'] else None
        row = {'name': name, 'kind': kind, 'params': prm, 'room': room, 'noise': nz, 'scen': sc, 'seed': sd,
               'finite': bool(np.all(np.isfinite(tp))), 'complete': len(tp) == rec['hops_full'], 'NR_dB': nr,
               'metrics': met, 'wall_s': rec['wall_s'], 'n_events': rec.get('n_events'),
               'restart_hops': rec.get('restart_hops'), 'cond_log': rec.get('cond_log'), 'sw_log': rec.get('sw_log'),
               'sw_hops': rec.get('sw_hops'), 'detections': rec.get('detections'), 'events_own': rec.get('events')}
        rows.append(row); print(name, room, nz, sc, f"NR {nr:.2f} dB", f"{rec['wall_s']} s", flush=True)
        return own

    dg = R.dependent_grids(mu_m)
    if part == 'A':
        sets = [('A', 'ar1', 'S8 stationary'), ('A', 'ar1', 'S2 src 30cm'), ('A', 'harmonic', 'R2 rig 30cm')]
        cand = [(R.VARIANTS[g][0], 'E-PCG-F', R.VARIANTS[g][1]) for g in R.VARIANTS]
        cand += [('MFBLMS', 'fixed_binwise', {'mu': mu, 'mod': True}) for mu in (0.1, 0.3)]
        cand += [('switching FD-FxNLMS [6]', 'SW-FBLMS', dg['switching FD-FxNLMS [6]'][1][2]),
                 ('switching FD-FxNLMS + det', 'SW-FBLMS', dg['switching FD-FxNLMS + det'][1][2]),
                 ('RLS + det (cond.)', 'R-RLS', R.GRID11['RLS + det (cond.)'][1][2])]
        # the other new configurations (Rule 11a Sec. 3.2 (s2): tuning-grid rows)
        cand += [('RLS + det + growth', 'R-RLS', R.GRID11['RLS + det + growth'][1][0]),
                 ('RLS + det + growth (from start)', 'R-RLS', R.GRID11['RLS + det + growth (from start)'][1][0]),
                 ('MFBLMS + det', 'fixed_binwise', dg['MFBLMS + det'][1][0])]
        for base, pts in list(R.OUTER.items()) + list(R.OUTER_OPT.items()):
            cand.append((f'{base} [outer 1]', *pts[0]))
    else:
        room = {'B': 'B', 'C': 'C'}[part]
        sets = [(room, 'harmonic', 'R2 rig 30cm')]
        cand = [('E-PCG', *R.PROP['E-PCG'])] + [(m, *v) for m, v in R.BASE13.items()] + [('E-PCG bank', *R.PROP['E-PCG bank'])]
        cand += [('MFBLMS', 'fixed_binwise', {'mu': 0.3, 'mod': True}),
                 ('MFBLMS + det', 'fixed_binwise', dg['MFBLMS + det'][1][0]),
                 ('switching FD-FxNLMS [6]', 'SW-FBLMS', dg['switching FD-FxNLMS [6]'][1][2]),
                 ('switching FD-FxNLMS + det', 'SW-FBLMS', dg['switching FD-FxNLMS + det'][1][2]),
                 ('RLS + det (cond.)', 'R-RLS', R.GRID11['RLS + det (cond.)'][1][2]),
                 ('RLS + det + growth', 'R-RLS', R.GRID11['RLS + det + growth'][1][0]),
                 ('RLS + det + growth (from start)', 'R-RLS', R.GRID11['RLS + det + growth (from start)'][1][0])]
    for room, nz, sc in sets:
        own = one('E-PCG', *R.PROP['E-PCG'], room, nz, sc, None)          # events of E-PCG main on this run
        for name, kind, prm in cand:
            if name == 'E-PCG':
                continue
            one(name, kind, prm, room, nz, sc, own)
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / f'smoke_{part}.json').write_text(json.dumps({**_env_info(), 'rows': rows}, indent=1, default=str) + '\n')


def smoke_class(r):
    """Rule 11a Sec. 3.2 class of a smoke row: 'fixed' (G0-G5, the proposals and existing selected methods: NR >= 0 dB
    is a failure, s3) or 'grid' (a tuning-grid configuration of GRID11 / dependent_grids / outer points / MFBLMS
    extension points: NR >= 0 dB is recorded only, s2)."""
    import revision11_methods as R
    fixed = {'E-PCG', 'E-PCG bank'} | {v[0] for v in R.VARIANTS.values()} | set(R.BASE13)
    return 'fixed' if r['name'] in fixed else 'grid'


def smoke_log_missing(r):
    """Rule 11a Sec. 3.2 (s4): the switching / restart log the row must carry is absent."""
    import revision11_methods as R
    kind, prm = r.get('kind'), r['params']
    need = []
    if kind == 'SW-FBLMS':
        need.append('sw_log')
    if kind == 'R-RLS' and 'det_cond_db' in prm:
        need.append('cond_log')
    if kind == 'E-PCG-F':
        need.append('detections')
    if kind == 'R-RLS' and 'cusum_h' in prm:
        need.append('events_own')
    if kind is not None and R.needs_events(r['name'], kind, prm):
        need += ['n_events', 'restart_hops']
    return [k for k in need if r.get(k) is None]


def smoke_md():
    lines = ['# Rule 11 Sec. 6.4 smoke (tuning seed 300 only; performance recorded, not used for any choice)', '',
             'Criterion (Rule 11a Sec. 3.2, room-A rows): (s1) any non-finite value -> FAIL; (s2) NR >= 0 dB in a',
             'tuning-grid configuration -> recorded only (the tuning admissibility removes it); (s3) NR >= 0 dB in G0-G5 or',
             'an existing selected method -> FAIL; (s4) a switching / restart log missing -> FAIL. Rooms B / C: one key',
             '(harmonic R2) of the 11-D method set, for the run-time estimate only (no criterion).', '',
             '| method | room | noise | cell | finite | NR (dB) | A1 / A2 (dB) | wall (s) | events / restarts | log |',
             '|---|---|---|---|---|---|---|---|---|---|']
    s1, s2, s3, s4 = [], [], [], []
    for part in ('A', 'B', 'C'):
        p = OUT / f'smoke_{part}.json'
        if not p.exists():
            lines.append(f'| (smoke {part} not run) |'); continue
        for r in json.loads(p.read_text())['rows']:
            tag = ''
            if part == 'A':
                key = f"{r['name']} / {r['noise']} {r['scen']}"
                if not r['finite'] or not np.isfinite(r['NR_dB']):
                    s1.append(key); tag = ' (s1 FAIL)'
                elif r['NR_dB'] >= 0:
                    if smoke_class(r) == 'fixed':
                        s3.append(key); tag = ' (s3 FAIL)'
                    else:
                        s2.append(key); tag = ' (s2 recorded)'
                miss = smoke_log_missing(r)
                if miss:
                    s4.append(f'{key}: {miss}'); tag += ' (s4 FAIL)'
            met = f"{r['metrics']['A1']:.2f} / {r['metrics']['A2']:.2f}" if r['metrics'] else 'stopped early'
            ev_ = '' if r['n_events'] is None else f"{r['n_events']} / {len(r['restart_hops'] or [])}"
            log = (f"sw {r['sw_log']} hops {r['sw_hops']}" if r['sw_log'] is not None else
                   f"cond {r['cond_log']}" if r['cond_log'] is not None else
                   f"det {r['detections']}" if r['detections'] is not None else
                   f"cusum {r['events_own']}" if r['events_own'] is not None else '')
            lines.append(f"| {r['name']} | {r['room']} | {r['noise']} | {r['scen']} | {r['finite']} | {r['NR_dB']:.2f}"
                         f"{tag} | {met} | {r['wall_s']} | {ev_} | {log} |")
    ok = not (s1 or s3 or s4)
    lines += ['', '## Judgement (Rule 11a Sec. 3.2)',
              f'- (s1) non-finite rows: {s1 or "none"}',
              f'- (s2) NR >= 0 dB in tuning-grid configurations (recorded only): {s2 or "none"}',
              f'- (s3) NR >= 0 dB in G0-G5 / existing selected methods: {s3 or "none"}',
              f'- (s4) rows without the required log: {s4 or "none"}', '']
    for part in ('A', 'B', 'C'):
        p = OUT / f'smoke_{part}.json'
        if p.exists():
            rs = json.loads(p.read_text())['rows']
            lines.append(f"- wall time, smoke {part}: total {sum(r['wall_s'] for r in rs):.1f} s over {len(rs)} runs")
    lines += ['', f'Result (room-A rows, Rule 11a s1 / s3 / s4): {"PASS" if ok else "FAIL"}']
    (OUT / 'smoke.md').write_text('\n'.join(lines) + '\n')
    print('\n'.join(lines[-12:]))
    if not ok:
        sys.exit(1)


if __name__ == '__main__':
    cmd = sys.argv[1]
    sys.path[:0] = [str(ROOT / 'experiments'), str(ROOT / 'src')] if cmd != 'regress-dump' else []
    if cmd == 'regress-dump':
        regress_dump(sys.argv[2], sys.argv[3])
    elif cmd == 'regress':
        regress()
    elif cmd == 'envA':
        envA()
    elif cmd == 'envC':
        envC()
    elif cmd == 'equiv':
        equiv()
    elif cmd == 'repeat':
        repeat()
    elif cmd == 'repeat-one':
        repeat_one(sys.argv[2])
    elif cmd == 'ref-localize':
        ref_localize()
    elif cmd == 'localize':
        localize()
    elif cmd == 'smoke':
        smoke(sys.argv[2])
    elif cmd == 'smoke-md':
        smoke_md()
    else:
        raise ValueError(sys.argv)
