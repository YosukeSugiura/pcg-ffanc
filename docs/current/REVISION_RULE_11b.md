# Revision 11b: 事前検証 §6.2 の不一致の扱い（環境の再定義と、ビット一致の置き換え）

**固定版（著者の包括的な委任による、2026-11-07）。** 本書は `REVISION_RULE_11.md`（固定版、sha256 `6ba432af58880a94d6915beab8f7183af645b706bff37b959d4acdd6519bf270`。以下 Rule 11）と `REVISION_RULE_11a.md`（固定版、sha256 `6d26fe9394c9bcba244065171812ddc6e5418689be89a13609ac16db4c077563`。以下 Rule 11a）の追補である。Rule 11 の手法・グリッド・閾値・シード・指標・検定・family・§7 の文・§9 の決定、Rule 11a の B-1・B-2・M-2・§5・§6 は**一切変更しない**。本書が定めるのは、(1) 実行担当の環境で §6.2 環境 C が FAIL した事象の原因の特定と扱い、(2) 実行環境の定義の訂正（pyroomacoustics のスレッド数）、(3) 「ビット一致」の判定を「完全一致すべき項目＋測定前に固定した相対差の上限」に置き換える規則と、(4) それにより影響を受ける Rule 11 の比較の閉じ方、(5) 開示、(6) コード修正、である。

- 作成: 2026-11-07 JST、[provenance note omitted]。対象ブランチ `[working branch]`（HEAD 8fb13e0）。実行担当の記録は `[run branch]` c09572a（`results/r11_preflight/env_C.json`、`"pass": false`）。
- 著者の方針（2026-11-07、了承済み）: 「比較は実行環境の中で閉じる。ビット一致を、events 等の完全一致＋tp/up の相対差上限（測定前に固定）に置き換え、差の大きさを記録する」。本書はこの方針を、原因の特定結果（§1）を踏まえて具体化したものである。
- 前例: `REVISION_RULE_9a.md`（結合検査の停止後、性能結果を見る前に環境を固定）、Rule 11a §3.1（環境 A の不一致 → 経路 (b)）。

## 0. 経緯の開示（何を見た後に固定したか）

| 時点 | 行ったこと | 見た数値 |
|---|---|---|
| 2026-11-07 | Rule 11・11a の固定、実装、内部コードレビュー 2 回（[internal review records]） | smoke（seed 300）のみ |
| 2026-11-06 23:03 UTC | 実行担当の環境（Python 3.13.5 / numpy 2.5.3 / scipy 1.18.1 / pyroomacoustics 0.10.1、1 スレッド、`[absolute-path]`）で §4 事前検証。pytest 129 passed、§6.1 回帰 PASS、**§6.2 環境 C FAIL**（4 キーすべてで `tp`・`up` 不一致、`flag_stable`・`hops_full`・`events` 一致）。環境 A は未実施。開始条件 c4 を満たさず停止 | 真偽値のみ（差の大きさは未記録） |
| 2026-11-07 | **本書の起草のための原因調査**（開発機）。§6.2 と同じ保存済みキー（部屋 B E-PCG 480、部屋 A holdout E-PCG 800/839 ×2 セル、RLS + det 800）を pyroomacoustics のスレッド数を変えて再実行し、保存記録との相対差を測った。出力は `/tmp` のみで `results/**` には書いていない。性能の比較・集計・新しいシードの実行はしていない | §1 の表の相対差 |
| 同日 | **本書の固定** | — |

- 評価シード 480–519・holdout 800–839 の新しい記録は作っていない。調整（450 run）も未実行。実行担当の preflight も既存記録との照合であり、新しい評価ではない。
- 本書のどの決定も性能値（A1/A2/NR）を根拠にしない。§2 の上限は §1 の相対差の**桁**から決め、実行担当の測定の前に固定する。

## 1. 事象と原因（確定事項と推定を分けて書く）

