#!/usr/bin/env python3
"""
Graphiques d'évolution des taxes foncières (TFPB, TFNB) des villages
avant la fusion en Thue et Mue (2017) et de Thue et Mue depuis 2017.
Focus : taux bâti et non bâti. Liaison 2016 → 2017. Logos sources.
Données : data/rei_thue_et_mue.json, data/meta.json — police : d-din/D-DIN.otf
"""

import io
import json
from pathlib import Path

import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import matplotlib.image as mimg

BASE = Path(__file__).resolve().parent
DATA_JSON = BASE / "data" / "rei_thue_et_mue.json"
DATA_CALVADOS = BASE / "data" / "rei_calvados_e12_b12.json"
META_JSON = BASE / "data" / "meta.json"
FONT_PATH = BASE / "d-din" / "D-DIN.otf"
GRAPHICS_DIR = BASE / "graphics"
LOGOS_DIR = GRAPHICS_DIR / "logos"  # logos des sources (optionnel)
ANNE_FUSION = 2017
NOM_APRES = "THUE ET MUE"
# Texte source si pas de logo
SOURCE_TEXTE = "Source : DGFiP - REI"

# Déclinaisons
CODES_MONTANTS = ["E13", "E23", "E33", "B13", "B23", "B33"]
CODES_TAUX = ["E12", "E22", "E32", "B12", "B22", "B32"]
CODES_BASES = ["E11", "E21", "E31", "B11", "B21", "B31"]
BASE_FOR_TAUX = {"E12": "E11", "E22": "E21", "E32": "E31", "B12": "B11", "B22": "B21", "B32": "B31"}


def load_categories(codes):
    with open(DATA_JSON, encoding="utf-8") as f:
        data = json.load(f)
    cat = data["category"]
    out = {}
    for code in codes:
        if code not in cat:
            continue
        out[code] = {}
        for an_str, bloc in cat[code]["year"].items():
            an = int(an_str)
            out[code][an] = {c["name"]: c["value"] for c in bloc["city"]}
    return out


def load_calvados_moyenne(code):
    """Charge le fichier Calvados et retourne pour un code (E12 ou B12) la série année -> moyenne départementale."""
    if not DATA_CALVADOS.exists():
        return {}
    with open(DATA_CALVADOS, encoding="utf-8") as f:
        data = json.load(f)
    cat = data.get("category", {})
    if code not in cat:
        return {}
    out = {}
    for an_str, bloc in cat[code]["year"].items():
        an = int(an_str)
        vals = [c["value"] for c in bloc["city"] if c.get("value") is not None]
        out[an] = sum(vals) / len(vals) if vals else None
    return out


def load_meta_labels(codes):
    with open(META_JSON, encoding="utf-8") as f:
        meta = json.load(f)
    labels = {}
    for code in codes:
        if code not in meta:
            labels[code] = code
            continue
        lab = meta[code].get("label", code)
        if "FB - COMMUNE" in lab:
            labels[code] = "TFPB commune"
        elif "FB - SYNDICATS" in lab:
            labels[code] = "TFPB syndicats"
        elif "FB - GFP" in lab:
            labels[code] = "TFPB interco"
        elif "FNB - COMMUNE" in lab:
            labels[code] = "TFNB commune"
        elif "FNB - SYNDICATS" in lab:
            labels[code] = "TFNB syndicats"
        elif "FNB - GFP" in lab:
            labels[code] = "TFNB interco"
        else:
            labels[code] = lab[:40] if len(lab) > 40 else lab
    return labels


def get_villages_and_years(series_by_year):
    annees = sorted(series_by_year.keys())
    villages = set()
    for an in annees:
        if an < ANNE_FUSION:
            villages.update(series_by_year[an].keys())
    return sorted(villages), [a for a in annees if a < ANNE_FUSION], [a for a in annees if a >= ANNE_FUSION]


def apply_font(ax, font_prop):
    for label in ax.get_xticklabels() + ax.get_yticklabels():
        label.set_fontproperties(font_prop)


