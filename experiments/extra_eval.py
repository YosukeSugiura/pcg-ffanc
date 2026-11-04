"""Step 6 (cost vs convergence) and Step 5 (S-model error) of the plan; rule docs/current/EXTRA_EVAL_RULE.md.

usage:
  python experiments/extra_eval.py reuse                       # copy the M = 512 records of results/final_eval (Step 6)
  RLS_FAST=1 SHARD=0/2 PART=_a python experiments/extra_eval.py run ; ... SHARD=1/2 PART=_b ...
  python experiments/extra_eval.py summary                     # results/extra_eval/{summary.md, fig_cost_*.png, fig_shat_*.png}
"""
import json, os, sys, time, zlib
from pathlib import Path
import numpy as np
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src')); sys.path.insert(0, str(ROOT / 'experiments'))
import final_eval as FE  # noqa: E402
from ffanc_norm import cost as COST  # noqa: E402
D = FE.D
OUT = ROOT / 'results' / 'extra_eval'; OUT.mkdir(parents=True, exist_ok=True)
SEEDS = FE.SEEDS; ALL = FE.ALL; PROP = FE.PROP; METH = FE.METH
MS = [256, 512, 1024]; COST_CELLS = ['S8 stationary', 'S2 src 30cm']
NMSE = [-30.0, -20.0, -15.0, -10.0]; SHAT_CELLS = ['S8 stationary', 'S1 src 10cm']
NOISES = ['ar1', 'harmonic']
ANALYTIC = {'FD-FxNLMS': COST.fd_fxnlms, 'leaky FD-FxNLMS': COST.leaky_fd_fxnlms, 'convex FD-FxNLMS': COST.convex_fd_fxnlms,
            'FDKF': COST.fdkf, 'RLS': COST.rls, 'VFF-RLS': COST.vff_rls}


def jobs():
    j = [('cost', m, M, None, nz, sc, sd) for m in ALL for M in MS if M != 512 for nz in NOISES for sc in COST_CELLS for sd in SEEDS]
    j += [('shat', m, 512, q, nz, sc, sd) for m in ALL for q in NMSE for nz in NOISES for sc in SHAT_CELLS for sd in SEEDS]
    return j


def key(r):
    return (r['part'], r['method'], r['M'], r['nmse'], r['noise'], r['scen'], r['seed'])


def one(part, m, M, q, nz, sc, sd):
    meth, prm = METH[m]
    cfg = dict(D.SCEN[sc], controller_length=M, fft_length=2 * M, **({} if nz == 'ar1' else {'noise_type': nz}),
               **({} if q is None else {'shat_nmse_db': q}))
    ch = not sc.startswith('S8'); t0 = time.time()
    r = D.P.run(cfg, sd, meth, dict(prm), FE.TT, D.CH if ch else None)
    tp = np.array(r['total_power']); up = np.array(r['uncontrolled_power'])
    return {'part': part, 'method': m, 'prm': prm, 'M': M, 'nmse': q, 'noise': nz, 'scen': sc, 'seed': sd,
            'flag_stable': bool(r['stable']), 'tp': tp.tolist(), 'up': up[:len(tp)].tolist(), 'hops_full': len(up),
            'wall_s': round(time.time() - t0, 2), 'flops_hop': float(np.mean(r['flop_hist'])) if r.get('flop_hist') else None}


def reuse():
    fn = OUT / 'runs_reuse512.jsonl'
    if fn.exists():
        print('exists', fn); return
    n = 0
    with fn.open('w') as fh:
        for f in sorted(FE.OUT.glob('runs*.jsonl')):
            for r in FE.read_jsonl(f)[0]:
                if r['scen'] in COST_CELLS and r.get('prm') == METH[r['method']][1]:
                    fh.write(json.dumps(dict(r, part='cost', M=512, nmse=None)) + '\n'); n += 1
    print(f'{n} M = 512 records reused -> {fn}')


def _load():
    by = {}; _load.dup = 0
    for f in sorted(OUT.glob('runs*.jsonl')):
        for r in FE.read_jsonl(f)[0]:
            if r.get('prm') == METH[r['method']][1]:
                _load.dup += key(r) in by
                by.setdefault(key(r), r)
    return by


def run():
    done = set(_load())
    si, sn = map(int, os.environ.get('SHARD', '0/1').split('/'))
    fn = OUT / f"runs{os.environ.get('PART', '')}.jsonl"
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


def _metrics(r, full_up):
    nh = int(FE.TT * int(D.SCEN[r['scen']]['sample_rate'])) // int(D.SCEN[r['scen']]['hop_length'])
    r = dict(r); r['_up_full'] = full_up[(r['noise'], r['scen'], r['seed'])]   # uncontrolled power: method independent
    return FE.metrics(r, nh)[0]


