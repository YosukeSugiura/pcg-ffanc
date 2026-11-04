# Ablation v6.5 -> core, set b (tuning seeds 300-309, 600-619; M = 512; T = 5 s)
Rules and metrics: experiments/ablation_core.py docstring (fixed before the runs). d = variant - reference, median over the 30 paired seeds; positive dA / dtau = the variant is worse. fail = failed runs (variant / reference).

## W2 C1 = core + fixes vs V0 v6.5
| noise | cell | median A ref (dB) | median dA (dB) | median dA1 (dB) | median dtau (s) | fail |
|---|---|---|---|---|---|---|
| ar1 | S8 stationary | -16.01 | -0.00 | - | +0.000 | 0 / 0 |
| ar1 | S1 src 10cm | -15.41 | -0.06 | -0.28 | +0.000 | 0 / 0 |
| ar1 | S2 src 30cm | -15.05 | -0.12 | -0.58 | -0.008 | 0 / 0 |
| ar1 | S5 src 30cm cont | -14.58 | -0.22 | +0.00 | +0.000 | 0 / 0 |
| ar1 | S7 rd abrupt | -13.42 | -1.92 | -2.64 | -0.072 | 0 / 0 |
| ar1 | R1 rig 10cm | -15.47 | -0.06 | -0.31 | +0.000 | 0 / 0 |
| ar1 | R2 rig 30cm | -15.24 | -0.10 | -0.59 | -0.016 | 0 / 0 |
| ar1 | R3 rig 30cm cont | -14.68 | -0.31 | +0.08 | +0.000 | 0 / 0 |
| harmonic | S8 stationary | -19.37 | +0.00 | - | +0.000 | 0 / 0 |
| harmonic | S1 src 10cm | -18.21 | -0.37 | -1.16 | +0.000 | 0 / 0 |
| harmonic | S2 src 30cm | -17.43 | -0.31 | -0.98 | -0.008 | 0 / 0 |
| harmonic | S5 src 30cm cont | -15.78 | -0.85 | -0.74 | +0.000 | 0 / 0 |
| harmonic | R1 rig 10cm | -18.14 | -0.41 | -1.36 | +0.000 | 0 / 0 |
| harmonic | R2 rig 30cm | -16.75 | -0.52 | -1.09 | -0.016 | 0 / 0 |
| harmonic | R3 rig 30cm cont | -15.61 | -1.12 | -0.96 | +0.000 | 0 / 0 |

Decision: adopted as core (more failures: False; max median dA +0.00 dB)

## W3 C1 -bank vs W2 C1 = core + fixes
| noise | cell | median A ref (dB) | median dA (dB) | median dA1 (dB) | median dtau (s) | fail |
|---|---|---|---|---|---|---|
| ar1 | S8 stationary | -16.02 | +0.18 | - | +0.000 | 0 / 0 |
| ar1 | S1 src 10cm | -15.52 | +0.06 | -0.04 | +0.000 | 0 / 0 |
| ar1 | S2 src 30cm | -15.16 | +0.08 | -0.01 | +0.000 | 0 / 0 |
| ar1 | S5 src 30cm cont | -14.82 | +0.08 | +0.06 | +0.000 | 0 / 0 |
| ar1 | S7 rd abrupt | -15.46 | +0.02 | -0.08 | +0.000 | 0 / 0 |
| ar1 | R1 rig 10cm | -15.55 | +0.08 | -0.07 | +0.000 | 0 / 0 |
| ar1 | R2 rig 30cm | -15.35 | +0.08 | -0.06 | +0.000 | 0 / 0 |
| ar1 | R3 rig 30cm cont | -15.11 | +0.16 | +0.22 | +0.000 | 0 / 0 |
| harmonic | S8 stationary | -19.36 | +0.24 | - | +0.000 | 0 / 0 |
| harmonic | S1 src 10cm | -18.52 | +0.14 | +0.20 | +0.000 | 0 / 0 |
| harmonic | S2 src 30cm | -17.89 | +0.13 | +0.13 | +0.000 | 0 / 0 |
| harmonic | S5 src 30cm cont | -17.65 | +1.76 | +1.68 | +0.112 | 0 / 0 ** |
| harmonic | R1 rig 10cm | -18.52 | +0.14 | +0.20 | +0.000 | 0 / 0 |
| harmonic | R2 rig 30cm | -17.50 | +0.02 | -0.17 | +0.000 | 0 / 0 |
| harmonic | R3 rig 30cm cont | -17.12 | +2.13 | +1.79 | +0.240 | 0 / 0 ** |

