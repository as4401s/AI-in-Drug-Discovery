import sys,json
sys.path.insert(0,'/home/claude/work/lib')
from cues import Lesson
L=Lesson(1)
def T(s,p,o=1): return L.t(s,p,o)
# ---------------- Stack
s='stack'
full=[0,0,1273,1280]
t_ctx=T(s,'The January 2026 pre-print');t_learn=T(s,'It learns representations');t_ex=T(s,'and can use example cells');t_gen=T(s,'when generating predicted')
t_int=T(s,'The useful intuition');t_less=T(s,'In this lesson');t_not=T(s,'We are not running')
C={'img':'../../data/fig/stack_x2.png','iw':2546,'ih':2560,'ox':0,'oy':0,'k':2,'full':full,'cardH':118,'mmDy':44,
 'caption':'Figure 1 from the Stack preprint · publisher figure, enlarged · panels A–C used here',
 'cam':[{'t':0,'r':full},
  {'t':t_ctx-.1,'r':[60,395,720,690],'hl':[100,430,385,548]},
  {'t':t_learn-.1,'r':[0,0,640,330],'hl':[10,38,340,155]},
  {'t':t_ex-.1,'r':[90,675,440,890],'hl':[112,705,395,868]},
  {'t':t_gen-.1,'r':[980,675,1273,880],'hl':[1070,678,1250,830]},
  {'t':t_int-.1,'r':[60,395,1000,690]},
  {'t':t_less-.1,'r':full}],
 'steps':[
  {'t0':t_ctx-.1,'t1':t_learn-.1,'title':'Cells read in context','body':'A cell is read together with the other cells in its set.','cls':'b-blue'},
  {'t0':t_learn-.1,'t1':t_ex-.1,'title':'Learns from big collections','body':'Large single-cell collections (about 149 million cells in the paper).','cls':'b-lav'},
  {'t0':t_ex-.1,'t1':t_int-.1,'title':'Example cells as context','body':'Example cells (a prompt) steer the predicted expression profiles.','cls':'b-mint'},
  {'t0':t_int-.1,'t1':t_less-.1,'title':'Why context helps','body':'A cell is easier to read when we know its neighbours in the sample.','cls':'b-amber'}],
 'notes':[{'t0':.4,'t1':t_ctx-.3,'text':'Paper example 1 · Stack · Arc Institute and collaborators · January 2026 preprint','cls':'b-blue'},
  {'t0':t_less,'t1':t_not-.3,'text':'In this lesson we explain the paper’s approach.','cls':'b-lav'},
  {'t0':t_not-.1,'text':'We did not run Stack or reproduce its reported benchmarks.','cls':'b-amber'}],
 'panelFadeAt':None}
