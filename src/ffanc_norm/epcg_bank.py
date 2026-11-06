"""Deprecated alias of :mod:`ffanc_norm.pcg_wls_mw`.

The multi-window variant was called E-PCG (bank) before v1.1.0 and is called PCG-WLS (multi-window) from v1.1.0.
This module keeps the former import path and class name working: ``EPCGBank`` is ``PcgWlsMultiWindow`` (the same
object). Importing it emits a DeprecationWarning.
"""
import warnings

from .pcg_wls import CMUL, FFTCounter, PcgWls, PcgWlsConfig  # noqa: F401
from .pcg_wls_mw import PcgWlsMultiWindow, _CfgProxy, _FDExpert, _SumCounter  # noqa: F401

warnings.warn("ffanc_norm.epcg_bank is deprecated: E-PCG (bank) was renamed PCG-WLS (multi-window) in v1.1.0. "
              "Use ffanc_norm.pcg_wls_mw (PcgWlsMultiWindow).", DeprecationWarning, stacklevel=2)

EPCGBank = PcgWlsMultiWindow
EPCG = PcgWls
EPCGConfig = PcgWlsConfig

__all__ = ["EPCGBank", "EPCG", "EPCGConfig", "PcgWlsMultiWindow", "PcgWls", "PcgWlsConfig", "FFTCounter", "CMUL"]
