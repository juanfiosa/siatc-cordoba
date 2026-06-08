# -*- coding: utf-8 -*-
"""
workflow.py — Modelo del flujo contravencional CCC como ÁRBOL por carril.

El estado físico en la DB sigue siendo el enum lineal de 6 valores
(ingresada/clasificada/notificada/en_mediacion/resuelta/archivada), pero el
PROCESO real se ramifica según el carril del triaje:

    🟢 Verde     → Mediación
    🟡 Amarillo  → Suspensión del proceso a prueba
    🔴 Rojo      → Proceso contravencional pleno

Este módulo deriva, a partir de (estado + carril + señales), la RUTA de la
causa, en qué ETAPA está parada y cuál es el SIGUIENTE PASO. Es la fuente
única para el riel de progreso, el badge de ruta y la acción principal.
"""
from __future__ import annotations

CARRIL_RUTA = {
    "verde":    ("🟢", "Mediación"),
    "amarillo": ("🟡", "Suspensión a prueba"),
    "rojo":     ("🔴", "Proceso pleno"),
}

# Etapas canónicas (orden del trámite). Labels de audiencia/resolución se
# ajustan por carril en ruta_causa().
_ETAPAS_BASE = [
    ("ingreso",      "Ingreso",       "📥"),
    ("triaje",       "Triaje",        "🔍"),
    ("notificacion", "Notificación",  "📬"),
    ("audiencia",    "Audiencia",     "📅"),
    ("resolucion",   "Resolución",    "⚖️"),
    ("seguimiento",  "Seguimiento",   "🔁"),
    ("cierre",       "Archivo",       "🗄️"),
]

_LABEL_POR_CARRIL = {
    "verde":    {"audiencia": "Audiencia de mediación", "resolucion": "Acuerdo de mediación"},
    "amarillo": {"audiencia": "Audiencia",              "resolucion": "Suspensión a prueba"},
    "rojo":     {"audiencia": "Audiencia",              "resolucion": "Resolución / elevación"},
}


def _aplica_seguimiento(carril: str, tiene_seguimiento: bool) -> bool:
    """El seguimiento es obligatorio en amarillo (suspensión); en verde/rojo
    solo si efectivamente se registró un seguimiento con condiciones."""
    return carril == "amarillo" or tiene_seguimiento


def ruta_causa(carril: str, tiene_seguimiento: bool = False) -> list[dict]:
    """Devuelve la lista ordenada de etapas de la ruta de ESTE carril."""
    carril = carril or "amarillo"
    labels = _LABEL_POR_CARRIL.get(carril, _LABEL_POR_CARRIL["amarillo"])
    etapas = []
    for key, label, icono in _ETAPAS_BASE:
        if key == "seguimiento" and not _aplica_seguimiento(carril, tiene_seguimiento):
            continue
        etapas.append({"key": key, "label": labels.get(key, label), "icono": icono})
    return etapas


def _etapa_actual_key(estado: str, carril: str, tiene_audiencia: bool,
                      aplica_seg: bool, seg_completo: bool) -> str | None:
    """Clave de la etapa donde está parada la causa (None = finalizada)."""
    if estado == "ingresada":
        return "triaje"
    if estado == "clasificada":
        return "notificacion"
    if estado == "notificada":
        return "resolucion" if tiene_audiencia else "audiencia"
    if estado == "en_mediacion":
        return "resolucion"
    if estado == "resuelta":
        if aplica_seg and not seg_completo:
            return "seguimiento"
        return "cierre"
    if estado == "archivada":
        return None
    return "triaje"


def progreso_causa(causa: dict, *, tiene_audiencia: bool = False,
                   tiene_seguimiento: bool = False, seg_completo: bool = False) -> dict:
    """
    Devuelve {carril, ruta_label, etapas:[{key,label,icono,status}], idx_actual}.
    status ∈ {'done','current','future'}.
    """
    carril = (causa.get("carril") or "amarillo")
    estado = causa.get("estado", "ingresada")
    aplica_seg = _aplica_seguimiento(carril, tiene_seguimiento)
    etapas = ruta_causa(carril, tiene_seguimiento)
    actual = _etapa_actual_key(estado, carril, tiene_audiencia, aplica_seg, seg_completo)

    keys = [e["key"] for e in etapas]
    if actual is None:                       # archivada → todo hecho
        idx_actual = len(etapas)
    elif actual in keys:
        idx_actual = keys.index(actual)
    else:
        idx_actual = 0

    for i, e in enumerate(etapas):
        e["status"] = "done" if i < idx_actual else ("current" if i == idx_actual else "future")

    ico, lbl = CARRIL_RUTA.get(carril, CARRIL_RUTA["amarillo"])
    return {"carril": carril, "ruta_icono": ico, "ruta_label": lbl,
            "etapas": etapas, "idx_actual": idx_actual}


def siguiente_accion(causa: dict, *, tiene_audiencia: bool = False,
                     tiene_seguimiento: bool = False, seg_completo: bool = False) -> dict:
    """
    Devuelve {icono, texto, accion} para la etapa actual.
    accion: 'clasificar' | 'audiencia' | 'seguimiento' | 'doc:<tipo>' | None
    """
    carril = (causa.get("carril") or "amarillo")
    estado = causa.get("estado", "ingresada")
    aplica_seg = _aplica_seguimiento(carril, tiene_seguimiento)
    actual = _etapa_actual_key(estado, carril, tiene_audiencia, aplica_seg, seg_completo)

    if actual is None:
        return {"icono": "✅", "texto": "Causa finalizada — sin acciones pendientes", "accion": None}
    if actual == "triaje":
        return {"icono": "📋", "texto": "Clasificar la causa para determinar el carril (triaje)",
                "accion": "clasificar"}
    if actual == "notificacion":
        if carril == "verde":
            return {"icono": "📨", "texto": "Enviar cédula de citación a **mediación**",
                    "accion": "doc:citacion_mediacion"}
        if carril == "rojo":
            return {"icono": "⚖️", "texto": "Notificar y preparar **requerimiento de apertura**",
                    "accion": "doc:requerimiento"}
        return {"icono": "📨", "texto": "Citar al imputado para **suspensión a prueba**",
                "accion": "doc:citacion_acta"}
    if actual == "audiencia":
        return {"icono": "📅", "texto": "Programar la audiencia", "accion": "audiencia"}
    if actual == "resolucion":
        if carril == "verde":
            return {"icono": "✍️", "texto": "Registrar el **acuerdo de mediación**",
                    "accion": "doc:acta_compromiso"}
        if carril == "rojo":
            return {"icono": "⚖️", "texto": "Elevar **requerimiento de apertura** del proceso",
                    "accion": "doc:requerimiento"}
        return {"icono": "✍️", "texto": "Otorgar la **suspensión a prueba** (acta de compromiso)",
                "accion": "doc:acta_compromiso"}
    if actual == "seguimiento":
        if tiene_seguimiento:
            return {"icono": "🔍", "texto": "Controlar el cumplimiento de las condiciones",
                    "accion": "seguimiento"}
        return {"icono": "🔍", "texto": "Registrar el **seguimiento** de condiciones",
                "accion": "seguimiento"}
    if actual == "cierre":
        return {"icono": "🗄️", "texto": "Archivar la causa (decreto de archivo)",
                "accion": "doc:decreto_archivo"}
    return {"icono": "📋", "texto": "Continuar con el trámite", "accion": None}
