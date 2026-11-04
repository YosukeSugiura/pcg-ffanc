"""Revision 9-D stationary measured paths, frozen Rule 8a preprocessing."""
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
import measured_paths as mp
from revision9_holdout import ROOT, METHODS

OUT=ROOT/'results/final_eval_meas_s_8a'
COMBOS=[(nz,'S8 stationary') for nz in ('ar1','harmonic')]
SEEDS=range(480,520)

def cfg(nz):
    c=ev.cfg_of('M_8a',nz,'S8 stationary')
    c['move_target']='source'
    return c

def provenance():
    mp.write_provenance(OUT, list(SEEDS), 'meas_s_8a', 5434)
    p=OUT/'provenance.json'; data=json.loads(p.read_text())
    rule=(ROOT/'docs/current/REVISION_RULE_9.md').read_text()
    rule9a=(ROOT/'docs/current/REVISION_RULE_9a.md').read_text()
    data.update(revision9_rule_full_text=rule,revision9_rule_sha256=hashlib.sha256(rule.encode()).hexdigest(),
                revision9a_rule_full_text=rule9a,revision9a_rule_sha256=hashlib.sha256(rule9a.encode()).hexdigest(),
                stationary=True,change_at=None)
    p.write_text(json.dumps(data,indent=2,ensure_ascii=False)+'\n')
    from importlib.metadata import version
    import platform
    data['python']=platform.python_version()
    data['RLS_FAST']=os.environ.get('RLS_FAST')
    data['threads']={x:os.environ.get(x) for x in ('OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','OMP_NUM_THREADS')}
    p.write_text(json.dumps(data,indent=2,ensure_ascii=False)+'\n')
    if {x:version(x) for x in ('numpy','scipy','pyroomacoustics')} != {'numpy':'2.5.3','scipy':'1.18.1','pyroomacoustics':'0.10.1'}:
        raise ValueError('Rule 9a numeric environment mismatch')
    if data['RLS_FAST']!='1' or any(v!='1' for v in data['threads'].values()): raise ValueError('Rule 9a thread or RLS_FAST mismatch')

def one(m,nz,sd,events=None):
    kind,prm=METHODS[m]; pars=dict(prm)
    if m in ev.DET:
        if events is None: raise ValueError('missing same-run detector events')
        pars['det_events']=events
    start=time.time(); r=ev.D.P.run(cfg(nz),sd,kind,pars,5.0,None)
    tp,up=r['total_power'],r['uncontrolled_power']
    path=dict(r['path_provenance']); path['scenario']='M-S'
    rec=dict(method=m,prm=prm,room='M_8a',noise=nz,scen='S8 stationary',seed=sd,
             flag_stable=bool(r['stable']),tp=list(map(float,tp)),up=list(map(float,up[:len(tp)])),
             hops_full=len(up),wall_s=round(time.time()-start,2),
             flops_hop=float(np.mean(r['flop_hist'])) if r.get('flop_hist') else None,
             n_restarts=len(pars.get('det_events',[])),path_provenance=path)
    if m=='E-PCG':
        if len(r['reset_hops'])!=len(r['loc_hist']):raise ValueError('unaligned events')
        return rec,[[(int(h)+1)*ev.H,int(t)] for h,t in zip(r['reset_hops'],r['loc_hist'])]
    return rec,None

