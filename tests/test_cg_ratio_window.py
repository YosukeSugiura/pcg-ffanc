"""Membership and reproduction gates for the window audit."""
import importlib.util
from pathlib import Path


spec = importlib.util.spec_from_file_location(
    'cg_ratio_window', Path(__file__).parents[1] / 'experiments/cg_ratio_window.py')
audit = importlib.util.module_from_spec(spec)
spec.loader.exec_module(audit)


def test_reproduction_checks_order_shape_and_absolute_tolerance():
    assert audit.compare_ratios({'x': [0.03, 0.1]}, {'x': [0.03 + 5e-13, 0.1]})[0]
    assert not audit.compare_ratios({'x': [0.03, 0.1]}, {'x': [0.1, 0.03]})[0]
    assert not audit.compare_ratios({'x': [0.03]}, {'x': [0.03, 0.1]})[0]
    assert not audit.compare_ratios({'x': [float('nan')]}, {'x': [0.03]})[0]
    assert not audit.compare_ratios({'x': [1e6 + 1e-6]}, {'x': [1e6]})[0]


def test_full_window_requires_original_eligibility_and_actual_plain_solve():
    row = dict(legacy_selected=True, full_window=True, weighted_solve_called=False)
    assert audit.full_plain(row)
    for key, value in [('legacy_selected', False), ('full_window', False),
                       ('weighted_solve_called', True)]:
        assert not audit.full_plain(dict(row, **{key: value}))


def test_load_does_not_install_hook_or_create_output(tmp_path):
    module = audit.load_original(tmp_path / 'not-created')
    assert module.E.PcgWls._finish_hop is module._orig
    assert module.OUT == tmp_path / 'not-created'
    assert not module.OUT.exists()
    assert module.M == 512 and module.SEEDS == list(range(300, 305))
