"""Final evaluation on the evaluation seeds (rule: docs/current/FINAL_EVAL_RULE.md, fixed before the runs).

usage:
  RLS_FAST=1 SHARD=0/2 PART=_a python experiments/final_eval.py run ; ... SHARD=1/2 PART=_b ...
  python experiments/final_eval.py summary      # results/final_eval/{summary.md, metrics.jsonl, curves.npz, fig_*.png}
  python experiments/final_eval.py selftest     # one run per method (S2 harmonic, seed 480) -> results/final_eval/selftest.txt
"""
import json, math, os, sys, time, zlib
from fractions import Fraction
from pathlib import Path
import numpy as np
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src')); sys.path.insert(0, str(ROOT / 'experiments'))
import strict_div as SD  # noqa: E402
from ffanc_norm import naming as N  # noqa: E402
D = SD.D
OUT = ROOT / 'results' / 'final_eval'; OUT.mkdir(parents=True, exist_ok=True)
SEEDS = list(range(480, 520))
CELLS = ['S8 stationary', 'S1 src 10cm', 'S2 src 30cm', 'S5 src 30cm cont', 'S7 rd abrupt',
         'R1 rig 10cm', 'R2 rig 30cm', 'R3 rig 30cm cont']
CONT = {'S5 src 30cm cont', 'R3 rig 30cm cont'}
NOISES = ['ar1', 'harmonic']
COMBOS = [(nz, sc) for nz in NOISES for sc in CELLS if (nz, sc) != ('harmonic', 'S7 rd abrupt')]   # 15
M = 512; TT = 5.0; T_CAP = 4.0; WIN = 16; LEVELS = (-9.0, -12.0)
THR_A1 = 1.0; THR_A2 = 0.5; NBOOT = 1000

_sel = json.loads((ROOT / 'results/protocol_final_sel/selected.json').read_text())
BASE = ['FD-FxNLMS', 'leaky FD-FxNLMS', 'convex FD-FxNLMS', 'RLS', 'VFF-RLS', 'FDKF']
METH = {m: (_sel['grids'][m][0], _sel['grids'][m][1][_sel['selected'][m]]) for m in BASE}
# 'E-PCG' and 'E-PCG bank' are the record labels of PCG-WLS and PCG-WLS (multi-window) in results/ (names before
# v1.1.0). They are kept so that runs resume from and compare with the archived records (see ffanc_norm.naming).
# The saved configurations carry the former method key 'E-PCG-F'; load_config maps it to 'PCG-WLS-F'.
for _lab, _f in (('E-PCG', 'final_config_core_main.json'), ('E-PCG bank', 'final_config_core_final.json')):
    _c = N.load_config(ROOT / 'results/final_dev' / _f)
    METH[_lab] = (_c['method'], _c['flags'])
PROP = ['E-PCG', 'E-PCG bank']
ALL = BASE + PROP


def jobs():
    keep = os.environ.get('METHODS'); keep = keep.split(';') if keep else ALL
    return [(m, nz, sc, sd) for m in ALL if m in keep for nz, sc in COMBOS for sd in SEEDS]


def one(m, nz, sc, sd):
    meth, prm = METH[m]
    cfg = dict(D.SCEN[sc], controller_length=M, fft_length=2 * M, **({} if nz == 'ar1' else {'noise_type': nz}))
    ch = not sc.startswith('S8')
    t0 = time.time()
    r = D.P.run(cfg, sd, meth, dict(prm), TT, D.CH if ch else None)
    tp = np.array(r['total_power']); up = np.array(r['uncontrolled_power'])
    return {'method': m, 'prm': prm, 'noise': nz, 'scen': sc, 'seed': sd, 'flag_stable': bool(r['stable']),
            'tp': tp.tolist(), 'up': up[:len(tp)].tolist(), 'hops_full': len(up), 'wall_s': round(time.time() - t0, 2),
            'flops_hop': float(np.mean(r['flop_hist'])) if r.get('flop_hist') else None}


EXTRA_UP = {}   # {(noise, scen, seed): full-length uncontrolled power} from a separate no-control run (eval_v2)


def read_jsonl(path):
    out, bad = [], 0
    for line in path.read_text().splitlines():
        try:
            out.append(json.loads(line))
        except json.JSONDecodeError:
            bad += 1
    return out, bad


