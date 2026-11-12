/* Carte de vœux 2027 en réalité augmentée — A-Frame + MindAR
   1. coloriage      : récupère les couleurs de la carte filmée et les plaque sur le modèle 3D
   2. animation-glb  : joue les animations exportées de Blender
   3. feux-artifice  : feux d'artifice en particules */

const HAUTEUR_CARTE = 297.6378 / 609.4488; // hauteur / largeur de la carte

/* ---------- 1. Coloriage en direct ---------- */
AFRAME.registerComponent('coloriage', {
  init() {
    const THREE = AFRAME.THREE;
    this.fige = false;
    this.visible = false;
    // Texture "à plat" de la carte, redressée depuis l'image de la caméra
    this.cible = new THREE.WebGLRenderTarget(1024, 512);
    this.sceneRedressage = new THREE.Scene();
    this.camRedressage = new THREE.OrthographicCamera(-1, 1, 1, -1, 0, 1);
    this.materiau = new THREE.ShaderMaterial({
      uniforms: {
        video: { value: null },
        mvp: { value: new THREE.Matrix4() },   // carte -> écran
        cadre: { value: new THREE.Vector4() }, // écran -> image vidéo
        hauteur: { value: HAUTEUR_CARTE },
      },
      vertexShader: `varying vec2 vUv; void main(){ vUv = uv; gl_Position = vec4(position.xy, 0.0, 1.0); }`,
      fragmentShader: `
        uniform sampler2D video; uniform mat4 mvp; uniform vec4 cadre; uniform float hauteur;
        varying vec2 vUv;
        void main(){
          // point de la carte correspondant à ce pixel de texture (le glb a ses UV origine en haut)
          vec4 p = mvp * vec4(vUv.x - 0.5, (0.5 - vUv.y) * hauteur, 0.0, 1.0);
          vec2 ecran = p.xy / p.w * 0.5 + 0.5;
          vec2 uvVideo = ecran * cadre.xy + cadre.zw;
          vec3 c = texture2D(video, uvVideo).rgb;
          c = clamp((c - 0.02) * 1.25, 0.0, 1.0); // papier un peu plus blanc
          gl_FragColor = vec4(c, 1.0);
        }`,
      depthTest: false, depthWrite: false,
    });
    this.sceneRedressage.add(new THREE.Mesh(new THREE.PlaneGeometry(2, 2), this.materiau));
    this.materiauModele = new THREE.MeshBasicMaterial({ map: this.cible.texture, side: THREE.DoubleSide });

    // On remplace les matériaux du modèle par la texture coloriée
    this.el.addEventListener('model-loaded', (e) => {
      e.detail.model.traverse((o) => { if (o.isMesh) o.material = this.materiauModele; });
    });
    this.el.addEventListener('targetFound', () => { this.visible = true; });
    this.el.addEventListener('targetLost', () => { this.visible = false; this.historique = []; });

    const bouton = document.getElementById('figer');
    bouton.addEventListener('click', () => {
      this.fige = !this.fige;
      bouton.setAttribute('aria-pressed', this.fige);
      bouton.textContent = this.fige ? 'Couleurs en direct' : 'Figer mes couleurs';
    });
  },

  tick() {
    if (!this.visible || this.fige) return;
    const THREE = AFRAME.THREE;
    const scene = this.el.sceneEl;
    const video = document.querySelector('video');
    if (!video || video.readyState < 2) return;
    if (!this.materiau.uniforms.video.value) {
      const t = new THREE.VideoTexture(video);
      t.colorSpace = THREE.SRGBColorSpace;
      this.materiau.uniforms.video.value = t;
    }
    // carte -> écran
    const cam = scene.camera;
    this.materiau.uniforms.mvp.value
      .multiplyMatrices(cam.projectionMatrix, cam.matrixWorldInverse)
      .multiply(this.el.object3D.matrixWorld);
    // On ne recopie les couleurs que si la carte est stable à l'écran (sinon elles bavent)
    // (la toute première fois, on copie tout de suite pour ne pas afficher un modèle vide)
    const stable = this.stable();
    if (!stable && this.premiereCopie) return;
    this.premiereCopie = true;
    // écran -> vidéo (MindAR recadre la vidéo en "cover" derrière le canvas)
    const c = scene.canvas.getBoundingClientRect();
    const v = video.getBoundingClientRect();
    this.materiau.uniforms.cadre.value.set(
      c.width / v.width, c.height / v.height,
      (c.left - v.left) / v.width, (v.bottom - c.bottom) / v.height);

    const r = scene.renderer;
    const ancienne = r.getRenderTarget();
    const xr = r.xr.enabled;
    r.xr.enabled = false;
    r.setRenderTarget(this.cible);
    r.render(this.sceneRedressage, this.camRedressage);
    r.setRenderTarget(ancienne);
    r.xr.enabled = xr;
  },
});

