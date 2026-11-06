"""Former names (E-PCG, before v1.1.0) still work and emit a DeprecationWarning; archived configurations are read
unchanged and mapped to the current method key."""
import hashlib
import json
import sys
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src')); sys.path.insert(0, str(ROOT / 'experiments'))
from ffanc_norm import cost, naming  # noqa: E402
from ffanc_norm.pcg_wls import PcgWls, PcgWlsConfig  # noqa: E402
from ffanc_norm.pcg_wls_mw import PcgWlsMultiWindow  # noqa: E402


def _fresh(name):
    sys.modules.pop(name, None)
    pkg = sys.modules['ffanc_norm']
    if hasattr(pkg, name.rsplit('.', 1)[1]):
        delattr(pkg, name.rsplit('.', 1)[1])


def test_former_imports_warn_and_alias_the_new_classes():
    _fresh('ffanc_norm.epcg')
    with pytest.warns(DeprecationWarning, match='pcg_wls'):
        from ffanc_norm.epcg import EPCG, EPCGConfig
    assert EPCG is PcgWls and EPCGConfig is PcgWlsConfig
    _fresh('ffanc_norm.epcg_bank')
    with pytest.warns(DeprecationWarning, match='pcg_wls_mw'):
        from ffanc_norm.epcg_bank import EPCGBank
    assert EPCGBank is PcgWlsMultiWindow
    with pytest.warns(DeprecationWarning, match='pcg_wls_model'):
        old = cost.epcg_model(512, 256, 16, 4)
    assert old == cost.pcg_wls_model(512, 256, 16, 4)


def test_former_method_key_and_archived_config():
    with pytest.warns(DeprecationWarning, match='PCG-WLS-F'):
        assert naming.method_key('E-PCG-F') == 'PCG-WLS-F'
    assert naming.method_key('RLS') == 'RLS'
    path = ROOT / 'results/final_dev/final_config_core_main.json'
    before = hashlib.sha256(path.read_bytes()).hexdigest()
    raw = json.loads(path.read_text())
    cfg = naming.load_config(path)
    assert raw['method'] == 'E-PCG-F' and cfg['method'] == 'PCG-WLS-F' and cfg['flags'] == raw['flags']
    assert hashlib.sha256(path.read_bytes()).hexdigest() == before
    assert naming.display_label('E-PCG bank') == 'PCG-WLS (multi-window)'
    assert naming.display_text('E-PCG minus baselines; E-PCG (bank)') == 'PCG-WLS minus baselines; PCG-WLS (multi-window)'


def test_runner_accepts_the_former_key_with_identical_output():
    import prototype_new_algorithms as P
    cfg = json.loads((ROOT / 'configs/random_decay.json').read_text())
    flags = naming.load_config(ROOT / 'results/final_dev/final_config_core_main.json')['flags']
    new = P.run(cfg, 100, 'PCG-WLS-F', dict(flags), 0.5, None)
    with pytest.warns(DeprecationWarning):
        old = P.run(cfg, 100, 'E-PCG-F', dict(flags), 0.5, None)
    assert np.array_equal(np.asarray(new['total_power']), np.asarray(old['total_power']))
