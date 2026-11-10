# Revision 11-D M-S (MeshRIR, Rule 8a preprocessing) (holdout seeds 800-839; family F3, Rule 11 Sec. 5.3)

Baselines (26 = 13 + n_new): ['FD-FxNLMS', 'leaky FD-FxNLMS', 'convex FD-FxNLMS', 'FDKF', 'RLS', 'VFF-RLS', 'FD-FxNLMS + det', 'RLS + det', 'FD-FxNLMS + restart', 'SFTF + det', 'SFTF-H + det', 'CFTF + det', 'RLS + CUSUM', 'MFBLMS', 'MFBLMS + det', 'switching FD-FxNLMS [6]', 'switching FD-FxNLMS + det', 'RLS + det (cond.)', 'RLS + det + growth', 'RLS + det + growth (from start)', 'RLS (extended grid)', 'VFF-RLS (extended grid)', 'RLS + CUSUM (extended grid)', 'FD-FxNLMS (extended grid)', 'FDKF (extended grid)', 'FD-FxNLMS + det (extended grid)'].

## A1 / A2 median (Q1, Q3) over seeds (failed runs A1 = A2 = 0 dB); failures; success-only medians
| method | noise | cell | A1 | A2 | failures | A1 success-only | A2 success-only |
|---|---|---|---|---|---|---|---|
| E-PCG | ar1 | S8 stationary | -2.91 (-4.50, 0.46) | -6.42 (-7.41, -3.58) | 0/40 | -2.91 (-4.50, 0.46) | -6.42 (-7.41, -3.58) |
| E-PCG | harmonic | S8 stationary | -7.51 (-9.11, -3.65) | -14.47 (-15.71, -11.90) | 0/40 | -7.51 (-9.11, -3.65) | -14.47 (-15.71, -11.90) |
| FD-FxNLMS | ar1 | S8 stationary | -3.47 (-4.36, -1.32) | -5.33 (-6.42, -2.18) | 2/40 | -3.52 (-4.48, -2.23) | -5.38 (-6.52, -3.89) |
| FD-FxNLMS | harmonic | S8 stationary | -6.06 (-7.20, -4.62) | -11.31 (-13.18, -6.88) | 1/40 | -6.08 (-7.22, -4.84) | -11.34 (-13.19, -7.18) |
| leaky FD-FxNLMS | ar1 | S8 stationary | -3.21 (-4.31, -1.14) | -5.21 (-6.27, -2.25) | 2/40 | -3.26 (-4.48, -1.93) | -5.37 (-6.39, -3.81) |
| leaky FD-FxNLMS | harmonic | S8 stationary | -5.98 (-7.05, -3.77) | -10.25 (-12.41, -5.76) | 4/40 | -6.55 (-7.16, -4.57) | -10.67 (-12.54, -7.02) |
| convex FD-FxNLMS | ar1 | S8 stationary | -3.69 (-4.61, -1.76) | -5.49 (-6.63, -2.29) | 2/40 | -3.74 (-4.70, -2.48) | -5.63 (-6.69, -3.95) |
| convex FD-FxNLMS | harmonic | S8 stationary | -6.90 (-8.30, -4.85) | -12.78 (-13.86, -8.20) | 0/40 | -6.90 (-8.30, -4.85) | -12.78 (-13.86, -8.20) |
| FDKF | ar1 | S8 stationary | 0.48 (0.00, 1.07) | -5.35 (-6.38, -2.29) | 4/40 | 0.58 (0.02, 1.24) | -5.52 (-6.54, -4.02) |
| FDKF | harmonic | S8 stationary | -1.56 (-2.11, -0.57) | -12.14 (-13.45, -9.08) | 0/40 | -1.56 (-2.11, -0.57) | -12.14 (-13.45, -9.08) |
| RLS | ar1 | S8 stationary | -2.53 (-4.29, 0.61) | -6.06 (-7.07, -3.32) | 2/40 | -2.82 (-4.31, 0.61) | -6.22 (-7.23, -4.21) |
| RLS | harmonic | S8 stationary | -7.71 (-9.85, -2.76) | -14.13 (-15.38, -11.40) | 0/40 | -7.71 (-9.85, -2.76) | -14.13 (-15.38, -11.40) |
| VFF-RLS | ar1 | S8 stationary | 0.31 (-1.63, 4.37) | -6.11 (-7.12, -3.36) | 2/40 | 0.35 (-1.93, 4.54) | -6.27 (-7.30, -4.24) |
| VFF-RLS | harmonic | S8 stationary | -4.11 (-7.74, 2.88) | -14.28 (-15.50, -11.51) | 0/40 | -4.11 (-7.74, 2.88) | -14.28 (-15.50, -11.51) |
| FD-FxNLMS + det | ar1 | S8 stationary | -3.56 (-4.35, -1.74) | -5.42 (-6.58, -2.09) | 2/40 | -3.78 (-4.46, -2.41) | -5.61 (-6.60, -3.76) |
| FD-FxNLMS + det | harmonic | S8 stationary | -5.70 (-6.99, -3.77) | -12.59 (-13.77, -8.53) | 0/40 | -5.70 (-6.99, -3.77) | -12.59 (-13.77, -8.53) |
| RLS + det | ar1 | S8 stationary | -2.88 (-4.48, 0.78) | -6.66 (-7.62, -3.79) | 0/40 | -2.88 (-4.48, 0.78) | -6.66 (-7.62, -3.79) |
| RLS + det | harmonic | S8 stationary | -7.83 (-10.01, -3.06) | -14.65 (-15.92, -12.08) | 0/40 | -7.83 (-10.01, -3.06) | -14.65 (-15.92, -12.08) |
| FD-FxNLMS + restart | ar1 | S8 stationary | -3.47 (-4.36, -1.32) | -5.33 (-6.42, -2.18) | 2/40 | -3.52 (-4.48, -2.23) | -5.38 (-6.52, -3.89) |
| FD-FxNLMS + restart | harmonic | S8 stationary | -6.06 (-7.20, -4.62) | -11.31 (-13.18, -6.88) | 1/40 | -6.08 (-7.22, -4.84) | -11.34 (-13.19, -7.18) |
| SFTF + det | ar1 | S8 stationary | -2.92 (-4.50, 0.74) | -6.66 (-7.62, -3.79) | 0/40 | -2.92 (-4.50, 0.74) | -6.66 (-7.62, -3.79) |
| SFTF + det | harmonic | S8 stationary | -7.85 (-10.03, -3.14) | -14.65 (-15.92, -12.08) | 0/40 | -7.85 (-10.03, -3.14) | -14.65 (-15.92, -12.08) |
| SFTF-H + det | ar1 | S8 stationary | -2.92 (-4.50, 0.74) | -6.66 (-7.62, -3.79) | 0/40 | -2.92 (-4.50, 0.74) | -6.66 (-7.62, -3.79) |
| SFTF-H + det | harmonic | S8 stationary | -7.85 (-10.03, -3.14) | -14.65 (-15.92, -12.08) | 0/40 | -7.85 (-10.03, -3.14) | -14.65 (-15.92, -12.08) |
| CFTF + det | ar1 | S8 stationary | -2.92 (-4.50, 0.74) | -6.66 (-7.62, -3.79) | 0/40 | -2.92 (-4.50, 0.74) | -6.66 (-7.62, -3.79) |
| CFTF + det | harmonic | S8 stationary | -7.85 (-10.03, -3.14) | -14.65 (-15.92, -12.08) | 0/40 | -7.85 (-10.03, -3.14) | -14.65 (-15.92, -12.08) |
| RLS + CUSUM | ar1 | S8 stationary | -2.60 (-4.48, 0.41) | -6.39 (-7.48, -3.56) | 2/40 | -2.88 (-4.51, 0.60) | -6.50 (-7.79, -3.99) |
| RLS + CUSUM | harmonic | S8 stationary | -7.83 (-10.01, -3.06) | -14.62 (-15.92, -12.02) | 0/40 | -7.83 (-10.01, -3.06) | -14.62 (-15.92, -12.02) |
| MFBLMS | ar1 | S8 stationary | -1.65 (-2.20, -0.81) | -6.23 (-7.50, -3.58) | 2/40 | -1.82 (-2.21, -0.97) | -6.37 (-7.82, -3.93) |
| MFBLMS | harmonic | S8 stationary | -3.58 (-4.15, -2.80) | -13.22 (-14.40, -11.33) | 0/40 | -3.58 (-4.15, -2.80) | -13.22 (-14.40, -11.33) |
| MFBLMS + det | ar1 | S8 stationary | -1.65 (-2.20, -0.81) | -6.23 (-7.50, -3.58) | 2/40 | -1.82 (-2.21, -0.97) | -6.37 (-7.82, -3.93) |
| MFBLMS + det | harmonic | S8 stationary | -3.58 (-4.15, -2.80) | -13.22 (-14.40, -11.33) | 0/40 | -3.58 (-4.15, -2.80) | -13.22 (-14.40, -11.33) |
| switching FD-FxNLMS [6] | ar1 | S8 stationary | -3.39 (-4.36, -1.40) | -5.69 (-6.98, -3.61) | 1/40 | -3.44 (-4.42, -1.81) | -5.76 (-7.04, -4.00) |
| switching FD-FxNLMS [6] | harmonic | S8 stationary | -6.27 (-7.23, -4.90) | -13.36 (-14.36, -10.06) | 0/40 | -6.27 (-7.23, -4.90) | -13.36 (-14.36, -10.06) |
| switching FD-FxNLMS + det | ar1 | S8 stationary | -3.47 (-4.36, -1.32) | -6.58 (-7.63, -3.77) | 0/40 | -3.47 (-4.36, -1.32) | -6.58 (-7.63, -3.77) |
| switching FD-FxNLMS + det | harmonic | S8 stationary | -6.28 (-7.24, -4.95) | -13.89 (-15.18, -11.52) | 0/40 | -6.28 (-7.24, -4.95) | -13.89 (-15.18, -11.52) |
| RLS + det (cond.) | ar1 | S8 stationary | -2.88 (-4.48, 0.78) | -6.66 (-7.62, -3.79) | 0/40 | -2.88 (-4.48, 0.78) | -6.66 (-7.62, -3.79) |
| RLS + det (cond.) | harmonic | S8 stationary | -7.83 (-10.01, -3.06) | -14.65 (-15.92, -12.08) | 0/40 | -7.83 (-10.01, -3.06) | -14.65 (-15.92, -12.08) |
| RLS + det + growth | ar1 | S8 stationary | -2.88 (-4.48, 0.78) | -6.66 (-7.62, -3.79) | 0/40 | -2.88 (-4.48, 0.78) | -6.66 (-7.62, -3.79) |
| RLS + det + growth | harmonic | S8 stationary | -7.83 (-10.01, -3.06) | -14.65 (-15.92, -12.08) | 0/40 | -7.83 (-10.01, -3.06) | -14.65 (-15.92, -12.08) |
| RLS + det + growth (from start) | ar1 | S8 stationary | -2.01 (-3.13, 0.46) | -6.66 (-7.62, -3.79) | 0/40 | -2.01 (-3.13, 0.46) | -6.66 (-7.62, -3.79) |
| RLS + det + growth (from start) | harmonic | S8 stationary | -6.54 (-7.87, -4.05) | -14.65 (-15.92, -12.08) | 0/40 | -6.54 (-7.87, -4.05) | -14.65 (-15.92, -12.08) |
| RLS (extended grid) | ar1 | S8 stationary | -2.38 (-4.17, 0.76) | -5.71 (-6.74, -3.07) | 2/40 | -2.62 (-4.19, 0.76) | -5.88 (-6.83, -3.93) |
| RLS (extended grid) | harmonic | S8 stationary | -7.64 (-9.75, -2.60) | -13.85 (-15.12, -10.99) | 0/40 | -7.64 (-9.75, -2.60) | -13.85 (-15.12, -10.99) |
| VFF-RLS (extended grid) | ar1 | S8 stationary | 0.36 (-1.60, 4.39) | -6.09 (-7.10, -3.34) | 2/40 | 0.40 (-1.90, 4.56) | -6.25 (-7.27, -4.23) |
| VFF-RLS (extended grid) | harmonic | S8 stationary | -4.06 (-7.72, 2.90) | -14.24 (-15.44, -11.46) | 0/40 | -4.06 (-7.72, 2.90) | -14.24 (-15.44, -11.46) |
| RLS + CUSUM (extended grid) | ar1 | S8 stationary | -2.60 (-4.48, 0.41) | -6.45 (-7.48, -3.56) | 2/40 | -2.88 (-4.51, 0.60) | -6.54 (-7.78, -3.89) |
| RLS + CUSUM (extended grid) | harmonic | S8 stationary | -7.83 (-10.01, -3.06) | -14.61 (-15.83, -11.80) | 0/40 | -7.83 (-10.01, -3.06) | -14.61 (-15.83, -11.80) |
| FD-FxNLMS (extended grid) | ar1 | S8 stationary | -3.43 (-4.36, -1.22) | -5.30 (-6.38, -2.15) | 2/40 | -3.44 (-4.50, -2.13) | -5.34 (-6.48, -3.87) |
| FD-FxNLMS (extended grid) | harmonic | S8 stationary | -6.04 (-7.22, -3.90) | -10.94 (-13.08, -6.70) | 4/40 | -6.58 (-7.33, -4.81) | -11.06 (-13.15, -7.64) |
| FDKF (extended grid) | ar1 | S8 stationary | -2.35 (-2.91, -0.53) | -5.35 (-6.43, -2.34) | 4/40 | -2.56 (-3.05, -1.46) | -5.52 (-6.64, -4.01) |
| FDKF (extended grid) | harmonic | S8 stationary | -5.29 (-6.22, -3.82) | -12.15 (-13.54, -9.10) | 0/40 | -5.29 (-6.22, -3.82) | -12.15 (-13.54, -9.10) |
| FD-FxNLMS + det (extended grid) | ar1 | S8 stationary | -3.65 (-4.39, -1.85) | -5.42 (-6.58, -2.09) | 2/40 | -3.83 (-4.42, -2.44) | -5.61 (-6.60, -3.76) |
| FD-FxNLMS + det (extended grid) | harmonic | S8 stationary | -5.87 (-6.75, -4.40) | -12.70 (-13.75, -8.53) | 0/40 | -5.87 (-6.75, -4.40) | -12.70 (-13.75, -8.53) |
| E-PCG bank | ar1 | S8 stationary | -2.88 (-4.50, 0.45) | -6.28 (-7.23, -3.79) | 0/40 | -2.88 (-4.50, 0.45) | -6.28 (-7.23, -3.79) |
| E-PCG bank | harmonic | S8 stationary | -7.34 (-9.11, -3.59) | -14.69 (-15.83, -12.09) | 0/40 | -7.34 (-9.11, -3.59) | -14.69 (-15.83, -12.09) |

