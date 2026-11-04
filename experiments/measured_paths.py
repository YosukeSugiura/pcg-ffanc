"""MeshRIR S32-M441 paths and provenance, fixed by REVISION_RULE_8.md."""
from functools import lru_cache
import hashlib
from importlib.metadata import version
import json
from pathlib import Path
import subprocess

import numpy as np
from scipy.signal import resample_poly

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / 'data/meshrir'
ARCHIVE_MD5 = '4fcd6137bcadb6914d4170ff366c86f9'
FROZEN = {
    'results/protocol_v2_sel/selected_e.json': '76fa959eee7b431b9ecbb57f4e2f0614875e52035749c37287d3c33e516cc665',
    'results/final_dev/final_config_core_main.json': 'aab4a80cfcddd051d5b9fdfa8240227afb42faff5d03e622289d32a7f961e814',
    'results/final_dev/final_config_core_final.json': '5e2a342b4690c115ea8221d6bfd6d6dea3e7f7a8627465aee1dde0375c09752d',
}


@lru_cache(maxsize=1)
def coordinates():
    mic = np.load(DATA / 'S32-M441_npy/pos_mic.npy', allow_pickle=False)
    src = np.load(DATA / 'S32-M441_npy/pos_src.npy', allow_pickle=False)
    if mic.shape != (441, 3) or src.shape != (32, 3):
        raise ValueError('Unexpected MeshRIR coordinates')
    if not np.isfinite(mic).all() or not np.isfinite(src).all():
        raise ValueError('Non-finite MeshRIR coordinates')
    return mic, src


def allocation(seed):
    """Only coordinates and the seed determine the five original array indices."""
    mic, src = coordinates()
    g = np.random.Generator(np.random.PCG64(int(seed) + 31337))
    for _ in range(1000):
        m0 = int(g.integers(441))
        neighbours = np.flatnonzero(np.abs(np.linalg.norm(mic - mic[m0], axis=1) - 0.05) <= 1e-9)
        m1 = int(neighbours[int(g.integers(len(neighbours)))])
        j = int(g.integers(32))
        eligible = np.ones(32, dtype=bool)
        eligible[j] = False
        for m in (m0, m1):
            distances = np.linalg.norm(src - mic[m], axis=1)
            eligible &= distances - distances[j] >= 0.343
        candidates = np.flatnonzero(eligible)
        if len(candidates) >= 2:
            i0, i1 = map(int, g.choice(candidates, size=2, replace=False))
            return {'seed': int(seed), 'm0': m0, 'm1': m1, 'j': j, 'i0': i0, 'i1': i1,
                    'coordinates_m': {'m0': mic[m0].tolist(), 'm1': mic[m1].tolist(),
                                      'j': src[j].tolist(), 'i0': src[i0].tolist(), 'i1': src[i1].tolist()}}
    raise ValueError(f'MeshRIR allocation exhausted 1000 attempts for seed {seed}')


def _raw_path(source, microphone, length, d0=0):
    ir = np.load(DATA / f'S32-M441_npy/ir_{microphone}.npy', mmap_mode='r', allow_pickle=False)
    if ir.shape != (32, 32768):
        raise ValueError(f'Unexpected MeshRIR IR shape: {ir.shape}')
    h = np.asarray(ir[source], dtype=np.float64)
    if not np.isfinite(h).all():
        raise ValueError('Non-finite MeshRIR IR')
    h = h[d0:]
    h = resample_poly(h, up=1, down=6, window=('kaiser', 5.0), padtype='constant', cval=0.0)
    return np.pad(h, (0, max(0, length - len(h))))[:length]


@lru_cache(maxsize=256)
def _paths(seed, target, d0=0):
    meta = allocation(seed)
    m0, m1, j, i0, i1 = (meta[k] for k in ('m0', 'm1', 'j', 'i0', 'i1'))
    p = _raw_path(i0, m0, 1200, d0)
    s = _raw_path(j, m0, 512, d0)
    p2 = _raw_path(i1, m0, 1200, d0) if target == 'source' else _raw_path(i0, m1, 1200, d0)
    s2 = None if target == 'source' else _raw_path(j, m1, 512, d0)
    pn, sn = np.linalg.norm(p), np.linalg.norm(s)
    if not (np.isfinite(pn) and np.isfinite(sn) and pn > 0 and sn > 0):
        raise ValueError('Invalid initial MeshRIR path norm; no redraw is permitted')
    a, b = 1.0 / pn, 1.0 / sn
    return p * a, s * b, p2 * a, None if s2 is None else s2 * b


def meshrir_paths(cfg, seed, extra=None):
    """Return (p,s,p2,s2); preserve physical delay and initial-path normalization."""
    target = cfg.get('move_target', 'source')
    d0 = cfg.get('meshrir_d0', 0)
    if not isinstance(d0, (int, np.integer)) or not 0 <= d0 < 32768:
        raise ValueError('meshrir_d0 must be an integer in [0,32768) at 48 kHz')
    if (int(cfg['sample_rate']) != 8000 or int(cfg.get('len_p', 1200)) != 1200
            or int(cfg.get('len_s', 512)) != 512 or int(cfg.get('move_steps', 0)) != 0
            or target not in ('source', 'mic') or cfg.get('ref_dist')):
        raise ValueError('MeshRIR conditions differ from REVISION_RULE_8')
    if extra is not None:
        extra['meshrir'] = dict(allocation(seed), scenario='M-P' if target == 'source' else 'M-PS')
        if d0:
            extra['meshrir']['removed_leading_samples_48k'] = int(d0)
    return tuple(None if h is None else h.copy() for h in _paths(int(seed), target, int(d0)))


