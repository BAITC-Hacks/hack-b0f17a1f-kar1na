// One continuous collage, aligned to the twin but extending through the header.
const application = document.querySelector('#application');
const panel = document.querySelector('.turbine-panel');
const overview = document.querySelector('#overview');
const artwork = document.createElement('div');
artwork.className = 'overview-art';
artwork.setAttribute('aria-hidden', 'true');
application.prepend(artwork);

function alignArtwork() {
  if (application.hidden || overview.hidden || !panel.clientWidth) return;
  const origin = application.getBoundingClientRect();
  const bounds = panel.getBoundingClientRect();
  const top = bounds.top - origin.top;
  artwork.style.left = `${bounds.left - origin.left}px`;
  artwork.style.width = `${bounds.width * 1.15}px`;
  artwork.style.height = `${top + bounds.height + 72}px`;
  artwork.style.setProperty('--panel-top', `${top}px`);
  artwork.style.setProperty('--panel-bottom', `${top + bounds.height}px`);
}
const observer = new ResizeObserver(alignArtwork);
[application, panel, document.querySelector('.app-header'), document.querySelector('.data-toolbar')].forEach(element => observer.observe(element));
addEventListener('hashchange', () => requestAnimationFrame(alignArtwork));
alignArtwork();
