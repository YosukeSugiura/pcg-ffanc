"""Measure selected SciPy quantile calls inside controller updates; no algorithm changes.

Run only after plan review: OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1
MKL_NUM_THREADS=1 RLS_FAST=1 OPENBLAS_CORETYPE=SkylakeX taskset -c CPU python experiments/ringbuf_isf_profile.py OUT --execute
OUT must be a new directory under results. Results are observational,
include instrumentation overhead, and are not the sum of all uncounted work.
"""
from contextlib import contextmanager
import argparse
import hashlib
import json
import os
from pathlib import Path
import pickle
import platform
import subprocess
from importlib.metadata import version
import sys
import time

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT/'src'), str(ROOT/'experiments')]
CELLS = ('S8 stationary', 'S1 src 10cm', 'S2 src 30cm', 'S5 src 30cm cont',
         'S7 rd abrupt', 'R1 rig 10cm', 'R2 rig 30cm', 'R3 rig 30cm cont')
COMBOS = tuple((n, s) for n in ('ar1', 'harmonic') for s in CELLS if (n, s) != ('harmonic', 'S7 rd abrupt'))
SEEDS = tuple(range(300, 305))
FLAGS = {'main': ROOT/'results/final_dev/final_config_core_main.json',
         'bank': ROOT/'results/final_dev/final_config_core_final.json'}


def sha(data):
    return hashlib.sha256(data).hexdigest()


def serialized(value):
    return pickle.dumps(value, protocol=5)


def comparison(reference, observed):
    """Strict serialized bytes for every returned field, including raw e and event lists."""
    fields = sorted(set(reference) | set(observed))
    differences = [key for key in fields if key not in reference or key not in observed or
                   serialized(reference[key]) != serialized(observed[key])]
    if 'e' not in reference or 'e' not in observed:
        raise ValueError('raw error signal is required')
    a, b = reference['e'], observed['e']
    if not isinstance(a, np.ndarray) or not isinstance(b, np.ndarray):
        raise ValueError('raw error signal must be an ndarray')
    raw_equal = a.dtype == b.dtype and a.shape == b.shape and a.tobytes() == b.tobytes()
    return {'all_fields_equal': not differences, 'different_fields': differences,
            'raw_error_equal': raw_equal,
            'reference_e_sha256': sha(a.tobytes()), 'reference_e_dtype': str(a.dtype), 'reference_e_shape': list(a.shape),
            'instrumented_e_sha256': sha(b.tobytes()), 'instrumented_e_dtype': str(b.dtype), 'instrumented_e_shape': list(b.shape),
            'event_fields': {key: {'equal': serialized(reference[key]) == serialized(observed[key]),
                'reference_sha256': sha(serialized(reference[key])),
                'instrumented_sha256': sha(serialized(observed[key]))}
                for key in ('reset_hops', 'loc_hist', 'n_resets', 'events_total')},
            'reference_result_sha256': sha(serialized(reference)),
            'instrumented_result_sha256': sha(serialized(observed))}


@contextmanager
def profile_updates(classes, distributions, clock=time.perf_counter_ns):
    """Count outer update once, and quantile calls only while inside that update."""
    state = {'depth': 0, 'update_ns': 0, 'updates': 0,
             'isf': {name: {'ns': 0, 'calls': 0} for name in distributions}}
    restore = []
    try:
        for name, dist in distributions.items():
            # Capture an instance override without permanently shadowing the class method.
            prior = dist.__dict__.get('isf'); existed = 'isf' in dist.__dict__
            original = dist.isf
            def wrap_isf(*args, _original=original, _name=name, **kwargs):
                if not state['depth']:
                    return _original(*args, **kwargs)
                start = clock()
                try:
                    return _original(*args, **kwargs)
                finally:
                    state['isf'][_name]['ns'] += clock()-start
                    state['isf'][_name]['calls'] += 1
            setattr(dist, 'isf', wrap_isf); restore.append((dist, 'isf', prior, existed))
        for cls in classes:
            original = cls.update
            def wrap_update(self, *args, _original=original, **kwargs):
                outer = state['depth'] == 0
                start = clock() if outer else None
                state['depth'] += 1
                try:
                    return _original(self, *args, **kwargs)
                finally:
                    state['depth'] -= 1
                    if outer:
                        state['update_ns'] += clock()-start
                        state['updates'] += 1
            setattr(cls, 'update', wrap_update); restore.append((cls, 'update', original, True))
        yield state
    finally:
        for obj, name, value, existed in reversed(restore):
            if existed: setattr(obj, name, value)
            else: delattr(obj, name)


