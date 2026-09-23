// Object-space drafting lines stay attached to rotating and exploded parts.
export function blueprintSurface(root) {
  const updated = new Set();
  root.traverse(object => {
    if (!object.isMesh || object.name === 'Ground') return;
    for (const material of [object.material].flat()) {
      if (!material?.isMeshStandardMaterial || updated.has(material)) continue;
      updated.add(material);
      material.onBeforeCompile = shader => {
        shader.vertexShader = shader.vertexShader
          .replace('#include <common>', '#include <common>\nvarying vec3 vDraftPosition;')
          .replace('#include <begin_vertex>', '#include <begin_vertex>\nvDraftPosition = position;');
        shader.fragmentShader = shader.fragmentShader
          .replace('#include <common>', `#include <common>
            varying vec3 vDraftPosition;
            float draftingGrid(vec3 p) {
              vec3 width = max(fwidth(p), vec3(0.0001));
              vec3 line = 1.0 - smoothstep(width * 0.35, width * 1.1, abs(fract(p - 0.5) - 0.5));
              // Suppress perpendicular axes to avoid solid blue faces.
              line *= smoothstep(vec3(0.0001), vec3(0.005), fwidth(p));
              return max(max(line.x, line.y), line.z);
            }`)
          .replace('#include <color_fragment>', `#include <color_fragment>
            float fineGrid = draftingGrid(vDraftPosition * 2.0);
            float majorGrid = draftingGrid(vDraftPosition * 0.25);
            diffuseColor.rgb = mix(diffuseColor.rgb, vec3(0.12, 0.30, 0.80), fineGrid * 0.13 + majorGrid * 0.17);
          `);
      };
      material.customProgramCacheKey = () => 'windai-drafting-surface-v1';
      material.needsUpdate = true;
    }
  });
}
