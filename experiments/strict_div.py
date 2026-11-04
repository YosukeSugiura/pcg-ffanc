"""Stricter failure criterion (2026-10-26), first applied to the proposed method.
Per run the hop-wise NR trace (dB, 1 hop = 16 ms) is stored, so any criterion can be evaluated afterwards:
  failure(th) = some 32-hop window (0.5 s) after the reference time has NR > th dB (0.25 s: post-change excursion)
  (reference time: the move for the mic-move cells, 1.0 s for S8 (after the initial convergence));
  thresholds 0 dB (worse than no control; primary), +6 dB, +30 dB (the old hop-wise limit, here windowed).
The simulator's own flag (stable / aborted) also counts as a failure. One horizon, T = 5 s for every cell (4 s after the
move); the reference is normalized to unit power over the run, so a run of another length is a rescaled realization and
is not mixed in. Window-length sensitivity: 0.125 / 0.25 / 0.5 / 1.0 s.
usage: PART=_a KEYS='E-PCG-M v6.5:2' python experiments/strict_div.py run ; python experiments/strict_div.py summary
"""
import json, os, sys
from pathlib import Path
import numpy as np
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src')); sys.path.insert(0, str(ROOT / 'experiments'))
import sweep_tradeoff as S  # noqa: E402
D = S.D
OUT = ROOT / 'results' / os.environ.get('OUTDIR', 'tradeoff_v2'); OUT.mkdir(parents=True, exist_ok=True)
SEEDS = (list(range(300, 310)) + list(range(600, 620))) if os.environ.get('SEEDSET') == 'tune' else list(S.SEEDS)
# stress cells (2026-10-26, tuning seeds only): the mic moves |dx| = D = 0.1 m along the speaker axis
D.SCEN['X1 mic D radial-in'] = dict(D.SCEN['S4 mic 10cm'], move_dir='radial_in')
D.SCEN['X2 mic D radial-in slow'] = dict(D.SCEN['S11 mic 10cm slow'], move_dir='radial_in')
D.SCEN['X3 mic D radial-out slow'] = dict(D.SCEN['S11 mic 10cm slow'], move_dir='radial_out')
CELLS = os.environ['CELLS'].split(';') if os.environ.get('CELLS') else S.CELLS
TT = 5.0; WIN = 32; THS = (0.0, 6.0, 30.0)   # primary window 0.5 s (32 hops); 0.25 s = post-change excursion


def run():
    keys = [(k.rsplit(':', 1)[0], int(k.rsplit(':', 1)[1])) for k in os.environ.get('KEYS', 'E-PCG-M v6.5:2').split(';')]
    fn = OUT / f"runs{os.environ.get('PART', '')}.jsonl"
    done = set()
    for f in OUT.glob('runs*.jsonl'):
        for l in f.read_text().splitlines():
            r = json.loads(l); done.add((r['method'], r['pt'], r['noise'], r['scen'], r['seed']))
    with fn.open('a') as fh:
        for m, i in keys:
            meth, key, pts = S.SWEEP[m]
            ovr = json.loads(os.environ.get('OVR', '{}'))         # diagnostic variants: flag overrides, tagged name
            if ovr:
                pts = [dict(p_, **ovr) for p_ in pts]; m = m + ' ' + os.environ.get('TAG', json.dumps(ovr))
            for nz in os.environ.get('NOISES', 'ar1;harmonic').split(';'):
                for sc in CELLS:
                    for sd in SEEDS:
                        if (m, i, nz, sc, sd) in done:
                            continue
                        cfg = dict(D.SCEN[sc], controller_length=S.M, fft_length=2 * S.M, **({} if nz == 'ar1' else {'noise_type': nz}))
                        ch = not sc.startswith('S8')
                        r = D.P.run(cfg, sd, meth, pts[i], TT, D.CH if ch else None)
                        tp = np.array(r['total_power']); up = np.array(r['uncontrolled_power'])
                        fh.write(json.dumps({'method': m, 'pt': i, 'noise': nz, 'scen': sc, 'seed': sd, 'flag_stable': bool(r['stable']),
                                             'tp': tp.tolist(), 'up': up[:len(tp)].tolist(), 'hops_full': len(up),
                                             }) + '\n'); fh.flush()
            print(m, i, 'done', flush=True)


