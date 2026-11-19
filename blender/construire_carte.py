"""
Carte de voeux 2027 — construction de la scène Blender (carte animée pour la RA).

Ce script refait toute la scène : il suffit de l'ouvrir dans l'éditeur de texte
de Blender (onglet Scripting) et de cliquer sur "Run Script".

Repères à retenir pour l'oral :
- La carte fait 1 m de large dans Blender (1 unité = largeur de la carte, comme dans MindAR).
- On la regarde DE FACE, comme sur un écran ou tenue devant soi :
    +X = droite de la carte, +Y = HAUT de la carte, +Z = vers la personne qui regarde.
  Dans Blender, la vue de dessus (pavé num. 7) = ce que voit le téléphone.
- Les éléments ne se lèvent pas : ils SORTENT de la carte vers nous, chacun à sa profondeur
  (comme les décors d'un théâtre). Plus un élément est devant dans le dessin, plus il avance.
- Les matériaux sont "sans ombre" (unlit) et découpés par l'alpha du PNG.
- L'animation dure 12 s (288 images à 24 i/s) et boucle : tout rentre dans la carte à la fin.
- Deux versions : "Feux d'artifice" (assets/carte.glb) ou "Neige" (assets/carte-sans-feux.glb).
  On passe de l'une à l'autre avec l'appareil photo des 2 collections dans l'Outliner.
"""
import bpy, json, math, os
from mathutils import Vector, Matrix
from bpy_extras import anim_utils

# ------------------------------------------------------------------ chemins
BLEND_DIR = os.path.dirname(bpy.data.filepath) if bpy.data.filepath else r"C:\Users\mhdme\Documents\GitHub\CarteDeVoeux\blender"
CALQUES = os.path.join(BLEND_DIR, "calques")
CARTE_PNG = os.path.join(BLEND_DIR, "..", "impression", "carte-a-imprimer.png")

# ------------------------------------------------------------------ réglages
W_PX, H_PX = 2540, 1241          # taille du dessin en pixels
K = 1.0 / W_PX                   # 1 pixel = 1/2540 m  ->  la carte fait 1 m de large
FPS, FIN = 24, 288               # 12 secondes
INFO = json.load(open(os.path.join(CALQUES, "calques.json"), encoding="utf-8"))

def px(x, y):
    """Pixel du dessin -> coordonnées Blender (centre de la carte = origine)."""
    return ((x - W_PX / 2) * K, (H_PX / 2 - y) * K)


# ================================================================== 1. SCÈNE
def preparer_scene():
    for o in list(bpy.data.objects): bpy.data.objects.remove(o, do_unlink=True)
    for c in list(bpy.data.collections): bpy.data.collections.remove(c)
    for d in (bpy.data.meshes, bpy.data.materials, bpy.data.images, bpy.data.actions, bpy.data.cameras, bpy.data.lights):
        for x in list(d): d.remove(x)
    sc = bpy.context.scene
    sc.render.fps = FPS
    sc.frame_start, sc.frame_end, sc.frame_current = 0, FIN, 0
    sc.unit_settings.system = 'METRIC'
    sc.render.resolution_x, sc.render.resolution_y = 1280, 720


def collection(nom, parent=None):
    c = bpy.data.collections.new(nom)
    (parent or bpy.context.scene.collection).children.link(c)
    return c


# ================================================================== 2. MATÉRIAUX
def materiau_calque(nom, chemin_image):
    """Matériau sans ombre (KHR_materials_unlit) + découpe nette par l'alpha (alphaMode MASK)."""
    mat = bpy.data.materials.new(nom)
    mat.use_nodes = True
    nt = mat.node_tree; nt.nodes.clear(); N = nt.nodes.new; Lk = nt.links.new
    sortie = N('ShaderNodeOutputMaterial'); sortie.location = (650, 0)
    decoupe = N('ShaderNodeMixShader'); decoupe.location = (450, 0); decoupe.label = "Découpe (alpha)"
    transp = N('ShaderNodeBsdfTransparent'); transp.location = (250, 160)
    sans_ombre = N('ShaderNodeMixShader'); sans_ombre.location = (250, -60); sans_ombre.label = "Sans ombre"
    chemin = N('ShaderNodeLightPath'); chemin.location = (0, 300)
    transp2 = N('ShaderNodeBsdfTransparent'); transp2.location = (40, 0)
    emission = N('ShaderNodeEmission'); emission.location = (40, -160)
    image = N('ShaderNodeTexImage'); image.location = (-420, -120)
    image.image = bpy.data.images.load(chemin_image, check_existing=True)
    image.interpolation = 'Linear'; image.extension = 'CLIP'
    arrondi = N('ShaderNodeMath'); arrondi.operation = 'ROUND'; arrondi.location = (-100, 180); arrondi.label = "Alpha 0 ou 1"
    Lk(image.outputs['Color'], emission.inputs['Color'])
    Lk(image.outputs['Alpha'], arrondi.inputs[0])
    Lk(arrondi.outputs[0], decoupe.inputs[0])
    Lk(transp.outputs[0], decoupe.inputs[1])
    Lk(chemin.outputs['Is Camera Ray'], sans_ombre.inputs[0])
    Lk(transp2.outputs[0], sans_ombre.inputs[1])
    Lk(emission.outputs[0], sans_ombre.inputs[2])
    Lk(sans_ombre.outputs[0], decoupe.inputs[2])
    Lk(decoupe.outputs[0], sortie.inputs['Surface'])
    mat.use_backface_culling = False
    return mat


