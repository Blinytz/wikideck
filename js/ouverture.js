// Ouverture d'un paquet : déchirure au geste, cartes face cachée entourées du
// halo de leur rareté, révélation une par une par rareté croissante (la
// meilleure en dernier), une animation par rareté, tampon « Nouvelle »,
// puis récapitulatif (nouvelles cartes, collections, Résonance).

import { esc, NOMS_RARETE, htmlImageCarte } from './ui.js';
import { htmlCarte } from './carte.js';
import { config } from './config.js';

const ORDRE = ['commune', 'rare', 'epique', 'mythique', 'legendaire', 'pantheon'];
const COULEURS = {
  commune: '#8a93a6', rare: '#4aa8ff', epique: '#b05cff',
  mythique: '#ff5cd0', legendaire: '#ffd166', pantheon: '#ffffff',
};
const pause = ms => new Promise(r => setTimeout(r, ms));

/* ---------------- son (Web Audio, rien à télécharger) ---------------- */
let audio = null;
function ctx() {
  if (!config.get('sonActive')) return null;
  try { audio ??= new (window.AudioContext || window.webkitAudioContext)(); } catch { return null; }
  if (audio.state === 'suspended') audio.resume();
  return audio;
}
function note(freq, debut, duree, { type = 'sine', gain = 0.18, glisse } = {}) {
  const a = ctx(); if (!a) return;
  const t = a.currentTime + debut;
  const o = a.createOscillator(), g = a.createGain();
  o.type = type; o.frequency.setValueAtTime(freq, t);
  if (glisse) o.frequency.exponentialRampToValueAtTime(glisse, t + duree);
  g.gain.setValueAtTime(0.0001, t);
  g.gain.exponentialRampToValueAtTime(gain, t + 0.02);
  g.gain.exponentialRampToValueAtTime(0.0001, t + duree);
  o.connect(g).connect(a.destination);
  o.start(t); o.stop(t + duree + 0.05);
}
function bruit(debut, duree, gain = 0.25) {
  const a = ctx(); if (!a) return;
  const b = a.createBuffer(1, a.sampleRate * duree, a.sampleRate);
  const d = b.getChannelData(0);
  for (let i = 0; i < d.length; i++) d[i] = (Math.random() * 2 - 1) * (1 - i / d.length) ** 3;
  const s = a.createBufferSource(), g = a.createGain();
  s.buffer = b; g.gain.value = gain;
  s.connect(g).connect(a.destination);
  s.start(a.currentTime + debut);
}
const SONS = {
  dechirure: () => bruit(0, 0.35, 0.18),
  retourne: () => note(660, 0, 0.12, { type: 'triangle', gain: 0.06 }),
  rare: () => { note(880, 0, 0.25, { gain: 0.07 }); note(1320, 0.08, 0.3, { gain: 0.05 }); },
  epique: () => [523, 659, 784].forEach((f, i) => note(f, i * 0.09, 0.5, { gain: 0.07 })),
  mythique: () => { note(55, 0, 1.4, { type: 'sawtooth', gain: 0.22, glisse: 38 }); note(110, 0, 1.2, { gain: 0.12 }); },
  legendaire: () => [784, 988, 1175, 1568, 1976].forEach((f, i) => note(f, 0.25 + i * 0.12, 1.4, { gain: 0.07 })),
  fissure: () => { bruit(0, 0.25, 0.3); bruit(0.3, 0.2, 0.25); bruit(0.55, 0.4, 0.35); },
  pantheon: () => {
    // musique dédiée : nappe grave puis arpège ascendant et accord final
    note(65.4, 0, 6, { type: 'sawtooth', gain: 0.06 });
    note(98, 0.5, 5.5, { type: 'triangle', gain: 0.08 });
    [261.6, 329.6, 392, 523.3, 659.3, 784, 1046.5].forEach((f, i) => note(f, 1.2 + i * 0.28, 2.2, { gain: 0.06 }));
    [523.3, 659.3, 784, 1046.5].forEach(f => note(f, 3.4, 3.2, { type: 'triangle', gain: 0.06 }));
  },
};

