"""Reproducible architectural finish pass. Source layouts remain in metres.

Builds real door/panel/hardware geometry, surface-specific PBR and metric UVs.
Finishes are a presentation proposal; input architectural drawings remain authority.
No external texture licensing dependencies. Deterministic procedural PBR assets.
"""
from pathlib import Path
import json, struct, io, copy, math
import numpy as np
from PIL import Image, ImageFilter

ROOT = Path('work/sites/r15-ocala/dist')
OUT = Path('outputs/model-finishes'); OUT.mkdir(exist_ok=True, parents=True)
RNG = np.random.default_rng(141026)

def chamfer_box(center,size,bevel=.0025):
    """Small true chamfer: six faces, twelve edges and eight corner facets."""
    half=np.array(size)/2;b=min(bevel,float(min(half))*.20)
    signs=np.array([[x,y,z] for x in [-1,1] for y in [-1,1] for z in [-1,1]])
    verts=np.array([sign*(half-b+np.eye(3)[axis]*b) for sign in signs for axis in range(3)])
    planes=[np.array(v,float) for v in [(a,b,c)for a in [-1,0,1]for b in [-1,0,1]for c in [-1,0,1]if (a,b,c)!=(0,0,0)]]
    tris=[]
    for normal in planes:
        dots=verts@normal;ids=np.where(abs(dots-dots.max())<1e-8)[0]
        if len(ids)<3:continue
        ps=verts[ids];cc=ps.mean(0);normal/=np.linalg.norm(normal);u=(ps[0]-cc);u/=np.linalg.norm(u);v=np.cross(normal,u)
        angles=np.arctan2((ps-cc)@v,(ps-cc)@u);ps=ps[np.argsort(angles)]
        for j in range(1,len(ps)-1):tris.extend([ps[0],ps[j],ps[j+1]])
    return np.array(tris)+np.array(center)

def rgb(h):
    c = np.array([int(h[i:i+2],16)/255 for i in (1,3,5)])
    return np.where(c<=.04045,c/12.92,((c+.055)/1.055)**2.4).tolist()+[1]

def noise(n, cells):
    im=Image.fromarray(np.uint8(RNG.uniform(0,255,(cells,cells))))
    return np.asarray(im.resize((n,n),Image.Resampling.BICUBIC)).astype(float)/255-.5

