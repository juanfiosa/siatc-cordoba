# -*- coding: utf-8 -*-
"""
Tab de Agenda / Audiencias — SIATC
Ministerio Público Fiscal de Córdoba
"""

import streamlit as st
from datetime import date, datetime, timedelta
import database as db
from data_cordoba import TIPOS_INFRACCION, UNIDADES

CARRIL_COLOR = {"verde": "🟢", "amarillo": "🟡", "rojo": "🔴"}
ESTADO_BADGE = {
    "programada":   "🔵 Programada",
    "realizada":    "🟢 Realizada",
    "ausente":      "🔴 Ausente",
    "reprogramada": "🟡 Reprogramada",
    "cancelada":    "⚫ Cancelada",
}
ESTADO_COLOR_CSS = {
    "programada":   "#cce5ff",
    "realizada":    "#d4edda",
    "ausente":      "#f8d7da",
    "reprogramada": "#fff3cd",
    "cancelada":    "#e2e3e5",
}

TIPO_LABEL = {
    "audiencia":       "Audiencia contravencional",
    "mediacion":       "Audiencia de mediación",
    "acta_compromiso": "Suscripción acta de compromiso",
    "control_seg":     "Control de seguimiento",
    "reprogramada":    "Audiencia reprogramada",
}


# ── Barra de métricas ─────────────────────────────────────────────────────────

def _metricas():
    s = db.stats_audiencias()
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Total agendadas",  s["total"])
    c2.metric("Hoy",              s["hoy"],      delta="HOY" if s["hoy"] else None)
    c3.metric("Próximos 7 días",  s["proximas"])
    c4.metric("Realizadas",       s["realizadas"])
    c5.metric("Ausencias",        s["ausentes"],
              delta=f"⚠️ {s['ausentes']}" if s["ausentes"] else None,
              delta_color="inverse")


# ── Vista semana ──────────────────────────────────────────────────────────────

def _vista_semana(semana_offset: int = 0):
    hoy   = date.today()
    lunes = hoy - timedelta(days=hoy.weekday()) + timedelta(weeks=semana_offset)
    dias  = [lunes + timedelta(days=i) for i in range(5)]   # lun→vie

    aud_sem = db.listar_audiencias(
        desde=lunes.isoformat(),
        hasta=(lunes + timedelta(days=6)).isoformat()
    )
    por_dia = {d.isoformat(): [] for d in dias}
    for a in aud_sem:
        if a["fecha"] in por_dia:
            por_dia[a["fecha"]].append(a)

    nombres_dia = ["Lun", "Mar", "Mié", "Jue", "Vie"]
    cols = st.columns(5)
    for col, dia, nombre in zip(cols, dias, nombres_dia):
        es_hoy = dia == hoy
        audiencias_dia = por_dia[dia.isoformat()]
        n_aud = len(audiencias_dia)
        n_prog = sum(1 for a in audiencias_dia if a.get("estado") == "programada")

        # Header with day indicator and count badge
        header_bg = "background:#1a2f5e;color:white;border-radius:6px;padding:4px 8px;" if es_hoy else "background:#f0f0f0;border-radius:6px;padding:4px 8px;"
        badge = f"<span style='background:#28a745;color:white;border-radius:10px;padding:1px 7px;font-size:0.75rem;margin-left:4px'>{n_aud}</span>" if n_aud else ""
        hoy_lbl = " 🔸 HOY" if es_hoy else ""
        col.markdown(
            f"<div style='{header_bg}text-align:center'>"
            f"<strong>{nombre} {dia.strftime('%d/%m')}{hoy_lbl}</strong>{badge}"
            f"</div>",
            unsafe_allow_html=True
        )
        col.markdown("")

        if not audiencias_dia:
            col.caption("—")
        for a in sorted(audiencias_dia, key=lambda x: x["hora"]):
            bg = ESTADO_COLOR_CSS.get(a["estado"], "#f0f0f0")
            col.markdown(
                f"<div style='background:{bg};border-radius:6px;padding:6px 8px;"
                f"margin-bottom:4px;font-size:0.82rem'>"
                f"<strong>{a['hora']}</strong> — {a['apellido_nombre'].split(',')[0]}<br>"
                f"<span style='color:#555'>{TIPO_LABEL.get(a['tipo'], a['tipo'])}</span><br>"
                f"<span style='font-size:0.75rem;color:#888'>{a['numero']}</span>"
                f"</div>",
                unsafe_allow_html=True
            )


# ── Lista detallada ───────────────────────────────────────────────────────────