def run():
    shard,total=map(int,os.environ['SHARD'].split('/'))
    if total!=2 or shard not in (0,1):raise ValueError('expected 0/2 or 1/2')
    path=OUT/f'runs_{shard}.jsonl'; eventfile=OUT/f'det_events_{shard}.jsonl'
    prior=[json.loads(l) for l in path.read_text().splitlines()] if path.exists() else []
    seen={(r['method'],r['noise'],r['seed']) for r in prior}
    if len(seen)!=len(prior):raise ValueError('duplicate records')
    elist=[json.loads(l) for l in eventfile.read_text().splitlines()] if eventfile.exists() else []
    events={(r['noise'],r['seed']):r['events'] for r in elist}
    if len(events)!=len(elist):raise ValueError('duplicate events')
    with path.open('a') as stream,eventfile.open('a') as det:
        for nz,_ in COMBOS:
            for sd in SEEDS:
                key=(nz,sd)
                if zlib.crc32('|'.join(map(str,key)).encode())%2!=shard:continue
                if ('E-PCG',*key) not in seen:
                    if key in events:raise ValueError('event without E-PCG run')
                    rec,e=one('E-PCG',nz,sd)
                    det.write(json.dumps(dict(noise=nz,seed=sd,events=e))+'\n');det.flush()
                    stream.write(json.dumps(rec)+'\n');stream.flush();events[key]=e
                if key not in events:raise ValueError('E-PCG run without event')
                for m in METHODS:
                    if m=='E-PCG' or (m,*key) in seen:continue
                    rec,_=one(m,nz,sd,events[key]);stream.write(json.dumps(rec)+'\n');stream.flush()
                print(shard,nz,sd,flush=True)

def bound_for_seed(seed):
    import diag_meas_bound as b
    p,s,_,_=mp.meshrir_paths(dict(sample_rate=8000,len_p=1200,len_s=512,move_steps=0,
                                     move_target='source',meshrir_d0=5434),seed)
    out={'seed':seed,'noise':{}}
    for nz in ('ar1','harmonic'):
        x,weights=b.reference(seed,nz)
        sensor=float(np.mean(np.convolve(x,p)[:40000]**2))/100
        out['noise'][nz]=b.bound(p,s,s,weights,sensor)
    return out

def bounds():
    from concurrent.futures import ProcessPoolExecutor
    with ProcessPoolExecutor(max_workers=2) as pool:rows=list(pool.map(bound_for_seed,SEEDS))
    (OUT/'wiener_per_seed.json').write_text(json.dumps(rows,indent=2)+'\n')
    def q(v):return f'{np.median(v):.3f} ({np.quantile(v,.25):.3f}, {np.quantile(v,.75):.3f})'
    lines=['# M-S causal Wiener lower bound', '', '| noise | total NR median (Q1,Q3) | ANC-only NR median (Q1,Q3) | norm >1000 |', '|---|---|---|---|']
    for nz in ('ar1','harmonic'):
        values=[r['noise'][nz] for r in rows]
        lines.append(f"| {nz} | {q([v['total_nr_db'] for v in values])} | {q([v['anc_only_nr_db'] for v in values])} | {sum(v['exceeds_simulator_norm_limit_1000'] for v in values)}/40 |")
    (OUT/'wiener.md').write_text('\n'.join(lines)+'\n')

def summary():
    expected={(m,nz,sc,sd) for m in METHODS for nz,sc in COMBOS for sd in SEEDS};seen=set()
    for path in OUT.glob('runs_*.jsonl'):
        for line in path.open():
            r=json.loads(line);key=(r['method'],r['noise'],r['scen'],r['seed'])
            if key not in expected or key in seen or r['prm']!=METHODS[r['method']][1]:raise ValueError(f'unexpected or stale {key}')
            expected_path=dict(mp.allocation(r['seed']),scenario='M-S',removed_leading_samples_48k=5434)
            if r['path_provenance']!=expected_path:raise ValueError(f'path mismatch {key}')
            seen.add(key)
    if seen!=expected:raise ValueError(f'incomplete {len(seen)}/{len(expected)}')
    fe.OUT=OUT;fe.METH=METHODS;fe.BASE=list(ev.GRID);fe.PROP=['E-PCG','E-PCG bank'];fe.ALL=fe.BASE+fe.PROP
    fe.COMBOS=COMBOS;fe.SEEDS=list(SEEDS);fe.EXTRA_UP={};fe.summary()
    p=OUT/'summary.md';p.write_text('# Revision 9-D: stationary measured paths (M-S)\n\n'+p.read_text()+'\n'+(OUT/'wiener.md').read_text())

if __name__=='__main__':
    if sys.argv[1]=='provenance':provenance()
    elif sys.argv[1]=='run':run()
    elif sys.argv[1]=='bounds':bounds()
    elif sys.argv[1]=='summary':summary()
    else:raise ValueError(sys.argv)