def pbr(kind, n=1024):
    y,x=np.mgrid[0:n,0:n]/n; fine=RNG.normal(0,1,(n,n)); low=noise(n,12); mid=noise(n,64)
    h=np.zeros((n,n)); rough=np.full((n,n),.7)
    if kind in ('oak','planks'):
        # Six 200 mm boards, irregular end joints, grain and pores; 1.2 x 2.4 m repeat.
        col=np.floor(x*6).astype(int); xx=x*6-col; yy=(y*2+(col%3)*.327)%1
        var=RNG.uniform(-10,10,(6,3))[col,np.floor((y*2+(col%3)*.327)%3).astype(int)]
        warp=xx+np.sin(y*10+col)*.025+np.sin(y*31+col)*.004
        grain=(np.sin(warp*145+mid*.9)+.45*np.sin(warp*330+low*2))
        pore=np.maximum(0,np.sin(warp*710+mid))**14
        knots=np.exp(-((xx-.39)**2/.024+((y-.34-col*.021)%1)**2/.002))
        tone=grain*2.8-pore*3+var*(1 if kind=='planks' else .15)+low*8+fine*.55-knots*12
        base=np.array([176,143,105]) if kind=='oak' else np.array([185,153,114])
        a=base+tone[:,:,None]*[1,.86,.7]
        h=grain*.00015-pore*.00015+fine*.000035
        if kind=='planks':
            seam=(xx<.007)|(xx>.993)|(yy<.0015)
            a[seam]=[109,90,69];h[seam]=-.0015
        rough=.48+mid*.12+grain*.009
    elif kind in ('limestone','tile'):
        # Four 600 mm tiles in a 1.2 m square, restrained limestone mottling.
        variation=RNG.uniform(-5,5,(2,2))[(y*2).astype(int),(x*2).astype(int)]
        tone=low*15+mid*3+fine*.65+variation
        base=np.array([209,200,184]) if kind=='limestone' else np.array([192,194,189])
        a=base+tone[:,:,None];seam=(x%.5<.0025)|(y%.5<.0025)
        a[seam]=[155,149,137] if kind=='limestone' else [138,143,142]
        h=mid*.00011+fine*.000025;h[seam]=-.0009;rough=.55+low*.15
    elif kind=='stucco':
        a=np.array([232,227,216])+(low*2+mid*2+fine*1.2)[:,:,None]
        h=mid*.00035+fine*.000045;rough=.88+mid*.08
    elif kind=='concrete':
        a=np.array([164,162,153])+(low*18+mid*7+fine*2)[:,:,None]
        specks=RNG.random((n,n))<.016;a[specks]-=23
        h=mid*.0004+fine*.0001;h[specks]-=.0007;rough=.76+low*.1
    elif kind=='roof':
        row=(y*12).astype(int); xx=(x*6+(row%2)*.5)%1
        val=RNG.uniform(-5,5,(12,6))[row,((x*6+(row%2)*.5)%6).astype(int)]
        tone=val+fine*6+mid*4
        a=np.array([69,72,71])+tone[:,:,None]
        seam=(y%(1/12)<.0015)|(xx<.006);a[seam]*=.53
        h=(y%(1/12))*-.028+fine*.00013;h[seam]-=.001;rough=.87+mid*.05
    elif kind=='linen':
        weave=np.sin(x*math.tau*210)*np.cos(y*math.tau*210)
        a=np.array([220,210,192])+(mid*5+weave*3+fine*.7)[:,:,None]
        h=weave*.00016+fine*.000025;rough=.94+mid*.03
    elif kind=='quartz':
        vein=np.exp(-((np.sin(x*13+y*7+low*.5)+np.sin(x*4-y*9))/.07)**2)
        a=np.array([229,225,214])+(low*4+fine*.4-vein*9)[:,:,None]
        h=mid*.00001;rough=.27+low*.03
    else:raise ValueError(kind)
    # Tangent-space normal, physically scaled, OpenGL +Y. UV image rows flip in loader.
    metres={'planks':1.2,'oak':1.2,'roof':2.4,'linen':.7,'stucco':1.2}.get(kind,1.2)
    dx=(np.roll(h,-1,1)-np.roll(h,1,1))*n/metres*.5
    dy=(np.roll(h,-1,0)-np.roll(h,1,0))*n/metres*.5
    normal=np.stack([-dx,dy,np.ones_like(h)],-1);normal/=np.linalg.norm(normal,axis=-1,keepdims=True)
    mr=np.zeros((n,n,3),dtype=np.uint8);mr[:,:,0]=255;mr[:,:,1]=np.clip(rough*255,0,255)
    ims={'color':Image.fromarray(np.uint8(np.clip(a,0,255))), 'normal':Image.fromarray(np.uint8((normal*.5+.5)*255)), 'rough':Image.fromarray(mr)}
    for k,im in ims.items():
        im.save(OUT/f'{kind}-{k}.jpg',quality=93)
    return ims

TEXTURES={k:pbr(k) for k in ['oak','planks','limestone','tile','stucco','concrete','roof','linen','quartz']}

