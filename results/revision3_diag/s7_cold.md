# Review N6 diagnostic: cold vs warm restart of RLS + det, S7 AR(1), evaluation seeds (REVISION_RULE_3.md)

| method | median A1 (dB) | median A2 (dB) | failures |
|---|---|---|---|
| E-PCG | -10.99 | -17.28 | 0 |
| RLS + det (warm, selected) | -6.06 | -17.62 | 0 |
| RLS + det (cold, cfg 0) | -8.80 | -17.63 | 0 |
- E-PCG - RLS + det (warm, selected): A1 median paired -4.71 dB (p 3.6e-12), A2 +0.24 dB (p 1.8e-12)
- E-PCG - RLS + det (cold, cfg 0): A1 median paired -2.89 dB (p 1.2e-09), A2 +0.28 dB (p 1.8e-12)
- interpretation (REVISION_RULE_3): row 2 ((-3, -1] dB)

| hop | median samples since tau | E-PCG NR | warm NR | cold NR |
|---|---|---|---|---|
| 62 | 68 | -0.23 | -0.22 | -0.22 |
| 63 | 196 | 0.51 | 3.36 | 0.52 |
| 64 | 324 | -6.16 | 1.72 | -1.07 |
| 65 | 452 | -10.32 | 1.11 | -1.45 |
| 66 | 580 | -12.37 | 0.99 | -0.43 |
| 67 | 708 | -12.23 | -1.82 | -3.85 |
| 68 | 836 | -13.17 | -10.16 | -10.54 |
| 69 | 964 | -13.02 | -11.27 | -11.68 |
| 70 | 1092 | -13.47 | -12.81 | -13.13 |
| 71 | 1220 | -14.69 | -14.37 | -14.75 |
| 72 | 1348 | -14.37 | -14.12 | -14.49 |
- warm: share of the excess residual energy over E-PCG (hops 62-79) at n <= M: 67%, n <= 580 (~1.1 M): 89%
- cold: share of the excess residual energy over E-PCG (hops 62-79) at n <= M: 50%, n <= 580 (~1.1 M): 86%
