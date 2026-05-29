# -*- coding: utf-8 -*-
"""
Perfil del Imputado — SIATC
Vista consolidada de una persona: causas, seguimientos y audiencias.
"""

import streamlit as st
from datetime import date, datetime, timedelta
import database as db
from data_cordoba import TIPOS_INFRACCION, UNIDADES
from pdf_gen import pdf_perfil_persona
from database import causas_similares
import plotly.express as px
import pandas as pd

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

    # Compute a simple risk score (0-10)
    _riesgo_pts = 0
    _riesgo_pts += min(antec * 2, 4)          # up to 4 pts for antecedentes
    _n_rojo = sum(1 for c in causas if c.get("carril") == "rojo")
    _riesgo_pts += min(_n_rojo, 3)             # up to 3 pts for rojo carriles
    _n_ausente = sum(1 for a in auds if a.get("estado") == "ausente")
    _riesgo_pts += min(_n_ausente, 2)          # up to 2 pts for incomparecencias
    _n_inc = sum(1 for s in segs if s.get("estado") == "incumplido")
    _riesgo_pts += min(_n_inc, 1)              # 1 pt for seguimiento incumplido
    _riesgo_nivel = (
        ("🔴 Alto", "#f8d7da") if _riesgo_pts >= 5 else
        ("🟡 Medio", "#fff3cd") if _riesgo_pts >= 2 else
        ("🟢 Bajo", "#d4edda")
    )
    _r_lbl, _r_bg = _riesgo_nivel

    col_m1, col_m2, col_m3, col_m4, col_m5 = st.columns(5)
    col_m1.metric("Causas totales", perfil["total_causas"])
    col_m2.metric("Antecedentes",   antec)
    col_m3.metric("Seguimientos",   len(segs))
    col_m4.metric("Audiencias",     len(auds))
    col_m5.markdown(
        f"<div style='background:{_r_bg};border-radius:8px;padding:8px;text-align:center'>"
        f"<strong>Nivel de riesgo</strong><br>"
        f"<span style='font-size:1.2rem'>{_r_lbl}</span><br>"
        f"<small>Score: {_riesgo_pts}/10</small></div>",
        unsafe_allow_html=True
    )

    st.markdown(_badge_antecedentes(antec), unsafe_allow_html=True)

    # ── Actividad reciente de la persona (últimos 30 días) ───────────────────
    _hoy_pf = date.today()
    _hace30 = (_hoy_pf - timedelta(days=30)).isoformat()
    _auds_recientes = [a for a in auds if a.get("fecha","") >= _hace30]
    _causas_activas = [c for c in causas if c.get("estado") in
                       ("ingresada","clasificada","notificada","en_mediacion")]
    if _auds_recientes or _causas_activas:
        _tags = []
        if _causas_activas:
            _tags.append(f"📂 {len(_causas_activas)} causa(s) activa(s)")
        if _auds_recientes:
            _n_aud_prog = sum(1 for a in _auds_recientes if a.get("estado") == "programada")
            _n_aud_real = sum(1 for a in _auds_recientes if a.get("estado") == "realizada")
            _n_aud_aus  = sum(1 for a in _auds_recientes if a.get("estado") == "ausente")
            _tags.append(f"📅 {len(_auds_recientes)} audiencia(s) (últimos 30d): {_n_aud_prog} prog. / {_n_aud_real} realiz. / {_n_aud_aus} ausente(s)")
        _segs_activos = [s for s in segs if s.get("estado") == "activo"]
        if _segs_activos:
            _tags.append(f"🔍 {len(_segs_activos)} seguimiento(s) activo(s)")
        st.info("  |  ".join(_tags))

    # ── Línea de tiempo visual ────────────────────────────────────────────────
    _gantt_rows = []
    _today = date.today().isoformat()

    for c in causas:
        _inf_lbl = TIPOS_INFRACCION.get(c.get("tipo_infraccion",""), {}).get("label", c.get("tipo_infraccion",""))
        _start = (c.get("created_at") or _today)[:10]
        _fin   = (c.get("updated_at") or _today)[:10]
        # Ensure finish > start so Gantt renders a visible bar
        if _fin <= _start:
            _fin = (datetime.strptime(_start, "%Y-%m-%d") + timedelta(days=1)).strftime("%Y-%m-%d")
        _carril = c.get("carril", "")
        _gantt_rows.append({
            "Evento": f"Causa: {_inf_lbl[:25]}",
            "Inicio": _start,
            "Fin":    _fin,
            "Categoría": {"verde":"🟢 Mediación","amarillo":"🟡 Suspensión","rojo":"🔴 Proceso"}.get(_carril, "Causa"),
            "Detalle": f"{c.get('numero','')} — {c.get('estado','').capitalize()}",
        })

    for seg in segs:
        _gantt_rows.append({
            "Evento": "Seguimiento",
            "Inicio": (seg.get("fecha_inicio") or _today)[:10],
            "Fin":    (seg.get("fecha_fin") or _today)[:10],
            "Categoría": "🔍 Seguimiento",
            "Detalle": f"{seg.get('tipo_resolucion','').replace('_',' ').capitalize()} — {seg.get('estado','').capitalize()}",
        })

    for a in auds:
        _a_date = a.get("fecha", _today)
        _a_fin  = (datetime.strptime(_a_date, "%Y-%m-%d") + timedelta(days=1)).strftime("%Y-%m-%d")
        _gantt_rows.append({
            "Evento": f"Audiencia",
            "Inicio": _a_date,
            "Fin":    _a_fin,
            "Categoría": {"realizada":"📅 Audiencia realizada","ausente":"🚨 Incomparecencia",
                          "programada":"🔵 Audiencia programada"}.get(a.get("estado",""), "📅 Audiencia"),
            "Detalle": f"{a.get('tipo','').replace('_',' ').capitalize()} — {a.get('hora','')} {a.get('estado','').capitalize()}",
        })

    if _gantt_rows:
        _df_gantt = pd.DataFrame(_gantt_rows)
        _color_map = {
            "🟢 Mediación":           "#2ECC71",
            "🟡 Suspensión":          "#F39C12",
            "🔴 Proceso":             "#E74C3C",
            "🔍 Seguimiento":         "#2e5090",
            "📅 Audiencia realizada": "#28a745",
            "🚨 Incomparecencia":     "#dc3545",
            "🔵 Audiencia programada":"#007bff",
            "📅 Audiencia":           "#5a8de4",
        }
        try:
            fig_tl = px.timeline(
                _df_gantt,
                x_start="Inicio", x_end="Fin",
                y="Evento", color="Categoría",
                hover_data=["Detalle"],
                color_discrete_map=_color_map,
                title="Línea de tiempo del imputado/a",
            )
            fig_tl.update_yaxes(autorange="reversed")
            fig_tl.update_layout(
                height=max(180, 60 + len(_gantt_rows) * 35),
                margin=dict(l=0, r=0, t=40, b=10),
                legend=dict(orientation="h", y=1.18),
                showlegend=True,
            )
            st.plotly_chart(fig_tl, use_container_width=True)
        except Exception:
            pass   # si plotly.timeline no está disponible, omitir

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
        # Bulk-fetch upcoming audiencias for all causas of this persona
        _c_ids_pf = [c["id"] for c in causas]
        _prox_pf: dict = {}
        if _c_ids_pf:
            _today_pf = date.today().isoformat()
            _all_auds_pf = db.listar_audiencias(desde=_today_pf)
            for _a in _all_auds_pf:
                _cid = _a.get("causa_id")
                if _cid in _c_ids_pf and _cid not in _prox_pf and _a.get("estado") == "programada":
                    _prox_pf[_cid] = _a

        for c in causas:
            inf = TIPOS_INFRACCION.get(c.get("tipo_infraccion", ""), {})
            ic, bg, border = CARRIL_CSS.get(c.get("carril", ""), ("⚪", "#f8f9fa", "#ccc"))
            est_icon = ESTADO_BADGE.get(c.get("estado", ""), "")
            _pa = _prox_pf.get(c["id"])
            _aud_badge = f"  📅 {_pa['fecha']} {_pa['hora']}" if _pa else ""
            with st.expander(
                f"{ic} {c['numero']} — {inf.get('label', c.get('tipo_infraccion',''))} "
                f"| {est_icon} {c.get('estado','').capitalize()}{_aud_badge}"
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

                # Timeline de la causa — notas con estilo gris, transiciones en azul
                timeline = db.get_timeline(c["id"])
                if timeline:
                    st.markdown("**Línea de tiempo:**")
                    for t in timeline:
                        _es_nota_pf = (t.get("estado_anterior") == t.get("estado_nuevo")
                                       and t.get("estado_anterior"))
                        if _es_nota_pf:
                            st.markdown(
                                f"<div style='border-left:3px solid #6c757d;padding:3px 10px;"
                                f"margin:2px 0;background:#f0f0f0;border-radius:0 4px 4px 0;"
                                f"font-size:0.82rem'>"
                                f"📝 <strong>{t['created_at'][:16]}</strong> — "
                                f"{t.get('usuario','')}: <em>{t.get('observaciones','')}</em>"
                                f"</div>",
                                unsafe_allow_html=True
                            )
                        else:
                            _ant_lbl = db.ESTADOS_LABEL.get(t.get("estado_anterior",""), t.get("estado_anterior","") or "inicio")
                            _nvo_lbl = db.ESTADOS_LABEL.get(t.get("estado_nuevo",""), t.get("estado_nuevo",""))
                            st.markdown(
                                f"<div style='border-left:3px solid #2e5090;padding:3px 10px;"
                                f"margin:2px 0;background:#f8f9fa;border-radius:0 4px 4px 0;"
                                f"font-size:0.82rem'>"
                                f"<strong>{t['created_at'][:16]}</strong> — "
                                f"{_ant_lbl} → <strong>{_nvo_lbl}</strong>"
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
        import pandas as _pd_pf
        BADGE = {"programada": "🔵", "realizada": "🟢",
                 "ausente": "🔴", "reprogramada": "🟡", "cancelada": "⚫"}
        TIPO_AUD = {
            "audiencia": "Aud. contravencional", "mediacion": "Aud. mediación",
            "acta_compromiso": "Acta compromiso", "control_seg": "Control seguimiento",
        }
        _rows_aud_pf = []
        for a in sorted(auds, key=lambda x: x["fecha"], reverse=True):
            _rows_aud_pf.append({
                "Est.":  BADGE.get(a.get("estado",""),"⚪"),
                "Fecha": f"{a['fecha']} {a['hora']}",
                "Tipo":  TIPO_AUD.get(a.get("tipo",""), a.get("tipo","").replace("_"," ").capitalize()),
                "Estado": a.get("estado","").capitalize(),
                "Obs.":  a.get("observaciones","") or "",
            })
        st.dataframe(
            _pd_pf.DataFrame(_rows_aud_pf),
            use_container_width=True, hide_index=True,
            column_config={"Est.": st.column_config.TextColumn("", width="small")},
        )

    # ── Causas similares en el sistema ───────────────────────────────────────
    _tipos_persona = list({c.get("tipo_infraccion","") for c in causas if c.get("tipo_infraccion")})
    for tipo_inf in _tipos_persona[:3]:   # show at most 3 infraction types
        _sims = causas_similares(tipo_inf, exclude_persona_id=p["id"], limit=5)
        if _sims:
            _inf_lbl = TIPOS_INFRACCION.get(tipo_inf, {}).get("label", tipo_inf)
            with st.expander(f"📊 {len(_sims)} caso(s) similares — {_inf_lbl}"):
                for sc in _sims:
                    _ic_s = {"verde":"🟢","amarillo":"🟡","rojo":"🔴"}.get(sc.get("carril",""),"⚪")
                    _est_s = db.ESTADOS_LABEL.get(sc.get("estado",""), sc.get("estado",""))
                    _nom_s = (sc.get("apellido_nombre","") or "").split(",")[0]
                    st.markdown(
                        f"{_ic_s} **{sc['numero']}** — {_nom_s} &nbsp;|&nbsp; "
                        f"{_est_s} &nbsp;|&nbsp; {sc.get('created_at','')[:10]}"
                    )
                st.caption(f"Otros casos con la misma infracción en el sistema.")

    # ── Editar datos de contacto ─────────────────────────────────────────────
    with st.expander("✏️ Editar datos de contacto"):
        with st.form(key=f"edit_persona_{p['id']}"):
            col_e1, col_e2, col_e3 = st.columns(3)
            with col_e1:
                _new_nombre = st.text_input("Apellido y nombre", value=p.get("apellido_nombre",""))
                _new_edad   = st.number_input("Edad", min_value=16, max_value=99,
                                               value=int(p.get("edad") or 30))
            with col_e2:
                _new_dom = st.text_input("Domicilio", value=p.get("domicilio",""))
            with col_e3:
                _new_tel = st.text_input("Teléfono", value=p.get("telefono",""),
                                          placeholder="Ej: (0351) 4123456")
            if st.form_submit_button("💾 Guardar cambios", type="primary"):
                db.upsert_persona(
                    p["dni"], _new_nombre, _new_edad, _new_dom, _new_tel
                )
                st.success("Datos actualizados correctamente.")
                st.rerun()
        st.caption(f"Registrado: {p.get('created_at','')[:10]}  |  DNI: {p.get('dni','')}")


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
