// Observe individual cards so the entrance follows the responsive layout.
export function createOverviewMotion() {
  const root = document.querySelector('#overview');
  const reducedMotion = matchMedia('(prefers-reduced-motion: reduce)');
  if (!('IntersectionObserver' in window) || reducedMotion.matches) return () => {};

  const cards = [...root.querySelectorAll([
    '.telemetry-panel > .eyebrow', '.turbine-info > .select-row',
    '.turbine-info > h2', '.turbine-info > p', '.metric-trio > div',
    '.telemetry-note', '.turbine-panel', '.forecast-panel', '.agent-panel',
    '.summary-tile', '.lower-dashboard .panel',
  ].join(','))];
  const observer = new IntersectionObserver(entries => {
    const entering = entries.filter(entry => entry.isIntersecting)
      .sort((a, b) => a.boundingClientRect.top - b.boundingClientRect.top
        || a.boundingClientRect.left - b.boundingClientRect.left);
    entering.forEach(({target}, index) => {
      target.style.setProperty('--reveal-delay', `${Math.min(index * 65, 325)}ms`);
      target.classList.add('is-revealed');
      observer.unobserve(target);
    });
  }, {threshold: 0, rootMargin: '0px 0px -24px 0px'});

  // Keyboard navigation must never land on an invisible control.
  root.addEventListener('focusin', event => {
    const card = event.target.closest('.overview-reveal');
    if (!card) return;
    card.style.setProperty('--reveal-delay', '0ms');
    card.classList.add('is-revealed');
    observer.unobserve(card);
  });
  reducedMotion.addEventListener('change', () => {
    if (!reducedMotion.matches) return;
    observer.disconnect();
    cards.forEach(card => card.classList.add('is-revealed'));
  });

  return () => {
    observer.disconnect();
    cards.forEach(card => {
      card.classList.add('overview-reveal');
      card.classList.toggle('is-revealed', reducedMotion.matches);
      card.style.setProperty('--reveal-delay', '0ms');
      if (!reducedMotion.matches) observer.observe(card);
    });
  };
}
