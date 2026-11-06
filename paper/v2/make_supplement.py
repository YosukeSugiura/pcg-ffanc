"""Generate supplementary tables from archived results; never run a simulator.

Run from any directory: python paper/v2/make_supplement.py
Dependencies: numpy, scipy. Only supp_tables/ is written. Each generated file
records its input paths; sources.json records their SHA-256 hashes.
The proposed methods are read under their archived record labels (E-PCG, E-PCG bank); the written tables show
PCG-WLS and PCG-WLS (multi-window) (ffanc_norm.naming).
"""
import argparse
import ast
import hashlib
import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np
from scipy.stats import wilcoxon

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_OUT = Path(__file__).resolve().parent / "supp_tables"
sys.path.insert(0, str(ROOT / "src"))
from ffanc_norm import naming as N  # noqa: E402
REC, REC_MW = N.RECORD_LABEL, N.RECORD_LABEL_MW   # record labels of PCG-WLS and PCG-WLS (multi-window)
ORDER = ["FD-FxNLMS", "leaky FD-FxNLMS", "convex FD-FxNLMS", "FDKF", "RLS",
         "VFF-RLS", "FD-FxNLMS + det", "FD-FxNLMS + restart", "RLS + det",
         "SFTF + det", "SFTF-H + det", "CFTF + det", "RLS + CUSUM", REC_MW, REC]
PROPOSED = (REC, REC_MW)
DATASETS = ("final_eval", "final_eval_v2e", "eval_roomB", "eval_roomC", "eval_snr10", "final_eval_holdout", "eval_roomB_x2", "eval_roomC_x2", "eval_snr10_x2", "final_eval_meas_s_8a")
SOURCES = set()
SEEDS_TUNE = "tuning seeds 300--309"
SEEDS_EVAL = "evaluation seeds 480--519"
GAIN = r"(S8, $M=512$, " + SEEDS_TUNE + ")"
POST_HOC = "Corrected finite-time check (post hoc)"
OMITTED = ("Omitted: a trial-branch option, which is off, and an option that acts only with a robust ridge,"
           " which is not used.")
# Published captions. Archived titles name internal files, rules and revisions, so these captions are
# replaced in the written output. Only the matching \caption lines change; table bodies stay as generated.
# Per output file: (caption as generated, published caption), in order of appearance.
CAPTIONS = {
    "gap.tex": [
        (r"Gap check (idealized gain analysis): eigenvalues of K R for x\_f, S8, M = 512, N = 2M",
         r"Idealized averaged-gain analysis: eigenvalues of $\mathbf K\Rx$ for the filtered reference and predicted"
         r" asymptotic excess per seed (S8, $M=512$, $N=2M$, " + SEEDS_TUNE + ")"),
        ("ar1", "Excess over the oracle floor relative to exact growing-window LS by hop range, AR(1) noise " + GAIN),
        ("harmonic", "Excess over the oracle floor relative to exact growing-window LS by hop range, harmonic noise " + GAIN),
        ("ar1", "E-PCG and exact LS on the same 48-hop window: excess over the oracle floor relative to offline"
                " window LS by hop range, AR(1) noise " + GAIN),
        ("harmonic", "E-PCG and exact LS on the same 48-hop window: excess over the oracle floor relative to offline"
                     " window LS by hop range, harmonic noise " + GAIN),
    ],
    "cg.tex": [
        ("Archived CG summary, including full-window eigenvalues.",
         r"Archived CG summary, including the full-window eigenvalues of $\mathbf C_{\rm w}^{-1}\G$."),
    ],
    "restart.tex": [
        ("N1: FD-FxNLMS + restart minus FD-FxNLMS (negative = restart better); Holm over 30",
         "FD-FxNLMS+restart minus FD-FxNLMS, " + SEEDS_EVAL + " (negative: restart better, Holm over 30 tests)"),
        ("N2: E-PCG - RLS + det, S7 AR(1)",
         "E-PCG minus RLS+det after the abrupt primary-path change: NR per hop around the change (S7, AR(1), " + SEEDS_EVAL + ")"),
        (r"A2 vs memory length (REVISION\_RULE\_2.md section 5; stored records only, AR(1), S8)",
         "A2 versus memory length: observed and predicted differences (stored records only, AR(1), S8)"),
        (r"Review N6 diagnostic: cold vs warm restart of RLS + det, S7 AR(1), evaluation seeds (REVISION\_RULE\_3.md)",
         "Cold versus warm restart of RLS+det after the abrupt primary-path change: medians and failures (S7, AR(1), "
         + SEEDS_EVAL + ")"),
        (r"Review N6 diagnostic: cold vs warm restart of RLS + det, S7 AR(1), evaluation seeds (REVISION\_RULE\_3.md)",
         "Cold versus warm restart of RLS+det after the abrupt primary-path change: NR per hop (S7, AR(1), " + SEEDS_EVAL + ")"),
        (r"R2 rig 30cm: secondary-path change per room (S\_hat = S before the move; evaluation seeds 480-519, median)",
         r"Secondary-path change per room in the 30 cm control-unit move (R2), median over " + SEEDS_EVAL
         + r". The model $\Shat$ equals $S$ before the move."),
        (r"N8: RLS + det with a prewindowed restart (REVISION\_RULE\_5.md), S2 src 30cm, evaluation seeds",
         "Median A1 (dB) of RLS+det with a prewindowed restart after the 30 cm source move (S2, " + SEEDS_EVAL + ")"),
    ],
    "selection.tex": [
        ("", "A1-aligned baseline selection on tuning seeds 300--309 and 600--619: admissible configurations,"
             " selected configuration and score (dB)"),
    ],
    "settings.tex": [
        ("Selected v2e baseline settings (zero-based grid indices).",
         r"Baseline settings from the A1-aligned selection (zero-based grid indices). Configuration files are in"
         r" \texttt{results/protocol\_v2\_sel/}, \texttt{results/final\_dev/} and \texttt{results/protocol\_final\_sel/} of the"
         " public code release."),
        ("E-PCG: frozen flags.", "E-PCG: frozen configuration, with the symbols of the main paper where they exist. " + OMITTED),
        ("E-PCG bank: frozen flags.", "E-PCG bank: frozen configuration, with the symbols of the main paper where they"
                                      " exist. " + OMITTED),
        ("Selected v1 baselines (also used in the cost and model-error studies).",
         "Baseline settings of the first final evaluation, also used in the cost and model-error studies"
         " (zero-based grid indices)."),
    ],
    "wins.tex": [
        ("Comparison counts (each proposed method has its own Holm family).",
         r"Comparison counts by evaluation set. Each proposed method has its own Holm family. The first (v1) and"
         r" revised (v2) final evaluations are described in Section~\ref{supp:history}. All sets except the holdout"
         " use evaluation seeds 480--519."),
    ],
    "r9_environment.tex": [
        ("Archived environments by evaluation set; dependency versions can prevent bit reproduction.",
         r"Archived software environments by evaluation set. Dependency versions can prevent bit reproduction."
         r" For v2 only the NumPy family is known, from the numerical-environment amendment (Section~\ref{supp:rules})."),
    ],
    "r9_labels.tex": [
        ("Like-for-like comparison: v2e versus holdout: like-for-like 360-test families",
         "Labels that differ between the earlier evaluation (seeds 480--519) and the holdout (seeds 800--839)"
         " in like-for-like 360-test families"),
    ],
    "gap_check4.tex": [
        (r"gap\_check4: " + noise,
         r"Registered finite-time check with the pure $1/b$ schedule, " + display + " noise: excess relative to"
         " exact growing-window LS by hop range, and decay slope " + GAIN)
        for noise, display in (("ar1", "AR(1)"), ("harmonic", "harmonic"))
    ],
    "gap_check4a.tex": [
        (rf"gap\_check4a: {noise}, part {part}", f"{POST_HOC}, {display} noise, part {part}: {content} " + GAIN)
        for noise, display in (("ar1", "AR(1)"), ("harmonic", "harmonic"))
        for part, content in ((1, "excess of recursions A and B in dB relative to the LS reference by hop range"),
                              (2, "later hop ranges, decay slope, diverged seeds and last hop relative to the floor"))
    ],
    "gap_check4a_perseed.tex": [
        (r"gap\_check4a\_perseed: Revision 10a/10b: per-seed breakdown of recursion A (ar1, T = 5 s),"
         rf" descriptive only (no judgement), part {part}",
         rf"{POST_HOC}: per-seed breakdown of recursion A (AR(1), $T=5$ s), descriptive only, part {part}")
        for part in (1, 2)
    ],
    "gap_check4a_spectrum.tex": [
        ("Revision 10a/10b: median eigenvalue summaries and mean-field B bias relative to floor (dB).",
         f"{POST_HOC}: eigenvalue summaries and mean-field bias of recursion B relative to the floor (dB),"
         f" medians over {SEEDS_TUNE}."),
    ],
    "cftf.tex": [
        ("CFTF + det, S7 ar1, seed 515 (diagnosis)", "CFTF + det, S7, AR(1), seed 515 (diagnosis)"),
        ("CFTF + det, S7 ar1, seed 515, stabilization off (1, 1, 1)",
         "CFTF + det, S7, AR(1), seed 515, stabilization off (1, 1, 1)"),
    ],
    "extra.tex": [
        ("noise = ar1: failures / median A2 (dB) / median A1 (dB)",
         "AR(1) noise: failures / median A2 (dB) / median A1 (dB)"),
        ("noise = harmonic: failures / median A2 (dB) / median A1 (dB)",
         "Harmonic noise: failures / median A2 (dB) / median A1 (dB)"),
    ],
    "measured_rules.tex": [
        ("Measured-path additions to the rule summary; Rule 8a is a post-Rule-8-outcome correction.",
         "Measured-path additions to the rule summary. The common-delay correction was specified after the first"
         " measured-path evaluation."),
    ],
    "measured_allocation.tex": [
        ("Measured-path allocation: original zero-based indices, identical for Rules 8/8a, both scenarios and both noises.",
         "Measured-path allocation: original zero-based indices, identical before and after the common-delay"
         " correction, for both scenarios and both noises."),
    ],
    "measured_8a_wiener.tex": [
        ("Rule 8a stationary causal Wiener diagnostics: median (Q1, Q3), dB; true-S entries each use all archived seeds.",
         "Stationary causal Wiener diagnostics with the common-delay correction: median (Q1, Q3) in dB."
         " True-$S$ entries each use all archived seeds."),
    ],
    "measured_onset.tex": [
        ("INVALID Rule 8: secondary-path onset diagnostic before the common-delay correction.",
         "Secondary-path onset diagnostic of the invalid evaluation before the common-delay correction."),
    ],
}


