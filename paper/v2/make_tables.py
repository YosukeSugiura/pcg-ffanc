"""LaTeX tables of the manuscript v2 from the stored per-run metrics (results/<dir>/metrics.jsonl, written by
experiments/final_eval.py summary). No simulation.
  Table I  (paper/v2/tables/main.tex)  : median A1 / A2 (dB) and failures, main evaluation (results/final_eval_v2b; v1 vs v2 table: final_eval vs final_eval_v2b)
  Table II (paper/v2/tables/rooms.tex) : the same for the additional conditions (eval_roomB, eval_roomC, eval_snr10)
The proposed methods are read under their archived record labels (E-PCG, E-PCG bank) and shown as PCG-WLS and
PCG-WLS (multi-window) (ffanc_norm.naming).
usage: python paper/v2/make_tables.py
"""
import json
import sys
from pathlib import Path
import numpy as np
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'src'))
from ffanc_norm import naming as N  # noqa: E402
REC, REC_MW = N.RECORD_LABEL, N.RECORD_LABEL_MW   # record labels of PCG-WLS and PCG-WLS (multi-window)
OUT = Path(__file__).resolve().parent / 'tables'; OUT.mkdir(exist_ok=True)
MAIN_DIR = 'final_eval_holdout'
ORDER = ['FD-FxNLMS', 'leaky FD-FxNLMS', 'convex FD-FxNLMS', 'FDKF', 'RLS', 'VFF-RLS', 'FD-FxNLMS + det',
         'FD-FxNLMS + restart', 'RLS + det', 'SFTF + det', 'SFTF-H + det', 'CFTF + det', 'RLS + CUSUM',
         REC_MW, REC]
SHORT = {'FD-FxNLMS': 'FD-FxNLMS', 'leaky FD-FxNLMS': 'leaky', 'convex FD-FxNLMS': 'convex', 'FDKF': 'FDKF', 'RLS': 'RLS',
         'VFF-RLS': 'VFF-RLS', 'FD-FxNLMS + det': 'FD-FxNLMS+det',
         'FD-FxNLMS + restart': 'FD-FxNLMS+restart', 'SFTF + det': 'SFTF+det', 'SFTF-H + det': 'SFTF-H+det', 'CFTF + det': 'CFTF+det', 'RLS + det': 'RLS+det', REC_MW: N.PCG_WLS_MW,
         'RLS + CUSUM': 'RLS+CUSUM', REC: '\\textbf{' + N.PCG_WLS + '}'}
CSHORT = {'S8 stationary': 'S8', 'S1 src 10cm': 'S1', 'S2 src 30cm': 'S2', 'S5 src 30cm cont': 'S5', 'S7 rd abrupt': 'S7',
          'R1 rig 10cm': 'R1', 'R2 rig 30cm': 'R2', 'R3 rig 30cm cont': 'R3'}


def load(d):
    p = ROOT / 'results' / d / 'metrics.jsonl'
    if not p.exists():
        return None
    M = {}
    for line in p.read_text().splitlines():
        r = json.loads(line)
        M.setdefault((r['method'], r['noise'], r['scen']), []).append(r)
    return M


def table(M, combos, caption, label, decisions=None):
    meths = [m for m in ORDER if any((m, nz, sc) in M for nz, sc in combos)]
    cols = ' & '.join(f'{CSHORT.get(sc, sc)}{"$^h$" if nz == "harmonic" else ""}' for nz, sc in combos)
    lines = [r'\begin{table*}[t]\centering\caption{' + caption + r'}\label{' + label + r'}', r'\scriptsize',
             r'\RnineFitWidth{\begin{tabular}{l' + 'c' * len(combos) + '}', r'\toprule', f'method & {cols} \\\\', r'\midrule']
    for key, lab in (('A1', 'A1 (first 0.512 s after the change; S5/R3: 0.592 s; S8: first 0.512 s)'), ('A2', 'A2 (after A1 window; S8: last 1 s)')):
        lines.append(r'\multicolumn{' + str(len(combos) + 1) + r'}{l}{\emph{' + lab + r', median dB}}\\')
        for m in meths:
            vals = []
            for nz, sc in combos:
                rs = M.get((m, nz, sc), [])
                if not rs:
                    vals.append('--'); continue
                v = np.median([r[key] for r in rs]); f = sum(r['fail'] for r in rs)
                # (review n22) methods with failures in more than half of the runs are not candidates for bold
                cand = [mm for mm in meths if (mm, nz, sc) in M and 2 * sum(r['fail'] for r in M[(mm, nz, sc)]) <= len(M[(mm, nz, sc)])]
                best = min(np.median([r[key] for r in M[(mm, nz, sc)]]) for mm in cand) if cand else None
                s = f'{v:.1f}' + (f'$^{{\\dagger{f}}}$' if f else '')
                if decisions is not None and key == 'A1' and m not in (REC, REC_MW):
                    decision = decisions[(m, nz, sc)]
                    symbol = {'win': 'w', 'loss': 'l', '-': '-', 'mixed': 'm'}[decision]
                    s += r'$^{\text{--}}$' if symbol == '-' else r'$^{\mathrm{' + symbol + '}}$'
                vals.append(r'\textbf{' + s + '}' if best is not None and 2 * f <= len(rs) and np.isclose(v, best) else s)
            lines.append(f'{SHORT[m]} & ' + ' & '.join(vals) + r' \\')
        lines.append(r'\midrule')
    lines[-1] = r'\bottomrule'
    lines += [r'\end{tabular}}', r'\\[2pt]{\scriptsize $^h$ harmonic noise, otherwise AR(1). Bold: best median among methods failing in at most half of the runs; failure counts are separate outcomes. $^{\dagger k}$: $k$ failed runs of 40 (counted as 0 dB).}' + (r' {\scriptsize A1 superscripts w / -- / l / m: PCG-WLS win / no decision / loss / mixed over the A1 and A2 comparisons; not equivalence. See Section S11 of the supplementary material.}' if decisions is not None else ''), r'\end{table*}']
    return '\n'.join(lines) + '\n'


