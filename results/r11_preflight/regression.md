# Rule 11 Sec. 6.1 regression: new flags absent, this tree vs b3058bf

Methods: 12 selected baselines + RLS + CUSUM + E-PCG main + bank; cases [('ar1', 'S2 src 30cm', 300), ('harmonic', 'R2 rig 30cm', 300)]; T = 5 s;
RETURN_SIGNALS = True (also x_f, d_hat, e, y, w_final); every returned value compared byte for byte
(timing keys excluded); events of the + det baselines from this tree's E-PCG main run.

| method | noise | cell | identical |
|---|---|---|---|
| FD-FxNLMS | ar1 | S2 src 30cm | yes |
| leaky FD-FxNLMS | ar1 | S2 src 30cm | yes |
| convex FD-FxNLMS | ar1 | S2 src 30cm | yes |
| FDKF | ar1 | S2 src 30cm | yes |
| RLS | ar1 | S2 src 30cm | yes |
| VFF-RLS | ar1 | S2 src 30cm | yes |
| FD-FxNLMS + det | ar1 | S2 src 30cm | yes |
| RLS + det | ar1 | S2 src 30cm | yes |
| FD-FxNLMS + restart | ar1 | S2 src 30cm | yes |
| SFTF + det | ar1 | S2 src 30cm | yes |
| SFTF-H + det | ar1 | S2 src 30cm | yes |
| CFTF + det | ar1 | S2 src 30cm | yes |
| RLS + CUSUM | ar1 | S2 src 30cm | yes |
| E-PCG | ar1 | S2 src 30cm | yes |
| E-PCG bank | ar1 | S2 src 30cm | yes |
| FD-FxNLMS | harmonic | R2 rig 30cm | yes |
| leaky FD-FxNLMS | harmonic | R2 rig 30cm | yes |
| convex FD-FxNLMS | harmonic | R2 rig 30cm | yes |
| FDKF | harmonic | R2 rig 30cm | yes |
| RLS | harmonic | R2 rig 30cm | yes |
| VFF-RLS | harmonic | R2 rig 30cm | yes |
| FD-FxNLMS + det | harmonic | R2 rig 30cm | yes |
| RLS + det | harmonic | R2 rig 30cm | yes |
| FD-FxNLMS + restart | harmonic | R2 rig 30cm | yes |
| SFTF + det | harmonic | R2 rig 30cm | yes |
| SFTF-H + det | harmonic | R2 rig 30cm | yes |
| CFTF + det | harmonic | R2 rig 30cm | yes |
| RLS + CUSUM | harmonic | R2 rig 30cm | yes |
| E-PCG | harmonic | R2 rig 30cm | yes |
| E-PCG bank | harmonic | R2 rig 30cm | yes |

Result: PASS (30 runs).
