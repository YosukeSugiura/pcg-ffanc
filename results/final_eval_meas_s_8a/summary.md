# Revision 9-D: stationary measured paths (M-S)

# Final evaluation (evaluation seeds 480-519, M = 512, T = 5 s; rule docs/current/FINAL_EVAL_RULE.md)
Values: median (Q1, Q3) over the 40 seeds; failed runs: A1 = A2 = 0 dB, tau = 4 s (censored).

## Failures (runs out of 40)
| method | ar1 S8 | harmonic S8 |
|---|---|---|
| FD-FxNLMS | 6 | 2 |
| leaky FD-FxNLMS | 5 | 6 |
| convex FD-FxNLMS | 4 | 0 |
| FDKF | 6 | 0 |
| RLS | 0 | 0 |
| VFF-RLS | 0 | 0 |
| FD-FxNLMS + det | 6 | 0 |
| RLS + det | 0 | 0 |
| FD-FxNLMS + restart | 6 | 2 |
| SFTF + det | 0 | 0 |
| SFTF-H + det | 0 | 0 |
| CFTF + det | 0 | 0 |
| E-PCG | 0 | 0 |
| E-PCG bank | 0 | 0 |

## A1, noise = ar1
| method | S8 stationary |
|---|---|
| FD-FxNLMS | -2.06 (-4.08, -0.18) |
| leaky FD-FxNLMS | -1.59 (-3.79, 0.00) |
| convex FD-FxNLMS | -2.83 (-4.14, -0.92) |
| FDKF | 0.60 (0.00, 1.87) |
| RLS | -1.33 (-3.83, 2.05) |
| VFF-RLS | 2.16 (-1.76, 5.94) |
| FD-FxNLMS + det | -2.27 (-3.80, -0.87) |
| RLS + det | -1.55 (-4.05, 1.76) |
| FD-FxNLMS + restart | -2.06 (-4.08, -0.18) |
| SFTF + det | -1.57 (-4.06, 1.72) |
| SFTF-H + det | -1.57 (-4.06, 1.72) |
| CFTF + det | -1.57 (-4.06, 1.72) |
| E-PCG | -1.86 (-3.84, 1.63) |
| E-PCG bank | -1.79 (-3.81, 1.63) |

## A1, noise = harmonic
| method | S8 stationary |
|---|---|
| FD-FxNLMS | -5.23 (-6.80, -3.72) |
| leaky FD-FxNLMS | -4.77 (-6.72, -3.50) |
| convex FD-FxNLMS | -6.39 (-7.78, -4.03) |
| FDKF | -1.36 (-1.96, -0.75) |
| RLS | -6.30 (-8.82, -1.21) |
| VFF-RLS | -1.86 (-6.84, 4.79) |
| FD-FxNLMS + det | -4.94 (-6.44, -3.49) |
| RLS + det | -6.46 (-8.91, -1.40) |
| FD-FxNLMS + restart | -5.23 (-6.80, -3.72) |
| SFTF + det | -6.50 (-8.93, -1.44) |
| SFTF-H + det | -6.50 (-8.93, -1.44) |
| CFTF + det | -6.50 (-8.93, -1.44) |
| E-PCG | -5.50 (-8.82, 0.06) |
| E-PCG bank | -5.14 (-8.82, 0.07) |

## A2, noise = ar1
| method | S8 stationary |
|---|---|
| FD-FxNLMS | -3.82 (-5.75, -1.00) |
| leaky FD-FxNLMS | -3.89 (-5.62, -1.10) |
| convex FD-FxNLMS | -4.11 (-5.95, -1.07) |
| FDKF | -4.05 (-5.81, -0.91) |
| RLS | -4.96 (-6.77, -2.30) |
| VFF-RLS | -5.00 (-6.83, -2.33) |
| FD-FxNLMS + det | -4.23 (-5.87, -1.02) |
| RLS + det | -5.47 (-7.27, -2.71) |
| FD-FxNLMS + restart | -3.82 (-5.75, -1.00) |
| SFTF + det | -5.47 (-7.27, -2.71) |
| SFTF-H + det | -5.47 (-7.27, -2.71) |
| CFTF + det | -5.47 (-7.27, -2.71) |
| E-PCG | -5.22 (-7.01, -2.55) |
| E-PCG bank | -5.26 (-6.96, -2.67) |

