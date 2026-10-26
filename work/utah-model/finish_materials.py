"""PBR finish proposal, keeping the architectural shell and metric scale intact."""
from pathlib import Path
import json,struct,io,collections
import numpy as np
from PIL import Image,ImageDraw,ImageFilter
root=Path('work/sites/r15-ocala/dist/utah');raw=(root/'utah-propuesta.glb').read_bytes();n=struct.unpack_from('<I',raw,12)[0];g=json.loads(raw[20:20+n]);buf=bytearray(raw[28+n:]);rng=np.random.default_rng(24)
def append(data):
 while len(buf)%4:buf.append(0)
 i=len(g['bufferViews']);g['bufferViews'].append({'buffer':0,'byteOffset':len(buf),'byteLength':len(data)});buf.extend(data);return i
def accessor(a,typ):
 a=np.asarray(a,dtype='<f4');i=append(a.tobytes());g['accessors'].append({'bufferView':i,'componentType':5126,'count':len(a),'type':typ,'min':a.min(axis=0).tolist(),'max':a.max(axis=0).tolist()});return len(g['accessors'])-1
def readacc(i):
 a=g['accessors'][i];v=g['bufferViews'][a['bufferView']];return np.frombuffer(buf,dtype='<f4',offset=v.get('byteOffset',0)+a.get('byteOffset',0),count=a['count']*{'VEC2':2,'VEC3':3}[a['type']]).reshape(a['count'],-1).copy()
def tex(im):
 f=io.BytesIO();im.save(f,format='PNG',optimize=True);v=append(f.getvalue());g['images'].append({'bufferView':v,'mimeType':'image/png'});g['textures'].append({'source':len(g['images'])-1,'sampler':0});return len(g['textures'])-1