def evaluate(r, th, win=WIN):
    """(failed, time of failure after the reference time [s]) over the whole run (T = 5 s).
    Failure: the residual power over some win-hop window after the reference time exceeds th dB relative to the
    uncontrolled power, or the simulator aborted / flagged the run (weight norm, non-finite)."""
    cfg = D.SCEN[r['scen']]; H = int(cfg['hop_length']); fs = int(cfg['sample_rate'])
    ref = int(D.CH * fs) // H
    tp = np.array(r['tp']); up = np.array(r['up'])
    bad = []
    c = np.concatenate([[0.0], np.cumsum(tp)]); u = np.concatenate([[0.0], np.cumsum(up)])
    st = np.arange(ref, len(tp) - win + 1)
    if st.size:
        w = 10 * np.log10((c[st + win] - c[st] + 1e-300) / (u[st + win] - u[st]))
        k = np.flatnonzero(~np.isfinite(w) | (w > th))
        if k.size:
            bad.append(st[k[0]] + win)
    if not r['flag_stable']:
        # time of the flag: the abort hop, else the first hop over the simulator's +30 dB hop limit, else (weight norm
        # only, not logged per hop) the end of the run (review 2026-10-26: was always the end of the run)
        hd = 10 * np.log10((tp + 1e-300) / up)
        k30 = np.flatnonzero(~np.isfinite(hd) | (hd > 30.0))
        bad.append(len(tp) if len(tp) < r['hops_full'] else (int(k30[0]) + 1 if k30.size else len(tp)))
    return (bool(bad), (min(bad) - ref) * H / fs if bad else None)


def evaluate_div(r, last=1.0):
    """Divergence (primary-path cells, 2026-10-27): simulator flag, or the residual power over the last `last` s exceeds
    the uncontrolled power (not recovered at the end). A worse-than-off transient after a primary-path change is
    unavoidable until re-convergence (the old anti-noise no longer matches): it measures tracking speed, not failure.
    Returns (failed, time after the reference [s] or None)."""
    cfg = D.SCEN[r['scen']]; H = int(cfg['hop_length']); fs = int(cfg['sample_rate']); ref = int(D.CH * fs) // H
    tp = np.array(r['tp']); up = np.array(r['up'])
    if not r['flag_stable']:
        hd = 10 * np.log10((tp + 1e-300) / up); k30 = np.flatnonzero(~np.isfinite(hd) | (hd > 30.0))
        b = len(tp) if len(tp) < r['hops_full'] else (int(k30[0]) + 1 if k30.size else len(tp))
        return True, (b - ref) * H / fs
    n = int(last * fs) // H
    if 10 * np.log10(tp[-n:].sum() / up[-n:].sum()) > 0.0:
        return True, (len(tp) - ref) * H / fs
    return False, None


def summary():
    R = [json.loads(l) for f in sorted(OUT.glob('runs*.jsonl')) for l in f.read_text().splitlines()]
    out = ['Failure = residual power over a window after the reference time (move; S8: 1.0 s) exceeds the uncontrolled '
           'power by th dB, or the simulator flag. T = 5 s. Primary (failure): th = 0 dB, window 0.5 s (32 hops); '
           'the 0.25 s window counts short post-change excursions (reported separately).']
    for m, i in sorted({(r['method'], r['pt']) for r in R}):
        for nz in ('ar1', 'harmonic'):
            rs = [r for r in R if r['method'] == m and r['pt'] == i and r['noise'] == nz]
            if not rs:
                continue
            out.append(f'\n### {m} pt {i}, {nz} (seeds {min(r["seed"] for r in rs)}-{max(r["seed"] for r in rs)}, {len({r["seed"] for r in rs})} seeds)')
            out.append('| cell | n | **failure: 0 dB, 0.5 s** | excursion: 0 dB, 0.25 s | 0 dB, 0.125 s | 0 dB, 1.0 s | +6 dB, 0.5 s | +30 dB, 0.5 s | '
                       'simulator flag (counted in every column) | median time of the failure (s, window end) | NR after the reference time (dB; flagged run = 0 dB) |')
            out.append('|---' * 11 + '|')
            for sc in list(S.CELLS) + [k for k in D.SCEN if k.startswith('X')]:
                c = [r for r in rs if r['scen'] == sc]
                if not c:
                    continue
                f = lambda th, w=WIN: sum(evaluate(r, th, w)[0] for r in c)
                t0 = [evaluate(r, 0.0)[1] for r in c if evaluate(r, 0.0)[0]]
                ref = int(D.CH * 8000) // 128
                nr = np.mean([10 * np.log10(sum(r['tp'][ref:]) / sum(r['up'][ref:len(r['tp'])])) if r['flag_stable'] else 0.0 for r in c])
                out.append(f"| {sc} | {len(c)} | **{f(0.0)}** | {f(0.0, 16)} | {f(0.0, 8)} | {f(0.0, 64)} | {f(6.0)} | {f(30.0)} | "
                           f"{sum(not r['flag_stable'] for r in c)} | {np.median(t0) if t0 else float('nan'):.2f} | {nr:.2f} |")
    txt = '\n'.join(out); print(txt); (OUT / 'summary.md').write_text(txt + '\n')


if __name__ == '__main__':
    {'run': run, 'summary': summary}[sys.argv[1]]()
