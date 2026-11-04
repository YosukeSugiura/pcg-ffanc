# Final evaluation (evaluation seeds 480-519, M = 512, T = 5 s; rule docs/current/FINAL_EVAL_RULE.md)
Values: median (Q1, Q3) over the 40 seeds; failed runs: A1 = A2 = 0 dB, tau = 4 s (censored).

## Failures (runs out of 40)
| method | ar1 S8 | ar1 S2 | ar1 S5 | ar1 R2 | harmonic S8 | harmonic S2 | harmonic S5 | harmonic R2 |
|---|---|---|---|---|---|---|---|---|
| FD-FxNLMS | 0 | 0 | 0 | 2 | 0 | 0 | 0 | 32 |
| leaky FD-FxNLMS | 0 | 0 | 0 | 2 | 0 | 0 | 0 | 32 |
| convex FD-FxNLMS | 0 | 0 | 0 | 2 | 0 | 0 | 0 | 30 |
| FDKF | 0 | 0 | 0 | 1 | 0 | 0 | 0 | 7 |
| RLS | 1 | 1 | 1 | 10 | 0 | 0 | 0 | 13 |
| VFF-RLS | 5 | 5 | 5 | 11 | 0 | 0 | 0 | 13 |
| FD-FxNLMS + det | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 30 |
| RLS + det | 1 | 1 | 1 | 1 | 0 | 0 | 0 | 6 |
| E-PCG | 0 | 0 | 0 | 5 | 0 | 0 | 0 | 14 |
| E-PCG bank | 0 | 0 | 0 | 1 | 0 | 0 | 0 | 16 |

## A1, noise = ar1
| method | S8 stationary | S2 src 30cm | S5 src 30cm cont | R2 rig 30cm |
|---|---|---|---|---|
| FD-FxNLMS | -5.02 (-6.09, -3.36) | -8.52 (-9.06, -8.04) | -8.58 (-9.25, -8.24) | -7.49 (-8.55, -6.83) |
| leaky FD-FxNLMS | -4.72 (-5.72, -2.67) | -8.75 (-9.31, -8.33) | -8.76 (-9.62, -8.47) | -7.69 (-8.81, -7.07) |
| convex FD-FxNLMS | -5.69 (-6.95, -4.30) | -8.61 (-9.17, -8.08) | -8.63 (-9.36, -8.29) | -7.68 (-8.72, -6.83) |
| FDKF | -3.37 (-3.86, -3.10) | -7.70 (-8.23, -7.44) | -7.77 (-8.32, -7.41) | -7.20 (-7.71, -6.11) |
| RLS | -0.67 (-2.80, 2.79) | -8.94 (-9.69, -8.39) | -8.91 (-9.85, -8.65) | -7.62 (-8.93, -4.53) |
| VFF-RLS | 4.86 (0.20, 8.20) | -8.88 (-9.56, -8.29) | -8.92 (-9.89, -8.45) | -7.62 (-9.01, 0.00) |
| FD-FxNLMS + det | -5.68 (-6.58, -4.05) | -8.24 (-8.99, -8.00) | -8.62 (-9.25, -8.11) | -7.26 (-8.65, -6.12) |
| RLS + det | -0.85 (-2.88, 2.46) | -8.44 (-8.95, -7.88) | -8.85 (-9.42, -8.05) | -7.20 (-8.52, -5.02) |
| E-PCG | -5.24 (-6.03, -3.81) | -8.66 (-9.07, -8.09) | -8.77 (-9.45, -8.27) | -7.52 (-8.80, -6.00) |
| E-PCG bank | -5.23 (-5.98, -3.81) | -8.45 (-9.04, -7.90) | -8.79 (-9.39, -7.96) | -7.04 (-8.49, -5.62) |

## A1, noise = harmonic
| method | S8 stationary | S2 src 30cm | S5 src 30cm cont | R2 rig 30cm |
|---|---|---|---|---|
| FD-FxNLMS | -5.21 (-6.03, -4.50) | -7.15 (-7.86, -6.46) | -8.22 (-8.81, -7.28) | 0.00 (0.00, 0.00) |
| leaky FD-FxNLMS | -5.24 (-5.99, -4.56) | -7.58 (-8.19, -6.83) | -8.56 (-9.15, -7.41) | 0.00 (0.00, 0.00) |
| convex FD-FxNLMS | -6.32 (-7.46, -5.11) | -8.16 (-8.69, -7.15) | -9.09 (-9.72, -8.05) | 0.00 (0.00, 0.00) |
| FDKF | -3.82 (-4.25, -3.62) | -6.66 (-7.31, -5.81) | -8.69 (-9.20, -7.88) | -4.17 (-5.42, -1.64) |
| RLS | -6.57 (-7.56, -5.43) | -8.26 (-8.71, -7.58) | -9.11 (-9.75, -8.62) | -4.59 (-6.83, 0.00) |
| VFF-RLS | -0.91 (-2.87, 0.59) | -7.94 (-8.39, -7.31) | -8.91 (-9.58, -8.43) | -4.44 (-6.51, 0.00) |
| FD-FxNLMS + det | -4.83 (-5.57, -4.03) | -6.24 (-7.01, -5.55) | -7.43 (-7.82, -6.49) | 0.00 (-0.68, 0.00) |
| RLS + det | -6.66 (-7.65, -5.54) | -10.43 (-11.77, -9.29) | -9.26 (-9.82, -8.29) | -3.60 (-6.52, 0.00) |
| E-PCG | -7.69 (-8.83, -6.50) | -8.02 (-8.86, -5.98) | -8.50 (-9.36, -7.31) | -3.49 (-6.11, 0.00) |
| E-PCG bank | -7.61 (-8.76, -6.26) | -7.44 (-9.12, -6.16) | -9.16 (-10.65, -7.73) | 0.00 (-5.06, 0.00) |

## A2, noise = ar1
| method | S8 stationary | S2 src 30cm | S5 src 30cm cont | R2 rig 30cm |
|---|---|---|---|---|
| FD-FxNLMS | -9.06 (-9.70, -8.60) | -9.09 (-9.55, -8.68) | -9.09 (-9.53, -8.70) | -8.36 (-8.88, -7.43) |
| leaky FD-FxNLMS | -9.44 (-10.07, -8.78) | -9.61 (-10.00, -8.92) | -9.58 (-9.95, -8.91) | -8.61 (-9.51, -8.04) |
| convex FD-FxNLMS | -9.30 (-10.00, -8.79) | -9.44 (-9.89, -8.94) | -9.42 (-9.77, -8.92) | -8.53 (-9.25, -7.71) |
| FDKF | -8.24 (-8.92, -7.88) | -8.39 (-8.75, -8.04) | -8.39 (-8.75, -8.02) | -7.61 (-8.25, -6.55) |
| RLS | -9.85 (-10.40, -8.91) | -9.87 (-10.42, -9.07) | -9.87 (-10.43, -9.11) | -8.29 (-8.98, -4.52) |
| VFF-RLS | -9.79 (-10.35, -8.90) | -9.81 (-10.41, -9.02) | -9.77 (-10.36, -9.06) | -8.33 (-9.07, 0.00) |
| FD-FxNLMS + det | -9.27 (-9.89, -8.81) | -9.36 (-9.82, -8.89) | -9.40 (-9.85, -8.83) | -8.37 (-9.07, -7.74) |
| RLS + det | -10.21 (-10.75, -9.29) | -10.17 (-10.80, -9.37) | -9.98 (-10.74, -9.29) | -9.10 (-9.85, -8.74) |
| E-PCG | -9.99 (-10.46, -9.14) | -10.05 (-10.66, -9.26) | -9.96 (-10.58, -9.28) | -8.55 (-9.22, -7.15) |
| E-PCG bank | -9.91 (-10.59, -9.10) | -9.98 (-10.51, -9.10) | -9.87 (-10.45, -9.06) | -8.68 (-9.43, -8.25) |

