// Atelier — éditeur de cadrage : la photo ENTIÈRE sous un cadre 4:3 fixe
// (= exactement ce que la carte affiche). Glisser pour positionner, molette
// pour zoomer vers le curseur, pincement à deux doigts sur tactile.
// Le zoom minimal couvre toujours le cadre (jamais de bandes vides).

const RATIO = 4 / 3;          // cadre de l'illustration des cartes
export const EXPORT_FULL = [800, 600];
export const EXPORT_THUMB = [213, 160];
// format carte : la zone d'image de la carte (le haut, 66 % de sa hauteur) ;
// sous elle, le jeu prolonge l'image par un fond flou fondu
export const EXPORT_CARTE = [760, 700];

export class Editeur {
  constructor(conteneur, img, canvasApercu) {
    this.conteneur = conteneur;   // .ed-cadre-conteneur (le cadre = ses bords)
    this.img = img;               // <img> transformée en CSS
    this.apercu = canvasApercu;
    this.pointeurs = new Map();   // pincement : jusqu'à 2 pointeurs suivis
    this.s = 1; this.tx = 0; this.ty = 0;
    this.iw = 0; this.ih = 0;
    this._brancher();
  }

  /* ---------- chargement ---------- */

  chargerDepuisURL(url) {
    return new Promise((res, rej) => {
      const im = new Image();
      im.crossOrigin = 'anonymous';
      im.onload = () => { this._prendre(im); res(); };
      im.onerror = () => rej(new Error('image illisible : ' + url.slice(0, 80)));
      im.src = url;
    });
  }

  chargerDepuisBlob(blob) {
    return this.chargerDepuisURL(URL.createObjectURL(blob));
  }

  _prendre(im) {
    this.source = im;
    this.iw = im.naturalWidth; this.ih = im.naturalHeight;
    this.img.src = im.src;
    this.reset();
  }

  /* ---------- géométrie ---------- */

  get fw() { return this.conteneur.clientWidth; }
  get fh() { return this.conteneur.clientHeight; }
  // en format carte, on peut dézoomer jusqu'à voir toute l'image : le vide sera comblé par un flou
  get sMin() { return this.vide ? Math.min(this.fw / this.iw, this.fh / this.ih) : Math.max(this.fw / this.iw, this.fh / this.ih); }

  reset() {
    // recadrage auto : l'image couvre toujours le cadre ; dézoomer reste possible ensuite
    this.s = Math.max(this.fw / this.iw, this.fh / this.ih);
    this.tx = (this.fw - this.iw * this.s) / 2;
    this.ty = (this.fh - this.ih * this.s) / 2;
    this._rendre();
  }

  _clamp() {
    this.s = Math.max(this.sMin, Math.min(this.s, this.sMin * 12));
    const lw = this.fw - this.iw * this.s, lh = this.fh - this.ih * this.s;
    this.tx = lw <= 0 ? Math.min(0, Math.max(lw, this.tx)) : Math.max(0, Math.min(lw, this.tx));
    this.ty = lh <= 0 ? Math.min(0, Math.max(lh, this.ty)) : Math.max(0, Math.min(lh, this.ty));
  }

  _rendre() {
    this._clamp();
    this.img.style.transform = `translate(${this.tx}px, ${this.ty}px) scale(${this.s})`;
    this._rendreApercu();
    this.surRendu?.();
  }

  zoomer(facteur, px = this.fw / 2, py = this.fh / 2) {
    const avant = this.s;
    this.s *= facteur;
    this._clamp();
    const reel = this.s / avant;
    this.tx = px - (px - this.tx) * reel;
    this.ty = py - (py - this.ty) * reel;
    this._rendre();
  }

  // rectangle recadré, en pixels de l'image source
  _rectSource() {
    return { x: -this.tx / this.s, y: -this.ty / this.s,
             w: this.fw / this.s, h: this.fh / this.s };
  }

  // cadrage normalisé persistable {cx, cy, w} (fractions de l'image)
  getCadrage() {
    const r = this._rectSource();
    const q = v => Math.round(v * 1e4) / 1e4;     // 4 decimales : le fichier des notes reste leger
    return { cx: q((r.x + r.w / 2) / this.iw), cy: q((r.y + r.h / 2) / this.ih),
             w: q(r.w / this.iw) };
  }

  setCadrage(c) {
    if (!c || !c.w) { this.reset(); return; }
    this.s = this.fw / (c.w * this.iw);
    const r = { w: this.fw / this.s, h: this.fh / this.s };
    this.tx = -(c.cx * this.iw - r.w / 2) * this.s;
    this.ty = -(c.cy * this.ih - r.h / 2) * this.s;
    this._rendre();
  }

  /* ---------- exports ---------- */

