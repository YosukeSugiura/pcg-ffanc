# Revision 3: diagnostic for review N6 (fixed 2026-10-30 21:10, before running)

[provenance note omitted] for N6 of
[internal rationale omitted] Diagnostic only: no baseline is reselected, no claim of v2b changes its source.

## Run
- 'RLS + det' configuration 0 of experiments/eval_v2.GRID (lambda 0.9999, delta 1e-2, det_reset_w = True: COLD restart),
  which differs from the selected configuration 1 (warm) only in the restart mode. Cell S7 rd abrupt, AR(1), room A,
  evaluation seeds 480-519 (40 runs), same det_events. Script: experiments/diag_s7_cold.py ->
  results/revision3_diag/s7_cold.{jsonl,md}.
- Reported: median A1 / A2 of cold, warm (v2b record) and E-PCG; E-PCG - cold median paired difference (Wilcoxon pratt,
  single test, no Holm: diagnostic); failures; hop table 62-72 as in revision2_diag (cold added).
- Tuning seeds (already stored, protocol_v2_sel): S7 AR(1) median A1 cold cfg 0 -9.35 dB, warm cfg 1 -7.45 dB.

## Interpretation (the text follows the matching row)
| E-PCG - cold, S7 AR(1), median paired A1 | text |
|---|---|
| <= -3 dB | the S7 gain is stated against both restart modes; attribution stays 'consistent with the effective order' |
| (-3, -1] dB | the gain against the restarted RLS after an abrupt change is stated as the cold value; attribution 'partly' |
| > -1 dB | the S7 gain over a restarted RLS is not claimed; it is attributed to the restart mode of the selected baseline |
In every case the text states the selected RLS + det configuration (lambda 0.9999, delta 1e-2, warm) and the tuning-seed
values above, and cites ablation_core_b (W4 / W6: Stein weighting vs restart in S7) for the Stein part.

## Addendum (2026-10-30 21:40, before running): review N4, rooms B / C, R2 failures
- Diagnostic only (no ANC runs, no decision): for R2 rig 30cm in rooms A, B, C (configurations of experiments/eval_v2.ROOMS),
  evaluation seeds 480-519, the secondary path before (S = S_hat, kept by every method) and after the move (S2):
  broadband ||s2 - s|| / ||s|| and the fraction of 2048-point bins with |1 - S2 / S| >= 1 (the per-bin condition used in
  Section robust), median over seeds. Script experiments/diag_rooms_shat.py -> results/revision3_diag/rooms_shat.md.
- Text: the numbers are reported as a possible explanation of the R2 failures ('consistent with' if the fraction grows
  from room A to C; otherwise 'not explained'); no claim beyond that.

Note (2026-10-30, after review): the clock times in the headings are approximate; the commit times (1ca00bb 21:06,
the addendum in the commit before the run of diag_rooms_shat.py) are authoritative. Both were committed before the runs.