## A2, noise = harmonic
| method | S8 stationary | S2 src 30cm | S5 src 30cm cont | R2 rig 30cm |
|---|---|---|---|---|
| FD-FxNLMS | -12.64 (-14.39, -10.80) | -12.35 (-14.04, -10.60) | -11.84 (-13.40, -10.34) | 0.00 (0.00, 0.00) |
| leaky FD-FxNLMS | -12.12 (-13.75, -10.33) | -12.03 (-13.59, -10.23) | -11.70 (-13.18, -10.09) | 0.00 (0.00, 0.00) |
| convex FD-FxNLMS | -12.71 (-14.48, -10.94) | -12.32 (-14.04, -10.53) | -12.09 (-13.71, -10.37) | 0.00 (-0.08, 0.00) |
| FDKF | -11.55 (-13.22, -10.06) | -11.35 (-12.95, -9.89) | -11.25 (-12.71, -9.77) | -7.29 (-9.77, -3.91) |
| RLS | -13.75 (-15.08, -12.41) | -13.63 (-15.30, -12.28) | -13.38 (-14.83, -12.10) | -7.34 (-11.92, 0.00) |
| VFF-RLS | -13.82 (-15.19, -12.48) | -13.69 (-15.39, -12.34) | -13.40 (-14.82, -12.13) | -8.14 (-12.43, 0.00) |
| FD-FxNLMS + det | -12.66 (-14.50, -10.71) | -11.80 (-13.38, -10.20) | -11.25 (-12.85, -9.76) | 0.00 (-0.68, 0.00) |
| RLS + det | -14.16 (-15.60, -12.83) | -14.02 (-15.85, -12.59) | -13.35 (-14.47, -12.21) | -9.67 (-12.32, -3.81) |
| E-PCG | -13.98 (-15.43, -12.63) | -13.89 (-15.70, -12.44) | -13.25 (-14.43, -12.08) | -6.20 (-10.89, 0.00) |
| E-PCG bank | -14.16 (-15.55, -12.73) | -13.94 (-15.70, -12.47) | -13.48 (-15.28, -12.16) | -4.32 (-12.48, 0.00) |

## tau9, noise = ar1
| method | S8 stationary | S2 src 30cm | S5 src 30cm cont | R2 rig 30cm |
|---|---|---|---|---|
| FD-FxNLMS | 0.71 (0.54, 0.86) | 0.34 (0.26, 0.46) | 0.27 (0.26, 0.35) | 0.78 (0.40, 1.18) |
| leaky FD-FxNLMS | 0.67 (0.53, 0.82) | 0.30 (0.26, 0.39) | 0.26 (0.26, 0.29) | 0.66 (0.32, 1.02) |
| convex FD-FxNLMS | 0.61 (0.43, 0.82) | 0.32 (0.26, 0.42) | 0.26 (0.26, 0.34) | 0.78 (0.34, 1.15) |
| FDKF | 1.18 (0.98, 1.34) | 0.64 (0.40, 1.27) | 0.46 (0.27, 0.76) | 0.97 (0.68, 1.49) |
| RLS | 0.53 (0.43, 0.62) | 0.30 (0.26, 0.39) | 0.26 (0.26, 0.29) | 0.74 (0.31, 4.00) |
| VFF-RLS | 0.57 (0.45, 0.76) | 0.31 (0.26, 0.44) | 0.26 (0.26, 0.32) | 0.75 (0.30, 4.00) |
| FD-FxNLMS + det | 0.69 (0.56, 0.83) | 0.37 (0.26, 0.58) | 0.27 (0.26, 0.34) | 0.80 (0.37, 1.20) |
| RLS + det | 0.50 (0.43, 0.56) | 0.41 (0.29, 0.52) | 0.26 (0.26, 0.37) | 0.71 (0.37, 0.88) |
| E-PCG | 0.47 (0.40, 0.59) | 0.38 (0.26, 0.51) | 0.26 (0.26, 0.32) | 0.56 (0.36, 0.89) |
| E-PCG bank | 0.48 (0.40, 0.64) | 0.38 (0.26, 0.52) | 0.27 (0.26, 0.38) | 0.75 (0.36, 0.95) |

## tau9, noise = harmonic
| method | S8 stationary | S2 src 30cm | S5 src 30cm cont | R2 rig 30cm |
|---|---|---|---|---|
| FD-FxNLMS | 0.66 (0.52, 0.91) | 0.50 (0.42, 0.64) | 0.29 (0.26, 0.46) | 4.00 (4.00, 4.00) |
| leaky FD-FxNLMS | 0.62 (0.48, 0.86) | 0.43 (0.39, 0.54) | 0.26 (0.26, 0.39) | 4.00 (4.00, 4.00) |
| convex FD-FxNLMS | 0.44 (0.35, 0.75) | 0.38 (0.36, 0.51) | 0.26 (0.26, 0.31) | 4.00 (4.00, 4.00) |
| FDKF | 0.88 (0.80, 1.04) | 0.55 (0.47, 0.68) | 0.26 (0.26, 0.37) | 3.34 (0.86, 4.00) |
| RLS | 0.35 (0.34, 0.38) | 0.38 (0.36, 0.40) | 0.26 (0.26, 0.26) | 1.06 (0.44, 4.00) |
| VFF-RLS | 0.37 (0.37, 0.39) | 0.39 (0.38, 0.43) | 0.26 (0.26, 0.26) | 1.10 (0.49, 4.00) |
| FD-FxNLMS + det | 0.76 (0.58, 1.16) | 0.68 (0.58, 0.93) | 0.38 (0.30, 0.64) | 4.00 (4.00, 4.00) |
| RLS + det | 0.35 (0.34, 0.38) | 0.28 (0.26, 0.32) | 0.26 (0.26, 0.26) | 0.98 (0.44, 3.50) |
| E-PCG | 0.32 (0.30, 0.36) | 0.31 (0.30, 0.33) | 0.26 (0.26, 0.29) | 1.22 (0.37, 4.00) |
| E-PCG bank | 0.32 (0.30, 0.38) | 0.33 (0.31, 0.34) | 0.26 (0.26, 0.26) | 1.88 (0.48, 4.00) |

## tau12, noise = ar1
| method | S8 stationary | S2 src 30cm | S5 src 30cm cont | R2 rig 30cm |
|---|---|---|---|---|
| FD-FxNLMS | 4.00 (2.95, 4.00) | 4.00 (2.35, 4.00) | 4.00 (2.23, 4.00) | 4.00 (4.00, 4.00) |
| leaky FD-FxNLMS | 4.00 (1.53, 4.00) | 4.00 (1.96, 4.00) | 4.00 (1.74, 4.00) | 4.00 (3.85, 4.00) |
| convex FD-FxNLMS | 3.97 (1.41, 4.00) | 4.00 (2.20, 4.00) | 4.00 (1.70, 4.00) | 4.00 (4.00, 4.00) |
| FDKF | 4.00 (4.00, 4.00) | 4.00 (4.00, 4.00) | 4.00 (4.00, 4.00) | 4.00 (4.00, 4.00) |
| RLS | 3.68 (1.46, 4.00) | 3.66 (1.32, 4.00) | 3.65 (1.52, 4.00) | 4.00 (4.00, 4.00) |
| VFF-RLS | 3.34 (1.46, 4.00) | 3.07 (1.32, 4.00) | 3.41 (1.50, 4.00) | 4.00 (4.00, 4.00) |
| FD-FxNLMS + det | 3.97 (1.40, 4.00) | 4.00 (2.18, 4.00) | 4.00 (1.74, 4.00) | 4.00 (4.00, 4.00) |
| RLS + det | 1.95 (0.95, 3.88) | 2.65 (1.66, 4.00) | 2.05 (1.13, 4.00) | 4.00 (2.59, 4.00) |
| E-PCG | 2.74 (0.93, 4.00) | 2.34 (1.22, 4.00) | 2.04 (1.13, 4.00) | 4.00 (3.93, 4.00) |
| E-PCG bank | 2.53 (0.98, 4.00) | 3.18 (1.60, 4.00) | 2.47 (1.36, 4.00) | 4.00 (3.12, 4.00) |

