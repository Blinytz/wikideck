// Ouverture v3 : on déchire le paquet en suivant son propre tracé, puis on
// retourne les cartes une à une. Le dos est le même pour toutes : la rareté ne
// se lit qu'à la face. Chaque carte révélée se manipule en 3D.

import { htmlCarte, brancherManipulation, RARETES, esc } from './carte.js';
import { creerToile, AMBIANCES } from './particules.js';
import { son } from './son.js';

const ORDRE = Object.fromEntries(RARETES.map((r, i) => [r, i]));
const COULEURS = { rare: '#cfdbe8', epique: '#b69cff', mythique: '#ff8fd6', legendaire: '#f2c66d', pantheon: '#ffffff' };
const attendre = (ms) => new Promise((r) => setTimeout(r, ms));
const vibrer = (m) => { try { navigator.vibrate?.(m); } catch {} };
const phrase = (d) => { const s = (d || '').replace(/\s*\([^)]*\)/g, '').replace(/\s+/g, ' ').trim(); const m = s.match(/^.{50,240}?[.!?](\s|$)/); return m ? m[0].trim() : (s.length > 220 ? s.slice(0, 220) + '…' : s); };

// tirage = [{ carte, neuve }] ; renvoie une promesse résolue à la fermeture
// options d'essai : `direct` saute la déchirure ; `avant(r, ctx)` joue une anticipation avant le retournement ;
// `effet(r, ctx)` remplace l'effet de révélation (s'il renvoie undefined, l'effet habituel est joué)
export function ouvrirPaquet(tirage, { nom = 'WikiDeck', direct = false, avant = null, effet: effetPerso = null, classe = '' } = {}) {
  const suite = tirage.map((t, i) => ({ ...t, i })).sort((a, b) => ORDRE[a.carte.rarete] - ORDRE[b.carte.rarete] || a.i - b.i);
  const ov = document.createElement('div');
  ov.className = 'ov2' + (classe ? ' ' + classe : '');
  const marque = `<div class="pk-marque"><div class="k-mono">W</div><div class="pk-nom">${esc(nom)}</div><div class="pk-nb">${suite.length} CARTE${suite.length > 1 ? 'S' : ''}</div></div>`;
  ov.innerHTML = `
    <div class="ov2-voile"></div>
    <div class="ov2-fx"></div>
    <div class="ov2-scene">
      <div class="pk-boite"><div class="pk">
        <div class="pk-part pk-corps">${marque}</div>
        <div class="pk-part pk-haut">${marque}</div>
        <svg class="pk-trace"><polyline/></svg>
        <i class="ph ph-hand-pointing pk-guide"></i>
      </div></div>
    </div>
    <div class="ov2-legende"></div>
    <div class="ov2-flash"></div>
    <div class="ov2-haut"><span class="ov2-compte"></span><button class="ov2-btn" aria-label="Passer"><i class="ph ph-fast-forward"></i></button></div>`;
  document.body.append(ov);
  const fxBox = ov.querySelector('.ov2-fx');
  const toile = creerToile(ov);

  return new Promise((fin) => {
    if (direct) queueMicrotask(() => { ov.querySelector('.pk-boite').remove(); afficherPile(); verrou = false; prendre(); });
    const scene = ov.querySelector('.ov2-scene');
    const compte = ov.querySelector('.ov2-compte');
    const passer = ov.querySelector('.ov2-btn');
    const legende = ov.querySelector('.ov2-legende');
    passer.style.visibility = 'hidden';

    // ---------- 1. déchirer en suivant le doigt ----------
    const pk = ov.querySelector('.pk'), boite = ov.querySelector('.pk-boite');
    const trace = pk.querySelector('polyline');
    let pts = null, fait = false;
    const bande = () => ({ h: pk.offsetHeight, w: pk.offsetWidth, min: pk.offsetHeight * .06, max: pk.offsetHeight * .3 });
    const local = (e) => { const r = pk.getBoundingClientRect(); return { x: e.clientX - r.left, y: e.clientY - r.top }; };
    const dessinerTrace = () => trace.setAttribute('points', pts.map((p) => `${p.x.toFixed(1)},${p.y.toFixed(1)}`).join(' '));
    pk.addEventListener('pointerdown', (e) => {
      if (fait) return;
      const b = bande(), p = local(e);
      if (p.y > b.max + b.h * .12 || p.x > b.w * .35) { secouer(); return; }
      pts = [{ x: Math.max(0, p.x), y: Math.min(b.max, Math.max(b.min, p.y)) }];
      pk.classList.add('trace'); boite.classList.add('tenu');
      try { pk.setPointerCapture(e.pointerId); } catch {}
    });
    pk.addEventListener('pointermove', (e) => {
      if (!pts || fait) return;
      const b = bande(), p = local(e), der = pts.at(-1);
      if (p.x <= der.x + 1) return;   // la déchirure n'avance que vers la droite
      pts.push({ x: Math.min(b.w, p.x), y: Math.min(b.max, Math.max(b.min, p.y)) });
      dessinerTrace();
      if (p.x >= b.w * .97) dechirer();
    });
    const lacher = () => {
      if (fait || !pts) return;
      const avance = pts.at(-1).x - pts[0].x;
      pts = null; pk.classList.remove('trace'); boite.classList.remove('tenu'); trace.setAttribute('points', '');
      if (avance < 20) secouer();
    };
    pk.addEventListener('pointerup', lacher);
    pk.addEventListener('pointercancel', lacher);
    function secouer() { pk.classList.remove('secoue'); void pk.offsetWidth; pk.classList.add('secoue'); }

    async function dechirer() {
      fait = true;
      const { w, h } = bande();
      // bord déchiré : on suit le doigt et on ajoute de fines dents de papier
      const base = [{ x: 0, y: pts[0].y }, ...pts, { x: w, y: pts.at(-1).y }];
      const bord = [];
      for (let i = 0; i < base.length - 1; i++) {
        const a = base[i], b = base[i + 1], k = Math.max(1, Math.ceil((b.x - a.x) / 4));
        for (let j = 0; j < k; j++) { const t = j / k; bord.push({ x: a.x + (b.x - a.x) * t, y: a.y + (b.y - a.y) * t + (Math.random() - .5) * 2.6 }); }
      }
      bord.push(base.at(-1));
      const txt = (l) => l.map((p) => `${p.x.toFixed(1)}px ${p.y.toFixed(1)}px`).join(',');
      const haut = pk.querySelector('.pk-haut'), corps = pk.querySelector('.pk-corps');
      haut.style.clipPath = `polygon(0 0, ${w}px 0, ${txt([...bord].reverse())})`;
      corps.style.clipPath = `polygon(${txt(bord)}, ${w}px ${h}px, 0 ${h}px)`;
      pk.classList.remove('trace'); pk.classList.add('dechire');
      trace.setAttribute('points', '');
      vibrer(18); son('dechirure');
      haut.animate([{ transform: 'none' }, { transform: 'translate(12%, -18%) rotate(7deg)', offset: .35 }, { transform: 'translate(40%, -150%) rotate(28deg)', opacity: 0 }],
        { duration: 900, easing: 'cubic-bezier(.3,.5,.3,1)', fill: 'forwards' });
      // la pile est déjà dans le paquet, derrière l'emballage ; elle en sort par le haut ouvert
      afficherPile();
      const decal = boite.getBoundingClientRect().top - pile.getBoundingClientRect().top;
      pile.animate([{ transform: `translateY(${decal + h * .15}px)` }, { transform: `translateY(${decal - h * .12}px)`, offset: .55 }, { transform: 'none' }],
        { duration: 1300, delay: 200, easing: 'cubic-bezier(.3,.7,.3,1)', fill: 'backwards' })
        .finished.then(() => { verrou = false; prendre(); });
      boite.animate([{ transform: getComputedStyle(boite).transform === 'none' ? 'none' : getComputedStyle(boite).transform }, { transform: 'translateY(105vh) rotate(-4deg)' }],
        { duration: 800, delay: 650, easing: 'cubic-bezier(.55,0,.8,.4)', fill: 'forwards' })
        .finished.then(() => boite.remove());
    }

    // ---------- 2. la pile ----------
    let n = 0, verrou = true, revelee = false, manip = null, pile;
    const slot = (i) => pile.children[i];
    const carteEl = (i) => slot(i)?.querySelector('.k');
    function afficherPile() {
      pile = document.createElement('div');
      pile.className = 'pile';
      pile.innerHTML = suite.map((t, i) => `<div class="slot" style="z-index:${suite.length - i};transform:translateY(${-i * 2.5}px) rotate(${(i % 2 ? 1 : -1) * Math.min(i, 3) * .7}deg)">${htmlCarte(t.carte, { dos: true })}</div>`).join('');
      scene.prepend(pile);
      majCompte();
      passer.style.visibility = '';
    }
    const majCompte = () => { compte.textContent = `${Math.min(n + 1, suite.length)} / ${suite.length}`; };
    function prendre() {
      revelee = false;
      const el = carteEl(n), s = slot(n); if (!el) return;
      // la carte garde sa place dans la pile : aucun mouvement quand elle passe dessus
      s.dataset.base = s.style.transform || '';
      s.classList.add('actif');
      manip = brancherManipulation(el, { flotte: false, surTap: () => { if (!revelee) retourner(); } });
      el.addEventListener('retournee', (e) => { if (!e.detail.dos && !revelee) reveler(); });
      brancherLancer(el, s);
    }
    async function retourner() {
      if (verrou || revelee) return;
      if (avant) { verrou = true; manip.verrouiller(true); await avant(suite[n].carte.rarete, contexte()); verrou = false; manip.verrouiller(false); }
      manip.retourner(); son('retourne');
      reveler();
    }
    const contexte = () => ({ ov, fxBox, toile, el: carteEl(n), slot: slot(n), scene, ajouter, onde, flash, attendre, son, vibrer });
    async function reveler() {
      if (revelee) return;
      revelee = true; verrou = true;
      manip.verrouiller(true);   // révélée, la carte se lance au lieu de tourner
      manip.flotter(true);
      const t = suite[n], el = carteEl(n);
      await attendre(240);   // la face apparaît à mi-retournement
      if (t.neuve) el.querySelector('.k-in').insertAdjacentHTML('beforeend', '<span class="k-neuve">Nouvelle</span>');
      const perso = effetPerso?.(t.carte.rarete, contexte());
      const fini = perso !== undefined ? perso : effet(t.carte.rarete);
      legende.innerHTML = `<span class="tag">${esc(t.carte.collection)}</span><p>${esc(phrase(t.carte.description))}</p>`;
      legende.classList.add('vue');
      await fini;
      verrou = false;
    }
    // la carte révélée suit le doigt ; lâchée assez loin ou assez vite, elle part de ce côté
    function brancherLancer(el, s) {
      let p = null;
      el.addEventListener('pointerdown', (e) => {
        if (!revelee || verrou) return;
        p = { x0: e.clientX, y0: e.clientY, x: e.clientX, y: e.clientY, t: performance.now(), vx: 0, vy: 0 };
        try { el.setPointerCapture(e.pointerId); } catch {}
        s.getAnimations().forEach((a) => a.cancel());
      });
      el.addEventListener('pointermove', (e) => {
        if (!p) return;
        const now = performance.now(), dt = Math.max(8, now - p.t);
        p.vx = p.vx * .5 + (e.clientX - p.x) / dt * .5; p.vy = p.vy * .5 + (e.clientY - p.y) / dt * .5;
        p.x = e.clientX; p.y = e.clientY; p.t = now;
        const dx = p.x - p.x0, dy = p.y - p.y0;
        s.style.transform = `translate(${dx}px, ${dy}px) rotate(${dx * .05}deg) ${s.dataset.base}`;
        manip.etat.ry = dx * .1; manip.etat.rx = -dy * .06;
      });
      const lacher = () => {
        if (!p) return;
        const q = p; p = null;
        const dx = q.x - q.x0, dy = q.y - q.y0, dist = Math.hypot(dx, dy), v = Math.hypot(q.vx, q.vy);
        if (dist > 110 || (dist > 30 && v > .7)) { envoyer(dx, dy, q.vx, q.vy); return; }
        const depuis = s.style.transform; s.style.transform = s.dataset.base;
        if (depuis) s.animate([{ transform: depuis }, { transform: s.dataset.base || 'none' }], { duration: 420, easing: 'cubic-bezier(.2,1.2,.4,1)' });
      };
      el.addEventListener('pointerup', lacher);
      el.addEventListener('pointercancel', lacher);
    }
    function envoyer(dx = -1, dy = 0, vx = 0, vy = 0) {
      if (verrou) return;
      verrou = true;
      manip?.arreter();
      const s = slot(n);
      s.classList.remove('actif');
      son('envoie');
      legende.classList.remove('vue');
      // la carte poursuit la direction du geste jusqu'à sortir de l'écran
      const ang = Math.atan2(dy + vy * 120, dx + vx * 120), loin = Math.max(innerWidth, innerHeight) * 1.1;
      const depuis = s.style.transform || 'none';
      s.animate([{ transform: depuis }, { transform: `translate(${dx + Math.cos(ang) * loin}px, ${dy + Math.sin(ang) * loin}px) rotate(${Math.cos(ang) * 28}deg)` }],
        { duration: 480, easing: 'cubic-bezier(.3,.5,.6,1)', fill: 'forwards' })
        .finished.then(() => { s.style.visibility = 'hidden'; });
      nettoyerFx();
      n++;
      if (n >= suite.length) { setTimeout(recap, 380); return; }
      majCompte();
      setTimeout(() => { verrou = false; prendre(); }, 200);
    }

    // ---------- effets ----------
    function nettoyerFx() {
      ov.classList.remove('sombre');
      fxBox.querySelectorAll('.fx-halo, .fx-rayons, .fx-perso').forEach((x) => x.animate([{ opacity: getComputedStyle(x).opacity }, { opacity: 0 }], { duration: 300, fill: 'forwards' }).finished.then(() => x.remove()));
    }
    const ajouter = (cls, vars = {}) => {
      const x = document.createElement('div');
      x.className = cls;
      for (const [k, v] of Object.entries(vars)) x.style.setProperty(k, v);
      fxBox.append(x);
      return x;
    };
    const onde = (c, d = 0) => ajouter('fx-onde', { '--c': c, '--d': `${d}s` }).addEventListener('animationend', (e) => e.target.remove());
    const flash = (ms, op = .9) => ov.querySelector('.ov2-flash').animate([{ opacity: op }, { opacity: 0 }], { duration: ms, easing: 'ease-out' });

    async function effet(r) {
      if (r === 'commune') return attendre(120);
      son(r);
      AMBIANCES[r]?.(toile);
      if (r === 'rare') return attendre(300);
      vibrer(r === 'epique' ? 25 : [30, 40, 60]);
      ajouter('fx-halo', { '--c': COULEURS[r] });
      if (r === 'epique') return attendre(450);
      if (r === 'mythique') { onde('#ff8fd6'); onde('#67e8f9', .12); return attendre(700); }
      ov.classList.add('sombre');
      if (r === 'legendaire') { flash(500, .3); ajouter('fx-rayons', { '--c': '#f2c66d55' }); onde('#f2c66d'); return attendre(1100); }
      // panthéon : séquence longue, impossible à passer
      flash(1100, 1);
      ajouter('fx-rayons prisme');
      ajouter('fx-halo', { '--c': '#9fd8ff99' });
      onde('#ffffff'); onde('#9fd8ff', .3); onde('#ffd6f0', .6);
      return attendre(2600);
    }

    // ---------- 3. passer, récapitulatif ----------
    passer.addEventListener('click', async () => {
      if (!pile || verrou) return;
      const derniere = suite.length - 1;
      // on saute jusqu'à la dernière carte si elle est au moins légendaire : sa révélation reste à faire
      if (ORDRE[suite[derniere].carte.rarete] >= ORDRE.legendaire && n < derniere) {
        verrou = true; manip?.arreter(); nettoyerFx(); legende.classList.remove('vue');
        for (let i = n; i < derniere; i++) slot(i).animate([{ transform: 'none' }, { transform: 'translateY(-120vh)' }], { duration: 400, fill: 'forwards', delay: (i - n) * 40 });
        n = derniere; majCompte();
        await attendre(500); verrou = false; prendre();
        return;
      }
      recap();
    });

    function recap() {
      verrou = true;
      nettoyerFx();
      legende.remove();
      const neuves = suite.filter((t) => t.neuve).length;
      scene.innerHTML = `<div class="ov2-recap">
        <div class="titre"><b>${neuves}</b><span>${neuves > 1 ? 'nouvelles' : 'nouvelle'}</span></div>
        <div class="recap-grille">${suite.map((t) => htmlCarte(t.carte, { neuve: t.neuve })).join('')}</div>
        <button class="btn2"><i class="ph-bold ph-check"></i>Continuer</button>
      </div>`;
      ov.querySelector('.ov2-haut').remove();
      scene.querySelector('.btn2').addEventListener('click', () => {
        ov.animate([{ opacity: 1 }, { opacity: 0 }], { duration: 250 }).finished.then(() => { toile.detruire(); ov.remove(); fin(); });
      });
    }
  });
}
