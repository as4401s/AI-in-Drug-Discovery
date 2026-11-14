import sys
sys.path.insert(0,'/home/claude/work/scenes')
from mk import mk
from cuespec import build
P0='Introduction and contents'
# ---------------- ep2 question ----------------
cellsL=[(220,400),(360,490),(500,380),(640,520),(760,420),(420,610),(600,630),(250,600)]
cellsR=[(1190,410,-18),(1380,480,12),(1560,390,-8),(1670,540,25),(1250,590,8),(1480,610,-20),(1700,380,15)]
L=''.join("cd('',%d,%d,96,96,'c_one+%.2f',{css:'border-radius:50%%;background:radial-gradient(circle at 35%% 30%%,#d9fff0,#5fd0aa 55%%,#2c8f74);box-shadow:0 0 28px rgba(95,208,170,.7)',dy:0}),\n"%(x-48,y-48,.12*i) for i,(x,y) in enumerate(cellsL))
R=''.join("cd('',%d,%d,170,66,'c_two+%.2f',{css:'border-radius:50%%;background:radial-gradient(circle at 35%% 30%%,#d9fff0,#5fd0aa 55%%,#2c8f74);rotate:%ddeg',dy:0}),\n"%(x-85,y-33,.12*i,r) for i,(x,y,r) in enumerate(cellsR))
OV=''.join("cd('',1060,300,740,400,'c_two+.3',{css:'background:rgba(8,18,15,.30);border-radius:28px',b:'c_exp+%.1f',dy:0}),\n"%(.9+.8*i) for i in range(3))
mk('e2_question',0,P0,'Can we trust a microscope picture?','Teaching example · schematic pictures, not real microscope data','''
const FR='background:#0e1a17;border:6px solid #cfd9d4';
const SPEC={els:[
cd('',120,300,740,400,'c_arrive',{css:FR}),cd('',1060,300,740,400,'c_arrive+.3',{css:FR}),
'''+L+R+OV+'''
ch('bright and round',490,725,'mint','c_one+1.4',{b:'c_med-.3',fs:30}),ch('dim and stretched',1430,725,'coral','c_two+1.4',{b:'c_med-.3',fs:30}),
ch('“picture 2 proves the new medicine works”',1430,226,'amber','c_says',{fs:28,b:'c_before-.3'}),
tt('?',960,400,120,BIG(190),'c_believe',{b:'c_med-.3',pulse:true}),
ch('maybe the medicine changed the cells?',960,725,'mint','c_med',{fs:32,b:'c_cam-.2'}),
ch('camera exposure',520,725,'amber','c_exp-.4',{fs:30,b:'c_before-.3'}),ch('the dye',960,725,'blue','c_dye-.2',{fs:30,b:'c_before-.3'}),ch('how it was displayed',1400,725,'lav','c_disp-.2',{fs:30,b:'c_before-.3'}),
tt('exposure',400,788,160,'font:600 26px Inter;color:'+MUT,'c_exp-.4',{b:'c_before-.3'}),
br(520,812,880,22,'#e0a43a','c_exp-.4',{dir:'right',val:[0,1],vt:'c_exp',vd:2.6,b:'c_before-.3'}),
ch('what does the image actually measure?',960,790,'amber','c_before',{fs:38,b:'c_q-.3'}),
cd('b-mint',80,850,1760,110,'c_q-.1'),tt('How do we turn a picture of biology into evidence we can trust?',960,872,1700,'font:700 40px/1.2 Poppins;color:'+INK,'c_q+.1')
]};''',ep=2)
print(build('e2_question',2,'question',dict(c_arrive='Imagine',c_one='In one',c_two='In the other',c_says='Someone says',c_believe='Would you believe',c_med='Perhaps the medicine',c_cam='But perhaps',c_exp='camera exposure',c_dye='die',c_disp='the way the picture',c_before='Before we ask',c_q="today's question")))

