# Revision 5: review N8 diagnostic (fixed 2026-10-31, before running)

Protocol scope (2026-10-31 11:07) for N8 of [internal rationale omitted]: is the deficit of
SFTF + det due to the prewindowed restart or to the FTF implementation?

- Run: 'R-RLS' with the selected RLS + det configuration (lambda 0.9999, delta 1e-2, warm) and the new flag
  det_prewindow = True (after a detection the regressor is zero before tau, as inside SFTF + det; default off, all other
  records unchanged). Cells S2 src 30cm, both noises, evaluation seeds 480-519 (80 runs), same det_events.
  Script experiments/diag_rls_prewindow.py -> results/revision5_diag/rls_prewindow.md.
- Compared with v2c records of RLS + det (covariance restart) and SFTF + det: median A1 per cell.

| outcome (both cells) | text |
|---|---|
| prewindowed RLS + det within 1 dB of SFTF + det | the deficit of SFTF + det is attributed to the prewindowed restart, not to the FTF |
| prewindowed RLS + det within 1 dB of RLS + det | the deficit is attributed to the FTF implementation / numerics (not the restart form) |
| otherwise (or the cells disagree) | numbers only; mechanism 'not isolated' stays |
