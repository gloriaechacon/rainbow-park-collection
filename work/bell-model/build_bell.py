"""Bell 3D presentation asset, reconstructed from client's architectural sheet.
Feet/inches dimensions are converted to metres. Proposed finishes and furniture.
No construction geometry is certified by this presentation model.
"""
import json, struct, math, io, base64, shutil
from pathlib import Path
from collections import defaultdict
import numpy as np
from PIL import Image
ROOT=Path('work/sites/r15-ocala/dist'); OUT=ROOT/'bell'; OUT.mkdir(exist_ok=True)
FT=.3048; W=50.; D=29+4/12; CENTER_V=(D+5)/2; H=8+4/12
# Reuse the approved site's PBR textures rather than invent architectural finish facts.
old=(ROOT/'utah/utah-propuesta-v2.glb').read_bytes(); nn=struct.unpack_from('<I',old,12)[0]; og=json.loads(old[20:20+nn]); ob=old[28+nn:]
buf=bytearray(); g={'asset':{'version':'2.0','generator':'Rainbow Park Collection / Bell architectural reconstruction 2026-10-13'},'scene':0,'scenes':[{'nodes':[]}],'nodes':[],'meshes':[],'materials':[],'buffers':[{}],'bufferViews':[],'accessors':[],'images':[],'textures':[],'samplers':[{'magFilter':9729,'minFilter':9987,'wrapS':10497,'wrapT':10497}]}
def append(b,target=None):
 while len(buf)%4:buf.append(0)
 v={'buffer':0,'byteOffset':len(buf),'byteLength':len(b)}
 if target:v['target']=target
 g['bufferViews'].append(v);buf.extend(b);return len(g['bufferViews'])-1
texmap={}
def copytex(idx):
 if idx in texmap:return texmap[idx]
 im=og['images'][og['textures'][idx]['source']]; bv=og['bufferViews'][im['bufferView']]; data=ob[bv.get('byteOffset',0):bv.get('byteOffset',0)+bv['byteLength']]
 g['images'].append({'bufferView':append(data),'mimeType':im['mimeType']});g['textures'].append({'source':len(g['images'])-1,'sampler':0});texmap[idx]=len(g['textures'])-1;return texmap[idx]
def linear(hex):
 c=[int(hex[i:i+2],16)/255 for i in (1,3,5)];return [v/12.92 if v<=.04045 else ((v+.055)/1.055)**2.4 for v in c]
def material(name,hex='#ffffff',rough=.7,metal=0,alpha=1,match=None):
 m={'name':name,'doubleSided':True,'pbrMetallicRoughness':{'baseColorFactor':linear(hex)+[alpha],'metallicFactor':metal,'roughnessFactor':rough}}
 if match:
  source=next(x for x in og['materials'] if match(x)); p=source['pbrMetallicRoughness']
  for k in ['baseColorTexture','metallicRoughnessTexture']:
   if k in p:m['pbrMetallicRoughness'][k]={'index':copytex(p[k]['index'])}
  if 'normalTexture'in source:m['normalTexture']={**source['normalTexture'],'index':copytex(source['normalTexture']['index'])}
 if alpha<1:m['alphaMode']='BLEND'
 g['materials'].append(m);return len(g['materials'])-1
stucco=material('Bell / Estuco marfil · acabado propuesto',match=lambda m:m['name']=='Muros sin asignación')
roofmat=material('Bell / Teja asfáltica antracita · acabado propuesto',match=lambda m:'Roofing'in m['name'])
wood=material('Bell / Roble natural · acabado propuesto',match=lambda m:m['name']=='Propuesta #ae9473')
stone=material('Bell / Porcelánico cálido · acabado propuesto',match=lambda m:m['name']=='Propuesta #eee9db')
linen=material('Bell / Tapicería lino · mobiliario ilustrativo',match=lambda m:m['name']=='Propuesta #e8dfcb')
trim=material('Bell / Molduras y carpintería marfil','#e9e5d9',.55)
interior=material('Bell / Paredes interiores','#f5f1e8',.87)
frame=material('Bell / Aluminio bronce oscuro','#3a403b',.29,.58)
glass=material('Bell / Vidrio','#b9d2d7',.08,.15,.23)
concrete=material('Bell / Hormigón exterior','#b6b4aa',.97)
white=material('Bell / Porcelana sanitaria','#f7f6ee',.25)
quartz=material('Bell / Cuarzo cocina','#e6e3d9',.27)
black=material('Bell / Electrodomésticos','#242c2a',.24,.4)
steel=material('Bell / Acero cepillado','#969d9b',.27,.85)
fabricgreen=material('Bell / Textil verde salvia','#7e8874',.93)
terracotta=material('Bell / Acento cerámica','#b47b55',.8)
soil=material('Bell / Tierra','#4b3828',1)
leaf=material('Bell / Vegetación ornamental propuesta','#3e583b',.85)
leaf2=material('Bell / Hoja verde claro','#65764e',.89)
light=material('Bell / Vidrio luminaria','#f4e8c9',.3)
mat_scale={stucco:1.3,roofmat:2.1,wood:.85,stone:2.4,linen:.45}
# All coordinates below are feet: x from left, v from rear to street, h above finished floor.
groups={}; group_extras={}
def add(name,verts,faces,mat,extras=None):
 verts=np.array(verts,float); verts[:,0]=(verts[:,0]-W/2)*FT;verts[:,1]*=FT;verts[:,2]=(verts[:,2]-CENTER_V)*FT
 tri=verts[np.array(faces)].reshape(-1,3,3);nr=np.cross(tri[:,1]-tri[:,0],tri[:,2]-tri[:,0]);ln=np.linalg.norm(nr,axis=1);good=ln>1e-9;tri=tri[good];nr=nr[good]/ln[good,None];pos=tri.reshape(-1,3);nr=np.repeat(nr,3,axis=0)
 axis=np.argmax(abs(nr),axis=1);uv=np.c_[np.where(axis==0,pos[:,2],pos[:,0]),np.where(axis==1,pos[:,2],pos[:,1])]/mat_scale.get(mat,1)
 groups.setdefault(name,defaultdict(lambda:[[],[],[]])); a=groups[name][mat];a[0].extend(pos);a[1].extend(nr);a[2].extend(uv)
 if extras:group_extras[name]=extras
