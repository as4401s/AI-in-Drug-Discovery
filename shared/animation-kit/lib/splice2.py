#!/usr/bin/env python3
"""Assemble a v2 lesson film: the project's own original scene clips (stream copy) with every rebuilt scene clip swapped in,
plus an audio file chosen by --audio (the narration with spelled-out DNA/RNA sped up).  Video is never re-encoded.

usage: splice2.py --ep 1|2 --clips CLIPS_DIR --audio AUDIO.m4a --out OUT.mp4
  CLIPS_DIR holds one folder per rebuilt scene named NN-<scene_id>/scene.mp4 (NN = scene number, as in the alignment table).
Checks (assertions): every replacement has exactly the frame count of the scene it replaces; the output has one video packet per
frame of the original film; the audio stream is bit-identical to --audio and has the expected number of AAC frames; audio and video
durations agree to within one video frame."""
import argparse, csv, os, subprocess, sys, json
ROOT=os.path.expanduser('~/mnt/arjunsarkar--Tutorial/Playlists/ai-in-drug-discovery')
CFG={
 1:dict(table=f'{ROOT}/1/revisions/r3-foundations-parts/qa/SCENE_ALIGNMENT.csv',
        clips=f'{ROOT}/1/revisions/r3-foundations-parts/renders/lesson1-r3-foundations-v4',
        final=f'{ROOT}/1/revisions/r3-foundations-parts/exports/1-Can-AI-Simulate-a-Cell.mp4'),
 2:dict(table=f'{ROOT}/2/qa/final-pass2/46f95cf23fceb564/END_TO_END_SCENE_ALIGNMENT.csv',
        clips=f'{ROOT}/2/renders/lesson2-microscopy-v2',
        final=f'{ROOT}/2/exports/2-Microscopy-from-Cells-to-Organoids-and-Tissues-r2.mp4'),
}
def run(cmd):
    r=subprocess.run(cmd,capture_output=True,text=True)
    if r.returncode: print(r.stderr[-2000:]); sys.exit(1)
    return r.stdout
def packets(p,sel='v:0'):
    return int(run(['ffprobe','-v','error','-count_packets','-select_streams',sel,'-show_entries','stream=nb_read_packets','-of','csv=p=0',p]).strip())
ap=argparse.ArgumentParser(); ap.add_argument('--ep',type=int,required=True); ap.add_argument('--clips',required=True)
ap.add_argument('--audio',required=True); ap.add_argument('--out',required=True); a=ap.parse_args()
for k in ('clips','audio','out'): setattr(a,k,os.path.abspath(os.path.expanduser(getattr(a,k))))
cfg=CFG[a.ep]
rows=list(csv.DictReader(open(cfg['table'])))
dirs=sorted(d for d in os.listdir(cfg['clips']) if d[:2].isdigit() and os.path.isfile(f"{cfg['clips']}/{d}/scene.mp4"))
assert len(dirs)==len(rows),(len(dirs),len(rows))
newd={}
for d in sorted(os.listdir(a.clips)):
    p=f'{a.clips}/{d}/scene.mp4'
    if d[:2].isdigit() and os.path.isfile(p): newd[d]=p
tmp=os.path.expanduser('~/rev/tmp_splice'); os.makedirs(tmp,exist_ok=True)
lst=f'{tmp}/v2_ep{a.ep}.ffconcat'; total=0; changed=[]; used=set()
with open(lst,'w') as f:
    f.write('ffconcat version 1.0\n')
    for i,(d,r) in enumerate(zip(dirs,rows)):
        sid=r['scene_id']; assert d.split('-',1)[1]==sid,(d,sid)
        n=int(r['end_frame_exclusive'])-int(r['start_frame'])
        key=f"{int(r['scene_number']):02d}-{sid}"
        if key in newd:
            p=newd[key]; used.add(key)
            cnt=packets(p); assert cnt==n,f'{sid}: replacement has {cnt} frames, need {n}'
            changed.append(key)
        else: p=f"{cfg['clips']}/{d}/scene.mp4"
        f.write(f"file '{p}'\nduration {n/24:.9f}\n"); total+=n
assert used==set(newd),f'clips not matching any scene: {sorted(set(newd)-used)}'
silent=f'{tmp}/v2_silent_ep{a.ep}.mp4'
run(['ffmpeg','-v','error','-y','-f','concat','-safe','0','-i',lst,'-map','0:v','-c','copy','-video_track_timescale','24000',silent])
run(['ffmpeg','-v','error','-y','-i',silent,'-i',a.audio,'-map','0:v:0','-map','1:a:0','-c','copy','-movflags','+faststart',a.out])
# ---- checks
def md5stream(path,sel):
    return run(['ffmpeg','-v','error','-i',path,'-map',sel,'-c','copy','-f','md5','-']).strip()
nb=packets(a.out); na=packets(a.out,'a:0'); na_src=packets(a.audio,'a:0')
def dur(p,sel): return float(run(['ffprobe','-v','error','-select_streams',sel,'-show_entries','stream=duration','-of','csv=p=0',p]).strip())
dv,da=dur(a.out,'v:0'),dur(a.out,'a:0')
m_new=md5stream(a.out,'0:a'); m_src=md5stream(a.audio,'0:a')
res=dict(out=a.out,rebuilt_scenes=len(changed),video_packets=nb,expected_frames=total,audio_frames=na,audio_frames_in_source=na_src,
         video_duration=dv,audio_duration=da,audio_matches_source=(m_new==m_src),replaced=changed)
print(json.dumps(res,indent=1))
assert nb==total and na==na_src and m_new==m_src and abs(dv-da)<=1/24+1e-6
