# Gap check 3: E-PCG vs exact LS on the same 48-hop window (S8, M = 512, tuning seeds 300-309)

excess over the oracle floor (gap_check2 definition); ratios in dB relative to offline window LS

## ar1
| curve | hops 1-8 | hops 8-48 | hops 48-100 | hops 100-200 | hops 200-312 |
|---|---|---|---|---|---|
| offline growing LS | +0.00 dB | +0.00 dB | -1.35 dB | -3.94 dB | -5.46 dB |
| offline window LS | +0.00 dB | +0.00 dB | +0.00 dB | +0.00 dB | +0.00 dB |
| predicted window (sigma^2 tr R G_win^-1) | +5.38 dB | +0.01 dB | -0.31 dB | -0.90 dB | -0.66 dB |
| sim exact LS (RLS lam 1) | -22.01 dB | +0.04 dB | -1.41 dB | -3.93 dB | -5.48 dB |
| sim E-PCG (main) | -26.16 dB | -0.11 dB | -0.21 dB | -0.30 dB | -0.23 dB |

## harmonic
| curve | hops 1-8 | hops 8-48 | hops 48-100 | hops 100-200 | hops 200-312 |
|---|---|---|---|---|---|
| offline growing LS | +0.00 dB | +0.00 dB | -1.58 dB | -4.19 dB | -5.80 dB |
| offline window LS | +0.00 dB | +0.00 dB | +0.00 dB | +0.00 dB | +0.00 dB |
| predicted window (sigma^2 tr R G_win^-1) | +8.98 dB | -0.40 dB | -0.44 dB | -0.60 dB | -0.48 dB |
| sim exact LS (RLS lam 1) | -22.27 dB | -1.37 dB | -1.82 dB | -4.24 dB | -5.84 dB |
| sim E-PCG (main) | -24.25 dB | -0.72 dB | -0.71 dB | -0.64 dB | -0.73 dB |

