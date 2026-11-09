# Revision 11: 査読（2026-11-07）への追加実験の判定ルール

**固定版（2026-11-07 06:19 JST に著者が了承。§9 の決定を参照）。** [provenance note omitted] 本版の固定前に実装・調整・評価・性能 smoke は行わない（Rule 9 §「Order, runtime and stop」と同じ）。

- 作成: 2026-11-07 JST、[provenance note omitted]。対象ブランチ `[development branch]`（HEAD b3058bf）。
- 根拠: 査読（2026-11-07）の M3(a)(b)、S1、S2、S3 [internal review documents omitted]。著者の決定（2026-11-07）: 4 件すべて実施し、**結果を見てから本文に載せるものを取捨選択する。全結果は補足／Zenodo に報告し、取捨選択は本文に載せる場所だけに使う。**
- 本書で「変えないもの」: 既存の手法・設定（`selected_e.json` の 12 基線、RLS + CUSUM index 3、`final_config_core_{main,final}.json`）、既存の数値・ラベル・Holm family（390 族 139/195、360 族 350/360、部屋 B/C 160、SNR10 80、M-S 48）、既存の `results/**`、ルール文書、Zenodo の生データ。新しい結果は新しいディレクトリへ。新しい挙動は新しいフラグの後ろに置き、既定値は変えない。

## 0. 概要（4 件 → 4 サブルール）

| 子番号 | 査読 | 内容 | 新規実装 | 計算（2 プロセス理想） | 担当 |
|---|---|---|---|---|---|
| 11-A | M3(b) | PCG-WLS の制御器次数成長オフ（`grow_len` None）ほかアブレーション変種を holdout 800–839・部屋 A で評価。既存アブレーションと合わせた分離表 | フラグ追加なし（既存フラグの値だけ） | 約 0.2 h（任意の RLS + det + growth を含めて約 1 h） | 実装担当 |
| 11-B | M3(a) | 新基線: MFBLMS [31]、切替 FD 法 [6]（自前検出／共有検出の 2 版）。既存と同じ調整手順・予算・admissibility | `mod`（fixed_binwise）、新 method `SW-FBLMS` | 約 0.6 h | 調整＝実装担当、holdout＝実装担当 |
| 11-C | S1, S2 | RLS 系の端の外側グリッド確認（RLS λ、VFF N0、SFTF-H Th、任意: CUSUM K）と条件付き再始動 RLS（`det_cond_db`）。任意: RLS + det + 次数成長 | `det_cond_db`/`det_cond_k`、任意 `det_grow` | 約 2.6 h（任意込み約 4 h） | 実行担当 |
| 11-D | S3 | 部屋 B/C・SNR10・実測 M-S を holdout 800–839 で、全基線（13 ＋ 11-B/11-C の新基線）について再評価 | 新パイプライン（MeshRIR 抽出の一般化） | 約 7.6 h（予算 9–12 h） | 実行担当 |

実行順序: 固定 → 実装・回帰・smoke（§6）→ 11-A → 11-B 調整 → 11-C 調整 → 11-B/11-C の部屋 A holdout → 11-D → 集約。11-D は 11-B/11-C の選択が確定してから（新基線を含めるため）。

## 1. 共通規則

### 1.1 シード（`PROTOCOL_SEEDS.md`、Rule 9）
| 用途 | シード | 本ルールでの使用 |
|---|---|---|
| 調整・admissibility | 300–309 ＋ 600–619（30） | 11-B、11-C の選択。11-A はパラメータを持たないので調整しない |
| smoke test | **300 のみ** | §6。評価・判定には使わない |
| 評価 480–519 | — | **本ルールでは一切使わない**（新しい記録を作らない） |
| holdout 800–839（40） | 11-A、11-B/11-C の部屋 A 評価、11-D | 既存 holdout 記録（`results/final_eval_holdout/`）は読み取りのみ |

### 1.2 実行環境（Rule 9a）
| 環境 | 版 | 用途 | 事前検証 |
|---|---|---|---|
| 環境 A | Python 3.12.x（venv）/ numpy 2.3.5 / scipy 1.17.0 / pyroomacoustics 0.10.1 | 部屋 A holdout と結合するもの（11-A、11-B/11-C の部屋 A 評価）。既存 holdout（9-A/9-B）は 3.12.14 / 2.3.5 / 1.17.0 | §6.2: E-PCG main を 4 キー（COMBOS15 の先頭・末尾 × seed 800・839）再実行し、保存済み `tp`/`up`/`flag_stable`/イベント列とバイト一致。1 件でも不一致なら停止・報告（§9 項目 8 の fallback は著者判断） |
| 環境 C | Python 3.13.18 / numpy 2.5.3 / scipy 1.18.1 / pyroomacoustics 0.10.1（開発機の既定。pyroomacoustics は未インストール） | 11-B/11-C の調整（既存の v2 選択は numpy 2.5.x）、11-D（新規評価で既存記録と結合しない） | §6.2: `eval_roomB_x2` の E-PCG 4 キー（Rule 9a と同じ）を再実行しバイト一致 |
- 共通: `RLS_FAST=1`、OMP/OpenBLAS/MKL とも 1 スレッド/プロセス、最大 2 プロセス、`setsid nohup`、ログはファイルへ。provenance.json に commit、本ルールの sha256、Python/numpy/scipy/pyroomacoustics の版、スレッド設定、`git status --porcelain`、実行スクリプトの sha256 を記録。
- numpy 2.3.5 / scipy 1.17.0 の cp313 wheel が取得できることは確認済み（2026-11-07）。環境 A は Python 3.12（`/usr/bin/python3.12` あり）または 3.13 の venv で作り、§6.2 の一致で可否を決める。

