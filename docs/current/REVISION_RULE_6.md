# Revision 6: fast RLS with an exact (covariance) restart (fixed 2026-10-31, before running)

Protocol scope (2026-10-31 11:28): implement a fast RLS + detector whose restart keeps the true regressor
(review N8 of [internal rationale omitted], after REVISION_RULE_5 attributed the SFTF + det deficit to the prewindowed restart).

## Implementation (experiments/prototype_new_algorithms.py, R-SFTF flags; defaults unchanged)
- 'preroll' K (tested, not evaluated): FTF predictors restarted K samples before tau, joint process frozen before tau.
  Equals its O(M^2) twin ('det_preroll', 0.02 dB) but acts as a data-shaped prior toward the kept controller and is worse
  than RLS + det on the tuning smoke runs (S7 ar1 seed 300: A1 +2.2 vs -2.7 dB) -> not pursued.
- 'hybrid' T_h: after a detection, exact exponentially weighted RLS with the true regressor and P = I / R0 (= RLS + det)
  on [tau, tau + T_h); then an FTF re-initialized with a pre-roll of the T_h post-change samples (prewindowed at tau,
  joint process frozen) continues from the RLS controller at O(M). Smoke check (tuning seeds 300 / 301; S7 ar1, S2
  harmonic, S8 ar1): A1 / A2 within 0.03 dB of RLS + det for T_h = 1024 and 2048.
- Cost (analytic): 16 M flops / sample (SFTF) plus, per detection, T_h (4 M^2 + 4 M) for the exact RLS and 16 M T_h for
  the FTF re-initialization (T_h = 1024, M = 512: about 1.1e9 flops per detection), plus the detector.

## Grid, selection, evaluation
- 'SFTF-H + det': lambda 0.9999, delta 1e-2, warm (the selected RLS + det configuration), T_h in {512, 1024, 2048}.
- Selection as REVISION_RULE.md section 2 -> results/protocol_v2_sel/selected_d.json, selection_d.md.
- Evaluation 'v2d' (results/final_eval_v2d, EVAL_SET main_d): v2c records copied; new runs for SFTF-H + det only.
  Holm over 2 x 15 x 11 = 330 per proposed method; v2d replaces v2c for the claims. Rooms / SNR not rerun.

## Interpretation (the text follows the matching row)
| outcome | text |
|---|---|
| (a) selected SFTF-H + det: median A1 within 0.5 dB of RLS + det in >= 12 of 15 conditions, no failure | 'a fast RLS with an exact restart reproduces RLS + det at 8.2k flops / sample plus about 1e9 flops per detection (and a detector)'; no tracking advantage of E-PCG over it beyond the win rule; cost compared per detection rate |
| (b) otherwise | numbers only |

## Note after the results (2026-10-31, internal code review): cost count
The analytic count above (T_h (4 M^2 + 4 M)) differs from the RLS count used elsewhere (6 M^2 + 8 M per sample,
cost.rls); the paper uses the latter: 3.2e9 (T_h = 2048) / 1.6e9 (1024) flops per detection. Break-even with E-PCG uses a
two-term model (per sample + per detection; E-PCG 8.6k + about 1.2e8 per detection from the measured 12.6k with 1.4
detections per 5 s run). No decision of this rule depends on the cost count.