## tau12, noise = harmonic
| method | S8 stationary | S2 src 30cm | S5 src 30cm cont | R2 rig 30cm |
|---|---|---|---|---|
| FD-FxNLMS | 1.33 (0.92, 2.78) | 1.02 (0.74, 3.00) | 0.82 (0.59, 2.40) | 4.00 (4.00, 4.00) |
| leaky FD-FxNLMS | 1.19 (0.83, 4.00) | 0.99 (0.71, 3.68) | 0.86 (0.51, 3.54) | 4.00 (4.00, 4.00) |
| convex FD-FxNLMS | 1.05 (0.51, 2.69) | 0.95 (0.61, 3.22) | 0.70 (0.38, 2.62) | 4.00 (4.00, 4.00) |
| FDKF | 1.85 (1.48, 4.00) | 1.47 (0.88, 4.00) | 0.90 (0.46, 4.00) | 4.00 (4.00, 4.00) |
| RLS | 0.46 (0.38, 0.61) | 0.58 (0.50, 0.71) | 0.34 (0.29, 0.53) | 4.00 (0.82, 4.00) |
| VFF-RLS | 0.46 (0.38, 0.61) | 0.60 (0.55, 0.71) | 0.38 (0.32, 0.53) | 4.00 (0.87, 4.00) |
| FD-FxNLMS + det | 1.57 (1.18, 4.00) | 1.60 (1.13, 3.48) | 1.14 (0.70, 3.10) | 4.00 (4.00, 4.00) |
| RLS + det | 0.46 (0.37, 0.62) | 0.37 (0.30, 0.50) | 0.49 (0.40, 0.64) | 3.97 (0.88, 4.00) |
| E-PCG | 0.48 (0.35, 0.74) | 0.35 (0.33, 0.56) | 0.53 (0.46, 0.64) | 4.00 (0.76, 4.00) |
| E-PCG bank | 0.49 (0.35, 0.74) | 0.38 (0.34, 0.48) | 0.26 (0.26, 0.53) | 4.00 (0.89, 4.00) |

## E-PCG vs baselines (Wilcoxon pratt on seeds; Holm over 128)
| baseline | noise | cell | med dA1 | p_Holm A1 | med dA2 | p_Holm A2 | label |
|---|---|---|---|---|---|---|---|
| FD-FxNLMS | ar1 | S8 stationary | -0.13 | 1 | -0.81 | 2.33e-10 | win |
| FD-FxNLMS | ar1 | S2 src 30cm | -0.16 | 1 | -0.74 | 2.33e-10 | win |
| FD-FxNLMS | ar1 | S5 src 30cm cont | -0.23 | 1 | -0.72 | 2.33e-10 | win |
| FD-FxNLMS | ar1 | R2 rig 30cm | +0.00 | 1 | -0.47 | 1 | - |
| FD-FxNLMS | harmonic | S8 stationary | -2.34 | 2.33e-10 | -1.40 | 2.33e-10 | win |
| FD-FxNLMS | harmonic | S2 src 30cm | -0.60 | 1 | -1.77 | 2.33e-10 | win |
| FD-FxNLMS | harmonic | S5 src 30cm cont | -0.29 | 1 | -1.55 | 2.33e-10 | win |
| FD-FxNLMS | harmonic | R2 rig 30cm | -0.07 | 0.067 | -3.22 | 0.000591 | win |
| leaky FD-FxNLMS | ar1 | S8 stationary | -0.40 | 1 | -0.42 | 2.94e-09 | - |
| leaky FD-FxNLMS | ar1 | S2 src 30cm | +0.08 | 1 | -0.44 | 2.33e-10 | - |
| leaky FD-FxNLMS | ar1 | S5 src 30cm cont | +0.02 | 1 | -0.42 | 2.22e-09 | - |
| leaky FD-FxNLMS | ar1 | R2 rig 30cm | +0.28 | 0.0291 | -0.08 | 1 | - |
| leaky FD-FxNLMS | harmonic | S8 stationary | -2.33 | 2.33e-10 | -1.96 | 2.33e-10 | win |
| leaky FD-FxNLMS | harmonic | S2 src 30cm | -0.38 | 1 | -2.13 | 2.33e-10 | win |
| leaky FD-FxNLMS | harmonic | S5 src 30cm cont | -0.00 | 1 | -1.79 | 2.33e-10 | win |
| leaky FD-FxNLMS | harmonic | R2 rig 30cm | -0.04 | 0.0833 | -2.93 | 0.00384 | win |
| convex FD-FxNLMS | ar1 | S8 stationary | +0.83 | 0.616 | -0.57 | 2.94e-09 | win |
| convex FD-FxNLMS | ar1 | S2 src 30cm | -0.06 | 1 | -0.51 | 2.33e-10 | win |
| convex FD-FxNLMS | ar1 | S5 src 30cm cont | -0.18 | 1 | -0.49 | 3.49e-10 | - |
| convex FD-FxNLMS | ar1 | R2 rig 30cm | +0.01 | 1 | -0.21 | 1 | - |
| convex FD-FxNLMS | harmonic | S8 stationary | -1.28 | 3.13e-08 | -1.30 | 2.33e-10 | win |
| convex FD-FxNLMS | harmonic | S2 src 30cm | +0.06 | 1 | -1.82 | 2.33e-10 | win |
| convex FD-FxNLMS | harmonic | S5 src 30cm cont | +0.52 | 0.00332 | -1.26 | 2.33e-10 | win |
| convex FD-FxNLMS | harmonic | R2 rig 30cm | -0.67 | 0.032 | -2.77 | 0.00303 | win |
| FDKF | ar1 | S8 stationary | -1.65 | 0.0386 | -1.45 | 2.33e-10 | win |
| FDKF | ar1 | S2 src 30cm | -1.05 | 2.47e-07 | -1.49 | 2.33e-10 | win |
| FDKF | ar1 | S5 src 30cm cont | -1.10 | 2.47e-07 | -1.45 | 2.33e-10 | win |
| FDKF | ar1 | R2 rig 30cm | -0.87 | 1 | -1.24 | 1 | - |
| FDKF | harmonic | S8 stationary | -3.52 | 2.33e-10 | -2.43 | 2.33e-10 | win |
| FDKF | harmonic | S2 src 30cm | -0.69 | 0.341 | -2.58 | 2.33e-10 | win |
| FDKF | harmonic | S5 src 30cm cont | +0.08 | 1 | -2.07 | 2.33e-10 | win |
| FDKF | harmonic | R2 rig 30cm | +0.00 | 1 | +0.00 | 1 | - |
| RLS | ar1 | S8 stationary | -4.63 | 5.02e-10 | -0.20 | 9.43e-08 | win |
| RLS | ar1 | S2 src 30cm | +0.30 | 8.69e-05 | -0.21 | 3.49e-10 | - |
| RLS | ar1 | S5 src 30cm cont | +0.11 | 0.158 | -0.17 | 1.55e-06 | - |
| RLS | ar1 | R2 rig 30cm | +0.25 | 0.762 | -0.18 | 0.573 | - |
| RLS | harmonic | S8 stationary | -1.32 | 1.11e-07 | -0.25 | 5.53e-08 | win |
| RLS | harmonic | S2 src 30cm | +0.98 | 1 | -0.27 | 5.02e-10 | - |
| RLS | harmonic | S5 src 30cm cont | +0.81 | 0.00133 | +0.16 | 0.117 | - |
| RLS | harmonic | R2 rig 30cm | +0.85 | 0.532 | +0.00 | 1 | - |
| VFF-RLS | ar1 | S8 stationary | -10.13 | 3.49e-10 | -0.17 | 6.55e-06 | win |
| VFF-RLS | ar1 | S2 src 30cm | +0.24 | 0.28 | -0.16 | 2.22e-09 | - |
| VFF-RLS | ar1 | S5 src 30cm cont | +0.11 | 1 | -0.13 | 0.00015 | - |
| VFF-RLS | ar1 | R2 rig 30cm | +0.23 | 0.849 | -0.06 | 1 | - |
| VFF-RLS | harmonic | S8 stationary | -6.65 | 2.33e-10 | -0.14 | 9.13e-06 | win |
| VFF-RLS | harmonic | S2 src 30cm | +0.69 | 1 | -0.21 | 1.6e-09 | - |
| VFF-RLS | harmonic | S5 src 30cm cont | +0.66 | 0.0386 | +0.16 | 0.0575 | - |
| VFF-RLS | harmonic | R2 rig 30cm | +0.63 | 0.762 | +0.00 | 1 | - |
| FD-FxNLMS + det | ar1 | S8 stationary | +0.85 | 1 | -0.57 | 5.02e-10 | win |
| FD-FxNLMS + det | ar1 | S2 src 30cm | -0.10 | 0.85 | -0.47 | 2.33e-10 | - |
| FD-FxNLMS + det | ar1 | S5 src 30cm cont | -0.13 | 1 | -0.51 | 2.33e-10 | win |
| FD-FxNLMS + det | ar1 | R2 rig 30cm | +0.02 | 1 | -0.25 | 1 | - |
| FD-FxNLMS + det | harmonic | S8 stationary | -2.73 | 2.33e-10 | -1.37 | 2.33e-10 | win |
| FD-FxNLMS + det | harmonic | S2 src 30cm | -1.32 | 0.000614 | -2.24 | 2.33e-10 | win |
| FD-FxNLMS + det | harmonic | S5 src 30cm cont | -1.14 | 0.00425 | -1.90 | 2.33e-10 | win |
| FD-FxNLMS + det | harmonic | R2 rig 30cm | -0.53 | 0.0382 | -2.48 | 0.00468 | win |
| RLS + det | ar1 | S8 stationary | -4.45 | 1.13e-09 | +0.24 | 1.75e-06 | win |
| RLS + det | ar1 | S2 src 30cm | -0.02 | 1 | +0.12 | 2.24e-06 | - |
| RLS + det | ar1 | S5 src 30cm cont | +0.01 | 1 | +0.09 | 0.154 | - |
| RLS + det | ar1 | R2 rig 30cm | -0.06 | 1 | +0.50 | 4.88e-06 | - |
| RLS + det | harmonic | S8 stationary | -1.26 | 1.81e-07 | +0.19 | 3.49e-10 | win |
| RLS + det | harmonic | S2 src 30cm | +2.81 | 2.33e-10 | +0.14 | 2.33e-10 | loss |
| RLS + det | harmonic | S5 src 30cm cont | +0.85 | 2.41e-05 | +0.12 | 1.2e-06 | - |
| RLS + det | harmonic | R2 rig 30cm | +0.00 | 1 | +1.25 | 0.000298 | loss |

