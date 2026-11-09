"""Method names from v1.2.0 and the former names kept in the archived records.

The method is called PCG-WLS (PCG for windowed least squares) in the paper and in this code from v1.2.0. It was
called E-PCG before, and the multi-window variant was called E-PCG (bank). The archived records keep the former
names: run records, summaries, curve files and saved configurations under results/, the rule documents in
docs/current/, and the Zenodo archive (DOI 10.5281/zenodo.23965831). These records are not rewritten.

This module maps the former names to the current ones.

* Method keys of the experiment runner (experiments/prototype_new_algorithms.run) and the "method" field of saved
  configurations: the former keys are accepted and mapped on input (`method_key`, `normalize_config`,
  `load_config`).
* Record labels: the runners in experiments/ still write and read the proposed methods under the archived labels
  `RECORD_LABEL` and `RECORD_LABEL_MW`, so that new runs can be resumed from and compared with the archived
  records. `display_label` and `display_text` give the current names for tables and figures.
"""
from __future__ import annotations

import json
import re
import warnings
from pathlib import Path

PCG_WLS = "PCG-WLS"
PCG_WLS_MW = "PCG-WLS (multi-window)"

# Method keys of experiments/prototype_new_algorithms.run
METHOD_KEY = "PCG-WLS-F"        # production implementation (ffanc_norm.pcg_wls / ffanc_norm.pcg_wls_mw)
PROTOTYPE_KEY = "PCG-WLS"       # earlier prototype of the same method in the runner
LEGACY_METHOD_KEYS = {"E-PCG-F": METHOD_KEY, "E-PCG": PROTOTYPE_KEY}

# Labels of the proposed methods in the archived records (method field, summary headings, curve keys)
RECORD_LABEL = "E-PCG"
RECORD_LABEL_MW = "E-PCG bank"
LEGACY_LABELS = {
    RECORD_LABEL: PCG_WLS,
    RECORD_LABEL_MW: PCG_WLS_MW,
    "E-PCG (bank)": PCG_WLS_MW,
    "E-PCG (main)": "PCG-WLS (main)",
}

_TEXT = [(re.compile(r"(?<![A-Za-z])E-PCG \(bank\)"), PCG_WLS_MW),
         (re.compile(r"(?<![A-Za-z])E-PCG bank"), PCG_WLS_MW),
         (re.compile(r"(?<![A-Za-z])E-PCG"), PCG_WLS)]


def method_key(key: str, warn: bool = True) -> str:
    """Current method key for `key`. A former key is mapped, with a DeprecationWarning if `warn`."""
    new = LEGACY_METHOD_KEYS.get(key)
    if new is None:
        return key
    if warn:
        warnings.warn(f"method key {key!r} is deprecated; use {new!r} (E-PCG was renamed PCG-WLS in v1.2.0)",
                      DeprecationWarning, stacklevel=2)
    return new


def display_label(label: str) -> str:
    """Current name of a record label (labels of other methods are returned unchanged)."""
    return LEGACY_LABELS.get(label, label)


def display_text(text: str) -> str:
    """Replace the former method names in a display string (table cell, caption, legend)."""
    for pat, new in _TEXT:
        text = pat.sub(new, text)
    return text


def normalize_config(cfg: dict, warn: bool = True) -> dict:
    """Copy of a configuration dict with a former "method" key mapped to the current one."""
    out = dict(cfg)
    if isinstance(out.get("method"), str):
        out["method"] = method_key(out["method"], warn=warn)
    return out


def load_config(path) -> dict:
    """Read a saved configuration (e.g. results/final_dev/final_config_core_main.json) and map former keys.

    The file is not modified. Saved configurations are archived records, so the mapping is silent here."""
    return normalize_config(json.loads(Path(path).read_text()), warn=False)
