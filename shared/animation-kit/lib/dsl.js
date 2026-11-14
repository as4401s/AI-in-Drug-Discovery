// Declarative scene kit: DSL(S,C,spec) builds timed elements from data.  All motion goes through WB.out/lin/track.
// time expr: number | 'c_cue' | 'c_cue+1.2' | 'c_cue-0.3'
function DSL(S,C,spec){
  const {out,lin,mix,track}=WB;
  const cue=k=>Math.max(C[k],0.05);
  const T=v=>{if(v==null)return null;if(typeof v==='number')return v;const m=/^([A-Za-z0-9_]+)([+-][0-9.]+)?$/.exec(v);if(!m)throw new Error('bad time '+v);return cue(m[1])+(m[2]?parseFloat(m[2]):0)};
  const cols={g:GRN,c:COR,b:BLU,a:'#e0a43a',l:LAV,m:MINT,i:INK};
  const colOf=v=>cols[v]||v||GRN;
  const markers={};
  const mk=(col)=>{if(markers[col])return markers[col];const id='dm'+Object.keys(markers).length;const sv=svgLayer(S);sv.style.display='none';/*defs holder*/arrowDefs(sv,id,col);document.body.appendChild(sv);sv.style.position='absolute';markers[col]=id;return id};
  const defs=svgLayer(S);defs.style.zIndex=0;
  const els=[];
  const notes=spec.notes?NOTES({x:spec.notes.x,y:spec.notes.y,w:spec.notes.w,h:spec.notes.h,tfs:spec.notes.tfs||30,bfs:spec.notes.bfs||28,cls:spec.notes.cls,notes:spec.notes.list.map((n,i,arr)=>({a:cue(n[0]),b:i<arr.length-1?cue(arr[i+1][0])-.1:null,title:n[1],body:n[2]}))}):null;
  spec.els.forEach(sp=>{
    const e={sp,a:T(sp.a),b:T(sp.b),d:sp.d||.5};if(e.a==null)e.a=0.05;
    const type=sp.t;
    if(type=='icon'){e.ic=ico(sp.k,sp.x,sp.y,sp.w,{css:sp.css});}
    else if(type=='chip'){e.el=chip(sp.text,sp.x,sp.y,sp.col||'mint',{fs:sp.fs||28,px:sp.px,py:sp.py});}
    else if(type=='card'){e.el=box(sp.cls||'b-mint',sp.x,sp.y,sp.w,sp.h);if(sp.css)e.el.style.cssText+=';'+sp.css}
    else if(type=='text'){const css=(sp.css||'font:600 28px/1.25 Inter;color:'+INK);e.el=sp.c===false?tx(css+';white-space:normal',sp.html,sp.x,sp.y,sp.w):ctx(css,sp.html,sp.x,sp.y,sp.w)}
    else if(type=='arrow'){const col=colOf(sp.col);const sv=svgLayer(S);const id='da'+Math.random().toString(36).slice(2,7);arrowDefs(sv,id,col);e.sv=sv;e.p=WB.svg('path',{d:sp.d||`M${sp.x1} ${sp.y1} L ${sp.x2} ${sp.y2}`,stroke:col,'stroke-width':sp.w||8,fill:'none','stroke-linecap':'round','marker-end':sp.head===false?'':'url(#'+id+')','stroke-dasharray':sp.dash||''},sv);e.p0=sp.dash||''}
    else if(type=='dots'){const sv=svgLayer(S);e.sv=sv;e.path=WB.svg('path',{d:'M'+sp.pts.map(p=>p.join(' ')).join(' L '),fill:'none',stroke:sp.trail?colOf(sp.col):'none','stroke-width':sp.trail||0,opacity:sp.trailOp||.35,'stroke-linecap':'round','stroke-linejoin':'round'},sv);e.L=e.path.getTotalLength();e.cs=[];for(let i=0;i<(sp.n||3);i++)e.cs.push(WB.svg('circle',{r:sp.r||12,fill:colOf(sp.col||'c'),stroke:'#fff','stroke-width':4},sv))}
    else if(type=='bar'){e.el=box('',sp.x,sp.y,sp.w,sp.h);e.el.style.cssText+=`;background:${colOf(sp.col)};border-radius:${sp.r!=null?sp.r:10}px;opacity:0;transform-origin:${sp.dir=='right'?'left center':'bottom center'}`}
    else if(type=='ring'){const sv=svgLayer(S);e.sv=sv;e.c=WB.svg('circle',{fill:'none','stroke-width':sp.sw||8,stroke:colOf(sp.col)},sv)}
    else if(type=='tick'){const sv=svgLayer(S);e.sv=sv;const g=WB.svg('g',{},sv);e.g=g;WB.svg('circle',{cx:sp.x,cy:sp.y,r:sp.r||26,fill:'#4d8f7e',stroke:'#fff','stroke-width':4},g);const r=(sp.r||26)/26;WB.svg('path',{d:`M${sp.x-12*r} ${sp.y} L ${sp.x-3*r} ${sp.y+10*r} L ${sp.x+13*r} ${sp.y-12*r}`,stroke:'#fff','stroke-width':6*r,fill:'none','stroke-linecap':'round','stroke-linejoin':'round'},g)}
    else if(type=='tiles'){e.tl=[...sp.seq].map((l,i)=>{const el=tile(l,sp.x+i*(sp.w+(sp.gap||12)),sp.y,sp.w,{fs:sp.fs});if(sp.neutral||sp.pal){const P=PAL[sp.pal||'blue'];el.style.background=P[0];el.style.borderColor=P[1]}return el})}
    else if(type=='cross'){const sv=svgLayer(S);e.sv=sv;e.p=WB.svg('path',{d:`M${sp.x1} ${sp.y1} L ${sp.x2} ${sp.y2} M${sp.x1} ${sp.y2} L ${sp.x2} ${sp.y1}`,stroke:COR,'stroke-width':sp.w||10,'stroke-linecap':'round',fill:'none'},sv)}
    else if(type=='box'){e.el=box('',sp.x,sp.y,sp.w,sp.h);e.el.style.cssText+=';'+sp.css+';opacity:0'}
    else if(type=='segs'){e.segs=[0,1,2,3].map(i=>{const b=box('',sp.x+i*(sp.w+14),sp.y,sp.w,12);b.style.cssText+=';border-radius:6px;background:#cfd9d4;opacity:0';const f=box('',sp.x+i*(sp.w+14),sp.y,0,12);f.style.cssText+=';border-radius:6px;background:#26765d';return {b,f}})}
    else if(type=='wave'){const sv=svgLayer(S);e.sv=sv;e.p=WB.svg('path',{fill:'none',stroke:colOf(sp.col),'stroke-width':sp.w||6,'stroke-linecap':'round','stroke-linejoin':'round'},sv)}
    else if(type=='grid'){const R=sp.vals.length,Cn=sp.vals[0].length;e.cells=[];const gap=sp.gap==null?4:sp.gap;for(let r=0;r<R;r++)for(let c=0;c<Cn;c++){const el=box('',sp.x+c*sp.cw,sp.y+r*sp.ch,sp.cw-gap,sp.ch-gap);el.style.cssText+=';border-radius:6px;opacity:0;display:flex;align-items:center;justify-content:center;box-sizing:border-box;font:600 '+(sp.fs||20)+'px Inter';e.cells.push({el,r,c})}}
    els.push(e);
  });
  return function(t){
    if(notes)notes.update(t);
    els.forEach(e=>{const sp=e.sp,a=e.a,b=e.b;const o=out(t,a,e.d)*(b==null?1:(1-out(t,b,.4)));const type=sp.t;
      const bob=sp.bob?track(Math.sin(t*1.5+(sp.ph||0))*sp.bob)*o:0;
      if(type=='icon'){const p=out(t,a,sp.dd||.7);let x=sp.dx?(1-p)*sp.dx:0,y=(sp.dy!=null?(1-p)*sp.dy:0)+bob;let s=(sp.s0!=null?sp.s0:.8)+(1-(sp.s0!=null?sp.s0:.8))*p;
        if(sp.mv){const m=sp.mv;const q=out(t,T(m.a),m.dur||1.2);x+=(m.dx||0)*q;y+=(m.dy||0)*q;if(m.s!=null)s*=mix(1,m.s,q)}
        if(sp.shake){const sh=lin(t,T(sp.shake),.6);if(sh>0&&sh<1)x+=track(Math.sin(t*40)*6)}
        if(sp.spin)y+=0;
        e.ic.set({op:o*(sp.op==null?1:sp.op),x,y,s,r:sp.rot?track(Math.sin(t*1.3)*sp.rot)*o:0})}
      else if(type=='chip'||type=='card'||type=='text'||type=='box'){const el=e.el;const p=out(t,a,e.d);const dy=sp.dy==null?(type=='card'?18:8):sp.dy,dx=sp.dx||0;el.style.opacity=o*(sp.op==null?1:sp.op);let tr=`translate(${((1-p)*dx).toFixed(1)}px,${((1-p)*dy+bob).toFixed(1)}px)`;if(sp.s0!=null)tr+=` scale(${(sp.s0+(1-sp.s0)*p).toFixed(3)})`;el.style.transform=tr;if(sp.pulse)el.style.opacity=o*(.65+.35*track(Math.sin(t*4)*.5+.5))}
      else if(type=='arrow'){const g=out(t,a,sp.dur||.7);const L=e.p._L||(e.p._L=e.p.getTotalLength());if(!e.p0){e.p.setAttribute('stroke-dasharray',L);e.p.setAttribute('stroke-dashoffset',L*(1-g))}else{e.p.setAttribute('clip-path','')}e.p.style.opacity=(g>0?1:0)*(b==null?1:(1-out(t,b,.4)));if(e.p0){e.p.style.opacity=o*(g>0?1:0)}}
      else if(type=='dots'){const sp2=sp;const n=e.cs.length;e.cs.forEach((cc,i)=>{const q=track(((t-a)*(sp2.speed||.3)+i/n)%1);const pt=e.path.getPointAtLength(e.L*q);cc.setAttribute('cx',pt.x);cc.setAttribute('cy',pt.y);const env=sp2.env===false?1:Math.min(1,Math.sin(Math.PI*q)*4);cc.style.opacity=o*env});e.path.style.opacity=o*(sp2.trail?1:0)}
      else if(type=='bar'){const v=typeof sp.val=='function'?sp.val(t-a):Array.isArray(sp.val)?mix(sp.val[0],sp.val[1],out(t,T(sp.vt)||a,sp.vd||1)):sp.val;const g=out(t,a,.6);const el=e.el;if(sp.dir=='right'){el.style.width=(v*sp.w).toFixed(1)+'px';el.style.height=sp.h+'px'}else if(sp.dir=='down'){el.style.height=(sp.h*v).toFixed(1)+'px';el.style.top=sp.y+'px';el.style.transformOrigin='top center'}else{const h=sp.h*v;el.style.height=h.toFixed(1)+'px';el.style.top=(sp.y+sp.h-h).toFixed(1)+'px'}el.style.opacity=g*(b==null?1:(1-out(t,b,.4)));if(sp.recol){el.style.background=v>sp.recol[0]?colOf(sp.recol[1]):colOf(sp.col)}}
      else if(type=='ring'){const per=sp.every||1.6,tt=t-a;const p=tt<0?0:((tt%per)/(sp.dur||1.3));const pp=Math.min(1,p);const on=(b==null||t<b)&&tt>=0&&(sp.n==null||tt<per*sp.n);e.c.setAttribute('cx',sp.x);e.c.setAttribute('cy',sp.y);e.c.setAttribute('r',(sp.r0||20)+((sp.r1||80)-(sp.r0||20))*track(pp));e.c.style.opacity=on&&pp<1?(1-pp)*.9:0}
      else if(type=='tick'){e.g.setAttribute('opacity',o);}
      else if(type=='tiles'){e.tl.forEach((el,i)=>{const p=out(t,a+(sp.stag||.12)*i,.4);el.style.opacity=p*(b==null?1:(1-out(t,b,.4)));el.style.transform=`translateY(${((1-p)*(sp.dy||30)).toFixed(1)}px) scale(${(.6+.4*p).toFixed(3)})`;if(sp.hot&&sp.hot.indexOf(i)>=0){const h=out(t,T(sp.ht)||a,.4);el.style.boxShadow=`0 0 0 ${(7*h).toFixed(1)}px rgba(224,164,58,.55)`}})}
      else if(type=='cross'){const g=out(t,a,.4);e.p.style.opacity=g*(b==null?1:(1-out(t,b,.4)))}
      else if(type=='segs'){e.segs.forEach((s,i)=>{s.b.style.opacity=out(t,a+i*.1,.4);s.f.style.width=(i<sp.fill-1?sp.w:(i==sp.fill-1?sp.w*out(t,a+.7,1.2):0))+'px'})}
      else if(type=='wave'){const g=out(t,a,sp.dur||1.0);const L=(sp.len||600)*g;const ph=track((sp.speed||4)*t)*(sp.dir||1);const wl=sp.wl||60,amp=sp.amp||20;const pts=[];for(let x=0;x<=L;x+=4){pts.push((sp.x+x).toFixed(1)+' '+(sp.y+amp*Math.sin(2*Math.PI*x/wl-ph)).toFixed(1))}if(pts.length<2)pts.push(pts[0]||(sp.x+' '+sp.y));e.p.setAttribute('d','M'+pts.join(' L'));e.p.style.opacity=o>0?o:0}
      else if(type=='grid'){const v2=sp.merge?null:sp.vals2,vq=v2?out(t,T(sp.vt),sp.vd||1.2):0;const gray=sp.mode=='gray';e.cells.forEach((cl,i)=>{const p=out(t,a+(sp.stag==null?.03:sp.stag)*i,.35);let v=sp.vals[cl.r][cl.c];if(v2)v=mix(v,v2[cl.r][cl.c],vq);const vv=Math.max(0,Math.min(1,v));let bg;if(sp.merge){const P=sp.tint,Q=sp.tint2,A1=sp.vals[cl.r][cl.c],B1=sp.vals2[cl.r][cl.c];bg='rgb('+[0,1,2].map(k=>Math.min(255,Math.round(14+P[k]*A1+Q[k]*B1))).join(',')+')'}else if(sp.tint){bg='rgb('+[0,1,2].map(k=>Math.round(14+(sp.tint[k]-14)*vv)).join(',')+')'}else if(gray){const g=Math.round(18+230*vv);bg='rgb('+g+','+g+','+g+')'}else{const A=[228,241,235],B=[38,118,93];bg='rgb('+[0,1,2].map(k=>Math.round(A[k]+(B[k]-A[k])*vv)).join(',')+')'}const st=cl.el.style;st.opacity=(p*(b==null?1:(1-out(t,b,.4)))).toFixed(3);st.background=bg;st.transform='scale('+(.7+.3*p).toFixed(3)+')';if(sp.num){cl.el.textContent=Math.round(vv*sp.num);st.color=(gray?vv<.55:vv>.55)?'#ffffff':'#183b32'}const hot=sp.hot&&sp.hot.some(h=>h[0]==cl.r&&h[1]==cl.c);st.boxShadow=hot?'0 0 0 '+(6*out(t,T(sp.ht)||a,.4)).toFixed(1)+'px rgba(224,164,58,.7)':'none'})}
    });
  };
}
