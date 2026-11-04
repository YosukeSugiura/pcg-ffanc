# Final evaluation (evaluation seeds 480-519, M = 512, T = 5 s; rule docs/current/FINAL_EVAL_RULE.md)
Values: median (Q1, Q3) over the 40 seeds; failed runs: A1 = A2 = 0 dB, tau = 4 s (censored).

## Failures (runs out of 40)
| method | ar1 S8 | ar1 S2 | ar1 S5 | ar1 R2 | harmonic S8 | harmonic S2 | harmonic S5 | harmonic R2 |
|---|---|---|---|---|---|---|---|---|
| FD-FxNLMS | 0 | 0 | 0 | 27 | 2 | 4 | 4 | 39 |
| leaky FD-FxNLMS | 0 | 0 | 0 | 26 | 6 | 6 | 7 | 39 |
| convex FD-FxNLMS | 0 | 0 | 0 | 27 | 0 | 0 | 0 | 39 |
| FDKF | 0 | 0 | 0 | 17 | 3 | 2 | 2 | 37 |
| RLS | 0 | 0 | 0 | 38 | 1 | 0 | 0 | 38 |
| VFF-RLS | 0 | 0 | 0 | 38 | 1 | 0 | 0 | 38 |
| FD-FxNLMS + det | 0 | 0 | 0 | 13 | 0 | 0 | 0 | 38 |
| RLS + det | 0 | 0 | 0 | 9 | 0 | 0 | 0 | 37 |
| E-PCG | 0 | 0 | 0 | 26 | 0 | 0 | 0 | 39 |
| E-PCG bank | 0 | 0 | 0 | 24 | 6 | 2 | 1 | 38 |

## A1, noise = ar1
| method | S8 stationary | S2 src 30cm | S5 src 30cm cont | R2 rig 30cm |
|---|---|---|---|---|
| FD-FxNLMS | -4.84 (-5.27, -4.13) | -6.43 (-6.89, -5.62) | -6.26 (-7.05, -5.86) | 0.00 (-5.31, 0.00) |
| leaky FD-FxNLMS | -4.52 (-5.15, -3.59) | -6.25 (-6.59, -5.42) | -6.02 (-6.66, -5.61) | 0.00 (-5.18, 0.00) |
| convex FD-FxNLMS | -4.20 (-5.01, -3.61) | -5.99 (-6.69, -5.40) | -5.94 (-6.73, -5.49) | 0.00 (-3.91, 0.00) |
| FDKF | -1.51 (-2.21, -0.69) | -5.39 (-6.40, -4.99) | -5.46 (-6.27, -5.03) | -2.86 (-4.78, 0.00) |
| RLS | -3.88 (-5.10, -2.10) | -7.43 (-8.40, -6.44) | -7.41 (-8.49, -6.61) | 0.00 (0.00, 0.00) |
| VFF-RLS | -1.62 (-3.52, 1.61) | -7.45 (-8.41, -6.44) | -7.42 (-8.51, -6.64) | 0.00 (0.00, 0.00) |
| FD-FxNLMS + det | -4.67 (-5.29, -4.24) | -6.12 (-6.72, -5.49) | -6.22 (-6.92, -5.79) | -4.09 (-5.98, 0.00) |
| RLS + det | -4.05 (-5.31, -2.22) | -6.86 (-7.97, -6.03) | -7.46 (-8.46, -6.61) | -4.94 (-6.49, -0.90) |
| E-PCG | -4.76 (-5.90, -3.46) | -7.19 (-8.22, -6.28) | -7.47 (-8.39, -6.67) | 0.00 (-5.06, 0.00) |
| E-PCG bank | -4.70 (-5.89, -3.40) | -6.84 (-8.00, -6.00) | -7.41 (-8.46, -6.52) | 0.00 (-4.76, 0.00) |

## A1, noise = harmonic
| method | S8 stationary | S2 src 30cm | S5 src 30cm cont | R2 rig 30cm |
|---|---|---|---|---|
| FD-FxNLMS | -4.32 (-5.19, -2.88) | -4.21 (-5.21, -2.03) | -5.52 (-6.15, -3.13) | 0.00 (0.00, 0.00) |
| leaky FD-FxNLMS | -3.92 (-4.88, -0.83) | -4.10 (-5.25, -1.34) | -4.81 (-6.37, -0.74) | 0.00 (0.00, 0.00) |
| convex FD-FxNLMS | -4.99 (-5.97, -3.29) | -4.76 (-5.91, -3.42) | -5.66 (-7.11, -3.96) | 0.00 (0.00, 0.00) |
| FDKF | -1.87 (-2.17, -1.30) | -3.74 (-4.63, -2.15) | -5.47 (-6.55, -2.96) | 0.00 (0.00, 0.00) |
| RLS | -3.57 (-4.95, -1.93) | -5.84 (-6.57, -4.39) | -6.86 (-7.63, -4.57) | 0.00 (0.00, 0.00) |
| VFF-RLS | 1.18 (-1.03, 2.52) | -5.69 (-6.37, -4.34) | -6.73 (-7.48, -4.59) | 0.00 (0.00, 0.00) |
| FD-FxNLMS + det | -3.97 (-4.64, -2.52) | -3.89 (-4.45, -2.84) | -5.05 (-5.72, -3.52) | 0.00 (0.00, 0.00) |
| RLS + det | -3.69 (-5.07, -1.98) | -6.20 (-9.07, -2.38) | -6.30 (-8.21, -2.89) | 0.00 (0.00, 0.00) |
| E-PCG | -5.52 (-7.30, -3.36) | -4.19 (-5.93, -2.15) | -5.48 (-7.06, -3.30) | 0.00 (0.00, 0.00) |
| E-PCG bank | -5.22 (-7.32, -1.48) | -3.98 (-6.10, -1.17) | -5.60 (-8.25, -1.90) | 0.00 (0.00, 0.00) |

## A2, noise = ar1
| method | S8 stationary | S2 src 30cm | S5 src 30cm cont | R2 rig 30cm |
|---|---|---|---|---|
| FD-FxNLMS | -6.57 (-8.17, -6.13) | -6.62 (-7.80, -6.07) | -6.65 (-7.81, -6.04) | 0.00 (-3.81, 0.00) |
| leaky FD-FxNLMS | -6.54 (-7.63, -6.06) | -6.40 (-7.42, -5.96) | -6.43 (-7.43, -5.98) | 0.00 (-4.42, 0.00) |
| convex FD-FxNLMS | -6.69 (-8.16, -6.32) | -6.66 (-7.72, -6.21) | -6.66 (-7.72, -6.20) | 0.00 (-3.59, 0.00) |
| FDKF | -6.06 (-7.41, -5.30) | -5.78 (-7.28, -5.39) | -5.79 (-7.33, -5.38) | -2.43 (-3.97, 0.00) |
| RLS | -8.30 (-9.39, -7.46) | -8.15 (-9.60, -7.27) | -8.15 (-9.64, -7.25) | 0.00 (0.00, 0.00) |
| VFF-RLS | -8.35 (-9.43, -7.50) | -8.20 (-9.66, -7.31) | -8.19 (-9.70, -7.29) | 0.00 (0.00, 0.00) |
| FD-FxNLMS + det | -6.71 (-7.84, -6.29) | -6.85 (-7.87, -6.23) | -6.79 (-7.75, -6.20) | -3.69 (-5.90, 0.00) |
| RLS + det | -8.62 (-9.81, -7.88) | -8.50 (-9.95, -7.55) | -8.43 (-9.92, -7.44) | -4.96 (-6.70, -3.29) |
| E-PCG | -8.40 (-9.61, -7.62) | -8.38 (-9.86, -7.35) | -8.33 (-9.88, -7.31) | 0.00 (-3.81, 0.00) |
| E-PCG bank | -8.42 (-9.67, -7.72) | -8.25 (-9.77, -7.19) | -8.14 (-9.75, -7.14) | 0.00 (-4.55, 0.00) |