# ---------------- ep2 previous ----------------
mk('e2_previous',0,P0,'Where we are: from sequences to observations','Recap of lesson 1 · schematic icons · bars illustrative','''
const E1='c_notell-.3',E2='c_chain-.3';
const SPEC={els:[
// welcome
cd('b-mint',560,330,800,320,'c_welcome',{b:'c_prev-.3'}),tt('AI in Drug Discovery',960,380,740,'font:700 60px/1.1 Poppins;color:'+INK,'c_welcome+.3',{b:'c_prev-.3'}),
ch('WhiskerBrief course',960,490,'amber','c_welcome+.6',{b:'c_prev-.3',fs:34}),ch('Video 2 · microscopy',960,570,'mint','c_vid',{b:'c_prev-.3',fs:34}),
// recap row
ch('Lesson 1',480,236,'blue','c_prev',{b:E2,fs:30}),
ic('animal-cell',200,370,130,'c_cells',{b:E2,bob:4}),ch('cells',200,445,'coral','c_cells+.2',{b:E2,fs:26}),
ic('dna-helix',420,370,100,'c_dna',{b:E2,bob:4,ph:1}),ch('DNA',420,445,'blue','c_dna+.2',{b:E2,fs:26}),
ic('rna-strand',640,370,130,'c_dna+1.2',{b:E2,bob:4,ph:2}),ch('RNA',640,445,'amber','c_dna+1.4',{b:E2,fs:26}),
ic('folded-protein',860,370,130,'c_prot',{b:E2,bob:4,ph:3}),ch('proteins',860,445,'mint','c_prot+.2',{b:E2,fs:26}),
// model card
cd('b-lav',1040,300,800,420,'c_esm-.2',{b:E2}),tt('small ESM-2 protein model',1440,318,740,T2,'c_esm',{b:E2}),ic('attention-network',1200,540,180,'c_esm+.3',{b:E2,bob:4}),
ar(1310,540,1400,540,'g','c_esm+.9',{b:E2}),
br(1440,590,40,50,'#8b75b0','c_esm+1.1',{val:[0,1],vt:'c_esm+1.1',vd:.6,b:E2}),br(1498,520,40,120,'#8b75b0','c_esm+1.2',{val:[0,1],vt:'c_esm+1.2',vd:.6,b:E2}),br(1556,605,40,35,'#8b75b0','c_esm+1.3',{val:[0,1],vt:'c_esm+1.3',vd:.6,b:E2}),br(1614,550,40,90,'#8b75b0','c_esm+1.4',{val:[0,1],vt:'c_esm+1.4',vd:.6,b:E2}),br(1672,615,40,25,'#8b75b0','c_esm+1.5',{val:[0,1],vt:'c_esm+1.5',vd:.6,b:E2}),br(1730,570,40,70,'#8b75b0','c_esm+1.6',{val:[0,1],vt:'c_esm+1.6',vd:.6,b:E2}),
ch('probabilities for amino acids',1440,665,'lav','c_esm+1.6',{b:E2,fs:26}),
ch('= the model’s sequence preferences',1440,760,'amber','c_pref',{b:E2,fs:30}),
// not answered
cd('b-coral',80,560,420,330,'c_notell-.2',{b:E2}),ic('animal-cell',290,690,150,'c_notell',{b:E2}),tt('a living cell survived a treatment?',290,770,380,T2,'c_notell+.2',{b:E2}),{t:'cross',x1:230,y1:640,x2:350,y2:760,a:'c_notell+.7',b:E2},
cd('b-coral',540,560,420,330,'c_notell+.3',{b:E2}),ic('small-molecule',750,690,170,'c_notell+.5',{b:E2}),tt('a medicine helped a patient?',750,770,380,T2,'c_notell+.7',{b:E2}),{t:'cross',x1:690,y1:640,x2:810,y2:760,a:'c_notell+1.2',b:E2},
ch('not answered by those probabilities',520,925,'amber','c_notell+1.4',{b:E2,fs:28}),
// observations
cd('b-amber',1040,806,800,154,'c_obs-.2',{b:E2}),tt('to answer a biological question: observations',1440,824,760,T2,'c_obs',{b:E2}),ic('microscope',1160,900,100,'c_micro',{b:E2,bob:3}),ch('microscopy is one way to collect them',1530,880,'mint','c_micro+.2',{b:E2,fs:26}),
// chain
cd('b-blue',80,420,380,260,'c_chain',{}),tt('light',270,440,340,T1,'c_light',{}),ic('fluorescence-channels',270,570,150,'c_light+.2',{bob:4}),
ar(466,550,534,550,'g','c_img-.5'),
cd('b-lav',540,420,380,260,'c_img-.3'),tt('image',730,440,340,T1,'c_img'),ic('tissue-section-slide',730,570,150,'c_img+.2',{bob:4,ph:1}),
ar(926,550,994,550,'g','c_meas-.5'),
cd('b-amber',1000,420,380,260,'c_meas-.3'),tt('measurement',1190,440,340,T1,'c_meas'),ic('cell-segmentation-mask',1190,570,150,'c_meas+.2',{bob:4,ph:2}),
ar(1386,550,1454,550,'g','c_concl-.5'),
cd('b-mint',1460,420,380,260,'c_concl-.3'),tt('a carefully limited conclusion',1650,440,340,T2,'c_concl'),{t:'tick',x:1650,y:590,r:46,a:'c_concl+.5'},
dt([[466,550],[534,550]],'c','c_img',{n:2,speed:.5,r:9}),dt([[926,550],[994,550]],'c','c_meas',{n:2,speed:.5,r:9}),dt([[1386,550],[1454,550]],'c','c_concl',{n:2,speed:.5,r:9}),
ch('the chain we will follow today',960,780,'amber','c_chain+.3',{fs:38})
]};''',ep=2)
print(build('e2_previous',2,'previous',dict(c_welcome='Welcome back',c_vid='This is video',c_prev='In the previous lesson',c_cells='cells',c_dna='DNARNA',c_prot='proteins',c_esm='We also ran',c_pref='Those probabilities',c_notell='They did not tell',c_obs='To answer a biological',c_micro='Microscopy is one way',c_chain='Today we will follow',c_light='from light',c_img='from image',c_meas='from measurement',c_concl='carefully limited')))

