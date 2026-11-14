// Shared helpers for the microscopy scenes: real-pixel plane canvas, rolling note box, histogram widget.
const INK='#183b32',MUT='#60716a',GRN='#26765d',COR='#b76d66',BLU='#557eaf',AMB='#a65647';
function box(cls,x,y,w,h){const b=WB.el('div','box '+cls);WB.at(b,x,y,w,h);return b}
function tx(css,html,x,y,w){const e=WB.el('div','t');e.style.cssText+=';'+css;e.innerHTML=html;WB.at(e,x,y,w);return e}
const LABPAL=[[231,111,81],[42,157,143],[233,196,106],[38,70,83],[138,177,125],[244,162,97],[106,76,147],[25,130,196],[255,89,100],[138,201,38],[255,202,58],[89,205,176],[182,115,255],[255,141,161],[0,180,216],[199,125,60]];
// PLANE: draws a real 256x256 raw array into a canvas.  opts per draw: {src,lims,T,tint,alpha,lab,pal,dim}
function PLANE(S,x,y,size){
  const cv=document.createElement('canvas');cv.width=256;cv.height=256;
  cv.style.cssText=`position:absolute;left:${x}px;top:${y}px;width:${size}px;height:${size}px;image-rendering:pixelated;border:3px solid ${INK};border-radius:8px;box-sizing:content-box`;
  S.appendChild(cv);const g=cv.getContext('2d');const id=g.createImageData(256,256);const d=id.data;let key='';
  return {cv,size,x,y,
    draw(o){const k=o.key!=null?o.key:JSON.stringify({T:o.T,alpha:o.alpha,dim:o.dim,lo:o.lo,hi:o.hi});if(k===key)return;key=k;
      const src=o.src||D.P,lo=o.lo!=null?o.lo:D.LO,hi=o.hi!=null?o.hi:D.HI,T=o.T,tint=o.tint||[38,170,120],al=o.alpha==null?.55:o.alpha;
      const lab=o.lab,fn=o.colorFn;
      for(let i=0;i<65536;i++){const v=src[i];let gr=(v-lo)/(hi-lo);gr=gr<0?0:gr>1?1:gr;gr*=255;let r=gr,gg=gr,b=gr;
        if(o.dim!=null){r=gg=b=gr*o.dim+ (1-o.dim)*40}
        if(T!=null&&v>T){r=r*(1-al)+tint[0]*al;gg=gg*(1-al)+tint[1]*al;b=b*(1-al)+tint[2]*al}
        if(lab&&fn){const c=fn(lab[i],i);if(c){const a=c[3];r=r*(1-a)+c[0]*a;gg=gg*(1-a)+c[1]*a;b=b*(1-a)+c[2]*a}}
        const j=i*4;d[j]=r;d[j+1]=gg;d[j+2]=b;d[j+3]=255}
      g.putImageData(id,0,0)}};
}
// outline-only draw over labels (edge pixels of region mask)
function edgeMask(lab,pick){const e=new Uint8Array(65536);for(let y=0;y<256;y++)for(let x=0;x<256;x++){const i=y*256+x,l=lab[i];if(!pick(l))continue;
  const n=[y>0?lab[i-256]:-1,y<255?lab[i+256]:-1,x>0?lab[i-1]:-1,x<255?lab[i+1]:-1];if(n.some(v=>v!==l))e[i]=1}return e}
