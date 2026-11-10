# Revision 11 tuning (room A, tuning seeds 300-309 + 600-619; Rule 11 Sec. 1.4)

| group | config | params | result |
|---|---|---|---|
| MFBLMS | 0 (selected) | {"mu": 0.05, "mod": true} | -10.0348 |
| MFBLMS | 1 | {"mu": 0.1, "mod": true} | fail ('ar1', 'S7 rd abrupt', 606) |
| MFBLMS | 2 | {"mu": 0.15, "mod": true} | fail ('ar1', 'S7 rd abrupt', 602) |
| MFBLMS | 3 | {"mu": 0.2, "mod": true} | fail ('ar1', 'S7 rd abrupt', 301) |
| MFBLMS | 4 | {"mu": 0.25, "mod": true} | fail ('ar1', 'S7 rd abrupt', 301) |
| MFBLMS | 5 | {"mu": 0.3, "mod": true} | fail ('harmonic', 'S8 stationary', 300) |
| MFBLMS | 6 | {"mu": 0.025, "mod": true} | -7.3562 |
| MFBLMS + det | 0 (selected) | {"mu": 0.05, "mod": true, "det_boost": 0.0625, "det_reset_w": false} | -10.8548 |
| MFBLMS + det | 1 | {"mu": 0.05, "mod": true, "det_boost": 0.125, "det_reset_w": false} | fail ('ar1', 'S7 rd abrupt', 612) |
| MFBLMS + det | 2 | {"mu": 0.05, "mod": true, "det_boost": 0.25, "det_reset_w": false} | fail ('harmonic', 'S5 src 30cm cont', 300) |
| MFBLMS + det | 3 | {"mu": 0.05, "mod": true, "det_boost": 0.0, "det_reset_w": true} | -6.9861 |
| MFBLMS + det | 4 | {"mu": 0.05, "mod": true, "det_boost": 0.0625, "det_reset_w": true} | -7.8855 |
| MFBLMS + det | 5 | {"mu": 0.05, "mod": true, "det_boost": 0.125, "det_reset_w": true} | fail ('ar1', 'S7 rd abrupt', 612) |
| MFBLMS + det | 6 | {"mu": 0.05, "mod": true, "det_boost": 0.25, "det_reset_w": true} | fail ('harmonic', 'S5 src 30cm cont', 300) |
| switching FD-FxNLMS [6] | 0 (selected) | {"mu_n": 0.3, "mu_m": 0.05, "sw_thr": 0.01, "sw_dwell": 4, "sw_detect": "zeta"} | -12.9369 |
| switching FD-FxNLMS [6] | 1 | {"mu_n": 0.3, "mu_m": 0.05, "sw_thr": 0.01, "sw_dwell": 8, "sw_detect": "zeta"} | -12.9088 |
| switching FD-FxNLMS [6] | 2 | {"mu_n": 0.3, "mu_m": 0.05, "sw_thr": 0.03, "sw_dwell": 4, "sw_detect": "zeta"} | -12.6167 |
| switching FD-FxNLMS [6] | 3 | {"mu_n": 0.3, "mu_m": 0.05, "sw_thr": 0.03, "sw_dwell": 8, "sw_detect": "zeta"} | -12.8711 |
| switching FD-FxNLMS [6] | 4 | {"mu_n": 0.3, "mu_m": 0.05, "sw_thr": 0.1, "sw_dwell": 4, "sw_detect": "zeta"} | -12.0503 |
| switching FD-FxNLMS [6] | 5 | {"mu_n": 0.3, "mu_m": 0.05, "sw_thr": 0.1, "sw_dwell": 8, "sw_detect": "zeta"} | -12.4578 |
| switching FD-FxNLMS + det | 0 | {"mu_n": 0.3, "mu_m": 0.05, "sw_thr": 0.01, "sw_dwell": 4, "sw_detect": "det"} | -13.2950 |
| switching FD-FxNLMS + det | 1 (selected) | {"mu_n": 0.3, "mu_m": 0.05, "sw_thr": 0.01, "sw_dwell": 8, "sw_detect": "det"} | -13.4729 |
| switching FD-FxNLMS + det | 2 | {"mu_n": 0.3, "mu_m": 0.05, "sw_thr": 0.03, "sw_dwell": 4, "sw_detect": "det"} | -12.7868 |
| switching FD-FxNLMS + det | 3 | {"mu_n": 0.3, "mu_m": 0.05, "sw_thr": 0.03, "sw_dwell": 8, "sw_detect": "det"} | -13.1248 |
| switching FD-FxNLMS + det | 4 | {"mu_n": 0.3, "mu_m": 0.05, "sw_thr": 0.1, "sw_dwell": 4, "sw_detect": "det"} | -12.3733 |
| switching FD-FxNLMS + det | 5 | {"mu_n": 0.3, "mu_m": 0.05, "sw_thr": 0.1, "sw_dwell": 8, "sw_detect": "det"} | -12.7206 |
| RLS + det (cond.) | 0 (selected) | {"lam": 0.9999, "delta": 0.01, "det_reset_w": false, "det_cond_db": 1.0, "det_cond_k": 32} | -14.9424 |
| RLS + det (cond.) | 1 | {"lam": 0.9999, "delta": 0.01, "det_reset_w": false, "det_cond_db": 2.0, "det_cond_k": 32} | -14.9229 |
| RLS + det (cond.) | 2 | {"lam": 0.9999, "delta": 0.01, "det_reset_w": false, "det_cond_db": 4.0, "det_cond_k": 32} | -14.8607 |
| RLS + det (cond.) | 3 | {"lam": 0.9999, "delta": 0.01, "det_reset_w": false, "det_cond_db": 8.0, "det_cond_k": 32} | -14.1181 |
| RLS + det + growth | 0 (selected) | {"lam": 0.9999, "delta": 0.01, "det_reset_w": false, "det_grow": "half"} | -12.7567 |
| RLS + det + growth (from start) | 0 (selected) | {"lam": 0.9999, "delta": 0.01, "det_reset_w": false, "det_grow": "half", "det_grow_start": true} | -12.7803 |
| RLS + CUSUM [reference] | 0 (selected) | {"lam": 0.9999, "delta": 0.01, "cusum_h": 5, "cusum_k": 32} | -14.6932 |

