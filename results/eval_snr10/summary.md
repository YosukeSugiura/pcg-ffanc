# Final evaluation (evaluation seeds 480-519, M = 512, T = 5 s; rule docs/current/FINAL_EVAL_RULE.md)
Values: median (Q1, Q3) over the 40 seeds; failed runs: A1 = A2 = 0 dB, tau = 4 s (censored).

## Failures (runs out of 40)
| method | ar1 S8 | ar1 S2 | harmonic S8 | harmonic S2 |
|---|---|---|---|---|
| FD-FxNLMS | 0 | 0 | 0 | 0 |
| leaky FD-FxNLMS | 0 | 0 | 0 | 0 |
| convex FD-FxNLMS | 0 | 0 | 0 | 0 |
| FDKF | 0 | 0 | 0 | 0 |
| RLS | 0 | 0 | 0 | 0 |
| VFF-RLS | 0 | 0 | 0 | 0 |
| FD-FxNLMS + det | 0 | 0 | 0 | 0 |
| RLS + det | 0 | 0 | 0 | 0 |
| E-PCG | 0 | 0 | 0 | 0 |
| E-PCG bank | 0 | 0 | 0 | 0 |

## A1, noise = ar1
| method | S8 stationary | S2 src 30cm |
|---|---|---|
| FD-FxNLMS | -6.44 (-7.01, -5.78) | -7.78 (-8.39, -7.02) |
| leaky FD-FxNLMS | -6.31 (-7.00, -5.77) | -7.87 (-8.39, -7.20) |
| convex FD-FxNLMS | -6.28 (-7.21, -5.70) | -8.00 (-8.46, -7.11) |
| FDKF | -2.26 (-2.78, -1.72) | -7.57 (-8.02, -6.80) |
| RLS | -5.83 (-6.46, -4.20) | -7.95 (-8.50, -7.31) |
| VFF-RLS | -2.56 (-4.36, 0.12) | -7.73 (-8.41, -7.07) |
| FD-FxNLMS + det | -5.66 (-6.52, -4.74) | -7.35 (-8.19, -6.66) |
| RLS + det | -5.95 (-6.58, -4.31) | -7.62 (-8.05, -7.10) |
| E-PCG | -6.56 (-7.16, -5.91) | -8.28 (-8.64, -7.75) |
| E-PCG bank | -6.55 (-7.15, -5.91) | -8.01 (-8.46, -7.63) |

## A1, noise = harmonic
| method | S8 stationary | S2 src 30cm |
|---|---|---|
| FD-FxNLMS | -7.55 (-7.83, -7.35) | -6.15 (-6.82, -5.55) |
| leaky FD-FxNLMS | -7.56 (-7.85, -7.39) | -6.43 (-7.01, -5.86) |
| convex FD-FxNLMS | -7.38 (-7.71, -7.16) | -6.52 (-7.01, -6.14) |
| FDKF | -2.62 (-2.87, -2.37) | -5.57 (-6.26, -4.91) |
| RLS | -7.59 (-7.87, -7.45) | -5.73 (-6.54, -5.21) |
| VFF-RLS | -4.59 (-5.51, -3.66) | -5.28 (-6.15, -4.73) |
| FD-FxNLMS + det | -6.80 (-7.20, -6.52) | -5.22 (-6.33, -4.74) |
| RLS + det | -7.69 (-7.97, -7.55) | -7.93 (-8.44, -7.60) |
| E-PCG | -7.99 (-8.17, -7.72) | -8.02 (-8.53, -7.66) |
| E-PCG bank | -7.99 (-8.17, -7.72) | -8.09 (-8.52, -7.73) |

## A2, noise = ar1
| method | S8 stationary | S2 src 30cm |
|---|---|---|
| FD-FxNLMS | -9.45 (-9.61, -9.18) | -9.32 (-9.71, -9.03) |
| leaky FD-FxNLMS | -9.28 (-9.49, -9.03) | -9.19 (-9.58, -8.90) |
| convex FD-FxNLMS | -9.59 (-9.74, -9.31) | -9.43 (-9.80, -9.06) |
| FDKF | -9.31 (-9.46, -9.02) | -9.12 (-9.45, -8.86) |
| RLS | -9.38 (-9.51, -9.10) | -9.26 (-9.64, -8.97) |
| VFF-RLS | -9.52 (-9.65, -9.24) | -9.40 (-9.77, -9.09) |
| FD-FxNLMS + det | -9.62 (-9.78, -9.32) | -9.47 (-9.83, -9.13) |
| RLS + det | -9.81 (-9.94, -9.54) | -9.59 (-9.98, -9.33) |
| E-PCG | -9.54 (-9.69, -9.29) | -9.44 (-9.81, -9.15) |
| E-PCG bank | -9.86 (-9.98, -9.58) | -9.56 (-10.00, -9.35) |

