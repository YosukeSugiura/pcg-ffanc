"""Ordered, fail-stop Revision 11 job supervisor (Rule 11 Sec. 8). No scientific setting is chosen here.

Each job = two single-threaded worker processes (SHARD 0/2, 1/2) under one `setsid nohup` bash script, logs in the
output directory; the job is resumable (workers skip existing records). After a job: summary. Git operations are
opt-in (public release): with R11_GIT=1 the output directory is added and committed with the caller's own git
configuration (message trailer from R11_TRAILER, if set); with R11_PUSH=<remote> the commit is also pushed to
R11_BRANCH. Without R11_GIT nothing is committed or pushed.

Start it detached and monitor the log and the status flags (2026-11-07 review M-5):
  python3 experiments/revision11_pipeline.py start <job args>      # setsid nohup itself, returns at once
      log     results/r11_pipeline/<job>.log   (append; 'DONE' or 'STOP:' at the end)
      flags   results/r11_pipeline/<job>.running (pid) -> <job>.done (finished) | <job>.stop (stopped)
  Re-running the same start command resumes the job (workers skip complete records, drop a cut last line).
  One pipeline at a time (lock results/r11_pipeline/lock); each job first checks the software environment of
  Rule 11 Sec. 1.2 with the worker interpreter PY (A: path-A room-A holdout; C: everything else; meas: + numba,
  soundfile) and stops if it differs (review M-3).
<job args> (foreground form: python experiments/revision11_pipeline.py <job args>):
  python experiments/revision11_pipeline.py select B1|B2|C          # tuning stage (environment C), repeated to the end
  python experiments/revision11_pipeline.py holdout ablation|new     # room-A holdout (environment A; PY=<venv python>)
  R11_HOLDOUT_BASE=envC python experiments/revision11_pipeline.py holdout base|ablation|new   # Sec. 9 item 8 (b)
  python experiments/revision11_pipeline.py rooms roomB|roomC|snr10  # 11-D (environment C)
  python experiments/revision11_pipeline.py meas meas_s|meas_p       # 11-D measured (environment C, MeshRIR)
  options: PY=/path/to/python (default: this interpreter); ROWS=... (holdout new: subset of the selected rows);
           R11_GIT=1 (commit the outputs with your git configuration; default: no git operation);
           R11_PUSH=<remote> (with R11_GIT=1: also push); R11_BRANCH (push target, default r11-run)
"""
import fcntl
import os
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
os.chdir(ROOT)
os.environ.update(RLS_FAST='1', OPENBLAS_NUM_THREADS='1', MKL_NUM_THREADS='1', OMP_NUM_THREADS='1')
PY = os.environ.get('PY', sys.executable)


def log(*a):
    print(time.strftime('%Y-%m-%dT%H:%M:%S%z'), *a, flush=True)


def sh(*args):
    log('run', *args)
    subprocess.run(args, check=True)


def job(label, out, worker):
    """Two shards of `worker` (a shell command without SHARD) in one setsid / nohup job; stop on any failure."""
    out.mkdir(parents=True, exist_ok=True)
    script = Path('/tmp') / f'revision11_{label}_job.sh'
    script.write_text(f'''#!/bin/bash
set -u
cd {ROOT}
export RLS_FAST=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 OMP_NUM_THREADS=1
export PRA_NUM_THREADS={os.environ['PRA_NUM_THREADS']}
SHARD=0/2 {worker} >> {out}/worker_{label}_0.log 2>&1 & p0=$!
SHARD=1/2 {worker} >> {out}/worker_{label}_1.log 2>&1 & p1=$!
wait -n -p first "$p0" "$p1"; rc=$?
if test "$rc" -ne 0; then kill "$p0" "$p1" 2>/dev/null || true; wait "$p0" 2>/dev/null || true; wait "$p1" 2>/dev/null || true; exit "$rc"; fi
if test "$first" = "$p0"; then wait "$p1"; rc=$?; else wait "$p0"; rc=$?; fi
exit "$rc"
''')
    with (out / f'job_{label}.log').open('a') as fh:
        p = subprocess.Popen(['setsid', 'nohup', 'bash', str(script)], stdin=subprocess.DEVNULL, stdout=fh,
                             stderr=subprocess.STDOUT)
        log('started', label, 'pid', p.pid)
        rc = p.wait()
    if rc:
        raise RuntimeError(f'{label} failed (exit {rc}); see {out}/worker_{label}_*.log')
    log('completed', label)