corn=np.array([[-1,-1,-1],[1,-1,-1],[1,1,-1],[-1,1,-1],[-1,-1,1],[1,-1,1],[1,1,1],[-1,1,1]],float)/2
faces=[[0,2,1],[0,3,2],[4,5,6],[4,6,7],[0,1,5],[0,5,4],[3,7,6],[3,6,2],[0,4,7],[0,7,3],[1,2,6],[1,6,5]]
def box(name,x,v,h,w,d,t,mat,rotate=0,extras=None):
 a=corn*np.array([w,t,d]);r=math.radians(rotate);a[:,[0,2]]=a[:,[0,2]]@np.array([[math.cos(r),math.sin(r)],[-math.sin(r),math.cos(r)]]).T;a+=np.array([x,h,v]);add(name,a,faces,mat,extras)
def cylinder(name,x,v,h,r,height,mat,n=24,rx=None,rz=None):
 vs=[]
 for y in [h-height/2,h+height/2]:
  for i in range(n):a=i*math.tau/n;vs.append([x+(rx or r)*math.cos(a),y,v+(rz or r)*math.sin(a)])
 vs.extend([[x,h-height/2,v],[x,h+height/2,v]]);fs=[]
 for i in range(n):j=(i+1)%n;fs.extend([[i,j,n+j],[i,n+j,n+i],[2*n,j,i],[2*n+1,n+i,n+j]])
 add(name,vs,fs,mat)
def ellipsoid(name,x,v,h,rx,rz,ry,mat):
 vs=[];fs=[];n=20;m=12
 for j in range(m+1):
  a=j*math.pi/m
  for i in range(n+1):b=i*math.tau/n;vs.append([x+rx*math.sin(a)*math.cos(b),h+ry*math.cos(a),v+rz*math.sin(a)*math.sin(b)])
 for j in range(m):
  for i in range(n):a=j*(n+1)+i;fs.extend([[a,a+n+1,a+1],[a+1,a+n+1,a+n+2]])
 add(name,vs,fs,mat)
# Wall builder makes real openings rather than painting doors/windows on solid walls.
wall_plan=[]
def wall(name,axis,center,a,b,thick=.333,height=H,mat=interior,opens=()):
 # each opening: (a, b, sill, head)
 pieces=sorted([a,b]+[max(a,min(b,k)) for o in opens for k in o[:2]])
 for l,r in zip(pieces[:-1],pieces[1:]):
  if r-l<.01:continue
  hit=next((o for o in opens if o[0]-.001<(l+r)/2<o[1]+.001),None)
  ranges=[(0,height)] if hit is None else [(0,hit[2]),(hit[3],height)]
  for lo,hi in ranges:
   if hi-lo<.01:continue
   if axis=='x':box(name,(l+r)/2,center,(hi+lo)/2,r-l,thick,hi-lo,mat)
   else:box(name,center,(l+r)/2,(hi+lo)/2,thick,r-l,hi-lo,mat)
 wall_plan.append({'axis':axis,'center':center,'a':a,'b':b,'thickness':thick,'openings':list(opens)})
