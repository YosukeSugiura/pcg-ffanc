"""Revision 11 (docs/current/REVISION_RULE_11.md, fixed 2026-11-07): method definitions, GRID11, ablation variants and
the shared run / record / event helpers. eval_v2.GRID and results/protocol_v2_sel/selected_e.json are only read.

Nothing here changes an existing method: new behaviour sits behind the new flags 'mod' (fixed_binwise), 'SW-FBLMS'
(method), 'det_cond_db' / 'det_cond_k' / 'det_grow' (R-RLS) and 'solver' (E-PCG-F / EPCGConfig), all off by default.
"""
import hashlib
import json
import os
import platform
import subprocess
import sys
import time
from pathlib import Path

import numpy as np

import eval_v2 as ev

ROOT = Path(__file__).resolve().parents[1]
RES = ROOT / 'results'
RULE = ROOT / 'docs/current/REVISION_RULE_11.md'
RULE_SHA256 = '6ba432af58880a94d6915beab8f7183af645b706bff37b959d4acdd6519bf270'
# Rule 11a (corrections fixed before any tuning / evaluation run; commit 06a4a66). Checked at every job start (c1 / c8).
RULE11A = ROOT / 'docs/current/REVISION_RULE_11a.md'
RULE11A_SHA256 = '6d26fe9394c9bcba244065171812ddc6e5418689be89a13609ac16db4c077563'
# Rule 11b (environment classes, PRA_NUM_THREADS, in-environment comparisons; commit 4064555). Checked with 11 / 11a.
RULE11B = ROOT / 'docs/current/REVISION_RULE_11b.md'
RULE11B_SHA256 = '2e12b3cde994ac28cfc4cbc4f0248161dc2bc111e9a280fdafae83ddd548663e'
H = ev.H; TT = ev.TT
TUNE = list(ev.TUNE)                       # 300-309 + 600-619
HOLDOUT = list(range(800, 840))
SMOKE_SEED = 300
COMBOS15 = list(ev.COMBOS15)

SEL_DIR = RES / 'protocol_r11_sel'
HOLD_DIR = RES / 'final_eval_holdout_r11'
ABL_DIR = RES / 'r11_ablation_holdout'
PRE_DIR = RES / 'r11_preflight'
OLD_HOLD = RES / 'final_eval_holdout'      # read only
# Rule 11 Sec. 9 item 8 (b): if environment A cannot reproduce the saved holdout (Sec. 6.2), the room-A holdout of the
# 15 methods is re-run in environment C into a new directory and every Rule 11 room-A comparison uses it instead
# (the existing 390 family stays as it is). Selected with R11_HOLDOUT_BASE=envC; default: the saved 9-A holdout.
HOLDOUT_BASE = os.environ.get('R11_HOLDOUT_BASE', 'saved')
if HOLDOUT_BASE == 'envC':
    OLD_HOLD = RES / 'final_eval_holdout_r11_envC'
    ABL_DIR = RES / 'r11_ablation_holdout_envC'
    HOLD_DIR = RES / 'final_eval_holdout_r11_envC_new'
elif HOLDOUT_BASE != 'saved':
    raise ValueError(f'R11_HOLDOUT_BASE={HOLDOUT_BASE!r}')
PIPE_DIR = RES / 'r11_pipeline'            # pipeline logs, status flags and lock (2026-11-07 review M-5)

# ------------------------------------------------------------------ write guard (2026-11-07 review M-1)
# Every Rule 11 write goes to one of these new directories (Rule 11 Sec. 1.5 and the Sec. 9 item 8 (b) directories of
# the active holdout base); anything else under results/ (existing records such as results/final_eval_holdout/) is read
# only. The directories of the other holdout base are refused too, so path A and path B outputs never mix.
_OUT_SHARED = ('protocol_r11_sel', 'r11_preflight', 'r11_pipeline', 'eval_roomB_h', 'eval_roomC_h', 'eval_snr10_h',
               'final_eval_meas_s_h', 'final_eval_meas_p_h')
_OUT_BASE = {'saved': ('r11_ablation_holdout', 'final_eval_holdout_r11'),
             'envC': ('final_eval_holdout_r11_envC', 'r11_ablation_holdout_envC', 'final_eval_holdout_r11_envC_new')}
