import sys
sys.path.insert(0,'/home/claude/work/scenes')
from mk import mk
from cuespec import build
BADGE=lambda n,title,fill:'''cd('b-mint',80,230,600,250,'c_start',{dy:20}),
tt('Part %d of 4',116,252,500,'font:600 30px/1 Inter;color:#26765d','c_start+.2',{c:false}),
tt(%r,116,296,540,'font:700 50px/1.1 Poppins;color:'+INK,'c_start+.35',{c:false}),
{t:'segs',x:116,y:430,w:120,a:'c_start+.5',fill:%d},
'''%(n,title,fill)

# ---------------- part 3 intro ----------------
mk('e1_part3',3,'How models learn','Part 3 · How models learn','How models learn · schematic overview · letters and bars illustrative','''
const E='c_hidden-.9';
const SPEC={els:[
'''+BADGE(3,'How models learn',3)+'''
tl('MKTAYIAKQR',760,250,70,'c_seq',{stag:.1,neutral:true,pal:'blue'}),
ic('folded-protein',1700,300,150,'c_seq+1.0',{bob:4}),
ch('our first hands-on model: a protein sequence',1160,350,'amber','c_seq+.7',{fs:30}),
// learning loop
cd('b-blue',80,520,380,260,'c_ex-.1',{b:E}),tt('examples',270,538,340,T2,'c_ex',{b:E}),ic('training-test-split',270,640,150,'c_ex+.2',{b:E,bob:4}),ch('known answers',270,715,'blue','c_ex+.5',{b:E,fs:24}),
ar(466,650,534,650,'g','c_ex+.9',{b:E}),
cd('b-lav',540,520,380,260,'c_pred-.1',{b:E}),tt('predictions',730,538,340,T2,'c_pred',{b:E}),ic('attention-network',730,640,150,'c_pred+.2',{b:E,bob:4,ph:1}),ch('the model’s guesses',730,715,'lav','c_pred+.5',{b:E,fs:24}),
ar(926,650,994,650,'g','c_pred+.9',{b:E}),
cd('b-coral',1000,520,380,260,'c_loss-.1',{b:E}),tt('a loss',1190,538,340,T2,'c_loss',{b:E}),
br(1120,600,60,100,'#4d8f7e','c_loss+.2',{val:[0,1],vt:'c_loss+.2',vd:.7,b:E}),br(1210,645,60,55,'#cf8a83','c_loss+.5',{val:[0,1],vt:'c_loss+.5',vd:.7,b:E}),ch('how far off?',1190,715,'coral','c_loss+.8',{b:E,fs:24}),
ar(1386,650,1454,650,'g','c_loss+1.0',{b:E}),
cd('b-mint',1460,520,380,260,'c_upd-.1',{b:E}),tt('parameter update',1650,538,340,T2,'c_upd',{b:E}),ic('conformational-switch',1650,640,150,'c_upd+.2',{b:E,bob:4,ph:2}),ch('nudge the parameters',1650,715,'mint','c_upd+.5',{b:E,fs:24}),
dt([[466,650],[534,650]],'c','c_ex+1.1',{n:2,speed:.5,r:9,b:E}),dt([[926,650],[994,650]],'c','c_pred+1.1',{n:2,speed:.5,r:9,b:E}),dt([[1386,650],[1454,650]],'c','c_loss+1.2',{n:2,speed:.5,r:9,b:E}),
ar(0,0,0,0,'a','c_fit-.6',{d:'M1650 786 L1650 850 L270 850 L270 790',dur:1.4,b:E}),
dt([[1650,786],[1650,850],[270,850],[270,790]],'a','c_fit',{n:3,speed:.3,r:9,b:E}),
ch('repeat, again and again',960,825,'amber','c_fit',{b:E,fs:30}),
// hidden amino acid + representations
cd('b-blue',80,520,900,300,'c_hidden-.6'),tt('hidden amino acid exercise',530,540,860,T2,'c_hidden-.45'),
tl('MKTAY?AKQR',120,620,70,'c_hidden',{stag:.08,neutral:true,pal:'blue',hot:[5],ht:'c_hidden+.9'}),
ch('can the model guess the hidden one?',530,740,'amber','c_hidden+1.3',{fs:28}),
ar(990,670,1090,670,'g','c_rep-.5'),dt([[990,670],[1090,670]],'c','c_rep-.2',{n:2,speed:.5,r:9}),
cd('b-lav',1100,520,740,300,'c_rep-.3'),tt('the model’s representations',1470,540,680,T2,'c_rep'),ic('sequence-embedding',1470,655,210,'c_rep+.3',{bob:4}),ch('what it builds inside',1470,740,'lav','c_rep+.8',{fs:28})
]};''')
print(build('e1_part3',1,'part-3-intro',dict(c_start="Let's begin",c_seq='hands-on',c_ex='examples',c_pred='predictions',c_loss='a loss',c_upd='parameter updates',c_fit='fit together',c_then='Then we will',c_hidden='hidden amino',c_rep='representations')))

