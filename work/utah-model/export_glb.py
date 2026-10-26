import json,numpy as np,struct
from pathlib import Path
base=Path(__file__).parent;d=json.loads((base/'extracted.json').read_text());target=Path('work/sites/r15-ocala/dist/utah');target.mkdir(exist_ok=True)
binbuf=bytearray();gltf={'asset':{'version':'2.0','generator':'Rainbow Park / SketchUp original geometry'},'scene':0,'scenes':[{'nodes':[]}],'nodes':[],'meshes':[],'materials':[],'buffers':[{}],'bufferViews':[],'accessors':[],'images':[],'textures':[],'samplers':[{'magFilter':9729,'minFilter':9987,'wrapS':10497,'wrapT':10497}]}
def buffer(data,target=None):
 while len(binbuf)%4:binbuf.append(0)
 start=len(binbuf);binbuf.extend(data);v={'buffer':0,'byteOffset':start,'byteLength':len(data)}
 if target:v['target']=target
 gltf['bufferViews'].append(v);return len(gltf['bufferViews'])-1
def accessor(a,typ):
 a=np.asarray(a,dtype='<f4');bv=buffer(a.tobytes(),34962);r={'bufferView':bv,'componentType':5126,'count':len(a),'type':typ}
 if typ=='VEC3':r.update(min=a.min(0).tolist(),max=a.max(0).tolist())
 gltf['accessors'].append(r);return len(gltf['accessors'])-1
mats={}
for k,m in list(d['materials'].items())+[(None,{'name':'Muros sin asignación','color':[.88,.86,.80,1],'texture':None})]:
 pbr={'baseColorFactor':m['color'],'metallicFactor':0,'roughnessFactor':.7};mat={'name':m['name'],'pbrMetallicRoughness':pbr,'doubleSided':True}
 if m['texture']:
  v=buffer((base/m['texture']).read_bytes());gltf['images'].append({'bufferView':v,'mimeType':'image/png'});gltf['textures'].append({'sampler':0,'source':len(gltf['images'])-1});pbr['baseColorTexture']={'index':len(gltf['textures'])-1};pbr['baseColorFactor']=[1,1,1,1]
 if m['color'][3]<.9:mat['alphaMode']='BLEND';pbr['roughnessFactor']=.13
 gltf['materials'].append(mat);mats[k]=len(gltf['materials'])-1
transforms=[];world={};center=np.array([12.2,20.2,.25]);allbounds=[]
for i,n in enumerate(d['nodes']):
 xf=np.array(n['transform']).reshape(4,4).T if n['transform'] else np.eye(4)
 if n['parent'] is not None:xf=transforms[n['parent']]@xf
 transforms.append(xf);geo=d['geometries'][n['geometry']]
 if not geo['vertices']:continue
 v=np.array(geo['vertices']);v=(xf[:3,:3]@v.T).T+xf[:3,3];world[i]=(v,np.array(geo['triangles']))
 if i in [168,169,170]:continue
 allbounds.extend(v)
 inherited=n['props'].get('material');p=n['parent']
 while inherited is None and p is not None:inherited=d['nodes'][p]['props'].get('material');p=d['nodes'][p]['parent']
 mapped=[m or inherited for m in geo['materials']];primitives=[]
 for mk in dict.fromkeys(mapped):
  faces=np.array([tri for tri,key,hidden in zip(geo['triangles'],mapped,geo['hidden']) if key==mk and not hidden])
  if not len(faces):continue
  pos=v[faces].reshape(-1,3)-center;pos=pos[:,[0,2,1]];pos[:,2]*=-1
  normals=np.cross(pos.reshape(-1,3,3)[:,1]-pos.reshape(-1,3,3)[:,0],pos.reshape(-1,3,3)[:,2]-pos.reshape(-1,3,3)[:,0]);normals/=np.maximum(np.linalg.norm(normals,axis=1,keepdims=True),1e-12);normals=np.repeat(normals,3,axis=0);uv=np.array(geo['uvs'])[faces].reshape(-1,2);uv[:,1]=1-uv[:,1]
  primitives.append({'attributes':{'POSITION':accessor(pos,'VEC3'),'NORMAL':accessor(normals,'VEC3'),'TEXCOORD_0':accessor(uv,'VEC2')},'material':mats[mk]})
 if primitives:
  gltf['meshes'].append({'name':n['name'],'primitives':primitives});gltf['nodes'].append({'name':f'{i:03} {n["name"]}','mesh':len(gltf['meshes'])-1,'extras':{'sourceNode':i,'roof':i==165}});gltf['scenes'][0]['nodes'].append(len(gltf['nodes'])-1)
gltf['buffers'][0]['byteLength']=len(binbuf);js=json.dumps(gltf,separators=(',',':')).encode();js+=b' '*((-len(js))%4);binbuf+=b'\0'*((-len(binbuf))%4)
(target/'utah-original.glb').write_bytes(struct.pack('<III',0x46546c67,2,12+8+len(js)+8+len(binbuf))+struct.pack('<II',len(js),0x4e4f534a)+js+struct.pack('<II',len(binbuf),0x004e4942)+binbuf)
# Top surface footprint of base slab (not roof or site).
v,f=world[73];tri=v[f];cross=np.cross(tri[:,1]-tri[:,0],tri[:,2]-tri[:,0]);top=np.all(np.abs(tri[:,:,2]-.25)<.001,axis=1);area=np.abs(cross[top,2]).sum()/2
stats={'source':'kimsa-UTAH ANEXO.skp','coordinates':'metres converted from SketchUp internal inches','slab_top_area_m2':float(area),'slab_bounds':{'min':v.min(0).tolist(),'max':v.max(0).tolist()},'roof_bounds':{'min':world[165][0].min(0).tolist(),'max':world[165][0].max(0).tolist()},'source_site_m':[24.384,39.624],'center':center.tolist(),'source_camera':d['camera']}
(base/'measurements.json').write_text(json.dumps(stats,indent=2));print(json.dumps(stats,indent=2))
# Draft section plan at 1.2m above floor. Individual source wall meshes identify structure.
lines=[]
for i,(v,f) in world.items():
 if i in [165,168,169,170]:continue
 for tri in v[f]:
  points=[]
  for a,b in [(tri[0],tri[1]),(tri[1],tri[2]),(tri[2],tri[0])]:
   if (a[2]-1.45)*(b[2]-1.45)<0:points.append(a+(b-a)*(1.45-a[2])/(b[2]-a[2]))
  if len(points)==2:lines.append((points[0][:2],points[1][:2]))
scale=45
svg=['<svg xmlns="http://www.w3.org/2000/svg" width="1000" height="950" viewBox="0 0 1000 950"><rect width="1000" height="950" fill="#f4f0e6"/><text x="55" y="45" font-family="Arial" font-size="23">UTAH · PLANTA EXTRAÍDA DEL MODELO</text>']
for a,b in lines:
 x1,y1=(a[0]-2)*scale+30,850-(a[1]-12)*scale;x2,y2=(b[0]-2)*scale+30,850-(b[1]-12)*scale
 svg.append(f'<path d="M{x1:.2f},{y1:.2f} L{x2:.2f},{y2:.2f}" stroke="#20372d" stroke-width="1.5" fill="none"/>')
svg.append('<text x="55" y="920" font-family="Arial" font-size="13">Sección geométrica a 1.20 m sobre el piso · Borrador de revisión, no plano constructivo.</text></svg>');(target/'floorplan-draft.svg').write_text(''.join(svg))
