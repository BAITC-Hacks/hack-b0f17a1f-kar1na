// Keep the native SVG cursor as a fallback until the animated cursor is positioned.
const finePointer = matchMedia('(hover: hover) and (pointer: fine)');
const cursor = document.createElement('div');
cursor.className = 'animated-turbine-cursor';
cursor.setAttribute('aria-hidden', 'true');
cursor.innerHTML = `<svg xmlns="http://www.w3.org/2000/svg" width="32" height="32" viewBox="0 0 32 32">
  <g fill="#0734ff" stroke="#fff" stroke-width="1.1" stroke-linejoin="round">
    <path d="M15 15h2l1.5 15h-5z"/>
    <g class="cursor-rotor">
      <path d="M15.7 13.8C13.8 10.2 14.7 4.8 17 1l1 10.3-1.1 3z"/>
      <path d="M14.9 14.8C11 15 6.6 18.4 3.5 24l9.5-4.9 2.9-3.1z"/>
      <path d="M17.1 14.6c4 .1 8.4 3.6 11.4 9.1l-9.4-4.8-3-3z"/>
    </g>
    <circle cx="16" cy="15" r="2.7"/>
  </g>
</svg>`;
document.body.append(cursor);
const hide = () => document.documentElement.classList.remove('turbine-cursor-active');
window.addEventListener('pointermove', event => {
  if (!finePointer.matches || event.pointerType === 'touch') {
    hide();
    return;
  }
  cursor.style.transform = `translate3d(${event.clientX - 16}px,${event.clientY - 15}px,0)`;
  document.documentElement.classList.add('turbine-cursor-active');
}, {passive: true});
document.documentElement.addEventListener('pointerleave', hide);
window.addEventListener('blur', hide);
window.addEventListener('pointerdown', event => {
  if (event.pointerType === 'touch') hide();
}, {passive: true});
document.addEventListener('visibilitychange', () => {
  if (document.hidden) hide();
});
finePointer.addEventListener('change', hide);
