# Selected inverse-survival-function timing plan

Freeze this plan and the external runner and tests before any measurements.
The scope is the frozen main and bank controllers, room A, all 15 main-grid
noise/scenario cells, seeds 300–304, 5 seconds per run (150 cases, two runs
per case). Use `final_config_core_main.json` and `final_config_core_final.json`
unchanged, M=512, N=1024, H=128, and the original scenario definitions. S8 has
no change; the other scenarios use the original one-second change. Each case
runs uninstrumented first, then instrumented with identical settings; report
exceptions and failures rather than retrying selectively.

Enable `RETURN_SIGNALS` for both runs, restore it afterward, and require exact
byte equality of the raw error array and every returned field, especially reset
and localization events, before treating the timing as a valid paired result.
Report exact mismatch fields and hashes; do not substitute traces. Use the same
one-CPU affinity and single-thread BLAS/OMP/MKL conditions as the coordinated
full-history measurements; record actual platform, libraries, affinity and
thread pools. Set `RLS_FAST=1` and `OPENBLAS_CORETYPE=SkylakeX`, and verify
the loaded OpenBLAS architecture. Record load averages at start and end, and keep a
persistent process log. Store results in a new directory under `results`, with no
overwrite; record settings and flag/runner hashes before the first simulation.

The external context manager wraps the outermost `EPCG.update` or
`EPCGBank.update`, avoiding double-counting nested member updates. While an
update is active it individually counts and times `scipy.stats.chi2.isf`,
`scipy.stats.f.isf`, and `scipy.stats.norm.isf`. Report call counts, selected
quantile durations, and their ratio to measured outer update duration per case.
This is inclusive wall time and includes wrapper, clock and nested-call overhead;
the fraction is descriptive, not total uncounted computation, a FLOP measure,
a benchmark of speedup, a real-time guarantee or WCET. Quantile calls outside
updates are not included. Calls to the same distribution are aggregated, so the
chi-square screen and initial detector-threshold calls are not separated. No optimizations, parameter changes, selection, or
claim about other branches or externally forced restarts follows from this run.
