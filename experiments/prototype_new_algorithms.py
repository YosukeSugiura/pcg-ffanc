"""Screening prototypes for new frequency-domain FFANC update rules.

Candidates (all realizable: only current/past signals, secondary-path model S_hat):

A  Virtual-residual subspace least squares (VR-SLS)
   The disturbance is reconstructed as d_hat = e - S_hat*y.  For any candidate
   controller w, the residual it *would* have produced on past data is
       r(w) = d_hat + x_f * w,      x_f = S_hat * x,
   which is linear in w.  Each hop, a small set of frequency-domain search
   directions D = [d_1..d_K] is built and the coefficients alpha minimizing
   ||r(w + D alpha)||^2 + rho ||alpha||^2 over the last L hops are solved
   exactly (K x K system).  Variants:
     A-GB    : directions = global- and bin-wise-normalized gradients
               (the "combine two normalizations" idea as a 2-D subspace)
     A-GBm   : A-GB plus the previous update direction (momentum / CG-like)
     A-band  : bin-wise gradient split into K contiguous frequency bands
               (realizable counterpart of the per-bin oracle with K << N/2)

C  Filtered-x frequency-domain Kalman filter on the virtual error (FDKF-MFx)
   Diagonal FDKF (Enzner & Vary 2006 form with hop/frame ratio r = H/N),
   driven by the virtual error r(w) of the newest hop.  `gain_scale` > 1 is the
   overlap-correction hypothesis (effective mu > 1 at cold start).

Baselines: fixed bin-wise FD-FxNLMS on the physical error (project baseline)
and on the virtual error (isolates the effect of d_hat reconstruction).

Signals are generated with benchmark_transient_oracles._make_signals, i.e.
sample-identical to the conventional benchmark held-out signals.
"""
from __future__ import annotations

import argparse
import itertools
import json
from pathlib import Path
import sys
import time

import os
import numpy as np
from scipy.linalg import solve_toeplitz, toeplitz
from scipy.signal import lfilter

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
sys.path.insert(0, str(ROOT / 'experiments'))

from ffanc_norm.benchmark_metrics import (  # noqa: E402
    classify_diagnostic_run,
    cumulative_power_ratio_db,
    diagnostic_stability_summary,
    ensemble_power_ratio_db,
    threshold_times_from_db_curve,
)
from ffanc_norm.fd_fxnlms import fd_block_gradient  # noqa: E402
from ffanc_norm import naming as _naming  # noqa: E402
from ffanc_norm.normalization import PowerTracker  # noqa: E402
from ffanc_norm.simulation import causal_fir_block, right_aligned_history  # noqa: E402
from ffanc_norm.theory import primary_variance, wiener_solution  # noqa: E402
from benchmark_transient_oracles import _make_signals  # noqa: E402


def fir_window(signal: np.ndarray, coeffs: np.ndarray, start: int, stop: int) -> np.ndarray:
    return causal_fir_block(signal, coeffs, start, stop)


def conv_matrix(xf, t0, stop, M):
    """Rows n in [t0,stop): X[n-t0, m] = xf[n-m] (zero for n-m<0)."""
    t = np.arange(t0, stop)[:, None] - np.arange(M)[None, :]
    X = np.where(t >= 0, xf[np.clip(t, 0, None)], 0.0)
    return X


def xcorr_t(xf, z, t0, stop, M):
    """X^T z for the window [t0,stop) without forming X (via correlation)."""
    seg = xf[max(0, t0 - M + 1):stop]
    pad = M - 1 - (t0 - max(0, t0 - M + 1))
    seg = np.concatenate([np.zeros(pad), seg])            # covers xf[t0-M+1 .. stop-1]
    full = np.correlate(seg, z, mode='valid')             # length M, lag order reversed
    return full[::-1].copy()


def edge_matrix(xf, tb, M):
    """(M-1) x M edge matrix Z with Z[k, i] = xf[tb+k-i] if 0 <= tb+k-i < tb else 0.

    For a window [t0, stop) the exact covariance is
        X^T X = T(r) + Z(t0)^T Z(t0) - Z(stop)^T Z(stop),
    where T(r) is the Toeplitz matrix of r_l = sum_{n=t0}^{stop-1} xf[n] xf[n-l].
    Each edge term uses only the M-1 samples before the boundary, so a
    matrix-vector product costs two short convolutions (FFT-able).
    """
    k = np.arange(M - 1)[:, None]; i = np.arange(M)[None, :]
    idx = tb + k - i
    valid = (idx < tb) & (idx >= 0)
    Z = np.zeros((M - 1, M))
    Z[valid] = xf[idx[valid]]
    return Z


def window_autocorr(xf, t0, stop, M):
    """r_l = sum_{n=t0}^{stop-1} xf[n] xf[n-l], l = 0..M-1 (xf[<0] = 0)."""
    seg = np.concatenate([np.zeros(max(0, M - 1 - t0)), xf[max(0, t0 - M + 1):stop]])
    cur = seg[M - 1:]
    return np.array([cur @ seg[M - 1 - l:M - 1 - l + len(cur)] for l in range(M)])


def band_directions(xf_hist, err, denom, M, n_bands):
    """Bin-wise-normalized gradient split into contiguous frequency bands."""
    N = len(xf_hist)
    H = len(err)
    e_frame = np.zeros(N)
    e_frame[-H:] = err
    Z = np.conj(np.fft.rfft(xf_hist)) * np.fft.rfft(e_frame) / denom
    edges = np.linspace(0, len(Z), n_bands + 1).round().astype(int)
    dirs = []
    for i in range(n_bands):
        Zi = np.zeros_like(Z)
        Zi[edges[i]:edges[i + 1]] = Z[edges[i]:edges[i + 1]]
        dirs.append(np.fft.irfft(Zi, n=N)[:M])
    return dirs


RETURN_SIGNALS = False   # analysis scripts: also return x_f, d_hat, e


def changed_primary_path() -> np.ndarray:
    """Primary path after an abrupt change (tracking scenario)."""
    h = np.zeros(64)
    h[6], h[12], h[21], h[40] = 0.7, -0.4, 0.25, -0.1
    return h


