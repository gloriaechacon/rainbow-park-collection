exec(open('work/utah-model/extract_skp.py').read().split('A.SUInitialize();model=')[0])
A.SUInitialize();model=Ref();assert call('SUModelCreateFromFile',c.byref(model),b'/Users/robertochacon/Downloads/kimsa-UTAH ANEXO.skp')==0
changed=[]
def color(hex):return Color(*[int(hex[i:i+2],16) for i in [1,3,5]],255)
for m in items('SUModel','Materials',model):
 name=string('SUMaterialGetName',m);hex=None
 if any(x in name for x in ['M00','White','Charcoal','auto']):hex='#e9e4d5'
 elif any(x in name for x in ['Ventana','Alumin','Color M08']):hex='#303c32'
 if hex:
  col=color(hex);assert call('SUMaterialSetType',m,0)==0;assert call('SUMaterialSetColor',m,c.byref(col))==0;changed.append(name)
root=ref('SUModelGetEntities',model);proposal=ref('SUGroupCreate');call('SUGroupSetName',proposal,'RPC · Acabados y mobiliario propuestos'.encode());assert call('SUEntitiesAddGroup',root,proposal)==0;parent=ref('SUGroupGetEntities',proposal);materials={}
for item in json.loads(Path('work/utah-model/furnishings.json').read_text()):
 if item['kind']=='site':continue
 h=item['color']
 if h not in materials:
  mat=ref('SUMaterialCreate');call('SUMaterialSetName',mat,('RPC '+h).encode());col=color(h);call('SUMaterialSetColor',mat,c.byref(col));call('SUModelAddMaterials',model,1,(Ref*1)(mat));materials[h]=mat
 group=ref('SUGroupCreate');call('SUGroupSetName',group,('Propuesta · '+item['name']).encode());call('SUEntitiesAddGroup',parent,group);entities=ref('SUGroupGetEntities',group);geo=ref('SUGeometryInputCreate')
 x,y,z=item['position'];w,d,height=item['size'];verts=(V*8)(*[V((x+sx*w/2)/.0254,(y+sy*d/2)/.0254,(z+sz*height/2)/.0254) for sx,sy,sz in [(-1,-1,-1),(1,-1,-1),(1,1,-1),(-1,1,-1),(-1,-1,1),(1,-1,1),(1,1,1),(-1,1,1)]])
 assert call('SUGeometryInputSetVertices',geo,8,verts)==0
 for quad in [(0,3,2,1),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)]:
  loop=ref('SULoopInputCreate')
  for idx in quad:call('SULoopInputAddVertexIndex',loop,idx)
  fi=Size();assert call('SUGeometryInputAddFace',geo,c.byref(loop),c.byref(fi))==0
 assert call('SUEntitiesFill',entities,geo,True)==0;call('SUGeometryInputRelease',c.byref(geo));draw=convert('SUGroupToDrawingElement',group);call('SUDrawingElementSetMaterial',draw,materials[h])
for name,pos,target in [('01 Fachada',(25,-8,9),(12.2,18,1.5)),('02 Aerea',(29,-2,25),(12.2,20.2,1)),('03 Sala',(11.9,18.6,1.85),(9.4,16.55,1.1)),('04 Cocina',(12.6,19.1,1.85),(9.3,20.6,1.2)),('05 Dormitorio',(17,19.15,1.85),(18.8,21.1,1.1)),('06 Anexo',(8.7,24.45,1.85),(6.7,26.3,1.1))]:
 scene=ref('SUSceneCreate');call('SUSceneSetName',scene,name.encode());cam=ref('SUCameraCreate');eye=V(*[x/.0254 for x in pos]);look=V(*[x/.0254 for x in target]);up=V(0,0,1);call('SUCameraSetOrientation',cam,c.byref(eye),c.byref(look),c.byref(up));call('SUCameraSetPerspectiveFrustumFOV',cam,c.c_double(65));call('SUSceneSetCamera',scene,cam);call('SUSceneSetUseCamera',scene,True);call('SUModelAddScenes',model,1,(Ref*1)(scene))
path=Path('outputs/utah/Utah-propuesta-v1.skp').resolve();assert call('SUModelSaveToFile',model,str(path).encode())==0;call('SUModelRelease',c.byref(model));test=Ref();assert call('SUModelCreateFromFile',c.byref(test),str(path).encode())==0;print(json.dumps({'saved':str(path),'reopened':True,'scenes':len(items('SUModel','Scenes',test)),'changed_materials':changed},ensure_ascii=False));call('SUModelRelease',c.byref(test));A.SUTerminate()