def _phase_frac(sc, sd, q, M):
    """(fraction of bins with |angle(S / S_hat)| > 90 deg (small-step FxLMS condition), fraction with
    |1 - S / S_hat| >= 1 (quasi-static per-bin condition of a virtual-residual LS-type update with step ~ 1; derived,
    not verified)) on the 2M-point grid for the S_hat of shat_nmse_db = q."""
    cfg = dict(D.SCEN[sc], controller_length=M, fft_length=2 * M)
    p, s, _, _ = D.P.ism_paths(cfg, sd)
    srng = np.random.default_rng(sd + 555)                       # same construction as prototype run()
    env = np.convolve(np.abs(s) + 1e-3 * np.max(np.abs(s)), np.ones(5) / 5, mode='same')
    delta = srng.standard_normal(len(s)) * env
    delta *= np.linalg.norm(s) * 10 ** (q / 20) / np.linalg.norm(delta)
    S = np.fft.rfft(s, 2 * M); Sh = np.fft.rfft(s + delta, 2 * M)
    rt = S / Sh
    return float(np.mean(np.abs(np.angle(rt)) > np.pi / 2)), float(np.mean(np.abs(1.0 - rt) >= 1.0))


def summary():
    by = _load()
    miss = [j for j in jobs() if j not in by]
    miss += [('cost', m, 512, None, nz, sc, sd) for m in ALL for nz in NOISES for sc in COST_CELLS for sd in SEEDS
             if ('cost', m, 512, None, nz, sc, sd) not in by]
    if miss:
        print('INCOMPLETE:', miss[:5], f'({len(miss)} missing)'); sys.exit(1)
    full_up = {}
    nh = int(FE.TT * int(D.SCEN['S8 stationary']['sample_rate'])) // int(D.SCEN['S8 stationary']['hop_length'])
    for r in by.values():
        if len(r['up']) == nh:
            full_up.setdefault((r['noise'], r['scen'], r['seed']), np.asarray(r['up'], float))
    for r in by.values():                       # uncontrolled power independent of method, M and S_hat
        u = full_up[(r['noise'], r['scen'], r['seed'])]
        assert np.array_equal(u[:len(r['up'])], np.asarray(r['up'], float)), (r['method'], r['M'], r['nmse'])
        r['tp'] = np.nan_to_num(np.asarray(r['tp'], float), nan=1e30, posinf=1e30).tolist()
    Mx = {k: _metrics(r, full_up) for k, r in by.items()}
    H = int(D.SCEN['S8 stationary']['hop_length'])
    med = lambda v: float(np.median(v))
    out = ['# Additional evaluations (rule docs/current/EXTRA_EVAL_RULE.md; evaluation seeds 480-519)', '',
           '## Step 6: cost vs convergence (median over 40 seeds; cost = adaptation flops per sample, common filtering excluded)',
           '| method | M | cost S8 / S2 (flops/sample) | noise | S8 A1 | S8 A2 | S8 tau_-12 (s) | S2 A1 | S2 A2 | S2 tau_-12 (s) | failures (S8 / S2) |',
           '|---|---|---|---|---|---|---|---|---|---|---|']
    pts = {}
    for m in ALL:
        for M in MS:
            if m in PROP:
                c8 = np.mean([by[k]['flops_hop'] for k in by if k[0] == 'cost' and k[1] == m and k[2] == M and k[5].startswith('S8')]) / H
                c2 = np.mean([by[k]['flops_hop'] for k in by if k[0] == 'cost' and k[1] == m and k[2] == M and not k[5].startswith('S8')]) / H
            else:
                c8 = c2 = ANALYTIC[m](M, H) / H
            for nz in NOISES:
                g = lambda sc, kk: [Mx[('cost', m, M, None, nz, sc, sd)][kk] for sd in SEEDS]
                row = (med(g('S8 stationary', 'A1')), med(g('S8 stationary', 'A2')), med(g('S8 stationary', 'tau12')),
                       med(g('S2 src 30cm', 'A1')), med(g('S2 src 30cm', 'A2')), med(g('S2 src 30cm', 'tau12')))
                f8 = sum(g('S8 stationary', 'fail')); f2 = sum(g('S2 src 30cm', 'fail'))
                out.append(f'| {m} | {M} | {c8:.0f} / {c2:.0f} | {nz} | ' + ' | '.join(f'{v:.2f}' for v in row) + f' | {f8} / {f2} |')
                pts[(m, M, nz)] = ((c8, c2), row)
    for M in MS:
        out.append(f'| SFTF (cost point; performance = RLS) | {M} | {COST.sftf(M, H) / H:.0f} | - | | | | | | |')
    out += ['', '| M | common filtering (flops/sample, all methods) |', '|---|---|']
    out += [f'| {M} | {COST.common_filtering(M, H, 256) / H:.0f} |' for M in MS]
    # Step 5
    out += ['', '## Step 5: S-model error (M = 512; median over 40 seeds; failures out of 40)']
    pf = {}
    for q in NMSE:
        v = np.array([_phase_frac('S1 src 10cm', sd, q, 512) for sd in SEEDS])
        pf[q] = v.mean(0)
    out += ['| NMSE (dB) | mean fraction of bins with angle(S/S_hat) > 90 deg | mean fraction with abs(1 - S/S_hat) >= 1 |', '|---|---|---|']
    out += [f'| {q:g} | {pf[q][0]:.4f} | {pf[q][1]:.4f} |' for q in NMSE]
    out += ['', '(the same delta direction is scaled across NMSE levels (seed + 555): nested, not independent realizations; '
            'S8 and S1 share S for a seed, so one geometry is shown)']
    for nz in NOISES:
        out += ['', f'### noise = {nz}: failures / median A2 (dB) / median A1 (dB)', '| method | ' +
                ' | '.join(f'{sc.split()[0]} {q:g} dB' for sc in SHAT_CELLS for q in NMSE) + ' |', '|---' * (1 + len(SHAT_CELLS) * len(NMSE)) + '|']
        for m in ALL:
            cells = []
            for sc in SHAT_CELLS:
                for q in NMSE:
                    v = [Mx[('shat', m, 512, q, nz, sc, sd)] for sd in SEEDS]
                    cells.append(f"{sum(x['fail'] for x in v)} / {med([x['A2'] for x in v]):.2f} / {med([x['A1'] for x in v]):.2f}")
            out.append(f'| {m} | ' + ' | '.join(cells) + ' |')
    # figures
    import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
    COL = {'FD-FxNLMS': '#E69F00', 'leaky FD-FxNLMS': '#56B4E9', 'convex FD-FxNLMS': '#009E73', 'RLS': '#999999',
           'VFF-RLS': '#D55E00', 'FDKF': '#CC79A7', 'E-PCG': '#000000', 'E-PCG bank': '#0072B2'}
    for nz in NOISES:
        fig, axs = plt.subplots(1, 2, figsize=(10, 4))
        for ax, (idx, ci, lab) in zip(axs, [(3, 1, 'S2 A1: NR first 0.5 s after the change (dB)'), (1, 0, 'S8 A2: stationary NR (dB)')]):
            for m in ALL:
                xs = [pts[(m, M, nz)][0][ci] for M in MS]; ys = [pts[(m, M, nz)][1][idx] for M in MS]
                ax.plot(xs, ys, '-o', color=COL[m], lw=2 if m in PROP else 1, label=m)
                for M, x_, y_ in zip(MS, xs, ys):
                    ax.annotate(str(M), (x_, y_), fontsize=6, xytext=(2, 2), textcoords='offset points')
            sf = [COST.sftf(M, H) / H for M in MS]; ys = [pts[('RLS', M, nz)][1][idx] for M in MS]
            ax.plot(sf, ys, ':', color='#999999', marker='x', label='SFTF (RLS output)')
            ax.set_xscale('log'); ax.set_xlabel('adaptation cost (flops / sample)'); ax.set_ylabel(lab); ax.grid(alpha=0.3)
        axs[0].legend(fontsize=6, ncol=2); fig.suptitle(f'cost vs convergence, {nz} (M = 256 / 512 / 1024)', fontsize=10)
        fig.tight_layout(); fig.savefig(OUT / f'fig_cost_{nz}.png', dpi=130); plt.close(fig)
        fig, axs = plt.subplots(1, 2, figsize=(10, 4))
        for ax, sc in zip(axs, SHAT_CELLS):
            for m in ALL:
                ys = [med([Mx[('shat', m, 512, q, nz, sc, sd)]['A2'] for sd in SEEDS]) for q in NMSE]
                ax.plot(NMSE, ys, '-o', color=COL[m], lw=2 if m in PROP else 1, label=m)
            ax.set_xlabel('S_hat NMSE (dB)'); ax.set_ylabel(f'{sc}: median A2 (dB)'); ax.grid(alpha=0.3)
        axs[0].legend(fontsize=6, ncol=2); fig.suptitle(f'robustness to the S-model error, {nz} (failed runs: 0 dB)', fontsize=10)
        fig.tight_layout(); fig.savefig(OUT / f'fig_shat_{nz}.png', dpi=130); plt.close(fig)
    out += ['', f'- records {len(by)}; duplicates {getattr(_load, "dup", 0)}',
            '- baselines: configurations selected at M = 512 (protocol_final_sel), used unchanged at M = 256 / 1024 (FD step sizes are '
            'normalized, RLS lambda = 0.9995 gives N_eff / M = 7.8 / 3.9 / 2.0, E-PCG window L = 48 hops = 24 M / 12 M / 6 M; M also '
            'changes the controller expressiveness)',
            '- cost: E-PCG = measured implementation average (detection, rebuilds included); baselines = idealized analytic counts; '
            'the filtering common to the methods is excluded (S_hat * y only for the virtual-residual methods)',
            '- error structure: FD-FxNLMS and leaky adapt on the measured error e (FxLMS); convex, FDKF, RLS, VFF-RLS and E-PCG on '
            'the virtual residual d_hat + x_f * w (modified FxLMS): the S-model-error comparison reflects algorithm and structure jointly',
            '- VFF-RLS uses the true disturbance power for sigma_0 (oracle, as implemented)']
    (OUT / 'summary.md').write_text('\n'.join(out) + '\n'); print('\n'.join(out[:6])); print('written', OUT / 'summary.md')


if __name__ == '__main__':
    {'reuse': reuse, 'run': run, 'summary': summary}[sys.argv[1]]()