## A2, noise = harmonic
| method | S8 stationary |
|---|---|
| FD-FxNLMS | -9.26 (-12.57, -6.37) |
| leaky FD-FxNLMS | -7.58 (-11.65, -4.37) |
| convex FD-FxNLMS | -11.26 (-13.60, -6.60) |
| FDKF | -10.31 (-12.68, -7.87) |
| RLS | -12.79 (-14.55, -10.27) |
| VFF-RLS | -12.91 (-14.65, -10.35) |
| FD-FxNLMS + det | -11.09 (-13.46, -6.49) |
| RLS + det | -13.44 (-15.08, -10.83) |
| FD-FxNLMS + restart | -9.26 (-12.57, -6.37) |
| SFTF + det | -13.44 (-15.08, -10.83) |
| SFTF-H + det | -13.44 (-15.08, -10.83) |
| CFTF + det | -13.44 (-15.08, -10.83) |
| E-PCG | -13.30 (-14.97, -10.70) |
| E-PCG bank | -13.33 (-15.05, -10.86) |

## tau9, noise = ar1
| method | S8 stationary |
|---|---|
| FD-FxNLMS | 4.00 (4.00, 4.00) |
| leaky FD-FxNLMS | 4.00 (4.00, 4.00) |
| convex FD-FxNLMS | 4.00 (4.00, 4.00) |
| FDKF | 4.00 (4.00, 4.00) |
| RLS | 4.00 (4.00, 4.00) |
| VFF-RLS | 4.00 (4.00, 4.00) |
| FD-FxNLMS + det | 4.00 (4.00, 4.00) |
| RLS + det | 4.00 (3.90, 4.00) |
| FD-FxNLMS + restart | 4.00 (4.00, 4.00) |
| SFTF + det | 4.00 (3.90, 4.00) |
| SFTF-H + det | 4.00 (3.90, 4.00) |
| CFTF + det | 4.00 (3.90, 4.00) |
| E-PCG | 4.00 (3.90, 4.00) |
| E-PCG bank | 4.00 (4.00, 4.00) |

## tau9, noise = harmonic
| method | S8 stationary |
|---|---|
| FD-FxNLMS | 1.15 (0.46, 4.00) |
| leaky FD-FxNLMS | 2.65 (0.46, 4.00) |
| convex FD-FxNLMS | 0.51 (0.35, 4.00) |
| FDKF | 1.54 (1.14, 4.00) |
| RLS | 0.38 (0.35, 0.45) |
| VFF-RLS | 0.40 (0.38, 0.46) |
| FD-FxNLMS + det | 0.97 (0.53, 4.00) |
| RLS + det | 0.38 (0.33, 0.45) |
| FD-FxNLMS + restart | 1.15 (0.46, 4.00) |
| SFTF + det | 0.38 (0.33, 0.45) |
| SFTF-H + det | 0.38 (0.33, 0.45) |
| CFTF + det | 0.38 (0.33, 0.45) |
| E-PCG | 0.36 (0.32, 0.47) |
| E-PCG bank | 0.36 (0.32, 0.52) |

## tau12, noise = ar1
| method | S8 stationary |
|---|---|
| FD-FxNLMS | 4.00 (4.00, 4.00) |
| leaky FD-FxNLMS | 4.00 (4.00, 4.00) |
| convex FD-FxNLMS | 4.00 (4.00, 4.00) |
| FDKF | 4.00 (4.00, 4.00) |
| RLS | 4.00 (4.00, 4.00) |
| VFF-RLS | 4.00 (4.00, 4.00) |
| FD-FxNLMS + det | 4.00 (4.00, 4.00) |
| RLS + det | 4.00 (4.00, 4.00) |
| FD-FxNLMS + restart | 4.00 (4.00, 4.00) |
| SFTF + det | 4.00 (4.00, 4.00) |
| SFTF-H + det | 4.00 (4.00, 4.00) |
| CFTF + det | 4.00 (4.00, 4.00) |
| E-PCG | 4.00 (4.00, 4.00) |
| E-PCG bank | 4.00 (4.00, 4.00) |

