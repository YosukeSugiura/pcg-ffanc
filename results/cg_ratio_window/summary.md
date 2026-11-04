# CG optimization / estimation error under the final-evaluation conditions (E-PCG main, M = 512)
ratio = opt / est at every 4th plain-window hop (window >= 2M, no active event); tuning seeds 300-304.

| noise | cell | hops | median ratio | q90 ratio | max ratio | median lambda_min | median lambda_max |
|---|---|---|---|---|---|---|---|
| ar1 | S8 stationary | 385 | 0.033 | 0.076 | 0.098 | 0.621 | 9.58 |
| ar1 | S2 src 30cm | 337 | 0.033 | 0.074 | 0.099 | 0.621 | 9.58 |
| ar1 | R2 rig 30cm | 325 | 0.033 | 0.074 | 0.098 | 0.621 | 9.58 |
| harmonic | S8 stationary | 385 | 0.094 | 0.125 | 0.167 | 0.083 | 29.25 |
| harmonic | S2 src 30cm | 325 | 0.095 | 0.129 | 0.175 | 0.083 | 29.25 |
| harmonic | R2 rig 30cm | 325 | 0.093 | 0.131 | 0.329 | 0.083 | 29.25 |
