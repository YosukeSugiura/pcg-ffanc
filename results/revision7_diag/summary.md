# CFTF + det failure (S7 ar1, evaluation seed 515): diagnosis (no decision depends on it)
- Detection at sample 8064, tau = 7996. CFTF controller vs exact RLS with the same prior and window (cftf_515.md):
  relative deviation 8e-16 (8064) -> 1.8e-10 (8192) -> 2.8e-5 (8320) -> NaN (8448), i.e. round-off amplified by about
  1e5 per hop right after the restart (n < M, gamma_f ~ 0.03-0.05), then overflow; the exact LS solution stays bounded.
- Same run with the stabilization feedback off (mixing constants 1, 1, 1; cftf_515_nostab.md): deviation <= 1.6e-13 over
  the whole run, no failure. With the stabilization on and a larger prior (delta 0.1 or 1) the run does not fail either.
- Cause: the Slock-Kailath error feedback (constants 1.5 / 2.5), designed for the steady state, amplifies round-off in the
  transient after a covariance restart with a small prior. Not a property of the LS problem (RLS + det does not fail).
- The evaluated configuration is unchanged (REVISION_RULE_7 fixed); a remedy (feedback switched on only after n > 2M, or a
  larger prior) would need its own rule and runs.
