# Ablation v6.5 -> core, set d (tuning seeds 300-309, 600-619; M = 512; T = 5 s)
Rules and metrics: experiments/ablation_core.py docstring (fixed before the runs). d = variant - reference, median over the 30 paired seeds; positive dA / dtau = the variant is worse. fail = failed runs (variant / reference).

## X2 low-cost: single window + Prop. 9 + det_C_pre vs Y0 single window + Prop. 9 (no det_C_pre)
| noise | cell | median A ref (dB) | median dA (dB) | median dA1 (dB) | median dtau (s) | fail |
|---|---|---|---|---|---|---|
| ar1 | S8 stationary | -15.80 | +0.00 | - | +0.000 | 0 / 0 |
| ar1 | S1 src 10cm | -15.46 | +0.00 | +0.00 | +0.000 | 0 / 0 |
| ar1 | S2 src 30cm | -15.09 | +0.00 | +0.00 | +0.000 | 0 / 0 |
| ar1 | S5 src 30cm cont | -14.80 | +0.00 | +0.00 | +0.000 | 0 / 0 |
| ar1 | S7 rd abrupt | -15.42 | +0.00 | +0.00 | +0.000 | 0 / 0 |
| ar1 | R1 rig 10cm | -15.44 | +0.00 | +0.00 | +0.000 | 0 / 0 |
| ar1 | R2 rig 30cm | -15.29 | +0.00 | +0.00 | +0.000 | 0 / 0 |
| ar1 | R3 rig 30cm cont | -14.91 | +0.00 | +0.00 | +0.000 | 0 / 0 |
| harmonic | S8 stationary | -19.13 | +0.00 | - | +0.000 | 0 / 0 |
| harmonic | S1 src 10cm | -18.40 | -0.06 | -0.31 | +0.000 | 0 / 0 |
| harmonic | S2 src 30cm | -17.80 | -0.37 | -1.40 | +0.000 | 0 / 0 |
| harmonic | S5 src 30cm cont | -15.95 | -1.72 | -1.34 | -0.112 | 0 / 0 |
| harmonic | R1 rig 10cm | -18.32 | -0.23 | -0.84 | +0.000 | 0 / 0 |
| harmonic | R2 rig 30cm | -17.35 | -0.79 | -2.36 | -0.016 | 0 / 0 |
| harmonic | R3 rig 30cm cont | -14.65 | -2.20 | -2.06 | -0.240 | 0 / 0 |

Decision: diagnostic (more failures than Y0: False; max median dA +0.00 dB; mean dA1 -0.64 dB)

## L24 X2, L = 24 hops vs X2 low-cost: single window + Prop. 9 + det_C_pre
| noise | cell | median A ref (dB) | median dA (dB) | median dA1 (dB) | median dtau (s) | fail |
|---|---|---|---|---|---|---|
| ar1 | S8 stationary | -15.80 | +0.39 | - | +0.000 | 0 / 0 ** |
| ar1 | S1 src 10cm | -15.46 | +0.32 | +0.05 | +0.000 | 0 / 0 ** |
| ar1 | S2 src 30cm | -15.13 | +0.30 | +0.02 | +0.000 | 0 / 0 ** |
| ar1 | S5 src 30cm cont | -14.90 | +0.24 | -0.01 | +0.000 | 0 / 0 |
| ar1 | S7 rd abrupt | -15.55 | +0.18 | -0.00 | +0.000 | 0 / 0 |
| ar1 | R1 rig 10cm | -15.44 | +0.32 | +0.00 | +0.000 | 0 / 0 ** |
| ar1 | R2 rig 30cm | -15.30 | +0.32 | +0.00 | +0.000 | 0 / 0 ** |
| ar1 | R3 rig 30cm cont | -14.91 | +0.19 | -0.01 | +0.000 | 0 / 0 |
| harmonic | S8 stationary | -19.13 | +0.29 | - | +0.000 | 0 / 0 |
| harmonic | S1 src 10cm | -18.51 | +0.23 | +0.02 | +0.000 | 0 / 0 |
| harmonic | S2 src 30cm | -18.33 | +0.21 | +0.03 | +0.000 | 0 / 0 |
| harmonic | S5 src 30cm cont | -17.52 | +0.11 | +0.18 | +0.000 | 0 / 0 |
| harmonic | R1 rig 10cm | -18.54 | +0.26 | +0.19 | +0.000 | 0 / 0 |
| harmonic | R2 rig 30cm | -18.06 | +0.21 | +0.01 | +0.000 | 0 / 0 |
| harmonic | R3 rig 30cm cont | -17.23 | +0.22 | +0.12 | +0.000 | 0 / 0 |

Decision: diagnostic (more failures than X2: False; max median dA +0.39 dB; mean dA1 +0.05 dB)

