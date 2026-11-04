"""Audit CG window membership without changing the archived diagnostic's arithmetic.

The original module is loaded from its AST with only its output-directory creation
and hook installation removed. Its unmodified main() and _probe() do all numerical
work. This is the original 30 tuning-seed diagnostics, not a final evaluation.
"""
import ast
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import types

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'experiments/cg_ratio.py'
ARCHIVE = ROOT / 'results/cg_ratio'
OUT = ROOT / 'results/cg_ratio_window'


def compare_ratios(actual, expected, atol=1e-12):
    """Require identical membership/order and absolute error <= atol, with no rtol."""
    checks = {}
    if actual.keys() != expected.keys():
        return False, {'error': 'cell keys differ'}
    for key in expected:
        a, b = np.asarray(actual[key]), np.asarray(expected[key])
        same_shape = a.shape == b.shape
        error = float(np.max(np.abs(a - b))) if same_shape and a.size else None
        passed = bool(same_shape and error is not None and np.isfinite(a).all() and error <= atol)
        checks[key] = {'count': len(a), 'expected_count': len(b), 'bit_equal':
                       bool(same_shape and a.tobytes() == b.tobytes()),
                       'max_abs_error': error, 'passed': passed}
    return all(v['passed'] for v in checks.values()), checks


def load_original(out):
    tree = ast.parse(SOURCE.read_text(), filename=str(SOURCE))
    kept = []
    for node in tree.body:
        if isinstance(node, ast.Assign) and any(
                isinstance(t, ast.Name) and t.id == 'OUT' or
                isinstance(t, ast.Attribute) and t.attr == '_finish_hop'
                for t in node.targets):
            continue
        if isinstance(node, ast.Expr) and isinstance(node.value, ast.Call):
            f = node.value.func
            if isinstance(f, ast.Attribute) and isinstance(f.value, ast.Name) and f.value.id == 'OUT':
                continue
        kept.append(node)
    module = types.ModuleType('cg_ratio_archived_calculation')
    module.__file__ = str(SOURCE)
    module.OUT = out
    exec(compile(ast.Module(body=kept, type_ignores=[]), str(SOURCE), 'exec'), module.__dict__)
    return module


def full_plain(row):
    return row['legacy_selected'] and row['full_window'] and not row['weighted_solve_called']


def stats(values):
    return {'n': len(values), 'median': float(np.median(values)),
            'q90': float(np.quantile(values, .9)), 'max': float(np.max(values))}


def report_full_window(rows, reproduction):
    groups = {}
    for row in rows:
        if row['legacy_selected']:
            groups.setdefault(f"{row['noise']}|{row['cell']}", []).append(row)
    text = ['# CG window audit', '',
            f"Original raw ratios: {'PASS' if reproduction['passed'] else 'FAIL'}; "
            f"summary byte equality: {reproduction['summary_byte_equal']}.", '',
            'Full window means n >= L_hops × H (the configured window capacity), '
            'with an actual plain solve. The legacy ratio selection only requires n >= 2M. '
            'All-hop membership and event states are in hops.jsonl.', '',
            '| noise | cell | legacy hops | full plain hops | median | q90 | maximum |',
            '|---|---|---:|---:|---:|---:|---:|']
    aggregate = {}
    for key, group in groups.items():
        selected = [r['ratio'] for r in group if full_plain(r)]
        s = stats(selected)
        aggregate[key] = {'legacy_hops': len(group), 'full_plain': s}
        noise, cell = key.split('|')
        text.append(f"| {noise} | {cell} | {len(group)} | {s['n']} | "
                    f"{s['median']:.9f} | {s['q90']:.9f} | {s['max']:.9f} |")
    source = (ROOT / 'paper/v2/sections/algorithm.tex').read_text()
    paragraph = source.split(r'\noindent Measured under')[1].split('the stopping rule')[0]
    # The first six dollar-delimited scalar values are the two ratio pairs and
    # the two eigenvalues. Eigenvalues are explicitly qualified in the prose.
    numbers = re.findall(r'\$([0-9.]+)\$', paragraph)
    lam_ar = re.search(r'lambda_\{\\min\}=([0-9.]+)', paragraph).group(1)
    claims = {'ar1': (numbers[0], numbers[1], lam_ar),
              'harmonic': (numbers[2], numbers[3], numbers[4])}
    text += ['', 'The following comparison pools hops over the three cells and five seeds '
             'for each noise (the paper does not specify the pooling convention).', '',
             '| noise | statistic | paper | legacy pooled | full plain pooled | paper rounding supported |',
             '|---|---|---:|---:|---:|---|']
    comparisons = {}
    for noise, (paper_med, paper_max, paper_lam) in claims.items():
        group = [r for r in rows if r['noise'] == noise and r['legacy_selected']]
        old = stats([r['ratio'] for r in group])
        new = stats([r['ratio'] for r in group if full_plain(r)])
        eigen = [r['lam_min'] for r in group if 'lam_min' in r]
        checks = {}
        for name, claim, a, b in [('median', paper_med, old['median'], new['median']),
                                   ('maximum', paper_max, old['max'], new['max']),
                                   ('lambda_min median', paper_lam, float(np.median(eigen)),
                                    float(np.median(eigen)))]:
            precision = len(claim.split('.')[1])
            supported = f'{b:.{precision}f}' == claim
            checks[name] = {'paper': claim, 'legacy': a, 'full_plain': b, 'supported': supported}
            text.append(f'| {noise} | {name} | {claim} | {a:.9f} | {b:.9f} | '
                        f"{'yes' if supported else 'no'} |")
        comparisons[noise] = checks
    text += ['', 'No implementation, evaluation setting, original result, or paper text was changed. '
             'The full-window calculation is a filter on the reproduced legacy measurements; '
             'no extra controller solves are introduced.', '']
    (OUT / 'summary.md').write_text('\n'.join(text))
    (OUT / 'full_window.json').write_text(json.dumps(
        {'cells': aggregate, 'paper_comparison': comparisons}, indent=2) + '\n')


