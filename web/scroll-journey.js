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
  // Dissolve from the white hero and back into the white closing artwork.
  const white = Math.max(1 - progress / .1, (progress - .91) / .09, 0);
  journey.style.setProperty('--journey-white', clamp(white));
  journey.querySelector('.journey-percent').textContent = `${String(Math.round(progress * 100)).padStart(2, '0')}%`;
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

const targets = journey.querySelectorAll('.section-index, h2, .intro p, .process-lines > div, .agent-story article, .twin-copy p, .twin-copy .button');
if ('IntersectionObserver' in window) {
  const observer = new IntersectionObserver(entries => {
    for (const entry of entries) {
      if (entry.isIntersecting) {
        entry.target.classList.add('is-revealed');
        observer.unobserve(entry.target);
      }
    }
  }, {threshold:.12, rootMargin:'0px 0px -6% 0px'});
  targets.forEach((element, i) => {
    element.classList.add('scroll-reveal');
    element.style.setProperty('--reveal-delay', `${(i % 3) * 65}ms`);
    observer.observe(element);
  });
}
schedule();
