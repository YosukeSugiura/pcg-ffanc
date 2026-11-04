# Ablation v6.5 -> core, set c (tuning seeds 300-309, 600-619; M = 512; T = 5 s)
Rules and metrics: experiments/ablation_core.py docstring (fixed before the runs). d = variant - reference, median over the 30 paired seeds; positive dA / dtau = the variant is worse. fail = failed runs (variant / reference).

## X1 final core = C1 restart + det_C_pre vs W4 C1 restart (no Prop. 9)
| noise | cell | median A ref (dB) | median dA (dB) | median dA1 (dB) | median dtau (s) | fail |
|---|---|---|---|---|---|---|
| ar1 | S8 stationary | -16.02 | +0.00 | - | +0.000 | 0 / 0 |
| ar1 | S1 src 10cm | -15.43 | +0.00 | +0.00 | +0.000 | 0 / 0 |
| ar1 | S2 src 30cm | -15.13 | +0.00 | +0.00 | +0.000 | 0 / 0 |
| ar1 | S5 src 30cm cont | -14.79 | +0.00 | +0.00 | +0.000 | 0 / 0 |
| ar1 | S7 rd abrupt | -15.42 | +0.00 | +0.00 | +0.000 | 0 / 0 |
| ar1 | R1 rig 10cm | -15.38 | +0.00 | +0.00 | +0.000 | 0 / 0 |
| ar1 | R2 rig 30cm | -15.32 | +0.00 | +0.00 | +0.000 | 0 / 0 |
| ar1 | R3 rig 30cm cont | -15.03 | +0.00 | +0.00 | +0.000 | 0 / 0 |
| harmonic | S8 stationary | -19.36 | +0.00 | - | +0.000 | 0 / 0 |
| harmonic | S1 src 10cm | -18.51 | -0.04 | -0.18 | +0.000 | 0 / 0 |
| harmonic | S2 src 30cm | -17.90 | -0.32 | -1.27 | -0.008 | 0 / 0 |
| harmonic | S5 src 30cm cont | -17.48 | -0.01 | -0.02 | +0.000 | 0 / 0 |
| harmonic | R1 rig 10cm | -18.51 | -0.10 | -0.47 | +0.000 | 0 / 0 |
| harmonic | R2 rig 30cm | -17.49 | -0.69 | -2.43 | -0.024 | 0 / 0 |
| harmonic | R3 rig 30cm cont | -17.08 | -0.01 | -0.02 | +0.000 | 0 / 0 |

Decision: CONFIRMED (more failures: False; worse: False; max median dA +0.00 dB)

## X2 low-cost: single window + Prop. 9 + det_C_pre vs X1 final core = C1 restart + det_C_pre
| noise | cell | median A ref (dB) | median dA (dB) | median dA1 (dB) | median dtau (s) | fail |
|---|---|---|---|---|---|---|
| ar1 | S8 stationary | -16.02 | +0.18 | - | +0.000 | 0 / 0 |
| ar1 | S1 src 10cm | -15.37 | +0.03 | -0.26 | +0.000 | 0 / 0 |
| ar1 | S2 src 30cm | -15.12 | +0.06 | -0.14 | +0.000 | 0 / 0 |
| ar1 | S5 src 30cm cont | -14.79 | +0.05 | +0.11 | +0.000 | 0 / 0 |
| ar1 | S7 rd abrupt | -15.49 | -0.02 | -0.18 | +0.000 | 0 / 0 |
| ar1 | R1 rig 10cm | -15.38 | +0.02 | -0.37 | +0.000 | 0 / 0 |
| ar1 | R2 rig 30cm | -15.32 | +0.03 | -0.33 | +0.000 | 0 / 0 |
| ar1 | R3 rig 30cm cont | -15.03 | +0.09 | +0.04 | +0.000 | 0 / 0 |
| harmonic | S8 stationary | -19.36 | +0.24 | - | +0.000 | 0 / 0 |
| harmonic | S1 src 10cm | -18.64 | +0.14 | +0.19 | +0.000 | 0 / 0 |
| harmonic | S2 src 30cm | -18.23 | +0.02 | -0.22 | +0.000 | 0 / 0 |
| harmonic | S5 src 30cm cont | -17.49 | -0.01 | -0.05 | +0.000 | 0 / 0 |
| harmonic | R1 rig 10cm | -18.68 | +0.11 | +0.04 | +0.000 | 0 / 0 |
| harmonic | R2 rig 30cm | -18.11 | +0.07 | -0.10 | +0.000 | 0 / 0 |
| harmonic | R3 rig 30cm cont | -17.07 | -0.18 | -0.70 | +0.000 | 0 / 0 |

Decision: diagnostic (more failures than X1: False; max median dA +0.24 dB; mean dA1 -0.15 dB)

## Cost (mean of flop_hist = flops per hop as logged by the simulator; S8 / change cells)
| variant | S8 | change cells |
|---|---|---|
| W4 C1 restart (no Prop. 9) | 1949073 | 2375519 |
| X1 final core = C1 restart + det_C_pre | 1949045 | 2361222 |
| X2 low-cost: single window + Prop. 9 + det_C_pre | 1078769 | 1592117 |

## Decisions
- X1 final core = C1 restart + det_C_pre: CONFIRMED (more failures: False; worse: False; max median dA +0.00 dB)
- X2 low-cost: single window + Prop. 9 + det_C_pre: diagnostic (more failures than X1: False; max median dA +0.24 dB; mean dA1 -0.15 dB)
- set c: confirmation run (Prop. 9 removed by decision)
- unparsable lines skipped: 0; records: 1350; stale (prm differs): 0; duplicates: 0 (differing: 0)
