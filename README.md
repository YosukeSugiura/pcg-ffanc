# PCG-WLS for feedforward active noise control

This repository contains the code, configurations and result summaries of the paper
"Preconditioned Conjugate Gradients for Fast-Tracking Feedforward Active Noise Control" (Y. Sugiura).

PCG-WLS (preconditioned conjugate gradients for windowed least squares) is an adaptive controller for single-channel
feedforward active noise control. It solves the exact windowed least-squares problem of the modified filtered-x
structure by conjugate gradients. The preconditioner is the circulant gain of frequency-domain filtered-x NLMS. A
two-stage change detector, Stein weighting of the pre-change data and a controller order that grows after a restart
handle acoustic changes. The repository also contains the baselines of the paper (FD-FxNLMS and its variants, FDKF,
RLS, VFF-RLS, fast transversal RLS filters, detector-restarted versions, MFBLMS and the switching algorithm) and the
simulation of the image-source rooms and the measured paths.

## Contents

| Path | Content |
|---|---|
| `src/ffanc_norm/` | Python package: PCG-WLS (`pcg_wls`, `pcg_wls_mw`), baselines, simulation, cost counting |
| `experiments/` | Runners of the tuning, evaluation and diagnostic runs |
| `configs/` | Room and path configurations |
| `results/` | Summaries (`summary.md`, `summary.json`), per-run metrics (`metrics.jsonl`) and provenance of all runs |
| `docs/current/` | Rule documents that fixed the decision rules before the runs they govern |
| `paper/v2/` | Generators of the tables and figures of the paper |
| `tests/` | Test suite |

## Correspondence to the paper

| Paper | Generator | Records in `results/` |
|---|---|---|
| Tables II and III (main room, holdout seeds) | `paper/v2/make_tables.py` | `final_eval_holdout`, `final_eval_holdout_r11` |
| Table IV (ablation) | `paper/v2/make_tables.py` | `r11_ablation_holdout` |
| Table V (rooms B and C) | `paper/v2/make_tables.py` | `eval_roomB_h`, `eval_roomC_h` |
| Table VI (SNR 10 dB, measured paths) | `paper/v2/make_tables.py` | `eval_snr10_h`, `final_eval_meas_s_h`, `final_eval_meas_p_h` |
| Numbers in the text | `paper/v2/make_r9_values.py`, `make_r10_values.py`, `make_r11_values.py` | summaries listed in each script |
| Supplementary tables | `paper/v2/make_tables.py`, `paper/v2/make_supplement.py` | as above |
| Figures | `paper/v2/make_figures.py`, `paper/v2/make_times_figures.py` | `final_eval_holdout/curves.npz`, `gap_check2/`, `extra_eval/` |

The supplementary material of the paper lists the result directory of every reported quantity.

## Installation

Python 3.11 or later (the package installs on 3.10, but the MeshRIR check below uses `hashlib.file_digest`). Create a virtual environment and install the package with the locked requirements:

```sh
python3 -m venv .venv
. .venv/bin/activate
pip install -r requirements-lock.txt
pip install -e '.[dev]'          # '.[dev,opt]' adds the optional optimizer tests
pip install pyroomacoustics==0.10.1
```

## Tests

```sh
RLS_FAST=1 OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 PRA_NUM_THREADS=2 python -m pytest -q
```

Tests that need the optional `optuna` package or the MeshRIR dataset are skipped when these are absent.

## Reproducing the tables

The tables are generated from the stored summaries and per-run metrics. No simulation is run:

```sh
python paper/v2/make_tables.py
python paper/v2/make_supplement.py
python paper/v2/make_r9_values.py
python paper/v2/make_r10_values.py
python paper/v2/make_r11_values.py
git status --short paper/v2      # no output: the regenerated files equal the stored ones
```

The generators recompute the paired tests and check them against the stored decisions.

## Running simulations

Simulations use `RLS_FAST=1` and one BLAS thread per process. One run (main room, AR(1) noise, 30 cm source move,
seed 800, 5 s, PCG-WLS):

```sh
RLS_FAST=1 OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 PRA_NUM_THREADS=3 python -c "import sys; sys.path[:0] = ['src', 'experiments']; import eval_v2 as ev; r = ev.D.P.run(ev.cfg_of('A', 'ar1', 'S2 src 30cm'), 800, 'PCG-WLS-F', dict(ev.MAIN), 5.0, ev.D.CH); print(r['stable'], r['reset_hops'])"
```

It prints `True [62]` (stable run, detector restart at hop 62).

Floating-point trajectories depend on the NumPy, SciPy and BLAS versions and on the thread count of pyroomacoustics
(`PRA_NUM_THREADS`; `OMP_NUM_THREADS` does not set it). The image sources are summed in float32 per thread, so the
thread count changes the uncontrolled power by about 1e-7 to 1e-6 relative. Each `provenance.json` in `results/`
records the versions and the thread count of its runs. The main-room holdout runs used Python 3.12, NumPy 2.3.5,
SciPy 1.17.0 and 3 threads. The runs outside the main room used Python 3.13, NumPy 2.5.3, SciPy 1.18.1 and 2 threads.
Bitwise reproduction requires the same environment.

## Data

The run-level records, logs and arrays are archived at Zenodo, version DOI
[10.5281/zenodo.24103221](https://doi.org/10.5281/zenodo.24103221). That version also holds a source zip of this
release (tag v1.2.0). Extract the archives into the repository root to restore the paths listed in
`ZENODO_MANIFEST.txt`.

### MeshRIR

The measured paths use MeshRIR v1.1 (subset S32-M441) by S. Koyama, T. Nishida, K. Kimura, T. Abe, N. Ueno and
J. Brunnström, "MeshRIR: A dataset of room impulse responses on meshed grid points for evaluating sound field analysis
and synthesis methods," WASPAA 2021, https://doi.org/10.1109/WASPAA52581.2021.9632672. Dataset:
https://doi.org/10.5281/zenodo.5500451 (CC BY 4.0). The impulse responses are not redistributed here. Before use, the
common latency of the measurement system was removed, and the responses were resampled to 8 kHz, truncated to 1200
(primary path) and 512 (secondary path) taps and normalized. `results/r11_preflight/meshrir_holdout_allocation.json`
lists the source and microphone indices used.

To run the measured-path tests, download `S32-M441_npy.zip` from the dataset DOI into `data/meshrir/`, verify it and
record the marker used by the tests:

```sh
mkdir -p data/meshrir
printf '%s  %s\n' 4fcd6137bcadb6914d4170ff366c86f9 data/meshrir/S32-M441_npy.zip | md5sum -c -
unzip data/meshrir/S32-M441_npy.zip -d data/meshrir
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
    'source_doi': '10.5281/zenodo.5500451'}, indent=2) + '\n')
PY
```

## License and citation

Code: MIT. Archived data and documentation: CC BY 4.0. See `LICENSE`. Citation metadata are in `CITATION.cff`.

## Notes on the archived records

The stored records, rule documents and runner keys label the method with its former name E-PCG (multi-window variant:
E-PCG bank). The table and figure generators show the name PCG-WLS. The rule documents are in `docs/current/`.
