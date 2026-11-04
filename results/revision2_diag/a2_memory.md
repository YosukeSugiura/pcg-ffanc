# A2 vs memory length (REVISION_RULE_2.md section 5; stored records only, AR(1), S8)
Prediction: steady excess relative to the floor e = M (1 - lambda) / 2 (exponential window), e = M / (L H) (E-PCG window);
dB = 10 log10(1 + e). M = 512, H = 128, L = 48.

| check | records | observed (dB) | predicted (dB) | within +-0.1 |
|---|---|---|---|---|
| (i) RLS lambda 0.9995 - RLS + det 0.9999, median A2 | final_eval_v2 (evaluation seeds) | 0.45 | 0.41 | yes |
| (ii) RLS 0.9995 - 0.9999, median A2 | protocol_v2_sel (tuning seeds) | 0.46 | 0.41 | yes |
| (ii) RLS 0.9998 - 0.9999, median A2 | protocol_v2_sel | 0.11 | 0.11 | yes |
| (iii) E-PCG L = 24 - L = 48, median paired dA (A = NR over [1 s, end]) | ablation_core_d (tuning seeds) | 0.39 | 0.32 | yes |
| (consequence) E-PCG - RLS + det, A2 | final_eval_v2 | +0.26 (paired) / 0.27 (medians) | 0.24 | yes |

Verdict by the rule: all within +-0.1 dB -> the A2 difference to RLS + det is explained by the memory length
(window L H = 6144 samples vs exponential memory 1 / (1 - lambda) = 1e4); AR(1) only (harmonic: low rank, not claimed).
