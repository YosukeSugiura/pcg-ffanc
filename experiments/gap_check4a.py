"""Revision 10a (docs/current/REVISION_RULE_10a.md, corrective, written after the Rule 10 results). Analysis only.

S8 stationary, M = 512, N = 2M, H = 128, tuning seeds 300-309, ar1 and harmonic; T = 5 s (primary) and T = 20 s
(secondary, separate runs). Recursion A = the Prop. rho object (lag-truncated circulant gain K = P F^-1 D^-1 F P^T,
den_b = (b+1) H S_k with the run's full-run mean bin power S_k, step 1, no regularization, w_0 = 0). Recursion B = the
standard gradient-constrained FDAF (fd_block_gradient) with the same den_b. Metric: w-excess (w_b - w_LS)^T R (w_b - w_LS)
relative to sigma^2 M / (H b). Plus eigenvalues (harmonic, descriptive) and the mean-field fixed-point bias of B.
usage: RLS_FAST=1 OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 python experiments/gap_check4a.py
"""
import hashlib, json, os, platform, subprocess, sys
from importlib.metadata import version
from pathlib import Path
import numpy as np
from scipy.linalg import solve_toeplitz, toeplitz
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'experiments')); sys.path.insert(0, str(ROOT / 'src'))
import gap_check2 as G2  # noqa: E402
from ffanc_norm.fd_fxnlms import fd_block_gradient  # noqa: E402
from ffanc_norm.simulation import right_aligned_history, causal_fir_block  # noqa: E402

RULE = ROOT / 'docs/current/REVISION_RULE_10a.md'
RULE_B = ROOT / 'docs/current/REVISION_RULE_10b.md'   # reference correction (sigma^2 M/H (1/b - 1/n_h))
OUT = ROOT / 'results' / 'gap_check4a'
M, N, H = 512, 1024, 128
SEEDS = list(range(300, 310))
R5 = [(1, 8), (8, 32), (32, 100), (100, 312)]
R20 = R5 + [(312, 625), (625, 1250)]
RHO_PRED = 0.07          # results/gap_check/summary.md, rho_c median (ar1); also re-read below and checked
WMAX = 1e6               # divergence guard (harmonic): after ||w|| > WMAX or non-finite, the rest is NaN


def signals(nz, sd, tt):
    G2.D.P.RETURN_SIGNALS = True
    r = G2.D.P.run(G2.cfg_of(nz), sd, 'fixed_binwise', {'mu': 0.0}, tt, None)
    G2.D.P.RETURN_SIGNALS = False
    return np.asarray(r['xf'], float), np.asarray(r['dhat'], float)


