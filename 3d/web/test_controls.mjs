import * as THREE from 'three';import{GLTFLoader}from'three/addons/loaders/GLTFLoader.js';import{readFileSync,writeFileSync}from'node:fs';import assert from'node:assert/strict';import{createWindFarmControls}from'./wind_farm_controls.mjs';
const data=readFileSync(new URL('../models/wind_farm.glb',import.meta.url));const gltf=await new GLTFLoader().parseAsync(data.buffer.slice(data.byteOffset,data.byteOffset+data.byteLength),'');const f=createWindFarmControls(THREE,gltf),get=n=>gltf.scene.getObjectByName(n),checks=[];
const initial=new Map();gltf.scene.traverse(o=>{if(o.isMesh)initial.set(o,o.material.clone());});
f.selectTurbine('turbine_1');assert(get('T1_Tower').material.emissiveIntensity>0);assert.equal(get('T2_Tower').material.emissiveIntensity,initial.get(get('T2_Tower')).emissiveIntensity);checks.push('independent highlight');
f.selectTurbine('turbine_2');assert.equal(get('T1_Tower').material.emissive.getHex(),initial.get(get('T1_Tower')).emissive.getHex());checks.push('selection switch');
for(const cid of ['generator','gearbox','main_shaft']){f.inspectComponent('turbine_1',cid);get('T1_NacelleShell').traverse(o=>{if(o.isMesh)assert.equal(o.material.opacity,.18)});f.resetInspection();get('T1_NacelleShell').traverse(o=>{if(o.isMesh)assert.equal(o.material.opacity,1)});}checks.push('all internal inspections and restoration');
f.clearSelection();for(const[o,m]of initial){assert.equal(o.material.opacity,m.opacity);assert.equal(o.material.emissive.getHex(),m.emissive.getHex());}checks.push('clear restores materials');
const q1=get('T1_Rotor').quaternion.clone(),q2=get('T2_Rotor').quaternion.clone();f.setRotorSpeed('turbine_1',1);f.update(.1);assert(!get('T1_Rotor').quaternion.equals(q1));assert(get('T2_Rotor').quaternion.equals(q2));assert.equal(f.getTurbineId(get('T2_Blade_2')),'turbine_2');checks.push('independent rotation and child picking');
assert(f.getComponentFocusTarget('turbine_1','generator').size.length()>0);f.reset();assert(get('T1_Rotor').quaternion.equals(q1));checks.push('focus bounds and deterministic reset');
console.log(checks);
const movable=[];gltf.scene.traverse(o=>{if(o.userData.explodable)movable.push([o,o.position.clone(),o.quaternion.clone()]);});
assert(movable.length>=20);
f.setNacelleExploded('turbine_1',1,1);f.update(.5);assert.equal(f.getExplodedAmount('turbine_1'),.5);assert.equal(f.getExplodedAmount('turbine_2'),0);
for(const[o,p]of movable.filter(([o])=>o.userData.turbine_id==='turbine_2'))assert(o.position.equals(p));
f.update(.5);assert.equal(f.getExplodedAmount('turbine_1'),1);
for(const[o]of movable.filter(([o])=>o.userData.turbine_id==='turbine_1'))assert(o.position.distanceTo(new THREE.Vector3().fromArray(o.userData.exploded_position))<1e-6);
const stopped=get('T1_Rotor').quaternion.clone();f.setRotorSpeed('turbine_1',1);f.update(.1);assert(get('T1_Rotor').quaternion.equals(stopped));
for(let i=0;i<15;i++){f.setNacelleExploded('turbine_1',.75,0);f.setNacelleExploded('turbine_1',0,0);}
for(const[o,p]of movable)assert(o.position.distanceTo(p)<1e-6);
f.setNacelleExploded('turbine_2',1,0);f.reset();for(const[o,p,q]of movable){assert(o.position.distanceTo(p)<1e-6);assert(o.quaternion.equals(q));}
checks.push('animated disassembly midpoint and endpoint','independent turbine disassembly','rotor paused during disassembly','15 repeated reassemblies without drift','reset restores every movable component');
writeFileSync(new URL('../reports/web_validation.json',import.meta.url),JSON.stringify({status:'PASS',three_revision:THREE.REVISION,checks},null,2));console.log('Disassembly PASS');
