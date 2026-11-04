from __future__ import annotations

from dataclasses import dataclass
import numpy as np


def ar1_autocovariance(lags: np.ndarray | int, pole: float = 0.95) -> np.ndarray:
    """Unit-variance stationary AR(1) autocovariance."""
    lags = np.asarray(lags)
    return pole ** np.abs(lags)


def filtered_autocovariance(
    filt: np.ndarray,
    max_lag: int,
    pole: float = 0.95,
) -> np.ndarray:
    """r_z[l] for z = filt * x, x a unit-variance stationary AR(1).

    Returns nonnegative lags 0..max_lag. For this real WSS process,
    r_z[-l] = r_z[l].
    """
    h = np.asarray(filt, dtype=float)
    out = np.zeros(max_lag + 1, dtype=float)
    i = np.arange(len(h))[:, None]
    j = np.arange(len(h))[None, :]
    hh = h[:, None] * h[None, :]
    for lag in range(max_lag + 1):
        # E[z[n] z[n-lag]] = sum_i,j h_i h_j r_x[lag + j - i]
        out[lag] = np.sum(hh * (pole ** np.abs(lag + j - i)))
    return out


def toeplitz_from_autocov(r_nonnegative: np.ndarray, size: int) -> np.ndarray:
    r = np.asarray(r_nonnegative, dtype=float)
    if len(r) < size:
        raise ValueError("autocovariance does not cover requested matrix size")
    idx = np.arange(size)
    return r[np.abs(idx[:, None] - idx[None, :])]


def expected_rfft_power(r_nonnegative: np.ndarray, fft_length: int) -> np.ndarray:
    """E|FFT(z_0,...,z_{N-1})|^2 for an N-sample WSS real sequence."""
    r = np.asarray(r_nonnegative, dtype=float)
    N = int(fft_length)
    if len(r) < N:
        raise ValueError("autocovariance must include lags through N-1")

    # Expected periodogram: Fourier transform of triangularly weighted covariance.
    c = np.zeros(N, dtype=float)
    c[0] = N * r[0]
    for lag in range(1, N):
        value = (N - lag) * r[lag]
        c[lag] += value
        c[N - lag] += value
    p = np.fft.rfft(c).real
    # Numerical roundoff can create tiny negative edge values.
    return np.maximum(p, np.finfo(float).tiny)