AFRAME.components.coloriage.Component.prototype.stable = function () {
  // déplacement des 4 coins de la carte à l'écran depuis l'image précédente
  const m = this.materiau.uniforms.mvp.value, v = new AFRAME.THREE.Vector4();
  const coins = [];
  for (const [x, y] of [[-0.5, -0.5], [0.5, -0.5], [0.5, 0.5], [-0.5, 0.5]]) {
    v.set(x, y * HAUTEUR_CARTE, 0, 1).applyMatrix4(m);
    coins.push(v.x / v.w, v.y / v.w);
  }
  // stable = les coins ont à peine bougé pendant les 12 dernières images
  this.historique = this.historique || [];
  this.historique.push(coins);
  if (this.historique.length > 12) this.historique.shift();
  if (this.historique.length < 12) return false;
  let ecart = 0;
  for (const h of this.historique) for (let i = 0; i < 8; i++) ecart = Math.max(ecart, Math.abs(h[i] - coins[i]));
  return ecart < 0.003;
};

/* ---------- 2. Animations du .glb (Blender) ---------- */
AFRAME.registerComponent('animation-glb', {
  init() {
    const THREE = AFRAME.THREE;
    this.actions = [];
    this.el.addEventListener('model-loaded', (e) => {
      const modele = e.detail.model;
      this.recadrer(modele);
      this.mixer = new THREE.AnimationMixer(modele);
      // Les animations dont le nom contient "boucle" tournent en boucle, les autres jouent une fois
      for (const clip of modele.animations || []) {
        const action = this.mixer.clipAction(clip);
        if (!clip.name.toLowerCase().includes('boucle')) {
          action.setLoop(THREE.LoopOnce);
          action.clampWhenFinished = true;
        }
        this.actions.push(action);
      }
      this.rejouer();
    });
    const carte = this.el.parentEl;
    carte.addEventListener('targetFound', () => this.rejouer());
  },
  // Le rectangle "cadre" du .glb représente la carte : on met le modèle à l'échelle pour que
  // ce cadre fasse 1 de large et soit centré. On peut donc travailler à n'importe quelle taille dans Blender.
  recadrer(modele) {
    const THREE = AFRAME.THREE;
    const cadre = modele.getObjectByName('cadre');
    if (!cadre) return;
    // position d'un objet dans le repère du modèle (on remonte ses parents un par un)
    const dansModele = (o) => {
      const m = new THREE.Matrix4();
      for (let n = o; n && n !== modele; n = n.parent) { n.updateMatrix(); m.premultiply(n.matrix); }
      return m;
    };
    const boite = new THREE.Box3();
    cadre.traverse((o) => {
      if (!o.isMesh) return;
      o.geometry.computeBoundingBox();
      boite.union(o.geometry.boundingBox.clone().applyMatrix4(dansModele(o)));
    });
    const centre = boite.getCenter(new THREE.Vector3());
    const echelle = 1 / (boite.max.x - boite.min.x);
    modele.scale.setScalar(echelle);
    modele.position.copy(centre).multiplyScalar(-echelle);
    cadre.visible = false;
  },
  rejouer() {
    if (!this.mixer) return;
    for (const a of this.actions) a.reset().play();
    this.mixer.setTime(0);
  },
  tick(t, dt) {
    if (this.mixer && this.el.object3D.visible) this.mixer.update(Math.min(dt, 100) / 1000);
  },
});