class Model:
    def __init__(self,path):
        raw=path.read_bytes();n=struct.unpack_from('<I',raw,12)[0]
        self.g=json.loads(raw[20:20+n]);self.buf=bytearray(raw[28+n:]);self.groups={};self.tex={}
    def read(self,i):
        a=self.g['accessors'][i];v=self.g['bufferViews'][a['bufferView']];num={'VEC2':2,'VEC3':3,'VEC4':4}[a['type']]
        return np.frombuffer(self.buf,dtype='<f4',offset=v.get('byteOffset',0)+a.get('byteOffset',0),count=a['count']*num).reshape(-1,num).copy()
    def append(self,b):
        while len(self.buf)%4:self.buf.append(0)
        self.g['bufferViews'].append({'buffer':0,'byteOffset':len(self.buf),'byteLength':len(b)});self.buf.extend(b)
        return len(self.g['bufferViews'])-1
    def acc(self,a,typ='VEC3'):
        a=np.asarray(a,dtype='<f4');i=len(self.g['accessors']);self.g['accessors'].append({'bufferView':self.append(a.tobytes()),'componentType':5126,'count':len(a),'type':typ,'min':a.min(0).tolist(),'max':a.max(0).tolist()});return i
    def texture(self,kind,channel):
        key=(kind,channel)
        if key in self.tex:return self.tex[key]
        f=io.BytesIO();TEXTURES[kind][channel].save(f,format='JPEG',quality=94 if channel=='color' else 96)
        self.g['images'].append({'bufferView':self.append(f.getvalue()),'mimeType':'image/jpeg'})
        self.g['textures'].append({'source':len(self.g['images'])-1,'sampler':0});self.tex[key]=len(self.g['textures'])-1
        return self.tex[key]
    def mat(self,name,color='#ffffff',kind=None,rough=.7,metal=0):
        m={'name':name,'doubleSided':True,'pbrMetallicRoughness':{'baseColorFactor':rgb(color),'roughnessFactor':rough,'metallicFactor':metal}}
        if kind:
            m['pbrMetallicRoughness'].update(baseColorTexture={'index':self.texture(kind,'color')},metallicRoughnessTexture={'index':self.texture(kind,'rough')},roughnessFactor=1)
            m['normalTexture']={'index':self.texture(kind,'normal'),'scale':.65}
            m['extras']={'textureKind':kind}
        self.g['materials'].append(m);return len(self.g['materials'])-1
    def pbr_replace(self,index,kind,color='#ffffff'):
        m=self.mat(self.g['materials'][index]['name']+' · 2026 finish',color,kind)
        self.g['materials'][index]=self.g['materials'].pop();return index
    def bounds(self,node):
        p=np.concatenate([self.read(pr['attributes']['POSITION']) for pr in self.g['meshes'][node['mesh']]['primitives']]);return p.min(0),p.max(0)
    def assign(self,node,mat):
        for pr in self.g['meshes'][node['mesh']]['primitives']:pr['material']=mat
    def add(self,name,p,mat,extras=None):
        p=np.array(p);tr=p.reshape(-1,3,3);nr=np.cross(tr[:,1]-tr[:,0],tr[:,2]-tr[:,0]);norm=np.linalg.norm(nr,axis=1);ok=norm>1e-10;p=tr[ok].reshape(-1,3);nr=np.repeat(nr[ok]/norm[ok,None],3,0)
        key=(name,mat);group=self.groups.setdefault(key,[[],[],extras or {'kind':'finish-detail','proposal':True}]);group[0].extend(p);group[1].extend(nr)
    def box(self,name,c,s,mat,angle=0,extras=None):
        v=chamfer_box([0,0,0],s)
        a=math.radians(angle);v[:,[0,2]]=v[:,[0,2]]@np.array([[math.cos(a),math.sin(a)],[-math.sin(a),math.cos(a)]])
        v+=c;self.add(name,v,mat,extras)
    def finish(self,path):
        # Soften original box-built furniture and cabinet fronts without modifying walls.
        for node in self.g['nodes']:
            kind=node.get('extras',{}).get('kind','');name=node['name'].lower()
            if not (kind in ['furniture','furnishing','living','bedroom','dining','plan-detail'] or any(t in name for t in ['mobiliario','sofá','cama','encimera','tirador'])):continue
            for pr in self.g['meshes'][node['mesh']]['primitives']:
                pos=self.read(pr['attributes']['POSITION'])
                if len(pos)%36:continue
                pp=[]
                for v in pos.reshape(-1,36,3):
                    if all(len(np.unique(np.round(v[:,j],5)))==2 for j in range(3)):
                        lo,hi=v.min(0),v.max(0);pp.append(chamfer_box((lo+hi)/2,hi-lo,.009 if any(t in name for t in ['sofá','cama','mobiliario']) else .0025))
                    else:pp.append(v)
                pp=np.concatenate(pp);tr=pp.reshape(-1,3,3);nn=np.cross(tr[:,1]-tr[:,0],tr[:,2]-tr[:,0]);nn/=np.maximum(np.linalg.norm(nn,axis=1,keepdims=True),1e-10)
                pr['attributes']={'POSITION':self.acc(pp),'NORMAL':self.acc(np.repeat(nn,3,0))}
        for (name,mat),(p,n,ex) in self.groups.items():
            self.g['meshes'].append({'name':name,'primitives':[{'attributes':{'POSITION':self.acc(p),'NORMAL':self.acc(n)},'material':mat}]})
            self.g['nodes'].append({'name':name,'mesh':len(self.g['meshes'])-1,'extras':ex})
        # Reproject all PBR textures metrically, never stretch one bitmap across a house.
        for node in self.g['nodes']:
            for pr in self.g['meshes'][node['mesh']]['primitives']:
                kind=self.g['materials'][pr['material']].get('extras',{}).get('textureKind')
                if not kind:continue
                p=self.read(pr['attributes']['POSITION']);n=self.read(pr['attributes']['NORMAL']);ax=np.argmax(abs(n),axis=1)
                uv=np.c_[np.where(ax==0,p[:,2],p[:,0]),np.where(ax==1,p[:,2],p[:,1])]
                scale={'planks':[1.2,2.4],'oak':[1.2,2.4],'roof':[2.4,1.8],'linen':[.7,.7]}.get(kind,[1.2,1.2]);uv/=scale
                pr['attributes']['TEXCOORD_0']=self.acc(uv,'VEC2')
        # Compact only referenced data, dropping old revisions' abandoned image/vertex buffers.
        old=self.g;new={k:copy.deepcopy(old[k]) for k in ['asset','samplers']};new.update(scene=0,scenes=[{'nodes':[]}],nodes=[],meshes=[],materials=[],textures=[],images=[],accessors=[],bufferViews=[],buffers=[{}]);out=bytearray();maps={k:{} for k in ['materials','textures','images','accessors','bufferViews']}
        def cp(kind,i):
            if i in maps[kind]:return maps[kind][i]
            o=copy.deepcopy(old[kind][i]);j=len(new[kind]);maps[kind][i]=j;new[kind].append(o)
            if kind=='bufferViews':
                while len(out)%4:out.append(0)
                s=o.get('byteOffset',0);o['byteOffset']=len(out);out.extend(self.buf[s:s+o['byteLength']])
            elif kind in ('accessors','images'):o['bufferView']=cp('bufferViews',o['bufferView'])
            elif kind=='textures':o['source']=cp('images',o['source'])
            elif kind=='materials':
                for p in [o,o.get('pbrMetallicRoughness',{})]:
                    for k,v in p.items():
                        if k.endswith('Texture') and isinstance(v,dict):v['index']=cp('textures',v['index'])
            return j
        for node in old['nodes']:
            node=copy.deepcopy(node);mesh=copy.deepcopy(old['meshes'][node['mesh']]);node['mesh']=len(new['meshes'])
            for p in mesh['primitives']:
                p['material']=cp('materials',p['material']);p['attributes']={k:cp('accessors',v) for k,v in p['attributes'].items()}
            new['meshes'].append(mesh);new['scenes'][0]['nodes'].append(len(new['nodes']));new['nodes'].append(node)
        new['asset']['generator']='Rainbow Park Collection · architectural finishes v4';new['buffers'][0]['byteLength']=len(out)
        js=json.dumps(new,separators=(',',':')).encode();js+=b' '*((-len(js))%4);out+=b'\0'*((-len(out))%4)
        path.write_bytes(struct.pack('<III',0x46546c67,2,28+len(js)+len(out))+struct.pack('<II',len(js),0x4e4f534a)+js+struct.pack('<II',len(out),0x004e4942)+out)
        print(path,round(path.stat().st_size/1e6,2),'MB',len(new['nodes']),'nodes')