class TeX(str):
    """Published LaTeX; tex() leaves it unchanged."""


# Published method names. The archives (method keys, summaries, rule files) keep the former names E-PCG and
# E-PCG bank; only the written text changes, longest name first. Values are untouched.
DISPLAY_NAMES = ((REC_MW, N.PCG_WLS_MW), ("E-PCG (main)", N.PCG_WLS), (REC, N.PCG_WLS),
                 ("-bank", "-multi-window"))   # ablation labels: "-bank" removes the multi-window mixture


def display_names(body):
    for old, new in DISPLAY_NAMES:
        body = body.replace(old, new)
    return body


# Published names for archived identifiers in table headers and cells. Only labels change; values are untouched.
DATASET_LABELS = {
    "final_eval": "Room A, first evaluation (v1)",
    "final_eval_v2e": "Room A, earlier evaluation (v2)",
    "final_eval_holdout": "Room A, holdout (seeds 800--839)",
    "eval_roomB": "Room B",
    "eval_roomC": "Room C",
    "eval_snr10": "Room A, SNR 10 dB",
    "eval_roomB_x2": "Room B, added baselines",
    "eval_roomC_x2": "Room C, added baselines",
    "eval_snr10_x2": "Room A, SNR 10 dB, added baselines",
    "final_eval_meas_s_8a": "Measured paths, M-S",
    "final_eval_meas_p_8a": "Measured paths, M-P",
    "final_eval_meas_ps_8a": "Measured paths, M-PS",
    "protocol_v2_sel_cusum": "RLS+CUSUM selection (tuning seeds)",
}
IMPLEMENTATIONS = {
    "fixed_binwise": "per-bin normalized, fixed step",
    "leaky_binwise": "per-bin normalized, leaky",
    "convex_binwise": "per-bin normalized, convex combination",
    "C-FDKF": "diagonal FDKF",
    "R-RLS": "exponentially weighted RLS",
    "R-VFF": "variable-forgetting-factor RLS",
    "V-SCHED": TeX(r"$1/b$ step schedule"),
    "R-SFTF": "stabilized FTF",
}
# Parameter name -> format of its value, or the published text of each discrete value.
PARAMETERS = {
    "mu": r"$\mu={}$", "leak": "leakage ${}$", "mu_fast": r"$\mu_{{\rm fast}}={}$", "mu_slow": r"$\mu_{{\rm slow}}={}$",
    "mu_a": r"$\mu_a={}$", "P0": "$P_0={}$", "gain_scale": "gain scale ${}$", "A": "$A={}$",
    "lam": r"$\lambda={}$", "delta": r"$\delta={}$", "N0": "$N_0={}$", "lam_min": r"$\lambda_{{\min}}={}$",
    "scale": "step scale ${}$", "mu_min": r"$\mu_{{\min}}={}$", "det_boost": "$s={}$", "hybrid": "$T_h={}$",
    "cusum_h": "$h={}$", "cusum_k": "$W={}$",
    "denom": {"cum": "cumulative bin powers"},
    "det_reset_w": {False: "warm restart", True: "cold restart"},
    "cov": {True: "covariance window"},
}
HEADERS = {
    "lambda min": r"$\min_i\lambda_i$", "frac < 1/2": r"fraction $<1/2$",
    "rho_c (dB)": r"$\rho$, commuting (dB)", "rho_L (dB)": r"$\rho$, Lyapunov (dB)",
    "p_Holm A1": r"$p_{\rm Holm}$ A1", "p_Holm A2": r"$p_{\rm Holm}$ A2",
    "median samples since tau": r"median samples since $\tau$", "within +-0.1": r"within $\pm0.1$",
    "median lambda_min": r"median $\lambda_{\min}$", "median lambda_max": r"median $\lambda_{\max}$",
    "lambda_max(K R)": r"$\lambda_{\max}(\mathbf K\Rx)$",
    "nA": "$n_A$", "nB": "$n_B$", "nA D/M": r"$n_A\Delta/M$", "JS": "James--Stein",
    "m0": "$m_0$", "m1": "$m_1$", "j (secondary)": "$j$ (secondary)", "i0 (initial noise)": "$i_0$ (initial noise)",
    "i1 (M-P noise after)": "$i_1$ (M-P noise after)", "h": "$h$", "K": "$K$", "W": "$W$", "T": "$T$",
    "v2e label": "earlier label", "v2e dA1 / p / dA2 / p": "earlier dA1 / p / dA2 / p",
    "failures v2e proposal/baseline": "failures earlier proposal/baseline", "Dataset": "Evaluation set",
}
CELLS = {
    "exact LS (RLS lam 1)": r"exact LS (RLS, $\lambda=1$)",
    "sim exact LS (RLS lam 1)": r"simulated exact LS (RLS, $\lambda=1$)",
    "sim E-PCG (main)": "simulated E-PCG (main)",
    "predicted window (sigma^2 tr R G_win^-1)": r"predicted window ($\sigma^2\tr(\Rx\G_{\rm win}^{-1})$)",
    "pure 1/b schedule (V-SCHED)": r"pure $1/b$ schedule",
    "FD-FxNLMS mu 0.2": r"FD-FxNLMS, $\mu=0.2$",
    "FD-FxNLMS mu 0.5": r"FD-FxNLMS, $\mu=0.5$",
    "RLS + det (cold, cfg 0)": "RLS + det (cold, configuration 0)",
    "(i) RLS lambda 0.9995 - RLS + det 0.9999, median A2":
        r"(i) RLS, $\lambda=0.9995$, minus RLS + det, $\lambda=0.9999$, median A2",
    "(ii) RLS 0.9995 - 0.9999, median A2": r"(ii) RLS, $\lambda=0.9995$ minus $\lambda=0.9999$, median A2",
    "(ii) RLS 0.9998 - 0.9999, median A2": r"(ii) RLS, $\lambda=0.9998$ minus $\lambda=0.9999$, median A2",
    "(iii) E-PCG L = 24 - L = 48, median paired dA (A = NR over [1 s, end])":
        r"(iii) E-PCG, $L=24$ minus $L=48$, median paired dA (A: NR over $[1\,\mathrm s,\text{end}]$)",
    "(consequence) E-PCG - RLS + det, A2": "(consequence) E-PCG minus RLS + det, A2",
    "final_eval_v2 (evaluation seeds)": "v2 (evaluation seeds)",
    "final_eval_v2": "v2",
    "protocol_v2_sel (tuning seeds)": "A1-aligned selection (tuning seeds)",
    "protocol_v2_sel": "A1-aligned selection",
    "ablation_core_d (tuning seeds)": "ablation set d (tuning seeds)",
    "j_m0": r"$\mathrm{IR}(j,m_0)$", "j_m1": r"$\mathrm{IR}(j,m_1)$",
    # Scenario and noise names as in the main paper: the label only; harmonic is unchanged.
    "S8 stationary": "S8", "S1 src 10cm": "S1", "S2 src 30cm": "S2", "S5 src 30cm cont": "S5",
    "S7 rd abrupt": "S7", "R1 rig 10cm": "R1", "R2 rig 30cm": "R2", "R3 rig 30cm cont": "R3",
    "ar1": "AR(1)",
}
NOISE = {"ar1": "AR(1)", "harmonic": "harmonic"}
# Frozen E-PCG flags: notation of the main paper, or a short description where the paper has no symbol.
# Per flag: (published setting, None to print the archived value, or the published text of each value).
FLAGS = {
    "L_hops": (r"$L$ (window length, hops)", None),
    "ridge": (r"Tikhonov weight, relative to $r(0)$", None),
    "k_first": (r"$k_b$ (CG iterations per hop) in the first hops after a (re)start", None),
    "k_first_hops": ("number of these hops", None),
    "k_hops": (r"window length beyond which the steady-state $k_b$ applies (hops)", None),
    "k_steady": (r"steady-state $k_b$", None),
    "k": (r"$k_b$ otherwise", None),
    "steady_every": ("hops between steady-state CG updates", None),
    "cg_stat_tol": (r"$\epsilon$ (stopping-rule tolerance)", None),
    "cg_stat_mindof": (r"minimum residual degrees of freedom $n-M$ for the stopping rule", {"M": "$M$"}),
    "cg_stat_exactJ": (r"$\mathrm{RSS}$ in the stopping rule excludes the Tikhonov term", {True: "on"}),
    "grow_len": (r"controller length while $n<2M$", {"half": "$n/2$"}),
    "pre_window": ("preconditioner", {"bartlett_s": "circulant of the Bartlett-tapered autocorrelation"
                                                    " (full-length controller)"}),
    "detect": ("change detection", {True: "on"}),
    "screen_fa": ("stage-1 level", None),
    "J": (r"$J$ (hops in the stage-2 score test)", None),
    "det_stat": ("stage-2 statistic", {"sandwich": "sandwich score $T$"}),
    "det_C_pre": (r"$\boldsymbol\Sigma_u$ estimated on the pre-test segment $[t_0,t_J)$", {True: "on"}),
    "kd": ("stage-2 PCG iterations on the score system", None),
    "det_fa": (r"stage-2 nominal per-hop level", None),
    "localize": (r"change-point localization ($\tau$)", {True: "on"}),
    "loc_step": ("localization search step (samples)", None),
    "adapt": ("after a detection", {"weight": r"Stein weight $\alpha$", "restart": "restart"}),
    "weight_consistent": (r"weighted solve with the length and stopping rules at effective size $\alpha n_A+n_B$",
                          {True: "on"}),
    "fixes_1028": ("corrected bookkeeping of the change handling (block estimates, sample counts,"
                   " noise level, caches)", {True: "on"}),
    "mem_bank": ("windows (hops)", None),
    "mem_primary": ("window of the detecting member (hops)", None),
    "mem_cheap": ("cost reductions", {
        "share": "shared window statistics", "nodetect": "detection by one member only",
        "fftmin": "minimal FFT lengths", "sharescore": "shared stage-1 residual",
        "doze": "idle low-weight members"}),
}
# Flags without effect in the frozen configurations; their archived values are checked, not printed.
# branch_hops = 0 switches the trial branch off; score_unreg acts only with a robust ridge, which is not used.
OMITTED_FLAGS = {"branch_hops": 0, "score_unreg": True}