# Source sheet: 50' x 29'4" rectangle; entry 13'6" x 5'. Finished floor datum = 0.
box('00 Losa principal',25,D/2,-.22,50,D,.44,concrete,extras={'kind':'slab','areaSource':'Main envelope; see schedule for official areas'})
box('01 Porche de entrada',19.9167,D+2.5,-.18,13.5,5,.36,stone,extras={'kind':'slab'})
box('02 Patio posterior 10 × 8 pies',19.5,-4,-.24,10,8,.20,concrete,extras={'kind':'patio','unroofed':True})
box('03 Piso interior',18.833,D/2,.016,37.333,D-.6,.032,stone,extras={'kind':'floor'})
box('04 Piso garaje',43.6667,D/2,.009,11.6667,D-.667,.018,concrete,extras={'kind':'floor'})
front_open=[(4.67,7.67,2.167,7.167),(14.5,17.5,2.167,7.167),(21.6667,24.8333,0,7.167),(30.333,33.333,2.167,7.167),(38.667,48.667,0,7)]
rear_open=[(4.83,7.83,2.167,7.167),(17,23.333,0,7.167),(29.917,33.083,4.167,7.167)]
wall('10 Fachada delantera','x',D-.333,0,50,.667,H,stucco,front_open)
wall('11 Fachada posterior','x',.333,0,50,.667,H,stucco,rear_open)
wall('12 Fachada izquierda','v',.333,.667,D-.667,.667,H,stucco)
wall('13 Fachada derecha','v',49.667,.667,D-.667,.667,H,stucco)
# Actual interior wall structure, read from the client's dimensioned floor plan.
wall('20 Dormitorios secundarios · divisor','v',12.333,.667,D-.667,.333,H,interior,[(9.5,12.5,0,7)])
wall('21 Dormitorio 2 · pared sur','x',10.833,.667,12.167,.333,H,interior,[(9.167,12.0,0,7)])
wall('22 Closet dormitorio 2','v',14.5,.667,9.333,.333,H,interior)
wall('22 Closet dormitorio 2','x',9.333,12.5,14.5,.333,H,interior)
# Thin bi-fold openings on closet-facing wall, within bedroom 2.
# A closet is open to bedroom through central portion; dividing wall on that span removed below in mesh creation.
# Bath 2/hall, linen and bedroom 3 closet.
wall('23 Baño secundario · sur','x',16.1667,.667,8.5,.333,H,interior)
wall('23 Baño secundario · acceso','v',8.5,11,16.333,.333,H,interior,[(13.5,16.0,0,7)])
wall('24 Dormitorio 3 · norte','x',18.333,.667,12.167,.333,H,interior,[(1,7.5,0,7),(9.167,12,0,7)])
wall('24 Closet dormitorio 3','x',16.5,.667,8.333,.333,H,interior)
wall('24 Closet dormitorio 3','v',8.333,16.5,18.333,.333,H,interior)
# Main suite and kitchen block.
wall('25 Suite principal · oeste','v',25.667,7.667,D-.667,.333,H,interior,[(17.333,20.333,0,7)])
wall('26 Vestidor · norte','x',9.667,25.833,31.833,.333,H,interior)
wall('26 Vestidor · este','v',31.833,7.667,16.667,.333,H,interior)
wall('27 Suite principal · baños y vestidor','x',16.667,25.667,37.667,.333,H,interior,[(26.083,28.75,0,7),(34.667,37.333,0,7)])
wall('28 Baño principal · norte','x',7.667,31.833,37.667,.333,H,interior)
wall('29 Garaje · separación interior','v',37.667,.667,D-.667,.4,H,interior,[(3.167,6.167,0,7)])
wall('30 Lavandería · sur','x',7.833,37.667,44.5,.333,H,interior,[(41.167,44.167,0,7)])
wall('30 Lavandería · este','v',44.5,.667,7.833,.333,H,interior)
# Correct the bedroom 2 closet opening on the divider in geometry by rebuilding that group.
del groups['20 Dormitorios secundarios · divisor']
wall('20 Dormitorios secundarios · divisor','v',12.333,.667,D-.667,.333,H,interior,[(2.75,6.75,0,7),(9.5,12.5,0,7)])
# Baseboards highlight depth and finish at each continuous floor-level segment.
for seg in wall_plan:
 a,b=seg['a'],seg['b'];cuts=sorted([a,b]+[max(a,min(b,k)) for o in seg['openings'] if o[2]<.1 for k in o[:2]])
 for l,r in zip(cuts[:-1],cuts[1:]):
  if r-l<.01 or any(o[2]<.1 and o[0]<=(l+r)/2<=o[1] for o in seg['openings']):continue
  # Only interior wall faces; exterior base has a thin continuous plinth.
  if seg['thickness']>.5:continue
  for side in [-1,1]:
   c=seg['center']+side*(seg['thickness']/2+.02)
   if seg['axis']=='x':box('31 Rodapiés',(l+r)/2,c,.18,r-l,.045,.36,trim)
   else:box('31 Rodapiés',c,(l+r)/2,.18,.045,r-l,.36,trim)
# Real glazing, reveal trims and tracks.
def window(x,v,width,height=5,sill=2.167,side=1):
 name='40 Ventanas y marcos'; center=sill+height/2
 for xx in [x-width/2,x+width/2]:box(name,xx,v,center,.10,.17,height+.1,frame)
 for yy in [sill,sill+height]:box(name,x,v,yy,width+.1,.17,.10,frame)
 box(name,x,v,center,width-.12,.06,.07,frame)
 box('41 Vidrios',x,v,center,width-.15,.022,height-.15,glass)
 box('42 Alféizares',x,v+side*.14,sill-.09,width+.25,.39,.12,trim)
 # slim exterior trim flush with stucco, distinct from sash
 for xx in [x-width/2-.075,x+width/2+.075]:box('43 Recercados',xx,v+side*.07,center,.09,.09,height+.22,trim)
 box('43 Recercados',x,v+side*.07,sill+height+.08,width+.24,.09,.09,trim)
