"""Figures of the manuscript v2 (paper/v2/figs/*.pdf) from the stored results (no new simulations except the
eigenvalue analysis of gap_check, which re-runs the signal generator for 3 seeds: ~10 s).

Palette: validated categorical slots (dataviz validator, light surface: all checks pass; contrast WARN for aqua, yellow,
magenta -> secondary encoding by markers / line style and a legend). Proposed methods: near-black solid (PCG-WLS) and
blue dashed (PCG-WLS (multi-window)). Curves are read under their archived record labels; legends show the current
names (ffanc_norm.naming).
usage: python paper/v2/make_figures.py
"""
import re, sys
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent / 'figs'; OUT.mkdir(exist_ok=True)
sys.path.insert(0, str(ROOT / 'src')); sys.path.insert(0, str(ROOT / 'experiments'))
from ffanc_norm import naming as N  # noqa: E402
REC, REC_MW = N.RECORD_LABEL, N.RECORD_LABEL_MW   # record labels of PCG-WLS and PCG-WLS (multi-window)

INK = '#2b2b2a'; MUTED = '#6f6e69'; GRID = '#e4e3dd'
STYLE = {  # method: (color, linestyle, marker, linewidth)
    REC: ('#1a1a19', '-', None, 2.0), REC_MW: ('#2a78d6', '--', None, 1.6),
    'FD-FxNLMS': ('#eb6834', '-', 'o', 1.0), 'leaky FD-FxNLMS': ('#1baf7a', '-', 's', 1.0),
    'convex FD-FxNLMS': ('#eda100', '-', '^', 1.0), 'RLS': ('#e87ba4', '-', 'v', 1.0),
    'RLS + CUSUM': ('#a1436d', '--', 'x', 1.4), 'VFF-RLS': ('#008300', '-', 'D', 1.0), 'FDKF': ('#6250d6', '-', 'P', 1.0),
    # detector-equipped baselines (v2, 2026-10-30): colour of the base method, dash-dot
    'FD-FxNLMS + det': ('#eb6834', '-.', 'X', 1.0), 'RLS + det': ('#e87ba4', '-.', '*', 1.8),
    'FD-FxNLMS + restart': ('#eb6834', ':', 'P', 1.2), 'SFTF + det': ('#6f6e69', '--', 'd', 1.3), 'SFTF-H + det': ('#1baf7a', ':', 'h', 1.6), 'CFTF + det': ('#6250d6', ':', '*', 1.6)}
ORDER = ['FD-FxNLMS', 'leaky FD-FxNLMS', 'convex FD-FxNLMS', 'RLS', 'VFF-RLS', 'FDKF', REC_MW, REC]
ORDER_V2 = ['FD-FxNLMS', 'leaky FD-FxNLMS', 'convex FD-FxNLMS', 'RLS', 'VFF-RLS', 'FDKF', 'FD-FxNLMS + det',
            'FD-FxNLMS + restart', 'RLS + det', 'SFTF + det', 'SFTF-H + det', 'CFTF + det', 'RLS + CUSUM',
            REC_MW, REC]
plt.rcParams.update({'font.size': 8, 'axes.edgecolor': MUTED, 'axes.labelcolor': INK, 'xtick.color': MUTED,
                     'ytick.color': MUTED, 'axes.grid': True, 'grid.color': GRID, 'grid.linewidth': 0.6,
                     'legend.frameon': False, 'axes.spines.top': False, 'axes.spines.right': False,
                     'pdf.fonttype': 42})
COL1 = 3.5; COL2 = 7.16      # IEEE column / page width (inch)


def plot_method(ax, x, y, m, label=True, every=40):
    c, ls, mk, lw = STYLE[m]
    ax.plot(x, y, color=c, ls=ls, lw=lw, marker=mk, markevery=every, ms=3.5, label=N.display_label(m) if label else None,
            zorder=5 if m in (REC, REC_MW) else 3)


def _fig_learning(methods, basename):
    # The independent holdout curves are archived; no simulations are run.
    z = np.load(ROOT / 'results/final_eval_holdout/curves.npz'); t = z['time_s']
    panels = [('ar1', 'S8 stationary', '(a) stationary, AR(1)'), ('ar1', 'S7 rd abrupt', '(b) abrupt plant change, AR(1)'),
              ('harmonic', 'S2 src 30cm', '(c) source move 30 cm, harmonic'), ('harmonic', 'R2 rig 30cm', '(d) control-unit move 30 cm, harmonic')]
    fig, axs = plt.subplots(2, 2, figsize=(COL2, 4.4), sharex=True)
    for ax, (nz, sc, title) in zip(axs.ravel(), panels):
        for m in methods:
            k = f'{m}|{nz}|{sc}'
            plot_method(ax, t, z[k + '|mean'], m, label=(ax is axs[0, 0]))
            if m in (REC, 'RLS + det'):
                ax.fill_between(t, z[k + '|lo'], z[k + '|hi'], color=STYLE[m][0], alpha=0.12, lw=0)
        if not sc.startswith('S8'):
            ax.axvline(1.0, color=MUTED, ls=':', lw=0.8)
        ax.set_title(title, fontsize=8, color=INK, loc='left'); ax.set_ylim(top=0)
    for ax in axs[1]:
        ax.set_xlabel('time (s)')
    for ax in axs[:, 0]:
        ax.set_ylabel('NR (dB)')
    fig.legend(*axs[0, 0].get_legend_handles_labels(), loc='upper center', ncol=5, fontsize=6.5, bbox_to_anchor=(0.5, 1.0))
    fig.tight_layout(rect=(0, 0, 1, 0.92)); fig.savefig(OUT / (basename + '.pdf')); fig.savefig(OUT / (basename + '.png'), dpi=150); plt.close(fig)