### 1.1 確定: `up` は pyroomacoustics のスレッド数に依存する
- `pyroomacoustics 0.10.1` の RIR 生成（`simulation/ism.py:225-228` → `libroom.delay_sum`、`rir_builder.cpp:179-252`）は、像音源を `num_threads` 個のブロックに分けて **float32** の部分和バッファに足し、最後にブロック順で合算する。合算の分割がスレッド数で変わるので、RIR が float32 の丸め（相対 ~1e-7）だけ変わる。`fractional_delay` も `num_threads` を受ける。
- `num_threads` の既定は `parameters.py:get_num_threads()`。`OMP_NUM_THREADS`/`MKL_NUM_THREADS` を読む意図のコードが `getattr(os.environ, var, num_cores)` となっており環境変数を読めず、**常に `os.cpu_count()`** になる。唯一効くのは `PRA_NUM_THREADS`（または `pra.constants.set('num_threads', n)`）。Rule 9a・Rule 11 の「1 スレッド/プロセス」（OMP/OpenBLAS/MKL）は pyroomacoustics には及んでいなかった。
- したがって **`up`（無制御パワー、アルゴリズム非依存）は、記録を作った機械の CPU 数で決まる**。`tp` はその `up` の差を入力として受けるので連動して不一致になる。これが実行担当（CPU 数 ≠ 2 と推定）で `up`・`tp` だけが不一致で `events`・`flag_stable`・`hops_full` が一致した事象の説明である。

### 1.2 開発機での測定（2026-11-07、`RLS_FAST=1`、OMP/OpenBLAS/MKL 1 スレッド、`os.cpu_count()` = 2）
| 比較対象（保存記録） | 再実行の環境 | pra スレッド数 | `up` 最大相対差 | `tp` 最大相対差 | events / flag |
|---|---|---|---|---|---|
| `eval_roomB` E-PCG ar1 S8 480（9-C、環境 C、開発機系） | C（3.13.18 / 2.5.3） | **2** | **0（バイト一致）** | 0 | 一致 |
| 同 | C | 1 / 4 / 8 | 8.1e-7 / 3.9e-7 / 4.4e-7 | — | — |
| 同 | A venv（3.12.3 / 2.3.5 / 1.17.0） | 2 | 1.2e-12 | 1.7e-3 | — |
| 同 | A venv | 3 | 5.7e-7 | 2.1e-3 | — |
| `final_eval_holdout` E-PCG ar1 S8 800（9-A、3.12.14 / 2.3.5） | C | 1〜128（3 以外） | 3.5e-8 〜 1.8e-7（2 で 4.05e-8 = `env_A.json` の値） | — | — |
| 同 | C | **3** | 1.1e-12 | 3.2e-3 | 一致 |
| 9-A E-PCG 4 キー（S8 800/839、R3 800/839）＋ RLS + det R3 800 | **A venv、スレッド 3** | **3** | **0（5 キーすべてバイト一致）** | **0** | 一致 |
| 同 4 キー | C、スレッド 3 | 3 | ≤ 1.1e-12 | 1.3e-3 〜 5.5e-2 | 一致 |

### 1.3 結論
- **確定**: 不一致は 2 つの独立な層からなる。
  - **層 T（スレッド分割）**: pra のスレッド数の違い。`up` 相対 **4e-8 〜 1e-6**。スレッド数を記録時の値に合わせれば消える（表の太字）。9-A/9-B の記録は **3**、v2e・8a・9-C/9-D・`det_events/`・`eval_roomB(_x2)` の記録は **2** で作られている（開発機の `cpu_count()` = 2、9-A の機械は 3 と推定され、スレッド 3 で 5 キーがバイト一致したことで裏付けられる）。
  - **層 K（数値カーネル）**: numpy/OpenBLAS の版または CPU のカーネル経路（`np.convolve` は `cblas_ddot`、ufunc の SIMD 経路）。`up` 相対 **~1e-12**、`tp` 相対 1e-3 〜 5e-2（単一 run の軌道の丸め感度。論文補足 S2.1 の「カーネルで A1 最大 1.0 dB」と同じ性質）。events・flag はこの 5 キーで一致。
- **訂正される推定**: Rule 11a §3.1 の「環境 A の不一致は SIMD か Python パッチ版」は誤りで、原因は層 T（9-A の機械が 3 スレッド）である。Rule 9a §1 の「依存ライブラリ版による数値環境ドリフト（相対 1e-6）」も、その大きさは層 T（9-C 追加 run の機械が 3 スレッド）で説明され、版の差は 1e-12 の層 K に相当する。Rule 9a の**決定**（`eval_roomB_x` の不採用、`_x2` の再実行）は `up` の不一致という事実に基づき、そのまま正しい。記録・ラベルは変えない。開示文だけ §6 で改める。
- **扱い**: 実行担当の FAIL は実装・アルゴリズムの異常の兆候ではなく、環境定義の欠落（pra のスレッド数）である。**停止すべき兆候ではない**。ただし実行担当の CPU が開発機と異なるカーネル経路を選ぶ場合は層 K が残り得るので、§2 の判定で扱う。
- 実行担当の `env_C.json`（c09572a）は差の大きさを記録していないため、層 T と層 K の分離は実行担当の環境で §2.3 の再測定により確かめる。

