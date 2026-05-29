# -*- coding: utf-8 -*-
"""
Pantalla de bienvenida / introducción — SIATC
Se muestra una sola vez por sesión.
"""

import streamlit as st

INTRO_HTML = """
<style>
.intro-card {
    background: linear-gradient(135deg, #1a2f5e 0%, #2e5090 60%, #3a6bc4 100%);
    border-radius: 12px; padding: 2.2rem 2.5rem; color: white; margin-bottom: 1rem;
}
.intro-card h1 { margin: 0 0 0.3rem 0; font-size: 1.8rem; }
.intro-card p  { margin: 0; opacity: 0.88; font-size: 1rem; }
.lane-card {
    border-radius: 8px; padding: 1rem 1.2rem; height: 100%;
}
.lane-verde    { background: #d4edda; border-left: 5px solid #28a745; }
.lane-amarillo { background: #fff3cd; border-left: 5px solid #ffc107; }
.lane-rojo     { background: #f8d7da; border-left: 5px solid #dc3545; }
.lane-card h4  { margin: 0 0 0.4rem 0; }
.lane-card p   { margin: 0; font-size: 0.87rem; }
.tab-card {
    background: #f8f9fa; border: 1px solid #dee2e6;
    border-radius: 8px; padding: 0.9rem 1.1rem; margin-bottom: 0.5rem;
}
.tab-card strong { color: #1a2f5e; }
.stat-box {
    background: white; border: 1px solid #dee2e6; border-radius: 8px;
    padding: 0.8rem; text-align: center;
}
.stat-box .num { font-size: 2rem; font-weight: bold; color: #2e5090; }
.stat-box .lbl { font-size: 0.8rem; color: #666; }
</style>
<div class="intro-card">
  <h1>⚖️ SIATC — Sistema Inteligente de Apoyo al Trabajo Contravencional</h1>
  <p>Ministerio Público Fiscal · Provincia de Córdoba &nbsp;|&nbsp;
     Código de Convivencia Ciudadana — Ley N° 10.326</p>
</div>
"""

CONTEXTO_HTML = """
<div style="background:#f0f4ff;border-left:4px solid #2e5090;padding:0.9rem 1.2rem;
            border-radius:0 6px 6px 0;margin-bottom:1rem">
<strong>¿Qué es SIATC?</strong><br>
Un prototipo de sistema de gestión contravencional que automatiza el triaje de causas,
genera documentos institucionales, registra el ciclo de vida de cada expediente y
hace seguimiento del cumplimiento de condiciones post-resolución.
</div>
"""


def _render_lanes():
    # Try to compute real percentages from DB
    _verde_pct  = "~60%"
    _amar_pct   = "~30%"
    _rojo_pct   = "~10%"
    try:
        import database as _db
        _s = _db.stats_generales()
        _tot = _s.get("total", 0)
        if _tot > 0:
            _pc = _s.get("por_carril", {})
            _verde_pct  = f"{_pc.get('verde', 0) * 100 // _tot}% del sistema"
            _amar_pct   = f"{_pc.get('amarillo', 0) * 100 // _tot}% del sistema"
            _rojo_pct   = f"{_pc.get('rojo', 0) * 100 // _tot}% del sistema"
    except Exception:
        pass

    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown(f"""<div class="lane-card lane-verde">
<h4>🟢 Carril Verde</h4>
<p><strong>Mediación</strong><br>
Conflictos de mínima gravedad sin antecedentes.<br>
Derivación al Centro Judicial de Mediación.<br>
<em>{_verde_pct}</em></p>
</div>""", unsafe_allow_html=True)
    with c2:
        st.markdown(f"""<div class="lane-card lane-amarillo">
<h4>🟡 Carril Amarillo</h4>
<p><strong>Suspensión del proceso a prueba</strong><br>
Gravedad media o antecedentes leves.<br>
Condiciones de cumplimiento monitoreadas.<br>
<em>{_amar_pct}</em></p>
</div>""", unsafe_allow_html=True)
    with c3:
        st.markdown(f"""<div class="lane-card lane-rojo">
<h4>🔴 Carril Rojo</h4>
<p><strong>Proceso contravencional pleno</strong><br>
Alta gravedad, lesiones o reincidencia.<br>
Tramitación completa ante el Tribunal.<br>
<em>{_rojo_pct}</em></p>
</div>""", unsafe_allow_html=True)


