from __future__ import annotations

import math
import numpy as np

try:
    from numba import njit
except ImportError:  # pragma: no cover
    njit = None


def nlms_regularization(
    filtered_references: list[np.ndarray],
    controller_length: int,
    regularization_ratio: float,
) -> tuple[float, float]:
    """Fixed NLMS regularization constants from *design/training* signals only.

    Returns ``(delta, bin_floor)`` with

        delta     = ratio * M * mean(x_f^2)   (time-domain NLMS: delta + ||x_f||^2)
        bin_floor = ratio * mean(x_f^2)       (per DCT bin; orthonormal DCT keeps energy)

    This matches the fixed bin-wise FD-FxNLMS relative loading
    ``ratio * mean bin power``.  Held-out signals must not be passed here.
    """
    if controller_length <= 0 or regularization_ratio < 0.0:
        raise ValueError("invalid regularization arguments")
    if len(filtered_references) == 0:
        raise ValueError("need at least one design signal")
    power = float(np.mean([np.mean(np.asarray(xf, dtype=float) ** 2) for xf in filtered_references]))
    if not np.isfinite(power) or power <= 0.0:
        raise ValueError("design filtered-reference power must be positive")
    return float(regularization_ratio * controller_length * power), float(regularization_ratio * power)


def initialize_sss_diagonal(n_candidates: int, controller_length: int, rho: float) -> np.ndarray:
    """Initialize the diagonal MSD states used by SSS-FxNLMS.

    Each candidate starts from the same scalar MSD J_k(0)=rho, so every row
    satisfies ``sum_m P[k,m] = rho``.
    """
    if n_candidates <= 0 or controller_length <= 0 or rho <= 0.0:
        raise ValueError("n_candidates, controller_length and rho must be positive")
    return np.full((n_candidates, controller_length), rho / controller_length, dtype=float)


def sss_msd_diagonal_step(
    p_diag: np.ndarray,
    r_diag: np.ndarray,
    mu: float,
    sigma_e2: float,
    normalization_power: float,
) -> np.ndarray:
    """One Eq.-(25)-style diagonal MSD prediction step for SSS-FxNLMS.

    Parameters are expressed for the non-robust Gaussian-noise SSS-FxNLMS case.
    ``r_diag`` is the instantaneous diagonal approximation of the filtered-input
    covariance, i.e. the elementwise squared filtered-reference vector.
    """
    p_diag = np.asarray(p_diag, dtype=float)
    r_diag = np.asarray(r_diag, dtype=float)
    if p_diag.shape != r_diag.shape or p_diag.ndim != 1:
        raise ValueError("p_diag and r_diag must be equal-length vectors")
    if mu < 0.0 or sigma_e2 < 0.0 or normalization_power <= 0.0:
        raise ValueError("invalid SSS MSD parameters")

    p = float(normalization_power)
    p2 = p * p
    rp_sum = float(np.dot(r_diag, p_diag))
    mu2 = float(mu * mu)
    out = (
        (1.0 - 2.0 * mu * r_diag / p) * p_diag
        + mu2 * sigma_e2 * r_diag / p2
        + 2.0 * mu2 * r_diag * p_diag * r_diag / p2
        + mu2 * r_diag * rp_sum / p2
    )
    # Only suppress tiny negative values caused by floating-point roundoff.
    out = np.where((out < 0.0) & (out > -1e-12), 0.0, out)
    return out


def adaptive_decorrelation_step(
    xf_current: float,
    error_current: float,
    xf_past: np.ndarray,
    error_past: np.ndarray,
    q: np.ndarray,
    ad_mu: float,
    eps: float = 1e-12,
) -> tuple[float, float, np.ndarray]:
    """One adaptive-decorrelation step shared by AD-VSS2 and AD-SSS.

    The same linear predictor is applied to the filtered reference and error,
    while its coefficients are adapted from the filtered-reference prediction
    error.  This mirrors the AD preprocessing used for colored-input comparisons
    in the SSS-FxNLMS literature.
    """
    xf_past = np.asarray(xf_past, dtype=float)
    error_past = np.asarray(error_past, dtype=float)
    q = np.asarray(q, dtype=float)
    if xf_past.shape != error_past.shape or xf_past.shape != q.shape:
        raise ValueError("xf_past, error_past and q must have the same shape")
    if ad_mu < 0.0:
        raise ValueError("ad_mu must be nonnegative")

    pred_x = float(np.dot(q, xf_past))
    pred_e = float(np.dot(q, error_past))
    xf_dec = float(xf_current - pred_x)
    e_dec = float(error_current - pred_e)
    denom = float(np.dot(xf_past, xf_past) + eps)
    q_new = q.copy()
    if q.size:
        q_new += (ad_mu * xf_dec / denom) * xf_past
    return xf_dec, e_dec, q_new


