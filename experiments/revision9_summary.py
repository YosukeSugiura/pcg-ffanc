"""Summarize the registered revision 9 holdout and compare v2e labels."""
import json
import sys
from pathlib import Path
import numpy as np
import eval_v2 as ev
import final_eval as fe
from revision9_holdout import ROOT, OUT, METHODS, SEEDS

BASE=list(ev.GRID)
PROPOSALS=['E-PCG','E-PCG bank']

def metrics(path):
    rows=[json.loads(line) for line in path.read_text().splitlines()]
    by={(r['method'],r['noise'],r['scen'],r['seed']):r for r in rows}
    if len(by)!=len(rows): raise ValueError(f'duplicate metrics in {path}')
    return by

def comparisons(by,seeds):
    result={}
    for prop in PROPOSALS:
        rows=[]
        for baseline in BASE:
            for nz,sc in ev.COMBOS15:
                stats=[]
                for metric in ('A1','A2'):
                    d=np.array([by[(prop,nz,sc,sd)][metric]-by[(baseline,nz,sc,sd)][metric] for sd in seeds])
                    stats.append((float(np.median(d)),fe.pval(d)))
                fails=tuple(sum(by[(m,nz,sc,sd)]['fail'] for sd in seeds) for m in (prop,baseline))
                rows.append((baseline,nz,sc,stats,fails))
        adjusted=iter(fe.holm([p for _,_,_,v,_ in rows for _,p in v]))
        for baseline,nz,sc,v,fails in rows:
            p1,p2=next(adjusted),next(adjusted)
            result[(prop,baseline,nz,sc)]=dict(label=fe.label(v[0][0],p1,v[1][0],p2),
                A1=v[0][0],A2=v[1][0],p1=float(p1),p2=float(p2),fail=fails)
    return result

def report_labels():
    old=comparisons(metrics(ROOT/'results/final_eval_v2e/metrics.jsonl'),range(480,520))
    new=comparisons(metrics(OUT/'metrics.jsonl'),SEEDS)
    if old.keys()!=new.keys() or len(old)!=360: raise ValueError('unexpected comparison keys')
    saved={}; prop=None
    for line in (ROOT/'results/final_eval_v2e/summary.md').read_text().splitlines():
        if line.startswith('## E-PCG vs baselines '): prop='E-PCG'; continue
        if line.startswith('## E-PCG bank vs baselines '): prop='E-PCG bank'; continue
        if line.startswith('## '): prop=None
        if prop and line.startswith('|'):
            cols=[x.strip() for x in line.strip('|').split('|')]
            if len(cols)==8 and cols[0] in BASE:
                saved[(prop,cols[0],cols[1],cols[2])]=cols[7]
    if set(saved)!=set(old) or any(saved[k]!=old[k]['label'] for k in old):
        raise ValueError('v2e recalculated labels differ from the saved labels')
    matched=sum(old[k]['label']==new[k]['label'] for k in old)
    lines=['# v2e versus holdout: like-for-like 360-test families', '',
           f'Agreement: {matched}/360 ({100*matched/360:.2f}%).', '',
           '| proposal | baseline | noise | cell | v2e label | holdout label | v2e dA1 / p / dA2 / p | holdout dA1 / p / dA2 / p | failures v2e proposal/baseline | failures holdout proposal/baseline |',
           '|---|---|---|---|---|---|---|---|---|---|']
    for k in old:
        a,b=old[k],new[k]
        if a['label']==b['label']: continue
        vals=lambda x:f"{x['A1']:+.4f} / {x['p1']:.6g} / {x['A2']:+.4f} / {x['p2']:.6g}"
        lines.append('| '+' | '.join(map(str,k))+f" | {a['label']} | {b['label']} | {vals(a)} | {vals(b)} | {a['fail'][0]}/{a['fail'][1]} | {b['fail'][0]}/{b['fail'][1]} |")
    (OUT/'label_comparison.md').write_text('\n'.join(lines)+'\n')
    (OUT/'label_comparison.json').write_text(json.dumps({'agreement':matched,'total':360,'v2e':{'|'.join(k):v for k,v in old.items()},'holdout':{'|'.join(k):v for k,v in new.items()}},indent=2)+'\n')

def report_cusum():
    by=metrics(OUT/'metrics.jsonl')
    q=lambda x:f'{np.median(x):.3f} ({np.quantile(x,.25):.3f}, {np.quantile(x,.75):.3f})'
    rows=[]; gaps=[]
    for nz,sc in ev.COMBOS15:
        cus=[by[('RLS + CUSUM',nz,sc,sd)] for sd in SEEDS]
        det=[by[('RLS + det',nz,sc,sd)] for sd in SEEDS]
        d1=float(np.median([a['A1']-b['A1'] for a,b in zip(cus,det)]))
        d2=float(np.median([a['A2']-b['A2'] for a,b in zip(cus,det)]))
        gaps.append(abs(d1))
        rows.append(f"| {nz} | {sc} | {q([v['A1'] for v in cus])} | {q([v['A2'] for v in cus])} | {d1:+.3f} | {abs(d1):.3f} | {d2:+.3f} | {sum(v['fail'] for v in cus)}/{sum(v['fail'] for v in det)} |")
    lines=['# RLS + CUSUM versus RLS + det', '',
           f'Absolute A1 paired-median gaps range {min(gaps):.3f}–{max(gaps):.3f} dB; descriptive only.', '',
           '| noise | cell | CUSUM A1 median (Q1,Q3) | CUSUM A2 median (Q1,Q3) | paired dA1 | abs dA1 | paired dA2 | failures CUSUM/det |',
           '|---|---|---|---|---|---|---|---|']+rows
    txt='\n'.join(lines)+'\n'; (OUT/'cusum_comparison.md').write_text(txt)
    p=OUT/'summary.md';p.write_text(p.read_text()+'\n'+txt)

def summary(include_cusum):
    methods=dict(METHODS); base=list(BASE)
    if include_cusum:
        data=json.loads((ROOT/'results/protocol_v2_sel_cusum/selected.json').read_text())
        methods['RLS + CUSUM']=('R-RLS',data['params']); base.append('RLS + CUSUM')
    expected={(m,nz,sc,sd) for m in methods for nz,sc in ev.COMBOS15 for sd in SEEDS}
    seen=set()
    for path in sorted(OUT.glob('runs*.jsonl')):
        for line in path.read_text().splitlines():
            r=json.loads(line); key=(r['method'],r['noise'],r['scen'],r['seed'])
            if key not in expected or key in seen or r['prm'] != methods[r['method']][1]: raise ValueError(f'unexpected/duplicate/stale {key}')
            seen.add(key)
    if seen!=expected: raise ValueError(f'incomplete holdout: {len(seen)}/{len(expected)}')
    fe.OUT=OUT; fe.METH=methods; fe.BASE=base; fe.ALL=base+PROPOSALS; fe.PROP=PROPOSALS
    fe.COMBOS=ev.COMBOS15; fe.SEEDS=list(SEEDS)
    fe.summary()
    p=OUT/'summary.md'; txt=p.read_text().replace('evaluation seeds 480-519','evaluation seeds 800-839',1)
    p.write_text(txt)
    if not include_cusum:
        (OUT/'summary_360.md').write_text(txt)
    report_labels()
    if include_cusum:
        report_cusum()

if __name__=='__main__':
    if len(sys.argv)!=2 or sys.argv[1] not in ('360','390'): raise ValueError('choose 360 or 390')
    summary(sys.argv[1]=='390')