def git_enabled():
    """Commit only if R11_GIT=1 (opt-in in the public release; the development runs committed every job)."""
    return os.environ.get('R11_GIT') == '1' and not os.environ.get('NO_GIT')


def commit(msg, *paths):
    if not git_enabled():
        return
    log_file = PIPE / f'{job_name(sys.argv[1:])}.log'
    if log_file.exists():                                 # the pipeline log so far (the rest goes with the next job)
        paths += (str(log_file.relative_to(ROOT)),)
    sh('git', 'add', *paths)
    if subprocess.run(['git', 'diff', '--cached', '--quiet']).returncode == 0:
        log('nothing to commit'); return
    trailer = os.environ.get('R11_TRAILER', '')
    sh('git', 'commit', '-m', msg + ('\n\n' + trailer if trailer else ''))      # the caller's git user
    remote = os.environ.get('R11_PUSH')
    if remote:
        sh('git', 'push', remote, 'HEAD:refs/heads/' + os.environ.get('R11_BRANCH', 'r11-run'))


PIPE = ROOT / 'results/r11_pipeline'


def job_name(argv):
    envc = argv[0] == 'holdout' and os.environ.get('R11_HOLDOUT_BASE') == 'envC'
    return '_'.join(argv[:2]) + ('_envC' if envc else '')


PRA_THREADS = {'A': '3', 'C': '2'}          # Rule 11b Sec. 3 (= revision11_methods.ENVS[...]['pra_threads'])


def check_env(env, meas=False):
    """Rule 11 / 11a fixed texts (Rule 11a Sec. 3.3 c1, c8), the holdout base against env_A.json (c5, review N-M1)
    and the Rule 11 Sec. 1.2 environment of the worker interpreter PY (review M-3); raises on a mismatch, so the job
    does not start."""
    os.environ['PRA_NUM_THREADS'] = PRA_THREADS[env]     # inherited by every later step and the worker script
    sh(PY, 'experiments/revision11_methods.py', 'check-env', env, *(['meas'] if meas else []), 'job')


def select(stage):
    out = ROOT / 'results/protocol_r11_sel'
    check_env('C')
    sh(PY, 'experiments/revision11_select.py', 'provenance', stage)
    if stage in ('B2', 'C'):                              # Rule 11b Sec. 4 (c): stage E0 (runs only in class K)
        job(f'sel_E0_{stage}', out, f'{PY} experiments/revision11_select.py run E0')
    for it in range(4):                                   # base grid, then at most two extension rounds (+1 spare)
        wl = [out / f'worker_sel_{stage}_{it}_{s}.log' for s in (0, 1)]
        size = [f.stat().st_size if f.exists() else 0 for f in wl]   # only this start's lines (logs are appended)
        job(f'sel_{stage}_{it}', out, f'{PY} experiments/revision11_select.py run {stage}')
        logs = [f.read_bytes()[n:].decode(errors='replace') for f, n in zip(wl, size)]
        sh(PY, 'experiments/revision11_select.py', 'summary')
        if all(f'{stage}: nothing to run' in t for t in logs):
            break
    else:
        raise RuntimeError(f'{stage}: still configurations to run after 4 rounds')
    import json
    for x in json.loads((out / 'selected.json').read_text()).get('inadmissible', []):   # Rule 11a Sec. 4: report, go on
        log('NOTE: no admissible configuration:', x['group'], '-', x['reason'], '(reported, not evaluated)')
    commit(f'Rule 11 tuning stage {stage}', 'results/protocol_r11_sel')


def holdout(kind):
    envc = os.environ.get('R11_HOLDOUT_BASE') == 'envC'
    out = ROOT / ({'ablation': 'results/r11_ablation_holdout_envC', 'new': 'results/final_eval_holdout_r11_envC_new',
                   'base': 'results/final_eval_holdout_r11_envC'} if envc else
                  {'ablation': 'results/r11_ablation_holdout', 'new': 'results/final_eval_holdout_r11'})[kind]
    check_env('C' if envc else 'A')
    sh(PY, 'experiments/revision11_holdout.py', 'provenance', kind)
    job(f'hold_{kind}', out, f'{PY} experiments/revision11_holdout.py run {kind}')
    if not os.environ.get('ROWS') and not os.environ.get('VARIANTS'):
        sh(PY, 'experiments/revision11_summary.py', kind)
    commit(f'Rule 11 room-A holdout ({kind})', str(out.relative_to(ROOT)))