def fig_learning():
    # Retain the highlighted baselines, both self-contained systems and the proposed method.
    methods = ['FD-FxNLMS', 'leaky FD-FxNLMS', 'FD-FxNLMS + restart',
               'RLS + det', 'RLS + CUSUM', 'CFTF + det', REC]
    _fig_learning(methods, 'learning')


def fig_learning_all():
    _fig_learning(ORDER_V2, 'learning_all')


def fig_lambda():
    import gap_check as G
    fig, ax = plt.subplots(figsize=(COL1, 2.2))
    bins = np.logspace(-1.3, 1.8, 60)
    for nz, c, lab in [('ar1', '#2a78d6', 'AR(1)'), ('harmonic', '#eb6834', 'harmonic')]:
        lam = np.concatenate([G.analyse(*G.xf_of(nz, sd))[0] for sd in (300, 301, 302)])
        ax.hist(lam, bins=bins, histtype='step', color=c, lw=1.4, label=f'{lab} (3 seeds)', density=True)
    ax.axvline(0.5, color=INK, ls='--', lw=0.9); ax.text(0.47, ax.get_ylim()[1] * 0.85, r'$\lambda=1/2$', fontsize=7, color=INK, ha='right')
    ax.set_xscale('log'); ax.set_xlabel(r'eigenvalue $\lambda_i$ of $\mathbf{K}\mathbf{R}$'); ax.set_ylabel('density')
    ax.legend(fontsize=7); fig.tight_layout(); fig.savefig(OUT / 'lambda.pdf'); fig.savefig(OUT / 'lambda.png', dpi=150); plt.close(fig)


def _logbin(y, nb=28):
    """Mean of a per-hop excess in log-spaced hop bins (linear mean, then dB): the per-hop ensemble excess is a
    noisy difference of two powers and can be <= 0 in single hops."""
    n = len(y); edges = np.unique(np.round(np.logspace(0, np.log10(n), nb)).astype(int)); edges[0] = 0
    c = np.array([(a + b) / 2 for a, b in zip(edges[:-1], edges[1:])]); v = np.array([np.mean(y[a:b]) for a, b in zip(edges[:-1], edges[1:])])
    return c, 10 * np.log10(np.maximum(v, 1e-12))


def fig_excess():
    g = np.load(ROOT / 'results/gap_check2/curves.npz')
    w3 = ROOT / 'results/gap_check3/curves.npz'; g3 = np.load(w3) if w3.exists() else None
    fig, axs = plt.subplots(1, 2, figsize=(COL2, 2.4), sharey=True)
    H, fs = 128, 8000
    names = [('exact LS (RLS lam 1)', 'exact growing-window LS', '#6f6e69', '-', 1.2),
             ('FD-FxNLMS mu 0.2', r'FD-FxNLMS $\mu=0.2$', '#eb6834', '-', 1.0),
             ('FD-FxNLMS mu 0.5', r'FD-FxNLMS $\mu=0.5$', '#eda100', '-', 1.0),
             ('E-PCG (main)', N.PCG_WLS, '#1a1a19', '-', 2.0)]   # curve key: archived record label
    for ax, nz, title in zip(axs, ['ar1', 'harmonic'], ['(a) AR(1)', '(b) harmonic']):
        for key, lab, c, ls, lw in names:
            hb, yd = _logbin(g[f'{nz}|{key}'])
            ax.plot((hb + 1) * H / fs, yd, color=c, ls=ls, lw=lw, label=lab)
        if g3 is not None and f'{nz}|offline window LS' in g3:
            hb, yd = _logbin(g3[f'{nz}|offline window LS'])
            keep = hb >= 48                                 # window full (before: identical to growing LS, ill-posed early hops)
            ax.plot((hb[keep] + 1) * H / fs, yd[keep], color='#2a78d6', ls='--', lw=1.2, label='exact LS, same 48-hop window')
        ax.set_xscale('log'); ax.set_xlabel('time (s)'); ax.set_title(title, fontsize=8, loc='left', color=INK)
    axs[0].set_ylabel('excess over oracle floor (dB, rel.)'); axs[0].legend(fontsize=6.5)
    fig.tight_layout(); fig.savefig(OUT / 'excess.pdf'); fig.savefig(OUT / 'excess.png', dpi=150); plt.close(fig)


