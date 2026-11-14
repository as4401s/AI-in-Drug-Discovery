#!/usr/bin/env python3
"""Splice replacement scene clips into a lesson film.  Unchanged scenes are the project's own original clips
(stream copy); audio is the original final MP4's AAC stream, copied untouched.
usage: splice.py --ep 1|2 --out OUT.mp4 --replace id=path.mp4 [--replace id2=path2.mp4 ...]"""
import argparse, csv, os, subprocess, sys, json, hashlib
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
ap=argparse.ArgumentParser(); ap.add_argument('--ep',type=int,required=True); ap.add_argument('--out',required=True)
ap.add_argument('--replace',action='append',default=[]); a=ap.parse_args()
cfg=CFG[a.ep]; rep={}
for r in a.replace:
    k,v=r.split('=',1); rep[k]=os.path.abspath(os.path.expanduser(v))
rows=list(csv.DictReader(open(cfg['table'])))
dirs=sorted(d for d in os.listdir(cfg['clips']) if d[:2].isdigit() and os.path.isfile(f"{cfg['clips']}/{d}/scene.mp4"))
assert len(dirs)==len(rows),(len(dirs),len(rows))
tmp=os.path.expanduser('~/rev/tmp_splice'); os.makedirs(tmp,exist_ok=True)
lst=f'{tmp}/ep{a.ep}.ffconcat'; total=0; changed=[]
with open(lst,'w') as f:
    f.write('ffconcat version 1.0\n')
    for d,r in zip(dirs,rows):
        sid=r['scene_id']; assert d.split('-',1)[1]==sid,(d,sid)
        n=int(r['end_frame_exclusive'])-int(r['start_frame'])
        if sid in rep:
            p=rep[sid]
            cnt=int(run(['ffprobe','-v','error','-count_frames','-select_streams','v:0','-show_entries','stream=nb_read_frames','-of','csv=p=0',p]).strip())
            assert cnt==n,f'{sid}: replacement has {cnt} frames, need {n}'
            changed.append((sid,int(r['start_frame']),int(r['end_frame_exclusive'])))
        else: p=f"{cfg['clips']}/{d}/scene.mp4"
        f.write(f"file '{p}'\nduration {n/24:.9f}\n"); total+=n
silent=f'{tmp}/silent_ep{a.ep}.mp4'
run(['ffmpeg','-v','error','-y','-f','concat','-safe','0','-i',lst,'-map','0:v','-c','copy','-video_track_timescale','24000',silent])
run(['ffmpeg','-v','error','-y','-i',silent,'-i',cfg['final'],'-map','0:v:0','-map','1:a:0','-c','copy','-movflags','+faststart',a.out])
# ---- checks
def md5stream(path,sel):
    return run(['ffmpeg','-v','error','-i',path,'-map',sel,'-c','copy','-f','md5','-']).strip()
nb=int(run(['ffprobe','-v','error','-count_packets','-select_streams','v:0','-show_entries','stream=nb_read_packets','-of','csv=p=0',a.out]).strip())
dur=run(['ffprobe','-v','error','-show_entries','format=duration','-of','csv=p=0',a.out]).strip()
a_new=md5stream(a.out,'0:a'); a_old=md5stream(cfg['final'],'0:a')
res=dict(out=a.out,video_packets=nb,expected_frames=total,duration=dur,audio_md5_new=a_new,audio_md5_orig=a_old,audio_identical=(a_new==a_old),replaced=changed)
print(json.dumps(res,indent=1))
assert nb==total and a_new==a_old