def flag_row(key, value):
    setting, form = FLAGS[key]
    if form is None:
        text = ", ".join(map(json.dumps, value)) if isinstance(value, list) else json.dumps(value)
    elif isinstance(value, list):
        text = ", ".join(form[v] for v in value)
    else:
        text = form[value]
    return [TeX(setting), TeX(text) if form is not None else text]


def number(value):
    return str(int(value)) if isinstance(value, float) and value.is_integer() else str(value)


def parameters(grid):
    """Typeset an archived parameter dict; every name and discrete value must be listed."""
    out = []
    for key, value in grid.items():
        form = PARAMETERS[key]
        out.append(form[value] if isinstance(form, dict) else form.format(number(value)))
    return TeX(", ".join(out))


def publish(cell, mapping):
    """Published form of a header or cell: listed labels and 'index {dict}' cells; all else unchanged."""
    if isinstance(cell, str) and not isinstance(cell, TeX):
        if cell in mapping:
            return TeX(mapping[cell])
        m = re.fullmatch(r"(\d+) (\{.*\})", cell)
        if m:
            return TeX(m.group(1) + ": " + parameters(ast.literal_eval(m.group(2))))
    return cell


def publish_captions(name, body):
    """Replace the listed captions in order; every listed caption must be found."""
    pending = list(CAPTIONS.get(name, ()))
    lines = body.split("\n")
    for i, line in enumerate(lines):
        if pending and line == r"\caption{" + pending[0][0] + r"}\\":
            lines[i] = r"\caption{" + pending.pop(0)[1] + r"}\\"
    assert not pending, (name, pending)
    return "\n".join(lines)