OUT_DIRS = [RES / d for d in _OUT_SHARED + _OUT_BASE[HOLDOUT_BASE]]


def out_path(path):
    """Return `path` if it lies in a Rule 11 output directory; raise otherwise (never write existing results)."""
    p = Path(path).resolve()
    for d in OUT_DIRS:
        d = Path(d).resolve()
        if p == d or d in p.parents:
            return Path(path)
    raise PermissionError(f'refusing to write {path}: not a Rule 11 output directory (R11_HOLDOUT_BASE={HOLDOUT_BASE}); '
                          'existing results are read only')


def write_new(path, text):
    """Write a new file (out_path checked); an existing file is never overwritten (raise)."""
    path = out_path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, 'x') as fh:
        fh.write(text)
    return path


# ------------------------------------------------------------------ JSONL reading / resume (2026-11-07 review M-4)
def read_jsonl(path, mode='strict'):
    """Complete records of a JSONL file written line by line ('json + newline', flushed per record).

    A last line without its newline is a record cut by an interrupted writer:
      mode 'strict' : raise (summaries: the job did not finish)
      mode 'skip'   : ignore it (a file another shard may be appending to right now; never modified)
      mode 'repair' : truncate the file to the end of the last complete line, so the run is redone (the owning shard,
                      before it appends; the complete lines are not changed) and report the discarded bytes on stderr
    A malformed line before the last one always raises."""
    path = Path(path)
    if not path.exists():
        return []
    data = path.read_bytes()
    cut = data.rfind(b'\n') + 1                            # bytes of the complete lines
    if cut < len(data):
        if mode == 'strict':
            raise ValueError(f'{path}: last line has no newline (interrupted writer); resume the job first')
        if mode == 'repair':
            out_path(path)
            with open(path, 'r+b') as fh:
                fh.truncate(cut)
            print(f'NOTE: {path}: discarded an incomplete last line ({len(data) - cut} bytes); the run is redone',
                  file=sys.stderr, flush=True)
        elif mode != 'skip':
            raise ValueError(mode)
    out = []
    for i, line in enumerate(data[:cut].decode().split('\n')[:-1]):
        if not line.strip():
            continue
        try:
            out.append(json.loads(line))
        except json.JSONDecodeError as exc:
            raise ValueError(f'{path}: malformed line {i + 1} before the end of the file') from exc
    return out


# ------------------------------------------------------------------ software environment (2026-11-07 review M-3)
# Rule 11 Sec. 1.2: environment A (room-A holdout joined with the saved 9-A records, path A) and C (tuning, 11-D, the
# Sec. 9 item 8 (b) holdout). Python is checked at major.minor (Rule 11 table: C = 3.13.18, A = 3.12.x; the patch
# version is recorded in provenance.json and the byte checks of Sec. 6.2 / the `up` comparison decide).
ENVS = {'A': {'python': '3.12', 'numpy': '2.3.5', 'scipy': '1.17.0', 'pyroomacoustics': '0.10.1', 'pra_threads': 3},
        'C': {'python': '3.13', 'numpy': '2.5.3', 'scipy': '1.18.1', 'pyroomacoustics': '0.10.1', 'pra_threads': 2}}
# Rule 11b Sec. 3: pyroomacoustics splits the float32 RIR partial sums over num_threads (default os.cpu_count(); only
# PRA_NUM_THREADS sets it). The thread count of the recorded sets: A (9-A / 9-B) 3, C (v2e, 8a, 9-C / 9-D) 2.
MEAS_VERSIONS = {'numba': '0.68.1', 'soundfile': '0.14.0'}    # M-S / M-P (Rule 8a provenance)


def installed_versions(names):
    from importlib.metadata import PackageNotFoundError, version
    out = {}
    for n in names:
        try:
            out[n] = version(n)
        except PackageNotFoundError:
            out[n] = None
    return out


def pra_threads_now():
    """(PRA_NUM_THREADS of the environment, pyroomacoustics' effective num_threads)."""
    import pyroomacoustics as pra
    return os.environ.get('PRA_NUM_THREADS'), pra.constants.get('num_threads')


