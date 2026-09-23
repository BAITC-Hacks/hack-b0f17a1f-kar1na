import * as THREE from 'three';
import {GLTFLoader} from 'three/addons/loaders/GLTFLoader.js';
import {OrbitControls} from 'three/addons/controls/OrbitControls.js';
import {createWindFarmControls} from '../3d/web/wind_farm_controls.mjs';
export async function createTwin(onSelect){
 const host=document.querySelector('#twin-viewport'),status=document.querySelector('#model-status');
 try{
 const scene=new THREE.Scene();scene.background=null;
 const renderer=new THREE.WebGLRenderer({antialias:true,alpha:true});renderer.setPixelRatio(Math.min(devicePixelRatio,2));renderer.toneMapping=THREE.ACESFilmicToneMapping;host.append(renderer.domElement);
 const camera=new THREE.PerspectiveCamera(40,1,.1,1800);camera.position.set(-220,155,285);
 const orbit=new OrbitControls(camera,renderer.domElement);orbit.target.set(0,55,0);orbit.enableDamping=true;orbit.maxPolarAngle=Math.PI*.49;
 scene.add(new THREE.HemisphereLight(0xdcefff,0x7b8c83,3));const sun=new THREE.DirectionalLight(0xffeedb,3);sun.position.set(-100,180,70);scene.add(sun);
 new ResizeObserver(()=>{const w=host.clientWidth,h=host.clientHeight;if(!w||!h)return;camera.aspect=w/h;camera.updateProjectionMatrix();renderer.setSize(w,h,false);}).observe(host);
 const gltf=await new GLTFLoader().loadAsync('/models/wind_farm.glb');scene.add(gltf.scene);const farm=createWindFarmControls(THREE,gltf);let selected='turbine_1';
 const roots={turbine_1:gltf.scene.getObjectByName('Turbine_1'),turbine_2:gltf.scene.getObjectByName('Turbine_2')};
 const ground=gltf.scene.getObjectByName('Ground');if(ground)ground.visible=false;
 function portrait(id){
   for(const [key,root] of Object.entries(roots))if(root)root.visible=key===id;
   const info=farm.getComponentFocusTarget(id,'generator');
   orbit.target.copy(info.center).add(new THREE.Vector3(0,-2,0));
   camera.position.copy(orbit.target).add(new THREE.Vector3(-28,10,35));
 }
 portrait(selected);
 function focus(info){const size=Math.max(info.size.x,info.size.y,info.size.z);orbit.target.copy(info.center);camera.position.copy(info.center).add(new THREE.Vector3(-1,.55,1.4).normalize().multiplyScalar(size*2.2+5));}
 document.querySelector('#camera-reset').onclick=()=>{farm.resetInspection();for(const root of Object.values(roots))if(root)root.visible=true;camera.position.set(-220,155,285);orbit.target.set(0,55,0);};
 document.querySelector('#inspect-reset').onclick=()=>{farm.resetInspection();portrait(selected);};
 document.querySelectorAll('[data-component]').forEach(b=>b.onclick=()=>{farm.inspectComponent(selected,b.dataset.component);focus(farm.getComponentFocusTarget(selected,b.dataset.component));});
 document.querySelector('#disassembly').oninput=e=>{farm.resetInspection();farm.setNacelleExploded(selected,+e.target.value,0);focus(farm.getDisassemblyFocusTarget(selected));};
 let down;renderer.domElement.addEventListener('pointerdown',e=>down=[e.clientX,e.clientY]);renderer.domElement.addEventListener('pointerup',e=>{if(!down||Math.hypot(e.clientX-down[0],e.clientY-down[1])>5)return;const r=renderer.domElement.getBoundingClientRect(),ray=new THREE.Raycaster();ray.setFromCamera(new THREE.Vector2((e.clientX-r.left)/r.width*2-1,1-(e.clientY-r.top)/r.height*2),camera);for(const hit of ray.intersectObjects(scene.children,true)){const id=farm.getTurbineId(hit.object);if(id){onSelect(id);break;}}});
 const clock=new THREE.Clock();renderer.setAnimationLoop(()=>{const dt=Math.min(clock.getDelta(),.1);if(!host.clientWidth)return;farm.update(dt);orbit.update();renderer.render(scene,camera);});
 status.textContent='Drag to orbit · scroll to zoom · click a turbine';
 return {select(id){selected=id;farm.selectTurbine(id);portrait(id);document.querySelector('#disassembly').value=farm.getExplodedAmount(id);},apply(id,p){farm.applyTurbineState(id,{windSpeed:p.wind_speed});},stop(){for(const id of ['turbine_1','turbine_2'])farm.setRotorSpeed(id,0);}};
 }catch(e){status.textContent=`3D unavailable: ${e.message}. Forecasts remain available.`;return null;}
}
