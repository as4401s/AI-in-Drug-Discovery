import numpy as np, tifffile, json
from scipy import ndimage as ndi
st=tifffile.imread('src/2/data/cells3d-with-metadata.tif'); nuc=st[:,0]
img=nuc[30]; S8=np.ones((3,3))
def comps(im,T):
    lab,n=ndi.label(im>T,structure=S8); ar=ndi.sum(np.ones_like(lab),lab,range(1,n+1)).astype(int)
    edge=set(np.unique(np.concatenate([lab[0],lab[-1],lab[:,0],lab[:,-1]])))-{0}
    stt=[0]+[(1 if ar[i-1]<100 else (2 if i in edge else 0)) for i in range(1,n+1)]
    return lab,n,[0]+ar.tolist(),stt
lab,n,ar,stt=comps(img,10432)
mip=nuc.max(0); labm,nm,arm,sttm=comps(mip,14226)
am=nuc.argmax(0)
# histogram / otsu
hist=np.bincount(img.ravel(),minlength=65536).astype(float); cum=np.cumsum(hist); cumm=np.cumsum(hist*np.arange(65536)); tot=cum[-1]
with np.errstate(divide='ignore',invalid='ignore'):
    between=np.nan_to_num(cum*(tot-cum)*(cumm/cum-(cumm[-1]-cumm)/(tot-cum))**2)
BW=250;NB=128
hb=[int(hist[i*BW:(i+1)*BW].sum()) for i in range(NB)]
ot=[float(between[i*BW]) for i in range(NB+1)]; mx=max(ot); ot=[v/mx for v in ot]
lo,hi=[float(v) for v in np.percentile(img,[1,99.5])]
mlo,mhi=[float(v) for v in np.percentile(mip,[1,99.5])]
D=dict(P=img.ravel().tolist(),LAB=lab.ravel().tolist(),ST=stt,AR=ar,NL=n,
  MIP=mip.ravel().tolist(),LABM=labm.ravel().tolist(),STM=sttm,ARM=arm,NM=nm,AM=am.ravel().tolist(),
  HB=hb,BW=BW,OT=ot,HIGH=int((img>=NB*BW).sum()),LO=lo,HI=hi,MLO=mlo,MHI=mhi,T=10432,
  CROP=[[int(v) for v in r] for r in img[24:30,80:86]],
  PROF={'A':[int(v) for v in nuc[:,143,28]]},
  STACKMAX=int(nuc.max()))
# per-region mean (retained) for scene 32
D['MEAN11']=float(img[lab==11].mean())
open('assets2/data2.js','w').write('window.D='+json.dumps(D,separators=(',',':'))+';')

import csv
rows=list(csv.DictReader(open('src/2/code/outputs/nuclear_region_measurements.csv')))
D['CSV']=[dict(label=int(r['label']),area_px=int(r['area_px']),edge=r['touches_edge']=='True',cy=float(r['centroid_y_px']),cx=float(r['centroid_x_px']),area_um2=float(r['area_um2']),mean=float(r['mean_raw_intensity_au'])) for r in rows]
m=lab==30; ys,xs=np.where(m); holes=ndi.binary_fill_holes(m)&~m
D['HOLE']=dict(label=30,y0=int(ys.min()),y1=int(ys.max()),x0=int(xs.min()),x1=int(xs.max()),holes=int(holes.sum()),area=int(m.sum()),HM=holes.ravel().astype(int).tolist())
bl=[i for i in range(1,n+1) if stt[i]==2]; bi=max(bl,key=lambda i:ar[i]); mb=lab==bi; ys,xs=np.where(mb)
D['BORDER']=dict(label=bi,y0=int(ys.min()),y1=int(ys.max()),x0=int(xs.min()),x1=int(xs.max()),area=ar[bi])
open('assets2/data2.js','w').write('window.D='+json.dumps(D,separators=(',',':'))+';')
print('border',D['BORDER'],'hole',{k:v for k,v in D['HOLE'].items() if k!='HM'})

print('ok',len(json.dumps(D))//1024,'KB','NL',n,'NM',nm,'bins max',max(hb))
