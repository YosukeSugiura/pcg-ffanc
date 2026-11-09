"""Revision 11 (docs/current/REVISION_RULE_11.md): equivalences of the new flags (Sec. 6.3) and structural checks.

- fd_block_gradient_mod = recursion A of gap_check4a (lag-truncated correlation, then the bin gain) and = the time-domain
  form of the MFBLMS of Lu, Chen, Qiu (2017), Eq. (6): w(k+1) = w(k) + mu M1 X^T e, M1 = leading M x M block of the
  circulant F^-1 M_f F (here with the minus sign of the error convention e = d + s*y)
- the new flags off (or set to their neutral values) reproduce the existing paths bit for bit
- RLS + det (cond.): theta = -inf -> RLS + det, theta = +inf -> plain R-RLS (lam 0.9999) without events
- EPCG solver 'exact' = dense windowed LS (and = the converged PCG)
The long, registered versions of the run-level checks are in experiments/revision11_preflight.py (seed 300, T = 5 s).
"""
import json
import sys
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src')); sys.path.insert(0, str(ROOT / 'experiments'))
from ffanc_norm.fd_fxnlms import direct_block_gradient, fd_block_gradient, fd_block_gradient_mod  # noqa: E402
from ffanc_norm.pcg_wls import PcgWls as EPCG, PcgWlsConfig as EPCGConfig  # noqa: E402  (former names)


def _recursion_A(xh, r, den, M, N, H):
    """Verbatim recursion-A gradient of experiments/gap_check4a.py (lines 64-67)."""
    X = np.fft.rfft(xh)
    ef = np.zeros(N); ef[-H:] = r
    c = np.fft.irfft(np.conj(X) * np.fft.rfft(ef), N); c[M:] = 0.0
    return np.fft.irfft(np.fft.rfft(c) / den, N)[:M]


