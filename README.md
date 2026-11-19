# Carte de vœux 2027 en réalité augmentée

Carte à colorier de la préfecture du Haut-Rhin. Quand on vise la carte (imprimée ou affichée sur un écran)
avec un téléphone, le dessin prend des couleurs et ses éléments **sortent de la carte vers nous**, chacun à
sa profondeur, comme les décors d'un théâtre. Ensuite, rien ne s'arrête : les chiffres 2027 font la vague
(et deux fois un saut avec un tour sur eux-mêmes), les maisons respirent, les sapins se balancent dans le vent,
la rivière coule et une barque passe sous le pont, la cheminée fume, la neige tombe devant la carte,
et la cigogne s'envole vers nous avant de revenir se poser.
L'animation dure 12 secondes et tourne en boucle. Tout se passe dans le navigateur, sans application.

**Site :** https://last64.github.io/CarteDeVoeux/ (ouvrir sur le téléphone, autoriser la caméra, viser la carte)

![Aperçu de l'animation](apercu/apercu.png)

La vidéo `apercu/apercu-animation.mp4` montre l'animation complète.

---

## La chaîne de fabrication

```
Dessin (Illustrator)  →  calques PNG  →  Blender (animation)  →  carte.glb  →  page web A-Frame + MindAR  →  GitHub Pages
```

### 1. Le dessin et les calques

- `impression/carte-a-imprimer.png` est la carte à imprimer, à 300 dpi (215 × 105 mm).
  Le bas des deux « 2 » et du « 7 » manquait dans le dessin : il a été redessiné.
  La même correction est appliquée dans `impression/carte2027-corrigee.svg`.
- `blender/calques/` contient les 16 éléments du dessin, découpés et coloriés, en PNG transparents :
  les 4 chiffres, la rivière, les vignes, les feuilles, le château, le pont, les sapins, les maisons, le texte,
  et la cigogne en 3 morceaux (corps et 2 ailes) pour pouvoir battre des ailes.
  La rivière est un calque à part : elle sort du bas du « 0 », passe sous l'arche du milieu du pont
  et se perd doucement vers le texte (son PNG a un dégradé de transparence en bas).
  `bateau.png` est un élément en plus : une barque de la Petite Venise qui passe sur la rivière.
  Le fichier `calques.json` donne la position de chaque calque sur la carte, en pixels.

### 2. Blender : `blender/carte_popup.blend`

**Les repères**

- La carte fait **1 m de large** dans Blender, parce que dans MindAR 1 unité = la largeur de la carte.
- On regarde la carte **de face**, comme sur un écran ou tenue devant soi : **+X** = droite de la carte,
  **+Y** = haut de la carte, **+Z** = vers la personne qui regarde.
  Dans Blender, la carte est posée au sol (plan XY) : la vue de dessus (pavé num. 7) montre ce que voit le téléphone.
- La collection *Carte imprimée* sert seulement de repère. Elle est cachée au rendu, donc elle n'est pas exportée.

**Les calques**

- Chaque calque est un plan à la taille exacte de son PNG, placé à sa position sur la carte.
- Son **origine est sur sa charnière**, c'est-à-dire en bas de l'élément.
- Quand il sort, il **avance vers nous** (position Z) jusqu'à sa profondeur, de 0,01 pour la rivière à 0,085 pour les maisons (soit 2 mm à 2 cm sur la vraie carte).
  Plus il est devant dans le dessin, plus il avance. En sortant, son haut **bascule** vers nous puis revient (rotation X) :
  de face, c'est ce mouvement qui montre le relief.
- Ensuite, il **ne s'arrête plus** (le « mouvement continu ») : chaque mouvement est un **modificateur de courbe
  *Built-in Function* (sinus)**, visible dans le *Graph Editor*, panneau N > onglet *Modifiers*.
  - *Additive* : le sinus s'ajoute aux images clés de la même courbe (la sortie, les sauts des chiffres).
  - *Restrict Frame Range* + *Blend In / Blend Out* : il n'agit que pendant que l'élément est sorti, avec un fondu.
    Aux images 0 et 288 tout est à plat, donc la boucle ne se voit pas.
  - Les mouvements se font surtout **dans le plan de la carte** (monter, pencher, s'étirer),
    parce que ce sont eux qu'on voit le mieux quand on regarde la carte de face.
  - En plus, tout le relief **respire** : chaque élément avance et recule de 20 % de sa profondeur, tous en même temps.
    Comme c'est proportionnel, deux éléments ne passent jamais l'un devant l'autre.
- Le matériau est **sans ombre** : nœuds *Light Path > Is Camera Ray* + *Emission*,
  que l'export glTF transforme en `KHR_materials_unlit`. Les couleurs restent donc les mêmes quel que soit l'éclairage.
- La transparence du PNG passe par un nœud *Math > Round*, qui donne une découpe nette (`alphaMode MASK` dans le glTF).
  Seule exception : la rivière. Son alpha va directement au mélange, sans *Round*, pour garder les bords doux
  (`alphaMode BLEND`).

**L'animation** : images 0 à 288, soit 12 s à 24 i/s, avec des images clés et des modificateurs de courbe (sinus)

| Images | Ce qui se passe | Technique |
|---|---|---|
| 0 | La carte apparaît coloriée, à plat | – |
| 4 → 24 | La rivière se détache à peine de la carte : c'est le sol | Position Z seulement (0,01), sans bascule |
| 8 → 78 | Les éléments sortent de la carte un par un | Position Z, interpolation **Back** (rebond) + bascule en rotation X, interpolation **Elastic** |
| 48 → 269 | Les chiffres 2027 font la vague : ils montent, descendent et se penchent | Modificateurs sinus sur la position Y (± 0,016) et la rotation Z (± 5°), période 2 s, 6 images de décalage d'un chiffre à l'autre |
| 82 → 258 | Les maisons respirent comme dans un dessin animé | Sinus sur l'échelle : plus hautes (+ 5 %) et plus fines (− 3 %), puis l'inverse |
| 92 → 256 | « Meilleurs vœux » bat comme un cœur | Sinus sur l'échelle X et Y (± 4,5 %) |
| 38 → 273 | Les sapins et les feuilles se balancent dans le vent | Sinus sur la rotation Z (± 5 à 6°) autour de leur pied |
| 42 → 271 | Les vignes, le château et le pont flottent lentement | Sinus sur la position Y (± 0,005 à 0,006) et la rotation Z (± 1,2 à 1,5°), période 4 s |
| 84 → 252 | Le relief respire | Sinus sur la position Z de chaque élément (± 20 % de sa profondeur), tous en même temps |
| 70 → 250 | Une barque descend la rivière et passe sous le pont | Enfant du calque de la rivière (elle reste posée sur l'eau) : position le long de la rivière, taille qui augmente (elle s'approche) ; son demi-tour est caché sous le pont |
| 40 → 258 | Des reflets glissent sur l'eau | 9 petites ellipses blanches, enfants de la rivière, sur 3 « voies » : chacune descend en 4 s (position), apparaît, grossit puis s'efface (échelle) |
| 84 → 250 | La cheminée fume | Petites boules qui montent, grossissent puis disparaissent ; elles sont enfants du calque des maisons |
| 44 → 268 | Le drapeau alsacien se hisse sur la tour et flotte | Échelle (il se hisse) + 2 clés de forme qu'on alterne : la vague avance le long du tissu |
| 60 → 252 | La cigogne s'envole, vient vers nous, fait le tour de la carte et se repose | Vide parent *Cigogne* : position (elle grossit en s'approchant), demi-tour en rotation Y ; les ailes tournent autour de l'axe du corps |
| 84 et 196 | Deux grands sauts 2-0-2-7 : chaque chiffre saute et fait un tour sur lui-même | Position Y, interpolation **Bounce** + rotation Y de 360° |
| 0 → 288 | La neige tombe | 48 flocons à 6 branches, en bleu clair pour se voir sur le papier blanc : ils descendent en boucle (4 s ou 6 s par chute), tournent sur eux-mêmes (rotation Z) et se balancent. Ceux qui sont plus près de nous paraissent plus gros |
| 70 → 250 | Étoiles qui scintillent | Échelle de 0 à 1 puis 0 |
| 258 → 285 | Tout rentre dans la carte, puis l'animation recommence | Position Z jusqu'à 0, interpolation **Back** |

Les courbes se voient dans le *Graph Editor* et la *Dope Sheet*. Les sinus du mouvement continu
sont dans le *Graph Editor* : sélectionner une courbe, puis panneau N > onglet *Modifiers*.
Le script `blender/construire_carte.py`, dans l'onglet *Scripting*, reconstruit toute la scène.

**L'export** : *Fichier > Exporter > glTF 2.0*

- Format : **glTF Binary (.glb)** → `assets/carte.glb`
- Inclure : **Renderable Objects**. La carte repère n'est pas exportée.
- Transformation : **+Y Up**
- Animation : mode **Scene**, *Split by Object* décoché. Toute la timeline devient **une seule animation**.
- *Always Sample Animations* coché : les interpolations Back et Bounce et les sinus sont « cuits » image par image.

### 3. La page web : `index.html`

- **A-Frame 1.7.0** affiche la 3D.
- **MindAR 1.2.5** reconnaît la carte grâce à `assets/targets.mind`.
- **aframe-extras 7.6.0** fournit le composant `animation-mixer`, qui joue l'animation du `.glb`.

Ce sont les mêmes bibliothèques que dans l'exemple du cours.

```html
<a-entity id="carte" mindar-image-target="targetIndex: 0">
  <a-gltf-model src="#carte-popup" rotation="90 0 0" animation-mixer></a-gltf-model>
</a-entity>
```

- `rotation="90 0 0"` : dans Blender, la carte est au sol et les éléments montent vers Z.
  Dans MindAR, la carte est le plan XY et Z sort de la carte vers nous. La rotation de 90° fait correspondre les deux.
- Il n'y a ni échelle ni décalage à régler, parce que la carte fait 1 de large des deux côtés.
- Le petit script en bas de la page relance l'animation depuis le début chaque fois que la carte est retrouvée.
- `filterMinCF` et `filterBeta` lissent le suivi de MindAR : les éléments tremblent moins, avec un tout petit retard quand on bouge.
- `targets.mind` est l'image de la carte compilée par le compilateur de MindAR
  (le même que l'outil en ligne https://hiukim.github.io/mind-ar-js-doc/tools/compile).

`apercu.html` montre la même scène **sans caméra** : la carte de face, comme sur un écran, qui pivote doucement pour montrer le relief.
C'est pratique pour tester sur un ordinateur, ou comme solution de secours pendant une présentation.

### 4. La mise en ligne

La caméra ne fonctionne qu'en **https**, d'où GitHub Pages :
*Settings > Pages > Branch : main, dossier / (root) > Save*.

---

## Tester

- **Sur ordinateur** : ouvrir le dossier dans VS Code, puis *clic droit sur `apercu.html` > Open with Live Server*.
  Avec `index.html` et une webcam, on peut viser la carte imprimée ou affichée sur un autre écran.
- **Sur téléphone** : ouvrir le lien GitHub Pages et viser la carte.
  Elle doit être bien éclairée et entièrement visible au début. En bougeant un peu le téléphone,
  on voit les éléments à des profondeurs différentes.

## Modifier

- **L'animation** : modifier les images clés dans `carte_popup.blend` (ou l'amplitude et la période d'un sinus,
  dans le panneau *Modifiers* du *Graph Editor*), puis réexporter vers `assets/carte.glb` avec les réglages ci-dessus.
- **Le dessin** : recompiler `assets/targets.mind` avec la nouvelle image, puis refaire les calques concernés.

## Questions possibles à l'oral

- **Pourquoi les éléments avancent au lieu de se lever comme dans un livre pop-up ?** On regarde souvent la carte de face, sur un écran ou tenue devant soi. Un élément levé à la verticale serait alors vu par la tranche et paraîtrait plat. En avançant vers nous à des profondeurs différentes, avec une bascule au moment de sortir, le relief se voit de face, et encore plus quand on bouge le téléphone.

- **Pourquoi des modificateurs sinus plutôt que des images clés pour le mouvement continu ?** Un sinus se règle avec 3 valeurs
  (amplitude, période, décalage) au lieu de dizaines d'images clés, et on change le rythme en une seconde.
  Grâce à *Additive*, il s'ajoute aux sauts des chiffres sans les effacer. À l'export, *Always Sample Animations*
  calcule la position à chaque image : le résultat dans le .glb est exactement celui de Blender.
- **Pourquoi des mouvements dans le plan de la carte ?** De face, un élément qui avance vers nous grossit à peine :
  le mouvement ne se voit presque pas. Monter, pencher ou s'étirer se voit tout de suite, même avec le téléphone immobile.

- **Pourquoi la rivière est un calque à part ?** Au début, l'eau faisait partie du « 0 » : elle sautait et tournait avec le chiffre,
  et le reste de la rivière n'était pas colorié. Maintenant, toute la rivière est un calque posé près de la carte, derrière les autres :
  on la voit sortir du 0 et passer sous le pont, et la barque et les reflets glissent dessus.

- **Pourquoi un .glb ?** C'est un seul fichier qui contient la géométrie, les textures et l'animation. Il est léger (1,6 Mo) et lu directement par A-Frame (three.js).
- **Pourquoi des matériaux sans ombre ?** Pour garder les couleurs exactes du coloriage. Ainsi, le rendu ne dépend pas d'une lumière virtuelle qui ne correspond pas à la vraie pièce.
- **Pourquoi tout rentre dans la carte à la fin ?** Pour que la boucle soit invisible : la dernière image est identique à la première (tout à plat).
- **Pourquoi des clés de forme pour le drapeau ?** Le tissu est un seul objet. Deux clés de forme (*Vague_A* et *Vague_B*) le déforment en vague ; en alternant leurs poids, la vague avance le long du drapeau, sans os ni simulation.
- **Pourquoi des flocons bleu clair ?** Un flocon blanc serait invisible sur le papier blanc de la carte. Le bleu clair se voit sur le papier comme sur les couleurs du dessin.
- **Pourquoi pas de détection des couleurs du coloriage ?** Il faudrait beaucoup de code (shaders) et cela dépend de la lumière. Ici, tout est fait dans Blender, et le coloriage de la personne reste visible sur la carte, derrière les éléments.
