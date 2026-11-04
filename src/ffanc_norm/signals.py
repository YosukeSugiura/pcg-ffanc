import numpy as np

def white_noise(n_samples, rng):
    x = rng.standard_normal(n_samples)
    return x / np.std(x)

def colored_noise(n_samples, rng, pole=0.95):
    u = rng.standard_normal(n_samples)
    x = np.empty_like(u)
    state = 0.0
    for n, value in enumerate(u):
        state = pole * state + value
        x[n] = state
    return x / np.std(x)

def tonal_plus_broadband(n_samples, sample_rate, rng, tones_hz=(250.0, 600.0, 1000.0)):
    t = np.arange(n_samples) / sample_rate
    x = 0.3 * rng.standard_normal(n_samples)
    for f in tones_hz:
        x += np.sin(2.0 * np.pi * f * t + rng.uniform(0.0, 2.0 * np.pi))
    return x / np.std(x)