# ---------------- ep2 contents ----------------
def part_card(i,x,y,w,h,cls,title,icons,chiptxt,cue):
    out="cd('%s',%d,%d,%d,%d,'%s-.1'),ch('Part %d',%d,%d,'%s','%s',{fs:28}),tt(%r,%d,%d,%d,T2,'%s+.2',{c:false}),\n"%(cls,x,y,w,h,cue,i,x+110,y+16,{'b-blue':'blue','b-amber':'amber','b-lav':'lav','b-mint':'mint'}[cls],cue,title,x+40,y+68,w-80,cue)
    for k,(ik,ix,iw) in enumerate(icons):
        out+="ic(%r,%d,%d,%d,'%s+%.1f',{bob:4,ph:%d}),\n"%(ik,x+ix,y+165,iw,cue,.5+.5*k,k)
    out+="ch(%r,%d,%d,'%s','%s+1.4',{fs:24}),\n"%(chiptxt,x+w//2,y+h-70,{'b-blue':'blue','b-amber':'amber','b-lav':'lav','b-mint':'mint'}[cls],cue)
    return out
CT=part_card(1,80,226,880,300,'b-blue','Light becomes a measurement',[('fluorescence-channels',200,110),('microscope',440,110),('well-plate',680,110)],'fluorescence · channels · pixels · scale','c_p1')
CT+=part_card(2,1000,226,840,300,'b-mint','Cells, organoids and tissues',[('petri-dish',190,110),('organoid',420,110),('tissue',650,110)],'what each setting keeps and leaves out','c_p2')
CT+=part_card(3,80,550,880,300,'b-lav','A real pixels-to-measurements experiment',[('tissue-section-slide',200,110),('cell-segmentation-mask',440,110),('expression-heatmap',680,110)],'image → mask → measurements','c_p3')
CT+=part_card(4,1000,550,840,300,'b-amber','What AI adds, and what evidence still needs',[('attention-network',190,110),('training-test-split',420,110)],'AI + experimental validation','c_p4')
mk('e2_contents',0,P0,'Today’s four parts','Course roadmap · schematic icons','''
const SPEC={els:[
'''+CT+'''
cd('b-mint',80,880,1760,90,'c_listen-.1'),tt('You can follow the whole explanation by listening',110,904,960,'font:700 32px/1.2 Poppins;color:'+INK,'c_listen',{c:false}),
ch('companion files: exact code · images · sources',1480,899,'amber','c_comp',{fs:26})
]};''',ep=2)
print(build('e2_contents',2,'contents',dict(c_p1='Part one',c_p2='compares cells',c_p3='is a real Python',c_p4='explains what artificial',c_listen='You can follow',c_comp='The companion files')))

# ---------------- ep2 part 1 intro ----------------
def GR(rows,cols,f):
    return '['+','.join('['+','.join('%.2f'%f(r,c) for c in range(cols))+']' for r in range(rows))+']'
import math
G1=GR(4,4,lambda r,c:0.08+0.8*math.exp(-((r-1.4)**2+(c-1.6)**2)/2.2))
BADGE2=lambda n,title,fill:'''cd('b-mint',80,230,600,250,'c_start',{dy:20}),
tt('Part %d of 4',116,252,500,'font:600 30px/1 Inter;color:#26765d','c_start+.2',{c:false}),
tt(%r,116,296,540,'font:700 50px/1.1 Poppins;color:'+INK,'c_start+.35',{c:false}),
{t:'segs',x:116,y:430,w:120,a:'c_start+.5',fill:%d},
'''%(n,title,fill)
mk('e2_part1',1,'Light becomes a measurement','Part 1 · Light becomes a measurement','Part 1 · schematic overview · pixel values illustrative','''
const SPEC={els:[
'''+BADGE2(1,'Light becomes a measurement',1)+'''
ic('microscope',790,370,200,'c_scope',{bob:4,b:'c_signal-.3'}),ic('animal-cell',1060,380,80,'c_scope+.4',{mv:{a:'c_big',dx:60,dy:-10,s:2.4,dur:1.2},b:'c_signal-.3'}),
ch('more than just bigger',1060,470,'amber','c_big+.5',{fs:28,b:'c_signal-.3'}),
{t:'wave',x:760,y:370,len:520,amp:36,wl:90,col:'l',a:'c_signal',speed:5,w:7,dur:1.4},
{t:'wave',x:1290,y:370,len:520,amp:22,wl:46,col:'c',a:'c_signal+.6',speed:6,w:7,dur:1.4},
ch('a particular kind of signal',1020,300,'lav','c_signal+.4',{fs:28}),ch('under particular conditions',1560,300,'coral','c_cond',{fs:28}),
// chain of three
cd('b-blue',80,540,520,270,'c_label-.2'),ch('1',140,552,'amber','c_label',{fs:30}),tt('a fluorescent label',340,560,440,T2,'c_label+.1'),ic('fluorescence-channels',340,690,230,'c_label+.3',{bob:4}),
ar(606,675,694,675,'g','c_det-.5'),
cd('b-lav',700,540,520,270,'c_det-.2'),ch('2',760,552,'amber','c_det',{fs:30}),tt('the detector',960,560,440,T2,'c_det+.1'),
{t:'grid',x:840,y:620,cw:56,ch:56,vals:'''+G1+''',mode:'gray',a:'c_det+.3',stag:.04},
ar(1226,675,1314,675,'g','c_nums-.5'),
cd('b-amber',1320,540,520,270,'c_nums-.2'),ch('3',1380,552,'amber','c_nums',{fs:30}),tt('the saved numbers',1580,560,440,T2,'c_nums+.1'),
{t:'grid',x:1440,y:620,cw:56,ch:56,vals:'''+G1+''',mode:'gray',num:255,fs:17,a:'c_nums+.3',stag:.04},
dt([[606,675],[694,675]],'c','c_det',{n:2,speed:.5,r:9}),dt([[1226,675],[1314,675]],'c','c_nums',{n:2,speed:.5,r:9}),
rg(340,675,'a','c_order',{n:1,r0:60,r1:130,sw:8}),rg(960,675,'a','c_order+.3',{n:1,r0:60,r1:130,sw:8}),rg(1580,675,'a','c_order+.6',{n:1,r0:60,r1:130,sw:8}),
ch('what do the numbers actually mean?',1500,832,'amber','c_mean',{fs:28,b:'c_wrong-.3'}),
// wrong question
cd('b-coral',80,880,1760,90,'c_wrong-.1'),tt('a number analysed perfectly can still answer the wrong biological question',960,905,1700,'font:700 32px/1.2 Poppins;color:'+INK,'c_wrong+.2')
]};''',ep=2)
print(build('e2_part1',2,'part-1-intro',dict(c_start="Let's start",c_scope='A microscope',c_big='make a tiny',c_signal='It collects',c_cond='under particular',c_label='fluorescent label',c_det='to the detector',c_nums='the numbers',c_mean='actually mean',c_order='That order',c_wrong='A computer can analyze')))

# ---------------- ep2 part 3 / part 4 intros ----------------
BADGE3=lambda n,title,fill,fs:'''cd('b-mint',80,230,600,250,'c_start',{dy:20}),
tt('Part %d of 4',116,252,500,'font:600 30px/1 Inter;color:#26765d','c_start+.2',{c:false}),
tt(%r,116,296,540,'font:700 %dpx/1.12 Poppins;color:'+INK,'c_start+.35',{c:false}),
{t:'segs',x:116,y:430,w:120,a:'c_start+.5',fill:%d},
'''%(n,title,fs,fill)
mk('e2_part3',3,'A real pixels-to-measurements experiment','Part 3 · A real pixels-to-measurements experiment','Part 3 · schematic overview · icons conceptual','''
const SPEC={els:[
'''+BADGE3(3,'A real pixels-to-measurements experiment',3,38)+'''
cd('b-blue',720,230,350,250,'c_know-.1'),tt('describe the input honestly',895,250,310,T2,'c_know+.1'),ic('tissue-section-slide',895,385,130,'c_know+.3',{bob:4}),
cd('b-lav',1094,230,350,250,'c_know+1.0'),tt('understand a small analysis',1269,250,310,T2,'c_know+1.2'),ic('cell-segmentation-mask',1269,385,130,'c_know+1.4',{bob:4,ph:1}),
cd('b-amber',1468,230,372,250,'c_know+2.0'),tt('question its output',1654,250,330,T2,'c_know+2.2'),ic('expression-heatmap',1654,385,130,'c_know+2.4',{bob:4,ph:2}),
cd('b-coral',80,520,1760,80,'c_goal-.1'),tt('✗ not an impressive cell count at any cost',960,540,1700,'font:700 34px/1.2 Poppins;color:'+INK,'c_goal+.2'),
cd('b-blue',80,630,480,190,'c_chain-.1'),tt('source image',320,650,440,T2,'c_chain'),ic('tissue-section-slide',320,750,110,'c_chain+.2',{bob:4}),
ar(566,725,714,725,'g','c_chain+.8'),dt([[566,725],[714,725]],'c','c_chain+1.0',{n:2,speed:.5,r:9}),
cd('b-lav',720,630,480,190,'c_chain+.6'),tt('mask',960,650,440,T2,'c_chain+.8'),ic('cell-segmentation-mask',960,750,110,'c_chain+1.0',{bob:4,ph:1}),
ar(1206,725,1354,725,'g','c_chain+1.6'),dt([[1206,725],[1354,725]],'c','c_chain+1.8',{n:2,speed:.5,r:9}),
cd('b-amber',1360,630,480,190,'c_chain+1.4'),tt('measurement',1600,650,440,T2,'c_chain+1.6'),ic('expression-heatmap',1600,750,110,'c_chain+1.8',{bob:4,ph:2}),
ch('visible and reproducible',960,835,'mint','c_chain+2.4',{fs:30}),
cd('b-lav',80,885,1760,85,'c_base-.1'),tt('a simple classical baseline: no trained AI model',960,905,1700,'font:700 32px/1.2 Poppins;color:'+INK,'c_base+.2')
]};''',ep=2)
print(build('e2_part3',2,'part-3-intro',dict(c_start='We can now begin',c_know='We have enough',c_goal='Our goal',c_chain='It is to keep',c_base='We will use a simple')))
mk('e2_part4',4,'What AI adds, and what evidence still needs','Part 4 · What AI adds, and what evidence still needs','Part 4 · schematic overview · bars illustrative','''
const SPEC={els:[
'''+BADGE3(4,'What AI adds, and what evidence still needs',4,36)+'''
cd('b-blue',720,230,520,250,'c_base-.1'),tt('our simple baseline',980,248,480,T2,'c_base'),
br(780,400,40,40,'#7f9fc9','c_base+.3',{val:[0,1],vt:'c_base+.3',vd:.6}),br(840,350,40,90,'#7f9fc9','c_base+.4',{val:[0,1],vt:'c_base+.4',vd:.6}),br(900,380,40,60,'#7f9fc9','c_base+.5',{val:[0,1],vt:'c_base+.5',vd:.6}),br(960,330,40,110,'#7f9fc9','c_base+.6',{val:[0,1],vt:'c_base+.6',vd:.6}),br(1020,395,40,45,'#7f9fc9','c_base+.7',{val:[0,1],vt:'c_base+.7',vd:.6}),
ar(760,375,1070,375,'a','c_base+.9',{dash:'14 10',head:false}),ch('a threshold',1160,350,'amber','c_base+1.0',{fs:26}),ch('decisions are visible',980,445,'blue','c_base+1.3',{fs:24}),
cd('b-lav',1280,230,560,250,'c_cap-.1'),tt('more capable methods',1560,248,520,T2,'c_cap'),ic('attention-network',1560,370,150,'c_cap+.3',{bob:4}),ch('patterns a single threshold misses',1560,445,'lav','c_cap+.8',{fs:24}),
cd('b-amber',80,520,1760,150,'c_repl-.1'),tt('replacing a threshold with a trained model does not remove the measurement contract',960,540,1700,'font:700 32px/1.25 Poppins;color:'+INK,'c_repl+.1'),
ch('input',560,620,'blue','c_repl+1.4',{fs:30}),ch('output',960,620,'mint','c_repl+1.8',{fs:30}),ch('test',1360,620,'amber','c_repl+2.2',{fs:30}),
cd('b-coral',80,720,400,150,'c_adds-.1'),tt('training data',280,770,360,T2,'c_adds+.1'),
cd('b-lav',540,720,400,150,'c_adds+.7'),tt('reference labels',740,770,360,T2,'c_adds+.9'),
cd('b-mint',1000,720,400,150,'c_adds+1.7'),tt('evaluation',1200,770,360,T2,'c_adds+1.9'),
cd('b-blue',1460,720,380,150,'c_adds+2.7'),tt('when can we trust it?',1650,770,340,T2,'c_adds+2.9'),
ch('new questions the model adds',960,900,'amber','c_adds',{fs:34})
]};''',ep=2)
print(build('e2_part4',2,'part-4-intro',dict(c_start='We have reached',c_base='Our simple baseline',c_cap='More capable methods',c_repl='But replacing',c_adds='It adds new questions')))
