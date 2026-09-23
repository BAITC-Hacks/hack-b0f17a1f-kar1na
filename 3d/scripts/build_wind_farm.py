import bpy, math, json, sys
from pathlib import Path
from mathutils import Vector
P=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(P/'scripts'))
from turbine_details import build_details
bpy.ops.object.select_all(action='SELECT'); bpy.ops.object.delete(use_global=False)
bpy.context.scene.unit_settings.system='METRIC'
def material(name,color,metal=0,rough=.4):
 m=bpy.data.materials.new(name); m.diffuse_color=(*color,1); m.use_nodes=True
 s=m.node_tree.nodes.get('Principled BSDF'); s.inputs['Base Color'].default_value=(*color,1); s.inputs['Metallic'].default_value=metal; s.inputs['Roughness'].default_value=rough
 return m
white=material('Porcelain painted steel',(.78,.83,.85),.25)
blade_mat=material('Composite',(.92,.94,.91),.05)
steel=material('Machined steel',(.22,.29,.34),.8,.25)
teal=material('Generator teal',(.035,.32,.34),.55)
gold=material('Gearbox ochre',(.8,.38,.075),.55)
dark=material('Graphite',(.045,.075,.085),.4)
concrete=material('Concrete',(.34,.4,.4),0,.85)
red=material('Safety vermilion',(.88,.16,.07),.1)
def empty(name,parent=None,loc=(0,0,0)):
 o=bpy.data.objects.new(name,None); bpy.context.collection.objects.link(o); o.parent=parent; o.location=loc; return o
def finish(o,name,parent,mat):
 o.name=name; o.parent=parent; o.data.materials.append(mat)
 for p in o.data.polygons:p.use_smooth=True
 return o
def box(name,parent,loc,size,mat,bevel=.15):
 bpy.ops.mesh.primitive_cube_add(size=1,location=loc); o=bpy.context.object; o.scale=size; bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
 finish(o,name,parent,mat)
 if bevel:
  mod=o.modifiers.new('Manufactured radii','BEVEL'); mod.width=bevel; mod.segments=3
  bpy.context.view_layer.objects.active=o; bpy.ops.object.modifier_apply(modifier=mod.name)
 mod=o.modifiers.new('Weighted normals','WEIGHTED_NORMAL'); return o
def cyl(name,parent,loc,r,depth,mat,r2=None,axis='Z'):
 bpy.ops.mesh.primitive_cone_add(vertices=48,radius1=r,radius2=r if r2 is None else r2,depth=depth,location=loc)
 o=finish(bpy.context.object,name,parent,mat)
 if axis=='X':o.rotation_euler[1]=math.pi/2
 return o
def sphere(name,parent,loc,scale,mat):
 bpy.ops.mesh.primitive_uv_sphere_add(segments=32,ring_count=16,location=loc); o=finish(bpy.context.object,name,parent,mat);o.scale=scale;return o
def meta(o,tid,cid):o['turbine_id']=tid;o['component_id']=cid
root=empty('WindFarm'); root['digital_twin_type']='wind_farm'
box('Ground',root,(0,7,-1),(190,105,1.6),concrete,2)
# Span stations: circular root to twisted, tapered aerodynamic profile.
stations=[(1.1,.65,0),(2.3,.8,0),(4,1.65,18),(7,3.15,16),(12,2.85,12),(20,2.25,8),(29,1.5,4),(34,1.05,2),(35,1,2),(37,.75,1),(38,.65,1),(39,.52,1),(40,.38,0),(42,.12,0),(42.4,.015,0)]
verts=[];faces=[];N=24
for z,chord,twist in stations:
 for j in range(N):
  a=2*math.pi*j/N; u=(1-math.cos(a))/2
  thick=5*.18*(.2969*math.sqrt(u)-.126*u-.3516*u*u+.2843*u**3-.1036*u**4)
  y=(u-.32)*chord; x=thick*chord*(1 if j<N/2 else -1)
  if z<3:x=.45*math.sin(a);y=-.45*math.cos(a)
  t=math.radians(twist);verts.append((x*math.cos(t)-y*math.sin(t),y*math.cos(t)+x*math.sin(t)+.018*z,z))
for k in range(len(stations)-1):
 for j in range(N):a=k*N+j;b=k*N+(j+1)%N;faces.append((a,b,b+N,a+N))
