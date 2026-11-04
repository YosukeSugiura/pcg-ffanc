"""Read-only onset/window diagnosis for the original 48 kHz MeshRIR IRs."""
from concurrent.futures import ProcessPoolExecutor
from functools import lru_cache
import hashlib
import json
from pathlib import Path
import subprocess
import sys

import numpy as np
from scipy.signal import resample_poly

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'experiments'))
from measured_paths import DATA, allocation, coordinates

RAW_FS = 48000
C = 343.
OUT = ROOT / 'results/revision8_diag'
WINDOWS = {'P': 1200, 'S': 512}


def measure(h, source_position, mic_position):
    h = np.asarray(h, dtype=np.float64)
    if h.shape != (32768,) or not np.isfinite(h).all():
        raise ValueError('Invalid raw MeshRIR IR')
    magnitude = np.abs(h)
    peak = int(np.argmax(magnitude))
    if magnitude[peak] <= 0:
        raise ValueError('Zero IR')
    onset = int(np.flatnonzero(magnitude > .1 * magnitude[peak])[0])
    distance = float(np.linalg.norm(np.asarray(source_position) - mic_position))
    propagation_ms = 1000 * distance / C
    h8 = resample_poly(h, 1, 6, window=('kaiser', 5.), padtype='constant', cval=0.)
    energy = float(h @ h)
    energy8 = float(h8 @ h8)
    retention = {}
    for kind, length in WINDOWS.items():
        raw_end = 6 * length
        retention[kind] = {
            'window_8k_samples': [0, length], 'window_48k_samples': [0, raw_end],
            'raw_retained_energy_ratio': float(h[:raw_end] @ h[:raw_end] / energy),
            'pipeline_8k_retained_energy_ratio': float(h8[:length] @ h8[:length] / energy8),
            'peak_inside_raw_window': bool(peak < raw_end),
            'minus20db_onset_inside_raw_window': bool(onset < raw_end)}
    return {'peak_sample': peak, 'peak_ms': peak / 48., 'peak_abs': float(magnitude[peak]),
            'minus20db_threshold_abs': float(.1 * magnitude[peak]),
            'minus20db_first_exceed_sample': onset, 'minus20db_first_exceed_ms': onset / 48.,
            'geometric_distance_m': distance, 'geometric_propagation_ms': propagation_ms,
            'estimated_system_delay_ms_peak_minus_geometry': peak / 48. - propagation_ms,
            'estimated_system_delay_samples_peak_minus_geometry': peak - RAW_FS * distance / C,
            'raw_total_energy': energy, 'resampled_total_energy': energy8, 'retention': retention}


@lru_cache(maxsize=16)
def raw_mic(mic):
    h = np.load(DATA / f'S32-M441_npy/ir_{mic}.npy', mmap_mode='r', allow_pickle=False)
    if h.shape != (32, 32768):
        raise ValueError('Invalid MeshRIR shape')
    return h


def path(source, mic):
    microphones, sources = coordinates()
    return dict(source=source, microphone=mic, source_position_m=sources[source].tolist(),
                microphone_position_m=microphones[mic].tolist(),
                **measure(raw_mic(mic)[source], sources[source], microphones[mic]))


def seed_paths(seed):
    a = allocation(seed)
    roles = {'i0_m0': ('i0', 'm0', 'P', 'P before'),
             'i1_m0': ('i1', 'm0', 'P', 'P after M-P'),
             'i0_m1': ('i0', 'm1', 'P', 'P after M-PS'),
             'i1_m1': ('i1', 'm1', 'P', 'unused combination; diagnostic only'),
             'j_m0': ('j', 'm0', 'S', 'S before / fixed S of M-P'),
             'j_m1': ('j', 'm1', 'S', 'S after M-PS')}
    return {'seed': seed, 'allocation': a,
            'paths': {name: dict(kind=kind, role=role, **path(a[i], a[m])) for name, (i, m, kind, role) in roles.items()}}


def representative_mics():
    microphones, _ = coordinates()
    targets = [(0., 0., 0.), (-.5, -.5, 0.), (-.5, .5, 0.), (.5, -.5, 0.), (.5, .5, 0.)]
    ids = []
    for target in targets:
        distance = np.linalg.norm(microphones - target, axis=1)
        index = int(np.argmin(distance))
        if distance[index] > 1e-9:
            raise ValueError('Representative centre/corner microphone missing')
        ids.append(index)
    assert len(set(ids)) == 5
    return ids


