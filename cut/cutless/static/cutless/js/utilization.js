/* Presentación del aprovechamiento: no modifica los valores del cálculo. */
(() => {
  'use strict';
  const channels = new Map();
  const motion = matchMedia('(prefers-reduced-motion: reduce)');
  const clamp = value => Math.min(100, Math.max(0, Number(value) || 0));
  const stops = [[217, 0, 0], [145, 114, 32], [0, 135, 61]];

  function color(value) {
    const position = clamp(value) / 50;
    const index = Math.min(1, Math.floor(position));
    const fraction = position - index;
    return `rgb(${stops[index].map((component, i) =>
      Math.round(component + (stops[index + 1][i] - component) * fraction)).join(', ')})`;
  }

  function show(root, channel, initial) {
    const graph = root?.querySelector('[data-utilization]');
    const circle = graph?.querySelector('.donut-value');
    if (!circle) return;
    const target = clamp(graph.dataset.utilization);
    const previous = channels.get(channel);
    if (previous) cancelAnimationFrame(previous.frame);
    const state = {value: previous?.value ?? clamp(initial ?? target), frame: null};
    channels.set(channel, state);
    const start = state.value;
    function paint(value) {
      state.value = value;
      circle.setAttribute('pathLength', '100');
      circle.setAttribute('stroke-dasharray', `${value} 100`);
      circle.style.stroke = color(value);
    }
    paint(start);
    if (motion.matches || start === target) { paint(target); return; }
    const began = performance.now();
    function tick(now) {
      const progress = Math.min(1, (now - began) / 650);
      // Si cambia la preferencia durante la transición, terminar sin movimiento.
      const eased = 1 - Math.pow(1 - progress, 3);
      paint(motion.matches ? target : start + (target - start) * eased);
      if (progress < 1 && !motion.matches) state.frame = requestAnimationFrame(tick);
    }
    state.frame = requestAnimationFrame(tick);
  }

  window.CutlessUtilization = {show};
  const total = document.querySelector('.total-utilization');
  if (total) show(total, 'total');
})();
