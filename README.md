# Feedforward ANC: reproducibility snapshot

This directory contains the source, test suite, configurations, archived
summaries and the inputs required to reproduce the manuscript's LaTeX tables.
It is a preparation snapshot; no release identifier or archival DOI has been
assigned. The underlying MeshRIR dataset is separately available and attributed
at https://doi.org/10.5281/zenodo.5500451.

## Environment

Install Python and `pip install -r requirements-lock.txt`. Table generation uses
NumPy and SciPy; Matplotlib is needed for plots. The original experiment sets
were not all run in one numerical environment: holdout and CUSUM selection used
NumPy 2.3.5 / SciPy 1.17.0, while the additional rooms and measured stationary
set used NumPy 2.5.3 / SciPy 1.18.1 with pyroomacoustics 0.10.1. For experiments,
install the appropriate versions and use `RLS_FAST=1` with one BLAS thread.
The locked environment describes the table/plot generation environment, not a
promise that it reproduces every simulation bit for bit. Changing NumPy, SciPy,
BLAS, or hardware can alter floating-point trajectories and prevent bitwise
reproduction; use the archived summaries and rules for the conditions and scope.

## Reproduce tables without running an experiment

From this directory:

```sh
python paper/v2/make_tables.py
python paper/v2/make_supplement.py
python paper/v2/make_r9_values.py
python paper/v2/make_r10_values.py
```

The generated LaTeX tables under `paper/v2/tables/` and `supp_tables/` are
included for comparison. Generation recomputes the archived paired comparisons;
the saved decisions are checked during the run. This procedure does not perform
new simulations. The supplementary `sources.json` records hashes of the public
copies of inputs and therefore differs from the original private source manifest.

For the public snapshot, non-scientific workflow identifiers are redacted from
some protocol and provenance copies. `REDACTION_MANIFEST.json` records both the
original file digest and the digest of each redacted copy. The supplementary
generator accepts either an exact original digest or this explicit mapping; it
checks that the stored original digest agrees with the archived provenance and
that the release copy has the listed digest. The mapping is not a substitute for
possession of the original documents or independent verification of their contents.
Numeric records, decisions, parameters, and scientific calculations are unchanged.

## Figures and large records

Binary arrays, run-level files and logs are not included. Their candidate paths
and byte sizes are in `ZENODO_MANIFEST.txt`; no archive has been created or
uploaded. After obtaining an authorized archive and restoring the files at the
listed paths, `python paper/v2/make_figures.py learning learning_all excess cost shat` can
render the corresponding plots from stored inputs. The eigenvalue figure's
original generator computes new signal realizations; it is not part of the
no-experiment table reproduction. Inspect the separate archive, especially its
logs, for sensitive information and confirm licensing before publication.

The data include derived statistics from the separately distributed MeshRIR
measurements. Retain the dataset's license and attribution when reusing them.
Code is MIT-licensed; archived data and documentation are CC BY 4.0 as detailed
in `LICENSE`.

## Setup, sources, and citation

The recorded holdout runs used Python 3.12.14; the room and measured-stationary runs used Python 3.13.18. The
minimum supported Python version is 3.10. Install the package and test tools
with `pip install -e '.[dev]'`; run the test suite using `pytest`. Install
`pyroomacoustics==0.10.1` for the room simulations. The separate
`requirements-numpy253.txt` lists the recorded direct versions for the
NumPy 2.5.3 environment; it is not a fully resolved transitive lock file.
A platform-specific lock should be resolved and verified before use. Do not
expect bitwise equality across NumPy or BLAS versions.

The provenance commit hashes refer to a development history that is not
included in the public repository. See `CITATION.cff` for citation metadata.
Zenodo DOI: **pending**.

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
| Learning | `paper/v2/make_figures.py learning learning_all` | `results/final_eval_holdout/curves.npz` |
| Excess | `paper/v2/make_figures.py excess` | `results/gap_check2/curves.npz` and optional `results/gap_check3/curves.npz` |
| Cost | `paper/v2/make_figures.py cost` | `results/extra_eval/summary.md`, `results/final_eval_v2e/metrics.jsonl` |
| Secondary-path error | `paper/v2/make_figures.py shat` | `results/extra_eval/summary.md` |
| Other time figures | `paper/v2/make_times_figures.py` | saved arrays listed by the generator |

To prepare an archive after checking its sources, run
`python make_zenodo_archive.py SOURCE_ROOT OUTPUT_TAR` from this directory.
The script validates the manifest and sanitizes absolute filesystem paths in
log copies; it leaves source files untouched. Review the archive and licensing
before upload. No archive is bundled in this snapshot.

The optional optimizer tests require the optional `optuna` package. When it is
not installed, those tests are skipped; they are unrelated to reproducing the
archived tables. Install `optuna` to run them.

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
