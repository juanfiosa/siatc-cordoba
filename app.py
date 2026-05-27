"""
SIATC — Sistema Inteligente de Apoyo al Trabajo Contravencional
Ministerio Público Fiscal — Córdoba
Prototipo funcional v0.1
"""

import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
from datetime import datetime, timedelta
import random

from data_cordoba import TIPOS_INFRACCION, UNIDADES, CASOS_DEMO
from classifier import clasificar_caso, tiempo_estimado_resolucion
from document_gen import (
    generar_dictamen_mediacion,
    generar_dictamen_suspension,
    generar_citacion,
    generar_resumen_ejecutivo,
)

# ── Configuración de página ────────────────────────────────────────────────────
st.set_page_config(
    page_title="SIATC — Sistema Inteligente Contravencional",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── CSS personalizado ──────────────────────────────────────────────────────────
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(90deg, #1a2f5e 0%, #2e5090 100%);
        padding: 1.5rem 2rem;
        border-radius: 8px;
        color: white;
        margin-bottom: 1.5rem;
    }
    .carril-verde {background: #d4edda; border-left: 5px solid #28a745; padding: 1rem; border-radius: 4px;}
    .carril-amarillo {background: #fff3cd; border-left: 5px solid #ffc107; padding: 1rem; border-radius: 4px;}
    .carril-rojo {background: #f8d7da; border-left: 5px solid #dc3545; padding: 1rem; border-radius: 4px;}
    .metric-box {background: #f8f9fa; border: 1px solid #dee2e6; border-radius: 8px; padding: 1rem; text-align: center;}
    .doc-preview {background: #fafafa; border: 1px solid #ccc; border-radius: 4px; padding: 1.5rem;
                  font-family: 'Courier New', monospace; font-size: 0.78rem; white-space: pre-wrap;
                  max-height: 500px; overflow-y: auto;}
    .fundamento-item {padding: 0.3rem 0; border-bottom: 1px solid #eee;}
</style>
""", unsafe_allow_html=True)

# ── Estado de sesión ───────────────────────────────────────────────────────────
if "casos_procesados" not in st.session_state:
    st.session_state.casos_procesados = []
if "ultimo_caso" not in st.session_state:
    st.session_state.ultimo_caso = None

# ── Header ─────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="main-header">
    <h2 style="margin:0">⚖️ SIATC — Sistema Inteligente de Apoyo al Trabajo Contravencional</h2>
    <p style="margin:0.3rem 0 0 0; opacity:0.85">Ministerio Público Fiscal · Provincia de Córdoba &nbsp;|&nbsp;
    Código de Convivencia Ciudadana — Ley N° 10.326</p>
</div>
""", unsafe_allow_html=True)

# ── Sidebar ─────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.image("https://upload.wikimedia.org/wikipedia/commons/thumb/1/1a/Flag_of_C%C3%B3rdoba_Province.svg/200px-Flag_of_C%C3%B3rdoba_Province.svg.png", width=80)
    st.markdown("### Configuración")
    fiscal_nombre = st.text_input("Fiscal / Ayudante Fiscal", value="Dra. Ana Pérez")
    unidad_key = st.selectbox(
        "Unidad Contravencional",
        options=list(UNIDADES.keys()),
        format_func=lambda k: {"norte": "Norte", "sur": "Sur", "genero": "Género"}[k],
    )
    st.markdown("---")
    st.markdown("**Casos en sesión:** " + str(len(st.session_state.casos_procesados)))
    st.markdown(f"**Fecha:** {datetime.now().strftime('%d/%m/%Y %H:%M')}")
    if st.button("🗑️ Limpiar sesión"):
        st.session_state.casos_procesados = []
        st.session_state.ultimo_caso = None
        st.rerun()

# ── Tabs principales ────────────────────────────────────────────────────────────
tab_nuevo, tab_demo, tab_panel = st.tabs([
    "📋 Nuevo Caso",
    "📂 Casos de Demo",
    "📊 Panel de Control",
])

# ══════════════════════════════════════════════════════════════════════════════
# TAB 1 — NUEVO CASO
# ══════════════════════════════════════════════════════════════════════════════
with tab_nuevo:
    st.subheader("Ingreso de Caso Contravencional")

    col_izq, col_der = st.columns([1, 1], gap="large")

    with col_izq:
        st.markdown("#### Datos del imputado/a")
        nombre = st.text_input("Apellido y nombre", placeholder="Ej: García, Lucas Damián")
        col_dni, col_edad = st.columns(2)
        with col_dni:
            dni = st.text_input("D.N.I.", placeholder="Ej: 38.421.667")
        with col_edad:
            edad = st.number_input("Edad", min_value=16, max_value=99, value=30)

        antecedentes = st.select_slider(
            "Antecedentes contravencionales previos",
            options=[0, 1, 2, 3, 4],
            value=0,
            format_func=lambda x: "Ninguno" if x == 0 else f"{x} antecedente{'s' if x > 1 else ''}",
        )

        st.markdown("#### Datos del hecho")
        tipo_opciones = {k: v["label"] + f"  ({v['categoria']})" for k, v in TIPOS_INFRACCION.items()}
        tipo = st.selectbox("Tipo de infracción", options=list(tipo_opciones.keys()),
                            format_func=lambda k: tipo_opciones[k])

        descripcion = st.text_area("Descripción del hecho (según parte policial)",
                                   height=100, placeholder="Descripción breve del hecho...")

        col_v, col_l, col_r = st.columns(3)
        with col_v:
            victima = st.checkbox("Víctima identificada")
        with col_l:
            lesiones = st.checkbox("Lesiones físicas")
        with col_r:
            resistencia = st.checkbox("Resistencia a autoridad")

        numero_caso = st.text_input("N° de caso / acta policial",
                                    value=f"2024-UC{unidad_key[0].upper()}-{random.randint(400,599):05d}")

    with col_der:
        st.markdown("#### Clasificación automática")

        if nombre and dni and tipo:
            caso = {
                "numero": numero_caso,
                "tipo": tipo,
                "imputado": nombre,
                "dni": dni,
                "edad": edad,
                "antecedentes": antecedentes,
                "descripcion": descripcion,
                "unidad": unidad_key,
            }
            clf = clasificar_caso(tipo, antecedentes, victima, lesiones, resistencia)
            t = tiempo_estimado_resolucion(clf["carril"])

            # Banner de clasificación
            carril_class = f"carril-{clf['carril']}"
            st.markdown(f"""
<div class="{carril_class}">
<h3 style="margin:0">{clf['icono']} CARRIL {clf['carril'].upper()} — {clf['accion']}</h3>
<p style="margin:0.4rem 0 0 0">{clf['descripcion']}</p>
</div>
""", unsafe_allow_html=True)

            # Tiempo estimado
            st.markdown("##### Tiempo de resolución")
            col_a, col_b, col_c = st.columns(3)
            with col_a:
                st.metric("Proceso actual", f"~{t['actual_dias']} días")
            with col_b:
                st.metric("Con SIATC", f"~{t['con_sistema_dias']} días",
                          delta=f"-{t['actual_dias'] - t['con_sistema_dias']} días",
                          delta_color="inverse")
            with col_c:
                reduccion = round((1 - t["con_sistema_dias"] / t["actual_dias"]) * 100)
                st.metric("Reducción", f"{reduccion}%")

            # Fundamentos
            st.markdown("##### Fundamentos de la clasificación")
            for f in clf["fundamento"]:
                st.markdown(f"<div class='fundamento-item'>• {f}</div>", unsafe_allow_html=True)

            # Selector de documento
            st.markdown("---")
            st.markdown("##### Documento sugerido")

            if clf["carril"] == "verde":
                doc_opciones = ["Dictamen de derivación a mediación", "Cédula de citación a mediación"]
            elif clf["carril"] == "amarillo":
                doc_opciones = ["Dictamen de suspensión del proceso a prueba", "Cédula de citación", "Dictamen de derivación a mediación"]
            else:
                doc_opciones = ["Cédula de citación a audiencia", "Resumen ejecutivo del caso"]

            doc_seleccionado = st.selectbox("Documento a generar", doc_opciones)

            if st.button("⚡ Generar documento", type="primary", use_container_width=True):
                if doc_seleccionado == "Dictamen de derivación a mediación":
                    doc = generar_dictamen_mediacion(caso, clf, fiscal_nombre, unidad_key)
                elif doc_seleccionado == "Dictamen de suspensión del proceso a prueba":
                    doc = generar_dictamen_suspension(caso, clf, fiscal_nombre, unidad_key)
                elif "citación" in doc_seleccionado.lower():
                    motivo = "mediacion" if "mediación" in doc_seleccionado else "audiencia"
                    doc = generar_citacion(caso, fiscal_nombre, unidad_key, motivo)
                else:
                    doc = generar_resumen_ejecutivo(caso, clf)

                # Guardar en sesión
                caso["clasificacion"] = clf
                caso["documento"] = doc
                caso["timestamp"] = datetime.now().isoformat()
                st.session_state.ultimo_caso = caso
                if not any(c["numero"] == caso["numero"] for c in st.session_state.casos_procesados):
                    st.session_state.casos_procesados.append(caso)

            # Vista previa del documento
            if st.session_state.ultimo_caso and st.session_state.ultimo_caso["numero"] == numero_caso:
                doc = st.session_state.ultimo_caso.get("documento", "")
                if doc:
                    st.markdown("##### Vista previa del documento")
                    st.markdown(f"<div class='doc-preview'>{doc}</div>", unsafe_allow_html=True)
                    st.download_button(
                        "⬇️ Descargar documento (.txt)",
                        data=doc,
                        file_name=f"{numero_caso}_{doc_seleccionado[:20].replace(' ', '_')}.txt",
                        mime="text/plain",
                        use_container_width=True,
                    )
        else:
            st.info("Completá los datos del imputado/a y seleccioná el tipo de infracción para ver la clasificación automática.")

# ══════════════════════════════════════════════════════════════════════════════
# TAB 2 — CASOS DE DEMO
# ══════════════════════════════════════════════════════════════════════════════
with tab_demo:
    st.subheader("Casos de demostración")
    st.markdown(
        "Los siguientes casos representan una muestra típica de una semana en las Unidades Contravencionales de Capital. "
        "Hacé clic en un caso para procesarlo."
    )

    for i, caso_demo in enumerate(CASOS_DEMO):
        infraccion = TIPOS_INFRACCION.get(caso_demo["tipo"], {})
        clf = clasificar_caso(
            caso_demo["tipo"], caso_demo["antecedentes"], False
        )

        with st.expander(
            f"{clf['icono']} {caso_demo['numero']} — {caso_demo['imputado']}  |  {infraccion.get('label', '')}",
            expanded=(i == 0),
        ):
            col1, col2 = st.columns([2, 1])
            with col1:
                st.markdown(f"**Descripción:** {caso_demo['descripcion']}")
                st.markdown(f"**Antecedentes previos:** {caso_demo['antecedentes']}")
                st.markdown(f"**Unidad:** {UNIDADES[caso_demo['unidad']]}")
            with col2:
                carril_class = f"carril-{clf['carril']}"
                st.markdown(f"""
<div class="{carril_class}" style="margin-bottom:0.5rem">
<strong>{clf['icono']} {clf['accion']}</strong>
</div>
""", unsafe_allow_html=True)

            col_btn1, col_btn2, col_btn3 = st.columns(3)
            with col_btn1:
                if st.button(f"📄 Ver dictamen", key=f"dict_{i}", use_container_width=True):
                    if clf["carril"] == "verde":
                        doc = generar_dictamen_mediacion(caso_demo, clf, fiscal_nombre, caso_demo["unidad"])
                    else:
                        doc = generar_dictamen_suspension(caso_demo, clf, fiscal_nombre, caso_demo["unidad"])
                    caso_demo["clasificacion"] = clf
                    caso_demo["documento"] = doc
                    caso_demo["timestamp"] = datetime.now().isoformat()
                    st.session_state.ultimo_caso = caso_demo
                    if not any(c["numero"] == caso_demo["numero"] for c in st.session_state.casos_procesados):
                        st.session_state.casos_procesados.append(caso_demo)

            with col_btn2:
                if st.button(f"📬 Ver citación", key=f"cit_{i}", use_container_width=True):
                    doc = generar_citacion(caso_demo, fiscal_nombre, caso_demo["unidad"])
                    caso_demo["clasificacion"] = clf
                    caso_demo["documento"] = doc
                    caso_demo["timestamp"] = datetime.now().isoformat()
                    st.session_state.ultimo_caso = caso_demo
                    if not any(c["numero"] == caso_demo["numero"] for c in st.session_state.casos_procesados):
                        st.session_state.casos_procesados.append(caso_demo)

            with col_btn3:
                if st.button(f"📋 Resumen", key=f"res_{i}", use_container_width=True):
                    doc = generar_resumen_ejecutivo(caso_demo, clf)
                    caso_demo["clasificacion"] = clf
                    caso_demo["documento"] = doc
                    caso_demo["timestamp"] = datetime.now().isoformat()
                    st.session_state.ultimo_caso = caso_demo

            if (st.session_state.ultimo_caso and
                    st.session_state.ultimo_caso.get("numero") == caso_demo["numero"] and
                    st.session_state.ultimo_caso.get("documento")):
                doc = st.session_state.ultimo_caso["documento"]
                st.markdown("**Documento generado:**")
                st.markdown(f"<div class='doc-preview'>{doc}</div>", unsafe_allow_html=True)
                st.download_button(
                    "⬇️ Descargar",
                    data=doc,
                    file_name=f"{caso_demo['numero']}.txt",
                    mime="text/plain",
                    key=f"dl_{i}",
                )

# ══════════════════════════════════════════════════════════════════════════════
# TAB 3 — PANEL DE CONTROL
# ══════════════════════════════════════════════════════════════════════════════
with tab_panel:
    st.subheader("Panel de Control — Unidades Contravencionales Capital")
    st.markdown("*Datos simulados representativos de un mes de actividad. En producción, se alimenta del SAC en tiempo real.*")

    # Datos simulados realistas
    random.seed(42)
    n = 120
    tipos_list = list(TIPOS_INFRACCION.keys())
    pesos = [TIPOS_INFRACCION[t]["frecuencia"] for t in tipos_list]
    peso_num = {"muy_alta": 5, "alta": 3, "media": 2, "baja": 1}
    pesos_num = [peso_num[p] for p in pesos]
    total_peso = sum(pesos_num)
    pesos_norm = [p / total_peso for p in pesos_num]

    tipos_muestra = random.choices(tipos_list, weights=pesos_norm, k=n)
    antecedentes_muestra = [random.choices([0, 1, 2, 3], weights=[60, 25, 10, 5])[0] for _ in range(n)]
    carriles = []
    for tipo, ant in zip(tipos_muestra, antecedentes_muestra):
        clf = clasificar_caso(tipo, ant, random.random() < 0.2)
        carriles.append(clf["carril"])

    df = pd.DataFrame({
        "tipo": tipos_muestra,
        "antecedentes": antecedentes_muestra,
        "carril": carriles,
        "categoria": [TIPOS_INFRACCION[t]["categoria"] for t in tipos_muestra],
        "dias_actual": [{"verde": 45, "amarillo": 60, "rojo": 90}[c] for c in carriles],
        "dias_siatc": [{"verde": 5, "amarillo": 3, "rojo": 7}[c] for c in carriles],
        "fecha": [datetime.now() - timedelta(days=random.randint(0, 30)) for _ in range(n)],
    })

    # Métricas resumen
    verde_n = (df["carril"] == "verde").sum()
    amarillo_n = (df["carril"] == "amarillo").sum()
    rojo_n = (df["carril"] == "rojo").sum()
    no_punitivo = verde_n + amarillo_n
    dias_ahorrados = (df["dias_actual"] - df["dias_siatc"]).sum()

    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("Total del mes", n)
    col2.metric("🟢 Mediación", verde_n, f"{verde_n*100//n}%")
    col3.metric("🟡 Suspensión", amarillo_n, f"{amarillo_n*100//n}%")
    col4.metric("🔴 Proceso pleno", rojo_n, f"{rojo_n*100//n}%")
    col5.metric("Días-caso ahorrados", f"{dias_ahorrados:,}", f"{no_punitivo*100//n}% sin condena")

    st.markdown("---")
    col_g1, col_g2 = st.columns(2)

    with col_g1:
        # Distribución de carriles
        fig_carril = go.Figure(go.Pie(
            labels=["🟢 Mediación", "🟡 Suspensión a prueba", "🔴 Proceso completo"],
            values=[verde_n, amarillo_n, rojo_n],
            marker_colors=["#2ECC71", "#F39C12", "#E74C3C"],
            hole=0.4,
            textinfo="label+percent",
        ))
        fig_carril.update_layout(
            title="Distribución por carril de triaje",
            showlegend=False,
            height=350,
        )
        st.plotly_chart(fig_carril, use_container_width=True)

    with col_g2:
        # Tipos de infracciones más frecuentes
        cat_counts = df["categoria"].value_counts().reset_index()
        cat_counts.columns = ["Categoría", "Cantidad"]
        fig_cat = px.bar(
            cat_counts,
            x="Cantidad",
            y="Categoría",
            orientation="h",
            color="Cantidad",
            color_continuous_scale="Blues",
            title="Casos por categoría de infracción",
        )
        fig_cat.update_layout(height=350, coloraxis_showscale=False)
        st.plotly_chart(fig_cat, use_container_width=True)

    col_g3, col_g4 = st.columns(2)

    with col_g3:
        # Tiempo de resolución: actual vs SIATC
        fig_tiempo = go.Figure()
        for carril, color, label in [
            ("verde", "#2ECC71", "Mediación"),
            ("amarillo", "#F39C12", "Suspensión"),
            ("rojo", "#E74C3C", "Proceso pleno"),
        ]:
            sub = df[df["carril"] == carril]
            fig_tiempo.add_trace(go.Bar(
                name=f"{label} — Actual",
                x=[label], y=[sub["dias_actual"].mean()],
                marker_color=color, opacity=0.4,
            ))
            fig_tiempo.add_trace(go.Bar(
                name=f"{label} — SIATC",
                x=[label], y=[sub["dias_siatc"].mean()],
                marker_color=color,
            ))
        fig_tiempo.update_layout(
            barmode="group",
            title="Días promedio de resolución: Actual vs. SIATC",
            yaxis_title="Días",
            height=350,
            showlegend=True,
        )
        st.plotly_chart(fig_tiempo, use_container_width=True)

    with col_g4:
        # Evolución diaria de casos
        df["dia"] = df["fecha"].dt.date
        diario = df.groupby(["dia", "carril"]).size().unstack(fill_value=0).reset_index()
        fig_evol = go.Figure()
        def hex_to_rgba(h, a=0.15):
            r, g, b = int(h[1:3], 16), int(h[3:5], 16), int(h[5:7], 16)
            return f"rgba({r},{g},{b},{a})"

        for carril, color in [("verde", "#2ECC71"), ("amarillo", "#F39C12"), ("rojo", "#E74C3C")]:
            if carril in diario.columns:
                fig_evol.add_trace(go.Scatter(
                    x=diario["dia"],
                    y=diario[carril],
                    mode="lines+markers",
                    name=carril.capitalize(),
                    line=dict(color=color, width=2),
                    fill="tozeroy",
                    fillcolor=hex_to_rgba(color),
                ))
        fig_evol.update_layout(
            title="Ingresos diarios por carril",
            xaxis_title="Fecha",
            yaxis_title="Casos",
            height=350,
        )
        st.plotly_chart(fig_evol, use_container_width=True)

    # Tabla de casos procesados en sesión
    if st.session_state.casos_procesados:
        st.markdown("---")
        st.markdown("#### Casos procesados en esta sesión")
        rows = []
        for c in st.session_state.casos_procesados:
            clf = c.get("clasificacion", {})
            rows.append({
                "N° Caso": c["numero"],
                "Imputado/a": c["imputado"],
                "Infracción": TIPOS_INFRACCION.get(c["tipo"], {}).get("label", c["tipo"]),
                "Antec.": c["antecedentes"],
                "Carril": f"{clf.get('icono', '')} {clf.get('carril', '').upper()}",
                "Acción": clf.get("accion", ""),
            })
        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
