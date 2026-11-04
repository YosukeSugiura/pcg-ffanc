# Fixed seed sets (from 2026-10-26; user instruction: do not change the seed sets between experiments)

| use | seeds | rule |
|---|---|---|
| tuning | 300-309 and 600-619 (30) | every design decision and every parameter selection; small fixes are tested here |
| evaluation | 480-519 (40) | every evaluation of a frozen configuration; reused after small fixes |

* The method is essentially fixed; the evaluation set is reused (no reserve set). If results are not stable across
  re-evaluations, the remedy is more seeds (statistical power), not new seed sets.
* Earlier seed sets (320-359, 360-399, 400-439, 440-479) were used once each for v6.1-v6.4 and are not used again.
