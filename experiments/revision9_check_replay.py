"""Revision 9-B implementation check (not a performance run): RLS + CUSUM must restart exactly as RLS + det.

Run R-RLS with the CUSUM detector, feed its alarms (stop, tau) as det_events to the frozen RLS + det
configuration on the same data, and require bit-identical deterministic outputs, including the signals
e, y and the final controller w. Requires RLS_FAST=1 (production path). Exit 1 on mismatch, 2 if vacuous.
"""
import json
import os
import sys

import numpy as np

import eval_v2 as ev

CASES = [('ar1', 'S2 src 30cm', 300), ('harmonic', 'S5 src 30cm cont', 301), ('ar1', 'R1 rig 10cm', 302),
         ('ar1', 'S8 stationary', 303)]
CUS = dict(lam=0.9999, delta=0.01, cusum_h=3.0, cusum_k=16)      # grid index 0 (lowest h -> most alarms)
DET = dict(lam=0.9999, delta=0.01, det_reset_w=False)           # selected RLS + det (selected_e.json index 1)
# det_events path records reset_hops but not loc_hist / n_resets, so those two are excluded by construction
KEYS = ('total_power', 'uncontrolled_power', 'stable', 'failure', 'reset_hops', 'e', 'y', 'w_final')


def same(a, b):
    if isinstance(a, np.ndarray) or isinstance(b, np.ndarray):
        a, b = np.asarray(a), np.asarray(b)
        return a.shape == b.shape and a.dtype == b.dtype and a.tobytes() == b.tobytes()
    return a == b


def main():
    if not os.environ.get('RLS_FAST'):
        print('set RLS_FAST=1'); sys.exit(2)
    ev.D.P.RETURN_SIGNALS = True
    bad = 0; n_alarm = 0; n_multi = 0; n_nonlast = 0
    for nz, sc, sd in CASES:
        cfg = ev.cfg_of('A', nz, sc); ch = None if sc.startswith('S8') else ev.D.CH
        a = ev.D.P.run(cfg, sd, 'R-RLS', CUS, 5.0, ch)
        events = [[(int(h) + 1) * ev.H, int(t)] for h, t in zip(a['reset_hops'], a['loc_hist'])]
        b = ev.D.P.run(cfg, sd, 'R-RLS', dict(DET, det_events=events), 5.0, ch)
        diff = [k for k in KEYS if not same(a[k], b[k])]
        n_last = len(a['total_power'])
        n_alarm += len(events); bad += bool(diff)
        n_multi += sum(st - t > ev.H for st, t in events)              # replay spans more than one hop
        n_nonlast += sum(st // ev.H < n_last for st, _ in events)      # a later hop observes the replayed w
        print(json.dumps(dict(noise=nz, scen=sc, seed=sd, alarms=len(events), mismatch=diff)), flush=True)
    print(json.dumps(dict(cases=len(CASES), alarms=n_alarm, multi_hop_replays=n_multi,
                          non_last_alarms=n_nonlast, mismatching_cases=bad)))
    if n_alarm == 0 or n_multi == 0 or n_nonlast == 0:
        print('VACUOUS: need alarms, a multi-hop replay and a non-final alarm'); sys.exit(2)
    sys.exit(1 if bad else 0)


if __name__ == '__main__':
    main()
