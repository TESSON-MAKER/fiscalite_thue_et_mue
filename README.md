# Évolution des taxes foncières à Thue et Mue

Ce dossier contient les données et les graphiques d’évolution des taxes foncières sur le territoire de l’actuelle commune de Thue et Mue (fusion en 2017 des six anciennes communes). Il est destiné à la mairie et aux habitants pour suivre l’évolution des taux et des produits perçus.

---

## Contenu des graphiques

Les graphiques sont générés dans le dossier **graphics/**.

### Graphiques principaux (taux)

- **evolution_taux_tfpb_bati.png**  
  Évolution du **taux** de la taxe foncière sur les **propriétés bâties** (TFPB), part communale.  
  Une courbe par ancienne commune jusqu’en 2016, puis un trait par commune reliant 2016 au point unique de Thue et Mue en 2017, et la courbe de Thue et Mue à partir de 2017. La **moyenne du Calvados** est en pointillés gris. La ligne verticale en pointillés marque l’année de fusion (2017).

- **evolution_taux_tfnb_non_bati.png**  
  Même chose pour le **taux** de la taxe foncière sur les **propriétés non bâties** (TFNB), part communale.  
  Même principe : anciennes communes, liaison 2016–2017, Thue et Mue à partir de 2017, moyenne du Calvados en pointillés, ligne de fusion.

- **evolution_taux_bati_et_non_bati.png**  
  Les deux taux (TFPB et TFNB) sur un seul graphique, en taux moyen pondéré du territoire avant 2017 puis en valeur Thue et Mue après 2017.

### Autres graphiques

- **evolution_montant_tfpb.png**  
  Évolution du **montant** (produit en euros) de la taxe foncière sur les propriétés bâties (part communale), avec liaison 2016–2017 entre chaque ancienne commune et Thue et Mue.

- **evolution_taux_toutes_declinaisons.png**  
  Taux par type de taxe : commune, syndicats, intercommunalité, pour le bâti (TFPB) et le non bâti (TFNB).

- **evolution_montants_declinaisons.png**  
  Montants (euros) par même déclinaison (commune, syndicats, intercommunalité, bâti / non bâti).

### Légendes et sources

- **Fusion** : ligne verticale en pointillés à l’année 2017 (création de la commune nouvelle Thue et Mue).
- **Moyenne Calvados** : taux moyen de toutes les communes du département (données REI Calvados), en pointillés gris sur les graphiques de taux bâti et non bâti.
- Les logos des sources (par ex. DGFiP, Insee) sont affichés en bas à droite lorsqu’ils sont déposés dans **graphics/logos/** (formats png, jpg ou svg, au plus deux fichiers).

---

## Données utilisées

- **data/rei_thue_et_mue.json**  
  Indicateurs REI (Recensement des éléments d’imposition) pour les six anciennes communes et pour Thue et Mue à partir de 2017 (taux, montants, bases pour les taxes foncières bâti et non bâti).

- **data/rei_calvados_e12_b12.json**  
  Taux communaux E12 (TFPB) et B12 (TFNB) pour toutes les communes du Calvados, utilisés pour calculer la **moyenne du Calvados** affichée en pointillés.

- **data/meta.json**  
  Libellés des indicateurs (codes REI) pour les titres et légendes des graphiques.

Les données REI sont produites par la DGFiP (Direction générale des Finances publiques).

---

## Comment sont faits les graphiques

Le script **graphiques_taxe_fonciere_thue_mue.py** :

1. Charge les données Thue et Mue et, si présent, le fichier Calvados.
2. Calcule pour le Calvados la moyenne des taux (E12 et B12) par année sur toutes les communes du département.
3. Trace pour chaque ancienne commune la courbe jusqu’en 2016, puis un segment de 2016 au point Thue et Mue 2017, puis la courbe Thue et Mue à partir de 2017.
4. Ajoute la courbe « Moyenne Calvados » en pointillés sur les graphiques de taux bâti et non bâti.
5. Enregistre les figures dans **graphics/** et affiche les logos placés dans **graphics/logos/** en conservant leur proportion (échelle).

Pour régénérer les graphiques après mise à jour des données ou des logos :

```bash
python graphiques_taxe_fonciere_thue_mue.py
```

(En pratique, utiliser l’environnement Python du projet, par exemple : `./.venv/bin/python graphiques_taxe_fonciere_thue_mue.py`.)

---

## Structure du code (résumé)

- **Données**  
  - `load_categories()` : charge les indicateurs REI Thue et Mue (E12, B12, E11, B11, etc.).  
  - `load_calvados_moyenne(code)` : charge le fichier Calvados et retourne, pour un code E12 ou B12, la série année → moyenne départementale.  
  - `load_meta_labels()` : récupère les libellés courts à partir de meta.json.

- **Graphiques**  
  - `plot_taux_bati()` : graphique du taux TFPB (villages, liaison 2016–2017, Thue et Mue, moyenne Calvados en pointillés).  
  - `plot_taux_non_bati()` : idem pour le taux TFNB.  
  - `plot_unifie_montant()` : montant TFPB avec liaison 2016–2017.  
  - Autres fonctions pour les graphiques « toutes déclinaisons » (taux et montants).

- **Présentation**  
  - Police : D-DIN (dossier **d-din/**).  
  - Logos : chargés depuis **graphics/logos/** (png, jpg ou svg), affichés à l’échelle en bas à droite.

---

## Dépendances

- Python 3  
- matplotlib  
- cairosvg (pour l’affichage des logos au format SVG)

Les données sont au format JSON ; aucune base de données n’est requise.
