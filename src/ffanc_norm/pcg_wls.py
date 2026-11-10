"""PCG-WLS: PCG for windowed least squares, exact-covariance frequency-domain form for feedforward ANC.

Production form. The method was called E-PCG before v1.2.0 (ffanc_norm.epcg is the deprecated alias).

Per hop (H new samples) the controller is the ridge-regularized least-squares
solution on the window [t0, stop) of the virtual-residual regression

    d_hat = e - S_hat * y,   residual(w) = d_hat + x_f * w,   x_f = S_hat * x,

solved by warm-started preconditioned CG. Every matrix-vector product uses FFTs of
size 2M and O(M) vector operations:

    X^T X = T(r) + Z(t0)^T Z(t0) - Z(stop)^T Z(stop).

Statistics r (autocorrelation), p = X^T d_hat and ||d_hat||^2 are kept per hop
segment (one FFT correlation per new hop); moving a window start subtracts the
cached segment, so no statistic is recomputed. Change detection is the score test
of the recent J-hop gradient (Proposition 5); with kd = 0 the inverse covariance in
the statistic is replaced by the circulant (bin-PSD) preconditioner, i.e. the
frequency-domain score  S = sum_k |G_k|^2 / ((P_k + ridge) sigma^2). On detection
the change time is localized by an ML variance change point (Proposition 4).

The class keeps full signal histories for clarity; a real-time version needs only
the last L*H + M samples. All FFTs go through FFTCounter for flop accounting.
"""
from __future__ import annotations

import copy
from dataclasses import dataclass, field
import numpy as np


def fft_flops(n: int) -> float:
    """Real FFT of length n: 2.5 n log2 n flops (split-radix, real-input estimate)."""
    return 2.5 * n * np.log2(n)


class FFTCounter:
    """Counts real FFTs (forward + inverse) and other flops."""

    def __init__(self) -> None:
        self.calls: dict[int, int] = {}
        self.direct_flops = 0.0

    def rfft(self, a, n):
        self.calls[n] = self.calls.get(n, 0) + 1
        return np.fft.rfft(a, n)

    def irfft(self, A, n):
        self.calls[n] = self.calls.get(n, 0) + 1
        return np.fft.irfft(A, n)

    def n_fft(self) -> int:
        return sum(self.calls.values())

    def flops(self) -> float:
        return sum(c * fft_flops(n) for n, c in self.calls.items()) + self.direct_flops

    def reset(self) -> None:
        self.calls.clear(); self.direct_flops = 0.0


CMUL = 6.0   # flops per complex multiply
CADD = 2.0


@dataclass
class PcgWlsConfig:
    M: int = 256
    H: int = 128
    L_hops: int = 32
    ridge: float = 1e-3            # relative to r[0]
    k: int = 8                     # CG iterations per hop (transient)
    k_first: int = 32              # iterations during the first k_first_hops after (re)start
    k_first_hops: int = 4
    k_steady: int = 1              # iterations once the window holds > k_hops hops
    k_hops: int = 16
    detect: bool = True
    J: int = 4
    # stage 2 statistic:
    #   'sandwich' : g^T (X_J^T C X_J)^{-1} g / m0, C = residual autocovariance (colored residual, Prop. 7),
    #                m0 = M (1 - n_J/n_L) n_L/(n_L - M); threshold chi^2_M quantile at det_fa
    #   'score'    : g^T (G_J + rho I)^{-1} g / sigma^2 (white-residual model, Prop. 5; kept for reproduction)
    det_stat: str = 'sandwich'
    det_fa: float = 1e-7           # per-hop false-alarm target (sandwich); 0 -> use `threshold`
    threshold: float = 2.0         # S / M threshold when det_fa = 0
    det_ridge: float = 1e-3        # 'score' ridge, relative to rJ[0]
    kd: int = 32                   # stage-2 PCG iterations (conservative, Prop. 6a, early stop on crossing); -1 = dense reference
    sw_lags: int = 0               # residual autocovariance lags (Bartlett window); 0 -> H
    local_scale: bool = False      # Prop. 7b (rejected): J-window noise level, F(M, n_J - M) threshold; 2-3 hop detection delay
    sw_pre: str = 'L'              # stage-2 preconditioner spectrum: 'L' main-window PSD (x n_J/n_L) or 'J' J-window
    sw_refine: int = 8             # main-problem CG iterations before the score (theory assumes w = window LS)
    screen_fa: float = 1e-2        # stage 1: residual-energy test of the newest hop at this per-hop rate; 0 -> off
    localize: bool = True
    loc_step: int = 8
    # Prop. 8: after a detection keep the no-restart branch A next to the restarted branch B and
    # choose by the sequential predictive likelihood ratio on the following hops
    adapt: str = 'weight'          # on detection: 'restart' (Props. 4, 8) or 'weight' (Prop. 9: weight alpha on pre-change data)
    k_B: int = 8                   # 'weight': CG iterations per hop for the post-change-only solution w_B
    # weight_consistent (2026-10-28, bug fix behind a flag): the weighted solve (Prop. 9) uses the same growing-length rule
    # (grow_len) and statistical CG stopping (cg_stat_tol) as the plain window solve, with the effective number of
    # samples n_eff = alpha n_A + n_B. Without it the weighted path solved the full M-tap problem from n_B << M post-change
    # samples (and with alpha = 0 was NOT the restart solution: ablation_v6_5, S7 ar1 about 5 dB worse than restart).
    weight_consistent: bool = False
    # fixes_1028 (code review 2026-10-28; bug fixes behind a flag): (a) w_A of Prop. 9 = LS solution of the pre-change
    # window A = [t0, tau) only (was the pooled solution incl. post-change samples); (b) first plug-in hop: w_B warm
    # start = current w (was w_A, not converged in k_B iterations -> alpha spikes); (c) the w_A variance term of D_hat
    # uses n_A at the event (was the shrinking current n_A); (d) pre-change level sA2 from hops before tau (was before
    # the detection hop: post-change hops leaked in); (e) _sub_range's direct segment no longer overwrites the stage-1
    # FFT cache _lastB; (f) w_B solved to the statistical tolerance (cap 64 iterations); (g) during an event the score
    # refinement does not overwrite the weighted controller; (h) n_A at the event also in the n_B <= M + H branch.
    fixes_1028: bool = False
    # loc_wide: change-point search over the whole J window (was the detection hop only: tau stuck at the hop start
    # when the detection is late). det_C_pre: residual autocovariance of the sandwich test from [t0, tJ) (the reference
    # part, H0 nuisance) instead of the whole window incl. the tested J window.
    loc_wide: bool = False
    det_C_pre: bool = False
    band: str = 'none'             # 'weight' with n_B > M: 'tree' = band-wise Stein weights on (w_A, w_B), penalized-SURE dyadic tree
    band_kappa: float = 1.0        # tree penalty constant (theory value 1)
    steady_solver: str = 'pcg'     # 'richardson' (x <- x + C^{-1}(b - G x)) DIVERGES in practice (spec(C^{-1}G) exceeds 2
                                   # where the floored circulant PSD underestimates the windowed Toeplitz); kept for the record
    cg_stat_exactJ: bool = False   # (review 2026-10-25) the statistical stopping rule estimates the window LS cost as
                                   # J(x) = e0 + x.p - x.res; with the ridge and the robust ridge Lambda active, res
                                   # contains them, so this is J(x) + ridge |x|^2 + x^T Lambda x (an over-estimate after an
                                   # event -> early stop). True: subtract the penalty, x^T Lambda x by Parseval from the
                                   # spectrum of x, which is kept up to date from the search directions' spectra (one FFT
                                   # per solve, none per iteration)
    pre_window: object = None      # (2026-10-24, cost) None: preconditioner symbol = DFT of [r, 0, r reversed] (truncated
                                   # autocorrelation: Dirichlet sidelobes, can be <= 0 -> floored at 1e-3 max); 'bartlett':
                                   # DFT of the Bartlett-tapered autocorrelation (1 - k/M) r_k = Fejer-smoothed periodogram,
                                   # >= 0 (positive symbol as in the Strang / T. Chan theory), no floor needed
                                   # (results/pcg_iters/precond_choice.md: tracking excess / LS excess at 4 its 0.39 -> 0.05 harmonic)
    steady_every: int = 1          # steady state, no event: run the k_steady iterations only every n-th hop (the
                                   # statistics are still updated every hop; the solution lags by < n hops)
    reg_gate: str = 'always'       # 'after_event': the robust ridge is switched on at the first detected change (S_hat is
                                   # assumed exact until something moves; an error-mic movement also changes P -> detected)
    score_unreg: bool = False      # with reg_eps: compute the change score from the unregularized window LS solution
                                   # (the score test assumes w = LS; the robust ridge biases w and inflates the score)
    reg_eps: object = None         # Prop. 10: per-bin bound eps_k >= -Re((S_k - S_hat_k) / S_hat_k) on the 2M grid (M+1 values)
    reg_gamma: float = 0.5         # robust margin: -Re(rho_eff) <= gamma  (convergence exponent >= 1 - gamma)
    cg_auto: bool = False          # R3 (2026-10-20): no iteration schedule; every main-problem solve (steady, transient,
                                   # event-weighted, post-change-only w_B, refinement before the score) iterates until the
                                   # CG error is below cg_stat_tol (default 0.1) of the LS estimation error, capped at cg_cap.
                                   # Replaces k, k_first, k_first_hops, k_steady, k_hops, steady_every, k_B, sw_refine.
    cg_cap: int = 64
    cg_stat_tol: object = None     # statistical early stopping of the main PCG (None = fixed iteration counts, the
                                   # original behaviour): stop as soon as the optimization excess of the iterate,
                                   # r^T C^{-1} r ~ (w - w_LS)^T G (w - w_LS), is below tol * sigma^2 * M, the
                                   # estimation excess of the window LS solution itself (k_it stays the upper bound)
    grow_len: object = None        # (2026-10-24, v6) 'half': while the window holds n < 2M samples (start-up, restart),
                                   # the control solve uses only the first M_eff = max(n // 2, 1) taps (residual dof
                                   # n - M_eff >= M_eff, the same dof condition as cg_stat_mindof): the LS estimation
                                   # excess J M_eff / (n - M_eff) stays <= J instead of diverging at n ~ M. Detection
                                   # statistics keep the full length (the score is computed from the full-length LS
                                   # solution: score_unreg or det_stat 'sandwich' with sw_refine > 0 is required).
                                   # Applies to the plain window solve only (not to cg_auto, nor to the event-weighted
                                   # solve of Prop. 9, whose effective sample size includes the weighted pre-change
                                   # data). None = original behaviour
    cg_stat_mindof: object = None  # (2026-10-24, v6) the statistical rule needs a noise-level estimate J / (n - M): it is
                                   # applied only when the residual dof n - M >= cg_stat_mindof ('M' -> M); below, the
                                   # fixed iteration count is used. None = original behaviour (for n <= M the rule's
                                   # tolerance is tol M J(x) / 1 and stops the PCG before the first iteration: w stays 0)
    # Risk-comparison detection threshold (framework v2 step 1, 2026-10-23; off by default -> det_fa threshold).
    # Switch (event) iff the estimated loss of holding the pooled window exceeds the cost of switching:
    #   hold loss  L_H(D) = H sum_h M n_A n_B x^2 / (n_L^2 (n_L + n_B x)),  x = n_A D / M   (Prop. 9, alpha = 1 vs alpha*)
    #   switch cost C = (E_full - E_hold) (T_lat - T_rem)_+ / sigma^2 + V,  E = Thm 4 term (iii) ridge excess per sample,
    #   V = 2 ln(n_L / n_J) (positive-part Stein estimator at D = 0).  Threshold: q* = m0 + kappa D*,  L_H(D*) = C,
    #   kappa = (1 - n_J/n_L)^2 n_J (noncentrality of the J-window score for a change at the J-window start).
    det_risk: bool = False
    det_risk_eps: object = None    # full-spec bound eps_k (movement_bound of the current S_hat); None -> reg_eps
    det_risk_T: int = 0            # T_lat: samples from an event to the earliest SHRINK release (check window + spread)
    det_risk_Trem: int = 0         # samples of full-spec ridge still ahead under 'hold' (pending SHRINK); set per hop
    det_risk_hold0: bool = False   # True while a SHRINK is pending: ridge after release taken as 0 (residual spec ~ 0)
    # Safety cap (Thm 6, A2): harmful changes (-Re rho_eff,k > gamma in an excited bin) must be detected with probability
    # >= 1 - beta. With the direct-path family rho_k(u) (|u| <= D), the smallest harmful noncentrality is
    #   D_h = min_{u harmful} sum_k c_k |rho_k(u)|^2,  c_k = g_k P_k |W_k|^2 / (n2 n sigma^2) (anti-noise power per bin),
    # and q_safe = m0 + kappa D_h - z_beta sqrt(2 s m0 + 4 s kappa D_h), s = m0 / M (scaled noncentral chi^2, normal).
    # Threshold = min(q*, q_safe). None -> no cap.
    det_risk_rho: object = None    # (M+1, n_u) complex rho_k(u) of the direct-path family (set by the experiment wrapper)
    det_risk_beta: float = 0.01    # miss probability of a harmful change (= the one safety level alpha_s of v5)
    # det_risk_v2 (2026-10-23, with det_risk): (a) hold loss also for a secondary-path change u of the direct-path family:
    # Thm 4 per-bin mean recursion (terms i + ii) under hold (pooled window, S_hat uncorrected unless a SHRINK is pending)
    # vs switch (Prop. 9 weights, S_hat corrected and window rebuilt after T_lat), over the horizon 1/a hops; q*_S =
    # m0 + kappa min{D_S(u): L_S(u) > C}; (b) excited bins = anti-noise power above the per-bin noise floor
    # (c_k >= g_k / n2); (c) the safety cap applies only if a harmful change is detectable in one window at level beta
    # (q_safe >= null beta-quantile), otherwise A2 is not attainable by the window test and the cap is dropped (logged).
    det_risk_v2: bool = False
    det_risk_hz: int = 50          # horizon in hops = 1 / a (switching hazard; the multi-window variant's share a = 0.02)
    # det_bayes (framework v2 step 1, option A; with det_risk + det_risk_exact for C): Bayesian quickest detection,
    # one-step look-ahead (Shiryaev) rule: switch iff posterior odds of a change x delay cost per hop >= C, i.e.
    #   sum_{n_B in {H, 2H, ..., n_J}} (a / (1 - a)) B(q | n_B) c_d(D_hat(n_B), n_B) >= C,
    # a = 1 / det_risk_hz (switching hazard), B = GLR Bayes factor of q (normal approximation of the scaled noncentral
    # chi^2, D_hat = (q - m0) / kappa(n_B), kappa(n_B) = (1 - n_B/n_L)^2 n_B^2 / n_J), c_d = H * (e_H - e_S) of Prop. 9 at
    # (n_A, n_B) = (n_L - n_B, n_B). The risk threshold q* and the safety cap are not used.
    det_bayes: bool = False
    det_risk_exact: bool = False   # bias of the ridge on the UNregularized target W_T: (lambda/(P+lambda))^2 (exact Whittle);
                                   # the det_risk / det_risk_v2 runs used (lambda/P)^2 (G4 form, valid only for the applied
                                   # regularized W) on W_T -> switching cost overestimated where lambda >> P (bug, kept for records)
    # (2026-11-07, Revision 11-A G5) solver of every _pcg call: 'pcg' (default, unchanged) or 'exact' (the same
    # regularized windowed normal equations solved directly: dense operator from batched FFTs + LU solve; on the
    # grow_len subspace the leading meff x meff block). Iteration counts and statistical stopping do not apply.
    solver: str = 'pcg'
    branch_hops: int = 0           # max trial length in hops (0 = off; used with adapt='restart')
    branch_fa: float = 1e-3        # confirmation test level (rolling back a true change costs a re-detection)