for a,b,s,h in front_open[:2]+front_open[3:4]:window((a+b)/2,D+.015,b-a,h-s,s)
for a,b,s,h in [rear_open[0],rear_open[2]]:window((a+b)/2,-.015,b-a,h-s,s,-1)
# Sliding rear patio opening.
a,b,s,h=rear_open[1]
for xx in [a,b,(a+b)/2]:box('44 Puerta corrediza posterior',xx,0,h/2,.11,.18,h,frame)
for y in [.07,h-.03]:box('44 Puerta corrediza posterior',(a+b)/2,0,y,b-a,.18,.10,frame)
box('41 Vidrios',(a+b)/2,-.015,h/2,b-a-.15,.02,h-.15,glass)
box('44 Puerta corrediza posterior',(a+b)/2+.14,-.12,3.3,.08,.11,.70,frame)
# Front paneled entry door, closed; interior doors are shown open so the plan reads clearly.
def framed_door(name,x,v,width=3,height=7,axis='x',angle=0,exterior=False):
 mat=wood if exterior else trim
 if axis=='x':
  for xx in [x-width/2-.065,x+width/2+.065]:box(name,xx,v,height/2,.13,.24,height+.08,trim)
  box(name,x,v,height+.05,width+.25,.24,.13,trim)
  xx=x-width/2+width/2*math.cos(math.radians(angle));vv=v+width/2*math.sin(math.radians(angle))
 else:
  for zz in [v-width/2-.065,v+width/2+.065]:box(name,x,zz,height/2,.24,.13,height+.08,trim)
  box(name,x,v,height+.05,.24,width+.25,.13,trim)
  angle+=90;xx=x+width/2*math.sin(math.radians(angle-90));vv=v-width/2+width/2*math.cos(math.radians(angle-90))
 box(name,xx,vv,height/2,width,.11,height-.06,mat,angle)
 if angle==0:
  for yy in [1.4,3.6,5.8]:
   for dx in [-width*.235,width*.235]:box(name,xx+dx,vv+.075,yy,width*.34,.045,1.6,mat)
  cylinder(name,xx+width*.37,vv+.19,3.25,.08,.15,frame,12)
framed_door('45 Acceso principal',23.25,D+.015,3.167,7.167,exterior=True)
for name,x,v,w,axis,angle in [('46 Puertas interiores',10.583,10.833,2.833,'x',-70),('46 Puertas interiores',12.333,11,3,'v',70),('46 Puertas interiores',10.583,18.333,2.833,'x',70),('46 Puertas interiores',8.5,14.75,2.5,'v',60),('46 Puertas interiores',25.667,18.833,3,'v',-65),('46 Puertas interiores',27.417,16.667,2.667,'x',-55),('46 Puertas interiores',36,16.667,2.667,'x',-60),('46 Puertas interiores',37.667,4.667,3,'v',70),('46 Puertas interiores',42.667,7.833,3,'x',-70)]:framed_door(name,x,v,w,7,axis,angle)
# Garage: five raised panels by four rows, clearly recessed from the opening.
box('47 Puerta garaje',43.667,D-.12,3.5,9.95,.15,6.98,trim)
for row in range(4):
 for col in range(5):
  xx=38.667+(col+.5)*2;yy=(row+.5)*1.75
  box('47 Puerta garaje',xx,D-.015,yy,1.79,.10,1.48,trim)
  box('47 Puerta garaje',xx,D+.04,yy,1.51,.045,1.20,stucco)
for xx in [38.53,48.80]:box('47 Puerta garaje',xx,D+.04,3.52,.20,.24,7.14,trim)
box('47 Puerta garaje',43.667,D+.04,7.1,10.47,.24,.20,trim)
# Porch columns and roof structure follow the front elevation.
for xx in [13.667,26.167]:
 box('50 Columnas porche',xx,D+4.55,H/2,1,1,H,stucco)
 box('50 Columnas porche',xx,D+4.55,.15,1.08,1.08,.30,trim)
 box('50 Columnas porche',xx,D+4.55,H-.14,1.10,1.10,.28,trim)
# Four-sided hip roof, 6:12 pitch with 16-inch overhang.
e=16/12;x0=-e;x1=W+e;v0=-e;v1=D+e;cy=(v0+v1)/2;rise=(v1-v0)/4;ey=H+.1;ry=ey+rise;rx0=x0+(v1-v0)/2;rx1=x1-(v1-v0)/2
roofverts=[[x0,ey,v0],[x1,ey,v0],[x1,ey,v1],[x0,ey,v1],[rx0,ry,cy],[rx1,ry,cy]]
add('90 Cubierta principal · ocultable',roofverts,[[0,1,5],[0,5,4],[1,2,5],[2,3,4],[2,4,5],[3,0,4]],roofmat,{'roof':True,'kind':'roof','pitch':'6:12'})
# Under-eave plane kept in roof group, cutaway removes it along with roof.
# Flat ceilings over the bedroom/garage wings and pitched ceiling over social area.
box('90 Cubierta principal · ocultable',6.25,D/2,H+.005,12.5,D+2*e,.07,trim,extras={'roof':True,'kind':'roof'})
box('90 Cubierta principal · ocultable',37.75,D/2,H+.005,24.5,D+2*e,.07,trim,extras={'roof':True,'kind':'roof'})
vr=15.0;ch=H+6.7
add('90 Cubierta principal · ocultable',[[12.5,H,.55],[25.5,H,.55],[12.5,ch,vr],[25.5,ch,vr],[12.5,H,D-.55],[25.5,H,D-.55]],[[0,2,3],[0,3,1],[2,4,5],[2,5,3]],interior,{'roof':True,'kind':'roof'})
# Close both triangular clerestory returns at the transition from the vaulted
# social ceiling to the lower bedroom and kitchen ceilings. These planes stay
# in the roof group, so removing the roof still reveals the entire floor plan.
for xx in [12.5,25.5]:
 add('90 Cubierta principal · ocultable',[[xx,H,.55],[xx,H,vr],[xx,ch,vr],[xx,H,D-.55]],[[0,1,2],[1,3,2]],interior,{'roof':True,'kind':'roof'})