def materiau_couleur(nom, rgb):
    """Couleur unie sans ombre (feux d'artifice, étoiles)."""
    mat = bpy.data.materials.new(nom)
    mat.use_nodes = True
    nt = mat.node_tree; nt.nodes.clear(); N = nt.nodes.new; Lk = nt.links.new
    sortie = N('ShaderNodeOutputMaterial'); sortie.location = (400, 0)
    sans_ombre = N('ShaderNodeMixShader'); sans_ombre.location = (200, 0); sans_ombre.label = "Sans ombre"
    chemin = N('ShaderNodeLightPath'); chemin.location = (-50, 250)
    transp = N('ShaderNodeBsdfTransparent'); transp.location = (0, 40)
    emission = N('ShaderNodeEmission'); emission.location = (0, -120)
    emission.inputs['Color'].default_value = (*rgb, 1.0)
    Lk(chemin.outputs['Is Camera Ray'], sans_ombre.inputs[0])
    Lk(transp.outputs[0], sans_ombre.inputs[1])
    Lk(emission.outputs[0], sans_ombre.inputs[2])
    Lk(sans_ombre.outputs[0], sortie.inputs['Surface'])
    mat.use_backface_culling = False
    mat.diffuse_color = (*rgb, 1.0)
    return mat


def hexrgb(h):
    h = h.lstrip('#')
    srgb = [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    # Blender travaille en linéaire : on convertit la couleur sRGB
    return tuple(c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4 for c in srgb)


# ================================================================== 3. PLANS DES CALQUES
def plan_calque(nom, pivot_px, coll, z=0.0, parent=None):
    """Plan à la taille exacte du calque PNG, origine sur le pivot (charnière)."""
    x0, y0, x1, y1 = INFO[nom]['box']
    pxv, pyv = pivot_px
    me = bpy.data.meshes.new(nom + "_plan")
    me.from_pydata([((x0 - pxv) * K, (pyv - y1) * K, 0), ((x1 - pxv) * K, (pyv - y1) * K, 0),
                    ((x1 - pxv) * K, (pyv - y0) * K, 0), ((x0 - pxv) * K, (pyv - y0) * K, 0)], [], [(0, 1, 2, 3)])
    uv = me.uv_layers.new(name="UVMap")
    for i, c in enumerate([(0, 0), (1, 0), (1, 1), (0, 1)]):
        uv.data[i].uv = c
    me.materials.append(materiau_calque("M_" + nom, os.path.join(CALQUES, nom + ".png")))
    ob = bpy.data.objects.new(nom, me)
    coll.objects.link(ob)
    wx, wy = px(pxv, pyv)
    if parent is None:
        ob.location = (wx, wy, z)
    else:
        ob.parent = parent
        pw = parent.location
        ob.location = (wx - pw.x, wy - pw.y, z)
    return ob


def vide(nom, coll, loc=(0, 0, 0), parent=None, taille=0.03, forme='PLAIN_AXES'):
    ob = bpy.data.objects.new(nom, None)
    ob.empty_display_type = forme; ob.empty_display_size = taille
    ob.location = loc
    if parent: ob.parent = parent
    coll.objects.link(ob)
    return ob


# ================================================================== 4. IMAGES CLÉS
def fcourbe(ob, chemin, index):
    ad = ob.animation_data
    sac = anim_utils.action_get_channelbag_for_slot(ad.action, ad.action_slot)
    return sac.fcurves.find(chemin, index=index)


def cle(ob, chemin, index, frame, valeur, interp='BEZIER', easing='AUTO', back=None):
    """Pose une image clé et règle l'interpolation du segment qui suit."""
    getattr(ob, chemin)[index] = valeur
    ob.keyframe_insert(chemin, index=index, frame=frame)
    fc = fcourbe(ob, chemin, index)
    for k in fc.keyframe_points:
        if abs(k.co.x - frame) < 1e-3:
            k.interpolation = interp; k.easing = easing
            if back is not None: k.back = back
    return fc


R = math.radians

# Profondeur de chaque élément quand il est sorti (en largeur de carte : 0,1 = 2 cm).
# De l'arrière du paysage vers l'avant : plus c'est devant dans le dessin, plus ça avance.
PROFONDEUR = {
    'vignes': 0.022, 'feuilles': 0.035, 'chateau': 0.040,
    'chiffre_2a': 0.050, 'chiffre_0': 0.053, 'chiffre_2b': 0.050, 'chiffre_7': 0.053,
    'texte': 0.060, 'pont': 0.065, 'sapins_2': 0.072, 'sapin_1': 0.080, 'maisons': 0.085,
}


def sortie(ob, debut, repli, profondeur, duree=20):
    """Le calque sort de la carte vers nous (avec rebond), puis y rentre à la fin."""
    z0 = ob.location.z
    # 1) il avance vers le spectateur (position Z)
    cle(ob, 'location', 2, 0, z0, 'CONSTANT')
    cle(ob, 'location', 2, debut, z0, 'BACK', 'EASE_OUT', back=1.6)
    cle(ob, 'location', 2, debut + duree, z0 + profondeur, 'CONSTANT')
    cle(ob, 'location', 2, repli, z0 + profondeur, 'BACK', 'EASE_IN', back=1.4)
    cle(ob, 'location', 2, repli + 10, z0, 'CONSTANT')
    cle(ob, 'location', 2, FIN, z0, 'CONSTANT')
    # 2) en sortant, son haut bascule vers nous puis revient en tremblant (rotation X) :
    #    c'est ce mouvement qui montre le relief quand on regarde la carte de face
    cle(ob, 'rotation_euler', 0, 0, 0.0, 'CONSTANT')
    cle(ob, 'rotation_euler', 0, debut, 0.0, 'QUAD', 'EASE_OUT')
    cle(ob, 'rotation_euler', 0, debut + 6, R(30), 'ELASTIC', 'EASE_OUT')
    cle(ob, 'rotation_euler', 0, debut + 32, 0.0, 'CONSTANT')
    cle(ob, 'rotation_euler', 0, repli, 0.0, 'QUAD', 'EASE_OUT')
    cle(ob, 'rotation_euler', 0, repli + 5, R(18), 'QUAD', 'EASE_IN')
    cle(ob, 'rotation_euler', 0, repli + 10, 0.0, 'CONSTANT')
    cle(ob, 'rotation_euler', 0, FIN, 0.0, 'CONSTANT')
    return z0 + profondeur


# Une fois sorti, chaque élément "respire" : il avance et recule un peu (Z), monte et descend (Y)
# et pivote légèrement sur lui-même (rotation Y). Comme le relief change tout le temps,
# on voit la profondeur même sans bouger le téléphone.
#          amplitude Z, amplitude Y, pivot (°), période (images), décalage
FLOTTE = {
    'vignes':     (0.008, 0.003, 5, 96, 0),
    'feuilles':   (0.009, 0.000, 0, 84, 10),
    'chateau':    (0.008, 0.003, 5, 108, 20),
    'chiffre_2a': (0.010, 0.000, 0, 72, 0), 'chiffre_0': (0.010, 0.000, 0, 72, 9),
    'chiffre_2b': (0.010, 0.000, 0, 72, 18), 'chiffre_7': (0.010, 0.000, 0, 72, 27),
    'pont':       (0.009, 0.003, 6, 120, 30),
    'sapins_2':   (0.010, 0.000, 0, 90, 5),
    'sapin_1':    (0.010, 0.000, 0, 78, 15),
    'maisons':    (0.010, 0.004, 6, 100, 40),
    'texte':      (0.012, 0.004, 6, 88, 12),
}

def oscille(ob, chemin, index, t1, t2, centre, amplitude, periode, decalage):
    """Va-et-vient doux autour de "centre" entre les images t1 et t2."""
    cle(ob, chemin, index, t1, centre)
    f, signe = t1 + periode // 4 + decalage, 1
    while f < t2 - periode // 4:
        cle(ob, chemin, index, f, centre + signe * amplitude)
        signe = -signe; f += periode // 2
    cle(ob, chemin, index, t2, centre, 'CONSTANT')


def flotter(ob, debut, repli, z_sorti, nom):
    amp_z, amp_y, pivot, periode, decalage = FLOTTE[nom]
    t1, t2 = debut + 34, repli - 2
    oscille(ob, 'location', 2, t1, t2, z_sorti, amp_z, periode, decalage)
    if amp_y:
        y0 = ob.location.y
        cle(ob, 'location', 1, 0, y0, 'CONSTANT'); cle(ob, 'location', 1, FIN, y0, 'CONSTANT')
        oscille(ob, 'location', 1, t1, t2, y0, amp_y, int(periode * 0.75), decalage + 7)
    if pivot:
        cle(ob, 'rotation_euler', 1, 0, 0.0, 'CONSTANT'); cle(ob, 'rotation_euler', 1, FIN, 0.0, 'CONSTANT')
        oscille(ob, 'rotation_euler', 1, t1, t2, 0.0, R(pivot), int(periode * 1.25), decalage + 3)


def balancement(ob, debut, fin, amplitude=3.0, periode=48, dephasage=0):
    """Petit balancement dans le plan de la carte (rotation Z autour du pied) : le vent."""
    f = debut; signe = 1
    cle(ob, 'rotation_euler', 2, 0, 0.0, 'CONSTANT')
    cle(ob, 'rotation_euler', 2, f, 0.0)
    f += periode // 4 + dephasage
    while f < fin - periode // 2:
        cle(ob, 'rotation_euler', 2, f, R(amplitude * signe))
        signe = -signe; f += periode // 2
    cle(ob, 'rotation_euler', 2, fin, 0.0, 'CONSTANT')
    cle(ob, 'rotation_euler', 2, FIN, 0.0, 'CONSTANT')


# ================================================================== 5. LA CARTE QUI S'OUVRE
# nom : (image où il sort, image où il rentre)
CALENDRIER = {
    'vignes':     (12, 273),
    'chiffre_2a': (18, 271), 'chiffre_0': (23, 270), 'chiffre_2b': (28, 269), 'chiffre_7': (33, 268),
    'feuilles':   (8, 275),
    'chateau':    (26, 267),
    'pont':       (36, 265),
    'sapins_2':   (42, 263),
    'sapin_1':    (47, 262),
    'maisons':    (52, 260),
    'texte':      (62, 258),
}

def construire_popup(racine, coll):
    pieces = {}
    for rang, nom in enumerate(CALENDRIER):
        x0, y0, x1, y1 = INFO[nom]['box']
        charniere = INFO[nom]['hinge']
        # pivot = milieu du bas de l'élément ; petit décalage pour éviter que deux calques
        # à plat se chevauchent exactement au même endroit (z-fighting)
        ob = plan_calque(nom, ((x0 + x1) / 2, charniere), coll, z=0.0004 + 0.0003 * rang, parent=racine)
        debut, repli = CALENDRIER[nom]
        z_sorti = sortie(ob, debut, repli, PROFONDEUR[nom])
        flotter(ob, debut, repli, z_sorti, nom)
        pieces[nom] = ob
    # la vague 2-0-2-7 : chaque chiffre saute vers le haut et fait un tour sur lui-même
    for tour, vague in ((1, 84), (2, 196)):
        for i, nom in enumerate(('chiffre_2a', 'chiffre_0', 'chiffre_2b', 'chiffre_7')):
            ob = pieces[nom]; y0 = ob.location.y; f = vague + 5 * i
            if tour == 1:
                cle(ob, 'location', 1, 0, y0, 'CONSTANT')
                cle(ob, 'rotation_euler', 1, 0, 0.0, 'CONSTANT')
            cle(ob, 'location', 1, f, y0, 'QUAD', 'EASE_OUT')
            cle(ob, 'location', 1, f + 7, y0 + 0.03, 'BOUNCE', 'EASE_OUT')
            cle(ob, 'location', 1, f + 22, y0, 'CONSTANT')
            cle(ob, 'rotation_euler', 1, f, R(360 * (tour - 1)), 'CUBIC', 'EASE_IN_OUT')
            cle(ob, 'rotation_euler', 1, f + 16, R(360 * tour), 'CONSTANT')
            if tour == 2:
                cle(ob, 'location', 1, FIN, y0, 'CONSTANT')
                cle(ob, 'rotation_euler', 1, FIN, R(720), 'CONSTANT')
    # le vent dans les sapins et les feuilles de vigne
    balancement(pieces['sapin_1'], 64, 258, amplitude=3.0, periode=46)
    balancement(pieces['sapins_2'], 64, 258, amplitude=2.5, periode=54, dephasage=6)
    balancement(pieces['feuilles'], 30, 270, amplitude=2.5, periode=60)
    return pieces


# ================================================================== 5 bis. LES PETITS DÉTAILS QUI VIVENT
def construire_fumee(maisons, coll, n=5):
    """Fumée de la cheminée : des petites boules qui montent, grossissent puis disparaissent."""
    me = maillage_flocon("fumee", '#E4E9EE')
    cx, cy = (652 - 482.5) * K, (1000 - 522) * K      # haut de la cheminée, dans le repère du calque des maisons
    P = 60                                              # une bouffée dure 2,5 s
    for k in range(n):
        b = bpy.data.objects.new(f"Fumee_{k + 1}", me); coll.objects.link(b); b.parent = maisons
        for i in range(3): cle(b, 'scale', i, 0, 0.0, 'CONSTANT')
        s = 84 + k * (P // n)
        while s + P <= 250:
            cle(b, 'location', 0, s, cx, 'LINEAR'); cle(b, 'location', 1, s, cy, 'QUAD', 'EASE_OUT')
            cle(b, 'location', 2, s, 0.003, 'CONSTANT')
            cle(b, 'location', 0, s + P - 1, cx + 0.03, 'CONSTANT'); cle(b, 'location', 1, s + P - 1, cy + 0.07, 'CONSTANT')
            for i in range(3):
                cle(b, 'scale', i, s, 0.003, 'QUAD', 'EASE_OUT')
                cle(b, 'scale', i, s + P // 2, 0.011, 'QUAD', 'EASE_IN')
                cle(b, 'scale', i, s + P - 1, 0.0, 'CONSTANT')
            s += P
        for i in range(3): cle(b, 'scale', i, FIN, 0.0, 'CONSTANT')


def construire_drapeau(chateau, coll):
    """Drapeau alsacien (rouge et blanc) sur la tour : il se hisse puis flotte (2 clés de forme)."""
    base = vide("Drapeau", coll, ((2300 - 2126.5) * K, (705 - 300) * K, 0.001), parent=chateau, taille=0.01)
    h, e, L, F, n = 0.032, 0.0012, 0.036, 0.022, 8
    # le mât
    me = bpy.data.meshes.new("mat")
    v = [(x, y, z) for y in (0, h) for (x, z) in ((-e, -e), (e, -e), (e, e), (-e, e))]
    f = [(0, 1, 2, 3), (4, 7, 6, 5), (0, 4, 5, 1), (1, 5, 6, 2), (2, 6, 7, 3), (3, 7, 4, 0)]
    me.from_pydata(v, [], f); me.materials.append(materiau_couleur("M_mat", hexrgb('#5A4A3A')))
    mat = bpy.data.objects.new("Mat", me); coll.objects.link(mat); mat.parent = base
    # le tissu : bande rouge en haut, bande blanche en bas
    me = bpy.data.meshes.new("drapeau")
    v = [(L * i / n, h - F * j / 2, 0) for j in range(3) for i in range(n + 1)]
    f = [(j * (n + 1) + i, j * (n + 1) + i + 1, (j + 1) * (n + 1) + i + 1, (j + 1) * (n + 1) + i) for j in range(2) for i in range(n)]
    me.from_pydata(v, [], f)
    me.materials.append(materiau_couleur("M_drapeau_rouge", hexrgb('#D72631')))
    me.materials.append(materiau_couleur("M_drapeau_blanc", hexrgb('#FFFFFF')))
    for k, poly in enumerate(me.polygons): poly.material_index = 0 if k < n else 1
    tissu = bpy.data.objects.new("Drapeau_tissu", me); coll.objects.link(tissu); tissu.parent = base
    # deux clés de forme décalées d'un quart d'onde : en les alternant, la vague avance
    tissu.shape_key_add(name="Base", from_mix=False)
    for nom, fn in (("Vague_A", math.sin), ("Vague_B", math.cos)):
        kb = tissu.shape_key_add(name=nom, from_mix=False); kb.slider_min = -1.0
        for i, p in enumerate(v):
            kb.data[i].co = (p[0], p[1], 0.005 * (p[0] / L) * fn(2 * math.pi * p[0] / L))
    for k_f, f0 in enumerate(range(0, FIN + 1, 6)):
        cle_forme(tissu, "Vague_A", f0, (1, 0, -1, 0)[k_f % 4])
        cle_forme(tissu, "Vague_B", f0, (0, 1, 0, -1)[k_f % 4])
    # il se hisse quand le château sort, et redescend à la fin
    for i in range(3):
        cle(base, 'scale', i, 0, 0.0, 'CONSTANT')
        cle(base, 'scale', i, 44, 0.0, 'BACK', 'EASE_OUT')
        cle(base, 'scale', i, 56, 1.0, 'CONSTANT')
        cle(base, 'scale', i, 262, 1.0, 'QUAD', 'EASE_IN')
        cle(base, 'scale', i, 268, 0.0, 'CONSTANT')
        cle(base, 'scale', i, FIN, 0.0, 'CONSTANT')


# Le trajet de la barque sur la rivière : elle sort de derrière le « 0 »,
# passe sous l'arche du milieu du pont et grossit en s'approchant de nous.
RIVIERE = [  # (image, x, y en pixels du dessin, taille)
    (70, 1185, 515, 0.45), (95, 1150, 575, 0.52), (120, 1180, 630, 0.58), (145, 1265, 672, 0.65),
    (165, 1320, 735, 0.72), (185, 1300, 805, 0.80), (205, 1265, 880, 0.88), (225, 1215, 945, 0.95), (242, 1185, 995, 1.0)]

def construire_bateau(racine, coll):
    W, Hb = 220, 130                                   # taille du calque bateau.png en pixels
    me = bpy.data.meshes.new("bateau_plan")
    me.from_pydata([(-W / 2 * K, 0, 0), (W / 2 * K, 0, 0), (W / 2 * K, Hb * K, 0), (-W / 2 * K, Hb * K, 0)], [], [(0, 1, 2, 3)])
    uv = me.uv_layers.new(name="UVMap")
    for i, c in enumerate([(0, 0), (1, 0), (1, 1), (0, 1)]): uv.data[i].uv = c
    me.materials.append(materiau_calque("M_bateau", os.path.join(CALQUES, "bateau.png")))
    ob = bpy.data.objects.new("Bateau", me); coll.objects.link(ob); ob.parent = racine
    x0, y0 = px(*RIVIERE[0][1:3]); ob.location = (x0, y0, 0.022)
    for i in range(3): cle(ob, 'scale', i, 0, 0.0, 'CONSTANT')
    for i in range(3): cle(ob, 'scale', i, 62, 0.0, 'QUAD', 'EASE_OUT')
    for (f, xp, yp, taille) in RIVIERE:
        x, y = px(xp, yp)
        cle(ob, 'location', 0, f, x); cle(ob, 'location', 1, f, y)
        for i in range(3): cle(ob, 'scale', i, f, taille)
    for i in range(3): cle(ob, 'scale', i, 250, 0.0, 'CONSTANT')
    for i in range(3): cle(ob, 'scale', i, FIN, 0.0, 'CONSTANT')
    cle(ob, 'location', 2, 0, 0.022, 'CONSTANT')
    # proue vers la droite au début, puis demi-tour caché sous le pont (rotation Y)
    cle(ob, 'rotation_euler', 1, 0, 0.0, 'CONSTANT')
    cle(ob, 'rotation_euler', 1, 158, 0.0)
    cle(ob, 'rotation_euler', 1, 182, R(180), 'CONSTANT')
    cle(ob, 'rotation_euler', 1, FIN, R(180), 'CONSTANT')
    return ob


# ================================================================== 6. LA CIGOGNE
def construire_cigogne(racine, coll):
    maison = (2098, 222)                               # pivot du corps (pixels du dessin)
    hx, hy = px(*maison)
    cig = vide("Cigogne", coll, (hx, hy, 0.002), parent=racine, taille=0.04, forme='SPHERE')
    corps = plan_calque('cigogne_corps', maison, coll, z=0.0, parent=cig)
    aile_av = plan_calque('cigogne_aile_avant', (2100, 222), coll, z=0.0008, parent=cig)
    aile_ar = plan_calque('cigogne_aile_arriere', (2128, 232), coll, z=-0.0008, parent=cig)

    # trajectoire : (image, x, y, z, sens) — sens 0 = bec vers la gauche, 180 = demi-tour vers la droite
    # z = distance devant la carte : la cigogne vient vers nous (elle grossit) puis repart.
    vol = [(74, hx - 0.02, hy + 0.01, 0.14, 0), (92, 0.12, 0.22, 0.18, 0), (110, -0.10, 0.24, 0.20, 0),
           (128, -0.30, 0.20, 0.22, 20), (142, -0.40, 0.08, 0.26, 90), (156, -0.28, -0.04, 0.32, 180),
           (174, -0.02, -0.08, 0.36, 180), (192, 0.22, -0.04, 0.32, 190), (208, 0.38, 0.06, 0.26, 270),
           (222, 0.36, 0.14, 0.18, 330), (236, hx + 0.01, hy + 0.01, 0.10, 360)]
    # posée sur la carte
    for f in (0, 60):
        for i, v in enumerate((hx, hy, 0.002)): cle(cig, 'location', i, f, v)
        cle(cig, 'rotation_euler', 1, f, 0.0)
        for i in range(3): cle(cig, 'scale', i, f, 1.0)
    # envol puis tour de la scène (le demi-tour = rotation Y : elle se retourne)
    for (f, x, y, z, sens) in vol:
        for i, v in enumerate((x, y, z)): cle(cig, 'location', i, f, v)
        cle(cig, 'rotation_euler', 1, f, R(sens))
        for i in range(3): cle(cig, 'scale', i, f, 2.2)
    # elle se repose à sa place
    for f in (252, FIN):
        for i, v in enumerate((hx, hy, 0.002)): cle(cig, 'location', i, f, v)
        cle(cig, 'rotation_euler', 1, f, R(360))
        for i in range(3): cle(cig, 'scale', i, f, 1.0)
    # battements d'ailes (autour de l'axe du corps : elles sortent du plan de la carte)
    for aile, signe in ((aile_av, 1), (aile_ar, -1)):
        cle(aile, 'rotation_euler', 0, 0, 0.0, 'CONSTANT')
        cle(aile, 'rotation_euler', 0, 60, 0.0)
        f, haut = 65, True
        while f <= 242:
            cle(aile, 'rotation_euler', 0, f, R(signe * (12 if haut else 95)))
            haut = not haut; f += 5
        cle(aile, 'rotation_euler', 0, 252, 0.0, 'CONSTANT')
        cle(aile, 'rotation_euler', 0, FIN, 0.0, 'CONSTANT')
    return cig


# ================================================================== 7. FEUX D'ARTIFICE
# Chaque gerbe est UN seul objet avec 3 "clés de forme" (shape keys) :
#   Base      = toutes les étincelles réduites à un point au centre (invisible)
#   Explosion = les étincelles éparpillées sur une sphère
#   Fin       = encore plus loin, un peu plus bas (gravité) et réduites à rien
# L'animation ne fait que changer le poids des clés de forme -> fichier léger.
ETINCELLE_V = [(0, 0, 0.011), (0, 0, -0.0045), (0.0022, 0, 0), (-0.0022, 0, 0), (0, 0.0022, 0), (0, -0.0022, 0)]
ETINCELLE_F = [(0, 2, 4), (0, 4, 3), (0, 3, 5), (0, 5, 2), (1, 4, 2), (1, 3, 4), (1, 5, 3), (1, 2, 5)]
BAS_DE_LA_CARTE = -(H_PX / 2) * K - 0.01


def directions(n):
    """n directions bien réparties sur une sphère (spirale de Fibonacci)."""
    out = []
    for i in range(n):
        z = 1 - 2 * (i + 0.5) / n
        r = math.sqrt(1 - z * z); a = i * math.pi * (3 - math.sqrt(5))
        out.append(Vector((r * math.cos(a), r * math.sin(a), z)))
    return out


def cle_forme(ob, nom_cle, frame, valeur, interp='BEZIER', easing='AUTO'):
    """Image clé sur le poids d'une clé de forme."""
    kb = ob.data.shape_keys.key_blocks[nom_cle]
    kb.value = valeur
    kb.keyframe_insert('value', frame=frame)
    key = ob.data.shape_keys
    sac = anim_utils.action_get_channelbag_for_slot(key.animation_data.action, key.animation_data.action_slot)
    fc = sac.fcurves.find(f'key_blocks["{nom_cle}"].value')
    for k in fc.keyframe_points:
        if abs(k.co.x - frame) < 1e-3:
            k.interpolation = interp; k.easing = easing


def gerbe(nom, coll, parent, rayon, mat_couleur, mat_blanc, n=26):
    base, explosion, fin, faces, mats = [], [], [], [], []
    for j, d in enumerate(directions(n)):
        q = Vector((0, 0, 1)).rotation_difference(d)
        k0 = len(base)
        for v in ETINCELLE_V:
            vv = q @ Vector(v)
            base.append(vv * 0.001)                                   # minuscule, au centre
            explosion.append(d * rayon + vv)
            fin.append(d * rayon * 1.25 + Vector((0, -0.035, 0)) + vv * 0.001)   # retombe vers le bas
        for f in ETINCELLE_F:
            faces.append(tuple(k0 + i for i in f)); mats.append(1 if j % 3 == 0 else 0)
    me = bpy.data.meshes.new(nom)
    me.from_pydata([tuple(v) for v in base], [], faces)
    me.materials.append(mat_couleur); me.materials.append(mat_blanc)
    for poly, m in zip(me.polygons, mats): poly.material_index = m
    ob = bpy.data.objects.new(nom, me); coll.objects.link(ob); ob.parent = parent
    ob.shape_key_add(name="Base", from_mix=False)
    for nom_cle, pts in (("Explosion", explosion), ("Fin", fin)):
        kb = ob.shape_key_add(name=nom_cle, from_mix=False)
        for i, v in enumerate(pts): kb.data[i].co = v
    return ob


FEUX = [  # (image de l'explosion, position x y z, couleur, rayon) — au-dessus et devant le 2027
    (100, (-0.22, 0.20, 0.12), '#FFD24A', 0.070),
    (116, (0.12, 0.26, 0.16), '#FF4D5E', 0.075),
    (132, (0.32, 0.18, 0.12), '#4DA8FF', 0.065),
    (150, (-0.04, 0.22, 0.20), '#5BE37D', 0.080),
    (170, (-0.33, 0.12, 0.16), '#FF6FD8', 0.070),
    (190, (0.22, 0.14, 0.18), '#FFD24A', 0.080),
    (212, (0.00, 0.16, 0.22), '#FFFFFF', 0.095),
]

def construire_feux(racine, coll):
    blanc = materiau_couleur("M_feu_blanc", hexrgb('#FFF6D8'))
    me_fusee = bpy.data.meshes.new("fusee")
    me_fusee.from_pydata(ETINCELLE_V, [], ETINCELLE_F); me_fusee.materials.append(blanc)
    groupe = vide("Feux_artifice", coll, (0, 0, 0), parent=racine)
    for n, (tb, pos, couleur, rayon) in enumerate(FEUX, start=1):
        feu = vide(f"Feu_{n}", coll, pos, parent=groupe, taille=0.02)
        # 1) la fusée monte depuis le bas de la carte
        fusee = bpy.data.objects.new(f"Fusee_{n}", me_fusee); coll.objects.link(fusee)
        fusee.parent = feu
        fusee.rotation_euler = (R(-90), 0, 0)              # pointe vers le haut de la carte
        for i in range(3): cle(fusee, 'scale', i, 0, 0.0, 'CONSTANT')
        for i in range(3): cle(fusee, 'scale', i, tb - 14, 0.8, 'CONSTANT')
        for i in range(3): cle(fusee, 'scale', i, tb, 0.0, 'CONSTANT')
        cle(fusee, 'location', 1, tb - 14, BAS_DE_LA_CARTE - pos[1], 'QUAD', 'EASE_OUT')
        cle(fusee, 'location', 1, tb, 0.0, 'CONSTANT')
        # 2) la gerbe explose puis s'éteint (clés de forme)
        g = gerbe(f"Gerbe_{n}", coll, feu, rayon, materiau_couleur(f"M_feu_{n}", hexrgb(couleur)), blanc)
        cle_forme(g, "Explosion", 0, 0.0, 'CONSTANT')
        cle_forme(g, "Explosion", tb, 0.0, 'EXPO', 'EASE_OUT')
        cle_forme(g, "Explosion", tb + 14, 1.0, 'QUAD', 'EASE_IN')
        cle_forme(g, "Explosion", tb + 34, 0.0, 'CONSTANT')
        cle_forme(g, "Explosion", FIN, 0.0, 'CONSTANT')
        cle_forme(g, "Fin", 0, 0.0, 'CONSTANT')
        cle_forme(g, "Fin", tb + 14, 0.0, 'QUAD', 'EASE_IN')
        cle_forme(g, "Fin", tb + 34, 1.0, 'CONSTANT')
        cle_forme(g, "Fin", FIN, 1.0, 'CONSTANT')
    return groupe


# ================================================================== 8. ÉTOILES QUI SCINTILLENT
def maillage_etoile():
    me = bpy.data.meshes.new("etoile")
    v = [(0, 0, 0)]
    for i in range(8):
        a = i * math.pi / 4; r = 0.016 if i % 2 == 0 else 0.004
        v.append((r * math.sin(a), r * math.cos(a), 0))      # face à la personne qui regarde
    f = [(0, 1 + i, 1 + (i + 1) % 8) for i in range(8)]
    me.from_pydata(v, [], f)
    return me


ETOILES = [(-0.36, 0.14, 0.08, 70), (-0.22, 0.24, 0.10, 98), (0.02, 0.23, 0.12, 82), (0.27, 0.24, 0.09, 106),
           (0.40, 0.16, 0.07, 90), (-0.10, 0.12, 0.14, 120), (0.15, 0.12, 0.13, 140), (0.33, 0.06, 0.11, 76)]

def construire_etoiles(racine, coll):
    me = maillage_etoile()
    me.materials.append(materiau_couleur("M_etoile", hexrgb('#FFE27A')))
    groupe = vide("Etoiles", coll, (0, 0, 0), parent=racine)
    for n, (x, y, z, f0) in enumerate(ETOILES, start=1):
        e = bpy.data.objects.new(f"Etoile_{n}", me); coll.objects.link(e)
        e.parent = groupe; e.location = (x, y, z)
        for i in range(3): cle(e, 'scale', i, 0, 0.0, 'CONSTANT')
        f = f0
        while f + 16 < 250:
            for i in range(3): cle(e, 'scale', i, f, 0.0, 'QUAD', 'EASE_OUT')
            for i in range(3): cle(e, 'scale', i, f + 6, 1.0, 'QUAD', 'EASE_IN')
            for i in range(3): cle(e, 'scale', i, f + 16, 0.0, 'CONSTANT')
            f += 52
        cle(e, 'rotation_euler', 2, 0, 0.0, 'LINEAR')                 # elle tourne sur elle-même
        cle(e, 'rotation_euler', 2, FIN, R(360), 'LINEAR')
        for i in range(3): cle(e, 'scale', i, FIN, 0.0, 'CONSTANT')
    return groupe


# ================================================================== 8 bis. NEIGE (version sans feux d'artifice)
# Les flocons tombent du haut vers le bas de la carte, à différentes distances devant elle.
# Leur période (4 s ou 6 s) divise les 12 s : la boucle est parfaite.
def maillage_flocon(nom, couleur):
    import bmesh
    me = bpy.data.meshes.new(nom)
    bm = bmesh.new()
    bmesh.ops.create_icosphere(bm, subdivisions=1, radius=1.0)    # petite boule : visible sous tous les angles
    bm.to_mesh(me); bm.free()
    me.materials.append(materiau_couleur("M_" + nom, hexrgb(couleur)))
    return me


def construire_neige(racine, coll, n=48):
    import random
    alea = random.Random(2027)                       # toujours le même tirage
    me_blanc = maillage_flocon("flocon_blanc", '#FFFFFF')
    me_bleute = maillage_flocon("flocon_bleute", '#CFE3FF')   # bleuté : se voit aussi sur le papier blanc
    groupe = vide("Neige", coll, (0, 0, 0), parent=racine)
    HAUT, BAS = 0.33, -0.30                          # du haut de la carte jusqu'en bas
    for k in range(n):
        f = bpy.data.objects.new(f"Flocon_{k + 1:02d}", me_blanc if k % 2 else me_bleute)
        coll.objects.link(f); f.parent = groupe
        x0, z0 = alea.uniform(-0.48, 0.48), alea.uniform(0.02, 0.30)
        r = alea.uniform(0.0045, 0.0075)             # rayon du flocon
        P = 144 if k % 3 else 96                     # durée d'une chute : 6 s ou 4 s
        s = alea.randrange(P) - P                    # décalage : les flocons ne tombent pas ensemble
        f.location = (x0, HAUT, z0)
        while s < FIN + P:
            cle(f, 'location', 1, s, HAUT, 'LINEAR')
            cle(f, 'location', 1, s + P - 1, BAS, 'CONSTANT')
            for i in range(3):
                cle(f, 'scale', i, s, 0.0, 'QUAD', 'EASE_OUT')
                cle(f, 'scale', i, s + 12, r, 'CONSTANT')
                cle(f, 'scale', i, s + P - 19, r, 'QUAD', 'EASE_IN')
                cle(f, 'scale', i, s + P - 1, 0.0, 'CONSTANT')
            s += P
        # petit balancement gauche-droite pendant la chute
        g, signe, amp = alea.randrange(18) - 72, 1, alea.uniform(0.008, 0.02)
        while g < FIN + 72:
            cle(f, 'location', 0, g, x0 + amp * signe)
            signe = -signe; g += 18
    return groupe


# ================================================================== 9. CARTE DE RÉFÉRENCE + CAMÉRA
def carte_reference(coll):
    me = bpy.data.meshes.new("carte_plan")
    w, h = 1.0, H_PX / W_PX
    me.from_pydata([(-w / 2, -h / 2, 0), (w / 2, -h / 2, 0), (w / 2, h / 2, 0), (-w / 2, h / 2, 0)], [], [(0, 1, 2, 3)])
    uv = me.uv_layers.new(name="UVMap")
    for i, c in enumerate([(0, 0), (1, 0), (1, 1), (0, 1)]): uv.data[i].uv = c
    me.materials.append(materiau_calque("M_carte_imprimee", os.path.abspath(CARTE_PNG)))
    ob = bpy.data.objects.new("Carte_imprimee", me)
    coll.objects.link(ob)
    ob.location.z = -0.0005
    ob.hide_render = True          # sert de repère dans Blender, n'est pas exportée
    ob.hide_select = True
    return ob


def camera_apercu(coll):
    cam = bpy.data.objects.new("Camera_telephone", bpy.data.cameras.new("Camera_telephone"))
    coll.objects.link(cam)
    cam.location = (0.0, -0.30, 1.05)               # face à la carte, un peu en dessous : comme le téléphone
    direction = Vector((0.0, 0.0, 0.06)) - cam.location
    cam.rotation_euler = direction.to_track_quat('-Z', 'Y').to_euler()
    cam.data.lens = 30
    cam.hide_render = False
    bpy.context.scene.camera = cam
    return cam


# ================================================================== 10. TOUT CONSTRUIRE
def construire():
    preparer_scene()
    c_ref = collection("Carte imprimée (repère, non exportée)")
    c_pop = collection("Pop-up")
    c_cig = collection("Cigogne")
    c_feu = collection(FEUX_COLL)
    c_nei = collection(NEIGE_COLL)
    c_eto = collection("Etoiles")
    c_cam = collection("Caméra (aperçu)")
    carte_reference(c_ref)
    racine = vide("Carte_PopUp", c_pop, (0, 0, 0), taille=0.1, forme='ARROWS')
    pieces = construire_popup(racine, c_pop)
    construire_fumee(pieces['maisons'], c_pop)
    construire_drapeau(pieces['chateau'], c_pop)
    construire_bateau(racine, c_pop)
    construire_cigogne(racine, c_cig)
    construire_feux(racine, c_feu)
    construire_neige(racine, c_nei)
    construire_etoiles(racine, c_eto)
    cam = camera_apercu(c_cam)
    c_cam.hide_render = True        # la caméra n'est pas exportée non plus
    choisir_version(sans_feux=False)
    bpy.context.scene.frame_set(150)


FEUX_COLL = "Feux d'artifice"
NEIGE_COLL = "Neige (version sans feux)"

def choisir_version(sans_feux):
    """Comme cliquer sur l'appareil photo et l'œil des 2 collections dans l'Outliner."""
    feux, neige = bpy.data.collections[FEUX_COLL], bpy.data.collections[NEIGE_COLL]
    feux.hide_render, neige.hide_render = sans_feux, not sans_feux
    lc = bpy.context.view_layer.layer_collection.children
    lc[FEUX_COLL].hide_viewport, lc[NEIGE_COLL].hide_viewport = sans_feux, not sans_feux


def exporter_les_deux(dossier_assets):
    """assets/carte.glb (feux d'artifice) et assets/carte-sans-feux.glb (neige)."""
    choisir_version(sans_feux=True)
    exporter_glb(os.path.join(dossier_assets, "carte-sans-feux.glb"))
    choisir_version(sans_feux=False)
    exporter_glb(os.path.join(dossier_assets, "carte.glb"))


def exporter_glb(chemin):
    bpy.ops.export_scene.gltf(
        filepath=chemin, export_format='GLB',
        use_renderable=True,                 # seulement ce qui est "rendu" (pas la carte repère)
        export_yup=True,                     # +Y vers le haut (convention glTF / A-Frame)
        export_animations=True,
        export_animation_mode='SCENE',       # toute la timeline = une seule animation
        export_anim_scene_split_object=False,
        export_frame_range=True,
        export_force_sampling=True,          # les interpolations Back/Bounce sont "cuites"
        export_cameras=False, export_lights=False,
        export_image_format='AUTO')


if __name__ == "__main__":
    construire()
