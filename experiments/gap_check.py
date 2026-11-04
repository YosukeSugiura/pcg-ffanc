"""Numerical check 1 of [unpublished theory draft omitted] (Statement B), 2026-10-29. Analysis only (no method change).

For the actual filtered reference x_f of the stationary cell (S8, M = 512, N = 2M, H = 128; tuning seeds 300-309;
ar1 and harmonic):
  R_hat  = M x M Toeplitz autocorrelation of x_f (biased estimate over the 5 s run);
  S_k    = mean N-point periodogram |X_k|^2 / N of x_f frames (hop H; the FD-FxNLMS bin power, white input -> 1);
  K      = P_M F^{-1} diag(1 / S_k) F P_M^T (the FD-FxNLMS gain, M x M); exact RLS would have K = R^{-1};
  lambda = eigenvalues of K R_hat (real, positive: similar to R^{1/2} K R^{1/2});
  rho_c  = (1/M) sum lambda^2 / (2 lambda - 1)  (commuting approximation; inf if some lambda <= 1/2);
  rho_L  = tr(R Sigma) / M with (K R - I/2) Sigma + Sigma (K R - I/2)^T = K R K (general Lyapunov form; valid if
           min lambda > 1/2): asymptotic excess of the circulant-RLS schedule relative to the realizable bound.
Output: results/gap_check/summary.md (table per noise: lambda quantiles, fraction < 1/2, rho_c, rho_L in dB).
usage: python experiments/gap_check.py
"""
import sys
from pathlib import Path
import numpy as np
from scipy.linalg import toeplitz, solve_continuous_lyapunov
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src')); sys.path.insert(0, str(ROOT / 'experiments'))
import verify_protocol_defs as D  # noqa: E402
OUT = ROOT / 'results' / 'gap_check'; OUT.mkdir(parents=True, exist_ok=True)
M = 512; N = 2 * M; SEEDS = list(range(300, 310))


def xf_of(nz, sd):
    D.P.RETURN_SIGNALS = True
    cfg = dict(D.SCEN['S8 stationary'], controller_length=M, fft_length=N, **({} if nz == 'ar1' else {'noise_type': nz}))
    r = D.P.run(cfg, sd, 'fixed_binwise', {'mu': 0.0}, 5.0, None)
    return np.asarray(r['xf'], float), int(cfg['hop_length'])


def analyse(xf, H):
    n = len(xf)
    ac = np.correlate(xf, xf, 'full')[n - 1:n - 1 + M] / n
    R = toeplitz(ac)
    fr = [xf[s:s + N] for s in range(0, n - N + 1, H)]
    S = np.mean([np.abs(np.fft.rfft(f)) ** 2 for f in fr], 0) / N
    E = np.eye(N)[:, :M]                                         # P_M^T: embed M taps in an N frame
    K = (np.fft.irfft(np.fft.rfft(E, axis=0) / S[:, None], n=N, axis=0))[:M, :]
    K = 0.5 * (K + K.T)
    Rh = np.linalg.cholesky(R)
    lam = np.sort(np.linalg.eigvalsh(Rh.T @ K @ Rh))
    rho_c = float(np.mean(lam ** 2 / (2 * lam - 1))) if lam.min() > 0.5 else float('inf')
    rho_L = float('nan')
    if lam.min() > 0.5:
        A = K @ R - 0.5 * np.eye(M)
        Sig = solve_continuous_lyapunov(A, K @ R @ K)
        rho_L = float(np.trace(R @ Sig) / M)
    return lam, rho_c, rho_L


def main():
    out = ['# Gap check (Statement B of [unpublished theory draft omitted]): eigenvalues of K R for x_f, S8, M = 512, N = 2M',
           'rho = asymptotic excess of the circulant-RLS (1/b) FD-FxNLMS schedule over the realizable bound (1 = 0 dB);',
           'inf: some lambda <= 1/2 (slower than 1/b). Per seed; tuning seeds 300-309.', '',
           '| noise | seed | lambda min | q05 | median | q95 | max | frac < 1/2 | rho_c (dB) | rho_L (dB) |', '|---|---|---|---|---|---|---|---|---|---|']
    for nz in ['ar1', 'harmonic']:
        for sd in SEEDS:
            xf, H = xf_of(nz, sd)
            lam, rc, rl = analyse(xf, H)
            q = np.quantile(lam, [0.05, 0.5, 0.95])
            db = lambda z: ('inf' if not np.isfinite(z) else f'{10 * np.log10(z):.2f}') if z == z else 'n/a'
            out.append(f'| {nz} | {sd} | {lam.min():.3f} | {q[0]:.3f} | {q[1]:.3f} | {q[2]:.3f} | {lam.max():.2f} | '
                       f'{np.mean(lam < 0.5):.3f} | {db(rc)} | {db(rl)} |')
            print(out[-1], flush=True)
    (OUT / 'summary.md').write_text('\n'.join(out) + '\n')


if __name__ == '__main__':
    main()
