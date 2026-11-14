import json, re, csv, os
SRC='/home/claude/work/src'
def norm(w): return re.sub(r"[^a-z0-9']+","",w.lower().replace('’',"'"))
class Lesson:
    def __init__(self,ep):
        self.ep=ep
        NEW=f'{SRC}/audio/ep{ep}_words.json'
        if ep==1:
            wj=json.load(open(NEW if os.path.exists(NEW) else f'{SRC}/1/revisions/r3-foundations-parts/punctuation-v2/words.json'))
            rows=list(csv.DictReader(open(f'{SRC}/1/revisions/r3-foundations-parts/qa/SCENE_ALIGNMENT.csv')))
        else:
            wj=json.load(open(NEW if os.path.exists(NEW) else f'{SRC}/2/audio-production/r2-clear-phrases/punctuation-v2/words.json'))
            rows=list(csv.DictReader(open(f'{SRC}/2/qa/final-pass2/46f95cf23fceb564/END_TO_END_SCENE_ALIGNMENT.csv')))
        self.scenes={r['scene_id']:(int(r['scene_number']),int(r['start_frame']),int(r['end_frame_exclusive'])) for r in rows}
        self.words=wj['words']
    def span(self,sid):
        n,s,e=self.scenes[sid]; return n,s,e,e-s
    def scene_words(self,sid):
        return [w for w in self.words if w['scene_id']==sid]
    def t(self,sid,phrase,occurrence=1):
        """scene-relative start time (s) of the first word of `phrase` within the scene"""
        n,s,e,_=self.span(sid); t0=s/24
        ws=self.scene_words(sid); toks=[norm(w['word']) for w in ws]
        want=[norm(x) for x in phrase.split() if norm(x)]
        hits=0
        for i in range(len(toks)-len(want)+1):
            if toks[i:i+len(want)]==want:
                hits+=1
                if hits==occurrence: return round(ws[i]['start']-t0,2)
        raise KeyError(f'{sid}: phrase not found: {phrase!r}')
    def t_end(self,sid,phrase,occurrence=1):
        n,s,e,_=self.span(sid); t0=s/24
        ws=self.scene_words(sid); toks=[norm(w['word']) for w in ws]
        want=[norm(x) for x in phrase.split() if norm(x)]
        hits=0
        for i in range(len(toks)-len(want)+1):
            if toks[i:i+len(want)]==want:
                hits+=1
                if hits==occurrence: return round(ws[i+len(want)-1]['end']-t0,2)
        raise KeyError(phrase)
if __name__=='__main__':
    L=Lesson(1); print(L.span('loss')); print(L.t('loss','A logarithm reverses a power'), L.t('loss','Two times two times two is eight'))
