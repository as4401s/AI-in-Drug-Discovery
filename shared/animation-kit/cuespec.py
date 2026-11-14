import sys,json,os
sys.path.insert(0,'/home/claude/work/lib')
from cues import Lesson
_L={}
def L(ep):
    if ep not in _L:_L[ep]=Lesson(ep)
    return _L[ep]
def build(dirname,ep,sid,spec):
    """spec: {cue: 'phrase' | ('phrase',occurrence)}  -> scenes/<dirname>/cues.json (scene-relative seconds)"""
    out={}
    for k,v in spec.items():
        ph,occ=(v,1) if isinstance(v,str) else v
        out[k]=L(ep).t(sid,ph,occ)
    n,s,e,fr=L(ep).span(sid)
    out['_frames']=fr
    os.makedirs(f'/home/claude/work/scenes/{dirname}',exist_ok=True)
    json.dump(out,open(f'/home/claude/work/scenes/{dirname}/cues.json','w'))
    return out