def setup_font():
    if not FONT_PATH.exists():
        raise FileNotFoundError(f"Police introuvable : {FONT_PATH}")
    fm.fontManager.addfont(str(FONT_PATH))
    return fm.FontProperties(fname=str(FONT_PATH))


def _liste_logos(max_n=2):
    """Retourne jusqu'à max_n chemins de logos (png, jpg, svg) triés par nom."""
    if not LOGOS_DIR.exists():
        return []
    paths = []
    for ext in ("*.png", "*.jpg", "*.jpeg", "*.svg"):
        paths.extend(LOGOS_DIR.glob(ext))
    exts = (".png", ".jpg", ".jpeg", ".svg")
    paths = sorted(set(p for p in paths if p.suffix.lower() in exts))[:max_n]
    return paths


def _load_logo_as_array(path):
    """Charge une image (png/jpg/svg) en tableau numpy pour imshow. SVG converti via cairosvg."""
    path = Path(path)
    suf = path.suffix.lower()
    if suf in (".png", ".jpg", ".jpeg"):
        return mimg.imread(str(path))
    if suf == ".svg":
        try:
            import cairosvg
            buf = io.BytesIO()
            cairosvg.svg2png(url=str(path), write_to=buf)
            buf.seek(0)
            return mimg.imread(buf)
        except Exception:
            return None
    return None


# Marge basse réservée aux logos (coord. figure)
LOGO_BOTTOM_MARGIN = 0.14


def add_source_logo(fig, font_prop):
    """Ajoute jusqu'à 2 logos en bas à droite, proportion conservée (non déformés)."""
    logos = _liste_logos(2)
    if not logos:
        fig.text(0.99, 0.02, SOURCE_TEXTE, fontproperties=font_prop, fontsize=8, ha="right", va="bottom")
        return
    fig_w, fig_h = fig.get_size_inches()
    h_ax = 0.10
    gap = 0.02
    boxes = []
    for path in logos:
        img = _load_logo_as_array(path)
        if img is None:
            continue
        h_img, w_img = img.shape[:2]
        aspect = w_img / h_img if h_img else 1.0
        w_ax = h_ax * aspect * fig_h / fig_w
        w_ax = min(w_ax, 0.20)
        boxes.append((img, w_ax, h_ax))
    total_w = sum(b[1] for b in boxes) + gap * (len(boxes) - 1) if boxes else 0
    left = 1.0 - total_w - 0.02
    bottom = 0.02
    for img, w_ax, h_ax in boxes:
        ax_logo = fig.add_axes([left, bottom, w_ax, h_ax], anchor="SW")
        ax_logo.imshow(img, aspect="auto", interpolation="bilinear")
        ax_logo.axis("off")
        left += w_ax + gap


def valeur_agregee_2016(series_by_year, villages, an=2016):
    """Valeur agrégée (taux moyen pondéré) en 2016 pour le territoire des 6 villages. Pour taux il faut base."""
    if an not in series_by_year:
        return None
    vals = [series_by_year[an].get(v) for v in villages]
    vals = [x for x in vals if x is not None]
    if not vals:
        return None
    return sum(vals) / len(vals)


def valeur_agregee_2016_ponderee(d_taux, d_base, villages, an=2016):
    """Taux moyen pondéré par la base en 2016."""
    if an not in d_taux or not d_base:
        return valeur_agregee_2016(d_taux, villages, an)
    num = sum((d_base.get(an, {}).get(v, 0) or 0) * (d_taux.get(an, {}).get(v, 0) or 0) for v in villages)
    den = sum(d_base.get(an, {}).get(v, 0) or 0 for v in villages)
    return num / den if den else None