def movement_bound(shat, M, fs, D, rs, p_exc=0.025, win=8, c0=343.0):
    """Per-bin bound eps_k >= -Re((S'_k - S_hat_k)/S_hat_k) for an error-mic displacement |delta| <= D (Prop. 10 + 12).
    S_hat = S_d + S_r: direct part = taps within +-win of the main peak, reverberant part = the rest.
    Direct part (deterministic worst case over the new speaker distance r' in [rs - D, rs + D]):
        b_d,k = max_u -Re( (S_d,k / S_k) ((rs/(rs+u)) e^{-j w_k u / c} - 1) ),   u in [-D, D]
    Reverberant part (diffuse, random direction): dS_r,k ~ CN(0, 2 (1 - sinc(w_k D/c)) |S_r,k|^2), so
    -Re(dS_r,k / S_k) ~ N(0, (1 - sinc) |S_r,k|^2 / |S_k|^2); one-sided exceedance probability p_exc:
        b_r,k = Q^{-1}(p_exc) sqrt(1 - sinc(w_k D/c)) |S_r,k| / |S_k|.
    eps_k = b_d,k + b_r,k (2M grid, M+1 bins). No free constant besides the design specs (D, p_exc)."""
    from scipy.stats import norm
    n2 = 2 * M; om = 2 * np.pi * np.arange(M + 1) / n2 * fs
    pk = int(np.argmax(np.abs(shat))); sd = np.zeros_like(shat)
    lo, hi = max(0, pk - win), min(len(shat), pk + win + 1); sd[lo:hi] = shat[lo:hi]
    Sk = np.fft.rfft(shat, max(n2, len(shat)))[:: max(1, max(n2, len(shat)) // n2)][:M + 1]
    Sdk = np.fft.rfft(sd, max(n2, len(shat)))[:: max(1, max(n2, len(shat)) // n2)][:M + 1]
    Srk = Sk - Sdk
    q = Sdk / np.where(np.abs(Sk) > 1e-12, Sk, 1e-12)
    us = np.linspace(-D, D, 201)
    fac = (rs / (rs + us))[None, :] * np.exp(-1j * om[:, None] * us[None, :] / c0) - 1.0
    bd = np.max(-np.real(q[:, None] * fac), axis=1)
    z = om * D / c0
    br = norm.isf(p_exc) * np.sqrt(np.maximum(1.0 - np.sinc(z / np.pi), 0.0)) * np.abs(Srk) / np.maximum(np.abs(Sk), 1e-12)
    return np.maximum(bd, 0.0) + br


def movement_rho(shat, M, fs, D, rs, win=8, c0=343.0, nu=201):
    """det_risk safety cap (Thm 6, A2): direct-path loop ratios rho_k(u) = (S_d,k / S_k)((rs/(rs+u)) e^{-j w_k u/c} - 1)
    on the 2M grid (M+1 bins) for u on a grid over [-D, D] (same decomposition as movement_bound). Returns (M+1, nu)."""
    n2 = 2 * M; om = 2 * np.pi * np.arange(M + 1) / n2 * fs
    pk = int(np.argmax(np.abs(shat))); sd = np.zeros_like(shat)
    lo, hi = max(0, pk - win), min(len(shat), pk + win + 1); sd[lo:hi] = shat[lo:hi]
    Sk = np.fft.rfft(shat, max(n2, len(shat)))[:: max(1, max(n2, len(shat)) // n2)][:M + 1]
    Sdk = np.fft.rfft(sd, max(n2, len(shat)))[:: max(1, max(n2, len(shat)) // n2)][:M + 1]
    q = Sdk / np.where(np.abs(Sk) > 1e-12, Sk, 1e-12)
    us = np.linspace(-D, D, nu)
    return q[:, None] * ((rs / (rs + us))[None, :] * np.exp(-1j * om[:, None] * us[None, :] / c0) - 1.0)


def _third_octave_smooth(pw, om):
    """1/3-octave smoothing of a power spectrum on a DFT grid (at least the 3 nearest bins): estimate of the ensemble
    power S_bar of a diffuse reverberant response from one realization."""
    f = np.abs(om) / (2 * np.pi); out = np.empty_like(pw)
    for k in range(len(pw)):
        sel = (f >= f[k] * 2 ** (-1 / 6)) & (f <= f[k] * 2 ** (1 / 6))
        if sel.sum() < 3:
            sel = np.argsort(np.abs(f - f[k]))[:3]
        out[k] = np.mean(pw[sel])
    return out


def field_prior(Prk, om, Dp, c0=343.0, nD=64, amp_fs=None, n_lat=0):
    """Gaussian sound-field prior of the reverberant part after a movement, conditional on the pre-event response
    (THEOREM_A_PRIME.md sec. 8): P_r2,k | P_r1,k ~ CN(rho1_k P_r1,k, S_bar_k (1 - rho2_k) + (rho2_k - rho1_k^2) |P_r1,k|^2),
    rho_D = sinc(k D) (diffuse spatial correlation), D uniform in the ball |D| <= Dp, rho1 = E rho_D, rho2 = E rho_D^2.
    Returns (conditional mean per bin, conditional variance per bin)."""
    D = Dp * (np.arange(nD) + 0.5) / nD; wD = 3 * D ** 2; wD = wD / wD.sum()
    rho = np.sinc(np.outer(np.abs(om), D) / c0 / np.pi)
    r1 = rho @ wD; r2 = (rho ** 2) @ wD
    Sb = _third_octave_smooth(np.abs(Prk) ** 2, om)
    v = Sb * (1 - r2) + (r2 - r1 ** 2) * np.abs(Prk) ** 2
    if amp_fs is not None:
        # amplitude (spherical spreading) change of the images, -D cos(phi) / r_i: frequency-flat variance
        # E[D^2]/3 sum_n |p_r[n]|^2 / r(n)^2, r(n) = c n / fs (E D^2 = 3/5 Dp^2 in the ball). Without it the
        # model claims an unchanged response at DC (rho -> 1), which the exact test rejects as data accumulate.
        # n_lat (rev 2, review R7): system latency bound (peak of S_hat: the speaker is at distance >= 0), so the image
        # distance is c (n - n_lat) / fs >= the true one -> the variance is not underestimated
        pr_t = np.real(np.fft.ifft(Prk)); nn = np.arange(len(pr_t)); rn = c0 * np.maximum(nn - int(n_lat), 1) / float(amp_fs)
        v = v + 0.6 * Dp ** 2 / 3.0 * float(np.sum(pr_t ** 2 / rn ** 2))   # E|DFT_k of independent tap changes|^2 = sum of tap variances
    return r1 * Prk, v


def polack_prior(Pr, n_dir, fs, Dp, c0=343.0, nD=64, sm=16, env_mode='local', rev=1, n_lat=0):
    """Polack's statistical room response (THEOREM_A_PRIME.md sec. 8): reverberant part P_r[n] = env[n]^(1/2) b[n],
    b white Gaussian, env[n] = A exp(-(n - n_dir)/tau) (exponential decay fitted to the smoothed energy of P_r).
    Moving the source / microphone by D (uniform in the ball |D| <= Dp, random direction) changes b with the diffuse
    spatial correlation rho_D(k) = sinc(k D) per frequency and the image amplitudes by -D cos(phi)/r(n),
    r(n) = c (n / fs) the image distance. Conditional on the pre-event response:
      E[P_r2 | P_r1]   = env^(1/2) (rho1 * b_1),                       rho1 = E rho_D (filter)
      Cov[P_r2 | P_r1] = env^(1/2) C env^(1/2) + diag(env E[D^2]/3 / r(n)^2),   C Toeplitz with spectrum 1 - rho1^2
    The covariance is NOT stationary in time (the circulant 'diffuse'/'field' models are): the change follows the
    energy envelope of the response. Returns (mean of P_r2, covariance)."""
    Lg = len(Pr); n = np.arange(Lg)
    pw = np.convolve(Pr ** 2, np.ones(sm) / sm, mode='same')
    if env_mode == 'exp':
        sel = (n > n_dir) & (pw > 1e-12 * pw.max())
        A_ = np.vstack([np.ones(sel.sum()), n[sel] - n_dir]).T
        cf = np.linalg.lstsq(A_, np.log(pw[sel]), rcond=None)[0]
        env = np.exp(cf[0] + cf[1] * np.maximum(n - n_dir, 0))
        env[n <= n_dir] = np.maximum(pw[n <= n_dir], 1e-12 * pw.max())   # before the direct sound: measured energy
    else:
        # local energy envelope (moving average of |P_r|^2 over sm taps): Polack's model with a non-parametric
        # envelope; early reflections are not forced onto one exponential decay
        env = np.maximum(pw, 1e-12 * pw.max())
    om = 2 * np.pi * np.fft.fftfreq(Lg) * fs
    D = Dp * (np.arange(nD) + 0.5) / nD; wD = 3 * D ** 2; wD = wD / wD.sum()
    r1 = np.sinc(np.outer(np.abs(om), D) / c0 / np.pi) @ wD
    sq = np.sqrt(env)
    mean = sq * np.real(np.fft.ifft(r1 * np.fft.fft(Pr / sq)))
    if rev >= 2:
        # review R8: autocovariance from the spectrum on a 4L grid; the L x L Toeplitz matrix is then a principal
        # submatrix of a PSD circulant (PSD guaranteed); the circular L-point version is not
        N4 = 4 * Lg; om4 = 2 * np.pi * np.fft.fftfreq(N4) * fs
        r14 = np.sinc(np.outer(np.abs(om4), D) / c0 / np.pi) @ wD
        cl = np.real(np.fft.ifft(1.0 - r14 ** 2))
    else:
        cl = np.real(np.fft.ifft(1.0 - r1 ** 2))                        # autocovariance of the change of b
    C = cl[np.abs(n[:, None] - n[None, :])]
    ED2 = 0.6 * Dp ** 2                                                   # E D^2 for D uniform in the ball
    rn = c0 * np.maximum(n - (int(n_lat) if rev >= 2 else 0), 1) / fs
    Sig = sq[:, None] * C * sq[None, :] + np.diag(env * ED2 / 3.0 / rn ** 2)
    return mean, (Sig + Sig.T) / 2


def nuisance_prior(x, y, e, sh, a, b, Lg, Dp, fs, win=8, c0=343.0, joint=0, model='diffuse', parts=None, amp=False, rev=1):
    """Theorem A' (THEOREM_A_PRIME.md): Gaussian prior N(theta_bar, Sigma) on the x-lag nuisance (primary path, Lg taps)
    for the SHRINK test after an event, from the pre-event window [a, b):
      theta_bar = LS estimate of the primary path (e - S_hat * y on Lg x-lags), s2 = its residual variance;
      Sigma = Sigma_r + tau^2 g g^T + s2 (X^T X)^-1, with Sigma_r circulant (Lg-point DFT) with per-bin variance
      2 (1 - sinc(omega_k Dp / c)) |P_r,k|^2 (diffuse change of the reverberant part, Prop. 12 with spec Dp),
      direct part with two free directions (gain: P_d, variance 1; delay: dP_d/du, variance Dp^2 / 3), and the
      estimation covariance of theta_bar.
    Returns (theta_bar, Lam = s2 Sigma^-1, s2, Sigma)."""
    lo = max(a - len(sh), 0)
    dh = e[a:b] - np.convolve(y[lo:b], sh)[a - lo:b - lo]
    idx = np.arange(a, b)[:, None] - np.arange(Lg)[None, :]
    X = np.where(idx >= 0, x[np.clip(idx, 0, None)], 0.0)
    G = X.T @ X
    th = np.linalg.solve(G + 1e-9 * np.trace(G) / Lg * np.eye(Lg), X.T @ dh)
    s2 = float(np.sum((dh - X @ th) ** 2)) / max((b - a) - Lg, 1)
    pk = int(np.argmax(np.abs(th))); Pd = np.zeros(Lg); Pd[max(0, pk - win):pk + win + 1] = th[max(0, pk - win):pk + win + 1]
    Pr = th - Pd
    om = 2 * np.pi * np.fft.fftfreq(Lg) * fs
    n_lat = int(np.argmax(np.abs(sh))) if rev >= 2 else 0
    Sr_t = None
    if model == 'polack':
        # sid_prior_model 'polack': envelope-modulated (non-stationary) change covariance, conditional mean
        Pr, Sr_t = polack_prior(Pr, pk + win, fs, Dp, c0, rev=rev, n_lat=n_lat); th = Pr + Pd
        v = np.zeros(Lg)
    elif model == 'field':
        # sid_prior_model 'field': conditional Gaussian-field prior (mean rho1 P_r1, smoothed ensemble power)
        _Pm, v = field_prior(np.fft.fft(Pr), om, Dp, c0, amp_fs=(fs if amp else None), n_lat=n_lat)
        Pr = np.real(np.fft.ifft(_Pm)); th = Pr + Pd
    else:
        v = 2.0 * (1.0 - np.sinc(om * Dp / c0 / np.pi)) * np.abs(np.fft.fft(Pr)) ** 2
    F = np.fft.fft(np.eye(Lg))
    Sr = np.real(F.conj().T @ np.diag(v) @ F) / Lg ** 2 if Sr_t is None else Sr_t
    # direct part: gain and delay are independent when the distance of the moving element is unknown (n_d = 2):
    # gain direction P_d (relative gain change, flat prior: variance 1), delay direction dP_d/du of e^{-j w u / c}
    # (|u| <= Dp uniform: variance Dp^2 / 3)
    nf = 4096; omf = 2 * np.pi * np.fft.rfftfreq(nf) * fs
    gd = np.fft.irfft(np.fft.rfft(Pd, nf) * (-1j * omf / c0), nf)[:Lg]
    if joint and rev >= 2:
        # rev 2 (review R6): delay AND gain of the direct part are profiled (family g P_d(u_p)), so the gain direction moves
        # with u_p; the prior covers only the reverberant part and the estimation error
        Sig = Sr + s2 * np.linalg.inv(G + 1e-9 * np.trace(G) / Lg * np.eye(Lg))
    elif joint:
        # sid_prior_joint: the direct-part DELAY of the primary path is profiled exactly (family P_d(u_p), like S(u)), so the
        # prior only covers the reverberant part, a free gain of the direct part and the estimation error
        Sig = Sr + 1.0 * np.outer(Pd, Pd) + s2 * np.linalg.inv(G + 1e-9 * np.trace(G) / Lg * np.eye(Lg))
    else:
        Sig = Sr + 1.0 * np.outer(Pd, Pd) + (Dp ** 2 / 3.0) * np.outer(gd, gd) + s2 * np.linalg.inv(G + 1e-9 * np.trace(G) / Lg * np.eye(Lg))
    if parts is not None:
        # components for a hierarchical (empirical-Bayes) refit of the prior scales per band: Sigma(kappa) =
        # sum_b kappa_b Sr_b + Pd Pd^T + s2 G^-1 (prior_typeII)
        fr = np.abs(om) / (2 * np.pi); Srb = []
        for lo_, hi_ in parts:
            vb = np.where((fr >= lo_) & (fr < hi_), v, 0.0)
            Srb.append(np.real(F.conj().T @ np.diag(vb) @ F) / Lg ** 2)
        Sig_fix = np.outer(Pd, Pd) + s2 * np.linalg.inv(G + 1e-9 * np.trace(G) / Lg * np.eye(Lg))
    Sig = (Sig + Sig.T) / 2
    Lam = s2 * np.linalg.inv(Sig + 1e-12 * np.trace(Sig) / Lg * np.eye(Lg))
    if parts is not None:
        out = (th, (Lam + Lam.T) / 2, s2, Sig)
        if joint:
            ups = np.linspace(-Dp, Dp, int(joint))
            fams = np.stack([Pr + np.fft.irfft(np.fft.rfft(Pd, nf) * np.exp(-1j * omf * up / c0), nf)[:Lg] for up in ups])
            out = out + (fams,)
        return out + ({'Srb': Srb, 'fix': Sig_fix, 's2': s2},)
    if joint and rev >= 2:
        ups = np.linspace(-Dp, Dp, int(joint))
        famd = np.stack([np.fft.irfft(np.fft.rfft(Pd, nf) * np.exp(-1j * omf * up / c0), nf)[:Lg] for up in ups])
        return th, (Lam + Lam.T) / 2, s2, Sig, famd, Pr          # direct family (gain profiled) and reverberant mean
    if joint:
        ups = np.linspace(-Dp, Dp, int(joint))
        fams = np.stack([Pr + np.fft.irfft(np.fft.rfft(Pd, nf) * np.exp(-1j * omf * up / c0), nf)[:Lg] for up in ups])
        return th, (Lam + Lam.T) / 2, s2, Sig, fams
    return th, (Lam + Lam.T) / 2, s2, Sig


def prior_typeII(X, r, comp, kap0=None, s2=None, bounds=(-3.0, 6.0)):
    """Hierarchical prior (empirical Bayes, Type-II maximum likelihood): Sigma(kappa) = sum_b kappa_b Sr_b + fix,
    kappa_b >= 0 maximizing the marginal likelihood of r = d_hat - X theta_bar under r ~ N(0, s2 I + X Sigma X^T),
    s2 fixed (pre-event residual level). Returns (kappa, Lam = s2 Sigma^-1).
    -2 log L = r^T C^-1 r + log det C,  C = s2 I + X Sigma X^T  (Lg-dim via Sigma^{1/2}: det(I + Sigma^{1/2} G Sigma^{1/2}/s2))."""
    from scipy.optimize import minimize
    s2 = float(comp['s2'] if s2 is None else s2); G = X.T @ X; b = X.T @ r; rr = float(r @ r)
    Lg = G.shape[0]; nb = len(comp['Srb'])

    def sig(lk):
        S = comp['fix'] + sum(np.exp(l) * Sb for l, Sb in zip(lk, comp['Srb']))
        return (S + S.T) / 2

    def nll(lk):
        S = sig(lk); w, V = np.linalg.eigh(S); w = np.clip(w, 1e-14 * max(w.max(), 1e-300), None)
        R = V * np.sqrt(w)                                   # S = R R^T
        A = np.eye(Lg) + R.T @ G @ R / s2
        try:
            L = np.linalg.cholesky(A)
        except np.linalg.LinAlgError:
            return 1e30
        z = np.linalg.solve(L, R.T @ b) / s2
        return float(rr / s2 - z @ z + 2 * np.sum(np.log(np.diag(L))))

    x0 = np.zeros(nb) if kap0 is None else np.log(np.asarray(kap0, float))
    res = minimize(nll, x0, method='L-BFGS-B', bounds=[bounds] * nb)
    S = sig(res.x)
    Lam = s2 * np.linalg.inv(S + 1e-12 * np.trace(S) / Lg * np.eye(Lg))
    return np.exp(res.x), (Lam + Lam.T) / 2


def ridge_cost(ep, eps, w_app, gamma=None):
    """Thm 4 term (iii), exact Whittle form, per sample, for a ridge from the bound eps on the primary member's window:
    (1/(n2 n)) sum_k g_k P_k |W_T,k|^2 (lam_k / (P_k + lam_k))^2, W_T = W_app (P + lam_app) / P (unregularized target)."""
    m = ep.members[ep.ip] if hasattr(ep, 'members') else ep
    Cf = m._circ(m.r); P = np.maximum(Cf.real, 1e-3 * np.max(Cf.real))
    g = np.full(len(P), 2.0); g[0] = g[-1] = 1.0
    la = m._robust_reg(Cf); la = np.zeros_like(P) if la is None else la
    WT = np.fft.rfft(np.asarray(w_app, float), m.n2) * (P + la) / P
    gam = float(m.cfg.reg_gamma if gamma is None else gamma)
    lam = P * np.maximum(0.0, np.asarray(eps) / gam - 1.0)
    return float(np.sum(g * P * np.abs(WT) ** 2 * (lam / (P + lam)) ** 2) / (m.n2 * max(m.stop - m.t0, 1)))


def pre_event_s2(x, y, e, sh, a, b, Lg):
    """sid_bias: residual variance of the check model (two halves, Lg x-lags each, u = 0) on [a, b) before an event."""
    h = a + (b - a) // 2; J = 0.0
    lo = max(a - len(sh), 0)
    dh = e[a:b] - np.convolve(y[lo:b], sh)[a - lo:b - lo]
    for s0, s1 in ((a, h), (h, b)):
        idx = np.arange(s0, s1)[:, None] - np.arange(Lg)[None, :]
        X = np.where(idx >= 0, x[np.clip(idx, 0, None)], 0.0)
        r = dh[s0 - a:s1 - a]
        c, *_ = np.linalg.lstsq(X, r, rcond=None)
        J += float(np.sum((r - X @ c) ** 2))
    return J / max((b - a) - 2 * Lg - 1, 1)


def thmA_diag(x, y, e, shat, tau, stop, M, fs, D, rs, p_exc, ep, w_app, nu=20, win=8, c0=343.0, gamma=None):
    """Theorem A diagnostic on [tau, stop) (u0 = 0, i.e. S_hat = S(0); THEOREM_A.md sec. 5).
    Returns (stop, n, Lg, [||P_perp z(u1)||^2], ||P_perp (e - S_hat*y)||^2, [E*(0, u1)], E_ach, u1 grid) with
    z(u1) = (S(0) - S(u1)) * y and Psi = Lg x-lags (Lg of the 'direct' nuisance model). E in absolute power per sample
    (exact Whittle form on the unregularized target W_T = W_app (P + lam_app) / P), above the reverberant-only guard."""
    n = stop - tau; Lg = _sid_lg('direct', shat, M, D, fs)
    us = np.linspace(-D, D, nu + 1); us = us[np.abs(us) > 1e-12]
    Ls = len(shat); lo = max(tau - Ls - Lg, 0)
    idx = np.arange(tau, stop)[:, None] - np.arange(Lg)[None, :]
    Psi = np.where(idx >= 0, x[np.clip(idx, 0, None)], 0.0)
    yy = y[lo:stop]
    S0y = np.convolve(yy, shat)[tau - lo:stop - lo]
    Z = np.stack([S0y - np.convolve(yy, shat_shift(shat, u, rs, fs))[tau - lo:stop - lo] for u in us], 1)
    r0 = e[tau:stop] - S0y
    B = np.column_stack([Z, r0])
    coef, *_ = np.linalg.lstsq(Psi, B, rcond=None)
    R = B - Psi @ coef
    rz = (R[:, :-1] ** 2).sum(0); rr = float((R[:, -1] ** 2).sum())
    # E*(0, u1): cheapest configuration safe for both S(0) and S(u1) (centre c in {0, u1/2, u1}), direct part, on top
    # of the reverberant guard b_r that the oracle also pays
    m = ep.members[ep.ip] if hasattr(ep, 'members') else ep
    Cf = m._circ(m.r); P = np.maximum(Cf.real, 1e-3 * np.max(Cf.real))
    g = np.full(len(P), 2.0); g[0] = g[-1] = 1.0
    lam_app = m._robust_reg(Cf); lam_app = np.zeros_like(P) if lam_app is None else lam_app
    Wa = np.fft.rfft(np.asarray(w_app, float), m.n2); WT = Wa * (P + lam_app) / P
    gam = float(m.cfg.reg_gamma if gamma is None else gamma); nwin = max(m.stop - m.t0, 1)
    E = lambda eps: float(np.sum(g * P * np.abs(WT) ** 2 * (lam / (P + lam)) ** 2) / (m.n2 * nwin)) if (lam := P * np.maximum(0.0, eps / gam - 1.0)) is not None else 0.0
    n2 = 2 * M; om = 2 * np.pi * np.arange(M + 1) / n2 * fs
    pk = int(np.argmax(np.abs(shat))); sd = np.zeros_like(shat); a_, b_ = max(0, pk - win), min(Ls, pk + win + 1); sd[a_:b_] = shat[a_:b_]
    nf = max(n2, Ls); st = max(1, nf // n2)
    Sk = np.fft.rfft(shat, nf)[::st][:M + 1]; Sdk = np.fft.rfft(sd, nf)[::st][:M + 1]
    Su = lambda u: Sk + Sdk * ((rs / (rs + u)) * np.exp(-1j * om * u / c0) - 1.0)
    br = movement_bound(shat, M, fs, D, rs, p_exc) - movement_bound(shat, M, fs, D, rs, p_exc=0.5)
    Ebr = E(br)
    Es = []
    for u in us:
        best = np.inf
        for cc in (0.0, u / 2, u):
            Sc = Su(cc); Sc = np.where(np.abs(Sc) > 1e-12, Sc, 1e-12)
            eps = np.maximum(np.maximum(0.0, -np.real((Su(0.0) - Sc) / Sc)), np.maximum(0.0, -np.real((Su(u) - Sc) / Sc)))
            best = min(best, E(eps + br) - Ebr)
        Es.append(max(best, 0.0))
    Eapp = float(np.sum(g * P * np.abs(WT) ** 2 * (lam_app / (P + lam_app)) ** 2) / (m.n2 * nwin))
    # set version (Theorem A'): cheapest configuration safe for all of U_m = {0} + m uniform points on [-D, D]
    Um = np.linspace(-D, D, 10)
    Eset = np.inf
    for cc in (-D / 4, 0.0, D / 4):
        Sc = Su(cc); Sc = np.where(np.abs(Sc) > 1e-12, Sc, 1e-12)
        eps = np.max(np.stack([np.maximum(0.0, -np.real((Su(u) - Sc) / Sc)) for u in np.append(Um, 0.0)]), 0)
        Eset = min(Eset, E(eps + br) - Ebr)
    # Lemma S prediction factor per u1: Q(u1) = (1/(n2 n)) sum_k g_k P_k |W_T,k|^2 |rho_k|^4 / |1 + rho_k|^2 (rho rel. S(0));
    # I_self ~ phibar * t * Q / (2 sigma^2) over t post-change samples
    S0 = Su(0.0); S0 = np.where(np.abs(S0) > 1e-12, S0, 1e-12)
    Qs = []
    for u in us:
        rh = (Su(u) - S0) / S0
        Qs.append(float(np.sum(g * P * np.abs(WT) ** 2 * np.abs(rh) ** 4 / np.maximum(np.abs(1.0 + rh) ** 2, 1e-6)) / (m.n2 * nwin)))
    return (int(stop), int(n), int(Lg), rz.tolist(), rr, Es, max(Eapp - Ebr, 0.0), us.tolist(), max(Eset, 0.0), len(Um), Qs)


def movement_bound_split(shat, M, fs, Dd, Dr, rs, p_exc=0.025):
    """Prop. 13 bound with separate specs: direct part for a distance uncertainty Dd (after re-identification:
    the u-estimate confidence half-width), reverberant part for the full displacement spec Dr (the 1-parameter
    re-identification does not observe the diffuse change, Prop. 12)."""
    bd = movement_bound(shat, M, fs, Dd, rs, p_exc=0.5)                      # Q^{-1}(0.5) = 0: direct part only
    br = movement_bound(shat, M, fs, Dr, rs, p_exc) - movement_bound(shat, M, fs, Dr, rs, p_exc=0.5)
    return bd + br


def shat_shift(sh, u, rs=0.3, fs=8000, win=8, c0=343.0, nf=4096):
    """Prop. 13 direct-path model: S(u) = S_r + S_d (rs/(rs+u)) e^{-j w u / c} (speaker-distance change u)."""
    pk = int(np.argmax(np.abs(sh))); sd = np.zeros_like(sh); lo, hi = max(0, pk - win), pk + win + 1
    sd[lo:hi] = sh[lo:hi]; sr = sh - sd
    om = 2 * np.pi * np.fft.rfftfreq(nf) * fs
    return sr + np.fft.irfft(np.fft.rfft(sd, nf) * (rs / (rs + u)) * np.exp(-1j * om * u / c0), nf)[:len(sh)]


def sid_profile(x, y, e, sh, a, b, M, grid, rs=0.3, fs=8000, lrt=None):
    """1-parameter closed-loop check of S after a change: u_hat = argmin_u min_w ||d_hat(u) + X_f(u) w||^2 on [a, b)."""
    idx = np.arange(a, b)[:, None] - np.arange(M)[None, :]
    lag = lambda z: np.where(idx >= 0, z[np.clip(idx, 0, None)], 0.0)
    best, ub, c0 = np.inf, 0.0, None
    grid = np.unique(np.append(grid, 0.0)) if lrt is not None else grid
    for u in grid:
        su = shat_shift(sh, u, rs, fs)
        dh = e[:b] - np.convolve(y[:b], su)[:b]
        Xf = lag(np.convolve(x[:b], su)[:b])
        wls = np.linalg.lstsq(Xf, dh[a:b], rcond=None)[0]
        cst = float(np.sum((dh[a:b] - Xf @ wls) ** 2))
        if abs(u) < 1e-12:
            c0 = cst
        if cst < best:
            best, ub = cst, float(u)
    if lrt is not None and c0 is not None:
        # GLR test of H0: S unchanged (u = 0); n log(J0/J1) ~ chi2_1 under H0 (residual whiteness is an approximation)
        nw = b - a
        if nw * np.log(c0 / best) < lrt:
            return 0.0
    return ub


def _sid_lg(xreg, sh, M, D, fs, win=8, c0=343.0):
    """Length of the x-lag nuisance regression. 'auto': len(S_hat) + M (absorbs any LTI difference). 'direct': only
    the u-dependent part S_d(u0) - S_d(u) (direct window +-win around the main peak, shifted by at most 1.2 D fs / c
    samples, +4 samples of fractional-delay sinc tail) convolved with an M-tap controller difference must be absorbed:
    Lg = M + peak + win + ceil(1.2 D fs / c) + 4."""
    if xreg is None:
        return None
    if xreg == 'auto':
        return len(sh) + M
    if isinstance(xreg, str) and xreg.startswith('ctrl2'):
        # z + K lags of w_bar_1 x + K lags of w_bar_2 x (+ Lx x lags for 'ctrl2<Lx>'), all common filters
        return 2 * int(int(np.argmax(np.abs(sh))) + win + int(np.ceil(1.2 * D * fs / c0)) + 5) + 1 + int(xreg[5:] or 0)
    if isinstance(xreg, str) and xreg.startswith('ctrlc'):
        # z + K y_bar lags (+ Lx x lags for 'ctrlc<Lx>')
        return int(int(np.argmax(np.abs(sh))) + win + int(np.ceil(1.2 * D * fs / c0)) + 5) + 1 + int(xreg[5:] or 0)
    if isinstance(xreg, str) and xreg.startswith('ctrl') and xreg[4:].isdigit():
        # z + K y_bar lags + K y_bar_h lags + Lx x lags ('ctrl<Lx>')
        return 2 * int(int(np.argmax(np.abs(sh))) + win + int(np.ceil(1.2 * D * fs / c0)) + 5) + 1 + int(xreg[4:])
    if xreg == 'ctrl':
        return 2 * int(int(np.argmax(np.abs(sh))) + win + int(np.ceil(1.2 * D * fs / c0)) + 5) + 1   # P = 2K + 1
    if isinstance(xreg, str) and xreg.startswith('ybar'):
        # K lags of y_bar + S_hat * y_bar (+ Lx x lags for 'ybar<Lx>', absorbing the start of r_ss)
        return int(int(np.argmax(np.abs(sh))) + win + int(np.ceil(1.2 * D * fs / c0)) + 5) + 1 + int(xreg[4:] or 0)
    if xreg == 'direct':
        return int(M + int(np.argmax(np.abs(sh))) + win + int(np.ceil(1.2 * D * fs / c0)) + 4)
    if isinstance(xreg, str) and xreg.startswith('direct+'):
        # T7 (2026-10-23): 'direct' plus extra lags (larger nuisance dimension p)
        return int(M + int(np.argmax(np.abs(sh))) + win + int(np.ceil(1.2 * D * fs / c0)) + 4) + int(xreg[7:])
    return int(xreg)


def sid_cost_xreg_fast(nw, Lg, Ls, n_eval, wchow=True, reuse=None, resid=False):
    """Flops of sid_profile2(xreg=Lg, fastchol=True) in an FFT implementation (unified FFT rule 2.5 n log2 n):
    setup: spectrum of y on the window (+ len(S) history); per half the first Gram column by FFT autocorrelation
    (2 FFTs + products) and the generalized Schur factor (18 (Lg - k) flops at step k -> 9 Lg (Lg + 1));
    per u: dh(u) (one inverse FFT of the per-bin product), per half b = X^T dh (2 FFTs), the forward solve (Lg^2) and
    two norms; residual vectors (profile / HAC sigma) only at u_hat and its two neighbours: back solve (Lg^2) and
    X beta (2 FFTs) per half; constancy test: G_full first column = sum of the halves', generalized Schur factor,
    b_full = b_1 + b_2, forward solve."""
    F = lambda n: 2.5 * n * np.log2(n)
    nf = int(2 ** np.ceil(np.log2(nw + Ls))); nh = nw // 2; nfh = int(2 ** np.ceil(np.log2(nh + Lg)))
    gs = 9.0 * Lg * (Lg + 1)
    ns, nhe = (2, 2 * n_eval) if reuse is None else reuse
    setup = 2 * F(nf) + ns * (2 * F(nfh) + 6.0 * (nfh // 2 + 1) + gs)
    per_u_conv = F(nf) + 6.0 * (nf // 2 + 1)
    per_half = 2 * F(nfh) + 6.0 * (nfh // 2 + 1) + 1.0 * Lg * Lg + 2.0 * Lg + 2.0 * nh
    res = 3 * 2 * (1.0 * Lg * Lg + 2 * F(nfh) + 6.0 * (nfh // 2 + 1) + nh) if resid else 0.0
    full = (Lg + gs + 1.0 * Lg * Lg + 2.0 * Lg + 2.0) if wchow else 0.0
    nu = n_eval if reuse is None else min(n_eval, nhe)
    nhv = 2 * n_eval if reuse is None else nhe
    return setup + nu * per_u_conv + nhv * per_half + res + full


def sid_cost_xreg(nw, Lg, Ls, n_eval, wchow=True, reuse=None):
    """Flops of an FFT/Cholesky implementation that computes exactly the quantities of sid_profile2(xreg=Lg):
    setup: spectrum of y on the window (+ len(S) history), per half the x-lag Gram matrix (FFT autocorrelation +
    edge corrections) and its Cholesky factor (Lg^3 / 3); per u: dh(u) by one inverse FFT (S(u) spectrum formed by
    per-bin products), per half b = X^T dh (2 FFTs), J = ||dh||^2 - b^T G^{-1} b (two triangular solves); misspecification
    test: Gram + Cholesky on the whole window + one more b / solve. FFT(n) = 2.5 n log2 n (unified rule)."""
    F = lambda n: 2.5 * n * np.log2(n)
    nf = int(2 ** np.ceil(np.log2(nw + Ls))); nh = nw // 2; nfh = int(2 ** np.ceil(np.log2(nh + Lg)))
    ns, nhe = (2, 2 * n_eval) if reuse is None else reuse
    setup = 2 * F(nf) + ns * (F(nfh) + 2.0 * Lg * Lg + Lg ** 3 / 3.0)
    per_u_conv = F(nf) + 6.0 * (nf // 2 + 1)                    # dh(u): needed whenever a half is new
    per_half = 2 * F(nfh) + 2.0 * Lg * Lg + 2.0 * nh
    if reuse is None:
        return setup + n_eval * (per_u_conv + 2 * per_half) + _sid_cost_full(nw, Lg, wchow)
    return setup + min(n_eval, nhe) * per_u_conv + nhe * per_half + _sid_cost_full(nw, Lg, wchow)


def sid_cost_ybar(nw, K, Ls, M, H, n_eval, wchow=True, reuse=None):
    """Flops of an FFT/Cholesky implementation of sid_profile2 with the y_bar regressors (sid_xreg='ybar'): per half
    the mean applied controller w_bar (M adds per hop), y_bar = w_bar * x on [lo - Ls - K, hi) (3 FFTs), z = S_hat * y_bar
    (1 product + 1 inverse FFT), Gram of the K + 1 regressors (FFT autocorrelation of y_bar + z column) and its Cholesky
    factor ((K+1)^3 / 3); per u and half b = X^T dh (2 FFTs + one dot) and two triangular solves. The full-window
    controller-constancy test uses the same regressors (rows of each half with its own y_bar)."""
    F = lambda n: 2.5 * n * np.log2(n)
    P = K + 1
    nf = int(2 ** np.ceil(np.log2(nw + Ls))); nh = nw // 2
    nfy = int(2 ** np.ceil(np.log2(nh + Ls + K + M))); nfh = int(2 ** np.ceil(np.log2(nh + K)))
    ns, nhe = (2, 2 * n_eval) if reuse is None else reuse
    half_setup = (nh / H + 1) * M + 3 * F(nfy) + F(nfy) + 6.0 * (nfy // 2 + 1) + 2 * F(nfh) + 2.0 * nh + 2.0 * P * P + P ** 3 / 3.0
    setup = 2 * F(nf) + ns * half_setup
    per_u_conv = F(nf) + 6.0 * (nf // 2 + 1)
    per_half = 2 * F(nfh) + 2.0 * nh + 2.0 * P * P + 2.0 * nh
    full = 0.0
    if wchow:
        full = 2.0 * P * P + P ** 3 / 3.0 + 2 * F(nfh) * 2 + 2.0 * nw + 2.0 * P * P + 2.0 * nw
    if reuse is None:
        return setup + n_eval * (per_u_conv + 2 * per_half) + full
    return setup + min(n_eval, nhe) * per_u_conv + nhe * per_half + full


def _sid_cost_full(nw, Lg, wchow):
    F = lambda n: 2.5 * n * np.log2(n)
    if not wchow:
        return 0.0
    nff = int(2 ** np.ceil(np.log2(nw + Lg)))
    return F(nff) + 2.0 * Lg * Lg + Lg ** 3 / 3.0 + 2 * F(nff) + 2.0 * Lg * Lg + 2.0 * nw


def _sid_cost_xreg_old(nw, Lg, Ls, n_eval, wchow=True):
    F = lambda n: 2.5 * n * np.log2(n)
    nf = int(2 ** np.ceil(np.log2(nw + Ls))); nh = nw // 2; nfh = int(2 ** np.ceil(np.log2(nh + Lg)))
    setup = 2 * F(nf) + 2 * (F(nfh) + 2.0 * Lg * Lg + Lg ** 3 / 3.0)
    per_u = F(nf) + 6.0 * (nf // 2 + 1) + 2 * (2 * F(nfh) + 2.0 * Lg * Lg + 2.0 * nh)
    full = 0.0
    if wchow:
        nff = int(2 ** np.ceil(np.log2(nw + Lg)))
        full = F(nff) + 2.0 * Lg * Lg + Lg ** 3 / 3.0 + 2 * F(nff) + 2.0 * Lg * Lg + 2.0 * nw
    return setup + n_eval * per_u + full


def pre_event_theta(x, y, e, sh, a, b, Lg, ret_s2=False):
    """LS estimate of the x-lag representation of the primary path from the pre-event window [a, b) (residual
    e - S_hat * y on Lg lags of x) and its residual variance (sid_sub, 2026-10-24)."""
    lo = max(a - len(sh), 0)
    dh = e[a:b] - np.convolve(y[lo:b], sh)[a - lo:b - lo]
    idx = np.arange(a, b)[:, None] - np.arange(Lg)[None, :]
    X = np.where(idx >= 0, x[np.clip(idx, 0, None)], 0.0)
    G = X.T @ X
    Gi = np.linalg.inv(G + 1e-9 * np.trace(G) / Lg * np.eye(Lg))
    th = Gi @ (X.T @ dh)
    s2 = float(np.sum((dh - X @ th) ** 2)) / max((b - a) - Lg, 1)
    if ret_s2:
        return th, s2, (b - a) - Lg                    # estimate, residual variance, its degrees of freedom
    return th, s2 * np.diag(Gi)                       # estimate and its per-tap estimation variance


def change_basis(th, sh, fs, D, cov=0.9, kind='taps', win=8, c0=343.0, vth=None, sm=16):
    """Basis of the movement-induced change of the primary path in the x-lag domain (sid_sub, 2026-10-24;
    DICHOTOMY_AND_LENGTH.md follow-up 'change-adapted subspace'). The change of a room response after a displacement
    <= D concentrates in the direct sound (delay / gain) and in the strong early part of the reverberation (Polack:
    change variance per tap ~ energy envelope x (1 - rho^2)); above f0 = c / (2 pi D) the phase changes, below it
    hardly. Columns:
      direct block: free taps [pk - win - s, pk + win + s], s = ceil(1.2 D fs / c) + 4 (delay shift + sinc tail);
      early reverberation (pk + win + s, b_r): b_r = shortest end that holds the fraction `cov` of the predicted
      change energy of the reverberant part (Polack envelope of th, rev 2 model);
        kind 'taps': free taps;  kind 'dpss': discrete prolate (Slepian) sequences of that segment for the band
        [f0, fs/2] (eigenvectors of the time-band concentration operator with eigenvalue >= 1/2; their number ~ 2 B T,
        Landau-Pollak).
    Returns (B (Lg x r_P), info dict)."""
    Lg = len(th); pk = int(np.argmax(np.abs(th))); s = int(np.ceil(1.2 * D * fs / c0)) + 4
    a_d = max(0, pk - win - s); b_d = min(Lg, pk + win + s + 1)
    # predicted change variance per tap (diagonal of the Polack covariance, polack_prior rev 2):
    #   v_n = env_n (c_b(0) + E[D^2] / 3 / r_n^2),  c_b(0) = mean over frequency of 1 - rho_1(f)^2,
    # env = local energy envelope of the reverberant part with the estimation variance of th removed
    # (E th_n^2 = P_n^2 + vth_n: the plain envelope of th has a noise floor that would spread the coverage to the
    # end of the window)
    n = np.arange(Lg)
    Pr = th.copy(); Pr[max(0, pk - win):pk + win + 1] = 0.0
    q = Pr ** 2 - (0.0 if vth is None else vth); q[max(0, pk - win):pk + win + 1] = 0.0
    env = np.clip(np.convolve(q, np.ones(sm) / sm, mode='same'), 0.0, None)
    nD = 64; Dg = D * (np.arange(nD) + 0.5) / nD; wD = 3 * Dg ** 2; wD = wD / wD.sum()
    om = 2 * np.pi * np.fft.fftfreq(4 * Lg) * fs
    r1 = np.sinc(np.outer(np.abs(om), Dg) / c0 / np.pi) @ wD
    cb0 = float(np.mean(1.0 - r1 ** 2))
    rn = c0 * np.maximum(n - int(np.argmax(np.abs(sh))), 1) / fs
    v = env * (cb0 + 0.6 * D ** 2 / 3.0 / rn ** 2); vr = v[b_d:]
    tot = float(vr.sum())
    if tot <= 0 or b_d >= Lg:
        b_r = b_d
    else:
        cs = np.cumsum(vr) / tot
        b_r = b_d + int(np.searchsorted(cs, float(cov))) + 1
    b_r = min(b_r, Lg)
    cols = [np.eye(Lg)[:, a_d:b_d]]
    Tr = b_r - b_d
    nsl = Tr
    if Tr > 0:
        if kind == 'dpss':
            f0 = c0 / (2 * np.pi * D); wc = f0 / fs                   # normalized cutoff (cycles / sample)
            k = np.arange(Tr)[:, None] - np.arange(Tr)[None, :]
            low = np.where(k == 0, 2 * wc, np.sin(2 * np.pi * wc * k) / (np.pi * np.where(k == 0, 1, k)))
            A = np.eye(Tr) - low                                       # concentration on [f0, fs/2]
            lam, V = np.linalg.eigh((A + A.T) / 2)
            V = V[:, lam >= 0.5]; nsl = V.shape[1]
            E = np.zeros((Lg, nsl)); E[b_d:b_r] = V
            cols.append(E)
        else:
            cols.append(np.eye(Lg)[:, b_d:b_r])
    B = np.hstack(cols)
    return B, {'pk': pk, 'a_d': a_d, 'b_d': b_d, 'b_r': b_r, 'r_dir': b_d - a_d, 'r_rev': nsl, 'r_P': B.shape[1]}


class _SubReg:
    """Regressors of the subspace nuisance (sid_sub): [x * b_j (change basis of the primary path), lags 0..K-1 of the
    half's mean anti-noise y_bar = w_bar * x (absorbs the u-dependent LTI part (S_hat - S_hat(u)) y_bar of the direct
    window)]; the primary path itself enters as the known offset x * theta_bar (pre-event estimate), removed from e."""

    def __init__(self, xb, x, wlog, H, K):
        self.xb, self.x, self.wl, self.H, self.K = xb, x, wlog, H, int(K)

    def __call__(self, lo, hi):
        H = self.H
        ks = np.arange(lo // H, (hi - 1) // H + 1)
        c = np.minimum((ks + 1) * H, hi) - np.maximum(ks * H, lo)
        wb = np.tensordot(c / c.sum(), np.array([self.wl[k] for k in ks]), axes=1)
        a0 = max(lo - len(wb) - self.K, 0)
        yb = np.zeros(hi); yb[a0:hi] = np.convolve(self.x[a0:hi], wb)[:hi - a0]
        idx = np.arange(lo, hi)[:, None] - np.arange(self.K)[None, :]
        return np.hstack([self.xb[lo:hi], np.where(idx >= 0, yb[np.clip(idx, 0, None)], 0.0)])


def _ybar_reg(x, wlog, sh, H, K, Lx=0):
    """Regressor builder of the y_bar parameterization: (lo, hi) -> [S_hat * y_bar, y_bar lags 0..K-1] on [lo, hi),
    w_bar = sample-weighted mean of the controllers applied in [lo, hi) (wlog[k] = controller of hop k)."""
    def f(lo, hi):
        ks = np.arange(lo // H, (hi - 1) // H + 1)
        c = np.minimum((ks + 1) * H, hi) - np.maximum(ks * H, lo)
        wb = np.tensordot(c / c.sum(), np.array([wlog[k] for k in ks]), axes=1)
        yb = np.convolve(x[:hi], wb)[:hi]
        z = np.convolve(yb, sh)[:hi]
        idx = np.arange(lo, hi)[:, None] - np.arange(K)[None, :]
        cols = [z[lo:hi, None], np.where(idx >= 0, yb[np.clip(idx, 0, None)], 0.0)]
        if Lx:
            ix = np.arange(lo, hi)[:, None] - np.arange(Lx)[None, :]
            cols.append(np.where(ix >= 0, x[np.clip(ix, 0, None)], 0.0))
        return np.hstack(cols)
    return f


class _CtrlReg:
    """Controller-based nuisance regressors (sid_xreg='ctrl').
    With w* the current controller (LS fit of d_hat on M lags of x_f = S_hat x), w_bar the mean applied controller of
    the check window and w_bar_h that of half h:
        z = S_hat * w* * x                 (absorbs d + Delta_0 y_bar: the LTI part of d_hat, near-optimal M-tap fit)
        y_bar lags 0..K-1, y_bar = w_bar * x (common LTI filter: absorbs the d_hat mismatch of the window average)
        y_bar_h lags 0..K-1, y_bar_h = w_bar_h * x (absorbs (S - S(u)) y_bar_h, the u-dependent LTI part in half h)
    All regressors are u-independent; the first 1 + K are the SAME LTI filters of x in both halves, so under
    'P, S constant on the window' their coefficients are common -> the controller-constancy test is the F test of
    common vs per-half coefficients of these 1 + K columns (the y_bar_h-lag coefficients stay free per half).
    P = 2K + 1 columns instead of Lg ~ M + K x lags."""

    def __init__(self, x, wlog, sh, H, K, wstar, a, b, halfspec=True, Lx=0, two=False):
        self.x, self.sh, self.H, self.K, self.hs, self.Lx = x, sh, H, int(K), bool(halfspec), int(Lx)
        self.wl = wlog
        self.z = np.convolve(np.convolve(x[:b], sh)[:b], wstar)[:b]
        self.two = bool(two)
        if self.two:
            # 'ctrl2': lags of w_bar_1 * x and w_bar_2 * x over the WHOLE window (same filters in both halves)
            h = a + (b - a) // 2
            self.yb1, self.yb2 = self._wbar_filt(a, h, b), self._wbar_filt(h, b, b)
            self.hs = False
        else:
            self.yb = self._ybar(a, b, b)

    def _wbar_filt(self, lo, hi, b):
        H = self.H
        ks = np.arange(lo // H, (hi - 1) // H + 1)
        c = np.minimum((ks + 1) * H, hi) - np.maximum(ks * H, lo)
        wb = np.tensordot(c / c.sum(), np.array([self.wl[k] for k in ks]), axes=1)
        return np.convolve(self.x[:b], wb)[:b]

    def _ybar(self, lo, hi, b):
        H = self.H
        ks = np.arange(lo // H, (hi - 1) // H + 1)
        c = np.minimum((ks + 1) * H, hi) - np.maximum(ks * H, lo)
        wb = np.tensordot(c / c.sum(), np.array([self.wl[k] for k in ks]), axes=1)
        return np.convolve(self.x[:b], wb)[:b]

    def _lags(self, v, lo, hi):
        idx = np.arange(lo, hi)[:, None] - np.arange(self.K)[None, :]
        return np.where(idx >= 0, v[np.clip(idx, 0, None)], 0.0)

    def __call__(self, lo, hi):
        c = self._com(lo, hi)
        if not self.hs:
            return c
        return np.hstack([c, self._lags(self._ybar(lo, hi, hi), lo, hi)])

    def _com(self, lo, hi):
        if self.two:
            c = [self.z[lo:hi, None], self._lags(self.yb1, lo, hi), self._lags(self.yb2, lo, hi)]
        else:
            c = [self.z[lo:hi, None], self._lags(self.yb, lo, hi)]
        if self.Lx:
            ix = np.arange(lo, hi)[:, None] - np.arange(self.Lx)[None, :]
            c.append(np.where(ix >= 0, self.x[np.clip(ix, 0, None)], 0.0))
        return np.hstack(c)

    def common(self, halves):
        if not self.hs:
            # 'ctrlc': only common columns; (S - S(u)) (w_bar_h - w_bar) x is left to the identifying signal
            return np.vstack([self(lo, hi) for lo, hi in halves]), (1 + 2 * self.K + self.Lx) if self.two else (1 + self.K + self.Lx)
        Zc = np.vstack([self._com(lo, hi) for lo, hi in halves])
        Bh = [self._lags(self._ybar(lo, hi, hi), lo, hi) for lo, hi in halves]
        n1 = len(Bh[0])
        Zh = np.zeros((len(Zc), 2 * self.K)); Zh[:n1, :self.K] = Bh[0]; Zh[n1:, self.K:] = Bh[1]
        return np.hstack([Zc, Zh]), 1 + self.K + self.Lx


def sid_cost_ctrl(nw, P, Ls, M, H, n_eval, wchow=True):
    """Flops of an FFT/Cholesky implementation of sid_profile2 with the _CtrlReg regressors (P = 2K + 1): w_bar,
    w_bar_1, w_bar_2 (M adds per hop each), y_bar, y_bar_1, y_bar_2 and z = S_hat w* x by FFT (x spectrum shared),
    per half the Gram of P columns (FFT auto/cross-correlations of the three signals + edge corrections) and its
    Cholesky factor; per u: dh(u) (1 inverse FFT), per half b = Z^T dh (3 FFTs + dot) and two triangular solves;
    constancy test: Gram of the restricted model from the half blocks + Cholesky + solve."""
    F = lambda n: 2.5 * n * np.log2(n)
    nf = int(2 ** np.ceil(np.log2(nw + Ls))); nh = nw // 2
    nfy = int(2 ** np.ceil(np.log2(nw + Ls + M))); nfh = int(2 ** np.ceil(np.log2(nh + P)))
    # (counted for the largest variant: three y_bar signals; Gram blocks by FFT auto/cross-correlations of up to
    # four signals; restricted model of the constancy test with up to P + P/2 columns)
    setup = 2 * F(nf) + 3 * (nw / H + 2) * M + F(nfy) + 3 * 2 * F(nfy) + 2 * F(nfy) + 6.0 * (nfy // 2 + 1) * 4
    setup += 2 * (10 * F(nfh) + 2.0 * nh + 4.0 * P * P + P ** 3 / 3.0)
    per_u = F(nf) + 6.0 * (nf // 2 + 1) + 2 * (4 * F(nfh) + 4.0 * nh + 2.0 * P * P)
    Pc = 1.5 * P
    full = (4.0 * Pc * Pc + Pc ** 3 / 3.0 + 2.0 * Pc * Pc + 2.0 * nw) if wchow else 0.0
    return setup + n_eval * per_u + full


def gschur_chol(x, lo, hi, L):
    """Exact Cholesky factor of the lag Gram G = X^T X of the data window [lo, hi) (X[t, k] = x[t - k], zero before
    t = 0) by the generalized Schur algorithm (Kailath & Sayed): G - Z G Z^T = p p^T + a a^T - q q^T - c c^T with
    p = G[:, 0] / sqrt(G00), q = p - sqrt(G00) e_0, a_i = x[lo - i], c_i = x[hi - i] (i >= 1), i.e. displacement rank
    4 with signature (2, 2). Each step: two Givens rotations (positive / negative block) and one hyperbolic rotation
    (mixed form) bring the active generator row to [l_kk, 0, 0, 0]; column 0 is the k-th Cholesky column, then shifted
    by Z. 18 (L - k) flops per step -> 9 L^2 in total instead of L^3 / 3. Returns lower-triangular L."""
    xp = lambda t: np.where(t >= 0, x[np.clip(t, 0, None)], 0.0)
    i = np.arange(L); seg = xp(np.arange(lo, hi))
    g = np.array([seg @ xp(np.arange(lo, hi) - k) for k in range(L)])     # first Gram column (FFT in the cost)
    s0 = np.sqrt(g[0]); p = g / s0; q = p.copy(); q[0] = 0.0
    a_ = xp(lo - i); a_[0] = 0.0; c_ = xp(hi - i); c_[0] = 0.0
    Gn = np.stack([p, a_, q, c_], 1)
    Lf = np.zeros((L, L))
    for k in range(L):
        V = Gn[k:]
        for j0, j1 in ((0, 1), (2, 3)):
            r = np.hypot(V[0, j0], V[0, j1])
            if r > 0:
                cs, sn = V[0, j0] / r, V[0, j1] / r
                V[:, j0], V[:, j1] = cs * V[:, j0] + sn * V[:, j1], -sn * V[:, j0] + cs * V[:, j1]
        rho = V[0, 2] / V[0, 0]
        if not abs(rho) < 1.0:
            raise np.linalg.LinAlgError('gschur_chol: Gram matrix not positive definite')
        sq = np.sqrt(1.0 - rho * rho)
        n0 = (V[:, 0] - rho * V[:, 2]) / sq
        V[:, 2] = V[:, 2] * sq - rho * n0
        V[:, 0] = -n0 if n0[0] < 0 else n0
        Lf[k:, k] = V[:, 0]
        V[1:, 0] = V[:-1, 0].copy()
    return Lf


def _prior_members(prior):
    """(O, D) of _PriorFit from a prior tuple (theta_bar, Lam, fam, exact, s2, rev, Pr_mean):
    no family -> O = theta_bar; rev 1 -> O = full members theta_bar(u_p); rev 2 -> O = reverberant mean, D = direct
    family P_d(u_p) (gain profiled)."""
    fam = prior[2] if len(prior) > 2 else None
    rev = int(prior[5]) if (len(prior) > 5 and prior[5]) else 1
    if fam is None:
        return np.asarray(prior[0])[None, :], None
    if rev >= 2:
        return np.asarray(prior[6])[None, :], np.asarray(fam)
    return np.asarray(fam), None


class _PriorFit:
    """Marginal residual under the nuisance prior on one window (sid_prior; review 2026-10-24):
    J(member) = r^T (I + X Sigma X^T / s2)^-1 r = ||r||^2 - ||L^-1 X^T r||^2, r = d_hat - X theta, L = chol(G + Lam),
    over the prior-mean members theta = O_m (fixed offsets) or theta = O_0 + g D_j (rev 2: direct-part delay on a grid
    D_j, its gain g profiled in closed form: J = J0 - c_j^2 / q_j, g_j = c_j / q_j).
    Everything except b = X^T d_hat is precomputed, so one u costs one triangular solve (L^2) + O(L n_members)."""

    def __init__(self, X, Lam, O, D=None, G=None):
        from scipy.linalg import solve_triangular as _st
        self._st = _st
        self.X = X; self.G = X.T @ X if G is None else G
        self.L = np.linalg.cholesky(self.G + Lam)
        self.O = np.atleast_2d(O); self.GO = self.O @ self.G
        self.ZO = _st(self.L, self.GO.T, lower=True); self.OGO = np.sum(self.O * self.GO, 1)
        self.D = None if D is None else np.atleast_2d(D)
        if self.D is not None:
            self.GD = self.D @ self.G; self.ZD = _st(self.L, self.GD.T, lower=True)
            self.q = np.sum(self.D * self.GD, 1) - np.sum(self.ZD ** 2, 0)
            self.OGD = self.GD @ self.O[0]

    def J(self, b, dd):
        """min over members; returns (J, member) with member = (m, g)."""
        z = self._st(self.L, b, lower=True)
        r2 = dd - 2.0 * (self.O @ b) + self.OGO
        zr = z[:, None] - self.ZO
        J0 = r2 - np.sum(zr ** 2, 0)
        if self.D is None:
            m = int(np.argmin(J0)); return float(J0[m]), (m, 0.0)
        c = self.D @ b - self.OGD - zr[:, 0] @ self.ZD
        q = np.maximum(self.q, 1e-300)
        Jg = J0[0] - c ** 2 / q
        m = int(np.argmin(Jg)); return float(Jg[m]), (m, float(c[m] / q[m]))

    def theta(self, member):
        m, g = member
        return self.O[0] + g * self.D[m] if self.D is not None else self.O[m]

    def J_at(self, b, dd, member):
        """J at a fixed member (no profiling)."""
        m, g = member
        z = self._st(self.L, b, lower=True)
        if self.D is None:
            go, zo, ogo, o = self.GO[m], self.ZO[:, m], self.OGO[m], self.O[m]
        else:
            o = self.O[0] + g * self.D[m]; go = self.GO[0] + g * self.GD[m]; zo = self.ZO[:, 0] + g * self.ZD[:, m]
            ogo = self.OGO[0] + 2.0 * g * self.OGD[m] + g * g * float(self.D[m] @ self.GD[m])
        zr = z - zo
        return float(dd - 2.0 * (o @ b) + ogo - zr @ zr)

    def resid(self, dh_w, b, member):
        o = self.theta(member); s = dh_w - self.X @ o
        bs = b - self.G @ o
        return s - self.X @ self._st(self.L.T, self._st(self.L, bs, lower=True), lower=False)


def sid_cost_prior(nw, L, Ls, n_eval, n_o, n_d, wchow=True, exact=True, resid=True, rev=1, n_sig=None):
    """Flops of one prior-based check (sid_prior; review R3, 2026-10-24), same FFT rule as sid_cost_xreg_fast
    (2.5 n log2 n); dense parts counted as implemented: per half Gram (FFT autocorrelation + L^2 fill), Cholesky of
    G + Lam (L^3 / 3, Lam dense), precomputation of the members (3 L^2 per member); per u: d_hat (FFT), per half
    b = X^T d_hat (FFT), one triangular solve (L^2) and 4 L per member; residuals at u_hat and its neighbours; constancy
    test: common Cholesky, members, (rev 2: all evaluated u), fixed-member halves, G_i (G_i + Lam)^-1 (2 L^3 per half),
    product (2 L^3), eigenvalues (10 L^3), Imhof quadrature (5 n_sig per node, 4000 nodes); non-exact: d_eff per half (L^3)."""
    F = lambda n: 2.5 * n * np.log2(n)
    nf = int(2 ** np.ceil(np.log2(nw + Ls))); nh = nw // 2; nfh = int(2 ** np.ceil(np.log2(nh + L)))
    nm = n_o + n_d
    setup = 2 * F(nf) + 2 * (2 * F(nfh) + L * L + L ** 3 / 3.0 + 3.0 * L * L * nm + (0.0 if exact else L ** 3))
    per_u = F(nf) + 6.0 * (nf // 2 + 1) + 2 * (2 * F(nfh) + 6.0 * (nfh // 2 + 1) + L * L + 4.0 * L * nm + 2.0 * nh)
    res = 3 * 2 * (2.0 * L * L + 2 * F(nfh) + 2.0 * nh) if resid else 0.0
    full = 0.0
    if wchow:
        n_c = n_eval if rev >= 2 else 1
        full = L * L + L ** 3 / 3.0 + 3.0 * L * L * nm + n_c * (L * L + 4.0 * L * nm) + 2 * 3.0 * L * L
        if exact:
            full += 2 * 2.0 * L ** 3 + 2.0 * L ** 3 + 10.0 * L ** 3 + 4000 * 5.0 * (n_sig or L)
        else:
            full += L ** 3
    return setup + n_eval * per_u + res + full


def sid_cost_prior_build(n0, L, n_up, model='field'):
    """Flops of the prior construction at an event (review R3): LS fit of the pre-event path (FFT Gram + Cholesky +
    solve), inverse Gram for the estimation covariance (L^3), circulant / Polack covariance (2 L^3 dense product),
    Sigma^-1 (L^3), d_eff at the event (L^3), u_p family (one 4096-point FFT pair per member)."""
    F = lambda n: 2.5 * n * np.log2(n)
    nf = int(2 ** np.ceil(np.log2(n0 + L)))
    return 4 * F(nf) + L * L + L ** 3 / 3.0 + 2.0 * L * L + L ** 3 + 2.0 * L ** 3 + L ** 3 + L ** 3 + n_up * 2 * F(4096)


def gchi_pm_chi_sf(x, sg, k=0, tol=1e-13):
    """P(Q > x) for Q = sum_j sg_j (a_j^2 - b_j^2) + chi2_k (independent), a, b iid N(0,1) (review R5 / R6, rev 2: the
    per-half profiled scalars u_p and gain add k unit eigenvalues). Imhof (1961):
    P(Q > x) = 1/2 + (1/pi) int_0^inf sin(theta(v)) / (v rho(v)) dv, theta = (k/2) atan(v) - x v / 2,
    rho = prod_j (1 + sg_j^2 v^2)^(1/2) (1 + v^2)^(k/4). k = 0 is gchi_pm_sf."""
    if k == 0:
        return gchi_pm_sf(x, sg, tol)
    sg = np.asarray(sg, float); sg = sg[sg > 0]
    lenv = lambda v: (-0.5 * np.sum(np.log1p((sg[None, :] * np.atleast_1d(v)[:, None]) ** 2), 1)
                      - 0.25 * k * np.log1p(np.atleast_1d(v) ** 2))
    lo, hi = 0.0, 1.0
    while lenv(hi)[0] - np.log(hi) > np.log(tol):
        hi *= 2.0
    for _ in range(60):
        mid = 0.5 * (lo + hi)
        if lenv(mid)[0] - np.log(mid) > np.log(tol): lo = mid
        else: hi = mid
    vmax = hi
    N = int(min(max(4000, 40 * (abs(x) + k) * vmax / (4 * np.pi)), 400000))
    v = np.linspace(vmax / N * 1e-3, vmax, N)
    f = np.sin(0.5 * k * np.arctan(v) - 0.5 * x * v) / v * np.exp(lenv(v))
    I = np.trapezoid(f, v) + 0.5 * (k - x) * v[0]
    return float(np.clip(0.5 + I / np.pi, 0.0, 1.0))


def gchi_pm_sf(x, sg, tol=1e-13):
    """P(Q > x) for Q = sum_j sg_j (a_j^2 - b_j^2), a, b iid N(0,1) (sid_prior_exact). Imhof (1961) with the +-sg pairs:
    P(Q > x) = 1/2 - (1/pi) int_0^inf sin(x v / 2) / v * prod_j (1 + sg_j^2 v^2)^(-1/2) dv.
    The integrand envelope is integrated on [0, v_max] (envelope < tol beyond v_max), trapezoid on a grid resolving
    both the oscillation (period 4 pi / |x|) and the envelope."""
    sg = np.asarray(sg, float); sg = sg[sg > 0]
    if len(sg) == 0:
        return 1.0 if x <= 0 else 0.0
    env = lambda v: -0.5 * np.sum(np.log1p((sg[None, :] * np.atleast_1d(v)[:, None]) ** 2), 1)
    lo, hi = 0.0, 1.0
    while env(hi)[0] > np.log(tol):
        hi *= 2.0
    for _ in range(60):
        mid = 0.5 * (lo + hi)
        if env(mid)[0] > np.log(tol): lo = mid
        else: hi = mid
    vmax = hi
    nper = abs(x) * vmax / (4 * np.pi)
    N = int(min(max(4000, 40 * nper), 400000))
    v = np.linspace(vmax / N * 1e-3, vmax, N)
    f = np.sin(x * v / 2.0) / v * np.exp(env(v))
    I = np.trapezoid(f, v) + 0.5 * x * v[0]               # [0, v0] part: sin(x v/2)/v -> x/2
    return float(np.clip(0.5 - I / np.pi, 0.0, 1.0))


def sid_profile2(x, y, e, sh, a, b, M, grid, rs=0.3, fs=8000, lrt=None, chow=None, edge=False, c2f=None, wchow=None, xreg=None,
                 sig='crb', hac_lags=128, cache=None, yreg=None, fastchol=False, ci_alpha=0.05, chow_alpha=None, ci_mix=None,
                 vpower=None, bias_s2=None, gof=None, prior=None, s2ref=None):
    """Variant of sid_profile (new flags; sid_profile itself is unchanged).
    The window [a, b) is split into two halves; the controller w is fitted separately per half (P may change while a
    source still moves), the speaker-distance change u is common:  J(u) = J_1(u) + J_2(u),  u_hat = argmin J.
      chow : Chow-type test of H0 'u constant over the window' vs H1 'u_1 != u_2' (1 extra parameter):
             F = (min_u J(u) - (min J_1 + min J_2)) / ((min J_1 + min J_2) / dof) ~ F(1, dof) under H0; rejected ->
             model violated (S still moving)
      edge : reject u_hat on the boundary of the grid (movement beyond the search range or model violated)
      lrt  : test of 'S unchanged' (u = 0) on J, F form: (J(0) - J(u_hat)) / (J(u_hat) / dof) ~ F(1, dof)
      c2f  : coarse step (m); evaluate the coarse grid, then refine on the fine grid within +-c2f of the coarse minimum
      wchow: level of a misspecification test at u_hat (finite-sample Chow F-test of a common controller over the
             two halves): F = ((J_common - J) / M) / (J / (n - 2M - 1)) ~ F(M, n - 2M - 1) under 'P and S constant on
             the window and S = S(u_hat)' (Gaussian white residual); rejected -> P or S still changing / S outside
             the 1-parameter family -> no decision
      xreg : int Lg -> 'primary' parameterization (as in Hu, Xue, Lu): the nuisance LTI part is regressed on Lg
             lags of x (u-independent regressors), not on x_f(u) = S(u) * x. With x_f(u) the regressors depend on u and
             an advanced S(u) can explain the non-causally-controllable part of d (bias towards u < 0 when S is
             non-minimum-phase or the causality margin is small; observed on the random-decay plant). With Lg >=
             len(S_hat) + M the LTI part (S - S(u)) * w_bar * x is absorbed exactly, so only y~ identifies u.
             The controller-constancy test then has Lg instead of M parameters.
      sig  : 'crb' (default): sigma_u^2 = 2 sigma^2 / J''(u_hat) (white residual); 'hac': sandwich (Newey-West)
             variance of the M-estimator u_hat, Var = sum_k w_k sum_t s_t s_{t+k} / (sum_t g_t^2)^2 with
             s_t = r_t g_t, r the residual at u_hat, g = d r / d u (central difference on the fine grid), Bartlett
             weights w_k = 1 - |k|/(K+1), K = hac_lags; lower-bounded by the half-split estimate |u_1 - u_2| / 2
             (two independent half-window estimates; captures model mismatch). 'crb' is kept in info['sig_u_crb'].
      cache: dict kept across checks (xreg path only): per half-window [lo, hi) the factorization and the per-u
             J values and residuals are stored; a retry whose first half equals the previous check's second half
             (window shifted by T/2) reuses them exactly. info['reuse'] = (new half setups, new half evaluations).
      ci_mix: (alpha, tau) -> time-uniform (anytime-valid) threshold of the normal-mixture boundary instead of the
             fixed-level F quantile (v6 prototype): with V = J''(u_hat) / (2 J(u_hat)/dof) the standardized information
             and a N(0, tau^2) mixing prior on u, the set {Lambda(u) <= (1 + 1/(V tau^2)) (2 log(1/alpha) + log(1 + V tau^2))}
             (Robbins normal mixture, 1-D; Abbasi-Yadkori et al. 2011 form), Lambda = (J(u) - J(u_hat)) / (kappa J/dof).
      ci_alpha: level of the profile confidence set (sig='profile'); chow_alpha: if given, the u-constancy test uses the
             F(1, dof - 1) quantile at this level instead of the fixed threshold `chow` (R1 of PARAMETERS_v4.md).
      fastchol: (xreg x-lag path only) J from the exact Cholesky factor of the lag Gram computed by the generalized
             Schur algorithm (gschur_chol, O(Lg^2)) instead of a QR: J = ||dh||^2 - ||L^{-1} X^T dh||^2; the full-window
             factor of the constancy test uses G_full = G_1 + G_2 and b_full = b_1 + b_2. Same quantities as the QR
             path up to rounding.
      yreg : callable (lo, hi) -> regressor matrix (n x P) replacing the x lags (xreg must then be the column count
             P). Used for the y_bar parameterization (sid_xreg='ybar'): with w_bar the mean applied controller of the
             half, y_bar = w_bar * x and r_ss = d + S y_bar (steady residual): d + (S - S(u)) y_bar = r_ss - S(u) y_bar,
             and S(u) = S_hat + (direct-window change), so this lies in span{S_hat * y_bar, y_bar lags 0..K-1} + r_ss
             (K covers the direct window + the shift). K + 1 ~ 40 regressors replace Lg ~ 320 x lags; r_ss is left as
             noise (its cross term with (S - S(u))(y - y_bar) has zero mean because y - y_bar has zero mean per half);
             u is identified by the time-varying part y - y_bar as before.
    Returns (u_hat or None if rejected, info dict, number of evaluated u values)."""
    h = a + (b - a) // 2
    RES = {}
    halves = ((a, h), (h, b))
    J1, J2 = {}, {}
    new_setups = 0; new_half_evals = [0]
    if xreg is not None:
        Mr = int(xreg)
        _prev = int(prior[5]) if (prior is not None and len(prior) > 5 and prior[5]) else 1
        if prior is not None and len(prior[0]) != Mr:
            prior = None                                   # prior built for another nuisance length (S_hat changed): flat
        Qs = []; HC = []
        skey = hash(np.asarray(sh, float).tobytes())
        for lo, hi in halves:
            key = (lo, hi, Mr, skey, rs, yreg is not None, bool(fastchol))
            if cache is not None and key in cache and prior is None:   # review R2: key has no prior -> no reuse with a prior
                hc = cache[key]
            else:
                if yreg is not None:
                    Xx = yreg(lo, hi)
                else:
                    idx = np.arange(lo, hi)[:, None] - np.arange(Mr)[None, :]
                    Xx = np.where(idx >= 0, x[np.clip(idx, 0, None)], 0.0)
                if prior is not None and yreg is None:
                    # sid_prior (Theorem A'): Bayesian nuisance N(theta_bar, Sigma): J(u) = r^T (I + X Sigma X^T / s2)^-1 r,
                    # r = d_hat(u) - X theta_bar = ||r||^2 - b^T (G + Lam)^-1 b (Woodbury), Lam = s2 Sigma^-1 (_PriorFit)
                    _fit = _PriorFit(Xx, prior[1], *_prior_members(prior))
                    hc = {'X': Xx, 'L': _fit.L, 'fit': _fit, 'J': {}, 'R': {}, 'B': {}, 'Braw': {}, 'dd': {}, 'mem': {}}
                    if not (len(prior) > 3 and prior[3]):
                        # effective dimension (only the non-exact variant uses it, as residual dof)
                        hc['deff'] = float(np.trace(np.linalg.solve(_fit.L.T, np.linalg.solve(_fit.L, _fit.G))))
                elif fastchol and yreg is None:
                    hc = {'X': Xx, 'L': gschur_chol(x, lo, hi, Mr), 'J': {}, 'R': {}, 'B': {}}
                else:
                    hc = {'Q': np.linalg.qr(Xx)[0], 'J': {}, 'R': {}}
                new_setups += 1
                if cache is not None and prior is None:
                    cache[key] = hc
            Qs.append(hc.get('Q')); HC.append(hc)
    else:
        Mr = M
        lags = [np.arange(lo, hi)[:, None] - np.arange(M)[None, :] for lo, hi in halves]

    def ev(u):
        u = float(np.round(u, 6))
        if u in J1:
            return
        out = []
        rr = []
        if xreg is not None:
            dh = None
            for Q, hc, (lo, hi) in zip(Qs, HC, halves):
                if u in hc['J']:
                    out.append(hc['J'][u]); rr.append(hc['R'].get(u)); continue
                if dh is None:
                    su = shat_shift(sh, u, rs, fs)
                    dh = e[:b] - np.convolve(y[:b], su)[:b]
                if 'fit' in hc:
                    # prior path: profile over the prior-mean members (u_p grid; rev 2 also the direct gain)
                    _dw = dh[lo:hi]; _b = hc['X'].T @ _dw; _dd = float(_dw @ _dw)
                    _Jm, _mem = hc['fit'].J(_b, _dd)
                    hc['Braw'][u] = _b; hc['dd'][u] = _dd; hc['mem'][u] = _mem
                    out.append(_Jm); new_half_evals[0] += 1
                    r_ = hc['fit'].resid(_dw, _b, _mem) if sig in ('hac', 'profile') else None
                    rr.append(r_); hc['J'][u] = _Jm
                    if r_ is not None:
                        hc['R'][u] = r_
                    continue
                if 'L' in hc:
                    from scipy.linalg import solve_triangular as _st
                    sg = dh[lo:hi]
                    bb = hc['X'].T @ sg; zz = _st(hc['L'], bb, lower=True)
                    hc['B'][u] = bb
                    out.append(float(sg @ sg - zz @ zz)); new_half_evals[0] += 1
                    r_ = None
                    if sig in ('hac', 'profile'):
                        r_ = sg - hc['X'] @ _st(hc['L'].T, zz, lower=False)
                    rr.append(r_)
                    hc['J'][u] = out[-1]
                    if r_ is not None:
                        hc['R'][u] = r_
                    continue
                r_ = dh[lo:hi] - Q @ (Q.T @ dh[lo:hi])
                out.append(float(r_ @ r_)); rr.append(r_); new_half_evals[0] += 1
                hc['J'][u] = out[-1]
                if sig in ('hac', 'profile'):
                    hc['R'][u] = r_
        else:
            su = shat_shift(sh, u, rs, fs)
            dh = e[:b] - np.convolve(y[:b], su)[:b]
            xf = np.convolve(x[:b], su)[:b]
            for idx, (lo, hi) in zip(lags, halves):
                Xf = np.where(idx >= 0, xf[np.clip(idx, 0, None)], 0.0)
                wls = np.linalg.lstsq(Xf, dh[lo:hi], rcond=None)[0]
                r_ = dh[lo:hi] - Xf @ wls
                out.append(float(r_ @ r_)); rr.append(r_)
        J1[u], J2[u] = out
        if sig in ('hac', 'profile'):
            RES[u] = np.concatenate(rr)

    grid = np.round(np.asarray(grid, float), 6)
    if c2f is not None:
        co = grid[::max(1, int(round(float(c2f) / float(grid[1] - grid[0]))))]
        co = np.unique(np.concatenate([co, grid[[0, -1]], [0.0] if lrt is not None else []]))
        for u in co:
            ev(u)
        uc = min(J1, key=lambda u: J1[u] + J2[u])
        for u in grid[np.abs(grid - uc) <= float(c2f) + 1e-9]:
            ev(u)
    else:
        for u in grid:
            ev(u)
        if lrt is not None:
            ev(0.0)
    us = np.array(sorted(J1)); Jt = np.array([J1[u] + J2[u] for u in us])
    i = int(np.argmin(Jt)); ub = float(us[i]); nw = b - a
    # residual degrees of freedom: 2 Mr for the flat nuisance, sum of the per-half effective dimensions with a prior
    Mdof2 = (float(sum(hc['deff'] for hc in HC)) if (xreg is not None and prior is not None and HC and 'deff' in HC[0]) else 2 * Mr)
    _pex = bool(prior is not None and len(prior) > 3 and prior[3] and xreg is not None and HC and 'fit' in HC[0])
    if _pex:
        # sid_prior_exact: under the prior the marginal residual J_i(u) = r^T (I + X Sigma X^T/s2)^-1 r has E = s2 n_i exactly,
        # so only the profiled scalars cost degrees of freedom (u_p per half in the joint model; u is the extra 1 below)
        # profiled scalars per half: u_p (joint), + the direct gain (rev 2)
        Mdof2 = (4.0 if _prev >= 2 else 2.0) if (len(prior) > 2 and prior[2] is not None) else 0.0
    # review 2026-10-24 (R1): under sid_prior_exact every statistic uses the noise variance of the prior model (pre-event
    # estimate) when it is given; J(u_hat)/dof is biased (x0.5 .. x5 observed) when the prior is misspecified
    _s2ref = float(prior[4]) if (_pex and len(prior) > 4 and prior[4] is not None) else None
    # sid_s2pre (2026-10-24, THEORY_CLOSURE.md sec. 3): noise variance from a pre-event window (independent of this
    # window, s2ref = (s2, dof_ref)): every statistic is calibrated by it and its F laws use dof_ref as denominator
    # degrees of freedom; the check window then only needs n > 2 Lg (Theorem A floor) instead of the in-window dof
    _dref = None
    if s2ref is not None and prior is None:
        _s2ref = float(s2ref[0]); _dref = int(s2ref[1])
    _s2of = (lambda J_, d_: _s2ref) if _s2ref is not None else (lambda J_, d_: J_ / max(d_, 1))
    info = {'u': ub, 'chow': None, 'lrt': None, 'edge': bool(abs(ub) >= float(np.max(np.abs(grid))) - 1e-9), 'sig_u': None,
            'reuse': (new_setups, new_half_evals[0])}
    # local Cramer-Rao-type std of u_hat from the profile curvature: Var(u_hat) ~ 2 sigma^2 / J''(u_hat),
    # sigma^2 = J(u_hat) / dof (white-residual approximation); needs both fine-grid neighbours
    if 0 < i < len(us) - 1 and np.isclose(us[i + 1] - us[i], us[i] - us[i - 1]):
        hh = float(us[i + 1] - us[i]); J2c = (Jt[i + 1] - 2 * Jt[i] + Jt[i - 1]) / hh ** 2
        if J2c > 0:
            info['sig_u'] = float(np.sqrt(2.0 * _s2of(Jt[i], nw - Mdof2 - 1) / J2c))
        info['sig_u_crb'] = info['sig_u']
        if sig in ('hac', 'profile') and info['sig_u'] is not None:
            r0 = RES[float(us[i])]; g = (RES[float(us[i + 1])] - RES[float(us[i - 1])]) / (2 * hh)
            st = r0 * g; A = float(g @ g); K = int(hac_lags)
            V = float(st @ st) + 2.0 * sum((1.0 - k / (K + 1.0)) * float(st[k:] @ st[:-k]) for k in range(1, min(K, len(st) - 1) + 1))
            s_hac = float(np.sqrt(max(V, 0.0)) / max(A, 1e-300))
            u1 = min(J1, key=J1.get); u2 = min(J2, key=J2.get)
            info['sig_u_hac'] = s_hac; info['sig_u_split'] = abs(u1 - u2) / 2.0
            info['sig_u'] = max(s_hac, info['sig_u_split'], info['sig_u_crb']) if sig == 'hac' else info['sig_u_crb']
    if sig == 'profile':
        # 95 % profile-likelihood confidence set by test inversion: {u : (J(u) - J(u_hat)) / (J(u_hat)/dof) <=
        # kappa F_{0.95}(1, dof)}, kappa = max(1, sigma_hac^2 / sigma_crb^2) (sandwich correction of the LR statistic
        # for a colored residual). Covers u0 whatever the decision (also when 'S unchanged' is accepted with low
        # power); flat profiles give wide sets. Half-width relative to the value that is applied (u_hat or 0), with
        # one coarse step of slack where the set boundary lies between evaluated points; reaching the grid edge -> inf.
        from scipy.stats import f as _fd
        dof_ = max(nw - Mdof2 - 1, 1) if _dref is None else _dref
        kap = 1.0
        if info.get('sig_u_crb') and info.get('sig_u_hac'):
            kap = max(1.0, (info['sig_u_hac'] / info['sig_u_crb']) ** 2)
        thr_ = float(_fd.isf(float(ci_alpha), 1, dof_))
        if ci_mix is not None:
            _al, _tau = ci_mix
            _V = None
            if 0 < i < len(us) - 1 and np.isclose(us[i + 1] - us[i], us[i] - us[i - 1]):
                _hh = float(us[i + 1] - us[i]); _J2 = (Jt[i + 1] - 2 * Jt[i] + Jt[i - 1]) / _hh ** 2
                if _J2 > 0:
                    _V = _J2 / (2.0 * _s2of(Jt[i], dof_))
            if _V is not None:
                _vt = _V * float(_tau) ** 2
                thr_ = (1.0 + 1.0 / _vt) * (2.0 * np.log(1.0 / float(_al)) + np.log1p(_vt))
                info['ci_V'] = float(_V)
            else:
                thr_ = np.inf                          # no curvature information yet: the set is the whole range
        info['ci_thr'] = float(thr_)
        inside = (Jt - Jt[i]) / max(_s2of(Jt[i], dof_), 1e-300) <= kap * thr_
        ii = np.where(inside)[0]
        # conservative bounds: the nearest evaluated point OUTSIDE the set on each side (the set boundary lies
        # between it and the last inside point); none outside on a side -> the set reaches the grid edge
        lo_out = ii.min() - 1; hi_out = ii.max() + 1
        info['ci_edge'] = bool(lo_out < 0 or hi_out >= len(us))
        info['ci_set'] = (float(us[max(lo_out, 0)]), float(us[min(hi_out, len(us) - 1)]))
        if bias_s2 is not None and info.get('sig_u') is not None and not info['ci_edge']:
            # sid_bias (2026-10-23): a nuisance that drifts INSIDE a half leaves a residual r that the per-half LTI model
            # cannot absorb; linearizing the profile, u_hat - u0 = <P g, P r> / ||P g||^2 (g = dS/du * y), and by
            # Cauchy-Schwarz |bias| <= sigma_u sqrt(||P r||^2 / sigma0^2), ||P r||^2 / sigma0^2 ~ J(u_hat)/sigma0^2 - dof
            # (sigma0^2: residual level before the event). The set is widened by this bound (bias-aware set).
            _ex = max(float(Jt[i]) / float(bias_s2) - float(max(nw - Mdof2 - 1, 1)), 0.0)   # in-window dof (review fix 4)
            _bm = float(info['sig_u']) * np.sqrt(_ex)
            info['bias_max'] = _bm; info['bias_excess'] = _ex
            info['ci_set'] = (info['ci_set'][0] - _bm, info['ci_set'][1] + _bm)
            if info['ci_set'][0] < float(np.min(us)) or info['ci_set'][1] > float(np.max(us)):
                info['ci_edge'] = True
        info['ci_kappa'] = kap
        info['ci_slack'] = 0.0
    m1 = min(J1.values()); m2 = min(J2.values())
    # finite-sample F forms (residual dof n - 2M - 1 of the two-half fit); thresholds are F(1, dof) critical values
    # (~ chi2_1 quantiles for dof >> 1, e.g. 6.63 at 1 %)
    dof = max(nw - Mdof2 - 1, 1)
    info['s2'] = float(Jt[i] / dof)                       # residual noise variance (Theorem C bookkeeping)
    info['chow'] = float((Jt[i] - (m1 + m2)) / max(_s2of(m1 + m2, dof - 1), 1e-300))
    if 0.0 in J1:
        info['lrt'] = float((J1[0.0] + J2[0.0] - Jt[i]) / max(_s2of(Jt[i], dof), 1e-300))
    if wchow is not None:
        su = shat_shift(sh, ub, rs, fs)
        dh = e[:b] - np.convolve(y[:b], su)[:b]
        ncom = Mr
        if yreg is not None and hasattr(yreg, 'common'):
            Xf, ncom = yreg.common(halves)                          # restricted model (common LTI part), see _CtrlReg
        elif yreg is not None:
            Xf = np.vstack([yreg(lo, hi) for lo, hi in halves])     # common coefficients, each half its own y_bar
        else:
            xr = x[:b] if xreg is not None else np.convolve(x[:b], su)[:b]
            idx = np.arange(a, b)[:, None] - np.arange(Mr)[None, :]
            Xf = np.where(idx >= 0, xr[np.clip(idx, 0, None)], 0.0)
        if prior is not None and xreg is not None and yreg is None:
            # common fit (one nuisance for both halves) with the same members; X_f^T d_hat = b_1 + b_2 exactly
            _fc = _PriorFit(Xf, prior[1], *_prior_members(prior), G=HC[0]['fit'].G + HC[1]['fit'].G)
            _cand = list(us) if (_pex and _prev >= 2) else [ub]
            # rev 2 (review R5): (u, member) at the MLE of the common model (H0), over all evaluated u; rev 1: u = u_hat
            # of the two-half profile
            _best = None
            for _u in _cand:
                _uu = float(np.round(_u, 6))
                _Jcu, _mc = _fc.J(HC[0]['Braw'][_uu] + HC[1]['Braw'][_uu], HC[0]['dd'][_uu] + HC[1]['dd'][_uu])
                if _best is None or _Jcu < _best[0]:
                    _best = (_Jcu, _uu, _mc)
            Jc, _uc, _mc = _best
            info['wchow_u'] = float(_uc); info['wchow_member'] = (int(_mc[0]), float(_mc[1]))
            if not _pex:
                _dc = float(np.trace(np.linalg.solve(_fc.L.T, np.linalg.solve(_fc.L, _fc.G))))
                ncom = max(Mdof2 - _dc, 1.0)
            if _pex:
                # exact null law (sid_prior_exact): with (u, member) fixed, T = J_c - J_1 - J_2 is a Gaussian quadratic
                # form; T/s2 = sum_j sig_j (a_j^2 - b_j^2), sig_j^2 = eig(G1 (G1+Lam)^-1 G2 (G2+Lam)^-1) (canonical
                # correlations of the two halves under the prior). Imhof: P(T > x) = 1/2 - (1/pi) int_0^inf
                # sin(x v / 2) / (v prod_j (1 + sig_j^2 v^2)^(1/2)) dv
                if _prev >= 2:
                    # review R5 / R6 (rev 2): likelihood ratio against halves with their OWN profiled direct-part
                    # parameters (u_p, gain), so a change of the direct part between the halves is tested too; under H0
                    # the profiled scalars add chi2_k, k = their number (2), to the quadratic form
                    Jh = sum(hc['fit'].J(hc['Braw'][_uc], hc['dd'][_uc])[0] for hc in HC)
                    _kpl = 2 if (len(prior) > 2 and prior[2] is not None) else 0
                else:
                    Jh = sum(hc['fit'].J_at(hc['Braw'][_uc], hc['dd'][_uc], _mc) for hc in HC)
                    _kpl = 0
                Hm = [np.linalg.solve(hc['L'].T, np.linalg.solve(hc['L'], hc['fit'].G)).T for hc in HC]   # G_i (G_i + Lam)^-1
                _s2 = Jt[i] / max(nw - Mdof2 - 1, 1)
                if len(prior) > 4 and prior[4] is not None:
                    # noise variance of the prior model (pre-event estimate, independent of this window): under a
                    # misspecified prior E J != s2 n, so J must not calibrate the test
                    _s2 = float(prior[4])
                info['wchow_s2'] = float(_s2)
                _sg = np.sqrt(np.clip(np.real(np.linalg.eigvals(Hm[0] @ Hm[1])), 0.0, 1.0))
                _sg = _sg[_sg > 1e-6]
                Tst = (Jc - Jh) / max(_s2, 1e-300)
                pv = gchi_pm_chi_sf(Tst, _sg, _kpl)
                info['wchow'] = pv; info['wchow_T'] = float(Tst); info['wchow_sum_sig'] = float(np.sum(_sg))
                info['wchow_nsig'] = int(len(_sg))
                if pv < float(wchow):
                    return None, info, len(us) + 1
        elif xreg is not None and yreg is None and fastchol:
            from scipy.linalg import solve_triangular as _st
            Lfu = gschur_chol(x, a, b, Mr)                 # = chol(G_1 + G_2); generator: G00 from the halves, window ends
            bf = HC[0]['B'][ub] + HC[1]['B'][ub]
            zz = _st(Lfu, bf, lower=True)
            Jc = float(dh[a:b] @ dh[a:b] - zz @ zz)
        else:
            wls = np.linalg.lstsq(Xf, dh[a:b], rcond=None)[0]
            Jc = float(np.sum((dh[a:b] - Xf @ wls) ** 2))
        from scipy.stats import f as _fd
        dof = max(nw - Mdof2 - 1, 1) if _dref is None else _dref
        if not (_pex and prior is not None and yreg is None):
            Fst = ((Jc - Jt[i]) / ncom) / max(_s2of(Jt[i], dof), 1e-300)
            info['wchow'] = float(_fd.sf(Fst, ncom, dof))        # p-value
            if info['wchow'] < float(wchow):
                return None, info, len(us) + 1
    if edge and info['edge']:
        return None, info, len(us)
    if chow_alpha is not None:
        from scipy.stats import f as _fd
        chow = float(_fd.isf(float(chow_alpha), 1, max(dof - 1, 1) if _dref is None else _dref))
        # the u-constancy statistic is a likelihood-ratio statistic in u like the profile set: under a coloured residual
        # its null law is inflated by the same sandwich factor kappa = sigma_hac^2 / sigma_crb^2 (>= 1)
        chow *= float(info.get('ci_kappa', 1.0) or 1.0)
    if chow is not None and info['chow'] > float(chow):
        return None, info, len(us)
    if gof is not None:
        # sid_gof (2026-10-23, A3 with power against drift): goodness of fit of the check model against the residual level
        # before the event, F = (J(u_hat)/dof) / (J_pre/dof_pre) ~ F(dof, dof_pre) if the model holds (no drift of S or P
        # inside the halves, same noise level). Any unexplained drift raises J -> reject (decision postponed).
        from scipy.stats import f as _fd
        _s2p, _dfp, _ag = gof
        info['gof_F'] = float((Jt[i] / dof) / max(float(_s2p), 1e-300))
        if info['gof_F'] > float(_fd.isf(float(_ag), dof, max(int(_dfp), 1))):
            info['gof_fail'] = True
            return None, info, len(us)
    if vpower is not None:
        # sid_vpower (Theorem A / Thm 6 A3, 2026-10-23): accept only if the u-constancy test has power >= 1 - beta against
        # the smallest harmful violation, a movement Delta_v = 2 D_d inside the window (D_d = residual direct spec,
        # max(Q^-1(p) sigma_u, floor)): Delta_v / sqrt(kappa (sigma_1^2 + sigma_2^2)) >= z_{alpha/2} + z_beta, sigma_h from
        # the curvature of the half profile J_h at its minimum (sigma_h^2 = 2 s2_h / J_h'', s2_h = J_h(u_h) / dof_h).
        from scipy.stats import norm as _nm
        _a_c, _beta, _p, _fl = vpower
        sh_ = []
        for Jh in (J1, J2):
            uh = np.array(sorted(Jh)); jh = np.array([Jh[u] for u in uh]); k = int(np.argmin(jh))
            if not (0 < k < len(uh) - 1 and np.isclose(uh[k + 1] - uh[k], uh[k] - uh[k - 1])):
                sh_.append(np.inf); continue
            hh = float(uh[k + 1] - uh[k]); c2 = (jh[k + 1] - 2 * jh[k] + jh[k - 1]) / hh ** 2
            dofh = max(nw // 2 - Mr - 1, 1)
            sh_.append(float(np.sqrt(2.0 * (jh[k] / dofh) / c2)) if c2 > 0 else np.inf)
        su_ = info.get('sig_u') if info.get('sig_u') is not None else np.inf
        Dv = 2.0 * max(float(_nm.isf(_p)) * su_, float(_fl))
        zs = float(_nm.isf(float(_a_c) / 2.0) + _nm.isf(float(_beta)))
        den = np.sqrt(float(info.get('ci_kappa', 1.0) or 1.0) * (sh_[0] ** 2 + sh_[1] ** 2))
        info['vpower_z'] = float(Dv / den) if np.isfinite(den) and den > 0 else 0.0
        info['vpower_sig'] = (sh_[0], sh_[1]); info['vpower_Dv'] = Dv
        if not (info['vpower_z'] >= zs):
            info['vpower_fail'] = True
            return None, info, len(us)
    if lrt is not None and info['lrt'] is not None and info['lrt'] < float(lrt):
        return 0.0, info, len(us)
    return ub, info, len(us)


def ism_paths(cfg: dict, seed: int, extra: dict | None = None):
    """Seed-dependent image-source room (pyroomacoustics): primary path p (noise source -> error mic),
    secondary path s (control speaker 0.3 m from the error mic) and p2 = p after the noise source moved by
    cfg['move_dx'] metres in a random direction (S unchanged), or after the error mic moved (move_target='mic':
    P and S change).
    Optional (defaults keep the original behaviour):
      ism_causal_ms : require (direct delay of P) - (direct delay of S) >= this margin at every position (geometry
                      and move direction are redrawn otherwise; A4 of the review)
      move_steps K  : continuous movement; returns lists of K paths along the straight trajectory (A5).
      move_target='rig' : error mic and control speaker move together by dxv (speaker-mic distance fixed): P and S
                      both change, only the reflections of S change (direct part fixed)."""
    import pyroomacoustics as pra
    g = np.random.default_rng(seed + 31337)
    room_dim = [float(z) for z in cfg.get('ism_room', [6.0, 5.0, 3.0])]; fs_ = int(cfg['sample_rate'])
    e_abs, mo = pra.inverse_sabine(float(cfg.get('ism_rt60', 0.25)), room_dim)
    mo = min(mo, int(cfg.get('ism_max_order', 10)))
    unit = lambda: (lambda v: v / np.linalg.norm(v))(g.standard_normal(3))
    inside = lambda q, m: all(m < q[i] < room_dim[i] - m for i in range(3))
    mic_move = cfg.get('move_target', 'source') == 'mic'
    rig_move = cfg.get('move_target') == 'rig'          # error mic and control speaker move together (rigid)
    moved = mic_move or rig_move                        # P and S both change (error mic moved)
    K = int(cfg.get('move_steps', 0)); causal = cfg.get('ism_causal_ms')
    ts = np.linspace(0.0, 1.0, max(K, 2))
    c0 = 343.0

    def margin_ok(e, cs, ns, dxv):
        if causal is None:
            return True
        for t in ts:
            ee = e + t * dxv if moved else e; nn = ns if moved else ns + t * dxv
            cs_t = cs + t * dxv if rig_move else cs
            if (np.linalg.norm(nn - ee) - np.linalg.norm(cs_t - ee)) / c0 * 1e3 < float(causal):
                return False
        return True
    for _geo in range(1000):
        while True:
            e = np.array([g.uniform(min(0.8, d / 3), d - min(0.8, d / 3)) for d in room_dim]); cs = e + 0.3 * unit()
            ns = np.array([g.uniform(0.5, d - 0.5) for d in room_dim])
            if inside(cs, 0.3) and np.linalg.norm(ns - e) > float(cfg.get('ism_src_dist', 2.0)):
                break
        dxv = float(cfg.get('move_dx', 0.0)) * unit()
        if cfg.get('move_dir') in ('radial_in', 'radial_out'):
            # (2026-10-26, stress cells) mic moves along the speaker axis: the largest direct-path change for |dx|
            # (u = -/+|dx|); the random draw above is kept so that the RNG stream (and the geometry) is unchanged
            dxv = (1.0 if cfg['move_dir'] == 'radial_in' else -1.0) * float(cfg.get('move_dx', 0.0)) * (cs - e) / np.linalg.norm(cs - e)
        _base = e if moved else ns
        ok = False
        for _ in range(200):                  # redraw the direction only if the moved point leaves the room / breaks causality
            if inside(_base + dxv, 0.2) and (not rig_move or inside(cs + dxv, 0.2)) and margin_ok(e, cs, ns, dxv):
                ok = True
                break
            if cfg.get('move_dir') in ('radial_in', 'radial_out'):
                break                         # radial direction is fixed: redraw the geometry instead
            dxv = float(cfg.get('move_dx', 0.0)) * unit()
        if ok or causal is None:
            break
    if extra is not None and cfg.get('ref_dist'):
        # reference microphone attached to the noise source (C1 of the review): path source -> reference mic
        ur = unit(); rm = ns + float(cfg['ref_dist']) * ur
        for _ in range(100):
            if inside(rm, 0.1):
                break
            ur = unit(); rm = ns + float(cfg['ref_dist']) * ur
        rr = pra.ShoeBox(room_dim, fs=fs_, materials=pra.Material(e_abs), max_order=mo, air_absorption=False)
        rr.add_source(ns); rr.add_microphone_array(rm[:, None]); rr.compute_rir()
        # remove pyroomacoustics' global fractional-delay offset (it is already contained once in P and in S)
        off = int(pra.constants.get('frac_delay_length')) // 2
        hr = np.asarray(rr.rir[0][0])[off:off + int(cfg.get('len_r', 256))]
        extra['h_ref'] = hr / np.max(np.abs(hr))
    if extra is not None:
        # geometry for diagnostics (no effect on the simulation): true speaker-distance change for a mic move
        extra['geom'] = {'e': e.tolist(), 'cs': cs.tolist(), 'ns': ns.tolist(), 'dxv': dxv.tolist(), 'mic_move': mic_move,
                         'rig_move': rig_move,
                         'u_true': float(np.linalg.norm(cs - e - dxv) - np.linalg.norm(cs - e)) if mic_move else 0.0}
    room = pra.ShoeBox(room_dim, fs=fs_, materials=pra.Material(e_abs), max_order=mo, air_absorption=False)
    Lp = int(cfg.get('len_p', 1024)); Ls = int(cfg.get('len_s', 256))
    cut = lambda h, L: np.pad(h, (0, max(0, L - len(h))))[:L]
    if K >= 2:
        if rig_move:
            # sources: ns (index 0), cs + t dxv (index k+1 at step k); mics: e + t dxv
            room.add_source(ns)
            for t in ts:
                room.add_source(cs + t * dxv)
            room.add_microphone_array(np.stack([e + t * dxv for t in ts], 1)); room.compute_rir()
            pl = [cut(room.rir[k][0], Lp) for k in range(K)]; sl = [cut(room.rir[k][k + 1], Ls) for k in range(K)]
            sc = 1.0 / np.linalg.norm(pl[0]); ss = 1.0 / np.linalg.norm(sl[0])
            return pl[0] * sc, sl[0] * ss, [q * sc for q in pl], [q * ss for q in sl]
        if mic_move:
            for q in (ns, cs):
                room.add_source(q)
            room.add_microphone_array(np.stack([e + t * dxv for t in ts], 1)); room.compute_rir()
            pl = [cut(room.rir[m][0], Lp) for m in range(K)]; sl = [cut(room.rir[m][1], Ls) for m in range(K)]
        else:
            for t in ts:
                room.add_source(ns + t * dxv)
            room.add_source(cs)
            room.add_microphone_array(e[:, None]); room.compute_rir()
            pl = [cut(room.rir[0][k], Lp) for k in range(K)]; sl = None; s_ = cut(room.rir[0][K], Ls)
        sc = 1.0 / np.linalg.norm(pl[0])
        if mic_move:
            ss = 1.0 / np.linalg.norm(sl[0])
            return pl[0] * sc, sl[0] * ss, [q * sc for q in pl], [q * ss for q in sl]
        return pl[0] * sc, s_ / np.linalg.norm(s_), [q * sc for q in pl], None
    if rig_move:
        # sources: ns (0), cs (1), cs + dxv (2); mics: e (0), e + dxv (1)
        for q in (ns, cs, cs + dxv):
            room.add_source(q)
        room.add_microphone_array(np.stack([e, e + dxv], 1)); room.compute_rir()
        p, s_ = cut(room.rir[0][0], Lp), cut(room.rir[0][1], Ls)
        p2, s2 = cut(room.rir[1][0], Lp), cut(room.rir[1][2], Ls)
        sc = 1.0 / np.linalg.norm(p); ss = 1.0 / np.linalg.norm(s_)
        return p * sc, s_ * ss, p2 * sc, s2 * ss
    srcs = (ns, cs) if mic_move else (ns, cs, ns + dxv)
    for q in srcs:
        room.add_source(q)
    mics = np.stack([e, e + dxv], 1) if mic_move else e[:, None]
    room.add_microphone_array(mics); room.compute_rir()
    p, s_ = cut(room.rir[0][0], Lp), cut(room.rir[0][1], Ls)
    if mic_move:
        p2, s2 = cut(room.rir[1][0], Lp), cut(room.rir[1][1], Ls)
    else:
        p2, s2 = cut(room.rir[0][2], Lp), None
    sc = 1.0 / np.linalg.norm(p); ss = 1.0 / np.linalg.norm(s_)
    return p * sc, s_ * ss, p2 * sc, (None if s2 is None else s2 * ss)


def _cftf_init(xf, tau, M, lam, pi, w0):
    """(2026-10-31, REVISION_RULE_7) covariance-window stabilized FTF restarted at tau: window [tau, t] with the TRUE
    regressor and the prior pi lam^(t-tau+1) diag(lam^-i) centred at w0 (= RLS + det up to the lam^-i weights). The
    forward predictor lives on the window [tau-1] (the lower-right block of the extended Gram matrix); its gain is
    obtained from the gain of [tau] by a rank-one correction with z = R[tau]^-1 u(tau-1), updated at O(M) per sample.
    Checked against direct LS (M = 16, rel. error 4e-14) and against exact RLS (M = 64, lam 0.9999, 20000 samples, 1e-14)."""
    ub = np.array([xf[tau - 1 - i] if tau - 1 - i >= 0 else 0.0 for i in range(M + 1)])   # [x(tau-1), ..., x(tau-1-M)]
    v = ub[:M].copy()
    d0 = pi * lam ** (-np.arange(1, M + 1, dtype=float))
    z = v / d0
    return {'a': np.zeros(M), 'al': pi / lam, 'b': np.zeros(M), 'be': pi * lam ** (-(M + 1)), 'kf': z.copy(),
            'gf': 1.0 / (1.0 + v @ z), 'z_prev': None, 'z': z, 'k': None, 'v': v, 'tau': tau, 'ub': ub, 'first': True}


def _cftf_run(S, xf, dhat, w, t_from, t_to, lam, M, stab=(1.5, 2.5, 1.0)):
    a, b, ub, tau = S['a'], S['b'], S['ub'], S['tau']; k1, k2, k3 = stab
    for t in range(t_from, t_to):
        u_prev = ub[:M].copy()                                    # u(t-1)
        ub[1:] = ub[:-1]; ub[0] = xf[t]                            # ub = [x(t), ..., x(t-M)]
        u_now = ub[:M]
        if not S['first']:
            c = lam ** (t - tau - 1); zp = S['z_prev']
            S['kf'] = S['k'] - c * zp * (zp @ u_prev) / (lam * (1.0 + c * (zp @ S['v'])))
            S['gf'] = 1.0 / (1.0 + u_prev @ S['kf'])
        kf, gf = S['kf'], S['gf']
        ea = xf[t] - a @ u_prev
        al_old = S['al']; S['al'] = lam * al_old + gf * ea * ea
        kext = np.empty(M + 1); kext[0] = 0.0; kext[1:] = kf
        cc = ea / (lam * al_old); kext[0] += cc; kext[1:] -= cc * a
        a += gf * ea * kf
        m_ = kext[M]
        eb1 = lam * S['be'] * m_; eb2 = ub[M] - b @ u_now
        ebk = [k * eb2 + (1.0 - k) * eb1 for k in (k1, k2, k3)]
        kk = kext[:M] + m_ * b
        g = 1.0 / (1.0 / gf + cc * ea - m_ * ebk[2])
        S['be'] = lam * S['be'] + g * ebk[1] * ebk[1]
        b += g * ebk[0] * kk
        eps = dhat[t] + u_now @ w
        w = w - g * eps * kk
        z_new = (S['z'] - g * kk * (u_now @ S['z'])) / lam
        S['z_prev'], S['z'] = S['z'], z_new
        S['k'] = kk; S['first'] = False
    return w


def run(cfg: dict, seed: int, method: str, params: dict, eval_seconds: float,
        change_at: float | None = None) -> dict:
    method = _naming.method_key(method)          # former keys 'E-PCG-F' / 'E-PCG' (before v1.1.0) are accepted
    N = int(cfg['fft_length']); H = int(cfg['hop_length']); M = int(cfg['controller_length'])
    fs = int(cfg['sample_rate'])
    x, d, v, p, s, eval_samples = _make_signals(cfg, seed, 1, eval_seconds)
    shat = s.copy()                      # S_hat = S in the screening study
    n = len(x)
    xf = np.convolve(x, shat, mode='full')[:n]
    p2_ism = None; s2_ism = None; traj_p = None; traj_s = None
    src_sig = x                                      # noise-source signal (= reference unless ref_dist is set)
    if cfg.get('plant') == 'ism' or cfg.get('path_source', 'ism') == 'meshrir':
        _extra = {}
        if cfg.get('path_source', 'ism') == 'meshrir':
            from measured_paths import meshrir_paths
            p, s, p2_ism, s2_ism = meshrir_paths(cfg, seed, _extra)
        else:
            p, s, p2_ism, s2_ism = ism_paths(cfg, seed, _extra)
        if cfg.get('noise_type'):
            # other noise types (C2 of the review), normalized like the default AR(1) reference
            _gr = np.random.default_rng(seed + 777001); nt = cfg['noise_type']
            if nt == 'harmonic':
                tt = np.arange(n) / fs; f0 = float(cfg.get('f0', 40.0))
                ph = _gr.uniform(0, 2 * np.pi, 40)
                xh = sum(np.cos(2 * np.pi * f0 * (k + 1) * tt + ph[k]) / np.sqrt(k + 1) for k in range(int(min(40, (fs / 2 - 100) // f0))))
                xb = lfilter([1.0], [1.0, -0.9], _gr.standard_normal(n))
                x = xh / np.std(xh) + 10 ** (-10 / 20) * xb / np.std(xb)
            elif nt == 'pink':
                x = lfilter([1.0], [1.0, -1.6, 0.64], _gr.standard_normal(n))
            elif nt == 'white':
                x = _gr.standard_normal(n)
            x = x / np.std(x[:eval_samples]); src_sig = x
        if cfg.get('ref_dist'):
            # measured reference = source * h_ref + reference-microphone noise (ref_snr_db)
            xr = np.convolve(src_sig, _extra['h_ref'])[:n]
            xr = xr + np.random.default_rng(seed + 991).standard_normal(n) * np.std(xr) * 10 ** (-float(cfg.get('ref_snr_db', 30.0)) / 20)
            x = xr / np.std(xr[:eval_samples])
        if isinstance(p2_ism, list):                 # continuous movement (A5): paths along the trajectory
            traj_p, traj_s = p2_ism, s2_ism
            p2_ism = traj_p[-1]; s2_ism = None if traj_s is None else traj_s[-1]
        shat = s.copy()
        d = np.convolve(src_sig, p, mode='full')[:n]; xf = np.convolve(x, shat, mode='full')[:n]
        rng_v = np.random.default_rng(seed + 1000003)
        from ffanc_norm.simulation import secondary_noise_for_snr
        v_eval = secondary_noise_for_snr(d[:eval_samples], cfg.get('secondary_noise_snr_db'), rng_v)
        pv = float(np.mean(d[:eval_samples] ** 2)) / 10 ** (float(cfg['secondary_noise_snr_db']) / 10)
        v = np.concatenate([v_eval, rng_v.standard_normal(n - eval_samples) * np.sqrt(pv)])
    if cfg.get('plant') == 'random_decay':
        # Seed-dependent random plant with exponentially decaying impulse
        # responses (robustness check against the short synthetic paths).
        prng = np.random.default_rng(seed + 777)
        tp = float(cfg.get('tau_p', 40.0)); ts = float(cfg.get('tau_s', 12.0))
        Lp = int(cfg.get('len_p', 192)); Ls = int(cfg.get('len_s', 64))
        dp = int(cfg.get('delay_p', 5))
        p = np.zeros(Lp); k = np.arange(Lp - dp)
        p[dp:] = prng.standard_normal(Lp - dp) * np.exp(-k / tp)
        s = np.zeros(Ls); k = np.arange(Ls - 3)
        s[3:] = prng.standard_normal(Ls - 3) * np.exp(-k / ts)
        p /= np.linalg.norm(p); s /= np.linalg.norm(s)
        shat = s.copy()
        d = np.convolve(x, p, mode='full')[:n]
        xf = np.convolve(x, shat, mode='full')[:n]
        rng_v = np.random.default_rng(seed + 1000003)
        from ffanc_norm.simulation import secondary_noise_for_snr
        v_eval = secondary_noise_for_snr(d[:eval_samples], cfg.get('secondary_noise_snr_db'), rng_v)
        pv = float(np.mean(d[:eval_samples] ** 2)) / 10 ** (float(cfg['secondary_noise_snr_db']) / 10)
        v = np.concatenate([v_eval, rng_v.standard_normal(n - eval_samples) * np.sqrt(pv)])
    if cfg.get('shat_nmse_db') is not None or cfg.get('shat_delay_err', 0):
        # Secondary-path model error: S_hat = S + delta with NMSE
        # ||delta||^2/||S||^2 = 10^(nmse_db/10); delta has the same exponential
        # envelope as |S| (seed-dependent), optionally plus an integer delay error.
        srng = np.random.default_rng(seed + 555)
        shat = s.copy()
        if cfg.get('shat_nmse_db') is not None:
            env = np.abs(s) + 1e-3 * np.max(np.abs(s))
            env = np.convolve(env, np.ones(5) / 5, mode='same')
            delta = srng.standard_normal(len(s)) * env
            delta *= np.linalg.norm(s) * 10 ** (float(cfg['shat_nmse_db']) / 20) / np.linalg.norm(delta)
            shat = shat + delta
        dl = int(cfg.get('shat_delay_err', 0))
        if dl:
            shat = np.concatenate([np.zeros(dl), shat])[:len(s)] if dl > 0 else np.concatenate([shat[-dl:], np.zeros(-dl)])
        xf = np.convolve(x, shat, mode='full')[:n]
    if method == 'known':
        w_known, *_ = wiener_solution(s, p, M, pole=float(cfg.get('ar_pole', 0.95)))
    ctype = cfg.get('change_type', 'primary')
    if change_at is not None and ctype != 'primary':
        # non-plant changes (no change of the optimal controller): reference level step
        # ('xlevel', x -> g x) or sensor-noise step ('noise', v -> g v) at the change time
        c = int(round(change_at * fs)); gch = float(cfg.get('change_gain', 3.0))
        if ctype == 'xlevel':
            x = x.copy(); x[c:] *= gch
            d = np.convolve(x, p, mode='full')[:n]; xf = np.convolve(x, shat, mode='full')[:n]
        elif ctype == 'noise':
            v = v.copy(); v[c:] *= gch
        else:
            raise ValueError(ctype)
        change_at = None
    change_c = int(round(change_at * fs)) if change_at is not None else None
    if change_at is not None:
        c = int(round(change_at * fs))
        if cfg.get('plant') == 'random_decay':
            prng2 = np.random.default_rng(seed + 999)
            dp = int(cfg.get('delay_p', 5)); Lp = int(cfg.get('len_p', 192))
            p2 = np.zeros(Lp); k = np.arange(Lp - dp)
            p2[dp:] = prng2.standard_normal(Lp - dp) * np.exp(-k / float(cfg.get('tau_p', 40.0)))
            p2 /= np.linalg.norm(p2)
        elif p2_ism is not None:
            p2 = p2_ism
        else:
            p2 = changed_primary_path()
        if cfg.get('partial_rel_db') is not None:
            # partial change: p2 = p + delta, ||delta|| / ||p|| = 10^(rel_db/20), delta with |p|'s envelope
            prng3 = np.random.default_rng(seed + 4242)
            env = np.convolve(np.abs(p) + 1e-3 * np.max(np.abs(p)), np.ones(5) / 5, mode='same')
            dlt = prng3.standard_normal(len(p)) * env
            p2 = p + dlt * np.linalg.norm(p) * 10 ** (float(cfg['partial_rel_db']) / 20) / np.linalg.norm(dlt)
        d2 = np.convolve(src_sig, p2, mode='full')[:n]
        if method == 'known':
            w_known2, *_ = wiener_solution(s if s2_ism is None else s2_ism, p2, M, pole=float(cfg.get('ar_pole', 0.95)))
            switch_hop = c // H + 1   # first hop after the change has been observed
        if cfg.get('drift_seconds'):
            # linear drift of the primary path p -> p2 over drift_seconds starting at c
            a = np.clip((np.arange(n) - c) / (float(cfg['drift_seconds']) * fs), 0.0, 1.0)
            d = (1.0 - a) * d + a * d2
        else:
            d = np.concatenate([d[:c], d2[c:]])
        if traj_p is not None:
            # continuous movement: piecewise-constant primary path per hop over move_seconds after c
            msamp = max(int(float(cfg.get('move_seconds', 0.5)) * fs), 1); Kt = len(traj_p)
            for hs in range((c // H) * H, n, H):
                k_ = int(np.clip(round((max(hs, c) - c) / msamp * (Kt - 1)), 0, Kt - 1))
                he = min(hs + H, n); a_ = max(hs, c)
                d[a_:he] = fir_window(src_sig, traj_p[k_], hs, he)[a_ - hs:]
    # RLS state (R) and accumulated Toeplitz statistics (A-TPCG)
    Prls = None
    rls_pw = [None]        # (2026-10-31, review N8) R-RLS 'det_prewindow': start of the prewindowed regressor
    jp_from = [0]          # (2026-10-31) 'preroll' restarts (R-SFTF / R-RLS): joint-process updates only from tau
    cov = [None]           # (2026-10-31, REVISION_RULE_7) R-SFTF 'cov': covariance-window FTF state after a detection
    hyb = [None]           # (2026-10-31) R-SFTF 'hybrid' T_h: exact RLS on [tau, tau + T_h), then FTF (pre-roll T_h)
    sftf = None            # (2026-10-31, review option 2) state of 'R-SFTF'; None = (re)initialize at _rls_from
    hist_pw: list[float] = []; n_resets = [0]; since = [0]; eb_hist: list = []
    _ev_total = [0]                                  # (review 2026-10-24, fix 3) events over the whole run incl. rebuilds
    restart = [0]; score_hist: list = []; reset_hops: list = []; loc_hist: list = []; flop_hist: list = []
    fd_restart = [None]   # (2026-10-30, review N1) hop sample of the last shared detection for 'fixed_binwise'
    _sid = {'on': False, 'log': []}
    w_raw = np.zeros(M); w_avg = np.zeros(M); n_avg = [0]; cum_pow = np.zeros(N // 2 + 1)
    pq_score: dict = {}
    hyps: list = []; coll = [None, None]; log_evidence = [0.0]; rl_hist: list = []
    if method == 'BOCPD':
        _al = float(params['alpha']); _i = np.arange(M)
        K_tc = _al ** np.maximum(_i[:, None], _i[None, :])
        _lam = np.array([_al ** j * (1 - _al) for j in range(M - 1)] + [_al ** (M - 1)])
        _D = np.eye(M) - np.eye(M, k=1)
        Kinv_tc = _D.T @ np.diag(1.0 / _lam) @ _D
        # noise reference: sensor-noise power implied by the training SNR definition
        noise_ref = float(np.mean(d[:eval_samples] ** 2)) / 10 ** (float(cfg['secondary_noise_snr_db']) / 10)
        # (A3') colored residual: Cov(n_b) = sigma^2 (I + rho * T_x), T_x the Toeplitz
        # autocorrelation of the (observable) reference, normalized to unit variance;
        # rho = sigma_u2_rel. Hop-to-hop noise correlation is neglected.
        Wwhite = None; logdetW = 0.0
        if float(params.get('sigma_u2_rel', 0.0)) > 0.0:
            xr = x[:eval_samples]
            ac = np.array([xr[l:] @ xr[:len(xr) - l] for l in range(H)]) / len(xr)
            Tx = toeplitz(ac / ac[0])
            Lw = np.linalg.cholesky(np.eye(H) + float(params['sigma_u2_rel']) * Tx)
            Wwhite = np.linalg.inv(Lw)
            logdetW = -float(np.sum(np.log(np.diag(Lw))))
    r_acc = np.zeros(M); p_acc = np.zeros(M)

    gls_oracle_acf = None
    if method == 'PCG-WLS' and params.get('gls') == 'oracle':
        # true noise autocorrelation n = d + x_f * w* + v over the run (oracle check only)
        w_opt, *_ = wiener_solution(s, p, M, pole=float(cfg.get('ar_pole', 0.95)))
        nn = (d + np.convolve(xf, w_opt)[:n] + v)[:eval_samples]
        po = int(params.get('p', 8))
        gls_oracle_acf = np.array([nn[l:] @ nn[:len(nn) - l] for l in range(po + 1)]) / len(nn)
    w = np.zeros(M) if method != 'known' else w_known.copy()
    y = np.zeros(n); sec = np.zeros(n); e = np.zeros(n); dhat = np.zeros(n)
    # online secondary-path modeling (method 'osp_binwise', Eriksson 1989): auxiliary white noise u added to the
    # loudspeaker signal; all other methods have u = 0 (numerically identical to before)
    u_aux = np.zeros(n)
    if method == 'osp_binwise':
        _ur = np.random.default_rng(seed + 2024)
        u_aux = _ur.standard_normal(n) * float(params.get('u_std', 0.05))
        osp = {'sh': shat.copy(), 'xf': np.zeros(n), 'pw': PowerTracker(N // 2 + 1, float(cfg['power_smoothing']), float(cfg['regularization_ratio']))}
        if params.get('sched'):
            # variable auxiliary-noise power (Akhtar et al. 2006 type; new baseline 2026-10-23): u_std(t) = u_max
            # sqrt(min(1, P_f / P_e)), P_f = smoothed power of the modeling error f = e - S_hat*u - h*x (ZLS third
            # filter removes d + S y), P_e = smoothed error power; large while S_hat is wrong, small after convergence
            osp['z'] = u_aux / max(float(params.get('u_std', 0.05)), 1e-12); osp['sig'] = float(params.get('u_std', 0.05))
            osp['Pf'] = None; osp['Pe'] = None
    if method == 'osp_free':
        # auxiliary-noise-free online secondary-path modeling (new baseline 2026-10-23; Hu, Xue, Lu 2018/2019; Lian et
        # al. FDSCM 2023/2025): joint NLMS identification of the primary model h (on x) and S_hat (on y) from
        # e ~ h * x + S_hat * y; identifiable while the control filter varies; FD-FxNLMS with x_f = S_hat * x
        osp = {'sh': shat.copy(), 'h': np.zeros(int(params.get('Lh', 2 * M))), 'xf': np.zeros(n),
               'pw': PowerTracker(N // 2 + 1, float(cfg['power_smoothing']), float(cfg['regularization_ratio']))}
    power = PowerTracker(N // 2 + 1, float(cfg['power_smoothing']), float(cfg['regularization_ratio']))
    prev_step = np.zeros(M)
    # FDKF state (C)
    P = None; Psi = None

    total_power, uncontrolled_power = [], []
    max_w = 0.0; max_e = 0.0
    n_hops = eval_samples // H
    _cusum = None
    if method == 'R-RLS' and 'cusum_h' in params:
        from revision9_cusum import CUSUM
        # (2026-11-03, review) the CUSUM replay below mirrors only the selected RLS + det restart (fixed lam, P from
        # 'delta', no pre-window / pre-roll); refuse options that would make the two silently diverge
        assert not set(params) & {'det_events', 'det_delta', 'det_prewindow', 'det_preroll', 'det_replay',
                                  'det_reset_w'}, 'RLS + CUSUM supports only the selected RLS + det restart'
        _cusum = CUSUM(float(params['cusum_h']), int(params['cusum_k']), H)
    _wlog = []
    _rlog = []                                       # G4: predicted per-sample excess of the robust ridge (log_ridge)
    _dual = []                                       # Theorem C bookkeeping (log_ridge)
    for b in range(n_hops):
        start, stop = b * H, (b + 1) * H
        y[start:stop] = fir_window(x, w, start, stop)
        if method == 'osp_binwise' and params.get('sched'):
            u_aux[start:stop] = osp['z'][start:stop] * osp['sig']
        _wlog.append(np.array(w, float))             # applied controller per hop (read only by sid_xreg='ybar')
        sec[start:stop] = fir_window(y + u_aux if method == 'osp_binwise' else y, s, start, stop)
        if s2_ism is not None and change_c is not None and stop > change_c:
            # error microphone moved: the true secondary path switches to S2 at the change (S_hat stays S)
            a = max(start, change_c)
            s_now = s2_ism
            if traj_s is not None:                   # continuous movement: S along the trajectory
                msamp = max(int(float(cfg.get('move_seconds', 0.5)) * fs), 1)
                s_now = traj_s[int(np.clip(round((a - change_c) / msamp * (len(traj_s) - 1)), 0, len(traj_s) - 1))]
            sec[a:stop] = fir_window(y + u_aux if method == 'osp_binwise' else y, s_now, start, stop)[a - start:]
        e[start:stop] = d[start:stop] + sec[start:stop] + v[start:stop]
        total_power.append(float(np.mean(e[start:stop] ** 2)))
        uncontrolled_power.append(float(np.mean((d[start:stop] + v[start:stop]) ** 2)))
        max_e = max(max_e, float(np.max(np.abs(e[start:stop]))))

        # Disturbance reconstruction (realizable with S_hat and the emitted y).
        dhat[start:stop] = e[start:stop] - fir_window(y, shat, start, stop)

        xf_hist = right_aligned_history(xf, stop, N)
        Xf = np.fft.rfft(xf_hist)
        power.update(Xf)

        # (2026-10-30, review: separate the solver from the detector) shared change events for baselines: params
        # 'det_events' = [[stop, tau], ...] taken from a run of the proposed method on the same data (its detections and
        # localized change points). At the hop ending at 'stop' the baseline restarts at 'tau': R-RLS / R-VFF reset P and
        # replay [tau, stop); V-SCHED restarts its circulant-RLS step schedule. Off by default.
        _rls_from = start; _det_reset_pending = False
        if params.get('det_events'):
            for _st, _tau in params['det_events']:
                if int(_st) == stop:
                    _tau = int(min(max(int(_tau), 0), stop))
                    if method == 'V-SCHED':
                        # (review M1) bs counts from tau // H, cum_pow from this hop; _localize returns tau in the
                        # detection hop, so the two coincide (stop - tau <= H)
                        restart[0] = _tau; cum_pow[:] = 0.0
                        if params.get('det_reset_w'):
                            w_raw[:] = 0.0; w_avg[:] = 0.0; w = np.zeros(M)
                    elif method == 'R-SFTF':
                        # (2026-10-31) SFTF + det: prewindowed restart at tau (internal regressor zero before tau),
                        # replay [tau, stop); warm (keep w) or cold (det_reset_w)
                        sftf = None; _rls_from = _tau; _det_reset_pending = True
                        if params.get('preroll'):            # (2026-10-31) pre-roll restart: predictors from tau - K
                            _rls_from = max(0, _tau - int(params['preroll'])); jp_from[0] = _tau
                        if params.get('cov'):                # (2026-10-31) covariance-window FTF from tau (O(M))
                            assert not (params.get('preroll') or params.get('hybrid')), 'cov excludes preroll / hybrid'
                            cov[0] = 'pending'
                        if params.get('hybrid'):             # (2026-10-31) exact covariance RLS first, then FTF
                            Th = int(params['hybrid'])
                            hyb[0] = {'t1': _tau + Th, 'P': np.eye(M) / (float(params['delta'])
                                      * float(np.mean(xf[:eval_samples] ** 2)) * M)}
                        if params.get('det_reset_w'):
                            w = np.zeros(M)
                    elif method in ('R-RLS', 'R-VFF'):
                        # (2026-10-30, review N2) 'det_replay' False: reset P only, no replay of [tau, stop);
                        # 'det_delta': regularization of the reset P (default: the initial 'delta')
                        Prls = None; _rls_from = _tau if params.get('det_replay', True) else start
                        _det_reset_pending = True
                        if params.get('det_prewindow'):      # (2026-10-31, review N8) regressor zero before tau
                            rls_pw[0] = _tau
                        if params.get('det_preroll'):        # (2026-10-31) O(M^2) twin of the R-SFTF pre-roll restart
                            _rls_from = max(0, _tau - int(params['det_preroll'])); rls_pw[0] = _rls_from
                            jp_from[0] = _tau
                        if params.get('det_reset_w'):
                            w = np.zeros(M)
                    elif method == 'fixed_binwise':
                        # (2026-10-30, review N1) FD-FxNLMS + restart: step boost after a detection, decaying to mu
                        fd_restart[0] = _tau
                        if params.get('det_reset_w'):
                            w = np.zeros(M)
                    reset_hops.append(b)
        if method == 'known':
            w = w_known
            if change_at is not None and b + 1 >= switch_hop:
                w = w_known2
        elif method == 'fixed_binwise':
            g = fd_block_gradient(xf_hist, e[start:stop], power.denominator('binwise', b), M)
            mu_fd = params['mu']
            if fd_restart[0] is not None and params.get('det_boost'):
                # (2026-10-30, review N1) mu_b = max(mu, s (N / H) / (b_since + 1)), b_since from tau // H (as V-SCHED)
                mu_fd = max(mu_fd, float(params['det_boost']) * (N / H) / (b - fd_restart[0] // H + 1))
            w = w - mu_fd * g

        elif method == 'osp_binwise':
            # S_hat by block NLMS on the auxiliary noise: f = e - S_hat * u (d and S*y act as interference)
            Ls_ = len(osp['sh'])
            su_ = fir_window(u_aux, osp['sh'], start, stop)
            f_ = e[start:stop] - su_
            if params.get('zls'):
                # Zhang, Lan, Ser (IEEE TSAP 2001): a third filter h on x removes d + S*y from the modeling error
                if 'h' not in osp:
                    osp['h'] = np.zeros(int(params.get('Lh', M)))
                Lh_ = len(osp['h'])
                f_ = f_ - fir_window(x, osp['h'], start, stop)
                lox = max(0, start - Lh_ + 1)
                xseg = np.concatenate([np.zeros(Lh_ - 1 - (start - lox)), x[lox:stop]])
                gh = np.correlate(xseg, f_, 'valid')[::-1][:Lh_]
                osp['h'] = osp['h'] + float(params.get('mu_h', 0.5)) * gh / (float(xseg @ xseg) + 1e-12)
            lo_ = max(0, start - Ls_ + 1)
            useg = np.concatenate([np.zeros(Ls_ - 1 - (start - lo_)), u_aux[lo_:stop]])
            gs = np.correlate(useg, f_, 'valid')[::-1][:Ls_]          # g_k = sum_n f[n] u[n-k]
            osp['sh'] = osp['sh'] + float(params.get('mu_s', 0.5)) * gs / (float(useg @ useg) + 1e-12)
            osp['xf'][start:stop] = fir_window(x, osp['sh'], start, stop)
            xh_ = right_aligned_history(osp['xf'], stop, N)
            osp['pw'].update(np.fft.rfft(xh_))
            ec_ = e[start:stop] - su_ if params.get('zls') else e[start:stop]     # ZLS: control error without the auxiliary noise
            g = fd_block_gradient(xh_, ec_, osp['pw'].denominator('binwise', b), M)
            w = w - params['mu'] * g
            if params.get('sched'):
                _pf = float(np.mean(f_ ** 2)); _pe = float(np.mean(e[start:stop] ** 2)); _sm = float(cfg['power_smoothing'])
                osp['Pf'] = _pf if osp['Pf'] is None else _sm * osp['Pf'] + (1 - _sm) * _pf
                osp['Pe'] = _pe if osp['Pe'] is None else _sm * osp['Pe'] + (1 - _sm) * _pe
                osp['sig'] = float(params.get('u_max', 0.1)) * np.sqrt(min(1.0, osp['Pf'] / max(osp['Pe'], 1e-12)))

        elif method == 'osp_free':
            Ls_ = len(osp['sh']); Lh_ = len(osp['h'])
            f_ = e[start:stop] - fir_window(y, osp['sh'], start, stop) - fir_window(x, osp['h'], start, stop)
            lox = max(0, start - Lh_ + 1); xseg = np.concatenate([np.zeros(Lh_ - 1 - (start - lox)), x[lox:stop]])
            loy = max(0, start - Ls_ + 1); yseg = np.concatenate([np.zeros(Ls_ - 1 - (start - loy)), y[loy:stop]])
            nrm = float(xseg @ xseg) + float(yseg @ yseg) + 1e-12
            ms_ = float(params.get('mu_s', 0.1))
            osp['h'] = osp['h'] + ms_ * np.correlate(xseg, f_, 'valid')[::-1][:Lh_] / nrm
            osp['sh'] = osp['sh'] + ms_ * np.correlate(yseg, f_, 'valid')[::-1][:Ls_] / nrm
            osp['xf'][start:stop] = fir_window(x, osp['sh'], start, stop)
            xh_ = right_aligned_history(osp['xf'], stop, N)
            osp['pw'].update(np.fft.rfft(xh_))
            g = fd_block_gradient(xh_, e[start:stop], osp['pw'].denominator('binwise', b), M)
            w = w - params['mu'] * g

        elif method == 'spec_binwise':
            # FD-FxNLMS with the same movement spec as PCG-WLS (Prop. 10 + Prop. 12) as a per-bin leakage:
            # eps_k = kappa sqrt(1 - sinc(w_k dx/c)), leak_k = max(0, eps_k/gamma - 1) (normalized-gradient units)
            if b == 0:
                if params.get('bound'):
                    _ep = movement_bound(shat, M, fs, float(params['robust_dx']), float(params.get('robust_rs', 0.3)), float(params.get('robust_p', 0.025)))
                else:
                    _z = 2 * np.pi * np.arange(M + 1) / (2 * M) * fs * float(params['robust_dx']) / 343.0
                    _ep = float(params.get('kappa', 2.0)) * np.sqrt(np.maximum(1.0 - np.sinc(_z / np.pi), 0.0))
                spec_leak = np.maximum(0.0, _ep / float(params.get('gamma', 0.9)) - 1.0)
            g = fd_block_gradient(xf_hist, e[start:stop], power.denominator('binwise', b), M)
            if params.get('proximal', True):
                # proximal (implicit) per-bin leakage: W <- (W - mu G) / (1 + mu L_k); stable for any L_k >= 0,
                # fixed point W_opt / (1 + L_k) = (gamma/eps_k) W_opt as for the LS ridge of Prop. 10
                wn_ = w - params['mu'] * g
                w = np.fft.irfft(np.fft.rfft(wn_, 2 * M) / (1.0 + params['mu'] * spec_leak), 2 * M)[:M]
            else:
                g = g + np.fft.irfft(spec_leak * np.fft.rfft(w, 2 * M), 2 * M)[:M]
                w = w - params['mu'] * g

        elif method == 'leaky_binwise':
            # leaky FD-FxNLMS: w <- (1 - mu * leak) w - mu g  (robustness to S_hat error by leakage)
            g = fd_block_gradient(xf_hist, e[start:stop], power.denominator('binwise', b), M)
            w = (1.0 - params['mu'] * params['leak']) * w - params['mu'] * g

        elif method == 'convex_binwise':
            # convex combination of a fast and a slow FD-FxNLMS on virtual residuals (Ferrer, de Diego,
            # Gonzalez, IEEE TASLP 2013 for FxLMS; normalized mixing update, Azpicueta-Ruiz et al. 2008)
            if b == 0:
                cvx = {'w1': np.zeros(M), 'w2': np.zeros(M), 'a': 0.0, 'p': 1e-6}
            den = power.denominator('binwise', b)
            r1 = dhat[start:stop] + fir_window(xf, cvx['w1'], start, stop)
            r2 = dhat[start:stop] + fir_window(xf, cvx['w2'], start, stop)
            lam = 1.0 / (1.0 + np.exp(-cvx['a']))
            rc = lam * r1 + (1.0 - lam) * r2
            dr = r1 - r2
            cvx['p'] = 0.9 * cvx['p'] + 0.1 * float(dr @ dr)
            cvx['a'] = float(np.clip(cvx['a'] - params.get('mu_a', 1.0) * float(rc @ dr) * lam * (1 - lam) / (cvx['p'] + 1e-12), -4.0, 4.0))
            cvx['w1'] = cvx['w1'] - params['mu_fast'] * fd_block_gradient(xf_hist, r1, den, M)
            cvx['w2'] = cvx['w2'] - params['mu_slow'] * fd_block_gradient(xf_hist, r2, den, M)
            lam = 1.0 / (1.0 + np.exp(-cvx['a']))
            w = lam * cvx['w1'] + (1.0 - lam) * cvx['w2']

        elif method == 'fixed_binwise_virtual':
            r_new = dhat[start:stop] + fir_window(xf, w, start, stop)
            g = fd_block_gradient(xf_hist, r_new, power.denominator('binwise', b), M)
            w = w - params['mu'] * g

        elif method in ('A-GB', 'A-GBm', 'A-band'):
            L = int(params['L'])
            t0 = max(0, stop - L * H)
            r0 = dhat[t0:stop] + fir_window(xf, w, t0, stop)
            r_new = r0[-H:]
            dirs = []
            if method in ('A-GB', 'A-GBm'):
                dirs.append(fd_block_gradient(xf_hist, r_new, power.denominator('global', b), M))
                dirs.append(fd_block_gradient(xf_hist, r_new, power.denominator('binwise', b), M))
                if method == 'A-GBm' and np.any(prev_step):
                    dirs.append(prev_step.copy())
            elif method == 'A-band':
                dirs = band_directions(xf_hist, r_new, power.denominator('binwise', b), M, int(params['K']))
                if params.get('momentum') and np.any(prev_step):
                    dirs.append(prev_step.copy())
            else:
                raise ValueError(method)
            D = np.stack(dirs, axis=1)                      # M x K
            B = np.stack([fir_window(xf, D[:, k], t0, stop) for k in range(D.shape[1])], axis=1)
            G = B.T @ B
            rho = float(params.get('rho', 1e-3)) * float(np.trace(G)) / G.shape[0] + 1e-30
            alpha = -np.linalg.solve(G + rho * np.eye(G.shape[0]), B.T @ r0)
            step = D @ alpha
            w = w + step
            prev_step = step

        elif method in ('K-LS', 'K-EB'):
            # Kernel-regularized (Bayesian) LS with a TC prior
            #   w ~ N(0, c K),  K_ij = alpha^max(i,j)   (exponentially decaying
            # impulse response), v ~ N(0, sigma^2).  Posterior mean:
            #   w = -(K G + (sigma^2/c) I)^{-1} K X^T d_hat,   G = X^T X.
            # K-LS: (alpha, eta = c/sigma^2) fixed (tuned on train seeds).
            # K-EB: (alpha, eta) chosen every hop by maximizing the marginal
            #       likelihood of d_hat (empirical Bayes); sigma^2 profiled out.
            L = int(params['L'])
            t0 = max(0, stop - L * H)
            X = conv_matrix(xf, t0, stop, M)
            G = X.T @ X; bvec = X.T @ dhat[t0:stop]; yy = float(dhat[t0:stop] @ dhat[t0:stop])
            tt = stop - t0
            idx = np.arange(M)
            def post(alpha, eta):
                K = alpha ** np.maximum(idx[:, None], idx[None, :])
                Ainv_rhs = np.linalg.solve(eta * K @ G + np.eye(M), eta * K @ bvec)
                return -Ainv_rhs, K
            if method == 'K-LS':
                w, _ = post(float(params['alpha']), float(params['eta']) / max(float(np.trace(G)) / M, 1e-30))
            else:
                best = None
                gscale = max(float(np.trace(G)) / M, 1e-30)
                for alpha in params['alphas']:
                    K = alpha ** np.maximum(idx[:, None], idx[None, :])
                    # K = U U^T with U lower-triangular-like via Cholesky (jitter)
                    U = np.linalg.cholesky(K + 1e-10 * np.eye(M))
                    UGU = U.T @ G @ U; Ub = U.T @ bvec
                    for eta_rel in params['etas']:
                        eta = eta_rel / gscale
                        A = np.eye(M) + eta * UGU                 # I + eta U^T G U
                        cA = np.linalg.cholesky(A)
                        logdet = 2.0 * np.sum(np.log(np.diag(cA)))
                        z = np.linalg.solve(cA, Ub)
                        quad = yy - eta * float(z @ z)              # d^T (I + eta X K X^T)^{-1} d
                        sig2 = max(quad / tt, 1e-300)
                        nll = 0.5 * (tt * np.log(sig2) + logdet)
                        if best is None or nll < best[0]:
                            best = (nll, alpha, eta)
                w, _ = post(best[1], best[2])
                eb_hist.append((best[1], best[2] * gscale))

        elif method == 'V-SCHED':
            # Theory-scheduled FD-FxNLMS (cost of FD-FxNLMS + one H x M FIR):
            # RLS = Newton step on the newest hop with the *cumulative*
            # covariance.  With the circulant (bin-PSD) approximation of the
            # covariance of an N-sample frame and H new samples per hop, the
            # equivalent step is mu_b = (N/H) / (b + 1) (b = hops since restart).
            #   denom  : 'ema' (project PowerTracker) or 'cum' (running mean of
            #            |X_k|^2 since restart, the RLS-consistent choice)
            #   mu_min : floor for tracking / steady state
            #   avg    : Polyak-Ruppert tail averaging of the applied controller
            bs = b - restart[0] // H
            r_new = dhat[start:stop] + fir_window(xf, w_raw, start, stop)
            if params.get('denom', 'cum') == 'rls':
                # Circulant RLS: den_k = sum_j H * S_hat_k,j, with each hop's PSD
                # estimated from the frame's *nonzero* length (cold start frames
                # are zero-padded), i.e. (H / min(stop, N)) |X_k|^2.  Step = 1.
                fill = min(stop, N)
                cum_pow[:] = cum_pow + (H / fill) * np.abs(Xf) ** 2
                den = cum_pow + float(cfg['regularization_ratio']) * float(np.mean(cum_pow)) + 1e-30
                mu_b = max(float(params.get('scale', 1.0)), float(params.get('mu_min', 0.0)) * (bs + 1))
                mu_b = mu_b / 1.0
            elif params.get('denom', 'cum') == 'cum':
                cum_pow[:] = cum_pow + np.abs(Xf) ** 2
                den = cum_pow / (bs + 1) + float(cfg['regularization_ratio']) * float(np.mean(cum_pow)) / (bs + 1) + 1e-30
            else:
                den = power.denominator('binwise', b)
            if params.get('denom', 'cum') != 'rls':
                mu_b = max(float(params.get('scale', 1.0)) * (N / H) / (bs + 1), float(params.get('mu_min', 0.0)))
            mu_b = min(mu_b, float(params.get('mu_max', 1e9)))
            w_raw = w_raw - mu_b * fd_block_gradient(xf_hist, r_new, den, M)
            if params.get('avg', False) and bs >= int(params.get('avg_start', 4)):
                n_avg[0] += 1
                w_avg[:] = w_avg + (w_raw - w_avg) / min(n_avg[0], int(params.get('avg_max', 10 ** 9)))
                w = w_avg.copy()
            else:
                w_avg[:] = w_raw; n_avg[0] = 0
                w = w_raw.copy()

        elif method == 'PCG-WLS-F':
            # production implementation (src/ffanc_norm/pcg_wls.py): incremental FFT
            # statistics, FD score detector; params map onto PcgWlsConfig fields
            if b == 0:
                from ffanc_norm.pcg_wls import PcgWls as _PCGWLS, PcgWlsConfig as _EC
                _prm = dict(params)
                if _prm.pop('robust_kappa', None) is not None:
                    # Prop. 10: bound on -Re(Delta_k / S_hat_k): eps_k = kappa sigma_Delta / (sqrt(2) |S_hat_k|),
                    # sigma_Delta = ||delta|| from the stated S_hat NMSE spec (per-bin std of a white error)
                    _nm = cfg.get('shat_nmse_db')
                    if _nm is not None:
                        _Sh = np.abs(np.fft.rfft(shat, 2 * M))
                        _dn = 10 ** (float(_nm) / 20) * np.linalg.norm(shat)
                        _prm['reg_eps'] = float(params['robust_kappa']) * _dn / (np.sqrt(2.0) * np.maximum(_Sh, 1e-12))
                _rdx = _prm.pop('robust_dx', None)
                if _rdx is not None:
                    # Prop. 10 + Prop. 12: S_hat uncertainty from an assumed error-mic displacement dx (design spec):
                    # E|dS_k|^2 = 2 |S_k|^2 (1 - sinc(w_k dx / c))  ->  eps_k = kappa sqrt(1 - sinc(w_k dx / c))
                    _z = 2 * np.pi * np.arange(M + 1) / (2 * M) * fs * float(_rdx) / 343.0
                    _prm['reg_eps'] = float(_prm.pop('robust_kappa_dx', 2.0)) * np.sqrt(np.maximum(1.0 - np.sinc(_z / np.pi), 0.0))
                _bdx = _prm.pop('robust_bound_dx', None)
                _brs = _prm.pop('robust_rs', 0.3); _bp = _prm.pop('robust_p', 0.025)
                if _bdx is not None:
                    _prm['reg_eps'] = movement_bound(shat, M, fs, float(_bdx), float(_brs), float(_bp))
                _sidT = _prm.pop('sid_T', 0.25); _sidR = _prm.pop('sid_range', 1.2)
                _xr0 = _prm.get('sid_xreg')          # 'pdof<c>': window c x the ACTUAL nuisance dimension (T7, 2026-10-23)
                _sid = {'on': bool(_prm.pop('sid', False)),
                        # R4: sid_T = 'dof' -> window n = 4 Lg (each half has dof = n/2 - Lg >= Lg); sid_range = 'spec' ->
                        # search |u| <= D + one grid step (the spec plus the step that makes a boundary hit visible)
                        'T': (4.0 * _sid_lg('direct', shat, M, float(_bdx or 0.1), fs) / fs) if _sidT == 'dof' else
                             ((float(_sidT[3:]) * _sid_lg('direct', shat, M, float(_bdx or 0.1), fs) / fs)   # 'dof<c>': n = c Lg (Theorem A)
                              if (isinstance(_sidT, str) and _sidT.startswith('dof')) else
                              ((float(_sidT[4:]) * _sid_lg(_xr0, shat, M, float(_bdx or 0.1), fs) / fs)
                               if (isinstance(_sidT, str) and _sidT.startswith('pdof')) else float(_sidT))), 'Dres': (lambda z: z if z == 'crb' else float(z))(_prm.pop('sid_Dres', 0.02)), 'lrt': _prm.pop('sid_lrt', None),
                        'grid': (np.round(np.arange(-float(_bdx or 0.1) - 0.005, float(_bdx or 0.1) + 0.005 + 1e-9, 0.005), 4)
                                 if _sidR == 'spec' else
                                 np.round(np.arange(-float(_bdx or 0.1) * float(_sidR), float(_bdx or 0.1) * float(_sidR) + 1e-9, 0.005), 4)),
                        'seen': 0, 'pending': None, 'log': []}
                # sid v2 flags (all off by default -> original sid behaviour): Chow-type constancy test, boundary
                # rejection, retries on a sliding window, re-arming of the full-D ridge at a new event, coarse-to-fine
                # u search, cost spread over hops (decision applied sid_spread hops later)
                _sid.update(chow=_prm.pop('sid_chow', None), edge=bool(_prm.pop('sid_edge', False)),
                            retry=int(_prm.pop('sid_retry', 0)), rearm=bool(_prm.pop('sid_rearm', False)),
                            c2f=_prm.pop('sid_c2f', None), spread=int(_prm.pop('sid_spread', 0)), wchow=_prm.pop('sid_wchow', None), res_split=bool(_prm.pop('sid_res_split', False)), xreg=_prm.pop('sid_xreg', None), cost_exact=bool(_prm.pop('sid_cost_exact', False)), rgate=_prm.pop('sid_retry_gate', None), batch=bool(_prm.pop('sid_batch', False)), sigmode=_prm.pop('sid_sig', 'crb'), confirm=(lambda z: z if z == 'drift' else bool(z))(_prm.pop('sid_confirm', False)),
                            reuse=bool(_prm.pop('sid_reuse', False)), hcache={}, cand=None,
                            fastchol=bool(_prm.pop('sid_fastchol', False)),
                            # R1 + R2 (PARAMETERS_v4.md): confidence-set form of the SHRINK step at one level alpha_s.
                            # Validity tests (u constancy, controller constancy) at alpha_s; confidence set of attempt k at
                            # alpha_s 2^-(k+1) (alpha spending: family coverage >= 1 - alpha_s per event); no u = 0 test
                            # (0 in the set -> keep S_hat), no edge rule (set reaching the search boundary -> retry), no
                            # retry count (until the next event).
                            log_ridge=bool(_prm.pop('log_ridge', False)), rs_track=bool(_prm.pop('sid_rs_track', False)),
                            cs=_prm.pop('sid_cs', None),
                            seq=bool(_prm.pop('sid_seq', False)), seq_log=[], cs_center=_prm.pop('sid_cs_center', 'ml'),
                            D=float(_bdx or 0.1), tries=0, due=None, apply=None, decided=False, flq=[])
                if _sid['wchow'] == 'auto':
                    _sid['wchow'] = 0.01
                _sid['v2'] = bool(_sid['chow'] is not None or _sid['edge'] or _sid['retry'] or _sid['rearm']
                                  or _sid['c2f'] is not None or _sid['spread'] or _sid['wchow'] is not None or bool(_sid['cs'])
                                  or _sid['xreg'] is not None)
                # Theorem A diagnostic (new flag thmA_log = horizon in samples after the first event; off by default):
                # per hop the information quantity ||P_perp(Psi) (S(0) - S(u1)) * y||^2 on [tau, stop) for a u1 grid,
                # the residual energy of e - S_hat*y on the same lag space, E*(0, u1) and the achieved price.
                _sid['thA'] = int(_prm.pop('thmA_log', 0)); _sid['thA_log'] = []
                _sid['vpower'] = bool(_prm.pop('sid_vpower', False)); _sid['vgrow'] = False
                # sid_post (2026-10-23, self-revealing changes): after an accepted SHRINK keep re-running the 1-parameter
                # check on the latest T samples every T/2 around the current S_hat; the plant still moving (validity test
                # rejects, or an informative confidence set that excludes the current S_hat, i.e. u = 0) -> re-arm the
                # full-spec ridge and restart the identification; uninformative set (no transient = nothing moves) -> stop.
                _sid['post_on'] = bool(_prm.pop('sid_post', False)); _sid['post'] = None; _sid['post_log'] = []
                _sid['bias'] = bool(_prm.pop('sid_bias', False)); _sid['s2_0'] = None
                _sid['gof'] = bool(_prm.pop('sid_gof', False)); _sid['dof0'] = None
                # sid_adapt (2026-10-23, Theorem A trade-off): release an accepted SHRINK decision only when one more
                # step of waiting (Delta = Lg/2) costs more ridge excess than it saves in residual ridge over the horizon
                # 1/a: (E_full - E_res(n)) Delta >= (E_res(n) - E_res(n + Delta)) T_rem; otherwise re-check on the
                # window grown from the event; at most 4 Lg (the v5.2 window).
                _sid['adapt'] = bool(_prm.pop('sid_adapt', False)); _sid['agrow'] = False; _sid['adapt_log'] = []
                # sid_asym (2026-10-23, cost asymmetry of the two decisions): at the early check (n < 4 Lg) a release that
                # keeps S_hat (0 in the confidence set) is applied (no rebuild; errors covered by the residual spec and the
                # confirmation checks); an S_hat update (0 outside the set: rebuild + loop error if wrong) waits for the
                # window grown from the event to 4 Lg (v5.2 evidence) before it is applied.
                _sid['asym'] = bool(_prm.pop('sid_asym', False))
                # sid_prior (2026-10-23, Theorem A'): physical prior on the nuisance (primary path) for the SHRINK test;
                # value = Dp (primary-path movement spec in m, e.g. 0.3); window n = sid_prior_c x d_eff(Lg) (the flat-prior
                # rule n = c p with p replaced by the effective dimension); rejected checks re-run on the window grown
                # from the event.
                _sid['prior_Dp'] = _prm.pop('sid_prior', None); _sid['prior_c'] = float(_prm.pop('sid_prior_c', 3.0))
                _sid['prior_joint'] = int(_prm.pop('sid_prior_joint', 0))      # number of u_p grid points (0 = linearized delay)
                _sid['prior_exact'] = bool(_prm.pop('sid_prior_exact', False))   # exact marginal dof + exact null law of wchow
                _sid['prior_model'] = str(_prm.pop('sid_prior_model', 'diffuse'))   # 'field': conditional Gaussian-field prior
                _sid['prior_L'] = _prm.pop('sid_prior_L', None)     # nuisance length under the prior (default: flat Lg = M + K)
                _sid['prior_rev'] = int(_prm.pop('sid_prior_rev', 1))  # 2: review fixes R5-R9 (P1_PRIOR_SHRINK.md sec. 6-7)
                # sid_sub (2026-10-24): SHRINK check with the change-adapted subspace nuisance (change_basis): coverage of
                # the predicted reverberant change (e.g. 0.9); sid_sub_basis 'taps' | 'dpss'; window = sid_sub_c x r.
                # The post-acceptance confirmation keeps the full x-lag model (worst-case check at the full dimension).
                _sid['sub_cov'] = _prm.pop('sid_sub', None); _sid['sub_kind'] = str(_prm.pop('sid_sub_basis', 'taps'))
                _sid['sub_c'] = float(_prm.pop('sid_sub_c', 3.0)); _sid['sub'] = None; _sid['sub_log'] = []
                # sid_s2pre (2026-10-24): calibrate the SHRINK statistics by the noise variance of a pre-event window
                # (x-lag LS on 4 Lg samples ending a guard of sid_s2pre_guard samples before the event); use with a
                # shorter window rule (sid_T 'dof2.x'); THEORY_CLOSURE.md sec. 3
                _sid['s2pre'] = bool(_prm.pop('sid_s2pre', False)); _sid['s2pre_g'] = int(_prm.pop('sid_s2pre_guard', 1024))
                _sid['s2ref'] = None; _sid['s2pre_log'] = []
                # review 2026-10-24: fixes 1 and 2 change the frozen v6.2 behaviour in multi-event runs -> flag (off = v6.2)
                _sid['s2pre_fix'] = bool(_prm.pop('sid_s2pre_fix', False))
                _sid['post_space'] = _prm.pop('sid_post_space', None)
                # sid_consist (2026-10-24, DRIFT_DETECTION.md): S_hat-consistency detector in the calibrated state.
                # F = (J(0; [t - c Lg, t)) / (c Lg - Lg)) / (J_ref / d_ref): residual of d_hat = e - S_hat * y on Lg lags
                # of x (exact F law in closed loop when S = S_hat and the plant is constant on the window, Prop. CL);
                # evaluated every sid_consist_every hops at level sid_consist (per evaluation); reference = 4 Lg samples
                # at start-up (noise level; kept for the run, as sid_s2pre assumes); suspended from an event to the next
                # acceptance (the movement set is expanded then); after an acceptance the windows start at the accepted
                # check window. Rejection -> event at the window start.
                _sid['cons'] = None
                if _prm.get('sid_consist'):
                    _sid['cons'] = {'fa': float(_prm.pop('sid_consist')), 'k': int(_prm.pop('sid_consist_every', 1)),
                                    'c': float(_prm.pop('sid_consist_c', 2.0)), 'ref': None, 'active': False,
                                    'init': False, 'log': [],
                                    # 'pre': only before the first event (S_hat = calibrated S exactly); 'all': also after
                                    # acceptances (null S = S(u_hat), violated by the 1-D model misfit)
                                    'mode': str(_prm.pop('sid_consist_mode', 'all')),
                                    'anchor': _prm.pop('sid_consist_anchor', None)}
                else:
                    _prm.pop('sid_consist', None); _prm.pop('sid_consist_every', None); _prm.pop('sid_consist_c', None)
                    _prm.pop('sid_consist_mode', None); _prm.pop('sid_consist_anchor', None)
                # sid_s2pre_fb = 'dof<c>' (2026-10-24, v6.2 candidate): fallback to the in-window calibration with the
                # window c Lg once the event is c Lg old (Prop. W (b)); the pre-event calibration (Prop. W (a)) is used only
                # for the earlier, shorter windows. Guards against a noise-level / model-misfit change at the movement.
                _fb = _prm.pop('sid_s2pre_fb', None)
                _sid['T_short'] = _sid['T']
                _sid['T_long'] = (float(_fb[3:]) * _sid_lg('direct', shat, M, float(_bdx or 0.1), fs) / fs) if _fb else None
                _sid['s2_on'] = False

                def _build_prior(_p0, _win, _Dp_scale=1.0):
                    """Prior of the x-lag nuisance at an event at _p0 from the pre-event window [_p0 - 4L, _p0) (or _win =
                    (lo, hi)); sets _sid['prior'], 'Tev', 'due'; returns the construction flops."""
                    _Lgp = int(_sid.get('prior_L') or _sid_lg(_sid['xreg'], shat, M, _sid['D'], fs)); _n0 = 4 * _Lgp
                    _lo, _hi = (_p0 - _n0, _p0) if _win is None else _win
                    if _lo < len(shat) or _hi - _lo < _Lgp + 1:
                        _sid['prior'] = None; _sid['Tev'] = None; return 0.0
                    _mdl = _sid['prior_model']
                    _np_ = nuisance_prior(x, y, e, shat, _lo, _hi, _Lgp, float(_sid['prior_Dp']) * _Dp_scale, fs,
                                          joint=_sid['prior_joint'], model=_mdl.replace('+amp', ''), amp=_mdl.endswith('+amp'),
                                          rev=_sid['prior_rev'])
                    _th, _Lam, _s2p, _Sg = _np_[:4]; _fam = _np_[4] if len(_np_) > 4 else None
                    _prm_ = _np_[5] if len(_np_) > 5 else None
                    _idx = np.arange(_lo, _hi)[:, None] - np.arange(_Lgp)[None, :]
                    _Xp = np.where(_idx >= 0, x[np.clip(_idx, 0, None)], 0.0); _Gp = (_Lgp / (_hi - _lo)) * (_Xp.T @ _Xp)
                    _deff = float(np.trace(np.linalg.solve(_Gp + _Lam, _Gp)))
                    _Tev = int(max(2 * H, np.ceil(_sid['prior_c'] * _deff / H) * H))
                    _sid['prior'] = (_th, _Lam, _fam, _sid['prior_exact'], _s2p if _sid['prior_exact'] else None,
                                     _sid['prior_rev'], _prm_)
                    _sid['Tev'] = _Tev; _sid['due'] = _p0 + _Tev
                    _sid['prior_log'].append((int(_p0), int(_Lgp), float(_deff), int(_Tev), float(_s2p)))
                    return sid_cost_prior_build(_hi - _lo, _Lgp, 0 if _fam is None else len(_fam), _mdl)
                _sid['prior'] = None; _sid['Tev'] = None; _sid['prior_log'] = []
                # multi-window aggregation, PCG-WLS (multi-window) (flag mem_bank = list of window lengths in hops; off by default)
                _mb = _prm.pop('mem_bank', None); _mbs = float(_prm.pop('mem_share', 0.02)); _mbe = float(_prm.pop('mem_eta', 1.0)); _mbc = (lambda z: z if isinstance(z, (list, tuple, set)) else bool(z))(_prm.pop('mem_cheap', False))
                if _mb:
                    from ffanc_norm.pcg_wls_mw import PcgWlsMultiWindow as _MW
                    _mbp = _prm.pop('mem_primary', None)     # (v6.1) window (hops) of the detecting member; None = longest
                    _mbl = _prm.pop('mem_long_sched', None)  # (2026-10-24, cost) (every, k) of the longer members
                    _mk = lambda **kw: _MW(_EC(M=M, H=H, **kw), _mb, _mbe, _mbs, cheap=_mbc, primary=_mbp, long_sched=_mbl)
                else:
                    _mk = lambda **kw: _PCGWLS(_EC(M=M, H=H, **kw))
                _ep = _mk(**_prm)
            _f0 = _ep.fft.flops(); _extra_fl = 0.0
            if b == 0 and _sid.get('on') and _sid.get('cons') is not None:
                def _cons_J(lo, hi, Lg_, resid=False):
                    """J(0) on [lo, hi): residual of e - S_hat * y on Lg_ lags of x (generalized Schur factor) and flops;
                    resid: also the residual vector (back solve + X beta: Lg^2 + 2 FFTs)."""
                    from scipy.linalg import solve_triangular as _stc
                    a0 = max(lo - len(shat), 0)
                    dh_ = (e[a0:hi] - np.convolve(y[a0:hi], shat)[:hi - a0])[lo - a0:]
                    Lc = gschur_chol(x, lo, hi, Lg_)
                    idx = np.arange(lo, hi)[:, None] - np.arange(Lg_)[None, :]
                    Xc = np.where(idx >= 0, x[np.clip(idx, 0, None)], 0.0)
                    bb = Xc.T @ dh_                                                     # 2 FFTs in the cost
                    zz = _stc(Lc, bb, lower=True)
                    nf_ = int(2 ** np.ceil(np.log2(hi - lo + Lg_ + len(shat))))
                    fl = 6 * 2.5 * nf_ * np.log2(nf_) + 9.0 * Lg_ * (Lg_ + 1) + 1.0 * Lg_ ** 2 + 4.0 * (hi - lo)
                    Jv = max(float(dh_ @ dh_ - zz @ zz), 1e-300)
                    if not resid:
                        return Jv, fl
                    rv = dh_ - Xc @ _stc(Lc.T, zz, lower=False)
                    return Jv, fl + 1.0 * Lg_ ** 2 + 2 * 2.5 * nf_ * np.log2(nf_), rv

                def _cons_loc(rv, lo, step):
                    """ML variance change point of the consistency residual on the window (change of the plant inside)."""
                    cs_ = np.concatenate([[0.0], np.cumsum(rv ** 2)]); n_ = len(rv); best_, tb = -np.inf, lo
                    for k_ in range(step, n_ - step + 1, step):
                        s1_ = max(cs_[k_] / k_, 1e-300); s2_ = max((cs_[-1] - cs_[k_]) / (n_ - k_), 1e-300)
                        ll_ = -k_ * np.log(s1_) - (n_ - k_) * np.log(s2_)
                        if ll_ > best_:
                            best_, tb = ll_, lo + k_
                    return int(tb)

                def _cons_ref(lo, hi):
                    _cs = _sid['cons']; _Lg = _sid_lg('direct', shat, M, _sid['D'], fs)
                    if hi - lo <= _Lg + 8:
                        _cs['active'] = False; return 0.0
                    Jr, fl = _cons_J(lo, hi, _Lg)
                    _cs['ref'] = (Jr, (hi - lo) - _Lg, hi); _cs['active'] = True
                    return fl
            if getattr(_ep.cfg, 'det_risk', False):
                # det_risk (framework v2 step 1): switching cost inputs for the detector, from the SHRINK state.
                # T_lat = check window + decision spread; under 'hold' with a pending SHRINK the full ridge stays for
                # T_rem more samples and is ~0 after release (residual spec); otherwise the current ridge stays.
                _Kd = max(1, _sid['spread']) if _sid.get('on') else 1
                _Tl = (int(_sid['T'] * fs) + _Kd * H) if _sid.get('on') else 10 ** 9
                _pend = bool(_sid.get('on') and _sid.get('pending') is not None and not _sid.get('decided'))
                _Trem = 0
                if _pend:
                    _Trem = (_sid['apply'][0] - start) if _sid.get('apply') is not None else (max(int(_sid['due']) - start, 0) + _Kd * H)
                _key = (id(shat), float(_brs))
                if _sid.get('_dr_key') != _key:
                    _sid['_dr_key'] = _key
                    _sid['_dr_eps'] = movement_bound(shat, M, fs, float(_bdx or 0.1), float(_brs), float(_bp))
                    _sid['_dr_rho'] = movement_rho(shat, M, fs, float(_bdx or 0.1), float(_brs),
                                                   nu=(41 if getattr(_ep.cfg, 'det_risk_v2', False) else 201))
                _ep.cfg.det_risk_eps = _sid['_dr_eps']; _ep.cfg.det_risk_rho = _sid['_dr_rho']; _ep.cfg.det_risk_T = int(_Tl)
                _ep.cfg.det_risk_Trem = int(max(_Trem, 0)); _ep.cfg.det_risk_hold0 = _pend
                _ep.cfg.det_risk_hz = int(round(1.0 / _mbs)) if _mbs > 0 else 50   # horizon 1/a (memory share a)
            w = _ep.update(xf[start:stop], dhat[start:stop]).copy()
            if _sid.get('thA') and _ep.resets:
                _tau = int((_ep.locs[0] if _ep.locs else _ep.resets[0])) if not _sid.get('thA_tau') else _sid['thA_tau']
                _sid['thA_tau'] = _tau
                if stop - _tau <= _sid['thA']:
                    _sid['thA_log'].append(thmA_diag(x, y, e, shat, _tau, stop, M, fs, float(_bdx or 0.1), float(_brs),
                                                     float(_bp), _ep, w))
            if _sid.get('log_ridge'):
                # price of robustness (Thm 4 term iii, per bin): W_reg = P/(P+lam) W_T -> bias b = W_reg lam/P;
                # excess per sample = b^T G b / n = (1/(n2 n)) sum_k g_k P_k |W_k|^2 (lam_k/P_k)^2
                _m = _ep.members[_ep.ip] if hasattr(_ep, 'members') else _ep
                _Cf = _m._circ(_m.r); _lam = _m._robust_reg(_Cf)
                if _lam is None:
                    _rlog.append(0.0)
                else:
                    _P = np.maximum(_Cf.real, 1e-3 * np.max(_Cf.real)); _W = np.fft.rfft(w, _m.n2)
                    _g = np.full(len(_P), 2.0); _g[0] = _g[-1] = 1.0
                    _rlog.append(float(np.sum(_g * _P * np.abs(_W) ** 2 * (_lam / _P) ** 2) / (_m.n2 * max(_m.stop - _m.t0, 1))))
            if _sid['on'] and _sid['v2']:
                if (_sid.get('s2_on') and _sid.get('T_long') and _sid['pending'] is not None
                        and stop - _sid['pending'] >= _sid['T_long'] * fs):
                    # fallback (sid_s2pre_fb): in-window calibration on the long window from now on for this event
                    _sid['s2ref'] = None; _sid['s2_on'] = False; _sid['T'] = _sid['T_long']
                    _sid['s2pre_log'].append((int(stop), 'fallback'))
                _fsT = int(_sid['T'] * fs)
                if _sid['reuse']:
                    # hop-aligned retry geometry: window 2*Delta, retries every Delta (Delta a multiple of H), so the
                    # first half of a retry window is exactly the second half of the previous one
                    _fsT = 2 * H * max(1, int(round(_fsT / (2 * H))))
                if len(_ep.resets) > _sid['seen']:
                    _ev_total[0] += len(_ep.resets) - _sid['seen']   # review fix 3: survives bank rebuilds
                    if _sid.get('cons') is not None:
                        _sid['cons']['active'] = False; _sid['cons']['init'] = True
                    _sid['seen'] = len(_ep.resets)
                    _sid['pending'] = (_ep.locs[-1] if _ep.locs else _ep.resets[-1]); _sid['tries'] = 0
                    _sid['due'] = _sid['pending'] + _fsT; _sid['apply'] = None   # a new event cancels an unapplied decision
                    _sid['vgrow'] = False; _sid['post'] = None; _sid['agrow'] = False
                    if _sid.get('prior_Dp'):
                        _extra_fl += _build_prior(int(_sid['pending']), None)
                    if _sid.get('s2pre'):
                        _p0 = int(_sid['pending']); _Lgq = _sid_lg(_sid['xreg'], shat, M, _sid['D'], fs); _n0 = 4 * _Lgq
                        _b0 = _p0 - _sid['s2pre_g']
                        if _b0 - _n0 > len(shat):
                            _, _s2q, _dq = pre_event_theta(x, y, e, shat, _b0 - _n0, _b0, _Lgq, ret_s2=True)
                            _sid['s2ref'] = (float(_s2q), int(_dq)); _sid['s2_on'] = True
                            if _sid.get('T_long'):
                                _sid['T'] = _sid['T_short']
                            _sid['s2pre_log'].append((int(_p0), float(_s2q), int(_dq)))
                            _nfq = int(2 ** np.ceil(np.log2(2 * _n0)))
                            _extra_fl += 3 * 2.5 * _nfq * np.log2(_nfq) + 4.0 * _Lgq ** 2 + _Lgq ** 3 / 3.0 + 2.0 * _n0 * _Lgq
                        else:
                            # review 2026-10-24 (fix 1): no pre-event window -> no calibration: the long window with the
                            # in-window noise level (Prop. W (b)); the short window alone would have little power
                            _sid['s2ref'] = None; _sid['s2_on'] = False
                            if _sid.get('T_long') and _sid['s2pre_fix']:
                                _sid['T'] = _sid['T_long']
                        if _sid['s2pre_fix']:
                            # review 2026-10-24 (fix 2, flag sid_s2pre_fix): the first retry time of this event uses the
                            # window just set (v6.2 as frozen used the previous event's window for it)
                            _fsT2 = int(_sid['T'] * fs)
                            if _sid['reuse']:
                                _fsT2 = 2 * H * max(1, int(round(_fsT2 / (2 * H))))
                            _sid['due'] = _sid['pending'] + _fsT2
                    if _sid.get('sub_cov'):
                        _p0 = int(_sid['pending']); _Lgs = _sid_lg('direct', shat, M, _sid['D'], fs); _n0 = 4 * _Lgs
                        if _p0 > _n0 + len(shat):
                            _ths, _vth = pre_event_theta(x, y, e, shat, _p0 - _n0, _p0, _Lgs)
                            _Bs, _bi = change_basis(_ths, shat, fs, _sid['D'], float(_sid['sub_cov']), _sid['sub_kind'], vth=_vth)
                            _Ks = _sid_lg('ybar', shat, M, _sid['D'], fs) - 1
                            _r = _Bs.shape[1] + _Ks
                            from scipy.signal import fftconvolve as _fc
                            _xb = np.stack([_fc(x, _Bs[:, j])[:len(x)] for j in range(_Bs.shape[1])], 1)
                            _es = _fc(x, _ths)[:len(e)]           # x * theta_bar (e is filled hop by hop: subtract at check time)
                            _Tev = int(max(2 * H, np.ceil(_sid['sub_c'] * _r / H) * H))
                            _sid['sub'] = {'xb': _xb, 'e': _es, 'K': _Ks, 'r': _r, 'Tev': _Tev}
                            _sid['due'] = _sid['pending'] + _Tev
                            _sid['sub_log'].append((int(_p0), int(_Lgs), dict(_bi), int(_Ks), int(_r), int(_Tev)))
                            _nfs = int(2 ** np.ceil(np.log2(2 * len(x))))
                            _extra_fl += (_Bs.shape[1] + 1) * 3 * 2.5 * _nfs * np.log2(_nfs) + 4.0 * _n0 * _Lgs ** 2 / 2 + _Lgs ** 3 / 3.0
                        else:
                            _sid['sub'] = None
                    if _sid.get('bias') or _sid.get('gof'):
                        # residual level before the event with the SAME model as the check (two halves, Lg x-lags each,
                        # u = 0): sigma0^2 = J_pre / (n - 2 Lg - 1), so J(u_hat)/sigma0^2 - dof estimates ||P r||^2/sigma0^2
                        _p0 = int(_sid['pending']); _n0 = max(int(_fsT), H)
                        _sid['s2_0'] = pre_event_s2(x, y, e, shat, max(_p0 - _n0, 0), _p0,
                                                    _sid_lg(_sid['xreg'], shat, M, _sid['D'], fs)) if _p0 > _n0 else None
                        _sid['dof0'] = max(_n0 - 2 * _sid_lg(_sid['xreg'], shat, M, _sid['D'], fs) - 1, 1)
                    _sid['cand'] = None
                    if _sid['rearm'] and _sid['decided']:
                        # the next movement may again be up to D: restore the full-spec ridge around the current S_hat
                        _ep.cfg.reg_eps = movement_bound(shat, M, fs, _sid['D'], float(_brs), float(_bp))
                        _sid['decided'] = False
                _gate_ok = True
                if (_sid['rgate'] is not None and _sid['pending'] is not None and _sid['tries'] > 0
                        and stop >= _sid['due'] and getattr(_ep, 'pi_hist', None)):
                    # retry only when the memory posterior prefers the long window (plant no longer drifting);
                    # otherwise postpone by one hop (no check, no cost)
                    _gate_ok = float(_ep.pi_hist[-1][_ep.ip]) >= float(_sid['rgate'])
                    if not _gate_ok:
                        _sid['due'] = stop + H
                if _gate_ok and _sid['pending'] is not None and stop >= _sid['due']:
                    _a = (int(_sid['pending']) if (_sid['seq'] or (_sid['tries'] == 0 and _sid.get('cand') is None) or _sid.get('vgrow') or _sid.get('agrow')
                                                     or _sid.get('prior') is not None or _sid.get('sub') is not None)
                          else max(int(_sid['pending']), stop - _fsT))
                    _csl = _sid['cs']
                    _sb = _sid.get('sub')
                    u_hat, _inf, _nev = sid_profile2(x, y, (e - _sb['e'] if _sb is not None else e), shat, _a, stop, M, _sid['grid'], float(_brs), fs,
                                                     None if _csl else _sid['lrt'], None if _csl else _sid['chow'],
                                                     False if _csl else _sid['edge'], _sid['c2f'],
                                                     float(_csl) if _csl else _sid['wchow'],
                                                     (_sb['r'] if _sb is not None else
                                                      (len(_sid['prior'][0]) if _sid.get('prior') is not None else _sid_lg(_sid['xreg'], shat, M, _sid['D'], fs))), _sid['sigmode'],
                                                     s2ref=_sid.get('s2ref'),
                                                     cache=(_sid['hcache'] if _sid['reuse'] and not str(_sid['xreg']).startswith('ctrl') and _sb is None else None),
                                                     yreg=_SubReg(_sb['xb'], x, _wlog, H, _sb['K']) if _sb is not None else
                                                     _CtrlReg(x, _wlog, shat, H, (_sid_lg('ctrl', shat, M, _sid['D'], fs) - 1) // 2,
                                                                   np.asarray(w, float), _a, stop, not _sid['xreg'].startswith('ctrlc'),
                                                                   int(_sid['xreg'][5:] or 0) if _sid['xreg'].startswith('ctrl2')
                                                                   else int(_sid['xreg'].lstrip('ctrlc') or 0),
                                                                   two=_sid['xreg'].startswith('ctrl2'))
                                                     if str(_sid['xreg']).startswith('ctrl') else
                                                     _ybar_reg(x, _wlog, shat, H, _sid_lg('ybar', shat, M, _sid['D'], fs) - 1,
                                                                    int(_sid['xreg'][4:] or 0))
                                                     if str(_sid['xreg']).startswith('ybar') else None,
                                                     ci_alpha=(float(_csl) * 2.0 ** -(_sid['tries'] + 1)) if _csl else 0.05,
                                                     chow_alpha=float(_csl) if _csl else None,
                                                     fastchol=_sid['fastchol'],
                                                     ci_mix=((float(_csl) if _csl else 0.01), _sid['D']) if _sid['seq'] else None,
                                                     vpower=((float(_csl) if _csl else 0.01), (float(_csl) if _csl else 0.01),
                                                             float(_bp), 0.005) if _sid.get('vpower') else None,
                                                     bias_s2=_sid.get('s2_0') if _sid.get('bias') else None,
                                                     gof=((_sid['s2_0'], _sid['dof0'], float(_csl) if _csl else 0.01)
                                                          if (_sid.get('gof') and _sid.get('s2_0')) else None),
                                                     prior=_sid.get('prior'))
                    _sid['vgrow'] = bool(_sid.get('vpower') and _inf.get('vpower_fail'))
                    if _csl and u_hat is not None:
                        if _inf.get('ci_edge'):
                            u_hat = None                        # confidence set reaches the search boundary: not informative
                        elif (_sid.get('cs_center') == 'minimal' and _inf.get('ci_set')
                              and _inf['ci_set'][0] <= 0.0 <= _inf['ci_set'][1]):
                            u_hat = 0.0                         # S_hat is in the set: minimal change (variant)
                        # default: centre = u_hat (ML point of the set); the ridge covers the whole set either way
                    if _sid['seq']:
                        # v6 prototype: anytime-valid set C_t on the growing window since the event, every hop
                        _sci = _inf.get('ci_set')
                        if u_hat is None or _inf.get('ci_edge') or _sci is None:
                            if _sid.get('seq_shrunk'):           # no valid information (model rejected): full movement set
                                _ep.cfg.reg_eps = movement_bound(shat, M, fs, _sid['D'], float(_brs), float(_bp))
                                _sid['seq_shrunk'] = False
                            u_hat = None
                        elif _sci[0] <= 0.0 <= _sci[1]:
                            # S_hat in the set: release the ridge continuously to the set's extent around S_hat
                            _Dt = min(max(abs(_sci[0]), abs(_sci[1]), 0.005), _sid['D'])
                            _ep.cfg.reg_eps = movement_bound_split(shat, M, fs, _Dt, _sid['D'], float(_brs), float(_bp))
                            _sid['seq_shrunk'] = True; _sid['seq_log'].append((int(stop), float(_Dt)))
                            u_hat = 0.0 if _Dt <= 0.005 + 1e-9 else None
                        # else: 0 outside the set -> recentre on S(u_hat) through the acceptance path below
                    if _sid['reuse']:
                        for _k in [k for k in _sid['hcache'] if k[1] < stop - 2 * _fsT]:
                            del _sid['hcache'][_k]                 # half windows that can no longer recur
                    _nw = stop - _a; _nf = int(2 ** np.ceil(np.log2(2 * _nw)))
                    _K = max(1, _sid['spread'])
                    if _sid.get('sub') is not None and _sid.get('cost_exact'):
                        # dense QR of the n x r regressors per half (sid_cost_xreg) + the y_bar lags (one FFT convolution)
                        _cst = sid_cost_xreg(_nw, _sid['sub']['r'], len(shat), _nev, True) + 2 * 3 * 2.5 * _nf * np.log2(_nf)
                        if _sid['sigmode'] in ('hac', 'profile'):
                            _cst += 2.0 * 128 * _nw + 6.0 * _nw
                    elif _sid.get('prior') is not None and _sid.get('cost_exact'):
                        _pr = _sid['prior']; _Om, _Dm = _prior_members(_pr)
                        _cst = sid_cost_prior(_nw, len(_pr[0]), len(shat), _nev, len(_Om), 0 if _Dm is None else len(_Dm),
                                              True, bool(_pr[3]), _sid['sigmode'] in ('hac', 'profile'), _sid['prior_rev'],
                                              _inf.get('wchow_nsig'))
                        if _sid['sigmode'] in ('hac', 'profile'):
                            _cst += 2.0 * 128 * _nw + 6.0 * _nw
                    elif _sid['xreg'] is not None and _sid.get('cost_exact'):
                        _Lg = _sid_lg(_sid['xreg'], shat, M, _sid['D'], fs)
                        if str(_sid['xreg']).startswith('ctrl'):
                            _cst = sid_cost_ctrl(_nw, _Lg, len(shat), M, H, _nev, (_sid['wchow'] is not None or bool(_sid['cs'])))
                        elif str(_sid['xreg']).startswith('ybar'):
                            _cst = sid_cost_ybar(_nw, _Lg - 1, len(shat), M, H, _nev, (_sid['wchow'] is not None or bool(_sid['cs'])),
                                                 reuse=_inf.get('reuse') if _sid['reuse'] else None)
                        elif _sid['fastchol']:
                            _cst = sid_cost_xreg_fast(_nw, _Lg, len(shat), _nev, (_sid['wchow'] is not None or bool(_sid['cs'])),
                                                      reuse=_inf.get('reuse') if _sid['reuse'] else None,
                                                      resid=_sid['sigmode'] in ('hac', 'profile'))
                        else:
                            _cst = sid_cost_xreg(_nw, _Lg, len(shat), _nev, (_sid['wchow'] is not None or bool(_sid['cs'])),
                                                 reuse=_inf.get('reuse') if _sid['reuse'] else None)
                        if _sid['sigmode'] in ('hac', 'profile'):
                            _cst += 2.0 * 128 * _nw + 6.0 * _nw     # sandwich variance (K = 128 lags) on the residual
                    else:
                        _cst = _nev * (3 * 2.5 * _nf * np.log2(_nf) + 16 * 4 * 2.5 * 2 * M * np.log2(2 * M))
                    _sid['flq'] += [_cst / _K] * _K
                    if _sid.get('log_ridge'):
                        # Theorem C bookkeeping: passive information (CRB sigma_u, window), noise level, and the per-unit-power
                        # information / cost of a white auxiliary signal through the 1-parameter model at the current S_hat
                        _dd = 1e-3
                        _dS = (shat_shift(shat, _dd, float(_brs), fs) - shat_shift(shat, -_dd, float(_brs), fs)) / (2 * _dd)
                        _dual.append((int(stop), int(_nw), _inf.get('sig_u_crb'), _inf.get('s2'), float(_dS @ _dS),
                                      float(shat @ shat), int(_a)))
                    _sid['log'].append((stop, float('nan') if u_hat is None else u_hat, _inf['chow'], _inf['lrt'],
                                        int(_inf['edge']), _a, _nev, _inf.get('wchow'), _inf.get('sig_u_crb'),
                                        _inf.get('sig_u_hac'), _inf.get('sig_u_split')))
                    _need_cf = bool(_sid['confirm'])
                    if _sid['confirm'] == 'drift' and getattr(_ep, 'pi_hist', None):
                        # confirmation only while the memory posterior indicates drift: mean weight of the short
                        # members over the check window >= 0.5 (abrupt changes that are over need no confirmation)
                        _nh = max(1, (stop - _a) // H)
                        _pis = np.array(_ep.pi_hist[-_nh:])
                        _need_cf = float(1.0 - _pis[:, _ep.ip].mean()) >= 0.5
                    if _need_cf and u_hat is not None:
                        # confirmed acceptance: a candidate is applied only if the next check (T/2 later, latest T
                        # seconds) also accepts and the two confidence sets overlap (u not drifting = movement over)
                        _z = 1.959963984540054
                        _cs = _inf.get('ci_set') or ((u_hat - _z * (_inf.get('sig_u') or 0.0), u_hat + _z * (_inf.get('sig_u') or 0.0)))
                        _cd = _sid.get('cand')
                        if _cd is not None and _cd[0] <= _cs[1] + 1e-9 and _cs[0] <= _cd[1] + 1e-9:
                            _sid['cand'] = None; _sid['pending'] = None
                            _sid['apply'] = (stop + (_K - 1) * H, u_hat, _a, _inf.get('sig_u'),
                                             (_inf.get('ci_set'), _inf.get('ci_edge'), _inf.get('ci_slack')))
                        elif _sid['tries'] < _sid['retry']:
                            if _cd is not None:
                                _sid['tries'] += 1                         # sets disjoint: still moving
                            _sid['cand'] = _cs; _sid['due'] = stop + _fsT // 2
                        else:
                            _sid['cand'] = None; _sid['pending'] = None
                    elif u_hat is None and (_csl or _sid['tries'] < _sid['retry']):
                        _sid['cand'] = None
                        _sid['tries'] += 1; _sid['due'] = stop + (H if _sid['seq'] else (max(H, (_sid['Tev'] // 2 // H) * H) if _sid.get('prior') is not None else
                                                                                  (max(H, (_sid['sub']['Tev'] // 2 // H) * H) if _sid.get('sub') is not None else _fsT // 2)))   # retry (v6: every hop)
                    else:
                        _wait = False
                        if u_hat is not None and _sid.get('asym'):
                            _Lgd = _sid_lg('direct', shat, M, _sid['D'], fs); _nw_ = stop - _a
                            _cs_ = _inf.get('ci_set')
                            _keep = _cs_ is not None and _cs_[0] <= 0.0 <= _cs_[1]
                            if _keep:
                                u_hat = 0.0                              # release around the current S_hat (no rebuild)
                            elif _nw_ < 4 * _Lgd - H // 2:
                                _wait = True                             # S_hat update: more evidence first
                                _sid['due'] = stop + max(H, 4 * _Lgd - _nw_); _sid['agrow'] = True
                            _sid['adapt_log'].append((int(stop), int(_nw_), bool(_keep), bool(_wait)))
                        if u_hat is not None and _sid.get('adapt'):
                            _Lgd = _sid_lg('direct', shat, M, _sid['D'], fs); _nw_ = stop - _a; _Dl = max(H, (_Lgd // 2 // H) * H)
                            if _nw_ + _Dl <= 4 * _Lgd + H // 2 and _inf.get('ci_set') is not None and _inf.get('sig_u'):
                                _cs_ = _inf['ci_set']
                                _Dn = min(max(max(abs(_cs_[0] - u_hat), abs(_cs_[1] - u_hat)), 0.005), _sid['D'])
                                _fac = np.sqrt(max(_nw_ - _Lgd, 1) / max(_nw_ + _Dl - _Lgd, 1))
                                _Dn2 = min(max(_Dn * _fac, 0.005), _sid['D'])
                                _sn = shat_shift(shat, u_hat, float(_brs), fs) if abs(u_hat) > 1e-9 else shat
                                _rb_ = float(_brs) + (float(u_hat) if _sid.get('rs_track') else 0.0)
                                _Ef = ridge_cost(_ep, movement_bound(shat, M, fs, _sid['D'], float(_brs), float(_bp)), w)
                                _Er = ridge_cost(_ep, movement_bound_split(_sn, M, fs, _Dn, _sid['D'], _rb_, float(_bp)), w)
                                _Er2 = ridge_cost(_ep, movement_bound_split(_sn, M, fs, _Dn2, _sid['D'], _rb_, float(_bp)), w)
                                _Trem = H / max(_mbs, 1e-6)
                                _wait = (_Ef - _Er) * _Dl < (_Er - _Er2) * _Trem
                                _sid['adapt_log'].append((int(stop), int(_nw_), float(_Ef), float(_Er), float(_Er2), bool(_wait)))
                                if _wait:
                                    _sid['due'] = stop + _Dl; _sid['agrow'] = True
                        if not _wait:
                            _sid['pending'] = None; _sid['agrow'] = False
                            if u_hat is not None:
                                _sid['apply'] = (stop + (_K - 1) * H, u_hat, _a, _inf.get('sig_u'),
                                                 (_inf.get('ci_set'), _inf.get('ci_edge'), _inf.get('ci_slack')))
                if _sid['apply'] is not None and stop >= _sid['apply'][0]:
                    _, u_hat, _a, _sgu, _ci = _sid['apply']; _sid['apply'] = None
                    from scipy.stats import norm as _norm
                    if _sid['sigmode'] == 'profile' and _ci[0] is not None:
                        # half-width of the profile confidence set around the applied value (+ one coarse step)
                        _Dd = _sid['D'] if _ci[1] else max(abs(_ci[0][0] - u_hat), abs(_ci[0][1] - u_hat)) + float(_ci[2])
                        _Dd = min(max(_Dd, 0.005), _sid['D'])
                    elif _sid['Dres'] == 'crb':
                        # residual distance spec = one-sided (1 - p) confidence half-width of u_hat, floored at the grid step
                        _Dd = max(float(_norm.isf(float(_bp))) * (_sgu if _sgu is not None else np.inf), 0.005)
                        _Dd = min(_Dd, _sid['D'])
                    else:
                        _Dd = float(_sid['Dres'])
                    _snew = shat_shift(shat, u_hat, float(_brs), fs) if abs(u_hat) > 1e-9 else shat
                    # Theorem 6 step 3: the new S_hat has speaker distance r + u_hat (sid_rs_track; off = r kept)
                    _rb = float(_brs) + (float(u_hat) if _sid.get('rs_track') else 0.0)
                    if _sid['res_split']:
                        eps_res = movement_bound_split(_snew, M, fs, _Dd, _sid['D'], _rb, float(_bp))
                    else:
                        eps_res = movement_bound(_snew, M, fs, _Dd, _rb, float(_bp))
                    _sid['log'][-1] = tuple(_sid['log'][-1]) + (_sgu, _Dd)
                    if abs(u_hat) <= 1e-9:
                        _ep.cfg.reg_eps = eps_res
                    else:
                        shat = shat_shift(shat, u_hat, float(_brs), fs)
                        _brs = _rb
                        xf[:] = np.convolve(x, shat)[:n]
                        dhat[:stop] = e[:stop] - np.convolve(y[:stop], shat)[:stop]
                        _prm2 = dict(_prm, reg_eps=eps_res, reg_gate='always')
                        _fl_old = _ep.fft.flops() - _f0          # flop accounting across the rebuild (bug fix
                        _ep = _mk(**_prm2); _f0 = -_fl_old       # 2026-10-20: the replay was not counted before)
                        _h0 = (_a // H) * H
                        if _sid['batch'] and hasattr(_ep, 'catch_up'):
                            # batch rebuild: window statistics hop by hop, one solve at the end (only the final
                            # controller is needed; the past control signals were already emitted)
                            w = _ep.catch_up(xf[_h0:stop], dhat[_h0:stop], H, 2 * int(_prm.get('k_first', 16))).copy()
                        else:
                            for _h in range(_h0, stop, H):
                                w = _ep.update(xf[_h:_h + H], dhat[_h:_h + H]).copy()
                        _sid['seen'] = len(_ep.resets)
                    _sid['decided'] = True
                    if _sid.get('cons') is not None and _sid['cons']['ref'] is not None and _sid['cons']['mode'] == 'all':
                        # keep the pre-event noise reference (a window accepted during a movement would contaminate
                        # it); monitor windows start at the accepted check window
                        _r_ = _sid['cons']['ref']; _sid['cons']['ref'] = (_r_[0], _r_[1], int(_a)); _sid['cons']['active'] = True
                    if _sid.get('post_on'):
                        _sid['post'] = {'next': stop + _fsT // 2, 'a0': int(_a)}
                if (_sid.get('post') is not None and _sid['decided'] and _sid['pending'] is None and _sid['apply'] is None
                        and stop >= _sid['post']['next']):
                    _ac = max(int(stop - _fsT), int(_sid['post']['a0']))
                    _csl = _sid['cs']
                    u_c, _ic, _nevc = sid_profile2(x, y, e, shat, _ac, stop, M, _sid['grid'], float(_brs), fs,
                                                   None if _csl else _sid['lrt'], None if _csl else _sid['chow'],
                                                   False if _csl else _sid['edge'], _sid['c2f'],
                                                   float(_csl) if _csl else _sid['wchow'],
                                                   (len(_sid['prior'][0]) if _sid.get('prior') is not None else _sid_lg(_sid['xreg'], shat, M, _sid['D'], fs)), _sid['sigmode'],
                                                   ci_alpha=(float(_csl) if _csl else 0.05),
                                                   chow_alpha=float(_csl) if _csl else None, fastchol=_sid['fastchol'],
                                                   bias_s2=_sid.get('s2_0') if _sid.get('bias') else None,
                                                   gof=((_sid['s2_0'], _sid['dof0'], float(_csl) if _csl else 0.01)
                                                        if (_sid.get('gof') and _sid.get('s2_0')) else None),
                                                   prior=_sid.get('prior'))
                    _nwc = stop - _ac
                    if _sid['xreg'] is not None and (_sid['fastchol'] or _sid.get('prior') is not None):
                        if _sid.get('prior') is not None:
                            _pr = _sid['prior']; _Om, _Dm = _prior_members(_pr)
                            _cstc = sid_cost_prior(_nwc, len(_pr[0]), len(shat), _nevc, len(_Om), 0 if _Dm is None else len(_Dm),
                                                   True, bool(_pr[3]), _sid['sigmode'] in ('hac', 'profile'), _sid['prior_rev'],
                                                   _ic.get('wchow_nsig'))
                        else:
                            _cstc = sid_cost_xreg_fast(_nwc, _sid_lg(_sid['xreg'], shat, M, _sid['D'], fs), len(shat), _nevc,
                                                       True, resid=_sid['sigmode'] in ('hac', 'profile'))
                        if _sid['sigmode'] in ('hac', 'profile'):
                            _cstc += 2.0 * 128 * _nwc + 6.0 * _nwc
                        _sid['flq'] = (_sid['flq'] + [0.0] * max(1, _sid['spread']))[:max(len(_sid['flq']), max(1, _sid['spread']))]
                        for _j in range(max(1, _sid['spread'])):
                            _sid['flq'][_j] += _cstc / max(1, _sid['spread'])
                    _cset = _ic.get('ci_set'); _cedge = bool(_ic.get('ci_edge'))
                    _moved = (u_c is None and not _cedge) or (not _cedge and _cset is not None and not (_cset[0] <= 0.0 <= _cset[1]))
                    _sid['post_log'].append((int(stop), int(_ac), None if u_c is None else float(u_c), _cset, _cedge, bool(_moved)))
                    if _moved and _sid.get('cons') is not None:
                        _sid['cons']['active'] = False
                    if _moved:
                        # the plant moved after the acceptance: full-spec set around the current S_hat, identify again
                        _ep.cfg.reg_eps = movement_bound(shat, M, fs, _sid['D'], float(_brs), float(_bp))
                        _sid['decided'] = False; _sid['pending'] = int(_ac); _sid['due'] = stop + H; _sid['tries'] = 0
                        _a0c = int(_sid['post']['a0'])
                        _sid['cand'] = None; _sid['post'] = None
                        if _sid.get('prior') is not None and _sid['prior_rev'] >= 2:
                            # review R9: the event prior describes one movement from the path BEFORE the first event; after a
                            # second movement it is stale. Rebuild from the certified window [max(a0, a_c - 4L), a_c) (constant
                            # plant: accepted and confirmed up to a_c); if that is shorter than 2L, rebuild from the original
                            # pre-event window with twice the movement spec (two movements of at most Dp each)
                            _Lgq = len(_sid['prior'][0])
                            _wq = (max(_a0c, _ac - 4 * _Lgq), _ac)
                            _p0o = _sid['prior_log'][-1][0] if _sid['prior_log'] else _ac
                            _extra_fl += (_build_prior(int(_ac), _wq) if _wq[1] - _wq[0] >= 2 * _Lgq
                                          else _build_prior(int(_p0o), None, 2.0))
                            _sid['due'] = max(_sid['due'], stop + H)
                    elif _cedge:
                        _sid['post'] = None                      # no information left: nothing moves
                    else:
                        # sid_post_space = (n0, c) (2026-10-24, cost): after n0 confirmations the interval grows to c x
                        # fsT/2 (drift detection after an acceptance; the margin before divergence was >= 0.3 s)
                        _sid['post']['n'] = _sid['post'].get('n', 0) + 1
                        _psp = _sid.get('post_space')
                        _sid['post']['next'] = stop + (_fsT // 2) * (int(_psp[1]) if (_psp and _sid['post']['n'] >= int(_psp[0])) else 1)
                if _sid['flq']:
                    _extra_fl += _sid['flq'].pop(0)
            elif _sid['on']:
                if len(_ep.resets) > _sid['seen']:
                    _ev_total[0] += len(_ep.resets) - _sid['seen']
                    _sid['seen'] = len(_ep.resets)
                    _sid['pending'] = (_ep.locs[-1] if _ep.locs else _ep.resets[-1])
                if _sid['pending'] is not None and stop - _sid['pending'] >= _sid['T'] * fs:
                    # closed-loop 1-parameter check of S on the post-change window (Prop. 13 direct-path model)
                    _a = int(_sid['pending']); _sid['pending'] = None
                    u_hat = sid_profile(x, y, e, shat, _a, stop, M, _sid['grid'], float(_brs), fs, _sid['lrt'])
                    _sid['log'].append((stop, u_hat))
                    # cost of an FFT-based implementation: per u, filtering + correlations over the window + 16 PCG its
                    _nw = stop - _a; _nf = int(2 ** np.ceil(np.log2(2 * _nw)))
                    _extra_fl = len(_sid['grid']) * (3 * 2.5 * _nf * np.log2(_nf) + 16 * 4 * 2.5 * 2 * M * np.log2(2 * M))
                    eps_res = movement_bound(shat_shift(shat, u_hat, float(_brs), fs) if abs(u_hat) > 1e-9 else shat,
                                             M, fs, _sid['Dres'], float(_brs), float(_bp))
                    if abs(u_hat) <= 1e-9:
                        _ep.cfg.reg_eps = eps_res                      # S unchanged: shrink the ridge to the residual spec
                    else:
                        shat = shat_shift(shat, u_hat, float(_brs), fs)  # S changed: update S_hat, rebuild the window
                        xf[:] = np.convolve(x, shat)[:n]
                        dhat[:stop] = e[:stop] - np.convolve(y[:stop], shat)[:stop]
                        _prm2 = dict(_prm, reg_eps=eps_res, reg_gate='always')
                        _fl_old = _ep.fft.flops() - _f0          # flop accounting across the rebuild (bug fix
                        _ep = _mk(**_prm2); _f0 = -_fl_old       # 2026-10-20: the replay was not counted before)
                        _h0 = (_a // H) * H
                        for _h in range(_h0, stop, H):
                            w = _ep.update(xf[_h:_h + H], dhat[_h:_h + H]).copy()
                        _sid['seen'] = len(_ep.resets)
            if _sid.get('on') and _sid.get('cons') is not None:
                _cs_ = _sid['cons']
                _Lgc = _sid_lg('direct', shat, M, _sid['D'], fs)
                if not _cs_['init'] and _cs_['ref'] is None and stop >= 4 * _Lgc + len(shat) + H:
                    _extra_fl += _cons_ref(stop - 4 * _Lgc, stop); _cs_['init'] = True
                _nc = int(_cs_['c'] * _Lgc)
                if (_cs_['active'] and _cs_['ref'] is not None and (stop // H) % _cs_['k'] == 0
                        and stop - _nc >= _cs_['ref'][2]):
                    _Jc_, _fl_ = _cons_J(stop - _nc, stop, _Lgc); _extra_fl += _fl_
                    from scipy.stats import f as _fdc
                    _Fc = (_Jc_ / (_nc - _Lgc)) / (_cs_['ref'][0] / _cs_['ref'][1])
                    _thc = float(_fdc.isf(_cs_['fa'], _nc - _Lgc, _cs_['ref'][1]))
                    if _Fc > _thc:
                        # localize the change inside the window (an event at the window start would mix pre-change
                        # data into the SHRINK windows)
                        _, _fl2, _rv = _cons_J(stop - _nc, stop, _Lgc, resid=True); _extra_fl += _fl2 + 3.0 * _nc
                        _tau = _cons_loc(_rv, stop - _nc, max(H // 4, 8)) if _cs_.get('loc', True) else stop - _nc
                        if _cs_.get('anchor') == 'hop':
                            # anchor at the next hop boundary: the check windows must not contain pre-change samples
                            # (Lemma A2); the localization error is +- one step
                            _tau = int(min(-(-_tau // H) * H, stop))
                        _ep.force_event(_tau); _cs_['active'] = False
                        _cs_['log'].append((int(stop), float(_Fc), _thc, int(_tau)))
            flop_hist.append(_ep.fft.flops() - _f0 + _extra_fl)
            score_hist[:] = _ep.scores; reset_hops[:] = [s // H - 1 for s in _ep.resets]
            loc_hist[:] = _ep.locs; n_resets[0] = len(_ep.resets); rl_hist[:] = [s_ // H - 1 for s_ in _ep.rollbacks]

        elif method == 'PCG-WLS':
            # Exact-covariance FD-PCG (prototype of PCG-WLS).  Window [t0, stop) with t0 = max(restart,
            # stop - L*H).  X^T X = T(r) + Z(t0)^T Z(t0) - Z(stop)^T Z(stop):
            # Toeplitz part by a 2M-point circulant FFT, edge parts from M-1
            # samples at each boundary.  Preconditioner: circulant (bin PSD).
            # Change detection: score (LM) test of the recent-J-hop gradient at
            # the current w; reset the window start when S > c * M.
            L = int(params['L'])
            if params.get('detect', False):
                J = int(params.get('J', 4))
                tr0 = max(restart[0], stop - J * H)
                if stop - restart[0] >= (J + 4) * H:
                    Xr = conv_matrix(xf, tr0, stop, M)
                    rres = dhat[tr0:stop] + Xr @ w
                    g = Xr.T @ rres
                    tw = max(restart[0], stop - L * H)
                    sig2 = float(np.mean((dhat[tw:stop] + fir_window(xf, w, tw, stop)) ** 2))
                    Gr = Xr.T @ Xr
                    Sstat = float(g @ np.linalg.solve(Gr + 1e-3 * np.trace(Gr) / M * np.eye(M), g)) / max(sig2, 1e-300)
                    score_hist.append(Sstat)
                    if Sstat > float(params['c']) * M:
                        restart[0] = start          # keep only the newest hop
                        if params.get('localize', False):
                            # ML change-time estimate within the detection hop: variance
                            # change point of the residual of the pre-change controller on
                            # [start - H, stop) (one clean hop as reference), candidates
                            # every `loc_step` samples; restart at the estimate.
                            a0 = max(0, start - H)
                            rres2 = (dhat[a0:stop] + fir_window(xf, w, a0, stop)) ** 2
                            best_ll, tau_hat = -np.inf, start
                            for tau in range(start, stop - 8, int(params.get('loc_step', 8))):
                                n1, n2 = tau - a0, stop - tau
                                s1 = max(float(np.mean(rres2[:n1])), 1e-300); s2 = max(float(np.mean(rres2[n1:])), 1e-300)
                                ll = -0.5 * (n1 * np.log(s1) + n2 * np.log(s2))
                                if ll > best_ll:
                                    best_ll, tau_hat = ll, tau
                            restart[0] = tau_hat
                            loc_hist.append(tau_hat)
                        n_resets[0] += 1
                        reset_hops.append(b)
            if params.get('genie_change_sample') is not None:
                # oracle detection (analysis only): restart exactly at the true change
                gc = int(params['genie_change_sample'])
                if start <= gc < stop:
                    restart[0] = gc; reset_hops.append(b)
            t0 = max(restart[0], stop - L * H)
            # Feasible GLS: prewhiten x_f and d_hat with
            # the same AR(p) whitening filter A of the noise n = u + v. Any fixed
            # filter keeps the estimator unbiased (A d_hat = -(A x_f) * w + A n);
            # a correct A makes it the GLS / minimum-variance estimator.
            gls = params.get('gls')
            if gls:
                pord = int(params.get('p', 8))
                if gls == 'oracle':
                    acf = gls_oracle_acf
                else:   # feasible: residual of the current controller on the window
                    rr = dhat[t0:stop] + fir_window(xf, w, t0, stop)
                    acf = np.array([rr[l:] @ rr[:len(rr) - l] for l in range(pord + 1)]) / len(rr)
                if acf is not None and (gls == 'oracle' or stop - t0 >= 4 * pord):
                    acoef = solve_toeplitz(acf[:pord], acf[1:pord + 1])
                    Aw = np.concatenate([[1.0], -acoef])
                    xs = np.zeros(n); xs[:stop] = lfilter(Aw, [1.0], xf[:stop])
                    ds = np.zeros(n); ds[:stop] = lfilter(Aw, [1.0], dhat[:stop])
                else:
                    xs, ds = xf, dhat
            else:
                xs, ds = xf, dhat
            r = window_autocorr(xs, t0, stop, M)
            pvec = xcorr_t(xs, ds[t0:stop], t0, stop, M)
            Zh = edge_matrix(xs, t0, M); Zt = edge_matrix(xs, stop, M)
            ridge = float(params['ridge']) * r[0] + 1e-30
            # Short-record protection: the ridge grows as M/t when the window
            # holds fewer than ~M samples (cold start / just after a reset).
            if params.get('adaptive_ridge', False):
                ridge *= max(1.0, float(params.get('ar_scale', 1.0)) * M / max(stop - t0, 1))
            # Centered ridge: penalize the change from the controller in use
            # (prior mean = current w) instead of shrinking w toward zero.
            anchor = w.copy() if params.get('centered', False) else np.zeros(M)
            c = np.concatenate([r, [0.0], r[:0:-1]]); Cf = np.fft.rfft(c)
            def Gvec(u):
                tu = np.fft.irfft(Cf * np.fft.rfft(np.concatenate([u, np.zeros(M)])), n=2 * M)[:M]
                return tu + Zh.T @ (Zh @ u) - Zt.T @ (Zt @ u) + ridge * u
            pre = np.maximum(Cf.real, 1e-3 * np.max(Cf.real)) + ridge
            def Minv(rv):
                return np.fft.irfft(np.fft.rfft(np.concatenate([rv, np.zeros(M)])) / pre, n=2 * M)[:M]
            res = -pvec + ridge * anchor - Gvec(w)
            zv = Minv(res); pv = zv.copy(); rz = float(res @ zv)
            k_it = int(params['k'])
            # Transient-only iterations: k_steady CG iterations once the window
            # holds more than `k_hops` hops since the last restart.
            if 'k_steady' in params and (stop - t0) > int(params['k_hops']) * H:
                k_it = int(params['k_steady'])
            # just after a (re)start the warm start (previous controller) can be far
            # from the new solution: more iterations for the first k_first_hops hops
            if 'k_first' in params and (stop - t0) <= int(params['k_first_hops']) * H:
                k_it = int(params['k_first'])
            # Early stopping on short records (implicit regularization toward
            # the warm start): fewer CG iterations while the window holds
            # fewer than `short_factor * M` samples.
            if 'k_short' in params and (stop - t0) < float(params.get('short_factor', 1.0)) * M:
                k_it = int(params['k_short'])
            for _ in range(k_it):
                Ap = Gvec(pv)
                a = rz / float(pv @ Ap + 1e-300)
                w = w + a * pv
                res = res - a * Ap
                zv = Minv(res); rz_new = float(res @ zv)
                pv = zv + (rz_new / (rz + 1e-300)) * pv
                rz = rz_new

        elif method == 'BOCPD':
            # Exact Bayesian piecewise-stationary estimator (THEORY_TRACKING.md, sec. 4):
            # run-length posterior with conjugate Gaussian segments, TC-kernel
            # prior, moment-matched prior for new segments, pruning to R hypotheses.
            # Controller = posterior mean (eq. 3).
            th = params
            sig2 = float(th['sigma2_rel']) * noise_ref
            Xb = conv_matrix(xf, start, stop, M); yb = dhat[start:stop]
            if Wwhite is not None:
                # (A3') n = v + u, Cov = sig2 (I + rho T_x): prewhiten each hop
                Xb = Wwhite @ Xb; yb = Wwhite @ yb
            Gb = Xb.T @ Xb; bb = Xb.T @ yb
            def pred_ll(Lam, m, Laminv_chol=None):
                # log N(y; -X m, sig2 I + X Lam^{-1} X^T) via Woodbury / determinant lemma
                r = yb + Xb @ m
                A = sig2 * Lam + Gb                      # sig2 * (Lam + G/sig2)
                cA = np.linalg.cholesky(A); cL = np.linalg.cholesky(sig2 * Lam)
                z = np.linalg.solve(cA, Xb.T @ r)
                quad = (float(r @ r) - float(z @ z)) / sig2
                logdet = H * np.log(sig2) + 2 * np.sum(np.log(np.diag(cA))) - 2 * np.sum(np.log(np.diag(cL)))
                return -0.5 * (quad + logdet + H * np.log(2 * np.pi))
            if not hyps:
                Pi_inv = Kinv_tc / float(th['sigma0_2'])
                # evidence of the first hop under the cold-start prior
                log_evidence[0] += pred_ll(Pi_inv, np.zeros(M)) + logdetW
                hyps.append({'mu': np.zeros(M), 'Pi_inv': Pi_inv, 'Lam': Pi_inv.copy(), 'm': np.zeros(M),
                             'G': np.zeros((M, M)), 'bv': np.zeros(M), 'logw': 0.0, 'start': b})
            else:
                # predictive log-likelihoods of hop b, then run-length weight update (eq. 7)
                lls = [pred_ll(hp['Lam'], hp['m']) for hp in hyps]
                logw_prev = np.array([hp['logw'] for hp in hyps])
                m_bar = coll[0]; P_bar = coll[1]
                Pi_new = P_bar + float(th['sigmaD_2']) * K_tc
                Pi_new_inv = np.linalg.inv(Pi_new); Pi_new_inv = 0.5 * (Pi_new_inv + Pi_new_inv.T)
                ll_new = pred_ll(Pi_new_inv, m_bar)
                hz = float(th['hazard'])
                lse = float(np.logaddexp.reduce(logw_prev))
                for hp, ll in zip(hyps, lls):
                    hp['logw'] += np.log1p(-hz) + ll
                hyps.append({'mu': m_bar.copy(), 'Pi_inv': Pi_new_inv, 'Lam': Pi_new_inv.copy(), 'm': m_bar.copy(),
                             'G': np.zeros((M, M)), 'bv': np.zeros(M), 'logw': lse + np.log(hz) + ll_new, 'start': b})
                norm = float(np.logaddexp.reduce([hp['logw'] for hp in hyps]))
                # + log|det W| converts the whitened-data evidence back to d_hat units,
                # so evidences with different noise-color hyperparameters are comparable.
                log_evidence[0] += norm - lse + logdetW
                for hp in hyps:
                    hp['logw'] -= norm
            # include hop b in every hypothesis (eq. 5)
            for hp in hyps:
                hp['G'] += Gb; hp['bv'] += bb
                hp['Lam'] = hp['Pi_inv'] + hp['G'] / sig2
                hp['m'] = np.linalg.solve(hp['Lam'], hp['Pi_inv'] @ hp['mu'] - hp['bv'] / sig2)
            # prune to R hypotheses
            hyps.sort(key=lambda hp: -hp['logw'])
            del hyps[int(th.get('R', 6)):]
            norm = float(np.logaddexp.reduce([hp['logw'] for hp in hyps]))
            for hp in hyps:
                hp['logw'] -= norm
            pw = np.exp([hp['logw'] for hp in hyps])
            m_bar = sum(p_ * hp['m'] for p_, hp in zip(pw, hyps))
            P_bar = sum(p_ * (np.linalg.inv(hp['Lam']) + np.outer(hp['m'] - m_bar, hp['m'] - m_bar)) for p_, hp in zip(pw, hyps))
            coll[0] = m_bar; coll[1] = 0.5 * (P_bar + P_bar.T)
            w = m_bar.copy()
            rl_hist.append([(b - hp['start'], float(p_)) for p_, hp in zip(pw, hyps)][:3])

        elif method == 'I-LS':
            # Indirect estimation, exact prototype:
            # (1) p_hat = ridge LS of d_hat on the raw reference (M_p taps);
            # (2) w = noise-free LS design on the same window.
            L = int(params['L']); Mp = int(params['Mp'])
            t0 = max(0, stop - L * H)
            Xx = conv_matrix(x, t0, stop, Mp)
            Gx = Xx.T @ Xx
            if params.get('ridge_abs_hops') is not None:
                # constant prior precision (= `ridge_abs_hops` hops worth of reference
                # energy per tap): its influence vanishes as data accumulate
                lam_p = float(params['ridge_abs_hops']) * H * float(np.mean(x[:stop] ** 2))
            else:
                lam_p = float(params['ridge_p']) * np.trace(Gx) / Mp
            p_hat = np.linalg.solve(Gx + lam_p * np.eye(Mp), Xx.T @ dhat[t0:stop])
            Xf_ = conv_matrix(xf, t0, stop, M)
            dmod = Xx @ p_hat                      # noise-free model disturbance on the window
            design = params.get('design', 'cov')
            if design == 'hybrid':
                # empirical-risk (covariance) design once it is well posed (t >= c M),
                # population plug-in Wiener design before that
                design = 'cov' if (stop - t0) >= float(params.get('switch_c', 2.0)) * M else 'wiener'
            if design == 'wiener':
                # Plug-in Wiener design: minimize (p_hat + S_hat*w)^T T_x (p_hat + S_hat*w)
                # with T_x the Toeplitz of the biased (PSD) reference autocorrelation
                # estimated from all reference samples observed so far.
                Le = max(Mp, M + len(shat) - 1)
                xr_ = x[:stop]
                rx = np.array([xr_[l:] @ xr_[:len(xr_) - l] if l < len(xr_) else 0.0 for l in range(Le)]) / len(xr_)
                Tx_ = toeplitz(rx)
                Cs = conv_matrix(np.concatenate([shat, np.zeros(Le)]), 0, Le, M)   # Cs[n, m] = shat[n-m]
                pp = np.zeros(Le); pp[:Mp] = p_hat
                A_ = Cs.T @ Tx_ @ Cs
                w = np.linalg.solve(A_ + float(params['ridge_w']) * np.trace(A_) / M * np.eye(M), -Cs.T @ (Tx_ @ pp))
                Gf = None
            elif design == 'toeplitz':
                # Wiener design with the autocorrelation-method (Toeplitz, PSD) estimate
                # of the filtered-reference covariance: well posed for any t.
                n_w = stop - t0
                rf = window_autocorr(xf, t0, stop, M) / n_w
                Gf = toeplitz(rf)
                rhs = -(Xf_.T @ dmod) / n_w
            else:
                Gf = Xf_.T @ Xf_
                rhs = -Xf_.T @ dmod
            if Gf is not None:
                w = np.linalg.solve(Gf + float(params['ridge_w']) * np.trace(Gf) / M * np.eye(M), rhs)

        elif method == 'K-EBV':
            # Validated Bayesian estimate (safety guard against the overshoot of
            # K-EB on short records).  Candidates: TC-kernel posterior means on a
            # (alpha, eta) grid, plain ridge LS, and "keep the current w".
            # Selection: fit on [t0, start), score by the virtual-residual power
            # on the newest hop [start, stop) (data not used for the fit); then
            # refit the selected candidate on [t0, stop).
            L = int(params['L'])
            t0 = max(0, stop - L * H)
            idx = np.arange(M)
            def solve(t_a, t_b, alpha, eta_rel):
                Xa = conv_matrix(xf, t_a, t_b, M); Ga = Xa.T @ Xa; ba = Xa.T @ dhat[t_a:t_b]
                gs = max(float(np.trace(Ga)) / M, 1e-30)
                if alpha is None:   # ridge LS (relative ridge 1e-3), PCG-WLS equivalent
                    return np.linalg.solve(Ga + 1e-3 * gs * np.eye(M), -ba)
                K = alpha ** np.maximum(idx[:, None], idx[None, :])
                eta = eta_rel / gs
                return -np.linalg.solve(eta * K @ Ga + np.eye(M), eta * K @ ba)
            cands = [('keep', None, None), ('ls', None, None)] + [('tc', al, et) for al in params['alphas'] for et in params['etas']]
            if start - t0 >= H:
                xv = conv_matrix(xf, start, stop, M); dv = dhat[start:stop]
                best = None
                g_pq = float(params.get('pq_discount', 0.0))   # 0 -> single-hop validation (K-EBV)
                for kind, al, et in cands:
                    wc = w if kind == 'keep' else solve(t0, start, al, et)
                    err = float(np.mean((dv + xv @ wc) ** 2))
                    key = (kind, al, et)
                    pq_score[key] = g_pq * pq_score.get(key, 0.0) + err   # prequential (discounted) score
                    sc = pq_score[key]
                    if best is None or sc < best[0]:
                        best = (sc, kind, al, et)
                _, kind, al, et = best
            else:
                kind, al, et = ('keep', None, None)
            eb_hist.append((kind, al, et))
            if kind != 'keep':
                w = solve(t0, stop, al, et)

        elif method == 'K-EBP':
            # Bayesian *indirect* FFANC: put the TC prior on the physical primary
            # path, not on the controller.  (1) Empirical-Bayes TC-kernel
            # estimate of P from d_hat = P*x + v (regressor: raw reference x);
            # (2) controller design by noise-free LS on the same window:
            #     w = argmin || P_hat*x + w*(S_hat*x) ||^2 + tiny ridge.
            L = int(params['L']); Mp = int(params['Mp'])
            t0 = max(0, stop - L * H)
            Xr = conv_matrix(x, t0, stop, Mp)
            Gp = Xr.T @ Xr; bp = Xr.T @ dhat[t0:stop]; yy = float(dhat[t0:stop] @ dhat[t0:stop]); tt = stop - t0
            idp = np.arange(Mp); gscale = max(float(np.trace(Gp)) / Mp, 1e-30)
            best = None
            for alpha in params['alphas']:
                K = alpha ** np.maximum(idp[:, None], idp[None, :])
                U = np.linalg.cholesky(K + 1e-10 * np.eye(Mp))
                UGU = U.T @ Gp @ U; Ub = U.T @ bp
                for eta_rel in params['etas']:
                    eta = eta_rel / gscale
                    cA = np.linalg.cholesky(np.eye(Mp) + eta * UGU)
                    z = np.linalg.solve(cA, Ub)
                    sig2 = max((yy - eta * float(z @ z)) / tt, 1e-300)
                    nll = 0.5 * (tt * np.log(sig2) + 2.0 * np.sum(np.log(np.diag(cA))))
                    if best is None or nll < best[0]:
                        best = (nll, alpha, eta, K)
            _, alpha, eta, K = best
            p_hat = np.linalg.solve(eta * K @ Gp + np.eye(Mp), eta * K @ bp)   # d_hat ~ X p
            eb_hist.append((alpha, eta * gscale))
            # Design on the same window of reference data (no sensor noise enters).
            dmodel = fir_window(x, p_hat, t0, stop)
            Xf = conv_matrix(xf, t0, stop, M)
            G = Xf.T @ Xf
            w = np.linalg.solve(G + float(params['ridge']) * np.trace(G) / M * np.eye(M), -Xf.T @ dmodel)

        elif method == 'B-LS':
            # Realizable ceiling of A: exact ridge LS over the last L hops of
            # the virtual residual (all M coefficients free).  O(M^2..M^3).
            L = int(params['L'])
            t0 = max(0, stop - L * H)
            X = conv_matrix(xf, t0, stop, M)
            lam = float(params['ridge']) * float(np.trace(X.T @ X)) / M + 1e-30
            w = np.linalg.solve(X.T @ X + lam * np.eye(M), -X.T @ dhat[t0:stop])

        elif method == 'A-PCG':
            # k preconditioned-CG iterations per hop on the windowed normal
            # equations (X^T X + lam I) w = -X^T d_hat, warm-started at the
            # current w.  Preconditioner: bin-wise filtered-reference PSD
            # (circulant approximation applied by FFT) = the bin-wise
            # normalization used as a preconditioner instead of a step rule.
            L = int(params['L'])
            t0 = max(0, stop - L * H)
            seg_len = stop - t0
            lam = float(params['ridge']) * seg_len * float(np.mean(xf[t0:stop] ** 2)) + 1e-30
            def Avec(u):
                z = fir_window(xf, u, t0, stop)                 # X u
                return xcorr_t(xf, z, t0, stop, M) + lam * u    # X^T X u + lam u
            denom = power.denominator('binwise', b)
            def Minv(rv):
                R = np.fft.rfft(np.concatenate([rv, np.zeros(N - M)]))
                return np.fft.irfft(R / denom, n=N)[:M]
            rhs = -xcorr_t(xf, dhat[t0:stop], t0, stop, M)
            res = rhs - Avec(w)
            zv = Minv(res); pv = zv.copy(); rz = float(res @ zv)
            for _ in range(int(params['k'])):
                Ap = Avec(pv)
                a = rz / float(pv @ Ap + 1e-300)
                w = w + a * pv
                res = res - a * Ap
                zv = Minv(res); rz_new = float(res @ zv)
                pv = zv + (rz_new / (rz + 1e-300)) * pv
                rz = rz_new

        elif method in ('R-RLS', 'R-VFF'):
            # MFx-RLS baseline: exponentially weighted RLS on the virtual
            # residual d_hat + x_f^T w, processed sample by sample within the
            # hop; the controller is updated once per hop like all methods.
            # R-VFF: Fortescue, Kershenbaum & Ydstie (1981) variable forgetting
            #   lam(n) = 1 - (1 - u^T k) eps^2 / Sigma0,  clipped to [lam_min, 1],
            #   Sigma0 = sigma0^2 * N0 with sigma0^2 the expected noise power
            #   (estimated from the training-signal SNR) and N0 the memory length.
            lam = float(params.get('lam', 1.0))
            if Prls is None:
                _dl = float(params.get('det_delta', params['delta'])) if _det_reset_pending else float(params['delta'])
                Prls = np.eye(M) / (_dl * float(np.mean(xf[:eval_samples] ** 2)) * M)
            _fast = bool(os.environ.get('RLS_FAST'))      # (2026-10-24) same recursion, in-place rank-1 BLAS update
            if _fast:
                from scipy.linalg.blas import dger as _dger
                Prls = np.asfortranarray(Prls)
            _cusum_sq = 0.0
            _cusum_count = 0
            # (2026-11-03, review of 9-B) RLS + det replays [tau, stop) from the hop-start coefficients; keep them so a
            # CUSUM alarm at this hop restarts from the same state (not from w already updated on [start, stop))
            _w_hop0 = w.copy() if _cusum is not None else None
            for t in range(_rls_from, stop):
                u = np.zeros(M)
                m = min(M, t + 1)
                if rls_pw[0] is not None:                   # (review N8) prewindowed restart: x_f = 0 before tau
                    m = max(0, min(m, t - rls_pw[0] + 1))   # (review) 0 before tau, e.g. with det_replay False
                u[:m] = xf[t - m + 1:t + 1][::-1]
                eps = dhat[t] + u @ w
                if _cusum is not None and t >= start:
                    _cusum_sq += float(eps * eps)
                    _cusum_count += 1
                Pu = Prls @ u
                k = Pu / (lam + u @ Pu)
                if t >= jp_from[0]:
                    w = w - k * eps
                if _fast:
                    Prls = _dger(-1.0, k, Pu, a=Prls, overwrite_a=1); Prls *= (1.0 / lam)
                else:
                    Prls = (Prls - np.outer(k, Pu)) / lam
                if method == 'R-VFF':
                    sigma0 = float(np.mean(d[:eval_samples] ** 2)) / 10 ** (float(cfg['secondary_noise_snr_db']) / 10)
                    lam = 1.0 - (1.0 - float(u @ k)) * eps * eps / (sigma0 * float(params['N0']))
                    lam = min(1.0, max(float(params.get('lam_min', 0.95)), lam))

            if _cusum is not None:
                _tau = _cusum.update(_cusum_sq, _cusum_count, b)
                if _tau is not None:
                    reset_hops.append(b); loc_hist.append(_tau)
                    n_resets[0] += 1
                    Prls = np.asfortranarray(np.eye(M) / (float(params['delta']) * float(np.mean(xf[:eval_samples] ** 2)) * M))
                    w = _w_hop0
                    for t in range(_tau, stop):
                        u = np.zeros(M)
                        m = min(M, t + 1)
                        u[:m] = xf[t - m + 1:t + 1][::-1]
                        eps = dhat[t] + u @ w
                        Pu = Prls @ u
                        k = Pu / (lam + u @ Pu)
                        w = w - k * eps
                        if _fast:
                            Prls = _dger(-1.0, k, Pu, a=Prls, overwrite_a=1); Prls *= (1.0 / lam)
                        else:
                            Prls = (Prls - np.outer(k, Pu)) / lam

        elif method == 'R-SFTF':
            # (2026-10-31, review option 2) stabilized fast transversal filter (Slock & Kailath 1991) in the a priori
            # form of Benesty et al.: exponentially weighted prewindowed LS on the virtual residual d_hat + x_f^T w, the
            # same criterion as 'R-RLS' (soft initialization R0 = delta mean(x_f^2) M; the FTF soft start adds the
            # weights lam^-i on the diagonal, negligible for lam near 1). O(M) per sample. After a shared detection the
            # filter restarts at tau with a prewindowed regressor (x_f set to zero before tau inside the FTF), i.e. the
            # standard FTF restart (covariance-form O(M) fast RLS exist, at about twice the cost and with less analysis
            # of their stabilization; not used). No rescue: a divergence counts as a failure (REVISION_RULE_4.md).
            # Stabilization: backward a priori error computed two ways and mixed with kappa = (1.5, 2.5, 1.0).
            lam = float(params.get('lam', 1.0))
            assert 'det_delta' not in params, "R-SFTF: 'det_delta' not supported"
            if sftf is None:
                E0 = float(params['delta']) * float(np.mean(xf[:eval_samples] ** 2)) * M
                sftf = {'a': np.zeros(M), 'b': np.zeros(M), 'k': np.zeros(M), 'g': 1.0, 'al': E0,
                        'be': E0 * lam ** (-M), 't0': _rls_from, 'ub': np.zeros(M + 1)}
            if cov[0] == 'pending':
                cov[0] = _cftf_init(xf, _rls_from, M, lam, float(params['delta']) * float(np.mean(xf[:eval_samples] ** 2)) * M,
                                    w if not params.get('det_reset_w') else np.zeros(M))
            if cov[0] is not None:
                w = _cftf_run(cov[0], xf, dhat, w, _rls_from, stop, lam, M)
                _rls_from = stop                                       # the prewindowed FTF below is not used any more
            if hyb[0] is not None:
                # (2026-10-31) hybrid restart: exact exponentially weighted RLS (true regressor, P = I / R0) from tau until
                # t1 = tau + T_h, then an FTF re-initialized with a pre-roll of T_h samples (prewindowed at t1 - T_h = tau,
                # joint process frozen before t1) continues from the RLS controller. O(M^2) only for T_h samples per restart.
                Hs = hyb[0]; t_end = min(stop, Hs['t1'])
                for t in range(_rls_from, t_end):
                    u = np.zeros(M); m = min(M, t + 1); u[:m] = xf[t - m + 1:t + 1][::-1]
                    eps = dhat[t] + u @ w
                    Pu = Hs['P'] @ u; k = Pu / (lam + u @ Pu)
                    w = w - k * eps
                    Hs['P'] = (Hs['P'] - np.outer(k, Pu)) / lam
                if t_end < Hs['t1']:
                    _rls_from = stop                                   # whole hop handled by the exact RLS
                else:
                    t1 = Hs['t1']; hyb[0] = None
                    E0 = float(params['delta']) * float(np.mean(xf[:eval_samples] ** 2)) * M
                    sftf = {'a': np.zeros(M), 'b': np.zeros(M), 'k': np.zeros(M), 'g': 1.0, 'al': E0,
                            'be': E0 * lam ** (-M), 't0': t1 - int(params['hybrid']), 'ub': np.zeros(M + 1)}
                    jp_from[0] = t1; _rls_from = t1 - int(params['hybrid'])
            S_ = sftf; a_, b_, kk = S_['a'], S_['b'], S_['k']; t0_ = S_['t0']
            ub = S_['ub']                                   # u_{M+1}(t) = [x(t), ..., x(t-M)] (prewindowed at t0_)
            k1, k2, k3 = 1.5, 2.5, 1.0
            for t in range(_rls_from, stop):
                xt = xf[t] if t >= t0_ else 0.0
                ub[1:] = ub[:-1]; ub[0] = xt                # shift in x(t)
                u_prev = ub[1:]                             # u_M(t-1)
                u_now = ub[:-1]                             # u_M(t)
                ea = xt - a_ @ u_prev                       # forward a priori error
                al_old = S_['al']
                S_['al'] = lam * al_old + S_['g'] * ea * ea
                kext = np.empty(M + 1)                      # [t; m] = [0; k(t-1)] + ea / (lam al) [1; -a]
                kext[0] = 0.0; kext[1:] = kk
                c_ = ea / (lam * al_old)
                kext[0] += c_; kext[1:] -= c_ * a_
                a_ += S_['g'] * ea * kk                     # a(t) = a(t-1) + gamma(t-1) ea k(t-1)
                m_ = kext[M]
                eb1 = lam * S_['be'] * m_
                eb2 = ub[M] - b_ @ u_now                    # x(t-M) - b^T u_M(t)
                ebk = [k * eb2 + (1.0 - k) * eb1 for k in (k1, k2, k3)]
                kk = kext[:M] + m_ * b_                     # k(t) = t + m b(t-1)
                ginv = 1.0 / S_['g'] + c_ * ea - m_ * ebk[2]
                S_['g'] = 1.0 / ginv
                S_['be'] = lam * S_['be'] + S_['g'] * ebk[1] * ebk[1]
                b_ += S_['g'] * ebk[0] * kk                 # b(t) = b(t-1) + gamma(t) eb k(t)
                if t >= jp_from[0]:                         # pre-roll restart: no joint-process update before tau
                    eps = dhat[t] + u_now @ w               # joint process (prewindowed regressor)
                    w = w - S_['g'] * eps * kk
            S_['k'] = kk

        elif method in ('A-TPCG', 'A-TPCGr'):
            # Toeplitz frequency-domain PCG: accumulate autocorrelation r[l]
            # and cross-correlation p[m] with per-hop forgetting gamma, then
            # run k PCG iterations on Toeplitz(r) w = -p.  Matrix-vector
            # products use a 2M-point circulant embedding (FFT); the
            # preconditioner is the circulant/PSD diagonal, i.e. bin-wise
            # normalization appears as the circulant preconditioner.
            gam = float(params['gamma'])
            seg = xf[max(0, start - M + 1):stop]
            seg = np.concatenate([np.zeros(M - 1 - (start - max(0, start - M + 1))), seg])
            new_x = xf[start:stop]
            r_hop = np.array([new_x @ seg[M - 1 - l:M - 1 - l + H] for l in range(M)])
            p_hop = np.array([dhat[start:stop] @ seg[M - 1 - m:M - 1 - m + H] for m in range(M)])
            if method == 'A-TPCGr':
                # Change detector: virtual residual of the current controller on
                # the newest hop versus the recent median.  A jump by a factor
                # > kappa means the accumulated statistics describe a different
                # plant, so they are discarded (restart from this hop).
                r_new = dhat[start:stop] + fir_window(xf, w, start, stop)
                pw = float(np.mean(r_new ** 2))
                hist_pw.append(pw)
                ref = np.median(hist_pw[-9:-1]) if len(hist_pw) > 4 else np.inf
                if pw > float(params['kappa']) * ref:
                    r_acc[:] = 0.0; p_acc[:] = 0.0
                    n_resets[0] += 1
                    since[0] = 0
                    hist_pw[:] = [pw]
            r_acc = gam * r_acc + r_hop
            p_acc = gam * p_acc + p_hop
            ridge = float(params['ridge']) * r_acc[0] + 1e-30
            c = np.concatenate([r_acc, [0.0], r_acc[:0:-1]])          # 2M circulant embedding
            Cf = np.fft.rfft(c)
            pre = np.maximum(Cf.real, 1e-3 * np.max(Cf.real)) + ridge
            def Minv(rv):
                return np.fft.irfft(np.fft.rfft(np.concatenate([rv, np.zeros(M)])) / pre, n=2 * M)[:M]
            since[0] += H
            n_exact = int(params.get('exact_hops', 0)) * H
            if method == 'A-TPCGr' and since[0] <= n_exact:
                # Short record (cold start or just after a reset): the Toeplitz
                # approximation of X^T X can be indefinite, so use the exact
                # windowed normal equations (always PSD) over the samples since
                # the last restart.
                t0 = stop - since[0]
                def Tvec(u):
                    return xcorr_t(xf, fir_window(xf, u, t0, stop), t0, stop, M) + ridge * u
                rhs = -xcorr_t(xf, dhat[t0:stop], t0, stop, M)
            else:
                def Tvec(u):
                    return np.fft.irfft(Cf * np.fft.rfft(np.concatenate([u, np.zeros(M)])), n=2 * M)[:M] + ridge * u
                rhs = -p_acc
            res = rhs - Tvec(w)
            zv = Minv(res); pv = zv.copy(); rz = float(res @ zv)
            for _ in range(int(params['k'])):
                Ap = Tvec(pv)
                a = rz / float(pv @ Ap + 1e-300)
                w = w + a * pv
                res = res - a * Ap
                zv = Minv(res); rz_new = float(res @ zv)
                pv = zv + (rz_new / (rz + 1e-300)) * pv
                rz = rz_new

        elif method == 'C-FDKF':
            r_new = dhat[start:stop] + fir_window(xf, w, start, stop)
            e_frame = np.zeros(N); e_frame[-H:] = r_new
            E = np.fft.rfft(e_frame)
            rr = H / N
            X2 = np.abs(Xf) ** 2
            if P is None:
                # P0 relative to the expected |W_k|^2 scale of a unit-norm controller.
                P = np.full(len(Xf), float(params['P0']))
                Psi = np.abs(E) ** 2
            else:
                Psi = 0.5 * Psi + 0.5 * np.abs(E) ** 2
            mu_k = rr * P / (rr * X2 * P + Psi + 1e-30)     # Kalman gain / conj(X)
            c = float(params.get('gain_scale', 1.0))
            g = np.fft.irfft(c * mu_k * np.conj(Xf) * E, n=N)[:M]
            w = w - g
            A = float(params.get('A', 0.998))
            W = np.fft.rfft(np.concatenate([w, np.zeros(N - M)]))
            P = A * A * (1.0 - rr * mu_k * X2) * P + (1.0 - A * A) * (P + np.abs(W) ** 2)
        else:
            raise ValueError(method)

        max_w = max(max_w, float(np.linalg.norm(w)))
        if not np.all(np.isfinite(w)) or max_w > 1e3:
            break

    stable, failure = classify_diagnostic_run(
        total_power, uncontrolled_power, max_weight_norm=max_w, max_abs_error=max_e,
        disturbance_rms=float(np.sqrt(np.mean(d[:eval_samples] ** 2))),
    )
    if len(total_power) < n_hops:
        stable, failure = False, failure or 'aborted'
    extra = {'xf': xf[:eval_samples], 'dhat': dhat[:eval_samples], 'e': e[:eval_samples], 'w_final': w, 's': s, 'shat': shat, 'x': x[:eval_samples],
             'y': y[:eval_samples], 's2': s2_ism} if RETURN_SIGNALS else {}
    if cfg.get('path_source', 'ism') == 'meshrir':
        extra['path_provenance'] = _extra['meshrir']
    return {**extra, 'seed': seed, 'stable': stable, 'failure': failure, 'n_resets': n_resets[0], 'events_total': (_ev_total[0] if _ev_total[0] else len(reset_hops)), 'eb_hist': eb_hist, 'score_hist': score_hist,
            'log_evidence': log_evidence[0], 'rl_hist': rl_hist, 'reset_hops': reset_hops, 'loc_hist': loc_hist, 'flop_hist': flop_hist, 'sid_log': _sid['log'], 'ridge_excess': _rlog, 'dual_log': _dual, 'seq_log': _sid.get('seq_log', []), 'thA_log': _sid.get('thA_log', []), 'post_log': _sid.get('post_log', []), 'adapt_log': _sid.get('adapt_log', []), 'prior_log': _sid.get('prior_log', []), 'sub_log': _sid.get('sub_log', []), 's2pre_log': _sid.get('s2pre_log', []), 'cons_log': ((_sid.get('cons') or {}).get('log', [])), 'risk_log': ((_ep.members[_ep.ip] if hasattr(_ep, 'members') else _ep).risk_log if method == 'E-PCG-F' and _ep is not None and hasattr(_ep.members[_ep.ip] if hasattr(_ep, 'members') else _ep, 'risk_log') else []), 'mem_pi': (np.mean(_ep.pi_hist, 0).tolist() if method == 'E-PCG-F' and hasattr(_ep, 'pi_hist') and _ep.pi_hist else None), 'geom': (_extra.get('geom') if cfg.get('plant') == 'ism' else None),
            'total_power': total_power, 'uncontrolled_power': uncontrolled_power}


def summarize(runs, cfg, floor_db):
    H = int(cfg['hop_length']); fs = int(cfg['sample_rate'])
    status, rr = diagnostic_stability_summary(runs)
    if not rr:
        return status
    pe = np.asarray([r['total_power'] for r in rr]); p0 = np.asarray([r['uncontrolled_power'] for r in rr])
    db = ensemble_power_ratio_db(pe, p0)
    th = threshold_times_from_db_curve(db, H / fs, thresholds=(-10.0, -15.0, -18.0, floor_db + 0.5))
    th['floor+0.5'] = th.pop(f'{floor_db + 0.5:g}')
    pts = {f'{t}': float(db[min(len(db) - 1, int(np.ceil(t * fs / H)) - 1)]) for t in (0.05, 0.1, 0.25, 0.5, 1.0, 2.0)}
    m = {'curve_db': db.tolist(), 'points_db': pts, 'threshold_s': th, 'cumulative_db': cumulative_power_ratio_db(pe, p0)}
    out = dict(status)
    if status['primary_valid']:
        out.update(m)
    else:
        out['stable_only_diagnostic'] = m
    return out


GRIDS = {
    'known': {'oracle': [True]},
    'fixed_binwise': {'mu': [0.648]},  # benchmark-optimized value
    'fixed_binwise_virtual': {'mu': [0.3, 0.5, 0.648, 0.8, 1.0, 1.3]},
    'A-GB': {'L': [1, 2, 4, 8, 16, 32], 'rho': [1e-3, 1e-2]},
    'A-GBm': {'L': [2, 4, 8, 16, 32], 'rho': [1e-3, 1e-2]},
    'A-band': {'K': [4, 8, 16, 32, 64, 128], 'L': [2, 4, 8, 16, 32], 'rho': [1e-3, 1e-2], 'momentum': [False, True]},
    'B-LS': {'L': [2, 4, 8, 32], 'ridge': [1e-3, 1e-2, 1e-1]},
    'A-PCG': {'k': [1, 2, 4, 8], 'L': [8, 32], 'ridge': [1e-3, 1e-2]},
    'R-RLS': {'lam': [1.0, 0.9999, 0.9995], 'delta': [1e-3, 1e-2, 1e-1]},
    'R-VFF': {'N0': [500.0, 2000.0, 8000.0], 'lam_min': [0.98, 0.995], 'delta': [1e-3]},
    'A-TPCG': {'k': [2, 4, 8, 16], 'gamma': [1.0, 0.99, 0.97], 'ridge': [1e-3, 1e-2]},
    'A-TPCGr': {'k': [8], 'gamma': [1.0, 0.995, 0.99], 'ridge': [1e-3], 'kappa': [2.0, 4.0], 'exact_hops': [4, 8]},
    'K-LS': {'alpha': [0.8, 0.85, 0.9, 0.95], 'eta': [1e3, 1e4, 1e5, 1e6], 'L': [32]},
    'K-EB': {'alphas': [(0.7, 0.8, 0.85, 0.9, 0.93, 0.96, 0.98, 0.99)], 'etas': [(0.1, 1.0, 10.0, 100.0, 1e3, 1e4, 1e5, 1e6, 1e7)], 'L': [32]},
    'PCG-WLS': {'k': [8], 'L': [32], 'ridge': [1e-3]},
    'C-FDKF': {'P0': [1e-3, 1e-2, 1e-1, 1.0, 10.0, 100.0], 'gain_scale': [1.0, 2.0, 4.0, 8.0], 'A': [0.998]},
}


def grid(method):
    g = GRIDS[method]
    keys = list(g)
    for vals in itertools.product(*[g[k] for k in keys]):
        yield dict(zip(keys, vals))


def score(runs, cfg):
    """Training objective: ensemble cumulative residual (dB) over eval window; unstable -> +inf."""
    if not all(r['stable'] for r in runs):
        return float('inf')
    pe = np.asarray([r['total_power'] for r in runs]); p0 = np.asarray([r['uncontrolled_power'] for r in runs])
    return cumulative_power_ratio_db(pe, p0)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--config', default=str(ROOT / 'configs' / 'oracle_2s.json'))
    ap.add_argument('--methods', default=','.join(GRIDS))
    ap.add_argument('--train-seeds', default='0,1,2,3,4,5')
    ap.add_argument('--heldout-seeds', default=','.join(str(100 + i) for i in range(20)))
    ap.add_argument('--train-seconds', type=float, default=0.5)
    ap.add_argument('--heldout-seconds', type=float, default=2.0)
    ap.add_argument('--out', default=str(ROOT / 'results' / 'prototype_screening'))
    ap.add_argument('--change-at', type=float, default=None,
                    help='abrupt primary-path change time [s] (tracking scenario); applied to train and held-out')
    args = ap.parse_args()
    cfg = json.loads(Path(args.config).read_text())
    train = [int(s) for s in args.train_seeds.split(',')]
    held = [int(s) for s in args.heldout_seeds.split(',')]
    p = np.zeros(64); s = np.zeros(48)
    from ffanc_norm.paths import synthetic_primary_path, synthetic_secondary_path
    p = synthetic_primary_path(); s = synthetic_secondary_path(); M = int(cfg['controller_length'])
    _, _, _, jmin = wiener_solution(s, p, M, pole=0.95); vard = primary_variance(p, pole=0.95)
    varv = vard / 10 ** (float(cfg['secondary_noise_snr_db']) / 10)
    floor_db = float(10 * np.log10((jmin + varv) / (vard + varv)))

    out = {'conditions': {'train_seeds': train, 'heldout_seeds': held, 'train_seconds': args.train_seconds,
                          'heldout_seconds': args.heldout_seconds, 'S_hat': 'exact', 'floor_db': floor_db,
                          'selection': 'grid search on train seeds, ensemble cumulative dB, all train seeds stable',
                          'change_at_s': args.change_at},
           'methods': {}}
    for method in [_naming.method_key(m) for m in args.methods.split(',')]:
        t0 = time.time()
        rows = []
        for params in grid(method):
            runs = [run(cfg, sd, method, params, args.train_seconds, args.change_at) for sd in train]
            rows.append({'params': params, 'train_cumulative_db': score(runs, cfg)})
        rows.sort(key=lambda r: r['train_cumulative_db'])
        best = rows[0]['params']
        held_runs = [run(cfg, sd, method, best, args.heldout_seconds, args.change_at) for sd in held]
        out['methods'][method] = {'best_params': best, 'grid': rows, 'heldout': summarize(held_runs, cfg, floor_db),
                                  'n_grid': len(rows), 'elapsed_s': time.time() - t0}
        h = out['methods'][method]['heldout']
        m = h if h.get('primary_valid') else h.get('stable_only_diagnostic', {})
        print(f"{method:22s} best={best} stable={h['stable']}/{h['n']} "
              f"pts={ {k: round(v, 2) for k, v in m.get('points_db', {}).items()} } th={m.get('threshold_s')} "
              f"({time.time() - t0:.0f}s)", flush=True)
    od = Path(args.out); od.mkdir(parents=True, exist_ok=True)
    (od / 'summary.json').write_text(json.dumps(out, indent=1))


if __name__ == '__main__':
    main()
