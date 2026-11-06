"""Generate manuscript quantities from the archived Revision 9 summaries, without new experiments."""
import collections
import json
import math
import re
import numpy as np
from pathlib import Path
from make_tables import ROOT, OUT, MAIN_DIR, load, wins, REC, REC_MW   # record labels of PCG-WLS / multi-window

R = ROOT / 'results'
def macro(name, value):
    return r'\newcommand{\Rnine' + name + '}{' + str(value) + '}\n'

def label_counts(dataset):
    return collections.Counter(wins(dataset).values())

def summary_rows(dataset, proposal=REC):
    out=[]; active=False
    for line in (R / dataset / 'summary.md').read_text().splitlines():
        if line.startswith('## '): active=line.startswith(f'## {proposal} vs baselines')
        elif active and line.startswith('| ') and not line.startswith('| baseline'):
            cells=[c.strip() for c in line.strip('|').split('|')]
            if len(cells)==8: out.append(cells)
    return out

def generate():
    hold=load(MAIN_DIR); holdwins=wins(MAIN_DIR); h=label_counts(MAIN_DIR)
    keys=[r for r in summary_rows(MAIN_DIR) if r[0]=='RLS + det']
    ms=label_counts('final_eval_meas_s_8a')
    roomB=label_counts('eval_roomB_x2');roomC=label_counts('eval_roomC_x2'); snr=label_counts('eval_snr10_x2')
    c=collections.Counter(v for (m,n,z),v in holdwins.items() if m=='RLS + CUSUM')
    sel=json.loads((R/'final_eval_holdout/label_comparison.json').read_text())
    s7=next(float(r[3]) for r in keys if r[1]=='ar1' and r[2].startswith('S7 '))
    arwin=sum(r[-1]=='win' and r[1]=='ar1' for r in keys)
    hm=[float(r[3]) for r in keys if r[1]=='harmonic']
    a2=[float(r[5]) for r in keys]
    cvals=[]
    for line in (R/MAIN_DIR/'cusum_comparison.md').read_text().splitlines():
        if line.startswith('| harmonic |') and 'S8 stationary' not in line:
            cvals.append(float(line.split('|')[5]))
    measured=summary_rows('final_eval_meas_s_8a')
    ml=[float(r[3]) for r in measured if r[1]=='harmonic' and r[0] in ('RLS + det','SFTF + det','SFTF-H + det','CFTF + det') and r[-1]=='loss']
    assert len(keys)==15 and len(ml)==4 and len(cvals)==6
    selection=(R/'protocol_v2_sel_cusum/selection.md').read_text()
    index=int(re.search(r'Selected (\d+):', selection).group(1))
    provenance=json.loads((R/'protocol_v2_sel_cusum/provenance.json').read_text())
    grid=provenance['grid']
    floor=re.search(r'max\(mean\(eps_t\*\*2 over the H=\d+ NEW samples in hop j\), (1e[-+]\d+)\)',provenance['rule_full_text'])
    assert floor, 'CUSUM log floor not found in archived rule'
    floor_exp=int(floor.group(1).split('e')[1])
    selected=grid[index]
    cold=(R/'revision3_diag/s7_cold.md').read_text()
    oldwarm=float(re.search(r'warm, selected\): A1 median paired ([+-]?[0-9.]+)',cold).group(1))
    oldcold=float(re.search(r'cold, cfg 0\): A1 median paired ([+-]?[0-9.]+)',cold).group(1))
    wiener=json.loads((R/'revision8a_diag/per_seed.json').read_text())['seeds']
    def ref(scenario,noise):
        return f"{np.median([x['scenarios'][scenario]['after']['noise'][noise]['true_s_causal_wiener_bound']['total_nr_db'] for x in wiener]):.1f}"
    mix=next(r for r in measured if r[0]=='convex FD-FxNLMS' and r[1]=='ar1' and r[-1]=='mixed')
    def failures(dataset,method,noise,cell):
        m=load(dataset)
        rs=next(rs for (name,n,scenario),rs in m.items() if name==method and n==noise and scenario.startswith(cell+' '))
        return sum(r['fail'] for r in rs)
    room_rls=[(k,v) for k,v in wins('eval_roomB_x2').items() if k[0]=='RLS + det']
    room_c_rls=[(k,v) for k,v in wins('eval_roomC_x2').items() if k[0]=='RLS + det']
    assert (len(room_rls),sum(v=='loss' for _,v in room_rls)) == (len(room_c_rls),sum(v=='loss' for _,v in room_c_rls)), 'Room B and C RLS loss counts differ'
    seed=sorted({r['seed'] for rs in hold.values() for r in rs})
    previous=sorted({r['seed'] for rs in load('eval_roomB_x2').values() for r in rs})
    values={
        'SeedFirst':seed[0], 'SeedLast':seed[-1], 'PreviousSeedFirst':previous[0], 'PreviousSeedLast':previous[-1], 'HoldWins':h['win'], 'HoldPairs':len(holdwins), 'HoldLoss':h['loss'], 'HoldNone':h['-'], 'HoldTests':2*len(holdwins),
        'HoldBaselines':len({k[0] for k in holdwins}), 'RlsWins':arwin, 'RlsArCells':sum(r[1]=='ar1' for r in keys),
        'SsevenGap':f'{abs(s7):.1f}', 'HarmAoneMin':f'{min(hm):+.2f}', 'HarmAoneMax':f'{max(hm):+.2f}',
        'RlsAtwoMin':f'{min(a2):.2f}', 'RlsAtwoMax':f'{max(a2):.2f}',
        'CusumWins':c['win'], 'CusumNone':c['-'], 'CusumMin':f'{min(cvals):.2f}', 'CusumMax':f'{max(cvals):.2f}',
        'Agreement':sel['agreement'], 'AgreementTotal':sel['total'], 'AgreementPercent':f'{100*sel["agreement"]/sel["total"]:.1f}',
        'RoomBWins':roomB['win'], 'RoomBLoss':roomB['loss'], 'RoomBNone':roomB['-'],
        'RoomCWins':roomC['win'], 'RoomCLoss':roomC['loss'], 'RoomCNone':roomC['-'],
        'SnrWins':snr['win'], 'SnrLoss':snr['loss'], 'SnrNone':snr['-'],
        'MsWins':ms['win'], 'MsLoss':ms['loss'], 'MsMixed':ms['mixed'], 'MsNone':ms['-'],
        'MsLossMin':f'{min(ml):.2f}', 'MsLossMax':f'{max(ml):.2f}',
        'HarmAoneBound':f'{math.ceil(max(abs(x) for x in hm)*10)/10:.1f}',
        'CusumH':selected['cusum_h'], 'CusumK':selected['cusum_k'], 'CusumFloor':f'10^{{{floor_exp}}}',
        'CusumGridHs':','.join(map(str,sorted({r['cusum_h'] for r in grid}))),
        'CusumGridKs':','.join(map(str,sorted({r['cusum_k'] for r in grid}))),
        'PreviousWarmGap':f'{abs(oldwarm):.1f}', 'PreviousColdGap':f'{abs(oldcold):.1f}',
        'MsPairs':sum(ms.values()), 'MsLossApprox':f'{min(ml):.1f}',
        'RoomLossCells':sum(v=='loss' for k,v in room_rls), 'RoomCells':len(room_rls),
        'MPWienerAr':ref('meas_p','ar1'), 'MPWienerHarm':ref('meas_p','harmonic'),
        'MPSWienerAr':ref('meas_ps','ar1'), 'MPSWienerHarm':ref('meas_ps','harmonic'),
        'MixedAone':mix[3], 'MixedAtwo':mix[5],
        'RoomCBankSzero':failures('eval_roomC_x2',REC_MW,'harmonic','S8'),
        'RoomCBankStwo':failures('eval_roomC_x2',REC_MW,'harmonic','S2'),
        'RoomCBankSfive':failures('eval_roomC_x2',REC_MW,'harmonic','S5'),
        'RoomBEharmRtwo':failures('eval_roomB_x2',REC,'harmonic','R2'),
        'RoomBRlsharmRtwo':failures('eval_roomB_x2','RLS + det','harmonic','R2'),
        'RoomCEarRtwo':failures('eval_roomC_x2',REC,'ar1','R2'),
        'RoomCRlsarRtwo':failures('eval_roomC_x2','RLS + det','ar1','R2'),
        'HoldCftfFailures':sum(r['fail'] for k,rs in hold.items() if k[0]=='CFTF + det' for r in rs),
        'HoldCftfRuns':sum(len(rs) for k,rs in hold.items() if k[0]=='CFTF + det'),
        'VtwoCftfFailures':sum(r['fail'] for k,rs in load('final_eval_v2e').items() if k[0]=='CFTF + det' for r in rs),
        'VtwoCftfRuns':sum(len(rs) for k,rs in load('final_eval_v2e').items() if k[0]=='CFTF + det'),
    }
    out='% Generated from results summaries by make_r9_values.py; do not edit.\n'
    out += '% Sources: final_eval_holdout, eval_{roomB,roomC,snr10}_x2, final_eval_meas_s_8a, protocol_v2_sel_cusum, revision3_diag and revision8a_diag.\n'
    out += ''.join(macro(k,v) for k,v in values.items())
    (OUT/'r9_values.tex').write_text(out)
    print('generated',len(values),'quantities')
if __name__=='__main__': generate()
