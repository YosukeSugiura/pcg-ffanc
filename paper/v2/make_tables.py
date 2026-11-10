"""LaTeX tables of the manuscript v2 from the stored per-run metrics (results/<dir>/metrics.jsonl, written by
experiments/final_eval.py summary). No simulation.
  Table I  (paper/v2/tables/main.tex)  : median A1 / A2 (dB) and failures, main evaluation (results/final_eval_v2b; v1 vs v2 table: final_eval vs final_eval_v2b)
  Table II (paper/v2/tables/rooms.tex) : the same for the additional conditions (eval_roomB, eval_roomC, eval_snr10)
  merged tables used in the manuscript: tables/rooms_bc.tex (rooms B and C) and tables/snr_measured.tex (SNR 10 dB and MeshRIR)
The proposed methods are read under their archived record labels (E-PCG, E-PCG bank) and shown as PCG-WLS and
PCG-WLS (multi-window) (ffanc_norm.naming).
usage: python paper/v2/make_tables.py
"""
import json
import sys
from pathlib import Path
import numpy as np
ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent / 'tables'; OUT.mkdir(exist_ok=True)
MAIN_DIR = 'final_eval_holdout'
R11_DIR = 'final_eval_holdout_r11'
MAIN_A2 = ''          # A2 rows of the added main-table baselines (set in main(), placed in the supplement by r11_tables())
sys.path.insert(0, str(ROOT / 'src'))
from ffanc_norm import naming as N  # noqa: E402
REC, REC_MW = N.RECORD_LABEL, N.RECORD_LABEL_MW   # record labels of PCG-WLS and PCG-WLS (multi-window)
ORDER = ['FD-FxNLMS', 'leaky FD-FxNLMS', 'convex FD-FxNLMS', 'FDKF', 'RLS', 'VFF-RLS', 'FD-FxNLMS + det',
         'FD-FxNLMS + restart', 'RLS + det', 'SFTF + det', 'SFTF-H + det', 'CFTF + det', 'RLS + CUSUM',
         'MFBLMS', 'MFBLMS + det', 'switching FD-FxNLMS [6]', 'switching FD-FxNLMS + det',
         REC_MW, REC]
# Revision 11: the four Must baselines added to the main tables (family F1, results/final_eval_holdout_r11); they appear
# only where their records are merged in (main tables), so the tables of the other sets are unchanged.
ADDED_MAIN = ['MFBLMS', 'MFBLMS + det', 'switching FD-FxNLMS [6]', 'switching FD-FxNLMS + det']
SHORT = {'FD-FxNLMS': 'FD-FxNLMS', 'leaky FD-FxNLMS': 'leaky', 'convex FD-FxNLMS': 'convex', 'FDKF': 'FDKF', 'RLS': 'RLS',
         'VFF-RLS': 'VFF-RLS', 'FD-FxNLMS + det': 'FD-FxNLMS+det',
         'FD-FxNLMS + restart': 'FD-FxNLMS+restart', 'SFTF + det': 'SFTF+det', 'SFTF-H + det': 'SFTF-H+det', 'CFTF + det': 'CFTF+det', 'RLS + det': 'RLS+det', REC_MW: N.PCG_WLS_MW,
         'RLS + CUSUM': 'RLS+CUSUM', REC: '\\textbf{' + N.PCG_WLS + '}',
         'MFBLMS': 'MFBLMS$^\\ddagger$', 'MFBLMS + det': 'MFBLMS+det$^\\ddagger$',
         'switching FD-FxNLMS [6]': 'switching$^\\ddagger$', 'switching FD-FxNLMS + det': 'switching+det$^\\ddagger$'}
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


A1_LABEL = 'A1 (first 0.512 s after the change; S5/R3: 0.592 s; S8: first 0.512 s)'
A2_LABEL = 'A2 (after A1 window; S8: last 1 s)'


