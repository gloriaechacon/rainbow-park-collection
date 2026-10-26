import json,struct,collections,numpy as np
from pathlib import Path
p=Path('work/sites/r15-ocala/dist/utah');raw=(p/'utah-plan-v3.glb').read_bytes();n=struct.unpack_from('<I',raw,12)[0];g=json.loads(raw[20:20+n]);buf=raw[n+28:]
def read(i):
 a=g['accessors'][i];v=g['bufferViews'][a['bufferView']];k={'VEC3':3,'VEC2':2}[a['type']];return np.frombuffer(buf,dtype='<f4',offset=v.get('byteOffset',0)+a.get('byteOffset',0),count=a['count']*k).reshape(-1,k)
slab=next(n for n in g['nodes'] if n.get('extras',{}).get('sourceNode')==73)
edges=collections.Counter();area=0
for pr in g['meshes'][slab['mesh']]['primitives']:
 for tri in read(pr['attributes']['POSITION']).reshape(-1,3,3):
  if np.all(np.abs(tri[:,1])<1e-5):
   area+=np.linalg.norm(np.cross(tri[1]-tri[0],tri[2]-tri[0]))/2
   for a,b in [(tri[0],tri[1]),(tri[1],tri[2]),(tri[2],tri[0])]:edges[tuple(sorted([tuple(np.round(a[[0,2]],5)),tuple(np.round(b[[0,2]],5))]))]+=1
segments=[e for e,c in edges.items() if c==1];loops=[]
while segments:
 a,b=segments.pop();loop=[a,b]
 while loop[-1]!=loop[0]:
  idx=next((i for i,e in enumerate(segments) if loop[-1] in e),None)
  if idx is None:break
  e=segments.pop(idx);loop.append(e[1] if e[0]==loop[-1] else e[0])
 loops.append(loop)
meta=json.loads((p/'metadata-plan-v3.json').read_text())
meta['geometry_footprint']={'coordinate_system':'GLB local metres; x is east/west, z is rear/front, front = +z','source_node':73,'area_m2':float(area),'contours_xz':loops,'includes':'Source SKP slab includes side stoop and exterior entrance slab. Use as conservative house placement footprint; source architectural total is a separate 1,766 sq ft.'}
meta['cameras']={
 'exterior':{'position':[2.8,4.8,23],'target':[.6,1.5,0]},
 'living':{'label':'Sala','position':[-1.2,1.6,4.5],'target':[-2.0,1.14,2.4]},
 'kitchen':{'label':'Cocina','position':[-.05,1.6,-.05],'target':[-2.4,1.1,-.7]},
 'primary':{'label':'Dormitorio principal','position':[4.8,1.6,1.1],'target':[6.6,1.1,-.8]},
 'annex':{'label':'Estudio anexo','position':[-3.55,1.6,-4.5],'target':[-4.95,1.1,-5.8]},
 'annex_living':{'label':'Sala del anexo','position':[-2.1,1.6,-3.2],'target':[-5.5,1.05,-2.4]},
 'plan':{'position':[.6,28,.1],'target':[.6,0,0]}
}
meta['cutaway']={'predicate':'node.userData.roof === true','roof_names':[n['name'] for n in g['nodes'] if n.get('extras',{}).get('roof')],'ceiling_height_m':2.4384,'notes':'The entire hip roof plus fascia share roof:true. Flat ceiling planes share the same roof flag. All inner walls are now capped to 8 ft for an unobstructed plan cutaway.'}
(p/'metadata-plan-v3.json').write_text(json.dumps(meta,ensure_ascii=False,indent=2,default=float))
print('Actual GLB slab:',round(area,4),'m2;',len(loops),'contour(s);',len(meta['cutaway']['roof_names']),'roof parts. Camera coordinates included.')
