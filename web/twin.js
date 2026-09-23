import * as THREE from 'three';
import {GLTFLoader} from 'three/addons/loaders/GLTFLoader.js';
import {RoomEnvironment} from 'three/addons/environments/RoomEnvironment.js';
import {createBlueprint} from './twin-blueprint.js';
import {OrbitControls} from 'three/addons/controls/OrbitControls.js';
import {createWindFarmControls} from '../3d/web/wind_farm_controls.mjs';
export async function createTwin(onSelect){
 const host=document.querySelector('#twin-viewport'),status=document.querySelector('#model-status');
 try{
 const scene=new THREE.Scene();scene.background=null;
 const renderer=new THREE.WebGLRenderer({antialias:true,alpha:true});renderer.setPixelRatio(Math.min(devicePixelRatio,2));renderer.toneMapping=THREE.ACESFilmicToneMapping;host.append(renderer.domElement);
 renderer.shadowMap.enabled=true;renderer.shadowMap.type=THREE.PCFSoftShadowMap;
 const pmrem=new THREE.PMREMGenerator(renderer), room=new RoomEnvironment();
 const environment=pmrem.fromScene(room,.04);scene.environment=environment.texture;scene.environmentIntensity=.45;room.dispose();pmrem.dispose();
 const camera=new THREE.PerspectiveCamera(40,1,.1,1800);camera.position.set(-220,155,285);
 const orbit=new OrbitControls(camera,renderer.domElement);orbit.target.set(0,55,0);orbit.enableDamping=true;orbit.maxPolarAngle=Math.PI*.49;
 scene.add(new THREE.HemisphereLight(0xdcefff,0x718096,2.1));const sun=new THREE.DirectionalLight(0xfff5e8,3.2);sun.position.set(-100,180,70);sun.castShadow=true;sun.shadow.mapSize.set(2048,2048);sun.shadow.camera.left=-100;sun.shadow.camera.right=100;sun.shadow.camera.top=160;sun.shadow.camera.bottom=-100;sun.shadow.camera.far=500;sun.shadow.normalBias=.06;scene.add(sun);
 const bodyClip={value:new THREE.Vector4()};
 // Extend the transparent render surface without changing the panel's framing.
 new ResizeObserver(()=>{
   const w=host.clientWidth,h=host.clientHeight;if(!w||!h)return;
   const bleed=Math.min(90,Math.max(0,(window.innerWidth-w)/2-16));
   camera.aspect=w/h;camera.setViewOffset(w,h,-bleed,-bleed,w+2*bleed,h+2*bleed);
   renderer.setSize(w+2*bleed,h+2*bleed,false);
   const pixelRatio=renderer.getPixelRatio();bodyClip.value.set(bleed*pixelRatio,bleed*pixelRatio,(bleed+w)*pixelRatio,(bleed+h)*pixelRatio);
   Object.assign(renderer.domElement.style,{width:`${w+2*bleed}px`,height:`${h+2*bleed}px`,left:`${-bleed}px`,top:`${-bleed}px`});
 }).observe(host);
 const gltf=await new GLTFLoader().loadAsync('/models/wind_farm.glb');scene.add(gltf.scene);gltf.scene.traverse(o=>{if(o.isMesh){o.castShadow=true;o.receiveShadow=true;}});const farm=createWindFarmControls(THREE,gltf);let selected='turbine_1',zoomTarget=null;
 orbit.minDistance=8;
 const aimAtHead=()=>{zoomTarget=farm.getComponentFocusTarget(selected,'generator').center.clone();};
 renderer.domElement.addEventListener('wheel',aimAtHead,{passive:true,capture:true});
 renderer.domElement.addEventListener('touchstart',e=>{if(e.touches.length===2)aimAtHead();},{passive:true});
 // Shorten the airfoil span around its root, leaving the hub and collars intact.
 gltf.scene.traverse(object=>{
   if(!object.isMesh)return;
   if(/^blade_\d+$/.test(object.userData.component_id??'')){
     object.geometry=object.geometry.clone();
     const positions=object.geometry.attributes.position;
     for(let i=0;i<positions.count;i++)positions.setY(i,1.13+(positions.getY(i)-1.13)*.72);
     positions.needsUpdate=true;object.geometry.computeVertexNormals();object.geometry.computeBoundingBox();object.geometry.computeBoundingSphere();
     return;
   }

 });
 const setBlueprint=createBlueprint(gltf.scene,bodyClip);setBlueprint();
 const roots={turbine_1:gltf.scene.getObjectByName('Turbine_1'),turbine_2:gltf.scene.getObjectByName('Turbine_2')};
 const ground=gltf.scene.getObjectByName('Ground');if(ground)ground.visible=false;
 function portrait(id){
   zoomTarget=null;
   for(const [key,root] of Object.entries(roots))if(root)root.visible=key===id;
   const info=farm.getFocusTarget(id);
   orbit.target.copy(info.center);
   const height=info.size.y, width=Math.max(info.size.x,info.size.z);
   const distance=Math.max(height,width/Math.max(camera.aspect,.5)) / (2*Math.tan(THREE.MathUtils.degToRad(camera.fov/2))) * 1.12;
   camera.position.copy(orbit.target).add(new THREE.Vector3(-.65,.12,1).normalize().multiplyScalar(distance));
   orbit.update();
 }
 portrait(selected);
 function focus(info){zoomTarget=null;const size=Math.max(info.size.x,info.size.y,info.size.z);orbit.target.copy(info.center);camera.position.copy(info.center).add(new THREE.Vector3(-1,.55,1.4).normalize().multiplyScalar(size*2.2+5));}
 document.querySelector('#camera-reset').onclick=()=>{farm.resetInspection();farm.setNacelleExploded(selected,0,0);setBlueprint();portrait(selected);document.querySelector('#disassembly').value=0;};
 document.querySelector('#inspect-reset').onclick=()=>{farm.resetInspection();farm.setNacelleExploded(selected,0,0);setBlueprint();portrait(selected);document.querySelector('#disassembly').value=0;};
 document.querySelectorAll('[data-component]').forEach(b=>b.onclick=()=>{farm.setNacelleExploded(selected,0,0);farm.inspectComponent(selected,b.dataset.component);setBlueprint(b.dataset.component);document.querySelector('#disassembly').value=0;focus(farm.getComponentFocusTarget(selected,b.dataset.component));});
 document.querySelector('#disassembly').oninput=e=>{farm.resetInspection();farm.setNacelleExploded(selected,+e.target.value,0);setBlueprint(null,+e.target.value>0);if(+e.target.value>0)focus(farm.getDisassemblyFocusTarget(selected));else portrait(selected);};
 let down;renderer.domElement.addEventListener('pointerdown',e=>down=[e.clientX,e.clientY]);renderer.domElement.addEventListener('pointerup',e=>{if(!down||Math.hypot(e.clientX-down[0],e.clientY-down[1])>5)return;const r=renderer.domElement.getBoundingClientRect(),ray=new THREE.Raycaster();ray.setFromCamera(new THREE.Vector2((e.clientX-r.left)/r.width*2-1,1-(e.clientY-r.top)/r.height*2),camera);for(const hit of ray.intersectObjects(scene.children,true)){const id=farm.getTurbineId(hit.object);if(id){onSelect(id);break;}}});
 const clock=new THREE.Clock();renderer.setAnimationLoop(()=>{const dt=Math.min(clock.getDelta(),.1);if(!host.clientWidth)return;farm.update(dt);if(zoomTarget){orbit.target.lerp(zoomTarget,1-Math.exp(-10*dt));if(orbit.target.distanceToSquared(zoomTarget)<.0001){orbit.target.copy(zoomTarget);zoomTarget=null;}}orbit.update();renderer.render(scene,camera);});
 status.textContent='Drag to orbit · scroll to zoom · click a turbine';
 return {select(id){selected=id;farm.selectTurbine(id);setBlueprint(null,farm.getExplodedAmount(id)>0);portrait(id);document.querySelector('#disassembly').value=farm.getExplodedAmount(id);},apply(id,p){farm.applyTurbineState(id,{windSpeed:p.wind_speed});},stop(){for(const id of ['turbine_1','turbine_2'])farm.setRotorSpeed(id,0);}};
 }catch(e){status.textContent=`3D unavailable: ${e.message}. Forecasts remain available.`;return null;}
}