## Outer grid points (Sec. 4.2; reference = recorded score, or the re-run in this environment for ['RLS + CUSUM']; env_C class I, Rule 11b Sec. 4)

| base | recorded score | re-run score (this environment) | re-run - recorded | reference used | decision |
|---|---|---|---|---|---|
| RLS | -13.8600 |  |  | recorded | better: extended-grid row |
| VFF-RLS | -13.4400 |  |  | recorded | better: extended-grid row |
| SFTF-H + det | -14.9500 |  |  | recorded | interior (outer point not better by > 0.01 dB) |
| RLS + CUSUM | -14.6932 | -14.6932 | +0.0000 | rerun | better: extended-grid row |
| FD-FxNLMS | -13.5800 |  |  | recorded | better: extended-grid row |
| leaky FD-FxNLMS | -13.4900 |  |  | recorded | interior (outer point not better by > 0.01 dB) |
| FDKF | -12.0300 |  |  | recorded | better: extended-grid row |
| FD-FxNLMS + det | -13.0100 |  |  | recorded | better: extended-grid row |

- RLS: {"existing_score": -13.86, "reference_score": -13.86, "reference_source": "recorded", "first": [{"prm": {"lam": 0.9993, "delta": 0.01}, "result": "done", "value": -14.04653178890275}], "decision": "better: extended-grid row", "second": [{"prm": {"lam": 0.9991, "delta": 0.01}, "result": "fail", "value": ["ar1", "S8 stationary", 300]}], "second_decision": "failed", "status": "done", "row": {"kind": "R-RLS", "params": {"lam": 0.9993, "delta": 0.01}, "score": -14.04653178890275}}
- VFF-RLS: {"existing_score": -13.44, "reference_score": -13.44, "reference_source": "recorded", "first": [{"prm": {"N0": 250.0, "lam_min": 0.9995, "delta": 0.001}, "result": "done", "value": -13.480503077412354}], "decision": "better: extended-grid row", "second": [{"prm": {"N0": 125.0, "lam_min": 0.9995, "delta": 0.001}, "result": "done", "value": -13.509359066554527}], "second_decision": "better than the first step: row uses the second step (maximum two steps reached)", "status": "done", "row": {"kind": "R-VFF", "params": {"N0": 125.0, "lam_min": 0.9995, "delta": 0.001}, "score": -13.509359066554527}}
- SFTF-H + det: {"existing_score": -14.95, "reference_score": -14.95, "reference_source": "recorded", "first": [{"prm": {"lam": 0.9999, "delta": 0.01, "det_reset_w": false, "hybrid": 4096}, "result": "done", "value": -14.955178068128754}], "status": "done", "decision": "interior (outer point not better by > 0.01 dB)", "row": null}
- RLS + CUSUM: {"existing_score": -14.693186295224526, "reference_score": -14.693186285976768, "reference_source": "rerun", "reference_minus_recorded": 9.247758114838689e-09, "first": [{"prm": {"lam": 0.9999, "delta": 0.01, "cusum_h": 3, "cusum_k": 64}, "result": "fail", "value": ["ar1", "S7 rd abrupt", 303]}, {"prm": {"lam": 0.9999, "delta": 0.01, "cusum_h": 5, "cusum_k": 64}, "result": "done", "value": -14.768071547056097}, {"prm": {"lam": 0.9999, "delta": 0.01, "cusum_h": 8, "cusum_k": 64}, "result": "done", "value": -14.636905183870635}], "decision": "better: extended-grid row", "status": "done", "row": {"kind": "R-RLS", "params": {"lam": 0.9999, "delta": 0.01, "cusum_h": 5, "cusum_k": 64}, "score": -14.768071547056097}, "note": "Rule 11 defines no second step for this base: not run (report to the author)"}
- FD-FxNLMS: {"existing_score": -13.58, "reference_score": -13.58, "reference_source": "recorded", "first": [{"prm": {"mu": 0.32}, "result": "done", "value": -13.622916607069955}], "decision": "better: extended-grid row", "status": "done", "row": {"kind": "fixed_binwise", "params": {"mu": 0.32}, "score": -13.622916607069955}, "note": "Rule 11 defines no second step for this base: not run (report to the author)"}
- leaky FD-FxNLMS: {"existing_score": -13.49, "reference_score": -13.49, "reference_source": "recorded", "first": [{"prm": {"mu": 0.35, "leak": 0.03}, "result": "done", "value": -12.187281650929366}, {"prm": {"mu": 0.5, "leak": 0.01}, "result": "fail", "value": ["harmonic", "R2 rig 30cm", 302]}], "status": "done", "decision": "interior (outer point not better by > 0.01 dB)", "row": null}
- FDKF: {"existing_score": -12.03, "reference_score": -12.03, "reference_source": "recorded", "first": [{"prm": {"P0": 3.0, "gain_scale": 4.0, "A": 0.9995}, "result": "done", "value": -12.219271752825955}], "decision": "better: extended-grid row", "status": "done", "row": {"kind": "C-FDKF", "params": {"P0": 3.0, "gain_scale": 4.0, "A": 0.9995}, "score": -12.219271752825955}, "note": "Rule 11 defines no second step for this base: not run (report to the author)"}
- FD-FxNLMS + det: {"existing_score": -13.01, "reference_score": -13.01, "reference_source": "recorded", "first": [{"prm": {"denom": "cum", "scale": 0.03125, "mu_min": 0.2, "det_reset_w": false}, "result": "done", "value": -13.02681507615787}], "decision": "better: extended-grid row", "status": "done", "row": {"kind": "V-SCHED", "params": {"denom": "cum", "scale": 0.03125, "mu_min": 0.2, "det_reset_w": false}, "score": -13.02681507615787}, "note": "Rule 11 defines no second step for this base: not run (report to the author)"}

Stages complete: {'B1': True, 'B2': True, 'C': True}; n_new = 13 rows: ['MFBLMS', 'MFBLMS + det', 'switching FD-FxNLMS [6]', 'switching FD-FxNLMS + det', 'RLS + det (cond.)', 'RLS + det + growth', 'RLS + det + growth (from start)', 'RLS (extended grid)', 'VFF-RLS (extended grid)', 'RLS + CUSUM (extended grid)', 'FD-FxNLMS (extended grid)', 'FDKF (extended grid)', 'FD-FxNLMS + det (extended grid)']