# Close the tiny bearing strips at the front/rear ends of the central vault.
for vv in [.275,D-.275]:box('90 Cubierta principal · ocultable',19,vv,H,13,.55,.06,interior,extras={'roof':True,'kind':'roof'})
# Soffit rims outside the walls, leaving the vaulted area open inside.
for vv in [v0/2,D+e/2]:box('90 Cubierta principal · ocultable',25,vv,H,W+2*e,e,.07,trim,extras={'roof':True,'kind':'roof'})
for xx in [-e/2,W+e/2]:box('90 Cubierta principal · ocultable',xx,D/2,H,e,D,.07,trim,extras={'roof':True,'kind':'roof'})
for vv in [v0,v1]:box('91 Fascia principal · ocultable',25,vv,ey-.10,x1-x0,.10,.32,trim,extras={'roof':True,'kind':'roof'})
for xx in [x0,x1]:box('91 Fascia principal · ocultable',xx,D/2,ey-.10,.10,v1-v0,.32,trim,extras={'roof':True,'kind':'roof'})
# Front-facing gable of the porch, 6:12 matching the main hip roof.
px0=13.167-e;px1=26.667+e;pc=(px0+px1)/2;pr=ey+(px1-px0)/4;pv0=D-3;pv1=D+5+e
pv=[[px0,ey,pv0],[px1,ey,pv0],[pc,pr,pv0],[px0,ey,pv1],[px1,ey,pv1],[pc,pr,pv1]]
add('92 Cubierta porche · ocultable',pv,[[0,2,5],[0,5,3],[2,1,4],[2,4,5]],roofmat,{'roof':True,'kind':'roof'})
add('93 Tímpano porche · ocultable',[[px0,ey,pv1-.07],[px1,ey,pv1-.07],[pc,pr-.06,pv1-.07]],[[0,1,2]],stucco,{'roof':True,'kind':'roof'})
box('94 Sofito porche · ocultable',pc,(D+pv1)/2,H-.01,px1-px0,pv1-D,.08,trim,extras={'roof':True,'kind':'roof'})
for xx in [px0,px1]:box('95 Fascia porche · ocultable',xx,(pv0+pv1)/2,ey-.10,.12,pv1-pv0,.30,trim,extras={'roof':True,'kind':'roof'})
box('95 Fascia porche · ocultable',pc,pv1,ey-.10,px1-px0,.12,.30,trim,extras={'roof':True,'kind':'roof'})
# Sloped fascia beams are thin extruded rectangles following the gable slopes.
for a,b in [(np.array([px0,ey,pv1]),np.array([pc,pr,pv1])),(np.array([pc,pr,pv1]),np.array([px1,ey,pv1]))]:
 edge=b-a;n=np.array([-edge[1],edge[0],0]);n=n/np.linalg.norm(n)*.085;z=np.array([0,0,.07]);vv=[a-n-z,b-n-z,b+n-z,a+n-z,a-n+z,b-n+z,b+n+z,a+n+z];add('95 Fascia porche · ocultable',vv,faces,trim,{'roof':True,'kind':'roof'})
# Interior furniture and fittings, explicitly presentation proposals.
def bed(name,x,v,w=5,d=6.5):
 box(name,x,v,.65,w+.18,d+.2,.6,wood);box(name,x,v,1.15,w,d,.48,linen)
 box(name,x,v-d/2-.14,2.0,w+.35,.24,3.2,linen)
 box(name,x,v+d*.22,1.43,w+.05,d*.46,.08,fabricgreen)
 for xx in [x-w*.25,x+w*.25]:ellipsoid(name,xx,v-d*.29,1.55,w*.23,.63,.18,linen)
 for xx in [x-w/2-.85,x+w/2+.85]:
  box(name,xx,v-d/2+.50,.82,1.35,1.3,1.50,wood);cylinder(name,xx,v-d/2+.5,1.65,.08,.25,frame);cylinder(name,xx,v-d/2+.5,2.08,.30,.55,linen)