## A2, noise = harmonic
| method | S8 stationary | S2 src 30cm |
|---|---|---|
| FD-FxNLMS | -9.67 (-9.76, -9.57) | -9.57 (-9.93, -9.27) |
| leaky FD-FxNLMS | -9.52 (-9.59, -9.41) | -9.43 (-9.80, -9.14) |
| convex FD-FxNLMS | -9.90 (-9.98, -9.82) | -9.80 (-10.14, -9.43) |
| FDKF | -9.73 (-9.83, -9.63) | -9.52 (-9.85, -9.20) |
| RLS | -9.82 (-9.93, -9.76) | -9.76 (-10.14, -9.47) |
| VFF-RLS | -9.97 (-10.07, -9.91) | -9.88 (-10.26, -9.58) |
| FD-FxNLMS + det | -9.96 (-10.02, -9.85) | -9.77 (-10.12, -9.39) |
| RLS + det | -10.25 (-10.34, -10.19) | -10.11 (-10.49, -9.83) |
| E-PCG | -10.09 (-10.17, -10.01) | -10.01 (-10.39, -9.72) |
| E-PCG bank | -10.32 (-10.38, -10.23) | -10.14 (-10.52, -9.86) |

## tau9, noise = ar1
| method | S8 stationary | S2 src 30cm |
|---|---|---|
| FD-FxNLMS | 0.57 (0.50, 0.69) | 0.58 (0.47, 0.68) |
| leaky FD-FxNLMS | 0.58 (0.51, 0.71) | 0.57 (0.47, 0.69) |
| convex FD-FxNLMS | 0.56 (0.51, 0.69) | 0.51 (0.42, 0.65) |
| FDKF | 1.22 (1.08, 1.46) | 0.63 (0.50, 0.91) |
| RLS | 0.54 (0.46, 0.62) | 0.54 (0.42, 0.67) |
| VFF-RLS | 0.54 (0.49, 0.66) | 0.57 (0.47, 0.68) |
| FD-FxNLMS + det | 0.71 (0.60, 0.86) | 0.68 (0.50, 0.88) |
| RLS + det | 0.53 (0.43, 0.58) | 0.51 (0.42, 0.66) |
| E-PCG | 0.53 (0.45, 0.60) | 0.48 (0.39, 0.64) |
| E-PCG bank | 0.54 (0.45, 0.62) | 0.54 (0.40, 0.68) |

## tau9, noise = harmonic
| method | S8 stationary | S2 src 30cm |
|---|---|---|
| FD-FxNLMS | 0.35 (0.32, 0.37) | 0.62 (0.52, 0.71) |
| leaky FD-FxNLMS | 0.35 (0.32, 0.39) | 0.62 (0.50, 0.74) |
| convex FD-FxNLMS | 0.41 (0.33, 0.51) | 0.57 (0.45, 0.70) |
| FDKF | 1.71 (1.59, 1.79) | 0.78 (0.65, 1.07) |
| RLS | 0.35 (0.34, 0.37) | 0.60 (0.54, 0.66) |
| VFF-RLS | 0.41 (0.38, 0.45) | 0.68 (0.61, 0.73) |
| FD-FxNLMS + det | 0.54 (0.48, 0.58) | 0.76 (0.68, 0.92) |
| RLS + det | 0.35 (0.34, 0.37) | 0.36 (0.32, 0.41) |
| E-PCG | 0.34 (0.30, 0.37) | 0.35 (0.31, 0.42) |
| E-PCG bank | 0.34 (0.30, 0.37) | 0.33 (0.31, 0.40) |

