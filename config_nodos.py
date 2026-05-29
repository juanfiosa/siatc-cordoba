# -*- coding: utf-8 -*-
"""
Configuración de nodos jurisdiccionales — MPF Córdoba
Ley 8.000 (Mapa Judicial de la Provincia de Córdoba)

Hay 10 circunscripciones judiciales. Cada una es un "nodo" con su propia
estructura de oficinas, tipo de policía y flujos de comunicación.

TIPOS DE NODO:
  "capital"  → Córdoba Capital: Policía Judicial MPF, Unidades Contravencionales especializadas
  "interior" → Interior: Policía Provincial (externa al MPF), Fiscalías de Instrucción
               que manejan tanto causas penales como contravencionales
"""
from __future__ import annotations

# ── Constantes de tipo de policía ─────────────────────────────────────────────
POLICIA_JUDICIAL_MPF  = "judicial_mpf"    # Policía Judicial, órgano del MPF
POLICIA_PROVINCIAL    = "provincial"      # Policía de la Provincia, externa al MPF

# ── Módulos disponibles ───────────────────────────────────────────────────────
MODULO_CONTRAVENCIONAL = "contravencional"
MODULO_PENAL           = "penal"

# ── Definición de nodos ───────────────────────────────────────────────────────
NODOS: dict[str, dict] = {

    # ── 1ª Circunscripción — Córdoba Capital ──────────────────────────────────
    # Estructura especial: Policía Judicial MPF + Unidades Contravencionales
    "cba_norte": {
        "nombre": "Unidad Contravencional Norte",
        "circunscripcion": "1ª — Córdoba Capital",
        "ciudad": "Córdoba",
        "tipo": "capital",
        "tipo_policia": POLICIA_JUDICIAL_MPF,
        "modulos": [MODULO_CONTRAVENCIONAL],
        "oficinas": [
            {"key": "policia_judicial",  "label": "Policía Judicial (MPF)",         "icon": "🔎", "activa": True},
            {"key": "fiscal_cba_norte",  "label": "Unidad Contravencional Norte",   "icon": "⚖️", "activa": True},
            {"key": "camara_cba",        "label": "Fiscalía de Cámara",             "icon": "🏛️", "activa": True},
            {"key": "mesa_cba",          "label": "Mesa de Entradas",               "icon": "📋", "activa": True},
            {"key": "mediacion_cba",     "label": "Centro Judicial de Mediación",   "icon": "🤝", "activa": False},  # fantasma
            {"key": "juzgado_cba_cont",  "label": "Juzgado Contravencional",        "icon": "⚖️", "activa": False},  # fantasma
        ],
        "flujos": {
            "policia_judicial":  ["fiscal_cba_norte", "mesa_cba"],
            "fiscal_cba_norte":  ["policia_judicial", "camara_cba", "mesa_cba", "mediacion_cba", "juzgado_cba_cont"],
            "camara_cba":        ["fiscal_cba_norte"],
            "mesa_cba":          ["fiscal_cba_norte", "policia_judicial"],
            "mediacion_cba":     ["fiscal_cba_norte"],
            "juzgado_cba_cont":  ["fiscal_cba_norte", "camara_cba"],
        },
    },

    "cba_sur": {
        "nombre": "Unidad Contravencional Sur",
        "circunscripcion": "1ª — Córdoba Capital",
        "ciudad": "Córdoba",
        "tipo": "capital",
        "tipo_policia": POLICIA_JUDICIAL_MPF,
        "modulos": [MODULO_CONTRAVENCIONAL],
        "oficinas": [
            {"key": "policia_judicial",  "label": "Policía Judicial (MPF)",         "icon": "🔎", "activa": True},
            {"key": "fiscal_cba_sur",    "label": "Unidad Contravencional Sur",     "icon": "⚖️", "activa": True},
            {"key": "camara_cba",        "label": "Fiscalía de Cámara",             "icon": "🏛️", "activa": True},
            {"key": "mesa_cba",          "label": "Mesa de Entradas",               "icon": "📋", "activa": True},
            {"key": "mediacion_cba",     "label": "Centro Judicial de Mediación",   "icon": "🤝", "activa": False},
            {"key": "juzgado_cba_cont",  "label": "Juzgado Contravencional",        "icon": "⚖️", "activa": False},
        ],
        "flujos": {
            "policia_judicial": ["fiscal_cba_sur", "mesa_cba"],
            "fiscal_cba_sur":   ["policia_judicial", "camara_cba", "mesa_cba", "mediacion_cba", "juzgado_cba_cont"],
            "camara_cba":       ["fiscal_cba_sur"],
            "mesa_cba":         ["fiscal_cba_sur", "policia_judicial"],
            "mediacion_cba":    ["fiscal_cba_sur"],
            "juzgado_cba_cont": ["fiscal_cba_sur", "camara_cba"],
        },
    },

    "cba_genero": {
        "nombre": "Unidad Contravencional de Género",
        "circunscripcion": "1ª — Córdoba Capital",
        "ciudad": "Córdoba",
        "tipo": "capital",
        "tipo_policia": POLICIA_JUDICIAL_MPF,
        "modulos": [MODULO_CONTRAVENCIONAL],
        "oficinas": [
            {"key": "policia_judicial",  "label": "Policía Judicial (MPF)",         "icon": "🔎", "activa": True},
            {"key": "fiscal_cba_genero", "label": "Unidad Contravencional Género",  "icon": "⚖️", "activa": True},
            {"key": "camara_cba",        "label": "Fiscalía de Cámara",             "icon": "🏛️", "activa": True},
            {"key": "mesa_cba",          "label": "Mesa de Entradas",               "icon": "📋", "activa": True},
            {"key": "juzgado_cba_cont",  "label": "Juzgado Contravencional",        "icon": "⚖️", "activa": False},
        ],
        "flujos": {
            "policia_judicial":  ["fiscal_cba_genero", "mesa_cba"],
            "fiscal_cba_genero": ["policia_judicial", "camara_cba", "mesa_cba", "juzgado_cba_cont"],
            "camara_cba":        ["fiscal_cba_genero"],
            "mesa_cba":          ["fiscal_cba_genero", "policia_judicial"],
            "juzgado_cba_cont":  ["fiscal_cba_genero", "camara_cba"],
        },
    },

    # ── 2ª Circunscripción — Río Cuarto ──────────────────────────────────────
    # Fuente: MPF Córdoba — fiscalias-de-instruccion-interior / fiscalias-camara-interior
    # 2 Fiscalías Instrucción
    # 2 Fiscalías de Cámara
    "rio_cuarto": {
        "nombre": "MPF Río Cuarto",
        "circunscripcion": "2ª — Río Cuarto",
        "ciudad": "Río Cuarto",
        "tipo": "interior",
        "tipo_policia": POLICIA_PROVINCIAL,
        "modulos": [MODULO_PENAL, MODULO_CONTRAVENCIONAL],
        "oficinas": [
            {"key": "policia_rc",        "label": "Policía de la Provincia — Río Cuarto",         "icon": "🚓", "activa": True},
            {"key": "fiscal_inst_rc_1",  "label": "Fiscalía de Instrucción N°1",  "icon": "⚖️", "activa": True},
            {"key": "fiscal_inst_rc_2",  "label": "Fiscalía de Instrucción N°2",  "icon": "⚖️", "activa": True},
            {"key": "camara_rc_1",       "label": "Fiscalía de Cámara N°1",       "icon": "🏛️", "activa": True},
            {"key": "camara_rc_2",       "label": "Fiscalía de Cámara N°2",       "icon": "🏛️", "activa": True},
            {"key": "mesa_rc",           "label": "Mesa de Entradas — Río Cuarto",               "icon": "📋", "activa": True},
            {"key": "juzgado_control_rc","label": "Juzgado de Control — Río Cuarto",             "icon": "⚖️", "activa": False},
        ],
        "flujos": {
            "policia_rc":        ["fiscal_inst_rc_1", "fiscal_inst_rc_2", "mesa_rc"],
            "fiscal_inst_rc_1":  ["policia_rc", "camara_rc_1", "camara_rc_2", "mesa_rc", "juzgado_control_rc", "fiscal_inst_rc_2"],
            "fiscal_inst_rc_2":  ["policia_rc", "camara_rc_1", "camara_rc_2", "mesa_rc", "juzgado_control_rc", "fiscal_inst_rc_1"],
            "camara_rc_1":       ["fiscal_inst_rc_1", "fiscal_inst_rc_2"],
            "camara_rc_2":       ["fiscal_inst_rc_1", "fiscal_inst_rc_2"],
            "mesa_rc":           ["fiscal_inst_rc_1", "fiscal_inst_rc_2", "policia_rc"],
            "juzgado_control_rc":["fiscal_inst_rc_1", "fiscal_inst_rc_2", "camara_rc_1", "camara_rc_2"],
        },
    },

    # ── 3ª Circunscripción — Bell Ville ──────────────────────────────────────
    # 2 Fiscalías Instrucción
    # 1 Fiscalía de Cámara
    "bell_ville": {
        "nombre": "MPF Bell Ville",
        "circunscripcion": "3ª — Bell Ville",
        "ciudad": "Bell Ville",
        "tipo": "interior",
        "tipo_policia": POLICIA_PROVINCIAL,
        "modulos": [MODULO_PENAL, MODULO_CONTRAVENCIONAL],
        "oficinas": [
            {"key": "policia_bv",        "label": "Policía de la Provincia — Bell Ville",          "icon": "🚓", "activa": True},
            {"key": "fiscal_inst_bv_1",  "label": "Fiscalía de Instrucción N°1",    "icon": "⚖️", "activa": True},
            {"key": "fiscal_inst_bv_2",  "label": "Fiscalía de Instrucción N°2",     "icon": "⚖️", "activa": True},
            {"key": "camara_bv",         "label": "Fiscalía de Cámara",    "icon": "🏛️", "activa": True},
            {"key": "mesa_bv",           "label": "Mesa de Entradas — Bell Ville",                 "icon": "📋", "activa": True},
            {"key": "juzgado_bv",        "label": "Juzgado de Control — Bell Ville",              "icon": "⚖️", "activa": False},
        ],
        "flujos": {
            "policia_bv":       ["fiscal_inst_bv_1", "fiscal_inst_bv_2", "mesa_bv"],
            "fiscal_inst_bv_1": ["policia_bv", "camara_bv", "mesa_bv", "juzgado_bv", "fiscal_inst_bv_2"],
            "fiscal_inst_bv_2": ["policia_bv", "camara_bv", "mesa_bv", "juzgado_bv", "fiscal_inst_bv_1"],
            "camara_bv":        ["fiscal_inst_bv_1", "fiscal_inst_bv_2"],
            "mesa_bv":          ["fiscal_inst_bv_1", "fiscal_inst_bv_2", "policia_bv"],
            "juzgado_bv":       ["fiscal_inst_bv_1", "fiscal_inst_bv_2", "camara_bv"],
        },
    },

    # ── 4ª Circunscripción — Villa María ─────────────────────────────────────
    # 3 Fiscalías Instrucción
    # 1 Fiscalía de Cámara
    "villa_maria": {
        "nombre": "MPF Villa María",
        "circunscripcion": "4ª — Villa María",
        "ciudad": "Villa María",
        "tipo": "interior",
        "tipo_policia": POLICIA_PROVINCIAL,
        "modulos": [MODULO_PENAL, MODULO_CONTRAVENCIONAL],
        "oficinas": [
            {"key": "policia_vm",        "label": "Policía de la Provincia — Villa María",         "icon": "🚓", "activa": True},
            {"key": "fiscal_inst_vm_1",  "label": "Fiscalía de Instrucción N°1", "icon": "⚖️", "activa": True},
            {"key": "fiscal_inst_vm_2",  "label": "Fiscalía de Instrucción N°2",  "icon": "⚖️", "activa": True},
            {"key": "fiscal_inst_vm_3",  "label": "Fiscalía de Instrucción N°3",      "icon": "⚖️", "activa": True},
            {"key": "camara_vm",         "label": "Fiscalía de Cámara",             "icon": "🏛️", "activa": True},
            {"key": "mesa_vm",           "label": "Mesa de Entradas — Villa María",               "icon": "📋", "activa": True},
            {"key": "juzgado_vm",        "label": "Juzgado de Control — Villa María",             "icon": "⚖️", "activa": False},
        ],
        "flujos": {
            "policia_vm":       ["fiscal_inst_vm_1", "fiscal_inst_vm_2", "fiscal_inst_vm_3", "mesa_vm"],
            "fiscal_inst_vm_1": ["policia_vm", "camara_vm", "mesa_vm", "juzgado_vm", "fiscal_inst_vm_2", "fiscal_inst_vm_3"],
            "fiscal_inst_vm_2": ["policia_vm", "camara_vm", "mesa_vm", "juzgado_vm", "fiscal_inst_vm_1", "fiscal_inst_vm_3"],
            "fiscal_inst_vm_3": ["policia_vm", "camara_vm", "mesa_vm", "juzgado_vm", "fiscal_inst_vm_1", "fiscal_inst_vm_2"],
            "camara_vm":        ["fiscal_inst_vm_1", "fiscal_inst_vm_2", "fiscal_inst_vm_3"],
            "mesa_vm":          ["fiscal_inst_vm_1", "fiscal_inst_vm_2", "fiscal_inst_vm_3", "policia_vm"],
            "juzgado_vm":       ["fiscal_inst_vm_1", "fiscal_inst_vm_2", "fiscal_inst_vm_3", "camara_vm"],
        },
    },

    # ── 5ª Circunscripción — San Francisco ────────────────────────────────────
    # 1 Fiscalía Instrucción + 1 de Cámara
    "san_francisco": {
        "nombre": "MPF San Francisco",
        "circunscripcion": "5ª — San Francisco",
        "ciudad": "San Francisco",
        "tipo": "interior",
        "tipo_policia": POLICIA_PROVINCIAL,
        "modulos": [MODULO_PENAL, MODULO_CONTRAVENCIONAL],
        "oficinas": [
            {"key": "policia_sf",       "label": "Policía de la Provincia — San Francisco",       "icon": "🚓", "activa": True},
            {"key": "fiscal_inst_sf",   "label": "Fiscalía de Instrucción",           "icon": "⚖️", "activa": True},
            {"key": "camara_sf",        "label": "Fiscalía de Cámara",         "icon": "🏛️", "activa": True},
            {"key": "mesa_sf",          "label": "Mesa de Entradas — San Francisco",              "icon": "📋", "activa": True},
            {"key": "juzgado_sf",       "label": "Juzgado de Control — San Francisco",           "icon": "⚖️", "activa": False},
        ],
        "flujos": {
            "policia_sf":     ["fiscal_inst_sf", "mesa_sf"],
            "fiscal_inst_sf": ["policia_sf", "camara_sf", "mesa_sf", "juzgado_sf"],
            "camara_sf":      ["fiscal_inst_sf"],
            "mesa_sf":        ["fiscal_inst_sf", "policia_sf"],
            "juzgado_sf":     ["fiscal_inst_sf", "camara_sf"],
        },
    },

    # ── 6ª Circunscripción — Villa Dolores ────────────────────────────────────
    # 2 Fiscalías Instrucción + 1 de Cámara
    "villa_dolores": {
        "nombre": "MPF Villa Dolores",
        "circunscripcion": "6ª — Villa Dolores",
        "ciudad": "Villa Dolores",
        "tipo": "interior",
        "tipo_policia": POLICIA_PROVINCIAL,
        "modulos": [MODULO_PENAL, MODULO_CONTRAVENCIONAL],
        "oficinas": [
            {"key": "policia_vd",       "label": "Policía de la Provincia — Villa Dolores",       "icon": "🚓", "activa": True},
            {"key": "fiscal_inst_vd_1", "label": "Fiscalía de Instrucción N°1",  "icon": "⚖️", "activa": True},
            {"key": "fiscal_inst_vd_2", "label": "Fiscalía de Instrucción N°2",  "icon": "⚖️", "activa": True},
            {"key": "camara_vd",        "label": "Fiscalía de Cámara",              "icon": "🏛️", "activa": True},
            {"key": "mesa_vd",          "label": "Mesa de Entradas — Villa Dolores",             "icon": "📋", "activa": True},
            {"key": "juzgado_vd",       "label": "Juzgado de Control — Villa Dolores",          "icon": "⚖️", "activa": False},
        ],
        "flujos": {
            "policia_vd":      ["fiscal_inst_vd_1", "fiscal_inst_vd_2", "mesa_vd"],
            "fiscal_inst_vd_1":["policia_vd", "camara_vd", "mesa_vd", "juzgado_vd", "fiscal_inst_vd_2"],
            "fiscal_inst_vd_2":["policia_vd", "camara_vd", "mesa_vd", "juzgado_vd", "fiscal_inst_vd_1"],
            "camara_vd":       ["fiscal_inst_vd_1", "fiscal_inst_vd_2"],
            "mesa_vd":         ["fiscal_inst_vd_1", "fiscal_inst_vd_2", "policia_vd"],
            "juzgado_vd":      ["fiscal_inst_vd_1", "fiscal_inst_vd_2", "camara_vd"],
        },
    },

    # ── 7ª Circunscripción — Cruz del Eje ────────────────────────────────────
    # 1 Fiscalía Instrucción + 1 de Cámara
    "cruz_del_eje": {
        "nombre": "MPF Cruz del Eje",
        "circunscripcion": "7ª — Cruz del Eje",
        "ciudad": "Cruz del Eje",
        "tipo": "interior",
        "tipo_policia": POLICIA_PROVINCIAL,
        "modulos": [MODULO_PENAL, MODULO_CONTRAVENCIONAL],
        "oficinas": [
            {"key": "policia_ce",       "label": "Policía de la Provincia — Cruz del Eje",        "icon": "🚓", "activa": True},
            {"key": "fiscal_inst_ce",   "label": "Fiscalía de Instrucción",        "icon": "⚖️", "activa": True},
            {"key": "camara_ce",        "label": "Fiscalía de Cámara",          "icon": "🏛️", "activa": True},
            {"key": "mesa_ce",          "label": "Mesa de Entradas — Cruz del Eje",               "icon": "📋", "activa": True},
            {"key": "juzgado_ce",       "label": "Juzgado de Control — Cruz del Eje",            "icon": "⚖️", "activa": False},
        ],
        "flujos": {
            "policia_ce":     ["fiscal_inst_ce", "mesa_ce"],
            "fiscal_inst_ce": ["policia_ce", "camara_ce", "mesa_ce", "juzgado_ce"],
            "camara_ce":      ["fiscal_inst_ce"],
            "mesa_ce":        ["fiscal_inst_ce", "policia_ce"],
            "juzgado_ce":     ["fiscal_inst_ce", "camara_ce"],
        },
    },

    # ── 8ª Circunscripción — Laboulaye ────────────────────────────────────────
    # 1 Fiscalía Instrucción + 1 de Cámara
    "laboulaye": {
        "nombre": "MPF Laboulaye",
        "circunscripcion": "8ª — Laboulaye",
        "ciudad": "Laboulaye",
        "tipo": "interior",
        "tipo_policia": POLICIA_PROVINCIAL,
        "modulos": [MODULO_PENAL, MODULO_CONTRAVENCIONAL],
        "oficinas": [
            {"key": "policia_lb",       "label": "Policía de la Provincia — Laboulaye",           "icon": "🚓", "activa": True},
            {"key": "fiscal_inst_lb",   "label": "Fiscalía de Instrucción",          "icon": "⚖️", "activa": True},
            {"key": "camara_lb",        "label": "Fiscalía de Cámara",               "icon": "🏛️", "activa": True},
            {"key": "mesa_lb",          "label": "Mesa de Entradas — Laboulaye",                  "icon": "📋", "activa": True},
            {"key": "juzgado_lb",       "label": "Juzgado de Control — Laboulaye",               "icon": "⚖️", "activa": False},
        ],
        "flujos": {
            "policia_lb":     ["fiscal_inst_lb", "mesa_lb"],
            "fiscal_inst_lb": ["policia_lb", "camara_lb", "mesa_lb", "juzgado_lb"],
            "camara_lb":      ["fiscal_inst_lb"],
            "mesa_lb":        ["fiscal_inst_lb", "policia_lb"],
            "juzgado_lb":     ["fiscal_inst_lb", "camara_lb"],
        },
    },

    # ── 9ª Circunscripción — Deán Funes ──────────────────────────────────────
    # 1 Fiscalía Instrucción + 1 de Cámara
    "dean_funes": {
        "nombre": "MPF Deán Funes",
        "circunscripcion": "9ª — Deán Funes",
        "ciudad": "Deán Funes",
        "tipo": "interior",
        "tipo_policia": POLICIA_PROVINCIAL,
        "modulos": [MODULO_PENAL, MODULO_CONTRAVENCIONAL],
        "oficinas": [
            {"key": "policia_df",       "label": "Policía de la Provincia — Deán Funes",          "icon": "🚓", "activa": True},
            {"key": "fiscal_inst_df",   "label": "Fiscalía de Instrucción",         "icon": "⚖️", "activa": True},
            {"key": "camara_df",        "label": "Fiscalía de Cámara",               "icon": "🏛️", "activa": True},
            {"key": "mesa_df",          "label": "Mesa de Entradas — Deán Funes",                 "icon": "📋", "activa": True},
            {"key": "juzgado_df",       "label": "Juzgado de Control — Deán Funes",              "icon": "⚖️", "activa": False},
        ],
        "flujos": {
            "policia_df":     ["fiscal_inst_df", "mesa_df"],
            "fiscal_inst_df": ["policia_df", "camara_df", "mesa_df", "juzgado_df"],
            "camara_df":      ["fiscal_inst_df"],
            "mesa_df":        ["fiscal_inst_df", "policia_df"],
            "juzgado_df":     ["fiscal_inst_df", "camara_df"],
        },
    },

    # ── 10ª Circunscripción — Río Tercero ────────────────────────────────────
    # 2 Fiscalías Instrucción + 1 de Cámara
    "rio_tercero": {
        "nombre": "MPF Río Tercero",
        "circunscripcion": "10ª — Río Tercero",
        "ciudad": "Río Tercero",
        "tipo": "interior",
        "tipo_policia": POLICIA_PROVINCIAL,
        "modulos": [MODULO_PENAL, MODULO_CONTRAVENCIONAL],
        "oficinas": [
            {"key": "policia_rt",       "label": "Policía de la Provincia — Río Tercero",         "icon": "🚓", "activa": True},
            {"key": "fiscal_inst_rt_1", "label": "Fiscalía de Instrucción N°1",    "icon": "⚖️", "activa": True},
            {"key": "fiscal_inst_rt_2", "label": "Fiscalía de Instrucción N°2",      "icon": "⚖️", "activa": True},
            {"key": "camara_rt",        "label": "Fiscalía de Cámara",               "icon": "🏛️", "activa": True},
            {"key": "mesa_rt",          "label": "Mesa de Entradas — Río Tercero",                "icon": "📋", "activa": True},
            {"key": "juzgado_rt",       "label": "Juzgado de Control — Río Tercero",             "icon": "⚖️", "activa": False},
        ],
        "flujos": {
            "policia_rt":      ["fiscal_inst_rt_1", "fiscal_inst_rt_2", "mesa_rt"],
            "fiscal_inst_rt_1":["policia_rt", "camara_rt", "mesa_rt", "juzgado_rt", "fiscal_inst_rt_2"],
            "fiscal_inst_rt_2":["policia_rt", "camara_rt", "mesa_rt", "juzgado_rt", "fiscal_inst_rt_1"],
            "camara_rt":       ["fiscal_inst_rt_1", "fiscal_inst_rt_2"],
            "mesa_rt":         ["fiscal_inst_rt_1", "fiscal_inst_rt_2", "policia_rt"],
            "juzgado_rt":      ["fiscal_inst_rt_1", "fiscal_inst_rt_2", "camara_rt"],
        },
    },
}


