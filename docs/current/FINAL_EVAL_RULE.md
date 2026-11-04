# Final evaluation on the evaluation seeds (agreed 2026-10-29 21:30, fixed before running)

Script: experiments/final_eval.py -> results/final_eval/. Plan: [planning reference omitted] section 4, [workflow reference omitted].

## Methods (8)
- Baselines (6): results/protocol_final_sel/selected.json (FD-FxNLMS, leaky, convex, RLS, VFF-RLS, FDKF).
- Proposed main: E-PCG = single window L = 48 hops + detection (det_C_pre) + Prop. 9 (final_config_core_main.json).
- Proposed extension: memory bank [12, 48, 1000] + restart + det_C_pre (final_config_core_final.json).
M = 512, N = 2M, H = 128, T = 5 s, change at 1.0 s (S5 / R3: continuous 1.0-1.6 s).

## Data
15 cell x noise = {S8, S1, S2, S5, S7 (ar1 only), R1, R2, R3} x {ar1, harmonic}; evaluation seeds 480-519 (40), first
use for these configurations. 8 x 15 x 40 = 4800 runs.

## Metrics (per run; 1 hop = 16 ms; NR = 10 log10(sum residual / sum uncontrolled) over the hops)
| key | definition |
|---|---|
| fail | S8: strict_div.evaluate(th = 0); change cells: strict_div.evaluate_div |
| A1 | change cells: hops [ceil(1.0 fs/H), +32) (0.5 s); S5 / R3: [ceil(1.0 fs/H), ceil(1.6 fs/H)); S8: hops [0, 32) |
| A2 | change cells: from the end of the A1 window to the end of the run; S8: last 1 s (62 hops) |
| tau_L | L in {-9, -12} dB (absolute, method independent): first 16-hop window end k >= ceil(t_e fs/H) + 16 with window NR <= L; tau = k H/fs - t_e; t_e = 1.0 s (S5 / R3: 1.6 s; S8: 0); not reached: 4 s (censored) |
A failed run: A1 = A2 = 0 dB, tau = 4 s; a run stopped early by the simulator flag is completed with "no control"
(NR 0 dB) for the curves.

## Reported
- Main text: ensemble learning curves (16-hop window NR of the seed-summed powers) with a seed-bootstrap 95 % band
  (1000 resamples); A1 / A2 table (median, IQR); failure counts; reach curves (fraction of runs with tau_L <= t).
- Supplement: tau_L medians, all tests, win counts.
- Not reported: the self-referenced T, tau with a target set by the proposal.

## Tests
- Paired (seed) Wilcoxon signed-rank, zero_method = 'pratt'; d = proposed - baseline (negative = proposed better).
- Holm over 6 baselines x 15 combinations x {A1, A2} = 180 tests, separately for the main method and the extension.
- Win: Holm p < 0.05 and (median dA1 <= -1 dB or median dA2 <= -0.5 dB); loss: Holm p < 0.05 and (median dA1 >= +1 dB
  or median dA2 >= +0.5 dB); both: mixed.
- Main vs extension: the same test over 15 x {A1, A2} = 30 (Holm), reported with the medians.
- No method or configuration is changed after these results.
