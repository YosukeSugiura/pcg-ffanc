"""Measured-data wiring checks; no performance-based selection."""
from pathlib import Path
import sys

import numpy as np
import pytest
from scipy.signal import resample_poly

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'experiments'))
import measured_paths as MP

pytestmark = pytest.mark.skipif(not (MP.DATA / 'download_verified.json').exists(), reason='MeshRIR not downloaded')


def test_allocation_geometry_and_reproducibility():
    mic, src = MP.coordinates()
    for seed in range(480, 520):
        a = MP.allocation(seed)
        assert a == MP.allocation(seed)
        assert len({a['i0'], a['i1'], a['j']}) == 3
        assert abs(np.linalg.norm(mic[a['m0']] - mic[a['m1']]) - .05) <= 1e-9
        for m in (a['m0'], a['m1']):
            for i in (a['i0'], a['i1']):
                assert np.linalg.norm(src[i] - mic[m]) - np.linalg.norm(src[a['j']] - mic[m]) >= .343


@pytest.mark.parametrize('target', ['source', 'mic'])
@pytest.mark.parametrize('d0', [0, 5434])
def test_measured_paths_match_unshifted_resampling_and_initial_gains(target, d0):
    cfg = dict(sample_rate=8000, len_p=1200, len_s=512, move_target=target, move_steps=0, meshrir_d0=d0)
    extra = {}
    p, s, p2, s2 = MP.meshrir_paths(cfg, 300, extra)
    a = MP.allocation(300)

    def raw(i, m, length):
        h = np.load(MP.DATA / f'S32-M441_npy/ir_{m}.npy')[i]
        h = h[d0:]
        return resample_poly(h, 1, 6, window=('kaiser', 5.), padtype='constant', cval=0.)[:length]

    p0 = raw(a['i0'], a['m0'], 1200)
    s0 = raw(a['j'], a['m0'], 512)
    gain_p, gain_s = 1 / np.linalg.norm(p0), 1 / np.linalg.norm(s0)
    assert np.array_equal(p, p0 * gain_p)
    assert np.array_equal(s, s0 * gain_s)
    if target == 'source':
        assert np.array_equal(p2, raw(a['i1'], a['m0'], 1200) * gain_p)
        assert s2 is None
    else:
        assert np.array_equal(p2, raw(a['i0'], a['m1'], 1200) * gain_p)
        assert np.array_equal(s2, raw(a['j'], a['m1'], 512) * gain_s)
    assert extra['meshrir']['seed'] == 300
    p[:] = 0
    assert np.array_equal(MP.meshrir_paths(cfg, 300)[0], p0 * gain_p)


def test_unsupported_conditions_are_rejected():
    with pytest.raises(ValueError):
        MP.meshrir_paths(dict(sample_rate=48000), 300)


def test_zero_delay_is_the_default_and_cache_is_separate():
    cfg = dict(sample_rate=8000)
    default = MP.meshrir_paths(cfg, 480)
    zero = MP.meshrir_paths(dict(cfg, meshrir_d0=0), 480)
    corrected = MP.meshrir_paths(dict(cfg, meshrir_d0=5434), 480)
    for a, b in zip(default, zero):
        assert (a is None and b is None) or a.tobytes() == b.tobytes()
    assert not np.array_equal(default[1], corrected[1])
    with pytest.raises(ValueError):
        MP.meshrir_paths(dict(cfg, meshrir_d0=-1), 480)
