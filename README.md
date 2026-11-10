# Feedforward ANC: reproducibility snapshot

This directory contains the source, test suite, configurations, archived
summaries and the inputs required to reproduce the manuscript's LaTeX tables.
It is release v1.2.0.

The result records are archived at Zenodo. To cite them, use the concept DOI
https://doi.org/10.5281/zenodo.23965830. It covers all versions and resolves to the latest one.
The v1.0.0 record has the version DOI https://doi.org/10.5281/zenodo.23965831 and holds the
result archives of section v1.0.0 of `ZENODO_MANIFEST.txt`. Zenodo version v1.2.0 adds the
Revision 11 records (section v1.2.0); its version DOI is TODO (to be filled in when the version is
published). Zenodo version v1.2.0 holds two kinds of files: the source zip of code release v1.2.0 (this repository at
tag v1.2.0, including the summaries, metrics and provenance under `results/`) and the tar archives of the run-level
records and logs listed in `ZENODO_MANIFEST.txt`. The underlying MeshRIR dataset is separately available and attributed at
https://doi.org/10.5281/zenodo.5500451.

## Changes in v1.2.0

Release v1.2.0 follows v1.0.0. The renaming prepared after v1.0.0 (commit c6a08bc, intended as v1.1.0) was not
released separately and is part of v1.2.0.

- Method name: E-PCG is called PCG-WLS (see "Method name" below); the former names still work.
- Revision 11 (rules `docs/current/REVISION_RULE_11.md`, `11a.md`, `11b.md`): added baselines (MFBLMS, switching
  FD-FxNLMS [6] with its own or the shared detector, RLS + det with conditional restart or growing order, and the
  outer grid points of RLS, VFF-RLS, RLS + CUSUM, FD-FxNLMS, FDKF and FD-FxNLMS + det), the ablation of PCG-WLS, and the
  holdout re-evaluation (seeds 800-839) of rooms B and C, SNR 10 dB and the measured paths M-S and M-P.
  Code: `experiments/revision11_*.py`, the `mod` gradient (`ffanc_norm.fd_fxnlms.fd_block_gradient_mod`), the method
  `SW-FBLMS`, the R-RLS flags `det_cond_db`, `det_cond_k`, `det_grow`, `det_grow_start`, and `solver='exact'` of
  `PcgWlsConfig`; defaults are unchanged. Tests: `tests/test_revision11.py`.
- Records in `results/`: `r11_preflight`, `protocol_r11_sel`, `final_eval_holdout_r11`, `r11_ablation_holdout`,
  `eval_roomB_h`, `eval_roomC_h`, `eval_snr10_h`, `final_eval_meas_s_h`, `final_eval_meas_p_h`, the descriptive
  `detector_aggregates` and the screening `conventional_limit_benchmark`. Inputs of the Revision 11 runners that were
  missing before: `results/det_events/` (shared detections for tuning), `results/protocol_v2_sel_cusum/selected.json`,
  `results/protocol/selected_design.json` and `results/final_dev/final_config_v6_5.json`.
- Tables: `make_tables.py` writes the Revision 11 tables (`tables/ablation.tex`, `rooms_bc_h.tex`,
  `snr_measured_h.tex`, `supp_tables/r11_*.tex`); `make_r11_values.py` writes `tables/r11_values.tex`;
  `make_detector_aggregates.py` writes `results/detector_aggregates/` and `paper/v2/tables_detector/`.
  The supplement is now a short two-column document: `make_supplement.py` writes only its tables to `supp_tables/`.
  The former long-layout tables (identical to those of v1.0.0 and c6a08bc) are in `supp_tables_all/`
  (`make_supplement.py --all --output paper/v2/supp_tables_all`). `make_r10_values.py` regenerates the long-layout
  settings table in a temporary directory when `supp_tables/settings.tex` is absent.
- `make_zenodo_archive.py` archives one manifest section (`--section`) and splits the archive (`--max-mib`).
- `experiments/revision11_pipeline.py` performs no git operation unless `R11_GIT=1` (then it commits with your own git
  configuration; push only with `R11_PUSH=<remote>`).

## Method name

