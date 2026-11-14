import sys; sys.path.insert(0,'/home/claude/work/lib')
from cues import Lesson, norm
def narr(ep,sid,gap=0.0):
    L=Lesson(ep); n,s,e,_=L.span(sid); t0=s/24
    out=[]; cur=[]; st=None
    for w in L.scene_words(sid):
        if st is None: st=w['start']-t0
        cur.append(w['word'].strip())
        if w['word'].strip()[-1:] in '.?!':
            out.append((st,' '.join(cur))); cur=[]; st=None
    if cur: out.append((st,' '.join(cur)))
    print(f"--- ep{ep} {sid}  #{n}  {(e-s)/24:.1f}s")
    for t,x in out: print(f"  [{t:5.1f}] {x}")
if __name__=='__main__':
    ep=int(sys.argv[1])
    for sid in sys.argv[2:]: narr(ep,sid)
