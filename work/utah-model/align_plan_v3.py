"""Utah presentation revision from client architectural sheets.
Preserves source SketchUp wall plan, openings, hip-roof topology and PBR textures.
Reconciles ceilings, ridge and kitchen/bath furnishings with supplied drawings.
Coordinates for added fittings are original SketchUp metres: x, northing y, height z.
"""
from pathlib import Path
import json, struct, numpy as np, copy
root=Path('work/sites/r15-ocala/dist/utah')
raw=(root/'utah-propuesta-v2.glb').read_bytes(); n=struct.unpack_from('<I',raw,12)[0]; g=json.loads(raw[20:20+n]); buf=bytearray(raw[28+n:])

def read(i):
 a=g['accessors'][i]; v=g['bufferViews'][a['bufferView']]; k={'VEC2':2,'VEC3':3}[a['type']]
 return np.frombuffer(buf,dtype='<f4',count=a['count']*k,offset=v.get('byteOffset',0)+a.get('byteOffset',0)).reshape(-1,k).copy()
def acc(a,typ='VEC3'):
 a=np.asarray(a,dtype='<f4');
 while len(buf)%4:buf.append(0)
 g['bufferViews'].append({'buffer':0,'byteOffset':len(buf),'byteLength':a.nbytes,'target':34962});buf.extend(a.tobytes())
 g['accessors'].append({'bufferView':len(g['bufferViews'])-1,'componentType':5126,'count':len(a),'type':typ,'min':a.min(0).tolist(),'max':a.max(0).tolist()});return len(g['accessors'])-1

def write_mesh(pr,p):
 tr=p.reshape(-1,3,3); nn=np.cross(tr[:,1]-tr[:,0],tr[:,2]-tr[:,0]); lengths=np.linalg.norm(nn,axis=1); keep=lengths>1e-9
 tr=tr[keep]; nn=nn[keep]/lengths[keep,None];pr['attributes']['POSITION']=acc(tr.reshape(-1,3));pr['attributes']['NORMAL']=acc(np.repeat(nn,3,axis=0))
 if 'TEXCOORD_0' in pr['attributes']:
  uv=read(pr['attributes']['TEXCOORD_0']).reshape(-1,3,2)[keep].reshape(-1,2);pr['attributes']['TEXCOORD_0']=acc(uv,'VEC2')

# Supplied elevations: 8 ft bearing height; front elevation 14 ft 6 in overall ridge.
ceil=8*.3048; ridge=14.5*.3048; original_roof_min=2.3; original_roof_max=4.531482879708705
wall_ids=set(range(74,112))|set(range(136,141))|{166,167}
for node in g['nodes']:
 sid=node.get('extras',{}).get('sourceNode')
 if sid in wall_ids:
  for pr in g['meshes'][node['mesh']]['primitives']:
   pos=read(pr['attributes']['POSITION']);pos[:,1]=np.minimum(pos[:,1],ceil);write_mesh(pr,pos)
  node['extras']['planRevision']='8 ft ceiling / bearing line from FLOOR PLAN and ELEVATIONS'
 if sid==165 or node['name'].startswith('Remate alero'):
  node['extras']['roof']=True
  for pr in g['meshes'][node['mesh']]['primitives']:
   pos=read(pr['attributes']['POSITION']);pos[:,1]=ceil+(pos[:,1]-original_roof_min)*(ridge-ceil)/(original_roof_max-original_roof_min);write_mesh(pr,pos)

# Replace previous illustrative kitchen islands and bath boxes with fittings at the plan locations.
removed=[];nodes=[]
for node in g['nodes']:
 ex=node.get('extras',{}); name=node['name']
 if ex.get('proposal') and (ex.get('kind') in ['kitchen','bath'] or name in ['Taburete','Listón acceso']): removed.append(name)
 else:nodes.append(node)
g['nodes']=nodes;g['scenes'][0]['nodes']=list(range(len(nodes)))

# Interior surfaces: seamless counters, concrete garage and a removable flat ceiling.
g['materials'].append({'name':'Utah quartz counters','pbrMetallicRoughness':{'baseColorFactor':[.82,.80,.74,1],'roughnessFactor':.36,'metallicFactor':0},'doubleSided':True});quartz=len(g['materials'])-1
g['materials'].append({'name':'Utah sealed garage concrete','pbrMetallicRoughness':{'baseColorFactor':[.42,.43,.41,1],'roughnessFactor':.82,'metallicFactor':0},'doubleSided':True});garage_mat=len(g['materials'])-1
for node in g['nodes']:
 if node.get('extras',{}).get('sourceNode')==73:
  for pr in g['meshes'][node['mesh']]['primitives']:pr['material']=15

