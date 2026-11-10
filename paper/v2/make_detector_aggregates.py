"""Descriptive aggregates requested in the review of 2026-11-07 (items S4 and S5).

Reads stored records only; no simulation is run and no stored file is changed.
  (a) Detector behaviour of PCG-WLS (stored name E-PCG) on the holdout runs of the main room:
      results/final_eval_holdout/det_events_{0,1}.jsonl, one record per (noise, scen, seed) with
      events = [[alarm hop boundary (sample), localized change point tau_hat (sample)], ...]
      (format written by experiments/revision9_holdout.py). The change is at 1 s = 8000 samples, H = 128.
  (b) Failure counts and medians over the successful runs in the secondary-path-mismatch cell R2 of rooms B and C
      (results/eval_room{B,C}_x2/metrics.jsonl), where failed runs (A1 = A2 = 0 dB) dominate several medians.
Outputs (new files only):
  results/detector_aggregates/{detector.json, detector.md, success_r2.json, success_r2.md, provenance.json}
  paper/v2/tables_detector/{detector.tex, success_r2.tex}
usage: python paper/v2/make_detector_aggregates.py [--results-dir DIR] [--tex-dir DIR]
  (the defaults overwrite the archived results/detector_aggregates; give other directories to compare instead)
"""
import argparse
import hashlib
import json
import platform
import subprocess
from collections import defaultdict
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'results' / 'detector_aggregates'
TEX = Path(__file__).resolve().parent / 'tables_detector'
FS, H, T_CHANGE = 8000, 128, 8000
SCEN_ORDER = ['S8 stationary', 'S1 src 10cm', 'S2 src 30cm', 'S5 src 30cm cont', 'S7 rd abrupt',
              'R1 rig 10cm', 'R2 rig 30cm', 'R3 rig 30cm cont']
SHORT = {s: s.split()[0] for s in SCEN_ORDER}
NOISE = {'ar1': 'AR(1)', 'harmonic': 'harmonic'}
ORDER = ['FD-FxNLMS', 'leaky FD-FxNLMS', 'convex FD-FxNLMS', 'FDKF', 'RLS', 'VFF-RLS', 'FD-FxNLMS + det',
         'FD-FxNLMS + restart', 'RLS + det', 'SFTF + det', 'SFTF-H + det', 'CFTF + det', 'RLS + CUSUM',
         'E-PCG bank', 'E-PCG']
DISPLAY = {'FD-FxNLMS': 'FD-FxNLMS', 'leaky FD-FxNLMS': 'leaky', 'convex FD-FxNLMS': 'convex', 'FDKF': 'FDKF',
           'RLS': 'RLS', 'VFF-RLS': 'VFF-RLS', 'FD-FxNLMS + det': 'FD-FxNLMS+det',
           'FD-FxNLMS + restart': 'FD-FxNLMS+restart', 'RLS + det': 'RLS+det', 'SFTF + det': 'SFTF+det',
           'SFTF-H + det': 'SFTF-H+det', 'CFTF + det': 'CFTF+det', 'RLS + CUSUM': 'RLS+CUSUM',
           'E-PCG bank': 'PCG-WLS (multi-window)', 'E-PCG': 'PCG-WLS'}
SOURCES = []


def read_jsonl(rel):
    SOURCES.append(rel)
    return [json.loads(line) for line in (ROOT / rel).read_text().splitlines() if line.strip()]


def fmt(v, nd=1):
    return '--' if v is None else f'{v:.{nd}f}'