def wins(d, prop=REC):
    """{(baseline, noise, cell): label} of the '<prop> vs baselines' table in results/<d>/summary.md."""
    p = ROOT / 'results' / d / 'summary.md'
    if not p.exists():
        return None
    out, on = {}, False
    for line in p.read_text().splitlines():
        if line.startswith('## '):
            on = line.startswith(f'## {prop} vs baselines')
        elif on and line.startswith('| ') and not line.startswith('| baseline'):
            c = [x.strip() for x in line.strip('|').split('|')]
            out[(c[0], c[1], c[2])] = c[-1]
    return out


def v1v2():
    """Table III: first final evaluation (v1: mean-NR selection, no detector-equipped baselines) vs v2 (A1-aligned
    selection, detector-equipped baselines). Per condition: best baseline by median A1 and its median, PCG-WLS median,
    difference; win / loss / none counts of PCG-WLS. No simulation; both from the stored per-run metrics."""
    M1, M2 = load('final_eval'), load('final_eval_v2e')     # v2e = v2d + 'CFTF + det' (REVISION_RULE_7)
    W1, W2 = wins('final_eval'), wins('final_eval_v2e')
    if M1 is None or M2 is None:
        return None
    assert W1 and W2, 'summary.md of final_eval / final_eval_v2 missing'
    for k in M2:                                   # PCG-WLS records of v1 and v2 are the same (reused): check
        if k[0] == REC:
            assert sorted(r['A1'] for r in M1[k]) == sorted(r['A1'] for r in M2[k]), k
    combos = [(nz, sc) for nz in ('ar1', 'harmonic') for sc in CSHORT if (nz, sc) != ('harmonic', 'S7 rd abrupt')]
    med = lambda M, m, nz, sc: float(np.median([r['A1'] for r in M[(m, nz, sc)]]))
    lines = [r'\begin{table}[t]\centering\caption{First (v1) and revised (v2) final evaluation: median A1 (dB) of the best'
             r' baseline and of PCG-WLS.}\label{tab:v1v2}', r'\scriptsize', r'\begin{tabular}{llrlrrrr}', r'\toprule',
             r'cond. & \multicolumn{2}{c}{v1 best baseline} & \multicolumn{2}{c}{v2 best baseline} & PCG-WLS & $\Delta_1$ & $\Delta_2$ \\',
             r'\midrule']
    for nz, sc in combos:
        e = med(M2, REC, nz, sc)
        row = [f'{CSHORT.get(sc, sc)}{"$^h$" if nz == "harmonic" else ""}']
        ds = []
        for M in (M1, M2):
            bs = [m for m in ORDER if m not in (REC, REC_MW) and (m, nz, sc) in M]
            b = min(bs, key=lambda m: med(M, m, nz, sc))
            row += [SHORT[b], f'{med(M, b, nz, sc):.1f}']; ds.append(f'{e - med(M, b, nz, sc):+.1f}')
        lines.append(' & '.join(row + [f'{e:.1f}'] + ds) + r' \\')
    cnt = lambda W: {k: sum(v == lab for v in W.values()) for k, lab in
                     (('win', 'win'), ('loss', 'loss'), ('mixed', 'mixed'), ('none', '-'))}   # summary.md labels
    c1, c2 = cnt(W1 or {}), cnt(W2 or {})
    lines += [r'\bottomrule', r'\end{tabular}',
              r'\\[2pt]{\scriptsize $^h$ harmonic noise. $\Delta_{1,2}$: PCG-WLS minus the v1 / v2 best baseline (difference of '
              r'medians). PCG-WLS vs all baselines (Holm): ' +
              f'v1 {c1["win"]} win / {c1["loss"]} loss / {c1["mixed"]} mixed / {c1["none"]} none of {len(W1 or {})}; '
              f'v2 {c2["win"]} / {c2["loss"]} / {c2["mixed"]} / {c2["none"]} of {len(W2 or {})}. Holm over 180 (v1) / 360 (v2) tests.' + '}', r'\end{table}']
    return '\n'.join(lines) + '\n'



