"""
SIATC — Sistema Inteligente de Apoyo al Trabajo Contravencional
Ministerio Público Fiscal · Córdoba
"""

import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
from datetime import datetime
import random

from data_cordoba import TIPOS_INFRACCION, UNIDADES, CASOS_DEMO
from classifier import clasificar_caso, tiempo_estimado_resolucion
from document_gen import (
    generar_dictamen_mediacion,
    generar_dictamen_suspension,
    generar_citacion,
    generar_resumen_ejecutivo,
)
from pdf_gen import generar_pdf, pdf_reporte_diario
from database import (
    init_db, buscar_persona_por_dni, contar_antecedentes,
    guardar_causa, avanzar_estado, listar_causas, get_causa, get_timeline,
    guardar_documento, listar_documentos, stats_generales, causas_por_tipo,
    historial_persona, upsert_persona, ESTADOS, ESTADOS_LABEL,
    listar_seguimientos, stats_seguimiento, causas_por_mes, causas_por_fiscal,
    get_seguimiento_por_causa, get_condiciones, stats_tiempos_resolucion,
    causas_inactivas,
)
from seguimiento_tab import render_tab_seguimiento
from agenda_tab import render_tab_agenda
from perfil_tab import render_buscador_perfil
from demo_seed import poblar, ya_poblado
from bienvenida import mostrar_si_primera_vez
from export_excel import causas_a_excel, seguimientos_a_excel, audiencias_a_excel
from database import (
    audiencias_hoy, stats_audiencias, listar_audiencias,
    crear_audiencia, actualizar_estado_audiencia,
    perfil_persona, listar_personas,
)

# ── Init ───────────────────────────────────────────────────────────────────────
init_db()
if not ya_poblado():
    poblar()

