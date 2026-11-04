import numpy as np

def synthetic_primary_path():
    h = np.zeros(64)
    h[4], h[9], h[18], h[31] = 0.8, -0.35, 0.20, -0.08
    return h

def synthetic_secondary_path():
    h = np.zeros(48)
    h[3], h[7], h[15], h[27] = 0.65, 0.28, -0.16, 0.07
    return h
