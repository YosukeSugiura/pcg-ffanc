# Gap check 2 (Statement A, empirical): excess over the oracle floor, S8, M = 512, tuning seeds 300-309

excess = ensemble-mean residual power - ensemble-mean residual power of the whole-run LS controller (oracle floor);
ratio = 10 log10(excess(method) / excess(exact growing-window LS)) over hop ranges (1 hop = 16 ms).

## ar1
| method | hops 1-8 | hops 8-32 | hops 32-100 | hops 100-312 |
|---|---|---|---|---|
| exact LS (RLS lam 1) | +0.00 dB | +0.00 dB | +0.00 dB | +0.00 dB |
| FD-FxNLMS mu 0.2 | -1.00 dB | +8.03 dB | +6.47 dB | +5.39 dB |
| FD-FxNLMS mu 0.5 | -0.48 dB | +5.79 dB | +4.81 dB | +8.02 dB |
| E-PCG (main) | -4.15 dB | -0.21 dB | +0.79 dB | +4.39 dB |

oracle floor (mean NR of the whole-run LS controller relative to the uncontrolled power): see curves.npz

## harmonic
| method | hops 1-8 | hops 8-32 | hops 32-100 | hops 100-312 |
|---|---|---|---|---|
| exact LS (RLS lam 1) | +0.00 dB | +0.00 dB | +0.00 dB | +0.00 dB |
| FD-FxNLMS mu 0.2 | +3.15 dB | +10.08 dB | +7.25 dB | +7.88 dB |
| FD-FxNLMS mu 0.5 | +1.41 dB | +5.84 dB | +8.65 dB | +11.74 dB |
| E-PCG (main) | -1.98 dB | +0.71 dB | +0.90 dB | +4.31 dB |

oracle floor (mean NR of the whole-run LS controller relative to the uncontrolled power): see curves.npz