def read(path):
    SOURCES.add(path)
    return (ROOT / path).read_text()


def verify_original_or_redacted(path, expected):
    """Check archived digest or a documented release redaction against its commitment."""
    actual = hashlib.sha256(read(path).encode()).hexdigest()
    if actual == expected:
        return
    manifest = json.loads((ROOT / "REDACTION_MANIFEST.json").read_text())
    item = manifest["files"].get(path)
    assert item and item["original_sha256"] == expected and item["release_sha256"] == actual, path


def load_metrics(dataset):
    rows = [json.loads(line) for line in read(f"results/{dataset}/metrics.jsonl").splitlines()]
    groups = defaultdict(dict)
    for row in rows:
        k = row["method"], row["noise"], row["scen"]
        assert row["seed"] not in groups[k], (dataset, k, row["seed"])
        groups[k][row["seed"]] = row
    expected = range(800, 840) if dataset == "final_eval_holdout" else range(480, 520)
    assert all(set(g) == set(expected) for g in groups.values()), dataset
    return dict(groups)


def holm(p):
    p = np.nan_to_num(np.asarray(p), nan=1.0)
    order = np.argsort(p)
    out = np.empty(len(p))
    out[order] = np.minimum(1, np.maximum.accumulate((len(p) - np.arange(len(p))) * p[order]))
    return out


def pvalue(d):
    return 1.0 if np.all(d == 0) else float(wilcoxon(d, zero_method="pratt").pvalue)


def label(d1, p1, d2, p2):
    win = (p1 < .05 and d1 <= -1) or (p2 < .05 and d2 <= -.5)
    loss = (p1 < .05 and d1 >= 1) or (p2 < .05 and d2 >= .5)
    return "mixed" if win and loss else "win" if win else "loss" if loss else "none"


def comparisons(groups, proposed, baselines=None):
    if baselines is None:
        baselines = [m for m in ORDER if m not in PROPOSED and any(k[0] == m for k in groups)]
    rows, ps = [], []
    for baseline in baselines:
        for noise, scen in sorted((k[1], k[2]) for k in groups if k[0] == proposed):
            a, b = groups[proposed, noise, scen], groups[baseline, noise, scen]
            ds = [np.array([a[s][key] - b[s][key] for s in sorted(a)]) for key in ("A1", "A2")]
            rows.append([baseline, noise, scen, float(np.median(ds[0])), float(np.median(ds[1]))])
            ps.extend(map(pvalue, ds))
    adjusted = holm(ps)
    return [r + [float(adjusted[2*i]), float(adjusted[2*i+1]),
                 label(r[3], adjusted[2*i], r[4], adjusted[2*i+1])]
            for i, r in enumerate(rows)]


def tex(value):
    if isinstance(value, TeX):
        return str(value)
    text = str(value)
    if re.fullmatch(r"[+-]?\d+\.\d+(?:/[+-]?\d+\.\d+){2}", text):
        # Break between quartiles, never between a minus sign and its number.
        return " / ".join(r"\mbox{" + x + "}" for x in text.split("/"))
    return "".join({"\\": r"\textbackslash{}", "&": r"\&", "%": r"\%", "$": r"\$",
                    "#": r"\#", "_": r"\_", "{": r"\{", "}": r"\}",
                    "~": r"\textasciitilde{}", "^": r"\textasciicircum{}"}.get(c, c) for c in text)


