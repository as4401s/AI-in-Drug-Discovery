import sys,math
sys.path.insert(0,'/home/claude/work/scenes')
from mk import mk
from cuespec import build
P1='Light becomes a measurement'
def GR(rows,cols,f):
    return '['+','.join('['+','.join('%.2f'%max(0,min(1,f(r,c))) for c in range(cols))+']' for r in range(rows))+']'
def blobs(pts,sig=1.0,base=.08):
    return lambda r,c:base+sum(a*math.exp(-((r-pr)**2+(c-pc)**2)/(2*sig*sig)) for pr,pc,a in pts)
NUC=GR(5,5,blobs([(1,1,.95),(3,3,.8),(1,3.5,.45)],0.9))
MEM=GR(5,5,lambda r,c:.1+.85*math.exp(-((math.hypot(r-2,c-2)-1.6)**2)/.6))
def NOTES(lst,x=60,y=226,w=1800,h=150):
    items=','.join("['%s',%r,%r]"%(c,t,b) for c,t,b in lst)
    return "notes:{x:%d,y:%d,w:%d,h:%d,list:[%s]}"%(x,y,w,h,items)

# ---------------- fluorescence ----------------
mk('e2_fluor',1,P1,'How fluorescence works','Part 1 · schematic illustration · wavelengths and sizes not to scale','''
const SPEC={'''+NOTES([('c_mol','Fluorescence','a molecule can <b>absorb light</b> and then <b>emit light</b>'),('c_exc','Excitation','the light we <b>supply</b>'),('c_emi','Emission','the light <b>given off</b> afterwards'),('c_long','Often a longer wavelength','the emitted light usually has a <b>longer wavelength</b> than the exciting light'),('c_wl','Wavelength','the <b>spacing</b> of a light wave, related to its colour'),('c_filt','Filters','help <b>select</b> the excitation light and <b>collect</b> the desired emission'),('c_think','An analogy','a labelled part of the sample <b>“announces”</b> its location'),('c_real','But remember','molecules interact with light; they send <b>no intentional messages</b>'),('c_dist','The key distinction','the light going <b>in</b> versus the light we <b>measure coming back</b>')])+''',
els:[
cd('',90,590,110,110,'c_mol',{css:'border-radius:50%;background:radial-gradient(circle at 35% 30%,#fff6c9,#f2c84b 60%,#d99a1e);box-shadow:0 0 40px rgba(242,200,75,.7)',dy:0}),ch('light source',145,720,'amber','c_mol+.3',{fs:26}),
rg(145,645,'a','c_exc',{every:1.2,dur:1.2,n:6,r0:55,r1:110,sw:5}),
{t:'wave',x:220,y:645,len:470,amp:30,wl:44,col:'b',a:'c_exc',speed:6,w:7,dur:1.2},
ch('excitation',440,470,'blue','c_exc+.3',{fs:30}),
cd('',480,560,26,170,'c_filt',{css:'background:rgba(80,130,220,.5);border:3px solid #5c86d6;border-radius:8px',dy:0}),ch('filter',493,745,'blue','c_filt+.3',{fs:24}),
cd('b-mint',700,520,260,250,'c_mol+.5'),ic('small-molecule',830,640,210,'c_mol+.8',{bob:4}),ch('fluorescent molecule',830,785,'mint','c_mol+1.0',{fs:24}),
rg(830,640,'m','c_emi',{every:1.3,dur:1.2,n:4,r0:70,r1:140,sw:6}),
{t:'wave',x:980,y:645,len:440,amp:30,wl:96,col:'#3a9d6b',a:'c_emi',speed:6,w:7,dur:1.2},
ch('emission',1130,470,'mint','c_emi+.3',{fs:30}),
cd('',1270,560,26,170,'c_filt+.4',{css:'background:rgba(58,157,107,.45);border:3px solid #3a9d6b;border-radius:8px',dy:0}),ch('filter',1283,745,'mint','c_filt+.7',{fs:24}),
ch('shorter wavelength',440,520,'blue','c_long',{fs:24}),ch('longer wavelength',1130,520,'mint','c_long+.6',{fs:24}),
ar(985,705,1081,705,'a','c_wl',{head:false}),ch('one wavelength',1033,720,'amber','c_wl+.3',{fs:24}),
{t:'grid',x:1500,y:580,cw:62,ch:62,vals:'''+GR(3,3,lambda r,c:.15+.7*math.exp(-((r-1)**2+(c-1)**2)/1.2))+''',mode:'gray',a:'c_filt',stag:.05},ch('detector',1593,785,'lav','c_filt+.5',{fs:26}),
ar(1440,645,1490,645,'g','c_filt+.3'),
ch('“I’m here!”',830,470,'amber','c_think',{fs:32,b:'c_real'}),ch('just an analogy',830,470,'coral','c_real',{fs:30}),
ch('light going in',440,860,'blue','c_dist',{fs:32}),ch('light we measure coming back',1250,860,'mint','c_dist+.6',{fs:32})
]};''',ep=2)
print(build('e2_fluor',2,'fluorescence',dict(c_mol='Fluorescence begins',c_exc='called excitation',c_emi='called emission',c_long='longer wavelength',c_wl='Wavelength describes',c_filt='Filters help',c_think='Think of the experiment',c_real='Of course',c_dist='The important distinction')))

