# -*- coding: utf-8 -*-
"""
Perfil del Imputado — SIATC
Vista consolidada de una persona: causas, seguimientos y audiencias.
"""

import streamlit as st
from datetime import date, datetime
import database as db
from data_cordoba import TIPOS_INFRACCION, UNIDADES
from pdf_gen import pdf_perfil_persona

CARRIL_CSS = {
    "verde":    ("🟢", "#d4edda", "#28a745"),
    "amarillo": ("🟡", "#fff3cd", "#ffc107"),
    "rojo":     ("🔴", "#f8d7da", "#dc3545"),
}
ESTADO_BADGE = {
    "ingresada":    "📥", "clasificada": "🔍", "notificada": "📬",
    "en_mediacion": "🤝", "resuelta": "✅", "archivada": "🗄️",
}


def _badge_antecedentes(n: int) -> str:
    if n == 0:
        return "<span style='background:#28a745;color:white;border-radius:10px;padding:2px 10px;font-size:0.82rem'>Sin antecedentes</span>"
    color = "#ffc107" if n == 1 else "#dc3545"
    return (f"<span style='background:{color};color:white;border-radius:10px;"
            f"padding:2px 10px;font-size:0.82rem'>{n} antecedente(s)</span>")


def render_perfil(persona_id: int):
    """Renderiza el perfil completo de una persona dado su ID."""
    perfil = db.perfil_persona(persona_id)
    if not perfil:
        st.error("Persona no encontrada.")
        return

    p  = perfil["persona"]
    causas = perfil["causas"]
    segs   = perfil["seguimientos"]
    auds   = perfil["audiencias"]
    antec  = perfil["antecedentes"]

    # ── Header del perfil ────────────────────────────────────────────────────
    st.markdown(f"""
<div style='background:linear-gradient(90deg,#1a2f5e,#2e5090);border-radius:10px;
            padding:1.2rem 1.8rem;color:white;margin-bottom:1rem'>
  <h3 style='margin:0'>{p['apellido_nombre']}</h3>
  <p style='margin:0.2rem 0 0 0;opacity:0.85'>
    DNI: {p['dni']} &nbsp;|&nbsp; Edad: {p.get('edad','-')} años &nbsp;|&nbsp;
    Tel.: {p.get('telefono') or '—'} &nbsp;|&nbsp;
    Dom.: {p.get('domicilio','-')}
  </p>
</div>
""", unsafe_allow_html=True)

    col_m1, col_m2, col_m3, col_m4, col_m5 = st.columns(5)
    col_m1.metric("Causas totales", perfil["total_causas"])
    col_m2.metric("Antecedentes",   antec)
    col_m3.metric("Seguimientos",   len(segs))
    col_m4.metric("Audiencias",     len(auds))

    st.markdown(_badge_antecedentes(antec), unsafe_allow_html=True)

    # PDF export button
    try:
        _unidad_k = causas[0].get("unidad","norte") if causas else "norte"
        _pdf_pfil = pdf_perfil_persona(perfil, "", _unidad_k)
        col_m5.download_button(
            "⬇️ Ficha PDF",
            data=_pdf_pfil,
            file_name=f"perfil_{p['dni']}.pdf",
            mime="application/pdf",
            use_container_width=True,
            key=f"dl_perfil_{p['id']}",
        )
    except Exception:
        pass
    st.markdown("")

    # ── Historial de causas ──────────────────────────────────────────────────
    st.markdown("### 📂 Historial de causas")
    if not causas:
        st.info("Sin causas registradas.")
    else:
        for c in causas:
            inf = TIPOS_INFRACCION.get(c.get("tipo_infraccion", ""), {})
            ic, bg, border = CARRIL_CSS.get(c.get("carril", ""), ("⚪", "#f8f9fa", "#ccc"))
            est_icon = ESTADO_BADGE.get(c.get("estado", ""), "")
            with st.expander(
                f"{ic} {c['numero']} — {inf.get('label', c.get('tipo_infraccion',''))} "
                f"| {est_icon} {c.get('estado','').capitalize()}"
            ):
                col_a, col_b = st.columns([3, 2])
                with col_a:
                    st.markdown(f"**Artículo:** {inf.get('articulo','')}")
                    st.markdown(f"**Descripción:** {c.get('descripcion','')}")
                    st.markdown(f"**Fiscal:** {c.get('fiscal_asignado','')}")
                    st.markdown(f"**Unidad:** {c.get('unidad','').capitalize()}")
                with col_b:
                    st.markdown(
                        f"<div style='background:{bg};border-left:4px solid {border};"
                        f"padding:0.8rem;border-radius:4px'>"
                        f"<strong>{ic} Carril {c.get('carril','').capitalize()}</strong><br>"
                        f"{c.get('accion','')}"
                        f"</div>", unsafe_allow_html=True
                    )
                    st.caption(f"Ingresada: {c.get('created_at','')[:10]}")

                # Timeline de la causa
                timeline = db.get_timeline(c["id"])
                if timeline:
                    st.markdown("**Línea de tiempo:**")
                    for t in timeline:
                        st.markdown(
                            f"<div style='border-left:3px solid #2e5090;padding:3px 10px;"
                            f"margin:2px 0;background:#f8f9fa;border-radius:0 4px 4px 0;"
                            f"font-size:0.82rem'>"
                            f"<strong>{t['created_at'][:10]}</strong> — "
                            f"{t.get('estado_anterior','') or 'inicio'} → "
                            f"<strong>{t['estado_nuevo']}</strong>"
                            f"{' | ' + t['observaciones'] if t.get('observaciones') else ''}"
                            f"</div>",
                            unsafe_allow_html=True
                        )

    # ── Seguimientos ─────────────────────────────────────────────────────────
    if segs:
        st.markdown("### 🔍 Seguimientos post-resolución")
        for seg in segs:
            estado_col = {"activo": "#fff3cd", "cumplido": "#d4edda",
                          "incumplido": "#f8d7da"}.get(seg.get("estado",""), "#f0f0f0")
            prog = db.progress_seguimiento(seg["id"])
            st.markdown(
                f"<div style='background:{estado_col};border-radius:8px;"
                f"padding:0.8rem 1rem;margin-bottom:0.5rem'>"
                f"<strong>{seg.get('tipo_resolucion','').replace('_',' ').capitalize()}</strong>"
                f" — Estado: {seg.get('estado','').capitalize()} — "
                f"Período: {seg.get('fecha_inicio','')} → {seg.get('fecha_fin','')}<br>"
                f"Cumplimiento: {prog['cumplidas']}/{prog['total']} condiciones ({prog['pct']}%)"
                f"</div>",
                unsafe_allow_html=True
            )

    # ── Audiencias ───────────────────────────────────────────────────────────
    if auds:
        st.markdown("### 📅 Audiencias")
        BADGE = {"programada": "🔵", "realizada": "🟢",
                 "ausente": "🔴", "reprogramada": "🟡", "cancelada": "⚫"}
        for a in sorted(auds, key=lambda x: x["fecha"], reverse=True):
            st.markdown(
                f"{BADGE.get(a['estado'],'⚪')} **{a['fecha']} {a['hora']}** — "
                f"{a.get('tipo','').replace('_',' ').capitalize()} — "
                f"{a.get('estado','').capitalize()}"
                + (f" | _{a['observaciones']}_" if a.get("observaciones") else "")
            )

    # ── Teléfono / domicilio ─────────────────────────────────────────────────
    with st.expander("📋 Datos de contacto"):
        st.markdown(f"**Domicilio:** {p.get('domicilio') or 'No registrado'}")
        st.markdown(f"**Teléfono:** {p.get('telefono') or 'No registrado'}")
        st.caption(f"Registrado: {p.get('created_at','')[:10]}")


def render_buscador_perfil():
    """Widget de búsqueda de persona para mostrar su perfil."""
    st.subheader("🔎 Buscar imputado/a")
    busqueda = st.text_input("Nombre o DNI", placeholder="Ej: García o 38421667",
                             key="perfil_busqueda")
    if not busqueda:
        st.caption("Ingresá nombre o DNI para buscar.")
        return

    personas = db.listar_personas(busqueda=busqueda)
    if not personas:
        st.warning("No se encontraron personas con ese criterio.")
        return

    if len(personas) == 1:
        render_perfil(personas[0]["id"])
    else:
        sel = st.selectbox(
            f"{len(personas)} personas encontradas — seleccioná una:",
            personas,
            format_func=lambda p: f"{p['apellido_nombre']} — DNI {p['dni']}",
            key="perfil_sel"
        )
        if sel:
            render_perfil(sel["id"])
