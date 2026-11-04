# MeshRIR measured-path evaluation (REVISION_RULE_8)

Dataset: MeshRIR v1.1, S32-M441; DOI 10.5281/zenodo.5500451.
License: Creative Commons Attribution 4.0 International (CC BY 4.0) (https://creativecommons.org/licenses/by/4.0/).
Attribution: Shoichi Koyama, Tomoya Nishida, Keisuke Kimura, Takumi Abe, Natsuki Ueno, Jesper Brunnström. Archive MD5: 4fcd6137bcadb6914d4170ff366c86f9.
Preprocessing: 48 kHz -> 8 kHz resample_poly(1,6), Kaiser 5; P=1200, S=512 samples; no delay removal; initial P/S normalization reused. Full details: provenance.json.
Scenario labels S2/R2 denote M-P/M-PS here, not 30 cm ISM source/rig moves. Holm: 48 tests per proposed method per set; bank-minus-main: 4.
M-PS keeps the initial secondary-path model fixed.

# Final evaluation (evaluation seeds 480-519, M = 512, T = 5 s; rule docs/current/FINAL_EVAL_RULE.md)
Values: median (Q1, Q3) over the 40 seeds; failed runs: A1 = A2 = 0 dB, tau = 4 s (censored).

## Failures (runs out of 40)
| method | ar1 S2 | harmonic S2 |
|---|---|---|
| FD-FxNLMS | 28 | 1 |
| leaky FD-FxNLMS | 27 | 6 |
| convex FD-FxNLMS | 23 | 0 |
| FDKF | 36 | 31 |
| RLS | 1 | 0 |
| VFF-RLS | 2 | 1 |
| FD-FxNLMS + det | 25 | 0 |
| RLS + det | 0 | 0 |
| FD-FxNLMS + restart | 28 | 1 |
| SFTF + det | 0 | 0 |
| SFTF-H + det | 0 | 0 |
| CFTF + det | 0 | 0 |
| E-PCG | 0 | 0 |
| E-PCG bank | 0 | 0 |

## A1, noise = ar1
| method | S2 src 30cm |
|---|---|
| FD-FxNLMS | 0.00 (0.00, 0.29) |
| leaky FD-FxNLMS | 0.00 (0.00, 0.35) |
| convex FD-FxNLMS | 0.00 (0.00, 0.27) |
| FDKF | 0.00 (0.00, 0.00) |
| RLS | 0.02 (-0.25, 0.35) |
| VFF-RLS | 0.00 (-0.26, 0.33) |
| FD-FxNLMS + det | 0.00 (0.00, 0.35) |
| RLS + det | 0.24 (-0.07, 0.58) |
| FD-FxNLMS + restart | 0.00 (0.00, 0.29) |
| SFTF + det | 0.24 (-0.07, 0.58) |
| SFTF-H + det | 0.24 (-0.07, 0.58) |
| CFTF + det | 0.24 (-0.07, 0.58) |
| E-PCG | 0.23 (-0.09, 0.53) |
| E-PCG bank | 0.09 (-0.26, 0.33) |

## A1, noise = harmonic
| method | S2 src 30cm |
|---|---|
| FD-FxNLMS | 0.15 (-0.31, 0.70) |
| leaky FD-FxNLMS | 0.00 (-0.41, 0.56) |
| convex FD-FxNLMS | -0.26 (-0.76, 0.30) |
| FDKF | 0.00 (0.00, 0.00) |
| RLS | -2.18 (-2.68, -1.68) |
| VFF-RLS | -1.91 (-2.50, -1.36) |
| FD-FxNLMS + det | -0.12 (-0.73, 0.26) |
| RLS + det | -1.67 (-2.17, -1.06) |
| FD-FxNLMS + restart | 0.31 (-0.33, 1.48) |
| SFTF + det | -0.92 (-1.28, -0.28) |
| SFTF-H + det | -1.68 (-2.17, -1.06) |
| CFTF + det | -1.67 (-2.17, -1.06) |
| E-PCG | -2.11 (-3.01, -1.75) |
| E-PCG bank | -2.90 (-3.50, -2.26) |

## A2, noise = ar1
| method | S2 src 30cm |
|---|---|
| FD-FxNLMS | 0.00 (-0.00, 0.00) |
| leaky FD-FxNLMS | 0.00 (0.00, 0.00) |
| convex FD-FxNLMS | 0.00 (-0.30, 0.00) |
| FDKF | 0.00 (0.00, 0.00) |
| RLS | -0.85 (-1.43, -0.58) |
| VFF-RLS | -0.87 (-1.48, -0.59) |
| FD-FxNLMS + det | 0.00 (-0.24, 0.00) |
| RLS + det | -1.02 (-1.33, -0.80) |
| FD-FxNLMS + restart | 0.00 (-0.01, 0.00) |
| SFTF + det | -1.02 (-1.33, -0.80) |
| SFTF-H + det | -1.02 (-1.33, -0.80) |
| CFTF + det | -1.02 (-1.33, -0.80) |
| E-PCG | -0.90 (-1.14, -0.65) |
| E-PCG bank | -0.82 (-1.03, -0.54) |

## A2, noise = harmonic
| method | S2 src 30cm |
|---|---|
| FD-FxNLMS | -3.83 (-4.96, -2.58) |
| leaky FD-FxNLMS | -3.07 (-4.56, -0.77) |
| convex FD-FxNLMS | -4.87 (-5.59, -4.09) |
| FDKF | 0.00 (0.00, 0.00) |
| RLS | -8.66 (-9.20, -8.28) |
| VFF-RLS | -8.73 (-9.25, -8.35) |
| FD-FxNLMS + det | -4.38 (-4.81, -3.91) |
| RLS + det | -8.17 (-8.49, -7.43) |
| FD-FxNLMS + restart | -3.81 (-5.01, -2.45) |
| SFTF + det | -7.96 (-8.35, -7.31) |
| SFTF-H + det | -8.04 (-8.39, -7.32) |
| CFTF + det | -8.14 (-8.48, -7.41) |
| E-PCG | -6.60 (-7.20, -5.77) |
| E-PCG bank | -6.62 (-7.25, -5.84) |

## tau9, noise = ar1
| method | S2 src 30cm |
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

## tau9, noise = harmonic
| method | S2 src 30cm |
|---|---|
| FD-FxNLMS | 4.00 (4.00, 4.00) |
| leaky FD-FxNLMS | 4.00 (4.00, 4.00) |
| convex FD-FxNLMS | 4.00 (4.00, 4.00) |
| FDKF | 4.00 (4.00, 4.00) |
| RLS | 1.47 (0.82, 3.66) |
| VFF-RLS | 1.31 (0.81, 2.77) |
| FD-FxNLMS + det | 4.00 (4.00, 4.00) |
| RLS + det | 2.57 (2.02, 3.90) |
| FD-FxNLMS + restart | 4.00 (4.00, 4.00) |
| SFTF + det | 2.63 (2.32, 3.91) |
| SFTF-H + det | 2.63 (2.26, 3.90) |
| CFTF + det | 2.57 (2.02, 3.90) |
| E-PCG | 4.00 (4.00, 4.00) |
| E-PCG bank | 4.00 (4.00, 4.00) |

## tau12, noise = ar1
| method | S2 src 30cm |
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
| method | S2 src 30cm |
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

## E-PCG vs baselines (Wilcoxon pratt on seeds; Holm over 48)
| baseline | noise | cell | med dA1 | p_Holm A1 | med dA2 | p_Holm A2 | label |
|---|---|---|---|---|---|---|---|
| FD-FxNLMS | ar1 | S2 src 30cm | -0.03 | 1 | -0.86 | 8.73e-11 | win |
| FD-FxNLMS | harmonic | S2 src 30cm | -2.33 | 1.46e-10 | -2.51 | 2.82e-10 | win |
| leaky FD-FxNLMS | ar1 | S2 src 30cm | -0.06 | 1 | -0.89 | 8.73e-11 | win |
| leaky FD-FxNLMS | harmonic | S2 src 30cm | -2.25 | 1.75e-10 | -3.61 | 1.46e-10 | win |
| convex FD-FxNLMS | ar1 | S2 src 30cm | +0.02 | 1 | -0.76 | 8.73e-11 | win |
| convex FD-FxNLMS | harmonic | S2 src 30cm | -1.85 | 1.62e-09 | -1.61 | 4.16e-09 | win |
| FDKF | ar1 | S2 src 30cm | +0.22 | 1 | -0.93 | 8.73e-11 | win |
| FDKF | harmonic | S2 src 30cm | -2.37 | 8.73e-11 | -6.57 | 8.73e-11 | win |
| RLS | ar1 | S2 src 30cm | +0.16 | 0.00813 | -0.05 | 1 | - |
| RLS | harmonic | S2 src 30cm | -0.03 | 1 | +2.42 | 2.82e-10 | loss |
| VFF-RLS | ar1 | S2 src 30cm | +0.18 | 0.0157 | -0.02 | 1 | - |
| VFF-RLS | harmonic | S2 src 30cm | -0.31 | 1 | +2.49 | 3.8e-07 | loss |
| FD-FxNLMS + det | ar1 | S2 src 30cm | -0.04 | 1 | -0.79 | 8.73e-11 | win |
| FD-FxNLMS + det | harmonic | S2 src 30cm | -1.91 | 3.57e-10 | -2.04 | 1.46e-10 | win |
| RLS + det | ar1 | S2 src 30cm | -0.03 | 1 | +0.12 | 0.000192 | - |
| RLS + det | harmonic | S2 src 30cm | -0.49 | 9.96e-05 | +1.64 | 1.46e-10 | loss |
| FD-FxNLMS + restart | ar1 | S2 src 30cm | -0.03 | 1 | -0.84 | 8.73e-11 | win |
| FD-FxNLMS + restart | harmonic | S2 src 30cm | -2.54 | 1.46e-10 | -2.56 | 2.82e-10 | win |
| SFTF + det | ar1 | S2 src 30cm | -0.02 | 1 | +0.12 | 0.000192 | - |
| SFTF + det | harmonic | S2 src 30cm | -1.28 | 6.74e-08 | +1.50 | 1.46e-10 | mixed |
| SFTF-H + det | ar1 | S2 src 30cm | -0.03 | 1 | +0.12 | 0.000208 | - |
| SFTF-H + det | harmonic | S2 src 30cm | -0.49 | 0.000113 | +1.51 | 1.46e-10 | loss |
| CFTF + det | ar1 | S2 src 30cm | -0.03 | 1 | +0.12 | 0.000192 | - |
| CFTF + det | harmonic | S2 src 30cm | -0.49 | 9.55e-05 | +1.62 | 1.46e-10 | loss |

Counts (E-PCG): win 12, loss 5, mixed 1, none 6 (of 24)

## E-PCG bank vs baselines (Wilcoxon pratt on seeds; Holm over 48)
| baseline | noise | cell | med dA1 | p_Holm A1 | med dA2 | p_Holm A2 | label |
|---|---|---|---|---|---|---|---|
| FD-FxNLMS | ar1 | S2 src 30cm | -0.09 | 1 | -0.77 | 8.73e-11 | win |
| FD-FxNLMS | harmonic | S2 src 30cm | -2.94 | 8.73e-11 | -2.53 | 1.53e-10 | win |
| leaky FD-FxNLMS | ar1 | S2 src 30cm | -0.14 | 1 | -0.84 | 8.73e-11 | win |
| leaky FD-FxNLMS | harmonic | S2 src 30cm | -2.96 | 8.73e-11 | -3.65 | 8.73e-11 | win |
| convex FD-FxNLMS | ar1 | S2 src 30cm | +0.01 | 1 | -0.65 | 8.73e-11 | win |
| convex FD-FxNLMS | harmonic | S2 src 30cm | -2.59 | 8.73e-11 | -1.66 | 2.2e-09 | win |
| FDKF | ar1 | S2 src 30cm | +0.06 | 1 | -0.87 | 8.73e-11 | win |
| FDKF | harmonic | S2 src 30cm | -3.23 | 8.73e-11 | -6.62 | 8.73e-11 | win |
| RLS | ar1 | S2 src 30cm | +0.07 | 1 | +0.02 | 0.463 | - |
| RLS | harmonic | S2 src 30cm | -0.66 | 1.74e-05 | +2.39 | 1.53e-10 | loss |
| VFF-RLS | ar1 | S2 src 30cm | +0.08 | 1 | +0.05 | 0.35 | - |
| VFF-RLS | harmonic | S2 src 30cm | -0.90 | 2.04e-07 | +2.46 | 2.9e-07 | loss |
| FD-FxNLMS + det | ar1 | S2 src 30cm | -0.09 | 1 | -0.67 | 8.73e-11 | win |
| FD-FxNLMS + det | harmonic | S2 src 30cm | -2.64 | 8.73e-11 | -2.10 | 1.06e-10 | win |
| RLS + det | ar1 | S2 src 30cm | -0.04 | 0.403 | +0.18 | 2.2e-09 | - |
| RLS + det | harmonic | S2 src 30cm | -1.32 | 3.18e-10 | +1.61 | 8.73e-11 | mixed |
| FD-FxNLMS + restart | ar1 | S2 src 30cm | -0.09 | 1 | -0.77 | 8.73e-11 | win |
| FD-FxNLMS + restart | harmonic | S2 src 30cm | -3.19 | 8.73e-11 | -2.56 | 2.36e-10 | win |
| SFTF + det | ar1 | S2 src 30cm | -0.04 | 0.436 | +0.18 | 2.2e-09 | - |
| SFTF + det | harmonic | S2 src 30cm | -1.90 | 8.73e-11 | +1.47 | 8.73e-11 | mixed |
| SFTF-H + det | ar1 | S2 src 30cm | -0.04 | 0.403 | +0.18 | 2.2e-09 | - |
| SFTF-H + det | harmonic | S2 src 30cm | -1.31 | 3.18e-10 | +1.49 | 8.73e-11 | mixed |
| CFTF + det | ar1 | S2 src 30cm | -0.04 | 0.403 | +0.18 | 2.2e-09 | - |
| CFTF + det | harmonic | S2 src 30cm | -1.32 | 3.18e-10 | +1.59 | 8.73e-11 | mixed |

Counts (E-PCG bank): win 12, loss 2, mixed 4, none 6 (of 24)

## E-PCG bank - E-PCG (main) (Holm over 4)
| noise | cell | key | median d | p_Holm |
|---|---|---|---|---|
| ar1 | S2 src 30cm | A1 | -0.01 | 0.0842 |
| ar1 | S2 src 30cm | A2 | +0.08 | 1.46e-11 |
| harmonic | S2 src 30cm | A1 | -0.65 | 3.49e-09 |
| harmonic | S2 src 30cm | A2 | -0.03 | 5.38e-08 |

## Reach fraction at level -9 dB (tau <= t; t in [0.3, 0.5, 1.0, 2.0, 3.0, 4.0] s)
| method | noise | cell | t=0.3 | t=0.5 | t=1.0 | t=2.0 | t=3.0 | t=4.0 |
|---|---|---|---|---|---|---|---|---|
| FD-FxNLMS | ar1 | S2 src 30cm | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| FD-FxNLMS | harmonic | S2 src 30cm | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| leaky FD-FxNLMS | ar1 | S2 src 30cm | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| leaky FD-FxNLMS | harmonic | S2 src 30cm | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| convex FD-FxNLMS | ar1 | S2 src 30cm | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| convex FD-FxNLMS | harmonic | S2 src 30cm | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.03 |
| FDKF | ar1 | S2 src 30cm | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| FDKF | harmonic | S2 src 30cm | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| RLS | ar1 | S2 src 30cm | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| RLS | harmonic | S2 src 30cm | 0.00 | 0.00 | 0.38 | 0.62 | 0.72 | 0.75 |
| VFF-RLS | ar1 | S2 src 30cm | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| VFF-RLS | harmonic | S2 src 30cm | 0.00 | 0.00 | 0.40 | 0.68 | 0.75 | 0.78 |
| FD-FxNLMS + det | ar1 | S2 src 30cm | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| FD-FxNLMS + det | harmonic | S2 src 30cm | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| RLS + det | ar1 | S2 src 30cm | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| RLS + det | harmonic | S2 src 30cm | 0.00 | 0.00 | 0.03 | 0.25 | 0.70 | 0.78 |
| FD-FxNLMS + restart | ar1 | S2 src 30cm | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| FD-FxNLMS + restart | harmonic | S2 src 30cm | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| SFTF + det | ar1 | S2 src 30cm | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| SFTF + det | harmonic | S2 src 30cm | 0.00 | 0.00 | 0.03 | 0.17 | 0.62 | 0.75 |
| SFTF-H + det | ar1 | S2 src 30cm | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| SFTF-H + det | harmonic | S2 src 30cm | 0.00 | 0.00 | 0.03 | 0.23 | 0.65 | 0.75 |
| CFTF + det | ar1 | S2 src 30cm | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| CFTF + det | harmonic | S2 src 30cm | 0.00 | 0.00 | 0.03 | 0.23 | 0.68 | 0.75 |
| E-PCG | ar1 | S2 src 30cm | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| E-PCG | harmonic | S2 src 30cm | 0.00 | 0.00 | 0.03 | 0.03 | 0.05 | 0.05 |
| E-PCG bank | ar1 | S2 src 30cm | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| E-PCG bank | harmonic | S2 src 30cm | 0.00 | 0.00 | 0.03 | 0.03 | 0.05 | 0.05 |

## Reach fraction at level -12 dB (tau <= t; t in [0.3, 0.5, 1.0, 2.0, 3.0, 4.0] s)
| method | noise | cell | t=0.3 | t=0.5 | t=1.0 | t=2.0 | t=3.0 | t=4.0 |
|---|---|---|---|---|---|---|---|---|
| FD-FxNLMS | ar1 | S2 src 30cm | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| FD-FxNLMS | harmonic | S2 src 30cm | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| leaky FD-FxNLMS | ar1 | S2 src 30cm | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| leaky FD-FxNLMS | harmonic | S2 src 30cm | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| convex FD-FxNLMS | ar1 | S2 src 30cm | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| convex FD-FxNLMS | harmonic | S2 src 30cm | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| FDKF | ar1 | S2 src 30cm | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| FDKF | harmonic | S2 src 30cm | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| RLS | ar1 | S2 src 30cm | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| RLS | harmonic | S2 src 30cm | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| VFF-RLS | ar1 | S2 src 30cm | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| VFF-RLS | harmonic | S2 src 30cm | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| FD-FxNLMS + det | ar1 | S2 src 30cm | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| FD-FxNLMS + det | harmonic | S2 src 30cm | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| RLS + det | ar1 | S2 src 30cm | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| RLS + det | harmonic | S2 src 30cm | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| FD-FxNLMS + restart | ar1 | S2 src 30cm | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| FD-FxNLMS + restart | harmonic | S2 src 30cm | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| SFTF + det | ar1 | S2 src 30cm | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| SFTF + det | harmonic | S2 src 30cm | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| SFTF-H + det | ar1 | S2 src 30cm | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| SFTF-H + det | harmonic | S2 src 30cm | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| CFTF + det | ar1 | S2 src 30cm | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| CFTF + det | harmonic | S2 src 30cm | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| E-PCG | ar1 | S2 src 30cm | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| E-PCG | harmonic | S2 src 30cm | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| E-PCG bank | ar1 | S2 src 30cm | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| E-PCG bank | harmonic | S2 src 30cm | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |

## Cost of the proposed methods (mean flop_hist / H = flops per sample; S8 / change cells)
| method | S8 | change cells |
|---|---|---|
| E-PCG | nan | 11258 |
| E-PCG bank | nan | 18670 |

## Diagnostics
- records 1120; unparsable 0; stale 0; duplicates 0 (differing 0)
- win / loss: each metric with its own Holm-adjusted p (A1 with p_A1, A2 with p_A2), thresholds 1 dB (A1) / 0.5 dB (A2)
- curves are ensemble means of the seed-summed powers: one failed run can dominate a curve (read with the failure table)
- cost of the baselines: analytic counts in the cost table (Step 6), not measured here
- runs stopped early (completed with no control): 0