def rooms(name):
    out = ROOT / {'roomB': 'results/eval_roomB_h', 'roomC': 'results/eval_roomC_h', 'snr10': 'results/eval_snr10_h'}[name]
    check_env('C')
    sh(PY, 'experiments/revision11_rooms.py', 'provenance', name)
    job(f'rooms_{name}', out, f'{PY} experiments/revision11_rooms.py run {name}')
    sh(PY, 'experiments/revision11_rooms.py', 'fill', name)
    sh(PY, 'experiments/revision11_summary.py', 'rooms', name)
    commit(f'Rule 11-D {name} holdout', str(out.relative_to(ROOT)))


def meas(name):
    out = ROOT / {'meas_s': 'results/final_eval_meas_s_h', 'meas_p': 'results/final_eval_meas_p_h'}[name]
    check_env('C', meas=True)
    sh(PY, 'experiments/revision11_meas.py', 'prepare')
    sh(PY, 'experiments/revision11_meas.py', 'provenance', name)
    job(f'meas_{name}', out, f'{PY} experiments/revision11_meas.py run {name}')
    sh(PY, 'experiments/revision11_meas.py', 'validate', name)
    if name == 'meas_s':
        sh(PY, 'experiments/revision11_meas.py', 'bounds')
    sh(PY, 'experiments/revision11_summary.py', 'meas', name)
    commit(f'Rule 11-D {name} holdout', str(out.relative_to(ROOT)), 'results/r11_preflight/meshrir_holdout_allocation.json')


def refused(name, why):
    """A start refused by the lock: log STOP and leave <name>.stop (review N-L4), unless that same job is the one
    holding the lock (its own flags stay authoritative)."""
    log('STOP:', why)
    if not (PIPE / f'{name}.running').exists():
        (PIPE / f'{name}.stop').write_text(time.strftime('%Y-%m-%dT%H:%M:%S%z') + ' refused: ' + why + '\n')


def start(argv):
    """Launch this pipeline detached (setsid nohup) with its log in results/r11_pipeline/<job>.log; returns at once."""
    if len(argv) != 2 or argv[0] not in JOBS:
        raise SystemExit(__doc__)
    PIPE.mkdir(parents=True, exist_ok=True)
    name = job_name(argv)
    with (PIPE / 'lock').open('a') as lk:                  # refuse while another pipeline holds the lock
        try:
            fcntl.flock(lk, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            refused(name, 'another revision11 pipeline is running (results/r11_pipeline/lock); wait for it')
            raise SystemExit(2)
        fcntl.flock(lk, fcntl.LOCK_UN)
    with (PIPE / f'{name}.log').open('a') as fh:
        p = subprocess.Popen(['setsid', 'nohup', sys.executable, str(Path(__file__).resolve()), *argv],
                             stdin=subprocess.DEVNULL, stdout=fh, stderr=subprocess.STDOUT)
    print(f'started {name} (pid {p.pid})\n  log:   results/r11_pipeline/{name}.log\n'
          f'  flags: results/r11_pipeline/{name}.running -> .done | .stop', flush=True)


JOBS = {'select': select, 'holdout': holdout, 'rooms': rooms, 'meas': meas}


def main(argv):
    PIPE.mkdir(parents=True, exist_ok=True)
    name = job_name(argv)
    lk = (PIPE / 'lock').open('a')
    try:
        fcntl.flock(lk, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError:
        refused(name, 'another revision11 pipeline is running (results/r11_pipeline/lock); wait for it')
        raise SystemExit(2)
    for suffix in ('done', 'stop'):
        (PIPE / f'{name}.{suffix}').unlink(missing_ok=True)
    (PIPE / f'{name}.running').write_text(f'{os.getpid()}\n')
    try:
        JOBS[argv[0]](argv[1])
    except BaseException as exc:
        import traceback
        traceback.print_exc()
        log('STOP:', repr(exc))
        (PIPE / f'{name}.stop').write_text(time.strftime('%Y-%m-%dT%H:%M:%S%z') + ' ' + repr(exc) + '\n')
        raise
    finally:
        (PIPE / f'{name}.running').unlink(missing_ok=True)
    log('DONE', *argv)
    (PIPE / f'{name}.done').write_text(time.strftime('%Y-%m-%dT%H:%M:%S%z') + ' ' + subprocess.check_output(
        ['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True))


if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] == 'start':
        start(sys.argv[2:])
    else:
        main(sys.argv[1:])
