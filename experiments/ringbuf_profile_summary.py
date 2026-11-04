"""Descriptive summary of previously saved history and isf observations."""
from pathlib import Path
from collections import defaultdict, Counter
import gzip, json, statistics
import numpy as np

ROOT=Path(__file__).resolve().parents[1]
HISTORY=ROOT/'results/ringbuf_history_access'
ISF=ROOT/'results/ringbuf_isf_profile'
OUT=ROOT/'results/ringbuf_profile_analysis'

def main():
    OUT.mkdir(parents=True,exist_ok=False)
    grouped=defaultdict(list); call_counts=defaultdict(Counter); verified=Counter(); observed=defaultdict(set)
    for p in sorted((HISTORY/'cases').glob('*.json')):
        case=json.loads(p.read_text()); mode=case['mode']; noise,scene,seed=case['case']
        verified[(mode, bool(case['verified']))]+=1
        for key,value in case['traced']['calls'].items(): call_counts[mode][key]+=value
        with gzip.open(HISTORY/'access'/(p.stem+'.jsonl.gz'),'rt') as f:
            for line in f:
                row=json.loads(line); observed[mode].add(row['caller'])
                age=row['oldest_age_from_stop']
                if age is None: continue
                key=(mode,noise,scene,row['kind'],row['field'])
                grouped[key].append((age,int(seed),row['stop'],row['member'],row['caller']))
    groups=[]
    for key,items in sorted(grouped.items()):
        values=np.array([i[0] for i in items]); maximum=int(values.max()); worst=sorted(i for i in items if i[0]==maximum)
        example=worst[0]
        groups.append(dict(mode=key[0],noise=key[1],scene=key[2],kind=key[3],field=key[4],count=len(items),
             median=float(np.median(values)),q99=float(np.quantile(values,.99)),max=maximum,
             max_example=dict(seed=example[1],stop=example[2],hop=example[2]/128,member=example[3],caller=example[4]),
             ties=len(worst)))
    isf=defaultdict(list)
    for p in sorted(ISF.glob('*_*_*.json')):
        r=json.loads(p.read_text());isf[r['method']].append(r)
    iq={}
    for mode,rows in isf.items():
        vals=[r['isf_fraction_of_instrumented_update'] for r in rows];calls=[sum(x['calls'] for x in r['isf'].values()) for r in rows]
        iq[mode]=dict(n=len(rows),equal=sum(r['comparison']['all_fields_equal'] for r in rows),fraction_median=statistics.median(vals),fraction_min=min(vals),fraction_max=max(vals),calls_median=statistics.median(calls),calls_min=min(calls),calls_max=max(calls))
    result={'qualification':'One oldest sample age per nonempty access, in samples from stop; not per-element or future bound. append_copy separately.',
         'history_verified':{m:{'pass':verified[m,True],'fail':verified[m,False]} for m in ('main','bank')},
         'observed_callers':{m:sorted(v) for m,v in observed.items()},'instrumented_method_calls':{m:dict(v) for m,v in call_counts.items()},'history_groups':groups,'isf':iq}
    with (OUT/'summary.json').open('x') as f:json.dump(result,f,indent=2,allow_nan=False);f.write('\n')
    lines=['# History access and selected ISF summaries','',result['qualification'],'', '| Mode | Noise | Scene | Kind | Field | n | median | q99 | max | max example seed / stop / hop / member / caller |','|---|---|---|---|---|---:|---:|---:|---:|---|']
    for g in groups:
        e=g['max_example'];lines.append(f"| {g['mode']} | {g['noise']} | {g['scene']} | {g['kind']} | {g['field']} | {g['count']} | {g['median']:.1f} | {g['q99']:.1f} | {g['max']} | {e['seed']} / {e['stop']} / {e['hop']:g} / {e['member']} / {e['caller']} |")
    (OUT/'summary.md').write_text('\n'.join(lines)+'\n')
    print(json.dumps({'verified':result['history_verified'],'calls':result['instrumented_method_calls'],'isf':iq},indent=2))
if __name__=='__main__':main()
