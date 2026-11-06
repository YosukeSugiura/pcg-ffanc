"""Observe existing PcgWls history references without changing the implementation."""
import argparse
from contextlib import contextmanager
import hashlib
import gzip
import json
import os
from pathlib import Path
import platform
import subprocess
import sys
import weakref
import numpy as np

ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'experiments'),str(ROOT/'src')]
CELLS=('S8 stationary','S1 src 10cm','S2 src 30cm','S5 src 30cm cont',
       'S7 rd abrupt','R1 rig 10cm','R2 rig 30cm','R3 rig 30cm cont')
COMBOS=tuple((nz,sc) for nz in ('ar1','harmonic') for sc in CELLS
             if (nz,sc)!=('harmonic','S7 rd abrupt'))


def file_sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()


def immutable_json(path, value):
    with path.open('x') as fh:
        json.dump(value,fh,indent=2,allow_nan=False);fh.write('\n')


def runtime_info():
    import scipy
    from importlib.metadata import version
    from threadpoolctl import threadpool_info
    env=('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','RLS_FAST')
    if any(os.environ.get(k)!='1' for k in env): raise ValueError('one thread and RLS_FAST=1 required')
    kernel=os.environ.get('OPENBLAS_CORETYPE'); affinity=sorted(os.sched_getaffinity(0))
    pools=threadpool_info(); blas=[p for p in pools if p.get('internal_api')=='openblas']
    if kernel!='SkylakeX' or len(affinity)!=1 or not blas or any(p['num_threads']!=1 or p.get('architecture')!=kernel for p in blas):
        raise ValueError('BLAS or affinity not preregistered')
    return {'kernel':kernel,'affinity':affinity,'threadpools':pools,
        'environment':{k:os.environ[k] for k in env+('OPENBLAS_CORETYPE',)},
        'python':platform.python_version(),'numpy':np.__version__,'scipy':scipy.__version__,
        'pyroomacoustics':version('pyroomacoustics'),'platform':platform.platform()}
RULE=ROOT/'docs/current/RINGBUF_HISTORY_ACCESS_PREREG.md'
MAIN=ROOT/'results/final_dev/final_config_core_main.json'
BANK=ROOT/'results/final_dev/final_config_core_final.json'


def selections(key,n):
    """Min/max and count of positions selected from a one-dimensional array."""
    if isinstance(key,tuple) and len(key)==1: key=key[0]
    if isinstance(key,slice):
        a,b,step=key.indices(n); count=len(range(a,b,step))
        if not count: return None,None,0
        last=a+(count-1)*step
        return min(a,last),max(a,last),count
    if isinstance(key,(int,np.integer)) and not isinstance(key,(bool,np.bool_)):
        k=int(key); k=k+n if k<0 else k
        if not 0<=k<n: raise IndexError('index out of bounds')
        return k,k,1
    arr=np.asarray(key)
    if arr.dtype.kind == 'b' and arr.ndim==1 and len(arr)==n:
        ix=np.flatnonzero(arr)
    elif arr.dtype.kind in ('i','u'):
        ix=arr.astype(np.int64,copy=True).ravel(); ix[ix<0]+=n
        if (ix<0).any() or (ix>=n).any(): raise IndexError('index out of bounds')
    else:
        ix=np.asarray(np.arange(n)[key]).ravel()
    if not ix.size: return None,None,0
    return int(ix.min()),int(ix.max()),int(ix.size)


def context(arr):
    frame=sys._getframe(2); calls=[]; contextual_owner=None
    while frame is not None:
        if frame.f_code.co_filename.endswith(('pcg_wls.py','pcg_wls_mw.py')):
            calls.append(frame.f_code.co_name)
            obj=frame.f_locals.get('self')
            if contextual_owner is None and getattr(obj,'__dict__',{}).get(arr._field) is arr:
                contextual_owner=obj
        frame=frame.f_back
    return calls[0] if calls else '<external>', calls, contextual_owner


class Observer:
    def __init__(self):
        self.members=[]; self.member_ids={}; self.rows=[]; self.calls={}
    def add(self,obj):
        token=id(obj)
        if token not in self.member_ids:
            self.member_ids[token]=len(self.members); self.members.append(obj)
        return self.member_ids[token]
    def record(self,arr,kind,key=None):
        caller,stack,frame_owner=context(arr)
        owner=frame_owner if frame_owner is not None else arr._owner()
        n=len(arr); member=self.add(owner) if owner is not None else None
        lo,hi,count=(0,n-1,n) if kind=='append_copy' and n else ((None,None,0) if kind=='append_copy' else selections(key,n))
        stop=int(getattr(owner,'stop',0)) if owner is not None else None
        self.rows.append({'member':member,'field':arr._field,'kind':kind,'caller':caller,
            'stack':stack,'stop':stop,'history_length':n,'min_index':lo,'max_index':hi,'selected_count':count,
            'oldest_age_from_stop':None if lo is None or stop is None else stop-lo,
            'oldest_age_from_length':None if lo is None else n-lo})
    def method(self,name,obj):
        self.add(obj); self.calls[name]=self.calls.get(name,0)+1


