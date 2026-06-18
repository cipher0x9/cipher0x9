/* ═══════════════════════════════════════════════
   CYPHER MONKEY — Main JavaScript
   Smooth scroll · Theme toggle · Particles · Nav
   ═══════════════════════════════════════════════ */

/* ── THEME TOGGLE ── */
const themeBtn = document.getElementById('theme-toggle');

function applyTheme(theme) {
  if (theme === 'light') {
    document.body.classList.add('light');
    themeBtn.textContent = '🌙';
  } else {
    document.body.classList.remove('light');
    themeBtn.textContent = '☀️';
  }
}

// Load saved preference (default: dark)
const savedTheme = localStorage.getItem('cm-theme') || 'dark';
applyTheme(savedTheme);

themeBtn.addEventListener('click', () => {
  const next = document.body.classList.contains('light') ? 'dark' : 'light';
  applyTheme(next);
  localStorage.setItem('cm-theme', next);
});

/* ── HAMBURGER MOBILE MENU ── */
const hamburger = document.getElementById('hamburger');
const mobileMenu = document.getElementById('mobile-menu');

hamburger.addEventListener('click', () => {
  hamburger.classList.toggle('open');
  mobileMenu.classList.toggle('open');
});

// Close mobile menu when a link is clicked
mobileMenu.querySelectorAll('a').forEach(link => {
  link.addEventListener('click', () => {
    hamburger.classList.remove('open');
    mobileMenu.classList.remove('open');
  });
});

/* ── SMOOTH SCROLL FOR NAV LINKS ── */
document.querySelectorAll('a[href^="#"]').forEach(anchor => {
  anchor.addEventListener('click', e => {
    e.preventDefault();
    const target = document.querySelector(anchor.getAttribute('href'));
    if (target) {
      // Offset by nav height (60px)
      const offset = 60;
      const top = target.getBoundingClientRect().top + window.pageYOffset - offset;
      window.scrollTo({ top, behavior: 'smooth' });
    }
  });
});

/* ── INTERSECTION OBSERVER (scroll reveal) ── */
const revealObserver = new IntersectionObserver(
  (entries) => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        entry.target.classList.add('visible');
        revealObserver.unobserve(entry.target); // animate once
      }
    });
  },
  { threshold: 0.12 }
);

document.querySelectorAll('.reveal').forEach(el => revealObserver.observe(el));

/* ── CANVAS PARTICLE SYSTEM ── */
// Unified particle engine reused from the original cypher-monkey-living.html
const canvas = document.getElementById('particles-canvas');
const ctx    = canvas.getContext('2d');
let W, H;

function resizeCanvas() {
  W = canvas.width  = window.innerWidth;
  H = canvas.height = window.innerHeight;
}
resizeCanvas();
window.addEventListener('resize', resizeCanvas);

// Color palette — CYPHER DNA
const COLORS = ['#00CED1', '#8B5CF6', '#F59E0B'];

// Sacred characters — binary + vedic symbols
const SYMBOLS = ['0', '1', 'ॐ', '𑁍', '∞', 'ᛯ', '🔱'];

const particles  = [];
const rainDrops  = [];

function spawnParticle(x, y) {
  return {
    x:     x ?? Math.random() * W,
    y:     y ?? Math.random() * H,
    vx:    (Math.random() - 0.5) * 0.7,
    vy:    (Math.random() - 0.5) * 0.7 - 0.3,
    size:  Math.random() * 2 + 0.5,
    color: COLORS[Math.floor(Math.random() * COLORS.length)],
    life:  1,
    decay: Math.random() * 0.004 + 0.002,
    isSym: Math.random() > 0.88,
    char:  SYMBOLS[Math.floor(Math.random() * SYMBOLS.length)],
  };
}

// Seed initial particles
for (let i = 0; i < 100; i++) {
  particles.push(spawnParticle());
}

// Binary rain column spawner
function spawnRain() {
  rainDrops.push({
    x:       Math.random() * W,
    y:       -20,
    speed:   Math.random() * 1.5 + 0.8,
    char:    Math.random() > 0.5 ? '1' : '0',
    opacity: Math.random() * 0.12 + 0.02,
    color:   Math.random() > 0.5 ? '#00CED1' : '#8B5CF6',
  });
  // Cap rain pool size
  if (rainDrops.length > 60) rainDrops.shift();
}

// Click / tap burst
canvas.addEventListener('click', (e) => {
  for (let i = 0; i < 25; i++) {
    const p   = spawnParticle(e.clientX, e.clientY);
    p.vx      = (Math.random() - 0.5) * 6;
    p.vy      = (Math.random() - 0.5) * 6;
    p.size    = Math.random() * 4 + 1;
    p.life    = 1.5;
    p.decay   = 0.015;
    particles.push(p);
  }
});

function drawParticles() {
  ctx.clearRect(0, 0, W, H);

  // Dots & symbol particles
  for (let i = particles.length - 1; i >= 0; i--) {
    const p = particles[i];
    p.x += p.vx;
    p.y += p.vy;
    p.life -= p.decay;
    if (p.life <= 0) { particles.splice(i, 1); continue; }

    ctx.globalAlpha = p.life * 0.55;
    if (p.isSym) {
      ctx.fillStyle = p.color;
      ctx.font = `${p.size * 8}px monospace`;
      ctx.fillText(p.char, p.x, p.y);
    } else {
      ctx.fillStyle = p.color;
      ctx.beginPath();
      ctx.arc(p.x, p.y, p.size, 0, Math.PI * 2);
      ctx.fill();
    }
  }

  // Binary rain
  if (Math.random() > 0.55) spawnRain();
  for (let i = rainDrops.length - 1; i >= 0; i--) {
    const r = rainDrops[i];
    r.y += r.speed;
    if (r.y > H + 20) { rainDrops.splice(i, 1); continue; }
    ctx.globalAlpha = r.opacity;
    ctx.fillStyle   = r.color;
    ctx.font        = '11px monospace';
    ctx.fillText(r.char, r.x, r.y);
  }

  // Replenish pool
  if (particles.length < 70 && Math.random() > 0.65) {
    particles.push(spawnParticle());
  }

  ctx.globalAlpha = 1;
  requestAnimationFrame(drawParticles);
}
drawParticles();

/* ── ACTIVE NAV LINK HIGHLIGHT ── */
// Highlights the nav link matching the current visible section
const sections  = document.querySelectorAll('section[id], div[id].section-alt');
const navAnchors = document.querySelectorAll('.nav-links a');

const navObserver = new IntersectionObserver(
  (entries) => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        const id = entry.target.id;
        navAnchors.forEach(a => {
          a.style.color = a.getAttribute('href') === `#${id}` ? 'var(--cyan)' : '';
        });
      }
    });
  },
  { rootMargin: '-40% 0px -40% 0px' }
);

document.querySelectorAll('section[id]').forEach(sec => navObserver.observe(sec));
