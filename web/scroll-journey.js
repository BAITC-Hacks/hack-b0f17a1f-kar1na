const journey = document.querySelector('#wind-journey');
const video = document.querySelector('#journey-video');
const reducedMotion = matchMedia('(prefers-reduced-motion: reduce)');
const clamp = n => Math.max(0, Math.min(1, n));
let targetTime = 0;
let scheduled = false;

function seek() {
  if (reducedMotion.matches || video.seeking || video.readyState < 1) return;
  if (Math.abs(video.currentTime - targetTime) > .045) {
    try { video.currentTime = targetTime; } catch { /* Metadata may change during loading. */ }
  }
}
function update() {
  scheduled = false;
  if (document.querySelector('#landing').hidden) return;
  const rect = journey.getBoundingClientRect();
  const progress = clamp(-rect.top / Math.max(1, rect.height - innerHeight));
  journey.style.setProperty('--journey-progress', progress);
  // Spatial fades at the edges keep the film visible throughout the story.
  journey.style.setProperty('--journey-white', 0);
  journey.querySelectorAll('.journey-popup').forEach((card, index) => {
    const box = card.getBoundingClientRect();
    const enter = clamp((innerHeight - box.top) / (innerHeight * .32));
    const leave = clamp(box.bottom / (innerHeight * .22));
    const amount = reducedMotion.matches ? 1 : Math.min(enter, leave);
    const eased = amount * amount * (3 - 2 * amount);
    card.style.setProperty('--popup-opacity', eased);
    card.style.setProperty('--popup-x', `${(1 - eased) * (index % 2 ? 110 : -110)}px`);
    card.style.setProperty('--popup-scale', .96 + eased * .04);
  });
  if (Number.isFinite(video.duration)) {
    targetTime = progress * Math.max(0, video.duration - .05);
    seek();
  }
}
function schedule() {
  if (!scheduled) { scheduled = true; requestAnimationFrame(update); }
}
video.addEventListener('loadedmetadata', schedule);
video.addEventListener('loadeddata', schedule);
video.addEventListener('seeked', seek);
video.addEventListener('error', () => journey.classList.add('video-unavailable'));
addEventListener('scroll', schedule, {passive:true});
addEventListener('resize', schedule);
addEventListener('hashchange', schedule);
reducedMotion.addEventListener('change', schedule);

// Reveal whole cards from alternating sides, in both scroll directions.
schedule();