# --- Taux bâti (E12) : un graphique, liaison 2016 → 2017 ---
def plot_taux_bati(series_e12, categories_data, font_prop, calvados_moyenne=None):
    """Taux TFPB (bâti). Villages jusqu'en 2016, un segment par commune 2016 → point Thue et Mue 2017."""
    villages, annees_avant, annees_apres = get_villages_and_years(series_e12)
    colors = plt.rcParams["axes.prop_cycle"].by_key().get("color", ["C0", "C1", "C2", "C3", "C4", "C5"])

    fig, ax = plt.subplots(figsize=(14, 6))

    for i, v in enumerate(villages):
        y_avant = [series_e12[an].get(v) for an in annees_avant]
        ax.plot(annees_avant, y_avant, label=v, marker="o", markersize=3, color=colors[i % len(colors)])

    val_2017 = series_e12.get(2017, {}).get(NOM_APRES) if annees_apres else None
    if 2016 in series_e12 and val_2017 is not None:
        for i, v in enumerate(villages):
            val_2016 = series_e12[2016].get(v)
            if val_2016 is not None:
                c = colors[i % len(colors)]
                ax.plot([2016, 2017], [val_2016, val_2017], color=c, linestyle="-", alpha=0.8, lw=1.5, zorder=4)
    if annees_apres:
        y_apres = [series_e12[an].get(NOM_APRES) for an in annees_apres]
        ax.plot(annees_apres, y_apres, color="C0", label=NOM_APRES, marker="o", markersize=4, lw=2)

    if calvados_moyenne:
        annees_toutes = sorted(series_e12.keys())
        y_calv = [calvados_moyenne.get(an) for an in annees_toutes]
        ax.plot(annees_toutes, y_calv, linestyle="--", color="black", lw=0.8, label="Moyenne Calvados", zorder=3)

    ax.axvline(x=ANNE_FUSION, color="gray", linestyle="--", linewidth=1.5, label="Fusion")
    ax.set_xlabel("Année", fontproperties=font_prop)
    ax.set_ylabel("Taux net (%)", fontproperties=font_prop)
    ax.set_title("Taux de la taxe foncière sur les propriétés bâties (TFPB) — commune", fontproperties=font_prop)
    ax.legend(prop=font_prop, fontsize=8)
    ax.grid(True, alpha=0.3)
    apply_font(ax, font_prop)
    plt.tight_layout(rect=[0, LOGO_BOTTOM_MARGIN, 1, 1])
    add_source_logo(fig, font_prop)
    return fig


# --- Taux non bâti (B12) ---
def plot_taux_non_bati(series_b12, categories_data, font_prop, calvados_moyenne=None):
    """Taux TFNB (non bâti). Un segment par commune 2016 → point Thue et Mue 2017."""
    villages, annees_avant, annees_apres = get_villages_and_years(series_b12)
    colors = plt.rcParams["axes.prop_cycle"].by_key().get("color", ["C0", "C1", "C2", "C3", "C4", "C5"])

    fig, ax = plt.subplots(figsize=(14, 6))

    for i, v in enumerate(villages):
        y_avant = [series_b12[an].get(v) for an in annees_avant]
        ax.plot(annees_avant, y_avant, label=v, marker="o", markersize=3, color=colors[i % len(colors)])

    val_2017 = series_b12.get(2017, {}).get(NOM_APRES) if annees_apres else None
    if 2016 in series_b12 and val_2017 is not None:
        for i, v in enumerate(villages):
            val_2016 = series_b12[2016].get(v)
            if val_2016 is not None:
                c = colors[i % len(colors)]
                ax.plot([2016, 2017], [val_2016, val_2017], color=c, linestyle="-", alpha=0.8, lw=1.5, zorder=4)
    if annees_apres:
        y_apres = [series_b12[an].get(NOM_APRES) for an in annees_apres]
        ax.plot(annees_apres, y_apres, color="C0", label=NOM_APRES, marker="o", markersize=4, lw=2)

    if calvados_moyenne:
        annees_toutes = sorted(series_b12.keys())
        y_calv = [calvados_moyenne.get(an) for an in annees_toutes]
        ax.plot(annees_toutes, y_calv, linestyle="--", color="black", lw=0.8, label="Moyenne Calvados", zorder=3)

    ax.axvline(x=ANNE_FUSION, color="gray", linestyle="--", linewidth=1.5, label="Fusion")
    ax.set_xlabel("Année", fontproperties=font_prop)
    ax.set_ylabel("Taux net (%)", fontproperties=font_prop)
    ax.set_title("Taux de la taxe foncière sur les propriétés non bâties (TFNB) — commune", fontproperties=font_prop)
    ax.legend(prop=font_prop, fontsize=8)
    ax.grid(True, alpha=0.3)
    apply_font(ax, font_prop)
    plt.tight_layout(rect=[0, LOGO_BOTTOM_MARGIN, 1, 1])
    add_source_logo(fig, font_prop)
    return fig


