# Revision 8a: MeshRIR共通系遅延の除去（2026-11-01 JST、承認前）

Protocol provenance: `[working branch]`。本書はRule 8の結果および不具合診断を見た後に作成した不具合修正版であり、結果を見る前の事前登録ではない。
修正版の性能はまだ計算していない。パラメータの再調整・手法設定の変更は行わない。科学的な前処理変更は全IRからの同一共通遅延の除去だけとする。

## 1. 唯一の前処理変更：全体で一度だけ決める共通遅延

- 対象はS32-M441全体、32音源×441マイク＝14,112本の生IR（48 kHz、32768点）。部分集合や評価結果による選び直しはしない。
- 各IRについて `a_ij = argmax_n |h_ij[n]|`（0始まり、同値なら最初）と `g_ij = 48000 * ||source_i - mic_j|| / 343` を計算する。
- `d0 = floor(min_ij(a_ij - g_ij) - 96)`。96サンプルは48 kHzで2 ms。
- **固定値：`d0 = 5434` サンプル（48 kHz）、113.208333333333 ms。**
- 最小値は `5530.5051807837945` サンプル。音源23・マイク110においてピーク5741、幾何遅延210.49481921620512サンプル。したがって `floor(5530.5051807837945 - 96) = 5434`。
- 全体の推定系遅延中央値は5671.507859541656サンプル（約118.1564 ms）。d0は中央値ではなく上記最小値から決定した。
- 全経路 `P, P2, S, S2` に同一の `h_shift = h[5434:]` を適用してから、Rule 8と同じ `resample_poly(1,6, window=('kaiser',5.0), padtype='constant', cval=0.0)` と打ち切りを行う。
- P/P2は1200点、S/S2は512点（8 kHz）のまま。経路ごとのピーク整列、到達位置整列、d0の再推定はしない。相対遅延は保たれるため、幾何学的因果性・割り当てはRule 8のまま。
- 初期P/Sの打ち切り後L2ノルムから得た利得を変化後にも再利用する。正規化方法は変更しない。
- 承認後の実装は `cfg['meshrir_d0']` で制御し、既定値は0（Rule 8そのもの）。Rule 8aの実行時のみ5434を指定する。現時点では実装していない。

## 2. 事前確認（性能計算なし）：合格

- 元の最大値の0.1倍を初めて厳密に超える点を−20 dB到達とする。除去前の到達点から5434を引いた位置が非負かつ窓内であることを確認した。
- さらに同じ共通除去・リサンプリング後の全長IRでも−20 dB到達を測定し、実際の8 kHz打ち切り窓内であることを確認した。
- 全14,112本を潜在的Pとして、同じ全14,112本を潜在的Sとして確認した。P/P2の評価窓は[0:1200]、S/S2は[0:512]。
- 除去後の生IR到達位置は305–534サンプル（48 kHz）。8 kHzでの到達位置は47–88サンプル。
- P：生IR・8 kHzとも窓外0/14,112本。S：生IR・8 kHzとも窓外0/14,112本。
- 評価シード480–519に実際に割り当てるP（初期・M-P変化後・M-PS変化後）120件とS（初期・M-PS変化後）80件もすべて窓内。
- エネルギー比は正規化前に計算する。主な保持率は「共通除去・リサンプリング後の打ち切りエネルギー / 同じ除去・リサンプリング後の全長エネルギー」。併せて「48 kHzの[h[d0:d0+6L]]のエネルギー / 元の生IR全長エネルギー」も記録する。
- 保持率に指定されていない受理閾値は追加しない。全保持率は有限かつ0より大きく1以下。値を見て窓長・d0を変更しない。到達条件不合格・非有限・ゼロノルム等があれば停止して報告する。

### 全14,112本の保持率（%、中央値 (Q1, Q3)）

| 窓 | 実際の8 kHz保持率 | 実際の8 kHz保持率 min–max | 元の生IR全長に対する保持率 |
|---|---|---|---|
| P | 99.6273 (99.4712, 99.7523) | 87.7970–99.9709 | 99.9066 (99.8605, 99.9398) |
| S | 98.8378 (98.4680, 99.1866) | 84.5763–99.8403 | 99.6221 (99.4636, 99.7428) |

### 評価シードの割り当て別保持率（各40件、%）

