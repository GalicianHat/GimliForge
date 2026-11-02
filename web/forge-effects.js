const canvas = document.getElementById('forge-effects');
if (canvas && !matchMedia('(prefers-reduced-motion: reduce)').matches) {
  const context = canvas.getContext('2d');
  const flames = Array.from({length: 46}, (_, index) => ({
    x: (index + .5) / 46,
    height: 32 + Math.random() * 75,
    phase: Math.random() * Math.PI * 2,
    speed: .002 + Math.random() * .002
  }));
  let width = 1, height = 1, nextBolt = 0, bolt = null;
  function resize() {
    const ratio = Math.min(devicePixelRatio || 1, 2);
    width = innerWidth; height = innerHeight;
    canvas.width = Math.round(width * ratio);
    canvas.height = Math.round(height * ratio);
    context.setTransform(ratio, 0, 0, ratio, 0, 0);
  }
  addEventListener('resize', resize);
  resize();
  function makeBolt(now) {
    const startX = width * (.05 + Math.random() * .9);
    const startY = height * (.02 + Math.random() * .58);
    const points = [[startX, startY]];
    const step = height * (.018 + Math.random() * .016);
    for (let i = 1; i <= 11; i++) {
      const previous = points[i - 1];
      points.push([Math.max(12, Math.min(width - 12, previous[0] + (Math.random() - .5) * 54)),
                   startY + i * step]);
    }
    const branches = [3, 6, 8].map(index => {
      const arm = [points[index]];
      const direction = Math.random() < .5 ? -1 : 1;
      for (let i = 1; i <= 4; i++) {
        arm.push([arm[i - 1][0] + direction * (10 + Math.random() * 22),
                  arm[i - 1][1] + step * .65]);
      }
      return arm;
    });
    return {points, branches, until: now + 170};
  }
  function strokeBolt(points, alpha, thickness) {
    context.beginPath();
    points.forEach(([x, y], index) => index ? context.lineTo(x, y) : context.moveTo(x, y));
    context.strokeStyle = `rgba(255,214,132,${alpha})`;
    context.lineWidth = thickness;
    context.shadowColor = '#ffbd65';
    context.shadowBlur = 22;
    context.stroke();
    context.strokeStyle = `rgba(255,251,225,${alpha})`;
    context.lineWidth = Math.max(.6, thickness * .35);
    context.shadowBlur = 4;
    context.stroke();
    context.shadowBlur = 0;
  }
  function drawFire(now) {
    const glow = context.createRadialGradient(width / 2, height + 20, 10, width / 2, height + 20, width * .62);
    glow.addColorStop(0, 'rgba(220,75,16,.24)');
    glow.addColorStop(.45, 'rgba(169,49,10,.12)');
    glow.addColorStop(1, 'rgba(169,49,10,0)');
    context.fillStyle = glow;
    context.fillRect(0, height - 210, width, 210);
    for (const flame of flames) {
      const x = flame.x * width;
      const pulse = .7 + .3 * Math.sin(now * flame.speed + flame.phase);
      const top = height - flame.height * pulse;
      const bend = Math.sin(now * flame.speed * 1.4 + flame.phase) * 13;
      const half = Math.max(12, width / 56);
      const gradient = context.createLinearGradient(x, height, x, top);
      gradient.addColorStop(0, 'rgba(255,106,25,.35)');
      gradient.addColorStop(.55, 'rgba(255,147,43,.2)');
      gradient.addColorStop(1, 'rgba(255,206,91,0)');
      context.fillStyle = gradient;
      context.beginPath();
      context.moveTo(x - half, height);
      context.quadraticCurveTo(x - half * .65, top + 25, x + bend, top);
      context.quadraticCurveTo(x + half * .7, top + 30, x + half, height);
      context.closePath();
      context.fill();
    }
  }
  function frame(now) {
    context.clearRect(0, 0, width, height);
    drawFire(now);
    if (now > nextBolt) {bolt = makeBolt(now); nextBolt = now + 950 + Math.random() * 1150;}
    if (bolt && now < bolt.until) {
      const alpha = .52 + .4 * Math.random();
      strokeBolt(bolt.points, alpha, 2.6);
      bolt.branches.forEach(branch => strokeBolt(branch, alpha * .55, 1.3));
    }
    requestAnimationFrame(frame);
  }
  requestAnimationFrame(frame);
}