bed('60 Dormitorio principal · mobiliario',31.8,22.1,5,6.5)
bed('61 Dormitorio 2 · mobiliario',6.15,4.9,4.5,6.25)
bed('62 Dormitorio 3 · mobiliario',5.9,23.7,4.5,6.25)
# Great room: sofa along left wall, seating facing the suite partition.
box('63 Sala · mobiliario',14.2,23.1,.52,2.7,6.8,.7,wood)
box('63 Sala · mobiliario',14.3,23.1,1.04,2.6,6.8,.55,linen)
box('63 Sala · mobiliario',13.13,23.1,1.68,.4,6.8,1.5,linen)
for vv in [19.9,26.3]:box('63 Sala · mobiliario',14.35,vv,1.5,2.65,.4,1.28,linen)
for vv in [21.0,23.1,25.2]:box('63 Sala · mobiliario',14.47,vv,1.36,2.12,1.96,.15,linen)
box('63 Sala · mobiliario',19.5,23.2,.05,7,9,.04,linen)
cylinder('63 Sala · mobiliario',19.3,23.1,1.2,1.7,.15,wood)
for a in [0,math.tau/3,2*math.tau/3]:cylinder('63 Sala · mobiliario',19.3+1.0*math.cos(a),23.1+1.0*math.sin(a),.6,.09,1.1,frame,12)
box('63 Sala · mobiliario',24.9,24.8,.74,.95,5.6,1.4,wood)
box('63 Sala · mobiliario',25.40,24.8,4.15,.085,4.8,2.7,black)
box('63 Sala · mobiliario',25.345,24.8,4.15,.011,4.6,2.5,frame)
# Dining between the slider and living area, leaves circulation to kitchen and bedrooms.
box('64 Comedor · mobiliario',20.0,5.0,2.48,3.1,5.2,.15,wood)
for xx in [18.75,21.25]:
 for vv in [2.7,7.3]:box('64 Comedor · mobiliario',xx,vv,1.23,.17,.17,2.40,wood)
for xx in [17.72,22.28]:
 for vv in [3.4,6.5]:
  box('64 Comedor · mobiliario',xx,vv,1.45,1.5,1.65,.22,linen)
  bx=xx+(-.72 if xx<20 else .72);box('64 Comedor · mobiliario',bx,vv,2.2,.10,1.65,1.5,wood)
  for dx in [-.55,.55]:
   for dz in [-.55,.55]:box('64 Comedor · mobiliario',xx+dx,vv+dz,.7,.09,.09,1.4,wood)
cylinder('64 Comedor · mobiliario',20,5,2.72,.55,.28,terracotta)
# Kitchen: rear counter, sink, dishwasher, refrigerator, stove block exactly as the sheet.
def cabinet(x,v,w,d=2):
 box('65 Cocina · mobiliario',x,v,1.38,w,d,2.6,wood);box('65 Cocina · mobiliario',x,v,2.77,w+.06,d+.10,.14,quartz)
 count=max(1,round(w/1.5))
 for i in range(count):
  xx=x-w/2+(i+.5)*w/count;box('65 Cocina · mobiliario',xx,v+d/2+.035,1.50,w/count-.055,.035,2.05,wood);box('65 Cocina · mobiliario',xx,v+d/2+.07,2.18,.42,.06,.035,frame)
cabinet(27.667,1.7,8.0)
cabinet(34.33,1.7,2.33)
cabinet(28.75,8.65,5.6)
# sink double bowls in quartz countertop, dark inset and stainless lip
box('65 Cocina · mobiliario',31.1,1.7,2.861,2.35,1.45,.022,steel)
for xx in [30.55,31.65]:box('65 Cocina · mobiliario',xx,1.7,2.874,.94,1.15,.018,frame)
cylinder('65 Cocina · mobiliario',31.1,1.08,3.10,.055,.55,steel,12)
box('65 Cocina · mobiliario',31.1,1.31,3.36,.10,.52,.07,steel)
box('65 Cocina · mobiliario',27.8,1.72,1.47,2.0,2.04,2.55,steel)
box('65 Cocina · mobiliario',27.8,2.755,2.5,1.7,.07,.035,frame)
box('65 Cocina · mobiliario',35.75,1.86,3.0,2.6,2.55,5.95,steel)
for xx in [35.70,35.83]:box('65 Cocina · mobiliario',xx,3.17,3.0,.08,.12,2.0,frame)
box('65 Cocina · mobiliario',28.7,8.65,2.87,2.5,1.90,.09,black)
for xx in [28.0,29.4]:
 for vv in [8.15,9.12]:cylinder('65 Cocina · mobiliario',xx,vv,2.93,.37,.035,frame,20)
box('65 Cocina · mobiliario',28.7,9.73,1.42,2.4,.06,1.5,black)
box('65 Cocina · mobiliario',28.7,9.8,2.27,2.1,.1,.055,steel)
# Wall cabinets above dry rear countertop; no cupboards over window.
for xx in [24.8,26.6]:box('65 Cocina · mobiliario',xx,1.3,5.65,1.72,1.22,2.6,wood)
# Laundry and utility equipment.
for xx in [40.45,42.65]:
 box('66 Lavandería',xx,1.8,1.63,2,2.25,3.2,white);box('66 Lavandería',xx,1.8,3.25,1.85,2.10,.06,quartz)
 cylinder('66 Lavandería',xx,1.8,3.29,.63,.03,frame,24)