def write_provenance(out, seeds, eval_set, meshrir_d0=0):
    """Check frozen inputs before running; retain the complete rule and software versions."""
    for name, expected in FROZEN.items():
        if hashlib.sha256((ROOT / name).read_bytes()).hexdigest() != expected:
            raise ValueError(f'Frozen configuration changed: {name}')
    with (DATA / 'S32-M441_npy.zip').open('rb') as fh:
        actual = hashlib.file_digest(fh, 'md5').hexdigest()
    if actual != ARCHIVE_MD5:
        raise ValueError('MeshRIR archive checksum mismatch')
    if meshrir_d0 not in (0, 5434):
        raise ValueError('Only the fixed Rule 8 / Rule 8a delay is permitted')
    rule_name = 'REVISION_RULE_8a.md' if meshrir_d0 else 'REVISION_RULE_8.md'
    rule = (ROOT / 'docs/current' / rule_name).read_text()
    meta = {'dataset': 'MeshRIR', 'doi': '10.5281/zenodo.5500451', 'version': 'v1.1',
            'subset': 'S32-M441', 'license': 'Creative Commons Attribution 4.0 International (CC BY 4.0)',
            'license_url': 'https://creativecommons.org/licenses/by/4.0/',
            'attribution': 'Shoichi Koyama, Tomoya Nishida, Keisuke Kimura, Takumi Abe, Natsuki Ueno, Jesper Brunnström',
            'archive_md5': actual, 'eval_set': eval_set, 'frozen_config_sha256': FROZEN,
            'preprocessing': {'resample_poly': {'up': 1, 'down': 6, 'window': ['kaiser', 5.0],
                                              'padtype': 'constant', 'cval': 0.0},
                              'len_p': 1200, 'len_s': 512, 'removed_leading_samples': meshrir_d0,
                              'normalization': 'Initial P/S L2 gains reused for changed paths'},
            'implementation_commit': subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip(),
            'rule_sha256': hashlib.sha256(rule.encode()).hexdigest(), 'rule_full_text': rule,
            'software': {p: version(p) for p in ('numpy', 'scipy', 'pyroomacoustics', 'soundfile', 'numba')},
            'allocation': [allocation(seed) for seed in seeds]}
    if meshrir_d0:
        meta['preprocessing']['removed_leading_samples_sample_rate'] = 48000
    path = out / 'provenance.json'
    if path.exists():
        from summary_provenance import check_existing_metadata
        check_existing_metadata(ROOT, json.loads(path.read_text()), meta)
    else:
        out.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(meta, indent=2, ensure_ascii=False) + '\n')


def validate_records(out, methods, combos, seeds):
    """Do not let the legacy summary silently discard corrupt or stale measured records."""
    expected = {(m, nz, sc, sd) for m in methods for nz, sc in combos for sd in seeds}
    seen = set()
    d0 = json.loads((out / 'provenance.json').read_text())['preprocessing']['removed_leading_samples']
    for path in sorted(out.glob('runs*.jsonl')):
        for line in path.read_text().splitlines():
            r = json.loads(line)
            k = r['method'], r['noise'], r['scen'], r['seed']
            if k not in expected or k in seen or r['prm'] != methods[r['method']][1]:
                raise ValueError(f'Unexpected/duplicate/stale record: {k}')
            expected_path = dict(allocation(r['seed']), scenario='M-P' if r['scen'].startswith('S2') else 'M-PS')
            if d0:
                expected_path['removed_leading_samples_48k'] = d0
            if r['path_provenance'] != expected_path:
                raise ValueError(f'Path provenance differs: {k}')
            seen.add(k)
    if seen != expected:
        raise ValueError(f'Incomplete measured records: {len(seen)} of {len(expected)}')


def annotate_summary(out):
    meta = json.loads((out / 'provenance.json').read_text())
    d0 = meta['preprocessing']['removed_leading_samples']
    rule = 'REVISION_RULE_8a' if d0 else 'REVISION_RULE_8'
    delay = f'common removal of {d0} samples at 48 kHz before resampling' if d0 else 'no delay removal'
    text = (f'# MeshRIR measured-path evaluation ({rule})\n\n'
            f"Dataset: MeshRIR {meta['version']}, {meta['subset']}; DOI {meta['doi']}.\n"
            f"License: {meta['license']} ({meta['license_url']}).\n"
            f"Attribution: {meta['attribution']}. Archive MD5: {meta['archive_md5']}.\n"
            'Preprocessing: 48 kHz -> 8 kHz resample_poly(1,6), Kaiser 5; P=1200, S=512 samples; '
            f'{delay}; initial P/S normalization reused. Full details: provenance.json.\n'
            'Scenario labels S2/R2 denote M-P/M-PS here, not 30 cm ISM source/rig moves. '
            'Holm: 48 tests per proposed method per set; bank-minus-main: 4.\n'
            'M-PS keeps the initial secondary-path model fixed.\n\n')
    if d0:
        text += ('Rule 8 results are retained but invalid as measured-path evidence due to missing direct sound. '
                 'Rule 8a is a defect correction specified after inspecting those results; no retuning.\n\n')
    path = out / 'summary.md'
    path.write_text(text + path.read_text())