def short(scen):
    return scen.split()[0]


def table(caption, headers, rows, weights=None):
    """Fixed-width paragraph columns keep long source labels within the page."""
    n = len(headers)
    weights = weights or [1] * n
    widths = [w / sum(weights) for w in weights]
    spec = "".join(r">{\raggedright\arraybackslash}p{" +
                   f"\\dimexpr{w:.6f}\\linewidth-2\\tabcolsep\\relax" + "}" for w in widths)
    heading = " & ".join(tex(publish(h, HEADERS)) for h in headers) + r" \\ \midrule"
    out = [r"{\scriptsize\setlength{\tabcolsep}{3pt}", r"\begin{longtable}{" + spec + "}",
           r"\caption{" + tex(caption) + r"}\\", r"\toprule", heading, r"\endfirsthead",
           r"\toprule", heading, r"\endhead", r"\bottomrule\endfoot"]
    out += [" & ".join(tex(publish(c, CELLS)) for c in row) + r" \\" for row in rows]
    return "\n".join(out + [r"\end{longtable}}", ""])


def markdown_tables(path):
    """Read archived diagnostic tables, including tables without a header title."""
    blocks, block, title = [], [], ""
    for line in read(path).splitlines() + [""]:
        if line.startswith("|"):
            block.append(line)
        else:
            if block:
                parsed = [[c.strip() for c in x.strip().strip("|").split("|")] for x in block]
                headers = parsed[0]
                rows = [r for r in parsed[1:] if not all(re.fullmatch(r"[:\- ]+", c) for c in r)]
                if rows:
                    # The room diagnostic's header contains literal norm/condition pipes.
                    if path.endswith("rooms_shat.md"):
                        headers = ["Room", "RT60 (s)", "S taps", "Relative path change", "Violating bin fraction"]
                    # Analytic SFTF cost-only rows have omitted trailing empty fields.
                    if path == "results/extra_eval/summary.md":
                        rows = [r + [""] * (len(headers) - len(r)) for r in rows]
                    assert all(len(r) == len(headers) for r in rows), (path, title)
                    blocks.append((title, headers, rows))
                block = []
            if line.startswith("#"):
                title = line.lstrip("# ")
    return blocks


def median_iqr(values):
    q1, median, q3 = np.quantile(values, [.25, .5, .75])
    return f"{median:.3f} ({q1:.3f}, {q3:.3f})"


