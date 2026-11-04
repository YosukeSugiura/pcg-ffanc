"""Redraw stored-data figures with a Times-compatible font; no simulations.

The eigenvalue figure is intentionally excluded: its original generator reruns
signal generation. It remains in figs/ until its underlying histogram is available.
"""
from pathlib import Path
import matplotlib.font_manager as fm
import make_figures as figures

font_dir = Path('/usr/share/fonts/truetype/liberation')
for name in ('LiberationSerif-Regular.ttf', 'LiberationSerif-Bold.ttf',
             'LiberationSerif-Italic.ttf', 'LiberationSerif-BoldItalic.ttf'):
    fm.fontManager.addfont(str(font_dir / name))
figures.plt.rcParams.update({'font.family': 'Liberation Serif', 'mathtext.fontset': 'custom',
    'mathtext.rm': 'Liberation Serif', 'mathtext.it': 'Liberation Serif:italic',
    'mathtext.bf': 'Liberation Serif:bold', 'pdf.fonttype': 42})
figures.OUT = Path(__file__).resolve().parent / 'figs_times'
figures.OUT.mkdir(exist_ok=True)
for name in ('excess', 'cost', 'shat'):
    getattr(figures, 'fig_' + name)()
    print('redrawn from stored data:', name, flush=True)