# --- Graphique unifié montant (avec liaison 2016→2017) ---
def plot_unifie_montant(series_by_year, font_prop):
    villages, annees_avant, annees_apres = get_villages_and_years(series_by_year)
    colors = plt.rcParams["axes.prop_cycle"].by_key().get("color", ["C0", "C1", "C2", "C3", "C4", "C5"])

    fig, ax = plt.subplots(figsize=(14, 6))

    for i, v in enumerate(villages):
        y_avant = [series_by_year[an].get(v) for an in annees_avant]
        ax.plot(annees_avant, y_avant, label=v, marker="o", markersize=3, color=colors[i % len(colors)])

    val_2017 = series_by_year.get(2017, {}).get(NOM_APRES) if annees_apres else None
    if 2016 in series_by_year and val_2017 is not None:
        for i, v in enumerate(villages):
            val_2016 = series_by_year[2016].get(v)
            if val_2016 is not None:
                c = colors[i % len(colors)]
                ax.plot([2016, 2017], [val_2016, val_2017], color=c, linestyle="-", alpha=0.8, lw=1.5, zorder=4)
    if annees_apres:
        y_apres = [series_by_year[an].get(NOM_APRES) for an in annees_apres]
        ax.plot(annees_apres, y_apres, color="C0", label=NOM_APRES, marker="o", markersize=4, lw=2)

    ax.axvline(x=ANNE_FUSION, color="gray", linestyle="--", linewidth=1.5, label="Fusion")
    ax.set_xlabel("Année", fontproperties=font_prop)
    ax.set_ylabel("Montant réel (€)", fontproperties=font_prop)
    ax.set_title("Produit de la taxe foncière (propriétés bâties, commune)", fontproperties=font_prop)
    ax.legend(prop=font_prop, fontsize=8)
    ax.grid(True, alpha=0.3)
    apply_font(ax, font_prop)
    plt.tight_layout(rect=[0, LOGO_BOTTOM_MARGIN, 1, 1])
    add_source_logo(fig, font_prop)
    return fig


# --- Détaillé : taux bâti + non bâti (E12, B12) avec liaison ---
def plot_detaille_taux_bati_non_bati(categories_data, meta_labels, font_prop):
    """Deux séries : E12 (TFPB) et B12 (TFNB). Territoire agrégé avant 2017, liaison 2016→2017, Thue et Mue après."""
    codes = [c for c in ["E12", "B12"] if c in categories_data]
    if not codes:
        return None
    base_for = {"E12": "E11", "B12": "B11"}
    annees_avant = sorted(set().union(*(set(y for y in categories_data[c] if y < ANNE_FUSION) for c in codes)))
    annees_apres = sorted(set().union(*(set(y for y in categories_data[c] if y >= ANNE_FUSION) for c in codes)))
    villages = set()
    for code in codes:
        for an in categories_data.get(code, {}):
            if an < ANNE_FUSION:
                villages.update(categories_data[code][an].keys())
    villages = sorted(villages)

    fig, ax = plt.subplots(figsize=(14, 6))
    for code in codes:
        d_taux = categories_data.get(code, {})
        d_base = categories_data.get(base_for.get(code), {})
        y_avant = []
        for an in annees_avant:
            num = sum((d_base.get(an, {}).get(v, 0) or 0) * (d_taux.get(an, {}).get(v, 0) or 0) for v in villages)
            den = sum(d_base.get(an, {}).get(v, 0) or 0 for v in villages)
            y_avant.append(num / den if den else None)
        y_apres = [d_taux.get(an, {}).get(NOM_APRES) for an in annees_apres]
        label = meta_labels.get(code, code)
        ax.plot(annees_avant + annees_apres, y_avant + y_apres, marker="o", markersize=3, label=label)

    ax.axvline(x=ANNE_FUSION, color="gray", linestyle="--", linewidth=1.5, label="Fusion")
    ax.set_xlabel("Année", fontproperties=font_prop)
    ax.set_ylabel("Taux net (%)", fontproperties=font_prop)
    ax.set_title("Taux des taxes foncières — bâti et non bâti (territoire agrégé puis Thue et Mue)", fontproperties=font_prop)
    ax.legend(prop=font_prop, fontsize=8)
    ax.grid(True, alpha=0.3)
    apply_font(ax, font_prop)
    plt.tight_layout(rect=[0, LOGO_BOTTOM_MARGIN, 1, 1])
    add_source_logo(fig, font_prop)
    return fig


