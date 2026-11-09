# Revision 11a: Rule 11 の訂正（smoke・コードレビュー後、本実行前に固定）

**固定版（著者の包括的な委任による、2026-11-07）。** 本書は `REVISION_RULE_11.md`（固定版、sha256 `6ba432af58880a94d6915beab8f7183af645b706bff37b959d4acdd6519bf270`。以下 Rule 11）の追補であり、Rule 11 の §9 の決定（最大範囲）を前提とする。Rule 11 の手法・グリッド・閾値・シード・指標・検定・family・§7 の文・§9 の決定は**一切変更しない**。本書が定めるのは、(1) コードレビューがルールの欠陥と判定した 2 点の確定（B-1、B-2）、(2) 事前検証の不合格の扱いと実行担当の開始条件（B-3）、(3) Rule 11 が沈黙していた細部の明文化、(4) 予算の改定、である。新しい挙動はすべて新しいフラグの後ろに置き、既定経路は変えない。

- 作成: 2026-11-07 JST、[provenance note omitted]。対象ブランチ `[working branch]`（HEAD 62eb0a4、基点 35df6af）。
- 根拠: [implementation notes]（実装者の判断 21 項目）、[internal review record]（内部コードレビュー: B-1〜B-3、M-1〜M-6、L-1〜L-11、§3「11a が必要な項目」）、`results/r11_preflight/`（§6.1 PASS、§6.2 環境 C PASS・環境 A FAIL、§6.3 PASS、§6.4 smoke 室 A 1 件 FAIL）、[run guide]。
- 著者の方針（2026-11-07）: 「すべてお任せ。査読で突っ込まれても答えられるよう、できるだけやる」。本書の各決定はこの委任のもとで下された。結果を見てから決め直す余地は残さない。
- 前例: `REVISION_RULE_9a.md`（9-C の結合検査停止の後、性能結果を見る前に環境を固定した追補）。本書も同じ位置づけである。

## 0. 経緯の開示（何を見た後に固定したか）

| 時点 | 行ったこと | 見た数値 |
|---|---|---|
| 2026-11-07 06:19 JST | Rule 11 固定（著者了承） | — |
| 同日 | 実装（`[working branch]` 0b74f62 → 62eb0a4）、単体テスト 13 件、§6.1 回帰、§6.2 環境 A/C、§6.3 同値性、§6.4 smoke | smoke（**調整シード 300 のみ**、室 A 63 run ＋ 部屋 B/C 各 21 run）の NR・A1/A2・切替／再始動ログ |
| 同日 | 内部コードレビュー（[internal review record]）。B-1 の根拠は seed 300 での J_m の追跡（smoke シード、診断量） | SW-FBLMS の ΔJ/J_m の値（−0.050、−0.158）と切替 hop |
| 同日 | **本書の固定** | — |
| 本書の後 | コード修正 → テスト・§6.3・smoke の再実行 → 本実行（11-A → 11-B → 11-C → holdout → 11-D） | — |

- 評価シード 480–519、holdout シード 800–839 での新しい記録は作っていない（§6.2 は保存済みキーの再実行と比較だけ）。調整（450 run）も未実行。
- 本書のどの決定も、smoke の性能値（A1/A2/NR）を根拠にしていない。B-1 は切替の**時刻**と J_m の**符号**（挙動の欠陥）から、B-2 はコード読解から、B-3 は検証の合否から決めた。smoke の性能値は Rule 11 §6.4 のとおり記録するだけである。
- Rule 11 §1.6「結果を見てから手法・設定・グリッド・閾値・family・ルールを変えない。問題の修正は Rule 11a 以降として別途固定する」に従う。

## 1. B-1: SW-FBLMS の N → M 切替条件

### 1.1 原論文 [6] の確認（2026-11-07、web 取得。UTS OPUS の著者版 PDF、式は文字化け）

| 項目 | 確認できたこと（[6] の記述） | 本研究の実装（Rule 11 §3.4） | 判定 |
|---|---|---|---|
| J_m の初期値 | 「J_m(k) is initialized using the instantaneous squared error J(k)」 | J_m(−1) = J(0)（実装メモ #6） | 一致 |
| J_m の再帰 | b J_m(k−1) ＋ J(k) の項を含む（Eq. (16)。正則化係数 α は「瞬時推定の変動を抑える小さな係数」。式の形は読めない） | J_m(k) = b J_m(k−1) + (1 − b) J(k)、α なし | α の入り方は未確認。使わない（§1.3 で開示） |
| b | (1 − μ/2)² + μ²/4 | 同（μ = μ_N = 0.3 → 0.745） | 一致 |
| ΔJ の定義 | **ΔJ(k) = J_m(k−1) − J_m(k)**（前 − 今。絶対値なし） | 同 | 一致 |
| N → M の条件 | 「When ΔJ(k) is smaller than a preset threshold（Δ_THR）」→「the NFBLMS algorithm reaches the steady-state and … should switch to the MFBLMS algorithm」。フローチャートは「ΔJ(k) < Δ_THR & m > M」 | ΔJ < Δ_THR·J_m かつ dwell ≥ M_dwell | 形は一致。**[6] も負の ΔJ（J_m の増加）を扱っていない**。閾値は [6] が絶対値、本研究は相対値（Rule 11 §3.4 で開示済み） |
| 数値 | Δ_THR、ζ_THR、M、μ、α は**記載なし**。実験: fs 16 kHz、制御器 1024、ブロック 1024、FFT 2048、10 試行平均、約 1.0 s で M へ切替、42 s で音源移動 | グリッド {0.01, 0.03, 0.1} × {4, 8} hop | 確認不能（Rule 11 §3.2 のとおり） |
| ζ(k)（Eq. (17)） | 「The steady-state tracking parameter is set as」に続く式。誤差 e_f と参照 x_f を Q 型行列（Q_{0,N} と読める）で挟んだ 2 つの期待値の比。平滑化の記述なし | 平滑化‖IFFT(conj(X)E/D) のラグ M..N−1‖² ／ 平滑化‖e‖²（係数 b） | **式本体は読めない。再構成のまま**（§5.5） |
| M → N | 「When ζ(k) suddenly increases above a threshold ζ_THR, the ANC system needs to be re-initialized to the NFBLMS algorithm」。フローチャート「ζ(k) > ζ_THR & m > M」 | ζ > ζ_THR かつ dwell ≥ M_dwell | 一致 |
| ζ_THR の決め方 | 「the proposed algorithm switches to the NFBLMS algorithm for a short while」、その大きい ζ を ζ_THR とする。フローチャートに「ζ_THR = 0; m = 0」「ζ(k−1) ≤ ζ(k) & m > M」「ζ_THR = ζ(k); m = 0」の枝がある（配置は読めない） | M に入ると ζ_THR 未較正、M_dwell hop 後に N を M_dwell hop 走らせ、その間の平滑化 ζ の最大値を ζ_THR | 枝の読みが正しければ、[6] の較正終了は「ζ が減少をやめた最初のブロック（m > M）」で、その時点の ζ(k) を ζ_THR とする。本研究は固定長の N 区間の最大値。**どちらも再構成**（§5.5 で扱う。本書では変えない） |
| dwell | 「each algorithm needs to run continuously at least for M blocks after a switch」 | 同（hop 単位） | 一致 |