def palette(m):
    return {k:m.mat('RPC · '+name,color,kind,rough,metal) for k,name,color,kind,rough,metal in [
        ('door','Puerta lacada arena','#c1b49d',None,.46,0),
        ('trim','Molduras blanco cálido','#e9e5dc',None,.52,0),
        ('garage','Garaje · acero pintado greige','#a6aaa3',None,.38,.15),
        ('panel','Garaje · panel interior','#b9bdb6',None,.43,.08),
        ('hardware','Herrajes grafito','#353b3a',None,.27,.75),
        ('gasket','Burletes y juntas','#333732',None,.92,0),
        ('oak','Carpintería roble','#ffffff','oak',.5,0),
        ('floor','Piso roble 20 cm','#ffffff','planks',.5,0),
        ('stone','Porcelánico caliza 60 cm','#ffffff','limestone',.6,0),
        ('tile','Piso baños 60 cm','#ffffff','tile',.55,0),
        ('concrete','Concreto pulido','#ffffff','concrete',.7,0),
        ('quartz','Cuarzo satinado','#ffffff','quartz',.3,0),
        ('ceiling','Cielo raso blanco','#ebe9e3',None,.95,0),
    ]}

def garage(m,c,width,height,p):
    x,z=c; name='Garaje · paneles seccionales y herrajes'
    m.box(name,[x,height/2,z],[width,.0+height,.064],p['gasket'])
    rows=4;cols=4 if width<2.7 else 5
    for row in range(rows):
        cy=(row+.5)*height/rows
        m.box(name,[x,cy,z+.039],[width-.025,height/rows-.012,.024],p['garage'])
        for col in range(cols):
            cx=x-width/2+(col+.5)*width/cols
            m.box(name,[cx,cy,z+.054],[width/cols-.075,height/rows-.095,.018],p['panel'])
        # visible interior reinforcing rails
        m.box(name,[x,cy-height/rows*.44,z-.056],[width-.04,.024,.025],p['hardware'])
    for side in [-1,1]:
        m.box(name,[x+side*(width/2+.043),height/2,z+.08],[.085,height+.10,.075],p['trim'])
        m.box(name,[x+side*(width/2-.05),height/2,z-.09],[.035,height,.03],p['hardware'])
    m.box(name,[x,height+.05,z+.08],[width+.17,.10,.075],p['trim'])
    m.box(name,[x,.055,z+.07],[width,.035,.032],p['gasket'])
    for dx in [-.21,.21]:m.box(name,[x+dx,.85,z+.086],[.13,.022,.026],p['hardware'])