/* ---------------- particules ---------------- */
function particules(toile, { n = 60, couleurs = ['#fff'], mode = 'eclat', duree = 1500, x = 0.5, y = 0.45, vitesse = 1 }) {
  const c = toile.getContext('2d');
  const W = toile.width = toile.clientWidth * devicePixelRatio;
  const H = toile.height = toile.clientHeight * devicePixelRatio;
  const ps = Array.from({ length: n }, () => {
    const ang = Math.random() * Math.PI * 2, v = (2 + Math.random() * 7) * vitesse * devicePixelRatio;
    return mode === 'pluie'
      ? { x: Math.random() * W, y: -Math.random() * H * 0.6, vx: (Math.random() - 0.5) * 1.5, vy: 2 + Math.random() * 4 * devicePixelRatio,
          r: (1 + Math.random() * 2.5) * devicePixelRatio, c: couleurs[Math.floor(Math.random() * couleurs.length)] }
      : { x: W * x, y: H * y, vx: Math.cos(ang) * v, vy: Math.sin(ang) * v,
          r: (1 + Math.random() * 3) * devicePixelRatio, c: couleurs[Math.floor(Math.random() * couleurs.length)] };
  });
  const t0 = performance.now();
  return new Promise(fin => {
    const frame = (t) => {
      const k = (t - t0) / duree;
      c.clearRect(0, 0, W, H);
      if (k >= 1) return fin();
      for (const p of ps) {
        p.x += p.vx; p.y += p.vy;
        if (mode === 'eclat') { p.vx *= 0.97; p.vy = p.vy * 0.97 + 0.06; }
        c.globalAlpha = Math.max(0, 1 - k);
        c.fillStyle = p.c;
        c.beginPath(); c.arc(p.x, p.y, p.r, 0, Math.PI * 2); c.fill();
      }
      requestAnimationFrame(frame);
    };
    requestAnimationFrame(frame);
  });
}