def check_env(env, meas=False):
    """Raise unless this interpreter is Rule 11 environment `env` ('A' or 'C'; meas: + numba / soundfile), including the
    pyroomacoustics thread count of Rule 11b Sec. 3 (PRA_NUM_THREADS and pra.constants both)."""
    want = dict(ENVS[env]); py = want.pop('python'); nthr = want.pop('pra_threads')
    if meas:
        want.update(MEAS_VERSIONS)
    have = installed_versions(want)
    bad = {k: (have[k], v) for k, v in want.items() if have[k] != v}
    if '.'.join(platform.python_version().split('.')[:2]) != py:
        bad['python'] = (platform.python_version(), py + '.x')
    env_thr, pra_thr = pra_threads_now()
    if env_thr != str(nthr) or pra_thr != nthr:
        bad['pra_threads'] = ({'PRA_NUM_THREADS': env_thr, 'pra.constants': pra_thr}, nthr)
    if bad:
        raise RuntimeError(f'environment {env} required (Rule 11 Sec. 1.2); found / required: {bad}')
    return True


def holdout_env():
    """Environment of the room-A holdout jobs: A on path A (joined with the saved 9-A records), C on path B."""
    return 'C' if HOLDOUT_BASE == 'envC' else 'A'

# ------------------------------------------------------------------ frozen existing methods (read only)
_SEL_E = json.loads((ev.SEL / 'selected_e.json').read_text())['selected']
_CUSUM = json.loads((RES / 'protocol_v2_sel_cusum/selected.json').read_text())
BASE13 = {m: (ev.GRID[m][0], ev.GRID[m][1][i]) for m, i in _SEL_E.items()}
BASE13['RLS + CUSUM'] = ('R-RLS', _CUSUM['params'])
PROP = {'E-PCG': ('E-PCG-F', ev.MAIN), 'E-PCG bank': ('E-PCG-F', ev.BANK)}
DET_OLD = set(ev.DET)                      # existing baselines that consume the E-PCG main events

# ------------------------------------------------------------------ 11-A ablation variants (Sec. 2.3)
def _variant(**change):
    f = dict(ev.MAIN)
    for k, v in change.items():
        if v is None:
            f.pop(k, None)
        else:
            f[k] = v
    return f


VARIANTS = {
    'G1': ('PCG-WLS (fixed order)', _variant(grow_len=None)),
    'G2': ('PCG-WLS (restart)', _variant(adapt='restart')),
    'G3': ('PCG-WLS (no detector)', _variant(detect=False)),
    'G4': ('PCG-WLS (fixed order, restart)', _variant(grow_len=None, adapt='restart')),
    'G5': ('PCG-WLS (exact solver)', _variant(solver='exact')),
}

# ------------------------------------------------------------------ 11-B / 11-C grids (Sec. 3.3, 3.4, 4.2, 4.3, 2.6)
MU_GRID = (0.05, 0.1, 0.15, 0.2, 0.25, 0.3)
MU_N = 0.3                                 # selected FD-FxNLMS step (selected_e.json index 5)
assert BASE13['FD-FxNLMS'][1] == {'mu': MU_N}
SW_GRID = [(thr, dw) for thr in (0.01, 0.03, 0.1) for dw in (4, 8)]
# edge rule of Sec. 3.3 / 4.2 for MFBLMS: one step outward (at most two); below 0.05 the step halves (0.05 - 0.05 = 0)
MU_EDGE = {0.3: (0.35, 0.4), 0.05: (0.025, 0.0125)}