## F3: E-PCG vs baselines (Holm over 104)
| baseline | noise | cell | med dA1 | HL dA1 [95% CI] | p_Holm A1 | med dA2 | HL dA2 [95% CI] | p_Holm A2 | label | fails prop/base |
|---|---|---|---|---|---|---|---|---|---|---|
| FD-FxNLMS | ar1 | S8 stationary | +0.52 | +0.82 [+0.29, +1.37] | 0.0424 | -0.96 | -0.95 [-1.13, -0.78] | 1.89e-10 | win | 0/2 |
| FD-FxNLMS | harmonic | S8 stationary | -1.29 | -0.40 [-1.38, +0.57] | 1 | -2.82 | -2.94 [-3.50, -2.47] | 1.89e-10 | win | 0/1 |
| leaky FD-FxNLMS | ar1 | S8 stationary | +0.36 | +0.57 [+0.07, +1.08] | 0.604 | -0.94 | -1.00 [-1.17, -0.84] | 1.89e-10 | win | 0/2 |
| leaky FD-FxNLMS | harmonic | S8 stationary | -1.53 | -0.70 [-1.76, +0.26] | 1 | -3.54 | -4.09 [-4.91, -3.27] | 1.89e-10 | win | 0/4 |
| convex FD-FxNLMS | ar1 | S8 stationary | +1.00 | +1.12 [+0.57, +1.68] | 0.00353 | -0.79 | -0.79 [-0.99, -0.64] | 1.89e-10 | win | 0/2 |
| convex FD-FxNLMS | harmonic | S8 stationary | -0.44 | +0.36 [-0.47, +1.19] | 1 | -1.87 | -2.06 [-2.40, -1.79] | 1.89e-10 | win | 0/0 |
| FDKF | ar1 | S8 stationary | -3.31 | -3.11 [-3.96, -2.25] | 0.00022 | -0.92 | -1.01 [-1.25, -0.82] | 1.89e-10 | win | 0/4 |
| FDKF | harmonic | S8 stationary | -5.65 | -5.12 [-6.19, -3.81] | 2.11e-07 | -2.13 | -2.23 [-2.44, -2.05] | 1.89e-10 | win | 0/0 |
| RLS | ar1 | S8 stationary | -0.39 | -0.29 [-0.57, +0.12] | 1 | -0.26 | -0.27 [-0.32, -0.22] | 5.73e-10 | - | 0/2 |
| RLS | harmonic | S8 stationary | +0.49 | +0.48 [+0.08, +0.90] | 0.75 | -0.35 | -0.36 [-0.40, -0.33] | 1.89e-10 | - | 0/0 |
| VFF-RLS | ar1 | S8 stationary | -3.28 | -3.31 [-3.86, -2.79] | 1.72e-06 | -0.22 | -0.23 [-0.27, -0.19] | 3.48e-09 | win | 0/2 |
| VFF-RLS | harmonic | S8 stationary | -2.83 | -3.17 [-4.00, -2.39] | 2.68e-09 | -0.24 | -0.25 [-0.30, -0.22] | 1.89e-10 | win | 0/0 |
| FD-FxNLMS + det | ar1 | S8 stationary | +0.92 | +0.96 [+0.40, +1.55] | 0.0347 | -0.82 | -0.86 [-1.06, -0.69] | 1.89e-10 | win | 0/2 |
| FD-FxNLMS + det | harmonic | S8 stationary | -1.68 | -0.79 [-1.73, +0.04] | 1 | -1.89 | -1.99 [-2.34, -1.75] | 1.89e-10 | win | 0/0 |
| RLS + det | ar1 | S8 stationary | -0.15 | -0.12 [-0.40, +0.19] | 1 | +0.21 | +0.21 [+0.18, +0.24] | 1.89e-10 | - | 0/0 |
| RLS + det | harmonic | S8 stationary | +0.60 | +0.61 [+0.21, +1.03] | 0.198 | +0.19 | +0.18 [+0.17, +0.20] | 1.89e-10 | - | 0/0 |
| FD-FxNLMS + restart | ar1 | S8 stationary | +0.52 | +0.82 [+0.29, +1.37] | 0.0424 | -0.96 | -0.95 [-1.13, -0.78] | 1.89e-10 | win | 0/2 |
| FD-FxNLMS + restart | harmonic | S8 stationary | -1.29 | -0.40 [-1.38, +0.57] | 1 | -2.82 | -2.94 [-3.50, -2.47] | 1.89e-10 | win | 0/1 |
| SFTF + det | ar1 | S8 stationary | -0.12 | -0.09 [-0.36, +0.22] | 1 | +0.21 | +0.21 [+0.18, +0.24] | 1.89e-10 | - | 0/0 |
| SFTF + det | harmonic | S8 stationary | +0.63 | +0.64 [+0.23, +1.05] | 0.14 | +0.19 | +0.18 [+0.17, +0.20] | 1.89e-10 | - | 0/0 |
| SFTF-H + det | ar1 | S8 stationary | -0.12 | -0.09 [-0.36, +0.22] | 1 | +0.21 | +0.21 [+0.18, +0.24] | 1.89e-10 | - | 0/0 |
| SFTF-H + det | harmonic | S8 stationary | +0.63 | +0.64 [+0.23, +1.05] | 0.14 | +0.19 | +0.18 [+0.17, +0.20] | 1.89e-10 | - | 0/0 |
| CFTF + det | ar1 | S8 stationary | -0.12 | -0.09 [-0.36, +0.22] | 1 | +0.21 | +0.21 [+0.18, +0.24] | 1.89e-10 | - | 0/0 |
| CFTF + det | harmonic | S8 stationary | +0.63 | +0.64 [+0.23, +1.05] | 0.14 | +0.19 | +0.18 [+0.17, +0.20] | 1.89e-10 | - | 0/0 |
| RLS + CUSUM | ar1 | S8 stationary | -0.12 | -0.11 [-0.41, +0.21] | 1 | +0.15 | +0.12 [+0.03, +0.17] | 0.23 | - | 0/2 |
| RLS + CUSUM | harmonic | S8 stationary | +0.60 | +0.61 [+0.21, +1.03] | 0.198 | +0.16 | +0.16 [+0.14, +0.18] | 0.0001 | - | 0/0 |
| MFBLMS | ar1 | S8 stationary | -1.13 | -0.87 [-1.85, +0.10] | 1 | +0.08 | +0.09 [+0.04, +0.13] | 0.0911 | - | 0/2 |
| MFBLMS | harmonic | S8 stationary | -3.85 | -3.20 [-4.30, -1.66] | 0.00101 | -1.05 | -1.03 [-1.21, -0.88] | 1.89e-10 | win | 0/0 |
| MFBLMS + det | ar1 | S8 stationary | -1.13 | -0.87 [-1.85, +0.10] | 1 | +0.08 | +0.09 [+0.04, +0.13] | 0.0911 | - | 0/2 |
| MFBLMS + det | harmonic | S8 stationary | -3.85 | -3.20 [-4.30, -1.66] | 0.00101 | -1.05 | -1.03 [-1.21, -0.88] | 1.89e-10 | win | 0/0 |
| switching FD-FxNLMS [6] | ar1 | S8 stationary | +0.52 | +0.81 [+0.30, +1.36] | 0.0803 | -0.29 | -0.34 [-0.52, -0.21] | 0.00518 | - | 0/1 |
| switching FD-FxNLMS [6] | harmonic | S8 stationary | -1.15 | -0.26 [-1.18, +0.68] | 1 | -1.12 | -1.13 [-1.28, -0.98] | 1.89e-10 | win | 0/0 |
| switching FD-FxNLMS + det | ar1 | S8 stationary | +0.52 | +0.79 [+0.29, +1.33] | 0.0671 | +0.19 | +0.20 [+0.17, +0.22] | 5.73e-10 | - | 0/0 |
| switching FD-FxNLMS + det | harmonic | S8 stationary | -1.11 | -0.24 [-1.16, +0.73] | 1 | -0.45 | -0.48 [-0.54, -0.41] | 1.89e-10 | - | 0/0 |
| RLS + det (cond.) | ar1 | S8 stationary | -0.15 | -0.12 [-0.40, +0.19] | 1 | +0.21 | +0.21 [+0.18, +0.24] | 1.89e-10 | - | 0/0 |
| RLS + det (cond.) | harmonic | S8 stationary | +0.60 | +0.61 [+0.21, +1.03] | 0.198 | +0.19 | +0.18 [+0.17, +0.20] | 1.89e-10 | - | 0/0 |
| RLS + det + growth | ar1 | S8 stationary | -0.15 | -0.12 [-0.40, +0.19] | 1 | +0.21 | +0.21 [+0.18, +0.24] | 1.89e-10 | - | 0/0 |
| RLS + det + growth | harmonic | S8 stationary | +0.60 | +0.61 [+0.21, +1.03] | 0.198 | +0.19 | +0.18 [+0.17, +0.20] | 1.89e-10 | - | 0/0 |
| RLS + det + growth (from start) | ar1 | S8 stationary | -0.85 | -0.83 [-1.17, -0.43] | 0.011 | +0.21 | +0.21 [+0.18, +0.24] | 1.89e-10 | - | 0/0 |
| RLS + det + growth (from start) | harmonic | S8 stationary | -0.67 | -0.53 [-1.01, +0.17] | 1 | +0.19 | +0.19 [+0.17, +0.20] | 1.89e-10 | - | 0/0 |
| RLS (extended grid) | ar1 | S8 stationary | -0.53 | -0.43 [-0.72, -0.01] | 1 | -0.52 | -0.53 [-0.60, -0.48] | 1.89e-10 | win | 0/2 |
| RLS (extended grid) | harmonic | S8 stationary | +0.40 | +0.40 [-0.01, +0.81] | 1 | -0.63 | -0.65 [-0.72, -0.61] | 1.89e-10 | win | 0/0 |
| VFF-RLS (extended grid) | ar1 | S8 stationary | -3.31 | -3.34 [-3.88, -2.82] | 1.72e-06 | -0.24 | -0.24 [-0.29, -0.20] | 1.11e-09 | win | 0/2 |
| VFF-RLS (extended grid) | harmonic | S8 stationary | -2.87 | -3.21 [-4.02, -2.41] | 2.07e-09 | -0.29 | -0.30 [-0.34, -0.27] | 1.89e-10 | win | 0/0 |
| RLS + CUSUM (extended grid) | ar1 | S8 stationary | -0.12 | -0.11 [-0.41, +0.21] | 1 | +0.16 | +0.10 [-0.00, +0.17] | 1 | - | 0/2 |
| RLS + CUSUM (extended grid) | harmonic | S8 stationary | +0.60 | +0.61 [+0.21, +1.03] | 0.198 | +0.14 | +0.15 [+0.13, +0.17] | 0.00114 | - | 0/0 |
| FD-FxNLMS (extended grid) | ar1 | S8 stationary | +0.43 | +0.74 [+0.21, +1.25] | 0.17 | -1.00 | -0.98 [-1.17, -0.81] | 1.89e-10 | win | 0/2 |
| FD-FxNLMS (extended grid) | harmonic | S8 stationary | -1.52 | -0.60 [-1.66, +0.41] | 1 | -2.88 | -3.33 [-4.13, -2.70] | 1.89e-10 | win | 0/4 |
| FDKF (extended grid) | ar1 | S8 stationary | -0.44 | -0.37 [-0.96, +0.27] | 1 | -0.93 | -1.00 [-1.24, -0.82] | 1.89e-10 | win | 0/4 |
| FDKF (extended grid) | harmonic | S8 stationary | -2.00 | -1.45 [-2.49, -0.35] | 0.298 | -2.10 | -2.15 [-2.38, -1.99] | 1.89e-10 | win | 0/0 |
| FD-FxNLMS + det (extended grid) | ar1 | S8 stationary | +0.94 | +0.92 [+0.36, +1.57] | 0.0529 | -0.82 | -0.86 [-1.06, -0.69] | 1.89e-10 | win | 0/2 |
| FD-FxNLMS + det (extended grid) | harmonic | S8 stationary | -1.38 | -0.83 [-1.82, -0.01] | 1 | -1.89 | -1.99 [-2.33, -1.74] | 1.89e-10 | win | 0/0 |

