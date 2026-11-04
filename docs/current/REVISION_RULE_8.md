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
