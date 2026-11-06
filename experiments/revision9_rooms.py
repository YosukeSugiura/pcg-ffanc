"""Revision 9-C additional baselines, using the existing PCG-WLS event cache."""
import json
import os
import sys
import time
import zlib
from pathlib import Path
import numpy as np
import eval_v2 as ev
import final_eval as fe
from revision9_holdout import ROOT, METHODS

SETS={'roomB':('B','eval_roomB'), 'roomC':('C','eval_roomC'), 'snr10':('A_snr10','eval_snr10')}
ADDED=['SFTF-H + det','CFTF + det']
OLD_BASE=['FD-FxNLMS','leaky FD-FxNLMS','convex FD-FxNLMS','FDKF','RLS','VFF-RLS','FD-FxNLMS + det','RLS + det']
PROP=['E-PCG','E-PCG bank']

def setup(name):
    if name not in SETS: raise ValueError(name)
    room,folder=SETS[name]
    _,combos,_=ev.EVAL_SETS[name]
    return room,combos,ROOT/'results'/folder,ROOT/'results'/(folder+'_x2')

def read_events(room,combos):
    events={}
    needed={(nz,sc,sd) for nz,sc in combos for sd in range(480,520)}
    for f in sorted((ROOT/'results/det_events').glob('*.jsonl')):
        for line in f.open():
            r=json.loads(line)
            if r['room']!=room: continue
            k=(r['noise'],r['scen'],r['seed'])
            if k not in needed: continue
            if k in events and events[k]!=r['events']: raise ValueError(f'conflicting event {room} {k}')
            events[k]=r['events']
    missing=needed-events.keys()
    if missing: raise ValueError(f'events missing: {len(missing)}; stop for verification, do not reuse another run')
    return events

def provenance(name):
    import hashlib,platform,subprocess
    from importlib.metadata import version
    room,combos,src,out=setup(name)
    events=read_events(room,combos)
    out.mkdir(parents=True,exist_ok=True)
    rule=(ROOT/'docs/current/REVISION_RULE_9.md').read_text()
    rule9a=(ROOT/'docs/current/REVISION_RULE_9a.md').read_text()
    versions={x:version(x) for x in ('numpy','scipy','pyroomacoustics')}
    expected={'numpy':'2.5.3','scipy':'1.18.1','pyroomacoustics':'0.10.1'}
    files=list(src.glob('runs*.jsonl'))+list((ROOT/'results/det_events').glob('*.jsonl'))
    data={'implementation_commit':subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),
          'rule_full_text':rule,'rule_sha256':hashlib.sha256(rule.encode()).hexdigest(),
          'event_keys':len({(nz,sc,sd) for nz,sc in combos for sd in range(480,520)}),
          'input_sha256':{str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(files)},
          'revision9a_rule_full_text':rule9a,'revision9a_rule_sha256':hashlib.sha256(rule9a.encode()).hexdigest(),
          'python':platform.python_version(),'software':versions,
          'RLS_FAST':os.environ.get('RLS_FAST'),
          'threads':{x:os.environ.get(x) for x in ('OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','OMP_NUM_THREADS')}}
    (out/'provenance.json').write_text(json.dumps(data,indent=2)+'\n')
    if versions!=expected: raise ValueError(f'Rule 9a version mismatch: {versions}')
    if os.environ.get('RLS_FAST')!='1' or any(os.environ.get(x)!='1' for x in ('OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','OMP_NUM_THREADS')):
        raise ValueError('Rule 9a thread or RLS_FAST mismatch')

def preflight(name):
    import hashlib,struct
    room,combos,src,out=setup(name)
    keys=[(nz,sc,sd) for nz,sc in (combos[0],combos[-1]) for sd in (480,519)]
    saved={}
    for f in sorted(src.glob('runs*.jsonl')):
        for line in f.open():
            r=json.loads(line); key=(r['noise'],r['scen'],r['seed'])
            if r['method']!='E-PCG' or key not in keys or r.get('prm')!=METHODS['E-PCG'][1]: continue
            if key in saved and any(saved[key][k]!=r[k] for k in ('tp','up','flag_stable','hops_full','flops_hop','n_restarts')):
                raise ValueError(f'conflicting saved E-PCG records: {key}')
            saved[key]=r
    if set(saved)!=set(keys): raise ValueError(f'missing saved E-PCG keys: {set(keys)-set(saved)}')
    events=read_events(room,combos); results=[]
    def array_bytes(v): return np.asarray(v,dtype='<f8').tobytes()
    def scalar_bytes(v): return None if v is None else struct.pack('<d',float(v))
    for nz,sc,sd in keys:
        key=(nz,sc,sd); old=saved[key]
        r=ev.D.P.run(ev.cfg_of(room,nz,sc),sd,'PCG-WLS-F',dict(ev.MAIN),5.0,None if sc.startswith('S8') else ev.D.CH)
        if len(r['reset_hops'])!=len(r['loc_hist']): raise ValueError(f'unaligned detections: {key}')
        got_events=[[(int(h)+1)*ev.H,int(t)] for h,t in zip(r['reset_hops'],r['loc_hist'])]
        tp=list(map(float,r['total_power'])); up=list(map(float,r['uncontrolled_power'][:len(tp)]))
        flop=float(np.mean(r['flop_hist'])) if r.get('flop_hist') else None
        checks={'tp':array_bytes(tp)==array_bytes(old['tp']), 'up':array_bytes(up)==array_bytes(old['up']),
                'flag_stable':bool(r['stable']) is bool(old['flag_stable']),
                'det_events':json.dumps(got_events,separators=(',',':')).encode()==json.dumps(events[key],separators=(',',':')).encode(),
                'hops_full':len(r['uncontrolled_power'])==old['hops_full'],
                'flops_hop':scalar_bytes(flop)==scalar_bytes(old['flops_hop']),
                'n_restarts':old['n_restarts']==0}
        results.append({'noise':nz,'scen':sc,'seed':sd,'checks':checks,
                        'tp_sha256':hashlib.sha256(array_bytes(tp)).hexdigest(),
                        'up_sha256':hashlib.sha256(array_bytes(up)).hexdigest()})
        (out/'preflight.json').write_text(json.dumps({'set':name,'cases':results,'pass':len(results)==4 and all(all(x['checks'].values()) for x in results)},indent=2)+'\n')
        print(name,key,checks,flush=True)
        if not all(checks.values()): raise ValueError(f'Rule 9a preflight mismatch: {key}')