def dct_sss_msd_step(
    J: float,
    mu: float,
    q_correlation: float,
    transformed_filtered_reference: np.ndarray,
    normalization_diag: np.ndarray,
    sigma_e2: float,
) -> float:
    """Practical non-robust SSS-DCT-FxNLMS MSD-trend update.

    Implements the instantaneous form of Li et al. (2026), Eq. (35), obtained
    from Appendix Eq. (A.7)-(A.8) with g[e]=1 for Gaussian noise:

        J+ = J - (2 mu / q) * Tr(Lambda^-1 xhat xhat^T) * J
                 + mu^2 sigma_e^2 ||xhat^T Lambda^-1||_2^2.
    """
    xh = np.asarray(transformed_filtered_reference, dtype=float)
    lam = np.asarray(normalization_diag, dtype=float)
    if xh.shape != lam.shape or xh.ndim != 1:
        raise ValueError("transformed_filtered_reference and normalization_diag must match")
    if J < 0.0 or mu < 0.0 or q_correlation < 1.0 or sigma_e2 < 0.0:
        raise ValueError("invalid DCT-SSS MSD parameters")
    if np.any(lam <= 0.0):
        raise ValueError("normalization_diag must be positive")
    inv = 1.0 / lam
    a = float(np.dot(xh * xh, inv))
    b = float(np.dot(xh * xh, inv * inv))
    return float(J - (2.0 * mu / q_correlation) * a * J + (mu * mu) * sigma_e2 * b)


def _run_sss_python(
    x: np.ndarray,
    d: np.ndarray,
    xf: np.ndarray,
    v: np.ndarray,
    s: np.ndarray,
    mus: np.ndarray,
    lam: float,
    rho: float,
    controller_length: int,
    delta: float,
    hop_length: int,
    max_residual_ratio_db: float,
    max_weight_norm_limit: float,
    max_abs_error: float,
    ad_order: int,
    ad_mu: float,
) -> tuple:
    """Sample-wise SSS-FxNLMS / AD-SSS-FxNLMS simulator.

    The diagonal MSD recursion follows Li et al. (IEEE Access, 2026), Eq. (25).
    Repository sign convention is e=d+S*y+v, so descent uses a minus sign.
    """
    n_samples = x.size
    M = int(controller_length)
    Ls = s.size
    K = mus.size
    eps = 1e-12

    w = np.zeros(M, dtype=np.float64)
    y = np.zeros(n_samples, dtype=np.float64)
    error = np.zeros(n_samples, dtype=np.float64)
    mu_hist = np.zeros(n_samples, dtype=np.float64)
    P = np.full((K, M), rho / M, dtype=np.float64)
    sigma_e2 = 0.0

    q = np.zeros(max(ad_order, 1), dtype=np.float64)
    xf_dec = np.zeros(n_samples, dtype=np.float64)

    max_wnorm = 0.0
    max_mu = 0.0

    for n in range(n_samples):
        m = min(M, n + 1)
        yn = 0.0
        for j in range(m):
            yn += w[j] * x[n - j]
        y[n] = yn

        ls = min(Ls, n + 1)
        ys = 0.0
        for j in range(ls):
            ys += s[j] * y[n - j]
        e = d[n] + ys + v[n]
        error[n] = e

        if (not math.isfinite(e)) or abs(e) > max_abs_error:
            return False, error, mu_hist, max_mu, max_wnorm, n, 1

        if ad_order > 0:
            Kd = min(ad_order, n)
            pred_x = 0.0
            pred_e = 0.0
            denom_q = eps
            for j in range(Kd):
                xv = xf[n - 1 - j]
                ev = error[n - 1 - j]
                pred_x += q[j] * xv
                pred_e += q[j] * ev
                denom_q += xv * xv
            xf_n_dec = xf[n] - pred_x
            e_up = e - pred_e
            if Kd > 0:
                scale_q = ad_mu * xf_n_dec / denom_q
                for j in range(Kd):
                    q[j] += scale_q * xf[n - 1 - j]
        else:
            xf_n_dec = xf[n]
            e_up = e
        xf_dec[n] = xf_n_dec

        mf = min(M, n + 1)
        p = 0.0
        for j in range(mf):
            z = xf_dec[n - j]
            p += z * z
        # Regularized NLMS denominator delta + ||x_f||^2.  The same value is
        # used in the update and in the MSD recursion.  With delta=0 a
        # near-zero first filtered-reference sample (e.g. xf[3]=-1e-5 for
        # held-out seed 117) makes the cold-start update explode; see
        # results/conventional_limit_benchmark/NOTES.md.
        p_safe = max(p + delta, eps)
        denom = p_safe

        sigma_e2 = lam * sigma_e2 + (1.0 - lam) * (e_up * e_up)

        best_k = 0
        best_J = 1e300
        for k in range(K):
            mu = mus[k]
            mu2 = mu * mu
            rp_sum = 0.0
            for j in range(mf):
                rj = xf_dec[n - j] * xf_dec[n - j]
                rp_sum += rj * P[k, j]

            J = 0.0
            p2 = p_safe * p_safe
            for j in range(M):
                if j < mf:
                    rj = xf_dec[n - j] * xf_dec[n - j]
                else:
                    rj = 0.0
                old = P[k, j]
                val = (1.0 - 2.0 * mu * rj / p_safe) * old
                val += mu2 * sigma_e2 * rj / p2
                val += 2.0 * mu2 * rj * old * rj / p2
                val += mu2 * rj * rp_sum / p2
                if val < 0.0 and val > -1e-12:
                    val = 0.0
                P[k, j] = val
                J += val
            if math.isfinite(J) and J < best_J:
                best_J = J
                best_k = k

        mu_sel = mus[best_k]
        mu_hist[n] = mu_sel
        if mu_sel > max_mu:
            max_mu = mu_sel

        scale = mu_sel * e_up / denom
        for j in range(mf):
            w[j] -= scale * xf_dec[n - j]

        wnorm2 = 0.0
        for j in range(M):
            wnorm2 += w[j] * w[j]
        wnorm = math.sqrt(wnorm2)
        if wnorm > max_wnorm:
            max_wnorm = wnorm
        if (not math.isfinite(wnorm)) or wnorm > max_weight_norm_limit:
            return False, error, mu_hist, max_mu, max_wnorm, n, 2

        if (n + 1) % hop_length == 0:
            i0 = n + 1 - hop_length
            num = 0.0
            den = 0.0
            for t in range(i0, n + 1):
                num += error[t] * error[t]
                u = d[t] + v[t]
                den += u * u
            ratio_db = 10.0 * math.log10((num + 1e-30) / (den + 1e-30))
            if (not math.isfinite(ratio_db)) or ratio_db > max_residual_ratio_db:
                return False, error, mu_hist, max_mu, max_wnorm, n, 3

    return True, error, mu_hist, max_mu, max_wnorm, -1, 0


