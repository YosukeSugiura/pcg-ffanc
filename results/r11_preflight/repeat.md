# Rule 11b Sec. 2.3 m3: in-environment determinism (two processes)

- key: room B, ar1 S8 stationary, seed 480, E-PCG main, 5 s, RETURN_SIGNALS
- PRA_NUM_THREADS 2; compared values: ['adapt_log', 'cons_log', 'dhat', 'dual_log', 'e', 'eb_hist', 'events_total', 'failure', 'flop_hist', 'geom', 'loc_hist', 'log_evidence', 'mem_pi', 'n_resets', 'post_log', 'prior_log', 'reset_hops', 'ridge_excess', 'risk_log', 'rl_hist', 's', 's2', 's2pre_log', 'score_hist', 'seed', 'seq_log', 'shat', 'sid_log', 'stable', 'sub_log', 'thA_log', 'total_power', 'uncontrolled_power', 'w_final', 'x', 'xf', 'y']
- machine: {"cpu_model": "INTEL(R) XEON(R) PLATINUM 8573C", "cpu_count": 3, "cpu_flags_sha256": "16a7227851bbd0d54c1a76b00030c349f39b11fe7860f6e2de2e0b7e1261be4c"}

Result: PASS