def detector():
    recs = read_jsonl('results/final_eval_holdout/det_events_0.jsonl') + \
        read_jsonl('results/final_eval_holdout/det_events_1.jsonl')
    keys = [(r['noise'], r['scen'], r['seed']) for r in recs]
    assert len(keys) == len(set(keys)), 'duplicate event records'
    cells = defaultdict(list)
    for r in recs:
        cells[(r['noise'], r['scen'])].append(r)
    rows, total = [], {'runs': 0, 'pre_change_alarms': 0, 'runs_with_pre_change_alarm': 0}
    for noise in ('ar1', 'harmonic'):
        for scen in SCEN_ORDER:
            rs = cells.get((noise, scen))
            if not rs:
                continue
            assert len(rs) == 40, (noise, scen, len(rs))
            stationary = scen.startswith('S8')
            pre = [sum(1 for a, _ in r['events'] if a <= T_CHANGE) for r in rs] if not stationary else \
                [len(r['events']) for r in rs]
            post = [[(a, t) for a, t in r['events'] if a > T_CHANGE] for r in rs] if not stationary else [[] for _ in rs]
            first = [e[0] for e in post if e]
            delay = [(a - T_CHANGE) / H for a, _ in first]
            tau_err = [t - T_CHANGE for _, t in first]
            row = {'noise': noise, 'scen': scen, 'runs': len(rs),
                   'alarms_before_change' if not stationary else 'alarms_stationary': int(sum(pre)),
                   'runs_without_alarm_after_change': None if stationary else int(sum(1 for e in post if not e)),
                   'runs_with_two_or_more_alarms_after_change': None if stationary else int(sum(1 for e in post if len(e) >= 2)),
                   'first_alarm_delay_hops_median': float(np.median(delay)) if delay else None,
                   'first_alarm_delay_hops_max': float(np.max(delay)) if delay else None,
                   'tau_hat_error_samples_median': float(np.median(tau_err)) if tau_err else None,
                   'tau_hat_error_samples_max_abs': float(np.max(np.abs(tau_err))) if tau_err else None}
            rows.append(row)
            total['runs'] += len(rs)
            if not stationary:
                total['pre_change_alarms'] += int(sum(pre))
                total['runs_with_pre_change_alarm'] += int(sum(1 for p in pre if p))
    stat = [r for r in rows if r['scen'].startswith('S8')]
    chg = [r for r in rows if not r['scen'].startswith('S8')]
    total.update({
        'stationary_runs': sum(r['runs'] for r in stat),
        'stationary_alarms': sum(r['alarms_stationary'] for r in stat),
        'change_runs': sum(r['runs'] for r in chg),
        'change_runs_without_alarm_after_change': sum(r['runs_without_alarm_after_change'] for r in chg),
        'hops_per_run': 312, 'pre_change_hops_per_run': T_CHANGE // H})
    return rows, total


def detector_tex(rows, total):
    idx = {(r['noise'], r['scen']): r for r in rows}
    lines = [r'% Generated by make_detector_aggregates.py from results/final_eval_holdout/det_events_{0,1}.jsonl; do not edit.',
             r'\begin{table}[t]\centering\caption{Detector of PCG-WLS on the holdout runs (40 per cell). Delay of the first alarm after the change in hops (median, maximum; 1 hop = 16 ms, to the end of the alarm hop), runs without an alarm, and median localization error $\hat\tau-\tau$ (samples).}\label{tab:detector}',
             r'\scriptsize\setlength{\tabcolsep}{2.5pt}',
             r'\begin{tabular}{lrrrrrrrr}\toprule',
             r' & \multicolumn{4}{c}{AR(1)} & \multicolumn{4}{c}{harmonic} \\\cmidrule(lr){2-5}\cmidrule(lr){6-9}',
             r'cell & med. & max & none & $\hat\tau-\tau$ & med. & max & none & $\hat\tau-\tau$ \\\midrule']
    for scen in SCEN_ORDER:
        if scen.startswith('S8'):
            continue
        cells = []
        for noise in ('ar1', 'harmonic'):
            r = idx.get((noise, scen))
            cells += ['--'] * 4 if r is None else [fmt(r['first_alarm_delay_hops_median']), fmt(r['first_alarm_delay_hops_max']),
                                                   str(r['runs_without_alarm_after_change']), fmt(r['tau_hat_error_samples_median'], 0)]
        lines.append(SHORT[scen] + ' & ' + ' & '.join(cells) + r' \\')
    lines += [r'\bottomrule\end{tabular}\\[2pt]',
              r'{\scriptsize No alarm before the change (' + str(total['change_runs']) + r' runs) or in S8 ('
              + str(total['stationary_alarms']) + ' alarms in ' + str(total['stationary_runs']) + r' runs). S5, R3: moves over 0.6 s, delay from their start.}',
              r'\end{table}']
    return '\n'.join(lines) + '\n'


def success_r2():
    out = []
    for room, d in (('B', 'eval_roomB_x2'), ('C', 'eval_roomC_x2')):
        g = defaultdict(list)
        for r in read_jsonl(f'results/{d}/metrics.jsonl'):
            if r['scen'] == 'R2 rig 30cm':
                g[(r['noise'], r['method'])].append(r)
        for noise in ('ar1', 'harmonic'):
            for m in ORDER:
                rs = g.get((noise, m))
                if not rs:
                    continue
                ok = [r for r in rs if not r['fail']]
                out.append({'room': room, 'noise': noise, 'method': m, 'runs': len(rs), 'failures': len(rs) - len(ok),
                            'A1_median_all': float(np.median([r['A1'] for r in rs])),
                            'A1_median_successful': float(np.median([r['A1'] for r in ok])) if ok else None,
                            'A2_median_successful': float(np.median([r['A2'] for r in ok])) if ok else None})
    return out


def success_tex(rows):
    groups = [('B', 'ar1'), ('B', 'harmonic'), ('C', 'ar1'), ('C', 'harmonic')]
    idx = {(r['room'], r['noise'], r['method']): r for r in rows}
    head = ' & '.join(r'\multicolumn{3}{c}{room ' + rm + ', ' + NOISE[nz] + '}' for rm, nz in groups)
    rules = ''.join(r'\cmidrule(lr){' + f'{2 + 3 * i}-{4 + 3 * i}' + '}' for i in range(4))
    lines = [r'% Generated by make_detector_aggregates.py from results/eval_room{B,C}_x2/metrics.jsonl; do not edit.',
             r'\begin{table*}[t]\centering\caption{Control-unit move R2 in rooms B and C (evaluation seeds 480--519): failed runs of 40 and medians over the successful runs only (dB). Descriptive; the medians exclude the failed runs and are not comparable across methods with different failure counts.}\label{tab:success-r2}',
             r'\scriptsize\setlength{\tabcolsep}{3pt}',
             r'\begin{tabular}{l' + 'rrr' * 4 + r'}\toprule',
             'method & ' + head + r' \\', rules,
             ' & ' + ' & '.join(['fail & A1 & A2'] * 4) + r' \\\midrule']
    for m in ORDER:
        cells = []
        for rm, nz in groups:
            r = idx.get((rm, nz, m))
            cells += ['--'] * 3 if r is None else [str(r['failures']), fmt(r['A1_median_successful']), fmt(r['A2_median_successful'])]
        if all(c == '--' for c in cells):
            continue
        lines.append(DISPLAY[m] + ' & ' + ' & '.join(cells) + r' \\')
    lines += [r'\bottomrule\end{tabular}', r'\end{table*}']
    return '\n'.join(lines) + '\n'


def md_table(rows, keys):
    s = '| ' + ' | '.join(keys) + ' |\n|' + '---|' * len(keys) + '\n'
    for r in rows:
        s += '| ' + ' | '.join('' if r[k] is None else (f'{r[k]:.2f}' if isinstance(r[k], float) else str(r[k])) for k in keys) + ' |\n'
    return s


def main():
    global OUT, TEX
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--results-dir', type=Path, default=OUT)
    parser.add_argument('--tex-dir', type=Path, default=TEX)
    args = parser.parse_args()
    OUT, TEX = args.results_dir, args.tex_dir
    OUT.mkdir(parents=True, exist_ok=True); TEX.mkdir(parents=True, exist_ok=True)
    det_rows, det_total = detector()
    (OUT / 'detector.json').write_text(json.dumps({'rows': det_rows, 'total': det_total}, indent=1) + '\n')
    keys = ['noise', 'scen', 'runs', 'alarms_before_change', 'alarms_stationary', 'runs_without_alarm_after_change',
            'runs_with_two_or_more_alarms_after_change', 'first_alarm_delay_hops_median', 'first_alarm_delay_hops_max',
            'tau_hat_error_samples_median', 'tau_hat_error_samples_max_abs']
    (OUT / 'detector.md').write_text('# PCG-WLS (E-PCG) detector on holdout seeds 800-839 (descriptive; stored events only)\n\n'
                                     + md_table([{k: r.get(k) for k in keys} for r in det_rows], keys)
                                     + '\nTotals: ' + json.dumps(det_total) + '\n')
    (TEX / 'detector.tex').write_text(detector_tex(det_rows, det_total))
    sr = success_r2()
    (OUT / 'success_r2.json').write_text(json.dumps(sr, indent=1) + '\n')
    (OUT / 'success_r2.md').write_text('# R2 in rooms B and C: failures and medians over successful runs (descriptive)\n\n'
                                       + md_table(sr, list(sr[0])))
    (TEX / 'success_r2.tex').write_text(success_tex(sr))
    commit = subprocess.run(['git', 'rev-parse', 'HEAD'], cwd=ROOT, capture_output=True, text=True).stdout.strip()
    prov = {'script': 'paper/v2/make_detector_aggregates.py', 'commit': commit, 'python': platform.python_version(),
            'numpy': np.__version__,
            'inputs_sha256': {p: hashlib.sha256((ROOT / p).read_bytes()).hexdigest() for p in sorted(set(SOURCES))}}
    (OUT / 'provenance.json').write_text(json.dumps(prov, indent=1) + '\n')
    print('written', OUT, TEX)


if __name__ == '__main__':
    main()
