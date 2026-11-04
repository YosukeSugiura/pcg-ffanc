import numpy as np

from ffanc_norm.normalization import PowerTracker


def test_first_spectrum_initializes_power_directly():
    tracker = PowerTracker(n_bins=3, smoothing=0.8, regularization_ratio=1e-3)
    X = np.array([1.0, 2.0, 4.0], dtype=complex)
    p = tracker.update(X)
    assert np.allclose(p, np.abs(X) ** 2)


def test_global_denominator_is_identical_across_bins():
    tracker = PowerTracker(n_bins=4, smoothing=0.0, regularization_ratio=1e-3)
    tracker.update(np.array([1.0, 2.0, 3.0, 4.0], dtype=complex))
    d = tracker.denominator("global", block_index=0)
    assert np.allclose(d, d[0])


def test_binwise_denominator_tracks_each_bin():
    tracker = PowerTracker(n_bins=3, smoothing=0.0, regularization_ratio=1e-3)
    tracker.update(np.array([1.0, 2.0, 4.0], dtype=complex))
    d = tracker.denominator("binwise", block_index=0)
    assert d[0] < d[1] < d[2]


def test_switched_mode_changes_at_requested_block():
    tracker = PowerTracker(n_bins=3, smoothing=0.0, regularization_ratio=1e-3)
    tracker.update(np.array([1.0, 2.0, 4.0], dtype=complex))

    before = tracker.denominator("switched", block_index=7, switch_block=8)
    after = tracker.denominator("switched", block_index=8, switch_block=8)

    assert np.allclose(before, before[0])
    assert not np.allclose(after, after[0])


def test_shrinkage_weight_is_bounded_and_zero_for_one_flat_spectrum():
    tracker = PowerTracker(n_bins=4, smoothing=0.8, regularization_ratio=1e-3)
    tracker.update(np.ones(4, dtype=complex))
    lam = tracker.confidence_weight()
    assert 0.0 <= lam <= 1.0
    assert lam == 0.0


def test_shrinkage_denominator_interpolates_global_and_binwise():
    tracker = PowerTracker(n_bins=3, smoothing=0.0, regularization_ratio=1e-3)
    tracker.update(np.array([1.0, 2.0, 4.0], dtype=complex))
    dg = tracker.denominator("global", block_index=0)
    db = tracker.denominator("binwise", block_index=0)
    ds0 = tracker.denominator("shrinkage", block_index=0, shrinkage_weight=0.0)
    ds1 = tracker.denominator("shrinkage", block_index=0, shrinkage_weight=1.0)
    assert np.allclose(ds0, dg)
    assert np.allclose(ds1, db)
