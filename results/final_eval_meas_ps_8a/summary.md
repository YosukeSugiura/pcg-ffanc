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
| method | ar1 R2 | harmonic R2 |
|---|---|---|
| FD-FxNLMS | 39 | 39 |
| leaky FD-FxNLMS | 39 | 39 |
| convex FD-FxNLMS | 39 | 39 |
| FDKF | 40 | 39 |
| RLS | 39 | 39 |
| VFF-RLS | 39 | 39 |
| FD-FxNLMS + det | 39 | 39 |
| RLS + det | 39 | 39 |
| FD-FxNLMS + restart | 39 | 39 |
| SFTF + det | 39 | 39 |
| SFTF-H + det | 39 | 39 |
| CFTF + det | 39 | 39 |
| E-PCG | 39 | 39 |
| E-PCG bank | 39 | 39 |

## A1, noise = ar1
| method | R2 rig 30cm |
|---|---|
| FD-FxNLMS | 0.00 (0.00, 0.00) |
| leaky FD-FxNLMS | 0.00 (0.00, 0.00) |
| convex FD-FxNLMS | 0.00 (0.00, 0.00) |
| FDKF | 0.00 (0.00, 0.00) |
| RLS | 0.00 (0.00, 0.00) |
| VFF-RLS | 0.00 (0.00, 0.00) |
| FD-FxNLMS + det | 0.00 (0.00, 0.00) |
| RLS + det | 0.00 (0.00, 0.00) |
| FD-FxNLMS + restart | 0.00 (0.00, 0.00) |
| SFTF + det | 0.00 (0.00, 0.00) |
| SFTF-H + det | 0.00 (0.00, 0.00) |
| CFTF + det | 0.00 (0.00, 0.00) |
| E-PCG | 0.00 (0.00, 0.00) |
| E-PCG bank | 0.00 (0.00, 0.00) |

## A1, noise = harmonic
| method | R2 rig 30cm |
|---|---|
| FD-FxNLMS | 0.00 (0.00, 0.00) |
| leaky FD-FxNLMS | 0.00 (0.00, 0.00) |
| convex FD-FxNLMS | 0.00 (0.00, 0.00) |
| FDKF | 0.00 (0.00, 0.00) |
| RLS | 0.00 (0.00, 0.00) |
| VFF-RLS | 0.00 (0.00, 0.00) |
| FD-FxNLMS + det | 0.00 (0.00, 0.00) |
| RLS + det | 0.00 (0.00, 0.00) |
| FD-FxNLMS + restart | 0.00 (0.00, 0.00) |
| SFTF + det | 0.00 (0.00, 0.00) |
| SFTF-H + det | 0.00 (0.00, 0.00) |
| CFTF + det | 0.00 (0.00, 0.00) |
| E-PCG | 0.00 (0.00, 0.00) |
| E-PCG bank | 0.00 (0.00, 0.00) |

## A2, noise = ar1
| method | R2 rig 30cm |
|---|---|
| FD-FxNLMS | 0.00 (0.00, 0.00) |
| leaky FD-FxNLMS | 0.00 (0.00, 0.00) |
| convex FD-FxNLMS | 0.00 (0.00, 0.00) |
| FDKF | 0.00 (0.00, 0.00) |
| RLS | 0.00 (0.00, 0.00) |
| VFF-RLS | 0.00 (0.00, 0.00) |
| FD-FxNLMS + det | 0.00 (0.00, 0.00) |
| RLS + det | 0.00 (0.00, 0.00) |
| FD-FxNLMS + restart | 0.00 (0.00, 0.00) |
| SFTF + det | 0.00 (0.00, 0.00) |
| SFTF-H + det | 0.00 (0.00, 0.00) |
| CFTF + det | 0.00 (0.00, 0.00) |
| E-PCG | 0.00 (0.00, 0.00) |
| E-PCG bank | 0.00 (0.00, 0.00) |