### 1.3 指標・検定・ラベル（`FINAL_EVAL_RULE.md`、`final_eval.py`。不変）
- 失敗: S8 は `strict_div.evaluate(th=0)`、他は `evaluate_div`。失敗 run は A1 = A2 = 0 dB、τ = 4 s。早期停止 run は無制御で補完（部屋 C の `uncontrolled_fill` 方式を含む）。
- A1/A2: 合計パワーの 10 log10。変化セルは hop ceil(1.0 fs/H) から 32 hop（S5/R3 は ceil(1.6 fs/H) まで）、A2 はその後から末尾。S8 は A1 先頭 32 hop、A2 末尾 62 hop。
- 対検定: シードで対にした両側 Wilcoxon（Pratt、全零は p = 1）。Holm 調整 p < 0.05。中央値 d = 提案 − 基線。win: dA1 ≤ −1 dB または dA2 ≤ −0.5 dB でその指標が有意。loss: ≥ +1 / +0.5 dB。両方 mixed、どちらも無ければ '-'（no decision、同等ではない）。
- Holm family は子ルールごとに §2–§5 で定義する。**既存 family（390、360、160、80、48）は再計算しない。**
- 加えて記述統計として、対差の中央値と Hodges–Lehmann 推定（対差の Walsh 平均の中央値）＋95 % CI（シード bootstrap 10 000 回、乱数 seed 0）を各セルに付ける。判定には使わない（照合 A の M2 対応と共用）。

### 1.4 調整（11-B、11-C。`REVISION_RULE.md` §2、Rule 9-B と同じ）
- データ: 部屋 A、15 セル × 調整シード 30 = 450 run/構成。admissible ⇔ 失敗 0。最初の失敗で早期打ち切り可。
- スコア: 15 セルの「30 シード平均の (A1 + A2)/2」の平均。最小を選択。スコアの厳密同値は最小 index。
- 同じ予算: 新基線のグリッドは 4–8 構成（既存基線は 2–8 構成）。入力不完全・admissible なし → 停止・報告。「admissible な構成なし」は手法として報告し評価しない（`REVISION_RULE.md` 修正 M6 と同じ）。
- 検出器付き基線（`+ det`）は、同じ run の E-PCG main（`final_config_core_main.json`、不変）のイベント `[[stop, tau], …]` を消費する。部屋 A holdout は `results/final_eval_holdout/det_events_{0,1}.jsonl`、調整は `results/det_events/`（既存キャッシュ、読み取りのみ。無いキーは 11 の出力先に新規作成し、既存キャッシュへは書かない）。

### 1.5 出力（すべて新規。既存ディレクトリへは書かない）
| 出力先 | 内容 |
|---|---|
| `results/r11_preflight/` | §6 の環境検証・回帰・smoke（seed 300 のみ）の記録 |
| `results/r11_ablation_holdout/` | 11-A の run・metrics・summary |
| `results/protocol_r11_sel/` | 11-B/11-C の調整 run、`selection.md`、`selected.json` |
| `results/final_eval_holdout_r11/` | 11-B/11-C の新基線の部屋 A holdout 記録、`metrics.jsonl`、summary（`final_eval_holdout/` の基線・提案法の記録を読み取りで結合） |
| `results/eval_roomB_h/`、`eval_roomC_h/`、`eval_snr10_h/`、`final_eval_meas_s_h/` | 11-D（各セット 1 ジョブ、同一ディレクトリ内に `det_events*.jsonl`） |
| `experiments/revision11_*.py` | `methods`（GRID11・変種定義）、`select`、`holdout`、`rooms`、`meas`、`summary`、`preflight`、`pipeline` |
- 新しいフラグは `experiments/prototype_new_algorithms.py` と `src/ffanc_norm/fd_fxnlms.py` に、既定値（フラグ無し）で既存経路と同一になるように追加する。`eval_v2.GRID`・`selected_e.json` は編集しない（GRID11 は新モジュールに置く）。
- 変更ごとに commit・push。

### 1.6 停止条件（共通）
非有限値・実装エラー・環境不一致（§1.2）・イベント欠落・`up` の不一致・調整の未完了・admissible 構成なし・MeshRIR の検証失敗、のいずれかで停止して報告する。結果を見てから手法・設定・グリッド・閾値・family・ルールを変えない。問題の修正は Rule 11a 以降として別途固定する（Rule 9a と同じ扱い）。

### 1.7 報告と「取捨選択」の規則（結果を見る前に固定）
1. **全結果を報告する。** すべての summary・表は補足（圧縮版は索引表で `results/` を案内）と Zenodo（新版 v1.2.0 を作るかは §9 項目 9）に載せる。
2. **取捨選択は本文に載せる場所だけ**に関わる。基準:
   - Must に直接答えるもの（11-A の G1、11-B の新基線）は、**結果の向きにかかわらず本文**に載せる（Tables II/III の行、アブレーション表の行）。
   - Should に答えるもの（11-C、11-D）は本文に数値付きで 1–3 文、表は補足。11-D の holdout 表で Tables V–VIII を差し替えるかは著者判断（§9 項目 7）。
3. **既存の主結果の定義は変えない。** 「139 of 195 better, 0 worse」は 390 族の数のまま、本文では "against the 13 prespecified baselines" を付し、新基線の family の数（§3.5）を同じ文か次の文に併記する。
4. **結果別の書き方は §7 に固定する。** 新基線が PCG-WLS より良いセル（loss）があれば、そのまま報告し、要旨・結論の該当文を §7 の文で制限する。

## 2. 11-A: 制御器次数成長オフのアブレーション（M3(b)）

### 2.1 目的
査読 M3(b)「S8/S7 の勝ちは主に n/2 の次数成長による（補足 S9 の自認）が、分離したアブレーションがない」に答える。`grow_len` を外した PCG-WLS を同じ holdout シード・同じ 13 基線に対して評価し、次数成長の寄与を分離する。あわせて主手法（単一窓）について、ソルバ／検出器／次数成長／Stein 重みの寄与を 1 表に並べられるようにする。