def test_mod_gradient_equals_recursion_A_on_100_random_frames():
    rng = np.random.default_rng(20261107)
    N, H, M = 1024, 128, 512
    worst = 0.0
    for _ in range(100):
        xh = rng.standard_normal(N) * rng.uniform(0.1, 10.0)
        r = rng.standard_normal(H)
        den = rng.uniform(0.01, 5.0, N // 2 + 1)
        a = fd_block_gradient_mod(xh, r, den, M)
        b = _recursion_A(xh, r, den, M, N, H)
        worst = max(worst, float(np.max(np.abs(a - b)) / np.max(np.abs(b))))
    assert worst <= 1e-12


def test_mod_gradient_equals_lu_chen_qiu_time_domain_form():
    rng = np.random.default_rng(5)
    N, H, M = 256, 64, 128
    xh = rng.standard_normal(N); r = rng.standard_normal(H); den = rng.uniform(0.2, 3.0, N // 2 + 1)
    C = np.fft.irfft(np.fft.rfft(np.eye(N), axis=0) / den[:, None], n=N, axis=0)    # F^-1 M_f F (circulant)
    M1 = C[:M, :M]
    g_time = M1 @ direct_block_gradient(xh, r, M)            # constraint (first M lags) before normalization
    assert np.allclose(fd_block_gradient_mod(xh, r, den, M), g_time, rtol=1e-11, atol=1e-12)
    # the standard gradient normalizes all N lags first: [C X^T e (all N lags)]_{0..M-1}
    full = np.array([np.dot(r, np.roll(xh, m)[N - H:]) for m in range(N)])          # circular correlation, N lags
    assert np.allclose(fd_block_gradient(xh, r, den, M), (C @ full)[:M], rtol=1e-10, atol=1e-11)
    assert not np.allclose(fd_block_gradient(xh, r, den, M), g_time)               # the two differ for den != const


def test_mod_gradient_equals_standard_for_a_constant_denominator():
    rng = np.random.default_rng(9)
    N, H, M = 512, 128, 256
    xh = rng.standard_normal(N); r = rng.standard_normal(H); den = np.full(N // 2 + 1, 2.5)
    assert np.allclose(fd_block_gradient_mod(xh, r, den, M), fd_block_gradient(xh, r, den, M), rtol=1e-12, atol=1e-13)


# ---------------------------------------------------------------- run-level equivalences (short runs, T = 2 s)
@pytest.fixture(scope='module')
def sim():
    import eval_v2 as ev
    return ev


def _run(ev, method, prm, nz='ar1', sc='S2 src 30cm', seed=300, tt=2.0):
    return ev.D.P.run(ev.cfg_of('A', nz, sc), seed, method, dict(prm), tt, ev.D.CH)


def _same(a, b, keys=('total_power', 'uncontrolled_power', 'stable', 'failure', 'reset_hops')):
    for k in keys:
        x, y = a[k], b[k]
        if isinstance(x, list) and x and isinstance(x[0], float):
            assert np.asarray(x).tobytes() == np.asarray(y).tobytes(), k
        else:
            assert x == y, k


def _events(ev, nz='ar1', sc='S2 src 30cm', seed=300, tt=2.0):
    r = ev.D.P.run(ev.cfg_of('A', nz, sc), seed, 'E-PCG-F', dict(ev.MAIN), tt, ev.D.CH)
    return [[(int(h) + 1) * ev.H, int(t)] for h, t in zip(r['reset_hops'], r['loc_hist'])]


def test_mod_false_is_the_existing_fd_path(sim):
    a = _run(sim, 'fixed_binwise', {'mu': 0.3}); b = _run(sim, 'fixed_binwise', {'mu': 0.3, 'mod': False})
    _same(a, b)
    assert set(a) == set(b)                                   # no new keys in the result without the new methods


def test_mfblms_differs_from_fd(sim):
    a = _run(sim, 'fixed_binwise', {'mu': 0.3}); b = _run(sim, 'fixed_binwise', {'mu': 0.3, 'mod': True})
    assert np.asarray(a['total_power']).tobytes() != np.asarray(b['total_power']).tobytes()


def test_switching_that_never_switches_is_fd_fxnlms(sim):
    ev = sim
    a = _run(ev, 'fixed_binwise', {'mu': 0.3})
    for det in ('zeta', 'det'):
        p = {'mu_n': 0.3, 'mu_m': 0.1, 'sw_thr': -np.inf, 'sw_dwell': 4, 'sw_detect': det}
        if det == 'det':
            p['det_events'] = _events(ev)
        b = _run(ev, 'SW-FBLMS', p)
        _same(a, b, keys=('total_power', 'uncontrolled_power', 'stable', 'failure'))
        assert b['sw_log'] == [] and set(b['sw_modes']) == {'N'}


def test_switching_steps_follow_the_mode():
    import prototype_new_algorithms as P
    rng = np.random.default_rng(3)
    N, H, M = 256, 64, 128
    prm = {'mu_n': 0.3, 'mu_m': 0.1, 'sw_thr': 0.03, 'sw_dwell': 4, 'sw_detect': 'zeta'}
    for mode, fn, mu in (('N', fd_block_gradient, 0.3), ('M', fd_block_gradient_mod, 0.1), ('C', fd_block_gradient, 0.3)):
        S = {'mode': mode, 'dwell': 0, 'Jm': None, 'b': 0.745, 'zn': None, 'zd': None, 'zthr': 1.0, 'zmax': 0.0,
             'log': [], 'modes': []}
        xh = rng.standard_normal(N); err = rng.standard_normal(H); den = rng.uniform(0.5, 2.0, N // 2 + 1)
        P._sw_hop(S, prm, 0, xh, np.fft.rfft(xh), err, den, M, N, H)
        assert np.array_equal(S['step'], mu * fn(xh, err, den, M))
    assert abs((1 - 0.3 / 2) ** 2 + 0.3 ** 2 / 4 - 0.745) < 1e-12        # b of Rule 11 Sec. 3.4


def test_zeta_calibration_sequence():
    """Z-A: N -> M (dJ rule) -> calibration (sw_dwell hops of N) -> M with zeta_THR = max zeta of the calibration."""
    import prototype_new_algorithms as P
    rng = np.random.default_rng(4)
    N, H, M = 256, 64, 128
    prm = {'mu_n': 0.3, 'mu_m': 0.1, 'sw_thr': np.inf, 'sw_dwell': 2, 'sw_detect': 'zeta'}
    S = {'mode': 'N', 'dwell': 0, 'Jm': None, 'b': 0.745, 'zn': None, 'zd': None, 'zthr': None, 'zmax': 0.0,
         'log': [], 'modes': []}
    zs = []
    for b in range(12):                                   # decreasing error power: J_m decreases (0 <= dJ, Rule 11a)
        xh = rng.standard_normal(N); err = rng.standard_normal(H) * 0.5 ** b; den = rng.uniform(0.5, 2.0, N // 2 + 1)
        P._sw_hop(S, prm, b, xh, np.fft.rfft(xh), err, den, M, N, H)
        zs.append(S['zn'] / S['zd'])
    assert S['modes'][:6] == ['N', 'N', 'M', 'M', 'C', 'C']
    assert S['log'][0] == [1, 'M', 'dJ'] and S['log'][1] == [3, 'C', 'calibrate']
    assert S['log'][2][:3] == [5, 'M', 'calibrated'] and S['log'][2][3] == max(zs[4:6])


def test_rls_cond_inf_limits(sim):
    ev = sim
    events = _events(ev)
    assert events, 'vacuous: no event in the short run'
    det = {'lam': 0.9999, 'delta': 0.01, 'det_reset_w': False}
    a = _run(ev, 'R-RLS', dict(det, det_events=events))
    b = _run(ev, 'R-RLS', dict(det, det_events=events, det_cond_db=-np.inf, det_cond_k=32))
    _same(a, b)
    assert b['cond_log'] and all(x[-1] for x in b['cond_log'])
    c = _run(ev, 'R-RLS', {'lam': 0.9999, 'delta': 0.01})
    d = _run(ev, 'R-RLS', dict(det, det_events=events, det_cond_db=np.inf, det_cond_k=32))
    _same(c, d)
    assert d['cond_log'] and not any(x[-1] for x in d['cond_log'])


def test_rls_grow_none_is_the_existing_path(sim):
    a = _run(sim, 'R-RLS', {'lam': 0.9995, 'delta': 0.01}, tt=1.0)
    b = _run(sim, 'R-RLS', {'lam': 0.9995, 'delta': 0.01, 'det_grow': None}, tt=1.0)
    _same(a, b)
    with pytest.raises(ValueError):
        _run(sim, 'R-RLS', {'lam': 0.9995, 'delta': 0.01, 'det_grow': 'full'}, tt=0.5)


# ---------------------------------------------------------------- EPCG exact solver
def _fed_epcg(solver='pcg', n_hops=20, M=64, H=16, seed=0):
    rng = np.random.default_rng(seed)
    cfg = EPCGConfig(M=M, H=H, L_hops=8, detect=False, k=8, k_first=16, solver=solver)
    ep = EPCG(cfg)
    x = np.convolve(rng.standard_normal(n_hops * H + 200), [1.0, 0.7, 0.2])[200:200 + n_hops * H]
    d = np.convolve(x, rng.standard_normal(12))[:len(x)] + 0.01 * rng.standard_normal(len(x))
    for h in range(n_hops):
        ep.update(x[h * H:(h + 1) * H], d[h * H:(h + 1) * H])
    return ep


def test_exact_solver_is_the_dense_window_ls():
    ep = _fed_epcg()
    M = ep.cfg.M; ridge = ep.cfg.ridge * ep.r[0] + 1e-30
    Cm = ep._circ(ep.r)
    G = ep._XtX_dense(ep.t0, ep.stop) + ridge * np.eye(M)
    ref = np.linalg.solve(G, -ep.p)
    x = ep._exact_solve(Cm, ep.t0, ridge, -ep.p, True, None)
    assert np.allclose(x, ref, rtol=1e-8, atol=1e-10 * np.max(np.abs(ref)))
    xp = ep._pcg(Cm, ep.t0, ridge, -ep.p, np.zeros(M), 400, use_reg=True)
    assert np.allclose(x, xp, rtol=1e-6, atol=1e-8 * np.max(np.abs(ref)))
    # growing-order subspace: leading block, other taps zero (= limit of the masked PCG)
    m = 20
    xm = ep._exact_solve(Cm, ep.t0, ridge, -ep.p, True, m)
    assert np.all(xm[m:] == 0.0)
    assert np.allclose(xm[:m], np.linalg.solve(G[:m, :m], -ep.p[:m]), rtol=1e-8, atol=1e-10)
    xpm = ep._pcg(Cm, ep.t0, ridge, -ep.p, np.zeros(M), 400, use_reg=True, meff=m)
    assert np.allclose(xm, xpm, rtol=1e-6, atol=1e-8)


def test_solver_default_is_pcg_and_exact_runs():
    assert EPCGConfig().solver == 'pcg'
    a = _fed_epcg('pcg'); b = _fed_epcg('exact')
    assert np.all(np.isfinite(b.w)) and np.linalg.norm(a.w - b.w) / np.linalg.norm(b.w) < 0.5


# ---------------------------------------------------------------- grids fixed by the rule
def test_grid11_sizes_and_frozen_inputs_untouched():
    import hashlib
    import eval_v2 as ev
    import revision11_methods as R
    assert [len(R.GRID11[m][1]) for m in ('MFBLMS', 'RLS + det (cond.)', 'RLS + det + growth')] == [6, 4, 1]
    dg = R.dependent_grids(0.2)
    assert [len(dg[m][1]) for m in ('MFBLMS + det', 'switching FD-FxNLMS [6]', 'switching FD-FxNLMS + det')] == [7, 6, 6]
    assert all(p['mu'] == 0.2 and p['mod'] for p in dg['MFBLMS + det'][1])
    assert [p['det_cond_db'] for p in R.GRID11['RLS + det (cond.)'][1]] == [1.0, 2.0, 4.0, 8.0]
    assert len(R.BASE13) == 13 and 'RLS + CUSUM' in R.BASE13
    assert R.VARIANTS['G1'][1].get('grow_len') is None and 'grow_len' not in R.VARIANTS['G1'][1]
    assert {k for k in R.VARIANTS['G4'][1] if R.VARIANTS['G4'][1].get(k) != ev.MAIN.get(k)} | \
        {k for k in ev.MAIN if k not in R.VARIANTS['G4'][1]} == {'grow_len', 'adapt'}
    sel = ROOT / 'results/protocol_v2_sel/selected_e.json'
    assert hashlib.sha256(sel.read_bytes()).hexdigest() == \
        '76fa959eee7b431b9ecbb57f4e2f0614875e52035749c37287d3c33e516cc665'
    assert len(ev.GRID) == 12 and 'MFBLMS' not in ev.GRID


# ---------------------------------------------------------------- 2026-11-07 code review fixes (M-1, M-3, M-4, L-*)
def _R():
    import revision11_methods as R
    return R


FAKE_MACHINE = {'cpu_model': 'Test CPU', 'cpu_count': 2, 'cpu_flags_sha256': 'f' * 64, 'PRA_NUM_THREADS': '2',
                'pra_num_threads': 2, 'openblas_corename': 'Test', 'numpy_blas': None, 'python': '3.13.18',
                'executable': 'python3'}


def _env_files(R, tmp_path, monkeypatch, a_class='I', c_class='I', a_machine=None, c_machine=None):
    """results/r11_preflight/env_{A,C}.json stand-ins made on the (fake) current machine (Rule 11b Sec. 5, 8 c4 / c5);
    a_class / c_class None: the file is absent."""
    pre = tmp_path / 'pre'; pre.mkdir(exist_ok=True)
    monkeypatch.setattr(R, 'PRE_DIR', pre)
    monkeypatch.setattr(R, 'machine_fingerprint', lambda: dict(FAKE_MACHINE))
    for name, cls, mach, thr in (('A', a_class, a_machine, 3), ('C', c_class, c_machine, 2)):
        f = pre / f'env_{name}.json'
        if cls is None:
            f.unlink(missing_ok=True); continue
        m = dict(mach or FAKE_MACHINE, PRA_NUM_THREADS=str(thr), pra_num_threads=thr)
        f.write_text(json.dumps({'class': cls, 'pass': cls == 'I', 'machine': m}))


def _env_a(R, tmp_path, monkeypatch, passed=True):
    """env_A.json class I (path A) or F (path (b)), env_C.json class I, all on this (fake) machine."""
    _env_files(R, tmp_path, monkeypatch, a_class='I' if passed else 'F')


@pytest.fixture(autouse=True)
def _class_i(monkeypatch):
    """Selection tests run as env_C class I unless a test says otherwise (Rule 11b; no dependence on the real file)."""
    import revision11_select as S
    monkeypatch.setattr(S, 'current_class', lambda: 'I')


def test_read_jsonl_cut_last_line(tmp_path, monkeypatch):
    R = _R(); monkeypatch.setattr(R, 'OUT_DIRS', [tmp_path])
    p = tmp_path / 'runs_0.jsonl'
    good = b'{"a": 1}\n{"a": 2}\n'
    p.write_bytes(good + b'{"a": 3, "tp": [0.1')
    assert R.read_jsonl(p, 'skip') == [{'a': 1}, {'a': 2}] and p.read_bytes().endswith(b'0.1')   # never modified
    with pytest.raises(ValueError, match='no newline'):
        R.read_jsonl(p, 'strict')
    assert R.read_jsonl(p, 'repair') == [{'a': 1}, {'a': 2}]
    assert p.read_bytes() == good                                                              # complete lines kept
    assert R.read_jsonl(p, 'strict') == [{'a': 1}, {'a': 2}]
    p.write_bytes(b'{"a": 1}\n{"a": \n{"a": 2}\n')
    with pytest.raises(ValueError, match='malformed line 2'):
        R.read_jsonl(p, 'repair')
    assert R.read_jsonl(tmp_path / 'missing.jsonl') == []
    q = tmp_path.parent / 'outside.jsonl'                                    # repair outside the R11 dirs is refused
    q.write_bytes(b'{"a": 1}\n{"a"')
    with pytest.raises(PermissionError):
        R.read_jsonl(q, 'repair')
    assert q.read_bytes() == b'{"a": 1}\n{"a"'


def _fake_runner(calls):
    def run_record(name, kind, prm, room, nz, sc, sd, events=None, extra=None):
        calls.append((name, sd))
        rec = {'method': name, 'prm': prm, 'room': room, 'noise': nz, 'scen': sc, 'seed': sd,
               'tp': [float(sd), 0.5], 'up': [1.0, 1.0], 'ev': events}
        return rec, ([[sd * 128, sd]] if kind == 'E-PCG-F' else None)
    return run_record


def test_run_set_resume_after_a_cut_line(tmp_path, monkeypatch):
    """A worker killed while writing: the cut last line is dropped and that run redone; the files end byte-identical to
    an uninterrupted run (also when the events line of the key was written but its E-PCG record was cut)."""
    import zlib
    R = _R(); import revision11_rooms as RM
    monkeypatch.setattr(R, 'OUT_DIRS', [tmp_path])
    monkeypatch.setattr(R, 'check_runtime_env', lambda *a, **k: None)
    monkeypatch.setenv('SHARD', '0/2')
    calls = []; monkeypatch.setattr(R, 'run_record', _fake_runner(calls))
    meth = {'E-PCG': ('E-PCG-F', {'m': 1}), 'X': ('fixed_binwise', {'mu': 0.1}), 'E-PCG bank': ('E-PCG-F', {'m': 2})}
    combos = [('ar1', 'S2 cell'), ('harmonic', 'S2 cell')]
    seeds = list(range(800, 812))
    keys = [(nz, sc, sd) for nz, sc in combos for sd in seeds
            if zlib.crc32('|'.join(map(str, (nz, sc, sd))).encode()) % 2 == 0]
    assert len(keys) >= 3
    ref = tmp_path / 'ref'; RM.run_set('A', combos, ref, meth, seeds)
    runs = (ref / 'runs_0.jsonl').read_bytes(); dets = (ref / 'det_events_0.jsonl').read_bytes()
    rl = runs.split(b'\n')[:-1]; dl = dets.split(b'\n')[:-1]
    assert len(rl) == 3 * len(keys) and len(dl) == len(keys)
    # (a) cut in the middle of the last record of key 2 (method 'E-PCG bank')
    a = tmp_path / 'a'; a.mkdir()
    (a / 'runs_0.jsonl').write_bytes(b'\n'.join(rl[:5]) + b'\n' + rl[5][:17])
    (a / 'det_events_0.jsonl').write_bytes(b'\n'.join(dl[:2]) + b'\n')
    calls.clear(); RM.run_set('A', combos, a, meth, seeds)
    assert (a / 'runs_0.jsonl').read_bytes() == runs and (a / 'det_events_0.jsonl').read_bytes() == dets
    assert calls[0] == ('E-PCG bank', keys[1][2])                       # only the cut run is redone for key 2
    # (b) events line of key 3 written, its E-PCG record cut
    b = tmp_path / 'b'; b.mkdir()
    (b / 'runs_0.jsonl').write_bytes(b'\n'.join(rl[:6]) + b'\n' + rl[6][:40])
    (b / 'det_events_0.jsonl').write_bytes(b'\n'.join(dl[:3]) + b'\n')
    calls.clear(); RM.run_set('A', combos, b, meth, seeds)
    assert (b / 'runs_0.jsonl').read_bytes() == runs and (b / 'det_events_0.jsonl').read_bytes() == dets
    assert calls[:2] == [('E-PCG', keys[2][2]), ('X', keys[2][2])]
    # (c) cut events line: dropped, E-PCG redone, events line rewritten
    c = tmp_path / 'c'; c.mkdir()
    (c / 'runs_0.jsonl').write_bytes(b'\n'.join(rl[:6]) + b'\n')
    (c / 'det_events_0.jsonl').write_bytes(b'\n'.join(dl[:2]) + b'\n' + dl[2][:9])
    RM.run_set('A', combos, c, meth, seeds)
    assert (c / 'runs_0.jsonl').read_bytes() == runs and (c / 'det_events_0.jsonl').read_bytes() == dets
    # (d) a saved events line that the E-PCG re-run does not reproduce stops the worker
    d = tmp_path / 'd'; d.mkdir()
    (d / 'runs_0.jsonl').write_bytes(b'\n'.join(rl[:6]) + b'\n')
    (d / 'det_events_0.jsonl').write_bytes(b'\n'.join(dl[:2]) + b'\n' + dl[2].replace(b'"events": [[', b'"events": [[1') + b'\n')
    with pytest.raises(ValueError, match='other events'):
        RM.run_set('A', combos, d, meth, seeds)


def test_writes_outside_the_rule11_dirs_are_refused(tmp_path):
    R = _R()
    import revision11_holdout as HO
    assert R.HOLDOUT_BASE == 'saved' and HO.KINDS['base'] == ROOT / 'results/final_eval_holdout'
    for p in (ROOT / 'results/final_eval_holdout/provenance.json', ROOT / 'results/eval_roomB_x2/summary.md',
              ROOT / 'results/det_events/ev.jsonl', ROOT / 'results/final_eval_holdout_r11_envC/runs_0.jsonl',
              tmp_path / 'x.json'):
        with pytest.raises(PermissionError):
            R.out_path(p)
    for p in (R.SEL_DIR / 'runs_B1_0.jsonl', R.HOLD_DIR / 'x', R.ABL_DIR, ROOT / 'results/eval_roomC_h/summary.md'):
        assert R.out_path(p) == p
    with pytest.raises(ValueError, match='R11_HOLDOUT_BASE=envC'):            # review M-1: provenance base / run base
        HO._check_base()
    with pytest.raises(PermissionError):
        R.provenance(HO.KINDS['base'], {'stage': 'x'})


def test_provenance_files_are_never_overwritten(tmp_path, monkeypatch):
    R = _R(); monkeypatch.setattr(R, 'OUT_DIRS', [tmp_path]); _env_a(R, tmp_path, monkeypatch)
    assert R.free_name(tmp_path, 'provenance_B1') == tmp_path / 'provenance_B1.json'
    R.write_new(tmp_path / 'provenance_B1.json', '{}\n')
    with pytest.raises(FileExistsError):
        R.write_new(tmp_path / 'provenance_B1.json', '{}\n')
    assert R.free_name(tmp_path, 'provenance_B1') == tmp_path / 'provenance_B1_resume1.json'
    d = R.provenance(tmp_path, {'stage': 'tuning B1'}, name='provenance_B1')
    assert (tmp_path / 'provenance_B1_resume1.json').exists() and d['rule_sha256'] == R.RULE_SHA256
    assert (tmp_path / 'provenance_B1.json').read_text() == '{}\n'
    assert R.free_name(tmp_path, 'provenance_B2') == tmp_path / 'provenance_B2.json'


def test_environment_check(monkeypatch):
    R = _R()
    good = {'numpy': '2.5.3', 'scipy': '1.18.1', 'pyroomacoustics': '0.10.1', 'numba': '0.68.1', 'soundfile': '0.14.0'}
    monkeypatch.setattr(R, 'installed_versions', lambda names: {n: good[n] for n in names})
    monkeypatch.setattr(R.platform, 'python_version', lambda: '3.13.18')
    monkeypatch.setattr(R, 'pra_threads_now', lambda: ('2', 2))
    assert R.check_env('C') and R.check_env('C', meas=True)
    with pytest.raises(RuntimeError, match='numpy'):
        R.check_env('A')                                   # environment-A job in environment C
    monkeypatch.setattr(R, 'installed_versions', lambda names: {n: dict(good, numba=None)[n] for n in names})
    assert R.check_env('C')
    with pytest.raises(RuntimeError, match='numba'):
        R.check_env('C', meas=True)
    monkeypatch.setattr(R.platform, 'python_version', lambda: '3.12.3')
    with pytest.raises(RuntimeError, match='python'):
        R.check_env('C')
    a = {'numpy': '2.3.5', 'scipy': '1.17.0', 'pyroomacoustics': '0.10.1'}
    monkeypatch.setattr(R, 'installed_versions', lambda names: {n: a[n] for n in names})
    with pytest.raises(RuntimeError, match='pra_threads'):
        R.check_env('A')                                   # Rule 11b: environment A needs PRA_NUM_THREADS=3
    monkeypatch.setattr(R, 'pra_threads_now', lambda: ('3', 3))
    assert R.check_env('A')
    assert R.holdout_env() == 'A'


def test_cond_restart_finite_theta_by_hand():
    """P_pre = mean of the hop powers of the last K hops ending at or before tau; P_post = mean square of the a priori
    residual on [tau, stop); restart iff 10 log10(P_post / P_pre) >= theta."""
    from prototype_new_algorithms import _cond_restart
    H = 4
    hp = [100.0] * 7 + [1.0, 2.0, 3.0] + [500.0]          # hop 10 (500) ends after tau -> not in P_pre
    tau, stop = 10 * H + 2, 11 * H                         # tau // H = 10 -> hops 7, 8, 9 (K = 3)
    eps = np.full(stop - tau, 2.0)                         # P_post = 4, P_pre = 2 -> +3.0103 dB
    for th, want in ((2.0, True), (3.0, True), (4.0, False), (-np.inf, True), (np.inf, False)):
        log = []
        assert _cond_restart({'det_cond_db': th, 'det_cond_k': 3}, hp, log, 10, stop, tau, eps, H) is want
        b, s, t, ratio, n_pre, r = log[0]
        assert (b, s, t, n_pre, r) == (10, stop, tau, 3, want) and ratio == pytest.approx(10 * np.log10(2.0), abs=1e-12)
    log = []                                               # K larger than the history: all complete hops
    _cond_restart({'det_cond_db': 1.0, 'det_cond_k': 32}, hp, log, 10, stop, tau, eps, H)
    assert log[0][4] == 10 and log[0][3] == pytest.approx(10 * np.log10(4.0 / np.mean(hp[:10])), abs=1e-12)
    log = []                                               # no complete hop before tau: restart unless theta = +inf
    assert _cond_restart({'det_cond_db': 8.0, 'det_cond_k': 3}, hp, log, 0, H, 2, eps[:2], H) is True
    assert log[0][3] is None and log[0][4] == 0
    assert _cond_restart({'det_cond_db': np.inf}, hp, [], 0, H, 2, eps[:2], H) is False


def test_det_grow_tap_count():
    import inspect
    import prototype_new_algorithms as P
    M = 512
    assert [P._grow_taps(n, M) for n in (1, 2, 3, 4, 5, 100, 2 * M - 1, 2 * M, 5 * M)] == \
        [1, 1, 1, 2, 2, 50, M - 1, M, M]
    assert 'u[_grow_taps(t - _grow0[0] + 1, M):] = 0.0' in inspect.getsource(P)


def _cfg_rows(group, idx, prm, value, fail_seed=None):
    R = _R(); rows = []
    for sd in R.TUNE:
        for nz, sc in R.COMBOS15:
            f = int(fail_seed is not None and sd == fail_seed)
            rows.append({'group': group, 'cfg': idx, 'prm': prm, 'noise': nz, 'scen': sc, 'seed': sd, 'fail': f,
                         'A1': value, 'A2': value})
            if f:
                return rows
    return rows


def test_mfblms_edge_extension():
    import revision11_select as S
    R = _R()
    grid = [p for _, p in [('fixed_binwise', p) for p in R.GRID11['MFBLMS'][1]]]
    mus = lambda rs: [p['mu'] for _, p in S.mfblms_cfgs(rs)]
    base = lambda best: [r for i, p in enumerate(grid) for r in _cfg_rows('MFBLMS', i, p, -10.0 - (i == best))]
    assert mus([]) == list(R.MU_GRID)
    assert mus(base(2)) == list(R.MU_GRID) and S.mfblms_selected(base(2)) == 0.15        # interior: no extension
    rs = base(5)                                                                          # upper edge 0.3
    assert mus(rs)[6:] == [0.35] and S.mfblms_selected(rs) is None                       # pending outer point
    up1 = rs + _cfg_rows('MFBLMS', 6, {'mu': 0.35, 'mod': True}, -12.0)
    assert mus(up1)[6:] == [0.35, 0.4] and S.mfblms_selected(up1) is None
    up2 = up1 + _cfg_rows('MFBLMS', 7, {'mu': 0.4, 'mod': True}, -13.0)
    assert mus(up2)[6:] == [0.35, 0.4] and S.mfblms_selected(up2) == 0.4                 # at most two steps
    up2b = up1 + _cfg_rows('MFBLMS', 7, {'mu': 0.4, 'mod': True}, -11.5)
    assert S.mfblms_selected(up2b) == 0.35
    fl = rs + _cfg_rows('MFBLMS', 6, {'mu': 0.35, 'mod': True}, -12.0, fail_seed=R.TUNE[3])
    assert mus(fl)[6:] == [0.35] and S.mfblms_selected(fl) == 0.3                        # outer point fails
    worse = rs + _cfg_rows('MFBLMS', 6, {'mu': 0.35, 'mod': True}, -10.5)
    assert mus(worse)[6:] == [0.35] and S.mfblms_selected(worse) == 0.3
    lo = base(0)                                                                          # lower edge 0.05: halves
    assert mus(lo)[6:] == [0.025]
    lo1 = lo + _cfg_rows('MFBLMS', 6, {'mu': 0.025, 'mod': True}, -12.0)
    assert mus(lo1)[6:] == [0.025, 0.0125]
    allfail = [r for i, p in enumerate(grid) for r in _cfg_rows('MFBLMS', i, p, -10.0, fail_seed=R.TUNE[0])]
    assert S.mfblms_selected(allfail) == 'none' and mus(allfail) == list(R.MU_GRID)


def test_outer_decision_branches():
    import revision11_select as S
    R = _R()
    first, second = [R.OUTER['RLS'][0]], [R.OUTER['RLS'][1]]
    ref = R.EXISTING_SCORE['RLS']                                                          # -13.86
    g1 = lambda v, **k: _cfg_rows('RLS [outer 1]', 0, first[0][1], v, **k)
    g2 = lambda v, **k: _cfg_rows('RLS [outer 2]', 0, second[0][1], v, **k)
    dec = lambda rs: S.outer_decision(rs, 'RLS', first, second)
    assert dec([])['status'] == 'open'
    d = dec(g1(-20.0, fail_seed=R.TUNE[5]))
    assert d['status'] == 'done' and d['row'] is None and d['decision'].startswith('edge')
    for v in (ref + 0.5, ref - 0.005):                                                    # not better by > 0.01 dB
        d = dec(g1(v)); assert d['row'] is None and d['decision'].startswith('interior')
    d = dec(g1(-14.0)); assert d['status'] == 'open' and d['pending'] == 'RLS [outer 2]'
    d = dec(g1(-14.0) + g2(-14.2))
    assert d['status'] == 'done' and d['row']['params'] == second[0][1] and d['row']['score'] == pytest.approx(-14.2)
    d = dec(g1(-14.0) + g2(-14.005))                                                       # within 0.01 dB: first step
    assert d['row']['params'] == first[0][1] and d['second_decision'] == 'not better than the first step'
    d = dec(g1(-14.0) + g2(-15.0, fail_seed=R.TUNE[0]))
    assert d['row']['params'] == first[0][1] and d['second_decision'] == 'failed'
    f2 = R.OUTER_OPT['FDKF']                                                               # no second step defined
    rs = _cfg_rows('FDKF [outer 1]', 0, f2[0][1], R.EXISTING_SCORE['FDKF'] - 1.0)
    d = S.outer_decision(rs, 'FDKF', f2, None)
    assert d['status'] == 'done' and d['row']['params'] == f2[0][1] and 'no second step' in d['note']
    ck = R.OUTER_OPT['RLS + CUSUM']                                                        # several points: best one
    rs = [r for i, (k, p) in enumerate(ck) for r in _cfg_rows('RLS + CUSUM [outer 1]', i, p, -30.0 + i)]
    assert S.outer_decision(rs, 'RLS + CUSUM', ck, None)['row']['params'] == ck[0][1]
    stage = S.stage_cfgs('C', g1(-14.0))                                                   # second step queued last
    assert stage[-1][0] == 'RLS [outer 2]' and not any(g == 'VFF-RLS [outer 2]' for g, *_ in stage)


def test_wiener_distance():
    import revision11_summary as SU
    seeds = [800, 801, 802]
    Mx = {('m', 'ar1', 'S8', sd): {'A2': a, 'fail': f} for sd, a, f in zip(seeds, (-5.0, -6.0, 0.0), (0, 0, 1))}
    bound = {(800, 'ar1'): -6.0, (801, 'ar1'): -8.0, (802, 'ar1'): -7.0}
    md, q1, q3, n = SU.wiener_distance(Mx, bound, ['m'], [('ar1', 'S8')], seeds)[('m', 'ar1')]
    assert n == 2 and md == pytest.approx(1.5) and q1 == pytest.approx(1.25) and q3 == pytest.approx(1.75)


# ---------------------------------------------------------------- Rule 11a (B-1, B-2, M-2)
def _sw_state():
    return {'mode': 'N', 'dwell': 0, 'Jm': None, 'b': 0.745, 'zn': None, 'zd': None, 'zthr': None, 'zmax': 0.0,
            'log': [], 'modes': []}


def _sw_feed(S, prm, amps, seed=5):
    import prototype_new_algorithms as P
    rng = np.random.default_rng(seed)
    N, H, M = 256, 64, 128
    e0 = rng.standard_normal(H); e0 /= np.sqrt(np.mean(e0 ** 2))          # unit power: J(k) = amp^2 exactly
    trace = []
    for b, a in enumerate(amps):
        xh = rng.standard_normal(N); den = rng.uniform(0.5, 2.0, N // 2 + 1)
        jm_old = S['Jm']
        P._sw_hop(S, prm, b, xh, np.fft.rfft(xh), a * e0, den, M, N, H)
        trace.append(((jm_old if jm_old is not None else a * a) - S['Jm'], S['Jm'], S['mode']))
    return trace


@pytest.mark.parametrize('detect', ['zeta', 'det'])
def test_sw_no_switch_while_jm_increases(detect):
    """Rule 11a Sec. 1.2: N -> M needs 0 <= dJ < thr * J_m and dwell >= M_dwell; while J_m increases (dJ < 0) the
    algorithm stays in N whatever the threshold (the former rule switched here, review B-1)."""
    prm = {'mu_n': 0.3, 'mu_m': 0.1, 'sw_thr': 0.1, 'sw_dwell': 4, 'sw_detect': detect}
    S = _sw_state()
    tr = _sw_feed(S, prm, [1.0] + [1.0 * 1.3 ** k for k in range(1, 20)])     # error growing for 19 hops
    assert all(dj < 0 for dj, _, _ in tr[1:]) and S['log'] == [] and set(S['modes']) == {'N'}
    S = _sw_state()                                                            # J(0) = J_m(-1): dJ(0) = 0
    tr = _sw_feed(S, prm, [1.0] * 6)
    assert tr[0][0] == 0.0 and S['log'][0] == [3, 'M', 'dJ'] and S['modes'][:5] == ['N'] * 4 + ['M']


def test_sw_switches_after_dwell_when_jm_decreases_slowly():
    prm = {'mu_n': 0.3, 'mu_m': 0.1, 'sw_thr': 0.03, 'sw_dwell': 4, 'sw_detect': 'det'}
    S = _sw_state()
    amps = [1.0, 0.5, 0.25] + [0.25 * 0.995 ** k for k in range(1, 40)]       # fast, then slow decrease
    tr = _sw_feed(S, prm, amps)
    first = S['log'][0][0]
    assert all(dj >= 0 for dj, _, _ in tr)
    # no switch before the dwell, and none while the relative decrease is >= the threshold
    assert first >= 3 and all(dj >= 0.03 * jm for dj, jm, _ in tr[3:first])
    assert 0.0 <= tr[first][0] < 0.03 * tr[first][1] and S['modes'][first + 1] == 'M'


def test_sw_zb_event_response(sim):
    """Rule 11a Sec. 5.6: Z-B switches M -> N at the event hop (no dwell); N -> M by the dJ rule only."""
    ev = sim
    events = _events(ev)
    assert events
    p = {'mu_n': 0.3, 'mu_m': 0.1, 'sw_thr': 0.1, 'sw_dwell': 4, 'sw_detect': 'det', 'det_events': events}
    r = _run(ev, 'SW-FBLMS', p)
    ev_hops = {e[0] // ev.H - 1 for e in events}
    for entry in r['sw_log']:
        if entry[1] == 'N':
            assert entry[2] == 'event' and entry[0] in ev_hops
        else:
            assert entry[1] == 'M' and entry[2] == 'dJ'
    modes = r['sw_modes']
    for b, m, why in (x[:3] for x in r['sw_log']):
        if why == 'event':
            assert modes[b] == 'N'


def _short(ev, prm, tt, events=None):
    ev.D.P.RETURN_SIGNALS = True
    try:
        p = dict(prm)
        if events is not None:
            p['det_events'] = events
        return ev.D.P.run(ev.cfg_of('A', 'ar1', 'S2 src 30cm'), 300, 'R-RLS', p, tt, ev.D.CH)
    finally:
        ev.D.P.RETURN_SIGNALS = False


def test_growth_version_i_restart_zeroes_the_tail(sim):
    """Rule 11a Sec. 2.2 (c2): at a restart w[1:] = 0 and the order grows as max(n // 2, 1); the run ends n < 2M
    samples after tau, so every tap >= max(n // 2, 1) is exactly 0 (and is not without the growth)."""
    import revision11_methods as R
    ev = sim
    cfg = ev.cfg_of('A', 'ar1', 'S2 src 30cm'); M = int(cfg['controller_length']); H = int(cfg['hop_length'])
    tt = 0.3; n_all = int(tt * int(cfg['sample_rate'])) // H * H        # the run processes whole hops only
    stop = (n_all // H - 2) * H; tau = stop - 40
    gi = R.GRID11['RLS + det + growth'][1][0]
    r = _short(ev, gi, tt, [[stop, tau]]); r0 = _short(ev, R.BASE13['RLS + det'][1], tt, [[stop, tau]])
    n = n_all - tau; m = max(n // 2, 1)
    assert n < 2 * M and len(r['reset_hops']) == 1
    w = np.asarray(r['w_final'])
    assert not np.any(w[m:]) and np.count_nonzero(w[:m]) == m
    assert np.count_nonzero(np.asarray(r0['w_final'])[m:]) > 0
    # (c1, short form) no event: version (i) == R-RLS lam 0.9999, delta 0.01 bit for bit
    a = _short(ev, gi, 0.5, []); b = _short(ev, {'lam': 0.9999, 'delta': 0.01}, 0.5)
    for k in ('total_power', 'uncontrolled_power', 'e', 'w_final'):
        assert np.asarray(a[k]).tobytes() == np.asarray(b[k]).tobytes(), k


def test_growth_version_ii_from_start(sim):
    import revision11_methods as R
    ev = sim
    tt = 0.1; n = int(tt * 8000) // 128 * 128; m = max(n // 2, 1)          # whole hops (H = 128)
    gii = R.GRID11['RLS + det + growth (from start)'][1][0]
    assert gii['det_grow_start'] is True and gii['det_grow'] == 'half'
    w2 = np.asarray(_short(ev, gii, tt, [])['w_final'])
    w1 = np.asarray(_short(ev, R.GRID11['RLS + det + growth'][1][0], tt, [])['w_final'])
    assert not np.any(w2[m:]) and np.count_nonzero(w2[:m]) == m and np.count_nonzero(w1[m:]) > 0
    with pytest.raises(ValueError, match='det_grow_start needs det_grow'):
        _short(ev, {'lam': 0.9999, 'delta': 0.01, 'det_grow_start': True}, 0.05)


def test_growth_groups_and_event_use():
    import revision11_methods as R
    import revision11_select as S
    assert R.GROUPS_C == ('RLS + det (cond.)', 'RLS + det + growth', 'RLS + det + growth (from start)')
    for g in R.GROUPS_C:
        k, grid = R.GRID11[g]
        assert R.needs_events(g, k, grid[0]) and g in R.DET_NEW
        assert R.needs_events(g + ' (extended grid)', k, grid[0])
    assert 'det_grow_start' not in R.GRID11['RLS + det + growth'][1][0]
    order = [g for g, *_ in S.stage_cfgs('C', [])]
    firsts = [order.index(x) for x in ('RLS + det (cond.)', 'RLS + det + growth', 'RLS + det + growth (from start)',
                                        'RLS [outer 1]', 'VFF-RLS [outer 1]', 'SFTF-H + det [outer 1]',
                                        'RLS + CUSUM [outer 1]', 'FD-FxNLMS [outer 1]')]
    assert firsts == sorted(firsts)                                           # Rule 11a Sec. 5.3 order


def test_rule11a_sha_and_provenance_fields(tmp_path, monkeypatch):
    import hashlib
    import revision11_methods as R
    assert R.rule_matches(R.RULE11A, R.RULE11A_SHA256) and R.check_rules()   # public copy: via REDACTION_MANIFEST
    monkeypatch.setattr(R, 'OUT_DIRS', [tmp_path]); _env_a(R, tmp_path, monkeypatch)
    d = R.provenance(tmp_path, {'stage': 'x'})
    assert d['rule11a_sha256'] == R.RULE11A_SHA256 and d['holdout_base'] == 'envA' and d['rule_sha256'] == R.RULE_SHA256
    monkeypatch.setattr(R, 'RULE11A_SHA256', '0' * 64)
    with pytest.raises(ValueError, match='11a'):
        R.check_rules()
    with pytest.raises(ValueError, match='11a'):
        R.provenance(tmp_path, {'stage': 'x'})


def test_inadmissible_groups_are_reported_and_the_selection_completes(tmp_path, monkeypatch):
    """Rule 11a Sec. 4: MFBLMS all failing -> MFBLMS + the 3 derived groups in 'inadmissible', B2 has no run,
    complete = true once C is done, none of them in new_rows; an inadmissible C group is reported likewise."""
    import json
    import revision11_methods as R
    import revision11_select as S
    monkeypatch.setattr(R, 'OUT_DIRS', [tmp_path]); monkeypatch.setattr(S, 'OUT', tmp_path)
    rs = [r for i, p in enumerate(R.GRID11['MFBLMS'][1]) for r in _cfg_rows('MFBLMS', i, p, -10.0, fail_seed=R.TUNE[0])]
    assert S.mfblms_selected(rs) == 'none' and S.stage_cfgs('B2', rs) == []
    for g, i, k, p in S.stage_cfgs('C', rs):
        if g == 'RLS + det + growth (from start)':
            rs += _cfg_rows(g, i, p, -9.0, fail_seed=R.TUNE[2])
        elif g.endswith('[outer 1]'):
            rs += _cfg_rows(g, i, p, 0.0)                                       # outer points: interior
        else:
            rs += _cfg_rows(g, i, p, -11.0 - i)
    assert not any(g.endswith('[outer 2]') for g, *_ in S.stage_cfgs('C', rs))
    monkeypatch.setattr(S, '_records', lambda mode='skip': rs)
    S.summary()
    data = json.loads((tmp_path / 'selected.json').read_text())
    bad = {x['group']: x['reason'] for x in data['inadmissible']}
    assert bad == {'MFBLMS': 'no admissible configuration', 'MFBLMS + det': 'MFBLMS has no admissible step',
                   'switching FD-FxNLMS [6]': 'MFBLMS has no admissible step',
                   'switching FD-FxNLMS + det': 'MFBLMS has no admissible step',
                   'RLS + det + growth (from start)': 'no admissible configuration'}
    assert data['complete'] is True and data['stages'] == {'B1': True, 'B2': True, 'C': True}
    assert set(data['new_rows']) == {'RLS + det (cond.)', 'RLS + det + growth'}
    assert data['new_rows']['RLS + det (cond.)']['params']['det_cond_db'] == 8.0          # lowest score (-14)
    assert 'Groups without an admissible configuration' in (tmp_path / 'selection.md').read_text()


def test_holdout_base_must_match_env_a(tmp_path, monkeypatch):
    """Review N-M1 / Rule 11b Sec. 5: the recorded holdout_base follows R11_HOLDOUT_BASE and must agree with the path
    decided on this machine (env_A.json class I -> envA, else envC) in every job."""
    R = _R()
    _env_a(R, tmp_path, monkeypatch, passed=True)
    assert R.check_holdout_base() == 'envA'
    _env_a(R, tmp_path, monkeypatch, passed=False)
    with pytest.raises(ValueError, match='export R11_HOLDOUT_BASE=envC'):
        R.check_holdout_base()
    monkeypatch.setattr(R, 'OUT_DIRS', [tmp_path])
    with pytest.raises(ValueError, match='contradicts env_A.json'):
        R.provenance(tmp_path, {'stage': 'x'})
    monkeypatch.setattr(R, 'HOLDOUT_BASE', 'envC')
    assert R.check_holdout_base() == 'envC' and R.provenance(tmp_path, {'stage': 'x'})['holdout_base'] == 'envC'
    (tmp_path / 'pre' / 'env_A.json').unlink()                         # no env_A.json -> path (b)
    assert R.check_holdout_base() == 'envC'


def test_env_records_from_this_machine_only(tmp_path, monkeypatch):
    """Rule 11b Sec. 5 / R-3: env_A.json of another machine (even class I) -> path (b); env_A class K -> (b);
    env_C.json missing / foreign / class F / made before 11b -> stop."""
    R = _R()
    other = dict(FAKE_MACHINE, cpu_model='Other CPU')
    _env_files(R, tmp_path, monkeypatch, a_class='I', a_machine=other)
    assert R.holdout_base_wanted() == 'envC'
    _env_files(R, tmp_path, monkeypatch, a_class='K')
    assert R.holdout_base_wanted() == 'envC'
    _env_files(R, tmp_path, monkeypatch, a_class='I')
    assert R.holdout_base_wanted() == 'envA' and R.env_class() == 'I'
    _env_files(R, tmp_path, monkeypatch, c_class='K')
    assert R.env_class() == 'K'
    for kw, msg in (({'c_class': None}, 'missing'), ({'c_machine': other}, 'another machine'), ({'c_class': 'F'}, 'class F')):
        _env_files(R, tmp_path, monkeypatch, **kw)
        with pytest.raises(ValueError, match=msg):
            R.check_holdout_base()
    _env_files(R, tmp_path, monkeypatch)
    (tmp_path / 'pre' / 'env_C.json').write_text(json.dumps({'pass': True, 'machine': dict(FAKE_MACHINE)}))
    with pytest.raises(ValueError, match='no class'):
        R.env_class()
    _env_files(R, tmp_path, monkeypatch)                     # env_C made with the wrong pra thread count
    (tmp_path / 'pre' / 'env_C.json').write_text(json.dumps({'class': 'I', 'machine': dict(FAKE_MACHINE, pra_num_threads=3)}))
    with pytest.raises(ValueError, match='pra threads'):
        R.env_class()


# ---------------------------------------------------------------- review N-B1: summaries end to end on synthetic records
def _synth_rec(method, prm, nz, sc, sd, gain_db, nh, extra=None):
    rng = np.random.default_rng(abs(hash((method, nz, sc, sd))) % 2 ** 32)
    up = (1.0 + 0.01 * (sd % 7)) * np.ones(nh)
    g = gain_db + 0.5 * rng.standard_normal()
    tp = up * 10 ** (g / 10)
    rec = {'method': method, 'prm': prm, 'room': 'A', 'noise': nz, 'scen': sc, 'seed': sd, 'flag_stable': True,
           'tp': tp.tolist(), 'up': up.tolist(), 'hops_full': nh}
    rec.update(extra or {})
    return rec


def _write_runs(path, recs):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(''.join(json.dumps(r) + '\n' for r in recs))



def test_summaries_end_to_end_on_synthetic_records(tmp_path, monkeypatch):
    """base(), ablation(), new() and set_summary() (room set and M-S with the Wiener distance) run to the end on small
    synthetic record sets (2 cells, 6 seeds, 2 prespecified baselines; the statistics are not checked here)."""
    R = _R()
    import revision11_summary as SU
    import revision11_rooms as RM
    combos = [('ar1', 'S2 src 30cm'), ('harmonic', 'S8 stationary')]
    seeds = list(range(800, 806))
    base13 = {'RLS + det': R.BASE13['RLS + det'], 'FD-FxNLMS': R.BASE13['FD-FxNLMS']}
    variants = {g: R.VARIANTS[g] for g in ('G1', 'G2')}
    new_rows = {'MFBLMS': {'kind': 'fixed_binwise', 'params': {'mu': 0.1, 'mod': True}, 'score': -10.0}}
    dirs = {k: tmp_path / k for k in ('old', 'abl', 'hold', 'sel', 'room', 'prev', 'meas')}
    for k, v in (('COMBOS15', combos), ('HOLDOUT', seeds), ('BASE13', base13), ('VARIANTS', variants),
                 ('OLD_HOLD', dirs['old']), ('ABL_DIR', dirs['abl']), ('HOLD_DIR', dirs['hold']), ('SEL_DIR', dirs['sel']),
                 ('HOLDOUT_BASE', 'envC'), ('OUT_DIRS', [tmp_path])):
        monkeypatch.setattr(R, k, v)
    nh = SU.NH
    gains = {'E-PCG': -14.0, 'E-PCG bank': -14.5, 'RLS + det': -12.0, 'FD-FxNLMS': -10.0,
             'PCG-WLS (fixed order)': -13.0, 'PCG-WLS (restart)': -13.5, 'MFBLMS': -9.0}
    meth = {**{m: v for m, v in base13.items()}, **R.PROP}
    old = [_synth_rec(m, v[1], nz, sc, sd, gains[m], nh) for m, v in meth.items() for nz, sc in combos for sd in seeds]
    _write_runs(dirs['old'] / 'runs_0.jsonl', old[::2]); _write_runs(dirs['old'] / 'runs_1.jsonl', old[1::2])
    SU.base()                                                            # writes old/metrics.jsonl and summary.md
    assert (dirs['old'] / 'metrics.jsonl').exists() and 'Counts:' in (dirs['old'] / 'summary.md').read_text()
    abl = [_synth_rec(v[0], v[1], nz, sc, sd, gains[v[0]], nh, {'detections': [[640, 600]]})
           for v in variants.values() for nz, sc in combos for sd in seeds]
    _write_runs(dirs['abl'] / 'runs_0.jsonl', abl)
    SU.ablation()
    assert '(iii) G1 - RLS + det' in (dirs['abl'] / 'summary.md').read_text()
    dirs['sel'].mkdir()
    (dirs['sel'] / 'selected.json').write_text(json.dumps({'complete': True, 'new_rows': new_rows}))
    hold = [_synth_rec('MFBLMS', new_rows['MFBLMS']['params'], nz, sc, sd, gains['MFBLMS'], nh)
            for nz, sc in combos for sd in seeds]
    _write_runs(dirs['hold'] / 'runs_1.jsonl', hold)
    SU.new()
    assert 'F1: E-PCG vs the 1 new baselines' in (dirs['hold'] / 'summary.md').read_text()
    # 11-D style set: E-PCG, the 2 baselines, MFBLMS, bank; like-for-like against a synthetic 480-519 record
    allm = RM.all_methods()
    assert list(allm) == ['E-PCG', 'RLS + det', 'FD-FxNLMS', 'MFBLMS', 'E-PCG bank']
    room = [_synth_rec(m, v[1], nz, sc, sd, gains[m], nh) for m, v in allm.items() for nz, sc in combos for sd in seeds]
    common = ['RLS + det', 'FD-FxNLMS']
    prev_seeds = list(range(480, 520))
    prev = {(m, nz, sc, sd): {'method': m, 'noise': nz, 'scen': sc, 'seed': sd, 'fail': 0,
                              'A1': gains[m] + 0.1 * (sd % 5), 'A2': gains[m] - 0.1 * (sd % 3)}
            for m in common + ['E-PCG', 'E-PCG bank'] for nz, sc in combos for sd in prev_seeds}
    dirs['prev'].mkdir()
    (dirs['prev'] / 'metrics.jsonl').write_text(''.join(json.dumps(v) + '\n' for v in prev.values()))
    md = []
    for prop in ('E-PCG', 'E-PCG bank'):
        rows, _ = SU.family(prev, prop, common, combos, prev_seeds, hl=False)
        md += [f'## {prop} vs baselines (saved)', '| baseline | noise | cell | a | b | c | d | label |']
        md += [f"| {r['baseline']} | {r['noise']} | {r['cell']} | 0 | 0 | 0 | 0 | {r['label']} |" for r in rows]
    (dirs['prev'] / 'summary.md').write_text('\n'.join(md) + '\n')
    for name, wiener in (('room', None), ('meas', {(sd, nz): -12.0 for sd in seeds for nz, _ in combos})):
        _write_runs(dirs[name] / 'runs_0.jsonl', room)
        SU.set_summary(dirs[name], combos, dirs['prev'], common, f'synthetic {name}', wiener=wiener)
        text = (dirs[name] / 'summary.md').read_text()
        assert 'F3: E-PCG vs baselines' in text and 'agreement' in text and 'E-PCG bank - E-PCG' in text
        assert ('Distance to the Wiener lower bound' in text) == (wiener is not None)


# ---------------------------------------------------------------- Rule 11b (R-1 .. R-5)
def test_pra_default_threads_is_cpu_count_even_with_omp_1():
    """Premise of Rule 11b Sec. 1.1 (pyroomacoustics 0.10.1): OMP/MKL do not set the RIR thread count; only
    PRA_NUM_THREADS does (a future pra release changing this should be noticed)."""
    import os
    import subprocess
    env = {k: v for k, v in os.environ.items() if k != 'PRA_NUM_THREADS'}
    env.update(OMP_NUM_THREADS='1', MKL_NUM_THREADS='1')
    code = 'import os, pyroomacoustics as p; print(p.constants.get("num_threads"), os.cpu_count())'
    a, b = subprocess.run([sys.executable, '-c', code], env=env, capture_output=True, text=True, check=True).stdout.split()
    assert a == b
    env['PRA_NUM_THREADS'] = '3'
    out = subprocess.run([sys.executable, '-c', code], env=env, capture_output=True, text=True, check=True).stdout.split()
    assert out[0] == '3'


def test_pipeline_pra_threads_match_envs():
    import revision11_pipeline as PL
    R = _R()
    assert {k: int(v) for k, v in PL.PRA_THREADS.items()} == {k: v['pra_threads'] for k, v in R.ENVS.items()} == \
        {'A': 3, 'C': 2}


def _case(tp_new, up_new, tp_old, up_old, ev_new=None, ev_old=None, flag=True, hops=None):
    import revision11_preflight as PF
    import revision11_methods as R
    r = {'total_power': list(tp_new), 'uncontrolled_power': list(up_new), 'stable': flag,
         'reset_hops': [h for h, _ in (ev_new or [])], 'loc_hist': [t for _, t in (ev_new or [])]}
    old = {'tp': list(tp_old), 'up': list(up_old), 'flag_stable': True, 'hops_full': hops or len(up_old)}
    evs = None if ev_old is None else [[(h + 1) * R.H, t] for h, t in ev_old]
    c, size = PF._compare(r, old, evs)
    return {'checks': c, 'size': size}


def test_env_classes_I_K_F():
    """Rule 11b Sec. 2.2 on synthetic arrays: identical -> I; up rel. 1e-12 -> K (tp differences allowed);
    up rel. 1e-8 -> F; one event different -> F; flag different -> F."""
    import revision11_preflight as PF
    up = np.linspace(1.0, 2.0, 50); tp = up * 0.1; ev = [(10, 1300)]
    same = _case(tp, up, tp, up, ev, ev)
    assert PF.classify([same]) == 'I' and same['size']['up_max_rel'] == 0.0
    k = _case(tp * 1.01, up * (1 + 1e-12), tp, up, ev, ev)
    assert PF.classify([same, k]) == 'K' and 5e-13 < k['size']['up_max_rel'] < 2e-12
    assert k['size']['tp_max_db'] == pytest.approx(10 * np.log10(1.01))
    f = _case(tp, up * (1 + 1e-8), tp, up, ev, ev)
    assert PF.classify([same, f]) == 'F'
    e = _case(tp, up * (1 + 1e-12), tp, up, [(11, 1400)], ev)
    assert PF.classify([e]) == 'F' and e['size']['events_diff']['first_mismatch'] == 0
    g = _case(tp, up, tp, up, flag=False)
    assert PF.classify([g]) == 'F'
    n = _case(np.r_[tp[:-1], np.nan], up, tp, up)
    assert PF.classify([n]) == 'F'


def test_rule11b_sha_and_provenance_items(tmp_path, monkeypatch):
    import hashlib
    R = _R()
    assert R.rule_matches(R.RULE11B, R.RULE11B_SHA256) and R.check_rules()   # public copy: via REDACTION_MANIFEST
    monkeypatch.setattr(R, 'OUT_DIRS', [tmp_path])
    _env_files(R, tmp_path, monkeypatch, c_class='K')
    d = R.provenance(tmp_path, {'stage': 'x'})
    assert d['rule11b_sha256'] == R.RULE11B_SHA256 and d['machine'] == FAKE_MACHINE and d['env_class'] == 'K'
    assert d['tuning_events_source'] == 'env' and set(d['outer_reference'].values()) == {'rerun'}
    assert d['pra_threads'] == 2
    _env_files(R, tmp_path, monkeypatch, c_class='I')
    d = R.provenance(tmp_path, {'stage': 'x'})
    assert d['tuning_events_source'] == 'cache'
    assert d['outer_reference'] == {b: ('rerun' if b == 'RLS + CUSUM' else 'recorded') for b in R.EXISTING_SCORE}
    monkeypatch.setattr(R, 'RULE11B_SHA256', '0' * 64)
    with pytest.raises(ValueError, match='11b'):
        R.check_rules()


def test_outer_reference_in_class_K_and_I(monkeypatch):
    """Rule 11b Sec. 4 (b), (b'): (a) class K: the reference is the re-run score of BASE13[base] in this environment
    (the recorded score is still reported); (b) class I: only RLS + CUSUM is re-run; (c) a failing reference stops."""
    import revision11_select as S
    R = _R()
    first, second = [R.OUTER['RLS'][0]], [R.OUTER['RLS'][1]]
    g1 = lambda v: _cfg_rows('RLS [outer 1]', 0, first[0][1], v)
    ref = lambda v, **k: _cfg_rows('RLS [reference]', 0, R.BASE13['RLS'][1], v, **k)
    refs_k = R.reference_bases('K')
    assert refs_k == list(R.EXISTING_SCORE) and R.reference_bases('I') == ['RLS + CUSUM']
    d = S.outer_decision(g1(-14.0), 'RLS', first, second, refs_k)
    assert d['status'] == 'open' and d['waiting_reference'] == 'RLS [reference]' and 'pending' not in d
    # recorded -13.86 would call -13.90 "better"; the re-run reference -13.95 makes it interior
    d = S.outer_decision(g1(-13.90) + ref(-13.95), 'RLS', first, second, refs_k)
    assert d['decision'].startswith('interior') and d['reference_source'] == 'rerun'
    assert d['existing_score'] == -13.86 and d['reference_score'] == pytest.approx(-13.95)
    assert d['reference_minus_recorded'] == pytest.approx(-0.09)
    d = S.outer_decision(g1(-13.90), 'RLS', first, second, R.reference_bases('I'))      # class I: recorded score
    assert d['reference_source'] == 'recorded' and d['pending'] == 'RLS [outer 2]'
    with pytest.raises(ValueError, match='reference re-run of the existing selection failed'):
        S.outer_decision(g1(-14.0) + ref(-14.0, fail_seed=R.TUNE[1]), 'RLS', first, second, refs_k)
    # stage C lists: references after the optional first points, before the second steps
    for cls, want in (('I', ['RLS + CUSUM [reference]']), ('K', [f'{b} [reference]' for b in R.EXISTING_SCORE])):
        groups = [g for g, *_ in S.stage_cfgs('C', g1(-14.5), cls)]
        refs = [g for g in groups if g.endswith('[reference]')]
        assert refs == want
        assert groups.index(refs[0]) > groups.index('FD-FxNLMS + det [outer 1]')
        if cls == 'I':
            assert groups[-1] == 'RLS [outer 2]'
    assert R.needs_events('FD-FxNLMS + det [reference]', *R.BASE13['FD-FxNLMS + det'])
    assert not R.needs_events('RLS + CUSUM [reference]', *R.BASE13['RLS + CUSUM'])


def test_tuning_events_env_source_reads_only_e0(tmp_path, monkeypatch):
    """Rule 11b Sec. 4 (c): source 'env' reads only det_events_env_*.jsonl (not results/det_events/ nor the per-shard
    cache), and a class-K stage stops while E0 is incomplete."""
    import revision11_select as S
    R = _R()
    rec = lambda sd, e: json.dumps({'room': 'A', 'noise': 'ar1', 'scen': 'S2 src 30cm', 'seed': sd, 'events': e}) + '\n'
    (tmp_path / 'det_events_env_0.jsonl').write_text(rec(300, [[128, 100]]))
    (tmp_path / 'det_events_0.jsonl').write_text(rec(999, [[256, 200]]))
    ev = R.tuning_events(tmp_path, source='env')
    assert ev == {('ar1', 'S2 src 30cm', 300): [[128, 100]]}
    cache = R.tuning_events(tmp_path, source='cache')
    assert ('ar1', 'S2 src 30cm', 999) in cache and len(cache) > 400        # results/det_events/ + shard cache
    monkeypatch.setattr(R, 'tuning_events', lambda cache_dir=None, source='cache': ev if source == 'env' else cache)
    with pytest.raises(ValueError, match='E0 incomplete'):
        S.stage_events('C', 'K')
    assert S.stage_events('C', 'I') is cache


def test_stage_e0_writes_this_shard_keys_once(tmp_path, monkeypatch, capsys):
    import zlib
    import revision11_select as S
    R = _R()
    monkeypatch.setattr(R, 'OUT_DIRS', [tmp_path]); monkeypatch.setattr(S, 'OUT', tmp_path)
    monkeypatch.setattr(R, 'COMBOS15', [('ar1', 'S2 src 30cm'), ('harmonic', 'R2 rig 30cm')])
    monkeypatch.setattr(R, 'TUNE', [300, 301, 302, 600])
    calls = []
    monkeypatch.setattr(R, 'run_record', lambda name, kind, prm, room, nz, sc, sd, *a: (
        calls.append((name, nz, sc, sd)) or {}, [[sd, sd - 1]]))
    monkeypatch.setenv('SHARD', '1/2')
    S.run_e0()                                                          # class I (autouse fixture): nothing
    assert calls == [] and 'nothing to run' in capsys.readouterr().out
    monkeypatch.setattr(S, 'current_class', lambda: 'K')
    S.run_e0(); S.run_e0()
    mine = [(nz, sc, sd) for sd in R.TUNE for nz, sc in R.COMBOS15
            if zlib.crc32('|'.join(map(str, (nz, sc, sd))).encode()) % 2 == 1]
    assert [c[1:] for c in calls] == mine and all(c[0] == 'E-PCG' for c in calls)
    got = R.tuning_events(tmp_path, source='env')
    assert set(got) == set(mine) and got[mine[0]] == [[mine[0][2], mine[0][2] - 1]]


def test_outer_decision_open_carries_existing_score():
    """Summary after B1 (stage C not run): open outer groups still carry the recorded score (KeyError fix)."""
    import revision11_select as S
    import revision11_methods as R
    for base, first, second in S.outer_groups():
        d = S.outer_decision([], base, first, second)
        assert d['status'] == 'open'
        assert d['existing_score'] == R.EXISTING_SCORE[base]
