"""Memory-length aggregation for E-PCG under continuous movement (new; does not change EPCG itself).

A bank of K E-PCG solvers that differ only in the window length L_hops (memory). Before each hop the controller
of every member is scored by its honest one-step predictive (virtual) residual on the new hop,
    l_i(b) = || d_hat_b + X_b w_i(b-1) ||^2   (w_i(b-1) uses data up to hop b-1 only),
and the applied controller is the posterior-weighted mixture
    w(b) = sum_i pi_i(b) w_i(b),   pi_i(b) ∝ exp(-eta * sum of past l_i) with a fixed-share (switching) prior.

Theory: with eta = 1/(2 sigma^2) the weights are the Bayesian
posterior over the K memories under a Gaussian one-step predictive likelihood, and fixed-share with rate a is the
Bayes mixture under a switching prior (hazard a per hop). The squared loss is exp-concave in w on bounded sets, so
the mixture's cumulative predictive loss is within (1/eta) [log K + (m+1) log(1/a) + T a] of the best sequence of
memories with m switches (Herbster and Warmuth 1998; Vovk 1990). The mixture is applied because the loss is convex
in w (no randomization needed).

Interface mirrors EPCG for the experiment wrapper: update(), resets / locs / scores / rollbacks (of the primary
member = longest window, i.e. the original detector), cfg (setting reg_eps / reg_gate applies to all members),
fft.flops() (sum over members + the scoring convolutions).
"""
from __future__ import annotations

import numpy as np

from .epcg import EPCG, EPCGConfig, FFTCounter, CMUL


class _SumCounter:
    def __init__(self, bank):
        self.bank = bank

    def flops(self) -> float:
        return self.bank.own.flops() + sum(m.fft.flops() for m in self.bank.members)


class _CfgProxy:
    """Reads from the primary member; writes reg_eps / reg_gate to every member."""

    def __init__(self, bank):
        object.__setattr__(self, 'bank', bank)

    def __getattr__(self, k):
        return getattr(self.bank.members[self.bank.ip].cfg, k)

    def __setattr__(self, k, v):
        for m in self.bank.members:
            setattr(m.cfg, k, v)