  _dessiner(canvas, [W, H]) {
    const r = this._rectSource();
    canvas.width = W; canvas.height = H;
    const ctx = canvas.getContext('2d');
    ctx.imageSmoothingQuality = 'high';
    const k = W / r.w;   // pixels de sortie par pixel source
    // position de l'image entière dans la sortie
    const dx = -r.x * k, dy = -r.y * k, dw = this.iw * k, dh = this.ih * k;
    const vide = dx > .5 || dy > .5 || dx + dw < W - .5 || dy + dh < H - .5;
    if (!vide) { ctx.drawImage(this.source, r.x, r.y, r.w, r.h, 0, 0, W, H); return; }
    // fond : l'image elle-même, agrandie et floutée, pour combler le vide
    const c = Math.max(W / this.iw, H / this.ih);
    ctx.filter = `blur(${Math.round(W * .04)}px) saturate(1.3) brightness(.62)`;
    ctx.drawImage(this.source, (W - this.iw * c) / 2 - W * .05, (H - this.ih * c) / 2 - H * .05, this.iw * c * 1.1, this.ih * c * 1.1);
    ctx.filter = 'none';
    // l'image nette, fondue sur les bords qui touchent le vide
    const t = document.createElement('canvas'); t.width = W; t.height = H;
    const tc = t.getContext('2d'); tc.imageSmoothingQuality = 'high';
    tc.drawImage(this.source, dx, dy, dw, dh);
    // on efface progressivement les bords (destination-out ne touche que la bande peinte)
    tc.globalCompositeOperation = 'destination-out';
    const fondu = (x0, y0, x1, y1) => {
      const g = tc.createLinearGradient(x0, y0, x1, y1);
      g.addColorStop(0, 'rgba(0,0,0,1)'); g.addColorStop(1, 'rgba(0,0,0,0)');
      return g;
    };
    const bande = Math.min(dh, dw) * .16;
    if (dy > .5) { tc.fillStyle = fondu(0, dy, 0, dy + bande); tc.fillRect(0, dy, W, bande); }
    if (dy + dh < H - .5) { tc.fillStyle = fondu(0, dy + dh, 0, dy + dh - bande); tc.fillRect(0, dy + dh - bande, W, bande); }
    if (dx > .5) { tc.fillStyle = fondu(dx, 0, dx + bande, 0); tc.fillRect(dx, 0, bande, H); }
    if (dx + dw < W - .5) { tc.fillStyle = fondu(dx + dw, 0, dx + dw - bande, 0); tc.fillRect(dx + dw - bande, 0, bande, H); }
    ctx.drawImage(t, 0, 0);
  }

  _versBlob(canvas, qualite) {
    return new Promise(res => canvas.toBlob(res, 'image/webp', qualite));
  }

  async exporter() {
    const c1 = document.createElement('canvas');
    this._dessiner(c1, EXPORT_FULL);
    const c2 = document.createElement('canvas');
    this._dessiner(c2, EXPORT_THUMB);
    return { full: await this._versBlob(c1, 0.9), thumb: await this._versBlob(c2, 0.82) };
  }

  async exporterCarte() {
    const c = document.createElement('canvas');
    this._dessiner(c, EXPORT_CARTE);
    return this._versBlob(c, 0.88);
  }

  // largeur réelle, en pixels de la source, de la zone cadrée
  resolution() { return Math.round(this._rectSource().w); }

  // l'image source complète re-encodée (≤1600 px) pour images/originaux/
  async exporterOriginal() {
    const c = document.createElement('canvas');
    const k = Math.min(1, 1600 / Math.max(this.iw, this.ih));
    c.width = Math.round(this.iw * k); c.height = Math.round(this.ih * k);
    c.getContext('2d').drawImage(this.source, 0, 0, c.width, c.height);
    return this._versBlob(c, 0.92);
  }

  _rendreApercu() {
    if (!this.source || !this.apercu) return;   // au format carte, l'atelier dessine son propre aperçu
    this._dessiner(this.apercu, [this.apercu.width, this.apercu.height]);
  }

  /* ---------- interactions ---------- */

  _brancher() {
    const el = this.conteneur;
    el.addEventListener('pointerdown', (ev) => {
      el.setPointerCapture(ev.pointerId);
      this.pointeurs.set(ev.pointerId, { x: ev.clientX, y: ev.clientY });
      ev.preventDefault();
    });
    el.addEventListener('pointermove', (ev) => {
      const p = this.pointeurs.get(ev.pointerId);
      if (!p) return;
      const autres = [...this.pointeurs.entries()].filter(([id]) => id !== ev.pointerId);
      if (autres.length === 0) {
        this.tx += ev.clientX - p.x;
        this.ty += ev.clientY - p.y;
        this._rendre();
      } else {
        // pincement : zoom autour du milieu des deux doigts
        const q = autres[0][1];
        const dAvant = Math.hypot(p.x - q.x, p.y - q.y);
        const dApres = Math.hypot(ev.clientX - q.x, ev.clientY - q.y);
        const rect = el.getBoundingClientRect();
        const mx = (ev.clientX + q.x) / 2 - rect.left;
        const my = (ev.clientY + q.y) / 2 - rect.top;
        if (dAvant > 0) this.zoomer(dApres / dAvant, mx, my);
      }
      p.x = ev.clientX; p.y = ev.clientY;
      ev.preventDefault();
    });
    const fin = (ev) => this.pointeurs.delete(ev.pointerId);
    el.addEventListener('pointerup', fin);
    el.addEventListener('pointercancel', fin);
    el.addEventListener('wheel', (ev) => {
      ev.preventDefault();
      const rect = el.getBoundingClientRect();
      this.zoomer(ev.deltaY < 0 ? 1.1 : 1 / 1.1,
                  ev.clientX - rect.left, ev.clientY - rect.top);
    }, { passive: false });
  }
}
