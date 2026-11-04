from pathlib import Path
import sys
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'experiments'))
from diag_meas_onset import measure


def test_delayed_direct_sound_is_outside_secondary_window():
    h = np.zeros(32768); h[5120] = 1.; h[5118] = .11; h[200] = .09
    r = measure(h, np.array([1., 0., 0.]), np.zeros(3))
    assert r['peak_sample'] == 5120 and r['minus20db_first_exceed_sample'] == 5118
    assert r['peak_ms'] == 5120 / 48
    assert np.isclose(r['geometric_propagation_ms'], 1000 / 343)
    assert np.isclose(r['estimated_system_delay_ms_peak_minus_geometry'], 5120 / 48 - 1000 / 343)
    assert not r['retention']['S']['minus20db_onset_inside_raw_window']
    assert r['retention']['S']['pipeline_8k_retained_energy_ratio'] < .01
    assert r['retention']['P']['raw_retained_energy_ratio'] == 1.


def test_inside_window_and_strict_threshold():
    h = np.zeros(32768); h[1000] = 1.; h[999] = .1
    r = measure(h, np.ones(3), np.ones(3))
    assert r['minus20db_first_exceed_sample'] == 1000
    assert r['retention']['S']['peak_inside_raw_window']
    assert np.isclose(r['retention']['S']['pipeline_8k_retained_energy_ratio'], 1.)