## tau12, noise = harmonic
| method | S8 stationary |
|---|---|
| FD-FxNLMS | 4.00 (1.45, 4.00) |
| leaky FD-FxNLMS | 4.00 (1.73, 4.00) |
| convex FD-FxNLMS | 4.00 (0.89, 4.00) |
| FDKF | 4.00 (2.08, 4.00) |
| RLS | 0.52 (0.40, 4.00) |
| VFF-RLS | 0.52 (0.42, 4.00) |
| FD-FxNLMS + det | 4.00 (1.42, 4.00) |
| RLS + det | 0.52 (0.40, 4.00) |
| FD-FxNLMS + restart | 4.00 (1.45, 4.00) |
| SFTF + det | 0.52 (0.40, 4.00) |
| SFTF-H + det | 0.52 (0.40, 4.00) |
| CFTF + det | 0.52 (0.40, 4.00) |
| E-PCG | 0.56 (0.39, 4.00) |
| E-PCG bank | 0.67 (0.39, 4.00) |

## E-PCG vs baselines (Wilcoxon pratt on seeds; Holm over 48)
| baseline | noise | cell | med dA1 | p_Holm A1 | med dA2 | p_Holm A2 | label |
|---|---|---|---|---|---|---|---|
| FD-FxNLMS | ar1 | S8 stationary | +0.76 | 0.0147 | -1.16 | 8.73e-11 | win |
| FD-FxNLMS | harmonic | S8 stationary | -0.03 | 1 | -2.83 | 8.73e-11 | win |
| leaky FD-FxNLMS | ar1 | S8 stationary | +0.39 | 0.215 | -1.16 | 8.73e-11 | win |
| leaky FD-FxNLMS | harmonic | S8 stationary | -0.34 | 1 | -4.01 | 8.73e-11 | win |
| convex FD-FxNLMS | ar1 | S8 stationary | +1.11 | 6.43e-05 | -1.01 | 8.73e-11 | mixed |
| convex FD-FxNLMS | harmonic | S8 stationary | +0.49 | 0.0871 | -2.03 | 8.73e-11 | win |
| FDKF | ar1 | S8 stationary | -2.62 | 0.00197 | -1.14 | 8.73e-11 | win |
| FDKF | harmonic | S8 stationary | -3.68 | 0.000926 | -2.26 | 8.73e-11 | win |
| RLS | ar1 | S8 stationary | -0.24 | 1 | -0.28 | 8.73e-11 | - |
| RLS | harmonic | S8 stationary | +1.00 | 0.00421 | -0.38 | 8.73e-11 | - |
| VFF-RLS | ar1 | S8 stationary | -3.50 | 2.18e-10 | -0.24 | 8.73e-11 | win |
| VFF-RLS | harmonic | S8 stationary | -2.71 | 1.55e-08 | -0.28 | 8.73e-11 | win |
| FD-FxNLMS + det | ar1 | S8 stationary | +0.73 | 0.0317 | -1.07 | 8.73e-11 | win |
| FD-FxNLMS + det | harmonic | S8 stationary | -0.68 | 1 | -2.11 | 8.73e-11 | win |
| RLS + det | ar1 | S8 stationary | +0.00 | 1 | +0.21 | 8.73e-11 | - |
| RLS + det | harmonic | S8 stationary | +1.14 | 0.000593 | +0.18 | 8.73e-11 | loss |
| FD-FxNLMS + restart | ar1 | S8 stationary | +0.76 | 0.0147 | -1.16 | 8.73e-11 | win |
| FD-FxNLMS + restart | harmonic | S8 stationary | -0.03 | 1 | -2.83 | 8.73e-11 | win |
| SFTF + det | ar1 | S8 stationary | +0.04 | 1 | +0.21 | 8.73e-11 | - |
| SFTF + det | harmonic | S8 stationary | +1.16 | 0.000379 | +0.18 | 8.73e-11 | loss |
| SFTF-H + det | ar1 | S8 stationary | +0.04 | 1 | +0.21 | 8.73e-11 | - |
| SFTF-H + det | harmonic | S8 stationary | +1.16 | 0.000379 | +0.18 | 8.73e-11 | loss |
| CFTF + det | ar1 | S8 stationary | +0.04 | 1 | +0.21 | 8.73e-11 | - |
| CFTF + det | harmonic | S8 stationary | +1.16 | 0.000379 | +0.18 | 8.73e-11 | loss |

