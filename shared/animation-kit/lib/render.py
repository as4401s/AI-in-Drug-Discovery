#!/usr/bin/env python3
"""Render one authored scene to an H.264 clip (or to preview PNGs).
usage: render.py SCENE_HTML --cues cues.json --frames N --out DIR [--preview t1,t2,...]
Frames are captured only when the scene's stamp changes (static holds are repeated via ffconcat durations)."""
import argparse, asyncio, json, os, subprocess, sys, hashlib
from playwright.async_api import async_playwright
FPS=24
async def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('html'); ap.add_argument('--cues',default=None); ap.add_argument('--frames',type=int,default=0)
    ap.add_argument('--out',required=True); ap.add_argument('--preview',default=None); ap.add_argument('--name',default='scene')
    a=ap.parse_args()
    os.makedirs(a.out,exist_ok=True)
    cues=json.load(open(a.cues)) if a.cues else {}
    async with async_playwright() as p:
        b=await p.chromium.launch(executable_path='/usr/bin/google-chrome',args=['--no-sandbox','--font-render-hinting=none','--disable-lcd-text','--force-color-profile=srgb'])
        pg=await b.new_page(viewport={'width':1920,'height':1080},device_scale_factor=1)
        await pg.add_init_script('window.CUES='+json.dumps(cues))
        msgs=[]
        pg.on('console',lambda m: msgs.append(m.text)); pg.on('pageerror',lambda e: msgs.append('PAGEERROR '+str(e)))
        await pg.goto('file://'+os.path.abspath(a.html))
        await pg.wait_for_function('window.ready===true',timeout=20000)
        if a.preview:
            for ts in a.preview.split(','):
                t=float(ts); await pg.evaluate(f'renderAt({t})')
                await pg.screenshot(path=f'{a.out}/preview_{t:07.2f}.png')
            for m in msgs: print('console:',m)
            await b.close(); return
        fdir=f'{a.out}/frames'; os.makedirs(fdir,exist_ok=True)
        entries=[]; prev=None; n_shot=0
        for f in range(a.frames):
            st=await pg.evaluate(f'renderAt({f/FPS})')
            if st!=prev:
                path=os.path.abspath(f'{fdir}/f{f:06d}.png')
                await pg.screenshot(path=path); n_shot+=1
                entries.append([path,1]); prev=st
            else: entries[-1][1]+=1
        for m in msgs[:10]: print('console:',m)
        await b.close()
    with open(f'{a.out}/images.ffconcat','w') as fh:
        fh.write('ffconcat version 1.0\n')
        for path,c in entries: fh.write(f"file '{path}'\nduration {c/FPS:.9f}\n")
        fh.write(f"file '{entries[-1][0]}'\n")
    clip=f'{a.out}/{a.name}.mp4'
    cmd=['ffmpeg','-v','error','-y','-f','concat','-safe','0','-i',f'{a.out}/images.ffconcat',
         '-vf',f'fps={FPS}:round=near,scale=out_color_matrix=bt709:out_range=tv:flags=accurate_rnd+full_chroma_int,format=yuv420p',
         '-frames:v',str(a.frames),'-c:v','libx264','-preset','veryfast','-crf','18','-pix_fmt','yuv420p',
         '-colorspace','bt709','-color_range','tv','-video_track_timescale','24000','-an',clip]
    subprocess.run(cmd,check=True)
    pr=subprocess.run(['ffprobe','-v','error','-count_frames','-select_streams','v:0','-show_entries','stream=nb_read_frames,duration','-of','csv=p=0',clip],capture_output=True,text=True).stdout.strip()
    print(f'rendered {a.frames} frames ({n_shot} unique screenshots) -> {clip}  probe={pr}')
asyncio.run(main())