Decision: component KEPT (more failures: False; dA >= 0.3: True; dA1 >= 0.5: True; dtau >= 0.05: True)

## W4 C1 restart (no Prop. 9) vs W2 C1 = core + fixes
| noise | cell | median A ref (dB) | median dA (dB) | median dA1 (dB) | median dtau (s) | fail |
|---|---|---|---|---|---|---|
| ar1 | S8 stationary | -16.02 | +0.00 | - | +0.000 | 0 / 0 |
| ar1 | S1 src 10cm | -15.52 | +0.02 | +0.11 | +0.000 | 0 / 0 |
| ar1 | S2 src 30cm | -15.16 | +0.02 | +0.09 | +0.000 | 0 / 0 |
| ar1 | S5 src 30cm cont | -14.82 | +0.01 | +0.00 | +0.000 | 0 / 0 |
| ar1 | S7 rd abrupt | -15.46 | +0.00 | -0.00 | +0.000 | 0 / 0 |
| ar1 | R1 rig 10cm | -15.55 | +0.05 | +0.25 | +0.000 | 0 / 0 |
| ar1 | R2 rig 30cm | -15.35 | +0.04 | +0.19 | +0.000 | 0 / 0 |
| ar1 | R3 rig 30cm cont | -15.11 | +0.05 | +0.01 | +0.000 | 0 / 0 |
| harmonic | S8 stationary | -19.36 | +0.00 | - | +0.000 | 0 / 0 |
| harmonic | S1 src 10cm | -18.52 | +0.00 | +0.00 | +0.000 | 0 / 0 |
| harmonic | S2 src 30cm | -17.89 | +0.00 | -0.00 | +0.000 | 0 / 0 |
| harmonic | S5 src 30cm cont | -17.65 | +0.01 | +0.02 | +0.000 | 0 / 0 |
| harmonic | R1 rig 10cm | -18.52 | +0.00 | -0.00 | +0.000 | 0 / 0 |
| harmonic | R2 rig 30cm | -17.50 | -0.00 | -0.00 | +0.000 | 0 / 0 |
| harmonic | R3 rig 30cm cont | -17.12 | +0.03 | +0.06 | +0.000 | 0 / 0 |

Decision: component DROPPED (more failures: False; dA >= 0.3: False; dA1 >= 0.5: False; dtau >= 0.05: False)

## W5 C1 -detection vs W2 C1 = core + fixes
| noise | cell | median A ref (dB) | median dA (dB) | median dA1 (dB) | median dtau (s) | fail |
|---|---|---|---|---|---|---|
| ar1 | S8 stationary | -16.02 | +0.08 | - | +0.000 | 0 / 0 |
| ar1 | S1 src 10cm | -15.52 | +0.25 | +0.22 | +0.000 | 0 / 0 |
| ar1 | S2 src 30cm | -15.16 | +0.43 | +0.85 | +0.032 | 0 / 0 ** |
| ar1 | S5 src 30cm cont | -14.82 | +0.13 | -0.02 | +0.000 | 0 / 0 |
| ar1 | S7 rd abrupt | -15.46 | +3.12 | +6.21 | +0.112 | 0 / 0 ** |
| ar1 | R1 rig 10cm | -15.55 | +0.25 | +0.33 | +0.000 | 0 / 0 |
| ar1 | R2 rig 30cm | -15.35 | +0.55 | +1.35 | +0.048 | 0 / 0 ** |
| ar1 | R3 rig 30cm cont | -15.11 | +0.14 | -0.08 | +0.000 | 0 / 0 |
| harmonic | S8 stationary | -19.36 | -0.00 | - | +0.000 | 0 / 0 |
| harmonic | S1 src 10cm | -18.52 | +0.24 | +0.42 | +0.000 | 0 / 0 |
| harmonic | S2 src 30cm | -17.89 | +0.97 | +1.76 | +0.048 | 0 / 0 ** |
| harmonic | S5 src 30cm cont | -17.65 | +0.11 | +0.27 | +0.000 | 0 / 0 |
| harmonic | R1 rig 10cm | -18.52 | +0.26 | +0.47 | +0.000 | 0 / 0 |
| harmonic | R2 rig 30cm | -17.50 | +0.95 | +1.76 | +0.048 | 0 / 0 ** |
| harmonic | R3 rig 30cm cont | -17.12 | +0.25 | +0.43 | +0.000 | 0 / 0 |

