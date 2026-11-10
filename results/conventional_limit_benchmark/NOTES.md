# conventional_limit_benchmark — run 2 (2026-10-17, commit 3af4262)

Same protocol as run 1 (60 Optuna trials/method, train 0-5, validation 20-29,
held-out 100-119, 0.5 s objective, 2 s held-out), with the regularized NLMS
denominator `delta + ||x_f||^2` for the sample-wise methods
(delta = 0.176319, DCT bin floor = 6.88748e-4, from training seeds only).

All 9 methods are stable on 20/20 held-out seeds, so every row is a primary
metric. SSS-family numbers remain provisional until the SSS / DCT-SSS
equations are checked against the publisher PDFs (candidate-state handling,
sigma_e^2 definition, DCT power-diagonal initialization).

Run 1 (delta = 0, seed 117 unstable for all sample-wise methods) is preserved
in `../conventional_limit_benchmark_run1_delta0`.