## tau12, noise = ar1
| method | S8 stationary | S2 src 30cm |
|---|---|---|
| FD-FxNLMS | 4.00 (4.00, 4.00) | 4.00 (4.00, 4.00) |
| leaky FD-FxNLMS | 4.00 (4.00, 4.00) | 4.00 (4.00, 4.00) |
| convex FD-FxNLMS | 4.00 (4.00, 4.00) | 4.00 (4.00, 4.00) |
| FDKF | 4.00 (4.00, 4.00) | 4.00 (4.00, 4.00) |
| RLS | 4.00 (4.00, 4.00) | 4.00 (4.00, 4.00) |
| VFF-RLS | 4.00 (4.00, 4.00) | 4.00 (4.00, 4.00) |
| FD-FxNLMS + det | 4.00 (4.00, 4.00) | 4.00 (4.00, 4.00) |
| RLS + det | 4.00 (4.00, 4.00) | 4.00 (4.00, 4.00) |
| E-PCG | 4.00 (4.00, 4.00) | 4.00 (4.00, 4.00) |
| E-PCG bank | 4.00 (4.00, 4.00) | 4.00 (4.00, 4.00) |

## tau12, noise = harmonic
| method | S8 stationary | S2 src 30cm |
|---|---|---|
| FD-FxNLMS | 4.00 (4.00, 4.00) | 4.00 (4.00, 4.00) |
| leaky FD-FxNLMS | 4.00 (4.00, 4.00) | 4.00 (4.00, 4.00) |
| convex FD-FxNLMS | 4.00 (4.00, 4.00) | 4.00 (4.00, 4.00) |
| FDKF | 4.00 (4.00, 4.00) | 4.00 (4.00, 4.00) |
| RLS | 4.00 (4.00, 4.00) | 4.00 (4.00, 4.00) |
| VFF-RLS | 4.00 (4.00, 4.00) | 4.00 (4.00, 4.00) |
| FD-FxNLMS + det | 4.00 (4.00, 4.00) | 4.00 (4.00, 4.00) |
| RLS + det | 4.00 (4.00, 4.00) | 4.00 (4.00, 4.00) |
| E-PCG | 4.00 (4.00, 4.00) | 4.00 (4.00, 4.00) |
| E-PCG bank | 4.00 (4.00, 4.00) | 4.00 (4.00, 4.00) |

## E-PCG vs baselines (Wilcoxon pratt on seeds; Holm over 64)
| baseline | noise | cell | med dA1 | p_Holm A1 | med dA2 | p_Holm A2 | label |
|---|---|---|---|---|---|---|---|
| FD-FxNLMS | ar1 | S8 stationary | +0.04 | 1 | -0.10 | 1.16e-10 | - |
| FD-FxNLMS | ar1 | S2 src 30cm | -0.40 | 2.4e-07 | -0.11 | 1.16e-10 | - |
| FD-FxNLMS | harmonic | S8 stationary | -0.38 | 4.88e-05 | -0.43 | 1.16e-10 | - |
| FD-FxNLMS | harmonic | S2 src 30cm | -1.67 | 7.13e-10 | -0.46 | 1.16e-10 | win |
| leaky FD-FxNLMS | ar1 | S8 stationary | -0.02 | 1 | -0.23 | 1.16e-10 | - |
| leaky FD-FxNLMS | ar1 | S2 src 30cm | -0.25 | 1.23e-06 | -0.25 | 1.16e-10 | - |
| leaky FD-FxNLMS | harmonic | S8 stationary | -0.38 | 4.88e-05 | -0.58 | 1.16e-10 | win |
| leaky FD-FxNLMS | harmonic | S2 src 30cm | -1.45 | 7.13e-10 | -0.60 | 1.16e-10 | win |
| convex FD-FxNLMS | ar1 | S8 stationary | +0.01 | 1 | +0.04 | 5.92e-05 | - |
| convex FD-FxNLMS | ar1 | S2 src 30cm | -0.24 | 2.09e-06 | -0.03 | 4.52e-06 | - |
| convex FD-FxNLMS | harmonic | S8 stationary | -0.52 | 3.87e-06 | -0.19 | 1.16e-10 | - |
| convex FD-FxNLMS | harmonic | S2 src 30cm | -1.34 | 4.6e-09 | -0.28 | 1.16e-10 | win |
| FDKF | ar1 | S8 stationary | -4.19 | 1.16e-10 | -0.23 | 1.16e-10 | win |
| FDKF | ar1 | S2 src 30cm | -0.64 | 1.16e-10 | -0.32 | 1.16e-10 | - |
| FDKF | harmonic | S8 stationary | -5.35 | 1.16e-10 | -0.34 | 1.16e-10 | win |
| FDKF | harmonic | S2 src 30cm | -2.11 | 1.16e-10 | -0.56 | 1.16e-10 | win |
| RLS | ar1 | S8 stationary | -0.56 | 0.000106 | -0.17 | 1.16e-10 | - |
| RLS | ar1 | S2 src 30cm | -0.17 | 0.000167 | -0.18 | 1.16e-10 | - |
| RLS | harmonic | S8 stationary | -0.25 | 0.000343 | -0.25 | 1.16e-10 | - |
| RLS | harmonic | S2 src 30cm | -1.91 | 8.64e-10 | -0.25 | 1.16e-10 | win |
| VFF-RLS | ar1 | S8 stationary | -3.35 | 1.16e-10 | -0.04 | 1.16e-10 | win |
| VFF-RLS | ar1 | S2 src 30cm | -0.30 | 5.23e-06 | -0.05 | 1.16e-10 | - |
| VFF-RLS | harmonic | S8 stationary | -3.25 | 1.16e-10 | -0.11 | 1.16e-10 | win |
| VFF-RLS | harmonic | S2 src 30cm | -2.37 | 7.13e-10 | -0.15 | 1.16e-10 | win |
| FD-FxNLMS + det | ar1 | S8 stationary | -0.70 | 0.00136 | +0.08 | 8.28e-09 | - |
| FD-FxNLMS + det | ar1 | S2 src 30cm | -0.66 | 3.06e-09 | +0.01 | 1 | - |
| FD-FxNLMS + det | harmonic | S8 stationary | -1.14 | 4.82e-08 | -0.14 | 1.16e-10 | win |
| FD-FxNLMS + det | harmonic | S2 src 30cm | -2.34 | 3.69e-10 | -0.30 | 1.16e-10 | win |
| RLS + det | ar1 | S8 stationary | -0.43 | 0.00136 | +0.25 | 1.16e-10 | - |
| RLS + det | ar1 | S2 src 30cm | -0.58 | 2.73e-10 | +0.17 | 1.16e-10 | - |
| RLS + det | harmonic | S8 stationary | -0.13 | 0.0244 | +0.17 | 1.16e-10 | - |
| RLS + det | harmonic | S2 src 30cm | -0.05 | 0.00214 | +0.11 | 1.16e-10 | - |

