"""Revision 9-A: independent holdout; one process per SHARD, no old-result writes."""
import hashlib
import json
import os
import sys
import time
import zlib
from pathlib import Path
import numpy as np
import eval_v2 as ev
import final_eval as fe

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'results/final_eval_holdout'
SEEDS = range(800, 840)
SELECTED = json.loads((ev.SEL / 'selected_e.json').read_text())['selected']
METHODS = {m: (ev.GRID[m][0], ev.GRID[m][1][i]) for m, i in SELECTED.items()}
# record labels of PCG-WLS / PCG-WLS (multi-window) in results/ (former names, see ffanc_norm.naming)
METHODS.update({'E-PCG': ('PCG-WLS-F', ev.MAIN), 'E-PCG bank': ('PCG-WLS-F', ev.BANK)})


def run_one(m, nz, sc, sd, events=None):
    method, prm = METHODS[m]
    params = dict(prm)
    if m in ev.DET:
        if events is None:
            raise ValueError('same-run E-PCG events missing')
        params['det_events'] = events
    start = time.time()
    r = ev.D.P.run(ev.cfg_of('A', nz, sc), sd, method, params, 5.0,
                   None if sc.startswith('S8') else ev.D.CH)
    tp, up = r['total_power'], r['uncontrolled_power']
    record = {'method': m, 'prm': prm, 'room': 'A', 'noise': nz, 'scen': sc, 'seed': sd,
              'flag_stable': bool(r['stable']), 'tp': list(map(float, tp)), 'up': list(map(float, up[:len(tp)])),
              'hops_full': len(up), 'wall_s': round(time.time()-start, 2),
              'flops_hop': float(np.mean(r['flop_hist'])) if r.get('flop_hist') else None,
              'n_restarts': len(params.get('det_events', []))}
    if m == 'E-PCG':
        if len(r['reset_hops']) != len(r['loc_hist']):
            raise ValueError('unaligned E-PCG detections')
        return record, [[(int(h)+1)*ev.H, int(t)] for h,t in zip(r['reset_hops'], r['loc_hist'])]
    return record, None


def run():
    shard, total = map(int, os.environ['SHARD'].split('/'))
    if total != 2 or shard not in (0,1): raise ValueError('expected 0/2 or 1/2')
    OUT.mkdir(parents=True, exist_ok=True)
    path = OUT / f'runs_{shard}.jsonl'
    eventpath = OUT / f'det_events_{shard}.jsonl'
    done = {}
    for line in path.read_text().splitlines() if path.exists() else []:
        r = json.loads(line); key = r['method'],r['noise'],r['scen'],r['seed']
        if key in done: raise ValueError(f'duplicate {key}')
        done[key] = r
    events = {}
    for line in eventpath.read_text().splitlines() if eventpath.exists() else []:
        r=json.loads(line); key=r['noise'],r['scen'],r['seed']
        if key in events: raise ValueError(f'duplicate event {key}')
        events[key]=r['events']
    with path.open('a') as out, eventpath.open('a') as det:
        for nz,sc in ev.COMBOS15:
            for sd in SEEDS:
                key=(nz,sc,sd)
                if zlib.crc32('|'.join(map(str,key)).encode())%2 != shard: continue
                ek=('E-PCG',*key)
                if ek not in done:
                    if key in events: raise ValueError(f'event without run {key}')
                    rec, e=run_one('E-PCG',nz,sc,sd)
                    det.write(json.dumps(dict(noise=nz,scen=sc,seed=sd,events=e))+'\n'); det.flush()
                    out.write(json.dumps(rec)+'\n'); out.flush(); events[key]=e
                if key not in events: raise ValueError(f'run without event {key}')
                for m in METHODS:
                    if m=='E-PCG' or (m,*key) in done: continue
                    rec,_=run_one(m,nz,sc,sd,events[key])
                    out.write(json.dumps(rec)+'\n'); out.flush()
                print(shard, nz,sc,sd,flush=True)


def provenance():
    import platform, subprocess
    from importlib.metadata import version
    OUT.mkdir(parents=True,exist_ok=True)
    rule=(ROOT/'docs/current/REVISION_RULE_9.md').read_text()
    p={'commit':subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),
       'rule':rule, 'rule_sha256':hashlib.sha256(rule.encode()).hexdigest(),
       'seeds':[800,839], 'python':platform.python_version(),
       'software':{x:version(x) for x in ['numpy','scipy','pyroomacoustics']},
       'RLS_FAST':os.environ.get('RLS_FAST'), 'threads':{x:os.environ.get(x) for x in ['OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','OMP_NUM_THREADS']}}
    (OUT/'provenance.json').write_text(json.dumps(p,indent=2)+'\n')

if __name__=='__main__':
    if sys.argv[1]=='run': run()
    elif sys.argv[1]=='provenance': provenance()
    else: raise ValueError(sys.argv)
