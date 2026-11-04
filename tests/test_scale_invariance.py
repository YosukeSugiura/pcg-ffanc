import numpy as np

from ffanc_norm.fd_fxnlms import FDFxNLMS


def make_algorithm():
    return FDFxNLMS(
        fft_length=512,
        hop_length=128,
        controller_length=256,
        mu=0.05,
        smoothing=0.8,
        regularization_ratio=1e-3,
        mode="binwise",
    )


def test_first_update_is_scale_invariant_for_joint_signal_scaling():
    rng = np.random.default_rng(2)
    xf = rng.standard_normal(512)
    err = rng.standard_normal(128)

    a1 = make_algorithm()
    a2 = make_algorithm()

    a1.update(xf, err)

    scale = 7.0
    a2.update(scale * xf, scale * err)

    assert np.allclose(a1.w, a2.w, rtol=1e-11, atol=1e-11)


def test_shrinkage_update_is_scale_invariant():
    rng = np.random.default_rng(3)
    xf = rng.standard_normal(512)
    err = rng.standard_normal(128)

    def make_shrinkage():
        return FDFxNLMS(
            fft_length=512,
            hop_length=128,
            controller_length=256,
            mu=0.055,
            smoothing=0.8,
            regularization_ratio=1e-3,
            mode="shrinkage",
            mu_global=0.055,
            mu_binwise=0.35,
        )

    a1 = make_shrinkage()
    a2 = make_shrinkage()
    a1.update(xf, err)
    scale = 7.0
    a2.update(scale * xf, scale * err)
    assert np.allclose(a1.w, a2.w, rtol=1e-11, atol=1e-11)
    assert np.isclose(a1.shrinkage_weight_history[-1], a2.shrinkage_weight_history[-1])
    assert np.isclose(a1.mu_history[-1], a2.mu_history[-1])
