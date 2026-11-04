# Additional evaluations: cost vs convergence (Step 6) and S-model error (Step 5) (fixed 2026-10-30, before running)

[provenance note omitted]; descriptive reports, no win / loss decisions.
Script: experiments/extra_eval.py -> results/extra_eval/. Methods: the 8 of docs/current/FINAL_EVAL_RULE.md with the
same configurations (baselines selected at M = 512; used unchanged at other M: stated as a limitation). Evaluation
seeds 480-519 (40). Metrics A1, A2, tau_-12, failures exactly as in FINAL_EVAL_RULE.md.

## Step 6: cost vs convergence
- M in {256, 512, 1024} (N = 2M, H = 128); cells S8 and S2 x {ar1, harmonic}. M = 512 records are reused from
  results/final_eval (identical configuration and runs).
- Cost (flops per sample, adaptation part, excluding the filtering common to all filtered-x methods, which is reported
  separately): E-PCG measured (mean flop_hist / H); baselines analytic (src/ffanc_norm/cost.py: fd_fxnlms, leaky,
  convex, fdkf, rls, vff_rls); SFTF (fast RLS, same output as RLS up to numerics) as an analytic cost point attached
  to the RLS performance.
- Reported: table of median A1 / A2 / tau_-12 per method x M x cell x noise with the cost; figure: A1 (S2) and
  A2 (S8) vs cost, one line per method through M = 256 / 512 / 1024.

## Step 5: robustness to the secondary-path model error
- S_hat = S + delta, NMSE ||delta||^2 / ||S||^2 in {-30, -20, -15, -10} dB (existing cfg flag shat_nmse_db: delta
  with the envelope of |S|, seed-dependent); M = 512; cells S8 and S1 x {ar1, harmonic}.
- Reported per method x NMSE x cell x noise: failure count (rule of FINAL_EVAL_RULE.md), median A2, median A1; and per
  NMSE the median fraction of bins with |angle(S / S_hat)| > 90 deg (the classical FxLMS stability condition).
- No method or configuration is changed after these results.

## Amendments before any summary (2026-10-30, code review; reporting only, the runs are unchanged)
- Cost: FDKF analytic count revised (virtual residual + W transform: +3 FFTs, ~40 flops/bin); E-PCG cost reported per
  cell (S8 / change); notes on measured vs analytic counts and on the S_hat * y term (virtual-residual methods only).
- S-model error: report both the mean fraction of bins with |angle(S/S_hat)| > 90 deg and with |1 - S/S_hat| >= 1;
  state the error structure of each method (FxLMS: FD-FxNLMS, leaky; modified FxLMS / virtual residual: the others).
- S8 tau_-12 added to the table; summary robustness checks (uncontrolled power, nan guard, duplicates).