json.dump(C,open('/home/claude/work/scenes/e1_stack/cues.json','w'));print('stack',t_ctx,t_learn,t_ex,t_gen,t_int,t_less,t_not)
# ---------------- X-Cell
s='xcell'
full=[130,120,1060,910]
t_gen=T(s,'emphasizes predicting');t_dif=T(s,'diffusion language model');t_pri=T(s,'It also uses several');t_ref=T(s,'Think of an initial prediction');t_int=T(s,'That is only an intuition');t_q=T(s,'The important scientific question')
C={'img':'../../data/fig/xcell_x25.png','iw':2475,'ih':2075,'ox':100,'oy':100,'k':2.5,'full':full,'cardH':118,'mmDy':44,
 'caption':'Figure 1 from the X-Cell preprint (page 4 render) · enlarged · panels A–C used here',
 'cam':[{'t':0,'r':full},
  {'t':t_gen-.1,'r':[150,132,700,322],'hl':[158,140,690,318]},
  {'t':t_dif-.2,'r':[370,392,610,652],'hl':[375,398,605,648]},
  {'t':t_pri-.1,'r':[280,420,440,620],'hl':[285,425,435,615]},
  {'t':t_ref-.1,'r':[150,695,595,865],'hl':[158,700,590,860]},
  {'t':t_q-.1,'r':full}],
 'steps':[
  {'t0':t_gen-.1,'t1':t_dif-.2,'title':'Genetic perturbations','body':'CRISPRi screens: genes switched down, cell response measured.','cls':'b-blue'},
  {'t0':t_dif-.2,'t1':t_pri-.1,'title':'Diffusion-style refinement','body':'A predicted move from control toward a perturbed state is refined repeatedly.','cls':'b-lav'},
  {'t0':t_pri-.1,'t1':t_ref-.1,'title':'Biological prior knowledge','body':'Several sources feed in, e.g. ESM-2, STRING, DepMap, scGPT.','cls':'b-mint'},
  {'t0':t_ref-.1,'t1':t_q-.1,'title':'Successive refinement','body':'Each step re-masks part of the output and predicts again (t = 0 → 0.5 → 1).','cls':'b-amber'}],
 'notes':[{'t0':.4,'t1':t_gen-.3,'text':'Paper example 2 · X-Cell · author manuscript (2026)','cls':'b-blue'},
  {'t0':t_int,'t1':t_q-.3,'text':'An intuition for the architecture, not a movie of molecules.','cls':'b-amber'},
  {'t0':t_q,'text':'Key question: do predicted changes match independent measurements?','cls':'b-lav'}]}
json.dump(C,open('/home/claude/work/scenes/e1_xcell/cues.json','w'));print('xcell',t_gen,t_dif,t_pri,t_ref,t_int,t_q)

# ---------------- ESM paper
s='esm-paper'
full=[0,0,1280,1139]
t_show=T(s,'The author showed');t_fold=T(s,'ESM fold system adds');t_dist=T(s,'That distinction matters');t_ours=T(s,'Our small ESM 2 run');t_not=T(s,'It will not produce')
t_some=T(s,'Some contact prediction methods');t_keep=T(s,'We will keep the actual output');t_done=T(s,'That completes part three');t_task=T(s,'We know the training task')
t_loss=T(s,'the loss');t_diff=T(s,'the difference between');t_p4=T(s,'In part four')
C={'img':'../../data/fig/esm_x2.png','iw':2560,'ih':2278,'ox':0,'oy':0,'k':2,'full':full,'cardH':118,'mmDy':44,
 'caption':'Figure 1 from Lin et al., ESM-2 / ESMFold · publisher figure, enlarged · panels A and F used here',
 'cam':[{'t':0,'r':full},
  {'t':t_show-.1,'r':[0,0,440,350],'hl':[110,20,430,335]},
  {'t':t_fold-.2,'r':[0,665,1280,1139],'hl':[10,675,1275,1135],'hlt':1.2},
  {'t':t_dist+.5,'r':full},
  {'t':t_some-.2,'r':[0,0,440,350],'hl':[110,20,430,335]}],
 'steps':[
  {'t0':t_show-.1,'t1':t_fold-.2,'title':'Representations carry structure','body':'Representations hold information useful for structure.','cls':'b-blue'},
  {'t0':t_fold-.2,'t1':t_dist+.5,'title':'ESMFold adds a component','body':'The ESMFold system adds a structure-prediction part.','cls':'b-lav'}],
 'notes':[{'t0':.4,'t1':t_show-.3,'text':'Published example · ESM-2 and ESMFold · Lin et al.','cls':'b-blue'}],
 'panelFadeAt':t_dist+.6,'mmFadeAt':t_dist+.6,'vpFadeAt':t_keep-.3,
 'cues':{'c_dist':t_dist,'c_ours':t_ours,'c_not':t_not,'c_some':t_some,'c_keep':t_keep,'c_done':t_done,'c_task':t_task,'c_loss':t_loss,'c_diff':t_diff,'c_p4':t_p4}}
json.dump(C,open('/home/claude/work/scenes/e1_esm_paper/cues.json','w'));print('esm',C['cues'])