def runtime():
    import scipy
    from threadpoolctl import threadpool_info
    env = {k: os.environ.get(k) for k in ('OPENBLAS_NUM_THREADS', 'OMP_NUM_THREADS', 'MKL_NUM_THREADS', 'RLS_FAST', 'OPENBLAS_CORETYPE')}
    pools = threadpool_info(); affinity = sorted(os.sched_getaffinity(0))
    if (any(env[k] != '1' for k in ('OPENBLAS_NUM_THREADS', 'OMP_NUM_THREADS', 'MKL_NUM_THREADS', 'RLS_FAST'))
            or env['OPENBLAS_CORETYPE'] != 'SkylakeX' or len(affinity) != 1 or not pools
            or any(p['num_threads'] != 1 for p in pools)
            or not any('openblas' in str(p).lower() for p in pools)
            or any(p.get('architecture') != 'SkylakeX' for p in pools if 'openblas' in str(p).lower())):
        raise ValueError('one pinned CPU and one BLAS/OMP/MKL thread required')
    return {'python': platform.python_version(), 'numpy': np.__version__, 'scipy': scipy.__version__,
            'platform': platform.platform(), 'pyroomacoustics': version('pyroomacoustics'),
            'affinity': affinity, 'environment': env, 'threadpools': pools, 'loadavg': os.getloadavg()}


def run_pair(protocol, classes, distributions, cfg, seed, flags, scene):
    previous = protocol.RETURN_SIGNALS
    try:
        protocol.RETURN_SIGNALS = True
        args = (cfg, seed, 'E-PCG-F', dict(flags), 5., None if scene.startswith('S8') else 1.)
        uninstrumented = protocol.run(*args)
        with profile_updates(classes, distributions) as stats:
            instrumented = protocol.run(*args)
        check = comparison(uninstrumented, instrumented)
        total_isf = sum(x['ns'] for x in stats['isf'].values())
        return {'comparison': check, 'update_ns': stats['update_ns'], 'updates': stats['updates'],
                'isf': stats['isf'], 'isf_ns': total_isf,
                'isf_fraction_of_instrumented_update': total_isf/stats['update_ns'] if stats['update_ns'] else None,
                'stable_reference': uninstrumented['stable'], 'stable_instrumented': instrumented['stable'],
                'hops_reference': len(uninstrumented['total_power']), 'hops_instrumented': len(instrumented['total_power'])}
    finally:
        protocol.RETURN_SIGNALS = previous


def main():
    p = argparse.ArgumentParser(description=__doc__); p.add_argument('out', type=Path); p.add_argument('--execute', action='store_true')
    args = p.parse_args()
    if not args.execute: raise ValueError('explicit --execute required')
    out = args.out.resolve()
    if not out.is_relative_to(ROOT/'results') or out == ROOT/'results':
        raise ValueError('output must be a new directory under results')
    import verify_protocol_defs as D
    from ffanc_norm.epcg import EPCG
    from ffanc_norm.epcg_bank import EPCGBank
    from scipy.stats import chi2, f, norm
    env = runtime()
    flags = {name: json.loads(path.read_text())['flags'] for name, path in FLAGS.items()}
    out.mkdir(parents=True, exist_ok=False)
    plan = {'combos': COMBOS, 'seeds': SEEDS, 'methods': list(FLAGS), 'duration_s': 5.,
            'order': 'unmeasured then instrumented, once per case', 'runtime': env,
            'flags': flags, 'flag_file_sha256': {k: sha(v.read_bytes()) for k, v in FLAGS.items()},
            'runner_sha256': sha(Path(__file__).read_bytes()),
            'plan_sha256': sha((ROOT/'docs/current/RINGBUF_ISF_PROFILE_PLAN.md').read_bytes()),
            'commit': subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip(),
            'source_sha256': {str(p.relative_to(ROOT)): sha(p.read_bytes()) for d, pat in
                (('src', '*.py'), ('experiments', '*.py'), ('configs', '*.json')) for p in (ROOT/d).rglob(pat)},
            'limits': 'Selected isf functions inside update only; timings include wrapper and clock overhead. Not total uncounted cost or WCET.'}
    (out/'plan.json').write_text(json.dumps(plan, indent=2)+'\n')
    for method in FLAGS:
        for noise, scene in COMBOS:
            for seed in SEEDS:
                cfg = dict(D.SCEN[scene], controller_length=512, fft_length=1024,
                           **({} if noise == 'ar1' else {'noise_type': noise}))
                key = f'{method}_{noise}_{scene.split()[0]}_{seed}'
                try:
                    row = run_pair(D.P, (EPCG, EPCGBank), {'chi2': chi2, 'f': f, 'norm': norm}, cfg, seed, flags[method], scene)
                except Exception as exc:
                    row = {'exception': f'{type(exc).__name__}: {exc}'}
                row.update(method=method, noise=noise, scene=scene, seed=seed)
                with (out/(key+'.json')).open('x') as stream: json.dump(row, stream, indent=2, allow_nan=False)
                print(key, row.get('comparison', {}).get('all_fields_equal'), row.get('exception', ''), flush=True)
    (out/'complete.json').write_text(json.dumps({'expected': 150, 'records': len(list(out.glob('*_*_*.json'))),
        'loadavg_end': os.getloadavg()})+'\n')


if __name__ == '__main__': main()