| 経路 | 実際の8 kHz保持率：中央値 (Q1, Q3) | min–max | 到達条件不合格 |
|---|---|---|---|
| P_before | 99.5229 (99.4244, 99.6276) | 99.2768–99.8911 | 0/40 |
| P_after_MP | 99.5498 (99.4328, 99.6902) | 99.1123–99.9191 | 0/40 |
| P_after_MPS | 99.5710 (99.4852, 99.6463) | 99.0816–99.7883 | 0/40 |
| S_before | 98.7633 (98.4549, 99.2655) | 97.3336–99.7359 | 0/40 |
| S_after_MPS | 98.8291 (98.5173, 99.2603) | 97.3736–99.7862 | 0/40 |

既存resultsの1,364ファイルについて実行前後のSHA256が不変。適応制御・Wiener下限・NR・統計・勝敗等の性能計算は行っていない。
なおonset.mdでは、元のP直接音は150 ms窓内、S直接音は64 ms窓外だった。両方を同じd0で処理することに変更はない。

## 3. 予想・開示・保存先

- 予想を修正版の性能を見る前に固定する：**制御可能性はRule 8より大きく改善する。改善しない場合もそのまま報告する。**
- Rule 8の結果は削除・改変しない。論文には「前処理の不具合で無効」と開示する前提とする。本タスクではpaper/と[workflow reference omitted]を編集しない。
- 割り当て、評価シード480–519、全14手法、選択済み設定、指標、失敗処理、統計、Holm族、閾値、判定表は、下記引用のRule 8原文のまま使う。新しいチューニングは0件。
- 承認後の保存先だけを分ける：制御可能性診断 `results/revision8a_diag/`、本評価 `results/final_eval_meas_p_8a/` と `results/final_eval_meas_ps_8a/`。引用中の旧保存先はRule 8の履歴として残し、8aでは書き込まない。
- 承認後はISMシード300のbit一致、meshrir_d0=0と保存済みRule 8スモーク出力のbit一致を確認してから、修正経路の制御可能性診断・本評価・同形式のsummary.mdを作る。
- 本評価は各セット1ジョブ、2プロセス並列、setsid nohup。結果を見た後で手法・設定・ルールを変更しない。問題が見つかったら修正せず停止して報告する。

## 4. フェーズ1の停止点

本書だけをcommit・pushし、全文・d0・事前確認結果を報告して停止する。承認されるまでは実装、回帰実行、制御可能性の性能計算、本評価を行わない。

## 5. Rule 8原文の全文引用（変更なし）

以下は参照用の原文を一字も変えず引用する。8aでは上記の共通遅延除去が、引用中の「Remove 0 leading samples」を置き換える。旧日付・旧出力先・旧フェーズの記述は履歴であり、8aの承認停止点と新保存先は上記を適用する。それ以外の科学的条件と判定表は引用どおりとする。
原文SHA256：`a42fea3be6d11b4b96161f2a62ee853c06e28c16b89d2cfd506bf11bdd58e71c`。

