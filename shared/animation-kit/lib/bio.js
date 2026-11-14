// Shared building blocks for the animated biology / intro / lab scenes (assets3/icons.js provides window.ICON).
const INK='#183b32',MUT='#60716a',GRN='#26765d',COR='#b76d66',BLU='#557eaf',AMB='#ac8b42',LAV='#8b75b0',MINT='#4d8f7e';
const PAL={blue:['#e3efff','#557eaf'],coral:['#fbe6e3','#b76d66'],lav:['#ece6fb','#8b75b0'],amber:['#fff0cf','#ac8b42'],mint:['#dff2ec','#4d8f7e']};
const BASEC={A:PAL.amber,T:PAL.coral,C:PAL.blue,G:PAL.mint,U:PAL.lav};
const COMP={A:'T',T:'A',C:'G',G:'C'},RNAC={A:'U',T:'A',C:'G',G:'C'};
const NS='http://www.w3.org/2000/svg';
function box(cls,x,y,w,h){const b=WB.el('div','box '+cls);WB.at(b,x,y,w,h);return b}
function tx(css,html,x,y,w){const e=WB.el('div','t');e.style.cssText+=';'+css;e.innerHTML=html;WB.at(e,x,y,w);return e}
// centre-anchored text
function ctx(css,html,cx,cy,w){const e=WB.el('div','t');e.style.cssText+=';text-align:center;white-space:normal;'+css;e.innerHTML=html;e.style.width=w+'px';e.style.left=(cx-w/2)+'px';e.style.top=cy+'px';return e}
// icon image, centre-anchored; set({x,y,s,r,op}) offsets are relative to its home position
function ico(key,cx,cy,w,o){o=o||{};const I=ICON[key];if(!I)throw new Error('no icon '+key);const h=w*I.h/I.w;
  const e=document.createElement('img');e.src='../../assets3/'+I.f;e.style.cssText=`position:absolute;left:${cx-w/2}px;top:${cy-h/2}px;width:${w}px;height:${h}px;opacity:0;pointer-events:none;`+(o.css||'');
  (o.parent||document.getElementById('stage')).appendChild(e);
  const s={e,cx,cy,w,h,set(p){p=p||{};const x=p.x||0,y=p.y||0,sc=p.s==null?1:p.s,r=p.r||0;e.style.transform=`translate(${x}px,${y}px) rotate(${r}deg) scale(${sc})`;e.style.opacity=p.op==null?1:p.op;if(p.z!=null)e.style.zIndex=p.z},
    at(x,y){e.style.left=(x-w/2)+'px';e.style.top=(y-h/2)+'px'}};return s}
// fade in at a, out at b (b may be null); optional rise dy
function life(e,t,a,b,o){o=o||{};const d=o.d||.5,i=WB.out(t,a,d),k=b==null?0:WB.out(t,b,o.dout||.4);const op=Math.max(0,i*(1-k));
  e.style.opacity=op;const dy=o.dy==null?12:o.dy,dx=o.dx||0,sc=o.s;let tr=`translate(${((1-i)*dx).toFixed(1)}px,${((1-i)*dy).toFixed(1)}px)`;if(sc!=null)tr+=` scale(${(WB.mix(sc,1,i)).toFixed(3)})`;if(o.keep)tr+=' '+o.keep;e.style.transform=tr;return op}
// pill label, centre-anchored
function chip(text,cx,cy,col,o){o=o||{};const P=PAL[col]||PAL.mint;const e=WB.el('div','t');e.style.cssText+=`;background:${P[0]};border:3px solid ${P[1]};border-radius:${o.r||30}px;padding:${o.py||8}px ${o.px||20}px;font:600 ${o.fs||26}px/1.2 Inter;color:${INK};white-space:nowrap;`+(o.css||'');e.innerHTML=text;
  const w=e.offsetWidth;e.style.left=(cx-w/2)+'px';e.style.top=(cy-(o.h||24))+'px';e._w=w;return e}
