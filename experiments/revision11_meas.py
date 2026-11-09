"""Revision 11-D measured paths on the holdout seeds 800-839 (Rule 11 Sec. 5.2; author decision 7: M-S and M-P).

  M-S: MeshRIR S32-M441, Rule 8a preprocessing (d0 = 5434), fixed S_hat, stationary (S8), cells ar1 / harmonic
       -> results/final_eval_meas_s_h/  (+ causal Wiener lower bound per seed, as Rule 9-D)
  M-P: same preprocessing, primary-path change (source move, S2 label), cells ar1 / harmonic
       -> results/final_eval_meas_p_h/  (directory name chosen by analogy; Rule 11 Sec. 1.5 lists only M-S)
All 13 + n_new baselines and both proposals, environment C. MeshRIR data: prepare (below) extracts the microphone files
needed by measured_paths.allocation(seed) for 800-839 (generalization of revision9_pipeline.prepare_data, which is
fixed to the 480-519 allocation); MD5, size, README / LICENSE checks unchanged.
usage:
  python experiments/revision11_meas.py prepare
  python experiments/revision11_meas.py provenance meas_s|meas_p
  RLS_FAST=1 OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 SHARD=0/2 python experiments/revision11_meas.py run meas_s
  python experiments/revision11_meas.py bounds        # M-S Wiener lower bound, 2 processes
(summary: experiments/revision11_summary.py meas meas_s|meas_p)
"""
import hashlib
import json
import sys
import zipfile

import numpy as np

import revision11_methods as R
from revision11_rooms import all_methods, run_set

ZIP_SIZE = 3534777656
SETS = {'meas_s': ('M_S', [(nz, 'S8 stationary') for nz in ('ar1', 'harmonic')], R.RES / 'final_eval_meas_s_h', 'M-S'),
        'meas_p': ('M_8a', [(nz, 'S2 src 30cm') for nz in ('ar1', 'harmonic')], R.RES / 'final_eval_meas_p_h', 'M-P')}
DATA = R.ROOT / 'data/meshrir'


def prepare(seeds=tuple(R.HOLDOUT)):
    zp = DATA / 'S32-M441_npy.zip'
    if not zp.exists() or zp.stat().st_size != ZIP_SIZE:
        raise RuntimeError('MeshRIR archive missing or incomplete')
    with zp.open('rb') as f:
        if hashlib.file_digest(f, 'md5').hexdigest() != '4fcd6137bcadb6914d4170ff366c86f9':
            raise RuntimeError('MeshRIR archive MD5 mismatch')
    if not (DATA / 'README.md').exists() or not (DATA / 'LICENSE').exists():
        raise RuntimeError('MeshRIR README or LICENSE unavailable')
    coords = {'S32-M441_npy/pos_mic.npy', 'S32-M441_npy/pos_src.npy'}
    with zipfile.ZipFile(zp) as z:
        if coords - set(z.namelist()):
            raise RuntimeError('MeshRIR archive without coordinates')
        for name in sorted(coords):
            z.extract(name, DATA)
        import measured_paths as mp
        mp.coordinates.cache_clear()
        alloc = [mp.allocation(sd) for sd in seeds]               # coordinates and the seed only
        mics = {int(a[k]) for a in alloc for k in ('m0', 'm1')}
        names = {f'S32-M441_npy/ir_{m}.npy' for m in mics}
        missing = names - set(z.namelist())
        if missing:
            raise RuntimeError(f'MeshRIR archive missing files: {sorted(missing)[:4]}')
        for name in sorted(names):
            z.extract(name, DATA)
    for m in sorted(mics):
        ir = np.load(DATA / f'S32-M441_npy/ir_{m}.npy', mmap_mode='r', allow_pickle=False)
        if ir.shape != (32, 32768) or not np.isfinite(np.asarray(ir)).all():
            raise RuntimeError(f'MeshRIR ir_{m}.npy invalid')
    R.out_path(R.PRE_DIR).mkdir(parents=True, exist_ok=True)
    R.out_path(R.PRE_DIR / 'meshrir_holdout_allocation.json').write_text(json.dumps(alloc, indent=1) + '\n')
    print(f'MeshRIR verified; {len(mics)} microphone files for seeds {seeds[0]}-{seeds[-1]}', flush=True)