Decision: component KEPT (more failures: False; dA >= 0.3: True; dA1 >= 0.5: True; dtau >= 0.05: True)

## W6 C1 -bank, restart (single window) vs W3 C1 -bank
| noise | cell | median A ref (dB) | median dA (dB) | median dA1 (dB) | median dtau (s) | fail |
|---|---|---|---|---|---|---|
| ar1 | S8 stationary | -15.80 | +0.00 | - | +0.000 | 0 / 0 |
| ar1 | S1 src 10cm | -15.46 | +0.10 | +0.54 | +0.000 | 0 / 0 ** |
| ar1 | S2 src 30cm | -15.09 | +0.11 | +0.59 | +0.000 | 0 / 0 ** |
| ar1 | S5 src 30cm cont | -14.80 | +0.21 | +0.45 | +0.000 | 0 / 0 |
| ar1 | S7 rd abrupt | -15.42 | +0.02 | +0.08 | +0.000 | 0 / 0 |
| ar1 | R1 rig 10cm | -15.44 | +0.14 | +0.72 | +0.000 | 0 / 0 ** |
| ar1 | R2 rig 30cm | -15.29 | +0.12 | +0.58 | +0.016 | 0 / 0 ** |
| ar1 | R3 rig 30cm cont | -14.91 | +0.21 | +0.51 | +0.000 | 0 / 0 ** |
| harmonic | S8 stationary | -19.13 | +0.00 | - | +0.000 | 0 / 0 |
| harmonic | S1 src 10cm | -18.40 | +0.05 | +0.24 | +0.000 | 0 / 0 |
| harmonic | S2 src 30cm | -17.80 | +0.06 | +0.17 | +0.000 | 0 / 0 |
| harmonic | S5 src 30cm cont | -15.95 | +0.04 | +0.17 | +0.000 | 0 / 0 |
| harmonic | R1 rig 10cm | -18.32 | +0.13 | +0.45 | +0.000 | 0 / 0 |
| harmonic | R2 rig 30cm | -17.35 | +0.05 | +0.15 | +0.000 | 0 / 0 |
| harmonic | R3 rig 30cm cont | -14.65 | +0.02 | +0.05 | +0.000 | 0 / 0 |

Decision: component KEPT (more failures: False; dA >= 0.3: False; dA1 >= 0.5: True; dtau >= 0.05: False)

## W7 C1 + loc_wide vs W2 C1 = core + fixes
| noise | cell | median A ref (dB) | median dA (dB) | median dA1 (dB) | median dtau (s) | fail |
|---|---|---|---|---|---|---|
| ar1 | S8 stationary | -16.02 | +0.00 | - | +0.000 | 0 / 0 |
| ar1 | S1 src 10cm | -15.52 | +0.00 | +0.00 | +0.000 | 0 / 0 |
| ar1 | S2 src 30cm | -15.16 | -0.00 | -0.00 | +0.000 | 0 / 0 |
| ar1 | S5 src 30cm cont | -14.82 | -0.00 | -0.00 | +0.000 | 0 / 0 |
| ar1 | S7 rd abrupt | -15.46 | +0.05 | +0.14 | +0.000 | 0 / 0 |
| ar1 | R1 rig 10cm | -15.55 | -0.00 | -0.01 | +0.000 | 0 / 0 |
| ar1 | R2 rig 30cm | -15.35 | -0.01 | -0.04 | +0.000 | 0 / 0 |
| ar1 | R3 rig 30cm cont | -15.11 | +0.00 | +0.00 | +0.000 | 0 / 0 |
| harmonic | S8 stationary | -19.36 | +0.00 | - | +0.000 | 0 / 0 |
| harmonic | S1 src 10cm | -18.52 | -0.03 | -0.14 | +0.000 | 0 / 0 |
| harmonic | S2 src 30cm | -17.89 | -0.03 | -0.08 | +0.000 | 0 / 0 |
| harmonic | S5 src 30cm cont | -17.65 | +0.03 | +0.07 | +0.000 | 0 / 0 |
| harmonic | R1 rig 10cm | -18.52 | -0.03 | -0.15 | +0.000 | 0 / 0 |
| harmonic | R2 rig 30cm | -17.50 | +0.01 | +0.03 | +0.000 | 0 / 0 |
| harmonic | R3 rig 30cm cont | -17.12 | +0.05 | +0.15 | +0.000 | 0 / 0 |

Decision: option not adopted (more failures: False; worse: False; better somewhere: False; mean dA1 -0.00 dB)