/* ---------------- ouverture ---------------- */
export function lancerOuverture(resultat, surFin, { titre = 'Paquet' } = {}) {
  // ordre de révélation : rareté croissante, la meilleure en dernier
  const cartes = resultat.cartes
    .map((x, i) => ({ ...x, i, k: ORDRE.indexOf(x.carte.rarete), alea: Math.random() }))
    .sort((a, b) => a.k - b.k || a.alea - b.alea);
  const overlay = document.createElement('div');
  overlay.className = 'overlay-ouverture ouv';
  overlay.innerHTML = `
    <canvas class="ouv-toile"></canvas>
    <div class="ouv-scene">
      <div class="ouv-paquet" tabindex="0" aria-label="Glisser pour déchirer">
        <div class="ouv-paquet-haut"></div>
        <div class="ouv-paquet-corps"><span class="ouv-paquet-logo">W</span><span class="ouv-paquet-titre">${esc(titre)}</span><span class="ouv-paquet-nb">${cartes.length} cartes</span></div>
        <div class="ouv-dechirure"></div>
      </div>
      <p class="ouv-astuce">Glisse pour déchirer →</p>
    </div>`;
  document.getElementById('overlays').append(overlay);
  const toile = overlay.querySelector('.ouv-toile');
  const scene = overlay.querySelector('.ouv-scene');
  const paquet = overlay.querySelector('.ouv-paquet');

  // --- déchirure au geste
  let x0 = null, ouvert = false;
  const largeur = () => paquet.getBoundingClientRect().width;
  paquet.addEventListener('pointerdown', e => { x0 = e.clientX; paquet.setPointerCapture(e.pointerId); ctx(); });
  paquet.addEventListener('pointermove', e => {
    if (x0 === null || ouvert) return;
    const k = Math.max(0, Math.min(1, (e.clientX - x0) / largeur()));
    paquet.style.setProperty('--dechire', k);
    if (k > 0.7) ouvrir();
  });
  paquet.addEventListener('pointerup', () => { if (!ouvert) paquet.style.setProperty('--dechire', 0); x0 = null; });
  paquet.addEventListener('keydown', e => { if (e.key === 'Enter' || e.key === ' ') ouvrir(); });

  async function ouvrir() {
    if (ouvert) return;
    ouvert = true;
    SONS.dechirure();
    paquet.style.setProperty('--dechire', 1);
    paquet.classList.add('ouvert');
    await pause(650);
    etalerCartes();
  }

  // --- cartes face cachée, halo de rareté, révélation une à une
  let index = -1, occupe = false;
  function etalerCartes() {
    scene.innerHTML = `
      <div class="ouv-compteur"></div>
      <div class="ouv-scene-carte"></div>
      <p class="ouv-astuce">Touche pour révéler</p>
      <div class="ouv-rangee">${cartes.map((x, j) => `
        <div class="ouv-dos" data-j="${j}" style="--halo:${COULEURS[x.carte.rarete]};animation-delay:${j * 70}ms"></div>`).join('')}
      </div>
      <button class="btn btn-discret ouv-passer">Tout révéler</button>`;
    scene.querySelector('.ouv-scene-carte').addEventListener('click', e => { if (!e.target.closest('a')) avancer(); });
    scene.querySelector('.ouv-passer').addEventListener('click', toutReveler);
    avancer();
  }

  async function avancer() {
    if (occupe) return;
    const zone = scene.querySelector('.ouv-scene-carte');
    const cur = zone.querySelector('.carte-jeu');
    if (cur && cur.classList.contains('dos-visible')) return reveler(index);
    index += 1;
    if (index >= cartes.length) return recapitulatif();
    const { carte } = cartes[index];
    scene.querySelector('.ouv-compteur').textContent = `${index + 1} / ${cartes.length}`;
    scene.querySelector(`.ouv-dos[data-j="${index}"]`)?.classList.add('courante');
    zone.style.setProperty('--halo', COULEURS[carte.rarete]);
    zone.className = `ouv-scene-carte halo-${carte.rarete}`;
    zone.innerHTML = htmlCarte(carte, { dosVisible: true });
    // une Panthéon se révèle seule, d'un bloc
    if (carte.rarete === 'pantheon') reveler(index);
  }

  async function reveler(j) {
    if (occupe) return;
    occupe = true;
    overlay.classList.toggle('bloque', cartes[j].carte.rarete === 'pantheon');
    const zone = scene.querySelector('.ouv-scene-carte');
    const el = zone.querySelector('.carte-jeu');
    await ANIMATIONS[cartes[j].carte.rarete]({ overlay, zone, el, toile, carte: cartes[j].carte });
    el.classList.remove('dos-visible');
    if (cartes[j].nouvelle) {
      await pause(300);
      zone.insertAdjacentHTML('beforeend', '<div class="ouv-tampon">Nouvelle</div>');
    }
    const dos = scene.querySelector(`.ouv-dos[data-j="${j}"]`);
    if (dos) { dos.classList.remove('courante'); dos.classList.add('revelee'); dos.innerHTML = htmlImageCarte(cartes[j].carte); }
    overlay.classList.remove('bloque', 'assombri', 'cosmos');
    occupe = false;
  }

  async function toutReveler() {
    if (occupe) return;
    // une Panthéon n'est jamais passable : sa séquence se joue quand même
    const p = cartes.findIndex((x, j) => j > index && x.carte.rarete === 'pantheon');
    if (p >= 0) {
      index = p - 1;
      return avancer();
    }
    recapitulatif();
  }

  function recapitulatif() {
    const nouvelles = resultat.cartes.filter(x => x.nouvelle);
    const resonances = resultat.resonances || [];
    const declenchees = resonances.flatMap(r => r.declenchees);
    const mini = (carte, nouvelle) => `
      <div class="mini-carte rarete-${carte.rarete}">
        ${htmlImageCarte(carte)}
        <span class="nom-mini">${esc(carte.nom)}</span>
        <span class="rarete-mini">${NOMS_RARETE[carte.rarete]}</span>
        ${nouvelle ? '<span class="pastille-nouvelle">★</span>' : ''}
      </div>`;
    scene.innerHTML = `
      <div class="ouv-recap">
        <h2>${nouvelles.length ? `${nouvelles.length} nouvelle${nouvelles.length > 1 ? 's' : ''}` : 'Aucune nouveauté'}</h2>
        <div class="grille-bilan">${cartes.map(x => mini(x.carte, x.nouvelle)).join('')}</div>
        ${resultat.progres?.length ? `
          <h3>Collections</h3>
          <div class="ouv-progres">${resultat.progres.map(p => `
            <div class="ouv-ligne"><span>${esc(p.nom)}</span><b>+${p.apres - p.avant}</b>
              <span class="texte-doux">${p.apres} / ${p.total}</span>
              <div class="barre-progression"><div style="width:${Math.round(100 * p.apres / p.total)}%"></div></div></div>`).join('')}
          </div>` : ''}
        ${resonances.length ? `
          <h3>Résonance</h3>
          <div class="ouv-progres">${resonances.map(r => `
            <div class="ouv-ligne ${r.declenchees.length ? 'declenchee' : ''}"><span>${esc(r.nom)}</span>
              <b>${r.declenchees.length ? '✦' : `${r.apres} / ${r.seuil}`}</b>
              <div class="barre-progression resonance"><div style="width:${r.declenchees.length ? 100 : Math.round(100 * r.apres / r.seuil)}%"></div></div></div>`).join('')}
          </div>
          ${declenchees.length ? `<div class="grille-bilan">${declenchees.map(c => mini(c, true)).join('')}</div>` : ''}` : ''}
        <button class="btn btn-primaire btn-large" id="btn-fin">Ranger dans la collection</button>
      </div>`;
    scene.querySelector('#btn-fin').addEventListener('click', () => { overlay.remove(); surFin?.(); });
  }
}

