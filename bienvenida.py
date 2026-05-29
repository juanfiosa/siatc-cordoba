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
        ("📋 Nuevo Caso",        "Ingresá DNI para autocompletar datos del imputado/a. Triaje automático determina carril y muestra pasos a seguir. Generá PDFs al instante y agregá observación inicial."),
        ("📂 Gestión de Causas", "Filtrá por estado, carril, unidad, fiscal y tipo de infracción. Ordená por urgencia. Vista detalle con siguiente paso sugerido y badge de reincidente, o tabla compacta con indicadores de inactividad."),
        ("🗂️ Casos Demo",       "15 casos representativos de una semana real. Cargá todos de una vez o individualmente. Explorá el flujo completo sin afectar datos reales."),
        ("🔍 Seguimiento",       "Registrá condiciones post-resolución con acreditación parcial. Agendá próximos controles. El Acta de Compromiso se genera automáticamente al guardar."),
        ("📅 Agenda",            "Vista semanal con detección de conflictos de horario. Lista filtrable con exportación a PDF, Excel (.xlsx) y calendario (.ics). KPI de comparecencia en tiempo real."),
        ("👤 Perfil",            "Historial completo con timeline visual Gantt. Causas similares en el sistema. Editá domicilio y teléfono. Próxima audiencia visible directamente en el historial."),
        ("📊 Panel de Control",  "Dashboard ejecutivo: tendencia mensual, pipeline por categoría, KPIs (8 métricas), rendimiento por fiscal y unidad, demografía, reincidentes, alertas y 6 formatos de exportación."),
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
**Gestión de Causas**
- 🚨 Urgencia sort · ⚠️ reincidente badge · 📋 siguiente paso sugerido
- ⭐ Causas prioritarias (bookmarks de sesión) · 📅 fecha estimada resolución
- 🗂️ Vista Kanban (pipeline por estado) · Filtro por fiscal + tipo + fechas + reincidentes
- 📍 Links Google Maps + tel: en domicilio/teléfono · Templates de notas rápidas
- ⬇️ Expediente completo PDF (dossier con timeline, audiencias, seguimientos)
- Motivo de cierre al archivar · Análisis de causas existentes al buscar por DNI

**Panel de Control**
- 📈 Tendencia ingresadas vs. cerradas · 🗂️ Pipeline por categoría × estado
- ⏳ Top 5 causas más antiguas · 🏛️ Rendimiento por unidad · 📊 8 KPIs
- 📅 Distribución por día de semana · ⏱️ Tiempo por tipo de infracción
- 💡 Recomendaciones automáticas · 🔴/🟡/✅ Semáforo de salud del sistema
- Exportación: 6 Excel sheets · Lista activas PDF · Informe mensual · Agenda semanal

**Seguimiento**
- 📅 Próximo control con badge de urgencia en el expander
- ⬇️ Acta de Compromiso automática al registrar
- ⬇️ Informe de incumplimiento para condiciones vencidas
- Filtro por tipo de resolución · Duración exacta o por meses

**Agenda**
- 📅 Exportar a iCal (.ics) · PDF agenda semanal
- Sugerencia de horarios libres cuando hay conflictos
- Seguimientos que vencen esta semana en vista semanal

**Perfil**
- 🔴/🟡/🟢 Nivel de riesgo (score 0-10) · Resumen de actividad últimos 30d
- Timeline distingue notas/estados · Próxima audiencia en historial

**Búsqueda y navegación**
- DNI en sidebar → perfil directo · Expediente UCN-XXXXX → pre-selección
- Fiscal sugerido según carga de trabajo en triage
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