Counts (E-PCG): win 13, loss 4, mixed 1, none 6 (of 24)

## E-PCG bank vs baselines (Wilcoxon pratt on seeds; Holm over 48)
| baseline | noise | cell | med dA1 | p_Holm A1 | med dA2 | p_Holm A2 | label |
|---|---|---|---|---|---|---|---|
| FD-FxNLMS | ar1 | S8 stationary | +0.74 | 0.0222 | -1.37 | 1.46e-10 | win |
| FD-FxNLMS | harmonic | S8 stationary | -0.01 | 1 | -3.04 | 8.73e-11 | win |
| leaky FD-FxNLMS | ar1 | S8 stationary | +0.39 | 0.25 | -1.40 | 1.46e-10 | win |
| leaky FD-FxNLMS | harmonic | S8 stationary | -0.31 | 1 | -4.22 | 8.73e-11 | win |
| convex FD-FxNLMS | ar1 | S8 stationary | +1.11 | 8.77e-05 | -1.17 | 6.37e-10 | mixed |
| convex FD-FxNLMS | harmonic | S8 stationary | +0.84 | 0.0765 | -2.19 | 8.73e-11 | win |
| FDKF | ar1 | S8 stationary | -2.64 | 0.00316 | -1.24 | 1.46e-10 | win |
| FDKF | harmonic | S8 stationary | -3.64 | 0.00157 | -2.48 | 8.73e-11 | win |
| RLS | ar1 | S8 stationary | -0.25 | 1 | -0.40 | 9.8e-07 | - |
| RLS | harmonic | S8 stationary | +1.09 | 0.00345 | -0.56 | 8.73e-11 | mixed |
| VFF-RLS | ar1 | S8 stationary | -3.52 | 3.27e-10 | -0.36 | 2.54e-06 | win |
| VFF-RLS | harmonic | S8 stationary | -2.70 | 2.23e-08 | -0.46 | 8.73e-11 | win |
| FD-FxNLMS + det | ar1 | S8 stationary | +0.74 | 0.0488 | -1.20 | 6.37e-10 | win |
| FD-FxNLMS + det | harmonic | S8 stationary | -0.43 | 1 | -2.30 | 8.73e-11 | win |
| RLS + det | ar1 | S8 stationary | +0.01 | 1 | +0.05 | 0.00344 | - |
| RLS + det | harmonic | S8 stationary | +1.18 | 0.000547 | -0.02 | 0.25 | loss |
| FD-FxNLMS + restart | ar1 | S8 stationary | +0.74 | 0.0222 | -1.37 | 1.46e-10 | win |
| FD-FxNLMS + restart | harmonic | S8 stationary | -0.01 | 1 | -3.04 | 8.73e-11 | win |
| SFTF + det | ar1 | S8 stationary | +0.04 | 1 | +0.05 | 0.00344 | - |
| SFTF + det | harmonic | S8 stationary | +1.20 | 0.000302 | -0.02 | 0.25 | loss |
| SFTF-H + det | ar1 | S8 stationary | +0.04 | 1 | +0.05 | 0.00344 | - |
| SFTF-H + det | harmonic | S8 stationary | +1.20 | 0.000302 | -0.02 | 0.25 | loss |
| CFTF + det | ar1 | S8 stationary | +0.04 | 1 | +0.05 | 0.00344 | - |
| CFTF + det | harmonic | S8 stationary | +1.20 | 0.000302 | -0.02 | 0.25 | loss |

Counts (E-PCG bank): win 13, loss 4, mixed 2, none 5 (of 24)

## E-PCG bank - E-PCG (main) (Holm over 4)
| noise | cell | key | median d | p_Holm |
|---|---|---|---|---|
| ar1 | S8 stationary | A1 | +0.00 | 0.202 |
| ar1 | S8 stationary | A2 | -0.13 | 0.0196 |
| harmonic | S8 stationary | A1 | +0.00 | 3.38e-05 |
| harmonic | S8 stationary | A2 | -0.21 | 2.29e-07 |

