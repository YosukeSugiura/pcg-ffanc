"""Performance-stability trade-off (2026-10-26): each method's main parameter swept, M = 512 for every method.
Per point and run (evaluation seeds 480-519, both references): stationary S8 (whole-run NR and steady-state tail) and
the microphone-movement cells S3 / S4 / S6 / S11 (divergence = the simulator's abort; time to divergence after the
change; post-change NR of the stable runs). Descriptive sweep (no selection), so the evaluation seeds are used.
usage: PART=_a METHODS='RLS;FD-FxNLMS' python experiments/sweep_tradeoff.py run ; python experiments/sweep_tradeoff.py summary
"""
import json, os, sys
from pathlib import Path
import numpy as np
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src')); sys.path.insert(0, str(ROOT / 'experiments'))
import verify_protocol_defs as D  # noqa: E402

D.SCEN.setdefault('S11 mic 10cm slow', dict(D.SCEN['S6 mic 10cm cont'], move_seconds=1.2, move_steps=32))
OUT = ROOT / 'results' / 'tradeoff'; OUT.mkdir(parents=True, exist_ok=True)
SEEDS = range(480, 520)
CELLS = ['S8 stationary', 'S3 mic 5cm', 'S4 mic 10cm', 'S6 mic 10cm cont', 'S11 mic 10cm slow']
M = 512
sel = json.loads((ROOT / 'results/protocol/selected_design.json').read_text())
L = D.GRID['E-PCG v2 light'][1][sel['E-PCG v2 light']]
v65 = json.loads((ROOT / 'results/final_dev/final_config_v6_5.json').read_text())['flags']
SWEEP = {
    'FD-FxNLMS': ('fixed_binwise', 'mu', [{'mu': m} for m in (0.02, 0.05, 0.1, 0.2, 0.35, 0.5, 0.8, 1.0)]),
    'leaky FD-FxNLMS': ('leaky_binwise', 'leak', [{'mu': 0.35, 'leak': lk} for lk in (1e-3, 3e-3, 1e-2, 3e-2, 0.1, 0.3)]),
    'convex FD-FxNLMS': ('convex_binwise', 'scale', [{'mu_fast': 1.0 * s, 'mu_slow': 0.35 * s, 'mu_a': 1.0} for s in (0.1, 0.25, 0.5, 1.0)]),
    'FDKF': ('C-FDKF', 'A', [{'P0': 1.0, 'gain_scale': 1.0, 'A': a} for a in (0.99, 0.995, 0.998, 0.999, 0.9995)]),
    'RLS': ('R-RLS', 'lam', [{'lam': lm, 'delta': 1e-2} for lm in (0.998, 0.999, 0.9995, 0.9998, 0.9999, 0.99995, 1.0)]),
    'VFF-RLS': ('R-VFF', 'lam_min', [{'N0': 8000.0, 'lam_min': lm, 'delta': 1e-3} for lm in (0.95, 0.98, 0.99, 0.995, 0.999)]),
    'E-PCG-M v6.5': ('PCG-WLS-F', 'D', [dict(L, **dict(v65, robust_bound_dx=dx)) for dx in (0.025, 0.05, 0.1, 0.15)]),   # D < rs (~0.2-0.3 m) required by shat_shift
    'E-PCG-M v6.5 (level)': ('PCG-WLS-F', 'fa', [dict(L, **dict(v65, det_fa=fa, sid_consist=fa)) for fa in (1e-4, 1e-10)]),
}
LABEL = {'scale': lambda p: f"x{p['mu_fast']:g}", 'D': lambda p: f"D={p['robust_bound_dx']:g}",
         'fa': lambda p: f"level={p['det_fa']:g}"}