def run():
    fn = OUT / f"runs{os.environ.get('PART', '')}.jsonl"
    done = set()
    for f in OUT.glob('runs*.jsonl'):
        recs, _ = read_jsonl(f)
        done |= {(r['method'], r['noise'], r['scen'], r['seed']) for r in recs
                 if r['method'] in METH and r.get('prm') == METH[r['method']][1]}   # (2026-10-30) methods outside METH skipped
    si, sn = map(int, os.environ.get('SHARD', '0/1').split('/'))
    torn = fn.exists() and fn.stat().st_size > 0 and not fn.read_bytes().endswith(b'\n')
    n = 0; t0 = time.time()
    with fn.open('a') as fh:
        if torn:
            fh.write('\n')
        for j in jobs():
            if zlib.crc32('|'.join(map(str, j)).encode()) % sn != si or j in done:
                continue
            fh.write(json.dumps(one(*j)) + '\n'); fh.flush(); n += 1
    print(f'{n} runs in {time.time() - t0:.0f} s -> {fn}', flush=True)


def hop_ceil(t, fs, H):
    return math.ceil(Fraction(str(t)) * fs / H)


def t_event(sc):
    return 0.0 if sc.startswith('S8') else (1.6 if sc in CONT else 1.0)


def metrics(r, nh):
    """Per-run metrics; also returns the (padded) power traces used for the curves."""
    sc = r['scen']; cfg = D.SCEN[sc]; H = int(cfg['hop_length']); fs = int(cfg['sample_rate'])
    s8 = sc.startswith('S8')
    fail = bool(SD.evaluate(r, 0.0)[0] if s8 else SD.evaluate_div(r)[0])
    tp = np.asarray(r['tp'], float); up = np.asarray(r['up'], float)
    if len(tp) < nh:                     # stopped by the simulator flag: complete with no control (NR 0 dB)
        up_full = r['_up_full']; tp = np.concatenate([tp, up_full[len(tp):]]); up = up_full.copy()
    out = {'method': r['method'], 'noise': r['noise'], 'scen': sc, 'seed': r['seed'], 'fail': int(fail)}
    nr = lambda a, b: float(10 * np.log10(tp[a:b].sum() / up[a:b].sum()))
    if s8:
        a1 = (0, 32); a2 = (nh - int(1.0 * fs) // H, nh)
    else:
        s = hop_ceil(1.0, fs, H); e = hop_ceil(1.6, fs, H) if sc in CONT else s + 32
        a1 = (s, e); a2 = (e, nh)
    if fail:
        out.update(A1=0.0, A2=0.0, **{f'tau{int(-L)}': T_CAP for L in LEVELS})
        return out, tp, up
    out['A1'] = nr(*a1); out['A2'] = nr(*a2)
    C = np.concatenate([[0.0], np.cumsum(tp)]); U = np.concatenate([[0.0], np.cumsum(up)])
    te = t_event(sc); s0 = hop_ceil(te, fs, H)
    for L in LEVELS:
        tau = T_CAP
        for k in range(s0 + WIN, nh + 1):
            if 10 * np.log10((C[k] - C[k - WIN]) / (U[k] - U[k - WIN])) <= L:
                tau = round(min(k * H / fs - te, T_CAP), 9); break
        out[f'tau{int(-L)}'] = tau
    return out, tp, up


def holm(p):
    p = np.asarray(p, float); p = np.where(np.isnan(p), 1.0, p); o = np.argsort(p); m = len(p)
    adj = np.empty(m); run_max = 0.0
    for i, k in enumerate(o):
        run_max = max(run_max, min(1.0, (m - i) * p[k])); adj[k] = run_max
    return adj


def pval(d):
    from scipy.stats import wilcoxon
    d = np.asarray(d, float)
    if d.size == 0 or np.all(d == 0):
        return 1.0
    return float(wilcoxon(d, zero_method='pratt').pvalue)


def label(dA1, pA1, dA2, pA2):
    w = (pA1 < 0.05 and dA1 <= -THR_A1) or (pA2 < 0.05 and dA2 <= -THR_A2)
    l = (pA1 < 0.05 and dA1 >= THR_A1) or (pA2 < 0.05 and dA2 >= THR_A2)
    return 'mixed' if (w and l) else 'win' if w else 'loss' if l else '-'


def summary():
    recs, bad = [], 0
    for f in sorted(OUT.glob('runs*.jsonl')):
        rr, nb = read_jsonl(f); recs += rr; bad += nb
    by = {}; stale = 0; dup = 0; dup_diff = 0
    for r in recs:
        if r['method'] not in METH or r.get('prm') != METH[r['method']][1]:
            stale += 1; continue
        k = (r['method'], r['noise'], r['scen'], r['seed'])
        if k in by:
            dup += 1; dup_diff += by[k]['tp'] != r['tp']
        else:
            by[k] = r
    if dup_diff:                                # (2026-10-30) differing duplicates: never pick one silently
        print(f'DUPLICATES WITH DIFFERENT RESULTS: {dup_diff}'); sys.exit(1)
    miss = [(m, nz, sc) for m in ALL for nz, sc in COMBOS if any((m, nz, sc, sd) not in by for sd in SEEDS)]
    if miss:
        print('INCOMPLETE:', miss[:8], f'({len(miss)} groups)'); sys.exit(1)
    fs0 = int(D.SCEN['S8 stationary']['sample_rate']); H0 = int(D.SCEN['S8 stationary']['hop_length'])
    nh = max(len(r['tp']) for r in by.values())
    assert nh == int(TT * fs0) // H0, f'unexpected run length {nh}'
    full_up = {}
    for r in by.values():
        if len(r['up']) == nh:
            full_up.setdefault((r['noise'], r['scen'], r['seed']), np.asarray(r['up'], float))
    filled = []
    for k, u in EXTRA_UP.items():               # (2026-10-30) only where no method ran to the end; default: empty
        if k not in full_up and len(u) == nh:
            full_up[k] = np.asarray(u, float); filled.append(k)
    for r in by.values():                       # the uncontrolled power must not depend on the method
        u = full_up.get((r['noise'], r['scen'], r['seed']))
        assert u is not None, f"no full-length run for {r['noise']}, {r['scen']}, {r['seed']}"
        assert np.array_equal(u[:len(r['up'])], np.asarray(r['up'], float)), f"uncontrolled power differs: {r['method']}"
        r['tp'] = np.nan_to_num(np.asarray(r['tp'], float), nan=1e30, posinf=1e30).tolist()
    Mx, P = {}, {}
    for k, r in by.items():
        r['_up_full'] = full_up[(r['noise'], r['scen'], r['seed'])]
        mt, tp, up = metrics(r, nh); Mx[k] = mt; P[k] = (tp, up)
    (OUT / 'metrics.jsonl').write_text(''.join(json.dumps(v) + '\n' for v in Mx.values()))
    rng = np.random.default_rng(0)
    out = ['# Final evaluation (evaluation seeds 480-519, M = 512, T = 5 s; rule docs/current/FINAL_EVAL_RULE.md)',
           'Values: median (Q1, Q3) over the 40 seeds; failed runs: A1 = A2 = 0 dB, tau = 4 s (censored).', '']
    # failures
    out += ['## Failures (runs out of 40)', '| method | ' + ' | '.join(f'{nz} {sc.split()[0]}' for nz, sc in COMBOS) + ' |',
            '|---' * (len(COMBOS) + 1) + '|']
    for m in ALL:
        out.append(f'| {m} | ' + ' | '.join(str(sum(Mx[(m, nz, sc, sd)]['fail'] for sd in SEEDS)) for nz, sc in COMBOS) + ' |')
    q = lambda v: f'{np.median(v):.2f} ({np.quantile(v, .25):.2f}, {np.quantile(v, .75):.2f})'
    for key in ('A1', 'A2', 'tau9', 'tau12'):
        for nz in NOISES:
            cs = [sc for n2, sc in COMBOS if n2 == nz]
            out += ['', f'## {key}, noise = {nz}', '| method | ' + ' | '.join(cs) + ' |', '|---' * (len(cs) + 1) + '|']
            for m in ALL:
                out.append(f'| {m} | ' + ' | '.join(q([Mx[(m, nz, sc, sd)][key] for sd in SEEDS]) for sc in cs) + ' |')
    # tests
    for p in PROP:
        rows = []
        for b in BASE:
            for nz, sc in COMBOS:
                rr = {}
                for key in ('A1', 'A2'):
                    d = np.array([Mx[(p, nz, sc, sd)][key] - Mx[(b, nz, sc, sd)][key] for sd in SEEDS])
                    rr[key] = (float(np.median(d)), pval(d))
                rows.append((b, nz, sc, rr))
        adj = iter(holm([x for *_, rr in rows for x in (rr['A1'][1], rr['A2'][1])]))
        out += ['', f'## {p} vs baselines (Wilcoxon pratt on seeds; Holm over {2 * len(rows)})',
                '| baseline | noise | cell | med dA1 | p_Holm A1 | med dA2 | p_Holm A2 | label |', '|---|---|---|---|---|---|---|---|']
        cnt = {'win': 0, 'loss': 0, 'mixed': 0, '-': 0}
        for b, nz, sc, rr in rows:
            pa1 = next(adj); pa2 = next(adj); lb = label(rr['A1'][0], pa1, rr['A2'][0], pa2); cnt[lb] += 1
            out.append(f'| {b} | {nz} | {sc} | {rr["A1"][0]:+.2f} | {pa1:.3g} | {rr["A2"][0]:+.2f} | {pa2:.3g} | {lb} |')
        out += ['', f'Counts ({p}): win {cnt["win"]}, loss {cnt["loss"]}, mixed {cnt["mixed"]}, none {cnt["-"]} (of {len(rows)})']
        print(f'{p} vs {len(BASE)} baselines ({len(rows)} pairs): {cnt}')
    rows = []
    for nz, sc in COMBOS:
        for key in ('A1', 'A2'):
            d = np.array([Mx[('E-PCG bank', nz, sc, sd)][key] - Mx[('E-PCG', nz, sc, sd)][key] for sd in SEEDS])
            rows.append((nz, sc, key, float(np.median(d)), pval(d)))
    adj = holm([r[4] for r in rows])
    out += ['', f'## E-PCG bank - E-PCG (main) (Holm over {len(rows)})', '| noise | cell | key | median d | p_Holm |', '|---|---|---|---|---|']
    out += [f'| {nz} | {sc} | {key} | {md:+.2f} | {pa:.3g} |' for (nz, sc, key, md, _), pa in zip(rows, adj)]
    # reach curves (fraction of runs with tau_L <= t)
    ts = [0.3, 0.5, 1.0, 2.0, 3.0, 4.0]          # tau >= 16 hops (0.256 s) by construction
    for L in LEVELS:
        out += ['', f'## Reach fraction at level {L:g} dB (tau <= t; t in {ts} s)', '| method | noise | cell | ' + ' | '.join(f't={t}' for t in ts) + ' |',
                '|---' * (len(ts) + 3) + '|']
        for m in ALL:
            for nz, sc in COMBOS:
                v = np.array([Mx[(m, nz, sc, sd)][f'tau{int(-L)}'] for sd in SEEDS]); cens = v >= T_CAP
                out.append(f'| {m} | {nz} | {sc} | ' + ' | '.join(f'{np.mean((v <= t) & ~cens):.2f}' for t in ts) + ' |')
    # cost (proposed: measured flop_hist / H)
    H = int(D.SCEN['S8 stationary']['hop_length'])
    out += ['', '## Cost of the proposed methods (mean flop_hist / H = flops per sample; S8 / change cells)', '| method | S8 | change cells |', '|---|---|---|']
    for p in PROP:
        f8 = [r['flops_hop'] for k, r in by.items() if k[0] == p and k[2].startswith('S8') and r.get('flops_hop')]
        fc = [r['flops_hop'] for k, r in by.items() if k[0] == p and not k[2].startswith('S8') and r.get('flops_hop')]
        out.append(f'| {p} | {np.mean(f8) / H:.0f} | {np.mean(fc) / H:.0f} |')
    # curves + bootstrap bands + figures
    arrs = {}
    import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
    COL = {'FD-FxNLMS': '#E69F00', 'leaky FD-FxNLMS': '#56B4E9', 'convex FD-FxNLMS': '#009E73', 'RLS': '#999999',
           'VFF-RLS': '#D55E00', 'FDKF': '#CC79A7', 'E-PCG': '#000000', 'E-PCG bank': '#0072B2'}
    MK = {'FD-FxNLMS': 'o', 'leaky FD-FxNLMS': 's', 'convex FD-FxNLMS': '^', 'RLS': 'v', 'VFF-RLS': 'P', 'FDKF': 'D'}
    fs = int(D.SCEN['S8 stationary']['sample_rate'])
    ends = np.arange(WIN, nh + 1); tt = ends * H / fs
    for nz, sc in COMBOS:
        fig, ax = plt.subplots(figsize=(7.5, 4.2))
        for m in ALL:
            TP = np.array([P[(m, nz, sc, sd)][0] for sd in SEEDS]); UP = np.array([P[(m, nz, sc, sd)][1] for sd in SEEDS])
            def curve(idx):
                c = np.concatenate([[0.0], np.cumsum(TP[idx].sum(0))]); u = np.concatenate([[0.0], np.cumsum(UP[idx].sum(0))])
                return 10 * np.log10((c[ends] - c[ends - WIN]) / (u[ends] - u[ends - WIN]))
            mean = curve(np.arange(len(SEEDS)))
            boot = np.array([curve(rng.integers(0, len(SEEDS), len(SEEDS))) for _ in range(NBOOT)])
            lo, hi = np.quantile(boot, [0.025, 0.975], axis=0)
            key = f'{m}|{nz}|{sc}'; arrs[key + '|mean'] = mean; arrs[key + '|lo'] = lo; arrs[key + '|hi'] = hi
            prop = m in PROP
            ax.plot(tt, mean, color=COL.get(m, '#555555'), lw=2.2 if prop else 1.1, ls='--' if m == 'E-PCG bank' else '-',
                    marker=None if prop else MK.get(m, 'x'), markevery=40, ms=4, label=m, zorder=5 if m == 'E-PCG' else 3)
            ax.fill_between(tt, lo, hi, color=COL.get(m, '#555555'), alpha=0.12 if prop else 0.06, lw=0)
        if not sc.startswith('S8'):
            ax.axvline(1.0, color='#555555', ls='--', lw=0.9)
            if sc in CONT:
                ax.axvline(1.6, color='#555555', ls='--', lw=0.9)
        ax.set_xlabel('time (s), window end'); ax.set_ylabel('ensemble-mean NR (dB)')
        ax.set_title(f'{sc}, {nz} (40 evaluation seeds, 95 % bootstrap band)', fontsize=10)
        ax.grid(alpha=0.3); ax.legend(fontsize=7, ncol=2)
        fig.tight_layout(); fig.savefig(OUT / f"fig_{sc.split()[0]}_{nz}.png", dpi=130); plt.close(fig)
    arrs['time_s'] = tt
    # reach curves on the hop grid (fraction of runs with tau_L <= t; censored runs count as not reached)
    tg = np.round(np.arange(0, int(T_CAP * fs / H) + 1) * H / fs, 9); arrs['reach_t'] = tg
    for L in LEVELS:
        for nz, sc in COMBOS:
            fig, ax = plt.subplots(figsize=(6.0, 3.6))
            for m in ALL:
                v = np.array([Mx[(m, nz, sc, sd)][f'tau{int(-L)}'] for sd in SEEDS]); ok = v < T_CAP
                frac = np.array([np.mean(ok & (v <= t + 1e-9)) for t in tg]); arrs[f'reach|{int(-L)}|{m}|{nz}|{sc}'] = frac
                ax.step(tg, frac, where='post', color=COL.get(m, '#555555'), lw=2.0 if m in PROP else 1.0,
                        ls='--' if m == 'E-PCG bank' else '-', label=m)
            ax.set_xlabel('time after the change (s)' if not sc.startswith('S8') else 'time (s)')
            ax.set_ylabel(f'fraction of runs at <= {L:g} dB'); ax.set_ylim(-0.02, 1.02); ax.grid(alpha=0.3)
            ax.set_title(f'reach {L:g} dB: {sc}, {nz}', fontsize=10); ax.legend(fontsize=7, ncol=2)
            fig.tight_layout(); fig.savefig(OUT / f"reach{int(-L)}_{sc.split()[0]}_{nz}.png", dpi=120); plt.close(fig)
    np.savez(OUT / 'curves.npz', **arrs)
    out += ['', '## Diagnostics', f'- records {len(by)}; unparsable {bad}; stale {stale}; duplicates {dup} (differing {dup_diff})',
            '- win / loss: each metric with its own Holm-adjusted p (A1 with p_A1, A2 with p_A2), thresholds 1 dB (A1) / 0.5 dB (A2)',
            '- curves are ensemble means of the seed-summed powers: one failed run can dominate a curve (read with the failure table)',
            '- cost of the baselines: analytic counts in the cost table (Step 6), not measured here',
            f'- runs stopped early (completed with no control): {sum(len(r["tp"]) < nh for r in by.values())}']
    if filled:
        out.append(f'- uncontrolled power after the stop taken from a no-control run (every method stopped early): {filled}')
    (OUT / 'summary.md').write_text('\n'.join(out) + '\n')
    print(f'files: {OUT}/summary.md, metrics.jsonl, curves.npz, fig_*.png')


def selftest():
    lines = []
    for m in ALL:
        r = one(m, 'harmonic', 'S2 src 30cm', 480); nh = len(r['up'])
        r['_up_full'] = np.asarray(r['up'], float)
        mt, *_ = metrics(r, nh)
        lines.append(f"{m}: wall {r['wall_s']} s, {mt}")
        print(lines[-1], flush=True)
    (OUT / 'selftest.txt').write_text('\n'.join(lines) + '\n')


if __name__ == '__main__':
    {'run': run, 'summary': summary, 'selftest': selftest}[sys.argv[1]]()