GRID11 = {
    'MFBLMS': ('fixed_binwise', [{'mu': mu, 'mod': True} for mu in MU_GRID]),
    'RLS + det (cond.)': ('R-RLS', [{'lam': 0.9999, 'delta': 0.01, 'det_reset_w': False, 'det_cond_db': th,
                                     'det_cond_k': 32} for th in (1.0, 2.0, 4.0, 8.0)]),
    # Rule 11a Sec. 2.2: (i) growth after each restart only (Rule 11 Sec. 2.6 text), (ii) also from the run start
    'RLS + det + growth': ('R-RLS', [{'lam': 0.9999, 'delta': 0.01, 'det_reset_w': False, 'det_grow': 'half'}]),
    'RLS + det + growth (from start)': ('R-RLS', [{'lam': 0.9999, 'delta': 0.01, 'det_reset_w': False,
                                                  'det_grow': 'half', 'det_grow_start': True}]),
}
GROUPS_C = ('RLS + det (cond.)', 'RLS + det + growth', 'RLS + det + growth (from start)')   # 11-C GRID11 groups
# fixed by Rule 11 Sec. 4.2: existing selected value -> one step outward, second step (only where the rule names one)
OUTER = {
    'RLS': [('R-RLS', {'lam': 0.9993, 'delta': 0.01}), ('R-RLS', {'lam': 0.9991, 'delta': 0.01})],
    'VFF-RLS': [('R-VFF', {'N0': 250.0, 'lam_min': 0.9995, 'delta': 1e-3}),
                ('R-VFF', {'N0': 125.0, 'lam_min': 0.9995, 'delta': 1e-3})],
    'SFTF-H + det': [('R-SFTF', {'lam': 0.9999, 'delta': 0.01, 'det_reset_w': False, 'hybrid': 4096}),
                     ('R-SFTF', {'lam': 0.9999, 'delta': 0.01, 'det_reset_w': False, 'hybrid': 8192})],
}
# optional points (Sec. 4.2 table, author decision 5: all included); no second step is defined by the rule for these
OUTER_OPT = {
    'RLS + CUSUM': [('R-RLS', {'lam': 0.9999, 'delta': 0.01, 'cusum_h': h, 'cusum_k': 64}) for h in (3, 5, 8)],
    'FD-FxNLMS': [('fixed_binwise', {'mu': 0.32})],
    'leaky FD-FxNLMS': [('leaky_binwise', {'mu': 0.35, 'leak': 0.03}), ('leaky_binwise', {'mu': 0.5, 'leak': 0.01})],
    'FDKF': [('C-FDKF', {'P0': 3.0, 'gain_scale': 4.0, 'A': 0.9995})],
    'FD-FxNLMS + det': [('V-SCHED', {'denom': 'cum', 'scale': 0.03125, 'mu_min': 0.2, 'det_reset_w': False})],
}
# existing scores: recorded values of protocol_v2_sel/selection_e.md (2 decimals) and the CUSUM selection (Sec. 4.2)
EXISTING_SCORE = {'RLS': -13.86, 'VFF-RLS': -13.44, 'SFTF-H + det': -14.95, 'FD-FxNLMS': -13.58,
                  'leaky FD-FxNLMS': -13.49, 'FDKF': -12.03, 'FD-FxNLMS + det': -13.01,
                  'RLS + CUSUM': float(_CUSUM['score'])}


def dependent_grids(mu_m):
    """Grids that need the selected MFBLMS step mu_m (Sec. 3.3 'MFBLMS + det', Sec. 3.4 SW-FBLMS Z-A / Z-B)."""
    mu_m = float(mu_m)
    boosts = ([{'det_boost': sb, 'det_reset_w': False} for sb in (0.0625, 0.125, 0.25)]
              + [{'det_boost': sb, 'det_reset_w': True} for sb in (0.0, 0.0625, 0.125, 0.25)])
    return {
        # mirror of 'FD-FxNLMS + restart' (eval_v2.GRID, 7 configurations) with the MFBLMS gradient and step
        'MFBLMS + det': ('fixed_binwise', [dict({'mu': mu_m, 'mod': True}, **b) for b in boosts]),
        'switching FD-FxNLMS [6]': ('SW-FBLMS', [{'mu_n': MU_N, 'mu_m': mu_m, 'sw_thr': thr, 'sw_dwell': dw,
                                                  'sw_detect': 'zeta'} for thr, dw in SW_GRID]),
        'switching FD-FxNLMS + det': ('SW-FBLMS', [{'mu_n': MU_N, 'mu_m': mu_m, 'sw_thr': thr, 'sw_dwell': dw,
                                                    'sw_detect': 'det'} for thr, dw in SW_GRID]),
    }


DET_NEW = {'MFBLMS + det', 'switching FD-FxNLMS + det', 'RLS + det (cond.)', 'RLS + det + growth',
           'RLS + det + growth (from start)'}


def needs_events(name, kind, prm):
    """Does this configuration consume the same-run E-PCG main events?"""
    base = name.split(' (extended grid')[0].split(' [outer')[0].split(' [reference]')[0]
    return base in DET_OLD or base in DET_NEW or (kind == 'SW-FBLMS' and prm.get('sw_detect') == 'det')


