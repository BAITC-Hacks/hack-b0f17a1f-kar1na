import * as THREE from 'three';

export function createBlueprint(root, bodyClip) {
  const parts = [];
  const meshes = [];
  root.traverse(object => { if (object.isMesh) meshes.push(object); });
  const clipMaterial = (material, blade) => {
    if (blade) return;
    material.onBeforeCompile = shader => {
      shader.uniforms.bodyClip = bodyClip;
      shader.fragmentShader = shader.fragmentShader
        .replace('#include <common>', '#include <common>\nuniform vec4 bodyClip;')
        .replace('#include <clipping_planes_fragment>', `#include <clipping_planes_fragment>
          if(gl_FragCoord.x<bodyClip.x || gl_FragCoord.y<bodyClip.y || gl_FragCoord.x>bodyClip.z || gl_FragCoord.y>bodyClip.w) discard;`);
    };
    material.customProgramCacheKey = () => 'blueprint-panel-clip-v1';
  };
  for (const mesh of meshes) {
    const blade = /^blade_\d+$/.test(mesh.userData.component_id ?? '');
    mesh.castShadow = false;
    mesh.receiveShadow = false;
    for (const material of [mesh.material].flat()) clipMaterial(material, blade);
    const lineMaterial = new THREE.LineBasicMaterial({color:0x2455df, transparent:true, opacity:0.8, depthWrite:false});
    clipMaterial(lineMaterial, blade);
    const outline = new THREE.LineSegments(new THREE.EdgesGeometry(mesh.geometry, 24), lineMaterial);
    outline.raycast = () => {};
    mesh.add(outline);
    parts.push({mesh, outline});
  }
  return (component = null, exploded = false) => {
    for (const {mesh, outline} of parts) {
      let active = false;
      for (let parent = mesh; parent; parent = parent.parent) {
        const id = parent.userData.component_id;
        if (component ? id === component : ['generator','gearbox','main_shaft'].includes(id)) active = true;
      }
      const inspecting = !!component || exploded;
      const faded = inspecting && !active;
      for (const material of [mesh.material].flat()) {
        material.color.setHex(active && inspecting ? 0xd3e4ff : 0xf1f6ff);
        material.emissive?.setHex(0x153365);
        material.emissiveIntensity = 0.12;
        material.roughness = 1;
        material.metalness = 0;
        material.envMapIntensity = 0;
        material.transparent = true;
        material.opacity = faded ? 0.09 : 0.94;
        material.depthWrite = !faded;
        material.polygonOffset = true;
        material.polygonOffsetFactor = 1;
        material.polygonOffsetUnits = 1;
        material.needsUpdate = true;
      }
      outline.material.opacity = faded ? 0.14 : 0.85;
      outline.material.color.setHex(active && inspecting ? 0x003bff : 0x3562ce);
      mesh.renderOrder = faded ? 2 : 0;
      outline.renderOrder = faded ? 3 : 1;
    }
  };
}
