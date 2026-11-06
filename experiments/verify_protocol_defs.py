"""Shared definitions of the frozen protocol (scenarios, method grids, one run).
"""
import json, os, sys
from pathlib import Path
import numpy as np
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src')); sys.path.insert(0, str(ROOT / 'experiments'))
import prototype_new_algorithms as P

T = 2.5; CH = 1.0
cab = dict(json.loads((ROOT / 'configs/ism_cabin.json').read_text()), ism_causal_ms=1.0)
rd = json.loads((ROOT / 'configs/random_decay.json').read_text())
SCEN = {
    'S1 src 10cm': dict(cab, move_dx=0.10),
    'S2 src 30cm': dict(cab, move_dx=0.30),
    'S3 mic 5cm': dict(cab, move_dx=0.05, move_target='mic'),
    'S4 mic 10cm': dict(cab, move_dx=0.10, move_target='mic'),
    'S5 src 30cm cont': dict(cab, move_dx=0.30, move_steps=16, move_seconds=0.6),
    'S6 mic 10cm cont': dict(cab, move_dx=0.10, move_target='mic', move_steps=16, move_seconds=0.6),
    'S7 rd abrupt': dict(rd),
    'S8 stationary': dict(cab, move_dx=0.0),
    'R1 rig 10cm': dict(cab, move_dx=0.10, move_target='rig'),
    'R2 rig 30cm': dict(cab, move_dx=0.30, move_target='rig'),
    'R3 rig 30cm cont': dict(cab, move_dx=0.30, move_target='rig', move_steps=16, move_seconds=0.6),
}
F = dict(k=8, L_hops=32, ridge=1e-3, detect=True, J=4, localize=True, loc_step=8, k_first=32, k_first_hops=4, k_steady=1,
         k_hops=16, det_stat='sandwich', kd=32, det_fa=1e-7, branch_hops=0, adapt='weight')
GRID = {
    'E-PCG (proposed)': ('PCG-WLS-F', [dict(F, screen_fa=sf, **({} if dx is None else {'robust_dx': dx, 'reg_gamma': 0.9}))
                                     for sf in (0.01, 0.05) for dx in (None, 0.05, 0.10)]),
    'FD-FxNLMS + spec (proposed rule)': ('spec_binwise', [{'mu': mu, 'robust_dx': dx, 'proximal': False} for mu in (0.35, 0.648, 1.0) for dx in (0.05, 0.10)]),
    'E-PCG v2 (bound + score fix)': ('PCG-WLS-F', [dict(F, screen_fa=sf, score_unreg=True, **({} if dx is None else {'robust_bound_dx': dx, 'reg_gamma': 0.9}))
                                            for sf in (0.01, 0.05) for dx in (None, 0.05, 0.10)]),
    'FD-FxNLMS + bound (proposed rule)': ('spec_binwise', [{'mu': mu, 'robust_dx': dx, 'bound': True, 'proximal': False} for mu in (0.35, 0.648, 1.0) for dx in (0.05, 0.10)]),
    'FD-FxNLMS + bound prox (proposed rule)': ('spec_binwise', [{'mu': mu, 'robust_dx': dx, 'bound': True, 'proximal': True} for mu in (0.35, 0.648, 1.0) for dx in (0.05, 0.10)]),
    'E-PCG v2 light': ('PCG-WLS-F', [dict(F, screen_fa=0.01, score_unreg=True, robust_bound_dx=0.10, reg_gamma=0.9,
                                        kd=16, k_first=16, steady_every=4)]),
    'FD-FxNLMS': ('fixed_binwise', [{'mu': mu} for mu in (0.2, 0.35, 0.5, 0.648, 0.8, 1.0)]),
    'leaky FD-FxNLMS': ('leaky_binwise', [{'mu': mu, 'leak': lk} for mu, lk in
                                          ((0.648, 1e-3), (0.648, 3e-3), (0.648, 1e-2), (0.648, 3e-2), (0.35, 1e-3), (0.35, 1e-2))]),
    'convex FD-FxNLMS': ('convex_binwise', [{'mu_fast': a, 'mu_slow': b, 'mu_a': 1.0} for a, b in
                                            ((0.9, 0.2), (1.0, 0.35), (0.8, 0.1), (1.2, 0.3), (0.9, 0.35), (1.0, 0.1))]),
    'OSP aux-free (Hu/Lian type)': ('osp_free', [{'mu': mu, 'mu_s': ms, 'Lh': 512} for mu in (0.35, 0.648) for ms in (0.02, 0.1, 0.5)]),
    'OSP sched (Akhtar type)': ('osp_binwise', [{'mu': 0.648, 'mu_s': ms, 'u_std': um, 'u_max': um, 'zls': True, 'Lh': 256, 'sched': True}
                                                for ms in (1e-3, 3e-3, 1e-2) for um in (0.05, 0.1)]),
    # v0 above used the ZLS third filter with its default step mu_h = 0.5 (too aggressive: S1 -5.7 vs -12.9 dB with 0.05); kept for the record
    'OSP sched (Akhtar type + ZLS)': ('osp_binwise', [{'mu': 0.648, 'mu_s': ms, 'u_std': um, 'u_max': um, 'zls': True, 'Lh': 256, 'mu_h': 0.05, 'sched': True}
                                                     for ms in (1e-3, 3e-3, 1e-2) for um in (0.05, 0.1)]),
    'OSP FD-FxNLMS (Eriksson)': ('osp_binwise', [{'mu': 0.648, 'mu_s': ms, 'u_std': us} for ms in (3e-4, 1e-3, 3e-3) for us in (0.05, 0.1)]),
    'RLS': ('R-RLS', [{'lam': lm, 'delta': 1e-2} for lm in (0.999, 0.9995, 0.9998, 0.9999, 0.99995, 1.0)]),
    'VFF-RLS': ('R-VFF', [{'N0': n0, 'lam_min': lmin, 'delta': 1e-3} for n0 in (500.0, 2000.0, 8000.0) for lmin in (0.98, 0.995)]),
    'FDKF': ('C-FDKF', [{'P0': p0, 'gain_scale': gs, 'A': 0.998} for p0 in (0.1, 1.0, 10.0) for gs in (1.0, 4.0)]),
}


def one(meth, prm, cfg, seed, change):
    r = P.run(cfg, seed, meth, prm, T, CH if change else None)
    tp = np.array(r['total_power']); up = np.array(r['uncontrolled_power'])
    fs = int(cfg['sample_rate']); H = int(cfg['hop_length']); hc = int(CH * fs) // H
    ok = bool(r['stable'] and len(tp) == len(up))
    o = {'stable': ok, 'events': len(r.get('reset_hops', []))}
    if ok:
        a = hc if change else 0
        o.update(post=float(tp[a:].sum()), post0=float(up[a:].sum()), early=float(tp[a:a + 16].sum()), early0=float(up[a:a + 16].sum()),
                 tail=float(tp[-len(tp) // 5:].sum()), tail0=float(up[-len(tp) // 5:].sum()))
    return o