## A2, noise = harmonic
| method | R2 rig 30cm |
|---|---|
| FD-FxNLMS | 0.00 (0.00, 0.00) |
| leaky FD-FxNLMS | 0.00 (0.00, 0.00) |
| convex FD-FxNLMS | 0.00 (0.00, 0.00) |
| FDKF | 0.00 (0.00, 0.00) |
| RLS | 0.00 (0.00, 0.00) |
| VFF-RLS | 0.00 (0.00, 0.00) |
| FD-FxNLMS + det | 0.00 (0.00, 0.00) |
| RLS + det | 0.00 (0.00, 0.00) |
| FD-FxNLMS + restart | 0.00 (0.00, 0.00) |
| SFTF + det | 0.00 (0.00, 0.00) |
| SFTF-H + det | 0.00 (0.00, 0.00) |
| CFTF + det | 0.00 (0.00, 0.00) |
| E-PCG | 0.00 (0.00, 0.00) |
| E-PCG bank | 0.00 (0.00, 0.00) |

## tau9, noise = ar1
| method | R2 rig 30cm |
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
| method | R2 rig 30cm |
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

## tau12, noise = ar1
| method | R2 rig 30cm |
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
| method | R2 rig 30cm |
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
| FD-FxNLMS | ar1 | R2 rig 30cm | +0.00 | 1 | +0.00 | 1 | - |
| FD-FxNLMS | harmonic | R2 rig 30cm | +0.00 | 1 | +0.00 | 1 | - |
| leaky FD-FxNLMS | ar1 | R2 rig 30cm | +0.00 | 1 | +0.00 | 1 | - |
| leaky FD-FxNLMS | harmonic | R2 rig 30cm | +0.00 | 1 | +0.00 | 1 | - |
| convex FD-FxNLMS | ar1 | R2 rig 30cm | +0.00 | 1 | +0.00 | 1 | - |
| convex FD-FxNLMS | harmonic | R2 rig 30cm | +0.00 | 1 | +0.00 | 1 | - |
| FDKF | ar1 | R2 rig 30cm | +0.00 | 1 | +0.00 | 1 | - |
| FDKF | harmonic | R2 rig 30cm | +0.00 | 1 | +0.00 | 1 | - |
| RLS | ar1 | R2 rig 30cm | +0.00 | 1 | +0.00 | 1 | - |
| RLS | harmonic | R2 rig 30cm | +0.00 | 1 | +0.00 | 1 | - |
| VFF-RLS | ar1 | R2 rig 30cm | +0.00 | 1 | +0.00 | 1 | - |
| VFF-RLS | harmonic | R2 rig 30cm | +0.00 | 1 | +0.00 | 1 | - |
| FD-FxNLMS + det | ar1 | R2 rig 30cm | +0.00 | 1 | +0.00 | 1 | - |
| FD-FxNLMS + det | harmonic | R2 rig 30cm | +0.00 | 1 | +0.00 | 1 | - |
| RLS + det | ar1 | R2 rig 30cm | +0.00 | 1 | +0.00 | 1 | - |
| RLS + det | harmonic | R2 rig 30cm | +0.00 | 1 | +0.00 | 1 | - |
| FD-FxNLMS + restart | ar1 | R2 rig 30cm | +0.00 | 1 | +0.00 | 1 | - |
| FD-FxNLMS + restart | harmonic | R2 rig 30cm | +0.00 | 1 | +0.00 | 1 | - |
| SFTF + det | ar1 | R2 rig 30cm | +0.00 | 1 | +0.00 | 1 | - |
| SFTF + det | harmonic | R2 rig 30cm | +0.00 | 1 | +0.00 | 1 | - |
| SFTF-H + det | ar1 | R2 rig 30cm | +0.00 | 1 | +0.00 | 1 | - |
| SFTF-H + det | harmonic | R2 rig 30cm | +0.00 | 1 | +0.00 | 1 | - |
| CFTF + det | ar1 | R2 rig 30cm | +0.00 | 1 | +0.00 | 1 | - |
| CFTF + det | harmonic | R2 rig 30cm | +0.00 | 1 | +0.00 | 1 | - |