## 2. 判定の置き換え（Rule 11 §6.2・§1.6 の「`up` の不一致」の読み替え）

### 2.1 原則
- [x] **Rule 11 の比較はすべて実行環境の中で閉じる。** 既存記録と**結合**（同じ表・同じ family・同じ `up` 照合）するのは、その記録を作った環境を**完全に**再現できた場合（判定 I）だけ。それ以外は、比較に必要な参照（G0・13 基線・提案法・イベント・既存選択のスコア）を実行環境で作り直し、その中で比べる。既存の数値・ラベル・family は変えない。
- [x] **環境内の決定論は要求し続ける。** 同じ機械・同じ環境での再実行は `tp`・`up`・events ともバイト一致でなければ停止（§2.3 の `repeat`、holdout の同一 run `up` 照合、summary の手法間 `up` 一致検査は従来どおり**許容誤差なし**）。許容誤差を置くのは**環境をまたぐ照合（§6.2）だけ**である。

### 2.2 判定クラス（§6.2 の各環境、全キーについて）
| 判定 | 条件（すべて満たす） | 意味 | 扱い |
|---|---|---|---|
| **I（identical）** | `tp`・`up`・`flag_stable`・`hops_full`・events がバイト一致 | 記録環境を完全再現 | Rule 11 のとおり既存記録と結合できる（環境 A なら経路 A、環境 C なら Rule 11 §1.4 のキャッシュ・§4.2 の記録スコアをそのまま使う） |
| **K（kernel）** | events・`flag_stable`・`hops_full` が全キーで一致、かつ `up` の最大相対差 ≤ **1e-9**（全キー・全 hop）、`tp` は有限 | 層 K だけが残る（層 T は除かれている） | §2.1 の「閉じる」を適用（§4）。`tp` の差は記録するだけで判定に使わない |
| **F（fail）** | 上のいずれでもない | 層 T が残る（スレッド数）、版の違い、乱数列の違い、実装差など | **停止・報告**（Rule 11 §1.6） |
- `up` の上限 1e-9 の根拠（測定前に固定）: §1.2 で層 K は ≤ 1.2e-12、層 T は ≥ 3.5e-8。1e-9 は層 K の最大観測値の約 800 倍上、層 T の最小観測値の約 35 倍下にあり、両者を分ける。相対差は hop ごとの |Δup| / |up_saved| の最大値（`up_saved` は正）。
- `tp` に上限を置かない根拠: 単一 run の `tp` は丸めに敏感で（補足 S2.1: カーネル差で A1 最大 1.0 dB）、上限を置くと「結果を見て上限を調整する」余地が生じる。代わりに K では `tp` を結合に使わず、比較を環境内で閉じる。events の完全一致は要求する（E-PCG の検出がカーネル差で変わるなら、借用イベントの前提が崩れるため。1 件でも違えば F）。
- `pass` の意味: `env_X.json` の `"pass"` は **I のときだけ true**（経路 A の条件は不変）。新しい項目 `"class": "I" | "K" | "F"` を加え、開始条件は class で判定する（§7）。

### 2.3 実行担当の環境で行う測定（§6.2 の再実行。評価シードの新記録は作らない）
| # | 内容 | 出力 |
|---|---|---|
| m1 | `PRA_NUM_THREADS=2` で `envC`（Rule 11 と同じ 4 キー）。各キーに `up`・`tp` の最大相対差・最大絶対差、hop パワーの最大 \|10 log10(tp_new/tp_saved)\| dB、events の差分（個数・最初の不一致）を記録 | `env_C.json`（class） |
| m2 | `PRA_NUM_THREADS=3`、環境 A の venv で `envA`（4 ＋ 1 キー）。python3.12 が無ければ実施せず、`env_A.json` を**作らない**（§5） | `env_A.json`（class） |
| m3 | `repeat`: 環境 C で E-PCG 1 キー（部屋 B ar1 S8 480）を別プロセスで 2 回実行し、全決定論的返却値がバイト一致 | `repeat.md`（FAIL なら停止） |
| m4 | 機械の指紋: CPU モデル名（`/proc/cpuinfo`）、`os.cpu_count()`、`PRA_NUM_THREADS` と `pra.constants.get('num_threads')`、OpenBLAS のコア名（`threadpoolctl.threadpool_info()` の `architecture`、無ければ ctypes で `openblas_get_corename`）、Python の完全な版、`numpy.show_config()` の OpenBLAS 文字列 | `env_*.json` の `machine`、各 `provenance.json` |
| m5 | K のときだけ: `up` の差がどこから来るかを 1 キーで特定する `localize`（部屋 B ar1 S8 480 の seed 480）: 参照信号 x（乱数列）、RIR p/s（pra）、`np.convolve` 後の d、`up` の各段で、開発機が commit する参照値（`results/r11_preflight/ref_localize_roomB_ar1_S8_480.npz`、§7 R-2）との最大相対差を記す。判定には使わず、報告と開示（§6）に使う | `localize.md` |
- 実行担当の c09572a の `env_C.json` は履歴に残す（上書きされるが commit で参照できる。[run guide] §4 の「再生成して commit」のとおり）。

