from pathlib import Path
import sys

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'experiments'))
from diag_meas_bound import symmetry, wiener, controller_power, band_sums


def test_causal_wiener_cancels_representable_path():
    weights = symmetry(8000) / 8000
    p = np.array([0., .3, -.2])
    s = np.array([1.])
    w, residual = wiener(p, s, weights, length=4)
    assert np.allclose(w, [0., -.3, .2, 0.], atol=1e-14)
    assert controller_power(p, s, w, weights) < 1e-26
    assert residual < 1e-12


def test_controller_length_limit_and_model_mismatch_are_not_hidden():
    weights = symmetry(8000) / 8000
    p = np.array([0., 0., 0., 0., 1.])
    w, _ = wiener(p, np.array([1.]), weights, length=4)
    assert abs(controller_power(p, np.array([1.]), w, weights) - 1.) < 1e-12
    w, _ = wiener(np.array([1.]), np.array([1.]), weights, length=4)
    assert abs(controller_power(np.array([1.]), np.array([-1.]), w, weights) - 4.) < 1e-12


def test_band_edges_partition_including_nyquist():
    frequencies = np.array([0., 99., 100., 299., 300., 999., 1000., 4000.])
    assert list(band_sums(np.ones(8), frequencies).values()) == [2., 2., 2., 2.]
