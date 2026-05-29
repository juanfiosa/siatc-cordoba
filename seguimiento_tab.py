# -*- coding: utf-8 -*-
"""
Tab de Seguimiento Post-Resolución — SIATC
Ministerio Público Fiscal de Córdoba
"""

import streamlit as st
from datetime import datetime, date, timedelta
import database as db
from data_cordoba import TIPOS_INFRACCION, CONDICIONES_SUSPENSION
from pdf_gen import pdf_informe_seguimiento, pdf_acta_compromiso

# ── Helpers ───────────────────────────────────────────────────────────────────

TIPO_RES_LABEL = {
    "suspension": "Suspensión del Proceso a Prueba",
    "mediacion":  "Acuerdo de Mediación",
    "acuerdo":    "Acuerdo Conciliatorio",
}

TIPO_COND_LABEL = {
    "trabajo_comunitario": "🤝 Trabajo comunitario",
    "curso":               "📚 Curso / capacitación",
    "multa":               "💰 Multa / pago",
    "abstencion":          "🚫 Abstención / prohibición",
    "presentacion":        "📋 Presentación periódica",
    "otro":                "📌 Otra condición",
}

ESTADO_COLOR = {
    "pendiente":   "🔵",
    "en_curso":    "🟡",
    "cumplido":    "🟢",
    "incumplido":  "🔴",
}

SEG_ESTADO_COLOR = {
    "activo":     "🟡 Activo",
    "cumplido":   "🟢 Cumplido",
    "incumplido": "🔴 Incumplido",
    "revocado":   "⚫ Revocado",
}

def dias_restantes(fecha_fin_str):
    try:
        fin = datetime.strptime(fecha_fin_str, "%Y-%m-%d").date()
        delta = (fin - date.today()).days
        return delta
    except Exception:
        return None


def badge_dias(dias):
    if dias is None:
        return ""
    if dias < 0:
        return f"⚠️ Vencido hace {abs(dias)} días"
    if dias == 0:
        return "🔴 Vence HOY"
    if dias <= 7:
        return f"🟠 Vence en {dias} días"
    if dias <= 30:
        return f"🟡 Vence en {dias} días"
    return f"🟢 {dias} días restantes"


# ── Formulario: crear seguimiento ─────────────────────────────────────────────

