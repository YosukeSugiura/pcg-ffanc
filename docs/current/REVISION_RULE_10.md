# Revision 10: Prop. rho の数値検証（純粋な 1/b スケジュール）（2026-11-04 JST、実行前に固定）

目的: 査読（`[internal rationale omitted]` の 3a）への対応。理論の主結果 Prop. rho（circulant-RLS の 1/b スケジュールの漸近 excess と実現可能限界の比 ρ）を数値で確かめる。分析のみで、既存の手法・設定・ルール・評価結果は変更しない。論文に載せるかどうかは、結果を見た後に著者が判断する（載せない場合も結果は results に残す）。

## 1. 対象と設定（固定）
- セル: S8 stationary、M=512、N=2M、T=5 s、雑音 ar1 と harmonic。シードは調整用の 300–309（評価 480–519・holdout 800–839 には触れない）。`results/gap_check/` と同じシード集合なので、ρ の予測値はそこから読む。
- 純粋な 1/b スケジュール: 既存手法 `V-SCHED`、パラメータ `{'denom': 'cum', 'scale': 1.0, 'mu_min': 0.0, 'avg': False}`。すなわち μ_b=(N/H)/(b+1)、分母は再始動以降の |X_k|² の累積平均（正則化は既定の `regularization_ratio`）。restart・検出なし。
- 参照: `gap_check2.py` と同じ。oracle floor（全区間 LS 制御器の残差）、exact growing-window LS（`R-RLS`、lam=1、delta=1e-2）。比較のため FD-FxNLMS μ=0.2 と E-PCG（main）も同じ実行で再計算する。
- 指標: excess(method, hop) = アンサンブル平均残差パワー − oracle floor のアンサンブル平均（`gap_check2.py` と同じ定義、下限 1e-12）。比 = 10 log10(excess(method)/excess(exact LS)) を hop 区間 1–8、8–32、32–100、100–312 で報告する。加えて、各手法の excess の hop 100–312 での log-log 傾き（最小二乗、log10 excess を log10 hop に回帰）を報告する。
- 予測値: `results/gap_check/summary.md` の ρ_c（ar1: 10 シードの中央値。harmonic: λ<1/2 の固有値があるため ρ=∞）。

## 2. 解釈（結果を見る前に固定）
| 雑音 | 判定 | 条件 | 本文に書ける文 |
|---|---|---|---|
| ar1 | 一致 | hop 100–312 の比と ρ_c の予測値の差が 1 dB 以内 | 「有限時間（5 s）で、純粋な 1/b スケジュールの excess は exact LS の +x dB で、Prop. rho の予測 +0.07 dB と 1 dB 以内で一致した」 |
| ar1 | 乖離 | 差が 1 dB を超える | 「5 s では漸近値に達しておらず、差は +x dB だった（Prop. rho は漸近の結果）」と、32–100 から 100–312 への比の変化とあわせて書く。予測が否定されたとは書かない |
| harmonic | 一致 | 比が 32–100 から 100–312 で増え、かつ傾きが exact LS より 0 に近い（減衰が遅い） | 「λ<1/2 の固有値を持つ線スペクトルでは、予測どおり 1/b スケジュールは exact LS より遅く減衰した」 |
| harmonic | 乖離 | 上の 2 条件のどちらかを満たさない | 観測値をそのまま書き、「5 s の範囲では予測された遅い減衰は確認できなかった」とする |
- 1 dB の幅は 5 s・10 シードの有限標本での目安で、同等性の検定ではない。p 値・検定は行わない（記述のみ）。
- 結果を見てから、スケジュールのパラメータ・シード・区間・閾値を変えない。数値的な問題（NaN、発散）が出たら停止して報告する。

## 3. 出力と手順
- スクリプト `experiments/gap_check4.py`（`gap_check2.py` を基に、手法の一覧と傾きの計算だけを追加）。出力は `results/gap_check4/`（summary.md、curves.npz、provenance.json：commit、本ルールの sha256、Python/numpy/scipy/pyroomacoustics の版、RLS_FAST、スレッド数）。既存の `results/gap_check*/` は上書きしない。
- 1 ジョブ（setsid nohup）、`RLS_FAST=1`、1 スレッド。