## 3. 実行環境の定義の訂正（Rule 11 §1.2 に加える）
| 環境 | 版（不変） | **pra スレッド数（本書で追加）** | 記録との対応 |
|---|---|---|---|
| A | Python 3.12.x / numpy 2.3.5 / scipy 1.17.0 / pyroomacoustics 0.10.1 | **`PRA_NUM_THREADS=3`** | 9-A/9-B（`final_eval_holdout/`、`protocol_v2_sel_cusum/`） |
| C | Python 3.13.x / numpy 2.5.3 / scipy 1.18.1 / pyroomacoustics 0.10.1 | **`PRA_NUM_THREADS=2`** | v2e、8a、9-C/9-D、`det_events/`、`eval_roomB_x2`、`protocol_v2_sel/` |
- `check_env` は `pra.constants.get('num_threads')` が上の値であることを検査する（環境変数だけでは不十分。`os.cpu_count()` の既定に戻る経路を塞ぐ）。pipeline はワーカーの環境変数に `PRA_NUM_THREADS` を環境ごとに付ける。
- スレッド数は数値の分割順序だけを決める（計算量・結果の意味は変えない）。「1 スレッド/プロセス」の規則は OMP/OpenBLAS/MKL について不変で、pra の 2 または 3 スレッドは RIR 生成の数十 ms に限られる。
- Rule 11 §1.2 の「Python 3.13.18」は Rule 11a 追記のとおり major.minor で検査（不変）。

## 4. 原則で影響を受ける箇所と対処（判定が K のとき。I なら Rule 11・11a のまま）