class History(np.ndarray):
    def __array_finalize__(self,obj):
        if obj is not None:
            self._observer=getattr(obj,'_observer',None)
            self._owner=getattr(obj,'_owner',lambda:None)
            self._field=getattr(obj,'_field',None)
    def __getitem__(self,key):
        value=super().__getitem__(key)
        if self._observer is not None: self._observer.record(self,'index',key)
        return np.asarray(value) if isinstance(value,np.ndarray) else value


def wrap_history(value,observer,owner,field):
    array=np.asarray(value).view(History)
    array._observer=observer; array._owner=weakref.ref(owner); array._field=field
    return array


@contextmanager
def capture(E,instrumented):
    cls=E.PcgWls; observer=Observer(); original_setattr=cls.__setattr__; original_init=cls.__init__
    own_setattr='__setattr__' in cls.__dict__
    original_concat=np.concatenate
    methods=('_band_solve','force_restart','_localize','_sandwich_q','_risk_threshold')
    originals={name:getattr(cls,name) for name in methods}
    def init(self,*args,**kwargs):
        original_init(self,*args,**kwargs); observer.add(self)
    def setter(self,name,value):
        if name in ('xf','dh') and isinstance(value,np.ndarray):
            value=wrap_history(value,observer,self,name)
        return original_setattr(self,name,value)
    def concatenate(arrays,*args,**kwargs):
        arrays=list(arrays)
        for arr in arrays:
            if isinstance(arr,History) and arr._observer is observer:
                observer.record(arr,'append_copy')
        return original_concat(arrays,*args,**kwargs)
    def method_wrapper(name,original):
        def wrapper(self,*args,**kwargs):
            observer.method(name,self)
            return original(self,*args,**kwargs)
        return wrapper
    try:
        cls.__init__=init
        if instrumented:
            cls.__setattr__=setter; np.concatenate=concatenate
            for name,fn in originals.items(): setattr(cls,name,method_wrapper(name,fn))
        yield observer
    finally:
        cls.__init__=original_init
        if own_setattr: cls.__setattr__=original_setattr
        elif '__setattr__' in cls.__dict__: delattr(cls,'__setattr__')
        np.concatenate=original_concat
        for name,fn in originals.items(): setattr(cls,name,fn)


def fingerprint(value):
    array=np.asarray(value)
    return {'shape':list(array.shape),'dtype':str(array.dtype),
            'sha256':hashlib.sha256(array.tobytes()).hexdigest()}


def execute(protocol,E,flags,case,instrumented):
    noise,scene,seed=case
    cfg=dict(protocol.SCEN[scene],controller_length=512,fft_length=1024,
             **({} if noise=='ar1' else {'noise_type':noise}))
    row={'case':list(case),'config':cfg,'instrumented':instrumented}; raw={}
    with capture(E,instrumented) as observer:
        try:
            result=protocol.P.run(cfg,seed,'PCG-WLS-F',dict(flags),5.,None if scene.startswith('S8') else 1.)
            keys=('e','total_power','uncontrolled_power','score_hist','reset_hops','loc_hist')
            raw={k:np.asarray(result[k]).copy() for k in keys}
            row.update(fingerprints={k:fingerprint(raw[k]) for k in keys},
                events={'reset_hops':result['reset_hops'],'loc_hist':result['loc_hist']},
                stable=bool(result['stable']),failure=result.get('failure'),hops=len(result['total_power']),
                members=[{'L_hops':o.cfg.L_hops,'stop':o.stop,'resets':list(o.resets),'locs':list(o.locs)} for o in observer.members],
                calls=observer.calls)
        except Exception as exc:
            row['exception']=f'{type(exc).__name__}: {exc}'
        return row,observer.rows,raw