## A2, noise = harmonic
| method | S8 stationary | S2 src 30cm | S5 src 30cm cont | R2 rig 30cm |
|---|---|---|---|---|
| FD-FxNLMS | -8.65 (-11.49, -4.05) | -7.61 (-10.67, -3.70) | -7.19 (-10.05, -3.19) | 0.00 (0.00, 0.00) |
| leaky FD-FxNLMS | -7.00 (-10.66, -1.96) | -6.94 (-9.70, -1.83) | -6.13 (-9.34, -1.60) | 0.00 (0.00, 0.00) |
| convex FD-FxNLMS | -9.98 (-12.18, -5.14) | -8.88 (-11.01, -4.98) | -8.72 (-10.65, -4.82) | 0.00 (0.00, 0.00) |
| FDKF | -7.63 (-10.75, -2.56) | -7.12 (-9.90, -2.77) | -6.96 (-9.67, -2.71) | 0.00 (0.00, 0.00) |
| RLS | -10.80 (-13.63, -6.49) | -10.51 (-13.64, -6.22) | -10.33 (-13.05, -6.17) | 0.00 (0.00, 0.00) |
| VFF-RLS | -10.90 (-13.76, -6.56) | -10.60 (-13.70, -6.31) | -10.39 (-13.04, -6.24) | 0.00 (0.00, 0.00) |
| FD-FxNLMS + det | -9.95 (-12.02, -5.41) | -8.22 (-10.43, -5.36) | -7.99 (-10.06, -5.12) | 0.00 (0.00, 0.00) |
| RLS + det | -11.40 (-14.24, -7.31) | -11.05 (-14.09, -6.90) | -10.63 (-12.92, -6.64) | 0.00 (0.00, 0.00) |
| E-PCG | -11.19 (-14.09, -7.00) | -10.87 (-13.90, -6.77) | -10.39 (-12.81, -6.58) | 0.00 (0.00, 0.00) |
| E-PCG bank | -11.15 (-14.15, -5.78) | -10.87 (-14.05, -6.24) | -10.44 (-13.37, -5.66) | 0.00 (0.00, 0.00) |

## tau9, noise = ar1
| method | S8 stationary | S2 src 30cm | S5 src 30cm cont | R2 rig 30cm |
|---|---|---|---|---|
| FD-FxNLMS | 4.00 (0.95, 4.00) | 3.55 (1.34, 4.00) | 2.95 (0.73, 4.00) | 4.00 (4.00, 4.00) |
| leaky FD-FxNLMS | 4.00 (1.21, 4.00) | 4.00 (1.45, 4.00) | 4.00 (1.20, 4.00) | 4.00 (4.00, 4.00) |
| convex FD-FxNLMS | 4.00 (1.48, 4.00) | 4.00 (1.45, 4.00) | 4.00 (1.20, 4.00) | 4.00 (4.00, 4.00) |
| FDKF | 4.00 (3.27, 4.00) | 4.00 (2.30, 4.00) | 4.00 (1.39, 4.00) | 4.00 (4.00, 4.00) |
| RLS | 0.78 (0.61, 1.72) | 0.63 (0.33, 0.97) | 0.38 (0.26, 1.08) | 4.00 (4.00, 4.00) |
| VFF-RLS | 0.78 (0.61, 1.72) | 0.61 (0.33, 0.97) | 0.38 (0.26, 1.08) | 4.00 (4.00, 4.00) |
| FD-FxNLMS + det | 4.00 (1.48, 4.00) | 3.54 (1.71, 4.00) | 4.00 (1.40, 4.00) | 4.00 (3.73, 4.00) |
| RLS + det | 0.74 (0.56, 1.36) | 0.70 (0.47, 1.22) | 0.39 (0.26, 0.91) | 3.58 (0.82, 4.00) |
| E-PCG | 0.67 (0.49, 1.16) | 0.69 (0.39, 0.97) | 0.42 (0.26, 0.83) | 4.00 (4.00, 4.00) |
| E-PCG bank | 0.70 (0.49, 1.36) | 0.66 (0.39, 0.98) | 0.42 (0.26, 0.74) | 4.00 (4.00, 4.00) |

## tau9, noise = harmonic
| method | S8 stationary | S2 src 30cm | S5 src 30cm cont | R2 rig 30cm |
|---|---|---|---|---|
| FD-FxNLMS | 1.38 (0.78, 4.00) | 2.42 (0.98, 4.00) | 1.53 (0.68, 4.00) | 4.00 (4.00, 4.00) |
| leaky FD-FxNLMS | 2.26 (0.81, 4.00) | 4.00 (1.04, 4.00) | 4.00 (0.77, 4.00) | 4.00 (4.00, 4.00) |
| convex FD-FxNLMS | 0.98 (0.57, 4.00) | 1.42 (0.71, 4.00) | 0.81 (0.41, 4.00) | 4.00 (4.00, 4.00) |
| FDKF | 3.18 (1.36, 4.00) | 2.76 (0.85, 4.00) | 2.46 (0.54, 4.00) | 4.00 (4.00, 4.00) |
| RLS | 0.46 (0.38, 2.12) | 0.52 (0.44, 4.00) | 0.34 (0.26, 4.00) | 4.00 (4.00, 4.00) |
| VFF-RLS | 0.48 (0.43, 2.12) | 0.55 (0.47, 4.00) | 0.34 (0.26, 4.00) | 4.00 (4.00, 4.00) |
| FD-FxNLMS + det | 1.50 (1.10, 4.00) | 1.55 (1.09, 4.00) | 1.08 (0.74, 4.00) | 4.00 (4.00, 4.00) |
| RLS + det | 0.44 (0.38, 2.06) | 0.44 (0.30, 3.36) | 0.40 (0.26, 4.00) | 4.00 (4.00, 4.00) |
| E-PCG | 0.40 (0.35, 3.03) | 0.43 (0.34, 4.00) | 0.45 (0.27, 4.00) | 4.00 (4.00, 4.00) |
| E-PCG bank | 0.50 (0.35, 4.00) | 0.46 (0.34, 4.00) | 0.26 (0.26, 4.00) | 4.00 (4.00, 4.00) |

## tau12, noise = ar1
| method | S8 stationary | S2 src 30cm | S5 src 30cm cont | R2 rig 30cm |
|---|---|---|---|---|
| FD-FxNLMS | 4.00 (4.00, 4.00) | 4.00 (4.00, 4.00) | 4.00 (4.00, 4.00) | 4.00 (4.00, 4.00) |
| leaky FD-FxNLMS | 4.00 (4.00, 4.00) | 4.00 (4.00, 4.00) | 4.00 (4.00, 4.00) | 4.00 (4.00, 4.00) |
| convex FD-FxNLMS | 4.00 (4.00, 4.00) | 4.00 (4.00, 4.00) | 4.00 (4.00, 4.00) | 4.00 (4.00, 4.00) |
| FDKF | 4.00 (4.00, 4.00) | 4.00 (4.00, 4.00) | 4.00 (4.00, 4.00) | 4.00 (4.00, 4.00) |
| RLS | 4.00 (2.16, 4.00) | 4.00 (2.48, 4.00) | 4.00 (1.88, 4.00) | 4.00 (4.00, 4.00) |
| VFF-RLS | 4.00 (2.16, 4.00) | 4.00 (2.48, 4.00) | 4.00 (1.88, 4.00) | 4.00 (4.00, 4.00) |
| FD-FxNLMS + det | 4.00 (4.00, 4.00) | 4.00 (4.00, 4.00) | 4.00 (4.00, 4.00) | 4.00 (4.00, 4.00) |
| RLS + det | 4.00 (1.39, 4.00) | 4.00 (2.41, 4.00) | 4.00 (1.81, 4.00) | 4.00 (4.00, 4.00) |
| E-PCG | 4.00 (1.41, 4.00) | 4.00 (2.16, 4.00) | 4.00 (1.81, 4.00) | 4.00 (4.00, 4.00) |
| E-PCG bank | 4.00 (1.51, 4.00) | 4.00 (2.16, 4.00) | 4.00 (1.88, 4.00) | 4.00 (4.00, 4.00) |