box('66 Lavandería',40.45,1.8,3.31,1.5,1.65,.055,white)
cylinder('66 Lavandería',46.1,1.7,2.4,.85,4.7,white)
box('66 Lavandería',46.2,5.6,2.35,1.95,2.85,4.6,steel)
# Bathroom fixtures with actual bathtub/shower positions.
def toilet(name,x,v,rot=0):
 ellipsoid(name,x,v,.54,.51,.75,.43,white);cylinder(name,x,v,.9,.6,.19,white,24,rx=.53,rz=.72)
 cylinder(name,x,v,.999,.4,.01,frame,24,rx=.37,rz=.50)
 box(name,x,v-.58,1.42,1.22,.48,1.43,white)
def vanity(name,x,v,w=2.3,d=1.7):
 box(name,x,v,1.27,w,d,2.45,wood);box(name,x,v,2.57,w+.10,d+.10,.15,quartz)
 ellipsoid(name,x,v,2.66,w*.36,d*.33,.07,white);ellipsoid(name,x,v,2.70,w*.29,d*.26,.012,frame)
 cylinder(name,x,v-d*.34,2.87,.045,.38,steel,10)
# Bath2 tub along left wall 5' x 2'8.
box('67 Baño secundario',2.1,13.60,.85,2.65,5.0,1.6,white)
box('67 Baño secundario',2.1,13.60,1.67,2.27,4.58,.015,quartz)
ellipsoid('67 Baño secundario',2.1,13.60,1.69,1.02,2.07,.01,frame)
toilet('67 Baño secundario',4.8,12.6)
vanity('67 Baño secundario',7.12,12.25,2.15,1.85)
box('67 Baño secundario',7.12,11.14,4.6,2.05,.06,2.6,glass)
# Master bath: shower at rear, WC middle, sink near bedroom door.
box('68 Baño principal',34.75,9.14,.10,5.42,2.58,.18,stone)
box('68 Baño principal',34.75,10.42,3.35,5.4,.033,6.7,glass)
box('68 Baño principal',34.75,10.44,6.70,5.5,.06,.065,frame)
box('68 Baño principal',32.10,9.18,5.1,.09,1.1,.08,steel)
toilet('68 Baño principal',33.3,12.15)
vanity('68 Baño principal',33.15,15.22,1.8,2.05)
box('68 Baño principal',32.05,15.2,4.60,.05,1.83,2.8,glass)
# WIC shelf + rail, secondary closets shelves.
for x,v,w,d in [(28.9,10.06,5.6,.85),(31.30,13.25,.85,5.4),(13.80,4.7,.85,7.5),(4.6,17.0,7.1,.85)]:
 box('69 Closets',x,v,6.5,w,d,.08,wood)
# Exterior small lighting and planter furnishings kept within porch.
for xx in [21.20,25.35]:
 box('70 Luminarias exteriores',xx,D+.22,5.9,.30,.37,1.1,frame)
 box('70 Luminarias exteriores',xx,D+.43,5.9,.22,.04,.80,light)
for xx in [14.8,25.1]:
 cylinder('71 Macetas de porche',xx,D+3.1,.65,.60,1.28,terracotta,24)
 cylinder('71 Macetas de porche',xx,D+3.1,1.30,.52,.05,soil,24)
 for j in range(14):
  a=j*2.4;r=.46*math.sqrt((j+1)/14);ellipsoid('71 Macetas de porche',xx+math.cos(a)*r,D+3.1+math.sin(a)*r,1.5+(j%4)*.15,.30,.22,.32,leaf if j%2 else leaf2)
# Export de-indexed float attribute buffers compatible with the site's lightweight loader.
def accessor(a,typ):
 a=np.asarray(a,dtype='<f4');g['accessors'].append({'bufferView':append(a.tobytes(),34962),'componentType':5126,'count':len(a),'type':typ,'min':a.min(0).tolist(),'max':a.max(0).tolist()});return len(g['accessors'])-1
for name,mats in groups.items():
 prim=[]
 for mat,(p,n,u) in mats.items():
  prim.append({'attributes':{'POSITION':accessor(p,'VEC3'),'NORMAL':accessor(n,'VEC3'),'TEXCOORD_0':accessor(u,'VEC2')},'material':mat})
 g['meshes'].append({'name':name,'primitives':prim});extra=group_extras.get(name,{})
 if int(name[:2])>=60 and int(name[:2])<90:extra.update({'proposal':True,'kind':'furnishing'})
 g['nodes'].append({'name':name,'mesh':len(g['meshes'])-1,'extras':extra});g['scenes'][0]['nodes'].append(len(g['nodes'])-1)