def run():
    sel_m = os.environ.get('METHODS')
    fn = OUT / f"runs{os.environ.get('PART', '')}.jsonl"
    done = set()
    for f in OUT.glob('runs*.jsonl'):
        for l in f.read_text().splitlines():
            r = json.loads(l); done.add((r['method'], r['pt'], r['noise'], r['scen'], r['seed']))
    with fn.open('a') as fh:
        for m, (meth, key, pts) in SWEEP.items():
            if sel_m and m not in sel_m.split(';'):
                continue
            for i, prm in enumerate(pts):
                if os.environ.get('PTS') and str(i) not in os.environ['PTS'].split(';'):
                    continue
                for nz in ('ar1', 'harmonic'):
                    for sc in CELLS:
                        for sd in SEEDS:
                            if (m, i, nz, sc, sd) in done:
                                continue
                            cfg = dict(D.SCEN[sc], controller_length=M, fft_length=2 * M, **({} if nz == 'ar1' else {'noise_type': nz}))
                            ch = not sc.startswith('S8')
                            r = D.P.run(cfg, sd, meth, prm, D.T, D.CH if ch else None)
                            tp = np.array(r['total_power']); up = np.array(r['uncontrolled_power'])
                            H = int(cfg['hop_length']); fs = int(cfg['sample_rate']); hc = int(D.CH * fs) // H
                            nh = int(D.T * fs) // H
                            ok = bool(r['stable'] and len(tp) == nh)
                            o = {'method': m, 'pt': i, 'noise': nz, 'scen': sc, 'seed': sd, 'stable': ok,
                                 'hops': int(len(tp)), 't_div': None if ok else float((len(tp) - (hc if ch else 0)) * H / fs)}
                            if ok:
                                a_ = hc if ch else 0
                                o['nr'] = float(10 * np.log10(tp[a_:].sum() / up[a_:].sum()))
                                o['tail'] = float(10 * np.log10(tp[-nh // 5:].sum() / up[-nh // 5:].sum()))
                            if not ok:                    # first hop over the +30 dB residual limit (classify_diagnostic_run), else the abort
                                hd = 10 * np.log10((tp + 1e-300) / up[:len(tp)]); k = np.flatnonzero(hd > 30.0)
                                o['t_div30'] = float(((k[0] if k.size else len(tp)) - (hc if ch else 0)) * H / fs)
                            fh.write(json.dumps(o) + '\n'); fh.flush()
                print(m, key, i, 'done', flush=True)


def fixdiv():
    """Runs written before t_div30 existed: re-run the diverged ones (deterministic) and store their first +30 dB hop."""
    fn = OUT / 'tdiv.jsonl'; have = set()
    if fn.exists():
        have = {tuple(json.loads(l)['key']) for l in fn.read_text().splitlines()}
    R = [json.loads(l) for f in sorted(OUT.glob('runs*.jsonl')) for l in f.read_text().splitlines()]
    todo = [r for r in R if not r['stable'] and 't_div30' not in r
            and (r['method'], r['pt'], r['noise'], r['scen'], r['seed']) not in have]
    if os.environ.get('METHODS'):
        todo = [r for r in todo if r['method'] in os.environ['METHODS'].split(';')]
    with fn.open('a') as fh:
        for r in todo:
            meth, key, pts = SWEEP[r['method']]; sc = r['scen']; ch = not sc.startswith('S8')
            cfg = dict(D.SCEN[sc], controller_length=M, fft_length=2 * M, **({} if r['noise'] == 'ar1' else {'noise_type': r['noise']}))
            q = D.P.run(cfg, r['seed'], meth, pts[r['pt']], D.T, D.CH if ch else None)
            tp = np.array(q['total_power']); up = np.array(q['uncontrolled_power'])
            H = int(cfg['hop_length']); fs = int(cfg['sample_rate']); hc = int(D.CH * fs) // H
            hd = 10 * np.log10((tp + 1e-300) / up[:len(tp)]); k = np.flatnonzero(hd > 30.0)
            fh.write(json.dumps({'key': [r['method'], r['pt'], r['noise'], sc, r['seed']], 'stable': bool(q['stable']),
                                 't_div30': float(((k[0] if k.size else len(tp)) - (hc if ch else 0)) * H / fs)}) + '\n'); fh.flush()


def points():
    """One row per (method, point, noise) with complete runs. S8 NR: mean per-run dB, a diverged run counted as 0 dB."""
    R, seen = [], set()
    for f in sorted(OUT.glob('runs*.jsonl')):
        for l in f.read_text().splitlines():
            r = json.loads(l); k = (r['method'], r['pt'], r['noise'], r['scen'], r['seed'])
            if k not in seen:
                seen.add(k); R.append(r)
    if (OUT / 'tdiv.jsonl').exists():
        T30 = {tuple(json.loads(l)['key']): json.loads(l)['t_div30'] for l in (OUT / 'tdiv.jsonl').read_text().splitlines()}
        for r in R:
            k = (r['method'], r['pt'], r['noise'], r['scen'], r['seed'])
            if not r['stable'] and 't_div30' not in r and k in T30:
                r['t_div30'] = T30[k]
    rows = []
    for nz in ('ar1', 'harmonic'):
        for m, (meth, key, pts) in SWEEP.items():
            for i, prm in enumerate(pts):
                rs = [r for r in R if r['method'] == m and r['pt'] == i and r['noise'] == nz]
                s8 = [r for r in rs if r['scen'].startswith('S8')]; mv = [r for r in rs if not r['scen'].startswith('S8')]
                if len(s8) < len(SEEDS) or len(mv) < 4 * len(SEEDS):
                    continue
                td = [r['t_div30'] for r in mv if not r['stable'] and 't_div30' in r]
                rows.append(dict(noise=nz, method=m, pt=i, label=LABEL[key](prm) if key in LABEL else f"{key}={prm[key]:g}",
                                 s8=float(np.mean([r['nr'] if r['stable'] else 0.0 for r in s8])),
                                 s8tail=float(np.mean([r['tail'] if r['stable'] else 0.0 for r in s8])),
                                 s8div=sum(not r['stable'] for r in s8), mvdiv=len(td), nmv=len(mv),
                                 tdiv=float(np.median(td)) if td and len(td) == sum(not r['stable'] for r in mv) else None,
                                 mvnr=float(np.mean([r['nr'] if r['stable'] else 0.0 for r in mv]))))
    return rows


def summary():
    rows = points(); out = []
    f2 = lambda v: '' if v is None else f'{v:.2f}'
    for nz in ('ar1', 'harmonic'):
        rn = [r for r in rows if r['noise'] == nz]
        out.append(f'\n### {nz} (M = 512, seeds 480-519; diverged run = 0 dB)')
        out.append('| method | parameter | S8 whole NR (dB) | S8 tail NR | S8 diverged /40 | moves diverged /160 | rate | median time to divergence after the move (s) | moves post-change NR |')
        out.append('|---|---|---|---|---|---|---|---|---|')
        for r in rn:
            out.append(f"| {r['method']} | {r['label']} | {r['s8']:.2f} | {r['s8tail']:.2f} | {r['s8div']} | {r['mvdiv']} | "
                       f"{100 * r['mvdiv'] / r['nmv']:.0f}% | {f2(r['tdiv'])} | {r['mvnr']:.2f} |")
        # matched-NR slice: per method, the lowest move-divergence rate among its points reaching the S8 NR level
        lv = sorted({round(r['s8'], 0) for r in rn})
        lv = [x for x in np.arange(min(lv), max(lv) + 1, 2.0)] if lv else []
        ms = list(dict.fromkeys(r['method'] for r in rn))
        out.append(f'\n#### {nz}: lowest move-divergence rate among the points with S8 whole NR <= level')
        out.append('| S8 NR level (dB) | ' + ' | '.join(ms) + ' |'); out.append('|---' * (len(ms) + 1) + '|')
        for x in lv:
            cell = []
            for m in ms:
                c = [r for r in rn if r['method'] == m and r['s8'] <= x + 1e-9]
                cell.append(f"{100 * min(r['mvdiv'] / r['nmv'] for r in c):.0f}%" if c else '—')
            out.append(f'| {x:.0f} | ' + ' | '.join(cell) + ' |')
    txt = '\n'.join(out); print(txt); (OUT / 'summary.md').write_text(txt + '\n')
    (OUT / 'points.json').write_text(json.dumps(rows, indent=1))


def plot():
    import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
    rows = points(); ms = list(SWEEP)
    fig, ax = plt.subplots(1, 2, figsize=(11, 4.2), sharey=True)
    for a, nz in zip(ax, ('ar1', 'harmonic')):
        for j, m in enumerate(ms):
            rr = sorted([r for r in rows if r['noise'] == nz and r['method'] == m], key=lambda r: r['pt'])
            if rr:
                a.plot([r['s8'] for r in rr], [100 * r['mvdiv'] / r['nmv'] for r in rr], 'o-' if 'E-PCG' not in m else 's-',
                       label=m, color=f'C{j}', lw=2.2 if 'E-PCG' in m else 1.2, ms=4)
        a.set_title(f'{nz} reference, M = 512'); a.set_xlabel('stationary S8: whole-run NR (dB, lower = better)')
        a.grid(alpha=.3); a.invert_xaxis()
    ax[0].set_ylabel('mic-move cells: diverged runs (%)'); ax[1].legend(fontsize=7, loc='upper left')
    fig.tight_layout(); fig.savefig(OUT / 'tradeoff.png', dpi=150); print('saved', OUT / 'tradeoff.png')


if __name__ == '__main__':
    {'run': run, 'summary': summary, 'plot': plot, 'fixdiv': fixdiv}[sys.argv[1]]()
