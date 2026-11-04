"""Diagnosis of the CFTF + det failure (S7 ar1, evaluation seed 515; [workflow reference omitted]). No decision depends on it.
Wraps _cftf_run: an exact RLS twin with the same prior and window is fed the same data, so the deviation of the CFTF
controller from the exact LS solution is traced per hop, with the FTF energies and the conversion factor.
usage: RLS_FAST=1 python experiments/diag_cftf_divergence.py -> results/revision7_diag/cftf_515.md"""
import sys
from pathlib import Path
import numpy as np
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'experiments')); sys.path.insert(0, str(ROOT / 'src'))
import eval_v2 as E  # noqa: E402
P = E.D.P
orig = P._cftf_run; rows = []; twin = {}


def wrapped(S, xf, dhat, w, t_from, t_to, lam, M, stab=(1.5, 2.5, 1.0)):
    if twin.get('id') != id(S):                              # new restart: exact RLS with the same prior, centred at w
        d0 = (1.0 / S['z'][0]) * S['v'][0] if S['v'][0] != 0 else None
        pi = S['al'] * lam if S['first'] else None
        twin.update(id=id(S), P=np.diag(1.0 / (pi * lam ** (-np.arange(1, M + 1)))), w=w.copy(), tau=S['tau'])
    Pm, wt = twin['P'], twin['w']
    for t in range(t_from, t_to):
        u = np.array([xf[t - i] if t - i >= 0 else 0.0 for i in range(M)])
        eps = dhat[t] + u @ wt; Pu = Pm @ u; k = Pu / (lam + u @ Pu); wt = wt - k * eps
        Pm = (Pm - np.outer(k, Pu)) / lam
    twin['P'], twin['w'] = Pm, wt
    w_new = orig(S, xf, dhat, w, t_from, t_to, lam, M, stab)
    rows.append((t_to, float(np.linalg.norm(w_new - wt) / (np.linalg.norm(wt) + 1e-30)), float(np.linalg.norm(w_new)),
                 float(np.linalg.norm(wt)), S['al'], S['be'], S['gf'], float(np.linalg.norm(S['z']))))
    return w_new


P._cftf_run = wrapped
prm = dict(E.GRID['CFTF + det'][1][1])
rec = E.simulate('CFTF + det', prm, 'A', 'ar1', 'S7 rd abrupt', 515); mt = E.run_metrics(rec)
L = ['# CFTF + det, S7 ar1, seed 515 (diagnosis)', '', f"stable {rec['flag_stable']}, hops {len(rec['tp'])} of {rec['hops_full']}, "
     f"fail {mt['fail']}, restarts {rec['n_restarts']}", '',
     '| sample | rel dev from exact LS | norm w (CFTF) | norm w (exact) | alpha | beta | gamma_f | norm z |', '|---|---|---|---|---|---|---|---|']
for r in rows:
    L.append('| %d | %.2e | %.3g | %.3g | %.3g | %.3g | %.3g | %.3g |' % r)
(ROOT / 'results/revision7_diag/cftf_515.md').write_text('\n'.join(L) + '\n'); print('\n'.join(L[:6] + L[6::4][:40]))