Counts (E-PCG): win 13, loss 0, mixed 0, none 19 (of 32)

## E-PCG bank vs baselines (Wilcoxon pratt on seeds; Holm over 64)
| baseline | noise | cell | med dA1 | p_Holm A1 | med dA2 | p_Holm A2 | label |
|---|---|---|---|---|---|---|---|
| FD-FxNLMS | ar1 | S8 stationary | +0.05 | 1 | -0.40 | 1.16e-10 | - |
| FD-FxNLMS | ar1 | S2 src 30cm | -0.09 | 0.266 | -0.30 | 1.16e-10 | - |
| FD-FxNLMS | harmonic | S8 stationary | -0.38 | 6.28e-05 | -0.65 | 1.16e-10 | win |
| FD-FxNLMS | harmonic | S2 src 30cm | -1.84 | 1.16e-10 | -0.60 | 1.16e-10 | win |
| leaky FD-FxNLMS | ar1 | S8 stationary | -0.02 | 1 | -0.53 | 1.16e-10 | win |
| leaky FD-FxNLMS | ar1 | S2 src 30cm | +0.00 | 1 | -0.44 | 1.16e-10 | - |
| leaky FD-FxNLMS | harmonic | S8 stationary | -0.38 | 6.47e-05 | -0.79 | 1.16e-10 | win |
| leaky FD-FxNLMS | harmonic | S2 src 30cm | -1.53 | 1.16e-10 | -0.74 | 1.16e-10 | win |
| convex FD-FxNLMS | ar1 | S8 stationary | +0.01 | 1 | -0.27 | 1.16e-10 | - |
| convex FD-FxNLMS | ar1 | S2 src 30cm | -0.03 | 1 | -0.22 | 1.16e-10 | - |
| convex FD-FxNLMS | harmonic | S8 stationary | -0.52 | 4.55e-06 | -0.41 | 1.16e-10 | - |
| convex FD-FxNLMS | harmonic | S2 src 30cm | -1.44 | 1.16e-10 | -0.42 | 1.16e-10 | win |
| FDKF | ar1 | S8 stationary | -4.18 | 1.16e-10 | -0.52 | 1.16e-10 | win |
| FDKF | ar1 | S2 src 30cm | -0.48 | 1.82e-05 | -0.51 | 1.16e-10 | win |
| FDKF | harmonic | S8 stationary | -5.35 | 1.16e-10 | -0.57 | 1.16e-10 | win |
| FDKF | harmonic | S2 src 30cm | -2.23 | 1.16e-10 | -0.69 | 1.16e-10 | win |
| RLS | ar1 | S8 stationary | -0.56 | 0.000154 | -0.48 | 1.16e-10 | - |
| RLS | ar1 | S2 src 30cm | +0.05 | 1 | -0.37 | 1.16e-10 | - |
| RLS | harmonic | S8 stationary | -0.25 | 0.000496 | -0.48 | 1.16e-10 | - |
| RLS | harmonic | S2 src 30cm | -2.00 | 1.16e-10 | -0.39 | 1.16e-10 | win |
| VFF-RLS | ar1 | S8 stationary | -3.35 | 1.16e-10 | -0.34 | 1.16e-10 | win |
| VFF-RLS | ar1 | S2 src 30cm | -0.08 | 0.805 | -0.24 | 1.16e-10 | - |
| VFF-RLS | harmonic | S8 stationary | -3.26 | 1.16e-10 | -0.33 | 1.16e-10 | win |
| VFF-RLS | harmonic | S2 src 30cm | -2.45 | 1.16e-10 | -0.28 | 1.16e-10 | win |
| FD-FxNLMS + det | ar1 | S8 stationary | -0.70 | 0.00187 | -0.23 | 1.16e-10 | - |
| FD-FxNLMS + det | ar1 | S2 src 30cm | -0.40 | 0.000496 | -0.18 | 1.16e-10 | - |
| FD-FxNLMS + det | harmonic | S8 stationary | -1.14 | 5.05e-08 | -0.37 | 1.16e-10 | win |
| FD-FxNLMS + det | harmonic | S2 src 30cm | -2.65 | 1.16e-10 | -0.44 | 1.16e-10 | win |
| RLS + det | ar1 | S8 stationary | -0.43 | 0.00193 | -0.05 | 1.16e-10 | - |
| RLS + det | ar1 | S2 src 30cm | -0.41 | 4.96e-07 | -0.02 | 0.000429 | - |
| RLS + det | harmonic | S8 stationary | -0.13 | 0.0438 | -0.05 | 1.16e-10 | - |
| RLS + det | harmonic | S2 src 30cm | -0.16 | 0.000251 | -0.02 | 1.16e-10 | - |