def provenance(name):
    """First start: provenance.json = the Rule 8a provenance (measured_paths.write_provenance: frozen inputs, MD5,
    allocation, numba / soundfile versions) + the Rule 11 block 'revision11'. A resumed start does not rewrite it: the
    Rule 8a part is checked against the file by measured_paths.check_existing_metadata (without the Rule 11 keys) and
    the Rule 11 block of this start goes to provenance_resume<n>.json (2026-11-07 review M-1 / L-3)."""
    import measured_paths as mp
    R.check_env('C', meas=True)
    room, combos, out, label = SETS[name]
    out = R.out_path(out)
    r11 = R.provenance_dict({'stage': f'11-D {label}', 'seeds': [800, 839], 'combos': combos,
                             'methods': all_methods()}, [__file__])
    p = out / 'provenance.json'
    if p.exists():
        from summary_provenance import check_existing_metadata
        old = json.loads(p.read_text())
        for k in ('revision11', 'stationary', 'scenario'):
            old.pop(k, None)
        tmp = R.out_path(out / '_r8a_check'); tmp.mkdir(exist_ok=True)
        try:                                              # fresh Rule 8a provenance, compared with the recorded one
            mp.write_provenance(tmp, list(R.HOLDOUT), f'{name}_h', 5434)
            check_existing_metadata(R.ROOT, old, json.loads((tmp / 'provenance.json').read_text()))
        finally:
            if (tmp / 'provenance.json').exists():
                (tmp / 'provenance.json').unlink()
            tmp.rmdir()
        q = R.write_new(R.free_name(out, 'provenance'), json.dumps({'revision11': r11}, indent=2) + '\n')
        print('provenance (resume) ->', q, flush=True)
        return
    mp.write_provenance(out, list(R.HOLDOUT), f'{name}_h', 5434)          # frozen inputs, MD5, Rule 8a, allocation
    data = json.loads(p.read_text())
    data.update(revision11=r11, stationary=(name == 'meas_s'), scenario=label)
    p.write_text(json.dumps(data, indent=2, ensure_ascii=False) + '\n')


def run(name):
    room, combos, out, label = SETS[name]
    run_set(room, combos, out, all_methods(), R.HOLDOUT, cfg_room=room, env='C', meas=True)


def validate(name):
    """Path provenance of every record = allocation(seed) with the scenario label and d0 (as Rule 9-D)."""
    import measured_paths as mp
    room, combos, out, label = SETS[name]
    n = 0
    for f in sorted(out.glob('runs_*.jsonl')):
        for r in R.read_jsonl(f):
            exp = dict(mp.allocation(r['seed']), scenario='M-P', removed_leading_samples_48k=5434)
            if r.get('path_provenance') != exp:
                raise ValueError(f"path provenance differs {r['method']} {r['noise']} {r['seed']}")
            n += 1
    print(f'{name}: {n} records with the expected MeshRIR paths ({label})')


def _bound(seed):
    import revision9_measured_s as m9
    return m9.bound_for_seed(seed)


def bounds():
    from concurrent.futures import ProcessPoolExecutor
    R.check_env('C', meas=True)
    out = R.out_path(SETS['meas_s'][2])
    with ProcessPoolExecutor(max_workers=2) as pool:
        rows = list(pool.map(_bound, R.HOLDOUT))
    (out / 'wiener_per_seed.json').write_text(json.dumps(rows, indent=2) + '\n')

    def q(v):
        return f'{np.median(v):.3f} ({np.quantile(v, .25):.3f}, {np.quantile(v, .75):.3f})'
    lines = ['# M-S causal Wiener lower bound (holdout seeds 800-839; same computation as Rule 9-D)', '',
             '| noise | total NR median (Q1,Q3) | ANC-only NR median (Q1,Q3) | norm >1000 |', '|---|---|---|---|']
    for nz in ('ar1', 'harmonic'):
        v = [r['noise'][nz] for r in rows]
        lines.append(f"| {nz} | {q([x['total_nr_db'] for x in v])} | {q([x['anc_only_nr_db'] for x in v])} | "
                     f"{sum(x['exceeds_simulator_norm_limit_1000'] for x in v)}/40 |")
    (out / 'wiener.md').write_text('\n'.join(lines) + '\n')


if __name__ == '__main__':
    cmd = sys.argv[1]
    if cmd == 'prepare':
        prepare()
    elif cmd == 'bounds':
        bounds()
    elif cmd in ('provenance', 'run', 'validate'):
        {'provenance': provenance, 'run': run, 'validate': validate}[cmd](sys.argv[2])
    else:
        raise ValueError(sys.argv)
