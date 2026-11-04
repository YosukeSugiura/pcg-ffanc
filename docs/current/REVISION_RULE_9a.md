# Revision 9a: 9-C の数値環境の固定（2026-11-03 JST、9-C 再実行前に固定）

Protocol provenance: `[working branch]`（HEAD 6df7fcb の後）。本書は 9-C 部屋 B の結合検査停止（`final_eval.py:177`「uncontrolled power differs」）の原因診断を見た後に作成した追補であり、9-C の性能結果を見る前の事前登録である。9-C 部屋 B の追加 640 run の集計・検定は行っていない。手法・設定・指標・検定・判定ラベル・解釈表は Rule 9 から一切変更しない。変更は「実行環境の固定」と「その事前検証」だけである。

## 1. 停止事象と原因（確定事項）
- 追加 640 run（CFTF + det, SFTF-H + det）の `up` は、同一 noise/scen/seed の既存記録と全件・全要素で不一致（相対差 中央値 4.9e-7、最大 1.26e-6、最大 5.5e-6 dB）。既存 10 手法 2880 組の `up` は互いに bit 一致。
- 追加 run の環境: Python 3.12.14 / numpy 2.3.5 / scipy 1.17.0 / pyroomacoustics 0.10.1。
- 既存 `results/eval_roomB/` は numpy 2.5.3 / scipy 1.18.1 / pyroomacoustics 0.10.1（Python 3.13.18）で FD-FxNLMS の 2 キーを再実行すると `up`・`tp` とも bit 一致（2026-11-03 査読時に確認）。
- 原因クラス: 依存ライブラリ版による数値環境ドリフト。手法・設定・ロジックの誤りではない。Rule 9 には環境の明記がなかったため、本書で固定する。

## 2. 環境の固定（9-C と 9-D に適用）
- numpy 2.5.3、scipy 1.18.1、pyroomacoustics 0.10.1。`RLS_FAST=1`、OMP/OpenBLAS/MKL とも 1 スレッド/プロセス、最大 2 プロセス。
- Python は 3.13.18 を推奨とする。他の版でも、3 節の事前検証に合格すれば可とする。合格・不合格にかかわらず、実際の版を provenance に記録する。

## 3. 事前検証（性能計算なし、各セットの本実行前に必須）
- 対象セット: 部屋 B、部屋 C、SNR10。各セットで E-PCG main を 4 キー再実行し、保存済み記録と比較する。
  - キー: 各セットの組合せ一覧（`revision9_rooms.py` の順）の先頭と末尾 × シード 480 と 519。
  - 比較: `tp`、`up`、`flag_stable`、`results/det_events/` の当該イベント列を、バイト単位（タイミング以外の全決定論的返却値）で比較する。
- 1 件でも不一致なら、そのセットは実行せず停止・報告する。許容誤差は設けない。
- 9-D は既存記録と結合しないため、上記検証は不要とする。ただし同じ固定環境で実行し、環境を provenance に記録する。

## 4. 記録の扱い
- `results/eval_roomB_x/`（numpy 2.3.5 環境の追加 640 run、ログ、結合検査の失敗ログ）は削除・上書きせず残す。provenance に「不採用：環境不一致（Rule 9a）」と記す。
- 9-C の新しい出力先は `results/eval_roomB_x2/`、`results/eval_roomC_x2/`、`results/eval_snr10_x2/` とする。出力先の変更以外、9-C の手順・キー・結合・検定は Rule 9 のとおり。部屋 C の `uncontrolled.jsonl` による補填も Rule 9 のとおり。
- 9-A（holdout）と 9-B（CUSUM 選択・holdout 評価）は、すべて numpy 2.3.5 / scipy 1.17.0 の単一環境で完結しており、手法間の `up` 一致検証も通過しているため、再実行しない。v2e とはシード独立で対にしないため、比較も有効とする。
- 論文の補足資料には、セット別の環境表を載せる（v2e・8a: numpy 2.5.x 系、9-A・9-B: 2.3.5 系、9-C・9-D: 2.5.3）。あわせて、numpy の版が異なると bit 再現しないことを明記する。

## 5. 順序と停止
- Rule 9a の commit → 環境構築 → 部屋 B の事前検証 → 部屋 B の本実行・summary → 部屋 C（検証 → 本実行・summary）→ SNR10（同）→ 9-D。
- 問題を発見した場合は、これまでどおり修正・再実行・ルール変更を行わず、停止して報告する。