/* ---------------- une animation par rareté ---------------- */
const ANIMATIONS = {
  async commune({ el }) {
    SONS.retourne();
    el.classList.add('anim-retourne');
    await pause(80);
  },
  async rare({ el }) {
    SONS.rare();
    el.classList.add('anim-retourne', 'anim-reflet');
    await pause(120);
  },
  async epique({ zone, el, toile }) {
    zone.classList.add('pulse');
    await pause(700);
    SONS.epique();
    particules(toile, { n: 40, couleurs: ['#b05cff', '#d9b8ff', '#fff'], duree: 1300, vitesse: 0.6 });
    el.classList.add('anim-retourne');
    await pause(150);
    zone.classList.remove('pulse');
  },
  async mythique({ overlay, el, toile }) {
    el.classList.add('anim-tremble');
    SONS.mythique();
    await pause(900);
    el.classList.remove('anim-tremble');
    overlay.classList.add('eclat');
    particules(toile, { n: 90, couleurs: ['#ff5cd0', '#ffc2f0', '#fff'], duree: 1600, vitesse: 1.2 });
    el.classList.add('anim-retourne');
    await pause(500);
    overlay.classList.remove('eclat');
  },
  async legendaire({ overlay, zone, el, toile }) {
    overlay.classList.add('assombri');
    await pause(500);
    zone.classList.add('faisceau');
    el.classList.add('anim-descente');
    SONS.legendaire();
    await pause(1300);
    el.classList.add('anim-retourne');
    particules(toile, { n: 160, couleurs: ['#ffd166', '#ffe9a8', '#fff3cf'], mode: 'pluie', duree: 2600 });
    await pause(700);
    zone.classList.remove('faisceau');
  },
  async pantheon({ overlay, zone, el, toile, carte }) {
    // séquence complète, jamais passable
    overlay.classList.add('fige');
    await pause(900);
    overlay.insertAdjacentHTML('beforeend', `<svg class="ouv-fissures" viewBox="0 0 100 100" preserveAspectRatio="none">
      <path d="M50 45 L38 20 L41 0"/><path d="M50 45 L70 28 L92 22 L100 12"/><path d="M50 45 L80 55 L100 70"/>
      <path d="M50 45 L58 75 L52 100"/><path d="M50 45 L22 60 L0 58"/><path d="M50 45 L18 35 L0 25"/></svg>`);
    SONS.fissure();
    await pause(1300);
    overlay.classList.remove('fige');
    overlay.classList.add('cosmos');
    SONS.pantheon();
    await pause(900);
    zone.classList.add('vortex');
    await pause(1600);
    overlay.classList.add('eclat');
    const arcEnCiel = ['#ff5c7a', '#ffa94d', '#ffd166', '#3ddc97', '#46c8ff', '#7c5cff', '#ff5cd0', '#fff'];
    particules(toile, { n: 260, couleurs: arcEnCiel, duree: 2400, vitesse: 1.6 });
    zone.classList.remove('vortex');
    el.classList.add('anim-retourne');
    overlay.querySelector('.ouv-fissures')?.remove();
    await pause(600);
    overlay.classList.remove('eclat');
    const nom = [...carte.nom].map((ch, i) => `<span style="animation-delay:${i * 110}ms">${ch === ' ' ? '&nbsp;' : esc(ch)}</span>`).join('');
    zone.insertAdjacentHTML('beforeend', `<div class="ouv-grave">${nom}</div>`);
    await pause(700 + [...carte.nom].length * 110);
    particules(toile, { n: 120, couleurs: arcEnCiel, mode: 'pluie', duree: 2200 });
    await pause(1200);
  },
};
