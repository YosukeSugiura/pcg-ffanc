"""Read-only compatibility checks for summaries of committed evaluation results.

Output/docs/test commits do not change the executed evaluation code. Within the
evaluation dependency graph, only the explicitly named summary functions may
change. Simulation, configuration, dependencies and data-path changes fail closed.
"""
import ast
from pathlib import Path
import re
import subprocess

SUMMARY_FUNCTIONS = {
    'experiments/final_eval.py': {'summary'},
    'experiments/measured_paths.py': {'write_provenance', 'annotate_summary'},
}
SUMMARY_MODULES = {'experiments/summary_provenance.py'}


def _git(root, *args):
    return subprocess.check_output(['git', *args], cwd=root, text=True, stderr=subprocess.DEVNULL).strip()


def _source(root, path, revision=None):
    if revision is None:
        p = Path(root) / path
        return p.read_text() if p.exists() else None
    try:
        return _git(root, 'show', f'{revision}:{path}')
    except subprocess.CalledProcessError:
        return None


def _dependencies(root, revision):
    pending = ['experiments/eval_v2.py', 'experiments/measured_paths.py']
    seen = set()
    while pending:
        path = pending.pop()
        if path in seen:
            continue
        seen.add(path)
        source = _source(root, path, revision)
        if source is None:
            continue
        for node in ast.walk(ast.parse(source)):
            modules = ([n.name for n in node.names] if isinstance(node, ast.Import)
                       else [node.module] if isinstance(node, ast.ImportFrom) and node.module else [])
            for module in modules:
                rel = module.replace('.', '/')
                for candidate in (f'experiments/{rel}.py', f'src/{rel}.py', f'src/{rel}/__init__.py'):
                    if candidate not in seen and _source(root, candidate, revision) is not None:
                        pending.append(candidate)
    return seen


def _without_summary(source, allowed):
    if source is None:
        return None
    tree = ast.parse(source)
    tree.body = [node for node in tree.body
                 if not (isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name in allowed)]
    return ast.dump(tree, include_attributes=False)


def check_summary_code(root, recorded_commit):
    if not re.fullmatch(r'[0-9a-fA-F]{40}', recorded_commit):
        raise ValueError('Invalid recorded implementation commit')
    _git(root, 'rev-parse', '--verify', f'{recorded_commit}^{{commit}}')
    relevant = _dependencies(root, recorded_commit) | _dependencies(root, None)
    changed = _git(root, 'diff', '--name-only', recorded_commit, '--').splitlines()
    forbidden = []
    for path in changed:
        is_input = (path.startswith(('src/', 'configs/')) or path in relevant
                    or path in ('pyproject.toml', 'requirements.txt', 'uv.lock', 'poetry.lock')
                    or path.startswith(('results/final_dev/', 'results/protocol_v2_sel/')))
        if not is_input or path in SUMMARY_MODULES:
            continue
        allowed = SUMMARY_FUNCTIONS.get(path, set())
        if not allowed or _without_summary(_source(root, path, recorded_commit), allowed) != _without_summary(_source(root, path), allowed):
            forbidden.append(path)
    if forbidden:
        raise ValueError(f'Non-summary evaluation changes since {recorded_commit}: {forbidden}')


def check_existing_metadata(root, recorded, current):
    old = dict(recorded)
    old_commit = old.pop('implementation_commit')
    new = dict(current)
    new.pop('implementation_commit')
    if old != new:
        raise ValueError('Existing provenance differs in inputs, rule, software or allocation')
    check_summary_code(root, old_commit)