## Reach fraction at level -9 dB (tau <= t; t in [0.3, 0.5, 1.0, 2.0, 3.0, 4.0] s)
| method | noise | cell | t=0.3 | t=0.5 | t=1.0 | t=2.0 | t=3.0 | t=4.0 |
|---|---|---|---|---|---|---|---|---|
| FD-FxNLMS | ar1 | S8 stationary | 0.00 | 0.00 | 0.00 | 0.00 | 0.03 | 0.03 |
| FD-FxNLMS | harmonic | S8 stationary | 0.00 | 0.28 | 0.47 | 0.53 | 0.57 | 0.57 |
| leaky FD-FxNLMS | ar1 | S8 stationary | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.03 |
| leaky FD-FxNLMS | harmonic | S8 stationary | 0.00 | 0.30 | 0.42 | 0.50 | 0.50 | 0.50 |
| convex FD-FxNLMS | ar1 | S8 stationary | 0.00 | 0.00 | 0.00 | 0.03 | 0.05 | 0.05 |
| convex FD-FxNLMS | harmonic | S8 stationary | 0.00 | 0.47 | 0.53 | 0.55 | 0.57 | 0.57 |
| FDKF | ar1 | S8 stationary | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| FDKF | harmonic | S8 stationary | 0.00 | 0.00 | 0.10 | 0.57 | 0.57 | 0.62 |
| RLS | ar1 | S8 stationary | 0.00 | 0.00 | 0.03 | 0.12 | 0.15 | 0.15 |
| RLS | harmonic | S8 stationary | 0.20 | 0.82 | 0.93 | 0.97 | 0.97 | 0.97 |
| VFF-RLS | ar1 | S8 stationary | 0.00 | 0.00 | 0.07 | 0.15 | 0.17 | 0.17 |
| VFF-RLS | harmonic | S8 stationary | 0.00 | 0.82 | 0.95 | 0.97 | 0.97 | 0.97 |
| FD-FxNLMS + det | ar1 | S8 stationary | 0.00 | 0.00 | 0.00 | 0.03 | 0.05 | 0.05 |
| FD-FxNLMS + det | harmonic | S8 stationary | 0.00 | 0.20 | 0.50 | 0.53 | 0.57 | 0.57 |
| RLS + det | ar1 | S8 stationary | 0.00 | 0.00 | 0.12 | 0.20 | 0.23 | 0.25 |
| RLS + det | harmonic | S8 stationary | 0.23 | 0.82 | 0.95 | 0.97 | 0.97 | 0.97 |
| FD-FxNLMS + restart | ar1 | S8 stationary | 0.00 | 0.00 | 0.00 | 0.00 | 0.03 | 0.03 |
| FD-FxNLMS + restart | harmonic | S8 stationary | 0.00 | 0.28 | 0.47 | 0.53 | 0.57 | 0.57 |
| SFTF + det | ar1 | S8 stationary | 0.00 | 0.00 | 0.12 | 0.20 | 0.23 | 0.25 |
| SFTF + det | harmonic | S8 stationary | 0.23 | 0.82 | 0.95 | 0.97 | 0.97 | 0.97 |
| SFTF-H + det | ar1 | S8 stationary | 0.00 | 0.00 | 0.12 | 0.20 | 0.23 | 0.25 |
| SFTF-H + det | harmonic | S8 stationary | 0.23 | 0.82 | 0.95 | 0.97 | 0.97 | 0.97 |
| CFTF + det | ar1 | S8 stationary | 0.00 | 0.00 | 0.12 | 0.20 | 0.23 | 0.25 |
| CFTF + det | harmonic | S8 stationary | 0.23 | 0.82 | 0.95 | 0.97 | 0.97 | 0.97 |
| E-PCG | ar1 | S8 stationary | 0.00 | 0.00 | 0.15 | 0.23 | 0.23 | 0.25 |
| E-PCG | harmonic | S8 stationary | 0.10 | 0.80 | 0.95 | 0.97 | 0.97 | 0.97 |
| E-PCG bank | ar1 | S8 stationary | 0.00 | 0.00 | 0.12 | 0.17 | 0.17 | 0.20 |
| E-PCG bank | harmonic | S8 stationary | 0.10 | 0.72 | 0.95 | 0.97 | 0.97 | 0.97 |

