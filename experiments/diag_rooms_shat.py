"""Review N4 diagnostic (REVISION_RULE_3.md addendum): change of the secondary path in the R2 rig move per room.
usage: python experiments/diag_rooms_shat.py -> results/revision3_diag/rooms_shat.md"""
import sys
from pathlib import Path
import numpy as np
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src')); sys.path.insert(0, str(ROOT / 'experiments'))
import eval_v2 as E  # noqa: E402
P = E.D.P
OUT = ROOT / 'results' / 'revision3_diag'; OUT.mkdir(exist_ok=True)
NFFT = 2048
L = ['# R2 rig 30cm: secondary-path change per room (S_hat = S before the move; evaluation seeds 480-519, median)', '',
     '| room | RT60 (s) | len_s | broadband ||s2-s||/||s|| | fraction of bins with |1 - S2/S| >= 1 |', '|---|---|---|---|---|']
for room in ('A', 'B', 'C'):
    cfg = E.cfg_of(room, 'ar1', 'R2 rig 30cm')
    rel, frac = [], []
    for sd in E.EVAL:
        p, s, p2, s2 = P.ism_paths(cfg, sd, {})
        s, s2 = np.asarray(s, float), np.asarray(s2, float)
        S, S2 = np.fft.rfft(s, NFFT), np.fft.rfft(s2, NFFT)
        rel.append(np.linalg.norm(s2 - s) / np.linalg.norm(s))
        frac.append(np.mean(np.abs(1 - S2 / S) >= 1))
    L.append(f"| {room} | {cfg.get('ism_rt60', 'A default')} | {len(s)} | {np.median(rel):.3f} | {np.median(frac):.3f} |")
(OUT / 'rooms_shat.md').write_text('\n'.join(L) + '\n'); print('\n'.join(L))
