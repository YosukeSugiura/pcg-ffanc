"""Runtime guards for expensive benchmark / optimization runs.

The sample-wise conventional kernels (VSS2, SSS and their AD variants) are
written so that Numba can compile them.  Without Numba they silently fall back
to pure Python, which was measured to be roughly two orders of magnitude slower
(0.5 s of signal: VSS2 0.77 s, SSS 4.9 s in pure Python versus a few ms with
Numba).  A full Optuna sweep then appears to hang.  These helpers make that
condition explicit and provide a runtime estimate before a sweep starts.
"""
from __future__ import annotations

from dataclasses import dataclass
import importlib.util
import warnings


def numba_available() -> bool:
    """Return True when Numba can be imported."""
    return importlib.util.find_spec("numba") is not None


def ensure_compiled_kernels(allow_python_fallback: bool, context: str) -> bool:
    """Require Numba for an expensive run, or warn loudly when falling back.

    Returns True when compiled kernels are available.  When Numba is missing,
    raises ``RuntimeError`` unless ``allow_python_fallback`` is set, in which
    case a ``RuntimeWarning`` is emitted and False is returned.
    """
    if numba_available():
        return True
    msg = (
        f"{context}: Numba is not installed, so the sample-wise conventional "
        "kernels run in pure Python (about 100-300x slower). A full sweep can "
        "take hours and look like a hang. Install it with "
        "`pip install -e \".[opt]\"`"
    )
    if not allow_python_fallback:
        raise RuntimeError(msg + " or pass --allow-python-fallback explicitly.")
    warnings.warn(msg + ".", RuntimeWarning, stacklevel=2)
    return False


@dataclass(frozen=True)
class RunCount:
    """Number of simulated signal-seconds a method needs in one benchmark."""

    method: str
    signal_seconds: float


def estimate_total_seconds(
    seconds_per_signal_second: dict[str, float],
    plan: list[RunCount],
) -> dict[str, float]:
    """Combine calibrated per-signal-second costs with a run plan.

    Returns per-method wall-clock estimates plus ``"total"``.
    """
    out: dict[str, float] = {}
    for item in plan:
        if item.signal_seconds < 0.0:
            raise ValueError("signal_seconds must be nonnegative")
        if item.method not in seconds_per_signal_second:
            raise KeyError(f"no calibration for method {item.method!r}")
        cost = float(seconds_per_signal_second[item.method]) * float(item.signal_seconds)
        out[item.method] = out.get(item.method, 0.0) + cost
    out["total"] = float(sum(v for k, v in out.items() if k != "total"))
    return out


def format_duration(seconds: float) -> str:
    seconds = float(seconds)
    if seconds < 120.0:
        return f"{seconds:.1f} s"
    if seconds < 7200.0:
        return f"{seconds / 60.0:.1f} min"
    return f"{seconds / 3600.0:.2f} h"
