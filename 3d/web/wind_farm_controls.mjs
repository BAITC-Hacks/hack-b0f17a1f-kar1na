export function createWindFarmControls(THREE,gltf){
 const root=gltf.scene, turbines=new Map(), originals=new Map(), rotations=new Map(), speeds=new Map();
 root.traverse(o=>{if(o.userData.assembly_id)turbines.set(o.userData.assembly_id,o);if(o.isMesh){originals.set(o,o.material);o.material=Array.isArray(o.material)?o.material.map(m=>m.clone()):o.material.clone();}});
 const get=id=>{const t=turbines.get(id);if(!t)throw new Error(`Unknown turbine: ${id}`);return t;};
 const component=(id,cid)=>{let found;get(id).traverse(o=>{if(o.userData.component_id===cid)found=o;});if(!found)throw new Error(`Unknown component: ${cid}`);return found;};
 for(const [id]of turbines){rotations.set(id,component(id,'rotor').quaternion.clone());speeds.set(id,0);}
 let selected=null,inspection=null;
 const mats=o=>Array.isArray(o.material)?o.material:[o.material];
 function paint(){
  for(const[o,original]of originals)mats(o).forEach((m,i)=>m.copy(Array.isArray(original)?original[i]:original));
  if(selected)get(selected).traverse(o=>{if(o.isMesh)mats(o).forEach(m=>{m.emissive?.setHex(0x125b62);m.emissiveIntensity=.16;});});
  if(inspection){const[id,cid]=inspection;const shell=component(id,'nacelle_shell');shell.traverse(o=>{if(o.isMesh)mats(o).forEach(m=>{m.transparent=true;m.opacity=.18;m.depthWrite=false;});});component(id,cid).traverse(o=>{if(o.isMesh)mats(o).forEach(m=>{m.emissive?.setHex(0x24e6c4);m.emissiveIntensity=.55;});});}
 }
 const focus=o=>{root.updateMatrixWorld(true);const boundingBox=new THREE.Box3().setFromObject(o);return{center:boundingBox.getCenter(new THREE.Vector3()),size:boundingBox.getSize(new THREE.Vector3()),boundingBox};};
 return{
 selectTurbine(id){get(id);selected=id;inspection=null;paint();return id;},
 clearSelection(){selected=null;inspection=null;paint();},
 inspectComponent(id,cid){component(id,cid);selected=id;inspection=[id,cid];paint();},
 resetInspection(){inspection=null;paint();},
 setRotorSpeed(id,speed){get(id);if(!Number.isFinite(speed))throw new Error('Speed must be finite');speeds.set(id,speed);},
 update(dt){if(!Number.isFinite(dt)||dt<0)return;for(const[id,speed]of speeds)component(id,'rotor').rotateX(speed*Math.min(dt,.1));},
 getTurbineId(object){for(let o=object;o;o=o.parent)if(o.userData.turbine_id||o.userData.assembly_id)return o.userData.turbine_id||o.userData.assembly_id;return null;},
 getFocusTarget(id){return focus(get(id));},getComponentFocusTarget(id,cid){return focus(component(id,cid));},
 applyTurbineState(id,state){get(id);if(Number.isFinite(state.windSpeed))this.setRotorSpeed(id,Math.max(0,Math.min(1.8,state.windSpeed*.06)));},
 reset(){selected=null;inspection=null;for(const[id,q]of rotations){component(id,'rotor').quaternion.copy(q);speeds.set(id,0);}paint();},
 dispose(){for(const[o,m]of originals){mats(o).forEach(m=>m.dispose());o.material=m;}},
 };
}