### 2.2 既存のアブレーションと不足（読み取り結果）
| 軸 | 既存の結果（調整シード、`results/ablation_core_*`） | 設定 | 不足 |
|---|---|---|---|
| 検出器 | W5（C1 −detection: S7 ΔA1 +6.2 dB 等） | 多窓 C1 | 単一窓（主手法）版なし。holdout 版なし |
| Stein 重み | W4（C1 restart、≈0）、W6 vs W3（単一窓 restart、A1 最大 +0.6/+0.7 dB） | C1 / 単一窓（kd 16、det_C_pre なし） | 主手法そのまま（det_C_pre 付き）の版なし。holdout 版なし |
| 窓長 L | set d（L 24/96/192） | 主手法 | — |
| det_C_pre | set d（X2 vs Y0） | 主手法 | — |
| **次数成長** | **なし**（`grow_len` を外した変種は未実行） | — | **本ルールで追加** |
| ソルバ | `gap_check*`（S8、厳密 LS との差）、`cg_ratio`（CG 誤差比） | 診断のみ | 全 run 変種なし（任意 G5） |

### 2.3 変種（主手法 `final_config_core_main.json` の flags を基に、記載の 1–2 項目だけ変える）
| 記号 | 名称（論文表記案） | 変更 | 必須／任意 |
|---|---|---|---|
| G0 | PCG-WLS（主手法） | なし（`final_eval_holdout/` の記録を読む。再実行しない） | 参照 |
| **G1** | PCG-WLS (fixed order) | `grow_len` を削除（None）。他は不変 | **必須（M3(b)）** |
| G2 | PCG-WLS (restart, no Stein weight) | `adapt: 'restart'` | 任意（推奨） |
| G3 | PCG-WLS (no detector) | `detect: False`（`localize` は無効化される） | 任意（推奨） |
| G4 | PCG-WLS (fixed order, restart) | G1 ＋ G2 | 任意（推奨: 「借用検出なしの素朴な再始動」に最も近く、RLS + det との差をソルバ・窓の差に絞る） |
| G5 | PCG-WLS (exact window LS) | 窓 LS を直接解法で厳密に解く（新フラグ `solver: 'exact'`、実装 0.5 日） | 任意（低優先。`gap_check` の表が代替） |
- G1 の挙動の確定事項（コード `epcg.py:148,918-920,1034` から）: `grow_len=None` では n < 2M でも M タップ全体を解く。`cg_stat_mindof='M'` により n − M < M では統計停止則は使われず、固定反復（k_first 16 / k 8）とリッジ 0.001 が未決定領域の解を定める（RLS + det の P0 = I/(δ·mean x_f²·M) と同系の正則化解）。この点は論文に開示する。
- 変種は E-PCG main のイベントを借りず、自前の検出で動く（検出器付き基線のイベントは G0 のまま）。G1–G4 の検出回数・警報時刻は記録して併記する。

### 2.4 評価と判定
- 部屋 A、15 セル、holdout 800–839、各変種 600 run。環境 A（§1.2）。`up` は保存済み holdout 記録とバイト一致でなければ停止。
- Family F2（変種ごと、提案法 = 変種として）:
  - (i) 変種 − G0: 15 セル × {A1, A2} = **30 検定**（Holm）。既存の bank − main 族と同形。報告は中央値・HL・CI・Holm p。「変種が悪い」は d ≥ +1 / +0.5 dB で有意。
  - (ii) 変種 vs 13 基線: 2 × 15 × 13 = **390 検定**（Holm、ラベル win/loss/mixed/'-'）。これは G0 の 390 族とは別の family で、G0 のラベルは変えない。
  - (iii) 記述: 各セルの G1 − RLS + det の対差中央値（(ii) に含まれる）を、G0 − RLS + det（`final_eval_holdout/summary.md` の記録値: S8 −3.02、S7 −5.39 dB 等）と並べる。
- 判定文（§7 に収録）: 「次数成長の寄与」= S8/S7 における (G1 − G0) の A1 中央値。G1 が S8/S7 で RLS + det に対し win を失えば「S8/S7 の優位は次数成長に依存する」と書く。残れば「次数成長を外しても残る」と書く。どちらも数値のまま報告。

### 2.5 計算量・担当
600 run × 0.47 s（holdout 記録の E-PCG `wall_s` 平均）≈ 5 分/変種（1 プロセス）。G1–G4 で約 20 分 → 2 プロセスで約 10 分。G5 は 1 run 約 3 s（512 × 512 の直接解法 × 312 hop）→ 30 分。**実装担当で実行。**