st.set_page_config(
    page_title="SIATC — Sistema Inteligente Contravencional",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
.main-header {
    background: linear-gradient(90deg,#1a2f5e 0%,#2e5090 100%);
    padding:1.2rem 2rem; border-radius:8px; color:white; margin-bottom:1.2rem;
}
.carril-verde    {background:#d4edda;border-left:5px solid #28a745;padding:1rem;border-radius:4px;margin:0.5rem 0}
.carril-amarillo {background:#fff3cd;border-left:5px solid #ffc107;padding:1rem;border-radius:4px;margin:0.5rem 0}
.carril-rojo     {background:#f8d7da;border-left:5px solid #dc3545;padding:1rem;border-radius:4px;margin:0.5rem 0}
.timeline-item   {border-left:3px solid #2e5090;padding:0.4rem 0.8rem;margin:0.3rem 0;background:#f8f9fa;border-radius:0 4px 4px 0}
.doc-preview     {background:#fafafa;border:1px solid #ccc;border-radius:4px;padding:1.2rem;
                  font-family:'Courier New',monospace;font-size:0.76rem;white-space:pre-wrap;
                  max-height:420px;overflow-y:auto}
.antec-badge     {background:#dc3545;color:white;border-radius:12px;padding:2px 10px;font-size:0.8rem;font-weight:bold}
.antec-ok        {background:#28a745;color:white;border-radius:12px;padding:2px 10px;font-size:0.8rem}
</style>
""", unsafe_allow_html=True)

# ── Sidebar ────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### ⚖️ SIATC")
    fiscal_nombre = st.text_input("Fiscal / Ayudante", value="Dra. Ana Pérez")
    unidad_key = st.selectbox(
        "Unidad Contravencional",
        options=list(UNIDADES.keys()),
        format_func=lambda k: {"norte":"Norte","sur":"Sur","genero":"Género"}[k],
    )
    st.markdown("---")
    stats = stats_generales()
    st.metric("Causas totales", stats["total"])
    col1, col2 = st.columns(2)
    col1.metric("🟢", stats["por_carril"].get("verde", 0))
    col2.metric("🟡", stats["por_carril"].get("amarillo", 0))
    col1.metric("🔴", stats["por_carril"].get("rojo", 0))
    col2.metric("👤 Personas", stats["personas"])

    # ── Alertas de seguimiento ─────────────────────────────────────────────
    st.markdown("---")
    seg_stats = stats_seguimiento()
    if seg_stats["total"] > 0:
        st.markdown("**🔔 Seguimientos activos**")
        col_s1, col_s2 = st.columns(2)
        col_s1.metric("Activos", seg_stats["activos"])
        col_s2.metric("Cumplidos", seg_stats["cumplidos"])
        if seg_stats["vencidos"] > 0:
            st.error(f"⚠️ {seg_stats['vencidos']} seguimiento(s) vencido(s) sin cierre")
        if seg_stats["incumplidos"] > 0:
            st.warning(f"❌ {seg_stats['incumplidos']} incumplido(s)")

        # Próximos vencimientos
        from datetime import date as _date
        activos = listar_seguimientos(estado="activo")
        proximos = []
        for s in activos:
            try:
                fin = datetime.strptime(s["fecha_fin"], "%Y-%m-%d").date()
                dias = (fin - _date.today()).days
                if dias <= 30:
                    proximos.append((dias, s))
            except Exception:
                pass
        proximos.sort(key=lambda x: x[0])
        if proximos:
            st.markdown("**⏳ Vencen pronto:**")
            for dias, s in proximos[:4]:
                if dias < 0:
                    st.caption(f"🔴 {s['apellido_nombre'].split(',')[0]} — vencido hace {abs(dias)}d")
                elif dias == 0:
                    st.caption(f"🔴 {s['apellido_nombre'].split(',')[0]} — vence HOY")
                elif dias <= 7:
                    st.caption(f"🟠 {s['apellido_nombre'].split(',')[0]} — {dias}d")
                else:
                    st.caption(f"🟡 {s['apellido_nombre'].split(',')[0]} — {dias}d")

    # ── Audiencias del día ─────────────────────────────────────────────────
    hoy_auds = audiencias_hoy()
    if hoy_auds:
        st.markdown("---")
        st.markdown(f"**📅 Audiencias hoy ({len(hoy_auds)})**")
        for a in hoy_auds:
            st.caption(f"🔵 {a['hora']} — {a['apellido_nombre'].split(',')[0]} ({a['numero']})")

    # Próximas audiencias esta semana
    aud_s = stats_audiencias()
    if aud_s["proximas"] > 0:
        st.markdown("---")
        st.markdown(f"**📆 Esta semana: {aud_s['proximas']} audiencia(s)**")

    # Búsqueda rápida
    st.markdown("---")
    st.markdown("**🔎 Búsqueda rápida**")
    _q_rapid = st.text_input("Causa o DNI", placeholder="Ej: García o UCN-00001",
                             key="busqueda", label_visibility="collapsed")
    if _q_rapid:
        st.session_state["busqueda_rapida_causas"] = _q_rapid

    st.markdown("---")
    st.caption(
        f"v1.0-demo · {datetime.now().strftime('%d/%m/%Y')}\n\n"
        "[GitHub](https://github.com/juanfiosa/siatc-cordoba)"
    )

# ── Bienvenida (primera vez por sesión) ────────────────────────────────────────
if not mostrar_si_primera_vez():
    st.stop()

# ── Header ─────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="main-header">
<h2 style="margin:0">⚖️ SIATC — Sistema Inteligente de Apoyo al Trabajo Contravencional</h2>
<p style="margin:0.3rem 0 0 0;opacity:0.85">
Ministerio Público Fiscal · Provincia de Córdoba &nbsp;|&nbsp; Código de Convivencia Ciudadana — Ley N° 10.326
</p>
</div>
""", unsafe_allow_html=True)

# ── Alertas críticas ──────────────────────────────────────────────────────────
_alertas = []
from datetime import date as _date_now
_hoy_str = _date_now.today().isoformat()

# Audiencias de hoy sin gestionar
_aud_hoy_count = stats_audiencias()["hoy"]
if _aud_hoy_count:
    _alertas.append(f"📅 **{_aud_hoy_count} audiencia(s) HOY** — revisá la pestaña Agenda")

# Seguimientos vencidos sin cierre
_venc = stats_seguimiento()["vencidos"]
if _venc:
    _alertas.append(f"⚠️ **{_venc} seguimiento(s) vencido(s)** sin cierre formal")

# Causas incumplidas
_inc = stats_seguimiento()["incumplidos"]
if _inc:
    _alertas.append(f"❌ **{_inc} seguimiento(s) incumplido(s)** — evaluar revocación")

# Ausencias recientes (últimos 7 días)
from database import listar_audiencias as _la_alerts
from datetime import timedelta as _tda
_hace7 = (_date_now.today() - _tda(days=7)).isoformat()
_ausentes_rec = len([a for a in _la_alerts(desde=_hace7, hasta=_hoy_str) if a.get("estado") == "ausente"])
if _ausentes_rec:
    _alertas.append(f"🚨 **{_ausentes_rec} incomparecencia(s)** en los últimos 7 días")

if _alertas:
    with st.container():
        for alerta in _alertas:
            st.warning(alerta)

# ── Tabs ───────────────────────────────────────────────────────────────────────
tab_nuevo, tab_causas, tab_demo, tab_seg, tab_agenda, tab_perfil, tab_panel = st.tabs([
    "📋 Nuevo Caso", "📂 Gestión de Causas", "🗂️ Casos Demo",
    "🔍 Seguimiento", "📅 Agenda", "👤 Perfil", "📊 Panel de Control"
])


# ══════════════════════════════════════════════════════════════════════════════
# TAB 1 — NUEVO CASO
# ══════════════════════════════════════════════════════════════════════════════
with tab_nuevo:
    st.subheader("Ingreso de Caso Contravencional")
    col_izq, col_der = st.columns([1, 1], gap="large")

    with col_izq:
        st.markdown("#### Datos del imputado/a")

        dni_input = st.text_input("D.N.I.", placeholder="Ej: 38.421.667", key="dni_nuevo")

        # Lookup automático por DNI
        persona_encontrada = None
        antecedentes_db = 0
        if dni_input and len(dni_input.replace(".", "").replace("-", "")) >= 7:
            persona_encontrada = buscar_persona_por_dni(dni_input)
            if persona_encontrada:
                antecedentes_db = contar_antecedentes(persona_encontrada["id"])
                st.success(f"✅ Persona encontrada en el sistema")
                historial = historial_persona(persona_encontrada["id"])
                if antecedentes_db > 0:
                    st.markdown(
                        f'<span class="antec-badge">⚠️ {antecedentes_db} antecedente{"s" if antecedentes_db>1 else ""} en el sistema</span>',
                        unsafe_allow_html=True
                    )
                else:
                    st.markdown('<span class="antec-ok">✔ Sin antecedentes</span>', unsafe_allow_html=True)

        nombre_default = persona_encontrada["apellido_nombre"] if persona_encontrada else ""
        edad_default   = persona_encontrada["edad"]             if persona_encontrada else 30

        nombre = st.text_input("Apellido y nombre", value=nombre_default, placeholder="Ej: García, Lucas Damián")
        col_e, col_d = st.columns(2)
        with col_e:
            edad = st.number_input("Edad", min_value=16, max_value=99, value=edad_default)
        with col_d:
            domicilio = st.text_input("Domicilio", value=persona_encontrada.get("domicilio","") if persona_encontrada else "")

        # Antecedentes: DB tiene prioridad, manual como fallback
        if persona_encontrada:
            antecedentes = antecedentes_db
            st.info(f"Antecedentes tomados del sistema: **{antecedentes}**")
        else:
            antecedentes = st.select_slider(
                "Antecedentes (carga manual — se actualizará con el sistema)",
                options=[0,1,2,3,4], value=0,
                format_func=lambda x: "Ninguno" if x==0 else f"{x} antecedente{'s' if x>1 else ''}",
            )

        st.markdown("#### Datos del hecho")
        tipo_opciones = {k: v["label"]+f"  ({v['categoria']})" for k,v in TIPOS_INFRACCION.items()}
        tipo = st.selectbox("Tipo de infracción", options=list(tipo_opciones.keys()),
                            format_func=lambda k: tipo_opciones[k])
        descripcion = st.text_area("Descripción (según parte policial)", height=90,
                                   placeholder="Descripción breve del hecho...")
        col_v, col_l, col_r = st.columns(3)
        victima    = col_v.checkbox("Víctima identificada")
        lesiones   = col_l.checkbox("Lesiones físicas")
        resistencia= col_r.checkbox("Resistencia a autoridad")

    with col_der:
        st.markdown("#### Clasificación automática")

        if nombre and dni_input and tipo:
            caso = {
                "numero": None,          # se asigna al guardar
                "tipo": tipo, "imputado": nombre, "dni": dni_input,
                "edad": edad, "antecedentes": antecedentes,
                "descripcion": descripcion, "unidad": unidad_key,
                "domicilio": domicilio,
                "victima": victima, "lesiones": lesiones, "resistencia": resistencia,
            }
            clf = clasificar_caso(tipo, antecedentes, victima, lesiones, resistencia)
            t   = tiempo_estimado_resolucion(clf["carril"])

            st.markdown(f"""
<div class="carril-{clf['carril']}">
<h3 style="margin:0">{clf['icono']} CARRIL {clf['carril'].upper()} — {clf['accion']}</h3>
<p style="margin:0.4rem 0 0 0">{clf['descripcion']}</p>
</div>""", unsafe_allow_html=True)

            col_a, col_b, col_c = st.columns(3)
            col_a.metric("Proceso actual",  f"~{t['actual_dias']} días")
            col_b.metric("Con SIATC",       f"~{t['con_sistema_dias']} días",
                         delta=f"-{t['actual_dias']-t['con_sistema_dias']} días", delta_color="inverse")
            col_c.metric("Reducción", f"{round((1-t['con_sistema_dias']/t['actual_dias'])*100)}%")

            st.markdown("##### Fundamentos")
            for f in clf["fundamento"]:
                st.markdown(f"• {f}")

            # Casos similares (misma infracción, en el sistema)
            _similares = listar_causas(limit=100)
            _similares = [c for c in _similares if c.get("tipo_infraccion") == tipo][:4]
            if _similares:
                with st.expander(f"📂 {len(_similares)} caso(s) similar(es) en el sistema"):
                    for sc in _similares:
                        _sc_inf = TIPOS_INFRACCION.get(sc["tipo_infraccion"], {})
                        _ic     = {"verde":"🟢","amarillo":"🟡","rojo":"🔴"}.get(sc.get("carril",""),"⚪")
                        _est    = ESTADOS_LABEL.get(sc["estado"], sc["estado"])
                        st.markdown(
                            f"**{sc['numero']}** — {sc.get('apellido_nombre','').split(',')[0]} &nbsp; "
                            f"{_ic} {sc.get('carril','').capitalize()} &nbsp;|&nbsp; {_est}"
                        )

            st.markdown("---")

            # Documento
            if clf["carril"] == "verde":
                doc_ops = ["Dictamen de derivación a mediación", "Cédula de citación a mediación"]
            elif clf["carril"] == "amarillo":
                doc_ops = ["Dictamen de suspensión del proceso a prueba", "Cédula de citación", "Dictamen de derivación a mediación"]
            else:
                doc_ops = ["Cédula de citación a audiencia", "Resumen ejecutivo del caso"]
            doc_sel = st.selectbox("Documento a generar", doc_ops)

            col_btn1, col_btn2 = st.columns(2)
            gen_doc = col_btn1.button("⚡ Generar documento", type="primary", use_container_width=True)
            guardar = col_btn2.button("💾 Guardar en sistema", use_container_width=True)

            if guardar:
                causa_id = guardar_causa(caso, clf, fiscal_nombre)
                c_saved  = get_causa(causa_id)
                numero_guardado = c_saved["numero"] if c_saved else f"ID#{causa_id}"
                st.success(
                    f"✅ Causa **{numero_guardado}** guardada — "
                    f"Carril {clf['carril'].upper()} | Ir a **📂 Gestión de Causas** para ver el expediente."
                )
                st.balloons()
                st.rerun()

            if gen_doc or st.session_state.get("doc_generado_nuevo"):
                # Generamos el número provisional para el documento
                numero_prov = f"BORRADOR-{datetime.now().strftime('%H%M%S')}"
                caso_doc = {**caso, "numero": numero_prov}
                if doc_sel == "Dictamen de derivación a mediación":
                    doc = generar_dictamen_mediacion(caso_doc, clf, fiscal_nombre, unidad_key)
                elif doc_sel == "Dictamen de suspensión del proceso a prueba":
                    doc = generar_dictamen_suspension(caso_doc, clf, fiscal_nombre, unidad_key)
                elif "citación" in doc_sel.lower():
                    motivo = "mediacion" if "mediación" in doc_sel else "audiencia"
                    doc = generar_citacion(caso_doc, fiscal_nombre, unidad_key, motivo)
                else:
                    doc = generar_resumen_ejecutivo(caso_doc, clf)

                st.markdown("##### Vista previa")
                st.markdown(f"<div class='doc-preview'>{doc}</div>", unsafe_allow_html=True)
                col_pdf, col_txt = st.columns(2)
                pdf_bytes = generar_pdf(doc_sel, caso_doc, clf, fiscal_nombre, unidad_key)
                col_pdf.download_button(
                    "⬇️ Descargar PDF",
                    data=pdf_bytes,
                    file_name=f"borrador_{doc_sel[:20].replace(' ','_')}.pdf",
                    mime="application/pdf",
                    use_container_width=True,
                    type="primary",
                )
                col_txt.download_button(
                    "📄 Descargar .txt",
                    data=doc,
                    file_name=f"borrador_{doc_sel[:20].replace(' ','_')}.txt",
                    mime="text/plain",
                    use_container_width=True,
                )
        else:
            st.info("Completá DNI, nombre y tipo de infracción para ver la clasificación.")


# ══════════════════════════════════════════════════════════════════════════════
# TAB 2 — GESTIÓN DE CAUSAS
# ══════════════════════════════════════════════════════════════════════════════
with tab_causas:
    st.subheader("Gestión de Causas")
    if st.session_state.pop("goto_perfil", False):
        st.info("👤 El perfil del imputado/a se muestra en la pestaña **Perfil**.")

    # Filtros
    col_f1, col_f2, col_f3, col_f4 = st.columns([2,1,1,1])
    _default_busqueda = st.session_state.pop("busqueda_rapida_causas", "")
    busqueda  = col_f1.text_input("Buscar por nombre, DNI o N° de causa",
                                   value=_default_busqueda,
                                   placeholder="Buscar...", label_visibility="collapsed")
    filtro_estado = col_f2.selectbox("Estado", ["Todos"] + ESTADOS,
                                      format_func=lambda x: "Todos los estados" if x=="Todos" else ESTADOS_LABEL.get(x,x))
    filtro_carril = col_f3.selectbox("Carril", ["Todos","verde","amarillo","rojo"],
                                      format_func=lambda x: {"Todos":"Todos","verde":"🟢 Verde","amarillo":"🟡 Amarillo","rojo":"🔴 Rojo"}[x])
    filtro_unidad = col_f4.selectbox("Unidad", ["Todas","norte","sur","genero"],
                                      format_func=lambda x: {"Todas":"Todas","norte":"Norte","sur":"Sur","genero":"Género"}[x])

    causas = listar_causas(
        estado   = None if filtro_estado=="Todos"  else filtro_estado,
        carril   = None if filtro_carril=="Todos"  else filtro_carril,
        unidad   = None if filtro_unidad=="Todas"  else filtro_unidad,
        busqueda = busqueda or None,
    )

    if not causas:
        st.info("No hay causas que coincidan con los filtros. Ingresá un caso nuevo en la pestaña 📋 o cargá los casos demo.")
    else:
        from collections import Counter as _Cnt
        _cnt = _Cnt(c.get("carril","") for c in causas)
        _cnt_est = _Cnt(c.get("estado","") for c in causas)
        st.markdown(
            f"**{len(causas)} causa{'s' if len(causas)!=1 else ''}** &nbsp;—&nbsp; "
            f"🟢 {_cnt.get('verde',0)} &nbsp; 🟡 {_cnt.get('amarillo',0)} &nbsp; 🔴 {_cnt.get('rojo',0)} "
            f"&nbsp;|&nbsp; "
            f"Ingresadas: {_cnt_est.get('ingresada',0)} &nbsp; "
            f"Notificadas: {_cnt_est.get('notificada',0)} &nbsp; "
            f"Resueltas: {_cnt_est.get('resuelta',0)}",
        )

        # Selector de causa para ver detalle
        causa_sel_id = st.session_state.get("causa_sel_id")

        for c in causas:
            carril_icon = {"verde":"🟢","amarillo":"🟡","rojo":"🔴"}.get(c.get("carril",""),"⚪")
            estado_label = ESTADOS_LABEL.get(c["estado"], c["estado"])
            infraccion_label = TIPOS_INFRACCION.get(c["tipo_infraccion"],{}).get("label", c["tipo_infraccion"])
            unidad_label = {"norte":"Norte","sur":"Sur","genero":"Género"}.get(c.get("unidad",""),"")

            with st.expander(
                f"{carril_icon} **{c['numero']}** — {c['apellido_nombre']}  |  {infraccion_label}  |  {estado_label}",
                expanded=(causa_sel_id == c["id"])
            ):
                col_info, col_acciones = st.columns([2,1])

                with col_info:
                    _col_dni, _col_pfil = st.columns([3, 1])
                    _col_dni.markdown(f"**DNI:** {c['persona_dni']}  |  **Unidad:** {unidad_label}  |  **Fiscal:** {c.get('fiscal_asignado','—')}")
                    if _col_pfil.button("👤 Ver perfil", key=f"pfil_{c['id']}", use_container_width=True):
                        st.session_state["perfil_busqueda"] = c["persona_dni"]
                        st.session_state["goto_perfil"] = True
                    st.markdown(f"**Descripción:** {c.get('descripcion') or '—'}")
                    st.markdown(f"**Ingresada:** {c['created_at']}")

                    # Timeline
                    timeline = get_timeline(c["id"])
                    if timeline:
                        st.markdown("**Historial de estados:**")
                        for t in timeline:
                            ant = ESTADOS_LABEL.get(t["estado_anterior"],"—") if t["estado_anterior"] else "—"
                            nvo = ESTADOS_LABEL.get(t["estado_nuevo"], t["estado_nuevo"])
                            obs = f" — {t['observaciones']}" if t.get("observaciones") else ""
                            st.markdown(
                                f"<div class='timeline-item'>{t['created_at'][:16]}  →  {ant} ➜ {nvo}{obs}</div>",
                                unsafe_allow_html=True
                            )

                    # Documentos previos
                    docs = listar_documentos(c["id"])
                    if docs:
                        st.markdown(f"**Documentos generados ({len(docs)}):**")
                        for d in docs:
                            with st.expander(f"📄 {d['tipo_documento']} — {d['created_at'][:16]}"):
                                st.markdown(f"<div class='doc-preview'>{d['contenido']}</div>", unsafe_allow_html=True)
                                _caso_d = {"numero": c["numero"], "tipo": c["tipo_infraccion"],
                                           "imputado": c["apellido_nombre"], "dni": c["persona_dni"],
                                           "edad": c.get("persona_edad", 0), "domicilio": ""}
                                _clf_d  = {"carril": c.get("carril","amarillo"), "score": c.get("score_clasificacion",2),
                                           "categoria": TIPOS_INFRACCION.get(c["tipo_infraccion"],{}).get("categoria",""),
                                           "accion": "", "fundamento": [], "icono": "", "descripcion": "", "color": ""}
                                try:
                                    _pdf = generar_pdf(d["tipo_documento"], _caso_d, _clf_d, d.get("generado_por",""), c.get("unidad","norte"))
                                    st.download_button("⬇️ Descargar PDF", data=_pdf,
                                                       file_name=f"{c['numero']}_{d['tipo_documento']}.pdf",
                                                       mime="application/pdf", key=f"dl_pdf_{d['id']}",
                                                       type="primary")
                                except Exception:
                                    st.download_button("⬇️ Descargar .txt", data=d["contenido"],
                                                       file_name=f"{c['numero']}_{d['tipo_documento']}.txt",
                                                       mime="text/plain", key=f"dl_doc_{d['id']}")

                with col_acciones:
                    st.markdown("**Avanzar estado:**")
                    idx_actual = ESTADOS.index(c["estado"]) if c["estado"] in ESTADOS else 0
                    estados_posibles = ESTADOS[idx_actual+1:] if idx_actual < len(ESTADOS)-1 else []

                    if estados_posibles:
                        nuevo_estado = st.selectbox(
                            "Nuevo estado", estados_posibles,
                            format_func=lambda x: ESTADOS_LABEL.get(x, x),
                            key=f"est_{c['id']}"
                        )
                        obs_estado = st.text_input("Observaciones", key=f"obs_{c['id']}", placeholder="Opcional")
                        if st.button("Actualizar estado", key=f"upd_{c['id']}", use_container_width=True):
                            avanzar_estado(c["id"], nuevo_estado, fiscal_nombre, obs_estado)
                            st.success(f"Estado actualizado a {ESTADOS_LABEL[nuevo_estado]}")
                            st.rerun()
                    else:
                        st.info("Causa archivada")

                    st.markdown("---")
                    st.markdown("**Programar audiencia:**")
                    with st.popover("📅 Nueva audiencia para esta causa", use_container_width=True):
                        from datetime import date as _dq, timedelta as _tq
                        from datetime import datetime as _dtq
                        _tipo_aud = st.selectbox(
                            "Tipo", ["audiencia","mediacion","acta_compromiso","control_seg"],
                            format_func=lambda k: {"audiencia":"Audiencia contravencional",
                                "mediacion":"Audiencia de mediación",
                                "acta_compromiso":"Suscripción acta de compromiso",
                                "control_seg":"Control de seguimiento"}.get(k,k),
                            key=f"qa_tipo_{c['id']}"
                        )
                        _qa_col1, _qa_col2 = st.columns(2)
                        with _qa_col1:
                            _fecha_aud = st.date_input("Fecha",
                                value=_dq.today() + _tq(days=5),
                                key=f"qa_fecha_{c['id']}")
                        with _qa_col2:
                            _hora_aud = st.time_input("Hora",
                                value=_dtq.strptime("09:00","%H:%M").time(),
                                key=f"qa_hora_{c['id']}")
                        from data_cordoba import UNIDADES as _UN
                        _lugar_aud = _UN.get(c.get("unidad","norte"), "Sede de la Unidad")
                        if st.button("Agendar", key=f"qa_btn_{c['id']}", type="primary"):
                            crear_audiencia(c["id"], _tipo_aud,
                                           _fecha_aud.isoformat(),
                                           _hora_aud.strftime("%H:%M"),
                                           _lugar_aud, "")
                            st.success(f"Audiencia agendada para {_fecha_aud.strftime('%d/%m/%Y')} {_hora_aud.strftime('%H:%M')}")
                            st.rerun()

                    st.markdown("---")
                    st.markdown("**Generar documento:**")

                    clf_stored = {
                        "carril": c.get("carril","amarillo"),
                        "accion": c.get("accion",""),
                        "fundamento": [],
                        "score": c.get("score_clasificacion",2),
                        "categoria": TIPOS_INFRACCION.get(c["tipo_infraccion"],{}).get("categoria",""),
                        "icono": {"verde":"🟢","amarillo":"🟡","rojo":"🔴"}.get(c.get("carril",""),"⚪"),
                        "descripcion": "",
                        "color": "",
                    }
                    caso_stored = {
                        "numero": c["numero"],
                        "tipo": c["tipo_infraccion"],
                        "imputado": c["apellido_nombre"],
                        "dni": c["persona_dni"],
                        "edad": c.get("persona_edad", 0),
                        "antecedentes": 0,
                        "descripcion": c.get("descripcion",""),
                        "unidad": c.get("unidad","norte"),
                    }
                    if c.get("carril") == "verde":
                        doc_opts_causa = ["Dictamen de derivación a mediación", "Cédula de citación a mediación"]
                    elif c.get("estado") in ("resuelta", "archivada"):
                        doc_opts_causa = ["Dictamen de suspensión a prueba", "Acta de compromiso",
                                          "Informe de incumplimiento", "Cédula de citación", "Resumen ejecutivo"]
                    else:
                        doc_opts_causa = ["Dictamen de suspensión a prueba", "Cédula de citación", "Resumen ejecutivo"]
                    doc_tipo = st.selectbox("Tipo", doc_opts_causa, key=f"dopt_{c['id']}", label_visibility="collapsed")
                    if st.button("Generar y guardar", key=f"gendoc_{c['id']}", use_container_width=True):
                        _needs_rerun = True
                        if doc_tipo == "Dictamen de derivación a mediación":
                            doc_txt = generar_dictamen_mediacion(caso_stored, clf_stored, fiscal_nombre, caso_stored["unidad"])
                        elif "suspensión" in doc_tipo or "prueba" in doc_tipo:
                            doc_txt = generar_dictamen_suspension(caso_stored, clf_stored, fiscal_nombre, caso_stored["unidad"])
                        elif "Acta de compromiso" in doc_tipo:
                            from data_cordoba import CONDICIONES_SUSPENSION
                            cat = TIPOS_INFRACCION.get(caso_stored["tipo"], {}).get("categoria", "Convivencia")
                            key_c = "transito_alcoholemia" if caso_stored["tipo"] == "transito_alcoholemia" else \
                                    ("transito" if cat == "Tránsito" else ("comercio" if cat == "Comercio" else
                                    ("integridad" if cat == "Integridad" else
                                    ("espacio_publico" if cat == "Espacio Público" else "convivencia"))))
                            conds_list = CONDICIONES_SUSPENSION.get(key_c, [])
                            pdf_bytes = generar_pdf("acta compromiso", caso_stored, {"condiciones": conds_list}, fiscal_nombre, caso_stored["unidad"])
                            st.session_state[f"_pdf_acta_{c['id']}"] = pdf_bytes
                            doc_txt = f"Acta de compromiso — {caso_stored['imputado']} — {c['numero']}"
                            _needs_rerun = False   # show download before rerun
                        elif "Informe de incumplimiento" in doc_tipo:
                            seg_info = get_seguimiento_por_causa(c["id"]) or {}
                            conds_inc = [cd for cd in get_condiciones(seg_info.get("id", 0))
                                         if cd["estado"] == "incumplido"] if seg_info else []
                            pdf_bytes = generar_pdf("informe incumplimiento", caso_stored,
                                                    {"seguimiento": seg_info, "condiciones_inc": conds_inc},
                                                    fiscal_nombre, caso_stored["unidad"])
                            st.session_state[f"_pdf_inf_{c['id']}"] = pdf_bytes
                            doc_txt = f"Informe de incumplimiento — {caso_stored['imputado']} — {c['numero']}"
                            _needs_rerun = False
                        elif "citación" in doc_tipo:
                            doc_txt = generar_citacion(caso_stored, fiscal_nombre, caso_stored["unidad"])
                        else:
                            doc_txt = generar_resumen_ejecutivo(caso_stored, clf_stored)
                        guardar_documento(c["id"], doc_tipo, doc_txt, fiscal_nombre)
                        st.success("Documento guardado en la causa")
                        if _needs_rerun:
                            st.rerun()

                    # Persistent download buttons for PDF-only docs
                    if st.session_state.get(f"_pdf_acta_{c['id']}"):
                        st.download_button("⬇️ Descargar Acta PDF",
                            data=st.session_state[f"_pdf_acta_{c['id']}"],
                            file_name=f"{c['numero']}_acta_compromiso.pdf",
                            mime="application/pdf", key=f"dl_acta_{c['id']}", type="primary")
                    if st.session_state.get(f"_pdf_inf_{c['id']}"):
                        st.download_button("⬇️ Descargar Informe PDF",
                            data=st.session_state[f"_pdf_inf_{c['id']}"],
                            file_name=f"{c['numero']}_informe_incumplimiento.pdf",
                            mime="application/pdf", key=f"dl_inf_{c['id']}", type="primary")


# ══════════════════════════════════════════════════════════════════════════════
# TAB 3 — CASOS DEMO
# ══════════════════════════════════════════════════════════════════════════════
with tab_demo:
    st.subheader("Casos de demostración")
    st.markdown("Casos representativos de una semana típica. Cargalos al sistema con un clic.")

    for i, cd in enumerate(CASOS_DEMO):
        inf  = TIPOS_INFRACCION.get(cd["tipo"], {})
        clf  = clasificar_caso(cd["tipo"], cd["antecedentes"], False)

        with st.expander(
            f"{clf['icono']} {cd['numero']} — {cd['imputado']}  |  {inf.get('label','')}",
            expanded=(i==0)
        ):
            col1, col2 = st.columns([3,1])
            with col1:
                st.markdown(f"**Descripción:** {cd['descripcion']}")
                st.markdown(f"**Antecedentes previos:** {cd['antecedentes']}")
                st.markdown(f"**Unidad:** {UNIDADES[cd['unidad']]}")
            with col2:
                st.markdown(f"""<div class="carril-{clf['carril']}">
<strong>{clf['icono']} {clf['accion']}</strong></div>""", unsafe_allow_html=True)

            col_b1, col_b2, col_b3 = st.columns(3)

            if col_b1.button("📥 Cargar al sistema", key=f"carga_{i}", use_container_width=True):
                causa_id = guardar_causa(
                    {**cd, "victima": False, "lesiones": False, "resistencia": False, "domicilio": ""},
                    clf, fiscal_nombre
                )
                st.success(f"Causa cargada — ID #{causa_id}. Verla en 📂 Gestión de Causas.")
                st.rerun()

            if col_b2.button("📄 Ver dictamen", key=f"dict_{i}", use_container_width=True):
                tipo_doc_demo = "mediacion" if clf["carril"]=="verde" else "suspension prueba"
                doc = (generar_dictamen_mediacion(cd, clf, fiscal_nombre, cd["unidad"])
                       if clf["carril"]=="verde"
                       else generar_dictamen_suspension(cd, clf, fiscal_nombre, cd["unidad"]))
                st.markdown(f"<div class='doc-preview'>{doc}</div>", unsafe_allow_html=True)
                pdf_d = generar_pdf(tipo_doc_demo, cd, clf, fiscal_nombre, cd["unidad"])
                col_pa, col_ta = st.columns(2)
                col_pa.download_button("⬇️ PDF", data=pdf_d,
                                       file_name=f"{cd['numero']}_dictamen.pdf",
                                       mime="application/pdf", key=f"dl_pdf_demo_{i}", type="primary")
                col_ta.download_button("📄 .txt", data=doc,
                                       file_name=f"{cd['numero']}_dictamen.txt",
                                       mime="text/plain", key=f"dl_demo_{i}")

            if col_b3.button("📬 Ver citación", key=f"cit_{i}", use_container_width=True):
                doc = generar_citacion(cd, fiscal_nombre, cd["unidad"])
                st.markdown(f"<div class='doc-preview'>{doc}</div>", unsafe_allow_html=True)
                pdf_c = generar_pdf("citacion audiencia", cd, clf, fiscal_nombre, cd["unidad"])
                col_pc, col_tc = st.columns(2)
                col_pc.download_button("⬇️ PDF", data=pdf_c,
                                       file_name=f"{cd['numero']}_citacion.pdf",
                                       mime="application/pdf", key=f"dl_pdf_cit_{i}", type="primary")
                col_tc.download_button("📄 .txt", data=doc,
                                       file_name=f"{cd['numero']}_citacion.txt",
                                       mime="text/plain", key=f"dl_cit_{i}")


# ══════════════════════════════════════════════════════════════════════════════
# TAB 4 — SEGUIMIENTO POST-RESOLUCIÓN
# ══════════════════════════════════════════════════════════════════════════════
with tab_seg:
    render_tab_seguimiento(fiscal_nombre)


# ══════════════════════════════════════════════════════════════════════════════
# TAB 5 — AGENDA
# ══════════════════════════════════════════════════════════════════════════════
with tab_agenda:
    render_tab_agenda(fiscal_nombre)


# ══════════════════════════════════════════════════════════════════════════════
# TAB 6 — PERFIL DEL IMPUTADO
# ══════════════════════════════════════════════════════════════════════════════
with tab_perfil:
    st.header("👤 Perfil del Imputado/a")
    st.caption("Historial completo de causas, seguimientos y audiencias de una persona.")
    render_buscador_perfil()


# ══════════════════════════════════════════════════════════════════════════════
# TAB 7 — PANEL DE CONTROL
# ══════════════════════════════════════════════════════════════════════════════
with tab_panel:
    st.subheader("Panel de Control")
    stats = stats_generales()
    total = stats["total"]

    if total == 0:
        st.info("Aún no hay causas en el sistema. Ingresá casos nuevos o cargá los demos desde la pestaña 🗂️.")
    else:
        # Métricas
        verde_n    = stats["por_carril"].get("verde",0)
        amarillo_n = stats["por_carril"].get("amarillo",0)
        rojo_n     = stats["por_carril"].get("rojo",0)
        no_punitivo = verde_n + amarillo_n

        col1,col2,col3,col4,col5 = st.columns(5)
        col1.metric("Total", total)
        col2.metric("🟢 Mediación",   verde_n,    f"{verde_n*100//total}%" if total else "")
        col3.metric("🟡 Suspensión",  amarillo_n, f"{amarillo_n*100//total}%" if total else "")
        col4.metric("🔴 Proceso",     rojo_n,     f"{rojo_n*100//total}%" if total else "")
        col5.metric("Sin condena", f"{no_punitivo*100//total}%" if total else "0%")

        st.markdown("---")
        col_g1, col_g2 = st.columns(2)

        # Gráfico carriles
        with col_g1:
            if any([verde_n, amarillo_n, rojo_n]):
                fig = go.Figure(go.Pie(
                    labels=["🟢 Mediación","🟡 Suspensión","🔴 Proceso completo"],
                    values=[verde_n, amarillo_n, rojo_n],
                    marker_colors=["#2ECC71","#F39C12","#E74C3C"],
                    hole=0.4, textinfo="label+percent",
                ))
                fig.update_layout(title="Distribución por carril", showlegend=False, height=320)
                st.plotly_chart(fig, use_container_width=True)

        # Gráfico tipos
        with col_g2:
            tipos = causas_por_tipo()
            if tipos:
                df_t = pd.DataFrame(tipos)
                df_t["label"] = df_t["tipo_infraccion"].map(
                    lambda x: TIPOS_INFRACCION.get(x, {}).get("label", x)
                )
                fig2 = px.bar(df_t.head(8), x="n", y="label", orientation="h",
                              color="n", color_continuous_scale="Blues",
                              title="Infracciones más frecuentes")
                fig2.update_layout(height=320, coloraxis_showscale=False,
                                   yaxis_title="", xaxis_title="Causas")
                st.plotly_chart(fig2, use_container_width=True)

        # Estados
        col_g3, col_g4 = st.columns(2)
        with col_g3:
            estados = stats["por_estado"]
            if estados:
                fig3 = go.Figure(go.Bar(
                    x=[ESTADOS_LABEL.get(k,k) for k in estados],
                    y=list(estados.values()),
                    marker_color="#2e5090",
                ))
                fig3.update_layout(title="Causas por estado", height=280,
                                   xaxis_tickangle=-30)
                st.plotly_chart(fig3, use_container_width=True)

        with col_g4:
            unidades_data = stats["por_unidad"]
            if unidades_data:
                fig4 = go.Figure(go.Bar(
                    x=[{"norte":"Norte","sur":"Sur","genero":"Género"}.get(k,k) for k in unidades_data],
                    y=list(unidades_data.values()),
                    marker_color=["#2ECC71","#F39C12","#9B59B6"][:len(unidades_data)],
                ))
                fig4.update_layout(title="Causas por unidad", height=280)
                st.plotly_chart(fig4, use_container_width=True)

        # Evolución temporal + por fiscal
        meses_data  = causas_por_mes(18)
        fiscal_data = causas_por_fiscal()
        col_time, col_fiscal = st.columns(2)

        with col_time:
            if len(meses_data) >= 2:
                df_mes = pd.DataFrame(meses_data)
                fig5 = go.Figure()
                fig5.add_trace(go.Bar(x=df_mes["mes"], y=df_mes["n"],
                                      marker_color="#2e5090", name="Causas"))
                fig5.add_trace(go.Scatter(x=df_mes["mes"], y=df_mes["n"],
                    mode="lines+markers",
                    line=dict(color="#28a745", width=2), marker=dict(size=6),
                    name="Tendencia"))
                fig5.update_layout(title="Causas ingresadas por mes", height=260,
                                   showlegend=False, xaxis_title="", yaxis_title="Causas")
                st.plotly_chart(fig5, use_container_width=True)
            else:
                st.caption("Se necesitan al menos 2 meses de datos para mostrar la evolución.")

        with col_fiscal:
            if fiscal_data:
                df_f = pd.DataFrame(fiscal_data)
                fig6 = go.Figure(go.Bar(
                    x=df_f["n"],
                    y=[n.replace("Dra. ","").replace("Dr. ","") for n in df_f["fiscal_asignado"]],
                    orientation="h",
                    marker_color=["#2e5090","#F39C12","#9B59B6"][:len(df_f)],
                    text=df_f["n"], textposition="auto",
                ))
                fig6.update_layout(title="Causas por fiscal", height=260,
                                   xaxis_title="Causas", yaxis_title="")
                st.plotly_chart(fig6, use_container_width=True)
            else:
                st.caption("Sin datos de fiscales.")

        # ── Tiempos de resolución vs. proceso tradicional ──────────────────
        tiempos = stats_tiempos_resolucion()
        if tiempos:
            st.markdown("---")
            st.subheader("⏱️ Tiempos de resolución vs. proceso tradicional")
            CARRIL_LABELS = {"verde": "🟢 Mediación", "amarillo": "🟡 Suspensión", "rojo": "🔴 Proceso pleno"}
            t_cols = st.columns(len(tiempos))
            for col, (carril, t) in zip(t_cols, tiempos.items()):
                with col:
                    if t["dias_promedio"] is not None:
                        col.metric(
                            CARRIL_LABELS.get(carril, carril),
                            f"~{t['dias_promedio']} días",
                            delta=f"-{t['tradicional'] - t['dias_promedio']}d vs. proceso tradicional",
                            delta_color="inverse",
                        )
                        col.caption(f"Tradicional: ~{t['tradicional']} días · {t['n']} causa(s) resuelta(s)")
                    else:
                        col.metric(CARRIL_LABELS.get(carril, carril), "Sin datos")

            # Gráfico comparativo
            if len(tiempos) >= 1:
                carriles  = list(tiempos.keys())
                labels    = [CARRIL_LABELS.get(c, c) for c in carriles]
                dias_siatc = [tiempos[c]["dias_promedio"] or 0 for c in carriles]
                dias_trad  = [tiempos[c]["tradicional"] for c in carriles]
                fig_t = go.Figure()
                fig_t.add_trace(go.Bar(name="Proceso tradicional", x=labels,
                                       y=dias_trad, marker_color="#adb5bd"))
                fig_t.add_trace(go.Bar(name="Con SIATC", x=labels,
                                       y=dias_siatc, marker_color="#2e5090"))
                fig_t.update_layout(
                    barmode="group", height=260,
                    title="Días promedio hasta resolución",
                    yaxis_title="Días", legend=dict(orientation="h", y=1.1),
                )
                st.plotly_chart(fig_t, use_container_width=True)

        # Total time saved banner
        if tiempos:
            _total_dias_ahorrados = sum(
                (t["tradicional"] - (t["dias_promedio"] or t["tradicional"])) * t["n"]
                for t in tiempos.values()
            )
            _total_causas_resueltas = sum(t["n"] for t in tiempos.values())
            if _total_dias_ahorrados > 0:
                st.success(
                    f"💡 **Impacto acumulado estimado:** SIATC habría ahorrado "
                    f"**{_total_dias_ahorrados:,} días-expediente** en las "
                    f"{_total_causas_resueltas} causas ya resueltas "
                    f"({round(_total_dias_ahorrados / max(_total_causas_resueltas, 1))} días promedio por causa)."
                )

        if stats["personas"]:
            st.markdown("---")
            col_r1, col_r2 = st.columns(2)
            with col_r1:
                st.caption(f"{stats['personas']} personas registradas")
            with col_r2:
                if stats["reincidentes"]:
                    pct_r = round(stats["reincidentes"] * 100 / stats["personas"], 1)
                    st.metric("Tasa reincidencia", f"{pct_r}%",
                              delta=f"{stats['reincidentes']} personas")

        # ── Bloque seguimiento ─────────────────────────────────────────────
        st.markdown("---")
        st.subheader("🔍 Seguimientos post-resolución")
        seg_s = stats_seguimiento()
        if seg_s["total"] == 0:
            st.info("No hay seguimientos registrados aún.")
        else:
            cs1, cs2, cs3, cs4, cs5 = st.columns(5)
            cs1.metric("Total", seg_s["total"])
            cs2.metric("🟡 Activos", seg_s["activos"])
            cs3.metric("🟢 Cumplidos", seg_s["cumplidos"])
            cs4.metric("🔴 Incumplidos", seg_s["incumplidos"])
            cs5.metric("⚠️ Vencidos s/cierre", seg_s["vencidos"],
                       delta="revisar" if seg_s["vencidos"] else None,
                       delta_color="inverse")

            # Gráfico de estados de seguimiento
            col_sg1, col_sg2 = st.columns(2)
            with col_sg1:
                labels_seg = ["Activos", "Cumplidos", "Incumplidos", "Revocados"]
                valores_seg = [
                    seg_s["activos"], seg_s["cumplidos"],
                    seg_s["incumplidos"],
                    seg_s["total"] - seg_s["activos"] - seg_s["cumplidos"] - seg_s["incumplidos"]
                ]
                valores_seg = [v for v in valores_seg if v >= 0]
                if sum(valores_seg) > 0:
                    fig_seg = go.Figure(go.Pie(
                        labels=labels_seg[:len(valores_seg)],
                        values=valores_seg,
                        marker_colors=["#F39C12","#2ECC71","#E74C3C","#95A5A6"],
                        hole=0.4, textinfo="label+value",
                    ))
                    fig_seg.update_layout(title="Estado de seguimientos", showlegend=False, height=280)
                    st.plotly_chart(fig_seg, use_container_width=True)

            with col_sg2:
                # Tabla de seguimientos activos con días restantes
                from datetime import date as _d2
                activos_list = listar_seguimientos(estado="activo")
                if activos_list:
                    rows_seg = []
                    for s in activos_list:
                        try:
                            fin = datetime.strptime(s["fecha_fin"], "%Y-%m-%d").date()
                            dias = (fin - _d2.today()).days
                        except Exception:
                            dias = 0
                        rows_seg.append({
                            "Imputado": s["apellido_nombre"].split(",")[0],
                            "Expediente": s["numero"],
                            "Vencimiento": s["fecha_fin"],
                            "Días": dias,
                            "Alerta": "🔴 VENCIDO" if dias < 0 else ("🟠 URGENTE" if dias <= 7 else ("🟡 PRONTO" if dias <= 30 else "🟢 OK"))
                        })
                    df_seg = pd.DataFrame(rows_seg).sort_values("Días")
                    st.dataframe(df_seg, use_container_width=True, hide_index=True,
                                 column_config={"Días": st.column_config.NumberColumn("Días rest.")})
                else:
                    st.info("No hay seguimientos activos.")

        # ── Bloque audiencias ──────────────────────────────────────────────
        st.markdown("---")
        st.subheader("📅 Audiencias")
        aud_s = stats_audiencias()
        if aud_s["total"] == 0:
            st.info("No hay audiencias registradas aún.")
        else:
            ca1, ca2, ca3, ca4, ca5 = st.columns(5)
            ca1.metric("Total agendadas",  aud_s["total"])
            ca2.metric("🔵 Hoy",           aud_s["hoy"],
                       delta="HOY" if aud_s["hoy"] else None)
            ca3.metric("📆 Próx. 7 días",  aud_s["proximas"])
            ca4.metric("🟢 Realizadas",    aud_s["realizadas"])
            ca5.metric("🔴 Ausencias",     aud_s["ausentes"],
                       delta=f"⚠️ {aud_s['ausentes']}" if aud_s["ausentes"] else None,
                       delta_color="inverse")

            col_a1, col_a2 = st.columns(2)
            with col_a1:
                labels_aud = ["Programadas", "Realizadas", "Ausentes", "Reprogramadas", "Canceladas"]
                vals_aud   = [
                    aud_s["total"] - aud_s["realizadas"] - aud_s["ausentes"],
                    aud_s["realizadas"], aud_s["ausentes"],
                    0, 0,
                ]
                # get actual breakdown from DB
                from database import listar_audiencias as _la
                all_auds = _la()
                from collections import Counter
                conteo = Counter(a["estado"] for a in all_auds)
                vals_aud = [
                    conteo.get("programada", 0),
                    conteo.get("realizada", 0),
                    conteo.get("ausente", 0),
                    conteo.get("reprogramada", 0),
                    conteo.get("cancelada", 0),
                ]
                if sum(vals_aud) > 0:
                    fig_aud = go.Figure(go.Pie(
                        labels=labels_aud,
                        values=vals_aud,
                        marker_colors=["#cce5ff", "#d4edda", "#f8d7da", "#fff3cd", "#e2e3e5"],
                        hole=0.4, textinfo="label+value",
                    ))
                    fig_aud.update_layout(title="Estado de audiencias",
                                          showlegend=False, height=280)
                    st.plotly_chart(fig_aud, use_container_width=True)

            with col_a2:
                # Proximas audiencias table
                from datetime import date as _d3
                proximas_auds = _la(desde=_d3.today().isoformat())
                proximas_auds = sorted(proximas_auds, key=lambda x: (x["fecha"], x["hora"]))[:8]
                if proximas_auds:
                    rows_aud = []
                    for a in proximas_auds:
                        rows_aud.append({
                            "Fecha": a["fecha"],
                            "Hora":  a["hora"],
                            "Imputado": a["apellido_nombre"].split(",")[0],
                            "Tipo": a.get("tipo","").replace("_"," ").capitalize(),
                            "Estado": a.get("estado","").capitalize(),
                        })
                    st.dataframe(
                        pd.DataFrame(rows_aud),
                        use_container_width=True, hide_index=True,
                    )
                else:
                    st.info("No hay audiencias programadas próximas.")

        # ── KPIs de eficiencia ─────────────────────────────────────────────
        if aud_s["total"] > 0:
            _comparecidas = aud_s["realizadas"]
            _total_cerradas = aud_s["realizadas"] + aud_s["ausentes"]
            _pct_comp = round(_comparecidas * 100 / _total_cerradas) if _total_cerradas else 0
            _pct_sin_condena = round(no_punitivo * 100 / total) if total else 0

            st.markdown("---")
            st.subheader("📈 KPIs de eficiencia")
            kc1, kc2, kc3, kc4 = st.columns(4)
            kc1.metric("Tasa de comparecencia",
                       f"{_pct_comp}%",
                       delta=f"{_comparecidas} de {_total_cerradas}",
                       help="Audiencias realizadas / (realizadas + ausencias)")
            kc2.metric("Resolución sin condena",
                       f"{_pct_sin_condena}%",
                       delta=f"{no_punitivo} de {total} causas",
                       help="Carriles verde + amarillo = mediación o suspensión a prueba")
            _pct_resuelta = round(stats["por_estado"].get("resuelta", 0) * 100 / total) if total else 0
            kc3.metric("Causas resueltas",
                       f"{_pct_resuelta}%",
                       delta=f"{stats['por_estado'].get('resuelta',0)} causa(s)",
                       help="Porcentaje de causas en estado 'Resuelta'")
            _archivadas = stats["por_estado"].get("archivada", 0)
            kc4.metric("Causas archivadas",
                       _archivadas,
                       delta=f"seguimiento completo" if _archivadas else None,
                       help="Causas con seguimiento completado y archivadas")

        # ── Exportación a Excel ────────────────────────────────────────────
        st.markdown("---")
        st.subheader("📥 Exportar datos")
        col_ex1, col_ex2, col_ex3, col_ex4 = st.columns(4)
        with col_ex1:
            try:
                xls_causas = causas_a_excel()
                st.download_button(
                    "⬇️ Causas y personas (.xlsx)",
                    data=xls_causas,
                    file_name=f"SIATC_causas_{datetime.now().strftime('%Y%m%d')}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True,
                )
            except Exception as e:
                st.error(f"Error generando Excel: {e}")
        with col_ex2:
            try:
                xls_seg = seguimientos_a_excel()
                st.download_button(
                    "⬇️ Seguimientos (.xlsx)",
                    data=xls_seg,
                    file_name=f"SIATC_seguimientos_{datetime.now().strftime('%Y%m%d')}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True,
                )
            except Exception as e:
                st.error(f"Error generando Excel: {e}")
        with col_ex3:
            try:
                xls_aud = audiencias_a_excel()
                st.download_button(
                    "⬇️ Audiencias (.xlsx)",
                    data=xls_aud,
                    file_name=f"SIATC_audiencias_{datetime.now().strftime('%Y%m%d')}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True,
                )
            except Exception as e:
                st.error(f"Error generando Excel audiencias: {e}")
        with col_ex4:
            try:
                from database import listar_audiencias as _la2
                from datetime import date as _d4
                _auds_hoy  = _la2(desde=_d4.today().isoformat(), hasta=_d4.today().isoformat())
                _pend      = listar_causas(estado="notificada") + listar_causas(estado="clasificada")
                rpt_bytes  = pdf_reporte_diario(stats, _auds_hoy, _pend, fiscal_nombre, unidad_key)
                st.download_button(
                    "⬇️ Reporte del día (.pdf)",
                    data=rpt_bytes,
                    file_name=f"SIATC_reporte_{datetime.now().strftime('%Y%m%d')}.pdf",
                    mime="application/pdf",
                    use_container_width=True,
                    type="primary",
                )
            except Exception as e:
                st.error(f"Error reporte: {e}")

        # ── Causas sin actividad reciente ─────────────────────────────────
        st.markdown("---")
        st.subheader("🔔 Causas que requieren atención")
        _col_inact1, _col_inact2 = st.columns([3, 1])
        with _col_inact2:
            _dias_inact = st.selectbox("Sin actividad desde (días)",
                                       [7, 14, 30, 60], index=1,
                                       key="dias_inactividad")
        inactivas = causas_inactivas(dias=_dias_inact)
        with _col_inact1:
            st.caption(f"Causas en estado activo sin actualización en más de {_dias_inact} días")
        if not inactivas:
            st.success(f"✅ Todas las causas activas tuvieron movimiento en los últimos {_dias_inact} días.")
        else:
            _rows_inact = []
            for c in inactivas:
                _rows_inact.append({
                    "Expediente":  c["numero"],
                    "Imputado/a":  (c.get("apellido_nombre","") or "").split(",")[0],
                    "Estado":      ESTADOS_LABEL.get(c["estado"], c["estado"]),
                    "Carril":      {"verde":"🟢","amarillo":"🟡","rojo":"🔴"}.get(c.get("carril",""),"⚪"),
                    "Sin act. (días)": c.get("dias_inactivo", "?"),
                    "Fiscal":      c.get("fiscal_asignado",""),
                })
            st.warning(f"⚠️ **{len(inactivas)} causa(s)** sin movimiento en más de {_dias_inact} días:")
            _df_inact = pd.DataFrame(_rows_inact).sort_values("Sin act. (días)", ascending=False)
            st.dataframe(_df_inact, use_container_width=True, hide_index=True,
                         column_config={"Sin act. (días)": st.column_config.NumberColumn("Sin act. (días)", format="%d días")})

        # ── Opciones de demostración ───────────────────────────────────────
        st.markdown("---")
        with st.expander("⚙️ Opciones de demostración"):
            col_r1, col_r2 = st.columns([2, 3])
            with col_r1:
                st.warning("**Restablecer datos demo**\n\n"
                           "Borra todas las causas y vuelve al estado inicial de demostración.")
                confirmar = st.checkbox("Confirmo que quiero borrar todos los datos")
                if st.button("🔄 Restablecer datos demo", disabled=not confirmar,
                             type="secondary"):
                    import os
                    from database import DB_PATH
                    try:
                        os.remove(DB_PATH)
                    except Exception:
                        pass
                    init_db()
                    poblar()
                    st.session_state.intro_vista = True   # no mostrar bienvenida de nuevo
                    st.success("Datos restablecidos correctamente.")
                    st.rerun()
            with col_r2:
                st.info("💡 **¿Cómo usar para una demo?**\n\n"
                        "1. Ingresá a **📋 Nuevo Caso** con DNI `38.421.667` "
                        "(detecta antecedentes y auto-completa).\n"
                        "2. Observá el triaje automático → generá y descargá el PDF.\n"
                        "3. Guardá la causa → aparece en **📂 Gestión de Causas**.\n"
                        "4. Desde la causa, agendá audiencia con ▶ popover y explorá el perfil.\n"
                        "5. En **📅 Agenda** verás la semana completa con tu audiencia.\n"
                        "6. En **👤 Perfil** buscá `García` → descargá la ficha PDF.\n"
                        "7. En **📊 Panel** mostrá gráficos, KPIs y tiempos de resolución.\n"
                        "8. Exportá a Excel o generá el Reporte del día en PDF.")
