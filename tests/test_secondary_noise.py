import numpy as np

from ffanc_norm.simulation import secondary_noise_for_snr


def test_secondary_noise_matches_requested_snr():
    rng = np.random.default_rng(123)
    d = rng.standard_normal(200000)
    v = secondary_noise_for_snr(d, 20.0, np.random.default_rng(456))
    snr = 10.0 * np.log10(np.mean(d**2) / np.mean(v**2))
    assert abs(snr - 20.0) < 1e-10


def test_none_secondary_noise_is_zero():
    d = np.ones(100)
    v = secondary_noise_for_snr(d, None, np.random.default_rng(0))
    assert np.all(v == 0.0)
