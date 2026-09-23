import bpy,json
from pathlib import Path
from mathutils import Vector
P=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(P/'models/wind_farm.blend'))
scene=bpy.context.scene;scene.frame_set(1)
parts=[o for o in bpy.data.objects if o.get('explodable')]
initial={o.name:o.matrix_world.copy() for o in bpy.data.objects}
geometry={o.name:len(o.data.vertices) for o in bpy.data.objects if o.type=='MESH'}
scene.frame_set(60);checks={'movable_assemblies':len(parts)>=20,'endpoints_match_metadata':all((o.location-Vector((o['exploded_position'][0],-o['exploded_position'][2],o['exploded_position'][1]))).length<1e-5 for o in parts)}
scene.frame_set(1);checks['reassemble_world_transforms']=all(max(abs(o.matrix_world[r][c]-initial[o.name][r][c]) for r in range(4) for c in range(4))<1e-5 for o in bpy.data.objects)
checks['same_geometry']=all(len(bpy.data.objects[n].data.vertices)==count for n,count in geometry.items())
(P/'reports/disassembly_validation.json').write_text(json.dumps({'status':'PASS' if all(checks.values()) else 'FAIL','movable_assembly_count':len(parts),'checks':checks},indent=2))
assert all(checks.values()),checks