def _lista_audiencias(fiscal):
    col_f1, col_f2, col_f3, col_f4 = st.columns([2, 1, 1, 1])
    with col_f1:
        busqueda_aud = st.text_input("Buscar por nombre o expediente",
                                     placeholder="Ej: García o UCN-00001",
                                     label_visibility="collapsed",
                                     key="aud_busqueda")
    with col_f2:
        rango = st.selectbox("Período", [
            "Hoy", "Esta semana", "Próximos 7 días", "Este mes", "Todos"
        ])
    with col_f3:
        filtro_estado = st.selectbox("Estado", ["Todos"] + db.ESTADOS_AUDIENCIA)
    with col_f4:
        filtro_tipo = st.selectbox("Tipo", ["Todos"] + list(TIPO_LABEL.keys()),
                                   format_func=lambda k: TIPO_LABEL.get(k, k) if k != "Todos" else "Todos")

    hoy = date.today()
    if rango == "Hoy":
        desde, hasta = hoy.isoformat(), hoy.isoformat()
    elif rango == "Esta semana":
        lunes = hoy - timedelta(days=hoy.weekday())
        desde, hasta = lunes.isoformat(), (lunes + timedelta(days=6)).isoformat()
    elif rango == "Próximos 7 días":
        desde, hasta = hoy.isoformat(), (hoy + timedelta(days=7)).isoformat()
    elif rango == "Este mes":
        desde = hoy.replace(day=1).isoformat()
        hasta = (hoy.replace(day=28) + timedelta(days=4)).replace(day=1) - timedelta(days=1)
        hasta = hasta.isoformat()
    else:
        desde, hasta = None, None

    estado_p = None if filtro_estado == "Todos" else filtro_estado
    audiencias = db.listar_audiencias(desde=desde, hasta=hasta, estado=estado_p)
    if filtro_tipo != "Todos":
        audiencias = [a for a in audiencias if a["tipo"] == filtro_tipo]
    if busqueda_aud:
        q = busqueda_aud.lower()
        audiencias = [a for a in audiencias
                      if q in (a.get("apellido_nombre","") or "").lower()
                      or q in (a.get("numero","") or "").lower()]

    if not audiencias:
        st.info("No hay audiencias para los filtros seleccionados.")
        return

    for a in audiencias:
        es_hoy_flag = a["fecha"] == hoy.isoformat()
        bg_exp = "#fff8e1" if es_hoy_flag else "#ffffff"
        with st.expander(
            f"{ESTADO_BADGE.get(a['estado'], a['estado'])} | "
            f"**{a['fecha']} {a['hora']}** | "
            f"{a['apellido_nombre']} — {a['numero']} | "
            f"{TIPO_LABEL.get(a['tipo'], a['tipo'])}"
            + (" 🔸 HOY" if es_hoy_flag else ""),
            expanded=es_hoy_flag
        ):
            col_i, col_a = st.columns([3, 2])
            with col_i:
                st.markdown(f"**Imputado/a:** {a['apellido_nombre']} (DNI: {a['dni']})")
                _tel_a = a.get("persona_telefono") or "—"
                _dom_a = a.get("persona_domicilio") or "—"
                st.markdown(f"📞 **Tel.:** {_tel_a}  |  🏠 **Dom.:** {_dom_a}")
                st.markdown(f"**Expediente:** {a['numero']}  |  "
                            f"**Unidad:** {a.get('unidad','').upper()}  |  "
                            f"{CARRIL_COLOR.get(a.get('carril',''), '')} Carril {a.get('carril','').capitalize()}")
                st.markdown(f"**Lugar:** {a['lugar'] or 'Sede de la Unidad'}")
                if a["observaciones"]:
                    st.caption(f"Obs.: {a['observaciones']}")
            with col_a:
                if a["estado"] == "programada":
                    nuevo = st.selectbox(
                        "Actualizar estado",
                        ["programada", "realizada", "ausente", "reprogramada", "cancelada"],
                        index=0,
                        key=f"aud_est_{a['id']}"
                    )
                    obs_aud = st.text_input("Observación", key=f"aud_obs_{a['id']}")
                    if nuevo != "programada":
                        if st.button("Aplicar", key=f"aud_apply_{a['id']}", type="primary"):
                            db.actualizar_estado_audiencia(a["id"], nuevo, obs_aud)
                            # Si hubo ausencia, agregar nota en la causa
                            if nuevo == "ausente":
                                db.avanzar_estado(
                                    a["causa_id"], "notificada", fiscal,
                                    f"Incomparecencia a audiencia del {a['fecha']}. Se evalúa continuación del proceso."
                                ) if False else None  # solo informativo
                            st.rerun()
                else:
                    st.markdown(f"**Estado:** {ESTADO_BADGE.get(a['estado'], a['estado'])}")


