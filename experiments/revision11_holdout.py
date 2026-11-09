"""Revision 11 room-A holdout runs (seeds 800-839, 15 cells; environment A; Rule 11 Sec. 2.4, 3.5, 4.3).

  ablation : 11-A variants G1-G5 (own detection; no borrowed events) -> results/r11_ablation_holdout/runs_<shard>.jsonl
  new      : 11-B / 11-C new baselines (selected.json 'new_rows'; '+ det' rows consume the saved E-PCG main holdout
             events) -> results/final_eval_holdout_r11/runs_<shard>.jsonl
The uncontrolled power of every new record must equal the saved holdout record of the same key byte for byte (stop
otherwise). Existing holdout records (results/final_eval_holdout/) are only read.
usage:
  RLS_FAST=1 OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 SHARD=0/2 python experiments/revision11_holdout.py run ablation
  ... ROWS='MFBLMS;switching FD-FxNLMS [6]' SHARD=0/2 python experiments/revision11_holdout.py run new   (ROWS optional)
  ... VARIANTS='G1;G2' (optional) for 'run ablation'
  python experiments/revision11_holdout.py provenance ablation|new
"""
import json
import os
import sys
import zlib

import numpy as np

import revision11_methods as R

KINDS = {'ablation': R.ABL_DIR, 'new': R.HOLD_DIR, 'base': R.OLD_HOLD}


def run_base():
    """Rule 11 Sec. 9 item 8 (b) only (R11_HOLDOUT_BASE=envC): the 15 methods (13 baselines + main + bank) on the room-A
    holdout in environment C, E-PCG main first per key and its events saved (the revision9_holdout order)."""
    _check_base()
    from revision11_rooms import run_set
    meth = {'E-PCG': R.PROP['E-PCG']}; meth.update(R.BASE13); meth['E-PCG bank'] = R.PROP['E-PCG bank']
    run_set('A', R.COMBOS15, R.OLD_HOLD, meth, R.HOLDOUT, env='C')


def _check_base():
    """'base' writes R.OLD_HOLD, which is the saved 9-A holdout (results/final_eval_holdout/) unless
    R11_HOLDOUT_BASE=envC: refuse every 'base' command (run, provenance) otherwise (2026-11-07 review M-1; R.out_path
    refuses the write as well)."""
    if R.HOLDOUT_BASE != 'envC':
        raise ValueError('holdout base only with R11_HOLDOUT_BASE=envC (never into results/final_eval_holdout)')


def saved_up():
    """{(noise, scen, seed): full-length uncontrolled power} from the saved E-PCG main holdout records (read only)."""
    out = {}
    for f in sorted(R.OLD_HOLD.glob('runs_[01].jsonl')):
        for line in f.open():
            if '"method": "E-PCG",' not in line[:40]:
                continue
            r = json.loads(line)
            if r['method'] != 'E-PCG':
                continue
            k = (r['noise'], r['scen'], r['seed'])
            if len(r['up']) != r['hops_full']:
                raise ValueError(f'saved E-PCG record stopped early {k}')
            out[k] = np.asarray(r['up'], float)
    need = {(nz, sc, sd) for nz, sc in R.COMBOS15 for sd in R.HOLDOUT}
    if set(out) != need:
        raise ValueError(f'saved holdout E-PCG records incomplete {len(out)}/{len(need)}')
    return out


def methods(kind):
    if kind == 'ablation':
        keep = os.environ.get('VARIANTS')
        keep = keep.split(';') if keep else list(R.VARIANTS)
        return {R.VARIANTS[g][0]: ('E-PCG-F', R.VARIANTS[g][1]) for g in keep}
    rows = R.selected_new()
    keep = os.environ.get('ROWS')
    if keep:
        missing = set(keep.split(';')) - set(rows)
        if missing:
            raise ValueError(f'unknown rows {missing}')
        rows = {m: v for m, v in rows.items() if m in keep.split(';')}
    return rows


def run(kind):
    R.check_runtime_env(R.holdout_env())
    shard, total = map(int, os.environ['SHARD'].split('/'))
    if total != 2 or shard not in (0, 1):
        raise ValueError('expected SHARD 0/2 or 1/2')
    out = R.out_path(KINDS[kind]); out.mkdir(parents=True, exist_ok=True)
    meth = methods(kind)
    ups = saved_up(); events = R.holdout_events()
    path = out / f'runs_{shard}.jsonl'
    prior = R.read_jsonl(path, 'repair')                   # own shard file: a cut last line is dropped and redone
    done = {(r['method'], r['noise'], r['scen'], r['seed']) for r in prior}
    if len(done) != len(prior):
        raise ValueError('duplicate records')
    for r in prior:
        if r['method'] in meth and r['prm'] != meth[r['method']][1]:
            raise ValueError(f"stale record {r['method']}")
    with path.open('a') as fh:
        for name, (k, prm) in meth.items():
            for nz, sc in R.COMBOS15:
                for sd in R.HOLDOUT:
                    key = (name, nz, sc, sd)
                    if zlib.crc32('|'.join(map(str, key)).encode()) % 2 != shard or key in done:
                        continue
                    rec, _ = R.run_record(name, k, prm, 'A', nz, sc, sd, events[(nz, sc, sd)])
                    if np.asarray(rec['up'], float).tobytes() != ups[(nz, sc, sd)][:len(rec['up'])].tobytes():
                        raise ValueError(f'uncontrolled power differs from the saved holdout record: {key}')
                    if not np.all(np.isfinite(rec['tp'])) and rec['flag_stable']:
                        raise ValueError(f'non-finite power in a stable run {key}')
                    fh.write(json.dumps(rec) + '\n'); fh.flush()
            print(kind, shard, name, 'done', flush=True)


if __name__ == '__main__':
    cmd, kind = sys.argv[1], sys.argv[2]
    if kind not in KINDS:
        raise ValueError(kind)
    if cmd == 'run':
        run_base() if kind == 'base' else run(kind)
    elif cmd == 'provenance':
        if kind == 'base':
            _check_base()
        R.check_env(R.holdout_env())
        R.provenance(KINDS[kind], {'stage': f'holdout {kind}', 'seeds': [800, 839],
                                   'methods': ({**R.BASE13, **R.PROP} if kind == 'base' else methods(kind))}, [__file__])
    else:
        raise ValueError(sys.argv)