def _form_nuevo_seguimiento(fiscal):
    st.subheader("➕ Registrar Seguimiento de Resolución")

    causas = (db.listar_causas(estado="resuelta")
              + db.listar_causas(estado="notificada")
              + db.listar_causas(estado="en_mediacion"))
    if not causas:
        st.info("No hay causas notificadas, en mediación o resueltas disponibles.")
        return

    opciones = {
        f"{c['numero']} — {c['apellido_nombre']}": c
        for c in causas
        if not db.get_seguimiento_por_causa(c["id"])
    }

    if not opciones:
        st.info("Todas las causas disponibles ya tienen seguimiento registrado.")
        return

    sel = st.selectbox("Causa", list(opciones.keys()))
    causa = opciones[sel]

    col1, col2 = st.columns(2)
    with col1:
        tipo_res = st.selectbox("Tipo de resolución",
                                list(TIPO_RES_LABEL.keys()),
                                format_func=lambda k: TIPO_RES_LABEL[k])
        fecha_inicio = st.date_input("Fecha de inicio", value=date.today())
    with col2:
        meses = st.selectbox("Duración (meses)", [3, 6, 9, 12], index=1)
        fecha_fin = fecha_inicio + timedelta(days=meses * 30)
        st.info(f"Vencimiento estimado: **{fecha_fin.strftime('%d/%m/%Y')}**")

    obs = st.text_area("Observaciones generales (opcional)", height=70)

    # Condiciones
    st.markdown("#### Condiciones a cumplir")
    st.caption("Agregue las condiciones impuestas en la resolución.")

    if "condiciones_temp" not in st.session_state:
        st.session_state.condiciones_temp = []

    # Precarga según tipo de infracción
    if st.button("📥 Pre-cargar condiciones estándar", key="preload_cond"):
        tipo_inf = causa.get("tipo_infraccion", "")
        cat      = TIPOS_INFRACCION.get(tipo_inf, {}).get("categoria", "Convivencia")
        if tipo_inf == "transito_alcoholemia":
            key = "transito_alcoholemia"
        elif cat == "Tránsito":
            key = "transito"
        elif cat == "Comercio":
            key = "comercio"
        elif cat == "Integridad":
            key = "integridad"
        elif cat == "Espacio Público":
            key = "espacio_publico"
        else:
            key = "convivencia"
        st.session_state.condiciones_temp = [
            {"tipo": "otro", "descripcion": c, "valor_objetivo": 0, "unidad": "", "fecha_limite": ""}
            for c in CONDICIONES_SUSPENSION.get(key, [])
        ]
        st.rerun()

    with st.expander("Agregar condición manual", expanded=len(st.session_state.condiciones_temp) == 0):
        tc = st.selectbox("Tipo", list(TIPO_COND_LABEL.keys()),
                          format_func=lambda k: TIPO_COND_LABEL[k], key="tc_tipo")
        td = st.text_input("Descripción de la condición", key="tc_desc")
        col_a, col_b, col_c = st.columns(3)
        with col_a:
            tv = st.number_input("Meta cuantitativa", min_value=0.0, step=1.0, key="tc_val",
                                 help="Ej: 40 (horas), 5000 (pesos). 0 si no aplica.")
        with col_b:
            tu = st.selectbox("Unidad", ["", "horas", "pesos", "controles", "sesiones"], key="tc_unidad")
        with col_c:
            tfl = st.date_input("Fecha límite (opcional)", value=None, key="tc_fl")

        if st.button("➕ Agregar condición", key="btn_add_cond"):
            if td.strip():
                st.session_state.condiciones_temp.append({
                    "tipo": tc, "descripcion": td.strip(),
                    "valor_objetivo": tv, "unidad": tu,
                    "fecha_limite": tfl.isoformat() if tfl else ""
                })
                st.rerun()
            else:
                st.warning("Ingrese una descripción.")

    if st.session_state.condiciones_temp:
        st.markdown("**Condiciones cargadas:**")
        for i, cond in enumerate(st.session_state.condiciones_temp):
            col_l, col_r = st.columns([5, 1])
            with col_l:
                meta = f" — Meta: {cond['valor_objetivo']} {cond['unidad']}" if cond["valor_objetivo"] > 0 else ""
                st.markdown(f"{i+1}. {TIPO_COND_LABEL.get(cond['tipo'], cond['tipo'])}: {cond['descripcion']}{meta}")
            with col_r:
                if st.button("✕", key=f"del_cond_{i}"):
                    st.session_state.condiciones_temp.pop(i)
                    st.rerun()

    st.divider()
    if st.button("💾 Registrar seguimiento", type="primary", key="btn_guardar_seg"):
        if not st.session_state.condiciones_temp:
            st.warning("Agregue al menos una condición.")
            return

        seg_id = db.crear_seguimiento(
            causa_id=causa["id"],
            tipo_resolucion=tipo_res,
            fecha_inicio=fecha_inicio.isoformat(),
            fecha_fin=fecha_fin.isoformat(),
            fiscal=fiscal,
            observaciones=obs
        )
        for cond in st.session_state.condiciones_temp:
            db.agregar_condicion(
                seguimiento_id=seg_id,
                tipo=cond["tipo"],
                descripcion=cond["descripcion"],
                valor_objetivo=cond["valor_objetivo"],
                unidad=cond["unidad"],
                fecha_limite=cond["fecha_limite"]
            )
        n_conds = len(st.session_state.condiciones_temp)
        st.success(f"✅ Seguimiento #{seg_id} registrado con {n_conds} condición(es).")
        st.balloons()
        # Offer immediate Acta de Compromiso download without waiting for rerun
        try:
            _caso_acta = {
                "numero": causa["numero"], "tipo": causa.get("tipo_infraccion",""),
                "imputado": causa.get("apellido_nombre",""), "dni": causa.get("persona_dni",""),
                "edad": causa.get("persona_edad", 0), "descripcion": causa.get("descripcion",""),
                "unidad": causa.get("unidad","norte"),
            }
            _clf_acta = {
                "carril": causa.get("carril","amarillo"), "accion": "", "score": 2,
                "fundamento": [], "icono": "", "descripcion": "", "color": "",
                "categoria": TIPOS_INFRACCION.get(causa.get("tipo_infraccion",""),{}).get("categoria",""),
            }
            _conds_acta = [c["descripcion"] for c in st.session_state.condiciones_temp] or \
                          [c["descripcion"] for c in db.get_condiciones(seg_id)]
            _pdf_acta = pdf_acta_compromiso(_caso_acta, _conds_acta, fiscal, _caso_acta["unidad"])
            st.download_button(
                "⬇️ Descargar Acta de Compromiso (PDF)",
                data=_pdf_acta,
                file_name=f"acta_compromiso_{causa['numero']}.pdf",
                mime="application/pdf",
                key="dl_acta_nueva",
                type="primary",
                use_container_width=True,
            )
        except Exception:
            pass
        st.session_state.condiciones_temp = []
        if st.button("Continuar", key="seg_continuar"):
            st.rerun()