## tau12, noise = harmonic
| method | S8 stationary | S2 src 30cm | S5 src 30cm cont | R2 rig 30cm |
|---|---|---|---|---|
| FD-FxNLMS | 4.00 (2.46, 4.00) | 4.00 (2.32, 4.00) | 4.00 (1.90, 4.00) | 4.00 (4.00, 4.00) |
| leaky FD-FxNLMS | 4.00 (4.00, 4.00) | 4.00 (4.00, 4.00) | 4.00 (4.00, 4.00) | 4.00 (4.00, 4.00) |
| convex FD-FxNLMS | 4.00 (2.29, 4.00) | 4.00 (1.84, 4.00) | 4.00 (1.72, 4.00) | 4.00 (4.00, 4.00) |
| FDKF | 4.00 (4.00, 4.00) | 4.00 (4.00, 4.00) | 4.00 (4.00, 4.00) | 4.00 (4.00, 4.00) |
| RLS | 2.34 (0.45, 4.00) | 2.69 (0.65, 4.00) | 2.39 (0.42, 4.00) | 4.00 (4.00, 4.00) |
| VFF-RLS | 2.34 (0.46, 4.00) | 2.69 (0.66, 4.00) | 2.39 (0.45, 4.00) | 4.00 (4.00, 4.00) |
| FD-FxNLMS + det | 3.86 (2.68, 4.00) | 4.00 (2.68, 4.00) | 4.00 (2.27, 4.00) | 4.00 (4.00, 4.00) |
| RLS + det | 1.39 (0.46, 4.00) | 1.25 (0.39, 4.00) | 1.06 (0.62, 4.00) | 4.00 (4.00, 4.00) |
| E-PCG | 1.39 (0.45, 4.00) | 1.26 (0.42, 4.00) | 1.01 (0.60, 4.00) | 4.00 (4.00, 4.00) |
| E-PCG bank | 2.60 (0.48, 4.00) | 1.26 (0.41, 4.00) | 1.02 (0.30, 4.00) | 4.00 (4.00, 4.00) |

## E-PCG vs baselines (Wilcoxon pratt on seeds; Holm over 128)
| baseline | noise | cell | med dA1 | p_Holm A1 | med dA2 | p_Holm A2 | label |
|---|---|---|---|---|---|---|---|
| FD-FxNLMS | ar1 | S8 stationary | +0.10 | 1 | -1.62 | 2.33e-10 | win |
| FD-FxNLMS | ar1 | S2 src 30cm | -0.91 | 2.64e-08 | -1.57 | 2.33e-10 | win |
| FD-FxNLMS | ar1 | S5 src 30cm cont | -1.19 | 3.17e-10 | -1.53 | 2.33e-10 | win |
| FD-FxNLMS | ar1 | R2 rig 30cm | +0.00 | 1 | +0.00 | 1 | - |
| FD-FxNLMS | harmonic | S8 stationary | -1.37 | 0.00382 | -1.88 | 2.33e-10 | win |
| FD-FxNLMS | harmonic | S2 src 30cm | -0.23 | 1 | -2.35 | 2.33e-10 | win |
| FD-FxNLMS | harmonic | S5 src 30cm cont | -0.47 | 1 | -2.09 | 2.33e-10 | win |
| FD-FxNLMS | harmonic | R2 rig 30cm | +0.00 | 1 | +0.00 | 1 | - |
| leaky FD-FxNLMS | ar1 | S8 stationary | -0.21 | 1 | -1.81 | 2.33e-10 | win |
| leaky FD-FxNLMS | ar1 | S2 src 30cm | -1.16 | 2.01e-09 | -1.85 | 2.33e-10 | win |
| leaky FD-FxNLMS | ar1 | S5 src 30cm cont | -1.43 | 3.17e-10 | -1.86 | 2.33e-10 | win |
| leaky FD-FxNLMS | ar1 | R2 rig 30cm | +0.00 | 1 | +0.00 | 1 | - |
| leaky FD-FxNLMS | harmonic | S8 stationary | -1.74 | 0.000557 | -2.42 | 2.33e-10 | win |
| leaky FD-FxNLMS | harmonic | S2 src 30cm | -0.31 | 1 | -3.16 | 2.33e-10 | win |
| leaky FD-FxNLMS | harmonic | S5 src 30cm cont | -0.55 | 1 | -2.52 | 2.33e-10 | win |
| leaky FD-FxNLMS | harmonic | R2 rig 30cm | +0.00 | 1 | +0.00 | 1 | - |
| convex FD-FxNLMS | ar1 | S8 stationary | -0.45 | 0.178 | -1.41 | 2.33e-10 | win |
| convex FD-FxNLMS | ar1 | S2 src 30cm | -1.01 | 2.01e-09 | -1.45 | 2.33e-10 | win |
| convex FD-FxNLMS | ar1 | S5 src 30cm cont | -1.39 | 3.17e-10 | -1.48 | 2.33e-10 | win |
| convex FD-FxNLMS | ar1 | R2 rig 30cm | +0.00 | 1 | +0.00 | 1 | - |
| convex FD-FxNLMS | harmonic | S8 stationary | -0.79 | 0.34 | -1.60 | 2.33e-10 | win |
| convex FD-FxNLMS | harmonic | S2 src 30cm | +0.00 | 1 | -2.03 | 2.33e-10 | win |
| convex FD-FxNLMS | harmonic | S5 src 30cm cont | -0.23 | 1 | -1.62 | 2.33e-10 | win |
| convex FD-FxNLMS | harmonic | R2 rig 30cm | +0.00 | 1 | +0.00 | 1 | - |
| FDKF | ar1 | S8 stationary | -2.99 | 2.33e-10 | -2.38 | 2.33e-10 | win |
| FDKF | ar1 | S2 src 30cm | -1.44 | 2.33e-10 | -2.28 | 2.33e-10 | win |
| FDKF | ar1 | S5 src 30cm cont | -2.08 | 2.33e-10 | -2.33 | 2.33e-10 | win |
| FDKF | ar1 | R2 rig 30cm | +0.00 | 1 | +0.00 | 1 | - |
| FDKF | harmonic | S8 stationary | -3.38 | 2.66e-09 | -3.56 | 2.33e-10 | win |
| FDKF | harmonic | S2 src 30cm | -0.63 | 0.0332 | -3.72 | 2.33e-10 | win |
| FDKF | harmonic | S5 src 30cm cont | -0.44 | 0.693 | -3.30 | 2.33e-10 | win |
| FDKF | harmonic | R2 rig 30cm | +0.00 | 1 | +0.00 | 1 | - |
| RLS | ar1 | S8 stationary | -1.28 | 1.43e-06 | -0.23 | 4.37e-10 | win |
| RLS | ar1 | S2 src 30cm | +0.21 | 0.000407 | -0.21 | 2.33e-10 | - |
| RLS | ar1 | S5 src 30cm cont | +0.04 | 1 | -0.17 | 2.33e-10 | - |
| RLS | ar1 | R2 rig 30cm | +0.00 | 0.0516 | +0.00 | 0.0118 | - |
| RLS | harmonic | S8 stationary | -2.16 | 4.5e-09 | -0.44 | 2.33e-10 | win |
| RLS | harmonic | S2 src 30cm | +0.73 | 0.00842 | -0.45 | 2.33e-10 | - |
| RLS | harmonic | S5 src 30cm cont | +0.62 | 0.0572 | -0.29 | 0.0489 | - |
| RLS | harmonic | R2 rig 30cm | +0.00 | 1 | +0.00 | 1 | - |
| VFF-RLS | ar1 | S8 stationary | -3.74 | 2.33e-10 | -0.17 | 5.71e-09 | win |
| VFF-RLS | ar1 | S2 src 30cm | +0.22 | 0.000132 | -0.16 | 3.17e-10 | - |
| VFF-RLS | ar1 | S5 src 30cm cont | +0.06 | 1 | -0.13 | 3.46e-09 | - |
| VFF-RLS | ar1 | R2 rig 30cm | +0.00 | 0.0516 | +0.00 | 0.0118 | - |
| VFF-RLS | harmonic | S8 stationary | -5.60 | 2.33e-10 | -0.32 | 2.33e-10 | win |
| VFF-RLS | harmonic | S2 src 30cm | +0.68 | 0.0365 | -0.35 | 2.33e-10 | - |
| VFF-RLS | harmonic | S5 src 30cm cont | +0.47 | 0.196 | -0.27 | 0.143 | - |
| VFF-RLS | harmonic | R2 rig 30cm | +0.00 | 1 | +0.00 | 1 | - |
| FD-FxNLMS + det | ar1 | S8 stationary | +0.02 | 1 | -1.59 | 2.33e-10 | win |
| FD-FxNLMS + det | ar1 | S2 src 30cm | -1.04 | 7.2e-09 | -1.67 | 2.33e-10 | win |
| FD-FxNLMS + det | ar1 | S5 src 30cm cont | -1.25 | 3.17e-10 | -1.64 | 2.33e-10 | win |
| FD-FxNLMS + det | ar1 | R2 rig 30cm | +0.00 | 1 | +0.21 | 0.043 | - |
| FD-FxNLMS + det | harmonic | S8 stationary | -1.79 | 0.000959 | -1.55 | 3.17e-10 | win |
| FD-FxNLMS + det | harmonic | S2 src 30cm | -0.30 | 1 | -2.16 | 2.33e-10 | win |
| FD-FxNLMS + det | harmonic | S5 src 30cm cont | -0.52 | 0.987 | -1.91 | 2.33e-10 | win |
| FD-FxNLMS + det | harmonic | R2 rig 30cm | +0.00 | 1 | +0.00 | 1 | - |
| RLS + det | ar1 | S8 stationary | -1.13 | 6.33e-05 | +0.19 | 2.33e-10 | win |
| RLS + det | ar1 | S2 src 30cm | -0.01 | 1 | +0.11 | 3.17e-10 | - |
| RLS + det | ar1 | S5 src 30cm cont | +0.03 | 0.182 | +0.06 | 0.0157 | - |
| RLS + det | ar1 | R2 rig 30cm | +0.06 | 0.105 | +1.91 | 3.13e-05 | loss |
| RLS + det | harmonic | S8 stationary | -2.20 | 4.5e-09 | +0.21 | 7.2e-09 | win |
| RLS + det | harmonic | S2 src 30cm | +1.45 | 0.0107 | +0.13 | 1.24e-05 | loss |
| RLS + det | harmonic | S5 src 30cm cont | +0.22 | 1 | +0.08 | 1 | - |
| RLS + det | harmonic | R2 rig 30cm | +0.00 | 1 | +0.00 | 1 | - |

