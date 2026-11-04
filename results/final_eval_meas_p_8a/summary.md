# MeshRIR measured-path evaluation (REVISION_RULE_8a)

Dataset: MeshRIR v1.1, S32-M441; DOI 10.5281/zenodo.5500451.
License: Creative Commons Attribution 4.0 International (CC BY 4.0) (https://creativecommons.org/licenses/by/4.0/).
Attribution: Shoichi Koyama, Tomoya Nishida, Keisuke Kimura, Takumi Abe, Natsuki Ueno, Jesper Brunnström. Archive MD5: 4fcd6137bcadb6914d4170ff366c86f9.
Preprocessing: 48 kHz -> 8 kHz resample_poly(1,6), Kaiser 5; P=1200, S=512 samples; common removal of 5434 samples at 48 kHz before resampling; initial P/S normalization reused. Full details: provenance.json.
Scenario labels S2/R2 denote M-P/M-PS here, not 30 cm ISM source/rig moves. Holm: 48 tests per proposed method per set; bank-minus-main: 4.
M-PS keeps the initial secondary-path model fixed.

Rule 8 results are retained but invalid as measured-path evidence due to missing direct sound. Rule 8a is a defect correction specified after inspecting those results; no retuning.

# Final evaluation (evaluation seeds 480-519, M = 512, T = 5 s; rule docs/current/FINAL_EVAL_RULE.md)
Values: median (Q1, Q3) over the 40 seeds; failed runs: A1 = A2 = 0 dB, tau = 4 s (censored).

## Failures (runs out of 40)
| method | ar1 S2 | harmonic S2 |
|---|---|---|
| FD-FxNLMS | 2 | 3 |
| leaky FD-FxNLMS | 2 | 7 |
| convex FD-FxNLMS | 2 | 0 |
| FDKF | 2 | 0 |
| RLS | 0 | 0 |
| VFF-RLS | 0 | 0 |
| FD-FxNLMS + det | 2 | 0 |
| RLS + det | 0 | 0 |
| FD-FxNLMS + restart | 2 | 3 |
| SFTF + det | 0 | 0 |
| SFTF-H + det | 0 | 0 |
| CFTF + det | 0 | 0 |
| E-PCG | 0 | 0 |
| E-PCG bank | 0 | 0 |

## A1, noise = ar1
| method | S2 src 30cm |
|---|---|
| FD-FxNLMS | -0.58 (-1.64, 0.00) |
| leaky FD-FxNLMS | -0.91 (-1.94, -0.18) |
| convex FD-FxNLMS | -0.91 (-2.15, 0.00) |
| FDKF | -0.09 (-0.88, 0.18) |
| RLS | -1.19 (-2.36, -0.41) |
| VFF-RLS | -1.12 (-2.23, -0.40) |
| FD-FxNLMS + det | -0.18 (-1.21, 0.32) |
| RLS + det | -0.87 (-2.78, 0.23) |
| FD-FxNLMS + restart | -0.73 (-1.79, 0.00) |
| SFTF + det | 0.48 (-0.14, 1.87) |
| SFTF-H + det | -0.87 (-2.79, 0.23) |
| CFTF + det | -0.87 (-2.80, 0.23) |
| E-PCG | -2.26 (-3.44, -0.00) |
| E-PCG bank | -1.69 (-2.75, -0.34) |

## A1, noise = harmonic
| method | S2 src 30cm |
|---|---|
| FD-FxNLMS | -1.76 (-2.93, 0.00) |
| leaky FD-FxNLMS | -1.43 (-3.17, 0.00) |
| convex FD-FxNLMS | -2.89 (-3.87, -0.67) |
| FDKF | -0.97 (-2.05, -0.09) |
| RLS | -3.03 (-3.53, -2.51) |
| VFF-RLS | -2.75 (-3.13, -2.18) |
| FD-FxNLMS + det | -1.33 (-2.33, 0.10) |
| RLS + det | -7.48 (-8.73, -5.44) |
| FD-FxNLMS + restart | -1.74 (-3.29, 0.00) |
| SFTF + det | -3.21 (-4.56, -1.50) |
| SFTF-H + det | -7.48 (-8.75, -5.43) |
| CFTF + det | -7.49 (-8.75, -5.44) |
| E-PCG | -6.80 (-8.54, -4.93) |
| E-PCG bank | -6.79 (-8.60, -4.72) |

## A2, noise = ar1
| method | S2 src 30cm |
|---|---|
| FD-FxNLMS | -4.20 (-5.47, -1.03) |
| leaky FD-FxNLMS | -4.19 (-5.41, -1.06) |
| convex FD-FxNLMS | -4.31 (-5.60, -1.13) |
| FDKF | -4.13 (-5.50, -0.92) |
| RLS | -5.04 (-6.39, -1.79) |
| VFF-RLS | -5.06 (-6.42, -1.82) |
| FD-FxNLMS + det | -4.21 (-5.64, -1.06) |
| RLS + det | -5.30 (-6.58, -2.03) |
| FD-FxNLMS + restart | -4.21 (-5.47, -1.03) |
| SFTF + det | -5.30 (-6.58, -2.03) |
| SFTF-H + det | -5.30 (-6.58, -2.03) |
| CFTF + det | -5.30 (-6.58, -2.03) |
| E-PCG | -5.18 (-6.64, -1.99) |
| E-PCG bank | -5.00 (-6.54, -1.99) |

## A2, noise = harmonic
| method | S2 src 30cm |
|---|---|
| FD-FxNLMS | -9.34 (-10.76, -5.23) |
| leaky FD-FxNLMS | -7.11 (-10.14, -4.39) |
| convex FD-FxNLMS | -10.20 (-12.00, -5.71) |
| FDKF | -9.76 (-11.70, -6.94) |
| RLS | -12.35 (-14.40, -9.77) |
| VFF-RLS | -12.41 (-14.41, -9.81) |
| FD-FxNLMS + det | -9.31 (-11.25, -5.01) |
| RLS + det | -13.00 (-14.97, -10.28) |
| FD-FxNLMS + restart | -9.07 (-10.80, -5.17) |
| SFTF + det | -12.99 (-14.90, -10.26) |
| SFTF-H + det | -13.00 (-14.96, -10.28) |
| CFTF + det | -13.00 (-14.97, -10.28) |
| E-PCG | -12.93 (-14.82, -10.17) |
| E-PCG bank | -12.96 (-14.90, -10.30) |

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
| FD-FxNLMS | 1.51 (0.95, 4.00) |
| leaky FD-FxNLMS | 1.66 (0.94, 4.00) |
| convex FD-FxNLMS | 1.20 (0.73, 4.00) |
| FDKF | 1.15 (0.88, 4.00) |
| RLS | 0.57 (0.53, 0.75) |
| VFF-RLS | 0.60 (0.57, 0.78) |
| FD-FxNLMS + det | 1.55 (1.11, 4.00) |
| RLS + det | 0.33 (0.30, 0.47) |
| FD-FxNLMS + restart | 1.53 (1.00, 4.00) |
| SFTF + det | 0.38 (0.36, 0.50) |
| SFTF-H + det | 0.33 (0.30, 0.47) |
| CFTF + det | 0.33 (0.30, 0.47) |
| E-PCG | 0.33 (0.30, 0.44) |
| E-PCG bank | 0.33 (0.30, 0.43) |

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
| FD-FxNLMS | 4.00 (2.10, 4.00) |
| leaky FD-FxNLMS | 4.00 (3.99, 4.00) |
| convex FD-FxNLMS | 4.00 (1.46, 4.00) |
| FDKF | 4.00 (1.64, 4.00) |
| RLS | 0.85 (0.68, 4.00) |
| VFF-RLS | 0.94 (0.73, 4.00) |
| FD-FxNLMS + det | 4.00 (2.14, 4.00) |
| RLS + det | 0.50 (0.34, 4.00) |
| FD-FxNLMS + restart | 4.00 (2.18, 4.00) |
| SFTF + det | 0.54 (0.41, 4.00) |
| SFTF-H + det | 0.50 (0.34, 4.00) |
| CFTF + det | 0.50 (0.34, 4.00) |
| E-PCG | 0.46 (0.34, 4.00) |
| E-PCG bank | 0.46 (0.34, 4.00) |

## E-PCG vs baselines (Wilcoxon pratt on seeds; Holm over 48)
| baseline | noise | cell | med dA1 | p_Holm A1 | med dA2 | p_Holm A2 | label |
|---|---|---|---|---|---|---|---|
| FD-FxNLMS | ar1 | S2 src 30cm | -0.87 | 5.4e-05 | -0.97 | 8.73e-11 | win |
| FD-FxNLMS | harmonic | S2 src 30cm | -5.13 | 8.73e-11 | -4.24 | 8.73e-11 | win |
| leaky FD-FxNLMS | ar1 | S2 src 30cm | -0.68 | 0.0015 | -1.02 | 8.73e-11 | win |
| leaky FD-FxNLMS | harmonic | S2 src 30cm | -4.81 | 8.73e-11 | -4.71 | 8.73e-11 | win |
| convex FD-FxNLMS | ar1 | S2 src 30cm | -0.74 | 5.4e-05 | -0.86 | 8.73e-11 | win |
| convex FD-FxNLMS | harmonic | S2 src 30cm | -4.31 | 8.73e-11 | -3.58 | 8.73e-11 | win |
| FDKF | ar1 | S2 src 30cm | -0.92 | 2.37e-05 | -1.06 | 8.73e-11 | win |
| FDKF | harmonic | S2 src 30cm | -5.19 | 8.73e-11 | -3.16 | 8.73e-11 | win |
| RLS | ar1 | S2 src 30cm | -0.42 | 0.081 | -0.25 | 8.73e-11 | - |
| RLS | harmonic | S2 src 30cm | -3.01 | 8.73e-11 | -0.43 | 8.73e-11 | win |
| VFF-RLS | ar1 | S2 src 30cm | -0.45 | 0.081 | -0.22 | 8.73e-11 | - |
| VFF-RLS | harmonic | S2 src 30cm | -3.19 | 8.73e-11 | -0.40 | 8.73e-11 | win |
| FD-FxNLMS + det | ar1 | S2 src 30cm | -1.21 | 1.23e-06 | -1.02 | 8.73e-11 | win |
| FD-FxNLMS + det | harmonic | S2 src 30cm | -5.36 | 8.73e-11 | -4.51 | 8.73e-11 | win |
| RLS + det | ar1 | S2 src 30cm | -0.75 | 5.51e-07 | +0.12 | 0.081 | - |
| RLS + det | harmonic | S2 src 30cm | +0.19 | 0.149 | +0.12 | 8.73e-11 | - |
| FD-FxNLMS + restart | ar1 | S2 src 30cm | -0.82 | 5.4e-05 | -0.97 | 8.73e-11 | win |
| FD-FxNLMS + restart | harmonic | S2 src 30cm | -5.34 | 8.73e-11 | -4.21 | 8.73e-11 | win |
| SFTF + det | ar1 | S2 src 30cm | -2.95 | 3.12e-08 | +0.11 | 0.081 | win |
| SFTF + det | harmonic | S2 src 30cm | -3.76 | 8.73e-11 | +0.08 | 1.82e-10 | win |
| SFTF-H + det | ar1 | S2 src 30cm | -0.75 | 5.51e-07 | +0.12 | 0.081 | - |
| SFTF-H + det | harmonic | S2 src 30cm | +0.18 | 0.149 | +0.12 | 8.73e-11 | - |
| CFTF + det | ar1 | S2 src 30cm | -0.73 | 5.51e-07 | +0.12 | 0.081 | - |
| CFTF + det | harmonic | S2 src 30cm | +0.20 | 0.149 | +0.12 | 8.73e-11 | - |

Counts (E-PCG): win 16, loss 0, mixed 0, none 8 (of 24)

## E-PCG bank vs baselines (Wilcoxon pratt on seeds; Holm over 48)
| baseline | noise | cell | med dA1 | p_Holm A1 | med dA2 | p_Holm A2 | label |
|---|---|---|---|---|---|---|---|
| FD-FxNLMS | ar1 | S2 src 30cm | -0.51 | 5.65e-06 | -0.91 | 8.73e-11 | win |
| FD-FxNLMS | harmonic | S2 src 30cm | -4.95 | 8.73e-11 | -4.36 | 8.73e-11 | win |
| leaky FD-FxNLMS | ar1 | S2 src 30cm | -0.29 | 0.00719 | -0.97 | 8.73e-11 | win |
| leaky FD-FxNLMS | harmonic | S2 src 30cm | -4.64 | 8.73e-11 | -4.82 | 8.73e-11 | win |
| convex FD-FxNLMS | ar1 | S2 src 30cm | -0.49 | 0.000419 | -0.89 | 8.73e-11 | win |
| convex FD-FxNLMS | harmonic | S2 src 30cm | -4.15 | 8.73e-11 | -3.72 | 8.73e-11 | win |
| FDKF | ar1 | S2 src 30cm | -0.68 | 1.29e-07 | -1.06 | 8.73e-11 | win |
| FDKF | harmonic | S2 src 30cm | -4.93 | 8.73e-11 | -3.29 | 8.73e-11 | win |
| RLS | ar1 | S2 src 30cm | +0.07 | 0.403 | -0.19 | 3.33e-08 | - |
| RLS | harmonic | S2 src 30cm | -2.81 | 9.82e-11 | -0.54 | 8.73e-11 | win |
| VFF-RLS | ar1 | S2 src 30cm | +0.04 | 0.403 | -0.16 | 8.29e-07 | - |
| VFF-RLS | harmonic | S2 src 30cm | -3.04 | 9.82e-11 | -0.51 | 8.73e-11 | win |
| FD-FxNLMS + det | ar1 | S2 src 30cm | -0.86 | 3.33e-08 | -0.99 | 8.73e-11 | win |
| FD-FxNLMS + det | harmonic | S2 src 30cm | -5.12 | 8.73e-11 | -4.60 | 8.73e-11 | win |
| RLS + det | ar1 | S2 src 30cm | -0.62 | 0.000195 | +0.09 | 0.000147 | - |
| RLS + det | harmonic | S2 src 30cm | +0.31 | 0.00719 | +0.03 | 0.221 | - |
| FD-FxNLMS + restart | ar1 | S2 src 30cm | -0.51 | 3.87e-05 | -0.92 | 8.73e-11 | win |
| FD-FxNLMS + restart | harmonic | S2 src 30cm | -5.20 | 8.73e-11 | -4.33 | 8.73e-11 | win |
| SFTF + det | ar1 | S2 src 30cm | -2.58 | 1.96e-09 | +0.09 | 0.000195 | win |
| SFTF + det | harmonic | S2 src 30cm | -3.65 | 8.73e-11 | -0.03 | 0.221 | win |
| SFTF-H + det | ar1 | S2 src 30cm | -0.62 | 0.000195 | +0.09 | 0.000195 | - |
| SFTF-H + det | harmonic | S2 src 30cm | +0.30 | 0.00719 | +0.02 | 0.268 | - |
| CFTF + det | ar1 | S2 src 30cm | -0.62 | 0.000195 | +0.09 | 0.000147 | - |
| CFTF + det | harmonic | S2 src 30cm | +0.32 | 0.00638 | +0.03 | 0.221 | - |

Counts (E-PCG bank): win 16, loss 0, mixed 0, none 8 (of 24)

## E-PCG bank - E-PCG (main) (Holm over 4)
| noise | cell | key | median d | p_Holm |
|---|---|---|---|---|
| ar1 | S2 src 30cm | A1 | +0.06 | 0.232 |
| ar1 | S2 src 30cm | A2 | +0.07 | 0.0902 |
| harmonic | S2 src 30cm | A1 | +0.13 | 0.00718 |
| harmonic | S2 src 30cm | A2 | -0.10 | 1.02e-10 |

## Reach fraction at level -9 dB (tau <= t; t in [0.3, 0.5, 1.0, 2.0, 3.0, 4.0] s)
| method | noise | cell | t=0.3 | t=0.5 | t=1.0 | t=2.0 | t=3.0 | t=4.0 |
|---|---|---|---|---|---|---|---|---|
| FD-FxNLMS | ar1 | S2 src 30cm | 0.00 | 0.00 | 0.03 | 0.07 | 0.07 | 0.10 |
| FD-FxNLMS | harmonic | S2 src 30cm | 0.00 | 0.00 | 0.28 | 0.57 | 0.57 | 0.60 |
| leaky FD-FxNLMS | ar1 | S2 src 30cm | 0.00 | 0.00 | 0.03 | 0.05 | 0.05 | 0.05 |
| leaky FD-FxNLMS | harmonic | S2 src 30cm | 0.00 | 0.00 | 0.30 | 0.53 | 0.53 | 0.53 |
| convex FD-FxNLMS | ar1 | S2 src 30cm | 0.00 | 0.00 | 0.03 | 0.05 | 0.05 | 0.10 |
| convex FD-FxNLMS | harmonic | S2 src 30cm | 0.00 | 0.00 | 0.47 | 0.57 | 0.57 | 0.60 |
| FDKF | ar1 | S2 src 30cm | 0.00 | 0.00 | 0.00 | 0.07 | 0.07 | 0.10 |
| FDKF | harmonic | S2 src 30cm | 0.00 | 0.00 | 0.40 | 0.57 | 0.62 | 0.62 |
| RLS | ar1 | S2 src 30cm | 0.00 | 0.00 | 0.07 | 0.10 | 0.15 | 0.15 |
| RLS | harmonic | S2 src 30cm | 0.00 | 0.10 | 0.88 | 0.97 | 0.97 | 1.00 |
| VFF-RLS | ar1 | S2 src 30cm | 0.00 | 0.00 | 0.07 | 0.10 | 0.15 | 0.15 |
| VFF-RLS | harmonic | S2 src 30cm | 0.00 | 0.05 | 0.88 | 1.00 | 1.00 | 1.00 |
| FD-FxNLMS + det | ar1 | S2 src 30cm | 0.00 | 0.00 | 0.00 | 0.05 | 0.07 | 0.07 |
| FD-FxNLMS + det | harmonic | S2 src 30cm | 0.00 | 0.00 | 0.10 | 0.57 | 0.57 | 0.57 |
| RLS + det | ar1 | S2 src 30cm | 0.00 | 0.03 | 0.10 | 0.12 | 0.20 | 0.23 |
| RLS + det | harmonic | S2 src 30cm | 0.35 | 0.75 | 0.95 | 1.00 | 1.00 | 1.00 |
| FD-FxNLMS + restart | ar1 | S2 src 30cm | 0.00 | 0.00 | 0.03 | 0.07 | 0.07 | 0.10 |
| FD-FxNLMS + restart | harmonic | S2 src 30cm | 0.00 | 0.00 | 0.25 | 0.53 | 0.57 | 0.60 |
| SFTF + det | ar1 | S2 src 30cm | 0.00 | 0.00 | 0.10 | 0.12 | 0.20 | 0.23 |
| SFTF + det | harmonic | S2 src 30cm | 0.00 | 0.70 | 0.95 | 1.00 | 1.00 | 1.00 |
| SFTF-H + det | ar1 | S2 src 30cm | 0.00 | 0.03 | 0.10 | 0.12 | 0.20 | 0.23 |
| SFTF-H + det | harmonic | S2 src 30cm | 0.35 | 0.75 | 0.95 | 1.00 | 1.00 | 1.00 |
| CFTF + det | ar1 | S2 src 30cm | 0.00 | 0.03 | 0.10 | 0.12 | 0.20 | 0.23 |
| CFTF + det | harmonic | S2 src 30cm | 0.38 | 0.75 | 0.95 | 1.00 | 1.00 | 1.00 |
| E-PCG | ar1 | S2 src 30cm | 0.00 | 0.03 | 0.10 | 0.12 | 0.17 | 0.17 |
| E-PCG | harmonic | S2 src 30cm | 0.30 | 0.78 | 0.97 | 1.00 | 1.00 | 1.00 |
| E-PCG bank | ar1 | S2 src 30cm | 0.00 | 0.03 | 0.10 | 0.15 | 0.23 | 0.23 |
| E-PCG bank | harmonic | S2 src 30cm | 0.28 | 0.78 | 0.95 | 1.00 | 1.00 | 1.00 |

## Reach fraction at level -12 dB (tau <= t; t in [0.3, 0.5, 1.0, 2.0, 3.0, 4.0] s)
| method | noise | cell | t=0.3 | t=0.5 | t=1.0 | t=2.0 | t=3.0 | t=4.0 |
|---|---|---|---|---|---|---|---|---|
| FD-FxNLMS | ar1 | S2 src 30cm | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| FD-FxNLMS | harmonic | S2 src 30cm | 0.00 | 0.00 | 0.07 | 0.25 | 0.35 | 0.38 |
| leaky FD-FxNLMS | ar1 | S2 src 30cm | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| leaky FD-FxNLMS | harmonic | S2 src 30cm | 0.00 | 0.00 | 0.07 | 0.20 | 0.23 | 0.25 |
| convex FD-FxNLMS | ar1 | S2 src 30cm | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| convex FD-FxNLMS | harmonic | S2 src 30cm | 0.00 | 0.00 | 0.07 | 0.30 | 0.42 | 0.45 |
| FDKF | ar1 | S2 src 30cm | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| FDKF | harmonic | S2 src 30cm | 0.00 | 0.00 | 0.03 | 0.30 | 0.40 | 0.42 |
| RLS | ar1 | S2 src 30cm | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| RLS | harmonic | S2 src 30cm | 0.00 | 0.00 | 0.55 | 0.57 | 0.57 | 0.57 |
| VFF-RLS | ar1 | S2 src 30cm | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| VFF-RLS | harmonic | S2 src 30cm | 0.00 | 0.00 | 0.55 | 0.57 | 0.57 | 0.57 |
| FD-FxNLMS + det | ar1 | S2 src 30cm | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| FD-FxNLMS + det | harmonic | S2 src 30cm | 0.00 | 0.00 | 0.00 | 0.23 | 0.40 | 0.45 |
| RLS + det | ar1 | S2 src 30cm | 0.00 | 0.00 | 0.00 | 0.03 | 0.03 | 0.03 |
| RLS + det | harmonic | S2 src 30cm | 0.07 | 0.50 | 0.57 | 0.57 | 0.60 | 0.62 |
| FD-FxNLMS + restart | ar1 | S2 src 30cm | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| FD-FxNLMS + restart | harmonic | S2 src 30cm | 0.00 | 0.00 | 0.07 | 0.23 | 0.35 | 0.38 |
| SFTF + det | ar1 | S2 src 30cm | 0.00 | 0.00 | 0.00 | 0.00 | 0.03 | 0.03 |
| SFTF + det | harmonic | S2 src 30cm | 0.00 | 0.47 | 0.55 | 0.57 | 0.60 | 0.62 |
| SFTF-H + det | ar1 | S2 src 30cm | 0.00 | 0.00 | 0.00 | 0.03 | 0.03 | 0.03 |
| SFTF-H + det | harmonic | S2 src 30cm | 0.07 | 0.50 | 0.55 | 0.57 | 0.60 | 0.62 |
| CFTF + det | ar1 | S2 src 30cm | 0.00 | 0.00 | 0.00 | 0.03 | 0.03 | 0.03 |
| CFTF + det | harmonic | S2 src 30cm | 0.07 | 0.50 | 0.57 | 0.57 | 0.60 | 0.62 |
| E-PCG | ar1 | S2 src 30cm | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| E-PCG | harmonic | S2 src 30cm | 0.10 | 0.50 | 0.57 | 0.57 | 0.60 | 0.60 |
| E-PCG bank | ar1 | S2 src 30cm | 0.00 | 0.00 | 0.00 | 0.00 | 0.03 | 0.03 |
| E-PCG bank | harmonic | S2 src 30cm | 0.07 | 0.50 | 0.57 | 0.60 | 0.62 | 0.62 |

## Cost of the proposed methods (mean flop_hist / H = flops per sample; S8 / change cells)
| method | S8 | change cells |
|---|---|---|
| E-PCG | nan | 10837 |
| E-PCG bank | nan | 16834 |

## Diagnostics
- records 1120; unparsable 0; stale 0; duplicates 0 (differing 0)
- win / loss: each metric with its own Holm-adjusted p (A1 with p_A1, A2 with p_A2), thresholds 1 dB (A1) / 0.5 dB (A2)
- curves are ensemble means of the seed-summed powers: one failed run can dominate a curve (read with the failure table)
- cost of the baselines: analytic counts in the cost table (Step 6), not measured here
- runs stopped early (completed with no control): 0
