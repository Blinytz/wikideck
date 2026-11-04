// Sons de l'interface v2 : synthèse Web Audio, rien à télécharger.
// Repris de l'ancienne ouverture, plus quelques sons d'interface très courts.

const CLE = 'wikideck-v2-son';
let audio = null;
export const sonActif = () => { try { return localStorage.getItem(CLE) !== '0'; } catch { return true; } };
export const activerSon = (oui) => { try { localStorage.setItem(CLE, oui ? '1' : '0'); } catch {} };

function ctx() {
  if (!sonActif()) return null;
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
  g.gain.exponentialRampToValueAtTime(gain, t + 0.015);
  g.gain.exponentialRampToValueAtTime(0.0001, t + duree);
  o.connect(g).connect(a.destination);
  o.start(t); o.stop(t + duree + 0.05);
}
function bruit(debut, duree, gain = 0.25, passeHaut = 0) {
  const a = ctx(); if (!a) return;
  const b = a.createBuffer(1, Math.max(1, a.sampleRate * duree), a.sampleRate);
  const d = b.getChannelData(0);
  for (let i = 0; i < d.length; i++) d[i] = (Math.random() * 2 - 1) * (1 - i / d.length) ** 3;
  const s = a.createBufferSource(), g = a.createGain();
  s.buffer = b; g.gain.value = gain;
  let n = s;
  if (passeHaut) { const f = a.createBiquadFilter(); f.type = 'highpass'; f.frequency.value = passeHaut; n = s.connect(f); }
  n.connect(g).connect(a.destination);
  s.start(a.currentTime + debut);
}

const SONS = {
  tap: () => note(1800, 0, 0.03, { type: 'triangle', gain: 0.025 }),
  onglet: () => note(1200, 0, 0.05, { type: 'sine', gain: 0.04, glisse: 1500 }),
  dechirure: () => bruit(0, 0.35, 0.18, 1200),
  retourne: () => { bruit(0, 0.08, 0.06, 3000); note(660, 0.02, 0.12, { type: 'triangle', gain: 0.05 }); },
  envoie: () => bruit(0, 0.18, 0.05, 2500),
  rare: () => { note(880, 0, 0.25, { gain: 0.07 }); note(1320, 0.08, 0.3, { gain: 0.05 }); },
  epique: () => [523, 659, 784].forEach((f, i) => note(f, i * 0.09, 0.5, { gain: 0.07 })),
  mythique: () => { note(55, 0, 1.4, { type: 'sawtooth', gain: 0.16, glisse: 38 }); [659, 831, 988, 1319].forEach((f, i) => note(f, 0.2 + i * 0.07, 0.6, { gain: 0.05 })); },
  legendaire: () => { note(65, 0, 1.6, { type: 'triangle', gain: 0.12 }); [784, 988, 1175, 1568, 1976].forEach((f, i) => note(f, 0.25 + i * 0.12, 1.4, { gain: 0.06 })); },
  pantheon: () => {
    note(65.4, 0, 6, { type: 'sawtooth', gain: 0.05 });
    note(98, 0.5, 5.5, { type: 'triangle', gain: 0.08 });
    [261.6, 329.6, 392, 523.3, 659.3, 784, 1046.5].forEach((f, i) => note(f, 1.0 + i * 0.22, 2.2, { gain: 0.05 }));
    [523.3, 659.3, 784, 1046.5].forEach((f) => note(f, 2.8, 3.2, { type: 'triangle', gain: 0.05 }));
  },
  juste: () => { note(784, 0, 0.18, { gain: 0.07 }); note(1175, 0.09, 0.3, { gain: 0.07 }); },
  palier: () => [784, 988, 1175, 1568].forEach((f, i) => note(f, i * 0.07, 0.4, { gain: 0.06 })),
  faux: () => { note(220, 0, 0.22, { type: 'triangle', gain: 0.09, glisse: 160 }); },
  pieces: () => [2093, 2637, 3136].forEach((f, i) => note(f, i * 0.05, 0.15, { type: 'triangle', gain: 0.03 })),
  achat: () => { bruit(0, 0.12, 0.05, 2000); [523, 784, 1047].forEach((f, i) => note(f, 0.05 + i * 0.06, 0.3, { gain: 0.05 })); },
  epingle: () => note(1400, 0, 0.08, { type: 'triangle', gain: 0.05, glisse: 1900 }),
};

export function son(nom) { try { SONS[nom]?.(); } catch {} }