# Helpers produce unindexed float32 primitives compatible with the site's light GLB loader.
def add(name,positions,mat=32,kind='plan-detail',uv=True):
 p=np.array(positions,float);t=p.reshape(-1,3,3); nn=np.cross(t[:,1]-t[:,0],t[:,2]-t[:,0]);ll=np.linalg.norm(nn,axis=1);mask=ll>1e-9;t=t[mask];nn=nn[mask]/ll[mask,None];p=t.reshape(-1,3);nr=np.repeat(nn,3,axis=0)
 attrs={'POSITION':acc(p),'NORMAL':acc(nr)}
 if uv:
  ax=np.argmax(np.abs(nr),axis=1); tc=np.c_[np.where(ax==0,p[:,2],p[:,0]),np.where(ax==1,p[:,2],p[:,1])]/.85;attrs['TEXCOORD_0']=acc(tc,'VEC2')
 g['meshes'].append({'name':name,'primitives':[{'attributes':attrs,'material':mat}]});g['nodes'].append({'name':name,'mesh':len(g['meshes'])-1,'extras':{'proposal':True,'kind':kind,'planBased':True}});g['scenes'][0]['nodes'].append(len(g['nodes'])-1)

corn=np.array([[-1,-1,-1],[1,-1,-1],[1,1,-1],[-1,1,-1],[-1,-1,1],[1,-1,1],[1,1,1],[-1,1,1]],float)/2
faces=np.array([[0,2,1],[0,3,2],[4,5,6],[4,6,7],[0,1,5],[0,5,4],[3,7,6],[3,6,2],[0,4,7],[0,7,3],[1,2,6],[1,6,5]])
def box(name,x,y,z,w,d,h,mat=32,kind='plan-detail'):
 v=corn*np.array([w,h,d])+np.array([x-12.2,z,20.2-y]);add(name,v[faces].reshape(-1,3),mat,kind)
def cyl(name,x,y,z,rx,ry,h,mat=49,segments=32):
 v=[]
 for i in range(segments):
  a=i*2*np.pi/segments;b=(i+1)*2*np.pi/segments
  p=[x-12.2+rx*np.cos(a),z-h/2,20.2-y+ry*np.sin(a)];q=[x-12.2+rx*np.cos(b),z-h/2,20.2-y+ry*np.sin(b)]
  pt=[p[0],z+h/2,p[2]];qt=[q[0],z+h/2,q[2]]
  v.extend([p,q,qt,p,qt,pt,[x-12.2,z+h/2,20.2-y],pt,qt,[x-12.2,z-h/2,20.2-y],q,p])
 add(name,v,mat)

def cabinet(label,x,y,w,d=.59):
 box(label+' · roble',x,y,.445,w,d,.85,31)
 box(label+' · zócalo',x,y,.07,w-.08,d-.05,.14,0)
 box(label+' · encimera',x,y,.885,w+.04,d+.04,.055,quartz)
 count=max(1,round(w/.55))
 for k in range(count):
  cx=x-w/2+(k+.5)*w/count;box(label+' · frente',cx,y-d/2-.006,.46,w/count-.024,.018,.73,31);box(label+' · tirador',cx,y-d/2-.025,.765,.2,.025,.018,0)

def cooker(label,x,y):
 box(label+' · placa',x,y,.921,.56,.5,.025,36)
 for dx in [-.14,.14]:
  for dy in [-.13,.13]:cyl(label+' · quemador',x+dx,y+dy,.94,.072,.072,.012,0,24)
 box(label+' · campana',x,y+.14,1.78,.60,.31,.12,3)
 box(label+' · conducto',x,y+.16,2.055,.22,.22,.44,3)
def sink(label,x,y,w=.55,d=.4):
 box(label+' · borde',x,y,.925,w,d,.025,37)
 box(label+' · cubeta',x,y,.939,w-.065,d-.065,.012,0)
 cyl(label+' · grifo',x,y+d/2-.02,1.06,.018,.018,.25,3,16)
 box(label+' · cuello grifo',x,y+d/2-.07,1.18,.032,.13,.028,3)
