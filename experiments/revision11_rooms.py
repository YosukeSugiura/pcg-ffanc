"""Revision 11-D (Rule 11 Sec. 5): rooms B / C and SNR 10 dB on the holdout seeds 800-839, all baselines (13 + n_new)
and both proposals, environment C. Order per key (as revision9_holdout): E-PCG main -> its events saved
(det_events_<shard>.jsonl in the set directory) -> the other methods, '+ det' baselines consuming those events.

  results/eval_roomB_h/, results/eval_roomC_h/, results/eval_snr10_h/   (new; nothing else is written)
usage:
  RLS_FAST=1 OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 SHARD=0/2 python experiments/revision11_rooms.py run roomB
  python experiments/revision11_rooms.py fill roomC        # uncontrolled power where every method stopped early
  python experiments/revision11_rooms.py provenance roomB
(summary: experiments/revision11_summary.py rooms roomB)
"""
import json
import os
import sys
import zlib

import eval_v2 as ev
import revision11_methods as R

SETS = {'roomB': ('B', 'eval_roomB_h'), 'roomC': ('C', 'eval_roomC_h'), 'snr10': ('A_snr10', 'eval_snr10_h')}


def setup(name):
    room, folder = SETS[name]
    combos = ev.EVAL_SETS[name][1]
    return room, combos, R.RES / folder


def all_methods():
    """13 baselines + the n_new selected new baselines + the two proposals (E-PCG main first)."""
    m = {'E-PCG': R.PROP['E-PCG']}
    m.update(R.BASE13); m.update(R.selected_new()); m['E-PCG bank'] = R.PROP['E-PCG bank']
    return m


def read_state(out, shard, meth):
    """Own shard files; a last line cut by an interrupted worker is dropped (file truncated to its complete lines) and
    that run is redone (2026-11-07 review M-4)."""
    path = out / f'runs_{shard}.jsonl'; evp = out / f'det_events_{shard}.jsonl'
    prior = R.read_jsonl(path, 'repair')
    done = {(r['method'], r['noise'], r['scen'], r['seed']) for r in prior}
    if len(done) != len(prior):
        raise ValueError('duplicate records')
    for r in prior:
        if r['method'] not in meth or r['prm'] != meth[r['method']][1]:
            raise ValueError(f"unexpected or stale record {r['method']}")
    el = R.read_jsonl(evp, 'repair')
    events = {(r['noise'], r['scen'], r['seed']): r['events'] for r in el}
    if len(events) != len(el):
        raise ValueError('duplicate events')
    return path, evp, done, events


def run_set(room, combos, out, meth, seeds, cfg_room=None, env='C', meas=False):
    """Shared loop for rooms and measured sets (one shard). Environment C (Rule 11 Sec. 1.2; meas: + numba, soundfile)."""
    R.check_runtime_env(env, meas)
    shard, total = map(int, os.environ['SHARD'].split('/'))
    if total != 2 or shard not in (0, 1):
        raise ValueError('expected SHARD 0/2 or 1/2')
    R.out_path(out).mkdir(parents=True, exist_ok=True)
    path, evp, done, events = read_state(out, shard, meth)
    with path.open('a') as fh, evp.open('a') as det:
        for nz, sc in combos:
            for sd in seeds:
                key = (nz, sc, sd)
                if zlib.crc32('|'.join(map(str, key)).encode()) % 2 != shard:
                    continue
                if ('E-PCG', *key) not in done:
                    rec, own = R.run_record('E-PCG', *meth['E-PCG'], cfg_room or room, nz, sc, sd)
                    rec['room'] = room
                    if key in events:
                        # the events line was written, the E-PCG record was cut (M-4): the re-run must give the same
                        # events (deterministic run); the events line is kept as it is
                        if own != events[key]:
                            raise ValueError(f'E-PCG re-run gives other events than the saved line {key}')
                    else:
                        det.write(json.dumps({'noise': nz, 'scen': sc, 'seed': sd, 'events': own}) + '\n'); det.flush()
                        events[key] = own
                    fh.write(json.dumps(rec) + '\n'); fh.flush()
                if key not in events:
                    raise ValueError(f'E-PCG run without event {key}')
                for m, (k, prm) in meth.items():
                    if m == 'E-PCG' or (m, *key) in done:
                        continue
                    rec, _ = R.run_record(m, k, prm, cfg_room or room, nz, sc, sd, events[key])
                    rec['room'] = room
                    fh.write(json.dumps(rec) + '\n'); fh.flush()
                print(shard, nz, sc, sd, flush=True)


def fill(name):
    """eval_v2.uncontrolled_fill for the new directory: a no-control run (FD-FxNLMS mu = 0) for keys where every
    method stopped early; stored in <set>/uncontrolled.jsonl (not a runs file)."""
    R.check_env('C')
    room, combos, out = setup(name)
    nh = int(R.TT * 8000) // R.H
    full, keys = set(), set()
    for f in out.glob('runs_*.jsonl'):
        for r in R.read_jsonl(f):
            k = (r['noise'], r['scen'], r['seed']); keys.add(k)
            if len(r['up']) == nh:
                full.add(k)
    fn = R.out_path(out / 'uncontrolled.jsonl')
    have = {(r['noise'], r['scen'], r['seed']) for r in R.read_jsonl(fn, 'repair')}
    for k in sorted(keys - full - have):
        rec, _ = R.run_record('no control', 'fixed_binwise', {'mu': 0.0}, room, *k)
        if len(rec['up']) != nh or not rec['flag_stable']:
            raise ValueError(f'no-control run stopped early {k}')
        with fn.open('a') as fh:
            fh.write(json.dumps({'noise': k[0], 'scen': k[1], 'seed': k[2], 'up': rec['up']}) + '\n')
    print(f'{name}: {len(keys - full)} key(s) without a full-length record', flush=True)


if __name__ == '__main__':
    cmd, name = sys.argv[1], sys.argv[2]
    room, combos, out = setup(name)
    if cmd == 'run':
        run_set(room, combos, out, all_methods(), R.HOLDOUT)
    elif cmd == 'fill':
        fill(name)
    elif cmd == 'provenance':
        R.check_env('C')
        R.provenance(out, {'stage': f'11-D {name}', 'seeds': [800, 839], 'combos': combos,
                           'methods': all_methods()}, [__file__])
    else:
        raise ValueError(sys.argv)