// rolling note box: notes=[{a,b,title,body,subs:[[t,html],...]}]
function NOTEBOX(S,cfg){
  const {out,show}=WB;const {x,y,w,h,notes}=cfg;
  const bx=box(cfg.cls||'b-amber',x,y,w,h);
  const els=notes.map(n=>{const wrap=tx('white-space:normal',`<div style="font:700 ${cfg.tfs||30}px/1.2 Poppins;color:${INK};margin-bottom:14px">${n.title||''}</div><div style="font:500 ${cfg.bfs||29}px/1.35 Inter;color:${INK}">${n.body||''}</div>`+(n.subs||[]).map((s,i)=>`<div class="sb" style="font:600 ${cfg.bfs||29}px/1.3 Inter;color:${n.subcol||INK};margin-top:12px;padding-left:34px;position:relative"><span style="position:absolute;left:0;color:${GRN}">●</span>${s[1]}</div>`).join(''),x+28,y+26,w-56);
    return {wrap,n,subs:[...wrap.querySelectorAll('.sb')]}});
  return {bx,update(t){show(bx,t,notes[0].a-.2,.6,{dy:0});
    els.forEach(({wrap,n,subs})=>{const nx=n.b==null?999:n.b;const a=out(t,n.a,.4)*(1-out(t,nx,.4));wrap.style.opacity=a;wrap.style.transform=`translateY(${((1-a)*8).toFixed(1)}px)`;
      subs.forEach((s,i)=>{s.style.opacity=out(t,n.subs[i][0],.5)})})}};
}
// histogram of the real plane with optional threshold line + class colouring; returns draw(t params)
function HISTO(S,x,y,w,h,opts){
  const sv=WB.svg('svg',{width:1920,height:1080,style:'position:absolute;left:0;top:0'},S);
  const NB=D.HB.length,mx=Math.max(...D.HB),bw=w/NB;const bars=[];
  const xmaxv=NB*D.BW;
  for(let i=0;i<NB;i++){const r=WB.svg('rect',{x:x+i*bw+.5,width:bw-1,y:y+h,height:0,fill:'#9fb9d9'},sv);bars.push(r)}
  const axis=WB.svg('line',{x1:x,y1:y+h+1,x2:x+w,y2:y+h+1,stroke:'#8aa59b','stroke-width':3},sv);
  const line=WB.svg('line',{x1:x,x2:x,y1:y-14,y2:y+h,stroke:COR,'stroke-width':5},sv);
  return {sv,bars,axis,line,x,y,w,h,mx,bw,NB,
    px(T){return x+T/xmaxv*w},
    set(prog,T,colorize){ // prog: bar growth 0..1; T: threshold or null
      bars.forEach((r,i)=>{const hh=Math.max(prog>0?1:0,D.HB[i]/mx*h*prog);r.setAttribute('y',y+h-hh);r.setAttribute('height',hh);
        const c=(T!=null&&colorize)?((i*D.BW+D.BW/2)>T?'#e3a7a0':'#7fa4cf'):'#9fb9d9';r.setAttribute('fill',c)});
      if(T==null){line.style.opacity=0}else{line.style.opacity=1;const px=x+T/xmaxv*w;line.setAttribute('x1',px);line.setAttribute('x2',px)}}};
}
// ---- z-stack helpers (assets2/data3.js: ZSB = 60x256x256 uint8, D3 = metadata/correlations) ----
function ZDEC(){if(window.ZS)return window.ZS;const b=atob(window.ZSB);const n=b.length,a=new Uint8Array(n);for(let i=0;i<n;i++)a[i]=b.charCodeAt(i);window.ZS=a;return a}
function zDraw(cv,z){if(cv._z===z)return;cv._z=z;const g=cv.getContext('2d');const id=cv._id||(cv._id=g.createImageData(256,256));const Z=ZDEC(),o=z*65536,d=id.data;for(let i=0;i<65536;i++){const v=Z[o+i];d[i*4]=d[i*4+1]=d[i*4+2]=v;d[i*4+3]=255}g.putImageData(id,0,0)}
function zCanvas(z,size,css){const cv=document.createElement('canvas');cv.width=256;cv.height=256;cv.style.cssText=`image-rendering:pixelated;width:${size}px;height:${size}px;`+(css||'');zDraw(cv,z);return cv}
function xzCanvas(row,w,css){const cv=document.createElement('canvas');cv.width=256;cv.height=60;const hh=60*(0.29/0.26)*w/256;cv.style.cssText=`image-rendering:pixelated;width:${w}px;height:${hh.toFixed(1)}px;`+(css||'');const g=cv.getContext('2d');const id=g.createImageData(256,60);const Z=ZDEC();for(let z=0;z<60;z++)for(let x=0;x<256;x++){const v=Z[z*65536+row*256+x],o=(z*256+x)*4;id.data[o]=id.data[o+1]=id.data[o+2]=v;id.data[o+3]=255}g.putImageData(id,0,0);cv._h=hh;return cv}
function STACK3D(S,x,y,size,o){
  o=o||{};const zl=o.zs||[0,6,12,18,24,30,36,42,48,54],gap=o.gap||38,rx=o.rx==null?58:o.rx,rz=o.rz==null?-30:o.rz;
  const root=document.createElement('div');root.style.cssText=`position:absolute;left:${x}px;top:${y}px;width:${size}px;height:${size}px;perspective:2200px;perspective-origin:50% 35%`;S.appendChild(root);
  const inner=document.createElement('div');inner.style.cssText=`position:absolute;left:0;top:0;width:${size}px;height:${size}px;transform-style:preserve-3d;transform:rotateX(${rx}deg) rotateZ(${rz}deg)`;root.appendChild(inner);
  const zmin=zl[0],zmax=zl[zl.length-1],total=(zl.length-1)*gap;
  const zpos=z=>(zmax-z)/(zmax-zmin)*total;
  const planes=zl.map(z=>{const cv=zCanvas(z,size,'position:absolute;left:0;top:0;border:3px solid #183b32;border-radius:3px;box-sizing:border-box;opacity:0');inner.appendChild(cv);return {cv,z}});
  const frame=document.createElement('div');frame.style.cssText=`position:absolute;left:0;top:0;width:${size}px;height:${size}px;border:6px solid ${COR};background:rgba(183,109,102,.20);box-sizing:border-box;border-radius:3px;opacity:0`;inner.appendChild(frame);
  const col=document.createElement('div');col.style.cssText=`position:absolute;width:10px;height:10px;border-radius:5px;background:${COR};opacity:0`;inner.appendChild(col);
  return {root,inner,planes,frame,total,zpos,
    setPlane(i,p){const pl=planes[i];pl.cv.style.opacity=p;pl.cv.style.transform=`translateZ(${(zpos(pl.z)+(1-p)*90).toFixed(1)}px)`},
    setFrame(z,a){frame.style.opacity=a;frame.style.transform=`translateZ(${(zpos(z)+2).toFixed(1)}px)`}};
}
