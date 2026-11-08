// Particules sur toile : chaque grain a sa taille, sa vitesse, son poids, sa durée
// et son scintillement ; aucune ne suit le pointeur. Une ambiance par rareté.

export const alea = (a, b) => a + Math.random() * (b - a);
export const choix = (t) => t[Math.floor(Math.random() * t.length)];

export function creerToile(parent) {
  const c = document.createElement('canvas');
  c.className = 'toile-fx';
  parent.append(c);
  const ctx = c.getContext('2d');
  const ps = [];
  let dpr = 1, W = 0, H = 0, tourne = false, dernier = 0;
  const taille = () => { dpr = Math.min(2, devicePixelRatio || 1); W = c.clientWidth; H = c.clientHeight; c.width = W * dpr; c.height = H * dpr; };
  taille(); addEventListener('resize', taille);

  function dessiner(p) {
    const vie = p.age / p.duree;
    const fondu = vie < .12 ? vie / .12 : 1 - Math.max(0, (vie - p.fin) / (1 - p.fin));
    const sc = p.scint ? .55 + .45 * Math.sin(p.age * p.scint + p.phase) : 1;
    const a = Math.max(0, fondu * sc * p.alpha);
    if (a <= .01) return;
    ctx.save();
    ctx.globalAlpha = a; ctx.globalCompositeOperation = 'lighter';
    ctx.translate(p.x, p.y); ctx.rotate(p.rot);
    ctx.fillStyle = p.couleur; ctx.shadowColor = p.couleur; ctx.shadowBlur = p.lueur;
    const r = p.r * (p.grossit ? .4 + vie * .9 : 1 - vie * .35);
    if (p.forme === 'etoile') {
      ctx.beginPath();
      for (let i = 0; i < 8; i++) { const ang = i * Math.PI / 4, rr = i % 2 ? r * .22 : r; ctx.lineTo(Math.cos(ang) * rr, Math.sin(ang) * rr); }
      ctx.closePath(); ctx.fill();
    } else if (p.forme === 'eclat') {
      // éclat de feuille holographique : un losange qui tourne et change de face
      const f = Math.abs(Math.cos(p.age * p.vflip));
      ctx.fillStyle = `hsl(${(p.teinte + p.age * 90) % 360} 90% ${55 + f * 25}%)`; ctx.shadowColor = ctx.fillStyle;
      ctx.beginPath(); ctx.moveTo(0, -r); ctx.lineTo(r * .6 * f + .3, 0); ctx.lineTo(0, r); ctx.lineTo(-r * .6 * f - .3, 0); ctx.closePath(); ctx.fill();
    } else if (p.forme === 'trait') {
      ctx.rotate(Math.atan2(p.vy, p.vx) - p.rot);
      const l = Math.min(40, Math.hypot(p.vx, p.vy) * 4 + r);
      const g = ctx.createLinearGradient(-l, 0, 0, 0); g.addColorStop(0, 'transparent'); g.addColorStop(1, p.couleur);
      ctx.fillStyle = g; ctx.fillRect(-l, -r * .35, l, r * .7);
    } else {
      ctx.beginPath(); ctx.arc(0, 0, r, 0, Math.PI * 2); ctx.fill();
    }
    ctx.restore();
  }
  function boucle(t) {
    const dt = Math.min(.05, (t - dernier) / 1000 || .016); dernier = t;
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0); ctx.clearRect(0, 0, W, H);
    for (let i = ps.length - 1; i >= 0; i--) {
      const p = ps[i];
      if (p.retard > 0) { p.retard -= dt; continue; }
      p.age += dt;
      if (p.age >= p.duree) { ps.splice(i, 1); continue; }
      p.vx += (p.ax + Math.sin(p.age * p.oscF + p.phase) * p.osc) * dt;
      p.vy += p.ay * dt;
      p.vx *= p.frein ** (dt * 60); p.vy *= p.frein ** (dt * 60);
      p.x += p.vx * dt * 60; p.y += p.vy * dt * 60;
      p.rot += p.vrot * dt;
      dessiner(p);
    }
    if (ps.length) requestAnimationFrame(boucle); else tourne = false;
  }
  function ajouter(o) {
    ps.push({ age: 0, retard: 0, x: W / 2, y: H / 2, vx: 0, vy: 0, ax: 0, ay: 0, frein: .97, r: 3, duree: 1.4, fin: .55, alpha: 1,
      rot: 0, vrot: 0, forme: 'rond', couleur: '#fff', lueur: 8, scint: 0, phase: Math.random() * 6.28, osc: 0, oscF: 3, vflip: alea(3, 9), teinte: 0, grossit: false, ...o });
    if (ps.at(-1).teinte === 'alea') ps.at(-1).teinte = Math.random() * 360;
    if (!tourne) { tourne = true; dernier = performance.now(); requestAnimationFrame(boucle); }
  }
  return { toile: c, ajouter, get centre() { return { x: W / 2, y: H * .46 }; }, detruire: () => { ps.length = 0; c.remove(); removeEventListener('resize', taille); } };
}

