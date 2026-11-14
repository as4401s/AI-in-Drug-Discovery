import sys,math
sys.path.insert(0,'/home/claude/work/scenes')
from mk import mk
from cuespec import build
from ep2_part1 import NOTES,GR   # reuse helpers (importing runs part1 builds too; harmless)
P2='Cells, organoids and tissues'
CELLCSS="background:radial-gradient(circle at 50% 50%,#7a5ea8 0 22%,#d7ecf7 24%);border:4px solid #4d8f7e;border-radius:50%"
def cellc(x,y,d,a,b=None,col=None,extra=''):
    css=CELLCSS if not col else CELLCSS.replace('#d7ecf7',col)
    return "cd('',%d,%d,%d,%d,%s,{css:'%s',dy:0%s%s}),\n"%(x-d//2,y-d//2,d,d,a,css,(",b:%s"%b) if b else '',extra)
BADGE2=lambda n,title,fill:'''cd('b-mint',80,230,600,250,'c_start',{dy:20}),
tt('Part %d of 4',116,252,500,'font:600 30px/1 Inter;color:#26765d','c_start+.2',{c:false}),
tt(%r,116,296,540,'font:700 50px/1.1 Poppins;color:'+INK,'c_start+.35',{c:false}),
{t:'segs',x:116,y:430,w:120,a:'c_start+.5',fill:%d},
'''%(n,title,fill)

# ---------------- part 2 intro ----------------
mk('e2_part2',2,P2,'Part 2 · Cells, organoids and tissues','Part 2 · schematic overview · icons conceptual','''
const E='c_same-.3';
const SPEC={els:[
'''+BADGE2(2,'Cells, organoids and tissues',2)+'''
ic('fluorescence-channels',840,340,170,'c_know',{b:E,bob:4}),ch('a labelled signal',840,430,'mint','c_know+.3',{b:E,fs:26}),
ar(950,340,1060,340,'g','c_know+.9',{b:E}),
ic('tissue-section-slide',1180,340,150,'c_know+1.2',{b:E,bob:4,ph:1}),ch('an image',1180,430,'blue','c_know+1.5',{b:E,fs:26}),
ar(1290,340,1400,340,'g','c_know+2.0',{b:E}),
ic('well-plate',1520,340,150,'c_know+2.3',{b:E,bob:4,ph:2}),ch('settings matter',1520,430,'amber','c_know+2.6',{b:E,fs:26}),
ic('microscope',1280,330,150,'c_same',{bob:4}),ch('the same kind of microscope',1280,425,'lav','c_same+.4',{fs:28}),
cd('b-blue',80,520,520,260,'c_same+.6'),tt('cells on a surface',340,540,480,T2,'c_same+.8'),ic('petri-dish',340,670,170,'c_same+1.0',{bob:4}),
cd('b-lav',700,520,520,260,'c_same+1.4'),tt('organoids',960,540,480,T2,'c_same+1.6'),ic('organoid',960,670,170,'c_same+1.8',{bob:4,ph:1}),
cd('b-mint',1320,520,520,260,'c_same+2.2'),tt('tissue',1580,540,480,T2,'c_same+2.4'),ic('tissue',1580,670,170,'c_same+2.6',{bob:4,ph:2}),
dt([[1250,470],[340,530]],'#8b75b0','c_same+.8',{n:2,speed:.3,r:8}),dt([[1280,470],[960,530]],'#8b75b0','c_same+1.5',{n:2,speed:.3,r:8}),dt([[1320,470],[1580,530]],'#8b75b0','c_same+2.3',{n:2,speed:.3,r:8}),
ch('what context does the sample preserve?',960,810,'amber','c_next',{fs:38,b:'c_fail-.3'}),
cd('b-coral',80,880,1760,90,'c_fail-.1'),tt('careful measurements can still miss the biological situation we care about',960,905,1700,'font:700 32px/1.2 Poppins;color:'+INK,'c_fail+.2')
]};''',ep=2)
print(build('e2_part2',2,'part-2-intro',dict(c_start='That brings us',c_know='We now know',c_same='But the same kind',c_next='The next question',c_fail='A measurement can be')))

# ---------------- cell culture ----------------
CUL=''
for i in range(8):
    CUL+=cellc(150+i*95,640,84,"'c_flat+%.2f'"%(.2+.3*i),extra=",dy:-170")
FOV=''.join("cd('',%d,%d,110,80,'c_nut+%.1f',{css:'background:rgba(215,236,247,.7);border:4px solid #7f9fc9;border-radius:10px',dy:0,b:'c_use-.3'}),\n"%(1120+(i%3)*130,470+(i//3)*100,1.8+.25*i) for i in range(6))
mk('e2_culture',2,P2,'Cell culture: a controlled, simplified system','Part 2 · schematic illustration · not measured data','''
const SPEC={'''+NOTES([('c_def','Cell culture','cells <b>maintained under controlled laboratory conditions</b>'),('c_flat','A common setup','cells attach to a <b>flat surface</b> and form a layer'),('c_nut','What we can do','supply <b>nutrients</b>, add a <b>treatment</b>, and image many <b>fields of view</b>'),('c_use','Useful','for repeated, relatively accessible measurements'),('c_simple','Also simplified','a <b>simplified</b> environment'),('c_flat2','A flat layer does not recreate','the 3D architecture, neighbouring cell types, mechanical conditions, or delivery barriers of the body'),('c_bad','Not a bad experiment','it means the experiment has a <b>scope</b>'),('c_conc','So our first conclusion','concerns <b>those cells</b>, <b>those conditions</b>, <b>that time</b>')])+''',
els:[
ic('petri-dish',230,560,200,'c_def',{bob:4,b:'c_flat-.3'}),ch('controlled laboratory conditions',300,680,'mint','c_def+.4',{fs:28,b:'c_flat-.3'}),
cd('',120,690,820,18,'c_flat',{css:'background:#b9a98a;border-radius:9px',dy:0}),ch('flat surface',530,725,'amber','c_flat+.5',{fs:26}),
'''+CUL+'''
ch('a layer of cells',530,500,'mint','c_flat+2.6',{fs:28}),
ch('nutrients',360,470,'blue','c_nut',{fs:26,b:'c_use-.3'}),dt([[300,520],[300,590]],'#7f9fc9','c_nut+.2',{n:3,speed:.5,r:7,b:'c_use-.3'}),dt([[420,520],[420,590]],'#7f9fc9','c_nut+.5',{n:3,speed:.5,r:7,b:'c_use-.3'}),
ch('treatment',640,470,'coral','c_nut+.8',{fs:26,b:'c_use-.3'}),dt([[640,520],[640,590]],'#cf8a83','c_nut+1.0',{n:3,speed:.5,r:7,b:'c_use-.3'}),
'''+FOV+'''
ch('many fields of view',1250,690,'lav','c_nut+2.0',{fs:26,b:'c_use-.3'}),
ch('✓ repeated, accessible measurements',1250,520,'mint','c_use',{fs:30,b:'c_simple-.3'}),
ch('also a simplified environment',1250,520,'coral','c_simple',{fs:32}),
ch('✗ 3D architecture',1500,610,'coral','c_arch',{fs:28}),ch('✗ neighbouring cell types',1500,680,'coral','c_arch+2.0',{fs:28}),ch('✗ mechanical conditions',1500,750,'coral','c_arch+4.0',{fs:28}),ch('✗ delivery barriers',1500,820,'coral','c_arch+5.8',{fs:28}),
ch('✓ not a bad experiment',960,880,'mint','c_bad',{fs:34,b:'c_conc-.3'}),ch('it has a scope',1500,880,'amber','c_bad+1.5',{fs:34,b:'c_conc-.3'}),
cd('b-amber',80,860,1760,110,'c_conc-.1'),ch('those cells',480,885,'mint','c_conc+.3',{fs:34}),ch('under those conditions',960,885,'blue','c_conc+1.5',{fs:34}),ch('at that time',1440,885,'lav','c_conc+3.0',{fs:34})
]};''',ep=2)
print(build('e2_culture',2,'cell-culture',dict(c_def='A cell culture',c_flat='In one common setup',c_nut='We can supply',c_use='That makes the setup',c_simple='It is also a simplified',c_arch='architecture',c_flat2='A flat layer does not',c_bad='This does not make',c_conc='If we measure a change')))

# ---------------- organoid ----------------
RING=''.join(cellc(500+int(130*math.cos(2*math.pi*i/10)),650+int(130*math.sin(2*math.pi*i/10)),70,"'c_cav+%.2f'"%(.25+.12*i),None) for i in range(10))
FLAT=''.join(cellc(1130+i*90,650,70,"'c_cav+%.2f'"%(1.6+.12*i),None) for i in range(6))
mk('e2_organoid',2,P2,'Organoids: selected features of an organ or tissue','Part 2 · schematic illustration · icons conceptual','''
const SPEC={'''+NOTES([('c_def','An organoid','a <b>3-dimensional</b> laboratory culture that organises to reproduce <b>selected features</b> of an organ or tissue'),('c_stem','Where it comes from','often grown from <b>stem cells</b> or tissue-derived <b>progenitor cells</b>'),('c_prog','Descendants','stem and progenitor cells can make more <b>specialised</b> cells with different capacities'),('c_sel','The important word','exact cell types and structures depend on the system: <b>selected</b>'),('c_not','What it is not','not a complete miniature person, not automatically a fully functioning tiny organ'),('c_use','Its usefulness','comes from the features it <b>does</b> preserve'),('c_cav','For example','cells may organise around a <b>cavity</b> or interact in a spatial arrangement a flat layer does not capture'),('c_q','Why choose one','because those particular features help answer a <b>defined question</b>')])+''',
els:[
ic('organoid',1050,610,300,'c_def',{bob:4,b:'c_cav-.3'}),ch('3D laboratory culture',1050,460,'lav','c_def+.4',{fs:30,b:'c_cav-.3'}),ch('reproduces selected features',1050,780,'mint','c_def+3.0',{fs:28,b:'c_not-.3'}),
ic('stem-cell-differentiation',380,610,280,'c_stem',{bob:4,b:'c_use-.3'}),ch('stem cells · progenitor cells',380,780,'blue','c_stem+.5',{fs:28,b:'c_use-.3'}),
ar(560,610,860,610,'g','c_stem+1.2',{b:'c_use-.3'}),dt([[560,610],[860,610]],'c','c_stem+1.8',{n:3,speed:.3,r:9,b:'c_use-.3'}),
ch('under supportive conditions',710,540,'amber','c_stem+2.0',{fs:26,b:'c_use-.3'}),
ch('more specialised descendants',710,690,'lav','c_prog',{fs:26,b:'c_use-.3'}),
ch('the important word: “selected”',1050,780,'amber','c_sel',{fs:36,b:'c_not-.3'}),
ch('✗ not a complete miniature person',1560,540,'coral','c_not',{fs:30,b:'c_use-.3'}),ch('✗ not automatically a working tiny organ',1560,630,'coral','c_not+2.4',{fs:30,b:'c_use-.3'}),
ch('useful for the features it does preserve',960,830,'mint','c_use',{fs:34,b:'c_cav-.3'}),
'''+RING+'''
ch('cells organise around a cavity',500,830,'mint','c_cav+1.6',{fs:30}),
'''+FLAT+'''
ch('a flat layer does not capture this',1400,830,'coral','c_cav+3.4',{fs:30}),
cd('b-amber',80,880,1760,90,'c_q-.1'),tt('we choose an organoid because those features help answer a defined question',960,905,1700,'font:700 32px/1.2 Poppins;color:'+INK,'c_q+.2')
]};''',ep=2)
print(build('e2_organoid',2,'organoid',dict(c_def='An organoid is',c_stem='Many organoid',c_prog='progenitor cells can',c_sel='The exact cell',c_not='An organoid is not',c_use='Its usefulness',c_cav='For example',c_q='We choose an organoid')))

# ---------------- organoid limits ----------------
DKS="background:radial-gradient(circle at 50% 50%,#33433f 0,#6f8f83 38%,#bde0d0 100%);border:6px solid #4d8f7e;border-radius:50%"
mk('e2_orglimits',2,P2,'Three dimensions bring new difficulties','Part 2 · schematic cross-section · not measured data','''
const SPEC={'''+NOTES([('c_hard','New difficulties','three dimensions also create <b>new difficulties</b>'),('c_reach','Treatment access','a treatment added outside may not <b>reach every internal region</b> the same way'),('c_light','Imaging depth','light must pass through material; signal from <b>deeper regions</b> is harder to acquire or interpret'),('c_lack','Missing components','the culture may lack a functioning <b>blood supply</b> or parts of the <b>immune system</b>'),('c_prop','Properties to investigate','not assumptions to hide behind a <b>realistic-looking picture</b>'),('c_dark','Be careful','a dark centre does <b>not by itself</b> prove the centre cells are dead'),('c_dark2','Darkness can reflect','labelling, imaging depth, optical effects, processing, or biology'),('c_need','To identify cell death','we need a <b>suitable measurement</b> and <b>controls</b> that support it')])+''',
els:[
cd('',280,470,380,380,'c_hard',{css:\''''+DKS+'''\',dy:0}),ch('organoid cross-section (schematic)',470,865,'lav','c_hard+.5',{fs:24}),
ch('treatment',130,640,'coral','c_reach-.2',{fs:26,b:'c_light-.3'}),dt([[200,665],[420,665]],'#cf8a83','c_reach',{n:5,speed:.3,r:10,b:'c_light-.3'}),dt([[200,615],[380,615]],'#cf8a83','c_reach+.3',{n:4,speed:.3,r:10,b:'c_light-.3'}),
ch('may not reach the centre',1050,560,'coral','c_reach+1.6',{fs:30,b:'c_light-.3'}),
{t:'wave',x:100,y:560,len:150,amp:14,wl:36,col:'a',a:'c_light',speed:6,w:6,dur:1.0,b:'c_lack-.3'},ch('light',130,500,'amber','c_light',{fs:24,b:'c_lack-.3'}),
ar(470,660,470,430,'a','c_light+1.0',{b:'c_lack-.3'}),ch('deeper signal: harder to acquire',1050,640,'amber','c_light+1.5',{fs:30,b:'c_lack-.3'}),
ch('– no functioning blood supply',1250,500,'coral','c_lack',{fs:30,b:'c_dark-.3'}),ch('– parts of the immune system missing',1250,580,'coral','c_lack+1.6',{fs:30,b:'c_dark-.3'}),
ch('properties to investigate, not assumptions',1250,680,'amber','c_prop',{fs:30,b:'c_dark-.3'}),
rg(470,660,'c','c_dark',{every:1.0,dur:1.0,n:5,r0:40,r1:120,sw:7}),tt('?',470,600,100,BIG(110),'c_dark+.2',{css:'font:700 110px/1 Poppins;color:#fff'}),
ch('✗ dark centre ≠ proof of cell death',1250,500,'coral','c_dark+.3',{fs:32,b:'c_need-.3'}),
ch('labelling',900,610,'mint','c_dark2',{fs:28,b:'c_need-.3'}),ch('imaging depth',1130,610,'blue','c_dark2+.5',{fs:28,b:'c_need-.3'}),ch('optical effects',1400,610,'lav','c_dark2+1.0',{fs:28,b:'c_need-.3'}),ch('processing',1130,690,'amber','c_dark2+1.5',{fs:28,b:'c_need-.3'}),ch('or biology',1400,690,'mint','c_dark2+2.0',{fs:28,b:'c_need-.3'}),
cd('b-mint',760,560,1080,260,'c_need-.1'),tt('to identify cell death',1300,590,1000,T1,'c_need+.1'),ch('a suitable measurement',1000,690,'blue','c_need+.5',{fs:32}),ch('+ controls',1500,690,'amber','c_need+1.3',{fs:32}),{t:'tick',x:1600,y:760,r:34,a:'c_need+1.8'}
]};''',ep=2)
print(build('e2_orglimits',2,'organoid-limits',dict(c_hard='Three dimensions also',c_reach='A treatment added',c_light='Light must pass',c_lack='The culture may lack',c_prop='These are properties',c_dark='In particular',c_dark2='Darkness can reflect',c_need='To identify cell death')))

# ---------------- tissue ----------------
TC=''
for r in range(3):
    for c in range(6):
        TC+=cellc(260+c*125,500+r*115,76,"'c_rel+%.2f'"%(.2+.07*(r*6+c)),"'c_word-.3'")
mk('e2_tissue',2,P2,'Tissue preserves relationships between neighbours','Part 2 · conceptual 2D teaching diagram · not measured data','''
const SPEC={'''+NOTES([('c_def','Tissue','an <b>organised collection</b> of cells and surrounding material that contribute to biological functions'),('c_rel','A tissue sample','can preserve <b>relationships</b> between cell types and their local environment'),('c_ctx','That context','can matter'),('c_vessel','Near a blood vessel','a response may differ from one <b>farther away</b>'),('c_neigh','Neighbours','a cell beside a particular neighbour may behave differently from an isolated cell'),('c_slice','But','a tissue section is still a <b>sample</b>, often a thin slice of a larger structure'),('c_not','We do not observe','every region or every moment of the original living system'),('c_word','The word “tissue”','tells us about <b>biological organisation</b>'),('c_need','It does not remove the need','to describe where the sample came from, how it was prepared, which part was measured')])+''',
els:[
cd('b-amber',80,420,1000,420,'c_def',{b:'c_slice-.3'}),ch('cells within surrounding matrix',460,435,'amber','c_def+.3',{fs:26,b:'c_slice-.3'}),
cd('',130,430,46,410,'c_vessel-1.5',{css:'background:linear-gradient(90deg,#c9594f,#e88b82);border-radius:23px',dy:0,b:'c_slice-.3'}),ch('blood vessel',153,383,'coral','c_vessel-1.0',{fs:24,b:'c_slice-.3'}),
'''+TC.replace("None","None")+'''
rg(300,500,'c','c_vessel',{every:1.2,dur:1.0,n:5,r0:30,r1:80,sw:6,b:'c_neigh-.3'}),rg(300,615,'c','c_vessel+.3',{every:1.2,dur:1.0,n:5,r0:30,r1:80,sw:6,b:'c_neigh-.3'}),
ch('near: one response',300,880,'coral','c_vessel+.5',{fs:26,b:'c_neigh-.3'}),ch('farther away: may differ',880,880,'blue','c_vessel+1.8',{fs:26,b:'c_neigh-.3'}),
ar(675,500,800,500,'a','c_neigh',{b:'c_slice-.3'}),ch('a neighbour changes behaviour',840,392,'amber','c_neigh+.4',{fs:26,b:'c_slice-.3'}),
'''+cellc(995,690,76,"'c_neigh+1.0'","'c_slice-.3'")+'''ch('isolated cell',995,735,'blue','c_neigh+1.3',{fs:24,b:'c_slice-.3'}),
ic('tissue',1470,560,330,'c_slice',{bob:4}),cd('',1520,430,24,260,'c_slice+.6',{css:'background:rgba(207,138,131,.8);border-radius:6px',dy:0}),ch('a thin slice of a larger structure',1470,740,'amber','c_slice+.8',{fs:28}),
ch('✗ not every region',1470,820,'coral','c_not',{fs:30,b:'c_word-.3'}),ch('✗ not every moment',1470,890,'coral','c_not+1.8',{fs:30,b:'c_word-.3'}),
cd('b-mint',80,600,1100,200,'c_word-.1',{b:'c_need-.3'}),tt('tissue = biological organisation',630,640,1000,T1,'c_word+.2',{b:'c_need-.3'}),
ch('where it came from',300,830,'blue','c_need',{fs:32}),ch('how it was prepared',700,830,'mint','c_need+.8',{fs:32}),ch('which part was measured',1120,830,'amber','c_need+1.6',{fs:32}),ch('still needs a description',960,900,'coral','c_need+2.4',{fs:30})
]};''',ep=2)
print(build('e2_tissue',2,'tissue',dict(c_def='Tissue is an organized',c_rel='A tissue sample can',c_ctx='That context',c_vessel='A response near',c_neigh='A cell beside',c_slice='but a tissue section',c_not='We do not observe',c_word='The word tissue',c_need='It does not remove')))

# ---------------- preparation ----------------
mk('e2_prep',2,P2,'Preparation shapes what an image can answer','Part 2 · schematic illustration · not measured data','''
const SPEC={'''+NOTES([('c_chg','Preparation','changes what questions an image can answer'),('c_fixed','Fixed samples','chemical preparation <b>preserves selected structures</b> for later examination'),('c_live','Living samples','we can observe <b>changes over time</b>, but illumination and labelling can <b>disturb</b> the system'),('c_neither','Neither approach','automatically tells the <b>full story</b>'),('c_still','A still image','records one <b>state</b> under its acquisition conditions'),('c_path','It does not reveal','the <b>path</b> that produced that state'),('c_fewer','Fewer visible objects?','in a treated sample — perhaps cells died'),('c_perh','Or perhaps','they detached, the stain failed, or segmentation missed them'),('c_dist','To tell these apart','time points, appropriate labels, controls, additional measurements'),('c_ev','Decide first','what evidence we need before choosing the most dramatic interpretation')])+''',
els:[
cd('b-blue',80,420,860,340,'c_fixed-.2',{b:'c_still-.3'}),tt('fixed',510,440,800,T1,'c_fixed',{b:'c_still-.3'}),ic('animal-cell',330,610,230,'c_fixed+.3',{b:'c_still-.3',css:'filter:saturate(.5) hue-rotate(10deg)'}),ch('structures preserved for later examination',510,700,'blue','c_fixed+.8',{fs:26,b:'c_still-.3'}),
cd('b-mint',980,420,860,340,'c_live-.2',{b:'c_still-.3'}),tt('living',1410,440,800,T1,'c_live',{b:'c_still-.3'}),
ic('animal-cell',1100,600,120,'c_live+.3',{b:'c_still-.3',bob:3}),ic('animal-cell',1260,600,120,'c_live+1.2',{b:'c_still-.3',bob:3,css:'filter:hue-rotate(25deg)'}),ic('animal-cell',1420,600,120,'c_live+2.2',{b:'c_still-.3',bob:3,css:'filter:hue-rotate(50deg)'}),ic('animal-cell',1580,600,120,'c_live+3.2',{b:'c_still-.3',bob:3,css:'filter:hue-rotate(80deg)'}),
ch('changes over time →',1340,690,'mint','c_live+1.0',{fs:26,b:'c_still-.3'}),
ch('light + labels can disturb the system',1410,790,'coral','c_live+3.0',{fs:26,b:'c_still-.3'}),
ch('neither tells the full story',960,845,'amber','c_neither',{fs:36,b:'c_still-.3'}),
ar(200,640,1720,640,'g','c_still-.2',{dash:'16 12',head:false,b:'c_fewer-.3'}),ic('animal-cell',960,640,230,'c_still',{b:'c_fewer-.3',bob:4}),ch('one state, one moment',960,780,'lav','c_still+.5',{fs:32,b:'c_fewer-.3'}),
ch('? how did it get here',480,560,'coral','c_path',{fs:32,b:'c_fewer-.3'}),ch('? what happens next',1440,560,'coral','c_path+1.2',{fs:32,b:'c_fewer-.3'}),
cd('',150,430,520,300,'c_fewer-.2',{css:'background:#0e1a17;border:6px solid #cfd9d4',dy:0,b:'c_ev-.3'}),cd('',750,430,520,300,'c_fewer-.2',{css:'background:#0e1a17;border:6px solid #cfd9d4',dy:0,b:'c_ev-.3'}),
'''+''.join("cd('',%d,%d,50,50,'c_fewer-.1',{css:'border-radius:50%%;background:radial-gradient(circle at 40%% 35%%,#e6fff4,#5fd0aa 60%%,#2c8f74)',dy:0,b:'c_ev-.3'}),\n"%(170+((i*113)%440),450+((i*71)%210)) for i in range(7))+''.join("cd('',%d,%d,50,50,'c_fewer-.1',{css:'border-radius:50%%;background:radial-gradient(circle at 40%% 35%%,#e6fff4,#5fd0aa 60%%,#2c8f74)',dy:0,b:'c_ev-.3'}),\n"%(770+((i*157)%440),450+((i*89)%210)) for i in range(2))+'''
ch('control: many objects',410,745,'mint','c_fewer',{fs:28,b:'c_ev-.3'}),ch('treated: fewer objects',1010,745,'coral','c_fewer+.6',{fs:28,b:'c_ev-.3'}),
ch('cells died?',1500,470,'coral','c_fewer+1.0',{fs:30,b:'c_dist-.3'}),ch('cells detached?',1500,545,'amber','c_perh',{fs:30,b:'c_dist-.3'}),ch('stain failed?',1500,620,'blue','c_perh+1.0',{fs:30,b:'c_dist-.3'}),ch('segmentation missed them?',1500,695,'lav','c_perh+2.0',{fs:30,b:'c_dist-.3'}),
ch('time points',1500,470,'mint','c_dist',{fs:30,b:'c_ev-.3'}),ch('appropriate labels',1500,545,'blue','c_dist+.8',{fs:30,b:'c_ev-.3'}),ch('controls',1500,620,'amber','c_dist+1.6',{fs:30,b:'c_ev-.3'}),ch('additional measurements',1500,695,'lav','c_dist+2.4',{fs:30,b:'c_ev-.3'}),
cd('b-amber',80,860,1760,110,'c_ev-.1'),tt('decide what evidence we need before choosing the most dramatic interpretation',960,885,1700,'font:700 32px/1.2 Poppins;color:'+INK,'c_ev+.2')
]};''',ep=2)
print(build('e2_prep',2,'preparation',dict(c_chg='Preparation changes',c_fixed='In fixed samples',c_live='When imaging living',c_neither='Neither approach',c_still='A still image',c_path='It does not reveal',c_fewer='If a treated sample',c_perh='Perhaps they detached',c_dist='Time points',c_ev='We should decide')))

# ---------------- choose context ----------------
E3='c_egfr-.3'
mk('e2_context',2,P2,'Choosing a sample for a drug-discovery question','Part 2 · schematic overview · icons conceptual','''
const E3='c_egfr-.3';
const SPEC={'''+NOTES([('c_conn','Connecting to drug discovery','which sample fits which kind of question?'),('c_simple','A simple response in one cell type','a controlled culture may be a useful <b>first experiment</b>'),('c_org','Spatial organisation or internal access','an appropriate <b>organoid</b> may help investigate that aspect'),('c_tissue','Relationships among cell types','in an existing architecture: <b>tissue</b> provides another kind of evidence'),('c_comp','Complementary tools','not a universal ranking from bad to perfect'),('c_harder','Trade-off','more complicated samples bring <b>harder measurement and interpretation</b>'),('c_egfr','For our EGFR and KRAS questions','a treatment claim needs a <b>real match</b> between sample, target or variant, compound, dose, exposure time and endpoint'),('c_public','Today’s public image','is a separate <b>teaching data set</b>')])+''',
els:[
cd('b-blue',80,420,520,330,'c_simple-.2',{b:E3}),tt('a simple response in one cell type',340,440,480,T2,'c_simple'),ic('petri-dish',340,580,170,'c_simple+.3',{b:E3,bob:4}),ch('controlled culture',340,680,'blue','c_simple+.8',{fs:28,b:E3}),
cd('b-lav',700,420,520,330,'c_org-.2',{b:E3}),tt('space or internal access matters',960,440,480,T2,'c_org'),ic('organoid',960,580,170,'c_org+.3',{b:E3,bob:4,ph:1}),ch('organoid',960,680,'lav','c_org+.8',{fs:28,b:E3}),
cd('b-mint',1320,420,520,330,'c_tissue-.2',{b:E3}),tt('relationships in an existing architecture',1580,440,480,T2,'c_tissue'),ic('tissue',1580,580,170,'c_tissue+.3',{b:E3,bob:4,ph:2}),ch('tissue',1580,680,'mint','c_tissue+.8',{fs:28,b:E3}),
ch('↔ complementary tools, not a ranking',960,790,'amber','c_comp',{fs:34,b:E3}),
ch('more complicated samples: harder measurement and interpretation',960,860,'coral','c_harder',{fs:30,b:E3}),
cd('b-blue',80,430,520,130,'c_egfr-.1'),tt('the sample',340,470,480,T2,'c_egfr+.1'),{t:'tick',x:550,y:495,r:24,a:'c_m1'},
cd('b-lav',700,430,520,130,'c_egfr+.1'),tt('molecular target or variant',960,470,480,T2,'c_egfr+.3'),{t:'tick',x:1170,y:495,r:24,a:'c_m2'},
cd('b-coral',1320,430,520,130,'c_egfr+.3'),tt('compound',1580,470,480,T2,'c_egfr+.5'),{t:'tick',x:1790,y:495,r:24,a:'c_m3'},
cd('b-amber',80,590,520,130,'c_egfr+.5'),tt('dose',340,630,480,T2,'c_egfr+.7'),{t:'tick',x:550,y:655,r:24,a:'c_m4'},
cd('b-mint',700,590,520,130,'c_egfr+.7'),tt('exposure time',960,630,480,T2,'c_egfr+.9'),{t:'tick',x:1170,y:655,r:24,a:'c_m5'},
cd('b-blue',1320,590,520,130,'c_egfr+.9'),tt('endpoint',1580,630,480,T2,'c_egfr+1.1'),{t:'tick',x:1790,y:655,r:24,a:'c_m6'},
ch('a treatment claim needs a real match of all six',960,770,'amber','c_m6+.8',{fs:34}),
ch('today’s public image: a separate teaching data set',960,860,'lav','c_public',{fs:34})
]};''',ep=2)
print(build('e2_context',2,'choose-context',dict(c_conn="Let's connect",c_simple='If our question concerns',c_org='spatial',c_tissue='If we need relationships',c_comp='complementary tools',c_harder='More complicated',c_egfr='For our courses',c_m1='between the sample',c_m2='molecular target',c_m3='compound',c_m4='dose',c_m5='exposure time',c_m6='endpoint',c_public="Today's public image")))
