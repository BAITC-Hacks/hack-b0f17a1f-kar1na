import bpy
from pathlib import Path
P=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(P/'models/wind_farm.blend'))
bpy.ops.object.select_all(action='DESELECT');root=bpy.data.objects['WindFarm'];root.select_set(True)
for o in root.children_recursive:o.select_set(True)
bpy.ops.export_scene.gltf(filepath=str(P/'models/wind_farm.glb'),use_selection=True,export_format='GLB',export_extras=True,export_animations=False,export_apply=True)
