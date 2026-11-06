import importlib.util, sys, os, struct, subprocess, tempfile
import numpy as np
sys.path[:0]=[os.path.abspath('experiments'),os.path.abspath('src')]
import eval_v2 as ev
base_source = subprocess.check_output(['git', 'show', '4602b0c4:experiments/prototype_new_algorithms.py'])
tmp = tempfile.NamedTemporaryFile(suffix='.py')
tmp.write(base_source); tmp.flush()
spec=importlib.util.spec_from_file_location('base_prototype',tmp.name)
base=importlib.util.module_from_spec(spec); sys.modules[spec.name]=base; spec.loader.exec_module(base)
new=ev.D.P
sel=__import__('json').load(open('results/protocol_v2_sel/selected_e.json'))['selected']
items=[(m,ev.GRID[m][0],ev.GRID[m][1][i]) for m,i in sel.items()] + [('E-PCG','PCG-WLS-F',ev.MAIN),('E-PCG bank','PCG-WLS-F',ev.BANK)]
cfg=ev.cfg_of('A','ar1','S2 src 30cm'); events=ev.events('A','ar1','S2 src 30cm',300)
def same(a,b,path=''):
 if isinstance(a,dict):
  if a.keys()!=b.keys(): raise AssertionError((path,'keys'))
  for k in a:
   if k not in ('wall_s','elapsed','time'): same(a[k],b[k],path+'/'+str(k))
 elif isinstance(a,(list,tuple)):
  if len(a)!=len(b): raise AssertionError((path,'len'))
  for i,(x,y) in enumerate(zip(a,b)): same(x,y,path+'/'+str(i))
 elif isinstance(a,np.ndarray):
  if a.dtype != b.dtype or a.shape != b.shape or a.tobytes() != b.tobytes(): raise AssertionError((path,'array'))
 elif isinstance(a,(float,np.floating)):
  if struct.pack('d',float(a)) != struct.pack('d',float(b)): raise AssertionError((path,a,b))
 elif a!=b: raise AssertionError((path,a,b))
for name,method,prm in items:
 p=dict(prm)
 if name in ev.DET: p['det_events']=events
 a=base.run(cfg,300,method,p,5.0,ev.D.CH); b=new.run(cfg,300,method,p,5.0,ev.D.CH)
 same(a,b,name)
 print('PASS',name,flush=True)