| # | 箇所 | Rule 11 の前提 | K での対処 | 追加計算（1 プロセス） |
|---|---|---|---|---|
| (a) | 部屋 A holdout（11-A の G0、11-B/11-C の F1 の比較対象、`up` 照合、イベント） | 経路 (b): B0 で 15 手法を環境 C で再実行 | **既に閉じている**（Rule 11a §3.1）。B0 の E-PCG が同じ環境で events・`up` を作る。変更なし | 0（B0 約 4 h は既定） |
| (b) | 11-C 外側グリッドの判定（Rule 11 §4.2、`revision11_select.outer_decision`）: 新スコアを `selection_e.md` の記録値（2 桁）・CUSUM の `selected.json` と比べ、0.01 dB で同値 | 記録スコアが環境 C の値である | **既存選択の構成を同じ環境で再実行し、その環境内スコアを参照にする**。group 名 `"<基線名> [reference]"`、構成は `BASE13[<基線名>]`（不変）、450 run、スコア定義は Rule 11 §1.4。判定規則（失敗／内点／0.01 dB 超良い／2 段目）は不変で、参照だけ記録値 → 環境内再実行値に置き換える。記録値も `selection.md` に併記し、再実行値との差を開示する | RLS 1.1 h、VFF-RLS 1.3 h、SFTF-H + det 0.5 h、RLS + CUSUM 1.1 h、FD 系 4 基線 計 0.2 h → **約 4.2 h（2 プロセス約 2.1 h）** |
| (b′) | 同、**RLS + CUSUM の参照** | 記録値は 9-B（環境 A 系: numpy 2.3.5、スレッド 3）のもので、I でも環境 C の値ではない | **I でも K でも再実行する**（1 基線だけ）。他 7 基線の記録値は v2（numpy 2.5.x、スレッド 2 = 環境 C 系）なので I ではそのまま | I: 約 1.1 h（2 プロセス約 0.6 h） |
| (c) | 調整用の借用イベント（`results/det_events/` キャッシュ、Rule 11 §1.4） | キャッシュは環境 C の E-PCG main の出力 | **同じ環境で作り直す**: 段 E0 として E-PCG main を調整 450 キーで実行し `protocol_r11_sel/det_events_env_{0,1}.jsonl` に保存。以後の調整（新基線、(b) の参照、2 段目）はこれを使い、キャッシュは読まない。キャッシュとの events 不一致キー数を `selection.md` に記す（記述）。理由: Rule 11 §1.4「同じ run の E-PCG main のイベント」の意味を環境内で満たし、RLS + det (cond.) の P_pre/P_post など hop 単位の量と同じ run に揃える | 450 × 約 0.5 s ≈ **4 分** |
| (d) | 11-D の like-for-like（Rule 11 §5.3: 480–519 の既存ラベルとの一致数） | 既存ラベルは別環境・別シード | **記述として残す**（変更なし）。シード集合が独立で対にしないため、環境差はシード差に埋もれる。報告に「環境が異なる（表 §6）」を 1 行加える | 0 |
| (e) | M-S/M-P の Rule 8a 部分（MeshRIR の MD5・割当・`path_provenance` の照合、Wiener 下限） | MeshRIR は実測データで pra を使わない | `up` は `np.convolve`（層 K ~1e-12）だけに依存し、新シードで結合しない。照合は MD5・割当・形状（浮動小数点ではない）で不変。Wiener 下限は環境内で再計算（Rule 11 のとおり）。**変更なし** | 0 |
| (f1) | §6.1 回帰、§6.3 同値性、§6.4 smoke | 環境内の新旧比較 | 変更なし（実行担当の環境で再生成、c3・c6・c7） | 0 |
| (f2) | 経路 (b) の 15 手法の参考ラベル（Rule 11a §3.1: 2 × 15 × 13 の Holm を再計算し 390 族との一致数） | — | 変更なし。報告に層 K の有無を添える | 0 |
| (f3) | 11-D の部屋 B/C/SNR10/M-S/M-P の新記録 | 新シード、結合なし | 変更なし（環境内で E-PCG → events → 他手法、`up` の環境内一致は許容誤差なし） | 0 |
| (f4) | MFBLMS の端の延長（Rule 11a §5.2）、SW-FBLMS の μ_M | 新グリッド内の比較 | 変更なし | 0 |
| 計 | | | **K: 約 4.3 h（2 プロセス約 2.2 h）。I: 約 1.1 h（約 0.6 h）** | |

- C 段の実行順（Rule 11a §5.3 を補う）: **E0（K のみ）→ 必須（RLS cond. 4、growth 2 版、外側 RLS・VFF・SFTF-H）→ 任意（CUSUM K64 × 3、FD 系 5）→ 参照（RLS + CUSUM は常に、他 7 は K のみ）→ 発動した 2 段目**。参照は 2 段目の判定にだけ必要なので、必須部分の後に置く。
- (b) の判定で「参照の再実行が失敗（admissible でない）」になった場合: 既存選択は v2 の admissibility を満たしていたので、同じ環境で失敗するなら層 K を超える差であり、**停止・報告**（Rule 11 §1.6 の「環境不一致」）。

## 5. 環境 A と経路の決め方（Rule 11a §3.1・§3.3 c5 の改定）
- [x] 経路の規則は不変: **実行担当の環境で `envA` が I のときだけ経路 A**、それ以外は経路 (b)。環境 A は `PRA_NUM_THREADS=3` で測る（§3）。開発機では環境 A がスレッド 3 で 5 キーともバイト一致したので、実行担当の CPU が同じカーネル経路なら経路 A が成立し、390 族の記録そのものと結合できる（比較の強さが増す）。成立しなければ (b)。試す費用は venv ＋ 5 キー ≈ 2 分。
- [x] **`env_A.json`・`env_C.json` は実行する機械で作ったものに限る。** `machine`（§2.3 m4）が現在の機械と一致しない `env_*.json` は無効: `env_C.json` が無効なら停止（c4）、`env_A.json` が無効または無ければ経路 (b)（c5）。Rule 11a §3.3 c5・[run guide] の「python3.12 が無ければコミット済み `env_A.json` のまま (b)」は、開発機の再測定（§7 R-8、PASS が見込まれる）後に別の機械で誤って経路 A を選ぶ危険があるため、この規則で置き換える。
- [x] 経路 (b) を**固定はしない**（機械的に決める）。ただし実行担当の `envC` が K なら、同じ CPU の `envA` も K 以下になるので、実質 (b) になる。