/* ---------- 3. Feux d'artifice en particules ---------- */
AFRAME.registerComponent('feux-artifice', {
  schema: {
    delai: { default: 2000 },      // ms après la détection avant le premier tir
    intervalle: { default: 700 },  // ms entre deux tirs
    particules: { default: 90 },   // par explosion
  },
  init() {
    const THREE = AFRAME.THREE;
    this.MAX = 6; // explosions simultanées
    const n = this.MAX * this.data.particules;
    this.pos = new Float32Array(n * 3);
    this.col = new Float32Array(n * 4); // rouge, vert, bleu, opacité
    this.vit = new Float32Array(n * 3);
    this.base = new Float32Array(n * 3);
    this.age = new Float32Array(this.MAX).fill(99);
    this.suivante = 0;
    this.attente = this.data.delai;
    const g = new THREE.BufferGeometry();
    g.setAttribute('position', new THREE.BufferAttribute(this.pos, 3));
    g.setAttribute('color', new THREE.BufferAttribute(this.col, 4));
    this.points = new THREE.Points(g, new THREE.PointsMaterial({
      size: 0.018, vertexColors: true, transparent: true, depthWrite: false, map: this.pastille(),
    }));
    this.points.frustumCulled = false;
    this.el.setObject3D('feux', this.points);
    this.el.parentEl.addEventListener('targetFound', () => { this.attente = this.data.delai; this.age.fill(99); });
  },
  pastille() { // petit disque lumineux
    const c = document.createElement('canvas'); c.width = c.height = 64;
    const x = c.getContext('2d'); const d = x.createRadialGradient(32, 32, 0, 32, 32, 32);
    d.addColorStop(0, '#fff'); d.addColorStop(0.4, 'rgba(255,255,255,.6)'); d.addColorStop(1, 'rgba(255,255,255,0)');
    x.fillStyle = d; x.fillRect(0, 0, 64, 64);
    return new AFRAME.THREE.CanvasTexture(c);
  },
  tirer() {
    const THREE = AFRAME.THREE;
    const i = this.suivante; this.suivante = (i + 1) % this.MAX;
    const P = this.data.particules;
    // centre de l'explosion : au-dessus du 2027 (x largeur, y hauteur de carte, z vers le spectateur)
    const cx = (Math.random() - 0.5) * 0.7, cy = 0.05 + Math.random() * 0.15, cz = 0.32 + Math.random() * 0.22;
    const teinte = new THREE.Color().setHSL(Math.random(), 1, 0.62);
    const force = 0.16 + Math.random() * 0.1;
    for (let k = 0; k < P; k++) {
      const j = (i * P + k) * 3;
      const u = Math.random() * 2 - 1, a = Math.random() * Math.PI * 2, s = Math.sqrt(1 - u * u);
      const f = force * (0.75 + Math.random() * 0.25);
      this.vit[j] = s * Math.cos(a) * f; this.vit[j + 1] = s * Math.sin(a) * f; this.vit[j + 2] = u * f;
      this.pos[j] = cx; this.pos[j + 1] = cy; this.pos[j + 2] = cz;
      this.base[j] = teinte.r; this.base[j + 1] = teinte.g; this.base[j + 2] = teinte.b;
    }
    this.age[i] = 0;
  },
  tick(t, dtms) {
    if (!this.el.parentEl.object3D.visible) return;
    // la taille des points suit l'échelle de la carte à l'écran
    this.points.material.size = 0.02 * this.el.object3D.getWorldScale(this.echelle || (this.echelle = new AFRAME.THREE.Vector3())).x;
    const dt = Math.min(dtms, 100) / 1000, P = this.data.particules, DUREE = 1.6;
    this.attente -= dtms;
    if (this.attente <= 0) { this.tirer(); this.attente = this.data.intervalle * (0.6 + Math.random() * 0.8); }
    for (let i = 0; i < this.MAX; i++) {
      this.age[i] += dt;
      const vie = Math.max(0, 1 - this.age[i] / DUREE), frein = Math.exp(-2.2 * dt);
      for (let k = 0; k < P; k++) {
        const j = (i * P + k) * 3;
        this.vit[j] *= frein; this.vit[j + 1] *= frein; this.vit[j + 2] = this.vit[j + 2] * frein - 0.05 * dt; // retombe vers la carte
        this.pos[j] += this.vit[j] * dt; this.pos[j + 1] += this.vit[j + 1] * dt; this.pos[j + 2] += this.vit[j + 2] * dt;
        const c = (i * P + k) * 4; // la particule s'efface en fin de vie
        this.col[c] = this.base[j]; this.col[c + 1] = this.base[j + 1]; this.col[c + 2] = this.base[j + 2]; this.col[c + 3] = Math.min(1, vie * 1.6);
      }
    }
    this.points.geometry.attributes.position.needsUpdate = true;
    this.points.geometry.attributes.color.needsUpdate = true;
  },
});

/* ---------- Interface ---------- */
window.addEventListener('DOMContentLoaded', () => {
  const scene = document.querySelector('a-scene');
  const carte = document.getElementById('carte');
  const aide = document.getElementById('aide');
  const figer = document.getElementById('figer');
  const chargement = document.getElementById('chargement');
  scene.addEventListener('arReady', () => { chargement.hidden = true; });
  scene.addEventListener('arError', () => {
    chargement.hidden = false;
    chargement.textContent = "Impossible d'ouvrir la caméra. Autorise-la et ouvre la page en https.";
  });
  carte.addEventListener('targetFound', () => { aide.hidden = true; figer.hidden = false; });
  carte.addEventListener('targetLost', () => { aide.hidden = false; });
});