def door_details(m,c,width,height,axis,p,label='Puerta interior',wood=False,rotation=None):
    x,z=c;angle=(90 if axis=='z' else 0) if rotation is None else rotation;mat=p['oak'] if wood else p['door'];r=math.radians(angle)
    def b(u,y,v,w,h,d,material):
        cx=x+u*math.cos(r)-v*math.sin(r);cz=z+u*math.sin(r)+v*math.cos(r)
        m.box(label,[cx,y,cz],[w,h,d],material,angle)
    # Leaf with a small undercut, two-sided recessed shaker panels and working-scale handle.
    b(0,height/2+.012,0,width,height-.024,.038,mat)
    for side in [-1,1]:
        for cy,hh in [(height*.26,height*.34),(height*.72,height*.43)]:
            b(0,cy,side*.025,width-.16,hh,.012,mat)
        b(width*.35,1.0,side*.036,.045,.13,.018,p['hardware'])
        b(width*.35-.037,1.0,side*.058,.12,.018,.025,p['hardware'])
    for y in [.22,height*.5,height-.22]:b(-width/2+.014,y,0,.018,.075,.059,p['hardware'])

def utah():
    m=Model(ROOT/'utah/utah-plan-v3.glb');p=palette(m)
    for i,kind in [(8,'stucco'),(13,'roof'),(9,'oak'),(25,'planks'),(26,'linen'),(29,'linen'),(27,'oak'),(30,'oak'),(31,'oak'),(34,'oak'),(35,'limestone'),(40,'linen'),(41,'linen'),(42,'linen'),(47,'linen'),(43,'oak'),(44,'oak'),(46,'oak'),(48,'oak'),(51,'limestone'),(55,'oak'),(62,'quartz'),(63,'concrete')]:m.pbr_replace(i,kind)
    # Material <auto>3 was stucco on every leaf and jamb, making doors disappear into walls.
    for i in [1,10,12,17,23,59]:
        m.g['materials'][i]=copy.deepcopy(m.g['materials'][p['trim']]);m.g['materials'][i]['name']='Utah · carpintería y aleros '+str(i)
    for i in [0,3,5,19]:
        m.g['materials'][i]=copy.deepcopy(m.g['materials'][p['hardware']])
    for i in [4,18,20]:
        m.g['materials'][i]={'name':'Utah · vidrio claro','alphaMode':'BLEND','doubleSided':True,'pbrMetallicRoughness':{'baseColorFactor':rgb('#adc3c7')[:3]+[.20],'roughnessFactor':.10,'metallicFactor':.12}}
    nodes={n.get('extras',{}).get('sourceNode'):n for n in m.g['nodes'] if 'sourceNode'in n.get('extras',{})}
    # New garage faces occupy the source opening (8 ft wide). Original white mesh removed.
    m.g['nodes'].remove(nodes[1]);garage(m,[-5.283,6.34],2.4384,2.035,p)
    leaves=[115,119,123,127,131,135,144,148,152,156,160,164]
    for i in leaves:
        node=nodes[i];lo,hi=m.bounds(node);s=hi-lo;c=(lo+hi)/2;axis='x' if s[0]>s[2] else 'z';w=max(s[0],s[2]);m.g['nodes'].remove(node)
        door_details(m,[c[0],c[2]],float(w),float(s[1]),axis,p,'Utah · puerta '+str(i),wood=(i==135))
    # Original main door retains its glass slots and exact dimensions; add exterior casing.
    for xx in [-.215,.72]:m.box('Utah · recercado entrada',[xx,1.05,5.045],[.07,2.12,.065],p['trim'])
    m.box('Utah · dintel entrada',[.2525,2.08,5.045],[1.005,.08,.065],p['trim'])
    # Slab top is real internal floor, previously using a generic concrete material.
    slab=nodes[73]
    for pr in m.g['meshes'][slab['mesh']]['primitives']:
        pos=m.read(pr['attributes']['POSITION']);tr=pos.reshape(-1,3,3);is_top=np.all(abs(tr[:,:,1])<1e-4,axis=1)
        interior=is_top & (tr[:,:,0].mean(1)>-6.97) & (tr[:,:,2].mean(1)<5.66)
        if interior.any():
            pp=tr[interior].copy();pp[:,:,1]=.005;m.add('Utah · pavimento área social',pp.reshape(-1,3),p['stone'],{'kind':'floor-finish','proposal':True})
    for node in m.g['nodes']:
        name=node['name']
        if 'piso roble'in name:m.assign(node,p['floor'])
        if 'porcelánico'in name:m.assign(node,p['tile'])
        if 'concreto sellado'in name:m.assign(node,p['concrete'])
        if 'cielo raso'in name:m.assign(node,p['ceiling'])
        if 'encimera'in name:m.assign(node,p['quartz'])
    # Replace solid chair blocks with seats, backs and four legs at the original positions.
    for node in list(m.g['nodes']):
        if 'silla comedor' not in node['name'].lower():continue
        lo,hi=m.bounds(node);cx,_,cz=(lo+hi)/2;m.g['nodes'].remove(node)
        back=-1 if cx<.15 else 1
        m.box('Utah · sillas tapizadas',[cx,.455,cz],[.46,.075,.47],47)
        m.box('Utah · sillas tapizadas',[cx+back*.20,.705,cz],[.06,.46,.47],47)
        for xx in [-.175,.175]:
            for zz in [-.18,.18]:m.box('Utah · patas sillas',[cx+xx,.215,cz+zz],[.032,.43,.032],p['oak'])
    # Upholstery arms and feet give the living room sofa a readable silhouette.
    for zz in [1.93,4.23]:m.box('Utah · brazos sofá',[-2.99,.57,zz],[.88,.47,.13],40)
    for xx in [-3.64,-2.65]:
        for zz in [2.10,4.05]:m.box('Utah · patas sofá',[xx,.065,zz],[.05,.13,.05],p['hardware'])
    # Baseboards follow the actual wall mesh bottom edges, including returns and openings.
    for i,node in nodes.items():
        if not (74<=i<=111 or 136<=i<=140):continue
        for pr in m.g['meshes'][node['mesh']]['primitives']:
            pos=m.read(pr['attributes']['POSITION']).reshape(-1,3,3);seen=set()
            for tr in pos:
                nr=np.cross(tr[1]-tr[0],tr[2]-tr[0]);ll=np.linalg.norm(nr)
                if ll<1e-9:continue
                nr/=ll
                if abs(nr[1])>.05:continue
                for a,b in [(tr[0],tr[1]),(tr[1],tr[2]),(tr[2],tr[0])]:
                    if max(abs(a[1]),abs(b[1]))>.001:continue
                    length=np.linalg.norm(b-a)
                    if length<.1:continue
                    key=tuple(np.round(np.r_[np.minimum(a,b),np.maximum(a,b)],3))
                    if key in seen:continue
                    seen.add(key);c=(a+b)/2+nr*.009;c[1]=.058;size=np.maximum(abs(b-a),[.018,.116,.018]);size[1]=.116
                    m.box('Utah · rodapiés continuos',c,size,p['trim'])
    m.finish(ROOT/'utah/utah-finished-v4.glb')