### 2.6 任意: RLS + det に次数成長を与える変種（査読 M3(b) の後半）
- 名称 `RLS + det + growth`、method `R-RLS`、新フラグ `det_grow: 'half'`。再始動（tau）から n < 2M の間、回帰ベクトル u の先頭 m_eff = max(n//2, 1) タップだけを使う（残りは 0。P は M × M のまま。新しいタップは初期 P の δ 正則化のまま入る）。他は選択済み RLS + det（λ 0.9999、δ 0.01、warm）と同一。n ≥ 2M で既存経路に一致。
- 構成 1 つ（グリッドなし）: 調整シードで admissibility のみ（450 run、失敗 0 なら評価）。評価は部屋 A holdout 600 run、family は 11-B/11-C の F1 に合流（§3.5）。計算 450 × 5.3 + 600 × 5.3 ≈ 1.5 h（1 プロセス）→ 約 0.8 h。著者判断（§9 項目 4）。

## 3. 11-B: 新基線 MFBLMS [31] と切替 FD 法 [6]（M3(a)）

### 3.1 目的
査読 M3(a)「変化検出で周波数領域法を切り替える直接の先行法 [6] と、バイアスのない modified FBLMS [31] が基線にない」に答える。既存基線と同じ調整手順・予算・admissibility で加える。

### 3.2 原論文の確認結果（2026-11-07、web 取得）
| 文献 | 取得 | 確認できたこと | 未確認 |
|---|---|---|---|
| [31] Lu, Qiu, Zou, Signal Process. 104, 2014 | 本文は closed access（UTS OPUS はログイン要求） | 要旨のみ: 参照が遅れる／フィルタ長不足で bin 正規化 FBLMS の定常解は偏る。修正法は定常最適を保証 | 式本体 |
| Lu, Chen, Qiu, Signal Process. 132, 2017（収束解析; UTS OPUS の著者版） | 取得（式は文字化け） | 標準形 Eq. (3): w_f(k+1) = w_f(k) + μ **F G_{N,0} F⁻¹ M_f** X_f^H e_f（正規化 → 拘束）。MFBLMS Eq. (6): w_f(k+1) = w_f(k) + μ **M_f F G_{N,0} F⁻¹** X_f^H e_f（拘束 → 正規化）。「差は M_f の位置」。時間域では w(k+1) = w(k) + μ M₁ X^T e、M₁ = 循環行列 F⁻¹ M_f F の左上 N × N ブロック、E[w] → R⁻¹r（Wiener、無条件収束）。追加コストは「FFT/IFFT 1 対」 | M_f の推定法（平滑化）の記述、ステップ上限 |
| [6] Wang, Xue, Lu, Qiu, JASA 146(2), 2019（UTS OPUS の著者版） | 取得（式は文字化け） | NFBLMS（bin 正規化、速いが偏る）と MFBLMS を切り替える。NFBLMS で開始。平滑化した誤差パワー J_m(k)（係数 b = (1 − μ/2)² + μ²/4、正則化 α）の減少量 ΔJ(k) = J_m(k−1) − J_m(k) が閾値 Δ_THR 未満 かつ 切替後 M ブロック以上 → MFBLMS へ。定常追跡量 ζ(k)（Q_{0,N} で重み付けた誤差・参照項の期待値の比。Eq. (17)）が ζ_THR を超え かつ M ブロック以上 → NFBLMS へ。ζ_THR は固定値でなく「短時間 NFBLMS を走らせて得た大きい ζ を ζ_THR とする」。実験: fs 16 kHz、N 1024、ブロック 1024、FFT 2048、音源移動 42 s | **Eq. (16)(17) の式本体、Δ_THR・ζ_THR・M・μ・α の数値（論文に記載なし）** |

### 3.3 MFBLMS の実装（確定案）
- 論文 eq.(fd)・Rule 10a の再帰 A と同じ作用素: 循環相関 c = IFFT(conj(X)·E) の先頭 M ラグだけ残し（N ≥ M + H − 1 なので線形相関に一致）、G = FFT([c, 0])、g = IFFT(G / D_b)[:M]。既存 `fd_block_gradient` は「全 N ラグを正規化してから切る」。実装は `src/ffanc_norm/fd_fxnlms.py` に新関数 `fd_block_gradient_mod`（FFT/IFFT 1 対の追加 = [31] の記述と一致）、`prototype_new_algorithms.py` の `fixed_binwise` 分岐に `params.get('mod')` で分岐。既定（フラグなし）は既存と同一。
- D_b は既存と同じ `PowerTracker`（平滑化 0.8、正則化比 0.001）。[31] の M_f 推定法は未確認なので、この点は「既存 FD-FxNLMS と同じ正規化」と明記する。
- コスト表: `cost.fd_fxnlms(M, H) + 2 fft_flops(N)`（解析値）。
- GRID11 `'MFBLMS': ('fixed_binwise', [{'mu': μ, 'mod': True} for μ in (0.05, 0.1, 0.15, 0.2, 0.25, 0.3)])`（FD-FxNLMS と同じ 6 点・同じ予算）。端の規則は §4.2 と共通（選択値が端なら 1 段外側を追加、最大 2 段。外側が既知の失敗なら追加しない）。
- 任意 `'MFBLMS + det'`（E-PCG のイベントで `det_boost` 再始動、FD-FxNLMS + restart の鏡像、7 構成）: 著者判断（§9 項目 2）。

### 3.4 切替 FD 法 [6] の実装（著者が決める点あり）
論文の式が取得できず閾値も未記載なので、**(Z-A) 論文の記述に忠実な再構成**と **(Z-B) 既存枠組みに合わせた版**を定義し、どちらを（または両方を）実装するかを著者が決める（§9 項目 1）。推奨は Z-C（両方）、最低 Z-B。

共通: 新 method `SW-FBLMS`（`fixed_binwise` と `mod` の 2 本の勾配を同じ w に適用、モードで切替）。μ_N = 選択済み FD-FxNLMS の 0.3、μ_M = 11-B で選択した MFBLMS の μ（**固定。切替パラメータだけを調整**）。開始は N モード。J(k) = 新しい H サンプルの誤差パワー、J_m(k) = b J_m(k−1) + (1 − b) J(k)、b = (1 − μ_N/2)² + μ_N²/4 = 0.745、ΔJ(k) = J_m(k−1) − J_m(k)。N → M の切替: ΔJ(k) < Δ_THR · J_m(k) かつ 切替後 ≥ M_dwell hop。
- **論文との相違（開示する）**: Δ_THR を J_m に対する相対値にする（論文は絶対値、数値未記載。セル間でレベルが違うため）。「ブロック」は本研究の hop（H = 128）。
- Z-A（自前検出、名称 `switching FD-FxNLMS [6]`）: ζ(k) = 平滑化‖Q_{0,N}（M_f X_f^H e_f）‖² / 平滑化‖e_f‖²（正規化勾配の非因果側ラグのエネルギー ÷ 誤差エネルギー、平滑化係数 b）。M モードで ζ(k) > ζ_THR かつ ≥ M_dwell hop → N モード。ζ_THR はフローチャートの再構成: M モードに入ったとき ζ_THR = 0、M_dwell hop 後に短時間（M_dwell hop）N モードを走らせてその ζ の最大値を ζ_THR とし、M モードに戻る。**Eq. (17) の ζ の定義は未確認で、ここは再構成である。著者が原論文で確認してから固定する。**
- Z-B（共有検出、名称 `switching FD-FxNLMS + det`）: M → N の切替を E-PCG main のイベント（stop）で行う（他の `+ det` 基線と同じ「同じ検出器、基線型の応答」）。N → M は ΔJ 規則。ζ は使わない。
- グリッド（Z-A、Z-B とも同じ 6 構成）: Δ_THR ∈ {0.01, 0.03, 0.1} × M_dwell ∈ {4, 8} hop。Z-A の ζ_THR 設定は上の規則で自動（グリッドにしない）。
- MFBLMS に admissible な構成がなければ SW-FBLMS は作れないので停止・報告（著者判断）。
- 検出回数・切替時刻・モード滞在時間を記録に残す（記述）。

### 3.5 評価と family F1（11-B と 11-C の新基線を合わせる）
- 部屋 A、15 セル、holdout 800–839、各新基線 600 run。環境 A。提案法 2 つ（main、bank）と既存 13 基線の記録は `final_eval_holdout/` から読む（再実行しない）。
- Family F1: 提案法ごとに 2 × 15 × n_new 検定（Holm）。n_new = admissible だった新基線行の数（MFBLMS、SW-FBLMS Z-A、SW-FBLMS Z-B、RLS + det (cond.)、任意の RLS + det + growth、§4.2 の外側グリッドの holdout 追加行）。n_new は選択後に確定するが、定義式は本ルールで固定する。
- 390 族は不変。本文では「13 基線の事前登録 family で 139/195、改訂で加えた n_new 基線の family で x/（2·15·n_new）」と併記（§7）。
- 記述: 各新基線の A1/A2 中央値 (Q1, Q3)、失敗数、PCG-WLS との対差中央値・HL・CI、RLS + det との対差。

### 3.6 計算量・担当・工数
| 作業 | run 数 | 1 run | 合計（1 プロセス） |
|---|---|---|---|
| MFBLMS 選択 | 6 × 450 | 0.2 s | 9 分 |
| SW-FBLMS Z-A 選択 | 6 × 450 | 約 0.5 s | 23 分 |
| SW-FBLMS Z-B 選択 | 6 × 450 | 約 0.5 s | 23 分 |
| 部屋 A holdout（3 基線） | 3 × 600 | 約 0.4 s | 12 分 |
| 計 | | | 約 1.1 h → 2 プロセスで約 0.6 h |
実装工数: MFBLMS 0.5 日、SW-FBLMS 1–1.5 日（Z-A の ζ を含む）、単体テスト（`fd_block_gradient_mod` が `gap_check4a.recursion` の再帰 A と乱数フレームで一致）0.25 日。**計算は実装担当で実行。**

## 4. 11-C: RLS 系の外側グリッドと条件付き再始動（S1、S2）

### 4.1 目的
S1「選ばれた値がグリッドの端」、S2「借用検出で常に再始動するため小変化で素の RLS より悪化。変化の大きさで restart/keep を決める RLS を」に答える。

### 4.2 外側グリッドの確認（S1）
| 基線 | 選択値（端） | 既知の外側 | 追加点（本ルール） | 1 run | 450 run |
|---|---|---|---|---|---|
| RLS | λ = 0.9995（下端） | v1 で λ = 0.999 は失敗（ar1 S8 seed 300、`protocol_final_sel/selection.md`、同じ失敗定義） | **λ = 0.9993**（δ 0.01） | 5.3 s | 40 分 |
| VFF-RLS | N0 = 500（下端） | v1 の下端も 500 | **N0 = 250**（λ_min 0.9995、δ 1e-3） | 6.4 s | 48 分 |
| SFTF-H + det | Th = 2048（上端） | Th → ∞ は RLS + det（表にある） | **Th = 4096**（確認用） | 約 2 s | 15 分 |
| RLS + CUSUM | K = 32（上端、h = 5 は内点） | — | 任意: K = 64 × h ∈ {3, 5, 8}（3 構成） | 5.45 s | 3 × 41 分 |
| RLS + det / CFTF + det / SFTF + det | λ 0.9999（{0.9999, 1.0} の内側、1.0 は悪化） | — | 追加なし | | |
| FD 系（FD-FxNLMS μ 0.3、leaky (0.35, 0.01)、FDKF P0 10、FD + det scale 0.0625） | 端 | FD μ ≥ 0.35、leaky μ 0.648 は v1 で失敗 | 任意（各 1.5 分）: FD μ 0.32、leaky (0.35, 0.03)・(0.5, 0.01)、FDKF P0 3、FD + det scale 0.03125 | 0.2 s | 各 1.5 分 |
- 規則（固定）: 追加点を調整シード 450 run で評価（admissibility と同じスコア）。
  - 失敗 → 「選択値は admissible 領域の端」と報告。既存選択は確認済み。
  - admissible かつ スコア ≥ 既存選択のスコア − 0.01 dB → 「内点」と報告。
  - admissible かつ 既存より 0.01 dB 超良い → **既存の選択・表・ラベルは変えない**。その構成を「<基線名> (extended grid)」として部屋 A holdout 600 run で追加評価し、F1（§3.5）に行として加える。さらに 1 段外側（RLS 0.9991、VFF N0 125、Th 8192）を同じ規則で確認（最大 2 段。失敗で停止）。
  - 既存スコアは `protocol_v2_sel/selection_e.md` の記録値（numpy 2.5.x）。環境 C で計算する新スコアとの差 0.01 dB 未満は同値扱い。
- 開示: 11-C の結果にかかわらず、本文 Protocol に「v1 の広いグリッドで次の値が同じ admissibility 規則で失敗した」の 1 文（照合 B の S1 修正案）を入れる。

### 4.3 条件付き再始動 RLS（S2）
- 名称 `RLS + det (cond.)`、method `R-RLS`、新フラグ `det_cond_db`（θ、dB）と `det_cond_k`（K、既定 32）。`det_events` を消費（E-PCG main の検出を借りる。他の `+ det` と同じ）。
- 規則: イベント [stop, tau] を受けた hop で、現在の w による a priori 残差 ε_t = d̂_t + u_tᵀw の [tau, stop) 平均パワー P_post と、tau より前の直近 K hop の a priori 残差パワー（RLS ループで hop ごとに蓄積。CUSUM の q と同じ量、§9-B）の平均 P_pre を比べ、10 log10(P_post / P_pre) ≥ θ なら **選択済み RLS + det と同じ再始動**（P リセット、δ 0.01、warm、[tau, stop) 再生）、未満なら **何もしない（keep）**。θ = −∞ は RLS + det に、θ = +∞ は λ 0.9999 の素の RLS に一致（§6.3 で bit 一致を確認）。
- 固定: λ 0.9999、δ 0.01、warm（選択済み RLS + det と同じ）。グリッド θ ∈ {1, 2, 4, 8} dB（4 構成）。
- 代替案（著者判断、§9 項目 3）: (b) 部分リセット P ← P + β P0（β ∈ {0.1, 0.3, 1.0}）、(c) E-PCG の Stein 推定 D̂（α）をイベントに付けて渡す（イベント記録に 3 列目を追加する新ファイルが必要、E-PCG は bit 一致で再実行）。推奨は上の θ 版（自己完結で、追加情報を借りない）。
- 評価: 部屋 A holdout 600 run → F1 の行。記述: RLS、RLS + det、RLS + CUSUM、RLS + det (cond.) の 4 者のセル別最良と PCG-WLS の対差（照合 B の S2 で求められた「RLS 族の最良との比較」）。

### 4.4 計算量・担当
| 作業 | 合計（1 プロセス） |
|---|---|
| 条件付き RLS 選択 4 × 450 × 5.3 s | 2.65 h |
| 条件付き RLS holdout 600 × 5.3 s | 0.9 h |
| 外側グリッド必須 3 点（RLS、VFF、SFTF-H） | 1.7 h |
| 任意: CUSUM K = 64（3 構成） | 2.0 h |
| 任意: FD 系 5 点 | 8 分 |
| 外側点が良かった場合の holdout 追加（1 行あたり 600 × 5–6 s） | 1.0 h/行 |
| 計（必須） | 5.3 h → 2 プロセスで約 2.6 h |
実装工数: `det_cond_*` 0.5 日、`det_grow` 0.25 日。**実行担当が実行**（調整は 1 ジョブ、holdout は 1 ジョブ）。

## 5. 11-D: 部屋 B/C・SNR10・実測 M-S の holdout 再評価（S3）

### 5.1 目的
S3「不利な条件は開発で使った 480–519 で追加評価扱い。RLS + CUSUM は部屋・実測で未評価」に答える。4 セットを holdout 800–839 で、全基線について新規に評価する。

### 5.2 対象
| セット | 部屋設定（`eval_v2.ROOMS`、不変） | セル | 手法 | 記録数（n_new = 3 のとき） |
|---|---|---|---|---|
| B | RT60 0.15 s、len_p 1200 / len_s 512 | S8, S2, S5, R2 × ar1/harmonic（8） | 13 基線 ＋ n_new ＋ main ＋ bank | 8 × 40 × 18 = 5 760 |
| C | RT60 0.3 s、len_p 2400 / len_s 1024（`uncontrolled_fill` 可） | 同 8 | 同 | 5 760 |
| SNR10 | 部屋 A、センサ SNR 10 dB | S8, S2 × 2（4） | 同 | 2 880 |
| M-S | MeshRIR S32-M441、Rule 8a 前処理（d0 5434、固定 Ŝ）、定常 | S8 × 2（2） | 同 | 1 440 |
- 13 基線 = `selected_e.json` の 12 ＋ RLS + CUSUM（index 3）。n_new = 11-B/11-C で admissible となった新基線（§3.5 と同じ集合。MFBLMS ＋ SW-FBLMS（Z-C なら 2 版）＋ RLS + det (cond.) で 3–4、任意項目で増える）。部屋 B/C/SNR10 の既存評価（12 手法）にはなかった FD-FxNLMS + restart、SFTF + det、RLS + CUSUM、M-S（14 手法）にはなかった RLS + CUSUM も走らせる。
- 検出器付き基線のイベントは同じセット・同じ run の E-PCG main（新規実行）から取る（9-A と同じ流れ。`revision9_holdout.py` の順序: E-PCG → イベント保存 → 他手法）。
- M-S: `measured_paths.allocation(seed)` を 800–839 に適用（座標と seed だけで決まる）。MeshRIR zip の抽出は新シードのマイク番号に合わせて一般化（`revision9_pipeline.prepare_data` は 480–519 の割当に固定されているので、新関数で。MD5・サイズ・README/LICENSE の検証は同じ）。Wiener 下限（真の S、因果 M = 512、0.1 Hz 格子）も 800–839 で再計算（記述、9-D と同じ計算）。
- M-P / M-PS: 本ルールの範囲外（著者決定は M-S のみ）。M-P を加えるなら S2 × 2 セル × 18 手法 = 1 440 記録・約 0.3 h（§9 項目 7）。

### 5.3 判定と family F3
- 指標・失敗・ラベルは §1.3。環境 C。
- セットごと・提案法ごとに Holm family: 2 × セル数 × (13 + n_new)（B/C: n_new = 3 なら 256、SNR10 128、M-S 64）。main/bank は別の 2 × セル数 族。
- 480–519 の既存結果との照合（9-A の 360 族と同じ like-for-like）: 既存セットと共通の基線（B/C/SNR10: 10 基線、M-S: 12 基線）だけで別に Holm を計算し（B/C 160、SNR10 80、M-S 48）、ラベル一致数と不一致の一覧（両ラベル、対差中央値、調整 p、失敗数）を報告する。シード集合は独立なので対にしない。
- 記述: 成功 run のみの A1/A2 中央値と失敗率（S4 への対応）、Wiener 下限との距離（M-S）、R2 の失敗数。

### 5.4 計算量・担当
1 キー（noise × scen × seed）あたりの合計（記録の `wall_s` から。部屋 B/C/SNR10 の RLS 系は 9–13 s、FD 系 0.2–0.4 s、E-PCG 0.6–0.7 s、新基線 MFBLMS 0.3 s・SW 0.5 s・RLS cond 約 10.5 s を仮定）:
| セット | キー数 | 1 キー | 合計（1 プロセス） |
|---|---|---|---|
| B | 320 | 約 65 s（RLS 系 5 本 ≈ 53 s） | 5.8 h |
| C | 320 | 約 70 s | 6.2 h |
| SNR10 | 160 | 約 62 s | 2.8 h |
| M-S | 80 | 約 24 s ＋ Wiener 下限 | 0.6 h |
| 計 | | | 15.4 h → 2 プロセスで **約 7.7 h**。I/O・不均衡・起動を含め 9–12 h を予算とする。任意の RLS + det + growth を含めると ＋約 1 h |
**実行担当が実行**（セットごとに 1 ジョブ、B → C → SNR10 → M-S の順。各ジョブの後に commit・push）。

## 6. 事前検証（実装後、本実行前。評価シードは使わない）
| # | 検証 | 合格条件 | 出力 |
|---|---|---|---|
| 6.1 回帰 | `revision9_regression.py` 方式: 新フラグなしで 15 手法（12 基線 ＋ CUSUM ＋ main ＋ bank）を seed 300、ar1 S2 と harmonic R2 で、本ルール実装前の HEAD（b3058bf の `prototype_new_algorithms.py`・`fd_fxnlms.py`・`epcg.py`）と比較 | タイミング以外の全決定論的返却値がバイト一致 | `results/r11_preflight/regression.md` |
| 6.2 環境 | 環境 A: holdout E-PCG main 4 キー（COMBOS15 先頭・末尾 × 800・839）＋ RLS + det 1 キー（BLAS 経路）を再実行し保存記録と比較。環境 C: `eval_roomB_x2` の E-PCG 4 キー（Rule 9a と同じ: 組合せ一覧の先頭・末尾 × seed 480・519）を比較 | `tp`・`up`・`flag_stable`・イベント列がバイト一致（許容誤差なし） | `results/r11_preflight/env_{A,C}.json` |
| 6.3 新フラグの同値性 | (a) `fd_block_gradient_mod` が `gap_check4a.recursion` の再帰 A の勾配と乱数フレーム 100 件で一致（相対 1e-12）。(b) `det_cond_db=-inf` の run が選択済み RLS + det と、`det_cond_db=+inf` が λ 0.9999 の R-RLS（det_events なし）と bit 一致（seed 300、ar1 S2・harmonic S5、`revision9_check_replay.py` 方式）。(c) `det_grow` は n ≥ 2M 以降の更新式が既存と同一であることをコードレビューで確認（任意実装時） | 一致 | `results/r11_preflight/equivalence.md` |
| 6.4 smoke（seed 300 のみ） | G1–G4、MFBLMS（μ 0.1・0.3）、SW-FBLMS（Δ_THR 0.03、M_dwell 4）、RLS cond（θ 4）を ar1 S8・ar1 S2・harmonic R2 で 1 run ずつ | 有限、NR < 0 dB、切替・再始動の回数と時刻がログに出る。**性能は記録するだけで、グリッド・設定の変更に使わない**（変えたくなったら Rule 11 を固定前に改訂し、その旨を書く） | `results/r11_preflight/smoke.md` |
| 6.5 コードレビュー | 内部コードレビューで新フラグ・新 method・family 計算・結合検査をレビュー | ブロッカーなし | [internal review record] |
- 6.1–6.4 のいずれかが不合格なら本実行に入らず報告する。

## 7. 解釈と本文の書き方（結果を見る前に固定）
| 子 | 結果 | 本文に書く文（英文は文体ガイドに従い、better/worse ＋ 判定基準を 1 回明示） |
|---|---|---|
| 11-A | G1 が S8/S7 で RLS + det に対する win を失う | "Without the controller-order growth, the A1 advantage over RLS+det in S8 and S7 shrinks from x/y dB to x'/y' dB and is no longer significant under the criterion of Section V-B; the growth, not the solver, carries most of these two gains. The gains after the other changes (cells …) remain." |
| 11-A | G1 が win を保つ | "The A1 gains in S8 and S7 remain without the growth (x'/y' dB); the growth adds x''/y'' dB." |
| 11-A | G1 が G0 より 30 族で有意に悪い／良い／差なし | 数値のまま。「良い」場合も主手法の設定は変えない（事前固定）と明記 |
| 11-A | G2/G3/G4 | アブレーション表の行として数値のみ。文は照合 B の既存文を holdout 値で置き換える |
| 11-B | 新基線に対し全セル win/'-' | "Against MFBLMS and the switching algorithm of [6], PCG-WLS was better in x of 2·15·n_new comparisons and worse in none." |
| 11-B | **新基線に対し loss があるセル** | そのまま報告: "The switching algorithm of [6] was better than PCG-WLS in cells … (paired A1 difference +z dB)." 要旨の "worse in none" は "worse in none of the 13 prespecified baselines; the [6]-type baseline added in revision was better in k cells" に改める。結論の "no loss in the main room" も同様に制限 |
| 11-B | MFBLMS/SW に admissible 構成なし | "No configuration of … completed the 450 tuning runs without failure under the admissibility rule; it is reported in S4 and not evaluated." |
| 11-C | 外側点が失敗／内点 | Protocol に 1 文: "Extending the RLS/VFF-RLS grids one step outward (λ = 0.9993, N0 = 250) gave no admissible/better configuration." |
| 11-C | 外側点が良い | "λ = 0.9993 scored better on the tuning seeds and is reported as an additional row (RLS, extended grid); the original selection is kept for the prespecified comparison." ラベルは F1 の行として報告 |
| 11-C | RLS cond. が S1/S5/R1/R3 で RLS + det より良く、PCG-WLS との差が '-' | "A conditional restart (threshold θ dB) removes the degradation of RLS+det after small changes; against it no difference was demonstrated in cells …" と書き、R1/R3 の win の限定（照合 B の S2 文）を残す |
| 11-C | RLS cond. が PCG-WLS より良い | 11-B の loss と同じ扱い |
| 11-D | holdout ラベルが 480–519 と一致 | "On holdout seeds the room/SNR/measured comparisons agree in k of K labels (S11); the holdout tables are used in the main text." |
| 11-D | 不一致（loss 増／減） | 両方を報告し、主張は holdout に基づく（9-A と同じ）。"The holdout evaluation of the rooms adds/removes losses in cells …; half of the losses remain in the control-unit move with a fixed secondary-path model." 不一致の一覧は補足 |
| 11-D | RLS + CUSUM が部屋・実測で PCG-WLS より良い | そのまま報告し、要旨の部屋の文に加える |
- どの結果でも、'-' は同等ではない、loss は一般化の制限、mixed はトレードオフ、と 1 回だけ書く（m3 の重複削減と整合）。
- 本文は 13 頁上限。追加分は照合 A/B の「削る」候補（Lorden 段落、重複但し書き、付録 B、`experiments.tex:36,53,56,149-152`）で相殺し、最終は IEEEtran ビルドで確認。

## 8. 実行順序・担当・見積もり

| 順 | 作業 | 担当 | 計算（2 プロセス理想） | 実装工数 |
|---|---|---|---|---|
| 0 | 本ルールの固定（著者了承 → `REVISION_RULE_11.md`、commit） | 著者・実装担当 | — | — |
| 1 | 実装: `mod`、`SW-FBLMS`、`det_cond_*`、（任意 `det_grow`、`solver='exact'`）、GRID11、`revision11_*.py` | 実装担当（コードは内部レビュー） | — | 2.5–3.5 日（任意込み 4 日） |
| 2 | §6 事前検証（環境 A/C 構築を含む） | 実装担当 | 約 20 分 | 0.5 日 |
| 3 | 11-A（G1 必須、G2–G4 推奨） | 実装担当 | 0.2 h | — |
| 4 | 11-B 調整（環境 C） | 実装担当 | 0.5 h | — |
| 5 | 11-C 調整（条件付き RLS、外側グリッド） | 実行担当 | 2.6 h（任意 ＋1.1 h） | — |
| 6 | 11-B/11-C の部屋 A holdout（環境 A）、F1 集約 | 実装担当（RLS 系の holdout は実行担当） | 0.5 h（＋外側点の行 0.5 h/行） | — |
| 7 | 11-D（環境 C、MeshRIR） | 実行担当 | 7.7 h（予算 9–12 h） | パイプライン 0.5 日 |
| 8 | 集約: summary、F1/F2/F3 の表、like-for-like 比較、[internal records omitted]、Zenodo 用 tar | 実装担当 | 1 h | 0.5 日 |
| 計 | | | **約 11.5 h（任意込み約 14 h）→ 実時間予算 14–18 h** | **約 4–5 日** |
- 「1 実験 = 1 ジョブ、2 コアを遊ばせない」: 11-A と 11-B 調整は FD 系が軽いので、同時に走らせるのは 2 プロセスまで。
- 数時間以上のジョブ（11-C、11-D）は `[run branch]`で実行し、こちらで確認してからマージ。

## 9. 著者の決定（2026-11-07 06:19 JST、「すべてお任せ。査読で突っ込まれても答えられるよう、できるだけやりたい」）
方針: 推奨案を採り、任意の項目はすべて含める（最大範囲）。
- [x] 1. [6] は **Z-C**（Z-A 自前検出の再構成と Z-B 借用検出の両方）。ζ(k)・ζ_THR は原論文の式が未確認のため「[6] に基づく再構成」と論文に明記する。Δ_THR は相対値、グリッド {0.01, 0.03, 0.1} × M_dwell {4, 8}。原論文 PDF が得られて式が §3.4 と食い違えば、実行前なら Rule 11 の訂正版（11a）を固定してから実装する。
- [x] 2. MFBLMS: FD-FxNLMS と同じ 6 点、既存 PowerTracker の正規化。**MFBLMS + det も含める。**
- [x] 3. 条件付き再始動: θ 版（K = 32、θ ∈ {1, 2, 4, 8} dB、λ 0.9999 固定）。
- [x] 4. RLS + det + growth を**含める**。
- [x] 5. 外側グリッド: 必須 3 点＋RLS + CUSUM K = 64＋FD 系 5 点を**含める**。「良ければ holdout に行を追加、最大 2 段」の規則を採る。
- [x] 6. アブレーション G1–G4 に加え **G5（厳密ソルバ）も含める**。
- [x] 7. 11-D: 全基線 1 族。主張は holdout に基づく（480–519 は補足）。**M-P も含める。** Tables V–VIII は holdout 版に差し替える（480–519 版は補足）。
- [x] 8. 環境 A が再現できない場合は (b)（部屋 A holdout 15 手法を環境 C で全再実行し、Rule 11 の比較はそこで閉じる。既存 390 族は不変）。
- [x] 9. Zenodo 新版 v1.2.0（pcg-ffanc のタグも）を作る。pcg-ffanc v1.1.0（c6a08bc）は Rule 11 の前に付ける。
- [x] 10. 担当: 11-C・11-D は実行担当、他は実装担当。
- [x] 11. 論文表記は草案のとおり（MFBLMS [31]、switching FD-FxNLMS [6]／+ det、RLS + det (cond.)、RLS + det + growth、PCG-WLS (fixed order)／(restart)／(no detector)／(exact solver)）。
- [x] 12. §7 の結果別の文と §1.7 の掲載基準を採る。

## 10. 固定後のチェックリスト
- [ ] 本ルールを `REVISION_RULE_11.md` として保存し、sha256 を provenance に使う（本草案はそのまま残す）
- [ ] 実装（新フラグ、既定値不変）→ 内部コードレビュー
- [ ] §6.1 回帰 bit 一致、§6.2 環境 A/C 一致、§6.3 同値性、§6.4 smoke（seed 300 のみ）
- [ ] 11-A 実行・summary（F2）
- [ ] 11-B 調整 → `selected.json`（MFBLMS、SW-FBLMS）
- [ ] 11-C 調整 → `selected.json`（RLS cond.、外側点の判定）
- [ ] 11-B/11-C の部屋 A holdout → F1 集約
- [ ] 11-D（B → C → SNR10 → M-S）→ F3 集約、like-for-like 比較
- [ ] [internal records omitted]、tab:rules に Rule 11 の行
- [ ] **結果を見てからの取捨選択（著者）**: §1.7 の基準で本文に載せる場所を決める。数値・ラベル・family は変えない