The method is called PCG-WLS (PCG for windowed least squares) in the paper and in this code from v1.2.0.
Earlier records use the former name E-PCG. These are the files under `results/` (including the Revision 11 records,
which use the same record labels), the rule documents in `docs/current/`, and the Zenodo records (v1.0.0 DOI
10.5281/zenodo.23965831, and the Revision 11 records of version v1.2.0). The multi-window variant was called
E-PCG (bank) and is now PCG-WLS (multi-window).

The implementation is in `ffanc_norm.pcg_wls` (`PcgWls`, `PcgWlsConfig`) and `ffanc_norm.pcg_wls_mw`
(`PcgWlsMultiWindow`). The former modules `ffanc_norm.epcg` and `ffanc_norm.epcg_bank`, the function
`cost.epcg_model` and the runner key `E-PCG-F` still work and emit a DeprecationWarning. Saved configurations
under `results/` are read unchanged, and their method key is mapped to `PCG-WLS-F` on loading
(`ffanc_norm.naming.load_config`). The runners in `experiments/` keep the record labels `E-PCG` and
`E-PCG bank`, so new runs can be resumed from and compared with the archived records. The table and figure
generators show the new names. The renaming changes no numerical result.

## Environment

Create a virtual environment and install the locked requirements:

```sh
python3 -m venv .venv
. .venv/bin/activate
pip install -r requirements-lock.txt
pip install -e '.[dev]'          # add ',opt' for the optional optimizer tests: '.[dev,opt]'
pip install pyroomacoustics==0.10.1
```

Table generation uses
NumPy and SciPy; Matplotlib is needed for plots. The original experiment sets
were not all run in one numerical environment: holdout and CUSUM selection used
NumPy 2.3.5 / SciPy 1.17.0, while the additional rooms and measured stationary
set used NumPy 2.5.3 / SciPy 1.18.1 with pyroomacoustics 0.10.1. For experiments,
install the appropriate versions and use `RLS_FAST=1` with one BLAS thread.
The locked environment describes the table/plot generation environment, not a
promise that it reproduces every simulation bit for bit. Changing NumPy, SciPy,
BLAS, or hardware can alter floating-point trajectories and prevent bitwise
reproduction; use the archived summaries and rules for the conditions and scope.

The room impulse responses of pyroomacoustics 0.10.1 also depend on its thread count. It is set by
`PRA_NUM_THREADS` (default: the number of CPUs; `OMP_NUM_THREADS` has no effect on it). The image sources are summed
in float32 in blocks per thread, so a different thread count changes the uncontrolled power by about 1e-7 to 1e-6
relative, and the controlled trajectories follow. The records were made with 2 threads (v2e, 8a, 9-C, 9-D and the
Revision 11 tuning and 11-D sets) or 3 threads (9-A, 9-B and the Revision 11 room-A holdout sets). Set
`PRA_NUM_THREADS` to the value of the set you reproduce (Rule 11b). The Revision 11 environments were:

| Revision 11 set | Python / NumPy / SciPy / pyroomacoustics | `PRA_NUM_THREADS` | Environment class (Rule 11b) |
|---|---|---|---|
| room-A holdout: `final_eval_holdout_r11`, `r11_ablation_holdout` | 3.12.14 / 2.3.5 / 1.17.0 / 0.10.1 | 3 | I (path A, joined with `final_eval_holdout`) |
| tuning: `protocol_r11_sel` | 3.13.5 / 2.5.3 / 1.18.1 / 0.10.1 | 2 | I |
| 11-D: `eval_roomB_h`, `eval_roomC_h`, `eval_snr10_h`, `final_eval_meas_s_h`, `final_eval_meas_p_h` | 3.13.5 / 2.5.3 / 1.18.1 / 0.10.1 | 2 | I |

All Revision 11 sets ran on one machine (Intel Xeon Platinum 8573C, 3 CPUs, OpenBLAS core SkylakeX) with `RLS_FAST=1`
and one BLAS thread per process; the fingerprint is in each `provenance.json` (`machine`).

One simulation run (room A, AR(1) noise, 30 cm source move, holdout seed 800, 5 s, PCG-WLS main configuration):