## 6. 開示（論文・補足・provenance）
| 場所 | 内容 |
|---|---|
| 補足 S2.1（Numerical reproducibility and BLAS sensitivity） | 1 段落追加: pyroomacoustics 0.10.1 の RIR 生成は float32 で、像音源をスレッド数のブロックに分けて部分和を取る。スレッド数の既定は CPU 数で（`OMP_NUM_THREADS` は効かない）、記録セットは 2（v2e、8a、9-C、9-D、Rule 11 の調整・11-D）または 3（9-A、9-B）で作られた。スレッド数が異なると無制御パワーが相対 1e-7 〜 1e-6 変わり、numpy の版が異なると 1e-12 変わる。前者は `PRA_NUM_THREADS` を記録値に合わせれば消える。Rule 9a の「版による差 1e-6」はスレッド数の差であったと訂正する（記録・判定は不変） |
| 補足の環境表（Rule 9a §4 の表、`supp_tables/r9_environment`） | 列「pra threads」を加え、各セットの値（2／3）と、Rule 11 の各出力（経路、class I/K、機械の指紋の要約: CPU モデル・OpenBLAS コア名）を 1 行ずつ |
| 本文 Protocol（Rule 11a §3.1 の 1 文に接続） | "The revision-11 comparisons were run in one numerical environment and compared only against records produced in it (Section S2.1)." K のときは "the uncontrolled power of the saved records was reproduced to 1e-9 relative; the controlled power was not reproduced bit for bit and was regenerated" を補足に |
| `provenance.json`（全出力） | `rule11b_sha256`、`machine`（§2.3 m4）、`pra_threads`、`env_class`（I/K、`env_C.json` から）、`tuning_events_source`（`cache`／`env`）、`outer_reference`（`recorded`／`rerun`、基線ごと） |
| `selection.md` | 外側点の表に「記録スコア／環境内再実行スコア／差」の 3 列、E0 のキャッシュ不一致キー数 |
| [internal records] | 「実行時は `RLS_FAST=1`、1 スレッド/プロセス」に「`PRA_NUM_THREADS` は記録セットの値（A 系 3、C 系 2）」を加え、「numpy の版が違うと bit 再現しない」に「pra のスレッド数が違っても再現しない（1e-7 級）」を加える |
| Zenodo v1.2.0 の README | 上の環境表と同じ内容 |

## 7. コード修正の要求一覧（本書の固定後、本実行の前。既定経路は変えない。各修正を commit・push）

