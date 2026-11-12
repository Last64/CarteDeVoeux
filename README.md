# Carte de vœux 2027 en réalité augmentée

Carte à colorier : on colorie la carte imprimée, on la vise avec le téléphone, les éléments
se soulèvent en pop-up **avec les couleurs du coloriage**, et un feu d'artifice part au-dessus du 2027.

Outils de la consigne : Illustrator (SVG) → Blender (animation, export glb) → A-Frame + MindAR → GitHub Pages.

## Contenu du dossier

| Fichier | Rôle |
|---|---|
| `index.html` | La scène A-Frame + MindAR |
| `app.js` | 3 composants : `coloriage`, `animation-glb`, `feux-artifice` |
| `style.css` | Bouton et messages |
| `assets/targets.mind` | La carte compilée pour la reconnaissance MindAR |
| `assets/carte.glb` | Le pop-up animé |
| `assets/decoupe.png` | Cache blanc sous les éléments qui se soulèvent |
| `libs/` | A-Frame 1.5.0 et MindAR 1.2.5 |
| `blender/calques-trait/` | La carte découpée en calques SVG (dessin au trait) |
| `blender/silhouettes/` | Les silhouettes pleines de chaque calque (SVG) |
| `impression/carte-a-imprimer.png` | La carte en 300 dpi |

## Tester sur ton PC

La caméra ne marche qu'en `https` ou sur `localhost`.

1. Ouvre le dossier dans VS Code, installe l'extension **Live Server**, clic droit sur `index.html` > *Open with Live Server*.
2. Autorise la webcam et montre-lui la carte imprimée (ou affichée sur un autre écran).

## Mettre en ligne (GitHub Pages)

1. Crée un dépôt public sur GitHub et envoie tout le contenu de ce dossier à la racine.
2. *Settings > Pages > Branch : main / root > Save*.
3. L'adresse est `https://TON-PSEUDO.github.io/NOM-DU-DEPOT/`. Fais-en un QR code à mettre sur la carte.

## Exporter l'animation depuis Blender

Dans ta scène Blender, la collection **PopUp_RA** contient le pop-up, posé sur ton SVG importé :
6 calques (vignes, chiffres_2027, chateau_colline, maisons, pont, cigogne), l'objet vide `cigogne_vol`
et le rectangle `cadre`.

1. Sélectionne tous les objets de la collection PopUp_RA (clic droit sur la collection > *Sélectionner les objets*).
2. *Fichier > Exporter > glTF 2.0 (.glb/.gltf)*, format **glTF Binary (.glb)**.
3. Coche *Inclure > Objets sélectionnés*, *Transformation > +Y vers le haut*,
   *Maillage > Appliquer les modificateurs* et *Animation*.
4. Enregistre sous `assets/carte.glb` (remplace le fichier existant).

Règles à garder pour que le site marche :
- le rectangle **`cadre`** représente la carte : le site s'en sert pour remettre le modèle à la bonne
  taille, donc ne le renomme pas et ne le supprime pas ;
- ne refais pas les **UV** des calques : elles correspondent à leur position sur la carte, c'est ce qui
  permet de récupérer le coloriage ;
- une animation dont le nom contient `boucle` tourne en boucle, les autres jouent une fois.

## Si tu changes le dessin de la carte

Il faut recompiler `targets.mind` avec la nouvelle image :
https://hiukim.github.io/mind-ar-js-doc/tools/compile
