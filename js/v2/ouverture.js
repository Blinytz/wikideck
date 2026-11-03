// Ouverture v2 : on déchire le paquet d'un glissé, puis on retourne les cartes
// une à une. Le dos est le même pour toutes : la rareté ne se lit qu'à la face.

import { htmlCarte, brancherInclinaison, RARETES } from './carte.js';

const ORDRE = Object.fromEntries(RARETES.map((r, i) => [r, i]));
const COULEURS = {
  rare: '#c9d6e3', epique: '#b69cff', mythique: '#ff8fd6', legendaire: '#f4c76a', pantheon: '#ffffff',
};
const attendre = (ms) => new Promise((r) => setTimeout(r, ms));

// tirage = [{ carte, neuve }] ; renvoie une promesse résolue à la fermeture
export function ouvrirPaquet(tirage, { nom = 'WikiDeck' } = {}) {
  // la plus rare en dernier, ordre stable sinon
  const suite = tirage.map((t, i) => ({ ...t, i })).sort((a, b) => ORDRE[a.carte.rarete] - ORDRE[b.carte.rarete] || a.i - b.i);
  const ov = document.createElement('div');
  ov.className = 'ov2';
  ov.innerHTML = `
    <div class="ov2-voile"></div>
    <div class="ov2-fx"></div>
    <div class="ov2-scene">
      <div class="pk">
        <div class="pk-part pk-haut"></div>
        <div class="pk-part pk-corps"><div class="pk-marque"><div class="k-mono">W</div><div class="pk-nom">${nom}</div><div class="pk-nb">${suite.length} CARTES</div></div></div>
        <div class="pk-ligne"><i></i><b></b></div>
        <i class="ph ph-hand-pointing pk-guide"></i>
      </div>
    </div>
    <div class="ov2-flash"></div>
    <div class="ov2-haut"><span class="ov2-compte"></span><button class="ov2-btn" aria-label="Passer"><i class="ph ph-fast-forward"></i></button></div>`;
  document.body.append(ov);

  return new Promise((fin) => {
    const scene = ov.querySelector('.ov2-scene');
    const fx = ov.querySelector('.ov2-fx');
    const compte = ov.querySelector('.ov2-compte');
    const passer = ov.querySelector('.ov2-btn');
    passer.style.visibility = 'hidden';

    // ---------- 1. déchirer ----------
    const pk = ov.querySelector('.pk');
    const ligne = pk.querySelector('.pk-ligne');
    let depart = null, fait = false;
    pk.addEventListener('pointerdown', (e) => {
      if (fait) return;
      depart = e.clientX;
      try { pk.setPointerCapture(e.pointerId); } catch {}
      ligne.style.setProperty('--o', 1);
    });
    pk.addEventListener('pointermove', (e) => {
      if (depart == null || fait) return;
      const p = Math.max(0, Math.min(1, (e.clientX - depart) / (pk.offsetWidth * .7)));
      ligne.style.setProperty('--p', p);
      if (p >= 1) dechirer();
    });
    const lacher = () => {
      if (fait || depart == null) return;
      depart = null;
      const p = +getComputedStyle(ligne).getPropertyValue('--p') || 0;
      ligne.style.setProperty('--p', 0); ligne.style.setProperty('--o', 0);
      if (p < .08) { pk.classList.remove('secoue'); void pk.offsetWidth; pk.classList.add('secoue'); }
    };
    pk.addEventListener('pointerup', lacher);
    pk.addEventListener('pointercancel', lacher);

    async function dechirer() {
      fait = true;
      navigator.vibrate?.(18);
      pk.classList.add('dechire');
      await attendre(500);
      afficherPile();
      setTimeout(() => pk.remove(), 900);
    }

    // ---------- 2. retourner ----------
    let n = 0, verrou = true;
    let pile;
    function afficherPile() {
      pile = document.createElement('div');
      pile.className = 'pile monte';
      pile.innerHTML = suite.map((t, i) => htmlCarte(t.carte, { dos: true, image: 'full' })).join('');
      // la première carte de la suite est au-dessus
      [...pile.children].forEach((el, i) => {
        el.style.setProperty('--i', suite.length - i);
        el.style.zIndex = suite.length - i;
        el.style.transform = `translateY(${i * -3}px) rotate(${(i % 2 ? 1 : -1) * Math.min(i, 3) * .6}deg)`;
        brancherInclinaison(el, 10);
      });
      scene.append(pile);
      pile.addEventListener('pointerdown', toucher);
      majCompte();
      passer.style.visibility = '';
      setTimeout(() => { pile.classList.remove('monte'); verrou = false; marquerDessus(); }, 550 + suite.length * 45 + 700);
    }
    const carteEl = (i) => pile.children[i];
    const marquerDessus = () => carteEl(n)?.classList.add('dessus');
    const majCompte = () => { compte.textContent = `${Math.min(n + 1, suite.length)} / ${suite.length}`; };

    let glisse = null;
    function toucher(e) {
      if (verrou) return;
      const el = carteEl(n);
      if (!el || !el.contains(e.target)) return;
      glisse = { x: e.clientX, y: e.clientY };
      try { el.setPointerCapture(e.pointerId); } catch {}
      const fin = (ev) => {
        el.removeEventListener('pointerup', fin);
        const dx = ev.clientX - glisse.x, dy = ev.clientY - glisse.y;
        glisse = null;
        if (el.classList.contains('dos')) retourner();
        else envoyer(Math.abs(dx) > 30 || Math.abs(dy) > 30 ? Math.atan2(dy, dx) : -Math.PI * .75);
      };
      el.addEventListener('pointerup', fin);
    }

    async function retourner() {
      verrou = true;
      const t = suite[n], el = carteEl(n);
      el.style.transform = '';
      el.classList.remove('dos');
      await attendre(260);   // la face apparaît à mi-retournement
      if (t.neuve) el.insertAdjacentHTML('beforeend', '<span class="k-neuve">Nouvelle</span>');
      await effet(t.carte.rarete, el);
      verrou = false;
    }

    function envoyer(angle) {
      verrou = true;
      const el = carteEl(n);
      const d = Math.max(innerWidth, innerHeight) * 1.1;
      el.classList.remove('dessus');
      el.classList.add('part');
      el.style.transform = `translate(${Math.cos(angle) * d}px, ${Math.sin(angle) * d}px) rotate(${Math.cos(angle) * 30}deg)`;
      nettoyerFx();
      n++;
      if (n >= suite.length) { setTimeout(recap, 350); return; }
      majCompte();
      marquerDessus();
      setTimeout(() => { verrou = false; }, 180);
    }

    // ---------- effets ----------
    function nettoyerFx() {
      ov.classList.remove('sombre');
      fx.querySelectorAll('.fx-halo, .fx-rayons').forEach((x) => x.animate([{ opacity: getComputedStyle(x).opacity }, { opacity: 0 }], { duration: 300, fill: 'forwards' }).finished.then(() => x.remove()));
    }
    function particules(nb, couleurs, portee = 260, duree = 1400) {
      for (let i = 0; i < nb; i++) {
        const p = document.createElement('i');
        p.className = 'fx-p';
        const c = couleurs[i % couleurs.length];
        p.style.setProperty('--c', c);
        p.style.setProperty('--t', `${3 + Math.random() * 6}px`);
        fx.append(p);
        const a = Math.random() * Math.PI * 2, r = portee * (.4 + Math.random() * .8);
        p.animate([
          { transform: 'translate(0,0) scale(1)', opacity: 1 },
          { transform: `translate(${Math.cos(a) * r}px, ${Math.sin(a) * r + 40}px) scale(.2)`, opacity: 0 },
        ], { duration: duree * (.7 + Math.random() * .5), easing: 'cubic-bezier(.1,.8,.3,1)' }).finished.then(() => p.remove());
      }
    }
    const ajouter = (cls, vars = {}) => {
      const x = document.createElement('div');
      x.className = cls;
      for (const [k, v] of Object.entries(vars)) x.style.setProperty(k, v);
      fx.append(x);
      return x;
    };
    const flash = (ms, op = .9) => ov.querySelector('.ov2-flash').animate([{ opacity: op }, { opacity: 0 }], { duration: ms, easing: 'ease-out' });

    async function effet(r, el) {
      const c = COULEURS[r];
      if (r === 'commune') return attendre(150);
      el.classList.add('revele');
      setTimeout(() => el.classList.remove('revele'), 600);
      el.querySelector('.k-face').insertAdjacentHTML('beforeend', '<div class="fx-balayage"></div>');
      setTimeout(() => el.querySelector('.fx-balayage')?.remove(), 1000);
      if (r === 'rare') return attendre(300);
      navigator.vibrate?.(r === 'epique' ? 25 : [30, 40, 60]);
      ajouter('fx-halo', { '--c': c });
      if (r === 'epique') return attendre(500);
      if (r === 'mythique') {
        ajouter('fx-onde', { '--c': c }).addEventListener('animationend', (e) => e.target.remove());
        particules(28, ['#ff8fd6', '#67e8f9', '#a78bfa', '#fff']);
        return attendre(700);
      }
      ov.classList.add('sombre');
      if (r === 'legendaire') {
        flash(500, .35);
        ajouter('fx-rayons', { '--c': '#f4c76a66' });
        ajouter('fx-onde', { '--c': c }).addEventListener('animationend', (e) => e.target.remove());
        particules(40, ['#f4c76a', '#fff3c4', '#ffffff'], 320, 1800);
        return attendre(1100);
      }
      // panthéon : séquence longue, impossible à passer
      flash(1200, 1);
      const r1 = ajouter('fx-rayons prisme');
      ajouter('fx-halo', { '--c': '#ffffffaa' });
      for (let i = 0; i < 3; i++) ajouter('fx-onde', { '--c': ['#ff8fd6', '#7dd3fc', '#f4c76a'][i], '--d': `${i * .25}s` }).addEventListener('animationend', (e) => e.target.remove());
      particules(70, ['#ff6b6b', '#f4c76a', '#6ee7b7', '#7dd3fc', '#b69cff', '#ff8fd6', '#ffffff'], 380, 2200);
      setTimeout(() => particules(40, ['#ffffff', '#f4c76a'], 300, 1800), 900);
      r1.style.animationDuration = '1s, 14s';
      return attendre(2600);
    }

    // ---------- 3. passer, récapitulatif ----------
    passer.addEventListener('click', async () => {
      if (verrou && !pile) return;
      // on saute jusqu'à la dernière carte si elle est au moins légendaire : son effet reste visible
      const derniere = suite.length - 1;
      const garder = ORDRE[suite[derniere].carte.rarete] >= ORDRE.legendaire;
      if (garder && n < derniere) {
        verrou = true; nettoyerFx();
        for (let i = n; i < derniere; i++) { const el = carteEl(i); el.classList.add('part'); el.style.transform = 'translateY(-120vh)'; }
        n = derniere; majCompte(); marquerDessus();
        await attendre(400); verrou = false;
        return;
      }
      recap();
    });

    function recap() {
      verrou = true;
      nettoyerFx();
      const neuves = suite.filter((t) => t.neuve).length;
      scene.innerHTML = `<div class="ov2-recap">
        <div class="titre"><b>${neuves}</b><span>${neuves > 1 ? 'nouvelles' : 'nouvelle'}</span></div>
        <div class="recap-grille">${suite.map((t, i) => htmlCarte(t.carte, { neuve: t.neuve, attrs: `data-i="${i}"` })).join('')}</div>
        <button class="btn2"><i class="ph-bold ph-check"></i>Continuer</button>
      </div>`;
      ov.querySelector('.ov2-haut').remove();
      scene.querySelector('.btn2').addEventListener('click', () => {
        ov.animate([{ opacity: 1 }, { opacity: 0 }], { duration: 250 }).finished.then(() => { ov.remove(); fin(); });
      });
    }
  });
}