Counts: win 27, loss 0, mixed 0, none 25 (of 52)

## F3: E-PCG bank vs baselines (Holm over 104)
| baseline | noise | cell | med dA1 | HL dA1 [95% CI] | p_Holm A1 | med dA2 | HL dA2 [95% CI] | p_Holm A2 | label | fails prop/base |
|---|---|---|---|---|---|---|---|---|---|---|
| FD-FxNLMS | ar1 | S8 stationary | +0.52 | +0.83 [+0.31, +1.38] | 0.063 | -0.86 | -0.95 [-1.17, -0.78] | 4.64e-10 | win | 0/2 |
| FD-FxNLMS | harmonic | S8 stationary | -1.16 | -0.34 [-1.33, +0.62] | 1 | -3.04 | -3.10 [-3.64, -2.66] | 1.89e-10 | win | 0/1 |
| leaky FD-FxNLMS | ar1 | S8 stationary | +0.36 | +0.58 [+0.09, +1.10] | 0.85 | -1.00 | -1.02 [-1.19, -0.85] | 4.64e-10 | win | 0/2 |
| leaky FD-FxNLMS | harmonic | S8 stationary | -1.29 | -0.66 [-1.69, +0.32] | 1 | -3.78 | -4.27 [-5.12, -3.47] | 1.89e-10 | win | 0/4 |
| convex FD-FxNLMS | ar1 | S8 stationary | +1.11 | +1.12 [+0.57, +1.68] | 0.00417 | -0.72 | -0.81 [-1.02, -0.63] | 2.01e-09 | mixed | 0/2 |
| convex FD-FxNLMS | harmonic | S8 stationary | -0.31 | +0.43 [-0.42, +1.24] | 1 | -2.10 | -2.22 [-2.57, -1.94] | 1.89e-10 | win | 0/0 |
| FDKF | ar1 | S8 stationary | -3.31 | -3.11 [-3.96, -2.24] | 0.000262 | -0.90 | -1.01 [-1.25, -0.81] | 3.2e-10 | win | 0/4 |
| FDKF | harmonic | S8 stationary | -5.61 | -5.06 [-6.14, -3.75] | 4.38e-07 | -2.37 | -2.40 [-2.60, -2.23] | 1.89e-10 | win | 0/0 |
| RLS | ar1 | S8 stationary | -0.34 | -0.26 [-0.56, +0.13] | 1 | -0.37 | -0.30 [-0.40, -0.20] | 0.000121 | - | 0/2 |
| RLS | harmonic | S8 stationary | +0.54 | +0.54 [+0.15, +0.96] | 0.595 | -0.52 | -0.53 [-0.58, -0.50] | 1.89e-10 | win | 0/0 |
| VFF-RLS | ar1 | S8 stationary | -3.25 | -3.31 [-3.87, -2.79] | 2.27e-06 | -0.32 | -0.25 [-0.35, -0.16] | 0.00128 | win | 0/2 |
| VFF-RLS | harmonic | S8 stationary | -2.80 | -3.08 [-3.94, -2.33] | 4.56e-09 | -0.42 | -0.43 [-0.47, -0.39] | 3.2e-10 | win | 0/0 |
| FD-FxNLMS + det | ar1 | S8 stationary | +0.92 | +0.95 [+0.41, +1.56] | 0.0439 | -0.79 | -0.86 [-1.10, -0.66] | 7.37e-10 | win | 0/2 |
| FD-FxNLMS + det | harmonic | S8 stationary | -1.52 | -0.71 [-1.69, +0.12] | 1 | -2.04 | -2.14 [-2.50, -1.90] | 1.89e-10 | win | 0/0 |
| RLS + det | ar1 | S8 stationary | -0.14 | -0.11 [-0.38, +0.22] | 1 | +0.15 | +0.17 [+0.10, +0.28] | 7.6e-05 | - | 0/0 |
| RLS + det | harmonic | S8 stationary | +0.66 | +0.66 [+0.28, +1.10] | 0.14 | +0.00 | +0.01 [-0.01, +0.04] | 1 | - | 0/0 |
| FD-FxNLMS + restart | ar1 | S8 stationary | +0.52 | +0.83 [+0.31, +1.38] | 0.063 | -0.86 | -0.95 [-1.17, -0.78] | 4.64e-10 | win | 0/2 |
| FD-FxNLMS + restart | harmonic | S8 stationary | -1.16 | -0.34 [-1.33, +0.62] | 1 | -3.04 | -3.10 [-3.64, -2.66] | 1.89e-10 | win | 0/1 |
| SFTF + det | ar1 | S8 stationary | -0.11 | -0.08 [-0.35, +0.25] | 1 | +0.15 | +0.17 [+0.10, +0.28] | 7.6e-05 | - | 0/0 |
| SFTF + det | harmonic | S8 stationary | +0.67 | +0.68 [+0.29, +1.12] | 0.103 | +0.00 | +0.01 [-0.01, +0.04] | 1 | - | 0/0 |
| SFTF-H + det | ar1 | S8 stationary | -0.11 | -0.08 [-0.35, +0.25] | 1 | +0.15 | +0.17 [+0.10, +0.28] | 7.6e-05 | - | 0/0 |
| SFTF-H + det | harmonic | S8 stationary | +0.67 | +0.68 [+0.29, +1.12] | 0.103 | +0.00 | +0.01 [-0.01, +0.04] | 1 | - | 0/0 |
| CFTF + det | ar1 | S8 stationary | -0.11 | -0.08 [-0.35, +0.25] | 1 | +0.15 | +0.17 [+0.10, +0.28] | 7.6e-05 | - | 0/0 |
| CFTF + det | harmonic | S8 stationary | +0.67 | +0.68 [+0.29, +1.12] | 0.103 | +0.00 | +0.01 [-0.01, +0.04] | 1 | - | 0/0 |
| RLS + CUSUM | ar1 | S8 stationary | -0.08 | -0.09 [-0.41, +0.23] | 1 | +0.04 | +0.04 [-0.02, +0.10] | 1 | - | 0/2 |
| RLS + CUSUM | harmonic | S8 stationary | +0.66 | +0.66 [+0.28, +1.10] | 0.14 | -0.02 | -0.02 [-0.05, +0.01] | 1 | - | 0/0 |
| MFBLMS | ar1 | S8 stationary | -1.13 | -0.84 [-1.84, +0.10] | 1 | -0.01 | +0.04 [-0.03, +0.14] | 1 | - | 0/2 |
| MFBLMS | harmonic | S8 stationary | -3.76 | -3.10 [-4.26, -1.62] | 0.00184 | -1.23 | -1.18 [-1.36, -1.04] | 1.89e-10 | win | 0/0 |
| MFBLMS + det | ar1 | S8 stationary | -1.13 | -0.84 [-1.84, +0.10] | 1 | -0.01 | +0.04 [-0.03, +0.14] | 1 | - | 0/2 |
| MFBLMS + det | harmonic | S8 stationary | -3.76 | -3.10 [-4.26, -1.62] | 0.00184 | -1.23 | -1.18 [-1.36, -1.04] | 1.89e-10 | win | 0/0 |
| switching FD-FxNLMS [6] | ar1 | S8 stationary | +0.52 | +0.82 [+0.32, +1.37] | 0.107 | -0.36 | -0.37 [-0.53, -0.20] | 0.00503 | - | 0/1 |
| switching FD-FxNLMS [6] | harmonic | S8 stationary | -0.96 | -0.19 [-1.11, +0.75] | 1 | -1.20 | -1.29 [-1.44, -1.13] | 1.89e-10 | win | 0/0 |
| switching FD-FxNLMS + det | ar1 | S8 stationary | +0.52 | +0.80 [+0.30, +1.34] | 0.0903 | +0.14 | +0.16 [+0.08, +0.26] | 0.000223 | - | 0/0 |
| switching FD-FxNLMS + det | harmonic | S8 stationary | -0.97 | -0.16 [-1.10, +0.79] | 1 | -0.64 | -0.64 [-0.72, -0.57] | 1.89e-10 | win | 0/0 |
| RLS + det (cond.) | ar1 | S8 stationary | -0.14 | -0.11 [-0.38, +0.22] | 1 | +0.15 | +0.17 [+0.10, +0.28] | 7.6e-05 | - | 0/0 |
| RLS + det (cond.) | harmonic | S8 stationary | +0.66 | +0.66 [+0.28, +1.10] | 0.14 | +0.00 | +0.01 [-0.01, +0.04] | 1 | - | 0/0 |
| RLS + det + growth | ar1 | S8 stationary | -0.14 | -0.11 [-0.38, +0.22] | 1 | +0.15 | +0.17 [+0.10, +0.28] | 7.6e-05 | - | 0/0 |
| RLS + det + growth | harmonic | S8 stationary | +0.66 | +0.66 [+0.28, +1.10] | 0.14 | +0.00 | +0.01 [-0.01, +0.04] | 1 | - | 0/0 |
| RLS + det + growth (from start) | ar1 | S8 stationary | -0.80 | -0.83 [-1.17, -0.42] | 0.0123 | +0.15 | +0.18 [+0.10, +0.28] | 7.6e-05 | - | 0/0 |
| RLS + det + growth (from start) | harmonic | S8 stationary | -0.66 | -0.46 [-0.95, +0.24] | 1 | -0.00 | +0.01 [-0.01, +0.04] | 1 | - | 0/0 |
| RLS (extended grid) | ar1 | S8 stationary | -0.49 | -0.41 [-0.70, -0.02] | 1 | -0.60 | -0.56 [-0.66, -0.46] | 2.7e-09 | win | 0/2 |
| RLS (extended grid) | harmonic | S8 stationary | +0.45 | +0.46 [+0.04, +0.88] | 1 | -0.81 | -0.83 [-0.88, -0.78] | 1.89e-10 | win | 0/0 |
| VFF-RLS (extended grid) | ar1 | S8 stationary | -3.28 | -3.34 [-3.89, -2.81] | 2.27e-06 | -0.35 | -0.27 [-0.37, -0.18] | 0.000428 | win | 0/2 |
| VFF-RLS (extended grid) | harmonic | S8 stationary | -2.84 | -3.10 [-3.97, -2.36] | 3.5e-09 | -0.46 | -0.48 [-0.52, -0.44] | 1.89e-10 | win | 0/0 |
| RLS + CUSUM (extended grid) | ar1 | S8 stationary | -0.08 | -0.09 [-0.41, +0.23] | 1 | +0.02 | +0.03 [-0.01, +0.09] | 1 | - | 0/2 |
| RLS + CUSUM (extended grid) | harmonic | S8 stationary | +0.66 | +0.66 [+0.28, +1.10] | 0.14 | -0.03 | -0.03 [-0.07, +0.01] | 1 | - | 0/0 |
| FD-FxNLMS (extended grid) | ar1 | S8 stationary | +0.43 | +0.75 [+0.24, +1.26] | 0.182 | -0.90 | -0.98 [-1.20, -0.81] | 4.64e-10 | win | 0/2 |
| FD-FxNLMS (extended grid) | harmonic | S8 stationary | -1.29 | -0.54 [-1.63, +0.44] | 1 | -3.13 | -3.49 [-4.33, -2.87] | 1.89e-10 | win | 0/4 |
| FDKF (extended grid) | ar1 | S8 stationary | -0.44 | -0.36 [-0.97, +0.28] | 1 | -0.88 | -0.99 [-1.25, -0.80] | 3.2e-10 | win | 0/4 |
| FDKF (extended grid) | harmonic | S8 stationary | -1.90 | -1.40 [-2.47, -0.25] | 0.564 | -2.31 | -2.34 [-2.54, -2.18] | 1.89e-10 | win | 0/0 |
| FD-FxNLMS + det (extended grid) | ar1 | S8 stationary | +0.94 | +0.94 [+0.38, +1.57] | 0.063 | -0.79 | -0.86 [-1.10, -0.66] | 7.37e-10 | win | 0/2 |
| FD-FxNLMS + det (extended grid) | harmonic | S8 stationary | -1.38 | -0.75 [-1.80, +0.13] | 1 | -2.02 | -2.13 [-2.48, -1.89] | 1.89e-10 | win | 0/0 |

