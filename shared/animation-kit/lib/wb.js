// Deterministic, time-driven scene helpers.  Every animated value must flow through ramp()/lin()/track()
// so renderAt(t) can return a stamp: identical stamp => identical pixels => no new screenshot needed.
const RS={sum:7};
function stampAdd(v){RS.sum=(RS.sum*131+Math.round(v*2000)+17)%1000000007}
const WB={
  clamp:(x,a=0,b=1)=>Math.min(b,Math.max(a,x)),
  ease:x=>x<.5?4*x*x*x:1-Math.pow(-2*x+2,3)/2,
  easeOut:x=>1-Math.pow(1-x,3),
  ramp(t,a,d=.6){const p=WB.clamp((t-a)/d);stampAdd(p);return WB.ease(p)},
  out(t,a,d=.6){const p=WB.clamp((t-a)/d);stampAdd(p);return WB.easeOut(p)},
  lin(t,a,d){const p=WB.clamp((t-a)/d);stampAdd(p);return p},
  track(v){stampAdd(v);return v},
  mix:(a,b,p)=>a+(b-a)*p,
  el(tag,cls,html,parent){const e=document.createElement(tag);if(cls)e.className=cls;if(html!=null)e.innerHTML=html;(parent||document.getElementById('stage')).appendChild(e);return e},
  svg(tag,attrs,parent){const e=document.createElementNS('http://www.w3.org/2000/svg',tag);for(const k in attrs)e.setAttribute(k,attrs[k]);if(parent)parent.appendChild(e);return e},
  at(e,x,y,w,h){e.style.left=x+'px';e.style.top=y+'px';if(w!=null)e.style.width=w+'px';if(h!=null)e.style.height=h+'px';return e},
  show(e,t,a,d=.6,o={}){const p=WB.out(t,a,d);const dy=o.dy==null?16:o.dy,dx=o.dx||0,s=o.scale;e.style.opacity=p;let tr=`translate(${(1-p)*dx}px,${(1-p)*dy}px)`;if(s!=null)tr+=` scale(${WB.mix(s,1,p)})`;e.style.transform=tr;return p},
  fmt:(v,n=3)=>v.toFixed(n),
};
function SCENE_INIT(meta,builder){
  const cv=document.getElementById('canvas');
  const parts=['','Biology foundations'];
  WB.el('div','wm','WhiskerBrief',cv);
  WB.el('div','ep','AI in Drug Discovery · '+meta.ep,cv);
  const pl=WB.el('div','partlbl',meta.part?('Part '+meta.part+' of 4 · '+meta.partTitle):meta.partTitle,cv);
  if(meta.part)for(let i=0;i<4;i++){const s=WB.el('div','seg'+(i<meta.part?' on':''),'',cv);s.style.left=(1390+i*115)+'px'}
  WB.el('div','hrule','',cv);WB.el('div','frule','',cv);
  WB.el('div','title',meta.title,cv);
  WB.el('div','foot',meta.foot||'',cv);
  const stage=WB.el('div','',null,cv);stage.id='stage';
  stage.style.zIndex=2;
  const update=builder(stage,window.CUES||{});
  window.renderAt=(t)=>{RS.sum=7;update(t);return RS.sum};
  Promise.all([document.fonts.load('700 70px Poppins'),document.fonts.load('400 30px Inter'),document.fonts.load('500 30px Inter'),document.fonts.ready,...[...document.images].map(i=>i.decode?i.decode().catch(()=>{}):0)]).then(()=>{window.renderAt(0);window.ready=true});
}