def aggregate(rows):
    groups={}
    for r in rows:
        key=(r['member'],r['field'],r['kind'],r['caller'],tuple(r['stack']))
        g=groups.setdefault(key,{'member':key[0],'field':key[1],'kind':key[2],'caller':key[3],
            'stack':list(key[4]),'calls':0,'selected_elements':0,'min_index':None,'max_index':None,
            'max_age_from_stop':None,'max_age_from_length':None,'min_stop':None,'max_stop':None})
        g['calls']+=1;g['selected_elements']+=r['selected_count']
        for field,func in (('min_index',min),('max_index',max),('oldest_age_from_stop',max),('oldest_age_from_length',max),('stop',min),('stop',max)):
            target={'oldest_age_from_stop':'max_age_from_stop','oldest_age_from_length':'max_age_from_length'}.get(field,field)
            if field=='stop': target='min_stop' if func is min else 'max_stop'
            value=r[field]
            if value is not None:g[target]=value if g[target] is None else func(g[target],value)
    return list(groups.values())


def main():
    p=argparse.ArgumentParser();p.add_argument('out',type=Path);p.add_argument('--execute',action='store_true');args=p.parse_args()
    if not args.execute: raise ValueError('execution requires --execute')
    out=args.out.resolve()
    if not out.is_relative_to((ROOT/'results').resolve()) or out==(ROOT/'results').resolve(): raise ValueError('output must be new results subdirectory')
    import verify_protocol_defs as protocol
    import ffanc_norm.pcg_wls as E
    import scipy.linalg.blas
    runtime=runtime_info()
    if runtime['kernel']!='SkylakeX':raise ValueError('preregistered SkylakeX required')
    flags={'main':json.loads(MAIN.read_text())['flags'],'bank':json.loads(BANK.read_text())['flags']}
    cases=[(noise,scene,seed) for noise,scene in COMBOS for seed in range(300,305)]
    out.mkdir(parents=True,exist_ok=False); (out/'cases').mkdir(); (out/'access').mkdir()
    immutable_json(out/'manifest.json',{'commit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
      'runtime':runtime,'rule_sha256':file_sha(RULE),'runner_sha256':file_sha(Path(__file__)),
      'source_sha256':{name:file_sha(ROOT/name) for name in ('src/ffanc_norm/pcg_wls.py',
         'src/ffanc_norm/pcg_wls_mw.py','experiments/prototype_new_algorithms.py',
         'experiments/verify_protocol_defs.py')},
      'main_sha256':file_sha(MAIN),'bank_sha256':file_sha(BANK),
      'supplement_sha256':file_sha(ROOT/'docs/current/RINGBUF_HISTORY_ACCESS_SUPPLEMENT_PREREG.md'),'flags':flags,'expected_pairs':len(cases)*len(flags)})
    old_return=protocol.P.RETURN_SIGNALS;protocol.P.RETURN_SIGNALS=True
    try:
        for mode,params in flags.items():
            for index,case in enumerate(cases):
                baseline,_,raw_a=execute(protocol,E,params,case,False); traced,access,raw_b=execute(protocol,E,params,case,True)
                keys=('e','total_power','uncontrolled_power','score_hist','reset_hops','loc_hist')
                comparisons={k:(k in raw_a and k in raw_b and raw_a[k].shape==raw_b[k].shape
                    and raw_a[k].dtype==raw_b[k].dtype and raw_a[k].tobytes()==raw_b[k].tobytes()) for k in keys}
                verified=all(comparisons.values()) and baseline.get('stable') is True and traced.get('stable') is True and baseline.get('hops')==traced.get('hops')==312 and baseline.get('members')==traced.get('members') and 'exception' not in baseline and 'exception' not in traced
                name=f"{mode}_{case[0]}_{case[1].split()[0]}_{case[2]}"
                with gzip.open(out/'access'/f'{name}.jsonl.gz','xt') as fh:
                    for row in access: fh.write(json.dumps(row,allow_nan=False)+'\n')
                immutable_json(out/'cases'/f'{name}.json',{'mode':mode,'case':case,'baseline':baseline,'traced':traced,
                    'bit_equal':comparisons,'verified':verified,'access_count':len(access),'summary':aggregate(access)})
                print(mode,index+1,'/',len(cases),case,'verified=',verified,flush=True)
    finally: protocol.P.RETURN_SIGNALS=old_return
    expected={f"{mode}_{nz}_{scene.split()[0]}_{sd}.json" for mode in flags for nz,scene,sd in cases}
    actual={p.name for p in (out/'cases').glob('*.json')}
    if actual!=expected: raise RuntimeError('missing or unexpected case files')
    immutable_json(out/'complete.json',{'expected':len(expected),'actual':len(actual)})

if __name__=='__main__':main()