def _vss2_mu_scalar(e_abs: float, beta: float, gamma: float) -> float:
    """Numba-compatible beta*atan(|e|**gamma), evaluated safely."""
    if e_abs <= 0.0:
        return 0.0
    z = gamma * math.log(e_abs)
    if z >= 36.0:
        return beta * (math.pi / 2.0)
    if z <= -745.0:
        return 0.0
    return beta * math.atan(math.exp(z))


def _run_vss2_python(
    x: np.ndarray,
    d: np.ndarray,
    xf: np.ndarray,
    v: np.ndarray,
    s: np.ndarray,
    beta: float,
    gamma: float,
    controller_length: int,
    delta: float,
    hop_length: int,
    max_residual_ratio_db: float,
    max_weight_norm_limit: float,
    max_abs_error: float,
    ad_order: int,
    ad_mu: float,
) -> tuple:
    """VSS2-FxNLMS / AD-VSS2-FxNLMS with early instability detection."""
    n_samples = x.size
    M = int(controller_length)
    Ls = s.size
    eps = 1e-12
    w = np.zeros(M, dtype=np.float64)
    y = np.zeros(n_samples, dtype=np.float64)
    error = np.zeros(n_samples, dtype=np.float64)
    mu_hist = np.zeros(n_samples, dtype=np.float64)
    q = np.zeros(max(ad_order, 1), dtype=np.float64)
    xf_dec = np.zeros(n_samples, dtype=np.float64)
    max_mu = 0.0
    max_wnorm = 0.0

    for n in range(n_samples):
        m = min(M, n + 1)
        yn = 0.0
        for j in range(m):
            yn += w[j] * x[n - j]
        y[n] = yn

        ls = min(Ls, n + 1)
        ys = 0.0
        for j in range(ls):
            ys += s[j] * y[n - j]
        e = d[n] + ys + v[n]
        error[n] = e
        if (not math.isfinite(e)) or abs(e) > max_abs_error:
            return False, error, mu_hist, max_mu, max_wnorm, n, 1

        if ad_order > 0:
            Kd = min(ad_order, n)
            pred_x = 0.0
            pred_e = 0.0
            denom_q = eps
            for j in range(Kd):
                xv = xf[n - 1 - j]
                ev = error[n - 1 - j]
                pred_x += q[j] * xv
                pred_e += q[j] * ev
                denom_q += xv * xv
            xf_n_dec = xf[n] - pred_x
            e_up = e - pred_e
            if Kd > 0:
                scale_q = ad_mu * xf_n_dec / denom_q
                for j in range(Kd):
                    q[j] += scale_q * xf[n - 1 - j]
        else:
            xf_n_dec = xf[n]
            e_up = e
        xf_dec[n] = xf_n_dec

        mf = min(M, n + 1)
        p = 0.0
        for j in range(mf):
            z = xf_dec[n - j]
            p += z * z
        # Regularized NLMS denominator delta + ||x_f||^2 (see SSS kernel).
        p_safe = max(p + delta, eps)
        denom = p_safe
        e_abs = abs(e_up)
        if e_abs <= 0.0:
            mu = 0.0
        else:
            zmu = gamma * math.log(e_abs)
            if zmu >= 36.0:
                mu = beta * (math.pi / 2.0)
            elif zmu <= -745.0:
                mu = 0.0
            else:
                mu = beta * math.atan(math.exp(zmu))
        mu_hist[n] = mu
        if mu > max_mu:
            max_mu = mu

        scale = mu * e_up / denom
        for j in range(mf):
            w[j] -= scale * xf_dec[n - j]

        wnorm2 = 0.0
        for j in range(M):
            wnorm2 += w[j] * w[j]
        wnorm = math.sqrt(wnorm2)
        if wnorm > max_wnorm:
            max_wnorm = wnorm
        if (not math.isfinite(wnorm)) or wnorm > max_weight_norm_limit:
            return False, error, mu_hist, max_mu, max_wnorm, n, 2

        if (n + 1) % hop_length == 0:
            i0 = n + 1 - hop_length
            num = 0.0
            den = 0.0
            for t in range(i0, n + 1):
                num += error[t] * error[t]
                u = d[t] + v[t]
                den += u * u
            ratio_db = 10.0 * math.log10((num + 1e-30) / (den + 1e-30))
            if (not math.isfinite(ratio_db)) or ratio_db > max_residual_ratio_db:
                return False, error, mu_hist, max_mu, max_wnorm, n, 3

    return True, error, mu_hist, max_mu, max_wnorm, -1, 0