def _render_tabs():
    tabs_info = [
        ("📋 Nuevo Caso",        "Ingresá DNI para autocompletar datos del imputado/a (nombre, domicilio, teléfono, antecedentes). Triaje automático con documento PDF listo para descargar."),
        ("📂 Gestión de Causas", "Buscá por nombre, DNI o descripción. Vista detalle o tabla compacta. Agregá notas rápidas, agendá audiencias y generá documentos desde cada causa."),
        ("🗂️ Casos Demo",       "15 casos representativos de una semana real. Cargalos con un clic para explorar el flujo completo."),
        ("🔍 Seguimiento",       "Registrá períodos de prueba y condiciones. Monitoreá avances, registrá acreditaciones parciales y cerrá seguimientos con un clic."),
        ("📅 Agenda",            "Vista semanal y lista de audiencias. Programá nuevas, actualizá estados (realizada/ausente/reprogramada) y exportá a Excel con teléfono."),
        ("👤 Perfil",            "Historial completo de una persona: causas, audiencias, seguimientos. Editá domicilio y teléfono directamente. Descargá la ficha institucional en PDF."),
        ("📊 Panel de Control",  "Dashboard completo: carriles, categorías, tiempos vs. proceso tradicional, KPIs, actividad reciente, alertas y exportación a Excel / reporte PDF del día."),
    ]
    for emoji_nombre, desc in tabs_info:
        st.markdown(f"""<div class="tab-card">
<strong>{emoji_nombre}</strong><br>
<span style="font-size:0.88rem">{desc}</span>
</div>""", unsafe_allow_html=True)


def _render_stats():
    try:
        import database as db
        s = db.stats_generales()
        sa = db.stats_audiencias()
        ss = db.stats_seguimiento()
        stats_items = [
            (str(s.get("total", 0)),       "causas en el sistema"),
            (str(s.get("personas", 0)),    "personas registradas"),
            (str(sa.get("total", 0)),      "audiencias agendadas"),
            (str(ss.get("activos", 0)),    "seguimientos activos"),
        ]
    except Exception:
        stats_items = [
            ("23.256", "causas/año en Córdoba"),
            ("27",     "unidades contravencionales"),
            ("76%",    "reduccion tiempo (Prometea CABA)"),
            ("3",      "unidades piloto MPF"),
        ]
    cols = st.columns(4)
    for col, (num, lbl) in zip(cols, stats_items):
        col.markdown(f"""<div class="stat-box">
<div class="num">{num}</div>
<div class="lbl">{lbl}</div>
</div>""", unsafe_allow_html=True)


def mostrar_si_primera_vez():
    """Muestra la introducción y retorna True si el usuario eligió continuar."""
    if st.session_state.get("intro_vista"):
        return True   # ya la vio, seguir normalmente

    st.markdown(INTRO_HTML, unsafe_allow_html=True)
    st.markdown(CONTEXTO_HTML, unsafe_allow_html=True)

    col_lanes, col_tabs = st.columns([3, 2])
    with col_lanes:
        st.markdown("#### Sistema de triaje automático — 3 carriles")
        _render_lanes()
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("#### El sistema en números")
        _render_stats()

    with col_tabs:
        st.markdown("#### ¿Qué puede hacer?")
        _render_tabs()

    st.markdown("---")

    with st.expander("📣 Novedades v1.3", expanded=False):
        st.markdown("""
**Mejoras en Gestión de Causas**
- 🚨 **Ordenamiento por urgencia** — prioriza causas con más días sin actividad, carril rojo y reincidentes
- ⚠️ **Filtro "Solo reincidentes"** — muestra sólo personas con más de una causa en el sistema
- 🏷️ **Badge de reincidente** en el encabezado de cada causa (detección automática)
- 📋 **Siguiente paso sugerido** — guía contextual basada en estado y carril de cada causa
- 📊 **Resumen rápido del filtro** — total / activas / resueltas / verde / amarillo / rojo

**Panel de Control**
- 📈 **Tendencia mensual** — gráfico de doble línea ingresadas vs. cerradas con alerta de backlog
- 🏛️ **Rendimiento por unidad** — métricas comparativas Norte / Sur / Género

**Seguimiento Post-Resolución**
- 📅 **Próximo control** — agendá la fecha del siguiente control directamente en el seguimiento
- ⬇️ **Acta de Compromiso** — descargá el PDF inmediatamente al registrar un seguimiento

**Perfil del Imputado/a**
- Línea de tiempo distingue notas (gris) de cambios de estado (azul)
- Próxima audiencia indicada en el título de cada causa del historial

**Exportación Excel**
- Ahora incluye 6 hojas: Causas · Personas · Estadísticas · Por Fiscal · **Por Unidad** · **Tendencia mensual**
""")

    col_btn, col_txt = st.columns([1, 3])
    with col_btn:
        if st.button("🚀 Ingresar al sistema", type="primary", use_container_width=True):
            st.session_state.intro_vista = True
            st.rerun()
    with col_txt:
        st.caption("Los datos cargados son de demostración. "
                   "El sistema no está conectado a SAC ni a redes del MPF.")

    return False   # todavía no ingresó