def texture_set(kind,size=512):
 y,x=np.mgrid[:size,:size];noise=rng.normal(0,1,(size,size));h=np.zeros((size,size));rough=np.full((size,size),220.)
 if kind=='roof':
  rows=8;rh=size//rows;cw=size//6;row=y//rh;col=((x+(row%2)*cw//2)//cw)%6;variation=rng.uniform(-4,4,(rows,6));base=69+variation[row,col]+noise*4;seams=(y%rh<3)|((x+(row%2)*cw//2)%cw<2);base[seams]-=24;h=(y%rh)/rh*.25+noise*.035;h[seams]=-.3;rgb=np.stack([base*.93,base*.99,base],axis=-1);rough[:]=205
 elif kind=='stucco':
  base=225+noise*3;rgb=np.stack([base+7,base+3,base-7],axis=-1);h=noise*.025
 elif kind=='wood':
  grain=np.sin(x*.55+np.sin(y*.008)*.4)+np.sin(x*1.3+np.sin(y*.01)*.1)*.4;knots=np.sin(x*.04)*2;base=grain*2+knots+noise*.7;rgb=np.stack([167+base,133+base*.86,91+base*.68],axis=-1);h=grain*.006;rough[:]=160
 elif kind=='stone':
  seams=(x%(size//4)<2)|(y%(size//4)<2);base=207+noise*3+np.sin(x*.06+y*.02)*2;base[seams]=171;rgb=np.stack([base+9,base+7,base],axis=-1);h=noise*.01;h[seams]=-.13;rough[:]=215
 else:
  weave=np.sin(x*np.pi)*.05+np.cos(y*np.pi)*.05;base=218+noise*2;rgb=np.stack([base+8,base+5,base],axis=-1);h=weave+noise*.018
 dx=(np.roll(h,-1,1)-np.roll(h,1,1))*1.7;dy=(np.roll(h,-1,0)-np.roll(h,1,0))*1.7;norm=np.stack([-dx,-dy,np.ones_like(h)],axis=-1);norm/=np.linalg.norm(norm,axis=-1,keepdims=True)
 normal=Image.fromarray(np.uint8(np.clip((norm*.5+.5)*255,0,255)));mr=np.zeros((size,size,3),dtype='uint8');mr[:,:,1]=np.clip(rough,0,255);mr[:,:,0]=255
 return {'base':tex(Image.fromarray(np.uint8(np.clip(rgb,0,255)))),'normal':tex(normal),'rough':tex(Image.fromarray(mr))}
sets={name:texture_set(name) for name in ['roof','stucco','wood','stone','linen']}
kind_by_mat={}
for i,m in enumerate(g['materials']):
 name=m['name'];p=m['pbrMetallicRoughness'];kind=None
 if 'Roofing' in name:kind='roof'
 elif any(k in name for k in ['M00','WhiteSmoke','Muros','<auto>']):kind='stucco'
 elif name=='[Color A04]' or name in ['Propuesta #ae9473','Propuesta #a28c6c','Propuesta #b6a17e','Propuesta #ad9572','Propuesta #b49a77','Propuesta #a08a69','Propuesta #ae9875','Propuesta #b39b78','Propuesta #bca483','Propuesta #927353']:kind='wood'
 elif 'Concrete' in name or name in ['Propuesta #eee9db','Propuesta #e8e4d8','Propuesta #f2efe6']:kind='stone'
 elif name in ['Propuesta #e8dfcb','Propuesta #f1ebdf']:kind='linen'
 if kind:
  t=sets[kind];p['baseColorFactor']=[1,1,1,1];p['baseColorTexture']={'index':t['base']};p['metallicRoughnessTexture']={'index':t['rough']};p['roughnessFactor']=1;p['metallicFactor']=0;m['normalTexture']={'index':t['normal'],'scale':.5 if kind=='stucco' else .75};kind_by_mat[i]=kind
 if 'Ventana' in name or 'Aluminum' in name or 'Color M08' in name:
  p.pop('baseColorTexture',None);p['baseColorFactor']=[.06,.075,.065,1];p['metallicFactor']=.65;p['roughnessFactor']=.3
 if m.get('alphaMode')=='BLEND':p['baseColorFactor']=[.44,.60,.62,.46];p['metallicFactor']=.25;p['roughnessFactor']=.1
for node in g['nodes']:
 if node.get('extras',{}).get('sourceNode')==214:
  for primitive in g['meshes'][node['mesh']]['primitives']:primitive['material']=9
# Consistent metric UVs; per-face projections retain roof pitch and wall surface directions.
for mesh in g['meshes']:
 for pr in mesh['primitives']:
  kind=kind_by_mat.get(pr['material'])
  if not kind:continue
  pos=readacc(pr['attributes']['POSITION']);norm=readacc(pr['attributes']['NORMAL']);axis=np.argmax(np.abs(norm),axis=1);uv=np.zeros((len(pos),2));uv[:,0]=np.where(axis==0,pos[:,2],pos[:,0]);uv[:,1]=np.where(axis==1,pos[:,2],pos[:,1]);scale={'roof':2.1,'stucco':1.3,'wood':.85,'stone':2.4,'linen':.45}[kind];uv/=scale;pr['attributes']['TEXCOORD_0']=accessor(uv,'VEC2')
def material(name,color,rough=.8):
 g['materials'].append({'name':name,'pbrMetallicRoughness':{'baseColorFactor':color,'metallicFactor':0,'roughnessFactor':rough},'doubleSided':True});return len(g['materials'])-1
leaf=[material('Vegetación propuesta '+str(i),c) for i,c in enumerate([[.018,.06,.009,1],[.038,.09,.015,1],[.065,.13,.028,1]])]
trim=material('Remates de cubierta marfil',[.76,.74,.65,1]);soil=material('Sustrato de jardineras',[.065,.042,.026,1]);lamp=material('Aplique bronce',[.045,.055,.045,1],.3)
def mesh(name,pos,normal,matid,kind='detail'):
 g['meshes'].append({'name':name,'primitives':[{'attributes':{'POSITION':accessor(pos,'VEC3'),'NORMAL':accessor(normal,'VEC3')},'material':matid}]});g['nodes'].append({'name':name,'mesh':len(g['meshes'])-1,'extras':{'proposal':True,'kind':kind}});g['scenes'][0]['nodes'].append(len(g['nodes'])-1)
corn=np.array([[-1,-1,-1],[1,-1,-1],[1,1,-1],[-1,1,-1],[-1,-1,1],[1,-1,1],[1,1,1],[-1,1,1]],float)/2
faces=np.array([[0,2,1],[0,3,2],[4,5,6],[4,6,7],[0,1,5],[0,5,4],[3,7,6],[3,6,2],[0,4,7],[0,7,3],[1,2,6],[1,6,5]])
def box(name,center,size,matid):
 v=corn*np.array(size)+np.array(center);pos=v[faces].reshape(-1,3);t=pos.reshape(-1,3,3);nr=np.cross(t[:,1]-t[:,0],t[:,2]-t[:,0]);nr/=np.linalg.norm(nr,axis=1,keepdims=True);mesh(name,pos,np.repeat(nr,3,axis=0),matid)
def sphere(name,center,scale,matid):
 v=[]
 for j in range(9):
  for i in range(13):
   ph=j*np.pi/8;th=i*2*np.pi/12;v.append([np.sin(ph)*np.cos(th),np.cos(ph),np.sin(ph)*np.sin(th)])
 v=np.array(v);fs=[]
 for j in range(8):
  for i in range(12):
   a=j*13+i;fs.extend([[a,a+13,a+1],[a+1,a+13,a+14]])
 fs=np.array(fs);mesh(name,(v*np.array(scale)+center)[fs].reshape(-1,3),v[fs].reshape(-1,3),matid,'landscape')
# Plant directly in the six existing proposed planters. Added geometry is clearly proposed.
for k,(x,y) in enumerate([(9.3,13.6),(10.3,13.6),(14.7,12.3),(15.7,12.3),(18.3,13.05),(19.3,13.05)]):
 cx=x-12.2;cz=20.2-y;box('Sustrato jardinera '+str(k),[cx,.20,cz],[.72,.035,.6],soil)
 for j in range(15):
  a=j*2.4;r=.22*np.sqrt((j+1)/15);sphere('Follaje '+str(k)+'-'+str(j),[cx+r*np.cos(a),.32+rng.uniform(.0,.30),cz+r*np.sin(a)],[.16,.22,.15],leaf[j%3])
# Thin edge finish on horizontal roof boundaries, preserving the actual roof outline.
roof=next(node for node in g['nodes'] if node.get('extras',{}).get('sourceNode')==165);edges=collections.Counter()
for pr in g['meshes'][roof['mesh']]['primitives']:
 pos=readacc(pr['attributes']['POSITION']).reshape(-1,3,3)
 for tr in pos:
  for a,b in [(tr[0],tr[1]),(tr[1],tr[2]),(tr[2],tr[0])]:
   if abs(a[1]-b[1])<.003 and a[1]<3.0:edges[tuple(sorted([tuple(np.round(a,4)),tuple(np.round(b,4))]))]+=1
for i,((a,b),count) in enumerate(edges.items()):
 a=np.array(a);b=np.array(b);d=b-a
 if count!=1 or np.linalg.norm(d)<.5:continue
 if abs(d[0])<.01 or abs(d[2])<.01:box('Remate alero '+str(i),(a+b)/2-np.array([0,.045,0]),[max(abs(d[0]),.045),.085,max(abs(d[2]),.045)],trim)
# Architectural light fixtures beside the entry, scale in metres.
for x in [10.95,12.85]:box('Aplique exterior',[x-12.2,1.9,20.2-15.18],[.085,.32,.11],lamp)
g['asset']['generator']='Rainbow Park · Utah finish proposal v2';g['buffers'][0]['byteLength']=len(buf);js=json.dumps(g,separators=(',',':')).encode();js+=b' '*((-len(js))%4);buf+=b'\0'*((-len(buf))%4);(root/'utah-propuesta-v2.glb').write_bytes(struct.pack('<III',0x46546c67,2,28+len(js)+len(buf))+struct.pack('<II',len(js),0x4e4f534a)+js+struct.pack('<II',len(buf),0x004e4942)+buf)
print('PBR model generated:',len(g['nodes']),'nodes,',round(len(buf)/1e6,1),'MB')