def cell(M, meths, m, nz, sc, key, decisions=None):
    """One table cell: median of `key` over the runs of (m, nz, sc), failure superscript, decision superscript, bold."""
    rs = M.get((m, nz, sc), [])
    if not rs:
        return '--'
    v = np.median([r[key] for r in rs]); f = sum(r['fail'] for r in rs)
    # (review n22) methods with failures in more than half of the runs are not candidates for bold
    cand = [mm for mm in meths if (mm, nz, sc) in M and 2 * sum(r['fail'] for r in M[(mm, nz, sc)]) <= len(M[(mm, nz, sc)])]
    best = min(np.median([r[key] for r in M[(mm, nz, sc)]]) for mm in cand) if cand else None
    s = f'{v:.1f}' + (f'$^{{\\dagger{f}}}$' if f else '')
    if decisions is not None and key == 'A1' and m not in (REC, REC_MW):
        decision = decisions[(m, nz, sc)]
        symbol = {'win': 'w', 'loss': 'l', '-': '-', 'mixed': 'm'}[decision]
        s += r'$^{\text{--}}$' if symbol == '-' else r'$^{\mathrm{' + symbol + '}}$'
    return r'\textbf{' + s + '}' if best is not None and 2 * f <= len(rs) and np.isclose(v, best) else s


def note(with_decisions, extra=''):
    """Table note under the tabular (shared by table() and grouped_table())."""
    return (r'\\[2pt]{\scriptsize NR in dB; lower is better. $^h$ harmonic noise, otherwise AR(1). Bold: best median among methods failing in at most half of the runs; failure counts are separate outcomes. $^{\dagger k}$: $k$ failed runs of 40 (counted as 0 dB).' + extra + '}'
            + (r' {\scriptsize A1 superscripts w / -- / l / m: PCG-WLS win / no decision / loss / mixed over the A1 and A2 comparisons (criterion in Section~V-B).}' if with_decisions else ''))


def grouped_table(groups, caption, label, extra_note='', tabcolsep=None, show=None, keys=('A1', 'A2'), env='table*'):
    """Several evaluation sets side by side as column groups (two-level header with cmidrule).
    groups: list of (heading, M, combos, decisions). Rows: union of the methods of all groups in ORDER; a method not
    evaluated in a group gets '--' there. Each cell (median, superscripts, bold) is computed within its own group
    exactly as in table(). tabcolsep: optional column padding (e.g. '4pt') so that wide tables fit without scaling."""
    gm = [[m for m in ORDER if any((m, nz, sc) in M for nz, sc in combos)] for _, M, combos, _ in groups]
    meths = [m for m in ORDER if any(m in g for g in gm)]
    if show is not None:                       # rows shown; bold is still decided among all methods of each group
        meths = [m for m in meths if m in show]
    ncol = sum(len(c) for _, _, c, _ in groups)
    head, rules, cols, start = [], [], [], 2
    for heading, _, combos, _ in groups:
        head.append(r'\multicolumn{' + str(len(combos)) + r'}{c}{' + heading + '}')
        rules.append(r'\cmidrule(lr){' + f'{start}-{start + len(combos) - 1}' + '}'); start += len(combos)
        cols += [f'{CSHORT.get(sc, sc)}{"$^h$" if nz == "harmonic" else ""}' for nz, sc in combos]
    lines = [r'\begin{' + env + r'}[t]\centering\caption{' + caption + r'}\label{' + label + r'}',
             r'\scriptsize' + (r'\setlength{\tabcolsep}{' + tabcolsep + '}' if tabcolsep else ''),
             r'\RnineFitWidth{\begin{tabular}{l' + 'c' * ncol + '}', r'\toprule',
             ' & ' + ' & '.join(head) + r' \\', ''.join(rules), 'method & ' + ' & '.join(cols) + r' \\', r'\midrule']
    for key, lab in (('A1', A1_LABEL), ('A2', A2_LABEL)):
        if key not in keys:
            continue
        lines.append(r'\multicolumn{' + str(ncol + 1) + r'}{l}{\emph{' + lab + r', median dB}}\\')
        for m in meths:
            vals = [cell(M, g, m, nz, sc, key, dec) for (_, M, combos, dec), g in zip(groups, gm) for nz, sc in combos]
            lines.append(f'{SHORT[m]} & ' + ' & '.join(vals) + r' \\')
        lines.append(r'\midrule')
    lines[-1] = r'\bottomrule'
    lines += [r'\end{tabular}}', note(any(g[3] is not None for g in groups), extra_note), r'\end{' + env + '}']
    return '\n'.join(lines) + '\n'