def measured_tables(write):
    """Read Rule 8/8a archives, checking coverage and saved test decisions."""
    measured_order = [m for m in ORDER if m != "RLS + CUSUM"]
    allocations = None
    provenance = {}
    for suffix, comparison_file, output in (
            ("_8a", "measured_paths_8a_comparisons.json", "measured_8a.tex"),
            ("", "measured_paths_comparisons.json", "measured_8_invalid.tex")):
        archive_path = "results/" + comparison_file
        archive = json.loads(read(archive_path))
        saved_metrics = {(r["scenario"], r["noise"], r["method"]): r for r in archive["metrics"]}
        saved_tests = {(r["set"], r["proposed"], r["baseline"], r["noise"]): r for r in archive["comparisons"]}
        assert len(saved_metrics) == len(measured_order) * 4
        assert len(saved_tests) == (len(measured_order) - len(PROPOSED)) * 8
        body, test_body, sources = "", "", [archive_path]
        for scenario, name in (("M-P", "meas_p"), ("M-PS", "meas_ps")):
            dataset = name + suffix
            path = f"results/final_eval_{dataset}/metrics.jsonl"
            provenance_path = f"results/final_eval_{dataset}/provenance.json"
            groups = load_metrics("final_eval_" + dataset)
            prov = json.loads(read(provenance_path))
            provenance[dataset] = prov
            rule = "docs/current/REVISION_RULE_8" + ("a" if suffix else "") + ".md"
            verify_original_or_redacted(rule, prov["rule_sha256"])
            sources.extend([path, provenance_path, rule])
            assert len(groups) == len(measured_order) * 2
            assert {k[0] for k in groups} == set(measured_order)
            assert {k[1] for k in groups} == {"ar1", "harmonic"}
            assert len({k[2] for k in groups}) == 1
            assert prov["preprocessing"]["removed_leading_samples"] == (5434 if suffix else 0)
            current_allocation = sorted(prov["allocation"], key=lambda r: r["seed"])
            assert [r["seed"] for r in current_allocation] == list(range(480, 520))
            if allocations is None:
                allocations = current_allocation
            assert current_allocation == allocations, dataset
            for source, digest in prov["frozen_config_sha256"].items():
                verify_original_or_redacted(source, digest)

            decisions = {}
            for prop in PROPOSED:
                tests = comparisons(groups, prop)
                assert len(tests) * 2 == 48
                for baseline, noise, scen, d1, d2, p1, p2, decision in tests:
                    saved = saved_tests[dataset, prop, baseline, noise]
                    assert saved["scenario"] == scenario and saved["family_size"] == 2 * len(tests)
                    assert np.allclose([d1, d2, p1, p2],
                                       [saved["dA1"], saved["dA2"], saved["pHolmA1"], saved["pHolmA2"]],
                                       rtol=1e-12, atol=1e-15), (dataset, prop, baseline, noise)
                    assert decision == ("none" if saved["label"] == "-" else saved["label"])
                    decisions[prop, baseline, noise] = saved["label"]
                if suffix:
                    test_body += table(f"Rule 8a, {scenario}: {prop} minus baselines; separate Holm family of {2*len(tests)} tests.",
                                       ["Baseline", "Noise", "dA1", "p Holm A1", "dA2", "p Holm A2", "Decision"],
                                       [[b, nz, f"{d1:+.3f}", f"{p1:.3g}", f"{d2:+.3f}", f"{p2:.3g}", decisions[prop, b, nz]]
                                        for b, nz, _, d1, d2, p1, p2, _ in tests],
                                       [2.4, 1, .9, 1.2, .9, 1.2, 1])
            for noise in ("ar1", "harmonic"):
                rows = []
                for method in measured_order:
                    rs = next(v for k, v in groups.items() if k[:2] == (method, noise))
                    a1 = [r["A1"] for r in rs.values()]
                    a2 = [r["A2"] for r in rs.values()]
                    failures = sum(r["fail"] for r in rs.values())
                    saved = saved_metrics[scenario, noise, method]
                    assert np.allclose([np.median(a1), np.median(a2)], [saved["A1"], saved["A2"]], rtol=0, atol=1e-12)
                    assert failures == saved["failures"]
                    assert all(r["A1"] == r["A2"] == 0 for r in rs.values() if r["fail"])
                    rows.append([method, median_iqr(a1), median_iqr(a2), f"{failures}/{len(rs)}"] +
                                [decisions.get((prop, method, noise), "n/a") for prop in PROPOSED])
                status = "Rule 8a" if suffix else "INVALID Rule 8: historical reference only"
                body += table(f"{status}, {scenario}, {NOISE[noise]}. A1/A2: median (Q1, Q3), dB.",
                              ["Method", "A1", "A2", "Fail / N", "PCG-WLS vs.", "Multi-window vs."],
                              rows, [2.2, 2.8, 2.8, .8, 1, 1])
        write(output, body, sources)
        if suffix:
            assert archive["old_rule8_results_invalid_due_to_preprocessing"]
            write("measured_8a_tests.tex", test_body, sources)

    p = "results/revision8a_diag/per_seed.json"
    diagnostic = json.loads(read(p))
    assert diagnostic["metadata"]["meshrir_d0_48k"] == 5434
    seeds = diagnostic["seeds"]
    assert sorted(s["seed"] for s in seeds) == list(range(480, 520))
    rows = []
    for scenario, key in (("M-P", "meas_p"), ("M-PS", "meas_ps")):
        for phase in ("before", "after"):
            for noise in ("ar1", "harmonic"):
                records = [s["scenarios"][key][phase]["noise"][noise] for s in seeds]
                true = [r["true_s_causal_wiener_bound"] for r in records]
                old = [r["frozen_shat_design_actual_residual_not_bound"]["total_nr_db"]
                       for r in records if "frozen_shat_design_actual_residual_not_bound" in r]
                rows.append([scenario, phase, noise, median_iqr([r["total_nr_db"] for r in true]),
                             median_iqr([r["anc_only_nr_db"] for r in true]), median_iqr(old) if old else "n/a"])
    write("measured_8a_wiener.tex", table("Rule 8a stationary causal Wiener diagnostics: median (Q1, Q3), dB; true-S entries each use all archived seeds.",
                                      ["Scenario", "Paths", "Noise", "True S: total bound", "True S: ANC-only bound", "Old model design: actual total (not a bound)"],
                                      rows, [.7, .7, .9, 2.5, 2.5, 2.5]), [p])

    p = "results/revision8_diag/onset.json"
    onset = json.loads(read(p))
    assert sorted(s["seed"] for s in onset["seeds"]) == list(range(480, 520))
    rows = []
    for key in ("j_m0", "j_m1"):
        paths = [s["paths"][key] for s in onset["seeds"]]
        times = [r["minus20db_first_exceed_ms"] for r in paths]
        windows = {tuple(r["retention"]["S"]["window_48k_samples"]) for r in paths}
        assert len(windows) == 1
        start, stop = windows.pop()
        outside = sum(not r["retention"]["S"]["minus20db_onset_inside_raw_window"] for r in paths)
        rows.append([key, f"{min(times):.3f}", f"{max(times):.3f}", f"[{start}, {stop})", f"{outside}/{len(paths)}"])
    write("measured_onset.tex", table("INVALID Rule 8: secondary-path onset diagnostic before the common-delay correction.",
                                     ["S path", "Earliest onset (ms)", "Latest onset (ms)", "Raw window (48 kHz samples)", "Onsets outside / N"], rows), [p])
    paths = [f"results/final_eval_{name}/provenance.json" for name in provenance]
    write("measured_allocation.tex", table("Measured-path allocation: original zero-based indices, identical for Rules 8/8a, both scenarios and both noises.",
                                          ["Seed", "m0", "m1", "j (secondary)", "i0 (initial noise)", "i1 (M-P noise after)"],
                                          [[r[k] for k in ("seed", "m0", "m1", "j", "i0", "i1")] for r in allocations]), paths)
    d0 = provenance["meas_p_8a"]["preprocessing"]["removed_leading_samples"]
    rule_paths = ["docs/current/REVISION_RULE_8.md", "docs/current/REVISION_RULE_8a.md"]
    write("measured_rules.tex", table("Measured-path additions to the rule summary; Rule 8a is a post-Rule-8-outcome correction.",
                                      ["Rule", "Preprocessing", "Timing and status"],
                                      [["8", "Resample and truncate without common-delay removal.",
                                        "Fixed before its evaluation; INVALID because truncated S missed its direct sound. Retained only as a historical reference."],
                                       ["8a", f"Remove the same {d0} samples at the raw sample rate from every IR before the unchanged preprocessing.",
                                        "Written after inspecting Rule 8 results and the onset diagnosis; fixed before corrected runs. Bug fix, not an independent pre-outcome registration; no retuning."]],
                                      [.5, 2, 3]), rule_paths + paths)