def fridge(label,x,y,w=.72,d=.72):
 box(label,x,y,1.0,w,d,2,33);box(label+' · cara',x,y-d/2-.007,1.05,w-.045,.018,1.83,3)
 box(label+' · asa',x+w*.3,y-d/2-.035,1.2,.025,.04,.6,0)

# Main kitchen: parallel rear counter and front sink peninsula, no freestanding island.
cabinet('Utah cocina · línea posterior',9.51,21.70,1.64)
cooker('Utah cocina',9.39,21.66)
fridge('Utah refrigerador',10.66,21.63,.70,.74)
cabinet('Utah cocina · península',9.91,19.97,2.38,.65)
sink('Utah fregadero',9.75,19.94,.62,.43)
box('Utah lavavajillas · frente',8.97,19.60,.46,.56,.024,.79,3)

# Annex has its own kitchen, refrigerator and W/D indicated in client drawing.
cabinet('Anexo cocina',6.31,22.53,2.12)
sink('Anexo fregadero',5.95,22.50,.55,.41)
cooker('Anexo cocina',6.94,22.5)
fridge('Anexo refrigerador',7.90,22.57,.69,.73)
box('Anexo lavadora / secadora',8.95,22.63,.91,.65,.64,1.80,52)
for h in [.52,1.37]:
 box('Anexo W/D · puerta',8.95,22.299,h,.38,.022,.38,3)

# Bathroom locations/fixture types follow the drawing; finishes are a presentation proposal.
def toilet(name,x,y):
 cyl(name+' · base',x,y,.19,.16,.22,.38,49)
 cyl(name+' · taza',x,y-.06,.405,.205,.27,.12,49)
 cyl(name+' · interior',x,y-.09,.472,.13,.19,.012,0)
 box(name+' · tanque',x,y+.23,.64,.4,.2,.56,49)
 box(name+' · tapa',x,y+.23,.93,.43,.23,.04,49)
def vanity(name,x,y,w=.85,d=.45):
 cabinet(name,x,y,w,d);cyl(name+' · lavamanos',x,y-.02,.943,.21,.16,.075,49)
 cyl(name+' · cubeta',x,y-.02,.984,.165,.115,.009,37)
 box(name+' · espejo',x,y+d/2+.022,1.61,w-.03,.028,.78,50)
 cyl(name+' · grifo',x,y+.11,1.03,.016,.016,.17,3,16)
def tub(name,x,y,w,d):
 box(name+' · base',x,y,.08,w,d,.16,49)
 box(name+' · fondo',x,y,.17,w-.16,d-.16,.02,49)
 for sx in [-1,1]:box(name+' · lateral',x+sx*(w/2-.045),y,.28,.09,d,.40,49)
 for sy in [-1,1]:box(name+' · cabecera',x,y+sy*(d/2-.045),.28,w-.12,.09,.4,49)
 box(name+' · grifería',x,y+d/2-.07,.57,.16,.07,.1,3)

# Master: shower to left, toilet and vanity along southern wall.
box('Principal ducha · plato',14.08,21.17,.045,.69,1.66,.09,49)
box('Principal ducha · vidrio',14.40,21.17,1.03,.012,1.65,1.98,4)
box('Principal ducha · grifería',13.77,21.8,1.12,.04,.09,.16,3)
box('Principal ducha · rociador',13.88,21.8,2.13,.22,.20,.025,3)
toilet('Principal sanitario',14.90,20.91)
vanity('Principal tocador',15.68,20.75,.95,.44)
# Shared bath: tub runs north/south in right-hand bay.
tub('Baño 2 bañera',15.81,19.46,.77,1.50)
toilet('Baño 2 sanitario',14.86,19.87)
vanity('Baño 2 tocador',14.09,18.98,.52,.43)
# Studio bathroom: transverse rear tub, middle toilet, front vanity.
tub('Anexo bañera',10.24,26.86,1.48,.75)
toilet('Anexo sanitario',10.61,25.86)
vanity('Anexo tocador',10.60,25.17,.64,.46)

# Warm bedroom floors and light stone wet rooms, surface overlays only.
for label,x,y,w,d in [
 ('Dormitorio 3',14.86,14.76,3.10,3.18),('Dormitorio 2',18.49,15.45,3.72,2.99),
 ('Dormitorio principal',18.34,20.34,3.83,3.38),('Estudio anexo',7.30,25.68,4.06,3.08)]:
 box(label+' · piso roble',x,y,.008,w,d,.014,25,'floor-finish')