## Reach fraction at level -12 dB (tau <= t; t in [0.3, 0.5, 1.0, 2.0, 3.0, 4.0] s)
| method | noise | cell | t=0.3 | t=0.5 | t=1.0 | t=2.0 | t=3.0 | t=4.0 |
|---|---|---|---|---|---|---|---|---|
| FD-FxNLMS | ar1 | S8 stationary | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| FD-FxNLMS | harmonic | S8 stationary | 0.00 | 0.00 | 0.17 | 0.35 | 0.42 | 0.42 |
| leaky FD-FxNLMS | ar1 | S8 stationary | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| leaky FD-FxNLMS | harmonic | S8 stationary | 0.00 | 0.00 | 0.12 | 0.30 | 0.35 | 0.40 |
| convex FD-FxNLMS | ar1 | S8 stationary | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| convex FD-FxNLMS | harmonic | S8 stationary | 0.00 | 0.07 | 0.30 | 0.42 | 0.47 | 0.47 |
| FDKF | ar1 | S8 stationary | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| FDKF | harmonic | S8 stationary | 0.00 | 0.00 | 0.00 | 0.25 | 0.42 | 0.47 |
| RLS | ar1 | S8 stationary | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| RLS | harmonic | S8 stationary | 0.00 | 0.47 | 0.57 | 0.57 | 0.57 | 0.57 |
| VFF-RLS | ar1 | S8 stationary | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| VFF-RLS | harmonic | S8 stationary | 0.00 | 0.47 | 0.57 | 0.57 | 0.57 | 0.57 |
| FD-FxNLMS + det | ar1 | S8 stationary | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| FD-FxNLMS + det | harmonic | S8 stationary | 0.00 | 0.00 | 0.15 | 0.38 | 0.45 | 0.47 |
| RLS + det | ar1 | S8 stationary | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| RLS + det | harmonic | S8 stationary | 0.00 | 0.47 | 0.57 | 0.62 | 0.62 | 0.62 |
| FD-FxNLMS + restart | ar1 | S8 stationary | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| FD-FxNLMS + restart | harmonic | S8 stationary | 0.00 | 0.00 | 0.17 | 0.35 | 0.42 | 0.42 |
| SFTF + det | ar1 | S8 stationary | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| SFTF + det | harmonic | S8 stationary | 0.00 | 0.47 | 0.57 | 0.62 | 0.62 | 0.62 |
| SFTF-H + det | ar1 | S8 stationary | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| SFTF-H + det | harmonic | S8 stationary | 0.00 | 0.47 | 0.57 | 0.62 | 0.62 | 0.62 |
| CFTF + det | ar1 | S8 stationary | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| CFTF + det | harmonic | S8 stationary | 0.00 | 0.47 | 0.57 | 0.62 | 0.62 | 0.62 |
| E-PCG | ar1 | S8 stationary | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| E-PCG | harmonic | S8 stationary | 0.00 | 0.47 | 0.57 | 0.60 | 0.62 | 0.62 |
| E-PCG bank | ar1 | S8 stationary | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| E-PCG bank | harmonic | S8 stationary | 0.00 | 0.47 | 0.57 | 0.62 | 0.62 | 0.62 |

## Cost of the proposed methods (mean flop_hist / H = flops per sample; S8 / change cells)
| method | S8 | change cells |
|---|---|---|
| E-PCG | 8167 | nan |
| E-PCG bank | 14866 | nan |

## Diagnostics
- records 1120; unparsable 0; stale 0; duplicates 0 (differing 0)
- win / loss: each metric with its own Holm-adjusted p (A1 with p_A1, A2 with p_A2), thresholds 1 dB (A1) / 0.5 dB (A2)
- curves are ensemble means of the seed-summed powers: one failed run can dominate a curve (read with the failure table)
- cost of the baselines: analytic counts in the cost table (Step 6), not measured here
- runs stopped early (completed with no control): 0

# M-S causal Wiener lower bound

| noise | total NR median (Q1,Q3) | ANC-only NR median (Q1,Q3) | norm >1000 |
|---|---|---|---|
| ar1 | -5.570 (-7.647, -3.017) | -5.682 (-7.855, -3.061) | 0/40 |
| harmonic | -13.378 (-15.547, -10.988) | -14.392 (-17.390, -11.514) | 0/40 |
