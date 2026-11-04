"""Prop. 9 check (pure regression, Monte Carlo): weighting the pre-change data.

Model: segment A (n_A samples, controller w_A), segment B (n_B samples, w_B = w_A + delta),
FIR regression with AR(1) (pole 0.95) input, white noise sigma^2. Target: w_B.
Excess = (w_hat - w_B)^T R (w_hat - w_B) / sigma^2  (R = per-sample input covariance).

Estimators
  restart  : LS on B only (ridge 1e-6 if n_B <= M)
  pooled   : LS on A and B (alpha = 1)
  oracle   : weighted LS, alpha* = 1 / (1 + n_A D / M),  D = delta^T R delta / sigma^2
  plug-in  : alpha from D_hat = ||w_B_hat - w_A_hat||_R^2 / s^2 - M (1/n_A + 1/n_B)  (n_B > M)
  JS       : w_A_hat + (1 - (M-2) s'^2 / ||w_B_hat - w_A_hat||^2_{G_B})_+ (w_B_hat - w_A_hat),
             s'^2 = RSS_B / (n_B - M + 2)   (n_B > M)
Theory (Whittle, proportional covariances):
  excess(alpha) = [ (alpha n_A)^2 D + M (alpha^2 n_A + n_B) ] / (alpha n_A + n_B)^2
  minimum at alpha* (independent of n_B):  excess* = M / (n_B + M / (D + M / n_A))
"""
import json, sys
from pathlib import Path
import numpy as np
from scipy.linalg import toeplitz
from scipy.signal import lfilter
ROOT = Path(__file__).resolve().parents[1]

M = 64; sig = 1.0; pole = 0.95; trials = 300
rng = np.random.default_rng(0)
ac = pole ** np.arange(M) / (1 - pole ** 2); R = toeplitz(ac)


def conv_mat(x, M):
    n = len(x); idx = np.arange(n)[:, None] - np.arange(M)[None, :]
    return np.where(idx >= 0, x[np.clip(idx, 0, None)], 0.0)


def theory(alpha, nA, nB, D):
    a = alpha * nA
    return (a * a * D + M * (alpha * alpha * nA + nB)) / (a + nB) ** 2


rows = []
for nA in (1024, 4096):
    for nB in (M // 2, M, 2 * M, 4 * M, 8 * M):
        for kD in (0.0, 0.1, 1.0, 10.0, 100.0):          # n_A D / M
            D = kD * M / nA
            ex = {k: [] for k in ('restart', 'pooled', 'oracle', 'plugin', 'JS')}
            alph = []
            for t in range(trials):
                x = lfilter([1.0], [1.0, -pole], rng.standard_normal(nA + nB + 200))[200:]
                X = conv_mat(x, M); XA, XB = X[:nA], X[nA:]
                wA = rng.standard_normal(M); wA /= np.sqrt(wA @ R @ wA)
                dl = rng.standard_normal(M)
                dl *= np.sqrt(D * sig ** 2 / max(dl @ R @ dl, 1e-300)) if D > 0 else 0.0
                wB = wA + dl
                yA = XA @ wA + sig * rng.standard_normal(nA); yB = XB @ wB + sig * rng.standard_normal(nB)
                GA, GB = XA.T @ XA, XB.T @ XB; bA, bB = XA.T @ yA, XB.T @ yB
                eps = 1e-6 * np.trace(GB) / M
                wAh = np.linalg.solve(GA, bA); wBh = np.linalg.solve(GB + eps * np.eye(M), bB)
                f = lambda w: float((w - wB) @ R @ (w - wB)) / sig ** 2
                ex['restart'].append(f(wBh))
                ex['pooled'].append(f(np.linalg.solve(GA + GB, bA + bB)))
                a = 1.0 / (1.0 + nA * D / M)
                ex['oracle'].append(f(np.linalg.solve(a * GA + GB, a * bA + bB)))
                if nB > M:
                    rss = float(np.sum((yB - XB @ wBh) ** 2))
                    s2 = rss / (nB - M)
                    dw = wBh - wAh
                    Dh = max(0.0, float(dw @ (GB / nB) @ dw) / s2 - M * (1.0 / nA + 1.0 / nB))
                    ah = 1.0 / (1.0 + nA * Dh / M); alph.append(ah)
                    ex['plugin'].append(f(np.linalg.solve(ah * GA + GB, ah * bA + bB)))
                    shrink = max(0.0, 1.0 - (M - 2) * (rss / (nB - M + 2)) / max(float(dw @ GB @ dw), 1e-300))
                    ex['JS'].append(f(wAh + shrink * dw))
            row = {'nA': nA, 'nB': nB, 'nA_D_over_M': kD, 'theory_oracle': theory(1.0 / (1.0 + nA * D / M), nA, nB, D),
                   'theory_restart': M / max(nB - M - 1, 1e-9) if nB > M + 1 else None, 'theory_pooled': theory(1.0, nA, nB, D)}
            for k, v in ex.items():
                row[k] = float(np.mean(v)) if v else None
            row['alpha_star'] = 1.0 / (1.0 + kD); row['alpha_hat_mean'] = float(np.mean(alph)) if alph else None
            rows.append(row)
            fmt = lambda z: '   -  ' if z is None else f'{z:7.3f}'
            print(f"nA {nA:5d} nB {nB:4d} nA*D/M {kD:6.1f} | restart {fmt(row['restart'])} pooled {fmt(row['pooled'])} "
                  f"oracle {fmt(row['oracle'])} (th {fmt(row['theory_oracle'])}) plug-in {fmt(row['plugin'])} JS {fmt(row['JS'])} | "
                  f"alpha* {row['alpha_star']:.3f} alpha_hat {fmt(row['alpha_hat_mean'])}", flush=True)
(ROOT / 'results' / 'shrink_theory.json').write_text(json.dumps(rows, indent=1))