# ── Helpers ────────────────────────────────────────────────────────────────────

def get_nodo(nodo_key: str) -> dict:
    """Retorna la configuración de un nodo. Fallback a cba_norte."""
    return NODOS.get(nodo_key, NODOS["cba_norte"])


def get_oficinas_nodo(nodo_key: str) -> dict[str, dict]:
    """
    Retorna {office_key: office_dict} para el nodo dado,
    incluyendo campo 'fantasma' (True si no está activa).
    """
    nodo = get_nodo(nodo_key)
    result = {}
    for o in nodo.get("oficinas", []):
        result[o["key"]] = {
            **o,
            "tipo": "activa" if o.get("activa", True) else "fantasma",
        }
    return result


def get_flujos_nodo(nodo_key: str) -> dict[str, list]:
    """Retorna el grafo de flujos permitidos para el nodo."""
    return get_nodo(nodo_key).get("flujos", {})


def nodos_por_ciudad() -> dict[str, list]:
    """Agrupa nodos por ciudad para la UI de selección."""
    result: dict[str, list] = {}
    for k, v in NODOS.items():
        result.setdefault(v["ciudad"], []).append(k)
    return result


def tiene_modulo(nodo_key: str, modulo: str) -> bool:
    """Verifica si un nodo tiene habilitado un módulo (penal/contravencional)."""
    return modulo in get_nodo(nodo_key).get("modulos", [])


