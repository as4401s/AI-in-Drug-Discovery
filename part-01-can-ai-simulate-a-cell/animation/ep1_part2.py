import sys;sys.path.insert(0,'/home/claude/work/scenes')
from mk import mk
FOOT='Define the research problem · schematic illustrations'
# ---- problem contract ----
mk('e1_contract',2,'Define the research problem','Specify inputs, output and a test','Define the research problem · illustrative study design, not a new experiment · schematic icons','''
const SPEC={notes:{x:60,y:226,w:1800,h:150,list:[
['c_ctrl','An illustrative study','a cell-response study with a <b>control group</b> and a group receiving a specified <b>intervention</b>'],
['c_input','Input','the starting <b>cell context</b> and a description of the <b>intervention</b> — for a compound, also <b>concentration</b> and <b>exposure time</b>'],
['c_out','Target output','the <b>RNA expression profile</b> measured afterward: which gene-associated RNA levels <b>rise</b>, <b>fall</b> or <b>stay similar</b>'],
['c_judge','Test','compare the prediction with <b>measurements kept separate</b> from model fitting, under a suitable test design and <b>baseline</b>'],
['c_def','What it tells us','a <b>defined cellular response</b> — it does not by itself establish that a medicine will help a patient'],
['c_attach','Keep it attached','the cell type, intervention, measurement and evaluation <b>stay attached</b> to the result'],
['c_next','Next','we can now introduce the proteins and experiments that recur through this course']]},
els:[
cd('b-blue',300,430,560,380,'c_ctrl',{b:'c_input-.3'}),tt('Control group',580,452,500,T1,'c_ctrl+.2',{b:'c_input-.3'}),ic('petri-dish',580,640,230,'c_ctrl+.3',{b:'c_input-.3',bob:5}),
cd('b-coral',1060,430,560,380,'c_interv-.2',{b:'c_input-.3'}),tt('Intervention group',1340,452,500,T1,'c_interv-.1',{b:'c_input-.3'}),ic('petri-dish',1340,660,230,'c_interv',{b:'c_input-.3',bob:5}),
ic('pipette',1500,520,150,'c_interv+.2',{b:'c_input-.3',bob:6}),dt([[1442,590],[1442,650]],'c','c_interv+.3',{n:2,speed:.6,r:9,b:'c_input-.3'}),
ch('an illustrative design — not an experiment we have run',960,925,'amber','c_illus',{b:'c_input-.3',fs:30}),
cd('b-blue',60,420,560,440,'c_input-.1'),tt('Input',340,436,520,T1,'c_input'),
ic('animal-cell',200,600,170,'c_ctx-.2',{bob:5}),ch('starting cell context',200,720,'blue','c_ctx',{fs:24}),
tt('+',340,560,80,BIG(70),'c_desc-.3'),
ic('small-molecule',480,610,190,'c_desc-.2',{bob:5}),ch('the intervention',480,720,'coral','c_desc',{fs:24}),
ch('concentration',200,790,'amber','c_conc-.2',{fs:24}),ch('exposure time',480,790,'lav','c_time-.2',{fs:24}),
cd('b-lav',680,420,560,440,'c_out-.1'),tt('Output',960,436,520,T1,'c_out'),
ic('expression-heatmap',960,590,250,'c_out+.3',{bob:5}),
ch('↑ rise',790,720,'coral','c_rise-.2',{fs:26}),ch('↓ fall',940,720,'blue','c_fall-.2',{fs:26}),ch('↔ stay similar',1110,720,'lav','c_sim-.2',{fs:26}),
ch('RNA expression profile',960,790,'mint','c_out+1.5',{fs:24}),
cd('b-amber',1300,420,560,440,'c_judge-.1'),tt('Test',1580,436,520,T1,'c_judge'),
ic('training-test-split',1580,590,240,'c_judge+.3',{bob:5}),
ch('measurements kept separate',1580,720,'amber','c_sep-.2',{fs:24}),ch('a suitable test design + baseline',1580,790,'mint','c_base-.8',{fs:24}),
ch('✓  a defined cellular response',600,905,'mint','c_def',{b:'c_attach-.3',fs:30}),
ch('✗  not: “a medicine will help a patient”',1340,905,'coral','c_not',{b:'c_attach-.3',fs:30}),
cd('b-mint',60,880,1800,110,'c_attach',{b:'c_next-.3'}),tt('the prediction result',960,908,560,T2,'c_attach+.2',{b:'c_next-.3'}),
ch('cell type',250,917,'blue','c_attach+.3',{b:'c_next-.3'}),ch('intervention',520,917,'coral','c_attach+1.2',{b:'c_next-.3'}),
ch('measurement',1400,917,'amber','c_attach+2.1',{b:'c_next-.3'}),ch('evaluation',1670,917,'lav','c_attach+3.0',{b:'c_next-.3'}),
cd('b-lav',360,880,1200,110,'c_next'),tt('next · the proteins and experiments we will reuse',960,908,1100,T2,'c_next+.2')
]};''')
# ---- EGFR ----
mk('e1_egfr',2,'Define the research problem','Our guided target: EGFR','Define the research problem · schematic illustrations · EGFR biology simplified','''
const SPEC={notes:{x:60,y:226,w:1800,h:150,list:[
['c_egfr','EGFR — our recurring example','a receptor involved in signals that influence <b>cell division</b> and <b>survival</b>'],
['c_recv','A receptor','receives a <b>molecular signal</b> and helps the cell respond to it'],
['c_cancer','In some cancers','changes involving the signaling system contribute to <b>abnormal growth</b> — which is why EGFR is an important <b>drug target</b>'],
['c_course','A consistent example','we will use it when learning about <b>sequences, molecules, assays and models</b>'],
['c_eval','The goal','we are learning how to <b>evaluate a research question</b> — not selecting treatment for an individual patient']]},
els:[
ic('membrane-receptor',560,700,330,'c_egfr',{bob:5}),ch('EGFR',560,915,'blue','c_egfr+.3',{fs:40,px:34}),
ch('a signal molecule',320,430,'amber','c_recv-1.4',{b:'c_cancer-.3'}),
ic('growth-factor-dimer',560,440,150,'c_recv-1.5',{mv:{a:'c_recv-1.0',dy:112,dur:1.4},b:'c_cancer-.3'}),
rg(560,590,'a','c_recv+.5',{n:2,b:'c_cancer-.3'}),
ch('receives the signal',850,560,'amber','c_recv',{b:'c_cancer-.3'}),
dt([[730,690],[1000,650],[1160,610]],'c','c_div-.8',{n:3,speed:.35,r:11,b:'c_cancer-.3',trail:6}),
dt([[730,710],[1000,760],[1160,820]],'c','c_surv-.8',{n:3,speed:.35,r:11,b:'c_cancer-.3',trail:6}),
ic('mitosis',1310,610,190,'c_div-.3',{b:'c_cancer-.3',bob:5}),ch('cell division',1310,725,'mint','c_div',{b:'c_cancer-.3'}),
ic('animal-cell',1310,830,150,'c_surv-.3',{b:'c_cancer-.3',bob:5,ph:1}),ch('cell survival',1310,915,'blue','c_surv',{b:'c_cancer-.3'}),
ch('the cell responds',960,805,'lav','c_resp-.3',{b:'c_cancer-.3',fs:26}),
ic('tumor-microenvironment',1460,690,340,'c_cancer+.3',{b:'c_course-.3',bob:5}),ch('abnormal growth in some cancers',1460,890,'coral','c_growth-.6',{b:'c_course-.3'}),
ic('small-molecule',240,560,190,'c_target-1.3',{mv:{a:'c_target-1.0',dx:160,dy:90,dur:1.4},b:'c_course-.3'}),
rg(450,650,'c','c_target+.4',{n:3,b:'c_course-.3'}),ch('an important drug target',860,640,'coral','c_target',{b:'c_course-.3'}),
ar(730,690,1100,540,'g','c_seqs-.3',{dash:'3 12',head:false,b:'c_eval-.3'}),ar(730,700,1100,640,'g','c_mols-.3',{dash:'3 12',head:false,b:'c_eval-.3'}),ar(730,710,1100,740,'g','c_assays-.3',{dash:'3 12',head:false,b:'c_eval-.3'}),ar(730,720,1100,840,'g','c_models-.3',{dash:'3 12',head:false,b:'c_eval-.3'}),
ch('sequences',1300,515,'blue','c_seqs-.2',{b:'c_eval-.3',fs:34}),ch('molecules',1300,615,'mint','c_mols-.2',{b:'c_eval-.3',fs:34}),ch('assays',1300,715,'amber','c_assays-.2',{b:'c_eval-.3',fs:34}),ch('models',1300,815,'lav','c_models-.2',{b:'c_eval-.3',fs:34}),
ch('✓  learning how to evaluate a research question',1360,640,'mint','c_eval',{fs:32}),ch('✗  not selecting treatment for an individual patient',1360,780,'coral','c_not',{fs:32})
]};''')
# ---- mutation ----
mk('e1_mutation',2,'Define the research problem','What does C797S mean?','Define the research problem · schematic sequence strip, neighbouring letters illustrative','''
const POS=['793','794','795','796','797','798','799','800','801'];
const X=i=>447+i*114;
const SPEC={notes:{x:60,y:226,w:1800,h:150,list:[
['c_seq','A precise label for a change','a protein sequence gives us a precise way to describe a change'],
['c_three','C797S has three parts','the letter it starts with, the <b>position</b>, and the letter it ends with'],
['c_means','What it means','the amino acid <b>cysteine at position 797</b> is replaced by <b>serine</b>'],
['c_ref','Check the numbering','the position refers to a particular <b>reference sequence</b> — check it before running any code'],
['c_chem','Why one position can matter','amino acids have <b>different chemical properties</b>'],
['c_alone','But…','the sequence change alone does not tell us the <b>full biological consequence</b>'],
['c_need','What we also need','a <b>method</b>, a <b>measurement</b> and an appropriate <b>comparison</b>']]},
els:[
...['L','G','V','D'].map((l,i)=>tl(l,X(i),450,100,'c_seq+'+(i*.15),{neutral:1})),
tl('C',X(4),450,100,'c_seq+.6',{b:'c_rep',hot:[0],ht:'c_C',pal:'amber'}),tl('S',X(4),450,100,'c_rep+.2',{hot:[0],ht:'c_rep+.4',pal:'coral'}),
...['A','P','E','K'].map((l,i)=>tl(l,X(5+i),450,100,'c_seq+'+(.9+i*.15),{neutral:1})),
...POS.map((p,i)=>tt(p,X(i)+50,562,100,'font:600 24px Inter;color:'+(i==4?INK:MUT),'c_seq+.9')),
cd('b-blue',520,650,230,140,'c_three',{b:'c_ref-.3'}),cd('b-amber',845,650,230,140,'c_three+.2',{b:'c_ref-.3'}),cd('b-coral',1170,650,230,140,'c_three+.4',{b:'c_ref-.3'}),
tt('C',635,672,200,BIG(80),'c_C',{b:'c_ref-.3'}),tt('797',960,690,200,BIG(66),'c_797',{b:'c_ref-.3'}),tt('S',1285,672,200,BIG(80),'c_S',{b:'c_ref-.3'}),
ch('starting letter',635,830,'blue','c_C+.3',{b:'c_ref-.3',fs:26}),ch('position',960,830,'amber','c_797+.3',{b:'c_ref-.3',fs:26}),ch('ending letter',1285,830,'coral','c_S+.3',{b:'c_ref-.3',fs:26}),
ch('cysteine → serine',960,905,'mint','c_rep',{b:'c_ref-.3',fs:34}),
ch('numbering follows one particular reference sequence',960,700,'amber','c_ref',{b:'c_chem-.3',fs:32}),ch('✓  check the sequence and numbering before running code',960,810,'mint','c_check',{b:'c_chem-.3',fs:32}),
cd('b-amber',640,640,180,180,'c_chem',{b:'c_alone-.3',css:'border-radius:50%;border:5px solid #ac8b42'}),tt('C',730,672,160,BIG(96),'c_chem+.2',{b:'c_alone-.3'}),
cd('b-coral',1100,640,180,180,'c_chem+.4',{b:'c_alone-.3',css:'border-radius:50%;border:5px solid #b76d66'}),tt('S',1190,672,160,BIG(96),'c_chem+.6',{b:'c_alone-.3'}),
tt('≠',960,670,140,BIG(110),'c_props-.3',{b:'c_alone-.3'}),ch('different chemical properties',960,880,'lav','c_props-.2',{b:'c_alone-.3',fs:32}),
ic('protein-mutation',640,740,330,'c_alone',{b:'c_need-.3',bob:5}),ar(830,740,1010,740,'g','c_alone+.8',{b:'c_need-.3'}),
cd('b-coral',1040,640,560,200,'c_alone+1.2',{b:'c_need-.3'}),tt('the full biological consequence',1270,690,400,T1,'c_alone+1.5',{b:'c_need-.3'}),tt('?',1530,690,100,BIG(96),'c_alone+1.8',{b:'c_need-.3',pulse:1}),
cd('b-mint',120,620,480,330,'c_need-.1'),ic('pipette',360,760,200,'c_need',{bob:5}),tt('a method',360,640,420,T1,'c_need+.2'),
cd('b-amber',720,620,480,330,'c_meas-.1'),ic('well-plate',960,770,240,'c_meas',{bob:5}),tt('a measurement',960,640,420,T1,'c_meas+.2'),
cd('b-lav',1320,620,480,330,'c_cmp-.1'),ic('protein-mutation',1560,780,260,'c_cmp',{bob:5}),tt('an appropriate comparison',1560,640,440,T1,'c_cmp+.2')
]};''')
# ---- KRAS ----
mk('e1_kras',2,'Define the research problem','A second target becomes your challenge','Define the research problem · schematic illustrations · protein biology simplified','''
const SPEC={notes:{x:60,y:226,w:1800,h:150,list:[
['c_k','KRAS — our challenge protein','helps us avoid learning <b>one example by rote</b>'],
['c_sig','A different protein','KRAS takes part in <b>cellular signaling</b> and behaves differently from EGFR'],
['c_g12','A change we will examine','<b>G12D</b>: glycine at position 12 becomes aspartate'],
['c_apply','Apply the ideas again','eventually apply related computational ideas to this <b>second protein</b> and ask <b>where the conclusions change</b>'],
['c_chem','Later','we will introduce the relevant <b>chemistry</b> and <b>disease biology</b> as we reach it'],
['c_today','For today','a method should be understandable enough to <b>apply to a second case</b> and recognize its <b>limitations</b>']]},
els:[
cd('b-blue',120,480,700,320,'c_k-.3'),tt('EGFR · our recurring example',470,500,640,T2,'c_k'),ic('membrane-receptor',300,665,210,'c_k+.2',{bob:5}),tt('a receptor in the cell membrane',590,610,300,'font:500 26px/1.25 Inter;color:'+INK,'c_k+.4',{c:false}),
cd('b-lav',1100,480,700,320,'c_k+.6'),tt('KRAS · our challenge protein',1450,500,640,T2,'c_k+.8'),ic('conformational-switch',1450,660,330,'c_k+1.0',{bob:5}),
ch('takes part in cellular signaling',1450,730,'lav','c_sig',{fs:26,dy:0}),
tt('≠',960,570,140,BIG(110),'c_diff-.3',{b:'c_apply-.3'}),ch('behaves differently',960,790,'coral','c_diff',{b:'c_apply-.3',fs:26}),
cd('b-blue',470,880,120,100,'c_g12',{b:'c_apply-.3'}),cd('b-amber',620,880,160,100,'c_g12+.2',{b:'c_apply-.3'}),cd('b-coral',810,880,120,100,'c_g12+.4',{b:'c_apply-.3'}),
tt('G',530,892,100,BIG(60),'c_g12',{b:'c_apply-.3'}),tt('12',700,896,140,BIG(54),'c_g12+.2',{b:'c_apply-.3'}),tt('D',870,892,100,BIG(60),'c_g12+.4',{b:'c_apply-.3'}),
tt('glycine at position 12 becomes aspartate',1370,900,780,'font:600 32px/1.2 Inter;color:'+INK,'c_gly',{b:'c_apply-.3'}),
ar(470,430,1130,430,'g','c_apply',{d:'M 470 470 Q 800 380 1130 470',b:'c_chem-.3'}),ch('same method',800,395,'mint','c_apply+.5',{b:'c_chem-.3',fs:28}),
ch('where do the conclusions change?',960,880,'amber','c_where-.3',{b:'c_chem-.3',fs:32}),
ch('chemistry',640,880,'blue','c_chem',{b:'c_today-.3',fs:34,op:.85}),ch('disease biology',1000,880,'coral','c_chem+.6',{b:'c_today-.3',fs:34,op:.85}),ch('introduced as we reach them',1480,880,'lav','c_chem+1.0',{b:'c_today-.3',fs:28}),
ch('✓  a method you can apply to a second case',640,880,'mint','c_second-.3',{fs:30}),ch('✓  and know its limitations',1330,880,'amber','c_lim-.3',{fs:30})
]};''')
# ---- assay ----
mk('e1_assay',2,'Define the research problem','What do experiments measure?','Define the research problem · schematic illustrations · assay bars illustrative','''
const SPEC={notes:{x:60,y:226,w:1800,h:150,list:[
['c_before','Before predicting','ask first what the <b>experiment measures</b>'],
['c_assay','An assay','a <b>procedure for measuring a particular effect</b>'],
['c_one','Assay type 1','does a molecule <b>reduce the activity of a purified protein</b>?'],
['c_another','Assay type 2','measure the <b>growth or appearance of cells</b> after exposure to the molecule'],
['c_related','Related, but different','they describe <b>different systems and endpoints</b>'],
['c_strong','One piece of evidence','a strong purified-protein result is <b>one piece</b> of the picture'],
['c_inside','Inside a cell','we also need information about <b>the cell itself</b> and the <b>conditions around it</b>']]},
els:[
ic('well-plate',560,690,420,'c_before',{b:'c_one-.3',bob:5}),ch('What does the experiment measure?',960,430,'amber','c_before+.3',{b:'c_assay-.3',fs:34}),
ic('pipette',820,560,170,'c_before+.6',{b:'c_one-.3',bob:6}),dt([[755,630],[755,690]],'c','c_before+.8',{n:2,speed:.6,r:9,b:'c_one-.3'}),
ch('an assay = a procedure for measuring one effect',1330,690,'mint','c_assay',{b:'c_one-.3',fs:30}),
cd('b-lav',140,430,800,400,'c_one-.2'),tt('Purified protein assay',540,452,720,T1,'c_one'),
ic('folded-protein',380,640,230,'c_one+.3',{bob:5}),ic('small-molecule',660,520,170,'c_one+.4',{mv:{a:'c_one+1.5',dx:-170,dy:110,dur:1.5},bob:4}),
tt('activity of the protein',540,740,560,'font:600 26px Inter;color:'+MUT,'c_prot-1.5'),br(300,775,480,26,'#4d8f7e','c_prot-1',{dir:'right',val:[.85,.3],vt:'c_prot',vd:1.6,recol:[.5,'#4d8f7e'],col:'#b76d66'}),
cd('b-mint',980,430,800,400,'c_another-.2'),tt('Cell assay',1380,452,720,T1,'c_another'),
ic('animal-cell',1260,640,180,'c_another+.3',{bob:5}),ic('animal-cell',1470,640,180,'c_another+.5',{bob:5,ph:1.5}),ic('animal-cell',1640,640,120,'c_growth+.2',{bob:5,ph:3}),
tt('growth or appearance after exposure',1380,740,720,'font:600 26px Inter;color:'+MUT,'c_growth'),
rg(1380,640,'m','c_growth+.8',{n:3,r0:60,r1:190}),
tt('↔',960,590,110,BIG(80),'c_related-.2',{b:'c_inside-.3'}),ch('related, but different systems and endpoints',960,860,'amber','c_related',{b:'c_strong-.3',fs:30}),
rg(380,650,'a','c_strong',{n:3,r0:130,r1:210,b:'c_inside-.3',sw:10}),ch('one piece of evidence',540,860,'lav','c_strong+.2',{b:'c_inside-.3',fs:30}),
ch('the cell itself',1100,890,'blue','c_inside',{fs:32}),ch('the conditions around it',1500,890,'coral','c_cond-.8',{fs:32}),
ar(1100,880,1250,810,'b','c_inside+.3',{w:7}),ar(1500,880,1470,810,'c','c_cond-.6',{w:7})
]};''')
# ---- matrix ----
rows=6;cols=8
import random
random.seed(7)
vals=[[random.random() for _ in range(cols)] for _ in range(rows)]
def col(v):
    a=(0xee,0xf3,0xf0);b=(0x3f,0x7f,0x6c)
    return '#%02x%02x%02x'%tuple(int(a[i]+(b[i]-a[i])*v) for i in range(3))
