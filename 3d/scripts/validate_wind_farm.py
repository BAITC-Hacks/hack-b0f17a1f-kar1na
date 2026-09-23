import bpy,json,struct,hashlib
from pathlib import Path
P=Path(__file__).resolve().parents[1];checks={}
bpy.ops.wm.open_mainfile(filepath=str(P/'models/wind_farm.blend'))
def snapshot():
 return {o.name:{'parent':o.parent.name if o.parent else None,'vertices':len(o.data.vertices) if o.type=='MESH' else 0,'world':[list(r) for r in o.matrix_world]} for o in bpy.data.objects if o.name=='WindFarm' or o in bpy.data.objects['WindFarm'].children_recursive}
a=snapshot();bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
bpy.ops.import_scene.gltf(filepath=str(P/'models/wind_farm.glb'));b=snapshot()
checks['names_and_hierarchy']=set(a)==set(b) and all(a[n]['parent']==b[n]['parent'] for n in a)
checks['one_root']=len([o for o in bpy.context.scene.objects if not o.parent])==1
for i in [1,2]:
 p=f'T{i}_';t=bpy.data.objects[f'Turbine_{i}'];r=bpy.data.objects[p+'Rotor'];checks[p+'metadata']=t.get('assembly_id')==f'turbine_{i}'
 checks[p+'components']=all(bpy.data.objects.get(p+n) is not None for n in ['Tower','Nacelle','NacelleShell','Generator','Gearbox','MainShaft','Hub','Blade_1','Blade_2','Blade_3'])
 checks[p+'rotor_hierarchy']=all(bpy.data.objects[p+n].parent==r for n in ['Hub','Blade_1','Blade_2','Blade_3'])
 checks[p+'pivot']=abs(r.location.z-81)<1e-4 and abs(r.location.x+4.5)<1e-4
checks['materials']=all(len(o.data.materials)>0 for o in bpy.context.scene.objects if o.type=='MESH')
checks['transforms_roundtrip']=all(max(abs(a[n]['world'][r][c]-b[n]['world'][r][c]) for r in range(4) for c in range(4))<1e-4 for n in a)
raw=(P/'models/wind_farm.glb').read_bytes();length=struct.unpack_from('<I',raw,12)[0];g=json.loads(raw[20:20+length]);tri=sum(g['accessors'][p['indices']]['count']//3 for m in g['meshes'] for p in m['primitives'])
manifest={'blender_version':bpy.app.version_string,'root_node':'WindFarm','turbine_count':2,'mesh_objects':len([o for o in bpy.context.scene.objects if o.type=='MESH']),'triangles_glb':tri,'material_count':len(g['materials']),'animation_clips':[],'rotor_animation':'runtime local X rotation','glb_bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest(),'selectable_assemblies':['turbine_1','turbine_2'],'component_ids':sorted(set(o.get('component_id') for o in bpy.data.objects if o.get('component_id')))}
(P/'reports/model_manifest.json').write_text(json.dumps(manifest,indent=2));(P/'reports/validation_report.json').write_text(json.dumps({'status':'PASS' if all(checks.values()) else 'FAIL','checks':checks},indent=2));print(checks)
assert all(checks.values()),checks