def main():
    OUT.mkdir(exist_ok=False)
    original_hash = hashlib.sha256(SOURCE.read_bytes()).hexdigest()
    legacy = load_original(OUT)
    original_finish = legacy.E.EPCG._finish_hop
    original_weighted = legacy.E.EPCG._weighted_solve
    original_run = legacy.D.P.run
    rows, context, stack = [], {}, []
    # Original main() prints each cell, but this wrapper also identifies each
    # run without reconstructing or replacing the original configuration.
    def run(cfg, seed, method, params, seconds, change):
        import inspect
        caller = inspect.currentframe().f_back.f_locals
        context.clear()
        context.update(noise=caller['nz'], cell=caller['sc'], seed=int(seed))
        print(f"start {context}", flush=True)
        return original_run(cfg, seed, method, params, seconds, change)

    def weighted(self, *args, **kwargs):
        stack[-1]['weighted'] = True
        return original_weighted(self, *args, **kwargs)

    with (OUT / 'hops.jsonl').open('w') as stream:
        def probe(self, Cm, Gw):
            marker = {'weighted': False}
            before = self.ev is not None
            count = len(legacy.LOG)
            stack.append(marker)
            try:
                w = legacy._probe(self, Cm, Gw)
            finally:
                stack.pop()
            c = self.cfg
            n = int(self.stop - self.t0)
            row = dict(context, stop=int(self.stop), t0=int(self.t0), n=n,
                       M=int(c.M), H=int(c.H), L_hops=int(c.L_hops),
                       full_window_samples=int(c.L_hops * c.H),
                       full_window=bool(n >= c.L_hops * c.H),
                       event_before=before, event_after=self.ev is not None,
                       weighted_solve_called=marker['weighted'], skip_solve=bool(self.skip_solve),
                       sampled_hop=bool((self.stop // c.H) % legacy.EVERY == 0),
                       legacy_selected=len(legacy.LOG) > count)
            if row['legacy_selected']:
                row.update(legacy.LOG[-1])
                row['ratio'] = row['opt'] / row['est']
            rows.append(row)
            stream.write(json.dumps(row) + '\n')
            return w
        legacy.E.EPCG._finish_hop = probe
        legacy.E.EPCG._weighted_solve = weighted
        legacy.D.P.run = run
        try:
            legacy.main()
        finally:
            legacy.E.EPCG._finish_hop = original_finish
            legacy.E.EPCG._weighted_solve = original_weighted
            legacy.D.P.run = original_run
    actual = json.loads((OUT / 'raw.json').read_text())
    expected = json.loads((ARCHIVE / 'raw.json').read_text())
    passed, checks = compare_ratios(actual, expected)
    summary_equal = (OUT / 'summary.md').read_bytes() == (ARCHIVE / 'summary.md').read_bytes()
    (OUT / 'legacy_summary.md').write_bytes((OUT / 'summary.md').read_bytes())
    reproduction = {'passed': passed, 'atol': 1e-12, 'rtol': 0.,
                    'summary_byte_equal': summary_equal, 'cells': checks,
                    'commit': subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip(),
                    'original_script_sha256': original_hash,
                    'numpy': np.__version__, 'RLS_FAST': os.environ.get('RLS_FAST'),
                    'blas_threads': os.environ.get('OPENBLAS_NUM_THREADS')}
    (OUT / 'reproduction.json').write_text(json.dumps(reproduction, indent=2) + '\n')
    if not passed:
        raise RuntimeError('Original CG ratios were not reproduced to 1e-12; stopping before full-window aggregation')
    assert hashlib.sha256(SOURCE.read_bytes()).hexdigest() == original_hash
    report_full_window(rows, reproduction)


if __name__ == '__main__':
    main()
