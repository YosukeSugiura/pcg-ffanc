# Rule 11 Sec. 6.3: equivalence of the new flags

## (a) fd_block_gradient_mod vs recursion A (gap_check4a)
- 100 random frames (N 1024, H 128, M 512): max relative difference 0.000e+00 (criterion 1e-12)
- 40-hop recursion, gap_check4a.recursion(kind="A") vs the same loop with fd_block_gradient_mod: max relative difference of the hop powers 0.000e+00
- PASS

## (b) RLS + det (cond.): theta = -inf == RLS + det; theta = +inf == R-RLS lam 0.9999 without events
| case | events | -inf vs RLS + det | +inf vs R-RLS | restarts (-inf / +inf) |
|---|---|---|---|---|
| ar1 S2 src 30cm | 1 | identical | identical | 1 / 0 |
| harmonic S5 src 30cm cont | 4 | identical | identical | 4 / 0 |

## (c) RLS + det + growth (Rule 11a Sec. 2.2; replaces the former (c))
- (c1) version (i) `det_grow: half` with no event vs R-RLS lam 0.9999 delta 0.01 (seed 300, ar1 S8, 5 s, signals and w_final): identical
- (c2) version (i), one event (stop 3712, tau 3648) in a 0.5 s run: the run ends n = 320 < 2M = 1024 samples after tau; w_final taps >= max(n // 2, 1) = 160 are exactly 0 and the 160 leading taps are non-zero; RLS + det (same event, no growth) has 352 non-zero taps there: PASS
- (c2) version (ii) `det_grow_start: True`, no event, 0.1 s run (n = 768 < 2M): taps >= 384 exactly 0 and the 384 leading taps non-zero; version (i) on the same run has 128 non-zero taps there (no growth at the start): PASS
- (c3) code review: for n = t - g0 + 1 >= 2M (or g0 = None) the regressor, gain, P update and w update are
  the existing statements; the growth adds only the truncation `u[_grow_taps(n, M):] = 0` and, at a restart,
  `w[_grow_taps(1, M):] = 0` (w[1:] = 0). det_grow absent: `_grow` is None and the loop is the existing one
  (tests/test_revision11.py::test_rls_grow_none_is_the_existing_path and Sec. 6.1). PASS (review)

Result: PASS