# --- Détaillé tous taux (6 déclinaisons) ---
def plot_detaille_taux_toutes(categories_data, meta_labels, font_prop):
    codes_taux = [c for c in CODES_TAUX if c in categories_data]
    base_for = BASE_FOR_TAUX
    annees_avant = sorted(set().union(*(set(y for y in categories_data[c] if y < ANNE_FUSION) for c in codes_taux)))
    annees_apres = sorted(set().union(*(set(y for y in categories_data[c] if y >= ANNE_FUSION) for c in codes_taux)))
    villages = set()
    for code in codes_taux:
        for an in categories_data.get(code, {}):
            if an < ANNE_FUSION:
                villages.update(categories_data[code][an].keys())
    villages = sorted(villages)

    fig, ax = plt.subplots(figsize=(14, 7))
    for code in codes_taux:
        d_taux = categories_data.get(code, {})
        base_code = base_for.get(code)
        d_base = categories_data.get(base_code, {}) if base_code else {}
        y_avant = []
        for an in annees_avant:
            if base_code and d_base:
                num = sum((d_base.get(an, {}).get(v, 0) or 0) * (d_taux.get(an, {}).get(v, 0) or 0) for v in villages)
                den = sum(d_base.get(an, {}).get(v, 0) or 0 for v in villages)
                y_avant.append(num / den if den else None)
            else:
                vals = [d_taux.get(an, {}).get(v) for v in villages]
                y_avant.append(sum(v for v in vals if v is not None) / len(vals) if vals else None)
        y_apres = [d_taux.get(an, {}).get(NOM_APRES) for an in annees_apres]
        label = meta_labels.get(code, code)
        ax.plot(annees_avant + annees_apres, y_avant + y_apres, marker="o", markersize=2.5, label=label)

    ax.axvline(x=ANNE_FUSION, color="gray", linestyle="--", linewidth=1.5, label="Fusion")
    ax.set_xlabel("Année", fontproperties=font_prop)
    ax.set_ylabel("Taux net (%)", fontproperties=font_prop)
    ax.set_title("Taux des taxes foncières par déclinaison", fontproperties=font_prop)
    ax.legend(prop=font_prop, fontsize=8)
    ax.grid(True, alpha=0.3)
    apply_font(ax, font_prop)
    plt.tight_layout(rect=[0, LOGO_BOTTOM_MARGIN, 1, 1])
    add_source_logo(fig, font_prop)
    return fig


def plot_detaille_montants(categories_data, meta_labels, font_prop):
    codes = [c for c in CODES_MONTANTS if c in categories_data]
    if not codes:
        return None
    annees_avant = sorted(set().union(*(set(y for y in d if y < ANNE_FUSION) for d in categories_data.values())))
    annees_apres = sorted(set().union(*(set(y for y in d if y >= ANNE_FUSION) for d in categories_data.values())))
    villages = set()
    for code in codes:
        for an in categories_data[code]:
            if an < ANNE_FUSION:
                villages.update(categories_data[code][an].keys())
    villages = sorted(villages)

    fig, ax = plt.subplots(figsize=(14, 7))
    for code in codes:
        d = categories_data[code]
        y_avant = [sum(d[an].get(v, 0) or 0 for v in villages) for an in annees_avant]
        y_apres = [d[an].get(NOM_APRES) for an in annees_apres]
        label = meta_labels.get(code, code)
        ax.plot(annees_avant + annees_apres, y_avant + y_apres, marker="o", markersize=2.5, label=label)

    ax.axvline(x=ANNE_FUSION, color="gray", linestyle="--", linewidth=1.5, label="Fusion")
    ax.set_xlabel("Année", fontproperties=font_prop)
    ax.set_ylabel("Montant réel (€)", fontproperties=font_prop)
    ax.set_title("Produits des taxes foncières par déclinaison", fontproperties=font_prop)
    ax.legend(prop=font_prop, fontsize=8)
    ax.grid(True, alpha=0.3)
    apply_font(ax, font_prop)
    plt.tight_layout(rect=[0, LOGO_BOTTOM_MARGIN, 1, 1])
    add_source_logo(fig, font_prop)
    return fig


