import sys
from pathlib import Path
import numpy as np
import pytest
sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'experiments'))
from ringbuf_isf_profile import profile_updates, comparison, run_pair


def test_nested_update_count_and_scoped_isf_restoration():
    class Distribution:
        def isf(self, x): return x+1
    d = Distribution()
    class Inner:
        def update(self): return d.isf(2)
    class Outer:
        def update(self): return Inner().update()
    initial_inner, initial_outer = Inner.update, Outer.update
    with profile_updates((Inner, Outer), {'test': d}) as state:
        assert d.isf(3) == 4
        assert Outer().update() == 3
        assert state['updates'] == 1 and state['isf']['test']['calls'] == 1
        assert state['update_ns'] >= state['isf']['test']['ns']
    assert Inner.update is initial_inner and Outer.update is initial_outer
    assert 'isf' not in d.__dict__


def test_restore_on_error():
    class C:
        def update(self): raise RuntimeError('boom')
    class D:
        def isf(self, x): return x
    d = D(); initial = C.update
    with pytest.raises(RuntimeError):
        with profile_updates((C,), {'test': d}): C().update()
    assert C.update is initial and 'isf' not in d.__dict__


def test_byte_comparison_of_error_and_events():
    a = {'e': np.array([0., -0.]), 'reset_hops': [0], 'loc_hist': [10], 'n_resets': 1, 'events_total': 1}
    b = dict(a, e=np.array([0., 0.]))
    assert not comparison(a,b)['raw_error_equal']
    assert comparison(a,a)['all_fields_equal']
    assert not comparison(a,dict(a, loc_hist=[11]))['event_fields']['loc_hist']['equal']


def test_paired_run_restores_signal_setting():
    class C:
        def update(self): return 1
    class D:
        def isf(self, x): return x
    class Protocol:
        RETURN_SIGNALS = False
        def run(self, *args):
            assert self.RETURN_SIGNALS
            C().update()
            return {'e': np.zeros(3), 'reset_hops': [], 'loc_hist': [], 'n_resets': 0,
                    'events_total': 0, 'stable': True, 'total_power': [1.]}
    p = Protocol()
    r = run_pair(p, (C,), {'d': D()}, {}, 300, {}, 'S8 stationary')
    assert r['comparison']['all_fields_equal'] and r['updates'] == 1
    assert not p.RETURN_SIGNALS