# ------------------------------------------------------------------ the selected new baselines (after 11-B / 11-C)
def selected_new():
    """{name: (kind, params)} of the admissible new baselines (Sec. 3.5 n_new set), from protocol_r11_sel/selected.json.
    Raises if the selection is incomplete."""
    p = SEL_DIR / 'selected.json'
    if not p.exists():
        raise FileNotFoundError(f'{p}: run revision11_select.py summary first')
    data = json.loads(p.read_text())
    if not data.get('complete'):
        raise ValueError('selection not complete (selected.json complete = false)')
    return {m: (v['kind'], v['params']) for m, v in data['new_rows'].items()}


# ------------------------------------------------------------------ events (read-only caches, new cache in r11 dirs)
def _read_jsonl(path, mode='strict'):
    return read_jsonl(path, mode)


def tuning_events(cache_dir=SEL_DIR, source='cache'):
    """Room-A tuning events.
    source 'cache': results/det_events/ (read only) + <cache_dir>/det_events_[01].jsonl (new keys only; a cut last line
                    of a cache file that the other shard may be appending to is skipped, its owner repairs it)
    source 'env'  : only <cache_dir>/det_events_env_[01].jsonl, written by stage E0 in this environment (Rule 11b
                    Sec. 4 (c): class K); results/det_events/ is not read"""
    out = {}
    if source == 'env':
        files = sorted(cache_dir.glob('det_events_env_[01].jsonl'))
    elif source == 'cache':
        files = sorted((RES / 'det_events').glob('*.jsonl')) + sorted(cache_dir.glob('det_events_[01].jsonl'))
    else:
        raise ValueError(source)
    for f in files:
        for r in _read_jsonl(f, 'skip' if f.parent == cache_dir else 'strict'):
            if r['room'] != 'A':
                continue
            k = (r['noise'], r['scen'], r['seed'])
            if k in out and out[k] != r['events']:
                raise ValueError(f'conflicting cached events {k}')
            out[k] = r['events']
    return out


def holdout_events():
    """Room-A holdout events of E-PCG main (results/final_eval_holdout/det_events_{0,1}.jsonl, read only)."""
    out = {}
    for f in sorted(OLD_HOLD.glob('det_events_*.jsonl')):
        for r in _read_jsonl(f):
            k = (r['noise'], r['scen'], r['seed'])
            if k in out:
                raise ValueError(f'duplicate holdout event {k}')
            out[k] = r['events']
    need = {(nz, sc, sd) for nz, sc in COMBOS15 for sd in HOLDOUT}
    if set(out) != need:
        raise ValueError(f'holdout events incomplete: {len(out)}/{len(need)}')
    return out


def epcg_events(r):
    if len(r['reset_hops']) != len(r['loc_hist']):
        raise ValueError('unaligned E-PCG detections')
    return [[(int(h) + 1) * H, int(t)] for h, t in zip(r['reset_hops'], r['loc_hist'])]


# ------------------------------------------------------------------ one run -> one record
def cfg_for(room, nz, sc):
    if room == 'M_S':                                     # Rule 9-D M-S: stationary measured paths, source target
        c = ev.cfg_of('M_8a', nz, 'S8 stationary'); c['move_target'] = 'source'; return c
    return ev.cfg_of(room, nz, sc)


