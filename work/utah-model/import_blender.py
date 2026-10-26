import bpy,json,math,sys
from pathlib import Path
from mathutils import Matrix,Vector
base=Path(__file__).resolve().parent;d=json.loads((base/'extracted.json').read_text());previous_scene=bpy.context.window.scene;scene=bpy.data.scenes.new('UTAH | Importación original');bpy.context.window.scene=scene
def linear(x):return x/12.92 if x<.04045 else ((x+.055)/1.055)**2.4
mats={}
for k,v in d['materials'].items():
 m=bpy.data.materials.new(v['name']);m.diffuse_color=tuple(v['color']);m.use_nodes=True;bs=m.node_tree.nodes.get('Principled BSDF');bs.inputs['Base Color'].default_value=(*[linear(a) for a in v['color'][:3]],1);bs.inputs['Roughness'].default_value=.65
 if v['texture']:
  tex=m.node_tree.nodes.new('ShaderNodeTexImage');tex.image=bpy.data.images.load(str(base/v['texture']));m.node_tree.links.new(tex.outputs['Color'],bs.inputs['Base Color'])
 if v['color'][3]<.9:bs.inputs['Transmission Weight'].default_value=.8;bs.inputs['Roughness'].default_value=.12
 mats[k]=m
fallback=bpy.data.materials.new('Unassigned');fallback.diffuse_color=(.72,.73,.71,1);fallback.use_nodes=True;mats[None]=fallback
objects=[]
for i,n in enumerate(d['nodes']):
 g=d['geometries'][n['geometry']];mesh=bpy.data.meshes.new(n['name']);mesh.from_pydata(g['vertices'],[],g['triangles']);mesh.update();o=bpy.data.objects.new(f'{i:03d} | '+n['name'],mesh);scene.collection.objects.link(o)
 if n['parent'] is not None:o.parent=objects[n['parent']]
 if n['transform']:o.matrix_local=Matrix([n['transform'][j:j+4] for j in range(0,16,4)]).transposed()
 inherited=n['props'].get('material');p=n['parent']
 while inherited is None and p is not None:inherited=d['nodes'][p]['props'].get('material');p=d['nodes'][p]['parent']
 keys=list(dict.fromkeys(mk or inherited for mk in g['materials']));[mesh.materials.append(mats[k]) for k in keys];indices={k:i for i,k in enumerate(keys)}
 if g['triangles']:
  uv=mesh.uv_layers.new(name='UVMap')
  for poly,mk in zip(mesh.polygons,g['materials']):
   poly.material_index=indices[mk or inherited]
   for loop in poly.loop_indices:uv.data[loop].uv=g['uvs'][mesh.loops[loop].vertex_index]
 o['source_node']=i;o['layer']=n['props'].get('layer','');o.hide_render=n['props'].get('hidden',False) or not n['props'].get('layerVisible',True);objects.append(o)
bpy.context.view_layer.update()
points=[o.matrix_world@Vector(v) for o in objects if len(o.data.vertices) for v in o.bound_box];mn=Vector([min(p[i] for p in points) for i in range(3)]);mx=Vector([max(p[i] for p in points) for i in range(3)]);center=(mn+mx)/2
report=[]
for o in objects:
 if len(o.data.vertices):
  pts=[o.matrix_world@Vector(v) for v in o.bound_box];lo=[min(v[j] for v in pts) for j in range(3)];hi=[max(v[j] for v in pts) for j in range(3)];report.append({'name':o.name,'min':lo,'max':hi,'triangles':len(o.data.polygons),'parent':o.parent.name if o.parent else None})
(base/'bounds.json').write_text(json.dumps({'min':list(mn),'max':list(mx),'objects':report},indent=2))
scene=bpy.context.scene;scene.unit_settings.system='METRIC';scene.render.engine='BLENDER_WORKBENCH';scene.display.shading.light='STUDIO';scene.display.shading.color_type='MATERIAL';scene.display.shading.show_shadows=True;scene.display.shading.show_cavity=True;scene.display.shading.cavity_type='BOTH';scene.display.shading.background_type='WORLD';scene.world=bpy.data.worlds.new('UTAH World');scene.world.color=(.85,.85,.85)
camdata=bpy.data.cameras.new('Camera');cam=bpy.data.objects.new('Camera',camdata);scene.collection.objects.link(cam);scene.camera=cam
cam.location=Vector(d['camera']['eye']);target=Vector(d['camera']['target']);cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler();camdata.lens=30
scene.render.resolution_x=1600;scene.render.resolution_y=1100;scene.render.resolution_percentage=100
bpy.data.libraries.write(str(base/'utah-source.blend'),{scene},path_remap='ABSOLUTE');scene.render.filepath=str(base/'source-view.png');bpy.ops.render.render(write_still=True)
camdata.type='ORTHO';camdata.ortho_scale=max(mx.x-mn.x,mx.y-mn.y)*1.2;cam.location=center+Vector((0,0,100));cam.rotation_euler=(0,0,0);scene.render.filepath=str(base/'source-top.png');bpy.ops.render.render(write_still=True)
print('BOUNDS',list(mn),list(mx))

bpy.context.window.scene=previous_scene