# ---------------- part 4 intro ----------------
mk('e1_part4',4,'The real ESM-2 experiment','Part 4 · The real ESM-2 experiment','The real ESM-2 experiment · schematic overview · letters and bars illustrative · window 767–827 from the notebook','''
const SPEC={els:[
'''+BADGE(4,'The real ESM-2 experiment',4)+'''
cd('b-lav',720,230,420,250,'c_use-.1'),tt('saved ESM-2 model',930,248,380,T2,'c_use+.1'),ic('attention-network',930,335,130,'c_esm',{bob:4}),ch('a small saved checkpoint',930,415,'lav','c_esm+.6',{fs:24}),
cd('b-blue',1180,230,660,250,'c_egfr-.4'),tt('checked EGFR sequence window',1510,248,600,T2,'c_egfr-.2'),tl('LGAEEKEYH',1226,330,56,'c_egfr',{stag:.08,neutral:true,pal:'blue'}),ch('61 amino acids · positions 767–827',1510,415,'blue','c_egfr+1.0',{fs:24}),
// four steps
cd('b-blue',80,520,380,260,'c_input-.2'),tt('the input',270,538,340,T2,'c_input'),tl('LGAEEK',96,625,50,'c_input+.2',{stag:.07,neutral:true,pal:'blue'}),ch('the sequence window',270,715,'blue','c_input+.7',{fs:24}),
ar(466,650,534,650,'g','c_hidden-.6'),dt([[466,650],[534,650]],'c','c_hidden-.2',{n:2,speed:.5,r:9}),
cd('b-amber',540,520,380,260,'c_hidden-.3'),tt('the hidden position',730,538,340,T2,'c_hidden'),tl('LGA?EK',556,625,50,'c_hidden+.2',{stag:.07,neutral:true,pal:'blue',hot:[3],ht:'c_hidden+.9'}),ch('hide one letter',730,715,'amber','c_hidden+.9',{fs:24}),
ar(926,650,994,650,'g','c_prob-.6'),dt([[926,650],[994,650]],'c','c_prob-.2',{n:2,speed:.5,r:9}),
cd('b-lav',1000,520,380,260,'c_prob-.3'),tt('the probabilities',1190,538,340,T2,'c_prob'),
br(1047,660,36,40,'#8b75b0','c_prob+.2',{val:[0,1],vt:'c_prob+.2',vd:.6}),br(1097,605,36,95,'#8b75b0','c_prob+.3',{val:[0,1],vt:'c_prob+.3',vd:.6}),br(1147,670,36,30,'#8b75b0','c_prob+.4',{val:[0,1],vt:'c_prob+.4',vd:.6}),br(1197,630,36,70,'#8b75b0','c_prob+.5',{val:[0,1],vt:'c_prob+.5',vd:.6}),br(1247,680,36,20,'#8b75b0','c_prob+.6',{val:[0,1],vt:'c_prob+.6',vd:.6}),br(1297,645,36,55,'#8b75b0','c_prob+.7',{val:[0,1],vt:'c_prob+.7',vd:.6}),
ar(1386,650,1454,650,'g','c_score-.6'),dt([[1386,650],[1454,650]],'c','c_score-.2',{n:2,speed:.5,r:9}),
cd('b-mint',1460,520,380,260,'c_score-.3'),tt('a comparison score',1650,538,340,T2,'c_score'),
br(1590,600,60,100,'#4d8f7e','c_score+.2',{val:[0,1],vt:'c_score+.2',vd:.7}),br(1680,645,60,55,'#cf8a83','c_score+.5',{val:[0,1],vt:'c_score+.5',vd:.7}),ch('one score',1650,715,'mint','c_score+.9',{fs:24}),
// the question
cd('b-amber',80,808,1760,160,'c_keep-.1'),tt('Keep our question precise',116,822,700,'font:600 28px/1 Inter;color:#9a6a12','c_keep',{c:false}),
tt('What does this sequence model prefer in this context, and what further evidence would biology require?',960,866,1680,'font:700 36px/1.3 Poppins;color:'+INK,'c_q'),
rg(960,890,'a','c_q+.2',{n:1,r0:60,r1:120,sw:6})
]};''')
print(build('e1_part4',1,'part-4-intro',dict(c_start='Now for part four',c_use='We will use',c_esm='ESM',c_egfr='EGFR',c_input='the input',c_hidden='hidden position',c_prob='probabilities',c_score='comparison score',c_keep='Keep our question',c_q='What does this')))
