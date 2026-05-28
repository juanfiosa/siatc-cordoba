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
from pdf_gen import generar_pdf
from database import (
    init_db, buscar_persona_por_dni, contar_antecedentes,
    guardar_causa, avanzar_estado, listar_causas, get_causa, get_timeline,
    guardar_documento, listar_documentos, stats_generales, causas_por_tipo,
    historial_persona, upsert_persona, ESTADOS, ESTADOS_LABEL,
)
from seguimiento_tab import render_tab_seguimiento

# ── Init ───────────────────────────────────────────────────────────────────────
init_db()

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
    st.markdown(f"*{datetime.now().strftime('%d/%m/%Y %H:%M')}*")

# ── Header ─────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="main-header">
<h2 style="margin:0">⚖️ SIATC — Sistema Inteligente de Apoyo al Trabajo Contravencional</h2>
<p style="margin:0.3rem 0 0 0;opacity:0.85">
Ministerio Público Fiscal · Provincia de Córdoba &nbsp;|&nbsp; Código de Convivencia Ciudadana — Ley N° 10.326
</p>
</div>
""", unsafe_allow_html=True)

# ── Tabs ───────────────────────────────────────────────────────────────────────
tab_nuevo, tab_causas, tab_demo, tab_seg, tab_panel = st.tabs([
    "📋 Nuevo Caso", "📂 Gestión de Causas", "🗂️ Casos Demo",
    "🔍 Seguimiento", "📊 Panel de Control"
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
                st.success(f"✅ Causa guardada — ID interno #{causa_id}")
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

    # Filtros
    col_f1, col_f2, col_f3, col_f4 = st.columns([2,1,1,1])
    busqueda  = col_f1.text_input("Buscar por nombre, DNI o N° de causa", placeholder="Buscar...", label_visibility="collapsed")
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
        st.markdown(f"**{len(causas)} causa{'s' if len(causas)!=1 else ''}**")

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
                    st.markdown(f"**DNI:** {c['persona_dni']}  |  **Unidad:** {unidad_label}  |  **Fiscal:** {c.get('fiscal_asignado','—')}")
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
                    doc_opts_causa = (
                        ["Dictamen de derivación a mediación", "Cédula de citación a mediación"]
                        if c.get("carril") == "verde"
                        else ["Dictamen de suspensión a prueba", "Cédula de citación", "Resumen ejecutivo"]
                    )
                    doc_tipo = st.selectbox("Tipo", doc_opts_causa, key=f"dopt_{c['id']}", label_visibility="collapsed")
                    if st.button("Generar y guardar", key=f"gendoc_{c['id']}", use_container_width=True):
                        if doc_tipo == "Dictamen de derivación a mediación":
                            doc_txt = generar_dictamen_mediacion(caso_stored, clf_stored, fiscal_nombre, caso_stored["unidad"])
                        elif "suspensión" in doc_tipo or "prueba" in doc_tipo:
                            doc_txt = generar_dictamen_suspension(caso_stored, clf_stored, fiscal_nombre, caso_stored["unidad"])
                        elif "citación" in doc_tipo:
                            doc_txt = generar_citacion(caso_stored, fiscal_nombre, caso_stored["unidad"])
                        else:
                            doc_txt = generar_resumen_ejecutivo(caso_stored, clf_stored)
                        guardar_documento(c["id"], doc_tipo, doc_txt, fiscal_nombre)
                        st.success("Documento guardado en la causa")
                        st.rerun()


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
# TAB 5 — PANEL DE CONTROL
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

        st.markdown(f"*Datos reales del sistema · {stats['personas']} personas registradas · {stats['reincidentes']} con más de una causa*")