## W8 C1 + det_C_pre vs W2 C1 = core + fixes
| noise | cell | median A ref (dB) | median dA (dB) | median dA1 (dB) | median dtau (s) | fail |
|---|---|---|---|---|---|---|
| ar1 | S8 stationary | -16.02 | +0.00 | - | +0.000 | 0 / 0 |
| ar1 | S1 src 10cm | -15.52 | +0.00 | +0.00 | +0.000 | 0 / 0 |
| ar1 | S2 src 30cm | -15.16 | +0.00 | +0.00 | +0.000 | 0 / 0 |
| ar1 | S5 src 30cm cont | -14.82 | +0.00 | +0.00 | +0.000 | 0 / 0 |
| ar1 | S7 rd abrupt | -15.46 | +0.00 | +0.00 | +0.000 | 0 / 0 |
| ar1 | R1 rig 10cm | -15.55 | +0.00 | +0.00 | +0.000 | 0 / 0 |
| ar1 | R2 rig 30cm | -15.35 | +0.00 | +0.00 | +0.000 | 0 / 0 |
| ar1 | R3 rig 30cm cont | -15.11 | +0.00 | +0.00 | +0.000 | 0 / 0 |
| harmonic | S8 stationary | -19.36 | +0.00 | - | +0.000 | 0 / 0 |
| harmonic | S1 src 10cm | -18.52 | -0.06 | -0.26 | +0.000 | 0 / 0 |
| harmonic | S2 src 30cm | -17.89 | -0.35 | -1.34 | -0.008 | 0 / 0 |
| harmonic | S5 src 30cm cont | -17.65 | -0.23 | -0.63 | +0.000 | 0 / 0 |
| harmonic | R1 rig 10cm | -18.52 | -0.11 | -0.51 | +0.000 | 0 / 0 |
| harmonic | R2 rig 30cm | -17.50 | -0.73 | -2.50 | -0.024 | 0 / 0 |
| harmonic | R3 rig 30cm cont | -17.12 | -0.50 | -1.24 | +0.000 | 0 / 0 |

Decision: option ADOPTED (more failures: False; worse: False; better somewhere: True; mean dA1 -0.50 dB)

## W9 C1 + kd 128 vs W2 C1 = core + fixes
| noise | cell | median A ref (dB) | median dA (dB) | median dA1 (dB) | median dtau (s) | fail |
|---|---|---|---|---|---|---|
| ar1 | S8 stationary | -16.02 | +0.00 | - | +0.000 | 0 / 0 |
| ar1 | S1 src 10cm | -15.52 | +0.00 | +0.00 | +0.000 | 0 / 0 |
| ar1 | S2 src 30cm | -15.16 | +0.00 | +0.00 | +0.000 | 0 / 0 |
| ar1 | S5 src 30cm cont | -14.82 | +0.00 | +0.00 | +0.000 | 0 / 0 |
| ar1 | S7 rd abrupt | -15.46 | +0.00 | +0.00 | +0.000 | 0 / 0 |
| ar1 | R1 rig 10cm | -15.55 | +0.00 | +0.00 | +0.000 | 0 / 0 |
| ar1 | R2 rig 30cm | -15.35 | +0.00 | +0.00 | +0.000 | 0 / 0 |
| ar1 | R3 rig 30cm cont | -15.11 | +0.00 | +0.00 | +0.000 | 0 / 0 |
| harmonic | S8 stationary | -19.36 | +0.00 | - | +0.000 | 0 / 0 |
| harmonic | S1 src 10cm | -18.52 | -0.17 | -0.84 | +0.000 | 0 / 0 |
| harmonic | S2 src 30cm | -17.89 | -0.49 | -1.89 | -0.008 | 0 / 0 |
| harmonic | S5 src 30cm cont | -17.65 | -0.31 | -0.64 | +0.000 | 0 / 0 |
| harmonic | R1 rig 10cm | -18.52 | -0.25 | -1.17 | +0.000 | 0 / 0 |
| harmonic | R2 rig 30cm | -17.50 | -0.76 | -2.57 | -0.024 | 0 / 0 |
| harmonic | R3 rig 30cm cont | -17.12 | -0.37 | -0.49 | +0.000 | 0 / 0 |

Decision: option ADOPTED (more failures: False; worse: False; better somewhere: True; mean dA1 -0.58 dB)