def main():
    GRAPHICS_DIR.mkdir(parents=True, exist_ok=True)
    font_prop = setup_font()

    all_codes = list(set(CODES_MONTANTS + CODES_TAUX + CODES_BASES))
    categories_data = load_categories(all_codes)
    meta_labels = load_meta_labels(all_codes)

    calvados_e12 = load_calvados_moyenne("E12") if DATA_CALVADOS.exists() else {}
    calvados_b12 = load_calvados_moyenne("B12") if DATA_CALVADOS.exists() else {}

    # Priorité : taux bâti et taux non bâti (avec liaison 2016 → 2017, moyenne Calvados en pointillés)
    if "E12" in categories_data:
        fig = plot_taux_bati(categories_data["E12"], categories_data, font_prop, calvados_moyenne=calvados_e12)
        fig.savefig(GRAPHICS_DIR / "evolution_taux_tfpb_bati.png", dpi=150, bbox_inches="tight")
        plt.close(fig)
    if "B12" in categories_data:
        fig = plot_taux_non_bati(categories_data["B12"], categories_data, font_prop, calvados_moyenne=calvados_b12)
        fig.savefig(GRAPHICS_DIR / "evolution_taux_tfnb_non_bati.png", dpi=150, bbox_inches="tight")
        plt.close(fig)

    # Taux bâti + non bâti sur un même graphique
    fig = plot_detaille_taux_bati_non_bati(categories_data, meta_labels, font_prop)
    if fig:
        fig.savefig(GRAPHICS_DIR / "evolution_taux_bati_et_non_bati.png", dpi=150, bbox_inches="tight")
        plt.close(fig)

    # Montant unifié (avec liaison 2016→2017)
    if "E13" in categories_data:
        fig = plot_unifie_montant(categories_data["E13"], font_prop)
        fig.savefig(GRAPHICS_DIR / "evolution_montant_tfpb.png", dpi=150, bbox_inches="tight")
        plt.close(fig)

    # Détaillé : tous les taux
    fig = plot_detaille_taux_toutes(categories_data, meta_labels, font_prop)
    if fig:
        fig.savefig(GRAPHICS_DIR / "evolution_taux_toutes_declinaisons.png", dpi=150, bbox_inches="tight")
        plt.close(fig)

    # Détaillé : montants
    fig = plot_detaille_montants(categories_data, meta_labels, font_prop)
    if fig:
        fig.savefig(GRAPHICS_DIR / "evolution_montants_declinaisons.png", dpi=150, bbox_inches="tight")
        plt.close(fig)

    print("Graphiques générés dans graphics/ :")
    print("  - evolution_taux_tfpb_bati.png           (taux bâti, liaison 2016→2017)")
    print("  - evolution_taux_tfnb_non_bati.png       (taux non bâti, liaison 2016→2017)")
    print("  - evolution_taux_bati_et_non_bati.png   (taux bâti + non bâti)")
    print("  - evolution_montant_tfpb.png")
    print("  - evolution_taux_toutes_declinaisons.png")
    print("  - evolution_montants_declinaisons.png")
    print("Logos sources : graphics/logos/ (png, jpg ou svg) — 2 logos affichés si présents.")


if __name__ == "__main__":
    main()