def table(M, combos, caption, label, decisions=None, extra_note='', a2_hide=()):
    meths = [m for m in ORDER if any((m, nz, sc) in M for nz, sc in combos)]
    cols = ' & '.join(f'{CSHORT.get(sc, sc)}{"$^h$" if nz == "harmonic" else ""}' for nz, sc in combos)
    lines = [r'\begin{table*}[t]\centering\caption{' + caption + r'}\label{' + label + r'}', r'\scriptsize',
             r'\RnineFitWidth{\begin{tabular}{l' + 'c' * len(combos) + '}', r'\toprule', f'method & {cols} \\\\', r'\midrule']
    for key, lab in (('A1', A1_LABEL), ('A2', A2_LABEL)):
        lines.append(r'\multicolumn{' + str(len(combos) + 1) + r'}{l}{\emph{' + lab + r', median dB}}\\')
        for m in meths:
            if key == 'A2' and m in a2_hide:     # bold candidates still include the hidden rows
                continue
            vals = [cell(M, meths, m, nz, sc, key, decisions) for nz, sc in combos]
            lines.append(f'{SHORT[m]} & ' + ' & '.join(vals) + r' \\')
        lines.append(r'\midrule')
    lines[-1] = r'\bottomrule'
    lines += [r'\end{tabular}}', note(decisions is not None, extra_note), r'\end{table*}']
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
             r'cell & \multicolumn{2}{c}{v1 best baseline} & \multicolumn{2}{c}{v2 best baseline} & PCG-WLS & $\Delta_1$ & $\Delta_2$ \\',
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