def cusum_table():
    source = ROOT / 'results' / MAIN_DIR / 'cusum_comparison.md'
    rows = []
    for line in source.read_text().splitlines():
        if line.startswith('| ar1 |') or line.startswith('| harmonic |'):
            c = [x.strip() for x in line.strip('|').split('|')]
            rows.append([c[0], c[1].split()[0], c[4], c[5], c[6], c[7]])
    assert len(rows) == 15
    seed_set = sorted({r['seed'] for rs in load(MAIN_DIR).values() for r in rs})
    caption = f'RLS+CUSUM minus RLS+det: paired median differences on holdout seeds {seed_set[0]}--{seed_set[-1]}; descriptive, dB.'
    body = [r'\begin{table}[t]\centering\caption{' + caption + r'}\label{tab:cusum}', r'\scriptsize\begin{tabular}{llrrrr}\toprule', r'Noise & Cell & $\Delta$A1 & $|\Delta$A1$|$ & $\Delta$A2 & Fail. \\ \midrule']
    body += [' & '.join(row) + r' \\' for row in rows]
    body += [r'\bottomrule\end{tabular}\\{\scriptsize Failures: CUSUM / det.}', r'\end{table}']
    (OUT / 'cusum.tex').write_text('\n'.join(body)+'\n')


def main():
    t = v1v2()
    if t is not None:
        (OUT / 'v1v2.tex').write_text(t); print('written', OUT / 'v1v2.tex')
    M = load(MAIN_DIR)
    if M is not None:
        combos = [(nz, sc) for nz in ('ar1', 'harmonic') for sc in CSHORT if (nz, sc) != ('harmonic', 'S7 rd abrupt')]
        seed_set = sorted({r['seed'] for rs in M.values() for r in rs})
        ntests = 2 * len(wins(MAIN_DIR))
        parts = []
        for noise, display, label in [('ar1', 'AR(1)', 'tab:main'), ('harmonic', 'harmonic', 'tab:main-harmonic')]:
            subset = [(nz, sc) for nz, sc in combos if nz == noise]
            caption = f'Main evaluation, {display} (holdout seeds {seed_set[0]}--{seed_set[-1]}, Holm over {ntests} tests, $M=512$): median A1 and A2. The +det and FD-FxNLMS+restart rows share PCG-WLS detections.'
            parts.append(table(M, subset, caption, label, decisions=wins(MAIN_DIR)))
        (OUT / 'main.tex').write_text('\n'.join(parts))
        print('written', OUT / 'main.tex')
    parts = []
    for d, name in (('eval_roomB_x2', 'RT$_{60}$ 0.15 s'), ('eval_roomC_x2', 'RT$_{60}$ 0.3 s'), ('eval_snr10_x2', 'SNR 10 dB')):
        M = load(d)
        if M is None:
            continue
        combos = sorted({(nz, sc) for (_, nz, sc) in M}, key=lambda c: (c[0], list(CSHORT).index(c[1])))
        seeds = sorted({r['seed'] for rs in M.values() for r in rs})
        family = 2 * len(wins(d))
        parts.append(table(M, combos, f'Additional condition: {name} (evaluation seeds {seeds[0]}--{seeds[-1]}; Holm over {family} tests; configurations unchanged).', f'tab:{d.removesuffix("_x2")}'))
    if parts:
        (OUT / 'rooms.tex').write_text('\n'.join(parts)); print('written', OUT / 'rooms.tex')
    cusum_table()
    # measured paths (MeshRIR, Revision 8a): meas_p runs carry the S2 label, meas_ps the R2 label
    Mm = {}
    for d, lab in (('final_eval_meas_s_8a', 'M-S'), ('final_eval_meas_p_8a', 'M-P'), ('final_eval_meas_ps_8a', 'M-PS')):
        M = load(d)
        if M is None:
            continue
        for (m, nz, _), rs in M.items():
            Mm.setdefault((m, nz, lab), []).extend(rs)
    if Mm:
        combos = [(nz, sc) for sc in ('M-S', 'M-P', 'M-PS') for nz in ('ar1', 'harmonic')]
        measurement_seeds = sorted({r['seed'] for rs in Mm.values() for r in rs})
        wiener_rows = [l for l in (ROOT / 'results/final_eval_meas_s_8a/wiener.md').read_text().splitlines() if l.startswith('| ar1 |') or l.startswith('| harmonic |')]
        assert len(wiener_rows) == 2
        ms_ref = '/'.join(f'{float(l.split("|")[2].strip().split()[0]):.1f}' for l in wiener_rows)
        (OUT / 'measured.tex').write_text(table(Mm, combos, f'Measured room impulse responses (MeshRIR; evaluation seeds {measurement_seeds[0]}--{measurement_seeds[-1]}; configurations unchanged). M-S stationary expectation reference with true $S$, total NR medians (AR(1)/harmonic): {ms_ref} dB.', 'tab:measured'))
        print('written', OUT / 'measured.tex')


if __name__ == '__main__':
    main()