/* ---------- ambiances par rareté ---------- */
export function gerbe(fx, n, { vmin, vmax, couleurs, formes = ['rond'], rmin = 1.2, rmax = 3.5, ay = .03, frein = .95, duree = [.8, 1.6], lueur = 10, scint = 0, retard = 0, dx = 0, dy = 0, ...autres }) {
  const { x, y } = fx.centre;
  for (let i = 0; i < n; i++) {
    const a = Math.random() * Math.PI * 2, v = alea(vmin, vmax);
    fx.ajouter({ x: x + alea(-dx, dx), y: y + alea(-dy, dy), vx: Math.cos(a) * v, vy: Math.sin(a) * v, ay, frein, r: alea(rmin, rmax),
      duree: alea(...duree), couleur: choix(couleurs), forme: choix(formes), lueur, scint: scint ? alea(scint * .5, scint * 1.5) : 0,
      vrot: alea(-6, 6), retard: alea(0, retard), ...autres });
  }
}

export const AMBIANCES = {
  rare(fx) {
    gerbe(fx, 14, { vmin: 2, vmax: 6, couleurs: ['#ffffff', '#dfe8f2'], formes: ['etoile', 'rond'], rmin: 1.5, rmax: 5, ay: 0, frein: .9, duree: [.5, 1], dx: 90, dy: 120, scint: 18 });
  },
  epique(fx) {
    gerbe(fx, 26, { vmin: 3, vmax: 10, couleurs: ['#b69cff', '#d9ccff', '#7dd3fc', '#f0abfc'], formes: ['trait', 'rond'], rmin: 1.5, rmax: 3.2, ay: .02, frein: .93, duree: [.6, 1.3] });
    gerbe(fx, 10, { vmin: .5, vmax: 2, couleurs: ['#ffffff', '#d9ccff'], formes: ['etoile'], rmin: 3, rmax: 7, ay: -.01, frein: .97, duree: [1, 1.8], dx: 120, dy: 160, scint: 14, retard: .3 });
  },
  mythique(fx) {
    // une pluie d'éclats holographiques qui tournoient et retombent
    gerbe(fx, 44, { vmin: 4, vmax: 13, couleurs: ['#fff'], formes: ['eclat'], rmin: 3, rmax: 7, ay: .16, frein: .955, duree: [1.4, 2.6], teinte: 'alea', osc: .4, oscF: 4 });
    gerbe(fx, 18, { vmin: 1, vmax: 4, couleurs: ['#ff8fd6', '#67e8f9', '#fde68a', '#ffffff'], formes: ['etoile'], rmin: 2, rmax: 6, ay: 0, frein: .96, duree: [.8, 1.6], dx: 100, dy: 140, scint: 16, retard: .25 });
  },
  legendaire(fx) {
    const { x, y } = fx.centre;
    // gerbe d'étincelles dorées, puis des braises qui montent en ondulant
    gerbe(fx, 40, { vmin: 5, vmax: 15, couleurs: ['#fff3c4', '#f2c66d', '#ffb347'], formes: ['trait'], rmin: 1.4, rmax: 2.6, ay: .12, frein: .94, duree: [.6, 1.4] });
    for (let i = 0; i < 70; i++) {
      fx.ajouter({ x: x + alea(-150, 150), y: y + alea(80, 260), vx: alea(-.3, .3), vy: alea(-1.6, -.5), ay: -.004, frein: .995, r: alea(1, 3.4),
        duree: alea(1.8, 3.4), couleur: choix(['#ffd27a', '#f2c66d', '#fff3c4', '#ff9f43']), lueur: 12, scint: alea(6, 14), osc: alea(.3, 1.2), oscF: alea(1.5, 4), retard: alea(0, 1.4) });
    }
  },
  pantheon(fx) {
    const { x, y } = fx.centre;
    // explosion d'étoiles de tailles très diverses, freinées comme dans le vide
    gerbe(fx, 26, { vmin: 4, vmax: 16, couleurs: ['#ffffff', '#cdeefe', '#fff0c2', '#ffd6f0', '#c9fbe4'], formes: ['etoile'], rmin: 2, rmax: 11, ay: 0, frein: .925, duree: [1.4, 2.8], scint: 10, lueur: 16 });
    gerbe(fx, 60, { vmin: 1, vmax: 9, couleurs: ['#ffffff', '#9fd8ff', '#e2d8ff'], formes: ['rond'], rmin: .6, rmax: 1.8, ay: 0, frein: .94, duree: [1.6, 3.2], scint: 20, lueur: 6 });
    // poussière d'étoiles qui descend lentement sur toute la scène
    for (let i = 0; i < 90; i++) {
      fx.ajouter({ x: alea(0, x * 2), y: alea(-40, y * 2), vx: alea(-.15, .15), vy: alea(.15, .6), ay: 0, frein: 1, r: alea(.5, 2.2), duree: alea(3, 5.5), fin: .7,
        couleur: choix(['#ffffff', '#cdeefe', '#ffe9f6']), lueur: 8, scint: alea(3, 9), retard: alea(.4, 2.5) });
    }
    // anneaux : de grosses étoiles posées en cercle qui s'écartent
    for (let k = 0; k < 2; k++) for (let i = 0; i < 18; i++) {
      const a = i / 18 * Math.PI * 2;
      fx.ajouter({ x, y, vx: Math.cos(a) * (6 + k * 3), vy: Math.sin(a) * (6 + k * 3), frein: .92, r: 2.2, duree: 1.6, forme: 'etoile', couleur: k ? '#ffd6f0' : '#9fd8ff', lueur: 14, retard: .15 + k * .25, vrot: 2 });
    }
  },
};