def r11_labels(d, prefix):
    """{(baseline, noise, cell): label} of a Revision 11 family table ('## <prefix>...') in results/<d>/summary.md."""
    from make_r11_values import section
    return {(r['baseline'], r['noise'], r['cell']): r['label'] for r in section(d, prefix)}


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
        # Revision 11: merge the four added Must baselines (records and F1 labels); the cells of the prespecified rows
        # are unchanged (checked in r11_check_main)
        Mn, Wn = load(R11_DIR), r11_labels(R11_DIR, f'F1: {REC} vs')
        dec = dict(wins(MAIN_DIR))
        for k, rs in Mn.items():
            if k[0] in ADDED_MAIN:
                M[k] = rs
        dec.update({k: v for k, v in Wn.items() if k[0] in ADDED_MAIN})
        ntests_new = 2 * len(Wn)
        assert ntests_new == ntests == 390
        parts = []
        for noise, display, label in [('ar1', 'AR(1)', 'tab:main'), ('harmonic', 'harmonic', 'tab:main-harmonic')]:
            subset = [(nz, sc) for nz, sc in combos if nz == noise]
            caption = f'Main evaluation, {display} (holdout seeds {seed_set[0]}--{seed_set[-1]}, Holm over {ntests} tests per family, $M=512$): median A1 and A2. The +det, FD-FxNLMS+restart and switching+det rows share PCG-WLS detections.'
            parts.append(table(M, subset, caption, label, decisions=dec,
                               extra_note=r' $^\ddagger$: baselines added in revision, tested in a separate Holm family (' + str(ntests_new) + ' tests) against the same PCG-WLS records; their A2 medians are in Section~S5.',
                               a2_hide=ADDED_MAIN))
        # supplement: A2 of the four added rows (bold decided among all rows of the main tables)
        ar = [(nz, sc) for nz, sc in combos if nz == 'ar1']; hm = [(nz, sc) for nz, sc in combos if nz == 'harmonic']
        global MAIN_A2
        MAIN_A2 = (grouped_table(
            [('AR(1)', M, ar, None), ('harmonic', M, hm, None)],
            f'Baselines added in revision, room A (holdout seeds {seed_set[0]}--{seed_set[-1]}): median A2 (the A1 rows are in Tables~\\Mref{{tab:main}} and~\\Mref{{tab:main-harmonic}}).',
            'tab:main-a2', show=ADDED_MAIN, keys=('A2',), tabcolsep='3pt'))   # merged into tab:moved by r11_tables()
        (OUT / 'main.tex').write_text('\n'.join(parts))
        print('written', OUT / 'main.tex')
    parts, extra = [], {}
    for d, name in (('eval_roomB_x2', 'RT$_{60}$ 0.15 s'), ('eval_roomC_x2', 'RT$_{60}$ 0.3 s'), ('eval_snr10_x2', 'SNR 10 dB')):
        M = load(d)
        if M is None:
            continue
        combos = sorted({(nz, sc) for (_, nz, sc) in M}, key=lambda c: (c[0], list(CSHORT).index(c[1])))
        seeds = sorted({r['seed'] for rs in M.values() for r in rs})
        family = 2 * len(wins(d))
        extra[d] = (M, combos, seeds, family)
        parts.append(table(M, combos, f'Additional evaluation set: {name} (evaluation seeds {seeds[0]}--{seeds[-1]}; Holm over {family} tests; configurations unchanged).', f'tab:{d.removesuffix("_x2")}'))
    if parts:
        (OUT / 'rooms.tex').write_text('\n'.join(parts)); print('written', OUT / 'rooms.tex')
    # merged table of rooms B and C (column groups); the separate tables above stay in rooms.tex for checking
    if 'eval_roomB_x2' in extra and 'eval_roomC_x2' in extra:
        (MB, cB, sB, fB), (MC, cC, sC, fC) = extra['eval_roomB_x2'], extra['eval_roomC_x2']
        assert sB == sC, 'room B / C seed sets differ'
        cap = (f'Additional evaluation sets, rooms B (RT$_{{60}}$ 0.15 s) and C (RT$_{{60}}$ 0.3 s) (evaluation seeds {sB[0]}--{sB[-1]}; '
               f'Holm over {fB} tests in room B and over {fC} tests in room C, separate families; configurations unchanged).')
        (OUT / 'rooms_bc.tex').write_text(grouped_table([('Room B, RT$_{60}$ 0.15 s', MB, cB, None), ('Room C, RT$_{60}$ 0.3 s', MC, cC, None)], cap, 'tab:eval_rooms', tabcolsep='4pt'))
        print('written', OUT / 'rooms_bc.tex')
    cusum_table()
    r11_tables()
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
        # merged table: SNR 10 dB (room A) and measured RIR as column groups; the separate tables stay for checking
        if 'eval_snr10_x2' in extra:
            Ms, cs, ss, fs = extra['eval_snr10_x2']
            cap = (f'Additional evaluation sets, SNR 10 dB (room A; evaluation seeds {ss[0]}--{ss[-1]}; Holm over {fs} tests) and measured room impulse responses '
                   f'(MeshRIR; evaluation seeds {measurement_seeds[0]}--{measurement_seeds[-1]}); separate families; configurations unchanged. '
                   f'M-S stationary expectation reference with true $S$, total NR medians (AR(1)/harmonic): {ms_ref} dB.')
            (OUT / 'snr_measured.tex').write_text(grouped_table([('SNR 10 dB (room A)', Ms, cs, None), ('Measured RIR (MeshRIR)', Mm, combos, None)],
                                                                cap, 'tab:snr_measured', extra_note=' --: not evaluated.'))
            print('written', OUT / 'snr_measured.tex')


# ---------------------------------------------------------------- Revision 11 tables
SUPP = Path(__file__).resolve().parent / 'supp_tables'
R11_SHORT = {'RLS + det (cond.)': 'RLS+det (cond.)', 'RLS + det + growth': 'RLS+det+growth',
             'RLS + det + growth (from start)': 'RLS+det+growth (start)', 'RLS (extended grid)': 'RLS (ext.)',
             'VFF-RLS (extended grid)': 'VFF-RLS (ext.)', 'RLS + CUSUM (extended grid)': 'RLS+CUSUM (ext.)',
             'FD-FxNLMS (extended grid)': 'FD-FxNLMS (ext.)', 'FDKF (extended grid)': 'FDKF (ext.)',
             'FD-FxNLMS + det (extended grid)': 'FD-FxNLMS+det (ext.)', 'MFBLMS': 'MFBLMS', 'MFBLMS + det': 'MFBLMS+det',
             'switching FD-FxNLMS [6]': 'switching [6]', 'switching FD-FxNLMS + det': 'switching+det'}