Counts (E-PCG): win 0, loss 0, mixed 0, none 24 (of 24)

## E-PCG bank vs baselines (Wilcoxon pratt on seeds; Holm over 48)
| baseline | noise | cell | med dA1 | p_Holm A1 | med dA2 | p_Holm A2 | label |
|---|---|---|---|---|---|---|---|
| FD-FxNLMS | ar1 | R2 rig 30cm | +0.00 | 1 | +0.00 | 1 | - |
| FD-FxNLMS | harmonic | R2 rig 30cm | +0.00 | 1 | +0.00 | 1 | - |
| leaky FD-FxNLMS | ar1 | R2 rig 30cm | +0.00 | 1 | +0.00 | 1 | - |
| leaky FD-FxNLMS | harmonic | R2 rig 30cm | +0.00 | 1 | +0.00 | 1 | - |
| convex FD-FxNLMS | ar1 | R2 rig 30cm | +0.00 | 1 | +0.00 | 1 | - |
| convex FD-FxNLMS | harmonic | R2 rig 30cm | +0.00 | 1 | +0.00 | 1 | - |
| FDKF | ar1 | R2 rig 30cm | +0.00 | 1 | +0.00 | 1 | - |
| FDKF | harmonic | R2 rig 30cm | +0.00 | 1 | +0.00 | 1 | - |
| RLS | ar1 | R2 rig 30cm | +0.00 | 1 | +0.00 | 1 | - |
| RLS | harmonic | R2 rig 30cm | +0.00 | 1 | +0.00 | 1 | - |
| VFF-RLS | ar1 | R2 rig 30cm | +0.00 | 1 | +0.00 | 1 | - |
| VFF-RLS | harmonic | R2 rig 30cm | +0.00 | 1 | +0.00 | 1 | - |
| FD-FxNLMS + det | ar1 | R2 rig 30cm | +0.00 | 1 | +0.00 | 1 | - |
| FD-FxNLMS + det | harmonic | R2 rig 30cm | +0.00 | 1 | +0.00 | 1 | - |
| RLS + det | ar1 | R2 rig 30cm | +0.00 | 1 | +0.00 | 1 | - |
| RLS + det | harmonic | R2 rig 30cm | +0.00 | 1 | +0.00 | 1 | - |
| FD-FxNLMS + restart | ar1 | R2 rig 30cm | +0.00 | 1 | +0.00 | 1 | - |
| FD-FxNLMS + restart | harmonic | R2 rig 30cm | +0.00 | 1 | +0.00 | 1 | - |
| SFTF + det | ar1 | R2 rig 30cm | +0.00 | 1 | +0.00 | 1 | - |
| SFTF + det | harmonic | R2 rig 30cm | +0.00 | 1 | +0.00 | 1 | - |
| SFTF-H + det | ar1 | R2 rig 30cm | +0.00 | 1 | +0.00 | 1 | - |
| SFTF-H + det | harmonic | R2 rig 30cm | +0.00 | 1 | +0.00 | 1 | - |
| CFTF + det | ar1 | R2 rig 30cm | +0.00 | 1 | +0.00 | 1 | - |
| CFTF + det | harmonic | R2 rig 30cm | +0.00 | 1 | +0.00 | 1 | - |

Counts (E-PCG bank): win 0, loss 0, mixed 0, none 24 (of 24)

## E-PCG bank - E-PCG (main) (Holm over 4)
| noise | cell | key | median d | p_Holm |
|---|---|---|---|---|
| ar1 | R2 rig 30cm | A1 | +0.00 | 1 |
| ar1 | R2 rig 30cm | A2 | +0.00 | 1 |
| harmonic | R2 rig 30cm | A1 | +0.00 | 1 |
| harmonic | R2 rig 30cm | A2 | +0.00 | 1 |