def expected_fd_update_matrix(
    r_nonnegative: np.ndarray,
    fft_length: int,
    hop_length: int,
    controller_length: int,
    denominator: np.ndarray,
) -> np.ndarray:
    """Expected finite-dimensional FD normalized-gradient Jacobian.

    This matches the implemented causal block gradient with:
      - N-sample filtered-reference history,
      - H new error samples right-aligned in the FFT frame,
      - frequency-domain normalization,
      - first M causal gradient coefficients retained.

    The denominator is treated as deterministic (stationary expected value).
    The returned K satisfies approximately
        E[w_{b+1}-w*] = (I - mu K) E[w_b-w*].
    """
    r = np.asarray(r_nonnegative, dtype=float)
    N = int(fft_length)
    H = int(hop_length)
    M = int(controller_length)
    denom = np.asarray(denominator, dtype=float)

    if N < M + H - 1:
        raise ValueError("need N >= M + H - 1")
    if denom.shape != (N // 2 + 1,):
        raise ValueError("unexpected denominator shape")
    if np.any(denom <= 0):
        raise ValueError("denominator must be positive")

    # The circular correlation vector for basis coefficient m has expectation
    # c_m[q] = sum_{n=N-H}^{N-1} r_z[((n-q) mod N) - (n-m)].
    # Since r_z is even, only |lag| is required.
    max_needed = N + M
    if len(r) <= max_needed:
        raise ValueError("autocovariance range is too short")

    n = np.arange(N - H, N)
    K = np.empty((M, M), dtype=float)

    for m in range(M):
        c = np.empty(N, dtype=float)
        for q in range(N):
            i = (n - q) % N
            lag = i - (n - m)
            c[q] = np.sum(r[np.abs(lag)])
        C = np.fft.rfft(c)
        g = np.fft.irfft(C / denom, n=N)
        K[:, m] = g[:M]

    return K


def primary_variance(primary_path: np.ndarray, pole: float = 0.95) -> float:
    p = np.asarray(primary_path, dtype=float)
    i = np.arange(len(p))[:, None]
    j = np.arange(len(p))[None, :]
    return float(np.sum(p[:, None] * p[None, :] * (pole ** np.abs(j - i))))


def filtered_primary_crosscov(
    secondary_path: np.ndarray,
    primary_path: np.ndarray,
    controller_length: int,
    pole: float = 0.95,
) -> np.ndarray:
    """q[m] = E[z[n-m] d[n]], z = s*x, d = p*x."""
    s = np.asarray(secondary_path, dtype=float)
    p = np.asarray(primary_path, dtype=float)
    q = np.zeros(controller_length, dtype=float)
    for m in range(controller_length):
        total = 0.0
        for i, si in enumerate(s):
            for j, pj in enumerate(p):
                total += si * pj * (pole ** abs(j - m - i))
        q[m] = total
    return q


def wiener_solution(
    secondary_path: np.ndarray,
    primary_path: np.ndarray,
    controller_length: int,
    pole: float = 0.95,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, float]:
    max_lag = max(controller_length - 1, 1)
    rz = filtered_autocovariance(secondary_path, max_lag=max_lag, pole=pole)
    R = toeplitz_from_autocov(rz, controller_length)
    q = filtered_primary_crosscov(secondary_path, primary_path, controller_length, pole)
    # e = d + z^T w, hence R w* + q = 0.
    w_star = -np.linalg.solve(R, q)
    var_d = primary_variance(primary_path, pole)
    j_min = float(var_d + 2.0 * q @ w_star + w_star @ R @ w_star)
    return w_star, R, q, j_min


def modal_time_constants(
    K: np.ndarray,
    mu: float,
    hop_length: int,
    sample_rate: float,
) -> dict[str, np.ndarray]:
    eig = np.linalg.eigvals(np.asarray(K, dtype=float))
    contraction = 1.0 - float(mu) * eig
    mag = np.abs(contraction)

    stable = mag < 1.0
    tau_amp_blocks = np.full_like(mag, np.inf, dtype=float)
    tau_power_blocks = np.full_like(mag, np.inf, dtype=float)

    valid = stable & (mag > 0.0)
    tau_amp_blocks[valid] = -1.0 / np.log(mag[valid])
    tau_power_blocks[valid] = -1.0 / (2.0 * np.log(mag[valid]))
    tau_amp_blocks[stable & (mag == 0.0)] = 0.0
    tau_power_blocks[stable & (mag == 0.0)] = 0.0

    sec_per_block = float(hop_length) / float(sample_rate)
    return {
        "eigenvalues": eig,
        "contraction": contraction,
        "magnitude": mag,
        "stable": stable,
        "tau_amp_blocks": tau_amp_blocks,
        "tau_power_blocks": tau_power_blocks,
        "tau_amp_seconds": tau_amp_blocks * sec_per_block,
        "tau_power_seconds": tau_power_blocks * sec_per_block,
    }


def theoretical_residual_curve(
    K: np.ndarray,
    mu: float,
    w_star: np.ndarray,
    R: np.ndarray,
    j_min: float,
    secondary_noise_variance: float,
    n_hops: int,
    uncontrolled_variance: float,
) -> dict[str, np.ndarray]:
    """Mean-mode deterministic convergence curve.

    It includes the independent secondary-noise floor in total error power but
    not stochastic-gradient misadjustment. The latter is typically small in the
    total-error curve when the secondary-noise floor dominates.
    """
    A = np.eye(len(w_star)) - float(mu) * np.asarray(K, dtype=float)
    delta = -np.asarray(w_star, dtype=float).copy()  # w_0 = 0

    anc_power = np.empty(n_hops, dtype=float)
    total_power = np.empty(n_hops, dtype=float)

    for b in range(n_hops):
        # Power during hop b is approximated from the coefficient state before
        # the subsequent update.
        anc_power[b] = max(float(j_min + delta @ R @ delta), 0.0)
        total_power[b] = anc_power[b] + secondary_noise_variance
        delta = A @ delta

    total_db = 10.0 * np.log10(np.maximum(total_power, 1e-300) / uncontrolled_variance)
    return {
        "anc_power": anc_power,
        "total_power": total_power,
        "total_residual_db": total_db,
    }


def secondary_noise_gradient_covariance(
    r_nonnegative: np.ndarray,
    fft_length: int,
    hop_length: int,
    controller_length: int,
    denominator: np.ndarray,
    secondary_noise_variance: float,
) -> np.ndarray:
    """Gradient-noise covariance caused by independent white error-sensor noise.

    The denominator is treated as deterministic. This function exactly matches
    the implemented block gradient for a stationary filtered reference with
    covariance ``r_nonnegative`` and H independent noise samples in each block.

    If g_v is the normalized FD gradient generated by secondary noise only,
    this returns

        Q = E[g_v g_v^T].

    The derivation writes the inverse spectral normalization as an N-point
    circular time-domain operator, evaluates its output covariance from the
    N-sample filtered-reference covariance, and sums the H independent error
    samples that enter one update.
    """
    r = np.asarray(r_nonnegative, dtype=float)
    N = int(fft_length)
    H = int(hop_length)
    M = int(controller_length)
    denom = np.asarray(denominator, dtype=float)
    sigma2 = float(secondary_noise_variance)

    if N < M + H - 1:
        raise ValueError("need N >= M + H - 1")
    if len(r) < N:
        raise ValueError("autocovariance must include lags through N-1")
    if denom.shape != (N // 2 + 1,):
        raise ValueError("unexpected denominator shape")
    if np.any(denom <= 0.0):
        raise ValueError("denominator must be positive")
    if sigma2 < 0.0:
        raise ValueError("secondary_noise_variance must be nonnegative")

    # Covariance of the chronological N-sample filtered-reference frame.
    idx = np.arange(N)
    R_N = r[np.abs(idx[:, None] - idx[None, :])]

    # h_d is the real circular impulse response corresponding to 1 / D_k.
    h_d = np.fft.irfft(1.0 / denom, n=N)

    # For an error impulse at circular position r_e, gradient component m is
    # u[(r_e-m) mod N], with
    #   u[j] = sum_q z[q] h_d[(q-j) mod N].
    j = np.arange(N)[:, None]
    q = np.arange(N)[None, :]
    U = h_d[(q - j) % N]
    C_u = U @ R_N @ U.T

    Q = np.zeros((M, M), dtype=float)
    m = np.arange(M)
    for r_e in range(N - H, N):
        inds = (r_e - m) % N
        Q += C_u[np.ix_(inds, inds)]

    return sigma2 * Q


def stationary_weight_error_covariance(
    K: np.ndarray,
    mu: float,
    gradient_noise_covariance: np.ndarray,
) -> np.ndarray:
    """Solve the additive-noise mean-square recursion at steady state.

    Approximation:

        C_{b+1} = A C_b A^T + mu^2 Q,
        A = I - mu K.

    This retains the exact finite-dimensional mean matrix K and the exact
    additive secondary-noise gradient covariance Q for a deterministic
    normalization denominator. Random-Hessian and random-denominator terms are
    not included in this closed-form Lyapunov approximation.
    """
    from scipy.linalg import solve_discrete_lyapunov

    K = np.asarray(K, dtype=float)
    Q = np.asarray(gradient_noise_covariance, dtype=float)
    if K.ndim != 2 or K.shape[0] != K.shape[1]:
        raise ValueError("K must be square")
    if Q.shape != K.shape:
        raise ValueError("gradient_noise_covariance must match K")

    A = np.eye(K.shape[0]) - float(mu) * K
    if np.max(np.abs(np.linalg.eigvals(A))) >= 1.0:
        raise ValueError("mean recursion is not stable")

    C = solve_discrete_lyapunov(A, (float(mu) ** 2) * Q)
    # Remove tiny numerical asymmetry.
    return 0.5 * (C + C.T)


def misadjustment_metrics(
    R: np.ndarray,
    weight_error_covariance: np.ndarray,
    minimum_anc_residual_power: float,
    secondary_noise_variance: float,
) -> dict[str, float]:
    """Return EMSE, dimensionless misadjustment, and implied error floor.

    We define the minimum total error power as

        J_min,total = J_min,ANC + sigma_v^2,

    and

        M = EMSE / J_min,total,
        EMSE = tr(R C_infinity).
    """
    R = np.asarray(R, dtype=float)
    C = np.asarray(weight_error_covariance, dtype=float)
    j_anc = float(minimum_anc_residual_power)
    sigma2 = float(secondary_noise_variance)
    emse = float(np.trace(R @ C))
    minimum_total = j_anc + sigma2
    if minimum_total <= 0.0:
        raise ValueError("minimum total error power must be positive")
    misadjustment = emse / minimum_total
    steady_total = minimum_total + emse
    floor_lift_db = 10.0 * np.log10(steady_total / minimum_total)
    return {
        "emse": emse,
        "minimum_total_error_power": minimum_total,
        "misadjustment": float(misadjustment),
        "misadjustment_percent": float(100.0 * misadjustment),
        "steady_total_error_power": float(steady_total),
        "floor_lift_db": float(floor_lift_db),
    }


def theoretical_residual_curve_mean_square(
    K: np.ndarray,
    mu: float,
    w_star: np.ndarray,
    R: np.ndarray,
    j_min: float,
    secondary_noise_variance: float,
    gradient_noise_covariance: np.ndarray,
    n_hops: int,
    uncontrolled_variance: float,
) -> dict[str, np.ndarray]:
    """Mean-square corrected convergence curve under additive gradient noise.

    The mean follows the finite-dimensional recursion ``A = I - mu K``. The
    coefficient covariance follows the discrete Lyapunov recursion with a
    deterministic denominator. This gives the transient EMSE and the
    steady-state misadjustment floor in one recursion.
    """
    K = np.asarray(K, dtype=float)
    R = np.asarray(R, dtype=float)
    Q = np.asarray(gradient_noise_covariance, dtype=float)
    mu = float(mu)
    A = np.eye(len(w_star)) - mu * K
    mean_delta = -np.asarray(w_star, dtype=float).copy()
    C = np.zeros_like(K)

    anc_power = np.empty(n_hops, dtype=float)
    emse = np.empty(n_hops, dtype=float)
    total_power = np.empty(n_hops, dtype=float)

    for b in range(n_hops):
        mean_excess = float(mean_delta @ R @ mean_delta)
        covariance_excess = float(np.trace(R @ C))
        emse[b] = covariance_excess
        anc_power[b] = max(float(j_min + mean_excess + covariance_excess), 0.0)
        total_power[b] = anc_power[b] + secondary_noise_variance

        mean_delta = A @ mean_delta
        C = A @ C @ A.T + (mu**2) * Q
        C = 0.5 * (C + C.T)

    total_db = 10.0 * np.log10(np.maximum(total_power, 1e-300) / uncontrolled_variance)
    return {
        "anc_power": anc_power,
        "emse": emse,
        "total_power": total_power,
        "total_residual_db": total_db,
    }