PNAME = {'mu': r'$\mu$', 'det_boost': 'boost', 'sw_thr': r'$\Delta_{\rm THR}$', 'sw_dwell': r'$M_{\rm dwell}$',
         'lam': r'$\lambda$', 'det_cond_db': r'$\theta$', 'cusum_h': '$h$', 'cusum_k': '$W$', 'N0': '$N_0$',
         'P0': '$P_0$', 'scale': 'scale'}


def _cfg(params):
    """Compact display of the parameters that distinguish a selected configuration."""
    out = []
    for k in ('mu', 'det_boost', 'sw_thr', 'sw_dwell', 'lam', 'det_cond_db', 'cusum_h', 'cusum_k', 'N0', 'P0', 'scale'):
        if k in params:
            v = params[k]
            v = r'1/32' if k == 'scale' and abs(v - 1 / 32) < 1e-12 else (f'{v:g}' if isinstance(v, float) else str(v))
            out.append(f'{PNAME[k]} {v}' + (' dB' if k == 'det_cond_db' else ''))
    if params.get('det_grow'):
        out.append('from start' if params.get('det_grow_start') else 'at restarts')
    return ', '.join(out)


def _subset(M, methods):
    return {k: v for k, v in M.items() if k[0] in methods}


def _merge_floats(parts, caption, label):
    """One table* from several grouped_table() outputs: keeps each tabular, drops their floats, captions and notes, and adds
    one caption and the note of the last part."""
    body, note_line = [], None
    for t in parts:
        for l in t.split('\n'):
            if not l.strip() or l.startswith('%') or l.startswith(r'\begin{table') or l.startswith(r'\end{table'):
                continue
            if l.startswith(r'\\[2pt]'):
                note_line = l
                continue
            body.append(l)
        body.append(r'\\[4pt]')
    body[-1] = note_line
    return '\n'.join([r'\begin{table*}[t]\centering\caption{' + caption + r'}\label{' + label + '}'] + body + [r'\end{table*}']) + '\n'