Counts (E-PCG): win 35, loss 2, mixed 0, none 27 (of 64)

## E-PCG bank vs baselines (Wilcoxon pratt on seeds; Holm over 128)
| baseline | noise | cell | med dA1 | p_Holm A1 | med dA2 | p_Holm A2 | label |
|---|---|---|---|---|---|---|---|
| FD-FxNLMS | ar1 | S8 stationary | -0.09 | 1 | -0.83 | 1.8e-09 | win |
| FD-FxNLMS | ar1 | S2 src 30cm | -0.08 | 1 | -0.66 | 3.82e-10 | win |
| FD-FxNLMS | ar1 | S5 src 30cm cont | -0.12 | 1 | -0.63 | 3.82e-10 | win |
| FD-FxNLMS | ar1 | R2 rig 30cm | +0.34 | 0.395 | -0.61 | 0.00219 | win |
| FD-FxNLMS | harmonic | S8 stationary | -2.22 | 2.33e-10 | -1.49 | 2.33e-10 | win |
| FD-FxNLMS | harmonic | S2 src 30cm | -0.27 | 1 | -1.81 | 2.33e-10 | win |
| FD-FxNLMS | harmonic | S5 src 30cm cont | -1.06 | 0.0358 | -1.82 | 2.33e-10 | win |
| FD-FxNLMS | harmonic | R2 rig 30cm | +0.00 | 1 | -1.24 | 0.0246 | win |
| leaky FD-FxNLMS | ar1 | S8 stationary | -0.37 | 1 | -0.49 | 6.14e-08 | - |
| leaky FD-FxNLMS | ar1 | S2 src 30cm | +0.15 | 0.677 | -0.30 | 1.48e-07 | - |
| leaky FD-FxNLMS | ar1 | S5 src 30cm cont | +0.19 | 0.899 | -0.25 | 1.19e-06 | - |
| leaky FD-FxNLMS | ar1 | R2 rig 30cm | +0.63 | 0.000685 | -0.19 | 0.409 | - |
| leaky FD-FxNLMS | harmonic | S8 stationary | -2.18 | 2.33e-10 | -2.05 | 2.33e-10 | win |
| leaky FD-FxNLMS | harmonic | S2 src 30cm | +0.06 | 1 | -2.14 | 2.33e-10 | win |
| leaky FD-FxNLMS | harmonic | S5 src 30cm cont | -0.80 | 0.616 | -2.13 | 2.33e-10 | win |
| leaky FD-FxNLMS | harmonic | R2 rig 30cm | +0.00 | 1 | -0.99 | 0.025 | win |
| convex FD-FxNLMS | ar1 | S8 stationary | +0.98 | 0.395 | -0.62 | 3.5e-08 | win |
| convex FD-FxNLMS | ar1 | S2 src 30cm | -0.07 | 1 | -0.42 | 1.24e-08 | - |
| convex FD-FxNLMS | ar1 | S5 src 30cm cont | +0.05 | 1 | -0.40 | 2.92e-08 | - |
| convex FD-FxNLMS | ar1 | R2 rig 30cm | +0.44 | 0.0285 | -0.36 | 0.0517 | - |
| convex FD-FxNLMS | harmonic | S8 stationary | -1.11 | 1.71e-07 | -1.35 | 2.33e-10 | win |
| convex FD-FxNLMS | harmonic | S2 src 30cm | +0.49 | 1 | -1.84 | 2.33e-10 | win |
| convex FD-FxNLMS | harmonic | S5 src 30cm cont | -0.24 | 1 | -1.64 | 2.33e-10 | win |
| convex FD-FxNLMS | harmonic | R2 rig 30cm | +0.00 | 1 | -1.32 | 0.0214 | win |
| FDKF | ar1 | S8 stationary | -1.64 | 0.0524 | -1.46 | 2.33e-10 | win |
| FDKF | ar1 | S2 src 30cm | -0.99 | 0.000409 | -1.30 | 2.33e-10 | win |
| FDKF | ar1 | S5 src 30cm cont | -0.91 | 0.00188 | -1.26 | 2.33e-10 | win |
| FDKF | ar1 | R2 rig 30cm | -0.40 | 1 | -1.37 | 0.000227 | win |
| FDKF | harmonic | S8 stationary | -3.50 | 2.33e-10 | -2.50 | 2.33e-10 | win |
| FDKF | harmonic | S2 src 30cm | -0.64 | 1 | -2.59 | 2.33e-10 | win |
| FDKF | harmonic | S5 src 30cm cont | -0.62 | 1 | -2.43 | 2.33e-10 | win |
| FDKF | harmonic | R2 rig 30cm | +0.43 | 0.522 | +0.00 | 1 | - |
| RLS | ar1 | S8 stationary | -4.63 | 1.29e-09 | -0.22 | 2.29e-05 | win |
| RLS | ar1 | S2 src 30cm | +0.33 | 4.56e-05 | -0.10 | 0.0285 | - |
| RLS | ar1 | S5 src 30cm cont | +0.25 | 0.0193 | -0.02 | 1 | - |
| RLS | ar1 | R2 rig 30cm | +0.68 | 1 | -0.31 | 0.000477 | - |
| RLS | harmonic | S8 stationary | -1.30 | 3.4e-05 | -0.36 | 1.48e-07 | win |
| RLS | harmonic | S2 src 30cm | +0.83 | 0.789 | -0.35 | 3.76e-07 | - |
| RLS | harmonic | S5 src 30cm cont | +0.03 | 1 | -0.30 | 2.29e-05 | - |
| RLS | harmonic | R2 rig 30cm | +1.53 | 0.0343 | +0.00 | 1 | loss |
| VFF-RLS | ar1 | S8 stationary | -10.06 | 3.82e-10 | -0.22 | 7.28e-05 | win |
| VFF-RLS | ar1 | S2 src 30cm | +0.26 | 0.251 | -0.09 | 0.686 | - |
| VFF-RLS | ar1 | S5 src 30cm cont | +0.22 | 1 | -0.00 | 1 | - |
| VFF-RLS | ar1 | R2 rig 30cm | +0.60 | 1 | -0.27 | 0.00132 | - |
| VFF-RLS | harmonic | S8 stationary | -6.50 | 2.33e-10 | -0.26 | 7.57e-06 | win |
| VFF-RLS | harmonic | S2 src 30cm | +0.59 | 1 | -0.28 | 2.57e-06 | - |
| VFF-RLS | harmonic | S5 src 30cm cont | -0.12 | 1 | -0.29 | 7.92e-05 | - |
| VFF-RLS | harmonic | R2 rig 30cm | +1.40 | 0.0444 | +0.00 | 1 | loss |
| FD-FxNLMS + det | ar1 | S8 stationary | +1.00 | 1 | -0.57 | 1.54e-08 | win |
| FD-FxNLMS + det | ar1 | S2 src 30cm | -0.04 | 1 | -0.36 | 2.92e-08 | - |
| FD-FxNLMS + det | ar1 | S5 src 30cm cont | -0.03 | 1 | -0.36 | 5.14e-08 | - |
| FD-FxNLMS + det | ar1 | R2 rig 30cm | +0.39 | 0.789 | -0.37 | 0.0524 | - |
| FD-FxNLMS + det | harmonic | S8 stationary | -2.59 | 2.33e-10 | -1.42 | 2.33e-10 | win |
| FD-FxNLMS + det | harmonic | S2 src 30cm | -1.05 | 0.0247 | -2.31 | 2.33e-10 | win |
| FD-FxNLMS + det | harmonic | S5 src 30cm cont | -1.80 | 0.000193 | -2.20 | 2.33e-10 | win |
| FD-FxNLMS + det | harmonic | R2 rig 30cm | +0.00 | 1 | -0.50 | 0.063 | - |
| RLS + det | ar1 | S8 stationary | -4.44 | 1.29e-09 | +0.15 | 7.92e-05 | win |
| RLS + det | ar1 | S2 src 30cm | -0.01 | 1 | +0.23 | 1.34e-06 | - |
| RLS + det | ar1 | S5 src 30cm cont | +0.08 | 1 | +0.22 | 0.00244 | - |
| RLS + det | ar1 | R2 rig 30cm | +0.06 | 1 | +0.32 | 5.36e-06 | - |
| RLS + det | harmonic | S8 stationary | -1.25 | 4.97e-05 | +0.09 | 0.000149 | win |
| RLS + det | harmonic | S2 src 30cm | +3.00 | 9.8e-09 | +0.09 | 9.28e-10 | loss |
| RLS + det | harmonic | S5 src 30cm cont | -0.07 | 1 | -0.27 | 0.0145 | - |
| RLS + det | harmonic | R2 rig 30cm | +0.74 | 0.786 | +0.28 | 0.00575 | - |

