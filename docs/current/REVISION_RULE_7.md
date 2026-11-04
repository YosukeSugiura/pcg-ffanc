# Revision 7: covariance-window FTF + det (fixed 2026-10-31, before running)

Protocol scope (2026-10-31 13:04). An O(M) fast RLS whose restart keeps the true regressor exactly.

## Method ('CFTF + det' = R-SFTF with flag cov; defaults unchanged)
- After a detection at tau: stabilized FTF on the covariance window [tau, t] with the true regressor and the prior
  pi lam^(t-tau+1) diag(lam^-i) centred at the kept (warm) or zero (cold) controller, pi = delta mean(x_f^2) M (RLS + det
  uses pi I). The forward predictor lives on the window [tau-1]; its gain follows from the gain of [tau] by a rank-one
  correction with z = R[tau]^-1 u(tau-1), updated at O(M) per sample (experiments/prototype_new_algorithms._cftf_*).
- Checks before this rule: direct LS (M = 16, rel. error 4e-14); exact RLS with the same prior (M = 64, lam 0.9999,
  20000 samples, 1e-14); tuning smoke (seeds 300-302; S7 ar1, S2 harmonic, R2 ar1): A1 within 0.06 dB, A2 equal to 3
  decimals, of RLS + det; about 1 s per run.
- Cost (analytic): about 28 M flops per sample (16 M SFTF + 12 M for the rank-one terms; 14.3k at M = 512), no extra
  cost per detection beyond the re-initialization (O(M)), plus a detector.

## Grid, selection, evaluation
- Grid mirrors RLS + det configurations 0-3: lambda in {0.9999, 1.0} x {cold, warm}, delta 1e-2, cov = True.
- Selection as REVISION_RULE.md section 2 -> selected_e.json / selection_e.md. Evaluation 'v2e' (results/final_eval_v2e,
  EVAL_SET main_e): v2d records copied; new runs for CFTF + det only; Holm over 2 x 15 x 12 = 360; v2e replaces v2d for
  the claims. Rooms / SNR not rerun.

## Interpretation
| outcome | text |
|---|---|
| (a) selected CFTF + det: median A1 within 0.5 dB of RLS + det in >= 12 of 15 conditions, no failure | 'an O(M) fast RLS with a covariance-window restart reproduces RLS + det at about 14k flops / sample plus a detector': E-PCG has no tracking advantage over it beyond the win rule and no cost advantage claim beyond the per-sample figures (8.6k / 12.6k vs about 14k + detector) |
| (b) otherwise | numbers only |
