# E-PCG full-history access instrumentation: preregistration

Before producing measurements, review and commit this document and the new
runner and tests. This experiment observes the existing implementation only;
it neither implements a circular buffer nor changes algorithm parameters or
modifies existing results. Output must be a new directory with refusal to
replace any existing artifact. Record code/config/rule hashes, source commit,
Python/NumPy/SciPy/threadpool versions and actual CPU/kernel affinity.

## Population and equivalence

Use `E-PCG-F` with exactly the frozen `results/final_dev/final_config_core_main.json`
flags for main and `final_config_core_final.json` flags for the bank. Bank has
its original `[12,48,1000]`, share/nodetect/fftmin/sharescore/doze flags; no
addition of Stein/band, detector or force-event tuning. Use M512/N1024/H128,
fs8000, 5 s, 312 complete hops, the 15 main cells ar1/harmonic × the eight
original scenarios except harmonic S7, seeds 300–304: 75 cases × 2 configs ×
2 instrumentation states = 300 simulations. These are previously used tuning
seeds, not an independent validation set. Set `RETURN_SIGNALS=True` for both
states to expose the actual full sample-level `e`, restoring it afterward; it
is a diagnostic output flag and not a controller change. Use SkylakeX BLAS,
one pinned CPU, BLAS/OMP/MKL thread counts 1, RLS_FAST=1. For each case run
uninstrumented followed by instrumented; do not read an outcome to change order,
cases, thresholds or configuration. Record exceptions, instability and incomplete
hops without dropping or retrying any case.

For each pair require exact shape, dtype and byte equality of the complete `e`
array and of reset-hop and localization arrays; also compare other available
returned `total_power`, `uncontrolled_power`, `score_hist` and stability. Store
per-case digests, comparison booleans, both event sequences, count and membership.
On any mismatch preserve the raw event and digest records and flag the case;
do not treat its access trace as a verified observation of the uninstrumented
run. Do not change the instrumentation in response to measured outcomes.

## Actual history access observations

Temporarily wrap EPCG's `xf` and `dh` history arrays in an ndarray subclass on
assignment; keep the same data and restore all class/global hooks in `finally`.
On each real `__getitem__` call, record array identity, controller identity,
method and relevant outer context (including `force_restart`), `stop`, array
length and the min/max absolute element index and element count actually selected.
Account for negative indices, Python slices, boolean masks and integer-index
arrays, including accesses executed by eager `np.where` evaluation. Empty
selections count as empty; slices are interpreted by NumPy semantics. Capture
references to each member of a memory bank separately; do not treat the bank's
separate fixed-length `xf_tail` as a full-history array. Record whether Stein
band code, detection/localization/score, force_restart, and bank-member accesses
actually run; never infer coverage from the configuration alone.

`np.concatenate([self.xf, xf_hop])` and the analogous `dh` operation read/copy
the previous entire history without `__getitem__`; also wrap concatenate to
record those whole-history copies separately from algorithmic indexed reads.
The resulting array is rewrapped at assignment; tests must prove this happens.
Record both oldest indexed sample and oldest append-copy sample, as well as
maximum age measured against the actual `stop` and against history length;
record at-access stop and length to avoid silently equating those quantities.
Aggregate counts and min/max per array, controller, caller/outer context, and
run. Retain raw per-access records in per-case files where practical; numeric
index summaries cannot establish future access bounds. Report logical indexed
reads separately from concatenation copies and other operations, and make no
claim to capture operating-system page faults or all C-level memory traffic.
The recording hook must not alter the original selected values or call any
method that changes the state of the controller.

Unit tests before the simulation cover integer/scalar/negative/slice/step/empty,
integer arrays, boolean indices, eager `np.where` access, concatenation and
rewrapping on assignment, object lifecycle, context classification, restoration
on exceptions, and stop/length values across update; test a bank with multiple
controllers. Any mismatch or uncovered mode is reported as a limitation. No
new claim of universal ring-buffer capacity or correctness follows from a finite
5-second observation; calls on other configurations, forced replay, unusual
localization history, access through other objects and longer durations may need
older samples. Forced-restart and optional Stein code not exercised in these
cases must be reported as uncovered, not presumed safe.