def r11_tables():
    """Revision 11 tables: holdout rooms (tab:eval_rooms), SNR 10 dB and measured paths (tab:snr_measured), the
    ablation (tab:ablation) in the manuscript; added baselines and HL intervals in the supplement. Read-only on results/."""
    import make_r11_values as V11
    if not (ROOT / 'results' / R11_DIR / 'metrics.jsonl').exists():
        return
    shown = [m for m in ORDER if m not in ADDED_MAIN]           # 13 prespecified baselines and the two proposals
    # rows moved to the supplement (author decision, 2026-11-09): FD-type variants whose individual values the text does
    # not quote (it states the six FD-type baselines as a group and quotes FD-FxNLMS itself); bold is still decided
    # among all 15 rows
    moved = ['leaky FD-FxNLMS', 'convex FD-FxNLMS', 'FD-FxNLMS + restart']
    main_rows = [m for m in shown if m not in moved]
    # --- rooms B and C, holdout
    sets = {}
    for d in ('eval_roomB_h', 'eval_roomC_h', 'eval_snr10_h', 'final_eval_meas_s_h', 'final_eval_meas_p_h'):
        Mfull = load(d)
        M = _subset(Mfull, shown)
        combos = sorted({(nz, sc) for (_, nz, sc) in M}, key=lambda c: (c[0], list(CSHORT).index(c[1])))
        seeds = sorted({r['seed'] for rs in M.values() for r in rs})
        nb = len({k[0] for k in Mfull} - {REC, REC_MW})
        fam = 2 * len(V11.section(d, f'F3: {REC} vs'))
        sets[d] = (M, combos, seeds, fam, nb)
    (MB, cB, sB, fB, nB), (MC, cC, sC, fC, nC) = sets['eval_roomB_h'], sets['eval_roomC_h']
    assert sB == sC and nB == nC == 26
    cap = (f'Rooms B (RT$_{{60}}$ 0.15 s) and C (RT$_{{60}}$ 0.3 s), holdout seeds {sB[0]}--{sB[-1]}: median A1 (A2 in Section~S5). '
           f'Holm over {fB} tests per room (PCG-WLS against all {nB} baselines, one family per room); configurations unchanged. '
           f'Leaky FD-FxNLMS, convex FD-FxNLMS and FD-FxNLMS+restart are in Section~S5 (bold decided among all 15 rows); the 13 baselines added in revision are in the archived results.')
    (OUT / 'rooms_bc_h.tex').write_text(grouped_table([('Room B, RT$_{60}$ 0.15 s', MB, cB, None), ('Room C, RT$_{60}$ 0.3 s', MC, cC, None)],
                                                      cap, 'tab:eval_rooms', tabcolsep='4pt', show=main_rows, keys=('A1',)))
    rooms_groups = [('Room B, RT$_{60}$ 0.15 s', MB, cB, None), ('Room C, RT$_{60}$ 0.3 s', MC, cC, None)]
    Ms, cs, ss, fs, _ = sets['eval_snr10_h']
    Mm, cm = {}, []
    for d, lab in (('final_eval_meas_s_h', 'M-S'), ('final_eval_meas_p_h', 'M-P')):
        M, _, sm, fm, _ = sets[d]
        for (m, nz, _), rs in M.items():
            Mm.setdefault((m, nz, lab), []).extend(rs)
        cm += [(nz, lab) for nz in ('ar1', 'harmonic')]
    assert sm == ss
    wl = [l for l in (ROOT / 'results/final_eval_meas_s_h/wiener.md').read_text().splitlines() if l.startswith('| ar1 |') or l.startswith('| harmonic |')]
    ms_ref = '/'.join(f'{float(l.split("|")[2].strip().split()[0]):.1f}' for l in wl)
    fms = sets['final_eval_meas_s_h'][3]; fmp = sets['final_eval_meas_p_h'][3]
    cap = (f'SNR 10 dB (room A; Holm over {fs} tests) and measured room impulse responses M-S and M-P (MeshRIR; Holm over {fms} and {fmp} tests), '
           f'holdout seeds {ss[0]}--{ss[-1]}: median A1 (A2 in Section~S5). Separate families with all 26 baselines; configurations unchanged. '
           f'M-S stationary expectation reference with true $S$, total NR medians (AR(1)/harmonic): {ms_ref} dB. Leaky FD-FxNLMS, convex FD-FxNLMS and FD-FxNLMS+restart are in Section~S5 (bold decided among all 15 rows).')
    (OUT / 'snr_measured_h.tex').write_text(grouped_table([('SNR 10 dB (room A)', Ms, cs, None), ('Measured RIR (MeshRIR)', Mm, cm, None)],
                                                          cap, 'tab:snr_measured', show=main_rows, keys=('A1',)))
    snr_groups = [('SNR 10 dB (room A)', Ms, cs, None), ('Measured RIR (MeshRIR)', Mm, cm, None)]
    # supplement (author decisions 2026-11-09): the A2 blocks of Tables V/VI (all 15 rows), the A1 rows of the three
    # FD-type baselines moved out of them, and the A2 rows of the four added baselines of Tables II/III
    t_rooms = [grouped_table(rooms_groups, 'x', 'x', tabcolsep='3pt', show=moved, keys=('A1',)),
               grouped_table(rooms_groups, 'x', 'x', tabcolsep='3pt', keys=('A2',))]
    t_snr = [grouped_table(snr_groups, 'x', 'x', tabcolsep='3pt', show=moved, keys=('A1',)),
             grouped_table(snr_groups, 'x', 'x', tabcolsep='3pt', keys=('A2',)), MAIN_A2]
    cap1 = ('Supplement to Table~\\Mref{tab:eval_rooms} (rooms B and C, holdout seeds): top, median A1 of leaky FD-FxNLMS, convex FD-FxNLMS and '
            'FD-FxNLMS+restart; bottom, median A2 of all 15 rows. Bold decided among all 15 rows.')
    cap2 = ('Supplement to Tables~\\Mref{tab:snr_measured}, \\Mref{tab:main} and~\\Mref{tab:main-harmonic} (holdout seeds): top, median A1 of leaky FD-FxNLMS, '
            'convex FD-FxNLMS and FD-FxNLMS+restart for SNR 10 dB, M-S and M-P; middle, median A2 of all 15 rows; bottom, median A2 of the four '
            'baselines added in revision in room A. Bold decided among all rows of the corresponding manuscript table.')
    (SUPP / 'r11_moved_rows.tex').write_text('% Generated by make_tables.py (r11_tables); do not edit.\n' +
                                             _merge_floats(t_rooms, cap1, 'tab:rooms-a2') + _merge_floats(t_snr, cap2, 'tab:snr-a2'))
    print('written', OUT / 'rooms_bc_h.tex', OUT / 'snr_measured_h.tex')

    # --- ablation (manuscript Table, compact) and full version (supplement)
    hold, new, abl = V11.load(MAIN_DIR), V11.load(R11_DIR), V11.load('r11_ablation_holdout')
    rows = [('PCG-WLS', hold, REC, None), ('fixed order', abl, V11.ABLATION[0], 0), ('restart', abl, V11.ABLATION[1], 1),
            ('no detector', abl, V11.ABLATION[2], 2), ('fixed order, restart', abl, V11.ABLATION[3], 3),
            ('exact solver', abl, V11.ABLATION[4], 4), ('RLS+det', hold, 'RLS + det', None),
            ('RLS+det+growth', new, 'RLS + det + growth', None), ('\\quad from start', new, 'RLS + det + growth (from start)', None)]
    cols = [('ar1', 'S8 stationary'), ('ar1', 'S7 rd abrupt'), ('ar1', 'S2 src 30cm'), ('ar1', 'R2 rig 30cm'),
            ('harmonic', 'S2 src 30cm'), ('harmonic', 'S5 src 30cm cont')]
    colname = lambda nz, sc: CSHORT[sc] + ('$^h$' if nz == 'harmonic' else '')
    body = []
    for name, M, m, gi in rows:
        if gi is not None:
            c = V11.counts_line('r11_ablation_holdout', f'(ii) {m} vs')
            worse = {(r['noise'], r['cell']) for r in V11.section('r11_ablation_holdout', f'(i) {m} - G0') if r['flag'] == 'worse'}
            bw, wc = f"{c['win']}/{c['loss']}/{c['mixed']}", str(len(worse))
        elif m == REC:
            P = V11.labels(V11.section(MAIN_DIR, f'{REC} vs baselines'))
            bw, wc = '/'.join(str(sum(r['label'] == k for r in P.values())) for k in ('win', 'loss', 'mixed')), '--'
        else:
            bw, wc = '--', '--'
        vals = [f"{V11.med(M, m, nz, sc, 'A1'):.1f}" for nz, sc in cols]
        body.append(' & '.join([name, bw, wc] + vals) + r' \\')
    cap = ('Ablation of PCG-WLS on the holdout seeds 800--839 (room A): median A1 (dB) in six cells. B/W/M: better/worse/mixed in the 195 '
           'comparisons with the 13 prespecified baselines (one Holm family of 390 tests per variant). '
           'Worse: cells in which the variant is worse than PCG-WLS (Holm over 30 tests, same criterion). All 15 cells are in the archived results (index in Section~S6).')
    lines = [r'\begin{table}[t]\centering\caption{' + cap + r'}\label{tab:ablation}', r'\scriptsize\setlength{\tabcolsep}{2.5pt}',
             r'\begin{tabular}{@{}lrr' + 'r' * len(cols) + r'@{}}\toprule',
             'variant & B/W/M & worse & ' + ' & '.join(colname(*c) for c in cols) + r' \\\midrule'] + body[:6] + [r'\midrule'] + body[6:] + \
            [r'\bottomrule\end{tabular}', r'\end{table}']
    (OUT / 'ablation.tex').write_text('% Generated by make_tables.py (r11_tables) from results/r11_ablation_holdout, final_eval_holdout, final_eval_holdout_r11; do not edit.\n' + '\n'.join(lines) + '\n')
    allc = V11.combos()
    # --- added baselines (supplement): selection, tuning score, labels against PCG-WLS (F1), paired A1 range
    sel = json.loads((ROOT / 'results/protocol_r11_sel/selected.json').read_text())
    F1 = V11.labels(V11.section(R11_DIR, f'F1: {REC} vs'))
    P = V11.labels(V11.section(MAIN_DIR, f'{REC} vs baselines'))
    body = []
    for b in V11.ADDED:
        row = sel['new_rows'][b]
        lab = [F1[(b, nz, sc)]['label'] for nz, sc in allc]
        dA1 = [V11.num(F1[(b, nz, sc)]['med dA1']) for nz, sc in allc]
        if b in V11.EXTENDED:
            base = V11.EXTENDED[b]
            ref = sel['outer'][base]['reference_score']
            bw0 = sum(P[(base, nz, sc)]['label'] == 'win' for nz, sc in allc)
            note_ = f'{ref:.2f}; {bw0}'
        else:
            note_ = '--'
        body.append(' & '.join([R11_SHORT[b], _cfg(row['params']), f"{row['score']:.2f}", note_,
                                f"{lab.count('win')}/{lab.count('loss')}", f'{min(dA1):+.1f} to {max(dA1):+.1f}']) + r' \\')
    cap = ('Baselines added in revision (room A). Score: tuning score (mean of (A1+A2)/2, dB) of the selected configuration. '
           'Orig.: score of the original selection and its number of holdout comparisons in which PCG-WLS was better. '
           'B/W: PCG-WLS better/worse of 15 (family of 390 tests). $\\Delta$A1: range over the 15 cells of the median paired A1 difference, PCG-WLS minus baseline.')
    lines = [r'\begin{table}[!t]\centering\caption{' + cap + r'}\label{tab:added}', r'\scriptsize\setlength{\tabcolsep}{2pt}',
             r'\begin{tabular}{@{}>{\raggedright}p{0.21\columnwidth}>{\raggedright}p{0.25\columnwidth}rlrr@{}}\toprule',
             r'baseline & selection & score & orig. & B/W & $\Delta$A1 \\\midrule'] + body + [r'\bottomrule\end{tabular}', r'\end{table}']
    (SUPP / 'r11_added.tex').write_text('% Generated by make_tables.py (r11_tables) from results/protocol_r11_sel and final_eval_holdout_r11; do not edit.\n' + '\n'.join(lines) + '\n')

    # --- PCG-WLS minus RLS+det: HL estimate and 95 % seed-bootstrap interval (descriptive)
    body = []
    for nz, sc in allc:
        cells = [colname(nz, sc)]
        for key in ('A1', 'A2'):
            A, B = hold[(REC, nz, sc)], hold[('RLS + det', nz, sc)]
            d = [A[s][key] - B[s][key] for s in sorted(A)]
            hl, lo, hi = V11.hl_ci(d)
            cells.append(f'{hl:+.2f} [{lo:+.2f}, {hi:+.2f}]')
        body.append(' & '.join(cells) + r' \\')
    cap = ('PCG-WLS minus RLS+det on the holdout seeds: Hodges--Lehmann estimate and 95\\,\\% seed-bootstrap interval (dB; '
           '10\\,000 resamples). Descriptive, computed after the labels were fixed.')
    lines = [r'\begin{table}[!t]\centering\caption{' + cap + r'}\label{tab:hl}', r'\scriptsize\setlength{\tabcolsep}{3pt}',
             r'\begin{tabular}{@{}lrr@{}}\toprule', r'cell & A1 & A2 \\\midrule'] + body + [r'\bottomrule\end{tabular}', r'\end{table}']
    (SUPP / 'r11_hl.tex').write_text('% Generated by make_tables.py (r11_tables) from results/final_eval_holdout/metrics.jsonl; do not edit.\n' + '\n'.join(lines) + '\n')

    print('written', OUT / 'ablation.tex', SUPP / 'r11_added.tex', SUPP / 'r11_hl.tex')


if __name__ == '__main__':
    main()