Counts: win 28, loss 0, mixed 1, none 23 (of 52)

## E-PCG bank - E-PCG (main) (Holm over 4)
| noise | cell | key | median d | HL [95% CI] | p_Holm |
|---|---|---|---|---|---|
| ar1 | S8 stationary | A1 | +0.00 | +0.00 [+0.00, +0.01] | 0.0537 |
| ar1 | S8 stationary | A2 | -0.09 | -0.06 [-0.13, +0.07] | 0.34 |
| harmonic | S8 stationary | A1 | +0.01 | +0.02 [+0.01, +0.04] | 4.64e-05 |
| harmonic | S8 stationary | A2 | -0.18 | -0.18 [-0.21, -0.13] | 2.91e-07 |

## Like-for-like with final_eval_meas_s_8a (seeds 480-519; 12 common baselines; Holm over 48)

### E-PCG: agreement 19/24
| baseline | noise | cell | 480-519 label | holdout label | 480-519 dA1 / p / dA2 / p | holdout dA1 / p / dA2 / p | fails 480-519 | fails holdout |
|---|---|---|---|---|---|---|---|---|
| convex FD-FxNLMS | ar1 | S8 stationary | mixed | win | +1.108 / 6.43e-05 / -1.008 / 8.73e-11 | +0.999 / 0.00144 / -0.790 / 8.73e-11 | 0/4 | 0/2 |
| RLS + det | harmonic | S8 stationary | loss | - | +1.138 / 0.000593 / +0.180 / 8.73e-11 | +0.605 / 0.0758 / +0.194 / 8.73e-11 | 0/0 | 0/0 |
| SFTF + det | harmonic | S8 stationary | loss | - | +1.156 / 0.000379 / +0.180 / 8.73e-11 | +0.626 / 0.059 / +0.194 / 8.73e-11 | 0/0 | 0/0 |
| SFTF-H + det | harmonic | S8 stationary | loss | - | +1.156 / 0.000379 / +0.180 / 8.73e-11 | +0.626 / 0.059 / +0.194 / 8.73e-11 | 0/0 | 0/0 |
| CFTF + det | harmonic | S8 stationary | loss | - | +1.156 / 0.000379 / +0.180 / 8.73e-11 | +0.626 / 0.059 / +0.194 / 8.73e-11 | 0/0 | 0/0 |

