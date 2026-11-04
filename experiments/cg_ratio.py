"""Item 4 of the revision (REVISION_RULE.md): optimization vs estimation error of E-PCG under the final-evaluation
conditions (main configuration, M = 512), measured against dense window LS. Diagnostic only (no decision).

At every 4th hop where the controller solves the plain window problem (no active change event, full controller
length: window >= 2M samples), with G = X^T X + ridge I of the window and w_LS = -G^{-1} p:
  opt   = (w - w_LS)^T G (w - w_LS)              (optimization error of the applied controller, G metric)
  est   = M J(w_LS) / (n - M)                    (estimation error of window LS, Theorem 1 in the G metric)
  ratio = opt / est ; Prop. 3 targets ratio <= eps / lambda_min with eps = 0.1
plus, once per run (at the first measured hop), lambda_min / lambda_max of P^{-1/2} G P^{-1/2} with the Bartlett
circulant preconditioner P actually used.
Cells S8, S2, R2 x {ar1, harmonic}; tuning seeds 300-304 (no evaluation seed is used).
usage: python experiments/cg_ratio.py -> results/cg_ratio/summary.md
"""
import json, sys
from pathlib import Path
import numpy as np
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src')); sys.path.insert(0, str(ROOT / 'experiments'))
import verify_protocol_defs as D  # noqa: E402
import ffanc_norm.epcg as E  # noqa: E402
OUT = ROOT / 'results' / 'cg_ratio'; OUT.mkdir(parents=True, exist_ok=True)
M = 512; SEEDS = [300, 301, 302, 303, 304]; EVERY = 4
MAIN = json.loads((ROOT / 'results/final_dev/final_config_core_main.json').read_text())['flags']
CELLS = ['S8 stationary', 'S2 src 30cm', 'R2 rig 30cm']
LOG = []
_orig = E.EPCG._finish_hop


def _probe(self, Cm, Gw):
    w = _orig(self, Cm, Gw)
    c = self.cfg; H = c.H; n = self.stop - self.t0
    if self.ev is not None or n < 2 * c.M or (self.stop // H) % EVERY or self.skip_solve:
        return w
    G = self._XtX_dense(self.t0, self.stop); rid = c.ridge * self.r[0] + 1e-30
    Gr = G + rid * np.eye(c.M)
    wls = np.linalg.solve(Gr, -self.p)
    J = self.e0 + 2.0 * float(wls @ self.p) + float(wls @ G @ wls)
    est = c.M * max(J, 1e-300) / max(n - c.M, 1)
    dw = self.w - wls
    rec = {'stop': int(self.stop), 'n': int(n), 'opt': float(dw @ Gr @ dw), 'est': float(est)}
    if not getattr(self, '_lam_done', False) and n >= c.L_hops * H:     # (review S3) full window n = L H
        self._lam_done = True
        rr = np.fft.irfft(self._circ(self.r), self.n2)[:c.M] * np.maximum(1.0 - np.arange(c.M) / c.M, 0.0)
        Cb = np.fft.rfft(np.concatenate([rr, [0.0], rr[:0:-1]]), self.n2)
        pre = np.maximum(Cb.real, 1e-9 * np.max(Cb.real)) + rid
        Pinv = np.fft.irfft(np.fft.rfft(np.eye(self.n2)[:, :c.M], axis=0) / pre[:, None], n=self.n2, axis=0)[:c.M, :]
        Pinv = 0.5 * (Pinv + Pinv.T)
        ev = np.linalg.eigvalsh(np.linalg.cholesky(Pinv + 1e-12 * np.eye(c.M)).T @ Gr @ np.linalg.cholesky(Pinv + 1e-12 * np.eye(c.M)))
        rec['lam_min'] = float(ev.min()); rec['lam_max'] = float(ev.max()); rec['lam_n'] = int(n)
    LOG.append(rec)
    return w


E.EPCG._finish_hop = _probe


def main():
    out = ['# CG optimization / estimation error under the final-evaluation conditions (E-PCG main, M = 512)',
           'ratio = opt / est at every 4th plain-window hop (window >= 2M, no active event); tuning seeds 300-304.', '',
           '| noise | cell | hops | median ratio | q90 ratio | max ratio | median lambda_min | median lambda_max |',
           '|---|---|---|---|---|---|---|---|']
    raw = {}
    for nz in ['ar1', 'harmonic']:
        for sc in CELLS:
            rs, lm, lx = [], [], []
            for sd in SEEDS:
                LOG.clear()
                cfg = dict(D.SCEN[sc], controller_length=M, fft_length=2 * M, **({} if nz == 'ar1' else {'noise_type': nz}))
                D.P.run(cfg, sd, 'E-PCG-F', dict(MAIN), 5.0, None if sc.startswith('S8') else D.CH)
                rs += [r['opt'] / r['est'] for r in LOG]
                lm += [r['lam_min'] for r in LOG if 'lam_min' in r]; lx += [r['lam_max'] for r in LOG if 'lam_max' in r]
            raw[f'{nz}|{sc}'] = rs
            q = np.quantile(rs, [0.5, 0.9]) if rs else [np.nan, np.nan]
            out.append(f'| {nz} | {sc} | {len(rs)} | {q[0]:.3f} | {q[1]:.3f} | {max(rs) if rs else np.nan:.3f} | '
                       f'{np.median(lm) if lm else np.nan:.3f} | {np.median(lx) if lx else np.nan:.2f} |')
            print(out[-1], flush=True)
    (OUT / 'raw.json').write_text(json.dumps(raw))
    (OUT / 'summary.md').write_text('\n'.join(out) + '\n')


if __name__ == '__main__':
    main()