Counts (E-PCG bank): win 34, loss 3, mixed 0, none 27 (of 64)

## E-PCG bank - E-PCG (main) (Holm over 16)
| noise | cell | key | median d | p_Holm |
|---|---|---|---|---|
| ar1 | S8 stationary | A1 | +0.02 | 2.29e-06 |
| ar1 | S8 stationary | A2 | -0.09 | 0.922 |
| ar1 | S2 src 30cm | A1 | +0.06 | 0.0563 |
| ar1 | S2 src 30cm | A2 | +0.12 | 1.83e-05 |
| ar1 | S5 src 30cm cont | A1 | +0.08 | 0.0563 |
| ar1 | S5 src 30cm cont | A2 | +0.13 | 1.31e-06 |
| ar1 | R2 rig 30cm | A1 | +0.33 | 0.0707 |
| ar1 | R2 rig 30cm | A2 | -0.16 | 0.00943 |
| harmonic | S8 stationary | A1 | +0.04 | 3.83e-05 |
| harmonic | S8 stationary | A2 | -0.11 | 0.000792 |
| harmonic | S2 src 30cm | A1 | +0.55 | 0.922 |
| harmonic | S2 src 30cm | A2 | -0.06 | 0.00362 |
| harmonic | S5 src 30cm cont | A1 | -0.78 | 0.00604 |
| harmonic | S5 src 30cm cont | A2 | -0.35 | 1.75e-06 |
| harmonic | R2 rig 30cm | A1 | +0.48 | 0.00148 |
| harmonic | R2 rig 30cm | A2 | +0.00 | 0.922 |

