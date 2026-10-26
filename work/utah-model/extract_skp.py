import ctypes as c, json, os, time
from pathlib import Path
A=c.CDLL('/Applications/Maxon Cinema 4D 2024/resource/modules/io_skp/Framework/SketchUpAPI.framework/Versions/A/SketchUpAPI')
Ref=c.c_void_p; Size=c.c_size_t
class V(c.Structure): _fields_=[('x',c.c_double),('y',c.c_double),('z',c.c_double)]
class Color(c.Structure): _fields_=[('r',c.c_ubyte),('g',c.c_ubyte),('b',c.c_ubyte),('a',c.c_ubyte)]
class Transform(c.Structure): _fields_=[('v',c.c_double*16)]
def call(name,*args):return getattr(A,name)(*args)
def ref(name,*args):
 r=Ref();result=call(name,*args,c.byref(r));return r if result==0 else Ref()
def convert(name,r):
 f=getattr(A,name);f.restype=Ref;return Ref(f(r))
def string(name,r):
 s=ref('SUStringCreate');call(name,r,c.byref(s));n=Size();call('SUStringGetUTF8Length',s,c.byref(n));b=c.create_string_buffer(n.value+1);call('SUStringGetUTF8',s,n.value+1,b,c.byref(n));call('SUStringRelease',c.byref(s));return b.value.decode('utf-8',errors='replace')
def items(prefix,kind,r):
 n=Size();call(prefix+'GetNum'+kind,r,c.byref(n));out=(Ref*n.value)();call(prefix+'Get'+kind,r,n.value,out,c.byref(n));return [Ref(out[i]) for i in range(n.value)]
A.SUInitialize();model=ref('SUModelCreateFromFile',b'/Users/robertochacon/Downloads/kimsa-UTAH ANEXO.skp') if False else Ref()
assert call('SUModelCreateFromFile',c.byref(model),b'/Users/robertochacon/Downloads/kimsa-UTAH ANEXO.skp')==0
out=Path(__file__).parent;materials={};geometries={};nodes=[];stats={'faces':0,'triangles':0};t0=time.time()
def material(r):
 if not r.value:return None
 k=str(r.value)
 if k in materials:return k
 color=Color(220,220,210,255);call('SUMaterialGetColor',r,c.byref(color));alpha=c.c_double(1);call('SUMaterialGetOpacity',r,c.byref(alpha));use=c.c_bool();call('SUMaterialGetUseOpacity',r,c.byref(use));tex=ref('SUMaterialGetTexture',r);path=None
 if tex.value:
  path=f'textures/{len(materials):03}.png';code=call('SUTextureWriteToFile',tex,str(out/path).encode());path=path if code==0 else None
 materials[k]={'name':string('SUMaterialGetName',r),'color':[color.r/255,color.g/255,color.b/255,alpha.value if use.value else 1],'texture':path};return k
def props(draw):
 hidden=c.c_bool();call('SUDrawingElementGetHidden',draw,c.byref(hidden));layer=ref('SUDrawingElementGetLayer',draw);vis=c.c_bool(True);call('SULayerGetVisibility',layer,c.byref(vis));return {'hidden':hidden.value,'layer':string('SULayerGetName',layer),'layerVisible':vis.value,'material':material(ref('SUDrawingElementGetMaterial',draw))}
def geometry(ent):
 key=str(ent.value)
 if key in geometries:return key
 vertices=[];uvs=[];triangles=[];mat=[];facehidden=[]
 for face in items('SUEntities','Faces',ent):
  mesh=Ref();err=call('SUMeshHelperCreate',c.byref(mesh),face)
  if err:continue
  nv=Size();nt=Size();call('SUMeshHelperGetNumVertices',mesh,c.byref(nv));call('SUMeshHelperGetNumTriangles',mesh,c.byref(nt));v=(V*nv.value)();uv=(V*nv.value)();idx=(Size*(nt.value*3))();n=Size();call('SUMeshHelperGetVertices',mesh,nv.value,v,c.byref(n));call('SUMeshHelperGetFrontSTQCoords',mesh,nv.value,uv,c.byref(n));call('SUMeshHelperGetVertexIndices',mesh,nt.value*3,idx,c.byref(n));offset=len(vertices)
  vertices.extend([[p.x*.0254,p.y*.0254,p.z*.0254] for p in v]);uvs.extend([[p.x/(p.z or 1),p.y/(p.z or 1)] for p in uv]);mk=material(ref('SUFaceGetFrontMaterial',face));mk=mk or material(ref('SUFaceGetBackMaterial',face));fp=props(convert('SUFaceToDrawingElement',face));hidden=fp['hidden'] or not fp['layerVisible']
  for i in range(nt.value):triangles.append([offset+idx[3*i],offset+idx[3*i+1],offset+idx[3*i+2]]);mat.append(mk);facehidden.append(hidden)
  stats['faces']+=1;stats['triangles']+=nt.value;call('SUMeshHelperRelease',c.byref(mesh))
 geometries[key]={'vertices':vertices,'uvs':uvs,'triangles':triangles,'materials':mat,'hidden':facehidden}
 return key
def walk(ent,name,parent=None,transform=None,pr=None,depth=0):
 node={'name':name,'parent':parent,'transform':transform,'props':pr or {},'geometry':geometry(ent)};i=len(nodes);nodes.append(node)
 for group in items('SUEntities','Groups',ent):
  xf=Transform();call('SUGroupGetTransform',group,c.byref(xf));matrix=list(xf.v);matrix[12:15]=[v*.0254 for v in matrix[12:15]];walk(ref('SUGroupGetEntities',group),string('SUGroupGetName',group) or 'Group',i,matrix,props(convert('SUGroupToDrawingElement',group)),depth+1)
 for inst in items('SUEntities','Instances',ent):
  definition=ref('SUComponentInstanceGetDefinition',inst);xf=Transform();call('SUComponentInstanceGetTransform',inst,c.byref(xf));matrix=list(xf.v);matrix[12:15]=[v*.0254 for v in matrix[12:15]];walk(ref('SUComponentDefinitionGetEntities',definition),string('SUComponentInstanceGetName',inst) or string('SUComponentDefinitionGetName',definition),i,matrix,props(convert('SUComponentInstanceToDrawingElement',inst)),depth+1)
walk(ref('SUModelGetEntities',model),'UTAH')
def camera(cam):
 eye=V();target=V();up=V();call('SUCameraGetOrientation',cam,c.byref(eye),c.byref(target),c.byref(up));return {'eye':[eye.x*.0254,eye.y*.0254,eye.z*.0254],'target':[target.x*.0254,target.y*.0254,target.z*.0254],'up':[up.x,up.y,up.z]}
scenes=[{'name':string('SUSceneGetName',s),'camera':camera(ref('SUSceneGetCamera',s))} for s in items('SUModel','Scenes',model)]
result={'nodes':nodes,'geometries':geometries,'materials':materials,'scenes':scenes,'camera':camera(ref('SUModelGetCamera',model)),'stats':stats,'unit':'metres','source':'kimsa-UTAH ANEXO.skp'}
(out/'extracted.json').write_text(json.dumps(result,separators=(',',':')))
print(json.dumps({'stats':stats,'nodes':len(nodes),'geometries':len(geometries),'materials':list(materials.values()),'scenes':scenes,'camera':result['camera'],'seconds':time.time()-t0},ensure_ascii=False))
call('SUModelRelease',c.byref(model));A.SUTerminate()
