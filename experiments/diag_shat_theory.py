"""Ŝ != S: per-bin loop ratio rho = (S - S_hat)/S_hat vs post-change excursions (diagnosis for Prop. 10).

For each seed: rho on the 2M grid; over bins with x_f-hat power >= 1e-2 of its max:
  rho_max = max |rho|,  re_min = min Re(S/S_hat).
Outcome: loss caused by S_hat = post-change cumulative dB (hops +0..+48) with S_hat minus the
same with S_hat = S (same seed), for E-PCG (weight) and fixed bin-wise.
usage: python experiments/diag_shat_theory.py NMSE_DB
"""
import json, sys
from pathlib import Path
import numpy as np
from scipy.stats import spearmanr
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src')); sys.path.insert(0, str(ROOT / 'experiments'))
import prototype_new_algorithms as P
P.RETURN_SIGNALS = True
nm = float(sys.argv[1])
cfg = dict(json.loads((ROOT / 'configs/random_decay.json').read_text()), shat_nmse_db=nm)
N = 512; hc = 63
F = dict(k=8, L_hops=32, ridge=1e-3, detect=True, J=4, localize=True, loc_step=8, k_first=32, k_first_hops=4,
         k_steady=1, k_hops=16, det_stat='sandwich', kd=32, det_fa=1e-7, screen_fa=1e-2, adapt='weight')
rows = []
for sd in range(100, 120):
    rk = P.run(cfg, sd, 'known', {}, 2.0, 1.0)
    s, sh, x = rk['s'], rk['shat'], rk['x']
    S = np.fft.rfft(s, N); Sh = np.fft.rfft(sh, N)
    Px = np.mean([np.abs(np.fft.rfft(x[i:i + N] * np.hanning(N))) ** 2 for i in range(0, len(x) - N, N)], 0)
    wgt = Px * np.abs(Sh) ** 2; m = wgt >= 1e-2 * wgt.max()
    rho = (S - Sh) / Sh
    out = {}
    cfg0 = dict(cfg); cfg0.pop('shat_nmse_db')
    for name, (meth, prm) in (('epcg', ('E-PCG-F', F)), ('fixed', ('fixed_binwise', {'mu': 0.648}))):
        cum = []
        for cc in (cfg, cfg0):
            r = P.run(cc, sd, meth, prm, 2.0, 1.0)
            tp = np.array(r['total_power']); up = np.array(r['uncontrolled_power'])
            cum.append(float(10 * np.log10(tp[hc:hc + 48].sum() / up[hc:hc + 48].sum())) if len(tp) >= hc + 48 and r['stable'] else 99.0)
        out[name] = cum[0] - cum[1] if cum[0] < 99 else 99.0
    rows.append({'seed': sd, 'rho_max': float(np.max(np.abs(rho[m]))), 're_min': float(np.min((S / Sh).real[m])),
                 'worst_epcg_db': out['epcg'], 'worst_fixed_db': out['fixed']})
rows.sort(key=lambda z: -z['rho_max'])
print(f'NMSE {nm} dB   seed  max|rho|  min Re(S/Sh) | loss from S_hat [dB]: E-PCG  fixed')
for z in rows:
    print(f"            {z['seed']}  {z['rho_max']:7.2f}  {z['re_min']:8.2f}     | {z['worst_epcg_db']:7.2f} {z['worst_fixed_db']:7.2f}")
a = np.array([[z['rho_max'], z['re_min'], z['worst_epcg_db'], z['worst_fixed_db']] for z in rows])
print('Spearman max|rho| vs worst E-PCG: %.2f  vs fixed: %.2f;  min Re vs E-PCG: %.2f  vs fixed: %.2f' % (
    spearmanr(a[:, 0], a[:, 2])[0], spearmanr(a[:, 0], a[:, 3])[0], spearmanr(a[:, 1], a[:, 2])[0], spearmanr(a[:, 1], a[:, 3])[0]))
(ROOT / 'results' / 'shat_range' / f'theory_diag_m{int(-nm)}.json').write_text(json.dumps(rows, indent=1))