## Reach fraction at level -9 dB (tau <= t; t in [0.3, 0.5, 1.0, 2.0, 3.0, 4.0] s)
| method | noise | cell | t=0.3 | t=0.5 | t=1.0 | t=2.0 | t=3.0 | t=4.0 |
|---|---|---|---|---|---|---|---|---|
| FD-FxNLMS | ar1 | S8 stationary | 0.00 | 0.17 | 0.88 | 1.00 | 1.00 | 1.00 |
| FD-FxNLMS | ar1 | S2 src 30cm | 0.42 | 0.82 | 1.00 | 1.00 | 1.00 | 1.00 |
| FD-FxNLMS | ar1 | S5 src 30cm cont | 0.57 | 0.90 | 0.97 | 1.00 | 1.00 | 1.00 |
| FD-FxNLMS | ar1 | R2 rig 30cm | 0.12 | 0.33 | 0.68 | 0.85 | 0.88 | 0.90 |
| FD-FxNLMS | harmonic | S8 stationary | 0.00 | 0.23 | 0.78 | 0.97 | 0.97 | 1.00 |
| FD-FxNLMS | harmonic | S2 src 30cm | 0.03 | 0.45 | 0.95 | 0.97 | 1.00 | 1.00 |
| FD-FxNLMS | harmonic | S5 src 30cm cont | 0.53 | 0.82 | 0.97 | 1.00 | 1.00 | 1.00 |
| FD-FxNLMS | harmonic | R2 rig 30cm | 0.03 | 0.03 | 0.07 | 0.12 | 0.15 | 0.15 |
| leaky FD-FxNLMS | ar1 | S8 stationary | 0.00 | 0.20 | 0.93 | 1.00 | 1.00 | 1.00 |
| leaky FD-FxNLMS | ar1 | S2 src 30cm | 0.50 | 0.88 | 1.00 | 1.00 | 1.00 | 1.00 |
| leaky FD-FxNLMS | ar1 | S5 src 30cm cont | 0.75 | 0.95 | 0.97 | 1.00 | 1.00 | 1.00 |
| leaky FD-FxNLMS | ar1 | R2 rig 30cm | 0.23 | 0.45 | 0.75 | 0.90 | 0.95 | 0.95 |
| leaky FD-FxNLMS | harmonic | S8 stationary | 0.00 | 0.30 | 0.78 | 0.97 | 0.97 | 0.97 |
| leaky FD-FxNLMS | harmonic | S2 src 30cm | 0.03 | 0.68 | 0.95 | 0.97 | 0.97 | 1.00 |
| leaky FD-FxNLMS | harmonic | S5 src 30cm cont | 0.57 | 0.85 | 0.97 | 0.97 | 0.97 | 1.00 |
| leaky FD-FxNLMS | harmonic | R2 rig 30cm | 0.03 | 0.03 | 0.07 | 0.12 | 0.15 | 0.15 |
| convex FD-FxNLMS | ar1 | S8 stationary | 0.00 | 0.40 | 0.90 | 1.00 | 1.00 | 1.00 |
| convex FD-FxNLMS | ar1 | S2 src 30cm | 0.47 | 0.82 | 0.97 | 1.00 | 1.00 | 1.00 |
| convex FD-FxNLMS | ar1 | S5 src 30cm cont | 0.65 | 0.95 | 0.97 | 1.00 | 1.00 | 1.00 |
| convex FD-FxNLMS | ar1 | R2 rig 30cm | 0.12 | 0.38 | 0.70 | 0.90 | 0.93 | 0.95 |
| convex FD-FxNLMS | harmonic | S8 stationary | 0.00 | 0.57 | 0.88 | 0.97 | 0.97 | 1.00 |
| convex FD-FxNLMS | harmonic | S2 src 30cm | 0.07 | 0.70 | 0.97 | 0.97 | 1.00 | 1.00 |
| convex FD-FxNLMS | harmonic | S5 src 30cm cont | 0.70 | 0.93 | 0.97 | 1.00 | 1.00 | 1.00 |
| convex FD-FxNLMS | harmonic | R2 rig 30cm | 0.03 | 0.03 | 0.07 | 0.15 | 0.15 | 0.15 |
| FDKF | ar1 | S8 stationary | 0.00 | 0.00 | 0.28 | 0.95 | 1.00 | 1.00 |
| FDKF | ar1 | S2 src 30cm | 0.10 | 0.40 | 0.72 | 1.00 | 1.00 | 1.00 |
| FDKF | ar1 | S5 src 30cm cont | 0.30 | 0.50 | 0.90 | 0.97 | 1.00 | 1.00 |
| FDKF | ar1 | R2 rig 30cm | 0.00 | 0.17 | 0.50 | 0.80 | 0.88 | 0.90 |
| FDKF | harmonic | S8 stationary | 0.00 | 0.00 | 0.68 | 0.95 | 0.97 | 1.00 |
| FDKF | harmonic | S2 src 30cm | 0.03 | 0.40 | 0.93 | 0.97 | 1.00 | 1.00 |
| FDKF | harmonic | S5 src 30cm cont | 0.70 | 0.82 | 0.97 | 1.00 | 1.00 | 1.00 |
| FDKF | harmonic | R2 rig 30cm | 0.03 | 0.10 | 0.38 | 0.45 | 0.50 | 0.50 |
| RLS | ar1 | S8 stationary | 0.00 | 0.47 | 0.97 | 0.97 | 0.97 | 0.97 |
| RLS | ar1 | S2 src 30cm | 0.55 | 0.90 | 0.97 | 0.97 | 0.97 | 0.97 |
| RLS | ar1 | S5 src 30cm cont | 0.75 | 0.97 | 0.97 | 0.97 | 0.97 | 0.97 |
| RLS | ar1 | R2 rig 30cm | 0.25 | 0.40 | 0.68 | 0.72 | 0.72 | 0.72 |
| RLS | harmonic | S8 stationary | 0.00 | 0.97 | 1.00 | 1.00 | 1.00 | 1.00 |
| RLS | harmonic | S2 src 30cm | 0.12 | 0.95 | 1.00 | 1.00 | 1.00 | 1.00 |
| RLS | harmonic | S5 src 30cm cont | 0.93 | 0.97 | 1.00 | 1.00 | 1.00 | 1.00 |
| RLS | harmonic | R2 rig 30cm | 0.05 | 0.35 | 0.50 | 0.57 | 0.60 | 0.60 |
| VFF-RLS | ar1 | S8 stationary | 0.00 | 0.38 | 0.88 | 0.88 | 0.88 | 0.88 |
| VFF-RLS | ar1 | S2 src 30cm | 0.50 | 0.80 | 0.88 | 0.88 | 0.88 | 0.88 |
| VFF-RLS | ar1 | S5 src 30cm cont | 0.70 | 0.88 | 0.88 | 0.88 | 0.88 | 0.88 |
| VFF-RLS | ar1 | R2 rig 30cm | 0.28 | 0.40 | 0.68 | 0.72 | 0.72 | 0.72 |
| VFF-RLS | harmonic | S8 stationary | 0.00 | 0.97 | 1.00 | 1.00 | 1.00 | 1.00 |
| VFF-RLS | harmonic | S2 src 30cm | 0.10 | 0.95 | 1.00 | 1.00 | 1.00 | 1.00 |
| VFF-RLS | harmonic | S5 src 30cm cont | 0.93 | 0.97 | 1.00 | 1.00 | 1.00 | 1.00 |
| VFF-RLS | harmonic | R2 rig 30cm | 0.05 | 0.30 | 0.50 | 0.57 | 0.60 | 0.60 |
| FD-FxNLMS + det | ar1 | S8 stationary | 0.00 | 0.23 | 0.88 | 0.97 | 1.00 | 1.00 |
| FD-FxNLMS + det | ar1 | S2 src 30cm | 0.38 | 0.65 | 0.95 | 1.00 | 1.00 | 1.00 |
| FD-FxNLMS + det | ar1 | S5 src 30cm cont | 0.62 | 0.85 | 0.97 | 1.00 | 1.00 | 1.00 |
| FD-FxNLMS + det | ar1 | R2 rig 30cm | 0.10 | 0.30 | 0.65 | 0.93 | 0.97 | 1.00 |
| FD-FxNLMS + det | harmonic | S8 stationary | 0.00 | 0.10 | 0.68 | 0.95 | 0.97 | 1.00 |
| FD-FxNLMS + det | harmonic | S2 src 30cm | 0.00 | 0.15 | 0.80 | 0.97 | 1.00 | 1.00 |
| FD-FxNLMS + det | harmonic | S5 src 30cm cont | 0.25 | 0.62 | 0.95 | 1.00 | 1.00 | 1.00 |
| FD-FxNLMS + det | harmonic | R2 rig 30cm | 0.00 | 0.00 | 0.07 | 0.12 | 0.17 | 0.17 |
| RLS + det | ar1 | S8 stationary | 0.00 | 0.53 | 0.97 | 0.97 | 0.97 | 0.97 |
| RLS + det | ar1 | S2 src 30cm | 0.28 | 0.72 | 0.97 | 0.97 | 0.97 | 0.97 |
| RLS + det | ar1 | S5 src 30cm cont | 0.62 | 0.90 | 0.97 | 0.97 | 0.97 | 0.97 |
| RLS + det | ar1 | R2 rig 30cm | 0.15 | 0.35 | 0.82 | 0.93 | 0.97 | 0.97 |
| RLS + det | harmonic | S8 stationary | 0.00 | 0.93 | 1.00 | 1.00 | 1.00 | 1.00 |
| RLS + det | harmonic | S2 src 30cm | 0.70 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 |
| RLS + det | harmonic | S5 src 30cm cont | 0.90 | 0.97 | 1.00 | 1.00 | 1.00 | 1.00 |
| RLS + det | harmonic | R2 rig 30cm | 0.05 | 0.33 | 0.50 | 0.65 | 0.68 | 0.78 |
| E-PCG | ar1 | S8 stationary | 0.00 | 0.60 | 1.00 | 1.00 | 1.00 | 1.00 |
| E-PCG | ar1 | S2 src 30cm | 0.35 | 0.68 | 1.00 | 1.00 | 1.00 | 1.00 |
| E-PCG | ar1 | S5 src 30cm cont | 0.68 | 0.93 | 1.00 | 1.00 | 1.00 | 1.00 |
| E-PCG | ar1 | R2 rig 30cm | 0.17 | 0.45 | 0.80 | 0.88 | 0.88 | 0.88 |
| E-PCG | harmonic | S8 stationary | 0.23 | 0.93 | 1.00 | 1.00 | 1.00 | 1.00 |
| E-PCG | harmonic | S2 src 30cm | 0.28 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 |
| E-PCG | harmonic | S5 src 30cm cont | 0.75 | 0.95 | 1.00 | 1.00 | 1.00 | 1.00 |
| E-PCG | harmonic | R2 rig 30cm | 0.03 | 0.42 | 0.47 | 0.53 | 0.53 | 0.55 |
| E-PCG bank | ar1 | S8 stationary | 0.00 | 0.55 | 1.00 | 1.00 | 1.00 | 1.00 |
| E-PCG bank | ar1 | S2 src 30cm | 0.38 | 0.68 | 1.00 | 1.00 | 1.00 | 1.00 |
| E-PCG bank | ar1 | S5 src 30cm cont | 0.60 | 0.93 | 0.97 | 1.00 | 1.00 | 1.00 |
| E-PCG bank | ar1 | R2 rig 30cm | 0.15 | 0.33 | 0.78 | 0.95 | 0.97 | 0.97 |
| E-PCG bank | harmonic | S8 stationary | 0.23 | 0.85 | 1.00 | 1.00 | 1.00 | 1.00 |
| E-PCG bank | harmonic | S2 src 30cm | 0.23 | 0.97 | 1.00 | 1.00 | 1.00 | 1.00 |
| E-PCG bank | harmonic | S5 src 30cm cont | 0.95 | 0.95 | 1.00 | 1.00 | 1.00 | 1.00 |
| E-PCG bank | harmonic | R2 rig 30cm | 0.05 | 0.25 | 0.38 | 0.50 | 0.53 | 0.60 |

