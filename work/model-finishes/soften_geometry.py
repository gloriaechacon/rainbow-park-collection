"""Blender finish processing: small real bevels and local contact occlusion.
Keeps named parts, source dimensions, PBR textures and removable-roof metadata.
Writes the same unindexed GLB convention consumed by the website and Cesium.
"""
import bpy, bmesh, json, struct, math
from pathlib import Path
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree

ROOT=Path('work/sites/r15-ocala/dist')

def process(file):
    raw=file.read_bytes();nn=struct.unpack_from('<I',raw,12)[0];g=json.loads(raw[20:20+nn]);buf=bytearray(raw[28+nn:]);stats={'beveled':0,'occlusion_vertices':0}
    def read(i):
        a=g['accessors'][i];v=g['bufferViews'][a['bufferView']];k={'VEC2':2,'VEC3':3,'VEC4':4}[a['type']]
        return np.frombuffer(buf,dtype='<f4',count=a['count']*k,offset=v.get('byteOffset',0)).reshape(-1,k).copy()
    def acc(a,typ):
        a=np.asarray(a,dtype='<f4')
        while len(buf)%4:buf.append(0)
        g['bufferViews'].append({'buffer':0,'byteOffset':len(buf),'byteLength':a.nbytes});buf.extend(a.tobytes())
        g['accessors'].append({'bufferView':len(g['bufferViews'])-1,'componentType':5126,'count':len(a),'type':typ,'min':a.min(0).tolist(),'max':a.max(0).tolist()});return len(g['accessors'])-1
    all_pos=[];all_faces=[];offset=0;records=[]
    for node in g['nodes']:
        name=node['name'].lower();kind=node.get('extras',{}).get('kind','')
        for pr in g['meshes'][node['mesh']]['primitives']:
            material=g['materials'][pr['material']];p=read(pr['attributes']['POSITION']);normal=read(pr['attributes']['NORMAL']);uv=read(pr['attributes']['TEXCOORD_0']) if 'TEXCOORD_0'in pr['attributes'] else None
            opaque=material.get('alphaMode')!='BLEND'
            # Retain architectural shell; soften only manufactured joinery and furniture.
            bevel=opaque and (kind in ['finish-detail','plan-detail','furnishing','furniture','bed','living','dining','kitchen'] or any(w in name for w in ['puerta','mobiliario','cocina','tocador','vanity']))
            if bevel and len(p)<14000:
                mesh=bpy.data.meshes.new('finish');mesh.from_pydata(p.tolist(),[],np.arange(len(p)).reshape(-1,3).tolist());mesh.update()
                if uv is not None:
                    layer=mesh.uv_layers.new(name='UVMap')
                    for loop in mesh.loops:layer.data[loop.index].uv=uv[loop.vertex_index]
                bm=bmesh.new();bm.from_mesh(mesh);bmesh.ops.remove_doubles(bm,verts=list(bm.verts),dist=.00001)
                # Clamp overlaps preserves narrow pulls, panel gaps and source openings.
                edges=[e for e in bm.edges if e.is_manifold and e.calc_face_angle(0)>.35]
                amount=.008 if any(w in name for w in ['sofá','sofa','cama','tapiz','mobiliario']) else .0025
                if edges:bmesh.ops.bevel(bm,geom=edges,offset=amount,segments=2,affect='EDGES',clamp_overlap=True)
                bmesh.ops.triangulate(bm,faces=list(bm.faces));bm.normal_update();bm.to_mesh(mesh);bm.free();mesh.update()
                ps=[];ns=[];us=[]
                for poly in mesh.polygons:
                    for li in poly.loop_indices:
                        ps.append(tuple(mesh.vertices[mesh.loops[li].vertex_index].co));ns.append(tuple(poly.normal))
                        if uv is not None:us.append(tuple(mesh.uv_layers[0].data[li].uv))
                p=np.array(ps);normal=np.array(ns);uv=np.array(us) if us else None;bpy.data.meshes.remove(mesh);stats['beveled']+=1
            # Subdivide visible floor surfaces to keep contact shadow detail under furniture.
            floor=opaque and ('piso'in name or 'pavimento'in name or 'porcelánico'in name or 'concreto sellado'in name)
            if floor:
                triangles=[]
                for j in range(0,len(p),3):
                    stack=[(p[j:j+3],normal[j:j+3],None if uv is None else uv[j:j+3])]
                    while stack:
                        pp,nt,tt=stack.pop();lens=[np.linalg.norm(pp[(k+1)%3]-pp[k]) for k in range(3)];k=int(np.argmax(lens))
                        if lens[k]<.42 or abs(nt[:,1].mean())<.8:triangles.append((pp,nt,tt));continue
                        a=k;b=(k+1)%3;c=(k+2)%3;mid=(pp[a]+pp[b])/2;mn=(nt[a]+nt[b])/2;mt=None if tt is None else (tt[a]+tt[b])/2
                        stack.append((np.array([pp[a],mid,pp[c]]),np.array([nt[a],mn,nt[c]]),None if tt is None else np.array([tt[a],mt,tt[c]])))
                        stack.append((np.array([mid,pp[b],pp[c]]),np.array([mn,nt[b],nt[c]]),None if tt is None else np.array([mt,tt[b],tt[c]])))
                p=np.concatenate([t[0]for t in triangles]);normal=np.concatenate([t[1]for t in triangles]);uv=np.concatenate([t[2]for t in triangles]) if uv is not None else None
            records.append((node,pr,p,normal,uv,opaque))
            if opaque:
                all_pos.extend(p.tolist());all_faces.extend((np.arange(len(p)).reshape(-1,3)+offset).tolist());offset+=len(p)
    tree=BVHTree.FromPolygons(all_pos,all_faces,all_triangles=True)
    # Fixed low-discrepancy hemisphere rays, distance-limited to avoid darkening closed rooms.
    rays=[]
    for k in range(12):
        z=math.sqrt((k+.5)/12);r=math.sqrt(1-z*z);a=k*2.399963;rays.append((r*math.cos(a),r*math.sin(a),z))
    for node,pr,p,n,uv,opaque in records:
        pr['attributes']['POSITION']=acc(p,'VEC3');pr['attributes']['NORMAL']=acc(n,'VEC3')
        if uv is not None:pr['attributes']['TEXCOORD_0']=acc(uv,'VEC2')
        if not opaque:continue
        colors=[];cache={}
        for pos,norm in zip(p,n):
            key=tuple(np.round(np.r_[pos,norm],4))
            if key not in cache:
                nn=Vector(norm);nn.normalize();up=Vector((0,1,0)) if abs(nn.y)<.9 else Vector((1,0,0));u=nn.cross(up).normalized();v=nn.cross(u).normalized();origin=Vector(pos)+nn*.012;blocked=0
                for a,b,c in rays:
                    hit,_,_,dist=tree.ray_cast(origin,u*a+v*b+nn*c,1.15)
                    if hit is not None:blocked+=(1-dist/1.15)**.7
                shade=max(.50,1-blocked/len(rays)*.62);cache[key]=[shade,shade,shade]
            colors.append(cache[key])
        pr['attributes']['COLOR_0']=acc(colors,'VEC3');stats['occlusion_vertices']+=len(cache)
    g['buffers'][0]['byteLength']=len(buf);js=json.dumps(g,separators=(',',':')).encode();js+=b' '*((-len(js))%4);buf+=b'\0'*((-len(buf))%4)
    file.write_bytes(struct.pack('<III',0x46546c67,2,28+len(js)+len(buf))+struct.pack('<II',len(js),0x4e4f534a)+js+struct.pack('<II',len(buf),0x004e4942)+buf)
    print(file,stats,flush=True)

for file in [ROOT/'utah/utah-finished-v4.glb',ROOT/'bell/bell-finished-v4.glb']:process(file)