## Reach fraction at level -9 dB (tau <= t; t in [0.3, 0.5, 1.0, 2.0, 3.0, 4.0] s)
| method | noise | cell | t=0.3 | t=0.5 | t=1.0 | t=2.0 | t=3.0 | t=4.0 |
|---|---|---|---|---|---|---|---|---|
| FD-FxNLMS | ar1 | R2 rig 30cm | 0.00 | 0.00 | 0.00 | 0.03 | 0.03 | 0.03 |
| FD-FxNLMS | harmonic | R2 rig 30cm | 0.03 | 0.03 | 0.03 | 0.03 | 0.03 | 0.03 |
| leaky FD-FxNLMS | ar1 | R2 rig 30cm | 0.00 | 0.00 | 0.00 | 0.00 | 0.03 | 0.03 |
| leaky FD-FxNLMS | harmonic | R2 rig 30cm | 0.03 | 0.03 | 0.03 | 0.03 | 0.03 | 0.03 |
| convex FD-FxNLMS | ar1 | R2 rig 30cm | 0.00 | 0.00 | 0.00 | 0.03 | 0.03 | 0.03 |
| convex FD-FxNLMS | harmonic | R2 rig 30cm | 0.00 | 0.03 | 0.03 | 0.03 | 0.03 | 0.03 |
| FDKF | ar1 | R2 rig 30cm | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| FDKF | harmonic | R2 rig 30cm | 0.00 | 0.03 | 0.03 | 0.03 | 0.03 | 0.03 |
| RLS | ar1 | R2 rig 30cm | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| RLS | harmonic | R2 rig 30cm | 0.03 | 0.03 | 0.03 | 0.03 | 0.03 | 0.03 |
| VFF-RLS | ar1 | R2 rig 30cm | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| VFF-RLS | harmonic | R2 rig 30cm | 0.03 | 0.03 | 0.03 | 0.03 | 0.03 | 0.03 |
| FD-FxNLMS + det | ar1 | R2 rig 30cm | 0.00 | 0.00 | 0.00 | 0.03 | 0.03 | 0.03 |
| FD-FxNLMS + det | harmonic | R2 rig 30cm | 0.00 | 0.03 | 0.03 | 0.03 | 0.03 | 0.03 |
| RLS + det | ar1 | R2 rig 30cm | 0.00 | 0.00 | 0.00 | 0.00 | 0.03 | 0.03 |
| RLS + det | harmonic | R2 rig 30cm | 0.00 | 0.00 | 0.03 | 0.03 | 0.03 | 0.03 |
| FD-FxNLMS + restart | ar1 | R2 rig 30cm | 0.00 | 0.00 | 0.00 | 0.03 | 0.03 | 0.03 |
| FD-FxNLMS + restart | harmonic | R2 rig 30cm | 0.00 | 0.03 | 0.03 | 0.03 | 0.03 | 0.03 |
| SFTF + det | ar1 | R2 rig 30cm | 0.00 | 0.00 | 0.00 | 0.00 | 0.03 | 0.03 |
| SFTF + det | harmonic | R2 rig 30cm | 0.00 | 0.00 | 0.03 | 0.03 | 0.03 | 0.03 |
| SFTF-H + det | ar1 | R2 rig 30cm | 0.00 | 0.00 | 0.00 | 0.00 | 0.03 | 0.03 |
| SFTF-H + det | harmonic | R2 rig 30cm | 0.00 | 0.00 | 0.03 | 0.03 | 0.03 | 0.03 |
| CFTF + det | ar1 | R2 rig 30cm | 0.00 | 0.00 | 0.00 | 0.00 | 0.03 | 0.03 |
| CFTF + det | harmonic | R2 rig 30cm | 0.00 | 0.00 | 0.03 | 0.03 | 0.03 | 0.03 |
| E-PCG | ar1 | R2 rig 30cm | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| E-PCG | harmonic | R2 rig 30cm | 0.00 | 0.03 | 0.03 | 0.03 | 0.03 | 0.03 |
| E-PCG bank | ar1 | R2 rig 30cm | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| E-PCG bank | harmonic | R2 rig 30cm | 0.00 | 0.03 | 0.03 | 0.03 | 0.03 | 0.03 |