def bell():
    m=Model(ROOT/'bell/bell.glb');p=palette(m)
    for i,kind in [(0,'stucco'),(1,'roof'),(2,'oak'),(3,'limestone'),(4,'linen'),(9,'concrete'),(11,'quartz')]:m.pbr_replace(i,kind)
    for node in list(m.g['nodes']):
        name=node['name']
        if name.startswith(('47 ','46 ')):m.g['nodes'].remove(node)
    garage(m,[(43.667-25)*.3048,(29+4/12-(29+4/12+5)/2)*.3048-.05],10*.3048,7*.3048,p)
    # Real leaf thickness, panels and handles, hinged at the actual wall opening.
    for i,(x,v,w,axis,angle) in enumerate([(10.583,10.833,2.833,'x',-70),(12.333,11,3,'z',70),(10.583,18.333,2.833,'x',70),(8.5,14.75,2.5,'z',60),(25.667,18.833,3,'z',-65),(27.417,16.667,2.667,'x',-55),(36,16.667,2.667,'x',-60),(37.667,4.667,3,'z',70),(42.667,7.833,3,'x',-70)]):
        cx=(x-25)*.3048;cz=(v-(29+4/12+5)/2)*.3048;w*=.3048;height=7*.3048
        for side in [-1,1]:
            m.box('Bell · marcos puertas interiores',[cx+(side*(w/2+.03) if axis=='x' else 0),height/2,cz+(side*(w/2+.03) if axis=='z' else 0)],[.065,height+.045,.095] if axis=='x' else [.095,height+.045,.065],p['trim'])
        m.box('Bell · marcos puertas interiores',[cx,height+.03,cz],[w+.12,.065,.095] if axis=='x' else [.095,.065,w+.12],p['trim'])
        theta=angle+(90 if axis=='z' else 0);r=math.radians(theta);hx=cx-(w/2 if axis=='x' else 0);hz=cz-(w/2 if axis=='z' else 0)
        door_details(m,[hx+w/2*math.cos(r),hz+w/2*math.sin(r)],w,height,axis,p,'Bell · puerta interior '+str(i),rotation=theta)
    # Bedroom overlays make the floor schedule visibly legible in the cutaway and interior tour.
    def floor(label,x0,x1,v0,v1,mat):
        m.box(label,[((x0+x1)/2-25)*.3048,.018,((v0+v1)/2-(29+4/12+5)/2)*.3048],[(x1-x0)*.3048,.018,(v1-v0)*.3048],mat,extras={'kind':'floor-finish','proposal':True})
    floor('Bell · piso roble dormitorio 2',.68,12.15,.68,10.66,p['floor'])
    floor('Bell · piso roble dormitorio 3',.68,12.15,18.50,28.65,p['floor'])
    floor('Bell · piso roble suite',25.84,37.46,16.84,28.65,p['floor'])
    floor('Bell · piso baño principal',32.02,37.45,7.85,16.48,p['tile'])
    floor('Bell · piso baño secundario',.68,8.32,11.02,15.98,p['tile'])
    floor('Bell · piso vestidor',25.85,31.65,9.85,16.48,p['floor'])
    # Closet sliding panels were absent from the initial reconstruction.
    door_details(m,[(12.333-25)*.3048,(4.75-(29+4/12+5)/2)*.3048],4*.3048,7*.3048,'z',p,'Bell · closet dormitorio 2')
    door_details(m,[(4.25-25)*.3048,(18.333-(29+4/12+5)/2)*.3048],6.5*.3048,7*.3048,'x',p,'Bell · closet dormitorio 3')
    m.finish(ROOT/'bell/bell-finished-v4.glb')

if __name__=='__main__':
    utah();bell()
