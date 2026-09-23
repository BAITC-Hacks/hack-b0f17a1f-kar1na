// Object-space weathering stays attached to moving blades and inspection parts.
export function weatherTurbine(root) {
  const updated = new Set();
  root.traverse(object => {
    if (!object.isMesh || object.name === 'Ground') return;
    for (const material of [object.material].flat()) {
      if (!material?.isMeshStandardMaterial || updated.has(material)) continue;
      updated.add(material);
      const painted = material.color.r + material.color.g + material.color.b > 1.4;
      material.roughness = painted ? 0.78 : 0.58;
      material.metalness = painted ? 0.12 : Math.min(material.metalness, 0.75);
      if ('clearcoat' in material) material.clearcoat = 0;
      material.onBeforeCompile = shader => {
        shader.vertexShader = shader.vertexShader
          .replace('#include <common>', '#include <common>\nvarying vec3 vWearPosition;')
          .replace('#include <begin_vertex>', '#include <begin_vertex>\nvWearPosition = position;');
        shader.fragmentShader = shader.fragmentShader.replace('#include <common>', `
          #include <common>
          varying vec3 vWearPosition;
          float wearHash(vec3 p) {
            return fract(sin(dot(p, vec3(127.1,311.7,74.7))) * 43758.5453);
          }
          float wearNoise(vec3 p) {
            vec3 i = floor(p), f = fract(p);
            f = f*f*(3.0-2.0*f);
            return mix(mix(mix(wearHash(i),wearHash(i+vec3(1,0,0)),f.x),
                           mix(wearHash(i+vec3(0,1,0)),wearHash(i+vec3(1,1,0)),f.x),f.y),
                       mix(mix(wearHash(i+vec3(0,0,1)),wearHash(i+vec3(1,0,1)),f.x),
                           mix(wearHash(i+vec3(0,1,1)),wearHash(i+vec3(1,1,1)),f.x),f.y),f.z);
          }
        `).replace('#include <color_fragment>', `
          #include <color_fragment>
          vec3 wp = vWearPosition;
          float mottling = wearNoise(wp * 2.4);
          float grain = wearNoise(wp * 85.0);
          float streaks = smoothstep(0.56,0.85,wearNoise(wp * vec3(14.0,0.35,14.0)));
          float scuffs = smoothstep(0.67,0.87,wearNoise(wp * vec3(48.0,3.0,48.0)));
          float wear = 0.10 * mottling + 0.17 * streaks + 0.11 * scuffs;
          diffuseColor.rgb *= 1.0 - wear;
          diffuseColor.rgb = mix(diffuseColor.rgb, diffuseColor.rgb * vec3(0.83,0.87,0.91), streaks * 0.3);
          diffuseColor.rgb *= 0.97 + grain * 0.06;
        `).replace('#include <roughnessmap_fragment>', `
          #include <roughnessmap_fragment>
          roughnessFactor = clamp(roughnessFactor + 0.16 * streaks + 0.12 * grain, 0.45, 0.98);
        `);
      };
      material.customProgramCacheKey = () => 'windai-weathered-v1';
      material.needsUpdate = true;
    }
  });
}