@dataclass
class PcgWls:
    cfg: PcgWlsConfig
    fft: FFTCounter = field(default_factory=FFTCounter)

    def __post_init__(self) -> None:
        c = self.cfg; M = c.M
        if c.grow_len is not None and not (c.score_unreg or (c.det_stat == 'sandwich' and c.sw_refine > 0)):
            # review 2026-10-24: otherwise the change score would be evaluated at the truncated controller
            raise ValueError("grow_len needs a full-length score solution (score_unreg or det_stat='sandwich', sw_refine>0)")
        self.n2 = 2 * M
        self.nseg = int(2 ** np.ceil(np.log2(c.H + M - 1)))
        kk = np.arange(M + 1)
        self.rot = np.exp(-2j * np.pi * kk * (M - 1) / self.n2)
        self.w = np.zeros(M)
        self.xf = np.zeros(0); self.dh = np.zeros(0)
        self.stop = 0; self.restart = 0
        self.t0 = 0; self.tJ = 0
        self.r = np.zeros(M); self.p = np.zeros(M); self.e0 = 0.0
        self.rJ = np.zeros(M); self.pJ = np.zeros(M); self.e0J = 0.0
        self.seg: dict[int, tuple] = {}            # s0 -> (s1, dr, dp, de)
        self.resets: list[int] = []; self.locs: list[int] = []; self.scores: list[float] = []
        self._ecache: dict[int, np.ndarray] = {}
        self.pe: list[tuple] = []                   # (hop start, one-step residual energy / H, |FFT_2H|^2)
        self.screen_hist: list[float] = []
        self.c1 = None
        self.thr = None
        self.risk_log: list[tuple] = []             # det_risk: (stop, C, D*, E_full / sigma^2, T)
        self.branch = None; self.br = None; self.rollbacks: list[int] = []; self.suppress_detect = False; self._pending = None
        self.noise_t0 = 0                          # start of the current noise regime (set by a rollback)
        self.ev = None; self.alpha_hist: list[tuple[int, float]] = []
        self.w_ls = None
        self.skip_solve = False                    # batch catch-up (sid rebuild): statistics only, no PCG solve

    # ---------- statistics ----------
    def _segment_stats(self, s0: int, s1: int):
        """dr[l] = sum_{n=s0}^{s1-1} xf[n] xf[n-l], dp[l] = sum dh[n] xf[n-l], de = ||dh||^2."""
        M = self.cfg.M
        n = max(self.nseg, int(2 ** np.ceil(np.log2(s1 - s0 + M - 1))))
        lo = max(0, s0 - M + 1)
        b = np.concatenate([np.zeros(M - 1 - (s0 - lo)), self.xf[lo:s1]])    # xf[s0-M+1 .. s1-1]
        B = self.fft.rfft(b, n)
        A = self.fft.rfft(self.xf[s0:s1], n); D = self.fft.rfft(self.dh[s0:s1], n)
        # c[j] = sum_i a[i] b[i+j]  ->  lag l = M-1-j
        cr = self.fft.irfft(np.conj(A) * B, n)[:M][::-1]
        cp = self.fft.irfft(np.conj(D) * B, n)[:M][::-1]
        de = float(self.dh[s0:s1] @ self.dh[s0:s1])
        self.fft.direct_flops += 2 * CMUL * (n // 2 + 1) + 2.0 * (s1 - s0)
        self._lastB = (B, n)
        return (s1, cr.copy(), cp.copy(), de)

    def _sub_range(self, a: int, b: int, which: str) -> None:
        """Remove [a, b) from a window, using cached segments when aligned."""
        while a < b:
            sg = self.seg.get(a)
            if sg is not None and sg[0] <= b:
                s1, dr, dp, de = sg
            else:                                       # unaligned piece (rare): direct
                s1 = min([s for s in self.seg if s > a] + [b])
                _lb = getattr(self, '_lastB', None)
                _, dr, dp, de = self._segment_stats(a, s1)
                if self.cfg.fixes_1028 and _lb is not None:
                    self._lastB = _lb                   # keep the stage-1 cache of the newest hop
            if which == 'main':
                self.r -= dr; self.p -= dp; self.e0 -= de
            else:
                self.rJ -= dr; self.pJ -= dp; self.e0J -= de
            a = s1

    def _prune(self) -> None:
        keep = min(self.t0, self.tJ) if self.cfg.detect else self.t0
        for s in [s for s, v in self.seg.items() if v[0] <= keep]:
            del self.seg[s]

    # ---------- operators ----------
    def _edge_fft(self, tb: int) -> np.ndarray:
        """FFT (size 2M) of the M-1 samples before boundary tb (zeros before 0); cached per hop."""
        E = self._ecache.get(tb)
        if E is None:
            M = self.cfg.M
            xs = np.zeros(M - 1)
            lo = max(0, tb - M + 1)
            if tb > 0:
                xs[M - 1 - (tb - lo):] = self.xf[lo:tb]
            E = self.fft.rfft(xs, self.n2)
            self._ecache[tb] = E
        return E

    def _edge(self, E: np.ndarray, U: np.ndarray) -> np.ndarray:
        """DFT of Z^T Z u (Z: edge matrix of the boundary whose FFT is E), U = DFT(u)."""
        M = self.cfg.M
        zu = self.fft.irfft(U * E, self.n2)[M - 1:2 * M - 2]
        self.fft.direct_flops += 3 * CMUL * (M + 1)
        return self.rot * self.fft.rfft(zu, self.n2) * np.conj(E)

    def _circ(self, r: np.ndarray) -> np.ndarray:
        return self.fft.rfft(np.concatenate([r, [0.0], r[:0:-1]]), self.n2)

    def _apply(self, Cf, ta, U, estop=None):
        """DFT-domain X^T X u on [ta, stop) (before truncation); estop = shared stop-edge term."""
        acc = Cf * U
        if isinstance(ta, (list, tuple)):              # weighted window: [(coef, boundary), ...]
            for coef, tb in ta:
                if tb > 0 and coef != 0.0:
                    acc = acc + coef * self._edge(self._edge_fft(tb), U)
        elif ta > 0:
            acc = acc + self._edge(self._edge_fft(ta), U)
        acc = acc - (estop if estop is not None else self._edge(self._edge_fft(self.stop), U))
        self.fft.direct_flops += (CMUL + 2 * CADD) * (self.cfg.M + 1)
        return acc

    def _ridge_excess(self, Cf, lam, W):
        """Thm 4 term (iii) per sample (Whittle): (1/(n2 n)) sum_k g_k P_k |W_k|^2 (lam_k / P_k)^2 (as in log_ridge, W =
        applied regularized controller); with det_risk_exact, W = unregularized target and factor (lam / (P + lam))^2."""
        if lam is None:
            return 0.0
        P = np.maximum(Cf.real, 1e-3 * np.max(Cf.real))
        g = np.full(len(P), 2.0); g[0] = g[-1] = 1.0
        f = (lam / (P + lam)) ** 2 if self.cfg.det_risk_exact else (lam / P) ** 2
        return float(np.sum(g * P * np.abs(W) ** 2 * f) / (self.n2 * max(self.stop - self.t0, 1)))

    def _risk_threshold(self, m0, sig2, nwin, nJ, Cm, w_applied):
        """det_risk: threshold on q from the risk comparison (see PcgWlsConfig.det_risk). Returns (q*, C, D*)."""
        c = self.cfg; M, H = c.M, c.H
        W = self.fft.rfft(w_applied, self.n2)
        P = np.maximum(Cm.real, 1e-3 * np.max(Cm.real))
        eps_full = c.det_risk_eps if c.det_risk_eps is not None else c.reg_eps
        lam_full = None if eps_full is None else P * np.maximum(0.0, np.asarray(eps_full) / c.reg_gamma - 1.0)
        E_full = self._ridge_excess(Cm, lam_full, W)
        E_hold = 0.0 if c.det_risk_hold0 else self._ridge_excess(Cm, self._robust_reg(Cm), W)
        T = max(int(c.det_risk_T) - int(c.det_risk_Trem), 0)
        nL = float(nwin); nJ = float(min(nJ, nwin - H))
        C = max(E_full - E_hold, 0.0) * T / max(sig2, 1e-300) + 2.0 * np.log(nL / max(nJ, 1.0))

        def LH(D):
            s, nB = 0.0, nJ
            while nB < nL:
                nA = nL - nB; x = nA * D / M
                s += H * M * nA * nB * x * x / (nL * nL * (nL + nB * x)); nB += H
            return s
        lo, hi = 1e-6, 1e6
        for _ in range(60):                               # bisection on log D (L_H increasing in D)
            mid = np.sqrt(lo * hi)
            lo, hi = (mid, hi) if LH(mid) < C else (lo, mid)
        Ds = hi
        kap = (1.0 - nJ / nL) ** 2 * nJ
        qs = m0 + kap * Ds
        if c.det_bayes:
            a = 1.0 / max(int(c.det_risk_hz), 1); s_ = m0 / M; v0 = 2.0 * s_ * m0
            nBs = np.arange(H, int(nJ) + 1, H, dtype=float)
            kaps = (1.0 - nBs / nL) ** 2 * nBs ** 2 / nJ

            def f(q):
                D = max(q - m0, 1e-12) / kaps
                v1 = v0 + 4.0 * s_ * kaps * D
                logB = (q - m0) ** 2 / (2.0 * v0) - 0.5 * np.log(v1 / v0)
                nA = nL - nBs; x = nA * D / M
                cd = H * M * nA * nBs * x * x / (nL * nL * (nL + nBs * x))
                lv = np.log(a / (1.0 - a)) + logB + np.log(np.maximum(cd, 1e-300))
                mx = np.max(lv)
                return mx + np.log(np.sum(np.exp(lv - mx))) - np.log(max(C, 1e-300))
            lo, hi = m0 * (1.0 + 1e-6), m0 * 50.0
            if f(lo) >= 0:
                qB = lo
            else:
                for _ in range(60):
                    mid = 0.5 * (lo + hi)
                    lo, hi = (mid, hi) if f(mid) < 0 else (lo, mid)
                qB = hi
            self.risk_log.append((self.stop, float(C), float(Ds), float(E_full / max(sig2, 1e-300)), T, np.inf,
                                  float(qs / m0), np.inf, float(qB / m0)))
            return qB, C, Ds
        Dh, qsafe, qS = np.inf, np.inf, np.inf
        if c.det_risk_rho is not None:
            from scipy.stats import norm
            rho = np.asarray(c.det_risk_rho)
            g = np.full(len(P), 2.0); g[0] = g[-1] = 1.0
            cu = g * P / (self.n2 * max(self.stop - self.t0, 1) * max(sig2, 1e-300))   # per-sample excess per |dW_k|^2
            ck = cu * np.abs(W) ** 2                                  # anti-noise power per bin / sigma^2
            lam = self._robust_reg(Cm)
            shv = np.ones(len(P)) if lam is None else P / (P + lam)  # current ridge: rho_eff = rho P / (P + lambda)
            if c.det_risk_v2:
                exc = ck >= g / self.n2                              # anti-noise above the per-bin noise floor
            else:
                exc = Cm.real > 1e-3 * np.max(Cm.real)               # excited bins (above the PSD floor)
            harm = np.max(np.where(exc[:, None], -np.real(rho) * shv[:, None], -np.inf), axis=0) > c.reg_gamma
            s = m0 / M; zb = norm.isf(c.det_risk_beta)
            if np.any(harm):
                Dh = float(np.min((ck[:, None] * np.abs(rho[:, harm]) ** 2).sum(0)))
                qsafe = m0 + kap * Dh - zb * np.sqrt(2 * s * m0 + 4 * s * kap * Dh)
                if c.det_risk_v2 and qsafe < m0 + zb * np.sqrt(2 * s * m0):
                    qsafe = np.inf                                   # A2 not attainable in one window: no cap
            if c.det_risk_v2:
                DS = (ck[:, None] * np.abs(rho) ** 2).sum(0)          # noncentrality of each u (per sample, sigma^2)
                LS = self._loop_loss(rho, W, cu, DS, nL, nJ, C)
                ok = LS > C
                if np.any(ok):
                    qS = m0 + kap * float(np.min(DS[ok]))
        self.risk_log.append((self.stop, float(C), float(Ds), float(E_full / max(sig2, 1e-300)), T, float(Dh),
                              float(qs / m0), float(qsafe / m0), float(qS / m0)))
        return min(qs, qsafe, qS), C, Ds

    def _loop_loss(self, rho, W, cu, DS, nL, nJ, C):
        """det_risk_v2: hold loss of a secondary-path change u (columns of rho), Thm 4 per-bin mean recursion (Whittle).
        Segments of H samples after the change; m_s = error of the controller applied in segment s (m_0 = -delta,
        delta_k = W_new - W_old = -W_k rho_k / (1 + rho_k)); estimate after segment s from the window segments:
            m_{s+1} = (-lam_pre n_pre delta - rho sum_{post in window} m_j) / (lam_pre n_pre + n_post)
        (pre-change segments: loop ratio 0; post: rho). Hold: lam_pre = 1, S_hat corrected only if a SHRINK is pending
        (at T_rem); switch at s0 = n_J / H: lam_pre = alpha_u = 1 / (1 + n_A D_S(u) / M), S_hat corrected and window
        rebuilt from the change after T_lat (mean error 0). Per-sample excess sum_k cu_k |m_k|^2 plus the variance term
        (hold M / n_L; switch M / (n_B + n_eff) before, M / n_B after the rebuild). Returns L_S(u), sigma^2 x samples."""
        c = self.cfg; M, H = c.M, c.H
        L = int(round(nL / H)); s0 = int(round(nJ / H)); hz = int(c.det_risk_hz)
        Tsw = max(int(np.ceil(int(c.det_risk_T) / H)), 1)       # a switch (re)starts the check: full T_lat from now
        Thold = int(np.ceil(int(c.det_risk_Trem) / H)) if c.det_risk_hold0 else None
        den = 1.0 + rho
        den = np.where(np.abs(den) < 1e-3, 1e-3, den)
        delta = -W[:, None] * rho / den
        nA0 = (L - s0) * H
        alpha = 1.0 / (1.0 + nA0 * DS / M)                         # (U,)

        def run(switch):
            cs = [np.zeros_like(delta), -delta]                    # cs[j] = sum_{i<j} m_i
            loss = np.zeros(rho.shape[1])
            for s in range(0, s0 + hz):
                n_post = min(s + 1, L); n_pre = L - n_post
                corrected = (switch and s + 1 >= s0 + Tsw) or ((not switch) and Thold is not None and s + 1 >= s0 + Thold)
                if corrected:
                    mn = np.zeros_like(delta)
                else:
                    lp = alpha if (switch and s + 1 > s0) else 1.0
                    sm = cs[s + 1] - cs[max(0, s + 1 - L)]
                    mn = (-lp * n_pre * delta - rho * sm) / (lp * n_pre + n_post)
                cs.append(cs[-1] + mn)
                if s + 1 >= s0:                                    # loss from the decision on
                    ex = (cu[:, None] * np.abs(mn) ** 2).sum(0)
                    nB = n_post * H
                    if corrected:
                        var = M / nB
                    elif switch and s + 1 > s0:
                        nA = n_pre * H; neff = M * nA / (nA * DS + M)
                        var = M / (nB + neff)
                    else:
                        var = M / nL * np.ones_like(ex)
                    loss += H * (ex + var)
            return loss
        return run(False) - run(True)

    def _robust_reg(self, Cf):
        """Prop. 10: lambda_k = P_k max(0, eps_k / gamma - 1) so that -Re(rho_k) P_k/(P_k + lambda_k) <= gamma."""
        eps = self.cfg.reg_eps
        if eps is None or (self.cfg.reg_gate == 'after_event' and not self.resets):
            return None
        P = np.maximum(Cf.real, 1e-3 * np.max(Cf.real))
        return P * np.maximum(0.0, np.asarray(eps) / self.cfg.reg_gamma - 1.0)

    def _pcg(self, Cf, ta, ridge, b, x0, iters, Gx0=None, use_reg=False, richardson=False, stop_rz=None, meff=None):
        """Warm-started PCG on (X^T X + ridge I) x = b, circulant preconditioner (or preconditioned Richardson).
        meff < M (grow_len): PCG on the subspace of the first meff taps (projected operator and preconditioner)."""
        M, n2 = self.cfg.M, self.n2
        if self.cfg.solver == 'exact' and not richardson:
            return self._exact_solve(Cf, ta, ridge, b, use_reg, meff)
        if meff is not None and meff < M:
            msk = np.zeros(M); msk[:meff] = 1.0
            x0 = x0 * msk; b = b * msk; Gx0 = None
        else:
            msk = None
        # 'bartlett_s': Bartlett symbol only on the full-length problem (n >= 2M, outside the growing window): the
        # Strang / T. Chan clustering is an n >> M statement; during the growth the truncated-autocorrelation symbol
        # gave the better first hops (AR1 start-up, results/v6_4_dev)
        _bart = (self.cfg.pre_window in ('bartlett', 'bartlett_m')
                 or (self.cfg.pre_window == 'bartlett_s' and (meff is None or meff >= M)))
        if _bart:
            # symbol of the Bartlett-tapered autocorrelation (2 FFTs per solve, not per iteration); 'bartlett_m': on the
            # truncated problem (meff < M, growing window) the taper length is the number of free taps
            mt = meff if (self.cfg.pre_window == 'bartlett_m' and meff is not None and meff < M) else M
            rr = self.fft.irfft(Cf, n2)[:M] * np.maximum(1.0 - np.arange(M) / mt, 0.0)
            Cb = self.fft.rfft(np.concatenate([rr, [0.0], rr[:0:-1]]), n2)
            self.fft.direct_flops += 2.0 * M
            pre = np.maximum(Cb.real, 1e-9 * np.max(Cb.real)) + ridge
        else:
            pre = np.maximum(Cf.real, 1e-3 * np.max(Cf.real)) + ridge
        lam = self._robust_reg(Cf) if use_reg else None
        if lam is not None:
            pre = pre + lam

        _last = {}

        def G(u):
            U = self.fft.rfft(u, n2)
            _last['U'] = U
            acc = self._apply(Cf, ta, U)
            if lam is not None:
                acc = acc + lam * U
            out_ = self.fft.irfft(acc, n2)[:M] + ridge * u
            return out_ if msk is None else out_ * msk

        def Minv(v):
            self.fft.direct_flops += 2.0 * (M + 1)
            out_ = self.fft.irfft(self.fft.rfft(v, n2) / pre, n2)[:M]
            return out_ if msk is None else out_ * msk

        x = x0.copy()
        if not np.any(x):
            res = b.copy()
        else:
            res = b - (Gx0 + ridge * x if (Gx0 is not None and lam is None) else G(x))
        if richardson:
            for it in range(iters):
                x = x + Minv(res)
                if it + 1 < iters:
                    res = b - G(x)
            self.fft.direct_flops += 4.0 * M * (iters + 1)
            return x
        z = Minv(res); pv = z.copy(); rz = float(res @ z)
        self.last_its = 0
        track = bool(self.cfg.cg_stat_exactJ and stop_rz is not None and msk is None)
        if track:
            Xs = self.fft.rfft(x, n2) if np.any(x) else np.zeros(n2 // 2 + 1, complex)
            gw = np.full(n2 // 2 + 1, 2.0); gw[0] = gw[-1] = 1.0
            pen = lambda: ridge * float(x @ x) + (float(np.sum(gw * lam * np.abs(Xs) ** 2)) / n2 if lam is not None else 0.0)
        for _ in range(iters):
            if stop_rz is not None and rz <= (stop_rz(x, res, pen()) if track else stop_rz(x, res)):
                break
            self.last_its += 1
            Ap = G(pv)
            a = rz / float(pv @ Ap + 1e-300)
            x = x + a * pv; res = res - a * Ap
            if track:
                Xs = Xs + a * _last['U']
                self.fft.direct_flops += 6.0 * (n2 // 2 + 1)
            z = Minv(res); rz_new = float(res @ z)
            pv = z + (rz_new / (rz + 1e-300)) * pv; rz = rz_new
        self.fft.direct_flops += 12.0 * M * (self.last_its + 1)
        return x

    def _exact_solve(self, Cf, ta, ridge, b, use_reg, meff):
        """(Revision 11-A G5) direct solve of the system that _pcg iterates on: (G + ridge I [+ Lambda]) x = b with G the
        operator of _apply (windowed X^T X incl. edges, possibly weighted). The dense matrix is built column-wise with
        batched FFTs of the identity (same operator as the PCG matvec, up to rounding); meff < M: leading block, other
        taps 0 (the limit of the masked PCG). Flops are counted analytically (2 batched FFT passes + LU)."""
        M, n2 = self.cfg.M, self.n2
        U = np.fft.rfft(np.eye(M), n2, axis=0)                  # (M+1, M): DFT of the unit vectors
        acc = Cf[:, None] * U

        def edge(E):
            zu = np.fft.irfft(U * E[:, None], n2, axis=0)[M - 1:2 * M - 2]
            return self.rot[:, None] * np.fft.rfft(zu, n2, axis=0) * np.conj(E)[:, None]
        if isinstance(ta, (list, tuple)):
            for coef, tb in ta:
                if tb > 0 and coef != 0.0:
                    acc = acc + coef * edge(self._edge_fft(tb))
        elif ta > 0:
            acc = acc + edge(self._edge_fft(ta))
        acc = acc - edge(self._edge_fft(self.stop))
        lam = self._robust_reg(Cf) if use_reg else None
        if lam is not None:
            acc = acc + lam[:, None] * U
        A = np.fft.irfft(acc, n2, axis=0)[:M] + ridge * np.eye(M)
        A = 0.5 * (A + A.T)                                      # symmetric by construction; remove rounding asymmetry
        m = M if (meff is None or meff >= M) else int(meff)
        x = np.zeros(M)
        x[:m] = np.linalg.solve(A[:m, :m], np.asarray(b, float)[:m])
        self.fft.direct_flops += 8.0 * M * fft_flops(n2) / 2 + (2.0 / 3.0) * m ** 3 + 2.0 * m * m
        self.last_its = 0
        return x

    def _sandwich_q(self, g, gam, CJ, iters, qthr=np.inf, Cpre=None, ta=None):
        """q_K for (X_J^T C X_J + eps I) z = g by PCG from 0; FFT only. C = Toeplitz(gam).
        q_K is nondecreasing and <= q (Prop. 6a): stops as soon as q_K >= qthr.
        Preconditioner: circulant with symbol (X_J^T X_J circulant) x (residual PSD) (Whittle)."""
        c = self.cfg; M, n2 = c.M, self.n2
        tJ = self.tJ if ta is None else ta
        stop = self.stop; nJ = stop - tJ
        Kg = len(gam)
        nf = int(2 ** np.ceil(np.log2(nJ + 2 * max(M, Kg))))
        lo = max(0, tJ - M + 1)
        Xs = self.fft.rfft(np.concatenate([np.zeros(M - 1 - (tJ - lo)), self.xf[lo:stop]]), nf)
        ker = np.zeros(nf); ker[:Kg] = gam; ker[nf - Kg + 1:] = gam[1:][::-1]
        K = self.fft.rfft(ker, nf)
        Kp = min(Kg, M)
        Phr = self.fft.rfft(np.concatenate([gam[:Kp], np.zeros(n2 - 2 * Kp + 1), gam[1:Kp][::-1]]), n2).real
        base = CJ.real if Cpre is None else Cpre
        pre = np.maximum(base * Phr, 1e-6 * np.max(base * Phr))
        eps = 1e-6 * float(np.mean(pre))

        def B(u):
            v = self.fft.irfft(Xs * self.fft.rfft(u, nf), nf)[M - 1:M - 1 + nJ]          # X_J u
            cv = self.fft.irfft(K * self.fft.rfft(v, nf), nf)[:nJ]                        # C v
            z = self.fft.irfft(np.conj(Xs) * self.fft.rfft(np.concatenate([np.zeros(M - 1), cv]), nf), nf)[:M]
            self.fft.direct_flops += 3 * CMUL * (nf // 2 + 1) + 12.0 * M
            return z + eps * u

        def Minv(v):
            self.fft.direct_flops += 2.0 * (M + 1)
            return self.fft.irfft(self.fft.rfft(v, n2) / (pre + eps), n2)[:M]

        x = np.zeros(M); res = g.copy(); zz = Minv(res); pv = zz.copy(); rz = float(res @ zz)
        q = 0.0
        for _ in range(iters):
            Ap = B(pv); a = rz / float(pv @ Ap + 1e-300)
            x = x + a * pv; res = res - a * Ap
            q = float(g @ x)
            if q >= qthr:
                break
            zz = Minv(res); rz_new = float(res @ zz)
            pv = zz + (rz_new / (rz + 1e-300)) * pv; rz = rz_new
        return q

    def _psd(self, gam):
        """Residual PSD on the 2M grid from an autocovariance (lags < M used)."""
        M, n2 = self.cfg.M, self.n2
        Kp = min(len(gam), M)
        return np.maximum(self.fft.rfft(np.concatenate([gam[:Kp], np.zeros(n2 - 2 * Kp + 1), gam[1:Kp][::-1]]), n2).real, 0.0)

    def _sandwich_dense(self, g, gam):
        """Dense reference of q (O(M^3); analysis only)."""
        from scipy.linalg import toeplitz
        M = self.cfg.M; tJ, stop = self.tJ, self.stop; nJ = stop - tJ
        col = np.zeros(nJ); kk = min(len(gam), nJ); col[:kk] = gam[:kk]
        idx = np.arange(tJ, stop)[:, None] - np.arange(M)[None, :]
        Xs = np.where(idx >= 0, self.xf[np.clip(idx, 0, None)], 0.0)
        Bm = Xs.T @ toeplitz(col) @ Xs
        return float(g @ np.linalg.solve(Bm + 1e-6 * np.trace(Bm) / M * np.eye(M), g))

    def _XtX_dense(self, a, b):
        M = self.cfg.M
        idx = np.arange(a, b)[:, None] - np.arange(M)[None, :]
        Xs = np.where(idx >= 0, self.xf[np.clip(idx, 0, None)], 0.0)
        return Xs.T @ Xs

    def _residual_autocov(self, K):
        """Biased autocovariance (lags < K, Bartlett window) of the in-sample residual of w on [t0, stop)."""
        M = self.cfg.M; t0, stop = max(self.t0, self.noise_t0), self.stop
        if self.cfg.det_C_pre and self.tJ - t0 >= max(2 * K, M):
            stop = self.tJ                              # reference part [t0, tJ): the residual under H0
        nL = stop - t0
        lo = max(0, t0 - M + 1)
        seg = np.concatenate([np.zeros(M - 1 - (t0 - lo)), self.xf[lo:stop]])
        nfl = int(2 ** np.ceil(np.log2(len(seg) + M)))
        res = self.dh[t0:stop] + self.fft.irfft(self.fft.rfft(seg, nfl) * self.fft.rfft(self.w, nfl), nfl)[M - 1:M - 1 + nL]
        nfa = int(2 ** np.ceil(np.log2(nL + K)))
        gam = self.fft.irfft(np.abs(self.fft.rfft(res, nfa)) ** 2, nfa)[:K] / nL
        self.fft.direct_flops += 8.0 * (nfl // 2 + 1) + 8.0 * (nfa // 2 + 1) + 2.0 * nL
        return gam * (1.0 - np.arange(K) / K)

    # ---------- main update ----------
    def _pred_energy(self, xf_hop, dhat_hop) -> float:
        """||d_hat + X_hop w||^2 on the new hop for the current w (one-step predictive residual)."""
        M = self.cfg.M; n = len(xf_hop)
        seg = np.concatenate([np.zeros(max(0, M - 1 - len(self.xf))), self.xf[-(M - 1):] if len(self.xf) else np.zeros(0), xf_hop])
        nf = int(2 ** np.ceil(np.log2(len(seg) + M)))
        y = self.fft.irfft(self.fft.rfft(seg, nf) * self.fft.rfft(self.w, nf), nf)[M - 1:M - 1 + n]
        self.fft.direct_flops += CMUL * (nf // 2 + 1) + 3.0 * n
        r = dhat_hop + y
        return float(r @ r)

    def update(self, xf_hop: np.ndarray, dhat_hop: np.ndarray) -> np.ndarray:
        """Feed one hop of filtered reference and reconstructed disturbance; return the applied w."""
        c = self.cfg
        if self.branch is None:
            w = self._update_core(xf_hop, dhat_hop)
            if self._pending is not None:          # detection in this hop -> start the trial
                self.branch = self._pending; self._pending = None
                self.br = {'LA': 0.0, 'LB': 0.0, 'n': 0, 'hops': 0, 'tau': self.restart}
            return w
        A = self.branch
        eA = A._pred_energy(xf_hop, dhat_hop); eB = self._pred_energy(xf_hop, dhat_hop)
        f0 = A.fft.flops()
        A._update_core(xf_hop, dhat_hop)
        self.fft.direct_flops += A.fft.flops() - f0
        self._update_core(xf_hop, dhat_hop)
        br = self.br; br['hops'] += 1
        M, H = c.M, c.H
        nB = self.stop - self.t0
        if nB - M >= H:
            # Prop. 8 (confirmation): sandwich score of A's controller on B's window [tau, stop) only
            # (no pre-change samples), residual model C from B's in-sample residual (local level).
            # H0 (no plant change): E q = M (1 + n_B / n_A) (A's w is out-of-sample here);
            # threshold F(M, n_B - M) since C is estimated from n_B - M residual dof.
            W = self.fft.rfft(A.w, self.n2)
            CB = self._circ(self.r)
            GBwA = self.fft.irfft(self._apply(CB, self.t0, W), self.n2)[:M]
            g = self.p + GBwA
            gam = self._residual_autocov(c.sw_lags or H) * nB / (nB - M)
            # H0 mean: M + tr(B_B^{-1} G_B Cov(w_A) G_B), Cov(w_A) = G_A^{-1} B_A G_A^{-1} (sandwich);
            # Whittle: per bin (n_B Phi_x,B / n_A Phi_x,A) (Phi_r,A / Phi_r,B)  -> handles level changes of x or n
            gamA = A._residual_autocov(c.sw_lags or H) * (A.stop - A.t0) / max(A.stop - A.t0 - M, 1)
            CA = A._circ(A.r)
            fl = lambda z: np.maximum(z, 1e-3 * np.max(z))          # same spectral floor as the preconditioner
            ratio = (fl(CB.real) / fl(CA.real)) * (fl(self._psd(gamA)) / fl(self._psd(gam)))
            wgt = np.full(M + 1, 2.0); wgt[0] = wgt[-1] = 1.0
            m0 = M + 0.5 * float(np.sum(wgt * ratio))
            from scipy.stats import f as fdist
            thrF = float(fdist.isf(c.branch_fa, M, nB - M))
            q = self._sandwich_q(g, gam, CB, max(c.kd, 1), qthr=thrF * m0, Cpre=CB.real, ta=self.t0)
            br.setdefault('conf', []).append(q / m0)
            if q >= thrF * m0:
                self.branch = None; self.br = None         # plant change confirmed: keep the restart
                return self.w
        if br['hops'] >= c.branch_hops:
            self._rollback(A)                             # not confirmed: no restart (Occam)
            return self.w
        return (A.w if eA < eB else self.w).copy()      # applied meanwhile: better on the latest hop

    def _rollback(self, A) -> None:
        keep = {k: getattr(self, k) for k in ('fft', 'resets', 'locs', 'scores', 'screen_hist', 'rollbacks', 'cfg', 'thr')}
        br = self.br
        self.__dict__.update(A.__dict__)
        self.__dict__.update(keep)
        self.br = br
        # the data preferred 'no plant change': the detection was a change of the residual
        # (noise) level -> keep the controller window, restart the noise statistics at tau
        self.noise_t0 = self.br['tau'] if self.br else self.stop
        self.rollbacks.append(self.stop); self.suppress_detect = False
        self.branch = None; self.br = None; self._pending = None

    def _update_core(self, xf_hop: np.ndarray, dhat_hop: np.ndarray) -> np.ndarray:
        c = self.cfg; M, H, n2 = c.M, c.H, self.n2
        start = self.stop
        self.xf = np.concatenate([self.xf, xf_hop]); self.dh = np.concatenate([self.dh, dhat_hop])
        self.stop = stop = start + len(xf_hop)
        self._ecache = {}
        sg = self._segment_stats(start, stop); self.seg[start] = sg
        _, dr, dp, de = sg
        self.r += dr; self.p += dp; self.e0 += de
        new_t0 = max(self.restart, stop - c.L_hops * H)
        self._sub_range(self.t0, new_t0, 'main'); self.t0 = new_t0
        if self.ev is not None:
            ev = self.ev
            ev['rB'] += dr; ev['pB'] += dp; ev['eB'] += de
            if self.t0 >= ev['tau']:                     # pre-change data aged out of the window
                self.ev = None
        Cm = None; Gw = None
        if c.detect:
            self.rJ += dr; self.pJ += dp; self.e0J += de
            new_tJ = max(self.restart, stop - c.J * H)
            self._sub_range(self.tJ, new_tJ, 'J'); self.tJ = new_tJ
        run_score = (c.detect and not self.suppress_detect and stop - self.restart >= (c.J + 4) * H
                     and stop - self.noise_t0 >= (c.J + 4 if c.adapt == 'weight' else c.J) * H)
        if c.detect and c.screen_fa > 0:
            # stage 1: one-step-ahead residual of the current w on the new hop (2 FFTs, reusing
            # the segment FFT), normalized by the mean one-step residual since the restart
            B, nb = self._lastB
            yw = self.fft.irfft(B * self.fft.rfft(self.w, nb), nb)[M - 1:M - 1 + (stop - start)]
            rn = self.dh[start:stop] + yw
            en = float(rn @ rn) / (stop - start)
            self.last_pred = (start, float(rn @ rn), B, nb)     # exposed for reuse (multi-window scoring)
            self.fft.direct_flops += CMUL * (nb // 2 + 1) + 3.0 * (stop - start)
            lo_h = max(self.restart, self.noise_t0, stop - (c.L_hops + 1) * H)
            past = [z for z in self.pe if z[0] >= lo_h]
            Rn = np.abs(self.fft.rfft(rn, 2 * H)) ** 2
            self.fft.direct_flops += 4.0 * (H + 1)
            self.pe = past + [(start, en, Rn)]
            if run_score and past:
                # E = ||r_new||^2 / (H sigma_pred^2) ~ chi^2_nu / nu (Satterthwaite) with
                # nu = H gamma_0^2 / sum_tau (1 - |tau|/H) gamma_tau^2 from the past one-step residuals
                E = en / max(float(np.mean([z[1] for z in past])), 1e-300)
                gm = np.fft.irfft(np.mean([z[2] for z in past], 0), 2 * H)[:H]
                tri = 1.0 - np.arange(H) / H
                nu = H * gm[0] ** 2 / max(gm[0] ** 2 + 2.0 * float(np.sum(tri[1:] * gm[1:] ** 2)), 1e-300)
                from scipy.stats import chi2
                c1 = float(chi2.isf(c.screen_fa, nu)) / nu
                self.screen_hist.append(E)
                self.last_screen = (start, E, c1)              # exposed (multi-window wake-up test)
                run_score = E > c1
            else:
                run_score = False
        _ft = getattr(self, 'force_tau', None)              # (2026-10-24) external event (consistency detector)
        if _ft is not None and c.detect and not self.suppress_detect:
            run_score = True
        if run_score:
            if self.thr is None:
                from scipy.stats import chi2
                if c.det_fa > 0 and c.det_stat == 'sandwich':
                    from scipy.stats import f as fdist
                    nJ0 = c.J * H
                    self.thr = float(fdist.isf(c.det_fa, M, nJ0 - M)) if (c.local_scale and nJ0 > M) else float(chi2.isf(c.det_fa, M)) / M
                else:
                    self.thr = c.threshold
            w_ctrl = None
            if c.score_unreg and c.reg_eps is not None:
                # score on the unregularized LS solution (kept warm in w_ls); the control filter stays regularized
                w_ctrl = self.w
                x0 = self.w_ls if self.w_ls is not None else self.w
                self.w = self._pcg(self._circ(self.r), self.t0, c.ridge * self.r[0] + 1e-30, -self.p, x0,
                                   c.cg_cap if c.cg_auto else max(c.sw_refine, 8), use_reg=False,
                                   stop_rz=self._stat_stop(self.e0, self.p, stop - self.t0) if c.cg_auto else None)
                self.w_ls = self.w.copy()
            elif c.det_stat == 'sandwich' and c.sw_refine > 0:
                # the score theory assumes w = LS solution of the window: refine the warm start first
                if c.fixes_1028 and self.ev is not None:
                    w_ctrl = self.w                     # event in progress: keep the weighted (Prop. 9) controller
                self.w = self._pcg(self._circ(self.r), self.t0, c.ridge * self.r[0] + 1e-30, -self.p, self.w,
                                   c.cg_cap if c.cg_auto else c.sw_refine, use_reg=True,
                                   stop_rz=self._stat_stop(self.e0, self.p, stop - self.t0) if c.cg_auto else None)
            W = self.fft.rfft(self.w, n2)
            estop = self._edge(self._edge_fft(stop), W)
            CJ = self._circ(self.rJ); Cm = self._circ(self.r)
            GJw = self.fft.irfft(self._apply(CJ, self.tJ, W, estop), n2)[:M]
            Gw = self.fft.irfft(self._apply(Cm, self.t0, W, estop), n2)[:M]
            g = self.pJ + GJw                                   # X_J^T (d_hat + X_J w)
            nwin = stop - self.t0
            if c.det_stat == 'sandwich':
                # Prop. 7: colored-residual (sandwich) score, H0 mean m0 = M (1 - n_J/n_L) n_L/(n_L - M)
                gam = self._residual_autocov(c.sw_lags or H)
                nJ = stop - self.tJ
                rho_ = max(1.0 - nJ / nwin, 1e-3)
                if c.local_scale:
                    # Prop. 7b (Chow-type): noise level from the J-window unrestricted residual,
                    # s2U = (||r_J||^2 - g^T G_J^{-1} g) / (n_J - M); truncated PCG overestimates s2U
                    # (q_K <= q), so the statistic stays conservative
                    eJ = self.e0J + 2.0 * float(self.w @ self.pJ) + float(self.w @ GJw)
                    qw = float(g @ self._pcg(CJ, self.tJ, 1e-6 * self.rJ[0] + 1e-30, g, np.zeros(M), max(c.kd, 0) or 32)) if c.kd >= 0 else \
                        float(g @ np.linalg.solve(self._XtX_dense(self.tJ, stop) + 1e-6 * self.rJ[0] * np.eye(M), g))
                    s2U = max(eJ - qw, 1e-300) / max(nJ - M, 1)
                    scale = gam[0] * nwin / max(nwin - M, 1) / s2U       # (global level, dof-corrected) / local level
                    m0 = M * rho_ / scale
                else:
                    m0 = M * rho_ * nwin / max(nwin - M, 1)
                if c.det_risk:
                    qs, _, _ = self._risk_threshold(m0, gam[0] * nwin / max(nwin - M, 1), nwin, nJ, Cm,
                                                    self.w if c.det_risk_exact else (w_ctrl if w_ctrl is not None else self.w))
                    self.thr = qs / m0                     # S = q M / m0 >= thr M  <=>  q >= q*
                if c.kd < 0:
                    q = self._sandwich_dense(g, gam)
                else:
                    Cpre = None if c.sw_pre == 'J' else Cm.real * nJ / nwin
                    q = self._sandwich_q(g, gam, CJ, c.kd, qthr=self.thr * m0, Cpre=Cpre)
                S = q * M / m0
            else:
                rj = c.det_ridge * self.rJ[0] + 1e-30
                if c.kd < 0:
                    idx = np.arange(self.tJ, stop)[:, None] - np.arange(M)[None, :]
                    Xs = np.where(idx >= 0, self.xf[np.clip(idx, 0, None)], 0.0)
                    Gr = Xs.T @ Xs
                    q = float(g @ np.linalg.solve(Gr + 1e-3 * np.trace(Gr) / M * np.eye(M), g))
                else:
                    q = float(g @ self._pcg(CJ, self.tJ, rj, g, np.zeros(M), c.kd))
                sig2 = max((self.e0 + 2.0 * float(self.w @ self.p) + float(self.w @ Gw)) / nwin, 1e-300)
                S = q / sig2
            self.scores.append(S / M)
            _forced = _ft is not None
            self.force_tau = None
            if w_ctrl is not None and not (S >= self.thr * M or _forced):
                self.w = w_ctrl                              # no detection: back to the regularized control filter
            if S >= self.thr * M or _forced:
                # forced (external detector): the location it supplies (localized there), clipped to [restart, start]
                tau = (int(min(max(_ft, self.restart), start)) if _forced else
                       (self._localize(start, stop) if c.localize else start))
                if c.localize:
                    self.locs.append(tau)
                if c.adapt == 'weight':
                    self._start_event(tau, start, stop)          # w_A = window LS solution (unregularized if score_unreg)
                    if w_ctrl is not None:
                        self.w = w_ctrl
                    self.resets.append(stop)
                    return self._finish_hop(None, None)
                if c.branch_hops > 0:
                    A = copy.copy(self)
                    for k in ('r', 'p', 'rJ', 'pJ', 'w'):
                        setattr(A, k, getattr(self, k).copy())
                    A.seg = dict(self.seg); A.pe = list(self.pe); A._ecache = dict(self._ecache)
                    A.fft = FFTCounter(); A.suppress_detect = True; A.branch = None; A._pending = None
                    A.resets, A.locs, A.scores, A.screen_hist, A.rollbacks = [], [], [], [], []
                    A._finish_hop(Cm, Gw)
                    self._pending = A
                self.restart = tau; self.resets.append(stop)
                # both windows restart at tau: statistics = those of [tau, stop)
                self.seg = {}
                sgn = self._segment_stats(tau, stop); self.seg[tau] = sgn
                _, dr, dp, de = sgn
                self.r, self.p, self.e0 = dr.copy(), dp.copy(), de
                self.rJ, self.pJ, self.e0J = dr.copy(), dp.copy(), de
                self.t0 = self.tJ = tau
                Cm = None; Gw = None
        return self._finish_hop(Cm, Gw)

    def force_restart(self, tau: int) -> None:
        """Restart the window at tau without a detection of its own (PcgWlsMultiWindow 'primary': a member with a longer memory
        than the detecting member forgets at the detector's events). Same statistics reset as a detection without
        event weighting; the current controller stays as the warm start."""
        stop = self.stop; tau = int(min(max(int(tau), 0), stop))
        self.restart = tau
        self.seg = {}
        if stop > tau:
            sgn = self._segment_stats(tau, stop); self.seg[tau] = sgn
            _, dr, dp, de = sgn
            self.r, self.p, self.e0 = dr.copy(), dp.copy(), de
            self.rJ, self.pJ, self.e0J = dr.copy(), dp.copy(), de
        else:
            M = self.cfg.M
            self.r = np.zeros(M); self.p = np.zeros(M); self.e0 = 0.0
            self.rJ = np.zeros(M); self.pJ = np.zeros(M); self.e0J = 0.0
        self.t0 = self.tJ = tau
        self.ev = None; self.w_ls = None

    def _stat_ok(self, n) -> bool:
        md = self.cfg.cg_stat_mindof
        if md is None:
            return True
        md = self.cfg.M if md == 'M' else int(md)
        return n - self.cfg.M >= md

    def _stat_stop(self, e0, p_, n):
        """Statistical stopping rule: stop when r^T z <= tol M J(x) / (n - M), J(x) = e0 + x.p - x.res (window LS
        cost without an extra operator product): optimization error <= tol x estimation error (Thm 1)."""
        c = self.cfg
        tol = float(c.cg_stat_tol if c.cg_stat_tol is not None else 0.1); Mn = c.M
        if not self._stat_ok(n):
            return None
        return lambda x, res, pen=0.0: tol * Mn * max(e0 + float(x @ p_) - float(x @ res) - pen, 0.0) / max(n - Mn, 1)

    def solve_now(self, iters: int) -> np.ndarray:
        """One warm-started PCG solve of the current window (used after a batch catch-up)."""
        c = self.cfg; nwin = self.stop - self.t0
        stop_rz = None
        if c.cg_stat_tol is not None and self._stat_ok(nwin):
            tol = float(c.cg_stat_tol); e0 = self.e0; p_ = self.p; Mn = c.M
            stop_rz = lambda x, res, pen=0.0: tol * Mn * max(e0 + float(x @ p_) - float(x @ res) - pen, 0.0) / max(nwin - Mn, 1)
        self.w = self._pcg(self._circ(self.r), self.t0, c.ridge * self.r[0] + 1e-30, -self.p, self.w, iters,
                           use_reg=True, stop_rz=stop_rz)
        return self.w

    def _finish_hop(self, Cm, Gw) -> np.ndarray:
        c = self.cfg; H = c.H; stop = self.stop
        self._prune()
        if self.skip_solve:
            return self.w
        # CG iteration schedule (transient-only iterations)
        nwin = stop - self.t0
        k_it = c.k
        if nwin > c.k_hops * H:
            k_it = c.k_steady
        if nwin <= c.k_first_hops * H:
            k_it = c.k_first
        ridge = c.ridge * self.r[0] + 1e-30
        if self.ev is not None:
            return self._weighted_solve(ridge)
        if c.cg_auto:
            if Cm is None:
                Cm = self._circ(self.r)
            self.w = self._pcg(Cm, self.t0, ridge, -self.p, self.w, c.cg_cap, Gx0=Gw, use_reg=True,
                               stop_rz=self._stat_stop(self.e0, self.p, nwin))
            return self.w
        if (c.steady_every > 1 and k_it == c.k_steady and nwin > c.k_hops * H and Cm is None
                and (stop // H) % c.steady_every):
            return self.w                                   # skipped hop (statistics already updated)
        if Cm is None:
            Cm = self._circ(self.r)
        if c.grow_len == 'risk' and nwin < 2 * c.M:
            return self._risk_len_solve(Cm, ridge, k_it, nwin)
        meff = max(nwin // 2, 1) if (c.grow_len == 'half' and nwin < 2 * c.M) else None
        if meff is not None:
            Gw = None                                       # Gw belongs to the full-length iterate
        stop_rz = None
        # review 2026-10-24: the statistical rule is written for M free taps; on the truncated problem (meff < M) the
        # fixed iteration count is used (with cg_stat_mindof = 'M' the two never overlap: both need n < 2M)
        if c.cg_stat_tol is not None and self._stat_ok(nwin) and meff is None:
            # J(x) = e0 + 2 x.p + x.G x and G x = b - res with b = -p  ->  J(x) = e0 + x.p - x.res (no extra operator)
            tol = float(c.cg_stat_tol); e0 = self.e0; p_ = self.p; Mn = c.M
            stop_rz = lambda x, res, pen=0.0: tol * Mn * max(e0 + float(x @ p_) - float(x @ res) - pen, 0.0) / max(nwin - Mn, 1)
        self.w = self._pcg(Cm, self.t0, ridge, -self.p, self.w, k_it, Gx0=Gw, use_reg=True,
                           richardson=(c.steady_solver == 'richardson' and k_it == c.k_steady and nwin > c.k_hops * H),
                           stop_rz=stop_rz, meff=meff)
        return self.w

    def _risk_len_solve(self, Cm, ridge, k_it, nwin):
        """grow_len = 'risk' (2026-10-24; Theorem B on a growing window, LENGTH_RULE_GROWING.md): while n < 2M the
        control length is the minimizer of the unbiased estimate of the prediction risk of the window LS controller,
            R_hat(m) = J_res(m) (n - 1) / ((n - m)(n - m - 1))
        (Gaussian random design: E[risk] = s_m^2 (1 + m / (n - m - 1)), E[J_res] = s_m^2 (n - m); Breiman & Freedman
        1983), i.e. the sample version of E_tr(m) + J_min m / (n - m - 1) of Theorem B with N_w = n. Candidates m in
        {n/4, n/2, 3n/4} and M once n > M + 1; each candidate keeps its own warm-started masked PCG iterate."""
        c = self.cfg; M, n2 = c.M, self.n2
        cands = {}                                          # key -> length (keys stable across hops: warm starts match)
        for f in (0.25, 0.5, 0.75):
            cands.setdefault(min(max(int(f * nwin), 1), M), f)
        if nwin > M + 1:
            cands[M] = 'M'
        cands = [(k, m) for m, k in sorted(cands.items()) if m < nwin - 1] or [(0.25, 1)]
        if not hasattr(self, '_risk_it') or nwin < getattr(self, '_risk_n', 0):
            self._risk_it = {}                              # new window (start-up / restart): fresh iterates
        self._risk_n = nwin
        best = None
        for key, m in cands:
            x0 = self._risk_it.get(key, self.w)
            x = self._pcg(Cm, self.t0, ridge, -self.p, x0, k_it, use_reg=True, meff=(None if m == M else m))
            self._risk_it[key] = x
            Gx = self.fft.irfft(self._apply(Cm, self.t0, self.fft.rfft(x, n2)), n2)[:M]
            Jr = max(self.e0 + 2.0 * float(x @ self.p) + float(x @ Gx), 1e-300)
            R = Jr * (nwin - 1) / ((nwin - m) * (nwin - m - 1))
            if best is None or R < best[0]:
                best = (R, m, x)
        self.risk_len_log = getattr(self, 'risk_len_log', [])
        self.risk_len_log.append((int(self.stop), int(nwin), int(best[1])))
        self.w = best[2]
        return self.w

    # ---------- Prop. 9: weighted pre-change data ----------
    def _start_event(self, tau, start, stop):
        c = self.cfg; M = c.M
        if self.ev is not None and self.ev['tau'] > self.t0:
            # a new event inside an event: data before the previous change point are dropped
            self._sub_range(self.t0, self.ev['tau'], 'main'); self.t0 = self.ev['tau']; self.restart = self.t0
        _lb = getattr(self, '_lastB', None)
        _, dr, dp, de = self._segment_stats(tau, stop)
        if c.fixes_1028 and _lb is not None:
            self._lastB = _lb
        nA = tau - self.t0
        # pre-change in-sample level: mean one-step residual before the event, minus its estimation excess
        past = [z[1] for z in self.pe if (z[0] + c.H <= tau if c.fixes_1028 else z[0] < start)]
        s1 = float(np.mean(past[-c.L_hops:])) if past else max(self.e0 / max(stop - self.t0, 1), 1e-300)
        sA2 = s1 / (1.0 + M / max(nA - M, 1))
        wA = self.w.copy()
        if c.fixes_1028 and nA > 0:
            # LS solution of A = [t0, tau): G_A = Circ(r_A) + Z(t0) - Z(tau) (+ Z(stop) cancels the default stop edge)
            rA = self.r - dr; pA = self.p - dp
            wA = self._pcg(self._circ(rA), [(1.0, self.t0), (-1.0, tau), (1.0, stop)], c.ridge * rA[0] + 1e-30, -pA,
                           self.w, max(c.k_first, 16), use_reg=False)
        self.ev = {'tau': tau, 'wA': wA, 'sA2': sA2, 'rB': dr.copy(), 'pB': dp.copy(), 'eB': de,
                   'wB': self.w.copy(), 'alpha': 0.0, 'nA0': nA, 'plug': False}
        self.noise_t0 = tau                               # noise statistics restart at the change point

    def _weighted_solve(self, ridge):
        """(alpha G_A + G_B) w = -(alpha p_A + p_B), A = [t0, tau), B = [tau, stop); alpha = 1/(1 + n_A D_hat/M)."""
        c = self.cfg; M, H, n2 = c.M, c.H, self.n2
        ev = self.ev; tau, stop = ev['tau'], self.stop
        nA, nB = tau - self.t0, stop - tau
        CB = self._circ(ev['rB'])
        GB = lambda u: self.fft.irfft(self._apply(CB, [(1.0, tau)], self.fft.rfft(u, n2)), n2)[:M]
        if nB <= M + H:
            # B alone cannot separate a plant change from a noise change: pre-change level (Prop. 9)
            wA = ev['wA']
            eBA = ev['eB'] + 2.0 * float(wA @ ev['pB']) + float(wA @ GB(wA))
            D = max(0.0, eBA / (nB * ev['sA2']) - 1.0 - M / max(ev.get('nA0', nA) if c.fixes_1028 else nA, 1))
        else:
            # plug-in with B's own noise level (robust to noise-level steps)
            if c.fixes_1028 and not ev.get('plug'):
                ev['wB'] = self.w.copy(); ev['plug'] = True          # first plug-in hop: warm start from the current w
            _fx = c.fixes_1028 and not c.cg_auto            # w_B to the statistical tolerance (D_hat needs w_B ~ LS of B)
            ev['wB'] = self._pcg(CB, [(1.0, tau)], c.ridge * ev['rB'][0] + 1e-30, -ev['pB'], ev['wB'],
                                 c.cg_cap if c.cg_auto else (max(c.k_B, 64) if _fx else c.k_B),
                                 stop_rz=self._stat_stop(ev['eB'], ev['pB'], nB) if (c.cg_auto or _fx) else None)
            wB = ev['wB']
            rss = max(ev['eB'] + 2.0 * float(wB @ ev['pB']) + float(wB @ GB(wB)), 1e-300)
            sB2 = rss / (nB - M)
            dw = wB - ev['wA']
            nAv = ev.get('nA0', nA) if c.fixes_1028 else nA
            D = max(0.0, float(dw @ GB(dw)) / (nB * sB2) - M * (1.0 / max(nAv, 1) + 1.0 / nB))
        if c.band == 'tree' and nB > M + H and nA > 0:
            return self._band_solve(ev, CB, sB2, nA, nB)
        alpha = 1.0 / (1.0 + nA * D / M) if nA > 0 else 0.0
        ev['alpha'] = alpha; self.alpha_hist.append((stop, alpha))
        Cw = alpha * self._circ(self.r) + (1.0 - alpha) * CB          # alpha C_A + C_B, C_A = C_main - C_B
        edges = [(alpha, self.t0), (1.0 - alpha, tau)]
        b = -(alpha * self.p + (1.0 - alpha) * ev['pB'])
        k_it = c.k_first if nB <= c.k_first_hops * H else (c.k if nB <= c.k_hops * H else max(c.k_steady, 2))
        rw = ridge * (alpha * (self.r[0] - ev['rB'][0]) + ev['rB'][0]) / max(self.r[0], 1e-300)
        if c.cg_auto:
            ew = alpha * (self.e0 - ev['eB']) + ev['eB']
            self.w = self._pcg(Cw, edges, rw + 1e-30, b, self.w, c.cg_cap, use_reg=True,
                               stop_rz=self._stat_stop(ew, -b, alpha * nA + nB))
            return self.w
        if c.weight_consistent:
            n_eff = alpha * nA + nB
            meff = max(int(n_eff) // 2, 1) if (c.grow_len == 'half' and n_eff < 2 * M) else None
            stop_rz = None
            if c.cg_stat_tol is not None and self._stat_ok(n_eff) and meff is None:
                ew = alpha * (self.e0 - ev['eB']) + ev['eB']
                stop_rz = self._stat_stop(ew, -b, n_eff)
            self.w = self._pcg(Cw, edges, rw + 1e-30, b, self.w, k_it, use_reg=True, stop_rz=stop_rz, meff=meff)
            return self.w
        self.w = self._pcg(Cw, edges, rw + 1e-30, b, self.w, k_it, use_reg=True)
        return self.w

    def _band_solve(self, ev, CB, sB2, nA, nB):
        """Band-wise data weights (Theorem 5 per band, K = 2 blocks): W = c_beta W_A + (1 - c_beta) W_B on each band of a
        penalized-SURE dyadic tree; c_beta = min(1, f_beta v_beta / D_beta) (positive-part James-Stein, f = (d-2)/d),
        D_beta = (1/2M) sum_k g_k Lambda_k |W_A,k - W_B,k|^2 / (n_B s_B^2), v_beta = d_beta / n_B (Prop. 9 units)."""
        c = self.cfg; M, n2 = c.M, self.n2
        WA = self.fft.rfft(ev['wA'], n2); WB = self.fft.rfft(ev['wB'], n2)
        g = np.full(M + 1, 2.0); g[0] = g[-1] = 1.0
        Dk = g * np.maximum(CB.real, 0.0) * np.abs(WA - WB) ** 2 / n2 / (nB * sB2)
        cs = np.concatenate([[0.0], np.cumsum(Dk)]); cg = np.concatenate([[0.0], np.cumsum(g)])
        pen = c.band_kappa * (2.0 + 2.0 * np.log(4.0)) / nB

        def leaf(a, b):
            d = M * (cg[b] - cg[a]) / n2; vb = d / nB; Db = cs[b] - cs[a]
            c1 = min(1.0, max(d - 2.0, 0.0) / d * vb / max(Db, 1e-300))
            return c1, c1 * c1 * Db + vb * (1.0 - 2.0 * c1)

        def best(a, b):
            c1, r = leaf(a, b); cost, part = r + pen, [(a, b, c1)]
            m = (a + b) // 2
            if a < m < b and M * (cg[m] - cg[a]) / n2 >= 3 and M * (cg[b] - cg[m]) / n2 >= 3:
                cl, pl = best(a, m); cr, pr = best(m, b)
                if cl + cr < cost:
                    cost, part = cl + cr, pl + pr
            return cost, part
        part = best(0, M + 1)[1]
        Wc = WB.copy()
        for a, b, c1 in part:
            Wc[a:b] = c1 * WA[a:b] + (1.0 - c1) * WB[a:b]
        self.w = self.fft.irfft(Wc, n2)[:M]
        ev['alpha'] = float(np.mean([c1 for *_, c1 in part])); ev['nbands'] = len(part)
        self.alpha_hist.append((self.stop, ev['alpha']))
        return self.w

    def _localize(self, start: int, stop: int) -> int:
        """ML variance change point of the residual of the current w on [start-H, stop)."""
        c = self.cfg; M, H = c.M, c.H
        a0 = max(0, start - H)
        if c.loc_wide:
            a0 = max(0, self.restart, self.t0, self.tJ - H); start = min(a0 + H, start)
        lo = max(0, a0 - M + 1)
        seg = np.concatenate([np.zeros(M - 1 - (a0 - lo)), self.xf[lo:stop]])
        nfft = int(2 ** np.ceil(np.log2(len(seg) + M)))
        yw = self.fft.irfft(self.fft.rfft(seg, nfft) * self.fft.rfft(self.w, nfft), nfft)[M - 1:M - 1 + stop - a0]
        e2 = (self.dh[a0:stop] + yw) ** 2
        cs = np.concatenate([[0.0], np.cumsum(e2)]); ntot = stop - a0
        best, tau = -np.inf, start
        for t in range(start, stop - 8, c.loc_step):
            n1, n2 = t - a0, stop - t
            s1 = max(cs[n1] / n1, 1e-300); s2 = max((cs[ntot] - cs[n1]) / n2, 1e-300)
            ll = -0.5 * (n1 * np.log(s1) + n2 * np.log(s2))
            if ll > best:
                best, tau = ll, t
        self.fft.direct_flops += 6.0 * (stop - a0)
        return tau
