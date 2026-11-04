# Revision experiments 2 (review N1-N3; fixed 2026-10-30, before running)

[provenance note omitted] for N1-N3 of
[internal rationale omitted], [editorial attribution omitted]. Same scripts as REVISION_RULE.md
(experiments/eval_v2.py); code flags in experiments/prototype_new_algorithms.py (defaults unchanged, bit-identity checked:
fixed_binwise with det_events and no boost = FD-FxNLMS; R-RLS with explicit det_delta = delta, det_replay = True = before).

## 1. N1: 'FD-FxNLMS + restart' (new baseline; the existing 'FD-FxNLMS + det' stays and is reported)
- The selected FD-FxNLMS (fixed_binwise, mu 0.3, same smoothed bin-power denominator) until a detection; at each detection
  of E-PCG (same det_events as the other detector-equipped baselines) a step boost mu_b = max(0.3, s (N / H) / (b_since + 1)),
  N / H = 8, b_since counted from tau // H; warm (keep w) or cold (w = 0).
- Grid (7): warm x s in {1/16, 1/8, 1/4} (1, 3, 6 boosted hops; initial mu_b 0.5, 1, 2), cold x s in {0, 1/16, 1/8, 1/4}
  (cold s = 0 = plain restart). Configurations that diverge are removed by the admissibility rule.
- Check before the summary: on runs without detections (all S8 runs of the evaluation seeds) the residual power trace equals
  that of FD-FxNLMS bit for bit; otherwise stop.

## 2. N2: restart of RLS + det
- Appended configurations (4): lambda 0.9999, initial delta 1e-2, reset regularization det_delta in {1e-1, 1}, warm / cold.
  Replay on / off not included (tau lies in the detection hop: replay <= H = 128 samples, no effect at memory 1e4).
- The four existing configurations are reused (records unchanged).

## 3. Selection and evaluation
- Selection exactly as REVISION_RULE.md section 2 (tuning seeds, 15 conditions, admissible = no failed run of 450, score =
  mean of (A1 + A2) / 2), over the full grids; output results/protocol_v2_sel/selected_b.json, selection_b.md
  (selected.json is kept). Other methods are not rerun (their records and selections are unchanged).
- Evaluation 'v2b' (results/final_eval_v2b, EVAL_SET=main_b): records of final_eval_v2 with an identical configuration are
  copied; new runs only for 'FD-FxNLMS + restart' and, if its selection changed, 'RLS + det'. Metrics, tests, thresholds as
  FINAL_EVAL_RULE.md; Holm over 2 x 15 x 10 = 300 per proposed method. v2 is kept; the claims are taken from v2b.
- Rooms B / C and SNR 10 dB are not rerun with the new baselines (disclosed).

## 4. Interpretation (fixed now; the text follows the matching row)
| outcome | text |
|---|---|
| N1: selected FD + restart within +-0.5 dB of FD-FxNLMS in A1 in >= 12 of 15 conditions and no win of FD + restart over FD-FxNLMS (paired test as in section 3, Holm over its 30 comparisons) | 'FD-FxNLMS does not profit from restarting at the detections' |
| N1: FD + restart beats FD-FxNLMS by the win rule in >= 3 conditions | the detector also helps FD-FxNLMS; E-PCG's gains reported against FD + restart; abstract / experiments wording replaced |
| otherwise | report the numbers without either statement |
| N2: with the reselected RLS + det, E-PCG - RLS + det in S7 (AR(1)) A1 (median paired difference) > -1 dB | the S7 gain is not claimed as a contribution of the estimator |
| N2: the difference stays <= -3 dB and the hop table (section 5) shows RLS + det's under-determined phase (n <= M after the restart) | the S7 gain is attributed to the effective order after a restart (E-PCG's growing length; Thm 1 with m_eff / n) |
| N2: between | report the numbers, attribution 'partly' |

## 5. Diagnostics from stored records (no runs)
- S7 hop table: per hop 62-72, NR of the ensemble (40 evaluation seeds, seed-summed powers) for E-PCG and RLS + det (v2b).
- A2 vs memory length (AR(1) only): predicted steady excess M (1 - lambda) / 2 (exponential window) vs M / (L H) (E-PCG
  window), checked on (i) S8 ar1 RLS lambda 0.9995 vs RLS + det 0.9999 (evaluation seeds, v2), (ii) RLS lambda in
  {0.9995, 0.9998, 0.9999} S8 A2 (tuning seeds, selection records), (iii) ablation L = 24 vs 48 (ablation_core_d). Predicted
  dB differences 10 log10((1 + e_a) / (1 + e_b)) with the excess e relative to the floor; agreement = within +-0.1 dB in all
  three -> 'memory length' explanation in the text; otherwise 'not explained'.

## 6. N3: fast RLS + the same detector
- Not implemented (option (b) of the advice): the stabilized FTF has the output of exponentially weighted RLS where it is
  stable, so 'SFTF + det' would reproduce RLS + det (including its under-determined phase after a restart, section 5) at
  ~8M flops/sample if a covariance-form restart were available; the prewindowed restart differs from RLS + det. The text
  states this, marks SFTF + det as an analytic point in the cost figure, and drops 'at a cost comparable to fast RLS' as a
  claim of superiority. A verification-only SFTF (few seeds) may be added later under a separate rule.

## Order
One job per core: selection (SHARD 0/2, 1/2; SELOUT=_b at the end) -> S8 identity check -> main_b reuse + final-run ->
final-summary -> diagnostics -> text.