## Reach fraction at level -12 dB (tau <= t; t in [0.3, 0.5, 1.0, 2.0, 3.0, 4.0] s)
| method | noise | cell | t=0.3 | t=0.5 | t=1.0 | t=2.0 | t=3.0 | t=4.0 |
|---|---|---|---|---|---|---|---|---|
| FD-FxNLMS | ar1 | S8 stationary | 0.00 | 0.03 | 0.12 | 0.17 | 0.28 | 0.42 |
| FD-FxNLMS | ar1 | S2 src 30cm | 0.00 | 0.05 | 0.12 | 0.20 | 0.35 | 0.42 |
| FD-FxNLMS | ar1 | S5 src 30cm cont | 0.00 | 0.03 | 0.10 | 0.20 | 0.35 | 0.40 |
| FD-FxNLMS | ar1 | R2 rig 30cm | 0.00 | 0.00 | 0.03 | 0.12 | 0.15 | 0.17 |
| FD-FxNLMS | harmonic | S8 stationary | 0.00 | 0.00 | 0.38 | 0.57 | 0.78 | 0.78 |
| FD-FxNLMS | harmonic | S2 src 30cm | 0.00 | 0.00 | 0.50 | 0.70 | 0.75 | 0.80 |
| FD-FxNLMS | harmonic | S5 src 30cm cont | 0.00 | 0.15 | 0.55 | 0.72 | 0.80 | 0.80 |
| FD-FxNLMS | harmonic | R2 rig 30cm | 0.00 | 0.00 | 0.00 | 0.03 | 0.03 | 0.03 |
| leaky FD-FxNLMS | ar1 | S8 stationary | 0.00 | 0.03 | 0.15 | 0.28 | 0.35 | 0.42 |
| leaky FD-FxNLMS | ar1 | S2 src 30cm | 0.00 | 0.05 | 0.17 | 0.25 | 0.38 | 0.47 |
| leaky FD-FxNLMS | ar1 | S5 src 30cm cont | 0.00 | 0.03 | 0.10 | 0.28 | 0.40 | 0.45 |
| leaky FD-FxNLMS | ar1 | R2 rig 30cm | 0.00 | 0.03 | 0.03 | 0.15 | 0.20 | 0.25 |
| leaky FD-FxNLMS | harmonic | S8 stationary | 0.00 | 0.00 | 0.47 | 0.57 | 0.70 | 0.72 |
| leaky FD-FxNLMS | harmonic | S2 src 30cm | 0.00 | 0.00 | 0.53 | 0.68 | 0.72 | 0.78 |
| leaky FD-FxNLMS | harmonic | S5 src 30cm cont | 0.00 | 0.23 | 0.53 | 0.65 | 0.72 | 0.75 |
| leaky FD-FxNLMS | harmonic | R2 rig 30cm | 0.00 | 0.00 | 0.00 | 0.03 | 0.03 | 0.03 |
| convex FD-FxNLMS | ar1 | S8 stationary | 0.00 | 0.00 | 0.10 | 0.33 | 0.38 | 0.50 |
| convex FD-FxNLMS | ar1 | S2 src 30cm | 0.00 | 0.03 | 0.12 | 0.20 | 0.42 | 0.47 |
| convex FD-FxNLMS | ar1 | S5 src 30cm cont | 0.00 | 0.03 | 0.12 | 0.33 | 0.45 | 0.47 |
| convex FD-FxNLMS | ar1 | R2 rig 30cm | 0.00 | 0.00 | 0.03 | 0.17 | 0.20 | 0.23 |
| convex FD-FxNLMS | harmonic | S8 stationary | 0.00 | 0.23 | 0.47 | 0.68 | 0.78 | 0.80 |
| convex FD-FxNLMS | harmonic | S2 src 30cm | 0.00 | 0.05 | 0.50 | 0.70 | 0.72 | 0.78 |
| convex FD-FxNLMS | harmonic | S5 src 30cm cont | 0.07 | 0.45 | 0.57 | 0.70 | 0.78 | 0.78 |
| convex FD-FxNLMS | harmonic | R2 rig 30cm | 0.00 | 0.00 | 0.00 | 0.10 | 0.10 | 0.10 |
| FDKF | ar1 | S8 stationary | 0.00 | 0.00 | 0.03 | 0.05 | 0.07 | 0.15 |
| FDKF | ar1 | S2 src 30cm | 0.00 | 0.00 | 0.03 | 0.05 | 0.12 | 0.23 |
| FDKF | ar1 | S5 src 30cm cont | 0.00 | 0.00 | 0.00 | 0.10 | 0.17 | 0.23 |
| FDKF | ar1 | R2 rig 30cm | 0.00 | 0.00 | 0.00 | 0.03 | 0.05 | 0.07 |
| FDKF | harmonic | S8 stationary | 0.00 | 0.00 | 0.00 | 0.53 | 0.65 | 0.70 |
| FDKF | harmonic | S2 src 30cm | 0.00 | 0.00 | 0.38 | 0.57 | 0.68 | 0.72 |
| FDKF | harmonic | S5 src 30cm cont | 0.00 | 0.28 | 0.53 | 0.62 | 0.72 | 0.72 |
| FDKF | harmonic | R2 rig 30cm | 0.00 | 0.00 | 0.00 | 0.12 | 0.15 | 0.23 |
| RLS | ar1 | S8 stationary | 0.00 | 0.00 | 0.10 | 0.38 | 0.45 | 0.50 |
| RLS | ar1 | S2 src 30cm | 0.00 | 0.10 | 0.23 | 0.33 | 0.45 | 0.53 |
| RLS | ar1 | S5 src 30cm cont | 0.03 | 0.10 | 0.15 | 0.35 | 0.47 | 0.50 |
| RLS | ar1 | R2 rig 30cm | 0.00 | 0.03 | 0.05 | 0.10 | 0.15 | 0.17 |
| RLS | harmonic | S8 stationary | 0.00 | 0.60 | 0.90 | 0.95 | 0.97 | 0.97 |
| RLS | harmonic | S2 src 30cm | 0.00 | 0.17 | 0.93 | 0.97 | 0.97 | 1.00 |
| RLS | harmonic | S5 src 30cm cont | 0.28 | 0.70 | 0.97 | 0.97 | 0.97 | 1.00 |
| RLS | harmonic | R2 rig 30cm | 0.00 | 0.03 | 0.33 | 0.38 | 0.40 | 0.40 |
| VFF-RLS | ar1 | S8 stationary | 0.00 | 0.00 | 0.15 | 0.38 | 0.47 | 0.53 |
| VFF-RLS | ar1 | S2 src 30cm | 0.00 | 0.10 | 0.23 | 0.33 | 0.50 | 0.55 |
| VFF-RLS | ar1 | S5 src 30cm cont | 0.00 | 0.10 | 0.15 | 0.38 | 0.50 | 0.50 |
| VFF-RLS | ar1 | R2 rig 30cm | 0.00 | 0.03 | 0.05 | 0.10 | 0.17 | 0.17 |
| VFF-RLS | harmonic | S8 stationary | 0.00 | 0.60 | 0.90 | 0.95 | 0.97 | 1.00 |
| VFF-RLS | harmonic | S2 src 30cm | 0.00 | 0.07 | 0.90 | 0.97 | 0.97 | 1.00 |
| VFF-RLS | harmonic | S5 src 30cm cont | 0.12 | 0.68 | 0.97 | 0.97 | 0.97 | 1.00 |
| VFF-RLS | harmonic | R2 rig 30cm | 0.00 | 0.00 | 0.35 | 0.38 | 0.40 | 0.40 |
| FD-FxNLMS + det | ar1 | S8 stationary | 0.00 | 0.00 | 0.07 | 0.30 | 0.35 | 0.50 |
| FD-FxNLMS + det | ar1 | S2 src 30cm | 0.00 | 0.00 | 0.07 | 0.17 | 0.40 | 0.45 |
| FD-FxNLMS + det | ar1 | S5 src 30cm cont | 0.00 | 0.05 | 0.10 | 0.30 | 0.42 | 0.42 |
| FD-FxNLMS + det | ar1 | R2 rig 30cm | 0.00 | 0.00 | 0.00 | 0.10 | 0.15 | 0.17 |
| FD-FxNLMS + det | harmonic | S8 stationary | 0.00 | 0.00 | 0.15 | 0.55 | 0.68 | 0.72 |
| FD-FxNLMS + det | harmonic | S2 src 30cm | 0.00 | 0.00 | 0.15 | 0.55 | 0.70 | 0.78 |
| FD-FxNLMS + det | harmonic | S5 src 30cm cont | 0.00 | 0.00 | 0.47 | 0.65 | 0.72 | 0.78 |
| FD-FxNLMS + det | harmonic | R2 rig 30cm | 0.00 | 0.00 | 0.00 | 0.05 | 0.05 | 0.05 |
| RLS + det | ar1 | S8 stationary | 0.00 | 0.00 | 0.30 | 0.50 | 0.68 | 0.75 |
| RLS + det | ar1 | S2 src 30cm | 0.00 | 0.03 | 0.12 | 0.38 | 0.60 | 0.68 |
| RLS + det | ar1 | S5 src 30cm cont | 0.00 | 0.03 | 0.17 | 0.50 | 0.68 | 0.68 |
| RLS + det | ar1 | R2 rig 30cm | 0.00 | 0.00 | 0.05 | 0.23 | 0.28 | 0.35 |
| RLS + det | harmonic | S8 stationary | 0.00 | 0.60 | 0.90 | 0.97 | 0.97 | 1.00 |
| RLS + det | harmonic | S2 src 30cm | 0.28 | 0.75 | 0.95 | 0.97 | 1.00 | 1.00 |
| RLS + det | harmonic | S5 src 30cm cont | 0.12 | 0.55 | 0.88 | 0.95 | 0.97 | 1.00 |
| RLS + det | harmonic | R2 rig 30cm | 0.00 | 0.05 | 0.30 | 0.40 | 0.47 | 0.50 |
| E-PCG | ar1 | S8 stationary | 0.00 | 0.00 | 0.33 | 0.45 | 0.55 | 0.65 |
| E-PCG | ar1 | S2 src 30cm | 0.00 | 0.05 | 0.23 | 0.42 | 0.60 | 0.70 |
| E-PCG | ar1 | S5 src 30cm cont | 0.00 | 0.07 | 0.17 | 0.50 | 0.68 | 0.70 |
| E-PCG | ar1 | R2 rig 30cm | 0.00 | 0.03 | 0.05 | 0.12 | 0.20 | 0.25 |
| E-PCG | harmonic | S8 stationary | 0.00 | 0.55 | 0.90 | 0.97 | 0.97 | 1.00 |
| E-PCG | harmonic | S2 src 30cm | 0.03 | 0.72 | 0.95 | 0.95 | 0.97 | 1.00 |
| E-PCG | harmonic | S5 src 30cm cont | 0.12 | 0.35 | 0.93 | 0.97 | 1.00 | 1.00 |
| E-PCG | harmonic | R2 rig 30cm | 0.00 | 0.10 | 0.38 | 0.40 | 0.42 | 0.42 |
| E-PCG bank | ar1 | S8 stationary | 0.00 | 0.00 | 0.28 | 0.45 | 0.60 | 0.70 |
| E-PCG bank | ar1 | S2 src 30cm | 0.00 | 0.05 | 0.17 | 0.33 | 0.47 | 0.60 |
| E-PCG bank | ar1 | S5 src 30cm cont | 0.00 | 0.05 | 0.15 | 0.40 | 0.57 | 0.60 |
| E-PCG bank | ar1 | R2 rig 30cm | 0.00 | 0.00 | 0.03 | 0.12 | 0.25 | 0.30 |
| E-PCG bank | harmonic | S8 stationary | 0.00 | 0.53 | 0.88 | 0.93 | 0.97 | 0.97 |
| E-PCG bank | harmonic | S2 src 30cm | 0.00 | 0.75 | 0.95 | 0.95 | 0.95 | 1.00 |
| E-PCG bank | harmonic | S5 src 30cm cont | 0.55 | 0.72 | 0.93 | 0.95 | 0.97 | 1.00 |
| E-PCG bank | harmonic | R2 rig 30cm | 0.03 | 0.07 | 0.28 | 0.38 | 0.42 | 0.45 |

## Cost of the proposed methods (mean flop_hist / H = flops per sample; S8 / change cells)
| method | S8 | change cells |
|---|---|---|
| E-PCG | 8638 | 11773 |
| E-PCG bank | 16138 | 20486 |

## Diagnostics
- records 3200; unparsable 0; stale 0; duplicates 0 (differing 0)
- win / loss: each metric with its own Holm-adjusted p (A1 with p_A1, A2 with p_A2), thresholds 1 dB (A1) / 0.5 dB (A2)
- curves are ensemble means of the seed-summed powers: one failed run can dominate a curve (read with the failure table)
- cost of the baselines: analytic counts in the cost table (Step 6), not measured here
- runs stopped early (completed with no control): 99
