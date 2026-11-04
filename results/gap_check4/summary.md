# Revision 10: Prop. rho check with the pure 1/b schedule (S8, M = 512, tuning seeds 300-309)

excess = ensemble-mean residual power - ensemble-mean residual power of the whole-run LS controller (oracle floor);
ratio = 10 log10(excess(method) / excess(exact growing-window LS)) over hop ranges (1 hop = 16 ms);
slope = least-squares slope of log10 excess vs log10 hop over hops 100-312 (exact 1/b decay = -1).
Prediction (results/gap_check/summary.md, rho_c median): ar1 +0.07 dB; harmonic infinite (eigenvalues < 1/2).

## ar1
| method | hops 1-8 | hops 8-32 | hops 32-100 | hops 100-312 | slope |
|---|---|---|---|---|---|
| exact LS (RLS lam 1) | +0.00 dB | +0.00 dB | +0.00 dB | +0.00 dB | +0.238 |
| pure 1/b schedule (V-SCHED) | +29.97 dB | +45.33 dB | +36.23 dB | +29.07 dB | -2.110 |
| FD-FxNLMS mu 0.2 | -1.00 dB | +8.03 dB | +6.47 dB | +5.39 dB | -2.331 |
| E-PCG (main) | -4.15 dB | -0.21 dB | +0.79 dB | +4.39 dB | -0.339 |

## harmonic
| method | hops 1-8 | hops 8-32 | hops 32-100 | hops 100-312 | slope |
|---|---|---|---|---|---|
| exact LS (RLS lam 1) | +0.00 dB | +0.00 dB | +0.00 dB | +0.00 dB | -0.433 |
| pure 1/b schedule (V-SCHED) | +37.50 dB | +48.07 dB | +45.84 dB | +45.17 dB | -0.779 |
| FD-FxNLMS mu 0.2 | +3.15 dB | +10.08 dB | +7.25 dB | +7.88 dB | -0.266 |
| E-PCG (main) | -1.98 dB | +0.71 dB | +0.90 dB | +4.31 dB | -0.033 |

## Pre-registered interpretation (REVISION_RULE_10 section 2)
- ar1: ratio over hops 100-312 +29.07 dB vs prediction +0.07 dB, difference +29.00 dB -> departure (more than 1 dB)
- harmonic: ratio 32-100 +45.84 -> 100-312 +45.17 dB (increase: False); slope -0.779 vs exact LS -0.433 (slower decay: False) -> departure