### E-PCG bank: agreement 19/24
| baseline | noise | cell | 480-519 label | holdout label | 480-519 dA1 / p / dA2 / p | holdout dA1 / p / dA2 / p | fails 480-519 | fails holdout |
|---|---|---|---|---|---|---|---|---|
| RLS | harmonic | S8 stationary | mixed | win | +1.091 / 0.00345 / -0.562 / 8.73e-11 | +0.540 / 0.244 / -0.520 / 8.73e-11 | 0/0 | 0/0 |
| RLS + det | harmonic | S8 stationary | loss | - | +1.180 / 0.000547 / -0.023 / 0.25 | +0.659 / 0.0519 / +0.001 / 1 | 0/0 | 0/0 |
| SFTF + det | harmonic | S8 stationary | loss | - | +1.200 / 0.000302 / -0.023 / 0.25 | +0.670 / 0.0412 / +0.001 / 1 | 0/0 | 0/0 |
| SFTF-H + det | harmonic | S8 stationary | loss | - | +1.200 / 0.000302 / -0.023 / 0.25 | +0.670 / 0.0412 / +0.001 / 1 | 0/0 | 0/0 |
| CFTF + det | harmonic | S8 stationary | loss | - | +1.200 / 0.000302 / -0.023 / 0.25 | +0.670 / 0.0412 / +0.001 / 1 | 0/0 | 0/0 |

