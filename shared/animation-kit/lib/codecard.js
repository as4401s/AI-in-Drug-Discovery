// Large, readable code card with per-line highlight windows (real source lines, real line numbers)
function CODECARD(S,cfg){
  const {el,at,out}=WB;const INK='#183b32',MUT='#60716a';
  const x=cfg.x||1200,y=cfg.y||222,w=cfg.w||640;
  const card=el('div','box');at(card,x,y,w,cfg.h);card.style.cssText+=';background:#f6f8f7;border:3px solid #d4ded9;border-radius:22px';
  const head=el('div','t','');head.innerHTML=cfg.title||'esm2_demo.py';head.style.cssText+=`;font:600 24px/1 Inter;color:${INK}`;at(head,x+24,y+18);
  const sub=el('div','t',cfg.sub||'Real source from the companion code');sub.style.cssText+=`;font:400 21px/1 Inter;color:${MUT}`;at(sub,x+24,y+50);
  let yy=y+92;
  const lines=cfg.lines.map(L=>{
    const row=el('div','',null);row.style.cssText=`position:absolute;left:${x+10}px;top:${yy}px;width:${w-20}px;display:flex;font:500 ${cfg.fs||21}px/${cfg.lh||30}px "DejaVu Sans Mono","Liberation Mono",monospace;color:${INK};border-radius:8px;padding:2px 0`;
    const num=document.createElement('div');num.textContent=L.n;num.style.cssText='width:56px;flex:none;text-align:right;color:#8a9a93;padding-right:14px';
    const txt=document.createElement('div');txt.textContent=L.t;txt.style.cssText=`white-space:pre-wrap;overflow-wrap:anywhere;flex:1;padding-left:${(L.ind||0)*12.6}px;text-indent:0`;
    row.appendChild(num);row.appendChild(txt);
    if(cfg.measure){yy+=row.offsetHeight+4+(L.gap||0)}
    else{const nlines=Math.max(1,Math.ceil((L.t.length+(L.ind||0))/ (cfg.cpl||43)));
    yy+=nlines*(cfg.lh||30)+4+(L.gap||0);}
    return {row,L};
  });
  return {card,head,sub,lines,bottom:yy,
    update(t,fadeIn){
      const a=fadeIn==null?1:fadeIn;card.style.opacity=a;head.style.opacity=a;sub.style.opacity=a;
      lines.forEach(({row,L})=>{const hl=(L.hl||[]).reduce((m,[a0,a1])=>Math.max(m,out(t,a0,.4)*(1-out(t,a1,.4))),0);
        row.style.opacity=a*(0.45+0.55*Math.max(hl,L.always?1:0));row.style.background=`rgba(255,214,110,${(0.55*hl).toFixed(3)})`})}
  };
}