```text
# Revision 8: measured-path evaluation (MeshRIR; fixed 2026-11-01 JST, before running)

Protocol scope: measured FFANC paths, phase 1 only until approval. Base: [development branch],
3dc70ced23afa76ed72e54f0cb808ff7ecfad18c; protocol provenance: [working branch] No retuning.
No measured-path performance run, including a smoke run, precedes this rule. Inspection of file formats,
coordinates and data integrity is permitted; paper/ and [workflow reference omitted] are not edited.

## Method (measured P / S; defaults unchanged)
- Data: MeshRIR v1.1, DOI 10.5281/zenodo.5500451, S32-M441 only: 32 sources, 441 microphones,
  48000 Hz, 32768 samples/IR, reported T60 0.19 s. Official S32-M441_npy.zip: 3534777656 bytes,
  MD5 4fcd6137bcadb6914d4170ff366c86f9. README confirms Creative Commons Attribution 4.0 International
  (CC BY 4.0; https://creativecommons.org/licenses/by/4.0/). Credit Koyama, Nishida, Kimura, Abe,
  Ueno and Brunnström. Keep data, archive, README and LICENSE under ignored data/meshrir/; no data commit.
  Record dataset, DOI, version, subset, license name/URL, attribution, archive checksum and preprocessing
  in provenance.json and summary.md in BOTH result directories. Unavailable/corrupt data: stop, report;
  no synthetic substitute, interpolation, denoising or hand-picked replacement.
- P = noise source -> error microphone; S = secondary source -> the SAME error microphone.
  Official file ir_<m>.npy is indexed [source, sample]; retain original zero-based source/mic indices.
  Geometry comes from pos_src.npy (32 x 3) and pos_mic.npy (441 x 3), in metres.
- Allocation, identical across methods, noises and the two scenarios: initialize
  g = numpy.random.Generator(numpy.random.PCG64(seed + 31337)). At each of at most 1000 attempts:
  (1) m0 = int(g.integers(441)); (2) form the ascending list of microphone indices whose Euclidean
  distance to m0 is 0.05 m within absolute tolerance 1e-9 m; draw m1 uniformly with g.integers(len(list));
  (3) secondary source j = int(g.integers(32)); (4) form the ascending list C of source indices i != j
  satisfying distance(i,m) - distance(j,m) >= 0.343 m at BOTH m=m0 and m=m1 (1 ms geometric
  causality margin at 343 m/s, matching main's ism_causal_ms=1.0). If len(C)<2, restart at (1).
  Otherwise draw (i0,i1) = g.choice(C, size=2, replace=False), in that returned order, and accept.
  If 1000 attempts fail, stop and report. No IR amplitudes, onset estimates or performance enter selection.
  P=IR(i0,m0), S=IR(j,m0); i0, i1 and j are distinct. Save all five indices and coordinates per seed.
  S32-M441 is a 21 x 21 square grid with 0.05 m nearest-neighbour spacing; boundary points remain eligible.
- Preprocessing, independently for each raw path: cast to float64; scipy.signal.resample_poly(h, up=1,
  down=6, window=('kaiser',5.0), padtype='constant', cval=0.0); keep samples [0:1200] for P/P2,
  [0:512] for S/S2, right-zero-pad only if necessary. Resample before truncating. Remove 0 leading
  samples: retain the physical direct-path delay and all pre-direct samples; do not align peaks/onsets.
  Let a=1/||P_raw||2 and b=1/||S_raw||2 AFTER resampling/truncation. Return P=a*P_raw, S=b*S_raw,
  P2=a*P2_raw, S2=b*S2_raw: reuse INITIAL gains, never independently renormalize changed paths
  (exactly ism_paths). Non-finite paths or zero initial norms: stop and report, do not redraw.
- M-P: abrupt noise-source switch i0 -> i1 at fixed m0; P2=IR(i1,m0); S fixed (s2=None,
  the existing ism_paths source-change convention). M-PS: i0 and j fixed; error microphone moves
  m0 -> m1 (exactly 0.05 m), P2=IR(i0,m1), S2=IR(j,m1). This is a mic move, NOT a rigid
  source/mic move. S_hat is the initial normalized S and stays fixed, as in existing R2.
  For each path above, apply the preprocessing/gains already specified.
- New meshrir_paths(cfg,seed,extra) returns (p,s,p2,s2), recording provenance in extra.
  Dispatch only for cfg['path_source']=='meshrir'; default path_source='ism' preserves existing behaviour.

## Grid, selection, evaluation
- Zero new configurations or tuning trials. Use selected_e.json's frozen 12 baselines, plus E-PCG and
  E-PCG bank (14 methods total). E-PCG uses final_config_core_main.json['flags']; bank uses
  final_config_core_final.json['flags']; all are loaded exactly as eval_v2._setup_final at the base commit.
  selected_e indices: FD-FxNLMS 5; leaky 5; convex 3; FDKF 2; RLS 0; VFF-RLS 0; FD-FxNLMS + det 7;
  RLS + det 1; FD-FxNLMS + restart 1; SFTF + det 1; SFTF-H + det 2; CFTF + det 1.
  selected_e.json SHA256: 76fa959eee7b431b9ecbb57f4e2f0614875e52035749c37287d3c33e516cc665.
  MAIN SHA256: aab4a80cfcddd051d5b9fdfa8240227afb42faff5d03e622289d32a7f961e814.
  BANK SHA256: 5e2a342b4690c115ea8221d6bfd6d6dea3e7f7a8627465aee1dde0375c09752d.
  Detector-equipped baselines receive E-PCG's events from the SAME measured closed loop; no ISM cache reuse.
  Keep the selected CFTF configuration despite its known numerical failure; no rescue or reselection.
- Add room M with path_source='meshrir', len_p=1200, len_s=512 (Room B lengths). meas_p uses
  the S2 abrupt-source template with M-P paths; meas_ps uses the R2 abrupt-change template with M-PS paths.
  These labels inherit timing/metrics only: measured changes are not claimed to be 30 cm source/rig moves.
  Two noises in each set: ar1 and harmonic, with existing main's generation, normalization and random streams.
  T=5.0 s, change_at=1.0 s (sample 8000), fs=8000 Hz, H=128, M=512, N=1024, sensor SNR=20 dB;
  move_steps=0 (abrupt). All other signal/controller/simulator conditions are unchanged from main.
  Outputs: results/final_eval_meas_p and results/final_eval_meas_ps; never overwrite existing results.
- Evaluation seeds 480..519 inclusive (40), no omissions: 14 x 2 x 40 = 1120 method records/set,
  2240 total. A1/A2 are the existing final_eval.metrics energy-ratio NR (lower is better):
  A1 hops [63,95), i.e. [1.008,1.520) s; A2 hops [95,312), i.e. [1.520,4.992) s.
  Use 10*log10(sum(error power)/sum(uncontrolled power)), not a mean of hop dB.
  Failures: SAME as main's nonstationary S2/R2: strict_div.evaluate_div (simulator flag/abort or
  last 62 hops' aggregate NR >0 dB); do not substitute the stricter mic-window evaluate criterion.
  Failed runs remain in all statistics with A1=A2=0 dB; failures reported as n/40. Pad aborted traces
  with the same run's uncontrolled power as existing final_eval; if all methods abort, obtain it from
  a separately recorded no-control run, never extrapolate. Missing/corrupt records are not failures: stop/report.
- Tables: median (Q1,Q3) A1/A2 and failures for every method x scenario x noise, preserving failed runs.
  Paired differences use the median of 40 per-seed differences, not a difference of medians.
  Two-sided scipy.stats.wilcoxon, zero_method='pratt', method='auto'; all-zero differences give p=1.
  Holm family: 2 metrics x 2 noises x 12 baselines = 48 tests per proposed method PER evaluation set;
  four separate 48-test families (E-PCG / bank x meas_p / meas_ps), not a pooled 96/192-test family.
  Bank-minus-main is secondary: 2 metrics x 2 noises = 4 tests per set, two separate families; no win claim.
  No significance test of failures. Alpha=0.05, adjusted p<0.05 (strict).
- Exactly final_eval.label: for d=proposed-baseline, a win flag if (p_A1<0.05 and dA1<=-1.0 dB)
  OR (p_A2<0.05 and dA2<=-0.5 dB); loss flag for the respective >=+1.0 / >=+0.5 dB.
  Both flags -> mixed; win only -> win; loss only -> loss; neither -> '-' (no demonstrated difference,
  not an equivalence claim). Failures are displayed alongside labels, never silently excluded.
- After approval only: ISM regression on seed 300, S2/ar1, T=5 s, E-PCG and frozen MAIN: compare all
  deterministic returned fields/arrays bit for bit with an untouched base-commit run, excluding timing.
  Measured smoke: meas_p/ar1, seeds 300 and 301, T=1.5 s, change_at=1.0 s, all 14 methods;
  test mechanics only, not selection/statistics/claims. No tuning or rule change based on smoke outcomes.
  Run with RLS_FAST=1 and 1 BLAS/OpenMP thread/process; production: two concurrent processes, one job/set,
  launched with setsid nohup, distinct log files. Keep both CPUs busy while jobs remain. No nested sharding
  that launches more than 2 workers. Record dependency versions and full rule/commit in results.
  Any discovered problem: stop and report without a code/configuration/rule repair or unapproved rerun.

## Interpretation
Prediction fixed in advance: M-PS is expected to degrade ALL methods because S_hat stays at the pre-move S.
This is a prediction, not a conclusion; report contrary observations. Geometry and the measured dataset differ
from ISM, so do not attribute any performance change solely to T60 or to a 30 cm displacement.

| outcome (E-PCG vs RLS + det, separately in each of the 4 scenario x noise cells) | text |
|---|---|
| win by the above rule | State the measured-path A1/A2 advantage only in that cell, with effect sizes, adjusted p and failures. If E-PCG has more failures, explicitly qualify the advantage as a stability/performance trade-off; do not claim robust superiority. |
| '-' (tie/no demonstrated difference) | State that measured-path tracking is comparable descriptively but superiority was not demonstrated; do not claim statistical equivalence. Report any A2 deficit and both failure counts. |
| loss | State that E-PCG did not generalize its advantage in that cell and RLS + det performed better under the fixed rule; restrict the paper's advantage claim to conditions actually supported. |
| mixed | State conflicting A1/A2 evidence as a trade-off; count neither a win nor a tie and do not make an overall superiority claim. |

No global majority vote across cells. Claim an advantage in all measured conditions only if all 4 cells are wins
and E-PCG has no more failures than RLS + det in each. Otherwise name the supported cells individually.
M-PS losses/failures are reported as a limit under secondary-model mismatch; never repair S_hat after seeing them.
These are instructions for a later paper revision: paper/ remains untouched in this task.

## Order
Download/verify data and fix this rule -> commit/push -> STOP and report the full rule for user approval.
Only after approval: implement -> ISM bit regression -> measured smoke -> commit/push -> two full jobs ->
summary.md in the existing format with the above families/decisions -> commit/push -> concise Japanese report.
```