## L96 X2, L = 96 hops vs X2 low-cost: single window + Prop. 9 + det_C_pre
| noise | cell | median A ref (dB) | median dA (dB) | median dA1 (dB) | median dtau (s) | fail |
|---|---|---|---|---|---|---|
| ar1 | S8 stationary | -15.80 | -0.16 | - | +0.000 | 0 / 0 |
| ar1 | S1 src 10cm | -15.46 | -0.03 | +0.30 | +0.000 | 0 / 0 |
| ar1 | S2 src 30cm | -15.13 | -0.03 | +0.27 | +0.000 | 0 / 0 |
| ar1 | S5 src 30cm cont | -14.90 | +0.04 | +0.23 | +0.000 | 0 / 0 |
| ar1 | S7 rd abrupt | -15.55 | -0.06 | +0.04 | +0.000 | 0 / 0 |
| ar1 | R1 rig 10cm | -15.44 | -0.00 | +0.45 | +0.000 | 0 / 0 |
| ar1 | R2 rig 30cm | -15.30 | -0.07 | +0.18 | +0.000 | 0 / 0 |
| ar1 | R3 rig 30cm cont | -14.91 | +0.01 | +0.28 | +0.000 | 0 / 0 |
| harmonic | S8 stationary | -19.13 | -0.14 | - | +0.000 | 0 / 0 |
| harmonic | S1 src 10cm | -18.51 | -0.08 | +0.05 | +0.000 | 0 / 0 |
| harmonic | S2 src 30cm | -18.33 | -0.07 | +0.02 | +0.000 | 0 / 0 |
| harmonic | S5 src 30cm cont | -17.52 | +0.10 | +0.20 | +0.000 | 0 / 0 |
| harmonic | R1 rig 10cm | -18.54 | -0.07 | +0.04 | +0.000 | 0 / 0 |
| harmonic | R2 rig 30cm | -18.06 | -0.07 | +0.02 | +0.000 | 0 / 0 |
| harmonic | R3 rig 30cm cont | -17.23 | +0.09 | +0.23 | +0.000 | 0 / 0 |

Decision: diagnostic (more failures than X2: False; max median dA +0.10 dB; mean dA1 +0.18 dB)

## L192 X2, L = 192 hops vs X2 low-cost: single window + Prop. 9 + det_C_pre
| noise | cell | median A ref (dB) | median dA (dB) | median dA1 (dB) | median dtau (s) | fail |
|---|---|---|---|---|---|---|
| ar1 | S8 stationary | -15.80 | -0.28 | - | +0.000 | 0 / 0 |
| ar1 | S1 src 10cm | -15.46 | -0.02 | +0.30 | +0.000 | 0 / 0 |
| ar1 | S2 src 30cm | -15.13 | -0.04 | +0.27 | +0.000 | 0 / 0 |
| ar1 | S5 src 30cm cont | -14.90 | +0.07 | +0.23 | +0.000 | 0 / 0 |
| ar1 | S7 rd abrupt | -15.55 | -0.08 | +0.04 | +0.000 | 0 / 0 |
| ar1 | R1 rig 10cm | -15.44 | +0.03 | +0.45 | +0.000 | 0 / 0 |
| ar1 | R2 rig 30cm | -15.30 | -0.10 | +0.18 | +0.000 | 0 / 0 |
| ar1 | R3 rig 30cm cont | -14.91 | +0.02 | +0.28 | +0.000 | 0 / 0 |
| harmonic | S8 stationary | -19.13 | -0.22 | - | +0.000 | 0 / 0 |
| harmonic | S1 src 10cm | -18.51 | -0.10 | +0.05 | +0.000 | 0 / 0 |
| harmonic | S2 src 30cm | -18.33 | -0.09 | +0.02 | +0.000 | 0 / 0 |
| harmonic | S5 src 30cm cont | -17.52 | +0.12 | +0.20 | +0.000 | 0 / 0 |
| harmonic | R1 rig 10cm | -18.54 | -0.10 | +0.04 | +0.000 | 0 / 0 |
| harmonic | R2 rig 30cm | -18.06 | -0.08 | +0.02 | +0.000 | 0 / 0 |
| harmonic | R3 rig 30cm cont | -17.23 | +0.13 | +0.23 | +0.000 | 0 / 0 |

Decision: diagnostic (more failures than X2: False; max median dA +0.13 dB; mean dA1 +0.18 dB)

## Cost (mean of flop_hist = flops per hop as logged by the simulator; S8 / change cells)
| variant | S8 | change cells |
|---|---|---|
| Y0 single window + Prop. 9 (no det_C_pre) | 1078797 | 1606593 |
| X2 low-cost: single window + Prop. 9 + det_C_pre | 1078769 | 1592117 |
| L24 X2, L = 24 hops | 1287015 | 1680903 |
| L96 X2, L = 96 hops | 944920 | 1496311 |
| L192 X2, L = 192 hops | 809979 | 1596257 |

## Decisions
- X2 low-cost: single window + Prop. 9 + det_C_pre: diagnostic (more failures than Y0: False; max median dA +0.00 dB; mean dA1 -0.64 dB)
- L24 X2, L = 24 hops: diagnostic (more failures than X2: False; max median dA +0.39 dB; mean dA1 +0.05 dB)
- L96 X2, L = 96 hops: diagnostic (more failures than X2: False; max median dA +0.10 dB; mean dA1 +0.18 dB)
- L192 X2, L = 192 hops: diagnostic (more failures than X2: False; max median dA +0.13 dB; mean dA1 +0.18 dB)
- set d: no component decision in this set
- unparsable lines skipped: 0; records: 2250; stale (prm differs): 0; duplicates: 0 (differing: 0)