Counts (E-PCG): win 36, loss 2, mixed 0, none 26 (of 64)

## E-PCG bank vs baselines (Wilcoxon pratt on seeds; Holm over 128)
| baseline | noise | cell | med dA1 | p_Holm A1 | med dA2 | p_Holm A2 | label |
|---|---|---|---|---|---|---|---|
| FD-FxNLMS | ar1 | S8 stationary | +0.12 | 1 | -1.68 | 2.33e-10 | win |
| FD-FxNLMS | ar1 | S2 src 30cm | -0.81 | 0.00295 | -1.43 | 2.33e-10 | win |
| FD-FxNLMS | ar1 | S5 src 30cm cont | -1.05 | 1.16e-07 | -1.39 | 2.33e-10 | win |
| FD-FxNLMS | ar1 | R2 rig 30cm | +0.00 | 1 | +0.00 | 1 | - |
| FD-FxNLMS | harmonic | S8 stationary | -1.23 | 0.972 | -1.75 | 0.00591 | win |
| FD-FxNLMS | harmonic | S2 src 30cm | -0.09 | 1 | -2.32 | 7.76e-07 | win |
| FD-FxNLMS | harmonic | S5 src 30cm cont | -0.41 | 1 | -2.44 | 4.12e-06 | win |
| FD-FxNLMS | harmonic | R2 rig 30cm | +0.00 | 1 | +0.00 | 1 | - |
| leaky FD-FxNLMS | ar1 | S8 stationary | -0.18 | 1 | -1.89 | 2.33e-10 | win |
| leaky FD-FxNLMS | ar1 | S2 src 30cm | -1.01 | 0.000349 | -1.78 | 2.33e-10 | win |
| leaky FD-FxNLMS | ar1 | S5 src 30cm cont | -1.32 | 1.06e-08 | -1.72 | 2.33e-10 | win |
| leaky FD-FxNLMS | ar1 | R2 rig 30cm | +0.00 | 1 | +0.00 | 1 | - |
| leaky FD-FxNLMS | harmonic | S8 stationary | -1.53 | 0.104 | -2.38 | 0.000588 | win |
| leaky FD-FxNLMS | harmonic | S2 src 30cm | -0.08 | 1 | -3.02 | 8.87e-07 | win |
| leaky FD-FxNLMS | harmonic | S5 src 30cm cont | -0.53 | 1 | -2.83 | 3.31e-06 | win |
| leaky FD-FxNLMS | harmonic | R2 rig 30cm | +0.00 | 1 | +0.00 | 1 | - |
| convex FD-FxNLMS | ar1 | S8 stationary | -0.36 | 0.421 | -1.50 | 2.33e-10 | win |
| convex FD-FxNLMS | ar1 | S2 src 30cm | -0.93 | 0.000234 | -1.36 | 2.33e-10 | win |
| convex FD-FxNLMS | ar1 | S5 src 30cm cont | -1.33 | 1.66e-08 | -1.33 | 2.33e-10 | win |
| convex FD-FxNLMS | ar1 | R2 rig 30cm | +0.00 | 1 | +0.00 | 0.979 | - |
| convex FD-FxNLMS | harmonic | S8 stationary | -0.40 | 1 | -1.48 | 0.104 | - |
| convex FD-FxNLMS | harmonic | S2 src 30cm | +0.44 | 1 | -1.98 | 8.21e-06 | win |
| convex FD-FxNLMS | harmonic | S5 src 30cm cont | +0.37 | 1 | -1.82 | 0.000165 | win |
| convex FD-FxNLMS | harmonic | R2 rig 30cm | +0.00 | 1 | +0.00 | 1 | - |
| FDKF | ar1 | S8 stationary | -2.97 | 2.33e-10 | -2.37 | 2.33e-10 | win |
| FDKF | ar1 | S2 src 30cm | -1.24 | 3.84e-08 | -2.24 | 2.33e-10 | win |
| FDKF | ar1 | S5 src 30cm cont | -1.97 | 2.33e-10 | -2.24 | 2.33e-10 | win |
| FDKF | ar1 | R2 rig 30cm | +0.00 | 1 | +0.00 | 1 | - |
| FDKF | harmonic | S8 stationary | -3.08 | 0.000115 | -3.41 | 1.81e-05 | win |
| FDKF | harmonic | S2 src 30cm | -0.45 | 1 | -3.64 | 6.11e-06 | win |
| FDKF | harmonic | S5 src 30cm cont | -0.42 | 1 | -3.27 | 2.57e-08 | win |
| FDKF | harmonic | R2 rig 30cm | +0.00 | 1 | +0.00 | 1 | - |
| RLS | ar1 | S8 stationary | -1.19 | 2.58e-06 | -0.21 | 1.02e-05 | win |
| RLS | ar1 | S2 src 30cm | +0.29 | 1.13e-05 | -0.11 | 0.0229 | - |
| RLS | ar1 | S5 src 30cm cont | +0.04 | 1 | -0.00 | 1 | - |
| RLS | ar1 | R2 rig 30cm | +0.00 | 0.0231 | +0.00 | 0.00531 | - |
| RLS | harmonic | S8 stationary | -1.88 | 3.67e-06 | -0.41 | 1 | win |
| RLS | harmonic | S2 src 30cm | +1.06 | 0.00652 | -0.42 | 1 | loss |
| RLS | harmonic | S5 src 30cm cont | +0.68 | 0.535 | -0.19 | 1 | - |
| RLS | harmonic | R2 rig 30cm | +0.00 | 1 | +0.00 | 1 | - |
| VFF-RLS | ar1 | S8 stationary | -3.71 | 2.33e-10 | -0.18 | 0.000483 | win |
| VFF-RLS | ar1 | S2 src 30cm | +0.30 | 3.31e-06 | -0.06 | 1 | - |
| VFF-RLS | ar1 | S5 src 30cm cont | +0.05 | 0.855 | +0.04 | 1 | - |
| VFF-RLS | ar1 | R2 rig 30cm | +0.00 | 0.0231 | +0.00 | 0.0231 | - |
| VFF-RLS | harmonic | S8 stationary | -5.23 | 2.33e-10 | -0.30 | 1 | win |
| VFF-RLS | harmonic | S2 src 30cm | +0.82 | 0.0344 | -0.34 | 1 | - |
| VFF-RLS | harmonic | S5 src 30cm cont | +0.69 | 1 | -0.16 | 1 | - |
| VFF-RLS | harmonic | R2 rig 30cm | +0.00 | 1 | +0.00 | 1 | - |
| FD-FxNLMS + det | ar1 | S8 stationary | +0.15 | 1 | -1.57 | 2.33e-10 | win |
| FD-FxNLMS + det | ar1 | S2 src 30cm | -0.87 | 0.000234 | -1.53 | 2.33e-10 | win |
| FD-FxNLMS + det | ar1 | S5 src 30cm cont | -1.15 | 5.64e-08 | -1.47 | 2.33e-10 | win |
| FD-FxNLMS + det | ar1 | R2 rig 30cm | +0.00 | 1 | +0.00 | 1 | - |
| FD-FxNLMS + det | harmonic | S8 stationary | -1.51 | 0.166 | -1.45 | 0.218 | - |
| FD-FxNLMS + det | harmonic | S2 src 30cm | +0.18 | 1 | -2.19 | 2.97e-05 | win |
| FD-FxNLMS + det | harmonic | S5 src 30cm cont | -0.05 | 1 | -2.07 | 0.000272 | win |
| FD-FxNLMS + det | harmonic | R2 rig 30cm | +0.00 | 1 | +0.00 | 1 | - |
| RLS + det | ar1 | S8 stationary | -1.07 | 0.000152 | +0.17 | 1.34e-08 | win |
| RLS + det | ar1 | S2 src 30cm | +0.03 | 1 | +0.21 | 2.33e-10 | - |
| RLS + det | ar1 | S5 src 30cm cont | +0.08 | 0.0344 | +0.21 | 1.53e-06 | - |
| RLS + det | ar1 | R2 rig 30cm | +0.34 | 0.00194 | +1.07 | 5.2e-05 | loss |
| RLS + det | harmonic | S8 stationary | -1.80 | 5.88e-06 | +0.19 | 2.75e-09 | win |
| RLS + det | harmonic | S2 src 30cm | +1.80 | 0.00181 | +0.13 | 3.7e-09 | loss |
| RLS + det | harmonic | S5 src 30cm cont | +0.30 | 1 | +0.17 | 1 | - |
| RLS + det | harmonic | R2 rig 30cm | +0.00 | 1 | +0.00 | 1 | - |

