// Shared "figure tour" scene: a camera that zooms across a real paper figure in step with the narration,
// step cards that light up as the camera visits them, a mini-map, and bottom notes.  Config comes from cues.json.
function FIGTOUR(S,C){
  const {el,at,show,out,ramp,mix,lin}=WB,clamp=WB.clamp;
  const INK='#183b32',MUT='#60716a';
  const VX=80,VY=222,VW=1140,VH=660,IW=VW-6,IH=VH-6;
  const vp=el('div','',null);vp.style.cssText=`position:absolute;left:${VX}px;top:${VY}px;width:${VW}px;height:${VH}px;overflow:hidden;border:3px solid #d4ded9;border-radius:18px;background:#fff`;
  const cam=document.createElement('div');cam.style.cssText='position:absolute;left:0;top:0;transform-origin:0 0;will-change:transform';vp.appendChild(cam);
  const img=document.createElement('img');img.src=C.img;img.style.cssText=`position:absolute;left:0;top:0;width:${C.iw}px;height:${C.ih}px`;cam.appendChild(img);
  const toImg=r=>[(r[0]-C.ox)*C.k,(r[1]-C.oy)*C.k,(r[2]-C.ox)*C.k,(r[3]-C.oy)*C.k];
  const keys=C.cam.map(k=>({t:k.t,r:toImg(k.r),hl:k.hl?toImg(k.hl):null,hlt:k.hlt}));
  const hls=keys.map((k,i)=>{if(!k.hl)return null;const d=document.createElement('div');d.style.cssText=`position:absolute;left:${k.hl[0]}px;top:${k.hl[1]}px;width:${k.hl[2]-k.hl[0]}px;height:${k.hl[3]-k.hl[1]}px;background:rgba(183,109,102,.07);opacity:0`;cam.appendChild(d);return d});
  // ---- step cards (right)
  const SX=1260,SW=580,CH=C.cardH||120,GAP=12;
  const cards=(C.steps||[]).map((s,i)=>{const y=VY+i*(CH+GAP);const b=el('div','box '+(s.cls||'b-blue'));at(b,SX,y,SW,CH);b.style.border='4px solid transparent';
    const n=el('div','t','');n.innerHTML=String(i+1);n.style.cssText+=`;width:42px;height:42px;border-radius:50%;background:${INK};color:#fff;font:700 24px/42px Poppins;text-align:center`;at(n,SX+22,y+14);
    const h=el('div','t',s.title);h.style.cssText+=';font:700 29px/1.15 Poppins;color:'+INK;at(h,SX+80,y+12);
    const bd=el('div','t',s.body);bd.style.cssText+=';font:400 25px/1.25 Inter;color:'+INK+';white-space:normal';at(bd,SX+80,y+52,SW-100);
    return {b,n,h,bd,s}});
  // ---- notes (under viewport)
  const cap=el('div','t',C.caption||'');cap.style.cssText+=';font:400 23px/1 Inter;color:'+MUT;at(cap,VX+6,VY+VH+10);
  const notes=(C.notes||[]).map(n=>{const e=el('div','pill '+(n.cls||'b-lav'),n.text);at(e,VX,VY+VH+40);e.style.cssText+=';font-size:29px;padding:11px 26px;text-align:left;white-space:nowrap;border-radius:34px';return {e,n}});
  // ---- mini-map
  const F=toImg(C.full);const fw=F[2]-F[0],fh=F[3]-F[1];const ms=Math.min(250/fw,200/fh);const MW=fw*ms,MH=fh*ms;
  const mx=SX+SW-MW,my=VY+VH+54-MH+ (C.mmDy||0);
  const mm=el('div','',null);mm.style.cssText=`position:absolute;left:${mx}px;top:${my}px;width:${MW}px;height:${MH}px;overflow:hidden;border:3px solid #d4ded9;border-radius:10px;background:#fff`;
  const mimg=document.createElement('img');mimg.src=C.img;mimg.style.cssText=`position:absolute;left:${-F[0]*ms}px;top:${-F[1]*ms}px;width:${C.iw*ms}px;height:${C.ih*ms}px`;mm.appendChild(mimg);
  const mr=document.createElement('div');mr.style.cssText='position:absolute;border:3px solid #b76d66;background:rgba(183,109,102,.12);border-radius:3px';mm.appendChild(mr);
  const mml=el('div','t','overview · red box = what is zoomed');mml.style.cssText+=';font:400 22px/1.2 Inter;color:'+MUT+';white-space:normal';at(mml,mx-280,my+MH-52,260);mml.style.textAlign='right';
  const stepsBottom=VY+(cards.length)*(CH+GAP);
  return function update(t){
    show(vp,t,.1,.6,{dy:0});
    // camera
    let r=keys[0].r.slice();
    for(let i=1;i<keys.length;i++){const p=ramp(t,keys[i].t,keys[i].dur||1.3);for(let j=0;j<4;j++)r[j]=mix(r[j],keys[i].r[j],p)}
    const w=r[2]-r[0],h=r[3]-r[1],s=Math.min(IW/w,IH/h)*.97;
    const tx=IW/2-s*(r[0]+r[2])/2,ty=IH/2-s*(r[1]+r[3])/2;
    cam.style.transform=`translate(${tx.toFixed(2)}px,${ty.toFixed(2)}px) scale(${s.toFixed(5)})`;
    hls.forEach((d,i)=>{if(!d)return;const k=keys[i];const nxt=keys[i+1];const a=out(t,k.t+(k.hlt==null?.9:k.hlt),.5)*(nxt?1-out(t,nxt.t+.1,.4):1);d.style.opacity=a;d.style.border=`${(5/s).toFixed(2)}px solid #b76d66`;d.style.borderRadius=(10/s).toFixed(2)+'px'});
    // minimap rect
    mr.style.left=((r[0]-F[0])*ms).toFixed(1)+'px';mr.style.top=((r[1]-F[1])*ms).toFixed(1)+'px';mr.style.width=(w*ms).toFixed(1)+'px';mr.style.height=(h*ms).toFixed(1)+'px';
    show(mm,t,.4,.6,{dy:0});show(mml,t,.6,.6,{dy:0});show(cap,t,.3,.6,{dy:0});
    // step cards
    const fadeAll=C.panelFadeAt!=null?1-out(t,C.panelFadeAt,.6):1;
    cards.forEach(c=>{const a=out(t,c.s.t0-.3,.6);const on=out(t,c.s.t0,.4)*(1-out(t,c.s.t1,.5));
      const op=a*(0.5+0.5*on)*fadeAll;c.b.style.opacity=op;c.b.style.borderColor=on>.5?'#26765d':'transparent';c.b.style.transform=`translateX(${((1-a)*24).toFixed(1)}px)`;
      [c.n,c.h,c.bd].forEach(e=>{e.style.opacity=op;e.style.transform=`translateX(${((1-a)*24).toFixed(1)}px)`})});
    notes.forEach(({e,n})=>{const a=out(t,n.t0,.5)*(n.t1!=null?1-out(t,n.t1,.4):1);e.style.opacity=a;e.style.transform=`translateY(${((1-a)*10).toFixed(1)}px)`});
    const vf=C.vpFadeAt!=null?1-out(t,C.vpFadeAt,.6):1;
    const mf=C.mmFadeAt!=null?1-out(t,C.mmFadeAt,.6):1;
    [vp,cap].forEach(e=>{e.style.opacity=parseFloat(e.style.opacity||0)*vf});[mm,mml].forEach(e=>{e.style.opacity=parseFloat(e.style.opacity||0)*vf*mf});
    notes.forEach(({e})=>{e.style.opacity=parseFloat(e.style.opacity||0)*vf});
    return {s,tx,ty,r,fadeAll};
  };
}
