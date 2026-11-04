# Revision 10a: Prop. rho の数値検証の訂正（2026-11-04 JST）

**本書は Rule 10 の結果（`results/gap_check4/`）と、その 1 seed 診断（seed 300、`results/gap_check4_diag/`）を見た後に作成した訂正版である。** Rule 8a と同じく、結果を見る前の事前登録ではない。Rule 10 の判定（ar1・harmonic とも乖離）は撤回せず、そのまま残す。

## 1. 位置づけ
Rule 10 の登録設定 `V-SCHED{cum}` は、次の 2 点で Prop. rho の数学的対象を写していなかった。10a はその訂正で、自由パラメータを持たない（チューニングではない）。
- (i) cold start のフレーム充填: 最初の 7 hop は N サンプルのフレームが (b+1)H しか埋まらず、実効ゲインが理論の最大 8 倍になる。
- (ii) 作用素の違い: 論文 eq.(fd) は K=P F⁻¹D⁻¹F Pᵀ（循環相関をラグ 0..M−1 に切ってから正規化）。実装の `fd_block_gradient` は N ラグ全体を正規化してから制約する標準の gradient-constrained FDAF。
結果の扱いは Rule 10 §2 と同じく記述のみで、検定は行わない。

## 2. 対象（固定）
- S8 stationary、M=512、N=2M、H=128、seed 300–309、ar1・harmonic。主判定は T=5 s、副判定は T=20 s の別実行（同じシード）。
- 再帰 A（命題の対象）: 循環相関 c を求めて c[M:]=0 とし、g=F⁻¹(F c / den_b)[:M]、den_b=(b+1)·H·S_k。S_k はその実行の全区間平均ビンパワー（gap_check.py と同じ定義、固定。非因果の oracle であることを開示する）。step 1、正則化なし、w₀=0。
- 再帰 B（記述用）: 同じ den_b・step 1 で `fd_block_gradient`（実装の標準形）。
- 参照: w_LS＝全区間 LS（Toeplitz）、理論 excess σ²M/(Hb)（σ²＝oracle floor の平均）。Rule 10 の exact LS（R-RLS lam 1）は T=5 s で再計算し、残差パワー比を記述的に併記する。

## 3. 指標
- w-excess(b)=(w_b−w_LS)ᵀR(w_b−w_LS)（R は全区間の Toeplitz 推定）。比＝10log10(アンサンブル平均 w-excess の区間平均 / σ²M/(Hb) の区間平均)。区間は 1–8、8–32、32–100、100–312。T=20 s では 312–625、625–1250 も加える。
- slope は下限 1e-12 で切った hop を除外し、hop 番号は 1 始まりで log-log 回帰する（Rule 10 の slope の不具合の訂正）。

## 4. 判定
- 主（Rule 10 と同一）: ar1、再帰 A、T=5 s、100–312 の比と +0.07 dB（gap_check の ρ_c 中央値）の差が 1 dB 以内 → 一致。超える → 乖離（Rule 10 §2 の文「5 s では漸近値に達していない」を、32–100→100–312 の変化とあわせて書く）。
- 副（10a で追加。有限時間の効果を分けるため）: ar1、再帰 A、T=20 s、625–1250 の比と +0.07 dB の差が 1 dB 以内 → 「20 s で漸近値と 1 dB 以内で一致」。超える → 観測値をそのまま書く。1 seed 診断で 625–1250 が −0.6 dB だったことを開示する。
- harmonic: 再帰 A・B とも、無正則化・固定 C では数値的に発散する（1 seed 診断）ため、この再帰では検証不能と事前に宣言する。実行はするが判定しない（‖w‖>1e6 または非有限になったら以降を NaN と記録）。代わりに、A（K R）と B（実装の平均更新行列）の固有値を 10 seed で表にし、λ<1/2 の割合を報告する（記述）。

## 5. 記述的出力（判定なし）
- 再帰 B の T=20 s の w-excess（区間比と最終 hop の値、floor 比）と、平均場の不動点から得る bias の予測値（floor 比 dB、10 seed）を並べる。論文には「標準形は u≠0 で biased（既知: Lu 2014、Yang 2021。本文確認後に引用）、本セルでは floor 比 約 −x dB」とだけ書く。

## 6. 出力と手順
- `experiments/gap_check4a.py`、出力 `results/gap_check4a/`（summary.md、numeric.json、curves.npz、provenance.json: commit・本ルールの sha256・版・環境）。既存の `results/gap_check4*/` は変更しない。
- 1 ジョブ（setsid nohup）、`RLS_FAST=1`、1 スレッド。結果を見てから設定・区間・閾値を変えない。数値的な問題が出たら停止して報告する。
