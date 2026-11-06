"""Deprecated alias of :mod:`ffanc_norm.pcg_wls`.

The method was called E-PCG before v1.1.0 and is called PCG-WLS from v1.1.0. This module keeps the former import
path and class names working: ``EPCG`` is ``PcgWls`` and ``EPCGConfig`` is ``PcgWlsConfig`` (the same objects).
Importing it emits a DeprecationWarning.
"""
import warnings

from .pcg_wls import CADD, CMUL, FFTCounter, PcgWls, PcgWlsConfig, fft_flops  # noqa: F401

warnings.warn("ffanc_norm.epcg is deprecated: E-PCG was renamed PCG-WLS in v1.1.0. "
              "Use ffanc_norm.pcg_wls (PcgWls, PcgWlsConfig).", DeprecationWarning, stacklevel=2)

EPCG = PcgWls
EPCGConfig = PcgWlsConfig

__all__ = ["EPCG", "EPCGConfig", "PcgWls", "PcgWlsConfig", "FFTCounter", "fft_flops", "CMUL", "CADD"]