## Reach fraction at level -12 dB (tau <= t; t in [0.3, 0.5, 1.0, 2.0, 3.0, 4.0] s)
| method | noise | cell | t=0.3 | t=0.5 | t=1.0 | t=2.0 | t=3.0 | t=4.0 |
|---|---|---|---|---|---|---|---|---|
| FD-FxNLMS | ar1 | R2 rig 30cm | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| FD-FxNLMS | harmonic | R2 rig 30cm | 0.00 | 0.00 | 0.03 | 0.03 | 0.03 | 0.03 |
| leaky FD-FxNLMS | ar1 | R2 rig 30cm | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| leaky FD-FxNLMS | harmonic | R2 rig 30cm | 0.00 | 0.00 | 0.03 | 0.03 | 0.03 | 0.03 |
| convex FD-FxNLMS | ar1 | R2 rig 30cm | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| convex FD-FxNLMS | harmonic | R2 rig 30cm | 0.00 | 0.00 | 0.03 | 0.03 | 0.03 | 0.03 |
| FDKF | ar1 | R2 rig 30cm | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| FDKF | harmonic | R2 rig 30cm | 0.00 | 0.00 | 0.00 | 0.03 | 0.03 | 0.03 |
| RLS | ar1 | R2 rig 30cm | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| RLS | harmonic | R2 rig 30cm | 0.00 | 0.03 | 0.03 | 0.03 | 0.03 | 0.03 |
| VFF-RLS | ar1 | R2 rig 30cm | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| VFF-RLS | harmonic | R2 rig 30cm | 0.00 | 0.03 | 0.03 | 0.03 | 0.03 | 0.03 |
| FD-FxNLMS + det | ar1 | R2 rig 30cm | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| FD-FxNLMS + det | harmonic | R2 rig 30cm | 0.00 | 0.00 | 0.00 | 0.03 | 0.03 | 0.03 |
| RLS + det | ar1 | R2 rig 30cm | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| RLS + det | harmonic | R2 rig 30cm | 0.00 | 0.00 | 0.03 | 0.03 | 0.03 | 0.03 |
| FD-FxNLMS + restart | ar1 | R2 rig 30cm | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| FD-FxNLMS + restart | harmonic | R2 rig 30cm | 0.00 | 0.00 | 0.03 | 0.03 | 0.03 | 0.03 |
| SFTF + det | ar1 | R2 rig 30cm | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| SFTF + det | harmonic | R2 rig 30cm | 0.00 | 0.00 | 0.03 | 0.03 | 0.03 | 0.03 |
| SFTF-H + det | ar1 | R2 rig 30cm | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| SFTF-H + det | harmonic | R2 rig 30cm | 0.00 | 0.00 | 0.03 | 0.03 | 0.03 | 0.03 |
| CFTF + det | ar1 | R2 rig 30cm | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| CFTF + det | harmonic | R2 rig 30cm | 0.00 | 0.00 | 0.03 | 0.03 | 0.03 | 0.03 |
| E-PCG | ar1 | R2 rig 30cm | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| E-PCG | harmonic | R2 rig 30cm | 0.00 | 0.03 | 0.03 | 0.03 | 0.03 | 0.03 |
| E-PCG bank | ar1 | R2 rig 30cm | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| E-PCG bank | harmonic | R2 rig 30cm | 0.00 | 0.00 | 0.03 | 0.03 | 0.03 | 0.03 |

## Cost of the proposed methods (mean flop_hist / H = flops per sample; S8 / change cells)
| method | S8 | change cells |
|---|---|---|
| E-PCG | nan | 40475 |
| E-PCG bank | nan | 46082 |

## Diagnostics
- records 1120; unparsable 0; stale 0; duplicates 0 (differing 0)
- win / loss: each metric with its own Holm-adjusted p (A1 with p_A1, A2 with p_A2), thresholds 1 dB (A1) / 0.5 dB (A2)
- curves are ensemble means of the seed-summed powers: one failed run can dominate a curve (read with the failure table)
- cost of the baselines: analytic counts in the cost table (Step 6), not measured here
- runs stopped early (completed with no control): 879