g['buffers'][0]['byteLength']=len(buf);js=json.dumps(g,separators=(',',':')).encode();js+=b' '*((-len(js))%4);buf+=b'\0'*((-len(buf))%4)
(OUT/'bell.glb').write_bytes(struct.pack('<III',0x46546c67,2,28+len(js)+len(buf))+struct.pack('<II',len(js),0x4e4f534a)+js+struct.pack('<II',len(buf),0x004e4942)+buf)
metadata={'model':'Bell','source_document':'BELL MODEL.pdf','source_sheet':'Floor Plan + Front/Rear/Left/Right Elevations, sheet 3 of 6','source_author':'Kimsa Construction LLC','source_date':'2024-08-14','job':'2024-140','units':'m','coordinates':{'up':'+Y','front':'+Z','origin':'Centre of main body + front porch bounding rectangle, finished floor at Y=0'},'bedrooms':3,'bathrooms':2,'garage_spaces':1,'official_schedule_ft2':{'living':1157,'entry':67,'garage':310,'total':1534},'official_schedule_m2':{k:round(v*.09290304,3) for k,v in {'living':1157,'entry':67,'garage':310,'total':1534}.items()},'footprint_m':{'width':15.24,'body_depth':round(D*FT,4),'max_depth_with_front_porch':round((D+5)*FT,4),'covered_total_area':round(1534*.09290304,3)},'roof':{'pitch':'6:12','bearing_height_m':round(H*FT,4),'overhang_m':.4064,'type':'Hip main roof with front gable over porch','cutaway':'Hide nodes with extras.roof === true'},'rear_pad':{'width_m':3.048,'depth_m':2.4384,'area_m2':7.432,'included_in_covered_area':False},'representation':'3D presentation reconstructed from supplied dimensioned architectural sheet. Exterior colors, material palette, furniture and decorative fixtures are proposed. Interior partitions/openings follow the drawing with presentation-level detail; verify against original architectural documents before construction.','floorplan':'floorplan.svg','source_floorplan':'floorplan.png','model_url':'bell.glb','camera_suggestions':{'exterior':{'position':[3.8,5.2,22],'target':[0,1.4,0]},'cutaway':{'position':[1,18,12],'target':[0,0,0]},'interior_living':{'position':[-2.00,1.60,2.10],'target':[-.15,1.35,-3.25],'fov':72},'interior_kitchen':{'position':[.90,1.60,-3.40],'target':[2.10,1.25,-4.70],'fov':72},'interior_master':{'position':[.82,1.60,3.18],'target':[2.05,.85,1.40],'fov':72},'interior_bedroom2':{'position':[-4.80,1.60,-2.78],'target':[-5.74,1.1,-4.1],'fov':72}},'revision':'2026-10-14 · closed vault returns and centered kitchen view'}
metadata['geometry_bounds_m']={'slab':{'min':[-7.62,-.134112,-5.2324],'max':[7.62,0,5.2324]},'covered_front_z':5.2324,'body_front_z':3.7084,'body_rear_z':-5.2324,'rear_pad_back_z':-7.6708,'roof_eave_front_z':5.6388,'roof_ridge_height':round(ry*FT,4)}
metadata['footprint_polygon_xz_m']=[[-7.62,-5.2324],[7.62,-5.2324],[7.62,3.7084],[.5081,3.7084],[.5081,5.2324],[-3.6067,5.2324],[-3.6067,3.7084],[-7.62,3.7084]]
metadata['modeling_note']='The covered area uses the architect schedule (142.513 m²); do not calculate finished living area from the bounding rectangle. The unroofed rear concrete pad is modeled separately. Furnishings and finishes are illustrative.'
(OUT/'metadata.json').write_text(json.dumps(metadata,ensure_ascii=False,indent=2))
# Architectural source crop, not a redrawn approximation. Source raster came from PDF at 6000 px width.
im=Image.open('work/house-plans/bell-full.png');crop=im.crop((310,490,2820,3210));crop.save(OUT/'floorplan.png',optimize=True)
f=io.BytesIO();crop.save(f,format='PNG',optimize=True);encoded=base64.b64encode(f.getvalue()).decode()
svg=f'''<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" width="1600" height="1900" viewBox="0 0 1600 1900"><rect width="1600" height="1900" fill="#fbfaf6"/><text x="70" y="73" font-family="Arial,sans-serif" font-size="37" fill="#193c31">BELL · PLANTA ARQUITECTÓNICA</text><text x="70" y="116" font-family="Arial,sans-serif" font-size="23" fill="#5c6b61">3 dormitorios · 2 baños · garaje individual</text><image x="45" y="147" width="1510" height="1636" xlink:href="data:image/png;base64,{encoded}"/><text x="70" y="1820" font-family="Arial,sans-serif" font-size="22" fill="#193c31">Vivienda: 1,157 ft² · Garaje: 310 ft² · Entrada: 67 ft² · Total: 1,534 ft²</text><text x="70" y="1860" font-family="Arial,sans-serif" font-size="18" fill="#5c6b61">Fuente: plano del cliente · Kimsa Construction LLC · 14 agosto 2024 · Hoja 3 de 6.</text></svg>'''
(OUT/'floorplan.svg').write_text(svg)
print(json.dumps({'file':str(OUT/'bell.glb'),'MB':round((OUT/'bell.glb').stat().st_size/1e6,2),'nodes':len(g['nodes']),'materials':len(g['materials']),'triangles':sum(a['count']//3 for a in g['accessors'] if a['type']=='VEC3')//2,'roof_nodes':[n['name'] for n in g['nodes'] if n.get('extras',{}).get('roof')],'footprint':metadata['footprint_m']},indent=2))