| # | 対象 | 修正 | 確認 |
|---|---|---|---|
| R-1 | `revision11_methods.py` `ENVS`・`check_env`・`check_runtime_env`、`revision11_pipeline.py`（ワーカーの環境変数） | `ENVS['A']['pra_threads'] = 3`、`ENVS['C']['pra_threads'] = 2`。`check_env` は `import pyroomacoustics as pra; pra.constants.get('num_threads') == pra_threads` と `os.environ.get('PRA_NUM_THREADS') == str(pra_threads)` の両方を検査。pipeline は `check-env … job` とワーカー起動のシェルに `export PRA_NUM_THREADS=<値>` を環境ごとに付ける。`revision11_preflight.py` の `envA`/`envC`/`equiv`/`smoke` も `check_runtime_env(env)` で同じ検査 | 単体テスト: `PRA_NUM_THREADS` 不一致で `RuntimeError`。`check-env C` が `OK` に `pra threads 2` を出す |
| R-2 | `revision11_preflight.py` `_compare`・`envA`・`envC`、新サブコマンド `repeat`・`localize`・`ref-localize` | `_compare` が真偽値に加え `up_max_rel`・`up_max_abs`・`tp_max_rel`・`tp_max_abs`・`tp_max_db`、`events_diff`（個数と最初の不一致）を返す。`env_*.json` に `class`（§2.2: I/K/F。`up` 上限 1e-9 は定数 `UP_REL_TOL = 1e-9`）、`pass`（I のみ true）、`machine`（§2.3 m4）を加える。`repeat`: 部屋 B ar1 S8 480 の E-PCG を 2 プロセスで実行しバイト一致 → `repeat.md`。`ref-localize`（開発機で 1 回実行し commit）: 同キーの x・p・s・d・`up` を `ref_localize_roomB_ar1_S8_480.npz` に保存。`localize`（実行担当、K のとき）: 同じ量を計算し参照との最大相対差を段ごとに `localize.md` へ | 単体テスト: 合成配列で I/K/F の分類（`up` 相対 1e-12 → K、1e-8 → F、events 1 件違い → F、完全一致 → I）。開発機で `envA`（スレッド 3）・`envC`（スレッド 2）が I |
| R-3 | `revision11_methods.check_holdout_base`、`revision11_pipeline.py` | `env_A.json`・`env_C.json` の `machine` を現在の機械の指紋と比較。`env_C.json` が無い／指紋不一致／class F → 停止（`STOP: env_C.json … run envC on this machine`）。`env_A.json` が無い／指紋不一致／class ≠ I → 経路 (b)。`R11_HOLDOUT_BASE` との整合検査は従来どおり | 単体テスト: 指紋の違う `env_A.json`（pass true）でも `want == 'envC'` |
| R-4 | `revision11_methods.py`（`RULE11B_SHA256`、`check_rules`、`provenance_dict`） | 定数 `RULE11B = docs/current/REVISION_RULE_11b.md`、`RULE11B_SHA256`（固定 commit 後に転記）。`check_rules` が 11・11a・11b の 3 件を照合。`provenance_dict` に §6 の項目（`rule11b_sha256`、`machine`、`pra_threads`、`env_class`、`tuning_events_source`、`outer_reference`）を加える | 転記値の一致。pipeline の空実行で照合が働く |
| R-5 | `revision11_select.py`（`stage_cfgs`、`run`、`outer_decision`、`summary`）、`revision11_methods.tuning_events` | (i) 段 **E0**（`env_C.json` の class が K のとき `select C` の冒頭で実行。I なら run なし）: 調整 450 キーの E-PCG main を shard 2 分割で実行し `det_events_env_{shard}.jsonl` に保存。`tuning_events(source='env')` はこのファイルだけを読む（`results/det_events/` は読まない）。K のとき以後の調整はすべて `source='env'`。`selection.md` にキャッシュとの events 不一致キー数と一覧。(ii) group `"<基線名> [reference]"`（構成 `BASE13[<基線名>]`、`EXISTING_SCORE` の 8 基線）を C 段の「任意」の後に置く。RLS + CUSUM は I でも K でも実行、他 7 基線は K のみ。(iii) `outer_decision` の `ref` を、参照 group が存在すればその環境内スコア、無ければ `EXISTING_SCORE`（I の 7 基線）とし、両方と `reference_source` を dict に出す。参照が失敗なら例外（§4 最終項の停止）。TOL・判定の分岐は不変 | 単体テスト: 合成記録で (a) K・参照あり → 参照値で判定、記録値も出力、(b) I・CUSUM 参照のみ、(c) 参照が失敗 → 例外、(d) `tuning_events('env')` がキャッシュを読まない。Rule 11a L-9 の `outer_decision` テストは `EXISTING_SCORE` 経路として維持 |
| R-6 | [run guide] §0・§2・§3・§4・§5・§7、[internal records] | §3: 環境 C に `export PRA_NUM_THREADS=2`、venvA の実行に `PRA_NUM_THREADS=3`、`pip install threadpoolctl`（指紋用。無くても ctypes で代替）。§4: `envC`・`envA`・`repeat`（・K なら `localize`）。§2: c4 を「`env_C.json` が**この機械**で作られ class ∈ {I, K}（`repeat.md` PASS）」、c5 を「`env_A.json` がこの機械で class I → 経路 A、それ以外 → (b)」に置き換え、c9「`RULE11B_SHA256` の一致」を加える。§5: C 段の順序に E0 と参照を加える。§6: 停止条件に「`env_C.json` class F」「`repeat` FAIL」「参照 group の失敗」。§7: `rule11b_sha256`・`machine`・`env_class`・`outer_reference` の確認。[internal records] に `PRA_NUM_THREADS` の 1 行と本書の固定と sha256 を 1 行 | 手順書の記述、sha256 の転記 |
| R-7 | `tests/test_revision11.py` | R-1〜R-5 の単体テスト（上の各行）。加えて pra の既定スレッド数が `os.cpu_count()` になること（`OMP_NUM_THREADS=1` でも）を**前提の確認**として 1 件（将来の pra 更新で挙動が変われば気づけるように） | pytest 全件 PASS |
| R-8 | 開発機での再検証 | 修正後に `envA`（`PRA_NUM_THREADS=3`、venvA）と `envC`（`PRA_NUM_THREADS=2`）を再実行し、両方 I を確認して `results/r11_preflight/` を更新・commit（`ref_localize_*.npz`、`repeat.md` を含む）。§6.1 回帰・§6.3・§6.4 は環境内比較なので再生成は任意（`PRA_NUM_THREADS=2` を付けて再生成し、バイト一致を確認するのが望ましい） | `env_A.json`・`env_C.json` とも `"class": "I"` |
| R-9 | 内部の差分レビュー | R-1〜R-7 の差分。ブロッカーなしで実行担当に渡す | [internal review record] |

