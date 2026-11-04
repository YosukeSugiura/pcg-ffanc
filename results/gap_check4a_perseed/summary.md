# Revision 10a/10b: per-seed breakdown of recursion A (ar1, T = 5 s), descriptive only (no judgement)

ratio = 10 log10(w-excess / sigma^2 (M/H)(1/b - 1/n_h)) with the per-seed sigma^2 (the ensemble in gap_check4a uses the
seed-mean sigma^2); peak = largest per-hop ratio within the first 32 hops.

| seed | 1-8 | 8-32 | 32-100 | 100-312 | peak hop | peak (dB) | lambda_max(K R) | share of ensemble 100-312 |
|---|---|---|---|---|---|---|---|---|
| 300 | +11.6 | +10.1 | +6.3 | +5.5 | 5 | +16.1 | 9.07 | 0 % |
| 301 | +32.6 | +31.2 | +23.8 | +21.4 | 4 | +38.3 | 9.24 | 7 % |
| 302 | +18.2 | +17.9 | +13.9 | +11.6 | 7 | +20.7 | 8.96 | 1 % |
| 303 | +25.2 | +23.2 | +17.2 | +14.8 | 3 | +31.8 | 9.19 | 2 % |
| 304 | +16.1 | +13.3 | +9.0 | +7.9 | 3 | +23.1 | 9.47 | 0 % |
| 305 | +20.6 | +21.0 | +15.0 | +12.7 | 5 | +26.7 | 9.17 | 1 % |
| 306 | +31.7 | +31.0 | +26.7 | +24.5 | 3 | +38.3 | 9.02 | 18 % |
| 307 | +38.5 | +37.0 | +31.9 | +30.0 | 6 | +45.6 | 9.38 | 66 % |
| 308 | +16.0 | +17.4 | +13.3 | +9.8 | 7 | +21.4 | 8.80 | 1 % |
| 309 | +25.5 | +24.9 | +21.5 | +18.8 | 3 | +29.9 | 8.89 | 4 % |

ensemble (seed-mean sigma^2): +22.57 dB; median of seeds: +13.73 dB