Counts (E-PCG bank): win 16, loss 0, mixed 0, none 16 (of 32)

## E-PCG bank - E-PCG (main) (Holm over 8)
| noise | cell | key | median d | p_Holm |
|---|---|---|---|---|
| ar1 | S8 stationary | A1 | +0.00 | 0.000324 |
| ar1 | S8 stationary | A2 | -0.29 | 1.46e-11 |
| ar1 | S2 src 30cm | A1 | +0.18 | 1.66e-05 |
| ar1 | S2 src 30cm | A2 | -0.19 | 1.46e-11 |
| harmonic | S8 stationary | A1 | +0.00 | 0.485 |
| harmonic | S8 stationary | A2 | -0.22 | 1.46e-11 |
| harmonic | S2 src 30cm | A1 | -0.15 | 0.00738 |
| harmonic | S2 src 30cm | A2 | -0.14 | 1.46e-11 |

## Reach fraction at level -9 dB (tau <= t; t in [0.3, 0.5, 1.0, 2.0, 3.0, 4.0] s)
| method | noise | cell | t=0.3 | t=0.5 | t=1.0 | t=2.0 | t=3.0 | t=4.0 |
|---|---|---|---|---|---|---|---|---|
| FD-FxNLMS | ar1 | S8 stationary | 0.00 | 0.25 | 0.95 | 1.00 | 1.00 | 1.00 |
| FD-FxNLMS | ar1 | S2 src 30cm | 0.10 | 0.35 | 0.95 | 1.00 | 1.00 | 1.00 |
| FD-FxNLMS | harmonic | S8 stationary | 0.05 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 |
| FD-FxNLMS | harmonic | S2 src 30cm | 0.00 | 0.17 | 0.95 | 1.00 | 1.00 | 1.00 |
| leaky FD-FxNLMS | ar1 | S8 stationary | 0.00 | 0.23 | 0.93 | 1.00 | 1.00 | 1.00 |
| leaky FD-FxNLMS | ar1 | S2 src 30cm | 0.10 | 0.40 | 0.95 | 1.00 | 1.00 | 1.00 |
| leaky FD-FxNLMS | harmonic | S8 stationary | 0.05 | 0.97 | 1.00 | 1.00 | 1.00 | 1.00 |
| leaky FD-FxNLMS | harmonic | S2 src 30cm | 0.00 | 0.23 | 0.95 | 1.00 | 1.00 | 1.00 |
| convex FD-FxNLMS | ar1 | S8 stationary | 0.00 | 0.25 | 0.88 | 1.00 | 1.00 | 1.00 |
| convex FD-FxNLMS | ar1 | S2 src 30cm | 0.10 | 0.47 | 0.93 | 1.00 | 1.00 | 1.00 |
| convex FD-FxNLMS | harmonic | S8 stationary | 0.00 | 0.72 | 1.00 | 1.00 | 1.00 | 1.00 |
| convex FD-FxNLMS | harmonic | S2 src 30cm | 0.00 | 0.30 | 0.93 | 1.00 | 1.00 | 1.00 |
| FDKF | ar1 | S8 stationary | 0.00 | 0.00 | 0.12 | 0.95 | 1.00 | 1.00 |
| FDKF | ar1 | S2 src 30cm | 0.03 | 0.23 | 0.90 | 1.00 | 1.00 | 1.00 |
| FDKF | harmonic | S8 stationary | 0.00 | 0.00 | 0.00 | 1.00 | 1.00 | 1.00 |
| FDKF | harmonic | S2 src 30cm | 0.00 | 0.05 | 0.65 | 1.00 | 1.00 | 1.00 |
| RLS | ar1 | S8 stationary | 0.00 | 0.42 | 0.97 | 1.00 | 1.00 | 1.00 |
| RLS | ar1 | S2 src 30cm | 0.10 | 0.45 | 0.95 | 1.00 | 1.00 | 1.00 |
| RLS | harmonic | S8 stationary | 0.00 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 |
| RLS | harmonic | S2 src 30cm | 0.00 | 0.20 | 1.00 | 1.00 | 1.00 | 1.00 |
| VFF-RLS | ar1 | S8 stationary | 0.00 | 0.35 | 1.00 | 1.00 | 1.00 | 1.00 |
| VFF-RLS | ar1 | S2 src 30cm | 0.10 | 0.38 | 0.95 | 1.00 | 1.00 | 1.00 |
| VFF-RLS | harmonic | S8 stationary | 0.00 | 0.95 | 1.00 | 1.00 | 1.00 | 1.00 |
| VFF-RLS | harmonic | S2 src 30cm | 0.00 | 0.15 | 1.00 | 1.00 | 1.00 | 1.00 |
| FD-FxNLMS + det | ar1 | S8 stationary | 0.00 | 0.12 | 0.90 | 1.00 | 1.00 | 1.00 |
| FD-FxNLMS + det | ar1 | S2 src 30cm | 0.07 | 0.25 | 0.88 | 1.00 | 1.00 | 1.00 |
| FD-FxNLMS + det | harmonic | S8 stationary | 0.03 | 0.30 | 1.00 | 1.00 | 1.00 | 1.00 |
| FD-FxNLMS + det | harmonic | S2 src 30cm | 0.00 | 0.12 | 0.78 | 1.00 | 1.00 | 1.00 |
| RLS + det | ar1 | S8 stationary | 0.00 | 0.45 | 1.00 | 1.00 | 1.00 | 1.00 |
| RLS + det | ar1 | S2 src 30cm | 0.03 | 0.45 | 0.95 | 1.00 | 1.00 | 1.00 |
| RLS + det | harmonic | S8 stationary | 0.00 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 |
| RLS + det | harmonic | S2 src 30cm | 0.15 | 0.93 | 1.00 | 1.00 | 1.00 | 1.00 |
| E-PCG | ar1 | S8 stationary | 0.00 | 0.42 | 1.00 | 1.00 | 1.00 | 1.00 |
| E-PCG | ar1 | S2 src 30cm | 0.12 | 0.53 | 0.95 | 1.00 | 1.00 | 1.00 |
| E-PCG | harmonic | S8 stationary | 0.05 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 |
| E-PCG | harmonic | S2 src 30cm | 0.20 | 0.88 | 1.00 | 1.00 | 1.00 | 1.00 |
| E-PCG bank | ar1 | S8 stationary | 0.00 | 0.40 | 1.00 | 1.00 | 1.00 | 1.00 |
| E-PCG bank | ar1 | S2 src 30cm | 0.07 | 0.40 | 0.95 | 1.00 | 1.00 | 1.00 |
| E-PCG bank | harmonic | S8 stationary | 0.05 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 |
| E-PCG bank | harmonic | S2 src 30cm | 0.20 | 0.88 | 1.00 | 1.00 | 1.00 | 1.00 |