Counts (E-PCG bank): win 34, loss 3, mixed 0, none 27 (of 64)

## E-PCG bank - E-PCG (main) (Holm over 16)
| noise | cell | key | median d | p_Holm |
|---|---|---|---|---|
| ar1 | S8 stationary | A1 | +0.01 | 0.000528 |
| ar1 | S8 stationary | A2 | -0.04 | 1 |
| ar1 | S2 src 30cm | A1 | +0.13 | 0.000125 |
| ar1 | S2 src 30cm | A2 | +0.11 | 6.71e-07 |
| ar1 | S5 src 30cm cont | A1 | +0.02 | 0.53 |
| ar1 | S5 src 30cm cont | A2 | +0.15 | 1.46e-10 |
| ar1 | R2 rig 30cm | A1 | +0.00 | 0.797 |
| ar1 | R2 rig 30cm | A2 | +0.00 | 0.639 |
| harmonic | S8 stationary | A1 | +0.15 | 2.85e-05 |
| harmonic | S8 stationary | A2 | -0.05 | 1 |
| harmonic | S2 src 30cm | A1 | +0.55 | 0.78 |
| harmonic | S2 src 30cm | A2 | -0.05 | 1 |
| harmonic | S5 src 30cm cont | A1 | +0.03 | 1 |
| harmonic | S5 src 30cm cont | A2 | +0.08 | 1 |
| harmonic | R2 rig 30cm | A1 | +0.00 | 1 |
| harmonic | R2 rig 30cm | A2 | +0.00 | 1 |

