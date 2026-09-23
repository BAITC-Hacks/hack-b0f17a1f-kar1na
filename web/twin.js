import * as THREE from 'three';
import {GLTFLoader} from 'three/addons/loaders/GLTFLoader.js';
import {RoomEnvironment} from 'three/addons/environments/RoomEnvironment.js';
import {createBlueprint} from './twin-blueprint.js';
import {OrbitControls} from 'three/addons/controls/OrbitControls.js';
import {createWindFarmControls} from '../3d/web/wind_farm_controls.mjs';
export async function createTwin(onSelect,onInspect=()=>{}){
 const host=document.querySelector('#twin-viewport'),status=document.querySelector('#model-status');
 try{
 const scene=new THREE.Scene();scene.background=null;
 const renderer=new THREE.WebGLRenderer({antialias:true,alpha:true});renderer.setPixelRatio(Math.min(devicePixelRatio,2));renderer.toneMapping=THREE.ACESFilmicToneMapping;host.append(renderer.domElement);
 renderer.shadowMap.enabled=true;renderer.shadowMap.type=THREE.PCFSoftShadowMap;
 const pmrem=new THREE.PMREMGenerator(renderer), room=new RoomEnvironment();
 const environment=pmrem.fromScene(room,.04);scene.environment=environment.texture;scene.environmentIntensity=.45;room.dispose();pmrem.dispose();
 const camera=new THREE.PerspectiveCamera(40,1,.1,1800);camera.position.set(-220,155,285);
 const orbit=new OrbitControls(camera,renderer.domElement);orbit.target.set(0,55,0);orbit.enableDamping=true;orbit.maxPolarAngle=Math.PI*.49;
 scene.add(new THREE.HemisphereLight(0xdcefff,0x4167b4,1.6));const sun=new THREE.DirectionalLight(0xf2f7ff,2.8);sun.position.set(-100,180,70);sun.castShadow=true;sun.shadow.mapSize.set(2048,2048);sun.shadow.camera.left=-100;sun.shadow.camera.right=100;sun.shadow.camera.top=160;sun.shadow.camera.bottom=-100;sun.shadow.camera.far=500;sun.shadow.normalBias=.06;scene.add(sun);
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
 const gltf=await new GLTFLoader().loadAsync('/models/wind_farm.glb');scene.add(gltf.scene);gltf.scene.traverse(o=>{if(o.userData.component_id==='rotor')o.rotateX(-.65);if(o.isMesh){o.castShadow=true;o.receiveShadow=true;}});const farm=createWindFarmControls(THREE,gltf);let selected='turbine_1',zoomTarget=null,cameraTransition=null;
 const reducedMotion=window.matchMedia('(prefers-reduced-motion: reduce)');
 function moveCamera(target,position,immediate=false){
   zoomTarget=null;
   if(immediate||reducedMotion.matches){cameraTransition=null;orbit.target.copy(target);camera.position.copy(position);orbit.update();return;}
   cameraTransition={from:camera.position.clone(),fromTarget:orbit.target.clone(),to:position.clone(),toTarget:target.clone(),elapsed:0};
 }
 orbit.addEventListener('start',()=>{cameraTransition=null;});
 orbit.minDistance=3;orbit.zoomSpeed=1.8;orbit.dampingFactor=.12;
 const aimAtHead=()=>{if(!zoomTarget)zoomTarget=farm.getComponentFocusTarget(selected,'generator').center.clone();};
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
 const assembledViews=Object.fromEntries(Object.keys(roots).map(id=>[id,farm.getFocusTarget(id)]));
 const componentViews=Object.fromEntries(Object.keys(roots).map(id=>[id,Object.fromEntries(['generator','gearbox','main_shaft','rotor'].map(key=>[key,farm.getComponentFocusTarget(id,key)]))]));
 function portrait(id,immediate=false){
   zoomTarget=null;
   for(const [key,root] of Object.entries(roots))if(root)root.visible=key===id;
   const info=assembledViews[id];

   // A close, assembled portrait: hub near the center, blade tips beyond the panel.
   // Use the cached assembled dimensions so inspection never changes the reset view.
   const target=componentViews[id].generator.center.clone();
   target.y-=2;
   const distance=info.size.y / (2*Math.tan(THREE.MathUtils.degToRad(camera.fov/2))) * .55;
   moveCamera(target,target.clone().add(new THREE.Vector3(-1,.06,1.1).normalize().multiplyScalar(distance)),immediate);
 }
 portrait(selected,true);
 function focus(info){zoomTarget=null;const size=Math.max(info.size.x,info.size.y,info.size.z);moveCamera(info.center,info.center.clone().add(new THREE.Vector3(-1,.55,1.4).normalize().multiplyScalar(size*2.2+5)));}
 document.querySelector('#camera-reset').onclick=()=>{farm.resetInspection();farm.setNacelleExploded(selected,0,reducedMotion.matches?0:.75);setBlueprint();portrait(selected);document.querySelector('#disassembly').value=0;onInspect({turbine_id:selected,component:'overview'});};
 document.querySelector('#inspect-reset').onclick=()=>{farm.resetInspection();farm.setNacelleExploded(selected,0,reducedMotion.matches?0:.75);setBlueprint();portrait(selected);document.querySelector('#disassembly').value=0;onInspect({turbine_id:selected,component:'overview'});};
 document.querySelectorAll('[data-component]').forEach(b=>b.onclick=()=>{farm.setNacelleExploded(selected,0,reducedMotion.matches?0:.75);farm.inspectComponent(selected,b.dataset.component);setBlueprint(b.dataset.component);document.querySelector('#disassembly').value=0;focus(componentViews[selected][b.dataset.component]);onInspect({turbine_id:selected,component:b.dataset.component});});
 document.querySelector('#disassembly').oninput=e=>{const amount=+e.target.value;farm.resetInspection();farm.setNacelleExploded(selected,amount,reducedMotion.matches?0:.18);setBlueprint(null,amount>0);onInspect({turbine_id:selected,component:amount>0?'nacelle':'overview'});};
 let down;renderer.domElement.addEventListener('pointerdown',e=>down=[e.clientX,e.clientY]);renderer.domElement.addEventListener('pointerup',e=>{if(!down||Math.hypot(e.clientX-down[0],e.clientY-down[1])>5)return;const r=renderer.domElement.getBoundingClientRect(),ray=new THREE.Raycaster();ray.setFromCamera(new THREE.Vector2((e.clientX-r.left)/r.width*2-1,1-(e.clientY-r.top)/r.height*2),camera);for(const hit of ray.intersectObjects(scene.children,true)){const id=farm.getTurbineId(hit.object);if(id){if(id!==selected)onSelect(id);else onInspect({turbine_id:selected,component:'overview'});break;}}});
 const clock=new THREE.Clock();renderer.setAnimationLoop(()=>{const dt=Math.min(clock.getDelta(),.1);if(!host.clientWidth)return;farm.update(dt);setBlueprint.update(reducedMotion.matches?1:dt);
 if(cameraTransition){
   const t=cameraTransition;t.elapsed+=dt;const progress=Math.min(1,t.elapsed/.9);
   const eased=progress*progress*progress*(progress*(progress*6-15)+10);
   camera.position.lerpVectors(t.from,t.to,eased);orbit.target.lerpVectors(t.fromTarget,t.toTarget,eased);
   if(progress===1)cameraTransition=null;
 }
 if(zoomTarget){const shift=zoomTarget.clone().sub(orbit.target).multiplyScalar(1-Math.exp(-7*dt));orbit.target.add(shift);camera.position.add(shift);if(orbit.target.distanceToSquared(zoomTarget)<.0001)zoomTarget=null;}orbit.update();renderer.render(scene,camera);});
 status.textContent='Drag to orbit · scroll to zoom · click a turbine';
 return {select(id){selected=id;farm.selectTurbine(id);setBlueprint(null,farm.getExplodedAmount(id)>0);portrait(id);document.querySelector('#disassembly').value=farm.getExplodedAmount(id);},apply(id,p){farm.applyTurbineState(id,{windSpeed:p.wind_speed});},stop(){for(const id of ['turbine_1','turbine_2'])farm.setRotorSpeed(id,0);}};
 }catch(e){status.textContent=`3D unavailable: ${e.message}. Forecasts remain available.`;return null;}
}