def ls_ref(xf, dh):
    """Whole-run LS controller (Toeplitz), per-hop floor, Toeplitz R, autocorrelation and cross-correlation."""
    n = len(xf); nf = int(2 ** np.ceil(np.log2(2 * n)))
    X = np.fft.rfft(xf, nf); Dh = np.fft.rfft(dh, nf)
    ac_full = np.fft.irfft(np.abs(X) ** 2, nf); cxd = np.fft.irfft(np.conj(X) * Dh, nf)
    w = solve_toeplitz(ac_full[:M], -cxd[:M])
    e = dh + np.fft.irfft(X * np.fft.rfft(w, nf), nf)[:n]
    floor = np.array([np.mean(e[b * H:(b + 1) * H] ** 2) for b in range(n // H)])
    return w, floor, toeplitz(ac_full[:M] / n), ac_full / n, cxd / n


def bin_power(xf):
    """gap_check.py definition: mean N-point periodogram |X_k|^2 / N of x_f frames with hop H."""
    n = len(xf)
    return np.mean([np.abs(np.fft.rfft(xf[s:s + N])) ** 2 for s in range(0, n - N + 1, H)], 0) / N


def recursion(xf, dh, Sx, w_ls, R, kind):
    n = len(xf); w = np.zeros(M); ew = np.full(n // H, np.nan); tp = np.full(n // H, np.nan); dead = False
    for b in range(n // H):
        start, stop = b * H, (b + 1) * H
        dw = w - w_ls; ew[b] = float(dw @ R @ dw)
        r = dh[start:stop] + causal_fir_block(xf, w, start, stop); tp[b] = float(np.mean(r ** 2))
        xh = right_aligned_history(xf, stop, N); X = np.fft.rfft(xh)
        den = (b + 1) * H * Sx
        if kind == 'A':                                     # Prop. rho: lag-truncated correlation, then K
            ef = np.zeros(N); ef[-H:] = r
            c = np.fft.irfft(np.conj(X) * np.fft.rfft(ef), N); c[M:] = 0.0
            g = np.fft.irfft(np.fft.rfft(c) / den, N)[:M]
        else:                                               # standard gradient-constrained FDAF
            g = fd_block_gradient(xh, r, den, M)
        w = w - g
        if not np.all(np.isfinite(w)) or np.linalg.norm(w) > WMAX:
            dead = True; break
    return ew, tp, dead


def eig_and_bias(xf, dh):
    """Eigenvalues of K R (A) and of the implemented mean update (B), and the mean-field fixed-point bias of B."""
    n = len(xf)
    ac = np.correlate(xf, xf, 'full')[n - 1:n - 1 + 2 * N] / n
    Rm = toeplitz(ac[:M]); S = bin_power(xf)
    Kfull = np.fft.irfft(np.fft.rfft(np.eye(N), axis=0) / S[:, None], n=N, axis=0)
    K = Kfull[:M, :M]; lam_a = np.sort(np.linalg.eigvals(0.5 * (K + K.T) @ Rm).real)
    m = np.arange(N)[:, None]; j = np.arange(M)[None, :]
    full = np.minimum(N - m, H); Hx = (full * ac[np.abs(m - j)] + (H - full) * ac[np.abs(N - m + j)]) / H
    A_impl = Kfull[:M, :] @ Hx; lam_b = np.linalg.eigvals(A_impl)
    nf = int(2 ** np.ceil(np.log2(2 * n))); X = np.fft.rfft(xf, nf); Dh = np.fft.rfft(dh, nf)
    cxd = np.fft.irfft(np.conj(X) * Dh, nf) / n
    mm = np.arange(N); fv = np.minimum(N - mm, H)
    c0 = (fv * cxd[mm % nf] + (H - fv) * cxd[(mm - N) % nf]) / H
    w_ls = solve_toeplitz(ac[:M], -cxd[:M]); w_b = np.linalg.solve(A_impl, -(Kfull[:M, :] @ c0))
    dw = w_b - w_ls; floor = np.mean(dh ** 2) + 2 * w_ls @ cxd[:M] + w_ls @ Rm @ w_ls
    q = lambda v: [float(v.min()), float(np.quantile(v, .05)), float(np.median(v)), float(np.quantile(v, .95)), float(v.max())]
    return {'A_eig': q(lam_a), 'A_frac_lt_half': float(np.mean(lam_a < .5)),
            'B_eig_real': q(np.sort(lam_b.real)), 'B_frac_lt_half': float(np.mean(lam_b.real < .5)),
            'B_max_abs_imag': float(np.abs(lam_b.imag).max()),
            'B_bias_rel_floor_db': float(10 * np.log10(dw @ Rm @ dw / floor))}


def ratios(ew_mean, s2, ranges):
    nh = len(ew_mean)                                         # Rule 10b: reference w_LS uses all n_h hops
    th = lambda a, b: np.mean(s2 * (M / H) * (1.0 / np.arange(a, b) - 1.0 / nh))
    return {f'{a}-{b}': (float(10 * np.log10(np.mean(ew_mean[a:b]) / th(a, b))) if np.all(np.isfinite(ew_mean[a:b])) else None)
            for a, b in ranges}


def slope(ew_mean, s2, a=100, b=312):
    # Rule 10b: add back the in-sample reference offset s2 M/(H n_h); regress on b = number of updates (= index)
    hops = np.arange(a, b); y = ew_mean[a:b] + s2 * M / (H * len(ew_mean)); ok = np.isfinite(y) & (y > 1e-12)
    return float(np.polyfit(np.log10(hops[ok]), np.log10(y[ok]), 1)[0]) if ok.sum() > 2 else None


def predicted():
    rows = [l.split('|') for l in (ROOT / 'results/gap_check/summary.md').read_text().splitlines() if l.startswith('| ar1 |')]
    return float(np.median([float(r[9]) for r in rows]))


def main():
    if OUT.exists():
        raise FileExistsError(f'refusing to overwrite {OUT}')
    rho = predicted()
    if abs(rho - RHO_PRED) > 1e-9:
        raise ValueError(f'prediction changed: {rho}')
    OUT.mkdir(parents=True)
    num = {}; curves = {}; resid = {}
    for nz in ['ar1', 'harmonic']:
        num[nz] = {}
        for tt, ranges in [(5.0, R5), (20.0, R20)]:
            ews = {'A': [], 'B': []}; tps = {'A': [], 'B': []}; dead = {'A': 0, 'B': 0}; s2s = []; fls = []
            for sd in SEEDS:
                xf, dh = signals(nz, sd, tt); w_ls, fl, R, _, _ = ls_ref(xf, dh); Sx = bin_power(xf); s2s.append(fl.mean()); fls.append(fl)
                for k in 'AB':
                    ew, tpk, d = recursion(xf, dh, Sx, w_ls, R, k); ews[k].append(ew); tps[k].append(tpk); dead[k] += int(d)
                print(nz, tt, sd, 'done', flush=True)
            s2 = float(np.mean(s2s))
            if nz == 'ar1' and (dead['A'] or dead['B']):
                raise FloatingPointError(f'ar1 diverged at T={tt}: {dead} (Rule 10b section 4: stop and report)')
            if tt == 5.0:
                resid[nz] = {k: np.mean(np.array(tps[k]), 0) for k in 'AB'}; resid[nz]['floor'] = np.mean(np.array(fls), 0)
            for k in 'AB':
                em = np.mean(np.array(ews[k]), 0)               # NaN propagates if any seed diverged
                curves[f'{nz}|T{int(tt)}|{k}'] = em
                num[nz][f'T{int(tt)}|{k}'] = {'ratios_db': ratios(em, s2, ranges), 'slope_100_312': slope(em, s2),
                                             'diverged_seeds': dead[k],
                                             'last_hop_rel_floor_db': (float(10 * np.log10(em[-1] / s2)) if np.isfinite(em[-1]) else None)}
            num[nz][f'T{int(tt)}|floor_mean_db'] = float(10 * np.log10(s2))
        tps_ls = [np.asarray(G2.D.P.run(G2.cfg_of(nz), sd, 'R-RLS', {'lam': 1.0, 'delta': 1e-2}, 5.0, None)['total_power'], float)
                  for sd in SEEDS]                              # Rule 10b section 3: residual-excess ratio vs exact LS (T = 5 s)
        fl = resid[nz]['floor']; tl = np.mean(tps_ls, 0)[:len(fl)]; el = np.maximum(tl - fl, 1e-12)
        num[nz]['T5|residual_excess_vs_exactLS_db'] = {
            k: {f'{a}-{b}': (float(10 * np.log10(np.mean(np.maximum(resid[nz][k][:len(fl)] - fl, 1e-12)[a:b]) / np.mean(el[a:b])))
                            if np.all(np.isfinite(resid[nz][k][a:b])) else None) for a, b in R5} for k in 'AB'}
        eg = [eig_and_bias(*signals(nz, sd, 20.0)) for sd in SEEDS]   # Rule 10b: same length as B at 20 s
        num[nz]['eig'] = {k: (np.median([e[k] for e in eg], 0).tolist() if isinstance(eg[0][k], list) else float(np.median([e[k] for e in eg])))
                          for k in eg[0]}
        num[nz]['eig_per_seed'] = eg
    a5 = num['ar1']['T5|A']['ratios_db']['100-312']; a20 = num['ar1']['T20|A']['ratios_db']['625-1250']
    j5 = 'agreement (within 1 dB)' if (a5 is not None and abs(a5 - rho) <= 1.0) else 'departure (more than 1 dB)'
    j20 = 'agreement (within 1 dB)' if (a20 is not None and abs(a20 - rho) <= 1.0) else 'observed value reported as is'
    fmt = lambda v: 'NaN' if v is None else f'{v:+.2f}'
    out = ['# Revision 10a/10b: Prop. rho check, corrected mapping (S8, M = 512, seeds 300-309)', '',
           '**Corrective rules written after the Rule 10 results** (REVISION_RULE_10a.md, 10b.md; 10b also after seeing seed-300 values). Rule 10 judgement stands.',
           'ratio = 10 log10(ensemble-mean w-excess / sigma^2 (M/H)(1/b - 1/n_h)) over hop ranges (Rule 10b reference); slope of w-excess + sigma^2 M/(H n_h); A = lag-truncated gain (Prop. rho, E-PCG preconditioner K),',
           'B = standard gradient-constrained FDAF; den_b = (b+1) H S_k with the full-run bin power (non-causal oracle), step 1.', '',
           f'Prediction (ar1): {rho:+.2f} dB. harmonic: not verifiable with these recursions (declared before running); eigenvalues only.', '']
    for nz in ['ar1', 'harmonic']:
        out += [f'## {nz}', '| recursion | T | ' + ' | '.join(f'{a}-{b}' for a, b in R20) + ' | slope 100-312 | diverged seeds | last hop rel. floor |',
                '|---' * (len(R20) + 5) + '|']
        for tt in (5, 20):
            for k in 'AB':
                d = num[nz][f'T{tt}|{k}']; rr = d['ratios_db']
                out.append(f'| {k} | {tt} s | ' + ' | '.join(fmt(rr.get(f'{a}-{b}')) if f'{a}-{b}' in rr else '' for a, b in R20)
                           + f' | {fmt(d["slope_100_312"])} | {d["diverged_seeds"]} | {fmt(d["last_hop_rel_floor_db"])} dB |')
        rx = num[nz]['T5|residual_excess_vs_exactLS_db']
        out += [''] + [f'residual-power excess of {k} relative to exact LS (R-RLS lam 1), T = 5 s, Rule 10 definition (descriptive): '
                       + ', '.join(f'{r} {fmt(v)} dB' for r, v in rx[k].items()) for k in 'AB'] + ['']
        e = num[nz]['eig']
        out += [f'eigenvalues (median over seeds of min / q05 / median / q95 / max): A (K R) {np.round(e["A_eig"], 3).tolist()}, frac<1/2 {e["A_frac_lt_half"]:.3f}; '
                f'B (implemented, real part) {np.round(e["B_eig_real"], 3).tolist()}, frac<1/2 {e["B_frac_lt_half"]:.3f}, max |imag| {e["B_max_abs_imag"]:.2e}',
                f'mean-field fixed-point bias of B: {e["B_bias_rel_floor_db"]:+.1f} dB rel. floor (median over seeds)', '']
    out += ['## Pre-registered judgement (REVISION_RULE_10a section 4)',
            f'- primary (ar1, A, T = 5 s, hops 100-312): {fmt(a5)} dB vs {rho:+.2f} dB -> {j5}',
            f'- secondary (ar1, A, T = 20 s, hops 625-1250): {fmt(a20)} dB vs {rho:+.2f} dB -> {j20} '
            '(1-seed diagnostic before this rule: -0.6 dB)',
            '- harmonic: not judged (declared unverifiable with these recursions); eigenvalues above. B may stay finite but large (not flagged as diverged).',
            '- disclosure (Rule 10b section 2): seed 300 alone gave about +3.1 dB (5 s) and +2.0 dB (20 s) with this reference before this run.', '']
    np.savez(OUT / 'curves.npz', **curves)
    (OUT / 'summary.md').write_text('\n'.join(out) + '\n')
    (OUT / 'numeric.json').write_text(json.dumps({'prediction_ar1_db': rho, 'results': num}, indent=2) + '\n')
    (OUT / 'provenance.json').write_text(json.dumps({
        'commit': subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip(),
        'rule_sha256': hashlib.sha256(RULE.read_bytes()).hexdigest(), 'rule_10b_sha256': hashlib.sha256(RULE_B.read_bytes()).hexdigest(),
        'script_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        'git_status_porcelain': subprocess.check_output(['git', 'status', '--porcelain'], cwd=ROOT, text=True), 'seeds': SEEDS, 'python': platform.python_version(),
        'software': {x: version(x) for x in ('numpy', 'scipy', 'pyroomacoustics')},
        'env': {x: os.environ.get(x) for x in ('RLS_FAST', 'OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'MKL_NUM_THREADS')}}, indent=2) + '\n')
    print('\n'.join(out))


if __name__ == '__main__':
    main()