def run(name):
    room,combos,_,out=setup(name); events=read_events(room,combos)
    shard,total=map(int,os.environ['SHARD'].split('/'))
    if total!=2 or shard not in (0,1): raise ValueError('expected 0/2 or 1/2')
    out.mkdir(parents=True,exist_ok=True); path=out/f'runs_added_{shard}.jsonl'
    prior=[json.loads(l) for l in path.read_text().splitlines()] if path.exists() else []
    seen={(r['method'],r['noise'],r['scen'],r['seed']) for r in prior}
    if len(prior)!=len(seen): raise ValueError('duplicate records')
    with path.open('a') as outstream:
        for nz,sc in combos:
            for sd in range(480,520):
                key=(nz,sc,sd)
                if zlib.crc32('|'.join(map(str,key)).encode())%2!=shard: continue
                for method in ADDED:
                    if (method,*key) in seen: continue
                    kind,prm=METHODS[method]; pars=dict(prm,det_events=events[key]); start=time.time()
                    r=ev.D.P.run(ev.cfg_of(room,nz,sc),sd,kind,pars,5.0,None if sc.startswith('S8') else ev.D.CH)
                    tp,up=r['total_power'],r['uncontrolled_power']
                    rec=dict(method=method,prm=prm,room=room,noise=nz,scen=sc,seed=sd,
                             flag_stable=bool(r['stable']),tp=list(map(float,tp)),up=list(map(float,up[:len(tp)])),
                             hops_full=len(up),wall_s=round(time.time()-start,2),
                             flops_hop=float(np.mean(r['flop_hist'])) if r.get('flop_hist') else None,
                             n_restarts=len(events[key]))
                    outstream.write(json.dumps(rec)+'\n');outstream.flush()
                print(shard,nz,sc,sd,flush=True)

def summary(name):
    room,combos,src,out=setup(name)
    methods={m:METHODS[m] for m in OLD_BASE+ADDED+PROP}; expected={(m,nz,sc,sd) for m in methods for nz,sc in combos for sd in range(480,520)}
    by={}
    for path in sorted(src.glob('runs*.jsonl'))+sorted(out.glob('runs_added_*.jsonl')):
        for line in path.open():
            r=json.loads(line); m=r['method']
            if m not in methods or r['prm']!=methods[m][1]: continue
            key=(m,r['noise'],r['scen'],r['seed'])
            if key not in expected: continue
            if key in by:
                a=by[key]
                if any(a[k]!=r[k] for k in ('tp','up','flag_stable')): raise ValueError(f'conflicting duplicate {key}')
            else: by[key]=r
    if set(by)!=expected: raise ValueError(f'incomplete combined data {len(by)}/{len(expected)}')
    # Reuse FE's strict validation and plots in the new directory only.
    combined=out/'runs_combined.jsonl'
    combined.write_text(''.join(json.dumps(r)+'\n' for r in by.values() if r['method'] not in ADDED))
    fe.OUT=out;fe.METH=methods;fe.BASE=OLD_BASE+ADDED;fe.PROP=PROP;fe.ALL=fe.BASE+PROP
    fe.COMBOS=combos;fe.SEEDS=list(range(480,520));fe.EXTRA_UP={}
    extra=src/'uncontrolled.jsonl'
    if extra.exists():
        for l in extra.open():
            r=json.loads(l); fe.EXTRA_UP[(r['noise'],r['scen'],r['seed'])]=r['up']
    fe.summary()
    p=out/'summary.md'; p.write_text(f'# Revision 9-C {name}: combined original and additional baselines\n\n'+p.read_text())

if __name__=='__main__':
    if len(sys.argv)!=3: raise ValueError('expected run|summary|provenance|preflight and roomB|roomC|snr10')
    if sys.argv[1]=='run':run(sys.argv[2])
    elif sys.argv[1]=='summary':summary(sys.argv[2])
    elif sys.argv[1]=='provenance':provenance(sys.argv[2])
    elif sys.argv[1]=='preflight':preflight(sys.argv[2])
    else:raise ValueError(sys.argv)