# ---------------- labels ----------------
def pan(i,x,y,w,h,a):
    return "cd('',%d,%d,%d,%d,'%s',{css:'background:#0e1a17;border:6px solid #cfd9d4',dy:0}),\n"%(x,y,w,h,a)
nuc=[(220,500),(350,590),(470,480),(300,430),(470,600)]
mem=[(900,500,140),(1090,560,120),(980,450,100),(1120,470,90)]
prot=[(1330+((i*97)%440),440+((i*61)%170)) for i in range(16)]
LB=pan(0,80,410,560,230,'c_nuc-.1')+pan(1,680,410,560,230,'c_mem-.1')+pan(2,1280,410,560,230,'c_prot-.1')
LB+=''.join("cd('',%d,%d,70,70,'c_nuc+%.1f',{css:'border-radius:50%%;background:radial-gradient(circle at 40%% 35%%,#e6f0ff,#6c9cff 55%%,#3f63c9);box-shadow:0 0 26px rgba(108,156,255,.8)',dy:0}),\n"%(x-35,y-35,.15*i) for i,(x,y) in enumerate(nuc))
LB+=''.join("cd('',%d,%d,%d,%d,'c_mem+%.1f',{css:'background:transparent;border-radius:50%%;border:7px solid #5fd08a;box-shadow:0 0 22px rgba(95,208,138,.7)',dy:0}),\n"%(x-d//2,y-d//2,d,d,.2*i) for i,(x,y,d) in enumerate(mem))
LB+=''.join("cd('',%d,%d,18,18,'c_prot+%.2f',{css:'border-radius:50%%;background:#ff7a70;box-shadow:0 0 14px rgba(255,122,112,.9)',dy:0}),\n"%(x,y,.07*i) for i,(x,y) in enumerate(prot))
mk('e2_labels',1,P1,'Fluorescent labels connect signal to structure','Part 1 · schematic pictures, not real microscope data','''
const SPEC={'''+NOTES([('c_label','A fluorescent label','associates a <b>signal</b> with something we want to study'),('c_nuc','One stain','may highlight <b>DNA-rich nuclei</b>'),('c_mem','A different label','may outline <b>cell membranes</b> or mark a <b>particular protein</b>'),('c_def','Two terms','the <b>nucleus</b> holds most of a typical human cell’s DNA; the <b>membrane</b> separates the cell from its surroundings'),('c_not','Limits of one channel','a bright nucleus image does <b>not</b> show every structure in the cell'),('c_gene','Limits of one channel','a membrane image does <b>not</b> reveal which genes are active'),('c_spec','Specificity','the label and its biological specificity define <b>part of the question</b>'),('c_ctrl','Controls','a stain can <b>bind imperfectly</b>'),('c_bg','Confounders','background adds light; structures can <b>overlap</b>'),('c_port','The honest picture','a <b>labelled signal</b>, not an all-knowing portrait of the cell')])+''',
els:[
'''+LB+'''
{t:'box',x:80,y:410,w:560,h:230,css:'background:rgba(120,160,255,.28);border-radius:12px',a:'c_bg',dy:0},
ch('DNA-rich nuclei',360,655,'blue','c_nuc+.8',{fs:28}),ch('cell membranes',960,655,'mint','c_mem+.8',{fs:28}),ch('a particular protein',1560,655,'coral','c_prot+.5',{fs:28}),
tt('nucleus: most of the cell’s DNA',360,715,520,'font:600 24px/1.2 Inter;color:'+INK,'c_def',{b:'c_not-.3'}),tt('membrane: separates the cell from its surroundings',960,715,520,'font:600 24px/1.2 Inter;color:'+INK,'c_def+1.4',{b:'c_not-.3'}),
ch('✗ not every structure',360,715,'coral','c_not',{fs:28,b:'c_spec-.3'}),ch('✗ not which genes are active',960,715,'coral','c_gene',{fs:28,b:'c_spec-.3'}),
ch('the label defines part of the question',960,780,'amber','c_spec',{fs:32,b:'c_ctrl-.3'}),
ch('controls: a stain can bind imperfectly',960,780,'mint','c_ctrl',{fs:32,b:'c_bg-.3'}),
ch('background light',360,715,'coral','c_bg',{fs:28,b:'c_port-.3'}),ch('overlapping structures',960,715,'coral','c_bg+.7',{fs:28,b:'c_port-.3'}),
cd('b-amber',80,860,1760,100,'c_port-.1'),tt('we measure a labelled signal, not an all-knowing portrait of the cell',960,886,1700,'font:700 34px/1.2 Poppins;color:'+INK,'c_port+.2')
]};''',ep=2)
print(build('e2_labels',2,'labels',dict(c_label='A fluorescent label',c_nuc='One stain',c_mem='A different label',c_prot='particular protein',c_def='Remember that the nucleus',c_not='A bright nucleus',c_gene='A membrane image',c_spec='The label and its',c_ctrl='We also need controls',c_bg='Background can',c_port='We are measuring')))

# ---------------- detector ----------------
G5=GR(5,5,blobs([(1,1,.9),(3,3,.75),(2,3.6,.4)],1.0))
mk('e2_detector',1,P1,'From light to numbers on a grid','Part 1 · schematic illustration · pixel values illustrative','''
const SPEC={'''+NOTES([('c_follow','Follow the light','the <b>emitted light</b> travels through the instrument'),('c_optics','Optics and detector','optics form an image; a <b>detector</b> converts the signal into <b>numbers on a grid</b>'),('c_pixel','A pixel','each small element of the grid is a <b>pixel</b>'),('c_array','A saved image','an <b>array of numbers</b> with an experimental history'),('c_gray','Grayscale view','a larger number is usually drawn <b>brighter</b>'),('c_depend','The number also depends on','detector settings, exposure, background and processing'),('c_notmol','A pixel is not','a single molecule or a single cell'),('c_many','Many sources','can contribute to the signal recorded at one location'),('c_before','Before interpreting','what was labelled, how it was acquired, what was transformed')])+''',
els:[
ic('animal-cell',170,640,170,'c_follow',{bob:4}),ch('sample',170,740,'mint','c_follow+.3',{fs:26}),
dt([[260,640],[430,640]],'#3a9d6b','c_follow+.5',{n:4,speed:.35,r:9}),
cd('',440,520,54,240,'c_optics',{css:'border-radius:50%;background:rgba(127,159,201,.35);border:5px solid #7f9fc9',dy:0}),ch('optics',467,775,'blue','c_optics+.3',{fs:26}),
dt([[510,640],[760,640]],'#3a9d6b','c_optics+.4',{n:4,speed:.35,r:9}),
{t:'grid',x:780,y:450,cw:72,ch:72,vals:'''+G5+''',mode:'gray',a:'c_pixel',stag:.03,hot:[[2,2]],ht:'c_notmol'},
ch('detector',960,825,'lav','c_optics+.8',{fs:26}),ch('one pixel',1210,520,'amber','c_pixel+.4',{fs:26,b:'c_array'}),ar(1160,570,1000,625,'a','c_pixel+.4',{b:'c_array'}),
{t:'grid',x:780,y:450,cw:72,ch:72,vals:'''+G5+''',mode:'gray',num:255,fs:22,a:'c_array',stag:.03,hot:[[2,2]],ht:'c_notmol'},
ch('numbers with an experimental history',1500,520,'amber','c_array+.3',{fs:28,b:'c_depend'}),
ch('bigger number → brighter',1500,600,'lav','c_gray',{fs:28,b:'c_depend'}),
ch('detector settings',1480,480,'coral','c_depend',{fs:26}),ch('exposure',1480,550,'coral','c_depend+.5',{fs:26}),ch('background',1480,620,'coral','c_depend+1.0',{fs:26}),ch('processing',1480,690,'coral','c_depend+1.5',{fs:26}),
dt([[560,470],[960,630]],'#3a9d6b','c_many',{n:3,speed:.4,r:8,b:'c_before'}),dt([[560,830],[960,630]],'#e0a43a','c_many+.3',{n:3,speed:.4,r:8,b:'c_before'}),dt([[1300,630],[1000,630]],'#cf8a83','c_many+.6',{n:3,speed:.4,r:8,b:'c_before'}),
ch('not one molecule or one cell',1500,780,'amber','c_notmol',{fs:28,b:'c_before'}),
ch('what was labelled',480,905,'mint','c_before',{fs:30}),ch('how it was acquired',960,905,'blue','c_before+.7',{fs:30}),ch('what was transformed',1440,905,'lav','c_before+1.4',{fs:30})
]};''',ep=2)
print(build('e2_detector',2,'detector',dict(c_follow='Now follow',c_optics='The optics',c_pixel='Each small element',c_array='A saved image',c_gray='In a grayscale',c_depend='That display helps',c_notmol='A pixel is not',c_many='Many sources',c_before='Before interpreting')))

# ---------------- channels ----------------
MEM2=GR(5,5,lambda r,c:.1+.85*math.exp(-((math.hypot(r-2,c-2)-1.7)**2)/.7))
NUC2=GR(5,5,blobs([(2,2,.95),(0.5,3.8,.3)],0.9))
mk('e2_channels',1,P1,'Channels: separate arrays of intensity','Part 1 · schematic arrays · values illustrative','''
const SPEC={'''+NOTES([('c_two','Two images','one of <b>nuclei</b>, another of <b>membranes</b>'),('c_sep','Separate channels','we can store them as <b>separate channels</b>'),('c_each','Each channel','is its own <b>array of intensities</b>'),('c_disp','Display colours','software may show nuclei in purple and membranes in green, then <b>combine</b> them'),('c_colors','Display colours','help us <b>distinguish</b> the channels'),('c_notcol','Not true colour','not necessarily what a person would see looking at the sample'),('c_merge','A merged picture','is useful, but we must <b>keep the separate measurements</b>'),('c_conf','The risk','confusing a pleasing colour combination with a <b>biological conclusion</b>'),('c_pos','Channel 0 and channel 1','are just <b>positions in a file</b>'),('c_meta','Meaning comes from','<b>verified metadata</b>, not from guessing that channel 1 is always the nucleus')])+''',
els:[
{t:'grid',x:140,y:460,cw:62,ch:62,vals:'''+NUC2+''',mode:'gray',a:'c_two',stag:.03,b:'c_disp'},{t:'grid',x:520,y:460,cw:62,ch:62,vals:'''+MEM2+''',mode:'gray',a:'c_two+.6',stag:.03,b:'c_disp'},
{t:'grid',x:140,y:460,cw:62,ch:62,vals:'''+NUC2+''',tint:[170,110,235],a:'c_disp',stag:.02},{t:'grid',x:520,y:460,cw:62,ch:62,vals:'''+MEM2+''',tint:[70,200,120],a:'c_disp+.5',stag:.02},
ch('image of nuclei',295,795,'blue','c_two',{fs:26}),ch('image of membranes',675,795,'mint','c_two+.6',{fs:26}),
ch('channel 0',295,394,'blue','c_sep',{fs:28}),ch('channel 1',675,394,'mint','c_sep+.4',{fs:28}),
ch('each: its own array of intensities',485,850,'amber','c_each',{fs:28,b:'c_colors'}),
tt('+',485,580,80,BIG(70),'c_disp+1.2'),ar(780,620,900,620,'g','c_disp+1.4'),
{t:'grid',x:960,y:460,cw:62,ch:62,vals:'''+NUC2+''',vals2:'''+MEM2+''',merge:true,tint:[170,110,235],tint2:[70,200,120],a:'c_disp+1.8',stag:.02},
ch('merged picture',1115,795,'lav','c_disp+2.2',{fs:26}),
ch('display colours help us tell channels apart',485,850,'mint','c_colors',{fs:28,b:'c_notcol'}),ch('✗ not necessarily the colours a person would see',485,850,'coral','c_notcol',{fs:28,b:'c_merge'}),
ch('useful, but keep the separate measurements',485,850,'amber','c_merge',{fs:28,b:'c_conf'}),ch('✗ pleasing colours ≠ a biological conclusion',485,850,'coral','c_conf',{fs:28,b:'c_pos'}),
ch('channel 0 = position 0 in the file',1590,480,'blue','c_pos',{fs:28}),ch('channel 1 = position 1 in the file',1590,560,'mint','c_pos+.7',{fs:28}),
cd('b-amber',1360,640,480,200,'c_meta-.1'),{t:'tick',x:1420,y:740,r:34,a:'c_meta+.5'},tt('verified metadata tells us which channel is the nucleus',1640,665,380,T2,'c_meta+.1'),
ch('not a guess',1590,880,'coral','c_meta+.9',{fs:28})
]};''',ep=2)
print(build('e2_channels',2,'channels',dict(c_two='Suppose we acquire',c_sep='We can store',c_each='Each channel',c_disp='Software may display',c_colors='Those display colors',c_notcol='They are not necessarily',c_merge='A merge picture',c_conf='Otherwise',c_pos='Channel 0',c_meta='Their biological meaning')))

# ---------------- intensity ----------------
def dots(n,x0,y0,w,h,a,cue,col,seed=0,b=None):
    out=''
    for i in range(n):
        x=x0+((i*83+seed*41)%w);y=y0+((i*57+seed*29)%h)
        out+="cd('',%d,%d,16,16,'%s+%.2f',{css:'background:%s;border-radius:50%%;box-shadow:0 0 12px %s',dy:0%s}),\n"%(x,y,cue,a+.08*i,col,col,(",b:'%s'"%b) if b else '')
    return out
PH1="c_raw-.3"
INTENS=cd=None
INT=''
INT+="cd('',240,420,520,270,'c_ctl',{css:'background:#0e1a17;border:6px solid #cfd9d4',dy:0,b:'%s'}),cd('',1160,420,520,270,'c_ctl+.3',{css:'background:#0e1a17;border:6px solid #cfd9d4',dy:0,b:'%s'}),\n"%(PH1,PH1)
INT+="cd('',430,500,130,130,'c_ctl+.5',{css:'background:radial-gradient(circle at 40%% 35%%,#e6fff4,#5fd0aa 60%%,#2c8f74);border-radius:50%%;box-shadow:0 0 30px rgba(95,208,170,.6)',op:.45,dy:0,b:'%s'}),\n"%PH1
INT+="cd('',1350,490,150,150,'c_ctl+.8',{css:'background:radial-gradient(circle at 40%% 35%%,#ffffff,#8ff0c8 55%%,#3fb48f);border-radius:50%%;box-shadow:0 0 60px rgba(143,240,200,.95)',dy:0,b:'%s'}),\n"%PH1
INT+=dots(5,300,440,400,220,.0,'c_twice','#ff7a70',1,PH1).replace("dy:0,b","dy:0,b")+dots(6,1220,440,400,220,.0,'c_twice','#ff7a70',2,PH1)
mk('e2_intensity',1,P1,'What can brightness tell us?','Part 1 · schematic illustration · values illustrative','''
const PH1='c_raw-.3',PH2='c_temp-.3';
const SPEC={'''+NOTES([('c_q','The question','what can <b>brightness</b> tell us?'),('c_ctl','Under controlled conditions','fluorescence intensity can help <b>compare</b> labelled signals'),('c_twice','But','twice the displayed brightness does <b>not automatically</b> mean twice the number of proteins'),('c_matter','Many things matter','label behaviour, illumination, detector response, background, sample preparation'),('c_raw','Raw detector values','we call them <b>arbitrary intensity units</b> unless a justified calibration exists'),('c_arb','Arbitrary','does <b>not</b> mean useless'),('c_define','It means','we must <b>define the measurement</b> and compare compatible observations'),('c_temp','Two kinds of quantity','a temperature reading in degrees vs an uncalibrated camera value'),('c_first','The first','has a specified <b>physical scale</b>'),('c_second','The second','still supports a useful comparison, but only within the <b>same acquisition and analysis conditions</b>')])+''',
els:[
'''+INT+'''
ch('sample A',500,712,'blue','c_ctl+.6',{fs:28,b:PH1}),ch('sample B',1420,712,'blue','c_ctl+.9',{fs:28,b:PH1}),
ch('comparable under controlled conditions',960,745,'lav','c_ctl+1.0',{fs:26,b:PH1}),
ch('2× brighter',960,520,'amber','c_twice',{fs:30,b:PH1}),ch('≠ 2× the proteins',960,600,'coral','c_twice+1.6',{fs:30,b:PH1}),
ch('label behaviour',230,830,'mint','c_matter',{fs:26,b:PH1}),ch('illumination',560,830,'amber','c_matter+.6',{fs:26,b:PH1}),ch('detector response',900,830,'lav','c_matter+1.2',{fs:26,b:PH1}),ch('background',1250,830,'coral','c_matter+1.8',{fs:26,b:PH1}),ch('sample preparation',1600,830,'blue','c_matter+2.4',{fs:26,b:PH1}),
{t:'grid',x:300,y:440,cw:80,ch:80,vals:'''+GR(5,5,blobs([(1,1,.9),(3,3,.65),(2,3.6,.35)],1.0))+''',mode:'gray',num:1000,fs:22,a:'c_raw',stag:.03,b:PH2},
ch('raw detector values',500,870,'lav','c_raw+.3',{fs:28,b:PH2}),
ch('arbitrary intensity units (a.u.)',1250,500,'amber','c_raw+.8',{fs:32,b:PH2}),ch('arbitrary ≠ useless',1250,590,'mint','c_arb',{fs:32,b:PH2}),
ch('define the measurement',1250,680,'blue','c_define',{fs:32,b:PH2}),ch('compare compatible observations',1250,760,'lav','c_define+1.2',{fs:32,b:PH2}),
cd('b-blue',140,430,780,420,'c_temp-.1'),tt('a temperature reading',530,450,740,T2,'c_temp+.1'),tt('37 °C',530,560,500,BIG(120),'c_temp+.4'),ch('degrees: a specified physical scale',530,740,'blue','c_first',{fs:30}),{t:'tick',x:210,y:790,r:30,a:'c_first+.5'},
cd('b-amber',1000,430,780,420,'c_temp+.2'),tt('an uncalibrated camera value',1390,450,740,T2,'c_temp+.4'),tt('1342 a.u.',1390,560,600,BIG(100),'c_temp+.7'),ch('comparable only under the same conditions',1390,740,'amber','c_second',{fs:28}),
ch('different kinds of quantity',960,900,'lav','c_second+1.5',{fs:32})
]};''',ep=2)
print(build('e2_intensity',2,'intensity',dict(c_q='What can brightness',c_ctl='Under controlled',c_twice='twice the displayed',c_matter="behavior",c_raw='We will call our raw',c_arb='Arbitrary does not',c_define='It means that',c_temp='A temperature reading',c_first='The 1st',c_second='The 2nd')))

# ---------------- background + saturation ----------------
P1E="c_sat-.3"
BG=''
sig=[0,30,120,200,120,30,0]
for i,h in enumerate(sig):
    x=220+i*100
    BG+="br(%d,740,70,60,'#9aa8a3','c_bg+%.2f',{val:[0,1],vt:'c_bg+%.2f',vd:.6,b:'%s'}),\n"%(x,.1*i,.1*i,P1E)
    if h: BG+="br(%d,%d,70,%d,'#4d8f7e','c_bg+%.2f',{val:[0,1],vt:'c_bg+%.2f',vd:.6,b:'%s'}),\n"%(x,740-h,h,1.2+.1*i,1.2+.1*i,P1E)
tv=[40,90,150,210,270,330,390]
SA=''
for i,v in enumerate(tv):
    x=220+i*100;cap=min(v,180);col='#4d8f7e' if v<=180 else '#cf8a83'
    SA+="cd('',%d,%d,70,%d,'c_lost+%.2f',{css:'background:#b8c4bf;border-radius:10px;border:3px dashed #8a9b94',op:.45,dy:0,b:'c_exp-.3'}),\n"%(x,820-v,v,.05*i) if v>180 else ''
    SA+="br(%d,%d,70,%d,'%s','c_sat+%.2f',{val:[0,1],vt:'c_sat+%.2f',vd:.6}),\n"%(x,820-cap,cap,col,.15*i+.3,.15*i+.3)
mk('e2_bgsat',1,P1,'Two problems: background and saturation','Part 1 · schematic bars · values illustrative','''
const SPEC={'''+NOTES([('c_two','Two common problems','that make the distinction practical'),('c_bg','Background','unwanted fluorescence and a <b>detector offset</b> add signal that is not the labelled structure'),('c_noise','Noise','random fluctuations: a <b>related but distinct</b> problem'),('c_est','Needed','a <b>documented way</b> to estimate background and assess uncertainty from noise'),('c_sat','Saturation','a detector has a <b>highest recordable value</b>'),('c_reach','Once a bright region reaches that limit','stronger signals may <b>all receive the same number</b>'),('c_lost','Differences lost','changes that exist in the sample are <b>no longer in the data</b>'),('c_exp','Exposure','more exposure can make a picture look clearer <b>while saturating</b> important pixels'),('c_cont','Display contrast','changing it later <b>cannot recover</b> the missing differences'),('c_qc','Quality control','an attractive image is <b>not</b> our criterion'),('c_check','We check','raw values, settings, background and clipped regions <b>before</b> interpreting brightness')])+''',
els:[
'''+BG+'''
{t:'wave',x:220,y:740,len:690,amp:7,wl:13,col:'c',a:'c_noise',speed:9,w:4,dur:.8,b:'c_sat-.3'},
cd('',200,800,740,6,'c_two',{css:'background:#8aa59b;border-radius:3px',dy:0,b:'c_sat-.3'}),
ch('background + offset',1380,470,'coral','c_bg',{fs:30,b:'c_sat-.3'}),ch('not the labelled structure',1380,550,'coral','c_bg+1.0',{fs:30,b:'c_sat-.3'}),
ch('noise: random fluctuations',1380,640,'lav','c_noise',{fs:30,b:'c_sat-.3'}),
ch('document how to estimate background and noise',1380,730,'mint','c_est',{fs:26,b:'c_sat-.3'}),
ch('signal we want',560,860,'mint','c_bg+1.5',{fs:26,b:'c_sat-.3'}),ch('background',280,860,'coral','c_bg+.3',{fs:26,b:'c_sat-.3'}),
cd('',200,820,740,6,'c_sat',{css:'background:#8aa59b;border-radius:3px',dy:0}),
'''+SA+'''
ar(190,640,950,640,'a','c_max',{dash:'14 10',head:false}),ch('highest recordable value',1250,615,'amber','c_max+.3',{fs:30,b:'c_exp-.3'}),
ch('bright region reaches the limit',1250,700,'coral','c_reach',{fs:28,b:'c_exp-.3'}),ch('stronger signals: the same number',1250,780,'coral','c_same',{fs:28,b:'c_exp-.3'}),ch('differences are lost',1250,860,'coral','c_lost',{fs:30,b:'c_exp-.3'}),
ch('more exposure: clearer picture, saturated pixels',1400,470,'amber','c_exp',{fs:28,b:'c_check-.3'}),ch('display contrast cannot recover them',1400,560,'coral','c_cont',{fs:28,b:'c_check-.3'}),ch('attractive image ≠ quality control',1400,650,'mint','c_qc',{fs:30,b:'c_check-.3'}),
ch('raw values',1180,470,'blue','c_check',{fs:28}),ch('acquisition settings',1480,470,'mint','c_check+.5',{fs:28}),ch('background',1180,560,'amber','c_check+1.0',{fs:28}),ch('clipped regions',1480,560,'coral','c_check+1.5',{fs:28})
]};''',ep=2)
print(build('e2_bgsat',2,'background-saturation',dict(c_two='Two common problems',c_bg='First, background',c_noise='Random fluctuations',c_est='We need a documented',c_sat='Second, saturation',c_max='A detector has a highest',c_reach='Once a bright region',c_same='Stronger signals',c_lost='Their differences',c_exp='Increasing the exposure',c_cont='Changing the display',c_qc='So an attractive',c_check='We check the raw')))

# ---------------- scale & resolution ----------------
BL=GR(8,8,blobs([(3,3,.9),(4.5,5,.7)],1.6,.05))
mk('e2_scale',1,P1,'Pixel spacing, resolution and display size','Part 1 · schematic illustration · numbers illustrative','''
const SPEC={'''+NOTES([('c_grid','Image grid ↔ physical space','we must connect the grid of pixels to <b>real distance</b>'),('c_spacing','Pixel spacing','distance in the sample for <b>one step</b> between neighbouring pixels'),('c_micro','Micrometres','recorded in <b>µm</b>; one micrometre is a millionth of a metre'),('c_res','Optical resolution','a different question: how close can <b>two structures</b> be and still be told apart?'),('c_samp','Finer sampling','does <b>not</b> automatically improve the optics'),('c_enl','Enlarging on a screen','adds <b>no</b> missing detail'),('c_bar','A scale bar','shows distance in the sample, <b>not</b> a promise that smaller features are resolved'),('c_three','Keep three ideas separate','<b>sampling</b>, <b>optical detail</b>, and the size we <b>display</b> the picture')])+''',
els:[
{t:'grid',x:200,y:440,cw:70,ch:70,vals:'''+GR(6,6,lambda r,c:.15+.7*math.exp(-((r-2.4)**2+(c-2.8)**2)/2.5))+''',mode:'gray',a:'c_grid',stag:.03,b:'c_res-.3'},
ar(235,430,305,430,'a','c_spacing',{head:false,b:'c_res-.3'}),ch('pixel spacing',270,382,'amber','c_spacing+.3',{fs:26,b:'c_res-.3'}),
ch('e.g. 2 µm per step',700,500,'amber','c_spacing+1.0',{fs:30,b:'c_res-.3'}),
cd('b-blue',640,590,640,200,'c_micro-.1',{b:'c_res-.3'}),tt('1 µm = 0.000001 m',960,620,600,T1,'c_micro+.1',{b:'c_res-.3'}),tt('one millionth of a metre',960,690,600,'font:600 28px Inter;color:'+MUT,'c_micro+.4',{b:'c_res-.3'}),
cd('',200,880,420,6,'c_micro+.3',{css:'background:#26765d;border-radius:3px',dy:0,b:'c_res-.3'}),ch('distance in the sample',410,830,'mint','c_micro+.6',{fs:26,b:'c_res-.3'}),
cd('',300,500,100,100,'c_res',{css:'background:radial-gradient(circle at 40% 35%,#e6fff4,#5fd0aa 60%,#2c8f74);border-radius:50%;box-shadow:0 0 30px rgba(95,208,170,.6)',dy:0,b:'c_samp-.3'}),cd('',520,500,100,100,'c_res+.2',{css:'background:radial-gradient(circle at 40% 35%,#e6fff4,#5fd0aa 60%,#2c8f74);border-radius:50%;box-shadow:0 0 30px rgba(95,208,170,.6)',dy:0,b:'c_samp-.3'}),
ch('far apart: two structures',460,640,'mint','c_res+.6',{fs:28,b:'c_samp-.3'}),
cd('',1190,500,100,100,'c_res+.8',{css:'background:radial-gradient(circle at 40% 35%,#e6fff4,#5fd0aa 60%,#2c8f74);border-radius:50%;box-shadow:0 0 30px rgba(95,208,170,.6)',dy:0,b:'c_samp-.3'}),cd('',1235,500,100,100,'c_res+1.0',{css:'background:radial-gradient(circle at 40% 35%,#e6fff4,#5fd0aa 60%,#2c8f74);border-radius:50%;box-shadow:0 0 30px rgba(95,208,170,.6)',dy:0,b:'c_samp-.3'}),
ch('too close: look like one',1260,640,'coral','c_res+1.6',{fs:28,b:'c_samp-.3'}),
tt('can the instrument tell them apart?',960,780,900,T2,'c_res+2.4',{b:'c_samp-.3'}),
{t:'grid',x:300,y:440,cw:60,ch:60,vals:'''+GR(4,4,lambda r,c:.1+.8*math.exp(-((r-1.5)**2+(c-1.5)**2)/1.2))+''',mode:'gray',a:'c_samp',stag:.03,b:'c_enl-.3'},
{t:'grid',x:760,y:440,cw:30,ch:30,vals:'''+BL+''',mode:'gray',gap:2,a:'c_samp+.6',stag:.01,b:'c_enl-.3'},
ch('coarse pixels',420,700,'blue','c_samp+.3',{fs:28,b:'c_enl-.3'}),ch('finer pixels',880,700,'blue','c_samp+1.0',{fs:28,b:'c_enl-.3'}),
tt('→',620,520,100,BIG(80),'c_samp+.6',{b:'c_enl-.3'}),ch('same blurry optics',1250,520,'coral','c_samp+1.6',{fs:32,b:'c_enl-.3'}),ch('✗ finer sampling ≠ better optics',1250,610,'coral','c_samp+2.2',{fs:30,b:'c_enl-.3'}),
ic('tissue-section-slide',420,620,130,'c_enl',{mv:{a:'c_enl+1.0',dx:260,dy:-30,s:2.4,dur:1.6},b:'c_bar-.3'}),ch('bigger on screen',850,820,'amber','c_enl+2.0',{fs:30,b:'c_bar-.3'}),ch('✗ no missing detail added',1300,700,'coral','c_enl+2.6',{fs:30,b:'c_bar-.3'}),
ic('tissue-section-slide',700,610,320,'c_bar',{b:'c_three-.3'}),cd('',640,800,260,10,'c_bar+.5',{css:'background:#183b32;border-radius:3px',dy:0,b:'c_three-.3'}),ch('10 µm (illustrative)',770,840,'mint','c_bar+.7',{fs:28,b:'c_three-.3'}),
ch('distance in the sample',1380,520,'mint','c_bar+.4',{fs:30,b:'c_three-.3'}),ch('✗ not a promise that smaller features are resolved',1380,610,'coral','c_bar+1.6',{fs:28,b:'c_three-.3'}),
cd('b-blue',100,500,520,300,'c_three-.1'),tt('sampling',360,540,480,T1,'c_three+.1'),tt('how finely we sample space',360,640,440,'font:600 26px Inter;color:'+INK,'c_three+.3'),
cd('b-lav',700,500,520,300,'c_three+.6'),tt('optical detail',960,540,480,T1,'c_three+.8'),tt('what the optics can tell apart',960,640,440,'font:600 26px Inter;color:'+INK,'c_three+1.0'),
cd('b-amber',1300,500,520,300,'c_three+1.3'),tt('display size',1560,540,480,T1,'c_three+1.5'),tt('how large we show the picture',1560,640,440,'font:600 26px Inter;color:'+INK,'c_three+1.7')
]};''',ep=2)
print(build('e2_scale',2,'scale-resolution',dict(c_grid='We also need',c_spacing='Pixel spacing',c_micro='micrometers',c_res='Optical resolution',c_samp='Sampling an image',c_enl='Enlarging the picture',c_bar='A scale bar',c_three='Keep these')))

# ---------------- area math ----------------
AM="'c_real-.3'"
mk('e2_area',1,P1,'A tiny example: pixels to area','Part 1 · teaching numbers, not measurements from the real image','''
const SPEC={'''+NOTES([('c_work','A tiny example','so the units become <b>concrete</b>'),('c_pix','The grid','each pixel is <b>2 µm wide</b> and <b>2 µm tall</b>'),('c_one','One pixel','2 × 2 = <b>4 square micrometres</b>'),('c_25','A region of 25 pixels','25 × 4 = <b>100 µm²</b>'),('c_both','Both directions','area has <b>two dimensions</b>; multiplying by the spacing once gives the wrong units and the wrong answer'),('c_teach','Teaching numbers','not measurements from today’s biological image'),('c_real','In the real code','read the actual spacing from the <b>source metadata</b> and keep it attached to the result')])+''',
els:[
{t:'grid',x:160,y:470,cw:80,ch:80,vals:'''+GR(5,5,lambda r,c:.35)+''',mode:'heat',a:'c_pix',stag:.02,hot:[[0,0]],ht:'c_one',gap:6},
ar(160,452,236,452,'a','c_pix+.4',{head:false}),ch('2 µm',198,405,'amber','c_pix+.6',{fs:28}),ar(138,470,138,546,'a','c_pix+.8',{head:false}),ch('2 µm',80,490,'amber','c_pix+1.0',{fs:26}),
cd('b-blue',640,440,600,120,'c_one-.1'),tt('one pixel: 2 × 2 = 4 µm²',940,470,560,T1,'c_one+.1'),
{t:'grid',x:160,y:470,cw:80,ch:80,vals:'''+GR(5,5,lambda r,c:.85)+''',mode:'heat',a:'c_25',stag:.03,gap:6},
cd('b-mint',640,580,860,120,'c_25-.1'),tt('25 pixels × 4 µm² = 100 µm²',1070,610,820,T1,'c_25+.2'),
ch('area has two dimensions: multiply in both directions',1000,730,'amber','c_both',{fs:30}),
ch('✗ spacing once: 25 × 2 = 50 µm  → wrong units, wrong answer',1090,810,'coral','c_both+2.6',{fs:28}),
ch('teaching numbers, not today’s image',1560,470,'amber','c_teach',{fs:28}),
cd('b-lav',640,860,1200,110,'c_real-.1'),tt('real code: read the spacing from the source metadata and keep it attached to the result',1240,890,1140,'font:700 30px/1.25 Poppins;color:'+INK,'c_real+.2')
]};''',ep=2)
print(build('e2_area',2,'area-math',dict(c_work="Let's work",c_pix='Imagine a square',c_one='One pixel then',c_25='If a selected',c_both='We multiply',c_teach='These are teaching',c_real='In the real code')))
