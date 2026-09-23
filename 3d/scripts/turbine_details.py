"""Detailed visual assemblies; dimensions are illustrative, not manufacturer CAD."""
import bpy, math
from mathutils import Vector

def build_details(pre, tid, t, nac, api):
 empty,box,cyl,sphere,meta,white,steel,teal,gold,dark,red=api
 def group(name,cid,loc,offset,parent=nac):
  o=empty(pre+name,parent,loc);meta(o,tid,cid)
  # Metadata lives in glTF local coordinates (Y up), not Blender coordinates.
  o['assembled_position']=[loc[0],loc[2],-loc[1]]
  o['exploded_position']=[loc[0]+offset[0],loc[2]+offset[2],-loc[1]-offset[1]]
  o['explodable']=True;return o
 def ring(name,parent,loc,major,minor,mat,axis='X'):
  bpy.ops.mesh.primitive_torus_add(major_radius=major,minor_radius=minor,major_segments=48,minor_segments=8,location=loc)
  o=bpy.context.object;o.name=pre+name;o.parent=parent;o.data.materials.append(mat)
  if axis=='X':o.rotation_euler[1]=math.pi/2
  for f in o.data.polygons:f.use_smooth=True
  return o
 def bolts(name,parent,x,r,count=12,size=.065):
  for k in range(count):
   a=k*math.tau/count
   cyl(pre+name+str(k),parent,(x,r*math.cos(a),r*math.sin(a)),size,.1,steel,axis='X')
 def gear(name,parent,x,r,depth,teeth,mat):
  cyl(pre+name+'Web',parent,(x,0,0),r*.86,depth,mat,axis='X')
  ring(name+'Rim',parent,(x,0,0),r*.8,.07,steel)
  for k in range(teeth):
   a=k*math.tau/teeth
   o=box(pre+name+f'Tooth{k}',parent,(x,r*.91*math.cos(a),r*.91*math.sin(a)),(depth,r*.17,r*.15),mat,.018);o.rotation_euler[0]=a
  cyl(pre+name+'Axle',parent,(x,0,0),r*.22,depth+.12,steel,axis='X')
 # Hollow shell panels, shaped cross sections and rounded rear taper.
 shell=empty(pre+'NacelleShell',nac);meta(shell,tid,'nacelle_shell')
 sections=[(-3.55,.98,1.1),(-3.15,1.6,1.55),(-2.3,2.08,1.9),(3.7,2.08,1.9),(5.3,1.72,1.55),(6.1,.9,1.05)]
 def panel(name,cid,start,end,offset):
  par=group(name,cid,(0,0,0),offset,shell);verts=[];faces=[];steps=16
  for x,w,h in sections:
   for j in range(steps+1):
    a=start+(end-start)*j/steps
    # superellipse produces softened industrial rectangular cross-section
    y=w*math.copysign(abs(math.cos(a))**.6,math.cos(a));z=h*math.copysign(abs(math.sin(a))**.6,math.sin(a))
    verts.append((x,y,z))
  for k in range(len(sections)-1):
   for j in range(steps):a=k*(steps+1)+j;faces.append((a,a+steps+1,a+steps+2,a+1))
  me=bpy.data.meshes.new(pre+name+'Surface');me.from_pydata(verts,[],faces);me.materials.append(white)
  o=bpy.data.objects.new(pre+name+'Panel',me);bpy.context.collection.objects.link(o);o.parent=par
  for f in me.polygons:f.use_smooth=True
  mod=o.modifiers.new('Shell thickness 65mm','SOLIDIFY');mod.thickness=.065
  mod=o.modifiers.new('Panel edge radii','BEVEL');mod.width=.04;mod.segments=2
  return par
 roof=panel('ShellRoof','shell_roof',.32,math.pi-.32,(0,0,6))
 left=panel('ShellLeft','shell_left',math.pi-.32,math.pi+1.1,(0,-5,1.5))
 right=panel('ShellRight','shell_right',-1.1,.32,(0,5,1.5))
 bottom=panel('ShellFloor','shell_floor',math.pi+1.1,math.tau-1.1,(0,0,-3.4))
 tail=group('RearCover','rear_cover',(6,0,0),(5,0,0),shell)
 box(pre+'RearCap',tail,(0,0,0),(.18,1.9,2.05),white,.3)
 for j in range(10):box(pre+f'RearVent{j}',tail,(-.12,0,-.65+j*.14),(.06,1.25,.035),dark,.01)
 box(pre+'RoofHatch',roof,(2.5,0,1.94),(1.7,1.45,.1),white,.08)
 for y in [-.65,.65]:box(pre+'HatchHandle'+str(y),roof,(2.5,y,2.07),(.5,.045,.07),steel,.02)
 # Main supporting frame stays in place to explain load paths.
 bed=group('Bedplate','bedplate',(0,0,-1.35),(0,0,-1.3))
 for y in [-.95,.95]:box(pre+'FrameRail'+str(y),bed,(.7,y,0),(8.7,.25,.4),dark,.065)
 for x in [-2.7,-.5,2.2,4.4]:box(pre+'FrameCross'+str(x),bed,(x,0,0),(.25,2.1,.28),steel,.04)
 shaft=group('MainShaft','main_shaft',(-2.5,0,0),(-3,0,1.7))
 cyl(pre+'ForgedShaft',shaft,(0,0,0),.36,3.8,steel,axis='X')
 for x in [-1.3,1.3]:
  cyl(pre+'ShaftFlange'+str(x),shaft,(x,0,0),.67,.18,steel,axis='X');bolts('FlangeBolt'+str(x),shaft,x-.1,.54)
 bearings=group('MainBearings','main_bearings',(-2.5,0,0),(-1,-3.4,1.3))
 for x in [-.9,.75]:
  ring('BearingOuter'+str(x),bearings,(x,0,0),.59,.16,dark)
  ring('BearingRace'+str(x),bearings,(x,0,0),.45,.06,steel)
  box(pre+'BearingPedestal'+str(x),bearings,(x,0,-.88),(.5,1.3,.6),teal,.1)
 gearbox=group('Gearbox','gearbox',(.05,0,0),(0,-3,2.7))
 cyl(pre+'Gearcase',gearbox,(0,0,0),1.05,1.6,gold,axis='X')
 for x in [-.83,.83]:ring('GearcaseSeam'+str(x),gearbox,(x,0,0),.97,.065,steel);bolts('CaseBolts'+str(x),gearbox,x,.87,16)
 cover=group('GearboxCover','gearbox_cover',(-.91,0,0),(-1.6,0,1.4),gearbox)
 cyl(pre+'GearboxEndCover',cover,(0,0,0),1.02,.14,gold,axis='X')
 gears=group('PlanetaryStage','planetary_stage',(-1.02,0,0),(-1.5,0,0),gearbox)
 gear('SunGear',gears,0,.29,.24,16,steel)
 for k in range(3):
  a=k*math.tau/3;planet=empty(pre+f'Planet{k}',gears,(0,.61*math.cos(a),.61*math.sin(a)));gear('PlanetGear'+str(k),planet,0,.31,.24,18,steel)
 ring('PlanetCarrier',gears,(.19,0,0),.64,.06,gold)
 brake=group('Brake','brake',(1.35,0,0),(0,-2,4.7))
 cyl(pre+'BrakeDisc',brake,(0,0,0),.69,.1,steel,axis='X')
 ring('DiscFrictionTrack',brake,(0,0,0),.55,.035,dark)
 for k in range(16):
  a=k*math.tau/16;cyl(pre+f'DiscFastener{k}',brake,(-.07,.44*math.cos(a),.44*math.sin(a)),.035,.03,dark,axis='X')
 box(pre+'BrakeCaliper',brake,(0,.53,.28),(.36,.38,.6),red,.07)
 coupling=group('HighSpeedCoupling','high_speed_coupling',(1.95,0,0),(1,3,2.5))
 cyl(pre+'HighSpeedShaft',coupling,(0,0,0),.18,1.1,steel,axis='X')
 for x in [-.18,.18]:cyl(pre+'CouplingFlange'+str(x),coupling,(x,0,0),.34,.15,dark,axis='X')
 gen=group('Generator','generator',(3.65,0,0),(4,0,2.5))
 cyl(pre+'GeneratorBody',gen,(0,0,0),.98,2.7,teal,axis='X')
 for x in [-1.4,1.4]:cyl(pre+'GeneratorEnd'+str(x),gen,(x,0,0),1.02,.17,dark,axis='X');bolts('GeneratorBolts'+str(x),gen,x,.84)
 for k in range(24):
  a=k*math.tau/24;o=box(pre+f'GeneratorFin{k}',gen,(0,1.01*math.cos(a),1.01*math.sin(a)),(2.35,.085,.14),teal,.025);o.rotation_euler[0]=a
 for x in [-.85,.85]:box(pre+'GeneratorFoot'+str(x),gen,(x,0,-1.14),(.45,1.6,.26),dark,.045)
 box(pre+'TerminalBox',gen,(.45,0,1.16),(.8,.85,.38),teal,.08)
 cooling=group('CoolingSystem','cooling_system',(4.15,1.45,.2),(3,4,1.5))
 box(pre+'Cooler',cooling,(0,0,0),(1.8,.32,1.35),dark,.07)
 for k in range(12):box(pre+f'CoolingPlate{k}',cooling,(-.78+k*.14,-.2,0),(.045,.15,1.2),steel,.012)
 # Yaw mechanism, drives and fasteners.
 yaw=group('YawBearing','yaw_mechanism',(0,0,79.2),(0,0,-3),t)
 ring('YawRace',yaw,(0,0,0),1.5,.2,steel,'Z');ring('YawSeal',yaw,(0,0,.24),1.5,.08,dark,'Z')
 for k in range(48):
  a=k*math.tau/48;o=box(pre+f'YawTooth{k}',yaw,(1.57*math.cos(a),1.57*math.sin(a),0),(.13,.16,.25),steel,.015);o.rotation_euler[2]=a
 for k in range(3):
  a=k*math.tau/3;cyl(pre+f'YawMotor{k}',yaw,(1.3*math.cos(a),1.3*math.sin(a),.55),.21,.6,teal)
 # Service ladder at lower tower and electrical cabinet, visible via tower X-ray.
 ladder=group('ServiceLadder','service_ladder',(-1.05,0,1.5),(0,-4,0),t)
 for y in [-.32,.32]:cyl(pre+'LadderRail'+str(y),ladder,(0,y,37),.035,74,steel)
 for k in range(185):
  o=cyl(pre+f'Rung{k}',ladder,(0,0,k*.4),.025,.68,steel);o.rotation_euler[0]=math.pi/2
 cabinet=group('PowerCabinet','power_cabinet',(.2,0,2.1),(0,4,0),t)
 box(pre+'ElectricalEnclosure',cabinet,(0,0,0),(1.15,1.4,2.3),white,.08)
 box(pre+'CabinetDoor',cabinet,(-.6,0,0),(.04,1.24,2.1),dark,.04)
 for z in [.6,.1,-.4]:box(pre+'ControlModule'+str(z),cabinet,(-.64,0,z),(.06,.8,.28),teal,.02)
 # Roof instrumentation follows roof during disassembly.
 cyl(pre+'SensorMast',roof,(4,0,2.7),.045,1.5,steel)
 for k in range(3):
  a=k*math.tau/3
  o=cyl(pre+f'AnemometerArm{k}',roof,(4+.22*math.cos(a),.22*math.sin(a),3.45),.025,.48,steel);o.rotation_euler=(0,math.pi/2,a)
  sphere(pre+f'AnemometerCup{k}',roof,(4+.48*math.cos(a),.48*math.sin(a),3.45),(.16,.16,.11),dark)
 cyl(pre+'VaneMast',roof,(3.1,0,2.75),.04,1.5,steel)
 box(pre+'WindVane',roof,(3.3,0,3.48),(.65,.035,.22),red,.025)
 return shell
