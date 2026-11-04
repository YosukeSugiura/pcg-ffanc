"""Revision 9-B tuning with the frozen six detector configurations."""
import json
import os
import sys
import time
from pathlib import Path
import numpy as np
import eval_v2 as ev

OUT = Path(__file__).resolve().parents[1] / 'results/protocol_v2_sel_cusum'
GRID = [dict(lam=0.9999,delta=0.01,cusum_h=h,cusum_k=k) for h in (3,5,8) for k in (16,32)]
TUNE = list(range(300,310)) + list(range(600,620))

def provenance():
    import hashlib,platform,subprocess
    from importlib.metadata import version
    OUT.mkdir(parents=True,exist_ok=True)
    rule=(ev.ROOT/'docs/current/REVISION_RULE_9.md').read_text()
    data={'implementation_commit':subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),
          'rule_full_text':rule,'rule_sha256':hashlib.sha256(rule.encode()).hexdigest(),
          'grid':GRID,'tuning_seeds':TUNE,'python':platform.python_version(),
          'software':{x:version(x) for x in ('numpy','scipy','pyroomacoustics')},
          'RLS_FAST':os.environ.get('RLS_FAST'),
          'threads':{x:os.environ.get(x) for x in ('OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','OMP_NUM_THREADS')}}
    (OUT/'provenance.json').write_text(json.dumps(data,indent=2)+'\n')

def select_run():
    shard,total=map(int,os.environ['SHARD'].split('/'))
    if total!=2 or shard not in (0,1): raise ValueError('expected 0/2 or 1/2')
    OUT.mkdir(parents=True,exist_ok=True)
    path=OUT/f'runs_{shard}.jsonl'
    records=[json.loads(l) for l in path.read_text().splitlines()] if path.exists() else []
    seen={(r['cfg'],r['noise'],r['scen'],r['seed']) for r in records}
    if len(seen)!=len(records): raise ValueError('duplicate records')
    bad={r['cfg'] for r in records if r['fail']}
    with path.open('a') as out:
        for ci,prm in enumerate(GRID):
            if ci%2!=shard: continue
            for sd in TUNE:
                if ci in bad: break
                for nz,sc in ev.COMBOS15:
                    if (ci,nz,sc,sd) in seen: continue
                    start=time.time()
                    r=ev.D.P.run(ev.cfg_of('A',nz,sc),sd,'R-RLS',prm,5.0,None if sc.startswith('S8') else ev.D.CH)
                    tp,up=r['total_power'],r['uncontrolled_power']
                    rec=dict(method='RLS + CUSUM',cfg=ci,prm=prm,noise=nz,scen=sc,seed=sd,
                             flag_stable=bool(r['stable']),tp=list(map(float,tp)),up=list(map(float,up[:len(tp)])),
                             hops_full=len(up),wall_s=round(time.time()-start,2),
                             events=[[(int(h)+1)*ev.H,int(t)] for h,t in zip(r['reset_hops'],r['loc_hist'])])
                    if len(r['reset_hops'])!=len(r['loc_hist']): raise ValueError('unaligned events')
                    met=ev.run_metrics(rec); rec.update(fail=met['fail'],A1=met['A1'],A2=met['A2'])
                    out.write(json.dumps(rec)+'\n'); out.flush()
                    if rec['fail']: bad.add(ci); break
            print(shard,ci,'failed' if ci in bad else 'complete',flush=True)

def summary():
    rs=[]
    for f in sorted(OUT.glob('runs_*.jsonl')):
        rs.extend(json.loads(l) for l in f.read_text().splitlines())
    expected={(nz,sc,sd) for nz,sc in ev.COMBOS15 for sd in TUNE}
    admissible=[]; notes=[]
    for ci,prm in enumerate(GRID):
        rows=[r for r in rs if r['cfg']==ci]
        if any(r['prm']!=prm for r in rows): raise ValueError('stale configuration')
        keys={(r['noise'],r['scen'],r['seed']) for r in rows}
        if len(keys)!=len(rows): raise ValueError('duplicate')
        if any(r['fail'] for r in rows): notes.append(f'{ci}: failed'); continue
        if keys!=expected: raise ValueError(f'incomplete configuration {ci}: {len(keys)}/450')
        score=ev.score(rows); admissible.append((score,ci)); notes.append(f'{ci}: {score:.12g}')
    if not admissible: raise ValueError('no admissible configuration')
    score,ci=min(admissible)
    data={'method':'RLS + CUSUM','selected':ci,'params':GRID[ci],'score':score,'grid':GRID,'results':notes}
    (OUT/'selected.json').write_text(json.dumps(data,indent=2)+'\n')
    (OUT/'selection.md').write_text('# RLS + CUSUM selection\n\n'+ '\n'.join(f'- {x}' for x in notes)+f'\n\nSelected {ci}: {GRID[ci]} (score {score:.12g}).\n')
    print(data)

def evaluate():
    from revision9_holdout import OUT as HOLDOUT, SEEDS
    shard,total=map(int,os.environ['SHARD'].split('/'))
    if total!=2 or shard not in (0,1): raise ValueError('expected 0/2 or 1/2')
    selected=json.loads((OUT/'selected.json').read_text())
    ci=selected['selected']; prm=GRID[ci]
    if selected['params']!=prm: raise ValueError('selection/config mismatch')
    path=HOLDOUT/f'runs_cusum_{shard}.jsonl'
    records=[json.loads(l) for l in path.read_text().splitlines()] if path.exists() else []
    seen={(r['noise'],r['scen'],r['seed']) for r in records}
    if len(seen)!=len(records) or any(r['prm']!=prm for r in records): raise ValueError('duplicate/stale record')
    with path.open('a') as out:
        for idx,(nz,sc,sd) in enumerate((nz,sc,sd) for nz,sc in ev.COMBOS15 for sd in SEEDS):
            if idx%2!=shard or (nz,sc,sd) in seen: continue
            start=time.time()
            r=ev.D.P.run(ev.cfg_of('A',nz,sc),sd,'R-RLS',prm,5.0,None if sc.startswith('S8') else ev.D.CH)
            if len(r['reset_hops'])!=len(r['loc_hist']): raise ValueError('unaligned events')
            tp,up=r['total_power'],r['uncontrolled_power']
            rec=dict(method='RLS + CUSUM',prm=prm,room='A',noise=nz,scen=sc,seed=sd,
                     flag_stable=bool(r['stable']),tp=list(map(float,tp)),up=list(map(float,up[:len(tp)])),
                     hops_full=len(up),wall_s=round(time.time()-start,2),
                     flops_hop=float(np.mean(r['flop_hist'])) if r.get('flop_hist') else None,
                     n_restarts=len(r['reset_hops']),
                     events=[[(int(h)+1)*ev.H,int(t)] for h,t in zip(r['reset_hops'],r['loc_hist'])])
            out.write(json.dumps(rec)+'\n'); out.flush()
            print(shard,nz,sc,sd,flush=True)

if __name__=='__main__':
    if sys.argv[1]=='run': select_run()
    elif sys.argv[1]=='summary': summary()
    elif sys.argv[1]=='evaluate': evaluate()
    elif sys.argv[1]=='provenance': provenance()
    else: raise ValueError(sys.argv)