for label,x,y,w,d in [('Baño principal',15.02,21.24,2.4,1.57),('Baño 2',15.04,19.44,2.4,1.57),('Baño anexo',10.23,26.02,1.49,2.41)]:
 box(label+' · porcelánico',x,y,.009,w,d,.016,32,'floor-finish')

box('Garaje · concreto sellado',6.91,17.12,.011,3.34,6.40,.019,garage_mat,'floor-finish')
# Ceiling derived from actual source slab top; side stoop excluded, tagged with roof.
slab_node=next(n for n in g['nodes'] if n.get('extras',{}).get('sourceNode')==73)
ceiling=[]
for pr in g['meshes'][slab_node['mesh']]['primitives']:
 for tri in read(pr['attributes']['POSITION']).reshape(-1,3,3):
  if np.all(np.abs(tri[:,1])<1e-5) and tri[:,0].mean()>-7.16:
   tr=tri.copy();tr[:,1]=ceil-.008;ceiling.extend(tr)
add('Utah · cielo raso a 8 ft',ceiling,12,'ceiling')
g['nodes'][-1]['extras']['roof']=True

# Metadata deliberately separates the architectural schedule from source-model slab area.
g['asset']['generator']='Rainbow Park / Utah plan revision v3'
g['asset']['extras']={'architecturalSources':['FLOOR PLAN.pdf','ELEVATIONS.pdf'],'designer':'Kimsa Construction LLC','sheetJob':'2025-713','presentationFinishes':True,'frontDirection':'+Z'}
g['buffers'][0]['byteLength']=len(buf);js=json.dumps(g,separators=(',',':')).encode();js+=b' '*((-len(js))%4);buf+=b'\0'*((-len(buf))%4)
(root/'utah-plan-v3.glb').write_bytes(struct.pack('<III',0x46546c67,2,28+len(js)+len(buf))+struct.pack('<II',len(js),0x4e4f534a)+js+struct.pack('<II',len(buf),0x004e4942)+buf)
meta={
 'model':'Utah / Anexo','architectural_sources':['utah-floor-plan.pdf','utah-elevations.pdf'],
 'author':'Kimsa Construction LLC','job':'2025-713','elevations_date':'2025-09-03',
 'areas_from_sheet_sqft':{'living':1490,'entry':13,'garage':263,'total':1766},
 'areas_from_sheet_m2':{'living':round(1490*.09290304,2),'entry':round(13*.09290304,2),'garage':round(263*.09290304,2),'total':round(1766*.09290304,2)},
 'wall_envelope_m':{'width':51*.3048,'total_depth':47.5*.3048,'main_depth':30.5*.3048},
 'source_skp_slab_envelope_m':{'width_including_side_stoop':16.751457966862515,'depth':14.486538519941988,'slab_area_including_stoops':169.5273611846705},
 'ceiling_m':ceil,'front_elevation_ridge_m':ridge,'bedrooms_main':3,'studio_annex':1,'bathrooms':3,'garage_spaces':1,
 'corrected':['Floorplan replaced with actual architectural sheet, preserving original room names and dimensions','Interior and exterior wall heights reconciled to 8 ft bearing height','Front roof ridge calibrated to 14 ft 6 in while preserving existing hip topology','Main kitchen revised to plan counters and sink peninsula; oversized prior island removed','Annex kitchen and W/D included','All three bathrooms fitted at plan locations','Decorative entry slats that covered the front door removed','Roof fascia and 8 ft flat ceilings included in removable roof group'],
 'retained':['Source SketchUp wall XY arrangement and window/door geometry','PBR finish textures from v2','Source roof topology, adjusted vertically to the front elevation'],
 'review_notes':['Presentation model derived from source SKP and architectural sheets; not a construction BIM','Source rear/right elevations omit some windows shown in the floorplan; model retains floorplan openings pending designer confirmation','Source sheet rear/side ridge dimensions differ slightly from front; v3 uses 14 ft 6 in front maximum','Materials and movable furnishings are a proposed design palette']
}
(root/'metadata-plan-v3.json').write_text(json.dumps(meta,ensure_ascii=False,indent=2))
print(json.dumps({'path':str(root/'utah-plan-v3.glb'),'nodes':len(g['nodes']),'bytes':len(buf),'removed_old_proposal_objects':len(removed),'areas_m2':meta['areas_from_sheet_m2']},indent=2))
