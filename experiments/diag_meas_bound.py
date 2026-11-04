"""Read-only Revision 8 controllability diagnosis; never run an adaptive method.

True-S values are stationary causal Wiener bounds. A controller designed using
an obsolete S_hat and evaluated with true S is a mismatch diagnostic, NOT a bound.
"""
from concurrent.futures import ProcessPoolExecutor
from functools import partial
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys

import numpy as np
from scipy.linalg import cho_factor, cho_solve, toeplitz
from scipy.signal import lfilter

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'experiments'))
sys.path.insert(0, str(ROOT / 'src'))
from measured_paths import meshrir_paths, ARCHIVE_MD5
from ffanc_norm.signals import colored_noise

FS = 8000
NFFT = 80000  # 0.1 Hz; every 40 Hz harmonic lies exactly on the integration grid
M = 512
BANDS = ((0, 100), (100, 300), (300, 1000), (1000, 4000))
BAND_NAMES = ('<100', '100-300', '300-1k', '1k-4k')
OUT = ROOT / 'results/revision8_diag'


def symmetry(n):
    q = np.full(n // 2 + 1, 2.)
    q[0] = 1.
    if n % 2 == 0:
        q[-1] = 1.
    return q


def band_sums(power, frequencies):
    return {name: float(np.sum(power[(frequencies >= lo) & ((frequencies < hi) if hi < 4000 else (frequencies <= hi))]))
            for name, (lo, hi) in zip(BAND_NAMES, BANDS)}


def reference(seed, noise):
    """Main's exact 5 s + one-hop generation; no P.run / evaluation invocation."""
    n, neval = 40128, 40000
    if noise == 'ar1':
        x = colored_noise(n, np.random.default_rng(seed), pole=.95)
        x = x / np.std(x[:neval])
        f = np.fft.rfftfreq(NFFT, 1 / FS)
        density = (1 - .95 ** 2) / np.abs(1 - .95 * np.exp(-2j * np.pi * f / FS)) ** 2
        weights = density * symmetry(NFFT) / NFFT
    elif noise == 'harmonic':
        g = np.random.default_rng(seed + 777001)
        t = np.arange(n) / FS
        phase = g.uniform(0, 2 * np.pi, 40)
        xh = sum(np.cos(2 * np.pi * 40 * (k + 1) * t + phase[k]) / np.sqrt(k + 1) for k in range(40))
        xb = lfilter([1.], [1., -.9], g.standard_normal(n))
        x = xh / np.std(xh) + 10 ** (-10 / 20) * xb / np.std(xb)
        x = x / np.std(x[:neval])
        f = np.fft.rfftfreq(NFFT, 1 / FS)
        density = .1 / np.var(xb) / np.abs(1 - .9 * np.exp(-2j * np.pi * f / FS)) ** 2
        weights = density * symmetry(NFFT) / NFFT
        for k in range(1, 41):
            weights[int(k * 40 * NFFT / FS)] += 1 / (2 * k * np.var(xh))
    else:
        raise ValueError(noise)
    # Infinite-time, unit-variance stationary counterpart of the main reference.
    weights /= weights.sum()
    return x, weights


def reference_band_ratios(x):
    x = x[:40000]
    power = np.abs(np.fft.rfft(x)) ** 2 * symmetry(len(x)) / len(x) ** 2
    return {k: v / power.sum() for k, v in band_sums(power, np.fft.rfftfreq(len(x), 1 / FS)).items()}


def path_bands(h):
    power = np.abs(np.fft.rfft(h, NFFT)) ** 2 * symmetry(NFFT) / NFFT
    energy = band_sums(power, np.fft.rfftfreq(NFFT, 1 / FS))
    return {'energy': energy, 'fraction': {k: v / power.sum() for k, v in energy.items()},
            'total_energy': float(power.sum())}


def wiener(p, model_s, weights, length=M):
    nfft = 2 * (len(weights) - 1)
    pfft, sfft = np.fft.rfft(p, nfft), np.fft.rfft(model_s, nfft)
    density = weights * nfft / symmetry(nfft)
    cov = np.fft.irfft(density * np.abs(sfft) ** 2, nfft)[:length]
    cross = np.fft.irfft(density * np.conj(sfft) * pfft, nfft)[:length]
    matrix = toeplitz(cov)
    w = cho_solve(cho_factor(matrix, lower=True), -cross)
    relative_gradient = float(np.linalg.norm(matrix @ w + cross) / max(np.linalg.norm(cross), 1e-300))
    if not np.isfinite(w).all() or relative_gradient > 1e-7:
        raise ValueError(f'Unverified Wiener solve: relative gradient {relative_gradient}')
    return w, relative_gradient


def controller_power(p, true_s, w, weights):
    nfft = 2 * (len(weights) - 1)
    residual = np.fft.rfft(p, nfft) + np.fft.rfft(true_s, nfft) * np.fft.rfft(w, nfft)
    return float(np.sum(weights * np.abs(residual) ** 2))


def bound(p, s, model_s, weights, sensor_power):
    w, gradient = wiener(p, model_s, weights)
    pd = float(np.sum(weights * np.abs(np.fft.rfft(p, NFFT)) ** 2))
    residual = controller_power(p, s, w, weights)
    model_residual = controller_power(p, model_s, w, weights)
    nr = lambda r, noise: float(10 * np.log10(max(r + noise, np.finfo(float).tiny) / (pd + noise)))
    return {'total_nr_db': nr(residual, sensor_power), 'anc_only_nr_db': nr(residual, 0.),
            'model_objective_anc_nr_db': nr(model_residual, 0.), 'controller_norm': float(np.linalg.norm(w)),
            'exceeds_simulator_norm_limit_1000': bool(np.linalg.norm(w) > 1000),
            'normal_equation_relative_gradient': gradient,
            'disturbance_power': pd, 'anc_residual_power': residual, 'sensor_power': sensor_power}


def seed_diagnosis(seed, meshrir_d0=0):
    cfg = dict(sample_rate=FS, len_p=1200, len_s=512, move_steps=0)
    if meshrir_d0:
        cfg['meshrir_d0'] = meshrir_d0
    p, s, p2, _ = meshrir_paths(dict(cfg, move_target='source'), seed)
    pm, sm, pm2, sm2 = meshrir_paths(dict(cfg, move_target='mic'), seed)
    assert np.array_equal(p, pm) and np.array_equal(s, sm)
    states = {'meas_p': {'before': (p, s), 'after': (p2, s)},
              'meas_ps': {'before': (p, s), 'after': (pm2, sm2)}}
    references = {nz: reference(seed, nz) for nz in ('ar1', 'harmonic')}
    result = {'seed': seed, 'ar1_band_energy_ratio': reference_band_ratios(references['ar1'][0]),
              'reference_sha256': {nz: hashlib.sha256(x[:40000].tobytes()).hexdigest() for nz, (x, _) in references.items()},
              'scenarios': {}}
    for scenario, stages in states.items():
        result['scenarios'][scenario] = {}
        for stage, (pp, ss) in stages.items():
            rec = {'P_bands': path_bands(pp), 'S_bands': path_bands(ss), 'noise': {}}
            for nz, (x, weights) in references.items():
                # Same constant sensor variance used by main: 20 dB vs initial P over the 5 s reference.
                d0 = np.convolve(x, p)[:40000]
                sensor = float(np.mean(d0 ** 2)) / 100
                rec['noise'][nz] = {'true_s_causal_wiener_bound': bound(pp, ss, ss, weights, sensor)}
                if scenario == 'meas_ps' and stage == 'after':
                    rec['noise'][nz]['frozen_shat_design_actual_residual_not_bound'] = bound(pp, ss, s, weights, sensor)
            result['scenarios'][scenario][stage] = rec
    return result


def input_hashes():
    return {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest()
            for scenario in ('meas_p', 'meas_ps')
            for p in sorted((ROOT / f'results/final_eval_{scenario}').rglob('*')) if p.is_file()}


def prechange():
    out = {}
    for scenario in ('meas_p', 'meas_ps'):
        out[scenario] = {}
        for line in (ROOT / f'results/final_eval_{scenario}/runs_full.jsonl').read_text().splitlines():
            r = json.loads(line)
            if r['method'] not in ('RLS + det', 'E-PCG'):
                continue
            key = f"{r['seed']}|{r['noise']}|{r['method']}"
            if len(r['tp']) < 62:
                out[scenario][key] = None
            else:
                out[scenario][key] = float(10 * np.log10(np.sum(r['tp'][30:62]) / np.sum(r['up'][30:62])))
    return out


def q(values):
    a = np.asarray([x for x in values if x is not None], float)
    return 'NA (n=0)' if not len(a) else f'{np.median(a):.3f} ({np.quantile(a,.25):.3f}, {np.quantile(a,.75):.3f}); n={len(a)}'


def summary(rows, pre):
    lines = ['# Revision 8: 実測経路の制御可能性診断', '',
             'MeshRIR v1.1 S32-M441、DOI 10.5281/zenodo.5500451、CC BY 4.0。',
             'Attribution: Shoichi Koyama, Tomoya Nishida, Keisuke Kimura, Takumi Abe, Natsuki Ueno, Jesper Brunnström。',
             '全表は評価シード480–519の中央値 (Q1, Q3)。既存評価・設定・ルールは変更せず、適応制御の再実行なし。', '',
             '## 定義', '',
             '- M=512の因果・実係数Wiener解。主雑音の定常スペクトルを0.1 Hz格子で積分。AR(1)はpole=0.95、harmonicは40 Hzの1–40倍音とpole=0.9の背景雑音（mainと同じ生成・混合比）。',
             '- mainと同じ40128点生成・評価先頭40000点の正規化を使用。harmonicの成分正規化も同じ。定常期待値では位相を時間平均し、初期過渡は含めない。',
             '- センサ雑音の分散はmain同様、初期Pによる5秒の平均擾乱電力/100に固定。total NRはこれを含む。ANC-onlyは雑音を除く。',
             '- 真Sによる値が物理的な下限。Ŝ固定自体は許容制御器集合を変えないため物理下限も変えない。「古いŜでWiener設計→真の変化後Sで評価」はモデル誤差診断値であり、下限ではない。特定適応法の固定点や性能保証でもない。',
             '- 制御器ノルム・出力振幅への制約は置かない。ノルムが既存シミュレータ上限1000を超える解もper_seed.jsonに明記する。', '',
             '## 定常NR（dB）', '',
             '| set | 経路 | 雑音 | true S: total下限 | true S: ANC-only下限 | 古いŜ設計: 実total残差（下限ではない） |',
             '|---|---|---|---|---|---|']
    for sc in ('meas_p', 'meas_ps'):
        for stage in ('before', 'after'):
            for nz in ('ar1', 'harmonic'):
                records = [r['scenarios'][sc][stage]['noise'][nz] for r in rows]
                mismatch = [r['frozen_shat_design_actual_residual_not_bound']['total_nr_db'] for r in records if 'frozen_shat_design_actual_residual_not_bound' in r]
                lines.append(f"| {sc} | {stage} | {nz} | {q([r['true_s_causal_wiener_bound']['total_nr_db'] for r in records])} | {q([r['true_s_causal_wiener_bound']['anc_only_nr_db'] for r in records])} | {q(mismatch)} |")
    for quantity, title in (('energy', 'P/S振幅特性の帯域別エネルギー（Parseval、絶対値）'), ('fraction', 'P/S帯域エネルギー比')):
        lines += ['', f'## {title}', '', '| set | 経路 | filter | ' + ' | '.join(BAND_NAMES) + ' |', '|---|---|---|---|---|---|---|']
        for sc in ('meas_p', 'meas_ps'):
            for stage in ('before', 'after'):
                for h in ('P', 'S'):
                    lines.append(f'| {sc} | {stage} | {h} | ' + ' | '.join(q([r['scenarios'][sc][stage][h+'_bands'][quantity][b] for r in rows]) for b in BAND_NAMES) + ' |')
    lines += ['', '## main生成AR(1)雑音の帯域エネルギー比', '',
              '先頭40000点の片側periodogramによる比率（DCを含む）。帯域は左閉右開、最終帯域のみ4 kHzを含む。', '',
              '| ' + ' | '.join(BAND_NAMES) + ' |', '|---|---|---|---|',
              '| ' + ' | '.join(q([r['ar1_band_energy_ratio'][b] for r in rows]) for b in BAND_NAMES) + ' |', '',
              '## 変化前の既存ログNR（dB）', '',
              'hop 31–62を1始まりとして解釈：Python [30:62]、0.480–0.992秒。0始まりのhop 62は変化時刻1秒をまたぐため含めない。',
              '失敗ペナルティで置換せず、この区間の実際の電力和から計算。区間未完了はNAとしてnを明記。', '',
              '| set | 雑音 | RLS + det | E-PCG |', '|---|---|---|---|']
    for sc in ('meas_p', 'meas_ps'):
        for nz in ('ar1', 'harmonic'):
            lines.append(f'| {sc} | {nz} | ' + ' | '.join(q([pre[sc][f"{r['seed']}|{nz}|{method}"] for r in rows]) for method in ('RLS + det', 'E-PCG')) + ' |')
    return '\n'.join(lines) + '\n'


def main():
    global OUT
    parser = argparse.ArgumentParser()
    parser.add_argument('--rule8a', action='store_true', help='Use the approved common delay 5434; write revision8a_diag')
    args = parser.parse_args()
    meshrir_d0 = 5434 if args.rule8a else 0
    if args.rule8a:
        OUT = ROOT / 'results/revision8a_diag'
    if OUT.exists():
        raise FileExistsError(f'Refusing to overwrite {OUT}')
    before = input_hashes()
    pre = prechange()
    with ProcessPoolExecutor(max_workers=2) as pool:
        rows = list(pool.map(partial(seed_diagnosis, meshrir_d0=meshrir_d0), range(480, 520)))
    assert input_hashes() == before, 'Existing evaluation files changed'
    for r in rows:
        r['prechange_nr_db'] = {sc: {nz: {method: pre[sc][f"{r['seed']}|{nz}|{method}"] for method in ('RLS + det', 'E-PCG')} for nz in ('ar1', 'harmonic')} for sc in ('meas_p', 'meas_ps')}
    meta = {'diagnostic_only': True, 'no_adaptive_runs': True, 'seeds': list(range(480, 520)),
            'controller_length': M, 'spectral_integration_fft_length': NFFT, 'sample_rate': FS,
            'source_commit': subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip(),
            'script_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            'license': 'CC BY 4.0', 'dataset_doi': '10.5281/zenodo.5500451', 'archive_md5': ARCHIVE_MD5,
            'existing_evaluation_file_sha256': before, 'existing_evaluation_files_unchanged': True,
            'prechange_hops': {'one_based_inclusive': [31, 62], 'python_slice': [30, 62]},
            'fixed_shat_result_is_not_a_physical_lower_bound': True}
    if args.rule8a:
        meta.update(meshrir_d0_48k=meshrir_d0,
                    rule_sha256=hashlib.sha256((ROOT / 'docs/current/REVISION_RULE_8a.md').read_bytes()).hexdigest(),
                    prechange_logs_are_invalid_rule8_historical_reference_only=True)
    OUT.mkdir(parents=True)
    (OUT / 'per_seed.json').write_text(json.dumps({'metadata': meta, 'seeds': rows}, indent=2) + '\n')
    text = summary(rows, pre)
    if args.rule8a:
        text = text.replace('# Revision 8:', '# Revision 8a:', 1)
        text = text.replace('## 変化前の既存ログNR（dB）', '## 旧Rule 8の変化前ログNR（無効な旧前処理の履歴参照のみ、Rule 8aの性能ではない）')
        text += ('\n共通除去は5434サンプル（48 kHz）、前処理以外の計算は従来と同一。'
                 '旧Rule 8結果は直接音欠落の不具合により無効として保持。'
                 'Rule 8aは旧結果を見た後の不具合修正であり、再チューニングなし。\n')
    (OUT / 'summary.md').write_text(text)
    print(f'Wrote {OUT}: 40 seeds, two workers; all existing evaluation hashes unchanged', flush=True)


if __name__ == '__main__':
    main()