cells=''
for r in range(rows):
    for c in range(cols):
        cells+="cd('',%d,%d,104,70,'c_roughly+%.2f',{css:'background:%s;border-radius:10px',b:null,dy:0}),\n"%(780+c*112,470+r*76,0.35*r+0.06*c,col(vals[r][c]))
    cells+="ic('animal-cell',690,%d,62,'c_roughly+%.2f',{bob:3,ph:%d}),\n"%(505+r*76,0.35*r,r)
heads=''.join("tt('gene %d',%d,430,100,'font:600 22px Inter;color:'+MUT,'c_table-.4'),\n"%(c+1,832+c*112) for c in range(cols))
mk('e1_matrix',2,'Define the research problem','A cell becomes a row of measurements','Define the research problem · schematic table, values illustrative, not measured data','''
const SPEC={notes:{x:60,y:226,w:1800,h:150,list:[
['c_sc','Single-cell RNA sequencing','one way to gather information about individual cells'],
['c_roughly','Very roughly','the experiment records <b>RNA linked to many genes</b> in <b>individual cells</b> — and we can organize it as a <b>table</b>'],
['c_row','Rows and columns','each <b>row</b> is a measured <b>cell</b>; each <b>column</b> is a <b>gene</b>'],
['c_entry','An entry','an <b>RNA count</b> or a processed <b>expression value</b>'],
['c_many','A detailed profile','a row with many columns gives the model a <b>detailed numerical profile</b> — not a photograph of the cell'],
['c_leaves','What it leaves out','much of the cell’s <b>protein activity</b> and its <b>physical organization</b>']]},
els:[
ic('animal-cell',300,650,280,'c_sc',{bob:5}),ch('single-cell RNA sequencing',300,455,'lav','c_sc+.3',{b:'c_row-.3',fs:30}),
dt([[430,650],[600,650],[760,600]],'c','c_roughly',{n:4,speed:.3,r:10,b:'c_row-.3',trail:6}),
'''+heads+cells+'''
ch('one cell per row',420,955,'blue','c_row',{b:'c_entry-.3',fs:30}),ch('one gene per column',1230,955,'mint','c_col',{b:'c_entry-.3',fs:30}),
cd('',774,%d,968,76,'c_row',{css:'border:6px solid #e0a43a;border-radius:16px;background:rgba(224,164,58,.1)',b:'c_entry-.3'}),
cd('',%d,425,116,%d,'c_col',{css:'border:6px solid #4d8f7e;border-radius:16px;background:rgba(77,143,126,.1)',b:'c_entry-.3'}),
cd('',%d,%d,116,80,'c_entry',{css:'border:7px solid #b76d66;border-radius:14px;background:rgba(183,109,102,.12)',b:'c_many-.3'}),
ch('an RNA count or expression value',1250,955,'coral','c_entry+.2',{b:'c_many-.3',fs:30}),
cd('',774,%d,968,76,'c_many',{css:'border:6px solid #e0a43a;border-radius:16px;background:rgba(224,164,58,.14)'}),
ch('a detailed numerical profile',1250,955,'amber','c_many+.3',{b:'c_leaves-.3',fs:30}),
ch('✗  not a photograph of the cell',700,955,'coral','c_photo',{b:'c_leaves-.3',fs:30}),
ch('leaves out much protein activity',720,955,'coral','c_prot-1.3',{fs:28}),ch('and its physical organization',1260,955,'lav','c_org-.5',{fs:28})
]};'''%(470+1*76-3, 780+2*112-6, rows*76+50, 780+4*112-6, 470+3*76-5, 470+2*76-3))
# ---- perturbation ----
genes=''.join("tt('gene %d',%d,792,100,'font:600 22px Inter;color:'+MUT,'c_rna+%.2f',{b:'c_job-.3'}),\n"%(i+1,560+i*125,i*.15) for i in range(8))
hs=[90,-60,40,-110,70,-30,110,20]
dbars=''
for i,h in enumerate(hs):
    if h>0: dbars+="br(%d,%d,70,%d,'#cf8a83','c_rna+%.2f',{val:[0,1],vt:'c_rna+%.2f',vd:.8,b:'c_job-.3'}),\n"%(540+i*125,640-h,h,i*.15+.3,i*.15+.3)
    else: dbars+="br(%d,644,70,%d,'#7f9fc9','c_rna+%.2f',{dir:'down',val:[0,1],vt:'c_rna+%.2f',vd:.8,b:'c_job-.3'}),\n"%(540+i*125,-h,i*.15+.3,i*.15+.3)