def representative_task(pair):
    return path(*pair)


def result_hashes():
    hashes = {}
    for p in sorted((ROOT / 'results').rglob('*')):
        if p.is_file():
            with p.open('rb') as f:
                hashes[str(p.relative_to(ROOT))] = hashlib.file_digest(f, 'sha256').hexdigest()
    return hashes


def stats(values):
    a = np.asarray(values, dtype=float)
    return {'n': len(a), 'min': float(a.min()), 'q1': float(np.quantile(a,.25)),
            'median': float(np.median(a)), 'q3': float(np.quantile(a,.75)),
            'max': float(a.max()), 'std_population': float(a.std())}


def q(values):
    s = stats(values)
    return f"{s['median']:.4f} ({s['q1']:.4f}, {s['q3']:.4f})"


def markdown(data):
    seeds, reps = data['seeds'], data['representative_paths']
    secondary = [r['paths'][role] for r in seeds for role in ('j_m0', 'j_m1')]
    peak_out = sum(not r['retention']['S']['peak_inside_raw_window'] for r in secondary)
    onset_out = sum(not r['retention']['S']['minus20db_onset_inside_raw_window'] for r in secondary)
    if onset_out:
        verdict = '前処理の不具合'
    elif not peak_out:
        verdict = '不具合ではない'
    else:
        verdict = '判定要注意：ピークは窓外だが−20 dB到達は窓内（直接音候補の確認が必要）'
    lines = ['# MeshRIR 生IRの到達位置と打ち切り窓診断', '', f'**判定：{verdict}**', '',
             f'S経路（40シード×変化前後、重複あり）のうち、−20 dB到達が窓外：{onset_out}/80、最大ピークが窓外：{peak_out}/80。',
             'Sの窓は8 kHz [0:512]＝64 ms、48 kHzでは[0:3072]（index 0–3071）。Pは[0:1200]＝150 ms、48 kHz [0:7200]。', '',
             '## 定義', '',
             '- 生IRは48 kHz、32768点。ピークはargmax(|h|)、到達候補は |h| > 0.1 max|h| を満たす最初の点（−20 dB、厳密な超過）。サンプル番号は0始まり。',
             '- 幾何遅延＝音源・マイク間距離/343。推定系遅延＝最大ピーク時刻−幾何遅延。ピークや閾値到達は直接音の代理指標であり、反射やノイズと自動的に分離できるものではない。',
             '- 全3音源 i0/i1/j × 全2マイク m0/m1 の6組を調査。i1/m1は評価で使わない補助組。Sの判定にはj/m0とj/m1を使用。',
             '- 保持率は、raw先頭7200/3072点とraw全長のエネルギー比、および実装と同じresample_poly(1,6)後の先頭1200/512点と全長のエネルギー比を併記。後者が実際の前処理の保持率。L2正規化は比率を変えない。',
             '- 窓の境界でリサンプラのフィルタがまたぐため、rawの単純打ち切り比と8 kHzの保持率は厳密には同じではない。', '',
             '## シード480–519の経路別集計：中央値 (Q1, Q3)', '',
             '| 組 | peak sample | peak ms | −20 dB sample | 幾何遅延 ms | 推定系遅延 ms | raw保持率 | 実装8k保持率 |',
             '|---|---|---|---|---|---|---|---|']
    for role in seeds[0]['paths']:
        rs = [s['paths'][role] for s in seeds]
        fields = [q([r[k] for r in rs]) for k in ('peak_sample', 'peak_ms', 'minus20db_first_exceed_sample', 'geometric_propagation_ms', 'estimated_system_delay_ms_peak_minus_geometry')]
        fields += [q([r['retention'][r['kind']][key] for r in rs]) for key in ('raw_retained_energy_ratio', 'pipeline_8k_retained_energy_ratio')]
        lines.append('| ' + role + ' | ' + ' | '.join(fields) + ' |')
    lines += ['', '## 代表マイク5点×全32音源', '',
              '結果を見ずに中心と四隅を選択。ばらつきのstdは母標準偏差（ddof=0）。', '',
              '| mic ID | 座標 m | peak ms: 中央値 (Q1,Q3) | peak min–max ms | 系遅延 ms: 中央値 (Q1,Q3) | 系遅延 min–max ms | 系遅延 std ms |',
              '|---|---|---|---|---|---|---|']
    for m in data['representative_mic_ids']:
        rs = [r for r in reps if r['microphone'] == m]
        p = stats([r['peak_ms'] for r in rs]); d = stats([r['estimated_system_delay_ms_peak_minus_geometry'] for r in rs])
        lines.append(f"| {m} | {rs[0]['microphone_position_m']} | {q([r['peak_ms'] for r in rs])} | {p['min']:.4f}–{p['max']:.4f} | {q([r['estimated_system_delay_ms_peak_minus_geometry'] for r in rs])} | {d['min']:.4f}–{d['max']:.4f} | {d['std_population']:.4f} |")
    lines += ['', '| source ID | peak min–max ms（5点） | peak std ms | 系遅延 中央値 ms | 系遅延 min–max ms | 系遅延 std ms |', '|---|---|---|---|---|---|']
    for source in range(32):
        rs = [r for r in reps if r['source'] == source]
        p = stats([r['peak_ms'] for r in rs]); d = stats([r['estimated_system_delay_ms_peak_minus_geometry'] for r in rs])
        lines.append(f"| {source} | {p['min']:.4f}–{p['max']:.4f} | {p['std_population']:.4f} | {d['median']:.4f} | {d['min']:.4f}–{d['max']:.4f} | {d['std_population']:.4f} |")
    p, d = data['representative_peak_ms_stats'], data['representative_system_delay_ms_stats']
    lines += ['', f"全160組のピーク：中央値 {p['median']:.4f} ms、範囲 {p['min']:.4f}–{p['max']:.4f} ms、std {p['std_population']:.4f} ms。",
              f"全160組の推定系遅延：中央値 {d['median']:.4f} ms、範囲 {d['min']:.4f}–{d['max']:.4f} ms、std {d['std_population']:.4f} ms。", '',
              '## 変更範囲', '',
              '本診断のみ。既存resultsの全ファイルを実行前後のSHA256で照合し、不変を確認。評価再実行、前処理・経路・設定・ルールの修正なし。',
              '旧Revision 8のNR下限・性能評価は、その打ち切り済み経路に対する結果であり、生IRの直接音を含む実測経路に一般化しない。',
              'MeshRIR v1.1 S32-M441、DOI 10.5281/zenodo.5500451、CC BY 4.0。Attribution: Koyama, Nishida, Kimura, Abe, Ueno, Brunnström。']
    return '\n'.join(lines) + '\n', verdict