# True when the sample-wise kernels below are Numba-compiled.  Expensive
# runners must check this (see ffanc_norm.runtime.ensure_compiled_kernels):
# the pure-Python fallback is correct but 100-300x slower.
KERNELS_COMPILED = njit is not None

if njit is not None:
    run_sss_kernel = njit(cache=True)(_run_sss_python)
    run_vss2_kernel = njit(cache=True)(_run_vss2_python)
else:  # pragma: no cover
    run_sss_kernel = _run_sss_python
    run_vss2_kernel = _run_vss2_python


def run_dct_sss(
    x: np.ndarray,
    d: np.ndarray,
    xf: np.ndarray,
    v: np.ndarray,
    s: np.ndarray,
    mus: np.ndarray,
    power_lambda: float,
    q_correlation: float,
    kappa: float,
    rho: float,
    controller_length: int,
    regularization_ratio: float,
    hop_length: int,
    max_residual_ratio_db: float = 30.0,
    max_weight_norm_limit: float = 1e3,
    max_abs_error: float = 1e6,
    normalization_floor: float = 0.0,
) -> tuple:
    """Reference SSS-DCT-FxNLMS implementation for Gaussian noise.

    ``normalization_floor`` is a fixed per-transform-bin loading added to the
    power diagonal (the transform-domain analogue of NLMS delta).  The
    relative loading ``regularization_ratio * mean(power)`` alone is not enough
    at cold start, because the running power estimate itself is near zero.

    It uses an orthonormal DCT-II, exponentially smoothed per-transform power
    estimates (Lambda), and the practical MSD-trend recursion of Li et al.
    (Circuits, Systems, and Signal Processing, 2026), Eq. (35)/Appendix A.

    This is intentionally a transparent reference implementation; it is not yet
    optimized for very large Optuna sweeps.
    """
    try:
        from scipy.fft import dct
    except ImportError as exc:  # pragma: no cover
        raise ImportError("run_dct_sss requires scipy") from exc

    x = np.asarray(x, dtype=float)
    d = np.asarray(d, dtype=float)
    xf = np.asarray(xf, dtype=float)
    v = np.asarray(v, dtype=float)
    s = np.asarray(s, dtype=float)
    mus = np.asarray(mus, dtype=float)
    if not (x.shape == d.shape == xf.shape == v.shape):
        raise ValueError("x, d, xf and v must have identical shapes")
    if mus.ndim != 1 or len(mus) == 0 or np.any(mus <= 0.0):
        raise ValueError("mus must be a nonempty positive vector")
    if not (0.0 < power_lambda < 1.0):
        raise ValueError("power_lambda must lie in (0,1)")
    if not (0.5 < kappa < 1.0):
        raise ValueError("kappa must lie in (0.5,1)")
    if q_correlation < 1.0 or rho <= 0.0:
        raise ValueError("q_correlation and rho are invalid")
    if normalization_floor < 0.0:
        raise ValueError("normalization_floor must be nonnegative")

    n_samples = len(x)
    M = int(controller_length)
    wt = np.zeros(M, dtype=float)
    y = np.zeros(n_samples, dtype=float)
    error = np.zeros(n_samples, dtype=float)
    mu_hist = np.zeros(n_samples, dtype=float)
    power = np.zeros(M, dtype=float)
    J = np.full(len(mus), float(rho), dtype=float)
    sigma_e2 = 0.0
    eps = 1e-12
    max_mu = 0.0
    max_wnorm = 0.0

    for n in range(n_samples):
        m = min(M, n + 1)
        xvec = np.zeros(M, dtype=float)
        xfvec = np.zeros(M, dtype=float)
        xvec[:m] = x[n - m + 1 : n + 1][::-1]
        xfvec[:m] = xf[n - m + 1 : n + 1][::-1]
        xhat = dct(xvec, type=2, norm="ortho")
        xfhat = dct(xfvec, type=2, norm="ortho")

        y[n] = float(np.dot(wt, xhat))
        ls = min(len(s), n + 1)
        ys = float(np.dot(s[:ls], y[n - ls + 1 : n + 1][::-1]))
        e = float(d[n] + ys + v[n])
        error[n] = e
        if (not math.isfinite(e)) or abs(e) > max_abs_error:
            return False, error, mu_hist, max_mu, max_wnorm, n, 1

        # Standard transform-domain power tracker used by DCT-FxNLMS.
        inst = xfhat * xfhat
        if n == 0:
            power = inst.copy()
        else:
            power = power_lambda * power + (1.0 - power_lambda) * inst
        scale_power = max(float(np.mean(power)), eps)
        normalization_diag = power + regularization_ratio * scale_power + normalization_floor + eps

        sigma_e2 = kappa * sigma_e2 + (1.0 - kappa) * (e * e)
        next_J = np.full_like(J, np.inf)
        for k, mu in enumerate(mus):
            # A candidate whose instantaneous MSD approximation becomes
            # non-positive is outside the validity/stability region of the
            # predictor for the current condition.  Disable that candidate
            # instead of allowing a negative ``MSD`` or raising on the next
            # sample.
            if not np.isfinite(J[k]) or J[k] <= 0.0:
                continue
            pred = dct_sss_msd_step(
                J=float(J[k]),
                mu=float(mu),
                q_correlation=float(q_correlation),
                transformed_filtered_reference=xfhat,
                normalization_diag=normalization_diag,
                sigma_e2=float(sigma_e2),
            )
            if np.isfinite(pred) and pred > 0.0:
                next_J[k] = pred
        J = next_J
        if not np.any(np.isfinite(J)):
            return False, error, mu_hist, max_mu, max_wnorm, n, 4
        best_k = int(np.argmin(J))
        mu = float(mus[best_k])
        mu_hist[n] = mu
        max_mu = max(max_mu, mu)

        # With e=d+S*y+v, gradient descent has a minus sign.
        wt -= mu * e * (xfhat / normalization_diag)
        wnorm = float(np.linalg.norm(wt))
        max_wnorm = max(max_wnorm, wnorm)
        if (not math.isfinite(wnorm)) or wnorm > max_weight_norm_limit:
            return False, error, mu_hist, max_mu, max_wnorm, n, 2

        if (n + 1) % hop_length == 0:
            i0 = n + 1 - hop_length
            num = float(np.dot(error[i0 : n + 1], error[i0 : n + 1]))
            u = d[i0 : n + 1] + v[i0 : n + 1]
            den = float(np.dot(u, u))
            ratio_db = 10.0 * math.log10((num + 1e-30) / (den + 1e-30))
            if (not math.isfinite(ratio_db)) or ratio_db > max_residual_ratio_db:
                return False, error, mu_hist, max_mu, max_wnorm, n, 3

    return True, error, mu_hist, max_mu, max_wnorm, -1, 0