def run_record(name, kind, prm, room, nz, sc, sd, events=None, extra=None):
    """Simulate one run and return (record, own E-PCG events or None). Records follow revision9_holdout.run_one and add
    the new descriptive fields (restarts actually applied, switching log, conditional-restart log)."""
    params = dict(prm)
    if needs_events(name, kind, prm):
        if events is None:
            raise ValueError(f'same-run E-PCG events missing for {name}')
        params['det_events'] = events
    start = time.time()
    r = ev.D.P.run(cfg_for(room, nz, sc), sd, kind, params, TT, None if sc.startswith('S8') else ev.D.CH)
    tp, up = r['total_power'], r['uncontrolled_power']
    if not np.all(np.isfinite(up)):
        raise ValueError(f'non-finite uncontrolled power {name} {nz} {sc} {sd}')
    rec = {'method': name, 'prm': prm, 'room': room, 'noise': nz, 'scen': sc, 'seed': sd,
           'flag_stable': bool(r['stable']), 'tp': list(map(float, tp)), 'up': list(map(float, up[:len(tp)])),
           'hops_full': len(up), 'wall_s': round(time.time() - start, 2),
           'flops_hop': float(np.mean(r['flop_hist'])) if r.get('flop_hist') else None,
           'n_events_given': len(params.get('det_events', []))}       # Rule 11a Sec. 5.8 (was n_restarts)
    if 'det_events' in params:
        rec['n_events'] = len(params['det_events']); rec['restart_hops'] = list(map(int, r['reset_hops']))
    if 'cond_log' in r:
        rec['cond_log'] = r['cond_log']
    if 'sw_log' in r:
        rec['sw_log'] = r['sw_log']
        modes = r['sw_modes']; rec['sw_hops'] = {m: modes.count(m) for m in ('N', 'M', 'C')}
    if 'path_provenance' in r:
        rec['path_provenance'] = r['path_provenance']
    if extra:
        rec.update(extra)
    own = None
    if kind == 'E-PCG-F':
        own = epcg_events(r)
        rec['detections'] = own                            # G1-G5: own detections (stop, tau), descriptive
    elif kind == 'R-RLS' and 'cusum_h' in prm:
        rec['events'] = epcg_events(r)
    return rec, own


def metrics_of(rec):
    """Selection-time metrics (eval_v2.run_metrics: failure, A1, A2) of one record."""
    m = ev.run_metrics(rec)
    return {'fail': int(m['fail']), 'A1': float(m['A1']), 'A2': float(m['A2'])}


# ------------------------------------------------------------------ provenance
def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def rule_matches(path, fixed_sha256):
    """True if the rule file on disk is the fixed version: its digest equals the fixed digest, or (public release) the
    file is the redacted copy listed in REDACTION_MANIFEST.json with that fixed digest as its original."""
    path = Path(path)
    if not path.exists():
        return False
    actual = sha256(path)
    if actual == fixed_sha256:
        return True
    manifest = ROOT / 'REDACTION_MANIFEST.json'
    if not manifest.exists():
        return False
    item = json.loads(manifest.read_text())['files'].get(path.resolve().relative_to(ROOT).as_posix())
    return bool(item) and item['original_sha256'] == fixed_sha256 and item['release_sha256'] == actual


def check_rules():
    """Rule 11, 11a and 11b on disk = the fixed versions (Rule 11a Sec. 3.3 c1 / c8, Rule 11b Sec. 8 c9).
    In the public release the rule files are redacted copies; rule_matches accepts them via REDACTION_MANIFEST.json."""
    if not rule_matches(RULE, RULE_SHA256):
        raise ValueError('REVISION_RULE_11.md differs from the fixed version')
    if not rule_matches(RULE11A, RULE11A_SHA256):
        raise ValueError(f'REVISION_RULE_11a.md missing or differs from the fixed version (sha256 {RULE11A_SHA256})')
    if not rule_matches(RULE11B, RULE11B_SHA256):
        raise ValueError(f'REVISION_RULE_11b.md missing or differs from the fixed version (sha256 {RULE11B_SHA256})')
    return True


# ------------------------------------------------------------------ machine fingerprint and environment classes (11b)
UP_REL_TOL = 1e-9                          # Rule 11b Sec. 2.2: class K bound on the max relative difference of `up`


def _cpuinfo():
    try:
        txt = Path('/proc/cpuinfo').read_text()
    except OSError:
        return None, None
    model = next((l.split(':', 1)[1].strip() for l in txt.splitlines() if l.startswith('model name')), None)
    flags = next((l.split(':', 1)[1].strip() for l in txt.splitlines() if l.startswith('flags')), '')
    return model, hashlib.sha256(' '.join(sorted(flags.split())).encode()).hexdigest()


def openblas_corename():
    """OpenBLAS core name of numpy (threadpoolctl if present, else ctypes on numpy's bundled library)."""
    try:
        import threadpoolctl
        for i in threadpoolctl.threadpool_info():
            if i.get('internal_api') == 'openblas':
                return i.get('architecture')
    except Exception:
        pass
    import ctypes
    import numpy
    libs = Path(numpy.__file__).resolve().parent.parent / 'numpy.libs'
    for lib in sorted(libs.glob('*openblas*')):
        try:
            h = ctypes.CDLL(str(lib))
        except OSError:
            continue
        for sym in ('scipy_openblas_get_corename64_', 'openblas_get_corename64_', 'openblas_get_corename'):
            fn = getattr(h, sym, None)
            if fn is not None:
                fn.restype = ctypes.c_char_p
                return fn().decode()
    return None