def get_label_policia(nodo_key: str) -> str:
    """Retorna la etiqueta del tipo de policía del nodo."""
    tipo = get_nodo(nodo_key).get("tipo_policia", POLICIA_PROVINCIAL)
    return {
        POLICIA_JUDICIAL_MPF: "Policía Judicial (MPF)",
        POLICIA_PROVINCIAL:   "Policía de la Provincia de Córdoba",
    }.get(tipo, tipo)


# ── Usuarios demo por nodo ────────────────────────────────────────────────────
# En producción esto vendría de una tabla de usuarios en la DB
USUARIOS_DEMO: dict[str, dict] = {
    # Córdoba Capital
    "aperez":    {"nombre": "Dra. Ana Pérez",         "nodo": "cba_norte",   "oficina": "fiscal_cba_norte",  "pass": "mpf2024"},
    "cmedina":   {"nombre": "Dr. Carlos Medina",      "nodo": "cba_sur",     "oficina": "fiscal_cba_sur",    "pass": "mpf2024"},
    "lsuarez":   {"nombre": "Dra. Laura Suárez",      "nodo": "cba_genero",  "oficina": "fiscal_cba_genero", "pass": "mpf2024"},
    "pjudicial": {"nombre": "Of. Roberto Sosa",       "nodo": "cba_norte",   "oficina": "policia_judicial",  "pass": "mpf2024"},
    # Río Cuarto
    "mrodriguez":{"nombre": "Dr. Miguel Rodríguez",   "nodo": "rio_cuarto",  "oficina": "fiscal_inst_rc_1",  "pass": "mpf2024"},
    "sgomez":    {"nombre": "Dra. Silvia Gómez",      "nodo": "rio_cuarto",  "oficina": "fiscal_inst_rc_2",  "pass": "mpf2024"},
    "policiarc": {"nombre": "Com. Jorge Herrera",     "nodo": "rio_cuarto",  "oficina": "policia_rc",        "pass": "mpf2024"},
    # Interior
    "demo":      {"nombre": "Usuario Demo",           "nodo": "cba_norte",   "oficina": "fiscal_cba_norte",  "pass": "demo"},
}