class _FDExpert:
    """Cheap short-memory member: FD-FxNLMS on the virtual residual d_hat + X w (bin-wise normalization, N = 2M frame),
    with the same robust ridge as the E-PCG members applied as a proximal per-bin leakage
    W <- (W - mu G) / (1 + mu max(0, eps_k/gamma - 1)) whenever the ridge is active (fixed point (gamma/eps_k) W_opt,
    as in Prop. 10). Memory ~ 1/mu blocks."""

    def __init__(self, base: EPCGConfig, mu: float = 1.0, smoothing: float = 0.8, reg_ratio: float = 1e-3):
        from types import SimpleNamespace
        self.M = base.M; self.N = 2 * base.M; self.mu = float(mu)
        self.cfg = SimpleNamespace(reg_eps=base.reg_eps, reg_gate=base.reg_gate, reg_gamma=base.reg_gamma)
        self.w = np.zeros(self.M); self.hist = np.zeros(self.N); self.pw = None
        self.sm = float(smoothing); self.rr = float(reg_ratio)
        self.fft = FFTCounter(); self.resets: list = []; self.locs: list = []; self.scores: list = []; self.rollbacks: list = []

    def update(self, xf_hop, dhat_hop):
        M, N, n = self.M, self.N, len(xf_hop)
        Wf = self.fft.rfft(self.w, N)
        self.hist = np.concatenate([self.hist, xf_hop])[-N:]
        X = self.fft.rfft(self.hist, N)
        y = self.fft.irfft(X * Wf, N)[N - n:]                   # (circular part discarded: N >= M + n - 1)
        r = dhat_hop + y
        P = np.abs(X) ** 2
        self.pw = P if self.pw is None else self.sm * self.pw + (1 - self.sm) * P
        den = self.pw + self.rr * float(np.mean(self.pw)) + 1e-30
        E = self.fft.rfft(np.concatenate([np.zeros(N - n), r]), N)
        g = self.fft.irfft(np.conj(X) * E / den, N)[:M]
        wn = self.w - self.mu * g
        self.fft.direct_flops += 4 * CMUL * (N // 2 + 1) + 4.0 * n
        eps = self.cfg.reg_eps
        if eps is not None and self.cfg.reg_gate == 'always':
            leak = np.maximum(0.0, np.asarray(eps) / float(self.cfg.reg_gamma) - 1.0)
            wn = self.fft.irfft(self.fft.rfft(wn, N) / (1.0 + self.mu * leak), N)[:M]
        self.w = wn
        return self.w


class EPCGBank:
    def __init__(self, base: EPCGConfig, L_list=(8, 16, 32), eta_scale: float = 1.0, share: float = 0.02,
                 sigma_mem: float = 0.98, cheap: bool = False, primary=None, long_sched=None):
        """cheap=True (cost reduction, TODO 2): (i) segment statistics computed once and shared by all members,
        (ii) change detection only in the primary (longest) member, the shorter members forget by their window,
        (iii) steady-state threshold k_hops scaled with the window (k_hops * L_i / L_max), so short members also
        reach the 1-iteration warm-started steady state."""
        import dataclasses
        # a member 'fd' (or 'fd:<mu>') is the cheap FD-FxNLMS expert instead of an E-PCG window
        self.kind = ['fd' if str(L).startswith('fd') else 'epcg' for L in L_list]
        fdmu = [float(str(L).split(':')[1]) if str(L).startswith('fd:') else 1.0 for L in L_list]
        L_list = [0 if k == 'fd' else int(L) for k, L in zip(self.kind, L_list)]
        self.L = [int(L) for L in L_list]
        self.ip = int(np.argmax(self.L)); Lm = max(self.L)
        # primary (2026-10-24, v6.1; None = original: the longest member detects): window length (hops) of the
        # detecting member. Members with a LONGER window keep the memory between events (Theorem B: per-tap
        # misadjustment J_min / N_w) and forget at the primary's events (force_restart at the event location), so the
        # detector's window and the memory length are decoupled.
        if primary is not None:
            self.ip = self.L.index(int(primary))
        self.long = [i for i in range(len(self.L)) if self.L[i] > self.L[self.ip]]
        # cheap: True (all three) or a subset of {'share', 'nodetect', 'khops'} (ablation of the cost reductions)
        opts = {'share', 'nodetect', 'khops'} if cheap is True else (set(cheap) if cheap else set())
        self.cheap = opts
        cf = lambda L, i: dataclasses.replace(
            base, L_hops=L,
            detect=(base.detect and (i == self.ip or 'nodetect' not in opts)),
            k_hops=(max(1, int(round(base.k_hops * L / Lm))) if ({'khops', 'khops2'} & opts) else base.k_hops),
            # members with a longer memory than the primary keep the primary's iteration schedule (they are not short)
            # 'khops2': scaled threshold but the shorter members iterate every hop with 2 iterations (a short window
            # moves by a large fraction per hop; 1 iteration every 4th hop lags under drift)
            **({'steady_every': 1, 'k_steady': 2} if ('khops2' in opts and L != Lm) else {}),
            # long_sched = (every, k) (2026-10-24, cost): members with a longer window than the primary iterate only every
            # `every` hops with k iterations in the steady state: their LS solution moves by ~ H / n per hop, so the
            # warm-started iterate needs a reduction of only sqrt(every H / n) per update (Prop. PCG)
            **({'steady_every': int(long_sched[0]), 'k_steady': int(long_sched[1])}
               if (long_sched and self.ip is not None and L > self.L[self.ip]) else {}))
        self.members = [EPCG(cf(L, i)) if k == 'epcg' else _FDExpert(base, fdmu[i])
                        for i, (L, k) in enumerate(zip(self.L, self.kind))]
        self._cache: dict = {}
        if 'share' in opts:
            for i, m in enumerate(self.members):
                if self.kind[i] == 'epcg':
                    self._share_stats(m, primary=(i == self.ip))
        self.K = len(self.members)
        self.logw = np.full(self.K, -np.log(self.K))
        self.eta_scale = float(eta_scale); self.share = float(share); self.sigma_mem = float(sigma_mem)
        self.sig2 = None
        self.ws = [np.zeros(base.M) for _ in self.members]
        self.xf_tail = np.zeros(max(base.M - 1, 0))
        self.own = FFTCounter()
        self.fft = _SumCounter(self)
        self.cfg = _CfgProxy(self)
        self.pi_hist: list = []
        self.M = base.M
        # 'doze' (cost, 2026-10-20): a secondary member whose posterior weight stays below doze_pi for L_i hops stops
        # solving (statistics are still updated, shared); its controller is tied to the primary's, which it would
        # approximately equal while nothing drifts. It wakes up when the primary's stage-1 screen rejects 'no
        # change' (one-step residual too large at level screen_fa), at a detected event, and for one probe solve
        # every L_i hops; on wake-up it warm-starts from the primary's controller.
        self.doze_pi = 0.05; self.dozing = [False] * self.K; self.low = [0] * self.K; self.since = [0] * self.K
        self.doze_hist: list = []

    def _share_stats(self, m, primary):
        orig = m._segment_stats
        cache = self._cache

        def seg(s0, s1):
            key = (s0, s1)
            if key in cache:
                B, sg = cache[key]
                m._lastB = B
                return (sg[0], sg[1].copy(), sg[2].copy(), sg[3])
            sg = orig(s0, s1)
            cache[key] = (m._lastB, sg)
            return sg
        m._segment_stats = seg

    def force_event(self, tau: int) -> None:
        """(2026-10-24) declare an event at tau in the primary member at its next update (external detector)."""
        self.members[self.ip].force_tau = int(tau)

    # primary member's event bookkeeping (original detector)
    resets = property(lambda s: s.members[s.ip].resets)
    locs = property(lambda s: s.members[s.ip].locs)
    scores = property(lambda s: s.members[s.ip].scores)
    rollbacks = property(lambda s: s.members[s.ip].rollbacks)

    def _losses(self, xf_hop, dhat_hop):
        M = self.M; n = len(xf_hop)
        seg = np.concatenate([self.xf_tail, xf_hop])
        # 'fftmin' in cheap: the smallest exact length (outputs M-1 .. len(seg)-1 are wrap-free iff nf >= len(seg))
        nf = int(2 ** np.ceil(np.log2(len(seg) if 'fftmin' in self.cheap else len(seg) + M)))
        Xs = self.own.rfft(seg, nf)
        out = []
        for w in self.ws:
            y = self.own.irfft(Xs * self.own.rfft(w, nf), nf)[M - 1:M - 1 + n]
            self.own.direct_flops += CMUL * (nf // 2 + 1) + 3.0 * n
            r = dhat_hop + y
            out.append(float(r @ r))
        self.xf_tail = seg[-(M - 1):] if M > 1 else np.zeros(0)
        return np.array(out)

    def catch_up(self, xf, dh, H, iters):
        """Batch rebuild (sid): feed the hops with statistics only (no solves, no detection), then one solve per
        member; memory weights restart uniform (the skipped solves give no honest one-step losses)."""
        for m in self.members:
            if hasattr(m, 'skip_solve'):
                m.skip_solve = True; m.suppress_detect = True
                m.force_tau = None                          # review 2026-10-25: no stale external event across a replay
        for h in range(0, len(xf), H):
            self.update(xf[h:h + H], dh[h:h + H])
        for i, m in enumerate(self.members):
            if hasattr(m, 'skip_solve'):
                m.skip_solve = False; m.suppress_detect = False; m.pe = []
                self.ws[i] = m.solve_now(iters).copy()
        self.logw = np.full(self.K, -np.log(self.K))
        return sum(w / self.K for w in self.ws)

    def _update_shared(self, xf_hop, dhat_hop):
        """'sharescore': the primary's own stage-1 screen already computes its one-step predictive residual on the new
        hop and the FFT of the hop's x_f segment; the bank reuses both (exact) and only filters the short members' w."""
        n = len(xf_hop); M = self.M; P_ = self.members[self.ip]
        start = P_.stop
        self._cache.clear()                                   # the primary fills the shared statistics first
        self.ws[self.ip] = np.asarray(P_.update(xf_hop, dhat_hop), float).copy()
        lp = getattr(P_, 'last_pred', None)
        if lp is None or lp[0] != start:
            return None                                       # screen did not run: caller falls back
        _, e_ip, B, nb = lp
        loss = np.empty(self.K); loss[self.ip] = e_ip
        for i in range(self.K):
            if i == self.ip:
                continue
            y = self.own.irfft(B * self.own.rfft(self.ws_prev[i], nb), nb)[M - 1:M - 1 + n]
            self.own.direct_flops += CMUL * (nb // 2 + 1) + 3.0 * n
            r = dhat_hop + y; loss[i] = float(r @ r)
        self.xf_tail = np.concatenate([self.xf_tail, xf_hop])[-(M - 1):] if M > 1 else np.zeros(0)
        return loss

    def _doze_step(self, i, p):
        P_ = self.members[self.ip]; m = self.members[i]; Li = self.L[i]
        ls = getattr(P_, 'last_screen', None)
        alarm = ls is not None and ls[0] >= P_.stop - P_.cfg.H and ls[1] > ls[2]     # screen of the current hop
        alarm = alarm or (len(P_.resets) > 0 and P_.resets[-1] == P_.stop)
        if not hasattr(self, 'sleep'):
            self.sleep = [L for L in self.L]
        if self.dozing[i]:
            self.since[i] += 1
            if alarm:                                         # wake up: full re-entry condition
                self.dozing[i] = False; self.low[i] = 0; self.sleep[i] = Li
                m.w = self.ws[self.ip].copy(); m.skip_solve = False
            elif self.since[i] >= self.sleep[i]:              # probe: one honest solve; re-doze after one low hop,
                self.dozing[i] = False; self.low[i] = Li - 1  # sleep interval doubled up to the primary's window
                self.sleep[i] = min(2 * self.sleep[i], max(self.L))
                m.w = self.ws[self.ip].copy(); m.skip_solve = False
        else:
            # no benefit from the short memory: the log Bayes factor of member i against the primary over its last
            # L_i hops, eta * sum(l_primary - l_i), is below log 3 (Jeffreys: 'not worth more than a bare mention')
            ev = self.bf_hist[i][-Li:] if hasattr(self, 'bf_hist') else []
            no_benefit = len(ev) >= Li and float(np.sum(ev)) < np.log(3.0)
            self.low[i] = self.low[i] + 1 if (p[i] < self.doze_pi or no_benefit) else 0
            if self.low[i] < Li - 1:
                self.sleep[i] = Li                            # weight came back: reset the back-off
            if self.low[i] >= Li and not alarm:
                self.dozing[i] = True; self.since[i] = 0; m.skip_solve = True
        self.doze_hist.append((P_.stop, i, int(self.dozing[i])))

    def update(self, xf_hop: np.ndarray, dhat_hop: np.ndarray) -> np.ndarray:
        n = len(xf_hop)
        if 'sharescore' in self.cheap and self.kind[self.ip] == 'epcg':
            self.ws_prev = [w.copy() for w in self.ws]
            loss = self._update_shared(xf_hop, dhat_hop)
            if loss is None:                                  # screen did not run: score from the stored controllers
                ws_now = self.ws; self.ws = self.ws_prev
                loss = self._losses(xf_hop, dhat_hop); self.ws = ws_now
            return self._finish(loss, xf_hop, dhat_hop, skip_primary=True)
        loss = self._losses(xf_hop, dhat_hop)
        return self._finish(loss, xf_hop, dhat_hop)

    def _finish(self, loss, xf_hop, dhat_hop, skip_primary=False):
        n = len(xf_hop)
        # noise level: exponentially weighted per-sample loss of the best member (scale of the likelihood)
        s_now = float(np.min(loss)) / max(n, 1)
        self.sig2 = s_now if self.sig2 is None else self.sigma_mem * self.sig2 + (1 - self.sigma_mem) * s_now
        eta = self.eta_scale / (2.0 * max(self.sig2, 1e-300))
        if not hasattr(self, 'bf_hist'):
            self.bf_hist = [[] for _ in range(self.K)]
        for i in range(self.K):
            self.bf_hist[i] = (self.bf_hist[i] + [eta * float(loss[self.ip] - loss[i])])[-max(self.L):]
        lw = self.logw - eta * (loss - np.min(loss))
        lw -= np.max(lw); p = np.exp(lw); p /= p.sum()
        # fixed share (switching prior)
        p = (1.0 - self.share) * p + self.share / self.K
        self.logw = np.log(p)
        self.own.direct_flops += 10.0 * self.K
        # update the members (primary first: with cheap=True it fills the shared statistics cache)
        if not skip_primary:
            self._cache.clear()
        for i in [self.ip] + [j for j in range(self.K) if j != self.ip]:
            if skip_primary and i == self.ip:
                continue
            if self.long and i in self.long and self.kind[i] == 'epcg':
                P_ = self.members[self.ip]
                if len(P_.resets) > getattr(self, '_seen_ev', 0) and P_.resets and P_.resets[-1] == P_.stop:
                    # the primary detected an event in this hop: the long memory forgets up to the event location
                    self.members[i].force_restart(P_.locs[-1] if P_.locs else P_.restart)
            if i != self.ip and 'doze' in self.cheap and self.kind[i] == 'epcg' and i not in self.long:
                # (v6.1) the long-memory members do not doze: their benefit (lower misadjustment) is small per hop but
                # persistent, so the per-hop Bayes-factor rule of the doze would tie them to the primary
                self._doze_step(i, p)
            self.ws[i] = np.asarray(self.members[i].update(xf_hop, dhat_hop), float).copy()
            if i != self.ip and self.dozing[i]:
                self.ws[i] = self.ws[self.ip].copy()          # tied to the primary while dozing
        self._seen_ev = len(self.members[self.ip].resets)
        # gate: once the primary detector has seen an event, every member uses the ridge
        if self.members[self.ip].resets:
            for m in self.members:
                if m.cfg.reg_gate == 'after_event':
                    m.cfg.reg_gate = 'always'
        self.pi_hist.append(p.copy())
        return sum(pi * w for pi, w in zip(p, self.ws))
