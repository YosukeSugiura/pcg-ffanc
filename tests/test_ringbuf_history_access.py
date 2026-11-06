import copy
import sys
from pathlib import Path
import numpy as np
import pytest
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'experiments'),str(ROOT/'src')]
from ringbuf_history_access import selections, capture, History
import ffanc_norm.pcg_wls as E


def test_positions_match_numpy_for_index_forms():
    n=9
    for key in (0,-1,slice(None),slice(7,1,-2),slice(2,2),np.array([0,-1,3,3]),
                np.array([True,False,True,False,False,False,True,False,False])):
        raw=np.asarray(np.arange(n)[key]).ravel(); lo,hi,count=selections(key,n)
        assert count==raw.size
        assert lo==(int(raw.min()) if raw.size else None)
        assert hi==(int(raw.max()) if raw.size else None)


def test_record_eager_where_and_append_then_rewrap():
    with capture(E,True) as log:
        o=E.PcgWls(E.PcgWlsConfig(M=8,H=4,detect=False)); o.xf=np.arange(8.); o.dh=np.arange(8.)
        assert isinstance(o.xf,History)
        out=np.where(np.array([False,True]),o.xf[np.clip(np.array([-3,2]),0,None)],0.)
        np.testing.assert_array_equal(out,[0,2]); assert log.rows[-1]['selected_count']==2
        before=len(log.rows); o.xf=np.concatenate([o.xf,np.arange(4.)])
        assert isinstance(o.xf,History)
        assert log.rows[before]['kind']=='append_copy' and log.rows[before]['selected_count']==8
        assert log.rows[before]['history_length']==8 and log.rows[before]['stop']==0
        np.testing.assert_array_equal(o.xf[8:],[0,1,2,3])


def test_real_update_stop_and_multi_window_members():
    with capture(E,True) as log:
        a=E.PcgWls(E.PcgWlsConfig(M=8,H=4,detect=False)); b=E.PcgWls(E.PcgWlsConfig(M=8,H=4,detect=False))
        for o in (a,b):
            o.update(np.ones(4),np.ones(4))
        assert len(log.members)==2
        copies=[r for r in log.rows if r['kind']=='append_copy']
        indexed=[r for r in log.rows if r['kind']=='index']
        assert copies and indexed
        assert all(r['history_length']==0 and r['stop']==0 for r in copies)
        assert all(r['history_length']==4 and r['stop']==4 for r in indexed)
        assert {r['member'] for r in indexed}=={0,1}


def test_copy_branch_context_is_correctly_attributed():
    with capture(E,True) as log:
        a=E.PcgWls(E.PcgWlsConfig(M=8,H=4,detect=False)); a.xf=np.arange(8.); a.stop=8
        b=copy.copy(a); b.stop=6
        ns={};exec(compile('def access(self):\n return self.xf[-1]\n','pcg_wls.py','exec'),ns)
        assert ns['access'](b)==7
        assert log.rows[-1]['stop']==6 and log.members[log.rows[-1]['member']] is b


def test_restore_on_exception():
    init=E.PcgWls.__init__; had='__setattr__' in E.PcgWls.__dict__; setter=E.PcgWls.__setattr__; concat=np.concatenate
    with pytest.raises(RuntimeError):
        with capture(E,True): raise RuntimeError('test')
    assert E.PcgWls.__init__ is init and E.PcgWls.__setattr__ is setter
    assert ('__setattr__' in E.PcgWls.__dict__)==had and np.concatenate is concat


def test_actual_multi_window_shared_members_and_forced_restart():
    from ffanc_norm.pcg_wls_mw import PcgWlsMultiWindow
    original_init=E.PcgWls.__init__; original_concat=np.concatenate
    with capture(E,True) as log:
        mw=PcgWlsMultiWindow(E.PcgWlsConfig(M=8,H=4,detect=False),L_list=[2,3,5],
                      primary=3,cheap=['share','nodetect'])
        for j in range(5):
            mw.update(np.full(4,1.+j/10),np.full(4,.5))
        assert len(log.members)==3
        assert all(o in log.members for o in mw.members)
        before=len(log.rows)
        mw.members[2].force_restart(4)
        forced=log.rows[before:]
        assert any('force_restart' in r['stack'] for r in forced)
        assert all(log.members[r['member']] is mw.members[2] for r in forced)
        assert log.calls['force_restart']==1
        assert {r['member'] for r in log.rows} == {0,1,2}
    assert E.PcgWls.__init__ is original_init and np.concatenate is original_concat