## Distance to the Wiener lower bound (Rule 11 Sec. 5.3; descriptive)
Per seed: A2 (last 1 s NR) minus the total-NR Wiener bound of the same seed and noise, successful runs only;
median (Q1, Q3) in dB (positive = above the bound).

| method | noise | A2 - bound median (Q1, Q3) | successful runs |
|---|---|---|---|
| E-PCG | ar1 | +0.32 (+0.20, +0.49) | 40/40 |
| E-PCG | harmonic | +0.30 (+0.15, +0.45) | 40/40 |
| FD-FxNLMS | ar1 | +1.22 (+0.80, +1.74) | 38/40 |
| FD-FxNLMS | harmonic | +3.14 (+2.11, +3.99) | 39/40 |
| leaky FD-FxNLMS | ar1 | +1.23 (+0.89, +1.77) | 38/40 |
| leaky FD-FxNLMS | harmonic | +3.69 (+2.80, +5.15) | 36/40 |
| convex FD-FxNLMS | ar1 | +1.03 (+0.67, +1.59) | 38/40 |
| convex FD-FxNLMS | harmonic | +2.19 (+1.76, +2.97) | 40/40 |
| FDKF | ar1 | +1.30 (+0.91, +1.51) | 36/40 |
| FDKF | harmonic | +2.48 (+2.25, +3.06) | 40/40 |
| RLS | ar1 | +0.61 (+0.29, +0.80) | 38/40 |
| RLS | harmonic | +0.68 (+0.43, +0.83) | 40/40 |
| VFF-RLS | ar1 | +0.56 (+0.24, +0.76) | 38/40 |
| VFF-RLS | harmonic | +0.60 (+0.33, +0.72) | 40/40 |
| FD-FxNLMS + det | ar1 | +1.10 (+0.69, +1.63) | 38/40 |
| FD-FxNLMS + det | harmonic | +2.19 (+1.79, +2.89) | 40/40 |
| RLS + det | ar1 | +0.10 (-0.11, +0.25) | 40/40 |
| RLS + det | harmonic | +0.11 (-0.06, +0.26) | 40/40 |
| FD-FxNLMS + restart | ar1 | +1.22 (+0.80, +1.74) | 38/40 |
| FD-FxNLMS + restart | harmonic | +3.14 (+2.11, +3.99) | 39/40 |
| SFTF + det | ar1 | +0.10 (-0.11, +0.25) | 40/40 |
| SFTF + det | harmonic | +0.11 (-0.06, +0.26) | 40/40 |
| SFTF-H + det | ar1 | +0.10 (-0.11, +0.25) | 40/40 |
| SFTF-H + det | harmonic | +0.11 (-0.06, +0.26) | 40/40 |
| CFTF + det | ar1 | +0.10 (-0.11, +0.25) | 40/40 |
| CFTF + det | harmonic | +0.11 (-0.06, +0.26) | 40/40 |
| RLS + CUSUM | ar1 | +0.15 (+0.07, +0.26) | 38/40 |
| RLS + CUSUM | harmonic | +0.12 (-0.03, +0.29) | 40/40 |
| MFBLMS | ar1 | +0.20 (+0.04, +0.38) | 38/40 |
| MFBLMS | harmonic | +1.37 (+0.91, +1.71) | 40/40 |
| MFBLMS + det | ar1 | +0.20 (+0.04, +0.38) | 38/40 |
| MFBLMS + det | harmonic | +1.37 (+0.91, +1.71) | 40/40 |
| switching FD-FxNLMS [6] | ar1 | +0.48 (+0.28, +1.04) | 39/40 |
| switching FD-FxNLMS [6] | harmonic | +1.44 (+1.06, +1.83) | 40/40 |
| switching FD-FxNLMS + det | ar1 | +0.13 (-0.08, +0.29) | 40/40 |
| switching FD-FxNLMS + det | harmonic | +0.72 (+0.55, +1.00) | 40/40 |
| RLS + det (cond.) | ar1 | +0.10 (-0.11, +0.25) | 40/40 |
| RLS + det (cond.) | harmonic | +0.11 (-0.06, +0.26) | 40/40 |
| RLS + det + growth | ar1 | +0.10 (-0.11, +0.25) | 40/40 |
| RLS + det + growth | harmonic | +0.11 (-0.06, +0.26) | 40/40 |
| RLS + det + growth (from start) | ar1 | +0.10 (-0.11, +0.25) | 40/40 |
| RLS + det + growth (from start) | harmonic | +0.11 (-0.06, +0.26) | 40/40 |
| RLS (extended grid) | ar1 | +0.87 (+0.55, +1.10) | 38/40 |
| RLS (extended grid) | harmonic | +0.97 (+0.70, +1.11) | 40/40 |
| VFF-RLS (extended grid) | ar1 | +0.58 (+0.26, +0.79) | 38/40 |
| VFF-RLS (extended grid) | harmonic | +0.64 (+0.37, +0.76) | 40/40 |
| RLS + CUSUM (extended grid) | ar1 | +0.16 (+0.02, +0.29) | 38/40 |
| RLS + CUSUM (extended grid) | harmonic | +0.14 (-0.02, +0.33) | 40/40 |
| FD-FxNLMS (extended grid) | ar1 | +1.25 (+0.84, +1.77) | 38/40 |
| FD-FxNLMS (extended grid) | harmonic | +3.11 (+2.18, +4.33) | 36/40 |
| FDKF (extended grid) | ar1 | +1.30 (+0.91, +1.50) | 36/40 |
| FDKF (extended grid) | harmonic | +2.36 (+2.22, +2.94) | 40/40 |
| FD-FxNLMS + det (extended grid) | ar1 | +1.10 (+0.69, +1.63) | 38/40 |
| FD-FxNLMS + det (extended grid) | harmonic | +2.19 (+1.77, +2.88) | 40/40 |
| E-PCG bank | ar1 | +0.21 (+0.06, +0.39) | 40/40 |
| E-PCG bank | harmonic | +0.10 (-0.02, +0.27) | 40/40 |

# M-S causal Wiener lower bound (holdout seeds 800-839; same computation as Rule 9-D)

| noise | total NR median (Q1,Q3) | ANC-only NR median (Q1,Q3) | norm >1000 |
|---|---|---|---|
| ar1 | -6.512 (-7.875, -3.947) | -6.669 (-8.098, -4.011) | 0/40 |
| harmonic | -14.661 (-16.055, -12.172) | -16.110 (-18.209, -12.903) | 0/40 |

