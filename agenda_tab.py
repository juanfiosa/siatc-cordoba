# -*- coding: utf-8 -*-
"""
Tab de Agenda / Audiencias — SIATC
Ministerio Público Fiscal de Córdoba
"""

import streamlit as st
from datetime import date, datetime, timedelta
import database as db
from database import agregar_nota_causa
from pdf_gen import pdf_agenda_semanal
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
    _cerradas = s["realizadas"] + s["ausentes"]
    _pct_comp = round(s["realizadas"] * 100 / _cerradas) if _cerradas else None
    c1, c2, c3, c4, c5, c6 = st.columns(6)
    c1.metric("Total agendadas",  s["total"])
    c2.metric("Hoy",              s["hoy"],      delta="HOY" if s["hoy"] else None)
    c3.metric("Próximos 7 días",  s["proximas"])
    c4.metric("Realizadas",       s["realizadas"])
    c5.metric("Ausencias",        s["ausentes"],
              delta=f"⚠️ {s['ausentes']}" if s["ausentes"] else None,
              delta_color="inverse")
    if _pct_comp is not None:
        c6.metric("Comparecencia", f"{_pct_comp}%",
                  delta=f"{s['realizadas']}/{_cerradas}",
                  delta_color="normal",
                  help="Audiencias realizadas / (realizadas + ausencias)")
    else:
        c6.metric("Comparecencia", "—", help="Sin audiencias finalizadas aún")


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

    # iCal export button
    try:
        def _to_ical(auds: list) -> bytes:
            lines = [
                "BEGIN:VCALENDAR", "VERSION:2.0",
                "PRODID:-//SIATC MPF Córdoba//SIATC//ES",
                "CALSCALE:GREGORIAN", "METHOD:PUBLISH",
            ]
            for a in auds:
                try:
                    _dt_start = datetime.strptime(f"{a['fecha']} {a.get('hora','09:00')}", "%Y-%m-%d %H:%M")
                    _dt_end   = _dt_start + timedelta(hours=1)
                    _uid = f"siatc-{a['id']}@mpfcordoba.gob.ar"
                    _summ = f"{TIPO_LABEL.get(a.get('tipo',''), a.get('tipo',''))} — {a.get('apellido_nombre','').split(',')[0]} ({a.get('numero','')})"
                    _loc  = a.get("lugar","") or "Sede de la Unidad Contravencional"
                    lines += [
                        "BEGIN:VEVENT",
                        f"UID:{_uid}",
                        f"DTSTART:{_dt_start.strftime('%Y%m%dT%H%M%S')}",
                        f"DTEND:{_dt_end.strftime('%Y%m%dT%H%M%S')}",
                        f"SUMMARY:{_summ}",
                        f"LOCATION:{_loc}",
                        f"STATUS:{'CONFIRMED' if a.get('estado','')=='programada' else 'TENTATIVE'}",
                        "END:VEVENT",
                    ]
                except Exception:
                    pass
            lines.append("END:VCALENDAR")
            return "\r\n".join(lines).encode("utf-8")

        _ical_bytes = _to_ical(audiencias)
        st.download_button(
            f"📅 Exportar {len(audiencias)} audiencia(s) (.ics)",
            data=_ical_bytes,
            file_name=f"audiencias_SIATC_{date.today().isoformat()}.ics",
            mime="text/calendar",
            key="aud_ical_export",
        )
    except Exception:
        pass

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
                            # Si hubo ausencia, registrar nota automática en la causa
                            if nuevo == "ausente":
                                _tipo_lbl = TIPO_LABEL.get(a.get("tipo", ""), a.get("tipo", ""))
                                db.agregar_nota_causa(
                                    a["causa_id"],
                                    f"INCOMPARECENCIA: Imputado/a no se presentó a {_tipo_lbl} "
                                    f"del {a['fecha']} a las {a.get('hora','')}.  "
                                    f"Se registra incumplimiento de citación. Evaluar continuación del proceso.",
                                    fiscal,
                                )
                            elif nuevo == "realizada":
                                _tipo_lbl = TIPO_LABEL.get(a.get("tipo", ""), a.get("tipo", ""))
                                db.agregar_nota_causa(
                                    a["causa_id"],
                                    f"AUDIENCIA REALIZADA: {_tipo_lbl} del {a['fecha']} a las "
                                    f"{a.get('hora','')} efectuada con presencia del imputado/a."
                                    + (f" Obs: {obs_aud}" if obs_aud.strip() else ""),
                                    fiscal,
                                )
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

    # ── Conflicto de horario ───────────────────────────────────────────────────
    _hora_str = hora.strftime("%H:%M")
    _conflictos = [
        a for a in db.listar_audiencias(desde=fecha.isoformat(), hasta=fecha.isoformat())
        if a.get("hora") == _hora_str and a.get("estado") == "programada"
        and a.get("causa_id") != causa["id"]
    ]
    if _conflictos:
        st.warning(
            f"⚠️ **Conflicto de horario**: ya existe(n) **{len(_conflictos)} audiencia(s)** "
            f"programada(s) el {fecha.strftime('%d/%m/%Y')} a las {_hora_str}: "
            + ", ".join(f"{c['numero']} ({c['apellido_nombre'].split(',')[0]})"
                       for c in _conflictos)
        )
        # Suggest available slots
        _auds_dia = db.listar_audiencias(desde=fecha.isoformat(), hasta=fecha.isoformat())
        _horas_ocupadas = {a["hora"] for a in _auds_dia if a.get("estado") == "programada"}
        _horarios_std = [f"{h:02d}:{m:02d}" for h in range(8, 17) for m in (0, 30)]
        _libres = [h for h in _horarios_std if h not in _horas_ocupadas][:4]
        if _libres:
            st.caption(f"💡 Horarios disponibles ese día: " + " | ".join(_libres))
    elif fecha.isoformat() == date.today().isoformat():
        st.info("📋 La audiencia está programada para **hoy**. Verificá disponibilidad.")
    elif fecha.weekday() >= 5:
        st.warning("⚠️ La fecha seleccionada es un fin de semana. Confirmá que es correcto.")

    if st.button("📅 Agendar audiencia", type="primary", key="btn_nueva_aud"):
        db.crear_audiencia(
            causa_id=causa["id"],
            tipo=tipo,
            fecha=fecha.isoformat(),
            hora=hora.strftime("%H:%M"),
            lugar=lugar,
            observaciones=obs
        )
        st.cache_data.clear() if hasattr(st, "cache_data") else None
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
        # Weekly stats summary + PDF export
        _sem_auds = db.listar_audiencias(
            desde=lunes.isoformat(),
            hasta=(lunes + timedelta(days=6)).isoformat()
        )
        _col_sum, _col_pdf = st.columns([4, 1])
        if _sem_auds:
            from collections import Counter as _C
            _cnt_sem = _C(a["estado"] for a in _sem_auds)
            _col_sum.markdown(
                f"<small>Semana: **{len(_sem_auds)} audiencias** — "
                f"🔵 {_cnt_sem.get('programada',0)} programadas &nbsp;"
                f"🟢 {_cnt_sem.get('realizada',0)} realizadas &nbsp;"
                f"🔴 {_cnt_sem.get('ausente',0)} ausentes &nbsp;"
                f"🟡 {_cnt_sem.get('reprogramada',0)} reprogramadas</small>",
                unsafe_allow_html=True
            )
            try:
                _unidad_ag = db.listar_causas(limit=1)
                _unidad_ag_key = _unidad_ag[0].get("unidad", "norte") if _unidad_ag else "norte"
                _pdf_sem = pdf_agenda_semanal(
                    _sem_auds, lunes.isoformat(), viernes.isoformat(), fiscal, _unidad_ag_key
                )
                _col_pdf.download_button(
                    "⬇️ PDF semana",
                    data=_pdf_sem,
                    file_name=f"agenda_{lunes.strftime('%Y%m%d')}.pdf",
                    mime="application/pdf",
                    key=f"dl_agenda_sem_{lunes.isoformat()}",
                    use_container_width=True,
                )
            except Exception:
                pass
        st.markdown("")
        _vista_semana(st.session_state.get("sem_offset", 0))

        # Seguimientos que vencen esta semana
        _segs_sem_venc = db.listar_seguimientos(estado="activo")
        _segs_sem_venc = [
            s for s in _segs_sem_venc
            if lunes.isoformat() <= s.get("fecha_fin","") <= viernes.isoformat()
        ]
        if _segs_sem_venc:
            st.markdown("---")
            st.markdown(f"**⏳ Seguimientos que vencen esta semana ({len(_segs_sem_venc)})**")
            for _sv in _segs_sem_venc:
                _nom_sv = (_sv.get("apellido_nombre","") or "").split(",")[0]
                _fin_sv = _sv.get("fecha_fin","")
                _tipo_sv = {"suspension":"Suspensión","mediacion":"Mediación","acuerdo":"Acuerdo"}.get(
                    _sv.get("tipo_resolucion",""), _sv.get("tipo_resolucion",""))
                st.caption(f"🔶 {_nom_sv} — {_tipo_sv} — Vence: {_fin_sv} | {_sv.get('numero','')}")

    elif vista == "📋 Lista de audiencias":
        _lista_audiencias(fiscal)

    else:
        _form_nueva_audiencia(fiscal)
