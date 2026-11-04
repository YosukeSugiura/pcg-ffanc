# Revision experiments after the strict review (fixed 2026-10-30, before running)

[provenance note omitted]. Addresses [internal rationale omitted], items 1-5 of the improvement list.
Script: experiments/eval_v2.py (stages select / final), experiments/cg_ratio.py (item 4).

## 1. Detector-equipped baselines (review: separate the solver from the detector)
- 'RLS + det' and 'FD-FxNLMS + det' receive exactly the detections of the proposed method on the same run (stop sample
  and localized change point tau; results/det_events/). RLS + det: reset P, replay [tau, stop) (covariance resetting);
  FD-FxNLMS + det: FD-FxNLMS with the circulant-RLS step schedule (V-SCHED, Prop. 2) restarted at tau. Variants: keep or
  zero the controller at the restart (det_reset_w), cumulative-mean ('cum') or circulant-RLS ('rls') denominator.
- Their grids are part of the selection below; same admissibility and score as every baseline.
- Pre-run smoke test (tuning seed 300, recorded here because it motivated the grid, not a decision): the FD restart is
  unstable in harmonic cells with the original 'cum' schedule (A1 > 0 dB), RLS + det improves with det_reset_w in S7.

## 2. Baseline (re)selection aligned with the claims
- Data: tuning seeds 300-309, 600-619; the 15 cell x noise of the final evaluation (room A).
- Grids (experiments/eval_v2.GRID): FD-FxNLMS mu {0.05, 0.1, 0.15, 0.2, 0.25, 0.3} (extended downwards: only 0.2 was
  admissible before); leaky mu {0.1, 0.2, 0.35} x leak {1e-3, 1e-2}; convex 6 pairs incl. smaller steps; FDKF as before;
  RLS lambda {0.9995, 0.9998, 0.9999}; VFF-RLS N0 {500, 2000} (lam_min 0.9995); the two detector-equipped grids (6 / 4).
- Admissible: no failed run among the 450 (failure as in FINAL_EVAL_RULE.md). Score: mean over the 15 combinations of
  the mean over seeds of (A1 + A2) / 2 (was: mean NR over [1 s, end], dominated by A2). Lowest score is selected.
- The proposed method is not retuned.

## 3. Final evaluation v2 (evaluation seeds 480-519, room A, 15 combinations)
- Methods: the selected baselines (incl. the two detector-equipped ones) + E-PCG + E-PCG bank. Records of the final
  evaluation with an identical configuration are reused (bit-identical runs).
- Metrics, tests and win / loss thresholds: exactly FINAL_EVAL_RULE.md (Holm over 2 x 15 x number of baselines).
- Reported side by side with the first final evaluation; neither replaces the other. The claims of the paper are taken
  from v2 (A1-aligned selection, detector-equipped baselines).

## 4. CG error ratio (diagnostic): experiments/cg_ratio.py, tuning seeds 300-304, S8 / S2 / R2 x 2 noises.

## 5. Additional rooms / SNR (evaluation seeds 480-519; configurations unchanged, no retuning)
- roomB: RT60 0.15 s, roomC: RT60 0.3 s (same 3 x 2 x 1.5 m room, reflection order 30); cells S8, S2, S5, R2 x 2 noises.
- snr10: room A with sensor SNR 10 dB (default 20 dB); cells S8, S2 x 2 noises.
- Same metrics and tests as section 3; reported per condition; no method or configuration changes afterwards.

## Amendments after the code review (2026-10-30, before the runs they affect)
- Wording (review S1): the detector-equipped baselines get the same detections (from E-PCG's own closed loop, review M2)
  but restart naively (no Prop. 9 weighting, no growing controller length): 'same detector, baseline-type restart',
  not an isolation of the estimator.
- 'FD-FxNLMS + det' grid: two configurations appended (warm start, step boost after a detection decaying to the
  FD-FxNLMS step 0.2: scale 0.125 / 0.0625, mu_min 0.2). They run in a later round of the selection job (resume); the
  selection rule is unchanged.
- Rooms B / C (review S2): impulse responses long enough for the reverberation: B len_p 1200 / len_s 512, C len_p 2400
  / len_s 1024 (was truncated at 1024 / 256 = 128 / 32 ms). Room A unchanged.
- cg_ratio (review S3): eigenvalues of the preconditioned window matrix computed at a full window (n = L H), rerun
  before the final stage.
- A method with no admissible configuration is reported as such and not evaluated (review M6).

## Order
cg_ratio + selection (one job) -> final v2 -> rooms (roomB, roomC, snr10; one job).