# ── Formulario nueva audiencia ────────────────────────────────────────────────

def _form_nueva_audiencia(fiscal):
    st.subheader("➕ Programar nueva audiencia")

    causas = db.listar_causas(limit=500)
    if not causas:
        st.info("No hay causas disponibles.")
        return

    opciones = {f"{c['numero']} — {c['apellido_nombre']}": c for c in causas}
    sel = st.selectbox("Causa", list(opciones.keys()), key="aud_nueva_causa")
    causa = opciones[sel]

    col1, col2, col3 = st.columns(3)
    with col1:
        tipo = st.selectbox("Tipo de audiencia", list(TIPO_LABEL.keys()),
                            format_func=lambda k: TIPO_LABEL[k], key="aud_nueva_tipo")
    with col2:
        fecha = st.date_input("Fecha", value=date.today() + timedelta(days=5),
                              key="aud_nueva_fecha")
    with col3:
        hora = st.time_input("Hora", value=datetime.strptime("09:00", "%H:%M").time(),
                             key="aud_nueva_hora")

    lugar = st.text_input(
        "Lugar",
        value=UNIDADES.get(causa.get("unidad", "norte"), "Sede de la Unidad Contravencional"),
        key="aud_nueva_lugar"
    )
    obs = st.text_area("Observaciones (opcional)", height=60, key="aud_nueva_obs")

    if st.button("📅 Agendar audiencia", type="primary", key="btn_nueva_aud"):
        db.crear_audiencia(
            causa_id=causa["id"],
            tipo=tipo,
            fecha=fecha.isoformat(),
            hora=hora.strftime("%H:%M"),
            lugar=lugar,
            observaciones=obs
        )
        st.success(f"Audiencia programada para el {fecha.strftime('%d/%m/%Y')} a las {hora.strftime('%H:%M')}.")
        st.rerun()


# ── Punto de entrada ──────────────────────────────────────────────────────────

def render_tab_agenda(fiscal):
    st.header("📅 Agenda de Audiencias")
    st.caption("Programación, seguimiento y registro de audiencias contravencionales.")

    _metricas()
    st.divider()

    vista = st.radio(
        "Vista",
        ["📆 Semana actual", "📋 Lista de audiencias", "➕ Nueva audiencia"],
        horizontal=True, label_visibility="collapsed", key="agenda_vista"
    )
    st.divider()

    if vista == "📆 Semana actual":
        col_nav1, col_nav2, col_nav3 = st.columns([1, 4, 1])
        with col_nav1:
            if st.button("◀ Semana anterior", key="sem_ant"):
                st.session_state["sem_offset"] = st.session_state.get("sem_offset", 0) - 1
                st.rerun()
        with col_nav3:
            if st.button("Semana siguiente ▶", key="sem_sig"):
                st.session_state["sem_offset"] = st.session_state.get("sem_offset", 0) + 1
                st.rerun()
        with col_nav2:
            offset = st.session_state.get("sem_offset", 0)
            hoy = date.today()
            lunes = hoy - timedelta(days=hoy.weekday()) + timedelta(weeks=offset)
            viernes = lunes + timedelta(days=4)
            st.markdown(f"<div style='text-align:center;font-weight:bold'>"
                        f"Semana del {lunes.strftime('%d/%m')} al {viernes.strftime('%d/%m/%Y')}"
                        f"</div>", unsafe_allow_html=True)
        # Weekly stats summary
        _sem_auds = db.listar_audiencias(
            desde=lunes.isoformat(),
            hasta=(lunes + timedelta(days=6)).isoformat()
        )
        if _sem_auds:
            from collections import Counter as _C
            _cnt_sem = _C(a["estado"] for a in _sem_auds)
            st.markdown(
                f"<small>Semana: **{len(_sem_auds)} audiencias** — "
                f"🔵 {_cnt_sem.get('programada',0)} programadas &nbsp;"
                f"🟢 {_cnt_sem.get('realizada',0)} realizadas &nbsp;"
                f"🔴 {_cnt_sem.get('ausente',0)} ausentes &nbsp;"
                f"🟡 {_cnt_sem.get('reprogramada',0)} reprogramadas</small>",
                unsafe_allow_html=True
            )
        st.markdown("")
        _vista_semana(st.session_state.get("sem_offset", 0))

    elif vista == "📋 Lista de audiencias":
        _lista_audiencias(fiscal)

    else:
        _form_nueva_audiencia(fiscal)