faces.extend([tuple(reversed(range(N))),tuple((len(stations)-1)*N+j for j in range(N))])
mesh=bpy.data.meshes.new('Twisted airfoil blade');mesh.from_pydata(verts,[],faces);mesh.materials.append(blade_mat);mesh.materials.append(red)
for p in mesh.polygons:p.use_smooth=True;p.material_index=1 if (35<p.center.z<37 or 39<p.center.z<41) else 0
for i,pos in enumerate([(-49,-9,0),(49,23,0)],1):
 tid=f'turbine_{i}';pre=f'T{i}_';t=empty(f'Turbine_{i}',root,pos);t['assembly_id']=tid;t['turbine_id']=tid;t['selectable']=True;t['component_type']='wind_turbine'
 cyl(pre+'Foundation',t,(0,0,.4),5,1.2,concrete)
 tower=cyl(pre+'Tower',t,(0,0,40.5),2.2,79,white,1.35);meta(tower,tid,'tower')
 for z in [1.3,26,53,79.5]:cyl(pre+f'TowerSeam_{z}',t,(0,0,z),2.2-(z/80)*.85+.035,.12,steel)
 box(pre+'AccessDoor',t,(-2.16,0,2.5),(.12,1.05,2.7),dark,.12)
 for j in range(12):
  a=j*math.tau/12;cyl(pre+f'Anchor_{j}',t,(3.5*math.cos(a),3.5*math.sin(a),1.08),.13,.18,steel)
 nac=empty(pre+'Nacelle',t,(0,0,81));meta(nac,tid,'nacelle')
 shell=build_details(pre,tid,t,nac,(empty,box,cyl,sphere,meta,white,steel,teal,gold,dark,red))
 rotor=empty(pre+'Rotor',t,(-4.5,0,81));meta(rotor,tid,'rotor');rotor['rotation_axis']='X';rotor['speed_units']='radians_per_second'
 hub=sphere(pre+'Hub',rotor,(-.5,0,0),(2.15,1.32,1.32),white);meta(hub,tid,'hub')
 for k in range(3):
  pitch=empty(pre+f'PitchBearing_{k+1}',rotor);pitch.rotation_euler[0]=k*math.tau/3+.15
  cyl(pre+f'BladeRootCollar_{k+1}',pitch,(0,0,1.25),.5,.32,steel)
  o=bpy.data.objects.new(pre+f'Blade_{k+1}',mesh);bpy.context.collection.objects.link(o);o.parent=rotor;o.rotation_euler[0]=k*math.tau/3+.15;meta(o,tid,f'blade_{k+1}'); mod=o.modifiers.new('Smooth airfoil transitions','SUBSURF'); mod.levels=1; mod.render_levels=1
# Studio rig, excluded from exported selection.
scene=bpy.context.scene;scene.render.engine='CYCLES';scene.cycles.samples=40
scene.world.color=(.35,.35,.35)
def aim(o,at):o.rotation_euler=(Vector(at)-o.location).to_track_quat('-Z','Y').to_euler()
bpy.ops.object.light_add(type='AREA',location=(-70,-80,160));bpy.context.object.data.energy=160000;bpy.context.object.data.shape='DISK';bpy.context.object.data.size=100;aim(bpy.context.object,(0,0,45))
bpy.ops.object.light_add(type='SUN',location=(0,0,100));bpy.context.object.rotation_euler=(.4,-.5,-.4);bpy.context.object.data.energy=2
bpy.ops.object.camera_add(location=(-220,-300,170));cam=bpy.context.object;aim(cam,(0,6,57));cam.data.type='ORTHO';cam.data.ortho_scale=255;scene.camera=cam
scene.render.resolution_x=1600;scene.render.resolution_y=1100;scene.render.resolution_percentage=100
scene.view_settings.view_transform='AgX'
# Blender timeline: assembled → exploded, same geometry and hierarchy.
scene.render.fps=30;scene.frame_end=60
scene.timeline_markers.new('ASSEMBLED',frame=1);scene.timeline_markers.new('EXPLODED',frame=60)
for o in root.children_recursive:
 if o.get('explodable'):
  original=o.location.copy();o.keyframe_insert(data_path='location',frame=1)
  e=o['exploded_position'];o.location=(e[0],-e[2],e[1]);o.keyframe_insert(data_path='location',frame=60);o.location=original
scene.frame_set(1)
bpy.ops.wm.save_as_mainfile(filepath=str(P/'models/wind_farm.blend'))
bpy.ops.object.select_all(action='DESELECT');root.select_set(True)
for o in root.children_recursive:o.select_set(True)
bpy.ops.export_scene.gltf(filepath=str(P/'models/wind_farm.glb'),use_selection=True,export_format='GLB',export_extras=True,export_animations=False,export_apply=True)
scene.render.filepath=str(P/'renders/assembled.png');bpy.ops.render.render(write_still=True)
# Cutaway preview by hiding shell only in this unsaved render state.
for i in [1,2]:
 for o in bpy.data.objects[f'T{i}_NacelleShell'].children_recursive:o.hide_render=True
cam.location=(-19,-24,94);aim(cam,(-48,-9,81));cam.data.ortho_scale=17
scene.render.filepath=str(P/'renders/inspection.png');bpy.ops.render.render(write_still=True)

for i in [1,2]:
 for o in bpy.data.objects[f'T{i}_NacelleShell'].children_recursive:o.hide_render=False
scene.frame_set(60)
cam.location=(-68,-38,100);aim(cam,(-48,-9,82));cam.data.ortho_scale=28
scene.render.filepath=str(P/'renders/exploded.png');bpy.ops.render.render(write_still=True)
