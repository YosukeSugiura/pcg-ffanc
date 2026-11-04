from pathlib import Path
import subprocess
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'experiments'))
from summary_provenance import check_existing_metadata, check_summary_code


def git(root, *args):
    return subprocess.check_output(['git', *args], cwd=root, text=True).strip()


@pytest.fixture
def repository(tmp_path):
    git(tmp_path, 'init', '-q')
    git(tmp_path, 'config', 'user.name', 'Test')
    git(tmp_path, 'config', 'user.email', 'test@example.invalid')
    for name, text in {
        'experiments/eval_v2.py': 'import simulator\n',
        'experiments/simulator.py': 'def run():\n    return 1\n',
        'experiments/measured_paths.py': 'def paths():\n    return 1\ndef write_provenance():\n    return 1\n',
        'experiments/final_eval.py': 'def metrics():\n    return 1\ndef summary():\n    return 1\n',
    }.items():
        p = tmp_path / name; p.parent.mkdir(parents=True, exist_ok=True); p.write_text(text)
    # Make final_eval part of the executed dependency graph.
    (tmp_path / 'experiments/eval_v2.py').write_text('import simulator\nimport final_eval\n')
    git(tmp_path, 'add', '.')
    git(tmp_path, 'commit', '-qm', 'Baseline')
    return tmp_path, git(tmp_path, 'rev-parse', 'HEAD')


def test_results_commit_and_summary_only_edits_allowed(repository):
    root, base = repository
    (root / 'results').mkdir(); (root / 'results/summary.md').write_text('results\n')
    git(root, 'add', '.'); git(root, 'commit', '-qm', 'Results')
    check_summary_code(root, base)
    p = root / 'experiments/final_eval.py'
    p.write_text(p.read_text().replace('def summary():\n    return 1', 'def summary():\n    return 2'))
    check_summary_code(root, base)
    old = {'implementation_commit': base, 'inputs': 'unchanged'}
    current = dict(old, implementation_commit=git(root, 'rev-parse', 'HEAD'))
    check_existing_metadata(root, old, current)
    assert old['implementation_commit'] == base  # no metadata rewrite


@pytest.mark.parametrize('path', ['experiments/simulator.py', 'experiments/final_eval.py', 'experiments/measured_paths.py'])
def test_simulation_metrics_or_paths_edits_rejected(repository, path):
    root, base = repository
    p = root / path
    p.write_text(p.read_text().replace('return 1', 'return 2', 1))
    with pytest.raises(ValueError, match='Non-summary'):
        check_summary_code(root, base)


def test_input_metadata_changes_and_invalid_commit_rejected(repository):
    root, base = repository
    with pytest.raises(ValueError, match='inputs'):
        check_existing_metadata(root, {'implementation_commit': base, 'seed': 480}, {'implementation_commit': base, 'seed': 481})
    with pytest.raises(ValueError, match='Invalid recorded'):
        check_summary_code(root, '--help')