```sh
RLS_FAST=1 OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 PRA_NUM_THREADS=3 python -c "import sys; sys.path[:0] = ['src', 'experiments']; import eval_v2 as ev; r = ev.D.P.run(ev.cfg_of('A', 'ar1', 'S2 src 30cm'), 800, 'PCG-WLS-F', dict(ev.MAIN), 5.0, ev.D.CH); print(r['stable'], r['reset_hops'])"
```

The run prints `True [62]`: the stability flag, and the hop at which the detector reset the window (the stored
holdout record for this key has its event at sample 8064, and 8064 // 128 - 1 = 62). With other library versions or
another `PRA_NUM_THREADS`, the floating-point values can differ slightly (see above), but the event hop is expected to
be the same.

The Revision 11 jobs are run with `experiments/revision11_pipeline.py` (see its docstring; git operations are off
unless `R11_GIT=1`). The preflight `experiments/revision11_preflight.py regress` compares against a development commit
(b3058bf) that is not public, so it cannot be re-run from this repository; its result is
`results/r11_preflight/regression.md`. The checks that re-run saved keys (`envA`, `envC`) need the run-level
records of the Zenodo archives; all preflight checks write into `results/r11_preflight/`.

## Reproduce tables without running an experiment

From this directory:

```sh
python paper/v2/make_tables.py
python paper/v2/make_supplement.py
python paper/v2/make_r9_values.py
python paper/v2/make_r10_values.py
python paper/v2/make_r11_values.py
python paper/v2/make_detector_aggregates.py --results-dir /tmp/det --tex-dir /tmp/det_tex   # compare with results/detector_aggregates
python paper/v2/make_supplement.py --all --output /tmp/supp_all                          # compare with supp_tables_all
```

The generated LaTeX tables under `paper/v2/tables/` and `supp_tables/` are
included for comparison; they are byte-identical to the tables of the manuscript build (except `sources.json`, see
below). `make_tables.py` also writes the merged tables used in the manuscript: `rooms_bc_h.tex` and
`snr_measured_h.tex` (holdout seeds, Revision 11), the earlier `rooms_bc.tex` (rooms B and C) and `snr_measured.tex`
(SNR 10 dB and MeshRIR), and `ablation.tex`. Without arguments `make_detector_aggregates.py` overwrites the archived
`results/detector_aggregates/` (including its `provenance.json`); give other directories to compare. The JSON and
Markdown outputs are byte-identical; the regenerated `provenance.json` differs in the commit and, with another Python or
NumPy, in the recorded versions. Generation recomputes the archived paired comparisons;
the saved decisions are checked during the run. This procedure does not perform
new simulations. The supplementary `sources.json` records hashes of the public
copies of inputs and therefore differs from the original private source manifest.

For the public snapshot, non-scientific workflow identifiers are redacted from
some protocol and provenance copies. `REDACTION_MANIFEST.json` records both the
original file digest and the digest of each redacted copy. The supplementary
generator accepts either an exact original digest or this explicit mapping; it
checks that the stored original digest agrees with the archived provenance and
that the release copy has the listed digest. The Revision 11 runners (`revision11_methods.check_rules`) accept the
redacted copies of Rules 11, 11a and 11b in the same way. In the Revision 11 provenance copies only the interpreter path
(`executable`) is replaced by `[absolute-path]` and embedded rule texts are replaced by the public rule copies; the
machine fingerprint is kept. The mapping is not a substitute for
possession of the original documents or independent verification of their contents.
Numeric records, decisions, parameters, and scientific calculations are unchanged.

## Figures and large records

The summaries (`summary.md`, `summary.json`), per-run metrics (`metrics.jsonl`) and provenance files under `results/`
are part of this repository, and therefore of the code release and its source zip in Zenodo version v1.2.0.
Binary arrays, run-level files, logs and rendered figures are not included here. The paths
and byte sizes of the archived files are in `ZENODO_MANIFEST.txt`. Section v1.0.0 is in the v1.0.0
Zenodo record (https://doi.org/10.5281/zenodo.23965831) as `pcg-ffanc-results-part1.tar`
and `pcg-ffanc-results-part2.tar`. Section v1.2.0 (Revision 11 run-level records, logs and one reference array) is in
Zenodo version v1.2.0 (version DOI: TODO) as `pcg-ffanc-results-v1.2.0-part1.tar` and
`pcg-ffanc-results-v1.2.0-part2.tar`; that version also carries the two v1.0.0 archives. Extract all of them into this
directory to restore the listed paths (the reference array `results/r11_preflight/ref_localize_roomB_ar1_S8_480.npz`
of the `localize` check was made on the development machine, not on the machine of the Revision 11 runs). Then `python paper/v2/make_figures.py learning learning_all excess cost shat` can
render the corresponding plots from stored inputs. The cost and secondary-path figures
(`cost`, `shat`) need only files in this repository. The eigenvalue figure's
original generator computes new signal realizations; it is not part of the
no-experiment table reproduction. Inspect the separate archive, especially its
logs, for sensitive information and confirm licensing before publication.

The data include derived statistics from the separately distributed MeshRIR
measurements. Changes made to the MeshRIR impulse responses before use: removal of the common system delay (Rule 8a),
resampling to 8 kHz, truncation to 1200 (primary path) and 512 (secondary path) taps, and normalization of the
initial paths. The impulse responses themselves are not redistributed; `results/r11_preflight/meshrir_holdout_allocation.json`
lists the source and microphone indices and coordinates used. Retain the dataset's license and attribution when reusing them.
Code is MIT-licensed; archived data and documentation are CC BY 4.0 as detailed
in `LICENSE`.

## Setup, sources, and citation

The recorded holdout runs used Python 3.12.14; the room and SNR 10 dB runs of Revision 9 (`eval_*_x2`) used Python
3.13.18 and the measured-stationary set (`final_eval_meas_s_8a`) used Python 3.13.5. The
minimum supported Python version is 3.10. Install the package and test tools
with `pip install -e '.[dev]'`; run the test suite with
`RLS_FAST=1 OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 PRA_NUM_THREADS=2 pytest`
(the Revision 11 tests check `PRA_NUM_THREADS`). Install
`pyroomacoustics==0.10.1` for the room simulations. The Revision 11 room-A holdout runs used Python 3.12.14; the
Revision 11 tuning and 11-D runs used Python 3.13.5 (see the table under Environment). The separate
`requirements-numpy253.txt` lists the recorded direct versions for the
NumPy 2.5.3 environment; it is not a fully resolved transitive lock file.
A platform-specific lock should be resolved and verified before use. Do not
expect bitwise equality across NumPy or BLAS versions.

The provenance commit hashes refer to a development history that is not
included in the public repository. The `scripts_sha256` of the Revision 11 provenance records hash the development
copies of the scripts; the public copies of `prototype_new_algorithms.py` and `src/ffanc_norm/epcg.py` differ from them
by the renaming, and the redacted or adapted copies are listed in `REDACTION_MANIFEST.json`. See `CITATION.cff` for citation metadata.
To cite the result records, use the Zenodo concept DOI https://doi.org/10.5281/zenodo.23965830.
The v1.0.0 record is https://doi.org/10.5281/zenodo.23965831; the version DOI of v1.2.0 is TODO.

The measured-path inputs use MeshRIR by Shoichi Koyama, Tomoya Nishida,
Keisuke Kimura, Takumi Abe, Natsuki Ueno, and Jesper Brunnström: “MeshRIR:
A Dataset of Room Impulse Responses on Meshed Grid Points for Evaluating
Sound Field Analysis and Synthesis Methods,” WASPAA 2021,
https://doi.org/10.1109/WASPAA52581.2021.9632672. Dataset:
https://doi.org/10.5281/zenodo.5500451 (CC BY 4.0).

### Artifact inputs

| Artifact | Generator | Archived inputs |
|---|---|---|
| Main, room, measured, cost and CUSUM tables | `paper/v2/make_tables.py` | `results/final_eval_holdout`, `eval_roomB_x2`, `eval_roomC_x2`, `eval_snr10_x2`, `final_eval_meas_*`, `extra_eval` and CUSUM summaries |
| Supplementary tables | `paper/v2/make_supplement.py` | archived summaries and metrics in `results/`; detailed paths appear in each generated table and `sources.json` |
| Revision 9 and 10 values | `paper/v2/make_r9_values.py`, `make_r10_values.py` | corresponding holdout, room, measured and `gap_check4*` summaries and numeric records |
| Revision 11 values (`tables/r11_values.tex`) | `paper/v2/make_r11_values.py` | `results/final_eval_holdout_r11`, `r11_ablation_holdout`, `protocol_r11_sel`, `eval_{roomB,roomC,snr10}_h`, `final_eval_meas_{s,p}_h`, `final_eval_holdout` |
| Ablation, holdout rooms and SNR/measured tables, added baselines, HL intervals | `paper/v2/make_tables.py` | the same Revision 11 records |
| Detector delays and R2 failures (descriptive) | `paper/v2/make_detector_aggregates.py` | `results/final_eval_holdout/det_events_*.jsonl`, `results/eval_room{B,C}_x2/metrics.jsonl` |
| Learning | `paper/v2/make_figures.py learning learning_all` | `results/final_eval_holdout/curves.npz` |
| Excess | `paper/v2/make_figures.py excess` | `results/gap_check2/curves.npz` and optional `results/gap_check3/curves.npz` |
| Cost | `paper/v2/make_figures.py cost` | `results/extra_eval/summary.md`, `results/final_eval_v2e/metrics.jsonl` |
| Secondary-path error | `paper/v2/make_figures.py shat` | `results/extra_eval/summary.md` |
| Other time figures | `paper/v2/make_times_figures.py` | saved arrays listed by the generator |

To prepare an archive after checking its sources, run
`python make_zenodo_archive.py SOURCE_ROOT OUTPUT_TAR [--section v1.2.0] [--max-mib 300]` from this directory.
The script validates the manifest and sanitizes absolute filesystem paths in
log copies; it leaves source files untouched. Review the archive and licensing
before upload. The run-level records and logs are in the Zenodo record above, not in this repository; the summaries
are in this repository (and in the source zip of the code release in Zenodo version v1.2.0).

The optional optimizer tests require the optional `optuna` package. When it is
not installed, those tests are skipped; they are unrelated to reproducing the
archived tables. `optuna` is not in the `dev` extra; install it with `pip install -e '.[dev,opt]'` (or
`pip install optuna`) to run them.

The measured-path wiring tests also require the separately licensed MeshRIR
S32-M441 dataset and its verified-download marker. They skip when those files
are absent; obtain and verify the original dataset to exercise those tests.

### Obtain and verify MeshRIR for measured-path tests

Download the official MeshRIR v1.1 `S32-M441_npy.zip` from
https://doi.org/10.5281/zenodo.5500451 into `data/meshrir/`. From the
snapshot root, check its published digest and extract it:

```sh
mkdir -p data/meshrir
printf '%s  %s\n' 4fcd6137bcadb6914d4170ff366c86f9 data/meshrir/S32-M441_npy.zip | md5sum -c -
unzip -t data/meshrir/S32-M441_npy.zip
unzip data/meshrir/S32-M441_npy.zip -d data/meshrir
test -f data/meshrir/S32-M441_npy/pos_mic.npy
test -f data/meshrir/S32-M441_npy/pos_src.npy
test -f data/meshrir/S32-M441_npy/ir_0.npy
```

After all of those checks succeed, record the verified-download marker used by
the tests (the marker's existence alone is not a checksum verification):

```sh
python - <<'PY'
import hashlib, json
from pathlib import Path
root = Path('data/meshrir')
with (root / 'S32-M441_npy.zip').open('rb') as f:
    md5 = hashlib.file_digest(f, 'md5').hexdigest()
if md5 != '4fcd6137bcadb6914d4170ff366c86f9':
    raise SystemExit('MeshRIR checksum mismatch')
(root / 'download_verified.json').write_text(json.dumps({
    'dataset': 'MeshRIR v1.1 S32-M441', 'archive_md5': md5,
    'source_doi': '10.5281/zenodo.5500451'
}, indent=2) + '\n')
PY
```

The dataset is distributed separately under its own license and is excluded
from this snapshot. Do not create the marker for an unverified or incomplete
extraction. The measured-path tests need the extracted impulse responses, not
only the archive and marker.

The history-access and inverse-survival diagnostics include their archived
preregistration documents, per-case profile JSON files and summary under
`docs/current/RINGBUF*` and `results/ringbuf*`. The compressed per-access
records are listed in `ZENODO_MANIFEST.txt` for the separate archive. These
are recorded diagnostics; they do not bound behavior on future runs.