mk('e1_pert',2,'Define the research problem','Change something and measure the response','Define the research problem · schematic illustrations · bars illustrative, not measured data','''
const SPEC={notes:{x:60,y:226,w:1800,h:150,list:[
['c_now','A more useful question','than simply naming a cell type: <b>what changes when we intervene?</b>'],
['c_pert','Perturbation','researchers call such an intervention a <b>perturbation</b>'],
['c_ex','Examples','reduce the activity of a <b>gene</b>, introduce a <b>chemical compound</b>, or change a cell’s <b>environment</b>'],
['c_meas','Measure and compare','measure a response and compare it with a <b>suitable control</b>'],
['c_rna','The target','if the measurement is RNA expression, the target is a <b>pattern of expression changes</b>'],
['c_job','The model’s job','connect the <b>intervention</b> and the <b>cellular context</b> to the measured outcome'],
['c_control','The control is essential','cells <b>vary</b> even when we have not deliberately changed anything']]},
els:[
ic('animal-cell',470,690,330,'c_now',{b:'c_meas-.3',bob:5}),
ch('What changes when we intervene?',1250,560,'amber','c_what-.2',{b:'c_ex-.3',fs:42,px:36}),ch('an intervention = a perturbation',1250,700,'coral','c_pert',{b:'c_ex-.3',fs:40,px:36}),
cd('b-lav',720,450,340,330,'c_ex-.1',{b:'c_meas-.3'}),tt('reduce the activity of a gene',890,468,300,T2,'c_ex+.1',{b:'c_meas-.3'}),ic('dna-helix',800,640,130,'c_ex+.3',{b:'c_meas-.3',bob:4}),br(900,570,60,140,'#8b75b0','c_ex+.5',{val:[1,.3],vt:'c_ex+.9',vd:1.4,b:'c_meas-.3'}),
cd('b-coral',1100,450,340,330,'c_chem-.3',{b:'c_meas-.3'}),tt('introduce a chemical compound',1270,468,300,T2,'c_chem-.1',{b:'c_meas-.3'}),ic('small-molecule',1270,640,230,'c_chem+.1',{b:'c_meas-.3',bob:4}),
cd('b-mint',1480,450,340,330,'c_env-.3',{b:'c_meas-.3'}),tt('change the cell’s environment',1650,468,300,T2,'c_env-.1',{b:'c_meas-.3'}),ic('petri-dish',1650,650,220,'c_env+.1',{b:'c_meas-.3',bob:4}),
rg(470,690,'l','c_ex+.8',{n:1,r0:80,r1:200,b:'c_meas-.3'}),rg(470,690,'c','c_chem+.4',{n:1,r0:80,r1:200,b:'c_meas-.3'}),rg(470,690,'m','c_env+.2',{n:1,r0:80,r1:200,b:'c_meas-.3'}),
cd('b-blue',200,450,700,380,'c_meas',{b:'c_rna-.3'}),tt('control',550,470,640,T1,'c_meas+.2',{b:'c_rna-.3'}),ic('animal-cell',380,650,210,'c_meas+.3',{b:'c_rna-.3',bob:4}),
br(560,705,60,110,'#7f9fc9','c_meas+.6',{dir:'up',val:[0,1],vt:'c_meas+.6',vd:.8,b:'c_rna-.3'}),br(640,745,60,70,'#7f9fc9','c_meas+.8',{val:[0,1],vt:'c_meas+.8',vd:.8,b:'c_rna-.3'}),br(720,675,60,140,'#7f9fc9','c_meas+1.0',{val:[0,1],vt:'c_meas+1.0',vd:.8,b:'c_rna-.3'}),br(800,725,60,90,'#7f9fc9','c_meas+1.2',{val:[0,1],vt:'c_meas+1.2',vd:.8,b:'c_rna-.3'}),
cd('b-coral',1020,450,700,380,'c_meas+.4',{b:'c_rna-.3'}),tt('perturbed',1370,470,640,T1,'c_meas+.6',{b:'c_rna-.3'}),ic('animal-cell',1200,650,210,'c_meas+.7',{b:'c_rna-.3',bob:4,ph:1}),
br(1380,755,60,60,'#cf8a83','c_meas+1.0',{val:[0,1],vt:'c_meas+1.0',vd:.8,b:'c_rna-.3'}),br(1460,685,60,130,'#cf8a83','c_meas+1.2',{val:[0,1],vt:'c_meas+1.2',vd:.8,b:'c_rna-.3'}),br(1540,675,60,140,'#cf8a83','c_meas+1.4',{val:[0,1],vt:'c_meas+1.4',vd:.8,b:'c_rna-.3'}),br(1620,775,60,40,'#cf8a83','c_meas+1.6',{val:[0,1],vt:'c_meas+1.6',vd:.8,b:'c_rna-.3'}),
tt('↔',960,590,110,BIG(80),'c_ctrl-.2',{b:'c_rna-.3'}),ch('measure a response',480,880,'lav','c_meas+.2',{b:'c_rna-.3',fs:30}),ch('compare with a suitable control',1250,880,'amber','c_ctrl',{b:'c_rna-.3',fs:30}),
cd('',480,636,1040,8,'c_rna',{css:'background:#8aa59b;border-radius:4px',b:'c_job-.3',dy:0}),
'''+genes+dbars+'''
ch('↑ up',1620,520,'coral','c_rna+.6',{b:'c_job-.3',fs:28}),ch('↓ down',1620,700,'blue','c_rna+.9',{b:'c_job-.3',fs:28}),ch('target: a pattern of expression changes',1060,935,'mint','c_rna',{b:'c_job-.3',fs:32}),
cd('b-coral',100,470,520,330,'c_job-.2',{b:'c_control-.3'}),tt('intervention + cellular context',360,490,460,T2,'c_job',{b:'c_control-.3'}),ic('small-molecule',250,660,150,'c_job+.2',{b:'c_control-.3',bob:4}),tt('+',360,620,80,BIG(60),'c_job+.2',{b:'c_control-.3'}),ic('animal-cell',470,660,150,'c_job+.3',{b:'c_control-.3',bob:4,ph:1}),
ar(640,640,720,640,'g','c_job+.6',{b:'c_control-.3'}),
cd('b-lav',740,470,440,330,'c_job+.5',{b:'c_control-.3'}),tt('the model',960,490,400,T1,'c_job+.7',{b:'c_control-.3'}),ic('attention-network',960,660,200,'c_job+.8',{b:'c_control-.3',bob:4}),
ar(1200,640,1280,640,'g','c_job+1.3',{b:'c_control-.3'}),
cd('b-mint',1300,470,520,330,'c_job+1.2',{b:'c_control-.3'}),tt('the measured outcome',1560,490,460,T1,'c_job+1.4',{b:'c_control-.3'}),ic('expression-heatmap',1560,660,240,'c_job+1.5',{b:'c_control-.3',bob:4}),
dt([[640,640],[720,640]],'c','c_job+1',{n:2,speed:.5,r:9,b:'c_control-.3'}),dt([[1200,640],[1280,640]],'c','c_job+1.6',{n:2,speed:.5,r:9,b:'c_control-.3'}),
ic('animal-cell',460,660,230,'c_control',{bob:4}),ic('animal-cell',960,660,230,'c_control+.3',{bob:4,ph:1,css:'filter:hue-rotate(35deg)'}),ic('animal-cell',1460,660,230,'c_control+.6',{bob:4,ph:2,css:'filter:hue-rotate(-30deg)'}),
br(380,830,50,70,'#7f9fc9','c_vary-.4',{val:[0,1],vt:'c_vary-.4',vd:.6}),br(440,790,50,110,'#7f9fc9','c_vary-.3',{val:[0,1],vt:'c_vary-.3',vd:.6}),br(880,800,50,100,'#7f9fc9','c_vary-.2',{val:[0,1],vt:'c_vary-.2',vd:.6}),br(940,840,50,60,'#7f9fc9','c_vary-.1',{val:[0,1],vt:'c_vary-.1',vd:.6}),br(1380,850,50,50,'#7f9fc9','c_vary',{val:[0,1],vt:'c_vary',vd:.6}),br(1440,785,50,115,'#7f9fc9','c_vary+.1',{val:[0,1],vt:'c_vary+.1',vd:.6}),
ch('untreated cells still vary',960,945,'coral','c_vary',{fs:34}),ch('so the control is essential',960,440,'amber','c_control',{fs:36})
]};''')
# ---- virtual cell ----
mk('e1_vcell',2,'Define the research problem','What is a virtual-cell prediction?','Define the research problem · schematic illustrations · bars illustrative','''
const SPEC={notes:{x:60,y:226,w:1800,h:150,list:[
['c_one','One practical meaning','a <b>virtual cell model</b> today'],
['c_give','Input','we give the system information about <b>cells</b>, their <b>context</b> and a <b>change</b> we want to study'],
['c_pred','Output','it predicts some aspect of the <b>resulting cellular state</b> — often an <b>expression profile</b>'],
['c_phrase','A broader ambition','the phrase can describe much more — so <b>examine the actual input and output</b> of each model'],
['c_defined','A defined task','predicting a set of <b>RNA measurements</b> is a defined scientific task'],
['c_sim','A far larger goal','simulating <b>every process</b> in a living cell, continuously and correctly'],
['c_keep','Keep them separate','keeping those meanings apart makes the progress <b>easier to appreciate</b>']]},
els:[
cd('b-blue',80,470,520,330,'c_give-.2',{b:'c_defined-.3'}),tt('cells, context, a change',340,490,480,T2,'c_give',{b:'c_defined-.3'}),
ic('animal-cell',200,650,150,'c_give+.3',{b:'c_defined-.3',bob:4}),ic('small-molecule',470,650,150,'c_give+.8',{b:'c_defined-.3',bob:4,ph:1}),ch('context',200,740,'blue','c_give+1.0',{b:'c_defined-.3',fs:24}),ch('a change',470,740,'coral','c_give+1.6',{b:'c_defined-.3',fs:24}),
ar(620,640,700,640,'g','c_give+1.8',{b:'c_defined-.3'}),dt([[620,640],[700,640]],'c','c_give+2.2',{n:2,speed:.5,r:9,b:'c_defined-.3'}),
cd('b-lav',720,470,480,330,'c_one-.2',{b:'c_defined-.3'}),tt('virtual cell model',960,490,440,T1,'c_one+.1',{b:'c_defined-.3'}),ic('attention-network',960,650,210,'c_one+.3',{b:'c_defined-.3',bob:4}),
ar(1220,640,1300,640,'g','c_pred-.2',{b:'c_defined-.3'}),dt([[1220,640],[1300,640]],'c','c_pred+.4',{n:2,speed:.5,r:9,b:'c_defined-.3'}),
cd('b-mint',1320,470,520,330,'c_pred-.2',{b:'c_defined-.3'}),tt('the resulting cellular state',1580,490,480,T2,'c_pred+.1',{b:'c_defined-.3'}),ic('expression-heatmap',1580,650,250,'c_pred+.3',{b:'c_defined-.3',bob:4}),ch('often an expression profile',1580,745,'mint','c_pred+.8',{b:'c_defined-.3',fs:24}),
cd('',60,440,1800,430,'c_phrase',{css:'border:6px dashed #e0a43a;border-radius:36px;background:rgba(224,164,58,.06)',b:'c_defined-.3',dy:0}),
ch('“virtual cell” can describe a much broader ambition',960,900,'amber','c_phrase',{b:'c_actual-.3',fs:32}),ch('so: look at each model’s actual input and output',960,900,'mint','c_actual',{b:'c_defined-.3',fs:32}),
cd('b-mint',60,450,840,420,'c_defined-.1'),ic('expression-heatmap',230,650,220,'c_defined+.2',{bob:4}),tt('predict a set of RNA measurements',360,560,520,T1,'c_defined+.3',{c:false}),ch('✓  a defined scientific task',620,740,'mint','c_defined+.9',{fs:30}),
cd('b-coral',1020,450,840,420,'c_sim-.2'),ic('animal-cell',1150,660,250,'c_sim+.1',{bob:4}),rg(1150,660,'c','c_sim+.6',{every:1.0,dur:1.0,r0:60,r1:170}),rg(1150,660,'c','c_sim+1.0',{every:1.0,dur:1.0,r0:60,r1:170}),
dt([[1050,520],[1150,640],[1250,520]],'c','c_sim+.5',{n:3,speed:.45,r:9}),dt([[1050,800],[1150,690],[1250,800]],'a','c_sim+.8',{n:3,speed:.45,r:9}),
tt('simulate every process in a living cell, continuously and correctly',1290,540,540,T2,'c_sim+.3',{c:false}),ch('far more demanding',1560,780,'coral','c_sim+1.2',{fs:30}),
tt('≠',960,620,120,BIG(100),'c_keep-.3'),ch('keep those meanings separate',960,935,'amber','c_keep',{fs:34})
]};''')
