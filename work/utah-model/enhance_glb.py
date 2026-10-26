import json,struct,numpy as np
from pathlib import Path
base=Path(__file__).parent;dst=Path('work/sites/r15-ocala/dist/utah');raw=(dst/'utah-original.glb').read_bytes();n=struct.unpack_from('<I',raw,12)[0];g=json.loads(raw[20:20+n]);buf=bytearray(raw[28+n:]);furn=json.loads((base/'furnishings.json').read_text())
def rgb(s):
 a=[int(s[i:i+2],16)/255 for i in [1,3,5]];return [x/12.92 if x<.04045 else ((x+.055)/1.055)**2.4 for x in a]+[1]
for m in g['materials']:
 name=m['name'];p=m['pbrMetallicRoughness']
 if any(x in name for x in ['M00','White','Charcoal','Muros','auto']):p.pop('baseColorTexture',None);p['baseColorFactor']=rgb('#e9e4d5');p['roughnessFactor']=.9
 elif any(x in name for x in ['Ventana','Alumin','Color M08']):p.pop('baseColorTexture',None);p['baseColorFactor']=rgb('#303c32');p['roughnessFactor']=.4;p['metallicFactor']=.35
 if m.get('alphaMode')=='BLEND':p['baseColorFactor']=rgb('#b7d0cf')[:3]+[.27];p['roughnessFactor']=.12
colors={}
def material(color):
 if color not in colors:
  colors[color]=len(g['materials']);g['materials'].append({'name':'Propuesta '+color,'pbrMetallicRoughness':{'baseColorFactor':rgb(color),'metallicFactor':0,'roughnessFactor':.75},'doubleSided':True})
 return colors[color]
def acc(a):
 a=np.array(a,dtype='<f4');idx=len(g['bufferViews']);g['bufferViews'].append({'buffer':0,'byteOffset':len(buf),'byteLength':a.nbytes,'target':34962});buf.extend(a.tobytes());g['accessors'].append({'bufferView':idx,'componentType':5126,'count':len(a),'type':'VEC3','min':a.min(0).tolist(),'max':a.max(0).tolist()});return len(g['accessors'])-1
corners=np.array([[-1,-1,-1],[1,-1,-1],[1,1,-1],[-1,1,-1],[-1,-1,1],[1,-1,1],[1,1,1],[-1,1,1]],float)/2
faces=np.array([[0,2,1],[0,3,2],[4,5,6],[4,6,7],[0,1,5],[0,5,4],[3,7,6],[3,6,2],[0,4,7],[0,7,3],[1,2,6],[1,6,5]])
for obj in furn:
 if obj['kind']=='site':continue
 x,y,z=obj['position'];w,d,h=obj['size'];v=corners*np.array([w,h,d])+np.array([x-12.2,z-.25,20.2-y]);pos=v[faces].reshape(-1,3);tri=pos.reshape(-1,3,3);norm=np.cross(tri[:,1]-tri[:,0],tri[:,2]-tri[:,0]);norm/=np.linalg.norm(norm,axis=1,keepdims=True);norm=np.repeat(norm,3,axis=0)
 g['meshes'].append({'name':obj['name'],'primitives':[{'attributes':{'POSITION':acc(pos),'NORMAL':acc(norm)},'material':material(obj['color'])}]});g['nodes'].append({'name':obj['name'],'mesh':len(g['meshes'])-1,'extras':{'proposal':True,'kind':obj['kind']}});g['scenes'][0]['nodes'].append(len(g['nodes'])-1)
g['buffers'][0]['byteLength']=len(buf);js=json.dumps(g,separators=(',',':')).encode();js+=b' '*((-len(js))%4);buf+=b'\0'*((-len(buf))%4);(dst/'utah-propuesta.glb').write_bytes(struct.pack('<III',0x46546c67,2,28+len(js)+len(buf))+struct.pack('<II',len(js),0x4e4f534a)+js+struct.pack('<II',len(buf),0x004e4942)+buf)
print('GLB propuesta',len(buf),'bytes')