def _table(path, header_start):
    rows, on = [], False
    for line in Path(path).read_text().splitlines():
        if line.startswith(header_start):
            on = True; continue
        if on:
            if not line.startswith('|'):
                if rows:
                    break
                continue
            if line.startswith('|---'):
                continue
            rows.append([c.strip() for c in line.strip('|').split('|')])
    return rows


def fig_cost():
    rows = _table(ROOT / 'results/extra_eval/summary.md', '| method | M | cost S8 / S2')
    from ffanc_norm import cost as C
    fig, axs = plt.subplots(1, 2, figsize=(COL2, 2.6))
    for ax, nz, title in zip(axs, ['ar1', 'harmonic'], ['(a) AR(1)', '(b) harmonic']):
        for m in ORDER:
            r = [x for x in rows if x[0] == m and x[3] == nz]
            if not r:
                continue
            xs = [float(x[2].split('/')[1]) for x in r]; ys = [float(x[7]) for x in r]   # S2 cost, S2 A1
            c, ls, mk, lw = STYLE[m]
            ax.plot(xs, ys, color=c, ls=ls, lw=lw, marker=mk or 'o', ms=4, label=N.display_label(m))
            for x_, y_, x in zip(xs, ys, r):
                ax.annotate(x[1], (x_, y_), fontsize=5.5, color=MUTED, xytext=(2, 2), textcoords='offset points')
        rl = [x for x in rows if x[0] == 'RLS' and x[3] == nz]
        ax.plot([C.sftf(int(x[1]), 128) / 128 for x in rl], [float(x[7]) for x in rl], color='#e87ba4', ls=':', lw=1.0,
                marker='x', ms=4, label='SFTF (cost; output = RLS)')
        # (REVISION_RULE_2 section 6) RLS + det at M = 512 (evaluation v2b, S2 median A1) at the RLS cost, and the same output
        # at the SFTF cost as an analytic point ('SFTF + det': not implemented; output = RLS + det where SFTF is stable)
        import json as _j
        a1 = np.median([_j.loads(l)['A1'] for l in (ROOT / 'results/final_eval_v2e/metrics.jsonl').read_text().splitlines()
                        if '"RLS + det"' in l and f'"{nz}"' in l and '"S2 src 30cm"' in l])
        c512 = [float(x[2].split('/')[1]) for x in rl if x[1] == '512'][0]
        ax.plot([c512], [a1], ls='none', color='#e87ba4', marker='*', ms=7, label='RLS + det (M = 512)')
        a1s = np.median([_j.loads(l)['A1'] for l in (ROOT / 'results/final_eval_v2e/metrics.jsonl').read_text().splitlines()
                         if '"SFTF + det"' in l and f'"{nz}"' in l and '"S2 src 30cm"' in l])
        ax.plot([C.sftf(512, 128) / 128], [a1s], ls='none', color='#6f6e69', marker='*', ms=7, mfc='none',
                label='SFTF + det (measured A1, analytic cost)')
        ax.set_xscale('log'); ax.set_xlabel('adaptation cost (flops / sample)'); ax.set_title(title, fontsize=8, loc='left', color=INK)
    axs[0].set_ylabel('A1 after 30 cm source move (dB)\n(up = better)'); axs[0].invert_yaxis(); axs[1].invert_yaxis()
    fig.legend(*axs[0].get_legend_handles_labels(), loc='lower center', ncol=5, fontsize=6.5, bbox_to_anchor=(0.5, 0.0))
    fig.tight_layout(rect=(0, 0.17, 1, 1)); fig.savefig(OUT / 'cost.pdf'); fig.savefig(OUT / 'cost.png', dpi=150); plt.close(fig)


def fig_shat():
    nm = [-30, -20, -15, -10]
    fig, axs = plt.subplots(1, 2, figsize=(COL2, 2.4), sharey=True)
    for ax, nz, title in zip(axs, ['ar1', 'harmonic'], ['(a) AR(1)', '(b) harmonic']):
        rows = _table(ROOT / 'results/extra_eval/summary.md', f'### noise = {nz}: failures')
        for m in ORDER:
            r = [x for x in rows if x[0] == m]
            if not r:
                continue
            cells = r[0][5:9]                                   # S1 at -30 / -20 / -15 / -10 dB
            fails = [int(c.split('/')[0]) for c in cells]
            c, ls, mk, lw = STYLE[m]
            ax.plot(nm, fails, color=c, ls=ls, lw=lw, marker=mk or 'o', ms=4, label=N.display_label(m))
        ax.set_xlabel(r'$\hat S$ NMSE (dB)'); ax.set_title(title + ', source move 10 cm', fontsize=8, loc='left', color=INK)
        ax.set_xticks(nm)
    axs[0].set_ylabel('failed runs (of 40)'); axs[1].legend(fontsize=6)
    fig.tight_layout(); fig.savefig(OUT / 'shat.pdf'); fig.savefig(OUT / 'shat.png', dpi=150); plt.close(fig)


if __name__ == '__main__':
    which = sys.argv[1:] or ['learning', 'excess', 'cost', 'shat', 'lambda']
    for w in which:
        globals()[f'fig_{w}'](); print('ok', w, flush=True)
