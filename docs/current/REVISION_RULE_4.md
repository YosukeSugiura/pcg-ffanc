# Revision 4: SFTF + det (option 2 after the third review; fixed 2026-10-31, before running)

[provenance note omitted]. Addresses N3 of
[provenance note omitted]: is the tracking of RLS + det available at fast-RLS cost?

## Method
- 'SFTF + det' = experiments/prototype_new_algorithms.py method 'R-SFTF': stabilized FTF (Slock & Kailath 1991; a priori
  form, mixing constants 1.5 / 2.5 / 1.0) on the same criterion as 'R-RLS' (virtual residual, exponential weighting,
  soft initialization delta mean(x_f^2) M), restarted at the detections of E-PCG (same det_events) with a PREWINDOWED
  restart at tau (the regressor inside the FTF is zero before tau) and replay of [tau, stop); warm (keep w) or cold.
  A covariance-form restart (that of RLS + det) has no O(M) form here; this is the standard FTF restart.
- Implementation check done before this rule (tuning seeds 300, 301; S8, both noises; no detections), against R-RLS with
  the same lambda 0.9999 and delta 1e-2: A2 equal to 3 decimals, A1 within 0.03 dB (soft-start weights), residual power
  trace within 0.7 % after hop 8, both stable; 1.2 s vs 12.4 s per run.

## Grid, selection, evaluation
- Grid (4) mirrors RLS + det configurations 0-3: lambda in {0.9999, 1.0} x {cold, warm}, delta 1e-2.
- Selection exactly as REVISION_RULE.md section 2 (tuning seeds, 15 conditions, admissible = no failed run of 450,
  score = mean of (A1 + A2) / 2). Output results/protocol_v2_sel/selected_c.json, selection_c.md. Other methods: records
  and selections unchanged.
- Evaluation 'v2c' (results/final_eval_v2c, EVAL_SET=main_c): v2b records copied; new runs only for SFTF + det (selected
  configuration, 600 runs). Metrics, tests, thresholds as FINAL_EVAL_RULE.md; Holm over 2 x 15 x 10 = 300 per proposed
  method. Rooms B / C and SNR 10 dB are not rerun (disclosed). Cost of SFTF + det: analytic (cost.sftf), as for SFTF.

## Interpretation (the text follows the matching row)
| outcome | text |
|---|---|
| (a) selected SFTF + det: median A1 within 0.5 dB of RLS + det in >= 12 of 15 conditions and no failure | 'a stabilized fast RLS restarted at the detections reproduces RLS + det at about 8k flops / sample': no tracking-per-cost advantage of E-PCG over it is claimed; E-PCG vs SFTF + det reported by the win rule |
| (b) no admissible configuration, or median A1 worse than RLS + det by >= 1 dB in >= 3 conditions | 'with the standard (prewindowed) restart the fast RLS does not reproduce RLS + det' (numbers); the cost statement of E-PCG vs fast RLS is made against SFTF + det as measured |
| (c) otherwise | the numbers, without either statement |

## Amendments after the code review (2026-10-31, while the selection runs, before any result was read)
- Wording: covariance-form (growing / sliding window) fast RLS algorithms of O(M) exist (Cioffi-Kailath family) at about
  twice the cost and with less analysis of their stabilization; the standard prewindowed restart is used here.
- The cost of SFTF + det (cost.sftf, 16 M flops / sample = 8.2k at M = 512) excludes the detector: its detections are
  those of E-PCG. Row (a) is stated as 'at about 8k flops / sample plus a detector'.
- No rescue / reinitialization in R-SFTF: a divergence (also for lambda = 1, outside the stability analysis of
  Slock-Kailath) counts as a failure of the configuration. 'det_delta' is not supported by R-SFTF (assert).
- The v2c summary replaces v2b for the claims; all labels are recomputed with Holm over 300.
- select-summary for this rule: SELOUT=_c python experiments/eval_v2.py select-summary.