function svgLayer(S){return WB.svg('svg',{width:1920,height:1080,style:'position:absolute;left:0;top:0;overflow:visible'},S)}
function arrowDefs(sv,id,col){const d=WB.svg('defs',{},sv);const m=WB.svg('marker',{id,viewBox:'0 0 10 10',refX:7,refY:5,markerWidth:5.5,markerHeight:5.5,orient:'auto'},d);WB.svg('path',{d:'M0 0L10 5L0 10z',fill:col},m)}
// progressively drawn path (0..1)
function pathGrow(p,v){const L=p._L||(p._L=p.getTotalLength());p.setAttribute('stroke-dasharray',L);p.setAttribute('stroke-dashoffset',L*(1-v));p.style.opacity=v>0?1:0}
function lerpPt(a,b,p){return [a[0]+(b[0]-a[0])*p,a[1]+(b[1]-a[1])*p]}
// base letter tile
function tile(letter,x,y,w,o){o=o||{};const P=BASEC[letter]||PAL.blue;const e=WB.el('div','t c');e.style.cssText+=`;left:${x}px;top:${y}px;width:${w}px;height:${o.h||w}px;border-radius:${o.r||Math.round(w*.2)}px;background:${P[0]};border:${o.bw||3}px solid ${P[1]};font:700 ${o.fs||Math.round(w*.52)}px/${(o.h||w)-(o.bw||3)*2}px Poppins;color:${INK};opacity:0`;e.textContent=letter;return e}
// double helix (vertical or horizontal).  returns {sv,draw({phase,grow,x0,x1})}
function helix(S,x,y,len,amp,o){o=o||{};const vert=o.vertical!==false,k=o.turns||3,steps=o.steps||90,rung=o.rungs||16;
  const sv=WB.svg('svg',{width:1920,height:1080,style:'position:absolute;left:0;top:0;overflow:visible'},S);
  const c1=o.c1||'#557eaf',c2=o.c2||'#b76d66',sw=o.sw||11;
  const back=WB.svg('g',{},sv),rungs=[],fr=WB.svg('g',{},sv);
  const pA=WB.svg('polyline',{fill:'none',stroke:c1,'stroke-width':sw,'stroke-linecap':'round','stroke-linejoin':'round'},sv);
  const pB=WB.svg('polyline',{fill:'none',stroke:c2,'stroke-width':sw,'stroke-linecap':'round','stroke-linejoin':'round'},sv);
  const R=[];for(let i=0;i<rung;i++){const l=WB.svg('line',{stroke:'#8aa59b','stroke-width':sw*.55,'stroke-linecap':'round'},back);R.push(l)}
  const pt=(u,ph,sg)=>{const a=u*k*2*Math.PI+ph,off=Math.sin(a)*amp*sg,dep=Math.cos(a)*sg;return vert?[x+off,y+u*len,dep]:[x+u*len,y+off,dep]};
  return {sv,draw(p){p=p||{};const ph=p.phase||0,g=p.grow==null?1:p.grow,op=p.op==null?1:p.op;sv.style.opacity=op;
    const a=[],b=[];const n=Math.max(2,Math.round(steps*g));for(let i=0;i<=n;i++){const u=g*i/n;const A=pt(u,ph,1),B=pt(u,ph,-1);a.push(A[0].toFixed(1)+','+A[1].toFixed(1));b.push(B[0].toFixed(1)+','+B[1].toFixed(1))}
    pA.setAttribute('points',a.join(' '));pB.setAttribute('points',b.join(' '));
    R.forEach((l,i)=>{const u=(i+.5)/rung;if(u>g){l.style.opacity=0;return}const A=pt(u,ph,1),B=pt(u,ph,-1);l.style.opacity=1;l.setAttribute('x1',A[0]);l.setAttribute('y1',A[1]);l.setAttribute('x2',B[0]);l.setAttribute('y2',B[1])})}}}
// positions inside the 004-animal-cell illustration (fractions of its width/height)
const CELLPT={nuc:[.38,.42],mito1:[.70,.28],mito2:[.22,.62],er:[.62,.60],rim:[.88,.50],rimL:[.08,.50],rimT:[.5,.13],rimB:[.5,.9]};
function cellAt(ic,k){const p=typeof k==='string'?CELLPT[k]:k;return [ic.cx-ic.w/2+p[0]*ic.w,ic.cy-ic.h/2+p[1]*ic.h]}
// pulse ring (svg circle), p 0..1
function ringSet(r,cx,cy,rad0,rad1,p,op){r.setAttribute('cx',cx);r.setAttribute('cy',cy);r.setAttribute('r',rad0+(rad1-rad0)*p);r.style.opacity=(op==null?1:op)*(p<=0?0:1-p*.85)}
// leader line: from (x1,y1) to (x2,y2), grown by p
function lineSet(l,x1,y1,x2,y2,p){l.setAttribute('x1',x1);l.setAttribute('y1',y1);l.setAttribute('x2',x1+(x2-x1)*p);l.setAttribute('y2',y1+(y2-y1)*p);l.style.opacity=p>0?1:0}
// rolling note box: notes=[{a,b,title,body}], appears with first note; one note visible at a time
function NOTES(cfg){const {out,show}=WB;const {x,y,w,h,notes}=cfg;const bx=box(cfg.cls||'b-amber',x,y,w,h);
  const els=notes.map(n=>{const wrap=tx('white-space:normal',`<div style="font:700 ${cfg.tfs||32}px/1.2 Poppins;color:${INK};margin-bottom:12px">${n.title||''}</div><div style="font:500 ${cfg.bfs||30}px/1.35 Inter;color:${INK}">${n.body||''}</div>`,x+28,y+24,w-56);return {wrap,n}});
  return {bx,update(t){show(bx,t,notes[0].a-.2,.6,{dy:0});els.forEach(({wrap,n})=>{const nx=n.b==null?999:n.b;const a=WB.out(t,n.a,.4)*(1-WB.out(t,nx,.4));wrap.style.opacity=a;wrap.style.transform=`translateY(${((1-a)*8).toFixed(1)}px)`})}}}
function pulseRing(r,x,y,t,a,dur,rad0,rad1,col){const p=WB.lin(t,a,dur||1.2);r.setAttribute('cx',x);r.setAttribute('cy',y);r.setAttribute('r',(rad0||14)+((rad1||60)-(rad0||14))*p);r.setAttribute('stroke',col||GRN);r.style.opacity=(p<=0||p>=1)?0:(1-p)*.9}