- 修正はすべて環境検査・preflight の記録・選択の参照の切り替え・手順書であり、手法・グリッド・閾値・family・既存 `results/**`・`eval_v2.GRID`・`selected_e.json` には触れない。E0 と参照 group は Rule 11 の出力ディレクトリ `protocol_r11_sel/` にだけ書く。
- 本書の固定後は、本書に書いていない変更を本実行の前に加えない。必要なら Rule 11c。

## 8. 実行担当の開始条件（Rule 11a §3.3 の c1–c8 を次のとおり改める。[run guide] §2 に転記）
| # | 条件 | 変更 |
|---|---|---|
| c1 | Rule 11a の sha256 一致 | 不変 |
| c2 | pytest 全件 PASS（R-7 を含む） | 件数更新 |
| c3 | `regression.md` PASS | 不変 |
| **c4** | `env_C.json` が**この機械**で `PRA_NUM_THREADS=2` により作られ（`machine` 一致）、`class` ∈ {I, K}。`repeat.md` が PASS。K のときは `localize.md` がある | 置き換え |
| **c5** | `env_A.json` がこの機械で `PRA_NUM_THREADS=3` により作られ `class` I → 経路 A。無い／指紋不一致／I でない → 経路 (b)（`export R11_HOLDOUT_BASE=envC`） | 置き換え |
| c6 | `equivalence.md` PASS | 不変 |
| c7 | `smoke.md` PASS（s1/s3/s4） | 不変 |
| c8 | pipeline が各ジョブ開始時に c1・c9 と環境（pra スレッド数を含む）と経路を検査 | 拡張 |
| **c9** | 本書 `docs/current/REVISION_RULE_11b.md` の sha256 が [run guide] §2 と `revision11_methods.RULE11B_SHA256` に一致 | 追加 |

## 9. 予算の改定（Rule 11a §7 に加える）
| 項目 | 追加（2 プロセス） |
|---|---|
| §2.3 の測定（m1–m5） | 約 5 分 |
| (b′) RLS + CUSUM の参照（常に） | 約 0.6 h |
| K のとき: E0 ＋ 他 7 基線の参照 | 約 1.6 h |
| **予算** | **経路 (b)・I: 予測 26–29 h、予算 29–33 h。経路 (b)・K: 予測 27–30 h、予算 30–34 h。経路 A・I: 予測 22–25 h、予算 25–29 h** |
- 予算は停止条件ではない（Rule 11a §7）。

## 10. 固定後のチェックリスト
- [ ] 本書を commit（sha256 を [run guide] §2・§7、[internal records]、`revision11_methods.RULE11B_SHA256` に転記）
- [ ] R-1〜R-7 → pytest → R-8（開発機で `envA`・`envC` とも I、`ref_localize` と `repeat.md` を commit）→ R-9 内部の差分レビュー
- [ ] 実行担当: §3 環境構築（`PRA_NUM_THREADS`）→ §4（`regress`、`envC`、`envA`、`repeat`、`equiv`、`smoke`、K なら `localize`）→ c1–c9 → 経路決定 → B0（(b) のみ）→ 11-A → B1 → B2 → C（E0 → 必須 → 任意 → 参照 → 2 段目）→ holdout new → 11-D
- [ ] 集約: Rule 11a §9 の項目に加え、`selection.md` の参照列、E0 の不一致キー数、`localize.md`、環境表（pra threads・class・機械の指紋）、補足 S2.1 の段落、Rule 9a の開示の訂正
- [ ] **結果を見てからの取捨選択（著者）**: Rule 11 §1.7 の基準で本文に載せる場所を決める。数値・ラベル・family は変えない
