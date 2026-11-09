# Rule 11 Sec. 6.4 smoke (tuning seed 300 only; performance recorded, not used for any choice)

Criterion (Rule 11a Sec. 3.2, room-A rows): (s1) any non-finite value -> FAIL; (s2) NR >= 0 dB in a
tuning-grid configuration -> recorded only (the tuning admissibility removes it); (s3) NR >= 0 dB in G0-G5 or
an existing selected method -> FAIL; (s4) a switching / restart log missing -> FAIL. Rooms B / C: one key
(harmonic R2) of the 11-D method set, for the run-time estimate only (no criterion).

| method | room | noise | cell | finite | NR (dB) | A1 / A2 (dB) | wall (s) | events / restarts | log |
|---|---|---|---|---|---|---|---|---|---|
| E-PCG | A | ar1 | S8 stationary | True | -15.84 | -13.74 / -16.09 | 0.39 |  | det [] |
| PCG-WLS (fixed order) | A | ar1 | S8 stationary | True | -15.59 | -12.58 / -16.09 | 0.39 |  | det [] |
| PCG-WLS (restart) | A | ar1 | S8 stationary | True | -15.84 | -13.74 / -16.09 | 0.39 |  | det [] |
| PCG-WLS (no detector) | A | ar1 | S8 stationary | True | -15.84 | -13.74 / -16.09 | 0.26 |  | det [] |
| PCG-WLS (fixed order, restart) | A | ar1 | S8 stationary | True | -15.59 | -12.58 / -16.09 | 0.39 |  | det [] |
| PCG-WLS (exact solver) | A | ar1 | S8 stationary | True | -15.81 | -13.58 / -16.09 | 12.11 |  | det [] |
| MFBLMS | A | ar1 | S8 stationary | True | -12.98 | -7.26 / -16.22 | 0.1 |  |  |
| MFBLMS | A | ar1 | S8 stationary | True | -14.52 | -9.95 / -15.49 | 0.1 |  |  |
| switching FD-FxNLMS [6] | A | ar1 | S8 stationary | True | -15.69 | -12.84 / -16.24 | 0.11 |  | sw [[34, 'M', 'dJ'], [38, 'C', 'calibrate'], [42, 'M', 'calibrated', 0.006236316740222726], [98, 'N', 'zeta'], [138, 'M', 'dJ'], [142, 'C', 'calibrate'], [146, 'M', 'calibrated', 0.006932424719884675]] hops {'N': 75, 'M': 229, 'C': 8} |
| switching FD-FxNLMS + det | A | ar1 | S8 stationary | True | -15.69 | -12.84 / -16.23 | 0.1 | 0 / 0 | sw [[34, 'M', 'dJ']] hops {'N': 35, 'M': 277, 'C': 0} |
| RLS + det (cond.) | A | ar1 | S8 stationary | True | -15.78 | -12.75 / -16.37 | 9.32 | 0 / 0 | cond [] |
| RLS + det + growth | A | ar1 | S8 stationary | True | -15.78 | -12.75 / -16.37 | 9.14 | 0 / 0 |  |
| RLS + det + growth (from start) | A | ar1 | S8 stationary | True | -15.74 | -12.61 / -16.37 | 9.11 | 0 / 0 |  |
| MFBLMS + det | A | ar1 | S8 stationary | True | -12.98 | -7.26 / -16.22 | 0.13 | 0 / 0 |  |
| RLS [outer 1] | A | ar1 | S8 stationary | True | -15.24 | -12.55 / -15.64 | 9.21 |  |  |
| VFF-RLS [outer 1] | A | ar1 | S8 stationary | True | -14.91 | -10.47 / -15.96 | 12.86 |  |  |
| SFTF-H + det [outer 1] | A | ar1 | S8 stationary | True | -15.78 | -12.77 / -16.37 | 0.79 | 0 / 0 |  |
| RLS + CUSUM [outer 1] | A | ar1 | S8 stationary | True | -15.63 | -12.75 / -16.04 | 10.71 |  | cusum [[28288, 25216], [29568, 28288], [31616, 29568]] |
| FD-FxNLMS [outer 1] | A | ar1 | S8 stationary | True | -15.61 | -13.00 / -16.00 | 0.09 |  |  |
| leaky FD-FxNLMS [outer 1] | A | ar1 | S8 stationary | True | -13.00 | -12.71 / -12.72 | 0.09 |  |  |
| FDKF [outer 1] | A | ar1 | S8 stationary | True | -12.74 | -7.26 / -14.92 | 0.11 |  |  |
| FD-FxNLMS + det [outer 1] | A | ar1 | S8 stationary | True | -15.06 | -10.70 / -16.18 | 0.11 | 0 / 0 |  |
| E-PCG | A | ar1 | S2 src 30cm | True | -16.26 | -15.07 / -17.35 | 0.52 |  | det [[8064, 7996]] |
| PCG-WLS (fixed order) | A | ar1 | S2 src 30cm | True | -15.57 | -12.77 / -17.35 | 0.47 |  | det [[8064, 7996]] |
| PCG-WLS (restart) | A | ar1 | S2 src 30cm | True | -16.22 | -14.85 / -17.35 | 0.39 |  | det [[8064, 7996]] |
| PCG-WLS (no detector) | A | ar1 | S2 src 30cm | True | -14.10 | -8.41 / -17.04 | 0.27 |  | det [] |
| PCG-WLS (fixed order, restart) | A | ar1 | S2 src 30cm | True | -13.73 | -7.74 / -17.35 | 0.4 |  | det [[8064, 7996]] |
| PCG-WLS (exact solver) | A | ar1 | S2 src 30cm | True | -16.22 | -15.03 / -17.35 | 14.31 |  | det [[8064, 7996]] |
| MFBLMS | A | ar1 | S2 src 30cm | True | -11.70 | -7.98 / -15.04 | 0.11 |  |  |
| MFBLMS | A | ar1 | S2 src 30cm | True | -13.97 | -10.05 / -16.83 | 0.12 |  |  |
| switching FD-FxNLMS [6] | A | ar1 | S2 src 30cm | True | -12.91 | -7.83 / -14.92 | 0.12 |  | sw [[34, 'M', 'dJ'], [38, 'C', 'calibrate'], [42, 'M', 'calibrated', 0.006236316740222726], [310, 'N', 'zeta']] hops {'N': 36, 'M': 272, 'C': 4} |
| switching FD-FxNLMS + det | A | ar1 | S2 src 30cm | True | -14.00 | -9.45 / -16.00 | 0.11 | 1 / 1 | sw [[34, 'M', 'dJ'], [62, 'N', 'event'], [73, 'M', 'dJ']] hops {'N': 47, 'M': 265, 'C': 0} |
| RLS + det (cond.) | A | ar1 | S2 src 30cm | True | -15.74 | -12.95 / -17.54 | 11.7 | 1 / 1 | cond [[62, 8064, 7996, 12.877725691789246, 32, True]] |
| RLS + det + growth | A | ar1 | S2 src 30cm | True | -15.70 | -12.79 / -17.54 | 9.06 | 1 / 1 |  |
| RLS + det + growth (from start) | A | ar1 | S2 src 30cm | True | -15.67 | -12.79 / -17.54 | 9.22 | 1 / 1 |  |
| MFBLMS + det | A | ar1 | S2 src 30cm | True | -11.95 | -8.50 / -15.33 | 0.12 | 1 / 1 |  |
| RLS [outer 1] | A | ar1 | S2 src 30cm | True | -14.87 | -11.04 / -16.92 | 9.26 |  |  |
| VFF-RLS [outer 1] | A | ar1 | S2 src 30cm | True | -14.24 | -10.09 / -17.13 | 13.24 |  |  |
| SFTF-H + det [outer 1] | A | ar1 | S2 src 30cm | True | -15.74 | -12.95 / -17.54 | 5.12 | 1 / 1 |  |
| RLS + CUSUM [outer 1] | A | ar1 | S2 src 30cm | True | -15.39 | -11.99 / -17.32 | 11.18 |  | cusum [[8448, 8192], [8960, 8448], [28544, 25344], [30464, 28672], [32128, 30592]] |
| FD-FxNLMS [outer 1] | A | ar1 | S2 src 30cm | True | -14.72 | -10.08 / -17.11 | 0.1 |  |  |
| leaky FD-FxNLMS [outer 1] | A | ar1 | S2 src 30cm | True | -12.60 | -9.64 / -13.46 | 0.1 |  |  |
| FDKF [outer 1] | A | ar1 | S2 src 30cm | True | -11.66 | -7.78 / -14.86 | 0.11 |  |  |
| FD-FxNLMS + det [outer 1] | A | ar1 | S2 src 30cm | True | -13.77 | -9.22 / -16.54 | 0.11 | 1 / 1 |  |
| E-PCG | A | harmonic | R2 rig 30cm | True | -16.65 | -13.71 / -18.25 | 0.47 |  | det [[8064, 7996]] |
| PCG-WLS (fixed order) | A | harmonic | R2 rig 30cm | True | -15.23 | -9.51 / -18.22 | 0.52 |  | det [[8064, 7996]] |
| PCG-WLS (restart) | A | harmonic | R2 rig 30cm | True | -16.48 | -12.91 / -18.25 | 0.45 |  | det [[8064, 7996]] |
| PCG-WLS (no detector) | A | harmonic | R2 rig 30cm | True | -11.84 | -3.40 / -17.25 | 0.34 |  | det [] |
| PCG-WLS (fixed order, restart) | A | harmonic | R2 rig 30cm | True | -12.55 | -4.35 / -18.14 | 0.45 |  | det [[8064, 7996]] |
| PCG-WLS (exact solver) | A | harmonic | R2 rig 30cm | True | -16.62 | -13.69 / -18.24 | 14.45 |  | det [[8064, 7996]] |
| MFBLMS | A | harmonic | R2 rig 30cm | True | -11.76 | -6.02 / -15.66 | 0.14 |  |  |
| MFBLMS | A | harmonic | R2 rig 30cm | True | 21.74 (s2 recorded) | 0.00 / 0.00 | 0.13 |  |  |
| switching FD-FxNLMS [6] | A | harmonic | R2 rig 30cm | True | -13.73 | -6.71 / -17.71 | 0.15 |  | sw [[22, 'M', 'dJ'], [26, 'C', 'calibrate'], [30, 'M', 'calibrated', 0.031187714478741198], [35, 'N', 'zeta'], [43, 'M', 'dJ'], [47, 'C', 'calibrate'], [51, 'M', 'calibrated', 0.032276359101071635], [58, 'N', 'zeta'], [67, 'M', 'dJ'], [71, 'C', 'calibrate'], [75, 'M', 'calibrated', 0.00499822956098764], [79, 'N', 'zeta'], [94, 'M', 'dJ'], [98, 'C', 'calibrate'], [102, 'M', 'calibrated', 0.02434583421934004], [110, 'N', 'zeta'], [120, 'M', 'dJ'], [124, 'C', 'calibrate'], [128, 'M', 'calibrated', 0.031177797474314924], [160, 'N', 'zeta'], [164, 'M', 'dJ'], [168, 'C', 'calibrate'], [172, 'M', 'calibrated', 0.029462620739475337], [176, 'N', 'zeta'], [182, 'M', 'dJ'], [186, 'C', 'calibrate'], [190, 'M', 'calibrated', 0.030078108323106305], [200, 'N', 'zeta'], [206, 'M', 'dJ'], [210, 'C', 'calibrate'], [214, 'M', 'calibrated', 0.03028234668229638], [221, 'N', 'zeta'], [235, 'M', 'dJ'], [239, 'C', 'calibrate'], [243, 'M', 'calibrated', 0.03015851199167018], [250, 'N', 'zeta'], [255, 'M', 'dJ'], [259, 'C', 'calibrate'], [263, 'M', 'calibrated', 0.04103979177302202], [285, 'N', 'zeta'], [290, 'M', 'dJ'], [294, 'C', 'calibrate'], [298, 'M', 'calibrated', 0.031681420577788874], [308, 'N', 'zeta']] hops {'N': 108, 'M': 160, 'C': 44} |
| switching FD-FxNLMS + det | A | harmonic | R2 rig 30cm | True | -13.29 | -6.45 / -16.65 | 0.14 | 1 / 1 | sw [[22, 'M', 'dJ'], [62, 'N', 'event'], [67, 'M', 'dJ']] hops {'N': 29, 'M': 283, 'C': 0} |
| RLS + det (cond.) | A | harmonic | R2 rig 30cm | True | -16.31 | -12.59 / -18.39 | 9.9 | 1 / 1 | cond [[62, 8064, 7996, 19.49174643980682, 32, True]] |
| RLS + det + growth | A | harmonic | R2 rig 30cm | True | -15.82 | -10.80 / -18.39 | 11.84 | 1 / 1 |  |
| RLS + det + growth (from start) | A | harmonic | R2 rig 30cm | True | -15.86 | -10.80 / -18.39 | 13.46 | 1 / 1 |  |
| MFBLMS + det | A | harmonic | R2 rig 30cm | True | -12.40 | -7.88 / -15.79 | 0.17 | 1 / 1 |  |
| RLS [outer 1] | A | harmonic | R2 rig 30cm | True | -13.82 | -6.58 / -17.79 | 12.45 |  |  |
| VFF-RLS [outer 1] | A | harmonic | R2 rig 30cm | True | -12.58 | -5.30 / -17.80 | 15.34 |  |  |
| SFTF-H + det [outer 1] | A | harmonic | R2 rig 30cm | True | -16.32 | -12.59 / -18.39 | 6.14 | 1 / 1 |  |
| RLS + CUSUM [outer 1] | A | harmonic | R2 rig 30cm | True | -15.59 | -10.11 / -18.39 | 12.62 |  | cusum [[8320, 8192], [8704, 8320]] |
| FD-FxNLMS [outer 1] | A | harmonic | R2 rig 30cm | True | -13.83 | -7.12 / -17.35 | 0.15 |  |  |
| leaky FD-FxNLMS [outer 1] | A | harmonic | R2 rig 30cm | True | -13.28 | -7.80 / -15.34 | 0.14 |  |  |
| FDKF [outer 1] | A | harmonic | R2 rig 30cm | True | -10.59 | -3.90 / -15.62 | 0.17 |  |  |
| FD-FxNLMS + det [outer 1] | A | harmonic | R2 rig 30cm | True | -12.51 | -5.53 / -17.08 | 0.16 | 1 / 1 |  |
| E-PCG | B | harmonic | R2 rig 30cm | True | 1.53 | 0.00 / 0.00 | 0.66 |  | det [[8192, 8076]] |
| FD-FxNLMS | B | harmonic | R2 rig 30cm | True | 29.87 | 0.00 / 0.00 | 0.23 |  |  |
| leaky FD-FxNLMS | B | harmonic | R2 rig 30cm | True | 33.90 | 0.00 / 0.00 | 0.22 |  |  |
| convex FD-FxNLMS | B | harmonic | R2 rig 30cm | True | 44.44 | 0.00 / 0.00 | 0.26 |  |  |
| FDKF | B | harmonic | R2 rig 30cm | True | 6.96 | 0.00 / 0.00 | 0.25 |  |  |
| RLS | B | harmonic | R2 rig 30cm | True | -11.43 | -8.28 / -12.73 | 11.13 |  |  |
| VFF-RLS | B | harmonic | R2 rig 30cm | True | -9.55 | -8.04 / -13.13 | 13.82 |  |  |
| FD-FxNLMS + det | B | harmonic | R2 rig 30cm | True | 6.22 | 0.00 / 0.00 | 0.24 | 1 / 1 |  |
| RLS + det | B | harmonic | R2 rig 30cm | True | -9.71 | -4.20 / -11.68 | 8.38 | 1 / 1 |  |
| FD-FxNLMS + restart | B | harmonic | R2 rig 30cm | True | 32.62 | 0.00 / 0.00 | 0.2 | 1 / 1 |  |
| SFTF + det | B | harmonic | R2 rig 30cm | True | -5.80 | 2.33 / -10.83 | 0.87 | 1 / 1 |  |
| SFTF-H + det | B | harmonic | R2 rig 30cm | True | -9.81 | -4.27 / -11.82 | 3.26 | 1 / 1 |  |
| CFTF + det | B | harmonic | R2 rig 30cm | True | -9.75 | -4.24 / -11.71 | 1.54 | 1 / 1 |  |
| RLS + CUSUM | B | harmonic | R2 rig 30cm | True | 39.99 | 0.00 / 0.00 | 5.13 |  | cusum [[8192, 7296], [8448, 8192], [8832, 8448], [9088, 8832], [9344, 9088], [9600, 9344], [9856, 9600], [10112, 9856], [10368, 10112], [10496, 10368], [10624, 10496], [10752, 10624], [10880, 10752], [11008, 10880], [11136, 11008], [11264, 11136], [11392, 11264], [11520, 11392], [11648, 11520], [11904, 11648], [12032, 11904], [12160, 12032], [12288, 12160], [12416, 12288], [12544, 12416], [12672, 12544], [12800, 12672], [12928, 12800], [13056, 12928], [13184, 13056], [13312, 13184], [13440, 13312], [13696, 13440]] |
| E-PCG bank | B | harmonic | R2 rig 30cm | True | -7.22 | -5.96 / -6.75 | 1.1 |  | det [[8192, 8076]] |
| MFBLMS | B | harmonic | R2 rig 30cm | True | 23.94 | 0.00 / 0.00 | 0.22 |  |  |
| MFBLMS + det | B | harmonic | R2 rig 30cm | True | -9.69 | -9.29 / -10.03 | 0.29 | 1 / 1 |  |
| switching FD-FxNLMS [6] | B | harmonic | R2 rig 30cm | True | -0.47 | 0.00 / 0.00 | 0.27 |  | sw [[10, 'M', 'dJ'], [14, 'C', 'calibrate'], [18, 'M', 'calibrated', 0.010324074791677443], [23, 'N', 'zeta'], [40, 'M', 'dJ'], [44, 'C', 'calibrate'], [48, 'M', 'calibrated', 0.016358013792825227], [52, 'N', 'zeta'], [59, 'M', 'dJ'], [63, 'C', 'calibrate'], [67, 'M', 'calibrated', 0.007162507248318095], [71, 'N', 'zeta'], [79, 'M', 'dJ'], [83, 'C', 'calibrate'], [87, 'M', 'calibrated', 0.010259782459875582], [97, 'N', 'zeta'], [105, 'M', 'dJ'], [109, 'C', 'calibrate'], [113, 'M', 'calibrated', 0.009757589954877494], [124, 'N', 'zeta'], [132, 'M', 'dJ'], [136, 'C', 'calibrate'], [140, 'M', 'calibrated', 0.01035698007048174], [152, 'N', 'zeta'], [159, 'M', 'dJ'], [163, 'C', 'calibrate'], [167, 'M', 'calibrated', 0.010212817957639998], [172, 'N', 'zeta'], [176, 'M', 'dJ'], [180, 'C', 'calibrate'], [184, 'M', 'calibrated', 0.00924318765143165], [189, 'N', 'zeta'], [203, 'M', 'dJ'], [207, 'C', 'calibrate'], [211, 'M', 'calibrated', 0.00764409468290366], [222, 'N', 'zeta'], [228, 'M', 'dJ'], [232, 'C', 'calibrate'], [236, 'M', 'calibrated', 0.006494478666692299], [240, 'N', 'zeta'], [251, 'M', 'dJ'], [255, 'C', 'calibrate'], [259, 'M', 'calibrated', 0.007977611674061878], [272, 'N', 'zeta'], [282, 'M', 'dJ'], [286, 'C', 'calibrate'], [290, 'M', 'calibrated', 0.008479036445659213], [300, 'N', 'zeta'], [305, 'M', 'dJ'], [309, 'C', 'calibrate']] hops {'N': 116, 'M': 146, 'C': 50} |
| switching FD-FxNLMS + det | B | harmonic | R2 rig 30cm | True | -9.76 | -8.83 / -9.81 | 0.23 | 1 / 1 | sw [[10, 'M', 'dJ'], [63, 'N', 'event'], [67, 'M', 'dJ']] hops {'N': 16, 'M': 296, 'C': 0} |
| RLS + det (cond.) | B | harmonic | R2 rig 30cm | True | -9.71 | -4.20 / -11.68 | 10.58 | 1 / 1 | cond [[63, 8192, 8076, 11.980943893575422, 32, True]] |
| RLS + det + growth | B | harmonic | R2 rig 30cm | True | -8.65 | -1.38 / -12.52 | 10.17 | 1 / 1 |  |
| RLS + det + growth (from start) | B | harmonic | R2 rig 30cm | True | -7.89 | -1.33 / -12.53 | 10.5 | 1 / 1 |  |
| E-PCG | C | harmonic | R2 rig 30cm | True | 47.62 | 0.00 / 0.00 | 1.5 |  | det [[8192, 8076]] |
| FD-FxNLMS | C | harmonic | R2 rig 30cm | True | 47.97 | 0.00 / 0.00 | 0.25 |  |  |
| leaky FD-FxNLMS | C | harmonic | R2 rig 30cm | True | 48.61 | 0.00 / 0.00 | 0.26 |  |  |
| convex FD-FxNLMS | C | harmonic | R2 rig 30cm | True | 48.85 | 0.00 / 0.00 | 0.27 |  |  |
| FDKF | C | harmonic | R2 rig 30cm | True | 28.55 | 0.00 / 0.00 | 0.35 |  |  |
| RLS | C | harmonic | R2 rig 30cm | True | 45.35 | 0.00 / 0.00 | 6.75 |  |  |
| VFF-RLS | C | harmonic | R2 rig 30cm | True | 45.57 | 0.00 / 0.00 | 9.19 |  |  |
| FD-FxNLMS + det | C | harmonic | R2 rig 30cm | True | 49.94 | 0.00 / 0.00 | 0.33 | 1 / 1 |  |
| RLS + det | C | harmonic | R2 rig 30cm | True | 37.08 | 0.00 / 0.00 | 9.99 | 1 / 1 |  |
| FD-FxNLMS + restart | C | harmonic | R2 rig 30cm | True | 47.96 | 0.00 / 0.00 | 0.27 | 1 / 1 |  |
| SFTF + det | C | harmonic | R2 rig 30cm | True | 39.41 | 0.00 / 0.00 | 1.04 | 1 / 1 |  |
| SFTF-H + det | C | harmonic | R2 rig 30cm | True | 38.03 | 0.00 / 0.00 | 2.8 | 1 / 1 |  |
| CFTF + det | C | harmonic | R2 rig 30cm | True | 37.05 | 0.00 / 0.00 | 1.36 | 1 / 1 |  |
| RLS + CUSUM | C | harmonic | R2 rig 30cm | True | 44.48 | 0.00 / 0.00 | 3.83 |  | cusum [[8192, 7040], [8448, 8192], [8704, 8448], [8960, 8704], [9216, 8960], [9472, 9216], [9600, 9472], [9728, 9600], [9856, 9728], [9984, 9856], [10112, 9984], [10240, 10112], [10368, 10240], [10496, 10368], [10624, 10496], [10752, 10624], [10880, 10752], [11008, 10880], [11136, 11008], [11264, 11136], [11392, 11264], [11520, 11392], [11648, 11520], [11776, 11648], [11904, 11776], [12032, 11904], [12160, 12032]] |
| E-PCG bank | C | harmonic | R2 rig 30cm | True | 43.60 | 0.00 / 0.00 | 0.8 |  | det [[8192, 8076]] |
| MFBLMS | C | harmonic | R2 rig 30cm | True | 46.77 | 0.00 / 0.00 | 0.2 |  |  |
| MFBLMS + det | C | harmonic | R2 rig 30cm | True | 44.08 | 0.00 / 0.00 | 0.29 | 1 / 1 |  |
| switching FD-FxNLMS [6] | C | harmonic | R2 rig 30cm | True | 41.35 | 0.00 / 0.00 | 0.33 |  | sw [[20, 'M', 'dJ'], [24, 'C', 'calibrate'], [28, 'M', 'calibrated', 0.007372358236505275], [32, 'N', 'zeta'], [39, 'M', 'dJ'], [43, 'C', 'calibrate'], [47, 'M', 'calibrated', 0.013409898040907359], [52, 'N', 'zeta'], [59, 'M', 'dJ'], [63, 'C', 'calibrate'], [67, 'M', 'calibrated', 0.012225804023056522], [78, 'N', 'zeta'], [91, 'M', 'dJ'], [95, 'C', 'calibrate'], [99, 'M', 'calibrated', 0.009242610898203362]] hops {'N': 48, 'M': 213, 'C': 16} |
| switching FD-FxNLMS + det | C | harmonic | R2 rig 30cm | True | 42.59 | 0.00 / 0.00 | 0.32 | 1 / 1 | sw [[20, 'M', 'dJ'], [63, 'N', 'event'], [69, 'M', 'dJ']] hops {'N': 28, 'M': 243, 'C': 0} |
| RLS + det (cond.) | C | harmonic | R2 rig 30cm | True | 37.08 | 0.00 / 0.00 | 9.66 | 1 / 1 | cond [[63, 8192, 8076, 14.071347419759938, 32, True]] |
| RLS + det + growth | C | harmonic | R2 rig 30cm | True | 37.74 | 0.00 / 0.00 | 9.9 | 1 / 1 |  |
| RLS + det + growth (from start) | C | harmonic | R2 rig 30cm | True | 37.88 | 0.00 / 0.00 | 9.88 | 1 / 1 |  |

## Judgement (Rule 11a Sec. 3.2)
- (s1) non-finite rows: none
- (s2) NR >= 0 dB in tuning-grid configurations (recorded only): ['MFBLMS / harmonic R2 rig 30cm']
- (s3) NR >= 0 dB in G0-G5 / existing selected methods: none
- (s4) rows without the required log: none

- wall time, smoke A: total 261.9 s over 66 runs
- wall time, smoke B: total 79.5 s over 22 runs
- wall time, smoke C: total 69.6 s over 22 runs

Result (room-A rows, Rule 11a s1 / s3 / s4): PASS