def machine_fingerprint():
    """Rule 11b Sec. 2.3 m4: CPU model, os.cpu_count(), CPU flags (sha256), pra threads, OpenBLAS core and build,
    full Python version and interpreter."""
    import numpy
    model, flags = _cpuinfo()
    try:
        blas = numpy.show_config(mode='dicts')['Build Dependencies']['blas']
        blas = {k: blas.get(k) for k in ('name', 'version', 'openblas configuration')}
    except Exception:
        blas = None
    env_thr, pra_thr = pra_threads_now()
    return {'cpu_model': model, 'cpu_count': os.cpu_count(), 'cpu_flags_sha256': flags,
            'PRA_NUM_THREADS': env_thr, 'pra_num_threads': pra_thr, 'openblas_corename': openblas_corename(),
            'numpy_blas': blas, 'python': platform.python_version(), 'executable': sys.executable}


MACHINE_KEYS = ('cpu_model', 'cpu_count', 'cpu_flags_sha256')   # the machine itself (not the interpreter)


def same_machine(recorded, current=None):
    current = current or machine_fingerprint()
    return isinstance(recorded, dict) and all(recorded.get(k) == current.get(k) for k in MACHINE_KEYS)


def _env_record(name, current=None):
    """env_<name>.json if it was made on this machine with the pra thread count of its environment, else None."""
    f = PRE_DIR / f'env_{name}.json'
    if not f.exists():
        return None, 'missing'
    d = json.loads(f.read_text())
    if not same_machine(d.get('machine'), current):
        return None, 'made on another machine (fingerprint differs)'
    if (d.get('machine') or {}).get('pra_num_threads') != ENVS[name]['pra_threads']:
        return None, f"pra threads {(d.get('machine') or {}).get('pra_num_threads')} != {ENVS[name]['pra_threads']}"
    if d.get('class') not in ('I', 'K', 'F'):
        return None, 'no class (made before Rule 11b)'
    return d, 'ok'


def env_class(current=None):
    """Class (I / K) of env_C.json made on this machine; raise (stop, Rule 11b c4) if missing, foreign or F."""
    d, why = _env_record('C', current)
    if d is None or d['class'] == 'F':
        raise ValueError(f"env_C.json {why if d is None else 'class F'}: run envC on this machine "
                         '(PRA_NUM_THREADS=2; Rule 11b Sec. 8 c4)')
    return d['class']


def holdout_base_wanted(current=None):
    """'envA' iff env_A.json was made on this machine with PRA_NUM_THREADS=3 and is class I (Rule 11b Sec. 5)."""
    d, _ = _env_record('A', current)
    return 'envA' if d is not None and d['class'] == 'I' else 'envC'


def reference_bases(cls):
    """Rule 11b Sec. 4 (b), (b'): outer-grid bases whose reference score is re-run in this environment."""
    return list(EXISTING_SCORE) if cls == 'K' else ['RLS + CUSUM']


def holdout_base_label():
    """'envA' (path A: joined with the saved 9-A holdout) or 'envC' (Rule 11 Sec. 9 item 8 (b)); Rule 11a Sec. 3.1."""
    return 'envC' if HOLDOUT_BASE == 'envC' else 'envA'


def check_holdout_base(current=None):
    """Rule 11b Sec. 5 / 8 (c4, c5): env_C.json must be from this machine and class I or K (else stop); the path is
    'envA' iff env_A.json is from this machine and class I, else 'envC'; R11_HOLDOUT_BASE must agree (review N-M1)."""
    env_class(current)
    want = holdout_base_wanted(current)
    if holdout_base_label() != want:
        raise ValueError(f'holdout base {holdout_base_label()} contradicts env_A.json (this machine -> {want}); '
                         + ('export R11_HOLDOUT_BASE=envC for every job' if want == 'envC'
                            else 'unset R11_HOLDOUT_BASE (path A)'))
    return want


