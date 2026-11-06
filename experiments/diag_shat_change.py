"""Diagnostic: post-change curves under S_hat error (random plants, NMSE -15 dB). Mean and median dB per hop."""
import json, sys
from pathlib import Path
import numpy as np
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src')); sys.path.insert(0, str(ROOT / 'experiments'))
import prototype_new_algorithms as P
nm = float(sys.argv[1]) if len(sys.argv) > 1 else -15.0
cfg = dict(json.loads((ROOT / 'configs/random_decay.json').read_text()), shat_nmse_db=nm)
F = dict(adapt='restart', k=8, L_hops=32, ridge=1e-3, detect=True, J=4, localize=True, loc_step=8, k_first=32, k_first_hops=4, k_steady=1, k_hops=16)
M = {'fixed': ('fixed_binwise', {'mu': 0.648}), 'nodet': ('PCG-WLS-F', dict(F, detect=False)),
     'det-nobranch': ('PCG-WLS-F', dict(F, det_stat='sandwich', kd=32, det_fa=1e-7, screen_fa=1e-2, branch_hops=0)),
     'full': ('PCG-WLS-F', dict(F, det_stat='sandwich', kd=32, det_fa=1e-7, screen_fa=1e-2, branch_hops=8)),
     'weight': ('PCG-WLS-F', dict(F, det_stat='sandwich', kd=32, det_fa=1e-7, screen_fa=1e-2, branch_hops=0, adapt='weight'))}
hc = 63; res = {}
for k, (m, p) in M.items():
    A = []
    for sd in range(100, 120):
        r = P.run(cfg, sd, m, p, 2.0, 1.0)
        if r['stable'] and len(r['total_power']) == len(r['uncontrolled_power']):
            A.append(10 * np.log10(np.array(r['total_power']) / np.array(r['uncontrolled_power'])))
    A = np.array(A); res[k] = A
    print(k, 'n', len(A))
hops = [-1, 0, 1, 2, 3, 4, 6, 8, 12, 16, 24, 32, 48]
print('hop  ' + ' '.join(f'{k:>16s}' for k in M) + '   (median / mean-power dB)')
for h in hops:
    print(f'{h:+4d} ' + ' '.join(f"{np.median(res[k][:, hc + h]):7.2f}/{10*np.log10(np.mean(10**(res[k][:, hc + h]/10))):7.2f}" for k in M))