# ── Panel principal de seguimientos ──────────────────────────────────────────

def _panel_seguimientos(fiscal):
    stats = db.stats_seguimiento()

    # Métricas rápidas
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total seguimientos", stats["total"])
    col2.metric("Activos", stats["activos"])
    col3.metric("Cumplidos", stats["cumplidos"])
    delta_venc = f"⚠️ {stats['vencidos']} vencidos" if stats["vencidos"] else None
    col4.metric("Incumplidos", stats["incumplidos"], delta=delta_venc, delta_color="inverse")

    # Global completion progress across all active seguimientos
    if stats["total"] > 0:
        _pct_total = round(stats["cumplidos"] * 100 / stats["total"])
        _estado_seg = "🟢 Buen ritmo de cumplimiento" if _pct_total >= 70 else \
                      ("🟡 Seguimiento en curso" if _pct_total >= 30 else "🔴 Bajo nivel de cumplimiento")
        st.progress(_pct_total / 100,
                    text=f"Cumplimiento global: {_pct_total}% ({stats['cumplidos']} de {stats['total']}) — {_estado_seg}")

    st.divider()

    # Filtros
    col_f1, col_f2, col_f3, col_f4 = st.columns([2, 1, 1, 1])
    with col_f1:
        filtro_estado = st.selectbox("Estado",
                                     ["Todos", "activo", "cumplido", "incumplido", "revocado"])
    with col_f2:
        filtro_unidad = st.selectbox("Unidad", ["Todas", "norte", "sur", "genero"])
    with col_f3:
        filtro_tipo_res = st.selectbox(
            "Tipo resolución",
            ["Todos", "suspension", "mediacion", "acuerdo"],
            format_func=lambda k: TIPO_RES_LABEL.get(k, k) if k != "Todos" else "Todos"
        )
    with col_f4:
        solo_vencen_pronto = st.checkbox("⏳ Próx. a vencer (≤30d)", key="seg_prox")

    estado_param = None if filtro_estado == "Todos" else filtro_estado
    unidad_param = None if filtro_unidad == "Todas" else filtro_unidad

    seguimientos = db.listar_seguimientos(estado=estado_param, unidad=unidad_param)
    # Apply tipo resolución filter in-memory
    if filtro_tipo_res != "Todos":
        seguimientos = [s for s in seguimientos if s.get("tipo_resolucion") == filtro_tipo_res]
    if solo_vencen_pronto:
        seguimientos = [
            s for s in seguimientos
            if (d := dias_restantes(s["fecha_fin"])) is not None and 0 <= d <= 30
        ]

    if not seguimientos:
        st.info("No hay seguimientos que coincidan con los filtros.")
        return

    for seg in seguimientos:
        dias = dias_restantes(seg["fecha_fin"])
        prog = db.progress_seguimiento(seg["id"])
        pct  = prog["pct"]
        # Fetch condiciones early so they are available for PDF generation below
        condiciones = db.get_condiciones(seg["id"])

        # Próximo control badge for expander header
        _pc_header = ""
        if seg.get("proximo_control") and seg.get("estado") == "activo":
            try:
                _pc_d = date.fromisoformat(seg["proximo_control"])
                _pc_diff = (_pc_d - date.today()).days
                if _pc_diff < 0:
                    _pc_header = f"  |  🔴 Control vencido {abs(_pc_diff)}d"
                elif _pc_diff == 0:
                    _pc_header = "  |  🔴 Control HOY"
                elif _pc_diff <= 3:
                    _pc_header = f"  |  🟠 Control en {_pc_diff}d"
                elif _pc_diff <= 7:
                    _pc_header = f"  |  🟡 Control en {_pc_diff}d"
            except Exception:
                pass

        with st.expander(
            f"{SEG_ESTADO_COLOR.get(seg['estado'], seg['estado'])} | "
            f"**{seg['apellido_nombre']}** — {seg['numero']} | "
            f"{TIPO_RES_LABEL.get(seg['tipo_resolucion'], seg['tipo_resolucion'])} | "
            f"{badge_dias(dias)}{_pc_header}"
        ):
            col_info, col_prog = st.columns([3, 2])
            with col_info:
                st.markdown(f"**Imputado/a:** {seg['apellido_nombre']} (DNI: {seg['dni']})")
                st.markdown(f"**Expediente:** {seg['numero']}  |  **Unidad:** {seg['unidad'].upper()}")
                st.markdown(f"**Período:** {seg['fecha_inicio']} → {seg['fecha_fin']}")
                st.markdown(f"**Fiscal:** {seg['fiscal']}")
                if seg["observaciones"]:
                    st.caption(seg["observaciones"])
                # Próximo control date picker (only for active seguimientos)
                if seg.get("estado") == "activo":
                    from datetime import date as _dt_sc
                    _pc_val = None
                    if seg.get("proximo_control"):
                        try:
                            _pc_val = _dt_sc.fromisoformat(seg["proximo_control"])
                        except Exception:
                            pass
                    _new_pc = st.date_input(
                        "📅 Próximo control",
                        value=_pc_val,
                        min_value=_dt_sc.today(),
                        key=f"s{seg['id']}_proximo_ctrl",
                        help="Fecha del próximo control de cumplimiento de condiciones",
                    )
                    if _new_pc and (_pc_val is None or _new_pc != _pc_val):
                        if st.button("Guardar fecha de control", key=f"s{seg['id']}_save_pc",
                                     use_container_width=True):
                            db.set_proximo_control(seg["id"], _new_pc.isoformat())
                            st.success(f"Próximo control agendado para {_new_pc.strftime('%d/%m/%Y')}")
                            st.rerun()
            with col_prog:
                st.metric("Condiciones cumplidas", f"{prog['cumplidas']}/{prog['total']}")
                st.progress(pct / 100, text=f"{pct}% completado")
                if prog["incumplidas"]:
                    st.error(f"⚠️ {prog['incumplidas']} condición(es) incumplida(s)")
                if prog["en_curso"]:
                    st.info(f"🔄 {prog['en_curso']} en curso")
                # PDF informe de seguimiento
                try:
                    _unidad_seg = seg.get("unidad", "norte")
                    _pdf_seg = pdf_informe_seguimiento(seg, condiciones, prog, fiscal, _unidad_seg)
                    st.download_button(
                        "⬇️ Informe PDF",
                        data=_pdf_seg,
                        file_name=f"informe_seg_{seg['numero']}.pdf",
                        mime="application/pdf",
                        key=f"dl_seg_{seg['id']}",
                        use_container_width=True,
                    )
                except Exception as _e_pdf:
                    st.caption(f"PDF no disponible: {_e_pdf}")

            # Detalle de condiciones
            st.markdown("##### Condiciones")
            sid = seg["id"]   # prefijo único por seguimiento para widget keys
            for ci, cond in enumerate(condiciones):
                acum = db.acumulado_condicion(cond["id"]) if cond["valor_objetivo"] > 0 else 0
                col_c1, col_c2, col_c3 = st.columns([4, 2, 2])
                with col_c1:
                    emoji = ESTADO_COLOR.get(cond["estado"], "⚪")
                    st.markdown(f"{emoji} {cond['descripcion']}")
                    if cond["valor_objetivo"] > 0:
                        pct_c = min(100, int(acum / cond["valor_objetivo"] * 100))
                        st.progress(pct_c / 100,
                                    text=f"{acum:.0f} / {cond['valor_objetivo']:.0f} {cond['unidad']}")
                with col_c2:
                    estados_list = ["pendiente", "en_curso", "cumplido", "incumplido"]
                    idx_actual = estados_list.index(cond["estado"]) if cond["estado"] in estados_list else 0
                    nuevo_estado = st.selectbox(
                        "Estado",
                        estados_list,
                        index=idx_actual,
                        key=f"s{sid}_est_{ci}"
                    )
                    if nuevo_estado != cond["estado"]:
                        if st.button("Aplicar", key=f"s{sid}_apply_{ci}"):
                            db.marcar_condicion(cond["id"], nuevo_estado)
                            st.rerun()
                with col_c3:
                    if cond["valor_objetivo"] > 0:
                        with st.popover("📝 Registrar avance", use_container_width=True):
                            val = st.number_input(
                                f"Avance ({cond['unidad']})",
                                min_value=0.0, step=1.0,
                                key=f"s{sid}_avval_{ci}"
                            )
                            obs_av = st.text_input("Observación", key=f"s{sid}_avobs_{ci}")
                            if st.button("Guardar avance", key=f"s{sid}_avsave_{ci}"):
                                db.registrar_avance(
                                    cond["id"],
                                    date.today().isoformat(),
                                    val, obs_av, fiscal
                                )
                                st.success("Avance registrado")
                                st.rerun()

                        # Mini historial
                        registros = db.get_registros(cond["id"])
                        if registros:
                            with st.expander(f"Historial ({len(registros)} registros)",
                                             expanded=False):
                                for r in registros:
                                    st.caption(f"{r['fecha']} | +{r['valor_parcial']:.0f} {cond['unidad']} — {r['observaciones']}")

            # Cierre del seguimiento
            if seg["estado"] == "activo":
                st.divider()

                # Auto-sugerencia de cierre cuando todas las condiciones están cumplidas
                if condiciones and prog["total"] > 0 and prog["cumplidas"] == prog["total"]:
                    st.success(
                        f"🎉 **¡Todas las condiciones cumplidas!** ({prog['total']}/{prog['total']})\n\n"
                        "Podés cerrar este seguimiento como **cumplido** y archivar la causa."
                    )
                elif condiciones and prog["incumplidas"] > 0:
                    st.error(
                        f"⚠️ **{prog['incumplidas']} condición(es) incumplida(s).** "
                        "Evaluá revocar o marcar el seguimiento como incumplido."
                    )

                col_btn1, col_btn2, col_btn3 = st.columns(3)
                with col_btn1:
                    _btn_ok_type = "primary" if (prog["total"] > 0 and prog["cumplidas"] == prog["total"]) else "secondary"
                    if st.button("✅ Marcar cumplido", key=f"seg_ok_{seg['id']}",
                                 type=_btn_ok_type):
                        db.cerrar_seguimiento(seg["id"], "cumplido")
                        db.avanzar_estado(seg["causa_id"], "archivada", fiscal,
                                          "Seguimiento completado satisfactoriamente")
                        db.agregar_nota_causa(
                            seg["causa_id"],
                            f"SEGUIMIENTO CERRADO: Todas las condiciones del período "
                            f"{seg['fecha_inicio']} → {seg['fecha_fin']} fueron cumplidas. "
                            "Causa archivada.",
                            fiscal,
                        )
                        st.success("Seguimiento cerrado como cumplido. Causa archivada.")
                        st.rerun()
                with col_btn2:
                    if st.button("❌ Marcar incumplido", key=f"seg_inc_{seg['id']}"):
                        db.cerrar_seguimiento(seg["id"], "incumplido")
                        db.agregar_nota_causa(
                            seg["causa_id"],
                            f"SEGUIMIENTO INCUMPLIDO: Se cierra el período "
                            f"{seg['fecha_inicio']} → {seg['fecha_fin']} por incumplimiento. "
                            "La causa puede retomar proceso contravencional pleno.",
                            fiscal,
                        )
                        st.error("Seguimiento marcado como incumplido. La causa puede retomar proceso.")
                        st.rerun()
                with col_btn3:
                    if st.button("⚫ Revocar", key=f"seg_rev_{seg['id']}"):
                        db.cerrar_seguimiento(seg["id"], "revocado")
                        db.agregar_nota_causa(
                            seg["causa_id"],
                            f"SEGUIMIENTO REVOCADO: El período de prueba fue revocado por disposición fiscal.",
                            fiscal,
                        )
                        st.warning("Seguimiento revocado.")
                        st.rerun()


# ── Punto de entrada público ──────────────────────────────────────────────────

def render_tab_seguimiento(fiscal):
    st.header("📋 Seguimiento Post-Resolución")
    st.caption("Control de cumplimiento de condiciones impuestas en suspensiones, mediaciones y acuerdos.")

    modo = st.radio(
        "Vista",
        ["Panel de seguimientos activos", "Registrar nuevo seguimiento"],
        horizontal=True, label_visibility="collapsed"
    )

    st.divider()

    if modo == "Registrar nuevo seguimiento":
        _form_nuevo_seguimiento(fiscal)
    else:
        _panel_seguimientos(fiscal)
