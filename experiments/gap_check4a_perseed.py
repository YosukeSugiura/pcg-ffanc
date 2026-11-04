"""Revision 10a/10b, descriptive per-seed breakdown (no judgement). Analysis only.

Recomputes recursion A (ar1, T = 5 s, seeds 300-309) with the gap_check4a.py functions and reports, per seed, the
w-excess ratio to the Rule 10b reference sigma^2 (M/H)(1/b - 1/n_h) (per-seed sigma^2), the early peak, lambda_max(K R)
from results/gap_check4a/numeric.json, and each seed's share of the ensemble mean over hops 100-312.
Diagnostic calculation (2026-11-04). usage: RLS_FAST=1 python experiments/gap_check4a_perseed.py
"""
import hashlib, json, subprocess, sys
from pathlib import Path
import numpy as np
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'experiments')); sys.path.insert(0, str(ROOT / 'src'))
import gap_check4a as G  # noqa: E402

OUT = ROOT / 'results' / 'gap_check4a_perseed'
M, H = G.M, G.H
RANGES = [(1, 8), (8, 32), (32, 100), (100, 312)]


def main():
    if OUT.exists():
        raise FileExistsError(f'refusing to overwrite {OUT}')
    ej = json.loads((ROOT / 'results/gap_check4a/numeric.json').read_text())['results']['ar1']['eig_per_seed']
    rows = []; ews = []; s2s = []
    for i, sd in enumerate(G.SEEDS):
        xf, dh = G.signals('ar1', sd, 5.0); w_ls, fl, R, _, _ = G.ls_ref(xf, dh); Sx = G.bin_power(xf)
        ew, _, dead = G.recursion(xf, dh, Sx, w_ls, R, 'A'); s2 = float(fl.mean()); ews.append(ew); s2s.append(s2)
        nh = len(ew); th = lambda a, b: np.mean(s2 * (M / H) * (1 / np.arange(a, b) - 1 / nh))
        rr = {f'{a}-{b}': float(10 * np.log10(np.mean(ew[a:b]) / th(a, b))) for a, b in RANGES}
        bb = np.arange(1, nh); perhop = 10 * np.log10(ew[1:] / (s2 * (M / H) * (1 / bb - 1 / nh)))
        pk = int(np.argmax(perhop[:32])) + 1
        rows.append({'seed': sd, 'ratios_db': rr, 'peak_hop': pk, 'peak_db': float(perhop[pk - 1]),
                     'lambda_max_KR': float(ej[i]['A_eig'][-1]), 'diverged': bool(dead)})
        print(sd, rr, pk, flush=True)
    E = np.array(ews); s2 = float(np.mean(s2s)); nh = E.shape[1]
    th = np.mean(s2 * (M / H) * (1 / np.arange(100, 312) - 1 / nh))
    share = E[:, 100:312].mean(1); share = share / share.sum()
    agg = {'ensemble_100_312_db': float(10 * np.log10(np.mean(E.mean(0)[100:312]) / th)),
           'median_of_seeds_100_312_db': float(np.median([r['ratios_db']['100-312'] for r in rows])),
           'share_of_ensemble_mean_pct': {str(r['seed']): float(100 * s) for r, s in zip(rows, share)}}
    out = ['# Revision 10a/10b: per-seed breakdown of recursion A (ar1, T = 5 s), descriptive only (no judgement)', '',
           'ratio = 10 log10(w-excess / sigma^2 (M/H)(1/b - 1/n_h)) with the per-seed sigma^2 (the ensemble in gap_check4a uses the',
           'seed-mean sigma^2); peak = largest per-hop ratio within the first 32 hops.', '',
           '| seed | 1-8 | 8-32 | 32-100 | 100-312 | peak hop | peak (dB) | lambda_max(K R) | share of ensemble 100-312 |',
           '|---|---|---|---|---|---|---|---|---|']
    for r, s in zip(rows, share):
        q = r['ratios_db']
        out.append(f"| {r['seed']} | {q['1-8']:+.1f} | {q['8-32']:+.1f} | {q['32-100']:+.1f} | {q['100-312']:+.1f} | "
                   f"{r['peak_hop']} | {r['peak_db']:+.1f} | {r['lambda_max_KR']:.2f} | {100 * s:.0f} % |")
    out += ['', f"ensemble (seed-mean sigma^2): {agg['ensemble_100_312_db']:+.2f} dB; median of seeds: {agg['median_of_seeds_100_312_db']:+.2f} dB", '']
    OUT.mkdir(parents=True)
    (OUT / 'summary.md').write_text('\n'.join(out) + '\n')
    (OUT / 'numeric.json').write_text(json.dumps({'rows': rows, 'aggregate': agg}, indent=2) + '\n')
    (OUT / 'provenance.json').write_text(json.dumps({
        'commit': subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip(),
        'script_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}, indent=2) + '\n')
    print('\n'.join(out))


if __name__ == '__main__':
    main()
