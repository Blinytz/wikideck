// Écran Questions : 3 propositions (thème et difficulté visibles), réponse
// libre, verdict avec la bonne réponse, correction dans les deux sens.

import { esc } from './ui.js';
import { config } from './config.js';
import { NIVEAUX, propositions, choisir, questionEnCours, repondre, corriger, suite,
         multiplicateur, questionDuJour, commencerQuestionDuJour, nbQuestions } from './questions.js';
import { bonnesDuJour } from './serie.js';

let verdict = null;

export function rendreEcranQuestions(section) {
  const entete = `<div class="entete-ecran"><h2>Questions</h2>
    <span class="texte-doux">Suite ${suite()} · ×${String(multiplicateur(suite() + 1)).replace('.', ',')} · ${bonnesDuJour()} / ${config.get('bonnesParJour')}</span></div>`;
  if (!nbQuestions()) {
    section.innerHTML = `${entete}<p class="texte-doux">Les questions arrivent avec le raccordement au serveur Éclats.</p>`;
    return;
  }
  if (verdict) return rendreVerdict(section, entete);
  const enCours = questionEnCours();
  if (enCours) return rendreQuestion(section, entete, enCours);

  const qdj = questionDuJour();
  const props = propositions();
  section.innerHTML = `${entete}
    ${qdj && !qdj.faite ? `<button class="carte-panneau proposition qdj" id="btn-qdj">
      <b>Question du jour</b><span>${esc(qdj.theme || '')} · ${NIVEAUX[qdj.difficulte]} · ${config.get('gainQuestionDuJour')} min</span></button>` : ''}
    <div class="propositions">${props.map(p => `
      <button class="carte-panneau proposition" data-id="${esc(p.id)}">
        <b>${esc(p.theme || 'Culture générale')}</b><span>${NIVEAUX[p.difficulte]}</span></button>`).join('')}</div>`;
  section.querySelector('#btn-qdj')?.addEventListener('click', () => { commencerQuestionDuJour(); rendreEcranQuestions(section); });
  for (const b of section.querySelectorAll('.proposition[data-id]')) {
    b.addEventListener('click', () => { choisir(b.dataset.id); rendreEcranQuestions(section); });
  }
}

function rendreQuestion(section, entete, qu) {
  section.innerHTML = `${entete}
    <div class="carte-panneau">
      <p class="texte-doux">${esc(qu.theme || '')} · ${NIVEAUX[qu.difficulte]}${qu.qdj ? ' · Question du jour' : ''}</p>
      <h3 class="enonce">${esc(qu.question)}</h3>
      <form id="form-rep"><input id="saisie" autocomplete="off" autocapitalize="off" spellcheck="false" placeholder="Ta réponse">
        <button class="btn btn-primaire btn-large">Valider</button></form>
    </div>`;
  const input = section.querySelector('#saisie');
  input.focus();
  section.querySelector('#form-rep').addEventListener('submit', ev => {
    ev.preventDefault();
    verdict = repondre(input.value);
    rendreEcranQuestions(section);
  });
}

function rendreVerdict(section, entete) {
  const v = verdict;
  section.innerHTML = `${entete}
    <div class="carte-panneau verdict ${v.correct ? 'bon' : 'faux'}">
      <h3>${v.correct ? 'Bonne réponse' : 'Raté'}${v.corrigee ? ' (corrigé)' : ''}</h3>
      <p class="enonce">${esc(v.question)}</p>
      <p>Réponse : <b>${esc(v.reponse)}</b></p>
      <p class="texte-doux">Ta réponse : ${esc(v.saisie || '—')}</p>
      ${v.correct ? `<p class="gain">+${String(Math.round(v.gain * 10) / 10).replace('.', ',')} min</p>` : ''}
      <div class="rangee-boutons">
        <button class="btn" id="btn-corriger">${v.correct ? 'En fait j’avais faux' : 'En fait j’avais bon'}</button>
        <button class="btn btn-primaire" id="btn-suivante">Suivante</button>
      </div>
    </div>`;
  section.querySelector('#btn-corriger').addEventListener('click', () => { verdict = corriger(); rendreEcranQuestions(section); });
  section.querySelector('#btn-suivante').addEventListener('click', () => { verdict = null; rendreEcranQuestions(section); });
}