- 原文 PDF の直接取得（curl）は開発機のプロキシで拒否された（403）。web 経由の抽出のみで、式は復元できない。Rule 11 §3.2 の「未確認」の範囲は変わらない。

### 1.2 決定

- [x] **N → M の条件を `0 ≤ ΔJ(k) < Δ_THR · J_m(k)` かつ dwell ≥ M_dwell に固定する**（Z-A、Z-B とも）。ΔJ(k) = J_m(k−1) − J_m(k) の定義、Δ_THR の相対化、グリッド {0.01, 0.03, 0.1} × {4, 8}、b = 0.745、J_m の初期値は不変。
- 理由:
  1. [6] の条件文は「減少量が閾値未満」であり、その意味は本文で「NFBLMS が定常に達した」と明言されている。J_m が**増えている**（ΔJ < 0）局面は定常ではなく、[6] の実験（ブロック 64 ms、dwell M ブロック）では N モードの最短滞在中に増加局面が終わるため、符号の扱いが問題にならなかったと解釈できる。本研究の hop は 8 ms、dwell は 4–8 hop（32–64 ms）なので、文字どおりの条件では変化直後の増加局面で N モードが最短で打ち切られる（レビュー B-1 の追跡: harmonic R2 で hop 62 → 65、ΔJ/J_m = −0.050、J_m は変化前の約 32 倍で増加中）。これは Must（11-B）の基線を不利に組むことになり、査読で指摘されうる。
  2. 候補 `|ΔJ| < Δ_THR·J_m` と比べ、`0 ≤ ΔJ` は [6] の条件 `ΔJ < Δ_THR` に符号条件を**加えるだけ**で、[6] の文言との差が最小である。「J_m の減少が止まった（減っているが、その幅が小さい）」という定常判定の自然な形でもある。
  3. 2 候補とも、J_m の山（増加から減少への転換点）で ΔJ ≈ 0 となり切替が起こりうる点は同じである。これは Δ_THR と M_dwell の調整（450 run、admissibility とスコア）で基線自身が選ぶ。本書で第 3 の条件（例: 連続 hop 数、J_m の水準）を加えることはしない（[6] に無い）。
- 開示（論文、「[6] に基づく再構成」の注記に含める）: (a) Δ_THR を J_m に対する相対値にした、(b) ΔJ ≥ 0 の条件を加えた（[6] は符号を扱っていない）、(c) J_m の正則化 α は形が確認できず用いない、(d) ブロック = hop（128 サンプル）。
- 実装: `experiments/prototype_new_algorithms.py` `_sw_hop`（1578 行付近）の判定を `0.0 <= dJ < sw_thr * Jm` に直す。フラグの追加はない（SW-FBLMS は新 method であり既定経路に無い）。
- やり直し: `tests/test_revision11.py::test_zeta_calibration_sequence` の更新、新テスト（§8）、§6.4 smoke の SW 2 行 × 3 セル（seed 300）。B2 段（SW-FBLMS の調整）の前に完了していること。

## 2. B-2: RLS + det + growth（Rule 11 §2.6）

### 2.1 問題（レビュー B-2、実装メモ #12）
- (a) 適用区間: Rule 11 §2.6 は「再始動（tau）から n < 2M の間」。実装は run の開始（g0 = 0）にも適用している。
- (b) warm 再始動での不整合: 成長中は u の末尾（タップ m_eff 以降）を 0 にするが、w の末尾（再始動前の値）はそのまま制御出力に使われる。再始動後の P は対角で、P u の末尾は 0、ゲイン k の末尾も 0 なので、末尾タップは凍結される。RLS は「末尾の無い制御器」の残差 ε = d̂ + u_headᵀ w_head で先頭を合わせるが、実際の出力には古い末尾が乗る。E-PCG の `grow_len` は反復の初期値を x0·mask で切り、解も部分空間上なので制御器の末尾は 0 である（`epcg.py:467-468`、Stein 重み付き解でも n_eff から m_eff を求めて同じく mask、`epcg.py:1071`）。鏡像になっていない。

### 2.2 決定
- [x] **両方の版を評価する**（著者の決定）。どちらも構成 1 つ、グリッドなし、調整シードで admissibility のみ（450 run、失敗 0 なら部屋 A holdout 600 run → F1 の行、11-D の行）。両者の間で選択はしない。