## W10 C1 + all three options vs W2 C1 = core + fixes
| noise | cell | median A ref (dB) | median dA (dB) | median dA1 (dB) | median dtau (s) | fail |
|---|---|---|---|---|---|---|
| ar1 | S8 stationary | -16.02 | +0.00 | - | +0.000 | 0 / 0 |
| ar1 | S1 src 10cm | -15.52 | +0.00 | +0.00 | +0.000 | 0 / 0 |
| ar1 | S2 src 30cm | -15.16 | +0.00 | +0.00 | +0.000 | 0 / 0 |
| ar1 | S5 src 30cm cont | -14.82 | -0.00 | -0.00 | +0.000 | 0 / 0 |
| ar1 | S7 rd abrupt | -15.46 | +0.05 | +0.12 | +0.000 | 0 / 0 |
| ar1 | R1 rig 10cm | -15.55 | +0.00 | +0.00 | +0.000 | 0 / 0 |
| ar1 | R2 rig 30cm | -15.35 | -0.00 | -0.02 | +0.000 | 0 / 0 |
| ar1 | R3 rig 30cm cont | -15.11 | +0.00 | -0.00 | +0.000 | 0 / 0 |
| harmonic | S8 stationary | -19.36 | +0.00 | - | +0.000 | 0 / 0 |
| harmonic | S1 src 10cm | -18.52 | -0.19 | -0.98 | +0.000 | 0 / 0 |
| harmonic | S2 src 30cm | -17.89 | -0.44 | -1.86 | +0.000 | 0 / 0 |
| harmonic | S5 src 30cm cont | -17.65 | -0.33 | -0.69 | +0.000 | 0 / 0 |
| harmonic | R1 rig 10cm | -18.52 | -0.24 | -1.16 | +0.000 | 0 / 0 |
| harmonic | R2 rig 30cm | -17.50 | -0.70 | -2.37 | -0.024 | 0 / 0 |
| harmonic | R3 rig 30cm cont | -17.12 | -0.45 | -1.00 | +0.000 | 0 / 0 |

Decision: option ADOPTED (more failures: False; worse: False; better somewhere: True; mean dA1 -0.61 dB)

## Cost (mean of flop_hist = flops per hop as logged by the simulator; S8 / change cells)
| variant | S8 | change cells |
|---|---|---|
| V0 v6.5 | 2400776 | 3551444 |
| W2 C1 = core + fixes | 1949073 | 2738545 |
| W3 C1 -bank | 1078797 | 1606593 |
| W4 C1 restart (no Prop. 9) | 1949073 | 2375519 |
| W5 C1 -detection | 2570708 | 2588697 |
| W6 C1 -bank, restart (single window) | 1078797 | 1245091 |
| W7 C1 + loc_wide | 1949073 | 2715323 |
| W8 C1 + det_C_pre | 1949045 | 2728931 |
| W9 C1 + kd 128 | 2800176 | 3533465 |
| W10 C1 + all three options | 2800148 | 3422588 |

## Decisions
- W2 C1 = core + fixes: adopted as core (more failures: False; max median dA +0.00 dB)
- W3 C1 -bank: component KEPT (more failures: False; dA >= 0.3: True; dA1 >= 0.5: True; dtau >= 0.05: True)
- W4 C1 restart (no Prop. 9): component DROPPED (more failures: False; dA >= 0.3: False; dA1 >= 0.5: False; dtau >= 0.05: False)
- W5 C1 -detection: component KEPT (more failures: False; dA >= 0.3: True; dA1 >= 0.5: True; dtau >= 0.05: True)
- W6 C1 -bank, restart (single window): component KEPT (more failures: False; dA >= 0.3: False; dA1 >= 0.5: True; dtau >= 0.05: False)
- W7 C1 + loc_wide: option not adopted (more failures: False; worse: False; better somewhere: False; mean dA1 -0.00 dB)
- W8 C1 + det_C_pre: option ADOPTED (more failures: False; worse: False; better somewhere: True; mean dA1 -0.50 dB)
- W9 C1 + kd 128: option ADOPTED (more failures: False; worse: False; better somewhere: True; mean dA1 -0.58 dB)
- W10 C1 + all three options: option ADOPTED (more failures: False; worse: False; better somewhere: True; mean dA1 -0.61 dB)
- Prop. 9 weighting: KEPT (kept if W4 or W6 keeps it)
- detector options adopted for the final core: W9 (single option with the largest mean improvement of A1)
- unparsable lines skipped: 0; records: 4500; stale (prm differs): 0; duplicates: 0 (differing: 0)