## Reach fraction at level -12 dB (tau <= t; t in [0.3, 0.5, 1.0, 2.0, 3.0, 4.0] s)
| method | noise | cell | t=0.3 | t=0.5 | t=1.0 | t=2.0 | t=3.0 | t=4.0 |
|---|---|---|---|---|---|---|---|---|
| FD-FxNLMS | ar1 | S8 stationary | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| FD-FxNLMS | ar1 | S2 src 30cm | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.03 |
| FD-FxNLMS | harmonic | S8 stationary | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| FD-FxNLMS | harmonic | S2 src 30cm | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| leaky FD-FxNLMS | ar1 | S8 stationary | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| leaky FD-FxNLMS | ar1 | S2 src 30cm | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.03 |
| leaky FD-FxNLMS | harmonic | S8 stationary | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| leaky FD-FxNLMS | harmonic | S2 src 30cm | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| convex FD-FxNLMS | ar1 | S8 stationary | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| convex FD-FxNLMS | ar1 | S2 src 30cm | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.03 |
| convex FD-FxNLMS | harmonic | S8 stationary | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| convex FD-FxNLMS | harmonic | S2 src 30cm | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| FDKF | ar1 | S8 stationary | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| FDKF | ar1 | S2 src 30cm | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.03 |
| FDKF | harmonic | S8 stationary | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| FDKF | harmonic | S2 src 30cm | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| RLS | ar1 | S8 stationary | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| RLS | ar1 | S2 src 30cm | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.03 |
| RLS | harmonic | S8 stationary | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| RLS | harmonic | S2 src 30cm | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| VFF-RLS | ar1 | S8 stationary | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| VFF-RLS | ar1 | S2 src 30cm | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.03 |
| VFF-RLS | harmonic | S8 stationary | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| VFF-RLS | harmonic | S2 src 30cm | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| FD-FxNLMS + det | ar1 | S8 stationary | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| FD-FxNLMS + det | ar1 | S2 src 30cm | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.03 |
| FD-FxNLMS + det | harmonic | S8 stationary | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| FD-FxNLMS + det | harmonic | S2 src 30cm | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| RLS + det | ar1 | S8 stationary | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| RLS + det | ar1 | S2 src 30cm | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.03 |
| RLS + det | harmonic | S8 stationary | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| RLS + det | harmonic | S2 src 30cm | 0.00 | 0.00 | 0.00 | 0.03 | 0.03 | 0.03 |
| E-PCG | ar1 | S8 stationary | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| E-PCG | ar1 | S2 src 30cm | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.03 |
| E-PCG | harmonic | S8 stationary | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| E-PCG | harmonic | S2 src 30cm | 0.00 | 0.00 | 0.00 | 0.03 | 0.03 | 0.03 |
| E-PCG bank | ar1 | S8 stationary | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| E-PCG bank | ar1 | S2 src 30cm | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.05 |
| E-PCG bank | harmonic | S8 stationary | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| E-PCG bank | harmonic | S2 src 30cm | 0.00 | 0.00 | 0.00 | 0.03 | 0.03 | 0.03 |

## Cost of the proposed methods (mean flop_hist / H = flops per sample; S8 / change cells)
| method | S8 | change cells |
|---|---|---|
| E-PCG | 7830 | 11295 |
| E-PCG bank | 14056 | 17082 |

## Diagnostics
- records 1600; unparsable 0; stale 0; duplicates 720 (differing 0)
- win / loss: each metric with its own Holm-adjusted p (A1 with p_A1, A2 with p_A2), thresholds 1 dB (A1) / 0.5 dB (A2)
- curves are ensemble means of the seed-summed powers: one failed run can dominate a curve (read with the failure table)
- cost of the baselines: analytic counts in the cost table (Step 6), not measured here
- runs stopped early (completed with no control): 0