def provenance_dict(extra=None, scripts=()):
    from importlib.metadata import version
    check_rules()
    machine = machine_fingerprint()
    check_holdout_base(machine)
    cls = env_class(machine)
    d = {'commit': subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip(),
         'git_status_porcelain': subprocess.check_output(['git', 'status', '--porcelain'], cwd=ROOT, text=True),
         'rule': 'docs/current/REVISION_RULE_11.md', 'rule_sha256': RULE_SHA256,
         'rule11a': 'docs/current/REVISION_RULE_11a.md', 'rule11a_sha256': RULE11A_SHA256,
         'rule11b': 'docs/current/REVISION_RULE_11b.md', 'rule11b_sha256': RULE11B_SHA256,
         'holdout_base': holdout_base_label(), 'machine': machine, 'pra_threads': machine['pra_num_threads'],
         'env_class': cls, 'tuning_events_source': 'env' if cls == 'K' else 'cache',
         'outer_reference': {b: ('rerun' if b in reference_bases(cls) else 'recorded') for b in EXISTING_SCORE},
         'python': platform.python_version(),
         'software': {x: version(x) for x in ('numpy', 'scipy', 'pyroomacoustics')},
         'RLS_FAST': os.environ.get('RLS_FAST'),
         'threads': {x: os.environ.get(x) for x in ('OPENBLAS_NUM_THREADS', 'MKL_NUM_THREADS', 'OMP_NUM_THREADS')},
         'written': time.strftime('%Y-%m-%dT%H:%M:%S%z'),
         'scripts_sha256': {str(Path(s).relative_to(ROOT)): sha256(s) for s in
                            [Path(__file__), ROOT / 'experiments/prototype_new_algorithms.py',
                             ROOT / 'src/ffanc_norm/fd_fxnlms.py', ROOT / 'src/ffanc_norm/pcg_wls.py', *scripts]}}
    if extra:
        d.update(extra)
    return d


def free_name(out, name):
    """<out>/<name>.json, or <name>_resume<n>.json (first free n) when it exists: provenance is never overwritten, so a
    resumed job keeps the provenance of every start (2026-11-07 review L-3)."""
    p = Path(out) / f'{name}.json'; n = 0
    while p.exists():
        n += 1; p = Path(out) / f'{name}_resume{n}.json'
    return p


def provenance(out, extra=None, scripts=(), name='provenance'):
    out = out_path(out)                                    # refuse a foreign directory before anything else
    d = provenance_dict(extra, scripts)
    p = write_new(free_name(out, name), json.dumps(d, indent=2) + '\n')
    print('provenance ->', p, flush=True)
    return d


def check_runtime_env(env=None, meas=False):
    """Worker start: RLS_FAST / single thread, and (env given) the Rule 11 software environment (review M-3)."""
    if env is not None:
        check_env(env, meas)
    if os.environ.get('RLS_FAST') != '1' or any(os.environ.get(x) != '1' for x in
                                                 ('OPENBLAS_NUM_THREADS', 'MKL_NUM_THREADS', 'OMP_NUM_THREADS')):
        raise ValueError('set RLS_FAST=1 and OPENBLAS/MKL/OMP_NUM_THREADS=1')


if __name__ == '__main__':
    import sys as _sys
    flags = set(_sys.argv[3:])
    if len(_sys.argv) >= 3 and _sys.argv[1] == 'check-env' and _sys.argv[2] in ENVS and flags <= {'meas', 'job'}:
        check_rules()
        if 'job' in flags:                                  # pipeline job start: the path must equal env_A.json
            check_holdout_base()
        check_env(_sys.argv[2], meas='meas' in flags)
        pkgs = ['numpy', 'scipy', 'pyroomacoustics'] + list(MEAS_VERSIONS)
        print(f'environment {_sys.argv[2]}{" + meas" if "meas" in flags else ""}: OK; rules OK (11, 11a, 11b); '
              f'pra threads {pra_threads_now()[1]}'
              + (f'; env_C class {env_class()}; holdout base {holdout_base_label()} (= env_A.json)' if 'job' in flags
                 else '') + f' (Python {platform.python_version()}, {installed_versions(pkgs)})')
    else:
        raise SystemExit('usage: python experiments/revision11_methods.py check-env A|C [meas] [job]')