## Reach fraction at level -9 dB (tau <= t; t in [0.3, 0.5, 1.0, 2.0, 3.0, 4.0] s)
| method | noise | cell | t=0.3 | t=0.5 | t=1.0 | t=2.0 | t=3.0 | t=4.0 |
|---|---|---|---|---|---|---|---|---|
| FD-FxNLMS | ar1 | S8 stationary | 0.00 | 0.03 | 0.30 | 0.38 | 0.47 | 0.47 |
| FD-FxNLMS | ar1 | S2 src 30cm | 0.00 | 0.05 | 0.15 | 0.40 | 0.45 | 0.53 |
| FD-FxNLMS | ar1 | S5 src 30cm cont | 0.10 | 0.12 | 0.30 | 0.45 | 0.50 | 0.53 |
| FD-FxNLMS | ar1 | R2 rig 30cm | 0.00 | 0.03 | 0.07 | 0.10 | 0.15 | 0.15 |
| FD-FxNLMS | harmonic | S8 stationary | 0.00 | 0.00 | 0.42 | 0.55 | 0.60 | 0.62 |
| FD-FxNLMS | harmonic | S2 src 30cm | 0.00 | 0.00 | 0.28 | 0.50 | 0.50 | 0.53 |
| FD-FxNLMS | harmonic | S5 src 30cm cont | 0.00 | 0.03 | 0.42 | 0.53 | 0.53 | 0.55 |
| FD-FxNLMS | harmonic | R2 rig 30cm | 0.00 | 0.00 | 0.00 | 0.03 | 0.03 | 0.03 |
| leaky FD-FxNLMS | ar1 | S8 stationary | 0.00 | 0.00 | 0.23 | 0.35 | 0.42 | 0.45 |
| leaky FD-FxNLMS | ar1 | S2 src 30cm | 0.00 | 0.03 | 0.15 | 0.30 | 0.38 | 0.45 |
| leaky FD-FxNLMS | ar1 | S5 src 30cm cont | 0.03 | 0.10 | 0.25 | 0.35 | 0.38 | 0.45 |
| leaky FD-FxNLMS | ar1 | R2 rig 30cm | 0.00 | 0.03 | 0.07 | 0.10 | 0.15 | 0.15 |
| leaky FD-FxNLMS | harmonic | S8 stationary | 0.00 | 0.00 | 0.40 | 0.47 | 0.53 | 0.55 |
| leaky FD-FxNLMS | harmonic | S2 src 30cm | 0.00 | 0.03 | 0.25 | 0.40 | 0.42 | 0.45 |
| leaky FD-FxNLMS | harmonic | S5 src 30cm cont | 0.00 | 0.07 | 0.35 | 0.42 | 0.47 | 0.47 |
| leaky FD-FxNLMS | harmonic | R2 rig 30cm | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| convex FD-FxNLMS | ar1 | S8 stationary | 0.00 | 0.00 | 0.15 | 0.30 | 0.38 | 0.47 |
| convex FD-FxNLMS | ar1 | S2 src 30cm | 0.00 | 0.03 | 0.15 | 0.30 | 0.40 | 0.45 |
| convex FD-FxNLMS | ar1 | S5 src 30cm cont | 0.03 | 0.10 | 0.25 | 0.38 | 0.42 | 0.45 |
| convex FD-FxNLMS | ar1 | R2 rig 30cm | 0.00 | 0.00 | 0.05 | 0.07 | 0.10 | 0.10 |
| convex FD-FxNLMS | harmonic | S8 stationary | 0.00 | 0.12 | 0.50 | 0.60 | 0.62 | 0.65 |
| convex FD-FxNLMS | harmonic | S2 src 30cm | 0.00 | 0.05 | 0.42 | 0.55 | 0.57 | 0.65 |
| convex FD-FxNLMS | harmonic | S5 src 30cm cont | 0.12 | 0.35 | 0.53 | 0.57 | 0.62 | 0.65 |
| convex FD-FxNLMS | harmonic | R2 rig 30cm | 0.00 | 0.00 | 0.00 | 0.03 | 0.03 | 0.03 |
| FDKF | ar1 | S8 stationary | 0.00 | 0.00 | 0.05 | 0.20 | 0.25 | 0.33 |
| FDKF | ar1 | S2 src 30cm | 0.00 | 0.03 | 0.15 | 0.25 | 0.33 | 0.40 |
| FDKF | ar1 | S5 src 30cm cont | 0.03 | 0.05 | 0.20 | 0.33 | 0.38 | 0.40 |
| FDKF | ar1 | R2 rig 30cm | 0.00 | 0.03 | 0.05 | 0.07 | 0.12 | 0.12 |
| FDKF | harmonic | S8 stationary | 0.00 | 0.00 | 0.03 | 0.45 | 0.50 | 0.50 |
| FDKF | harmonic | S2 src 30cm | 0.00 | 0.00 | 0.33 | 0.50 | 0.50 | 0.50 |
| FDKF | harmonic | S5 src 30cm cont | 0.03 | 0.25 | 0.50 | 0.50 | 0.50 | 0.50 |
| FDKF | harmonic | R2 rig 30cm | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| RLS | ar1 | S8 stationary | 0.00 | 0.15 | 0.55 | 0.85 | 0.93 | 0.97 |
| RLS | ar1 | S2 src 30cm | 0.20 | 0.40 | 0.78 | 0.88 | 0.95 | 0.97 |
| RLS | ar1 | S5 src 30cm cont | 0.38 | 0.53 | 0.70 | 0.90 | 0.95 | 0.95 |
| RLS | ar1 | R2 rig 30cm | 0.00 | 0.00 | 0.05 | 0.05 | 0.05 | 0.05 |
| RLS | harmonic | S8 stationary | 0.00 | 0.57 | 0.70 | 0.75 | 0.75 | 0.75 |
| RLS | harmonic | S2 src 30cm | 0.00 | 0.45 | 0.65 | 0.65 | 0.68 | 0.68 |
| RLS | harmonic | S5 src 30cm cont | 0.50 | 0.55 | 0.65 | 0.65 | 0.68 | 0.68 |
| RLS | harmonic | R2 rig 30cm | 0.00 | 0.00 | 0.05 | 0.05 | 0.05 | 0.05 |
| VFF-RLS | ar1 | S8 stationary | 0.00 | 0.15 | 0.55 | 0.85 | 0.93 | 0.97 |
| VFF-RLS | ar1 | S2 src 30cm | 0.20 | 0.42 | 0.78 | 0.90 | 0.95 | 0.97 |
| VFF-RLS | ar1 | S5 src 30cm cont | 0.38 | 0.53 | 0.70 | 0.90 | 0.95 | 0.95 |
| VFF-RLS | ar1 | R2 rig 30cm | 0.00 | 0.00 | 0.05 | 0.05 | 0.05 | 0.05 |
| VFF-RLS | harmonic | S8 stationary | 0.00 | 0.57 | 0.70 | 0.75 | 0.75 | 0.75 |
| VFF-RLS | harmonic | S2 src 30cm | 0.00 | 0.38 | 0.65 | 0.65 | 0.68 | 0.68 |
| VFF-RLS | harmonic | S5 src 30cm cont | 0.45 | 0.55 | 0.65 | 0.65 | 0.68 | 0.68 |
| VFF-RLS | harmonic | R2 rig 30cm | 0.00 | 0.00 | 0.05 | 0.05 | 0.05 | 0.05 |
| FD-FxNLMS + det | ar1 | S8 stationary | 0.00 | 0.00 | 0.17 | 0.30 | 0.38 | 0.45 |
| FD-FxNLMS + det | ar1 | S2 src 30cm | 0.00 | 0.03 | 0.17 | 0.33 | 0.42 | 0.53 |
| FD-FxNLMS + det | ar1 | S5 src 30cm cont | 0.03 | 0.07 | 0.23 | 0.33 | 0.47 | 0.47 |
| FD-FxNLMS + det | ar1 | R2 rig 30cm | 0.00 | 0.03 | 0.07 | 0.17 | 0.25 | 0.25 |
| FD-FxNLMS + det | harmonic | S8 stationary | 0.00 | 0.00 | 0.20 | 0.57 | 0.62 | 0.65 |
| FD-FxNLMS + det | harmonic | S2 src 30cm | 0.00 | 0.00 | 0.20 | 0.55 | 0.60 | 0.65 |
| FD-FxNLMS + det | harmonic | S5 src 30cm cont | 0.00 | 0.03 | 0.47 | 0.57 | 0.65 | 0.65 |
| FD-FxNLMS + det | harmonic | R2 rig 30cm | 0.00 | 0.00 | 0.00 | 0.03 | 0.03 | 0.03 |
| RLS + det | ar1 | S8 stationary | 0.00 | 0.20 | 0.60 | 0.90 | 0.93 | 0.97 |
| RLS + det | ar1 | S2 src 30cm | 0.05 | 0.30 | 0.72 | 0.90 | 0.95 | 0.97 |
| RLS + det | ar1 | S5 src 30cm cont | 0.33 | 0.55 | 0.75 | 0.93 | 0.97 | 0.97 |
| RLS + det | ar1 | R2 rig 30cm | 0.07 | 0.12 | 0.33 | 0.45 | 0.47 | 0.50 |
| RLS + det | harmonic | S8 stationary | 0.00 | 0.53 | 0.70 | 0.75 | 0.75 | 0.78 |
| RLS + det | harmonic | S2 src 30cm | 0.30 | 0.53 | 0.68 | 0.70 | 0.72 | 0.75 |
| RLS + det | harmonic | S5 src 30cm cont | 0.35 | 0.53 | 0.60 | 0.65 | 0.72 | 0.72 |
| RLS + det | harmonic | R2 rig 30cm | 0.00 | 0.00 | 0.03 | 0.05 | 0.05 | 0.05 |
| E-PCG | ar1 | S8 stationary | 0.00 | 0.30 | 0.65 | 0.90 | 0.93 | 0.97 |
| E-PCG | ar1 | S2 src 30cm | 0.10 | 0.33 | 0.78 | 0.90 | 0.95 | 0.97 |
| E-PCG | ar1 | S5 src 30cm cont | 0.38 | 0.53 | 0.80 | 0.90 | 0.95 | 0.95 |
| E-PCG | ar1 | R2 rig 30cm | 0.03 | 0.07 | 0.15 | 0.23 | 0.23 | 0.23 |
| E-PCG | harmonic | S8 stationary | 0.00 | 0.53 | 0.65 | 0.72 | 0.75 | 0.78 |
| E-PCG | harmonic | S2 src 30cm | 0.00 | 0.53 | 0.65 | 0.70 | 0.70 | 0.70 |
| E-PCG | harmonic | S5 src 30cm cont | 0.28 | 0.53 | 0.62 | 0.70 | 0.70 | 0.70 |
| E-PCG | harmonic | R2 rig 30cm | 0.00 | 0.00 | 0.03 | 0.03 | 0.03 | 0.03 |
| E-PCG bank | ar1 | S8 stationary | 0.00 | 0.28 | 0.60 | 0.88 | 0.93 | 0.97 |
| E-PCG bank | ar1 | S2 src 30cm | 0.07 | 0.38 | 0.75 | 0.90 | 0.95 | 0.97 |
| E-PCG bank | ar1 | S5 src 30cm cont | 0.38 | 0.53 | 0.80 | 0.90 | 0.97 | 0.97 |
| E-PCG bank | ar1 | R2 rig 30cm | 0.05 | 0.07 | 0.12 | 0.17 | 0.17 | 0.17 |
| E-PCG bank | harmonic | S8 stationary | 0.00 | 0.50 | 0.62 | 0.65 | 0.68 | 0.68 |
| E-PCG bank | harmonic | S2 src 30cm | 0.00 | 0.50 | 0.65 | 0.68 | 0.70 | 0.72 |
| E-PCG bank | harmonic | S5 src 30cm cont | 0.53 | 0.53 | 0.62 | 0.72 | 0.72 | 0.72 |
| E-PCG bank | harmonic | R2 rig 30cm | 0.00 | 0.00 | 0.03 | 0.05 | 0.05 | 0.05 |