| 版 | 論文表記（§9-11 の表記に加える） | 成長の適用区間 | フラグ | 位置づけ |
|---|---|---|---|---|
| (i) | **RLS + det + growth** | 各再始動（tau）から 2M サンプル（Rule 11 §2.6 の本文どおり）。run の開始は既存 RLS と同じ（u は m = min(M, t+1) タップ） | `det_grow: 'half'`（`det_grow_start` 無し／False） | Rule 11 本文の定義 |
| (ii) | **RLS + det + growth (from start)** | run の開始（g0 = 0）と各再始動（g0 = tau）から 2M サンプル | `det_grow: 'half', det_grow_start: True` | E-PCG の `grow_len`（立ち上がりと再始動）の鏡像。査読 M3(b) の「S8 の利得は立ち上がりの次数成長」に直接答える版 |

- 既定（`det_grow_start` 無し）を (i) にするのは、Rule 11 本文の定義に名前 `RLS + det + growth` を残すためである。現在の実装は (ii) に当たるので、`det_grow_start` が無いときの挙動を (i) に直す。
- [x] **warm 再始動時の w の末尾**: 再始動の時点（再生の開始 t = tau、n = 1）で **w[m_eff(n):] = 0、m_eff(n) = max(n//2, 1)、すなわち w[1:] = 0** とする。成長中（n < 2M）はゲイン k の末尾が 0 なので末尾は 0 のまま、新しいタップは 0 から入る。これは E-PCG の x0·mask（各 hop で m_eff の外側を 0 にし、部分空間で解く）と、サンプル単位での鏡像である。run の開始（(ii)）では w = 0 なので何も変わらない。
  - 退けた案と理由: (α) hop 粒度の mask（w[H//2:] = 0）— 最初の hop の内側で (b) の不整合が残る。(β) ε に全タップを使い更新を先頭に限る — 「古い末尾を固定して先頭を合わせる」という別の LS 問題になり、E-PCG の次数成長（制御器の次数そのものが n/2）ではない。
  - 開示（論文）: 「RLS + det + growth では、再始動時に成長区間の外側の係数を 0 にする（PCG-WLS の次数成長と同じ）。warm の意味は P のリセット・δ・[tau, stop) の再生が RLS + det と同一であることを指し、再始動前の係数は先頭タップしか残らない。」warm の係数をそのまま残す RLS 族の相手は RLS + det 自身である。
  - 成長中の未使用タップの P 対角は 1/λ 倍ずつ増える（δ 正則化が忘却で緩む）。Rule 11 §2.6「新しいタップは初期 P の δ 正則化のまま入る」は「初期 P の δ 正則化（忘却込み）」と読む。実装はそのまま。
- 他はすべて Rule 11 §2.6 のとおり（λ 0.9999、δ 0.01、warm、`det_replay` True、P は M × M、n ≥ 2M で既存経路に一致、RLS + CUSUM とは併用しない）。
- 同値性の確認（§6.3 (c) を置き換える）: (c1) 版 (i) で `det_events` が空の run は λ 0.9999・δ 0.01 の R-RLS（`det_events` なし）と**ビット一致**（成長は再始動後にしか起きないため。seed 300、ar1 S8 で確認）。(c2) 版 (i)(ii) とも、再始動直後の w の末尾が 0、切り詰めたタップ数が max(n//2, 1)（単体テスト、小さな合成データ）。(c3) n ≥ 2M の更新式が既存と同一（コードレビュー、現行の (c) と同じ）。
- 計算時間の追加（1 run 約 8.5–9.3 s、smoke）: 調整 450 run ≈ 1.1 h、部屋 A holdout 600 run ≈ 1.5 h、11-D（B 320 ＋ C 320 ＋ SNR10 160 ＋ M-S 80 ＋ M-P 80 キー）≈ 2.4 h。1 版あたり約 5.0 h（1 プロセス）→ 2 版で 2 プロセス約 **＋2.5 h**（Rule 11 の見積もりは 1 版・約 0.8 h ＋ 11-D 約 1 h）。§7 の予算に含める。
- `DET_NEW` に `RLS + det + growth (from start)` を加える（イベントを消費する）。n_new の候補に両版を含める（§5.4）。
- やり直し: §6.3 (c1)(c2)、smoke の growth 行（両版 × 3 セル、seed 300）。C 段（11-C 調整）の前に完了していること。

## 3. B-3: 事前検証の不合格の扱いと、実行担当の開始条件

### 3.1 §6.2 環境 A の不一致
- 事実（`results/r11_preflight/env_A.json`、commit 0b74f62）: Python 3.12.3 / numpy 2.3.5 / scipy 1.17.0 / pyroomacoustics 0.10.1 で、保存済み holdout（9-A、Python 3.12.14）の E-PCG 4 キーと RLS + det 1 キーの `tp`・`up` が不一致（イベント列・`flag_stable` は一致。S8 の `up` で相対 4e-8）。環境 C は部屋 B の 4 キーと v2e の部屋 A 記録にバイト一致（`env_C.json` PASS）。原因はハードウェアの SIMD 経路か Python のパッチ版と推定、未確定。
- [x] **決定: Rule 11 §9 項目 8 (b) で進める。** 部屋 A holdout の 15 手法（12 基線 ＋ RLS + CUSUM ＋ main ＋ bank）を環境 C で再実行し（`R11_HOLDOUT_BASE=envC`、出力 `results/final_eval_holdout_r11_envC/`）、Rule 11 の 11-A（F2）と 11-B/11-C（F1）の比較は**その中で閉じる**。G0・13 基線・提案法の比較対象・`up` の照合・イベントの読み込みは、すべてこのディレクトリの記録に切り替わる（実装済み、レビュー §2.4 で確認）。
- 既存の 390 族（`results/final_eval_holdout/`、139/195）は不変。論文では「Rule 11 の比較は環境 C の再実行記録に対して行った」と環境表（Rule 9a §4 の方式）に 1 行加え、再実行 15 手法のラベル（2 × 15 × 13 を同じ Holm で再計算した**参考値**）と 390 族のラベルの一致数を補足に記す。この参考値で 390 族の数は置き換えない。
- 経路 A への復帰条件（機械的）:実行担当の環境で `revision11_preflight.py envA` が `"pass": true` を返した場合**のみ**、経路 A（`PY=[venvA python]`、`final_eval_holdout/` と結合）。`"pass": false` なら経路 (b)。どちらになったかは各 `provenance.json` に `holdout_base: "envA" | "envC"` として記録する（§8 のコード修正）。著者への再確認は要らない。

### 3.2 §6.4 smoke の不合格 1 件（MFBLMS μ 0.3、harmonic R2、seed 300、NR +21.7 dB）
- [x] **決定: 実装の不合格ではなく、調整グリッドの 1 点の失敗として扱う。** 根拠: (1) 実装は `gap_check4a` の再帰 A および Lu–Chen–Qiu (2017) 式 (6) の時間域形と機械精度で一致（§6.3 (a)、単体テスト）。(2) harmonic R2 は帯域外ビンの小さい D_b で正規化ゲインが大きくなる構造的な発散で、μ 0.3 は FD-FxNLMS でも上端。(3) seed 300 × harmonic R2 は調整の 450 run に含まれる（調整シード 300、COMBOS15 のセル）ので、同じ環境 C で決定論的に再現し、μ 0.3 は Rule 11 §1.4 の admissibility で落ちる。
- グリッドは変えない（Rule 11 §6.4）。μ 0.3 が inadmissible なら上端は 0.25 以下になり、§5.2 の上側延長は発動しない。
- **smoke の合否規則（§6.4 の判定基準の明文化。本実行の開始条件に使う）**: 室 A の行について、
  - (s1) 非有限値（NaN／inf）が 1 行でもあれば**不合格・停止**（実装エラー）。
  - (s2) NR ≥ 0 dB の行が、**調整グリッドの構成**（GRID11・`dependent_grids`・外側点 `OUTER`/`OUTER_OPT`・MFBLMS の延長点）にだけ現れるなら**記録のみ**（その構成は調整で admissibility により落ちる）。smoke の行のうちこれに当たるのは MFBLMS（μ 0.1／0.3）、MFBLMS + det、SW-FBLMS（Δ_THR 0.03、M_dwell 4）、RLS + det (cond.)（θ 4）、RLS + det + growth（両版）、外側点の各行。
  - (s3) NR ≥ 0 dB の行が **G0〜G5**（調整しない変種）または既存の選択済み手法に現れたら**不合格・停止**。
  - (s4) 切替・再始動の回数と時刻がログに無い行があれば不合格・停止。
  - 部屋 B/C の行は時間計測のみで判定に使わない（Rule 11 §6.4 のとおり）。

### 3.3実行担当の開始条件（機械的に確かめられる形。[run guide] §2 をこれに置き換える）
本実行（B0 以降）に入る前に、実行担当は次をすべて確かめる。1 つでも満たさなければ §4 の事前検証までで停止・報告する。

| # | 条件 | 確かめ方 |
|---|---|---|
| c1 | 本書 `docs/current/REVISION_RULE_11a.md` がブランチにあり、その sha256 が [run guide] §2 と `experiments/revision11_methods.py` の定数 `RULE11A_SHA256` に転記された値と一致する | `sha256sum docs/current/REVISION_RULE_11a.md` |
| c2 | §8 のコード修正（B-1、B-2、M-1〜M-6）が commit 済みで、`pytest tests/test_revision11.py` が新テストを含めて全件 PASS | pytest |
| c3 | `results/r11_preflight/regression.md`（§6.1）が実行担当の環境で PASS | ファイルの末尾 `Result: PASS` |
| c4 | `results/r11_preflight/env_C.json` が `"pass": true` | JSON |
| c5 | `results/r11_preflight/env_A.json` が存在する。`"pass"` の値で経路を決める（true → A、false → (b)） | JSON |
| c6 | `results/r11_preflight/equivalence.md` が (a)(b)(c1)(c2)(c3) すべて PASS（コード修正後に再生成したもの） | ファイルの末尾 `Result: PASS` |
| c7 | `results/r11_preflight/smoke.md` が、コード修正後に再生成され、§3.2 の (s1)(s3)(s4) に該当する行が無い。(s2) の行は列挙して報告 | ファイル |
| c8 | pipeline が各ジョブの開始時に c1 と環境（§6 M-3）を検査し、不一致なら起動しない | 実装（§8） |

- 本書の sha256 は本書自身には書けない。固定 commit の後、実装者が [run guide] §2・§7、[internal records]、`revision11_methods.py` の `RULE11A_SHA256` に転記する（§8）。以後、本書は変更しない（変更が必要なら Rule 11b）。
- 各出力ディレクトリの `provenance.json` に `rule11a_sha256` と `holdout_base` を加える。§7 の完了確認は `rule_sha256`（Rule 11）と `rule11a_sha256`（本書）の両方を見る。M-S・M-P は `revision11.rule_sha256` / `revision11.rule11a_sha256` を見る（レビュー L-6）。

## 4. M-2: admissible な構成が無い group の扱い

- Rule 11 の記述: §1.4「『admissible な構成なし』は手法として報告し評価しない（`REVISION_RULE.md` 修正 M6 と同じ）」、§1.6「admissible 構成なし … で停止して報告する」、§3.4「MFBLMS に admissible な構成がなければ SW-FBLMS は作れないので停止・報告（著者判断）」。手順書 §6 は停止。実装は MFBLMS 以外では止まらずに進む。
- [x] **決定: §1.4 に揃える。「報告して評価しない、pipeline は進む」を唯一の規則にする。** 理由: (1) 既存基線の選択（`REVISION_RULE.md` M6）と同じ扱いで、新基線だけ別ルールにしない。(2) §7 に「No configuration of … completed the 450 tuning runs without failure under the admissibility rule; it is reported in S4 and not evaluated.」の文が既に固定されている。(3) 停止して著者が判断すると「結果を見てから決める」余地が生じる。
- 具体:
  - group（MFBLMS、MFBLMS + det、switching FD-FxNLMS [6]、switching FD-FxNLMS + det、RLS + det (cond.)、RLS + det + growth、RLS + det + growth (from start)、各外側点）に admissible な構成が無ければ、`selection.md` に全構成の失敗セルを記し、`selected.json` に `inadmissible: [group, …]` を出し、n_new から外す。`complete` は他の group が完了していれば true。pipeline は `NOTE: no admissible configuration: …` を標準出力とログに出して**進む**。
  - **MFBLMS に admissible な構成が無い場合**: μ_M が定まらないので、MFBLMS + det・Z-A・Z-B の 3 group は「構成できない（inadmissible の派生）」として同じく報告し評価しない（`inadmissible` に `reason: "MFBLMS has no admissible step"` を付す）。B2 段は run を持たず、C 段に進む。§1.6・§3.4 の「停止」はこの規則で置き換える。論文は §7 の文で報告し、[6] 型基線が本文に無い理由を 1 文で述べる。
  - 外側点の group が全失敗なら、Rule 11 §4.2 のとおり「選択値は admissible 領域の端」として報告（行の追加なし）。これは inadmissible ではなく §4.2 の判定である。
  - 手順書 §6 の「調整で admissible な構成が無い → 停止」を「報告して進む（NOTE）」に改める。
- 変わらないもの: 停止条件のうち「入力不完全」「非有限値」「実装エラー」「環境不一致」「イベント欠落」「`up` の不一致」「調整の未完了」「MeshRIR の検証失敗」は Rule 11 §1.6 のまま停止。

## 5. 細部の明文化（Rule 11 が沈黙していた点。実装メモ・レビューの指摘順）

### 5.1 G5（厳密ソルバ）の範囲（メモ #2、レビュー L-1）
- [x] `solver: 'exact'` は `_pcg` の**全呼び出し**（窓解、Stein 重み付き解、w_A・w_B、および検出の前の精緻化 sw_refine の窓 LS）を同じ正則化正規方程式の直接解にする。sandwich 統計 `_sandwich_q` の PCG は変えない。grow_len の部分空間では先頭 m_eff × m_eff ブロックを解き他は 0（mask 付き PCG の極限）。
- 精緻化が厳密解になるのでスコアの入力 g が変わり、**検出結果は G0 と同一とは限らない**。G1–G4 と同じく検出回数・警報時刻を記録して G0 と並べる（Rule 11 §2.3 の最終項）。論文の開示文: 「exact solver: the window solves and the refinement before the detection statistic are replaced by a direct solve of the same regularized normal equations; the PCG inside the sandwich statistic is unchanged」。
- `EPCGConfig.solver` は `epcg.py` に置く（メモ #1。Rule 11 §1.5 の 2 ファイルに加える）。既定 `'pcg'`、§6.1 で回帰一致済み。
- 1 run 約 13–15 s（Rule 11 の見積もり 3 s）。600 run ≈ 1.2 h（2 プロセス）。

### 5.2 MFBLMS の端の刻み（メモ #4）
- [x] 上端: 0.3 → 0.35 → 0.4。下端: 0.05 → 0.025 → 0.0125（0.05 刻みでは 0 になるので半分、以後も半分）。最大 2 段。延長点を含めた admissible 構成の最小スコアで選択（Rule 11 §3.3「端の規則は §4.2 と共通」の具体化）。
- Rule 11 §3.3「外側が既知の失敗なら追加しない」の「既知」は**同じ手法**の記録に限る。FD-FxNLMS の μ ≥ 0.35 の失敗（v1）は MFBLMS の既知の失敗ではないので、延長の判断には使わない。
- §3.2 のとおり、μ 0.3 が inadmissible なら上側の延長は起きない。

### 5.3 外側点（Rule 11 §4.2）の 2 段目と任意点（メモ #14・#15）
- [x] 2 段目の比較対象は **1 段目**（0.01 dB を超えて良ければ行を 2 段目に置き換える、最大 2 段）。1 段目の比較対象は Rule 11 のとおり既存スコア（`selection_e.md` の記録値、CUSUM は `protocol_v2_sel_cusum/selected.json`）。
- [x] Rule 11 が 2 段目を定義していない任意点（RLS + CUSUM K = 64、FD-FxNLMS μ 0.32、leaky 2 点、FDKF P0 3、FD + det scale 0.03125）は、1 段目が「良い」でも 2 段目を走らせず、「<基線名> (extended grid)」の行を holdout に加えて F1 に入れ、「1 段のみ」と報告する。
- [x] 1 つの基線に複数の外側点がある場合（CUSUM K64 × h ∈ {3, 5, 8}、leaky 2 点）は、その中の admissible な最小スコアの 1 点を既存スコアと比べ、行はその点。
- [x] C 段の実行順: 必須（RLS + det (cond.) 4、RLS + det + growth 2 版、外側点 RLS・VFF-RLS・SFTF-H）→ 任意（CUSUM K64 × 3、FD 系 5 点）→ 発動した 2 段目。途中で停止しても必須部分が先に揃う（レビュー L-10）。
- 「(extended grid)」の行は、元の選択・表・ラベルを変えない（Rule 11 §4.2）。

### 5.4 n_new の集合（Rule 11 §3.5 の列挙の補完）
- [x] n_new = 次のうち admissible（調整で選択できた）な行の数: MFBLMS、**MFBLMS + det**（§9-2。§3.5 の列挙に無かった）、switching FD-FxNLMS [6]（Z-A）、switching FD-FxNLMS + det（Z-B）、RLS + det (cond.)、RLS + det + growth、**RLS + det + growth (from start)**、「<基線名> (extended grid)」の行（最大 8 基線: RLS、VFF-RLS、SFTF-H + det、RLS + CUSUM、FD-FxNLMS、leaky FD-FxNLMS、FDKF、FD-FxNLMS + det）。最大 15。
- F1 = 提案法ごとに 2 × 15 × n_new（Holm）。F3 = 2 × セル数 × (13 + n_new)。11-D の行数 = 13 ＋ n_new ＋ 2。定義式は不変、集合だけ補完した。
- `selected.json` の `new_rows` がこの集合を機械的に与える（実装済み。growth の 2 版目を加える）。

### 5.5 Z-A の ζ の定義（メモ #8、レビュー L-5）と ζ_THR の較正
- [x] ζ(k) の分子 = 正規化勾配 IFFT(conj(X_f) E_f / D_b)（N 点循環相関）の**ラグ M..N−1**（勾配拘束で捨てる側。[6] の Q_{0,N} が残す成分）の二乗和、分母 = 新しい H サンプルの誤差の二乗和、両方を係数 b で平滑化。Rule 11 §3.4 の「非因果側ラグ」はこの「拘束で捨てる側のラグ」に読み替える（M..N−1 には因果側で M を超えるラグ M..N−H と、巡回で折り返す非因果側 N−H+1..N−1 の両方が入る）。
- [x] ζ_THR の較正は Rule 11 §3.4 のまま: M に入ると未較正（ζ_THR = 0 相当）、M_dwell hop 後に N モード（更新は N）を M_dwell hop 走らせ、その間の平滑化 ζ の最大値を ζ_THR として M に戻る。以後、M モードで ζ > ζ_THR かつ dwell ≥ M_dwell で N へ。
- 開示: §1.1 のとおり [6] のフローチャートには「ζ(k−1) ≤ ζ(k) & m > M → ζ_THR = ζ(k)」と読める枝があり、較正の終了が「ζ が減少をやめた最初のブロック」である可能性がある。式と枝の配置が確認できないので本研究は固定長の最大値を採る。ζ_THR の決め方への依存を避けるために Z-B（共有検出。M → N をイベントで行い ζ を使わない）を併置している。論文の注記「[6] に基づく再構成」に ζ の式・較正・ΔJ の符号・相対閾値をまとめて書く。

### 5.6 J_m の初期値・dwell・Z-B のイベント応答（メモ #6・#7・#9）
- [x] J(k) = 新しい H サンプルの誤差の平均二乗。J_m(−1) = J(0)（最初の hop の ΔJ = 0。[6] の「瞬時二乗誤差で初期化」と一致）。
- [x] dwell: run の開始と各切替（N → M、M → C、C → M、M → N、Z-B のイベントによる M → N）で 0 に戻し、hop ごとに 1 加える。判定は当該 hop の更新の後に行い、次の hop のモードを決める。「切替後 ≥ M_dwell hop」は dwell ≥ M_dwell。
- [x] Z-B: イベント [stop, tau] を受けた hop で、M（または C。Z-B に C は無い）なら dwell なしで N に切り替え、その hop の更新から N。N 中のイベントは何もしない（dwell も戻さない）。N → M は §1.2 の ΔJ 規則（dwell ≥ M_dwell）。
- [x] 切替時刻・モード・滞在 hop 数（`sw_log`、`sw_modes`）と、Z-B のイベント数を記録に残す（Rule 11 §3.4 の記述項目）。

### 5.7 M-P と経路 (b) の出力先（メモ #18・#21。Rule 11 §1.5 に加える）
| 出力先 | 内容 |
|---|---|
| `results/final_eval_meas_p_h/` | 11-D M-P（§9-7。S2 × 2 セル、like-for-like は `final_eval_meas_p_8a` の 12 基線、48 検定） |
| `results/final_eval_holdout_r11_envC/` | 経路 (b): 部屋 A holdout 15 手法の環境 C 再実行（E-PCG main を先に走らせ、`det_events*.jsonl` を同じディレクトリに保存） |
| `results/r11_ablation_holdout_envC/` | 経路 (b) の 11-A |
| `results/final_eval_holdout_r11_envC_new/` | 経路 (b) の 11-B/11-C 新基線の holdout |
| `results/protocol_r11_sel/provenance_<stage>.json` | 段（B1/B2/C）ごとの provenance（上書きしない。再開時は `*_resume<n>.json` を追加。レビュー L-3） |
| `results/r11_pipeline/` | pipeline のログ・状態フラグ・lock（ログだけ commit する。レビュー M-5） |
- 経路 A のときは Rule 11 §1.5 のディレクトリ。Rule 11 の出力ディレクトリ以外の `results/**` への書き込みはコードが拒否する（M-1 のガードを §8 で追加）。

### 5.8 条件付き再始動の細部（メモ #11。Rule 11 §4.3 の文言どおり、記録）
- P_pre = tau 以前に終わる直近 K = 32 hop の a priori 残差の hop 平均パワー（RLS ループ内で hop ごとに蓄積、CUSUM の q の log 前の量）の算術平均。P_post = その hop 開始時の w による [tau, stop) の a priori 残差の平均パワー。tau 前に完全な hop が無いときは再始動（θ = +∞ のときだけ keep。E-PCG の立ち上がり遅延により実際には起きない）。keep したイベントは `reset_hops` に入れない。`cond_log` に全イベント（hop、stop、tau、比 dB、pre hop 数、再始動の有無）を記録。`n_restarts` の列名は `n_events_given` に改め、実際の再始動数は `restart_hops` の長さとする（レビュー L-4）。

## 6. 実装メモの残りの判断（レビューが「範囲内、記録のみでよい」とした項目。本書で記録として固定）

| メモ # | 項目 | 判断（固定） |
|---|---|---|
| 1 | G5 のフラグの置き場所 | `EPCGConfig.solver`（`epcg.py`）。既定 `'pcg'` |
| 3 | MFBLMS の正規化 | 既存 `PowerTracker`（平滑化 0.8、正則化比 0.001）。正規化後に μ、時間域で先頭 M タップ。[31] の M_f 推定法は未確認で「既存 FD-FxNLMS と同じ正規化」と開示 |
| 5 | MFBLMS + det のグリッド | FD-FxNLMS + restart の 7 構成（det_boost {0.0625, 0.125, 0.25} × warm、{0, 0.0625, 0.125, 0.25} × cold）をそのまま、μ = 選択した μ_M、`mod: True` |
| 10 | smoke の μ_M | 選択前なので 0.1（smoke の MFBLMS の 1 点）。判定に使わない |
| 11 | 条件付き再始動の P_pre・P_post | §5.8 |
| 13 | 外側点の既存スコア | `selection_e.md` の記録値（2 桁）、CUSUM は `protocol_v2_sel_cusum/selected.json`。0.01 dB 以内は同値 |
| 16 | 「RLS 族のセル別最良」（§4.3 の記述） | 指標ごとに RLS・RLS + det・RLS + CUSUM・RLS + det (cond.) のうち中央値が最も低いものを最良とし、PCG-WLS との対差中央値。RLS + det + growth の 2 版は含めない（§4.3 の列挙どおり。表には別行で載る） |
| 17 | HL の CI | セルごとに `default_rng(0)`、シードの復元抽出 10 000 回、各回の Walsh 平均の中央値の 2.5/97.5 % 点 |
| 19 | 11-D M-S の記録 | 部屋名 `M_S`、`path_provenance` はシミュレータの値のまま、セット名は provenance.json に |
| 20 | shard の分け方 | 調整: 構成単位、コスト概算の貪欲割当（リストは末尾にしか伸びないので不変）。holdout/11-D: キーの crc32 % 2（9-A と同じ） |
| — | `results/protocol/selected_design.json` | slim 化で消えていた入力を archive ブランチから無変更で復元（sha256 020cc83b… でバイト一致）。[internal records omitted]（レビュー L-11） |
| — | コスト表（Rule 11 §3.3） | MFBLMS = `cost.fd_fxnlms(M, H) + 2 fft_flops(N)`、SW-FBLMS = N モード・M モードの各値（解析値）。論文の表を作る段階で加える。判定に影響しない（レビュー L-8） |
| — | Wiener 下限との距離（§5.3、M-S） | summary に各手法の成功 run の A2 中央値と下限の差を加える（記述。レビュー L-7） |

## 7. 予算の改定（Rule 11 §8「実時間予算 14–18 h」を改める）

| 項目 | Rule 11 | 実測ベース（実装メモ §4、2 プロセス、開発機） | 本書 |
|---|---|---|---|
| RLS 系 1 run | 5.3 s | 8–11 s（約 1.7 倍） | 実測を採る |
| G5 1 run | 3 s | 13–15 s | 同 |
| 経路 A | 11.5 h（任意込み 14 h） | 18–21 h | — |
| 経路 (b) | — | 22–25 h（15 手法の再実行 約 4 h を含む） | — |
| B-2 両版の追加（§2.2） | — | ＋約 2.5 h | — |
| **予算** | 14–18 h | — | **経路 (b): 予測 25–28 h、予算 28–32 h。経路 A: 予測 21–24 h、予算 24–28 h** |

- 予算は停止条件ではない（レビュー L-10）。超過しても手法・グリッドを削らない。超過の見込みが出たら実行担当は報告だけする。
- 順序は Rule 11 §0 のまま: B0（経路 (b) のみ）→ 11-A → B1 → B2 → C → holdout new → 11-D（B → C → SNR10 → M-S → M-P）。11-D は `selected.json` の `complete` が true になってから。
- 実装工数の追加: B-1・B-2・M-1〜M-6・テスト・手順書で約 0.5 日。

## 8. コード修正の要求一覧（本書の固定後、本実行の前。既定経路は変えない。各修正を commit・push）

| # | 対象 | 修正 | 確認 |
|---|---|---|---|
| B-1 | `prototype_new_algorithms.py` `_sw_hop`（1578 行付近） | N → M の判定を `0.0 <= dJ < sw_thr * Jm`（dwell 条件はそのまま） | `test_zeta_calibration_sequence` を新条件に更新。新テスト: J_m が増加中（ΔJ < 0）は dwell を満たしても N に留まる／J_m が緩やかに減少すると dwell 後に M へ。smoke の SW 2 行 × 3 セルを再実行 |
| B-2 | 同 R-RLS ループ（1751、1907–1908、3148–3149 行付近）、`revision11_methods.py` GRID11・`DET_NEW` | (a) `det_grow_start`（既定 False）を追加。False なら `_grow0` は再始動時にしか設定されず、run の開始には成長を適用しない（版 (i)）。True なら現行どおり開始にも適用（版 (ii)）。(b) 再始動（`_grow0[0] = _rls_from` の時点）で `w[1:] = 0`（m_eff(n=1) = 1）。(c) GRID11 に `'RLS + det + growth (from start)'`（`det_grow: 'half', det_grow_start: True`）を group として追加し、`DET_NEW` に加える。(d) `needs_events` が新名を正しく判定することを確認 | §6.3 (c1): 版 (i)・イベント無しの run が R-RLS λ 0.9999 δ 0.01 とビット一致（seed 300、ar1 S8）。(c2): 単体テストで再始動直後の `w[1:] == 0` と切り詰めタップ数 max(n//2, 1)。(c3): n ≥ 2M の更新式が既存と同一（コードレビュー）。`equivalence.md` を再生成。smoke の growth 行（両版 × 3 セル）を再実行 |
| B-3 | `revision11_methods.py`、`revision11_pipeline.py`、[run guide] §2・§6・§7、[internal records] | 定数 `RULE11A_SHA256` を置き、pipeline の各ジョブ起動時に `docs/current/REVISION_RULE_11a.md` の sha256 と照合（不一致なら起動しない）。`provenance.json` に `rule11a_sha256`・`holdout_base` を加える。手順書 §2 を §3.3 の c1–c8 に置き換え、§6 の「admissible なし → 停止」を「NOTE で進む」に、§7 に `rule11a_sha256` と M-S・M-P の `revision11.*` の確認を加える。[internal records] に本書の固定と sha256 を 1 行 | sha256 の転記値が一致。pipeline の空実行で照合が働く |
| M-1 | `revision11_holdout.py:109-111`、`revision11_methods.py` | Rule 11 の出力ディレクトリ（§1.5 ＋ §5.7、有効な holdout base の側だけ）以外への書き込みを共通の書き込みガードで拒否する（`PermissionError`）。とくに `provenance base` を経路 A で実行しても既存 `final_eval_holdout/provenance.json` を上書きしない | 単体テスト: 既存ディレクトリへの書き込みが例外になる |
| M-2 | `revision11_select.py`（`summary`、`stage_cfgs`）、`revision11_pipeline.py` | §4: `selected.json` に `inadmissible`（group と reason）を出す。MFBLMS が none なら B2 の 3 group を `inadmissible` に入れ、B2 を「run なしで完了」にする（例外にしない）。pipeline は `NOTE: no admissible configuration: …` を出して進む。`complete` の定義は「全 group が done または inadmissible」 | テスト: 合成記録で MFBLMS 全失敗 → `inadmissible` に 4 group、`complete` true、`new_rows` に含まれない |
| M-3 | `revision11_pipeline.py`（worker 起動時）、`revision11_methods.check_runtime_env` | ジョブの種類ごとに numpy/scipy の版を検査（調整・11-D・経路 (b) の holdout: 2.5.3/1.18.1、経路 A の holdout: 2.3.5/1.17.0）。合わなければ例外 | 空実行で確認 |
| M-4 | `revision11_holdout.py:80`、`revision11_select.py:34`、`revision11_rooms.py:38,45` | 書き込み途中で切れた最終行（改行で終わらない行）は、所有する shard が再開時に切り捨てて（完全な行は変えない）その run をやり直し、捨てたことを `worker_*.log` に `NOTE:` で残す。他 shard のファイルは読み飛ばす。summary は切れた行があれば例外（未完了） | 単体テスト: 途中で切れた行のあるファイルで再開できる |
| M-5 | `revision11_pipeline.py`、[run guide] §5 | pipeline 本体を切り離して起動する（`start` サブコマンド: 自身を `setsid nohup` で起動して戻る。同時に 1 つだけ、`results/r11_pipeline/lock`）。ログ・状態フラグ（`.running`/`.done`/`.stop`）は `results/r11_pipeline/`。中断後は同じ `start` コマンドで再開 | 空実行で `.done`／`.stop` が出る |
| M-6 | [run guide] §3 | `numba==0.68.1 soundfile==0.14.0` に固定（`measured_paths.write_provenance` が版を必須で読む） | 手順書の記述 |
| L-2 | `revision11_summary.py:219,251` | 部屋 A の `load_runs` に `revision11_holdout.saved_up()` を `extra_up` として渡す | 部分実行でも fill で止まらない |
| L-3 | `revision11_pipeline.py:76,93` | `protocol_r11_sel/provenance_<stage>.json` に分ける | ファイル |
| L-4 | `revision11_methods.py:209` | `n_restarts` → `n_events_given` | 列名 |
| L-7 | `revision11_summary.py:326-333` | M-S の summary に各手法の成功 run の A2 中央値と Wiener 下限の差（記述） | 表 |
| L-9 | `tests/test_revision11.py` | 追加: 有限 θ での `_cond_restart` の P_pre・P_post（手計算と照合）、`det_grow` の切り詰めタップ数と再始動後の末尾 0、`mfblms_cfgs` の端の延長（上 2 段・下 2 段）、`outer_decision` の分岐（失敗／内点／良い／2 段目良い／任意点は 2 段目なし）、M-2 の `inadmissible` | pytest |
| 再検証 | `revision11_preflight.py` | 修正後に `regress`（既定経路に触れないが念のため）、`equiv`（(a)(b)(c1)(c2)(c3)）、`smoke`（seed 300、全行）を再生成し `results/r11_preflight/` を更新（実行担当の環境でも §3.3 のとおり再実行） | §3.3 c3–c7 |

- 修正は B-1・B-2・M-2 のフラグの後ろの数行と、スクリプト・手順書の整備であり、既存の手法・記録・`eval_v2.GRID`・`selected_e.json`・既存 `results/**` には触れない。
- 本書の起草時点（62eb0a4）で、作業ツリーには M-1・M-3〜M-6・L-3 に当たる未コミットの修正（書き込みガード、環境検査、JSONL の再開、`start` サブコマンド、段ごとの provenance）が進行中だった。これらは本書の該当行に合うことを確認してから commit する。B-1・B-2・M-2・B-3 の修正はまだ無い。
- 本書の固定後は、本書に書いていない変更を本実行の前に加えない。必要なら Rule 11b を固定する。

## 9. 固定後のチェックリスト
- [ ] 本書を commit（本書の sha256 を [run guide] §2・§7、[internal records]、`revision11_methods.RULE11A_SHA256` に転記）
- [ ] §8 のコード修正 → `pytest` → §6.1・§6.3・§6.4 の再生成 → 内部の差分レビュー（ブロッカーなし）
- [ ]実行担当: §3.3 の c1–c8 → B0（経路 (b)）→ 11-A → B1 → B2 → C → holdout new → 11-D（B → C → SNR10 → M-S → M-P）
- [ ] 集約: F1/F2/F3、like-for-like、経路 (b) の 15 手法の参考ラベルと 390 族の一致数、[internal records omitted]、tab:rules に 11/11a の行
- [ ] **結果を見てからの取捨選択（著者）**: Rule 11 §1.7 の基準で本文に載せる場所を決める。数値・ラベル・family は変えない

## 追記（固定前、2026-11-07）: Python の版の検査
- 環境の検査は Python の major.minor（環境 A 3.12、環境 C 3.13）と numpy・scipy・pyroomacoustics（meas は numba・soundfile も）の完全な版で行う。Python の patch は provenance に記録するだけで、停止条件にしない（Rule 11 §1.2 の「3.13.18」と手順書の「3.13.x」の食い違いをこの形で解消する）。
