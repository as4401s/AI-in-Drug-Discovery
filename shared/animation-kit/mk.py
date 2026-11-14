import os
SHELL='''<!doctype html><html><head><meta charset="utf-8"><link rel="stylesheet" href="../../lib/wb.css"></head>
<body><div id="canvas"></div>
<script src="../../lib/wb.js"></script><script src="../../assets3/icons.js"></script><script src="../../lib/bio.js"></script><script src="../../lib/dsl.js"></script>
<script>
const ic=(k,x,y,w,a,o)=>Object.assign({t:'icon',k,x,y,w,a},o||{});
const ch=(text,x,y,col,a,o)=>Object.assign({t:'chip',text,x,y,col,a},o||{});
const cd=(cls,x,y,w,h,a,o)=>Object.assign({t:'card',cls,x,y,w,h,a},o||{});
const tt=(html,x,y,w,css,a,o)=>Object.assign({t:'text',html,x,y,w,css:css||'font:600 28px/1.25 Inter;color:'+INK,a},o||{});
const ar=(x1,y1,x2,y2,col,a,o)=>Object.assign({t:'arrow',x1,y1,x2,y2,col,a},o||{});
const dt=(pts,col,a,o)=>Object.assign({t:'dots',pts,col,a},o||{});
const rg=(x,y,col,a,o)=>Object.assign({t:'ring',x,y,col,a},o||{});
const tl=(seq,x,y,w,a,o)=>Object.assign({t:'tiles',seq,x,y,w,a},o||{});
const tk=(x,y,a,o)=>Object.assign({t:'tick',x,y,a},o||{});
const br=(x,y,w,h,col,a,o)=>Object.assign({t:'bar',x,y,w,h,col,a},o||{});
const T1='font:700 36px/1.1 Poppins;color:'+INK, T2='font:700 30px/1.15 Poppins;color:'+INK, BIG=(n)=>'font:700 '+n+'px/1 Poppins;color:'+INK;
SCENE_INIT(%(meta)s,(S,C)=>{
%(spec)s
const upd=DSL(S,C,SPEC);return function update(t){upd(t)};
});
</script></body></html>
'''
def mk(d,part,ptitle,title,foot,spec,ep=1):
    os.makedirs(f'/home/claude/work/scenes/{d}',exist_ok=True)
    meta="{ep:1,part:%d,partTitle:%r,title:%r,foot:%r}"%(part,ptitle,title,foot)
    import json
    meta="{ep:%d,part:%d,partTitle:%s,title:%s,foot:%s}"%(ep,part,json.dumps(ptitle),json.dumps(title),json.dumps(foot))
    open(f'/home/claude/work/scenes/{d}/scene.html','w').write(SHELL%dict(meta=meta,spec=spec))
