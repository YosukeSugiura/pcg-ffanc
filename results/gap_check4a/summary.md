# Revision 10a/10b: Prop. rho check, corrected mapping (S8, M = 512, seeds 300-309)

**Corrective rules written after the Rule 10 results** (REVISION_RULE_10a.md, 10b.md; 10b also after seeing seed-300 values). Rule 10 judgement stands.
ratio = 10 log10(ensemble-mean w-excess / sigma^2 (M/H)(1/b - 1/n_h)) over hop ranges (Rule 10b reference); slope of w-excess + sigma^2 M/(H n_h); A = lag-truncated gain (Prop. rho, E-PCG preconditioner K),
B = standard gradient-constrained FDAF; den_b = (b+1) H S_k with the full-run bin power (non-causal oracle), step 1.

Prediction (ar1): +0.07 dB. harmonic: not verifiable with these recursions (declared before running); eigenvalues only.

## ar1
| recursion | T | 1-8 | 8-32 | 32-100 | 100-312 | 312-625 | 625-1250 | slope 100-312 | diverged seeds | last hop rel. floor |
|---|---|---|---|---|---|---|---|---|---|---|
| A | 5 s | +31.01 | +29.69 | +24.57 | +22.57 |  |  | -2.10 | 0 | -3.35 dB |
| B | 5 s | +8.79 | +6.88 | +5.86 | +9.99 |  |  | -0.37 | 0 | -11.26 dB |
| A | 20 s | +30.00 | +28.56 | +22.92 | +18.65 | +15.74 | +16.25 | -2.03 | 0 | -15.96 dB |
| B | 20 s | +8.60 | +6.42 | +5.11 | +6.97 | +11.04 | +17.43 | -0.40 | 0 | -11.64 dB |

residual-power excess of A relative to exact LS (R-RLS lam 1), T = 5 s, Rule 10 definition (descriptive): 1-8 +17.65 dB, 8-32 +26.93 dB, 32-100 +22.44 dB, 100-312 +16.78 dB
residual-power excess of B relative to exact LS (R-RLS lam 1), T = 5 s, Rule 10 definition (descriptive): 1-8 -2.20 dB, 8-32 +4.17 dB, 32-100 +4.18 dB, 100-312 +4.93 dB

eigenvalues (median over seeds of min / q05 / median / q95 / max): A (K R) [0.93, 0.952, 0.986, 1.027, 9.117], frac<1/2 0.000; B (implemented, real part) [0.924, 0.947, 0.983, 1.016, 1.09], frac<1/2 0.000, max |imag| 2.81e-03
mean-field fixed-point bias of B: -11.7 dB rel. floor (median over seeds)

## harmonic
| recursion | T | 1-8 | 8-32 | 32-100 | 100-312 | 312-625 | 625-1250 | slope 100-312 | diverged seeds | last hop rel. floor |
|---|---|---|---|---|---|---|---|---|---|---|
| A | 5 s | +119.94 | NaN | NaN | NaN |  |  | NaN | 10 | NaN dB |
| B | 5 s | +48.36 | +55.60 | +52.14 | +52.11 |  |  | -1.12 | 0 | +29.03 dB |
| A | 20 s | +119.32 | NaN | NaN | NaN | NaN | NaN | NaN | 10 | NaN dB |
| B | 20 s | +47.60 | +54.44 | +50.71 | +47.46 | +48.46 | +53.01 | -1.21 | 0 | +23.17 dB |

residual-power excess of A relative to exact LS (R-RLS lam 1), T = 5 s, Rule 10 definition (descriptive): 1-8 +110.20 dB, 8-32 NaN dB, 32-100 NaN dB, 100-312 NaN dB
residual-power excess of B relative to exact LS (R-RLS lam 1), T = 5 s, Rule 10 definition (descriptive): 1-8 +37.78 dB, 8-32 +55.58 dB, 32-100 +50.86 dB, 100-312 +46.02 dB

eigenvalues (median over seeds of min / q05 / median / q95 / max): A (K R) [0.081, 0.154, 0.886, 6.946, 43.343], frac<1/2 0.204; B (implemented, real part) [0.077, 0.152, 0.883, 1.596, 1.813], frac<1/2 0.207, max |imag| 2.96e+00
mean-field fixed-point bias of B: -12.2 dB rel. floor (median over seeds)

## Pre-registered judgement (REVISION_RULE_10a section 4)
- primary (ar1, A, T = 5 s, hops 100-312): +22.57 dB vs +0.07 dB -> departure (more than 1 dB)
- secondary (ar1, A, T = 20 s, hops 625-1250): +16.25 dB vs +0.07 dB -> observed value reported as is (1-seed diagnostic before this rule: -0.6 dB)
- harmonic: not judged (declared unverifiable with these recursions); eigenvalues above. B may stay finite but large (not flagged as diverged).
- disclosure (Rule 10b section 2): seed 300 alone gave about +3.1 dB (5 s) and +2.0 dB (20 s) with this reference before this run.