def main():
    if any((OUT / name).exists() for name in ('onset.md', 'onset.json')):
        raise FileExistsError('Refusing to overwrite onset results')
    before = result_hashes()
    ids = representative_mics()
    with ProcessPoolExecutor(max_workers=2) as pool:
        seeds = list(pool.map(seed_paths, range(480, 520)))
        representative = list(pool.map(representative_task, [(i, m) for i in range(32) for m in ids]))
    assert result_hashes() == before, 'Existing results changed'
    data = {'metadata': {'diagnostic_only': True, 'no_adaptive_runs': True, 'no_preprocessing_fix': True,
                         'raw_sample_rate': RAW_FS, 'sound_speed_m_s': C, 'threshold_db': -20,
                         'source_commit': subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip(),
                         'script_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                         'existing_results_file_sha256': before, 'existing_results_unchanged': True},
            'seeds': seeds, 'representative_mic_ids': ids, 'representative_paths': representative,
            'representative_peak_ms_stats': stats([r['peak_ms'] for r in representative]),
            'representative_system_delay_ms_stats': stats([r['estimated_system_delay_ms_peak_minus_geometry'] for r in representative])}
    text, verdict = markdown(data)
    data['verdict'] = verdict
    (OUT / 'onset.json').write_text(json.dumps(data, indent=2, ensure_ascii=False) + '\n')
    (OUT / 'onset.md').write_text(text)
    print(verdict, flush=True)
    print(f'40 seeds, 240 raw IRs; 32 x 5 = 160 representative IRs; {len(before)} existing result files unchanged', flush=True)


if __name__ == '__main__':
    main()
