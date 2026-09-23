import * as THREE from 'three';
import {blueprintSurface} from './twin-materials.js';

export function createBlueprint(root, bodyClip) {
  blueprintSurface(root);
  const parts = [];
  const meshes = [];
  root.traverse(object => { if (object.isMesh) meshes.push(object); });
  const clipMaterial = (material, blade) => {
    if (blade) return;
    const surfaceShader = material.onBeforeCompile;
    const surfaceKey = material.customProgramCacheKey();
    material.onBeforeCompile = shader => {
      surfaceShader.call(material, shader);
      shader.uniforms.bodyClip = bodyClip;
      shader.fragmentShader = shader.fragmentShader
        .replace('#include <common>', '#include <common>\nuniform vec4 bodyClip;')
        .replace('#include <clipping_planes_fragment>', `#include <clipping_planes_fragment>
          if(gl_FragCoord.x<bodyClip.x || gl_FragCoord.y<bodyClip.y || gl_FragCoord.x>bodyClip.z || gl_FragCoord.y>bodyClip.w) discard;`);
    };
    material.customProgramCacheKey = () => `${surfaceKey}-blueprint-panel-clip-v2`;
  };
  for (const mesh of meshes) {
    const blade = /^blade_\d+$/.test(mesh.userData.component_id ?? '');
    mesh.castShadow = true;
    mesh.receiveShadow = true;
    for (const material of [mesh.material].flat()) clipMaterial(material, blade);
    const lineMaterial = new THREE.LineBasicMaterial({color:0x2455df, transparent:true, opacity:0.8, depthWrite:false});
    clipMaterial(lineMaterial, blade);
    const outline = new THREE.LineSegments(new THREE.EdgesGeometry(mesh.geometry, 24), lineMaterial);
    outline.raycast = () => {};
    mesh.add(outline);
    parts.push({mesh, outline, opacity:0.94, color:new THREE.Color(0xf5f8ff), lineOpacity:0.85, lineColor:new THREE.Color(0x2452cf)});
  }
  let initialized=false;
  const setState = (component = null, exploded = false) => {
    for (const part of parts) {
      const {mesh, outline}=part;
      let active = false;
      for (let parent = mesh; parent; parent = parent.parent) {
        const id = parent.userData.component_id;
        if (component ? id === component : ['generator','gearbox','main_shaft'].includes(id)) active = true;
      }
      const inspecting = !!component || exploded;
      const faded = inspecting && !active;
      part.targetOpacity=faded ? 0.09 : 1;
      part.targetColor=new THREE.Color(active && inspecting ? 0xd3e4ff : 0xf5f8ff);
      part.targetLineOpacity=faded ? 0.14 : 0.48;
      part.targetLineColor=new THREE.Color(active && inspecting ? 0x003bff : 0x2452cf);
      if(!initialized){part.opacity=part.targetOpacity;part.color.copy(part.targetColor);part.lineOpacity=part.targetLineOpacity;part.lineColor.copy(part.targetLineColor);}
      for (const material of [mesh.material].flat()) {
        material.color.copy(part.color);
        material.emissive?.setHex(0x153365);
        material.emissiveIntensity = 0.07;
        material.roughness = 0.48;
        material.metalness = 0.16;
        material.envMapIntensity = 0.65;
        material.transparent = true;
        material.opacity = part.opacity;
        material.depthWrite = !faded;
        material.polygonOffset = true;
        material.polygonOffsetFactor = 1;
        material.polygonOffsetUnits = 1;
        material.needsUpdate = true;
      }
      outline.material.opacity = part.lineOpacity;
      outline.material.color.copy(part.lineColor);
      mesh.renderOrder = faded ? 2 : 0;
      outline.renderOrder = faded ? 3 : 1;
    }
    initialized=true;
  };
  setState.update = dt => {
    const alpha=1-Math.exp(-7*dt);
    for(const part of parts){
      part.opacity=THREE.MathUtils.lerp(part.opacity,part.targetOpacity,alpha);
      part.lineOpacity=THREE.MathUtils.lerp(part.lineOpacity,part.targetLineOpacity,alpha);
      part.color.lerp(part.targetColor,alpha);part.lineColor.lerp(part.targetLineColor,alpha);
      for(const material of [part.mesh.material].flat()){
        material.opacity=part.opacity;material.color.copy(part.color);
      }
      part.outline.material.opacity=part.lineOpacity;
      part.outline.material.color.copy(part.lineColor);
    }
  };
  return setState;
}