def generate(out):
    out.mkdir(parents=True, exist_ok=True)
    generated = []

    def write(name, body, sources):
        generated.append(name)
        (out / name).write_text("% Generated by make_supplement.py; do not edit.\n" +
                               "".join(f"% Source: {s}\n" for s in sources) + display_names(publish_captions(name, body)))

    counts = []
    for dataset in DATASETS:
        groups = load_metrics(dataset)
        path = f"results/{dataset}/metrics.jsonl"
        rows = []
        combos = sorted({(k[1], k[2]) for k in groups})
        for noise, scen in combos:
            for method in ORDER:
                if (method, noise, scen) not in groups:
                    continue
                rs = list(groups[method, noise, scen].values())
                q = lambda key: "/".join(f"{v:.2f}" for v in np.quantile([r[key] for r in rs], [.25, .5, .75]))
                rows.append([noise, short(scen), method, q("A1"), q("A2"),
                             sum(r["fail"] for r in rs), q("tau9"), q("tau12")])
        body = table(f"{dataset}: all available methods and conditions. Triples are Q1/median/Q3; dB for A1/A2, seconds for reach times.",
                     ["Noise", "Cell", "Method", "A1", "A2", "Failures", "tau -9", "tau -12"], rows,
                     [1, .5, 2.3, 1.7, 1.7, .85, 1.6, 1.6])
        write(dataset + ".tex", body, [path])
        body = ""
        for prop in PROPOSED:
            tests = comparisons(groups, prop)
            rows = [[r[0], r[1], short(r[2]), f"{r[3]:+.2f}", f"{r[5]:.3g}",
                     f"{r[4]:+.2f}", f"{r[6]:.3g}", r[7]] for r in tests]
            # Independently recomputed tests must reproduce every archived entry.
            archived = {}
            for title, headers, saved in markdown_tables(f"results/{dataset}/summary.md"):
                if title.startswith(f"{prop} vs baselines ("):
                    archived = {(r[0], r[1], short(r[2])): r[3:] for r in saved}
            assert len(archived) == len(rows), (dataset, prop, "test coverage")
            for row in rows:
                saved = archived[tuple(row[:3])]
                assert row[3:-1] == saved[:-1], (dataset, prop, row, saved)
                assert row[-1] == ("none" if saved[-1] == "-" else saved[-1]), (dataset, row)
            body += table(f"{dataset}: {prop} minus baselines; Holm family = {2*len(tests)}.",
                          ["Baseline", "Noise", "Cell", "dA1", "p Holm", "dA2", "p Holm", "Decision"],
                          rows, [2.4, 1, .5, .8, 1.1, .8, 1.1, .8])
            cnt = Counter(r[-1] for r in tests)
            counts.append([DATASET_LABELS[dataset], prop, 2*len(tests), len(tests)] +
                          [cnt[k] for k in ("win", "loss", "mixed", "none")])
        tests = comparisons(groups, REC_MW, [REC])
        body += table(f"{dataset}: multi-window minus single-window variant; Holm family = {2*len(tests)}.",
                      ["Noise", "Cell", "dA1", "p Holm", "dA2", "p Holm"],
                      [[r[1], short(r[2]), f"{r[3]:+.2f}", f"{r[5]:.3g}", f"{r[4]:+.2f}", f"{r[6]:.3g}"] for r in tests])
        write(dataset + "_tests.tex", body, [path, f"results/{dataset}/summary.md"])
    write("wins.tex", table("Comparison counts (each proposed method has its own Holm family).",
                           ["Dataset", "Proposed", "Tests", "Pairs", "Win", "Loss", "Mixed", "None"], counts,
                           [2.4, 2.0, .6, .6, .55, .55, .55, .55]),
          [f"results/{d}/metrics.jsonl" for d in DATASETS])

    selected_path = "results/protocol_v2_sel/selected_e.json"
    selected = json.loads(read(selected_path))
    rows = []
    for m in ORDER:
        if m not in selected["selected"]:
            continue
        idx = selected["selected"][m]
        implementation, grid = selected["grids"][m]
        rows.append([m, idx, IMPLEMENTATIONS[implementation], parameters(grid[idx])])
    sources = [selected_path]
    body = table("Selected v2e baseline settings (zero-based grid indices).", ["Method", "Index", "Implementation", "Parameters"], rows, [1.8, .5, 1, 3.7])
    for name, file in ((REC, "main"), (REC_MW, "final")):
        p = f"results/final_dev/final_config_core_{file}.json"
        conf = json.loads(read(p)); sources.append(p)
        flags = conf["flags"]
        assert set(flags) <= set(FLAGS) | set(OMITTED_FLAGS), set(flags) - set(FLAGS) - set(OMITTED_FLAGS)
        assert all(flags[k] == v for k, v in OMITTED_FLAGS.items() if k in flags), name
        body += table(name + ": frozen flags.", ["Setting", "Value"],
                      [flag_row(k, flags[k]) for k in FLAGS if k in flags], [2, 1])
    p = "results/protocol_final_sel/selected.json"
    c = json.loads(read(p)); sources.append(p)
    body += table("Selected v1 baselines (also used in the cost and model-error studies).", ["Method", "Index", "Parameters"],
                  [[m, idx, parameters(c["grids"][m][1][idx])] for m, idx in c["selected"].items()], [1.5, .4, 3])
    write("settings.tex", body, sources)

    # Saved diagnostic summaries are the finest available artifact for some checks.
    diagnostics = [
        ("selection", ["protocol_v2_sel/selection_e.md"]),
        ("gap", ["gap_check/summary.md", "gap_check2/summary.md", "gap_check3/summary.md"]),
        ("restart", ["revision2_diag/n1_n2.md", "revision2_diag/a2_memory.md", "revision3_diag/s7_cold.md", "revision3_diag/rooms_shat.md", "revision5_diag/rls_prewindow.md"]),
        ("cftf", ["revision7_diag/cftf_515.md", "revision7_diag/cftf_515_nostab.md"]),
        ("extra", ["extra_eval/summary.md"]),
        ("ablation", ["ablation_core_b/stats.md", "ablation_core_c/stats.md", "ablation_core_d/stats.md"]),
    ]
    for name, files in diagnostics:
        body = ""
        for file in files:
            p = "results/" + file
            # No per-file heading: captions describe each table and the file header records its source.
            for title, headers, rows in markdown_tables(p):
                # Preserve archived values; omit the internal draft path from the published caption.
                if name == "gap":
                    title = title.replace("Statement B of [unpublished theory draft omitted]", "idealized gain analysis")
                if name == "extra" and len(headers) > 8:
                    rows = [[r[0], h, v] for r in rows for h, v in zip(headers[1:], r[1:]) if v]
                    headers = [headers[0], "Quantity / condition", "Archived value"]
                body += table(title, headers, rows, [2 if i == 0 else 1 for i in range(len(headers))])
        write(name + ".tex", body, ["results/" + p for p in files])

    p = "results/cg_ratio/raw.json"
    cg = json.loads(read(p))
    rows = []
    for k, ratios in cg.items():
        noise, cell = k.split("|")
        rows.append([noise, short(cell), len(ratios), f"{np.median(ratios):.6f}",
                     f"{np.quantile(ratios,.9):.6f}", f"{max(ratios):.6f}"])
    body = table("CG optimization/estimation error: archived plain-window hops (window at least 2M, no active event).",
                 ["Noise", "Cell", "Hops", "Median", "Q90", "Maximum"], rows)
    source = "results/cg_ratio/summary.md"
    for title, headers, rows in markdown_tables(source):
        body += table("Archived CG summary, including full-window eigenvalues.", headers, rows)
    write("cg.tex", body, [p, source])

    p = "results/shrink_theory.json"
    shrink = json.loads(read(p))
    body = table("Monte Carlo regression check: excess in units of noise variance. A dash means the plug-in was not evaluated.",
                 ["nA", "nB", "nA D/M", "Restart", "Pooled", "Oracle", "Plug-in", "JS"],
                 [[r["nA"], r["nB"], r["nA_D_over_M"]] +
                  ["--" if r[k] is None else f"{r[k]:.6f}" for k in ("restart", "pooled", "oracle", "plugin", "JS")]
                  for r in shrink])
    write("stein.tex", body, [p])

    # Revision 9: reproduce source content, not a reinterpreted summary.
    p = "results/final_eval_holdout/label_comparison.md"
    source = read(p)
    lines = source.splitlines()
    intro = [line for line in lines if line.strip() and not line.startswith(("#", "|"))]
    body = "".join(tex(line) + r"\par" + "\n" for line in intro)
    for title, headers, rows in markdown_tables(p):
        body += table("Like-for-like comparison: " + title, headers, rows, [1.6, 1.5, .85, .9, .85, 1.05, 2.1, 2.1, 1.8, 1.8])
    write("r9_labels.tex", body, [p])

    p = "results/protocol_v2_sel_cusum/selection.md"
    source = read(p)
    grid_path = "results/protocol_v2_sel_cusum/provenance.json"
    grid = json.loads(read(grid_path))["grid"]
    selection_rows = []
    for line in source.splitlines():
        m = re.match(r"- (\d+): (.+)", line)
        if m:
            idx = int(m.group(1)); cfg = grid[idx]
            selection_rows.append([idx, cfg["cusum_h"], cfg["cusum_k"], m.group(2)])
    assert len(selection_rows) == len(grid)
    body = table("CUSUM configuration selection (failed configurations are inadmissible).",
                 ["Index", "h", "W", "Selection score / status"], selection_rows)
    chosen = [re.fullmatch(r"Selected (\d+): (\{.*\}) \(score (\S+)\)\.", line) for line in source.splitlines()
              if line.startswith("Selected ")]
    assert len(chosen) == 1 and chosen[0], "selected CUSUM line"
    index, grid, score = chosen[0].groups()
    body += (f"Selected configuration {index}: " + parameters(ast.literal_eval(grid)) + f" (score {tex(score)})." +
             r"\par" + "\n")
    write("r9_cusum_selection.tex", body, [p, grid_path])

    p = "results/final_eval_meas_s_8a/wiener_per_seed.json"
    records = json.loads(read(p))
    rows = [[record["seed"], noise, f'{values["total_nr_db"]:.6f}',
             f'{values["anc_only_nr_db"]:.6f}', f'{values["controller_norm"]:.6f}']
            for record in records for noise, values in record["noise"].items()]
    assert len(rows) == 2 * len(records)
    write("r9_wiener_per_seed.tex", table("M-S stationary expectation reference per seed (dB), true secondary path.",
          ["Seed", "Noise", "Total NR", "ANC-only NR", "Controller norm"], rows), [p])

    metrics_path = "results/final_eval_meas_s_8a/metrics.jsonl"
    metrics = [json.loads(line) for line in read(metrics_path).splitlines()]
    references = {r["seed"]: r["noise"] for r in records}
    rows = []
    for noise in sorted({r["noise"] for r in metrics}):
        subset = [r for r in metrics if r["noise"] == noise and r["method"] == "RLS + det"]
        count = sum(r["A2"] < references[r["seed"]][noise]["total_nr_db"] for r in subset)
        rows.append([noise, count, len(subset)])
    write("r9_wiener_comparison.tex", table("M-S: seeds with RLS+det A2 below the stationary expectation reference; this reference is not a finite-run bound.",
          ["Noise", "Below reference", "Seeds"], rows), [p, metrics_path])

    datasets = ["final_eval_holdout", "protocol_v2_sel_cusum", "eval_roomB_x2", "eval_roomC_x2", "eval_snr10_x2", "final_eval_meas_s_8a", "final_eval_meas_p_8a", "final_eval_meas_ps_8a"]
    paths = [f"results/{d}/provenance.json" for d in datasets]
    rows = []
    for d, p in zip(datasets, paths):
        record = json.loads(read(p)); soft = record["software"]
        rows.append([DATASET_LABELS[d], record.get("python", "not recorded"), soft.get("numpy", "not recorded"), soft.get("scipy", "not recorded"), soft.get("pyroomacoustics", "not recorded")])
    rule = read("docs/current/REVISION_RULE_9a.md")
    version = re.search(r"v2e・8a: numpy ([0-9.]+x)", rule)
    assert version, "v2e NumPy family missing from Rule 9a"
    rows.insert(0, [DATASET_LABELS["final_eval_v2e"], "not recorded", version.group(1), "not recorded", "not recorded"])
    write("r9_environment.tex", table("Archived environments by evaluation set; dependency versions can prevent bit reproduction.",
          ["Dataset", "Python", "NumPy", "SciPy", "pyroomacoustics"], rows), paths+["docs/current/REVISION_RULE_9a.md"])

    # Revision 10: preserve every archived table value, splitting wide tables for legibility.
    for dataset in ("gap_check4", "gap_check4a", "gap_check4a_perseed"):
        path = f"results/{dataset}/summary.md"
        body = ""
        for title, headers, rows in markdown_tables(path):
            if len(headers) > 8:
                # Keep identifying columns in both parts of a wide table.
                split = 6
                for part, cols in enumerate((list(range(split)), [0] + list(range(split, len(headers))))):
                    body += table(f"{dataset}: {title}, part {part+1}", [headers[i] for i in cols], [[r[i] for i in cols] for r in rows])
            else:
                body += table(f"{dataset}: {title}", headers, rows)
        write(dataset + ".tex", body, [path])

    p = "results/gap_check4a/numeric.json"
    numeric = json.loads(read(p))["results"]
    rows = []
    for noise in ("ar1", "harmonic"):
        eig = numeric[noise]["eig"]
        rows.append([noise, "A", *[f"{v:.3f}" for v in eig["A_eig"]], f"{eig['A_frac_lt_half']:.3f}", "--"])
        rows.append([noise, "B (real)", *[f"{v:.3f}" for v in eig["B_eig_real"]], f"{eig['B_frac_lt_half']:.3f}", f"{eig['B_bias_rel_floor_db']:.1f}"])
    body = table("Revision 10a/10b: median eigenvalue summaries and mean-field B bias relative to floor (dB).", ["Noise", "Recursion", "min", "q05", "median", "q95", "max", "fraction below half", "B bias dB"], rows)
    write("gap_check4a_spectrum.tex", body, [p])

    measured_tables(write)
    manifest = {p: hashlib.sha256((ROOT / p).read_bytes()).hexdigest() for p in sorted(SOURCES)}
    (out / "sources.json").write_text(json.dumps({"inputs_sha256": manifest, "generated": generated}, indent=2) + "\n")
    print(f"Generated {len(generated)} tables from {len(manifest)} archived files in {out}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUT)
    generate(parser.parse_args().output)