## Reach fraction at level -12 dB (tau <= t; t in [0.3, 0.5, 1.0, 2.0, 3.0, 4.0] s)
| method | noise | cell | t=0.3 | t=0.5 | t=1.0 | t=2.0 | t=3.0 | t=4.0 |
|---|---|---|---|---|---|---|---|---|
| FD-FxNLMS | ar1 | S8 stationary | 0.00 | 0.00 | 0.00 | 0.03 | 0.03 | 0.03 |
| FD-FxNLMS | ar1 | S2 src 30cm | 0.00 | 0.00 | 0.03 | 0.03 | 0.03 | 0.05 |
| FD-FxNLMS | ar1 | S5 src 30cm cont | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.03 |
| FD-FxNLMS | ar1 | R2 rig 30cm | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| FD-FxNLMS | harmonic | S8 stationary | 0.00 | 0.00 | 0.00 | 0.23 | 0.40 | 0.45 |
| FD-FxNLMS | harmonic | S2 src 30cm | 0.00 | 0.00 | 0.03 | 0.20 | 0.35 | 0.40 |
| FD-FxNLMS | harmonic | S5 src 30cm cont | 0.00 | 0.00 | 0.03 | 0.28 | 0.33 | 0.38 |
| FD-FxNLMS | harmonic | R2 rig 30cm | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| leaky FD-FxNLMS | ar1 | S8 stationary | 0.00 | 0.00 | 0.00 | 0.03 | 0.03 | 0.03 |
| leaky FD-FxNLMS | ar1 | S2 src 30cm | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| leaky FD-FxNLMS | ar1 | S5 src 30cm cont | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| leaky FD-FxNLMS | ar1 | R2 rig 30cm | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| leaky FD-FxNLMS | harmonic | S8 stationary | 0.00 | 0.00 | 0.00 | 0.12 | 0.17 | 0.20 |
| leaky FD-FxNLMS | harmonic | S2 src 30cm | 0.00 | 0.00 | 0.00 | 0.07 | 0.07 | 0.10 |
| leaky FD-FxNLMS | harmonic | S5 src 30cm cont | 0.00 | 0.00 | 0.00 | 0.05 | 0.07 | 0.10 |
| leaky FD-FxNLMS | harmonic | R2 rig 30cm | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| convex FD-FxNLMS | ar1 | S8 stationary | 0.00 | 0.00 | 0.00 | 0.03 | 0.03 | 0.03 |
| convex FD-FxNLMS | ar1 | S2 src 30cm | 0.00 | 0.00 | 0.05 | 0.05 | 0.05 | 0.05 |
| convex FD-FxNLMS | ar1 | S5 src 30cm cont | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| convex FD-FxNLMS | ar1 | R2 rig 30cm | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| convex FD-FxNLMS | harmonic | S8 stationary | 0.00 | 0.00 | 0.05 | 0.17 | 0.42 | 0.47 |
| convex FD-FxNLMS | harmonic | S2 src 30cm | 0.00 | 0.00 | 0.10 | 0.30 | 0.35 | 0.45 |
| convex FD-FxNLMS | harmonic | S5 src 30cm cont | 0.00 | 0.00 | 0.07 | 0.28 | 0.38 | 0.45 |
| convex FD-FxNLMS | harmonic | R2 rig 30cm | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| FDKF | ar1 | S8 stationary | 0.00 | 0.00 | 0.00 | 0.03 | 0.03 | 0.03 |
| FDKF | ar1 | S2 src 30cm | 0.00 | 0.03 | 0.03 | 0.03 | 0.05 | 0.05 |
| FDKF | ar1 | S5 src 30cm cont | 0.00 | 0.00 | 0.00 | 0.03 | 0.03 | 0.03 |
| FDKF | ar1 | R2 rig 30cm | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| FDKF | harmonic | S8 stationary | 0.00 | 0.00 | 0.00 | 0.00 | 0.05 | 0.15 |
| FDKF | harmonic | S2 src 30cm | 0.00 | 0.00 | 0.00 | 0.03 | 0.17 | 0.23 |
| FDKF | harmonic | S5 src 30cm cont | 0.00 | 0.00 | 0.00 | 0.12 | 0.17 | 0.20 |
| FDKF | harmonic | R2 rig 30cm | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| RLS | ar1 | S8 stationary | 0.00 | 0.03 | 0.12 | 0.25 | 0.30 | 0.35 |
| RLS | ar1 | S2 src 30cm | 0.00 | 0.03 | 0.15 | 0.23 | 0.33 | 0.38 |
| RLS | ar1 | S5 src 30cm cont | 0.03 | 0.05 | 0.12 | 0.28 | 0.38 | 0.38 |
| RLS | ar1 | R2 rig 30cm | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| RLS | harmonic | S8 stationary | 0.00 | 0.38 | 0.50 | 0.50 | 0.50 | 0.50 |
| RLS | harmonic | S2 src 30cm | 0.00 | 0.03 | 0.47 | 0.50 | 0.50 | 0.50 |
| RLS | harmonic | S5 src 30cm cont | 0.03 | 0.40 | 0.50 | 0.50 | 0.50 | 0.50 |
| RLS | harmonic | R2 rig 30cm | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.03 |
| VFF-RLS | ar1 | S8 stationary | 0.00 | 0.03 | 0.12 | 0.25 | 0.30 | 0.35 |
| VFF-RLS | ar1 | S2 src 30cm | 0.00 | 0.03 | 0.15 | 0.23 | 0.33 | 0.38 |
| VFF-RLS | ar1 | S5 src 30cm cont | 0.03 | 0.05 | 0.15 | 0.28 | 0.38 | 0.38 |
| VFF-RLS | ar1 | R2 rig 30cm | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| VFF-RLS | harmonic | S8 stationary | 0.00 | 0.38 | 0.50 | 0.50 | 0.50 | 0.50 |
| VFF-RLS | harmonic | S2 src 30cm | 0.00 | 0.00 | 0.47 | 0.50 | 0.50 | 0.50 |
| VFF-RLS | harmonic | S5 src 30cm cont | 0.00 | 0.35 | 0.50 | 0.50 | 0.50 | 0.50 |
| VFF-RLS | harmonic | R2 rig 30cm | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.03 |
| FD-FxNLMS + det | ar1 | S8 stationary | 0.00 | 0.00 | 0.00 | 0.03 | 0.03 | 0.03 |
| FD-FxNLMS + det | ar1 | S2 src 30cm | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| FD-FxNLMS + det | ar1 | S5 src 30cm cont | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| FD-FxNLMS + det | ar1 | R2 rig 30cm | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| FD-FxNLMS + det | harmonic | S8 stationary | 0.00 | 0.00 | 0.00 | 0.12 | 0.38 | 0.50 |
| FD-FxNLMS + det | harmonic | S2 src 30cm | 0.00 | 0.00 | 0.00 | 0.12 | 0.33 | 0.42 |
| FD-FxNLMS + det | harmonic | S5 src 30cm cont | 0.00 | 0.00 | 0.00 | 0.20 | 0.33 | 0.38 |
| FD-FxNLMS + det | harmonic | R2 rig 30cm | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| RLS + det | ar1 | S8 stationary | 0.00 | 0.03 | 0.15 | 0.33 | 0.35 | 0.40 |
| RLS + det | ar1 | S2 src 30cm | 0.00 | 0.03 | 0.12 | 0.23 | 0.38 | 0.42 |
| RLS + det | ar1 | S5 src 30cm cont | 0.00 | 0.00 | 0.12 | 0.30 | 0.40 | 0.42 |
| RLS + det | ar1 | R2 rig 30cm | 0.00 | 0.03 | 0.03 | 0.03 | 0.07 | 0.10 |
| RLS + det | harmonic | S8 stationary | 0.00 | 0.33 | 0.50 | 0.50 | 0.55 | 0.57 |
| RLS + det | harmonic | S2 src 30cm | 0.00 | 0.42 | 0.50 | 0.53 | 0.53 | 0.53 |
| RLS + det | harmonic | S5 src 30cm cont | 0.05 | 0.20 | 0.50 | 0.53 | 0.53 | 0.53 |
| RLS + det | harmonic | R2 rig 30cm | 0.00 | 0.00 | 0.00 | 0.00 | 0.03 | 0.05 |
| E-PCG | ar1 | S8 stationary | 0.00 | 0.03 | 0.15 | 0.33 | 0.35 | 0.40 |
| E-PCG | ar1 | S2 src 30cm | 0.00 | 0.03 | 0.17 | 0.25 | 0.33 | 0.38 |
| E-PCG | ar1 | S5 src 30cm cont | 0.00 | 0.00 | 0.12 | 0.28 | 0.38 | 0.38 |
| E-PCG | ar1 | R2 rig 30cm | 0.00 | 0.03 | 0.03 | 0.03 | 0.03 | 0.05 |
| E-PCG | harmonic | S8 stationary | 0.00 | 0.33 | 0.47 | 0.53 | 0.55 | 0.55 |
| E-PCG | harmonic | S2 src 30cm | 0.00 | 0.45 | 0.50 | 0.53 | 0.53 | 0.53 |
| E-PCG | harmonic | S5 src 30cm cont | 0.05 | 0.12 | 0.50 | 0.53 | 0.53 | 0.53 |
| E-PCG | harmonic | R2 rig 30cm | 0.00 | 0.00 | 0.00 | 0.03 | 0.03 | 0.03 |
| E-PCG bank | ar1 | S8 stationary | 0.00 | 0.03 | 0.12 | 0.30 | 0.33 | 0.38 |
| E-PCG bank | ar1 | S2 src 30cm | 0.00 | 0.03 | 0.17 | 0.25 | 0.33 | 0.38 |
| E-PCG bank | ar1 | S5 src 30cm cont | 0.00 | 0.00 | 0.12 | 0.28 | 0.38 | 0.38 |
| E-PCG bank | ar1 | R2 rig 30cm | 0.00 | 0.03 | 0.03 | 0.03 | 0.03 | 0.03 |
| E-PCG bank | harmonic | S8 stationary | 0.00 | 0.30 | 0.47 | 0.50 | 0.50 | 0.50 |
| E-PCG bank | harmonic | S2 src 30cm | 0.00 | 0.40 | 0.50 | 0.53 | 0.53 | 0.53 |
| E-PCG bank | harmonic | S5 src 30cm cont | 0.25 | 0.42 | 0.50 | 0.53 | 0.53 | 0.53 |
| E-PCG bank | harmonic | R2 rig 30cm | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |

## Cost of the proposed methods (mean flop_hist / H = flops per sample; S8 / change cells)
| method | S8 | change cells |
|---|---|---|
| E-PCG | 8827 | 16117 |
| E-PCG bank | 16461 | 25287 |

## Diagnostics
- records 3200; unparsable 0; stale 0; duplicates 0 (differing 0)
- win / loss: each metric with its own Holm-adjusted p (A1 with p_A1, A2 with p_A2), thresholds 1 dB (A1) / 0.5 dB (A2)
- curves are ensemble means of the seed-summed powers: one failed run can dominate a curve (read with the failure table)
- cost of the baselines: analytic counts in the cost table (Step 6), not measured here
- runs stopped early (completed with no control): 312
- uncontrolled power after the stop taken from a no-control run (every method stopped early): [('harmonic', 'R2 rig 30cm', 482)]
