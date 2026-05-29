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
    generar_requerimiento_apertura,
)
from pdf_gen import generar_pdf, pdf_reporte_diario
from database import (
    init_db, reset_db, buscar_persona_por_dni, contar_antecedentes,
    guardar_causa, avanzar_estado, agregar_nota_causa, listar_causas, get_causa, get_timeline,
    guardar_documento, listar_documentos, stats_generales, causas_por_tipo,
    historial_persona, upsert_persona, ESTADOS, ESTADOS_LABEL,
    listar_seguimientos, stats_seguimiento, causas_por_mes, causas_por_fiscal,
    get_seguimiento_por_causa, get_condiciones, stats_tiempos_resolucion,
    causas_inactivas, causas_sin_audiencia_programada, personas_reincidentes,
    actividad_reciente, stats_edad, stats_edad_por_carril,
    causas_mes_actual_vs_anterior, stats_por_fiscal, causas_sin_seguimiento,
    proximas_audiencias_por_causa, causas_count_por_persona,
    stats_tendencia_mensual, stats_por_unidad, stats_tiempo_por_tipo,
    stats_por_dia_semana, stats_categoria_por_estado, asignar_fiscal,
    causas_mas_antiguas_activas, stats_eficiencia_carriles, mediaciones_estancadas,
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

# ── Cached DB helpers (TTL=60s — evita re-queries en cada rerun) ───────────────
@st.cache_data(ttl=60)
def _c_stats_generales():
    return stats_generales()

@st.cache_data(ttl=60)
def _c_stats_seguimiento():
    return stats_seguimiento()

@st.cache_data(ttl=60)
def _c_stats_audiencias():
    return stats_audiencias()

@st.cache_data(ttl=60)
def _c_sin_audiencia():
    return causas_sin_audiencia_programada()

@st.cache_data(ttl=60)
def _c_stats_por_fiscal():
    return stats_por_fiscal()

@st.cache_data(ttl=60)
def _c_sin_seguimiento():
    return causas_sin_seguimiento()

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
    box-shadow: 0 2px 8px rgba(30,47,94,0.25);
}
.carril-verde    {background:#d4edda;border-left:5px solid #28a745;padding:1rem;border-radius:4px;margin:0.5rem 0;
                  box-shadow:0 1px 3px rgba(40,167,69,0.15)}
.carril-amarillo {background:#fff3cd;border-left:5px solid #ffc107;padding:1rem;border-radius:4px;margin:0.5rem 0;
                  box-shadow:0 1px 3px rgba(255,193,7,0.15)}
.carril-rojo     {background:#f8d7da;border-left:5px solid #dc3545;padding:1rem;border-radius:4px;margin:0.5rem 0;
                  box-shadow:0 1px 3px rgba(220,53,69,0.15)}
.timeline-item   {border-left:3px solid #2e5090;padding:0.4rem 0.8rem;margin:0.3rem 0;background:#f8f9fa;
                  border-radius:0 4px 4px 0;transition:background 0.2s}
.timeline-item:hover {background:#e8eaf6}
.doc-preview     {background:#fafafa;border:1px solid #ccc;border-radius:4px;padding:1.2rem;
                  font-family:'Courier New',monospace;font-size:0.76rem;white-space:pre-wrap;
                  max-height:420px;overflow-y:auto;line-height:1.4}
.antec-badge     {background:#dc3545;color:white;border-radius:12px;padding:2px 10px;font-size:0.8rem;
                  font-weight:bold;display:inline-block;margin:4px 0}
.antec-ok        {background:#28a745;color:white;border-radius:12px;padding:2px 10px;font-size:0.8rem;
                  display:inline-block;margin:4px 0}
/* Subtle hover on expanders */
div[data-testid="stExpander"] > div:first-child:hover {background:#f0f4ff !important}
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
    stats = _c_stats_generales()
    st.metric("Causas totales", stats["total"])
    col1, col2 = st.columns(2)
    col1.metric("🟢", stats["por_carril"].get("verde", 0))
    col2.metric("🟡", stats["por_carril"].get("amarillo", 0))
    col1.metric("🔴", stats["por_carril"].get("rojo", 0))
    col2.metric("👤 Personas", stats["personas"])

    # ── Alertas de seguimiento ─────────────────────────────────────────────
    st.markdown("---")
    seg_stats = _c_stats_seguimiento()
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

        # Próximos controles agendados (dentro de 7 días)
        _controles_prox = []
        for s in activos:
            if s.get("proximo_control"):
                try:
                    _pc_d = datetime.strptime(s["proximo_control"], "%Y-%m-%d").date()
                    _pc_dias = (_pc_d - _date.today()).days
                    if 0 <= _pc_dias <= 7:
                        _controles_prox.append((_pc_dias, s))
                except Exception:
                    pass
        if _controles_prox:
            st.markdown("**📋 Controles próximos:**")
            for _cpd, _cps in sorted(_controles_prox)[:3]:
                _lbl = "HOY" if _cpd == 0 else f"en {_cpd}d"
                st.caption(f"🔵 {_cps['apellido_nombre'].split(',')[0]} — control {_lbl}")

    # ── Audiencias del día ─────────────────────────────────────────────────
    hoy_auds = audiencias_hoy()
    if hoy_auds:
        st.markdown("---")
        st.markdown(f"**📅 Audiencias hoy ({len(hoy_auds)})**")
        for a in hoy_auds:
            st.caption(f"🔵 {a['hora']} — {a['apellido_nombre'].split(',')[0]} ({a['numero']})")

    # Próximas audiencias esta semana
    aud_s = _c_stats_audiencias()
    if aud_s["proximas"] > 0:
        st.markdown("---")
        st.markdown(f"**📆 Esta semana: {aud_s['proximas']} audiencia(s)**")

    # Causas sin audiencia programada (sidebar alert)
    _sin_aud_sb = _c_sin_audiencia()
    if _sin_aud_sb:
        st.markdown("---")
        st.error(f"📋 {len(_sin_aud_sb)} sin audiencia")

    # Esta semana — quick activity snapshot
    st.markdown("---")
    try:
        from datetime import date as _dsb
        _lunes_sb = (_dsb.today() - timedelta(days=_dsb.today().weekday())).isoformat()
        _nuevas_sem = len(listar_causas(fecha_desde=_lunes_sb, limit=200))
        _auds_sem   = len(listar_audiencias(desde=_lunes_sb))
        st.markdown("**📊 Esta semana**")
        _cs1, _cs2 = st.columns(2)
        _cs1.metric("Nuevas causas", _nuevas_sem)
        _cs2.metric("Audiencias", _auds_sem)
    except Exception:
        pass

    # Búsqueda rápida
    st.markdown("---")
    st.markdown("**🔎 Búsqueda rápida**")
    _q_rapid = st.text_input("Nombre, DNI o expediente", placeholder="Ej: García, 38421667 o UCN-00001",
                             key="busqueda", label_visibility="collapsed")
    if _q_rapid:
        st.session_state["busqueda_rapida_causas"] = _q_rapid
        # DNI pattern — if input is all digits 7-9 chars, offer profile jump
        if _q_rapid.isdigit() and 7 <= len(_q_rapid) <= 9:
            if st.button(f"👤 Ver perfil DNI {_q_rapid}", key="sb_dni_perfil",
                         use_container_width=True, type="secondary"):
                st.session_state["perfil_busqueda"] = _q_rapid
                st.session_state["goto_perfil"] = True
        # Expediente pattern (UCN-NNNNN) — auto-select if exact match
        elif _q_rapid.upper().startswith("UCN-"):
            _match_causas = listar_causas(busqueda=_q_rapid, limit=5)
            if len(_match_causas) == 1:
                st.session_state["causa_sel_id"] = _match_causas[0]["id"]
                _ic_m = {"verde":"🟢","amarillo":"🟡","rojo":"🔴"}.get(_match_causas[0].get("carril",""),"⚪")
                st.caption(f"{_ic_m} {_match_causas[0]['numero']} — {ESTADOS_LABEL.get(_match_causas[0]['estado'], _match_causas[0]['estado'])}")

    # Últimas causas modificadas
    _ultimas = listar_causas(limit=4)
    if _ultimas:
        st.markdown("---")
        st.markdown("**📂 Últimas causas**")
        for _uc in _ultimas:
            _ic_uc = {"verde":"🟢","amarillo":"🟡","rojo":"🔴"}.get(_uc.get("carril",""),"⚪")
            _nombre_c = (_uc.get("apellido_nombre","") or "").split(",")[0]
            if st.button(
                f"{_ic_uc} {_uc['numero'][:14]}\n{_nombre_c}",
                key=f"sb_uc_{_uc['id']}",
                use_container_width=True,
            ):
                st.session_state["gc_busqueda"] = _uc["numero"]
                st.session_state["causa_sel_id"] = _uc["id"]

    st.markdown("---")
    st.caption(
        f"v1.3-demo · {datetime.now().strftime('%d/%m/%Y')}\n\n"
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
_aud_hoy_count = _c_stats_audiencias()["hoy"]
if _aud_hoy_count:
    _alertas.append(f"📅 **{_aud_hoy_count} audiencia(s) HOY** — revisá la pestaña Agenda")

# Seguimientos vencidos sin cierre
_venc = _c_stats_seguimiento()["vencidos"]
if _venc:
    _alertas.append(f"⚠️ **{_venc} seguimiento(s) vencido(s)** sin cierre formal")

# Causas incumplidas
_inc = _c_stats_seguimiento()["incumplidos"]
if _inc:
    _alertas.append(f"❌ **{_inc} seguimiento(s) incumplido(s)** — evaluar revocación")

# Ausencias recientes (últimos 7 días)
from database import listar_audiencias as _la_alerts
from datetime import timedelta as _tda
_hace7 = (_date_now.today() - _tda(days=7)).isoformat()
_ausentes_rec = len([a for a in _la_alerts(desde=_hace7, hasta=_hoy_str) if a.get("estado") == "ausente"])
if _ausentes_rec:
    _alertas.append(f"🚨 **{_ausentes_rec} incomparecencia(s)** en los últimos 7 días")

# Causas sin audiencia programada
_sin_aud = _c_sin_audiencia()
if _sin_aud:
    _alertas.append(f"📋 **{len(_sin_aud)} causa(s) notificada(s) o clasificada(s)** sin audiencia programada")

# Causas resueltas/en_mediacion sin seguimiento
_sin_seg = _c_sin_seguimiento()
if _sin_seg:
    _alertas.append(f"🔍 **{len(_sin_seg)} causa(s) resuelta(s)/en mediación** sin seguimiento registrado")

# Próximos controles HOY
try:
    _activos_ctrl = listar_seguimientos(estado="activo")
    _ctrl_hoy = [
        s for s in _activos_ctrl
        if s.get("proximo_control") == _hoy_str
    ]
    if _ctrl_hoy:
        _alertas.append(f"📋 **{len(_ctrl_hoy)} control(es) de seguimiento HOY** — verificar cumplimiento")
except Exception:
    pass

# Mediaciones estancadas (>30 días sin actualización)
try:
    _med_est = mediaciones_estancadas(dias=30)
    if _med_est:
        _alertas.append(f"🤝 **{len(_med_est)} mediación(es) estancada(s)** sin actualización en >30 días")
except Exception:
    pass

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

        # Validación de formato DNI
        _dni_digits = dni_input.replace(".", "").replace("-", "").replace(" ", "")
        if dni_input and _dni_digits:
            if not _dni_digits.isdigit():
                st.warning("⚠️ El DNI solo debe contener dígitos (y opcionalmente puntos o guiones).")
            elif len(_dni_digits) < 7:
                st.warning("⚠️ DNI demasiado corto — los DNI argentinos tienen 7 a 8 dígitos.")
            elif len(_dni_digits) > 9:
                st.warning("⚠️ DNI demasiado largo — verificá el número ingresado.")

        # Lookup automático por DNI
        persona_encontrada = None
        antecedentes_db = 0
        if dni_input and len(dni_input.replace(".", "").replace("-", "")) >= 7:
            persona_encontrada = buscar_persona_por_dni(dni_input)
            if persona_encontrada:
                antecedentes_db = contar_antecedentes(persona_encontrada["id"])
                st.success(f"✅ **{persona_encontrada['apellido_nombre']}** encontrada/o en el sistema")
                historial = historial_persona(persona_encontrada["id"])
                if antecedentes_db > 0:
                    st.markdown(
                        f'<span class="antec-badge">⚠️ {antecedentes_db} antecedente{"s" if antecedentes_db>1 else ""} en el sistema</span>',
                        unsafe_allow_html=True
                    )
                else:
                    st.markdown('<span class="antec-ok">✔ Sin antecedentes</span>', unsafe_allow_html=True)
                # Show existing causas for this person
                _causas_persona_nc = listar_causas(limit=50)
                _causas_persona_nc = [c for c in _causas_persona_nc
                                      if c.get("persona_id") == persona_encontrada["id"]]
                if _causas_persona_nc:
                    with st.expander(f"📂 {len(_causas_persona_nc)} causa(s) registrada(s) para esta persona"):
                        for _cp in _causas_persona_nc:
                            _cp_ic = {"verde":"🟢","amarillo":"🟡","rojo":"🔴"}.get(_cp.get("carril",""),"⚪")
                            _cp_est = ESTADOS_LABEL.get(_cp["estado"], _cp["estado"])
                            _cp_inf = TIPOS_INFRACCION.get(_cp.get("tipo_infraccion",""),{}).get("label","")[:35]
                            st.markdown(f"{_cp_ic} **{_cp['numero']}** | {_cp_inf} | {_cp_est} | {_cp.get('created_at','')[:10]}")
            else:
                st.caption("DNI no encontrado en el sistema — ingresá los datos manualmente.")

        # Búsqueda por nombre si no se encontró por DNI
        if not persona_encontrada:
            with st.expander("🔎 Buscar persona existente por nombre"):
                _nombre_busq = st.text_input("Apellido o nombre", placeholder="Ej: García",
                                              key="nuevo_busq_nombre")
                if _nombre_busq and len(_nombre_busq) >= 3:
                    _matches = listar_personas(busqueda=_nombre_busq)
                    if _matches:
                        _opts = {f"{p['apellido_nombre']} — DNI {p['dni']}": p for p in _matches}
                        _sel_p = st.selectbox("Resultado(s)", list(_opts.keys()), key="nuevo_sel_persona")
                        if st.button("Usar esta persona", key="nuevo_usar_persona"):
                            _p_sel = _opts[_sel_p]
                            st.session_state["_nuevo_persona_override"] = _p_sel
                            st.rerun()
                    else:
                        st.caption("Sin resultados.")

        # Si el usuario seleccionó una persona por nombre, usarla
        if "nuevos_persona_override" not in st.session_state:
            _persona_override = st.session_state.pop("_nuevo_persona_override", None)
            if _persona_override and not persona_encontrada:
                persona_encontrada = _persona_override
                antecedentes_db = contar_antecedentes(persona_encontrada["id"])

        nombre_default = persona_encontrada["apellido_nombre"] if persona_encontrada else ""
        edad_default   = persona_encontrada["edad"]             if persona_encontrada else 30

        nombre = st.text_input("Apellido y nombre", value=nombre_default, placeholder="Ej: García, Lucas Damián")
        col_e, col_d, col_t = st.columns(3)
        with col_e:
            edad = st.number_input("Edad", min_value=16, max_value=99, value=edad_default)
        with col_d:
            domicilio = st.text_input("Domicilio", value=persona_encontrada.get("domicilio","") if persona_encontrada else "")
        with col_t:
            telefono = st.text_input("Teléfono", value=persona_encontrada.get("telefono","") if persona_encontrada else "",
                                     placeholder="Ej: (0351) 4123456")

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
        # Info card para el tipo seleccionado
        _inf_sel = TIPOS_INFRACCION.get(tipo, {})
        if _inf_sel:
            _grav_txt  = {1: "Baja", 2: "Media", 3: "Alta"}.get(_inf_sel.get("gravedad_base", 1), "—")
            _grav_icon = {1: "🟢", 2: "🟡", 3: "🔴"}.get(_inf_sel.get("gravedad_base", 1), "⚪")
            _vec_txt   = "⚠️ Conflicto vecinal" if _inf_sel.get("es_conflicto_vecinal") else "🚦 No vecinal"
            st.info(
                f"**{_inf_sel.get('articulo', '')}** &nbsp;|&nbsp; "
                f"Categoría: **{_inf_sel.get('categoria', '')}** &nbsp;|&nbsp; "
                f"Gravedad base: {_grav_icon} **{_grav_txt}** &nbsp;|&nbsp; {_vec_txt}"
            )
        from datetime import date as _date_form
        col_desc, col_fech = st.columns([3, 1])
        with col_desc:
            descripcion = st.text_area("Descripción (según parte policial)", height=90,
                                       placeholder="Descripción breve del hecho...")
        with col_fech:
            fecha_hecho = st.date_input("Fecha del hecho", value=_date_form.today(),
                                        max_value=_date_form.today(), key="nuevo_fecha_hecho")
        col_v, col_l, col_r = st.columns(3)
        victima    = col_v.checkbox("Víctima identificada")
        lesiones   = col_l.checkbox("Lesiones físicas")
        resistencia= col_r.checkbox("Resistencia a autoridad")

    with col_der:
        st.markdown("#### Clasificación automática")

        if nombre and dni_input and tipo:
            # Advertencia de causa duplicada — misma persona + mismo tipo + estado activo
            if persona_encontrada and persona_encontrada.get("id"):
                _activos_dup = [
                    c for c in listar_causas(tipo_infraccion=tipo, limit=50)
                    if (c.get("persona_id") == persona_encontrada["id"]
                        or c.get("persona_dni") == dni_input)
                    and c.get("estado") not in ("resuelta", "archivada")
                ]
                if _activos_dup:
                    st.warning(
                        f"⚠️ **Esta persona ya tiene {len(_activos_dup)} causa(s) activa(s) "
                        f"del mismo tipo:** "
                        + ", ".join(f"**{c['numero']}** ({ESTADOS_LABEL.get(c['estado'],c['estado'])})"
                                    for c in _activos_dup)
                        + "  \nVerificá antes de registrar una causa duplicada."
                    )

            caso = {
                "numero": None,          # se asigna al guardar
                "tipo": tipo, "imputado": nombre, "dni": dni_input,
                "edad": edad, "antecedentes": antecedentes,
                "descripcion": descripcion, "unidad": unidad_key,
                "domicilio": domicilio, "telefono": telefono,
                "victima": victima, "lesiones": lesiones, "resistencia": resistencia,
                "fecha_hecho": fecha_hecho.isoformat(),
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

            # Fiscal sugerido basado en menor carga de trabajo
            try:
                _sfis_nc = stats_por_fiscal()
                if _sfis_nc:
                    _min_fis = min(_sfis_nc, key=lambda f: f["total"])
                    _act_fis = sum(1 for c in listar_causas(limit=200)
                                   if c.get("fiscal_asignado") == _min_fis["fiscal_asignado"]
                                   and c.get("estado") in ("ingresada","clasificada","notificada","en_mediacion"))
                    st.caption(f"💡 **Fiscal sugerido** (menor carga activa): "
                               f"**{_min_fis['fiscal_asignado']}** — {_act_fis} causas activas")
            except Exception:
                pass

            st.markdown("##### Fundamentos")
            for f in clf["fundamento"]:
                st.markdown(f"• {f}")

            # Pasos a seguir — guía procesal por carril
            _pasos_nc = {
                "verde": [
                    "**1.** Guardar la causa en el sistema (botón 💾)",
                    "**2.** Generar y firmar el **Dictamen de derivación a mediación**",
                    "**3.** Notificar al imputado/a con la **cédula de citación a mediación**",
                    "**4.** En **📅 Agenda**, programar la audiencia de mediación",
                    "**5.** Si hay acuerdo, registrar el seguimiento en **🔍 Seguimiento**",
                ],
                "amarillo": [
                    "**1.** Guardar la causa en el sistema (botón 💾)",
                    "**2.** Generar el **Dictamen de suspensión del proceso a prueba**",
                    "**3.** Enviar **cédula de notificación** al imputado/a",
                    "**4.** En **📅 Agenda**, programar audiencia para suscribir el acta",
                    "**5.** Al acordar condiciones, registrar el **seguimiento** en 🔍",
                ],
                "rojo": [
                    "**1.** Guardar la causa en el sistema (botón 💾)",
                    "**2.** Generar el **Requerimiento de apertura del proceso contravencional**",
                    "**3.** Notificar al imputado/a y a la defensa técnica",
                    "**4.** Programar **audiencia contravencional** en 📅 Agenda",
                    "**5.** Seguir el proceso conforme el Código de Convivencia Ciudadana",
                ],
            }
            with st.expander(f"📋 Pasos a seguir — Carril {clf['carril'].upper()}", expanded=True):
                for _paso in _pasos_nc.get(clf["carril"], []):
                    st.markdown(_paso)

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

            # Observación inicial (se guarda como primera nota en el timeline)
            _obs_inicial = st.text_area(
                "Observación inicial (opcional)",
                placeholder="Ej: Imputado/a colaboró con el procedimiento. Víctima solicitó no continuar con la denuncia.",
                height=60,
                key="nc_obs_inicial",
                help="Esta nota quedará registrada en el historial de estados de la causa al guardarla.",
            )

            # Documento
            if clf["carril"] == "verde":
                doc_ops = ["Dictamen de derivación a mediación", "Cédula de citación a mediación"]
            elif clf["carril"] == "amarillo":
                doc_ops = ["Dictamen de suspensión del proceso a prueba", "Cédula de citación", "Dictamen de derivación a mediación"]
            else:
                doc_ops = ["Requerimiento de apertura del proceso", "Cédula de citación a audiencia", "Resumen ejecutivo del caso"]
            doc_sel = st.selectbox("Documento a generar", doc_ops)

            col_btn1, col_btn2 = st.columns(2)
            gen_doc = col_btn1.button("⚡ Generar documento", type="primary", use_container_width=True)
            guardar = col_btn2.button("💾 Guardar en sistema", use_container_width=True)

            if guardar:
                causa_id = guardar_causa(caso, clf, fiscal_nombre)
                # Save initial observation as first nota in timeline
                if _obs_inicial and _obs_inicial.strip():
                    agregar_nota_causa(causa_id, _obs_inicial.strip(), fiscal_nombre)
                st.cache_data.clear()   # invalidar cache tras mutación
                c_saved  = get_causa(causa_id)
                numero_guardado = c_saved["numero"] if c_saved else f"ID#{causa_id}"
                st.success(
                    f"✅ Causa **{numero_guardado}** guardada — Carril {clf['carril'].upper()}"
                )
                st.balloons()
                # Set session state so Gestión pre-selects this causa
                st.session_state["gc_busqueda"] = numero_guardado
                st.session_state["causa_sel_id"] = causa_id
                st.rerun()

            if gen_doc or st.session_state.get("doc_generado_nuevo"):
                # Generamos el número provisional para el documento
                numero_prov = f"BORRADOR-{datetime.now().strftime('%H%M%S')}"
                caso_doc = {**caso, "numero": numero_prov}
                if doc_sel == "Dictamen de derivación a mediación":
                    doc = generar_dictamen_mediacion(caso_doc, clf, fiscal_nombre, unidad_key)
                elif doc_sel == "Dictamen de suspensión del proceso a prueba":
                    doc = generar_dictamen_suspension(caso_doc, clf, fiscal_nombre, unidad_key)
                elif "Requerimiento" in doc_sel:
                    doc = generar_requerimiento_apertura(caso_doc, clf, fiscal_nombre, unidad_key)
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

    # ── Causas prioritarias (session-based ⭐ bookmarks) ───────────────────────
    if "gc_prioritarias" not in st.session_state:
        st.session_state["gc_prioritarias"] = set()
    _prio_ids = st.session_state["gc_prioritarias"]
    if _prio_ids:
        with st.expander(f"⭐ Causas prioritarias ({len(_prio_ids)})", expanded=True):
            _prio_causas = [c for c in listar_causas(limit=500) if c["id"] in _prio_ids]
            for _pc in _prio_causas:
                _pc_ic = {"verde":"🟢","amarillo":"🟡","rojo":"🔴"}.get(_pc.get("carril",""),"⚪")
                _pc_est = ESTADOS_LABEL.get(_pc["estado"], _pc["estado"])
                _pc_nom = (_pc.get("apellido_nombre","") or "").split(",")[0]
                _c1_p, _c2_p = st.columns([5, 1])
                _c1_p.markdown(f"{_pc_ic} **{_pc['numero']}** — {_pc_nom} | {_pc_est}")
                if _c2_p.button("✕", key=f"prio_rm_{_pc['id']}", help="Quitar de prioritarias"):
                    _prio_ids.discard(_pc["id"])
                    st.rerun()
        st.markdown("")

    # Filtros — fila 1
    col_f1, col_f2, col_f3, col_f4, col_f5 = st.columns([2,1,1,1,0.6])
    # Pre-fill from sidebar quick-lookup if it just fired
    _rapid_val = st.session_state.pop("busqueda_rapida_causas", None)
    if _rapid_val is not None:
        st.session_state["gc_busqueda"] = _rapid_val
    busqueda  = col_f1.text_input("Buscar por nombre, DNI o N° de causa",
                                   placeholder="Buscar...", label_visibility="collapsed",
                                   key="gc_busqueda")
    filtro_estado = col_f2.selectbox("Estado", ["Todos"] + ESTADOS,
                                      format_func=lambda x: "Todos los estados" if x=="Todos" else ESTADOS_LABEL.get(x,x))
    filtro_carril = col_f3.selectbox("Carril", ["Todos","verde","amarillo","rojo"],
                                      format_func=lambda x: {"Todos":"Todos","verde":"🟢 Verde","amarillo":"🟡 Amarillo","rojo":"🔴 Rojo"}[x])
    filtro_unidad = col_f4.selectbox("Unidad", ["Todas","norte","sur","genero"],
                                      format_func=lambda x: {"Todas":"Todas","norte":"Norte","sur":"Sur","genero":"Género"}[x])
    col_f5.markdown("&nbsp;")   # vertical spacer
    if col_f5.button("✕ Todo", key="gc_clear_all", use_container_width=True,
                     help="Limpiar todos los filtros"):
        for _fk in ("gc_busqueda","gc_filtro_tipo","gc_fecha_desde","gc_fecha_hasta",
                    "gc_solo_rein","gc_filtro_fiscal"):
            if _fk in st.session_state:
                del st.session_state[_fk]
        st.rerun()

    # Filtros — fila 2: tipo infracción + rango de fechas + fiscal (colapsable)
    with st.expander("🔍 Filtros adicionales: tipo, fechas, fiscal y reincidencia", expanded=False):
        from datetime import date as _dt_gc
        _tipo_opciones_gc = {"": "Todos los tipos"} | {
            k: f"{v['categoria']} — {v['label'][:40]}" for k, v in TIPOS_INFRACCION.items()
        }
        _col_tipo_gc, _col_fd_gc, _col_fh_gc, _col_fc_gc = st.columns([2, 1, 1, 1])
        _filtro_tipo = _col_tipo_gc.selectbox(
            "Tipo de infracción",
            options=list(_tipo_opciones_gc.keys()),
            format_func=lambda k: _tipo_opciones_gc[k],
            key="gc_filtro_tipo",
        )
        _gc_fecha_desde = _col_fd_gc.date_input("Desde", value=None, key="gc_fecha_desde")
        _gc_fecha_hasta = _col_fh_gc.date_input("Hasta", value=None, key="gc_fecha_hasta")
        # Fiscal filter — pull distinct fiscales from DB
        _fiscales_gc = sorted({
            c.get("fiscal_asignado","") for c in listar_causas(limit=500)
            if c.get("fiscal_asignado","")
        })
        _fiscal_opciones_gc = ["Todos"] + _fiscales_gc
        _filtro_fiscal = st.selectbox(
            "Fiscal asignado",
            _fiscal_opciones_gc,
            key="gc_filtro_fiscal",
        )
        _gc_solo_rein = st.checkbox(
            "⚠️ Solo reincidentes (personas con más de 1 causa)",
            value=False, key="gc_solo_rein"
        )
        if _col_fc_gc.button("🗑️ Limpiar", key="gc_clear_ext"):
            for _k in ("gc_filtro_tipo", "gc_fecha_desde", "gc_fecha_hasta",
                       "gc_solo_rein", "gc_filtro_fiscal"):
                if _k in st.session_state:
                    del st.session_state[_k]
            st.rerun()
    _fecha_desde_str = _gc_fecha_desde.isoformat() if _gc_fecha_desde else None
    _fecha_hasta_str = _gc_fecha_hasta.isoformat() if _gc_fecha_hasta else None
    _fiscal_filtro = None if _filtro_fiscal == "Todos" else _filtro_fiscal

    causas = listar_causas(
        estado          = None if filtro_estado=="Todos"  else filtro_estado,
        carril          = None if filtro_carril=="Todos"  else filtro_carril,
        unidad          = None if filtro_unidad=="Todas"  else filtro_unidad,
        busqueda        = busqueda or None,
        tipo_infraccion = _filtro_tipo or None,
        fecha_desde     = _fecha_desde_str,
        fiscal          = _fiscal_filtro,
        fecha_hasta     = _fecha_hasta_str,
    )

    # Apply reincidente filter in-memory after bulk persona count
    if _gc_solo_rein and causas:
        _pids_rein = list({c["persona_id"] for c in causas if c.get("persona_id")})
        _cnt_rein  = causas_count_por_persona(_pids_rein) if _pids_rein else {}
        causas = [c for c in causas if _cnt_rein.get(c.get("persona_id"), 0) > 1]

    if not causas:
        _active_filters = [x for x in [busqueda, filtro_estado if filtro_estado != "Todos" else None,
                           filtro_carril if filtro_carril != "Todos" else None,
                           filtro_unidad if filtro_unidad != "Todas" else None] if x]
        if _active_filters:
            st.warning(f"🔍 No hay causas que coincidan con los filtros activos. Probá limpiarlos con el botón '✕ Todo'.")
        else:
            st.info("📂 No hay causas en el sistema todavía. Ingresá un caso nuevo en **📋 Nuevo Caso** o cargá los casos demo desde **🗂️ Casos Demo**.")
    else:
        from collections import Counter as _Cnt
        _cnt = _Cnt(c.get("carril","") for c in causas)
        _cnt_est = _Cnt(c.get("estado","") for c in causas)

        _sum_col, _ord_col, _vista_col = st.columns([3, 1, 1])
        _sum_col.markdown(
            f"**{len(causas)} causa{'s' if len(causas)!=1 else ''}** &nbsp;—&nbsp; "
            f"🟢 {_cnt.get('verde',0)} &nbsp; 🟡 {_cnt.get('amarillo',0)} &nbsp; 🔴 {_cnt.get('rojo',0)} "
            f"&nbsp;|&nbsp; "
            f"Ingresadas: {_cnt_est.get('ingresada',0)} &nbsp; "
            f"Notificadas: {_cnt_est.get('notificada',0)} &nbsp; "
            f"Resueltas: {_cnt_est.get('resuelta',0)}",
        )
        _orden = _ord_col.selectbox(
            "Ordenar por",
            ["Recientes", "Más antiguas", "Carril", "Estado", "🚨 Urgencia", "Fiscal"],
            label_visibility="collapsed", key="causas_orden"
        )
        _vista_gc = _vista_col.radio(
            "Vista", ["📋 Detalle", "📊 Tabla", "🗂️ Kanban"],
            horizontal=True, label_visibility="collapsed", key="causas_vista"
        )
        if _orden == "Más antiguas":
            causas = sorted(causas, key=lambda x: x.get("created_at",""))
        elif _orden == "Carril":
            _carril_ord = {"rojo": 0, "amarillo": 1, "verde": 2}
            causas = sorted(causas, key=lambda x: _carril_ord.get(x.get("carril",""), 3))
        elif _orden == "Estado":
            causas = sorted(causas, key=lambda x: ESTADOS.index(x["estado"]) if x["estado"] in ESTADOS else 99)
        elif _orden == "🚨 Urgencia":
            # Urgency score: days inactive + carril rojo bonus + reincidente bonus
            def _urgencia_score(c):
                score = 0
                # Days without activity
                if c["estado"] in {"ingresada","clasificada","notificada","en_mediacion"}:
                    try:
                        _upd_u = datetime.strptime(c["updated_at"][:16], "%Y-%m-%d %H:%M")
                        _d_u = (datetime.now() - _upd_u).days
                        if _d_u > 30:
                            score += 3
                        elif _d_u > 14:
                            score += 2
                        elif _d_u > 7:
                            score += 1
                    except Exception:
                        pass
                # Carril rojo = higher urgency
                if c.get("carril") == "rojo":
                    score += 2
                elif c.get("carril") == "amarillo":
                    score += 1
                # Reincidente
                if _pers_cnt_gc.get(c.get("persona_id"), 0) > 1:
                    score += 1
                return -score  # descending
            # Need _pers_cnt_gc available — compute it now if not yet in scope
            _pids_urg = list({c["persona_id"] for c in causas if c.get("persona_id")})
            _pers_cnt_gc = causas_count_por_persona(_pids_urg) if _pids_urg else {}
            causas = sorted(causas, key=_urgencia_score)
        elif _orden == "Fiscal":
            causas = sorted(causas, key=lambda x: (x.get("fiscal_asignado","") or ""))

        # ── Resumen rápido del filtro actual ──────────────────────────────
        if causas:
            _n_total_gc    = len(causas)
            _n_activos_gc  = sum(1 for c in causas if c["estado"] in {"ingresada","clasificada","notificada","en_mediacion"})
            _n_resueltos_gc= sum(1 for c in causas if c["estado"] == "resuelta")
            _n_archivados_gc= sum(1 for c in causas if c["estado"] == "archivada")
            _n_verde_gc    = sum(1 for c in causas if c.get("carril") == "verde")
            _n_amarillo_gc = sum(1 for c in causas if c.get("carril") == "amarillo")
            _n_rojo_gc     = sum(1 for c in causas if c.get("carril") == "rojo")
            _personas_gc   = {c["persona_id"] for c in causas if c.get("persona_id")}
            _n_personas_gc = len(_personas_gc)
            _sm1, _sm2, _sm3, _sm4, _sm5, _sm6, _sm7 = st.columns(7)
            _sm1.metric("Total causas", _n_total_gc)
            _sm2.metric("👤 Personas", _n_personas_gc,
                        help="Personas únicas en la vista actual")
            _sm3.metric("Activas", _n_activos_gc)
            _sm4.metric("Resueltas", _n_resueltos_gc)
            _sm5.metric("🟢 Verde", _n_verde_gc)
            _sm6.metric("🟡 Amarillo", _n_amarillo_gc)
            _sm7.metric("🔴 Rojo", _n_rojo_gc)
        else:
            st.info("No se encontraron causas con los filtros actuales.")

        # ── Vista Kanban (pipeline por estado) ────────────────────────────
        if _vista_gc == "🗂️ Kanban":
            _kanban_estados = ["ingresada","clasificada","notificada","en_mediacion","resuelta","archivada"]
            _kanban_labels  = ["📥 Ingresada","🔍 Clasificada","📬 Notificada","🤝 Mediación","✅ Resuelta","🗄️ Archivada"]
            _kanban_cols = st.columns(len(_kanban_estados))
            for _kcol, _kest, _klbl in zip(_kanban_cols, _kanban_estados, _kanban_labels):
                _kcausas = [c for c in causas if c.get("estado") == _kest]
                _kcol.markdown(f"**{_klbl}** ({len(_kcausas)})")
                _kcol.markdown("---")
                for _kc in _kcausas[:8]:  # limit 8 per column for readability
                    _kic = {"verde":"🟢","amarillo":"🟡","rojo":"🔴"}.get(_kc.get("carril",""),"⚪")
                    _knom = (_kc.get("apellido_nombre","") or "").split(",")[0]
                    _kcol.markdown(
                        f"<div style='background:#f8f9fa;border-left:3px solid "
                        f"{'#28a745' if _kc.get('carril')=='verde' else '#ffc107' if _kc.get('carril')=='amarillo' else '#dc3545'}"
                        f";padding:5px 8px;margin:3px 0;border-radius:0 4px 4px 0;font-size:0.78rem'>"
                        f"{_kic} <strong>{_kc['numero'][:12]}</strong><br>"
                        f"<span style='color:#555'>{_knom[:18]}</span>"
                        f"</div>",
                        unsafe_allow_html=True
                    )
                if len(_kcausas) > 8:
                    _kcol.caption(f"+ {len(_kcausas)-8} más…")

        # ── Vista tabla compacta ───────────────────────────────────────────
        if _vista_gc == "📊 Tabla":
            # Pre-fetch next hearing per causa for the table display
            _prox_auds = proximas_audiencias_por_causa()
            _rows_gc = []
            _activos_gc = {"ingresada", "clasificada", "notificada", "en_mediacion"}
            for c in causas:
                _ic = {"verde":"🟢","amarillo":"🟡","rojo":"🔴"}.get(c.get("carril",""),"⚪")
                # Days since last update (only for active cases)
                _dias_inact_gc = None
                if c.get("estado") in _activos_gc:
                    try:
                        _upd_gc = datetime.strptime(c["updated_at"][:16], "%Y-%m-%d %H:%M")
                        _dias_inact_gc = (datetime.now() - _upd_gc).days
                    except Exception:
                        pass
                # Next scheduled hearing
                _prox = _prox_auds.get(c["id"])
                if _prox:
                    try:
                        from datetime import date as _dtgc
                        _prox_dt = _dtgc.fromisoformat(_prox["fecha"])
                        _prox_dias = (_prox_dt - _dtgc.today()).days
                        if _prox_dias == 0:
                            _prox_str = f"⚡ HOY {_prox['hora']}"
                        elif _prox_dias == 1:
                            _prox_str = f"🔵 Mañana {_prox['hora']}"
                        elif _prox_dias <= 7:
                            _prox_str = f"🔵 {_prox['fecha']} ({_prox_dias}d)"
                        else:
                            _prox_str = f"{_prox['fecha']} ({_prox_dias}d)"
                    except Exception:
                        _prox_str = f"{_prox['fecha']} {_prox['hora']}"
                else:
                    _prox_str = ""
                _rows_gc.append({
                    "Carril":        _ic,
                    "Expediente":    c["numero"],
                    "Imputado/a":    (c.get("apellido_nombre","") or "").split(",")[0],
                    "Edad":          c.get("persona_edad","") or "",
                    "DNI":           c.get("persona_dni",""),
                    "Infracción":    TIPOS_INFRACCION.get(c.get("tipo_infraccion",""),{}).get("label","")[:30],
                    "Estado":        ESTADOS_LABEL.get(c["estado"], c["estado"]),
                    "Próximo paso":  (
                        {"verde":"Citar mediación","amarillo":"Citar suspensión","rojo":"Requerimiento"}.get(c.get("carril",""),"Notificar")
                        if c.get("estado") == "clasificada"
                        else "Registrar seguimiento" if c.get("estado") == "resuelta"
                        else {"ingresada":"Clasificar (triage)","notificada":"Programar audiencia",
                              "en_mediacion":"Suscribir acta","archivada":"—"}.get(c.get("estado",""), "")
                    ),
                    "Próx. audiencia": _prox_str,
                    "Unidad":        {"norte":"Norte","sur":"Sur","genero":"Género"}.get(c.get("unidad",""),""),
                    "Fiscal":        c.get("fiscal_asignado",""),
                    "Ingresada":     c.get("created_at","")[:10],
                    "Sin mov. (d)":  (f"🔴 {_dias_inact_gc}d" if _dias_inact_gc and _dias_inact_gc > 30
                                       else f"🟠 {_dias_inact_gc}d" if _dias_inact_gc and _dias_inact_gc > 14
                                       else f"🟡 {_dias_inact_gc}d" if _dias_inact_gc and _dias_inact_gc > 7
                                       else f"{_dias_inact_gc}d" if _dias_inact_gc is not None else ""),
                })
            st.dataframe(
                pd.DataFrame(_rows_gc),
                use_container_width=True,
                hide_index=True,
                column_config={
                    "Carril": st.column_config.TextColumn("", width="small"),
                    "Expediente": st.column_config.TextColumn("Expediente", width="medium"),
                    "Próx. audiencia": st.column_config.TextColumn(
                        "Próx. audiencia", help="Próxima audiencia programada (fecha + hora)"
                    ),
                    "Sin mov. (d)": st.column_config.TextColumn(
                        "Sin mov.",
                        help="🔴>30d · 🟠>14d · 🟡>7d · verde=reciente (solo causas activas)",
                        width="small",
                    ),
                }
            )
            st.caption("💡 Cambiá a vista '📋 Detalle' para acceder a acciones, documentos y gestión de estado.")
            # CSV export for the current filtered view
            import io as _io_gc
            _csv_buf = _io_gc.StringIO()
            pd.DataFrame(_rows_gc).to_csv(_csv_buf, index=False, encoding="utf-8")
            st.download_button(
                "⬇️ Exportar lista (CSV)",
                data=_csv_buf.getvalue().encode("utf-8"),
                file_name=f"causas_filtradas_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
                mime="text/csv",
                key="gc_csv_export",
            )

        # ── Vista detalle (expanders) ──────────────────────────────────────
        # Selector de causa para ver detalle
        causa_sel_id = st.session_state.get("causa_sel_id")

        # Bulk reincidente lookup — single query for all personas in current view
        _pids_gc = list({c["persona_id"] for c in causas if c.get("persona_id")})
        _pers_cnt_gc = causas_count_por_persona(_pids_gc) if _pids_gc else {}

        for c in causas:
            if _vista_gc in ("📊 Tabla", "🗂️ Kanban"):
                continue   # ya renderizados arriba
            carril_icon = {"verde":"🟢","amarillo":"🟡","rojo":"🔴"}.get(c.get("carril",""),"⚪")
            estado_label = ESTADOS_LABEL.get(c["estado"], c["estado"])
            infraccion_label = TIPOS_INFRACCION.get(c["tipo_infraccion"],{}).get("label", c["tipo_infraccion"])
            unidad_label = {"norte":"Norte","sur":"Sur","genero":"Género"}.get(c.get("unidad",""),"")

            # Reincidente badge when persona has more than one causa in the system
            _rein_badge_gc = "  ⚠️ Rein." if _pers_cnt_gc.get(c.get("persona_id"), 0) > 1 else ""

            # Days in current state — only meaningful for active states
            _dias_badge = ""
            if c["estado"] in {"ingresada", "clasificada", "notificada", "en_mediacion"}:
                try:
                    _upd = datetime.strptime(c["updated_at"][:16], "%Y-%m-%d %H:%M")
                    _dias_est = (datetime.now() - _upd).days
                    _dias_badge = (f"  🔴 {_dias_est}d sin actualizar" if _dias_est > 30 else
                                   f"  🟡 {_dias_est}d" if _dias_est > 7 else "")
                except Exception:
                    pass

            with st.expander(
                f"{carril_icon} **{c['numero']}** — {c['apellido_nombre']}  |  {infraccion_label}  |  {estado_label}{_dias_badge}{_rein_badge_gc}",
                expanded=(causa_sel_id == c["id"])
            ):
                col_info, col_acciones = st.columns([2,1])

                with col_info:
                    _col_dni, _col_pfil = st.columns([3, 1])
                    _inf_gc = TIPOS_INFRACCION.get(c.get("tipo_infraccion",""), {})
                    _art_gc = _inf_gc.get("articulo","")
                    _cat_gc = _inf_gc.get("categoria","")
                    _art_str = f"  |  **Art.:** {_art_gc}" if _art_gc else ""
                    _cat_str = f"  |  [{_cat_gc}]" if _cat_gc else ""
                    _col_dni.markdown(f"**DNI:** {c['persona_dni']}  |  **Unidad:** {unidad_label}  |  **Fiscal:** {c.get('fiscal_asignado','—')}{_art_str}{_cat_str}")
                    if _col_pfil.button("👤 Ver perfil", key=f"pfil_{c['id']}", use_container_width=True):
                        st.session_state["perfil_busqueda"] = c["persona_dni"]
                        st.session_state["goto_perfil"] = True
                    _tel_raw = c.get("persona_telefono") or ""
                    if _tel_raw:
                        _tel_digits = "".join(ch for ch in _tel_raw if ch.isdigit())
                        _tel = f"[{_tel_raw}](tel:{_tel_digits})" if _tel_digits else _tel_raw
                    else:
                        _tel = "—"
                    _dom = c.get("persona_domicilio") or "—"
                    # Build Google Maps link for the domicilio
                    if _dom and _dom != "—":
                        from urllib.parse import quote as _urlencode
                        _maps_addr = _urlencode(f"{_dom}, Córdoba, Argentina")
                        _maps_url = f"https://www.google.com/maps/search/?api=1&query={_maps_addr}"
                        _dom_display = f"[{_dom}]({_maps_url})"
                    else:
                        _dom_display = "—"
                    st.markdown(f"📞 **Tel.:** {_tel}  |  🏠 **Dom.:** {_dom_display}")
                    st.markdown(f"**Descripción:** {c.get('descripcion') or '—'}")
                    _fh = c.get("fecha_hecho","")
                    _fecha_hecho_str = _fh[:10] if _fh else "—"
                    # Estimated resolution date based on carril
                    _resol_est = ""
                    if c.get("estado") not in ("resuelta", "archivada") and c.get("carril"):
                        _dias_est_carril = {"verde": 20, "amarillo": 45, "rojo": 90}.get(c.get("carril",""), 45)
                        try:
                            _created_dt = datetime.strptime(c["created_at"][:10], "%Y-%m-%d")
                            _resol_date = _created_dt + timedelta(days=_dias_est_carril)
                            _resol_est = f"  |  📆 **Res. estimada:** {_resol_date.strftime('%d/%m/%Y')}"
                        except Exception:
                            pass
                    st.markdown(f"**Fecha del hecho:** {_fecha_hecho_str}  |  **Ingresada:** {c['created_at'][:10]}{_resol_est}")

                    # Siguiente paso sugerido — guía contextual según estado/carril
                    _pasos_gc = {
                        "ingresada":    ("📋", "Clasificar la causa para determinar el carril (triage)"),
                        "notificada":   ("📅", "Programar audiencia inicial"),
                        "en_mediacion": ("✍️", "Suscribir acta de compromiso o solicitar suspensión a prueba"),
                        "archivada":    ("✅", "Causa finalizada — sin acciones pendientes"),
                    }
                    if c["estado"] == "clasificada":
                        if c.get("carril") == "verde":
                            _paso_gc = ("📨", "Enviar cédula de citación a **mediación**")
                        elif c.get("carril") == "rojo":
                            _paso_gc = ("⚖️", "Notificar al imputado/a y preparar **requerimiento de apertura** del proceso")
                        else:
                            _paso_gc = ("📨", "Enviar cédula de notificación de **suspensión a prueba**")
                    elif c["estado"] == "resuelta":
                        _seg_ps = get_seguimiento_por_causa(c["id"])
                        if _seg_ps:
                            _paso_gc = ("✅", "Seguimiento registrado — controlar cumplimiento de condiciones")
                        else:
                            _paso_gc = ("🔍", "Registrar **seguimiento** de condiciones si corresponde")
                    else:
                        _paso_gc = _pasos_gc.get(c["estado"])
                    if _paso_gc:
                        _ps_ico, _ps_txt = _paso_gc
                        st.caption(f"{_ps_ico} **Siguiente paso:** {_ps_txt}")

                    # Timeline
                    timeline = get_timeline(c["id"])
                    if timeline:
                        st.markdown("**Historial de estados:**")
                        for t in timeline:
                            _es_nota = t.get("estado_anterior") == t.get("estado_nuevo") and t.get("estado_anterior")
                            if _es_nota:
                                st.markdown(
                                    f"<div class='timeline-item' style='border-color:#6c757d'>"
                                    f"📝 {t['created_at'][:16]}  —  {t.get('usuario','')}: "
                                    f"<em>{t.get('observaciones','')}</em></div>",
                                    unsafe_allow_html=True
                                )
                            else:
                                ant = ESTADOS_LABEL.get(t["estado_anterior"],"—") if t["estado_anterior"] else "—"
                                nvo = ESTADOS_LABEL.get(t["estado_nuevo"], t["estado_nuevo"])
                                obs = f" — {t['observaciones']}" if t.get("observaciones") else ""
                                st.markdown(
                                    f"<div class='timeline-item'>{t['created_at'][:16]}  →  {ant} ➜ {nvo}{obs}</div>",
                                    unsafe_allow_html=True
                                )

                    # Próxima audiencia badge
                    _prox_aud_gc = _prox_auds.get(c["id"])
                    if _prox_aud_gc:
                        from agenda_tab import TIPO_LABEL as _tl_gc
                        st.markdown(
                            f"<div style='border-left:3px solid #007bff;padding:3px 10px;"
                            f"margin:2px 0;background:#e7f3ff;border-radius:0 4px 4px 0;font-size:0.82rem'>"
                            f"📅 <strong>Próxima audiencia:</strong> {_prox_aud_gc['fecha']} {_prox_aud_gc['hora']} — "
                            f"{_tl_gc.get(_prox_aud_gc.get('tipo',''), _prox_aud_gc.get('tipo',''))}"
                            f"</div>",
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
                    # Prioritaria toggle
                    _is_prio = c["id"] in _prio_ids
                    _prio_lbl = "⭐ Prioritaria" if _is_prio else "☆ Marcar prioritaria"
                    if st.button(_prio_lbl, key=f"prio_{c['id']}", use_container_width=True,
                                 type="secondary"):
                        if _is_prio:
                            _prio_ids.discard(c["id"])
                        else:
                            _prio_ids.add(c["id"])
                        st.session_state["gc_prioritarias"] = _prio_ids
                        st.rerun()

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
                        # Closing note for archivada transition
                        if nuevo_estado == "archivada":
                            _cierre_templates = [
                                "— Seleccioná o escribí el motivo de cierre —",
                                "Seguimiento de condiciones completado satisfactoriamente.",
                                "Causa archivada por falta de mérito procesal.",
                                "Imputado/a cumplió con las condiciones impuestas.",
                                "Causa archivada a solicitud de la parte damnificada.",
                                "Archivada por prescripción de la acción contravencional.",
                            ]
                            _cierre_sel = st.selectbox("Motivo de cierre", _cierre_templates,
                                                        key=f"cierre_motivo_{c['id']}")
                            if _cierre_sel != _cierre_templates[0] and not obs_estado:
                                obs_estado = _cierre_sel
                        if st.button("Actualizar estado", key=f"upd_{c['id']}", use_container_width=True):
                            avanzar_estado(c["id"], nuevo_estado, fiscal_nombre, obs_estado)
                            st.cache_data.clear()
                            st.success(f"Estado actualizado a {ESTADOS_LABEL[nuevo_estado]}")
                            st.rerun()
                    else:
                        st.info("Causa archivada")

                    st.markdown("---")
                    st.markdown("**📝 Nota rápida:**")
                    with st.popover("Agregar nota a la causa", use_container_width=True):
                        _nota_templates = [
                            "— Template rápido (opcional) —",
                            "Imputado/a se comunicó. Se coordina próxima audiencia.",
                            "Intento de contacto sin respuesta. Se enviará nueva notificación.",
                            "Documentación presentada. Se procesa para el expediente.",
                            "Solicitud de prórroga recibida. Se evalúa viabilidad.",
                            "Imputado/a ausente a la audiencia. Se registra incomparecencia.",
                            "Acuerdo alcanzado en mediación. Se confecciona acta.",
                        ]
                        _nota_tpl_sel = st.selectbox("Template", _nota_templates,
                                                      key=f"nota_tpl_{c['id']}",
                                                      label_visibility="collapsed")
                        _nota_init = "" if _nota_tpl_sel == _nota_templates[0] else _nota_tpl_sel
                        _nota_txt = st.text_area("Texto de la nota", height=80,
                                                  value=_nota_init,
                                                  placeholder="Ej: Imputado se comunicó para avisar viaje. Se reprograma notificación.",
                                                  key=f"nota_txt_{c['id']}")
                        if st.button("Guardar nota", key=f"nota_btn_{c['id']}", type="primary"):
                            if _nota_txt and _nota_txt.strip():
                                agregar_nota_causa(c["id"], _nota_txt, fiscal_nombre)
                                st.cache_data.clear()
                                st.success("Nota registrada en el historial")
                                st.rerun()
                            else:
                                st.warning("Ingresá el texto de la nota.")

                    st.markdown("---")
                    with st.popover("📋 Datos para citar/referir", use_container_width=True):
                        _tel_disp = c.get("persona_telefono") or "No registrado"
                        _dom_disp = c.get("persona_domicilio") or "No registrado"
                        _inf_disp = TIPOS_INFRACCION.get(c.get("tipo_infraccion",""),{}).get("label","")
                        _art_disp = TIPOS_INFRACCION.get(c.get("tipo_infraccion",""),{}).get("articulo","")
                        st.code(
                            f"Expediente: {c['numero']}\n"
                            f"Imputado/a: {c['apellido_nombre']}\n"
                            f"DNI: {c['persona_dni']}\n"
                            f"Tel.: {_tel_disp}\n"
                            f"Dom.: {_dom_disp}\n"
                            f"Infracción: {_inf_disp} ({_art_disp})\n"
                            f"Fiscal: {c.get('fiscal_asignado','')}\n"
                            f"Estado: {ESTADOS_LABEL.get(c['estado'], c['estado'])}",
                            language=None
                        )
                        st.caption("Seleccioná el texto y copialo con Ctrl+C / Cmd+C")

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
                            st.cache_data.clear()
                            st.success(f"Audiencia agendada para {_fecha_aud.strftime('%d/%m/%Y')} {_hora_aud.strftime('%H:%M')}")
                            st.rerun()

                    st.markdown("---")
                    st.markdown("**📋 Expediente completo:**")
                    try:
                        from pdf_gen import pdf_expediente_causa as _pec
                        _timeline_exp  = get_timeline(c["id"])
                        _auds_exp      = listar_audiencias(causa_id=c["id"])
                        _segs_exp      = listar_seguimientos()
                        _segs_exp      = [s for s in _segs_exp if s.get("causa_id") == c["id"]]
                        _cond_map_exp  = {s["id"]: get_condiciones(s["id"]) for s in _segs_exp}
                        _causa_full    = get_causa(c["id"]) or c
                        _pdf_exp = _pec(
                            _causa_full, _timeline_exp, _auds_exp,
                            _segs_exp, _cond_map_exp, fiscal_nombre
                        )
                        st.download_button(
                            "⬇️ Expediente completo (PDF)",
                            data=_pdf_exp,
                            file_name=f"{c['numero']}_expediente.pdf",
                            mime="application/pdf",
                            key=f"dl_exp_{c['id']}",
                            use_container_width=True,
                        )
                    except Exception as _e_exp:
                        st.caption(f"PDF no disponible: {_e_exp}")

                    st.markdown("---")
                    st.markdown("**👨‍⚖️ Fiscal asignado:**")
                    with st.popover("Reasignar fiscal", use_container_width=True):
                        _fiscal_actual = c.get("fiscal_asignado","")
                        _nuevo_fiscal = st.text_input(
                            "Nombre del fiscal",
                            value=_fiscal_actual,
                            placeholder="Ej: Dr. Carlos Medina",
                            key=f"reasig_fiscal_{c['id']}",
                        )
                        if st.button("Guardar", key=f"reasig_btn_{c['id']}", type="primary"):
                            if _nuevo_fiscal.strip():
                                asignar_fiscal(c["id"], _nuevo_fiscal.strip())
                                agregar_nota_causa(
                                    c["id"],
                                    f"Causa reasignada al fiscal: {_nuevo_fiscal.strip()}.",
                                    fiscal_nombre,
                                )
                                st.cache_data.clear()
                                st.success(f"Reasignada a {_nuevo_fiscal.strip()}")
                                st.rerun()
                            else:
                                st.warning("Ingresá el nombre del fiscal.")

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
                    elif c.get("carril") == "rojo":
                        doc_opts_causa = ["Requerimiento de apertura del proceso", "Cédula de citación a audiencia",
                                          "Resumen ejecutivo"]
                        if c.get("estado") in ("resuelta", "archivada"):
                            doc_opts_causa += ["Informe de incumplimiento"]
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
                        elif "Requerimiento" in doc_tipo:
                            doc_txt = generar_requerimiento_apertura(caso_stored, clf_stored, fiscal_nombre, caso_stored["unidad"])
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
    st.subheader("🗂️ Casos de demostración")
    st.markdown("Casos representativos de una semana típica. Cargalos al sistema con un clic para explorar el flujo completo.")

    # Check which demo cases are already in the DB (by numero)
    _numeros_en_db = {c["numero"] for c in listar_causas(limit=500)}
    _n_cargados = sum(1 for cd in CASOS_DEMO if cd.get("numero","") in _numeros_en_db)
    _n_total_demo = len(CASOS_DEMO)

    _demo_col1, _demo_col2, _demo_col3 = st.columns([2, 1, 1])
    _demo_col1.progress(_n_cargados / _n_total_demo if _n_total_demo else 0,
                        text=f"{_n_cargados} / {_n_total_demo} casos cargados")
    if _n_cargados < _n_total_demo:
        if _demo_col2.button("📥 Cargar todos los casos", key="demo_cargar_todos",
                              use_container_width=True, type="primary"):
            _cargados_now = 0
            for cd in CASOS_DEMO:
                if cd.get("numero","") not in _numeros_en_db:
                    _clf_all = clasificar_caso(cd["tipo"], cd["antecedentes"], False)
                    guardar_causa(
                        {**cd, "victima": False, "lesiones": False, "resistencia": False, "domicilio": ""},
                        _clf_all, fiscal_nombre
                    )
                    _cargados_now += 1
            st.cache_data.clear()
            st.success(f"✅ {_cargados_now} caso(s) adicionales cargados al sistema.")
            st.rerun()
    else:
        _demo_col2.success("✅ Todos los casos demo están cargados")
    if _demo_col3.button("🗑️ Limpiar todos", key="demo_limpiar_todos",
                          use_container_width=True,
                          help="Restablecer todos los datos de demostración"):
        reset_db()
        init_db()
        poblar()
        st.cache_data.clear()
        st.rerun()

    st.divider()
    for i, cd in enumerate(CASOS_DEMO):
        inf  = TIPOS_INFRACCION.get(cd["tipo"], {})
        clf  = clasificar_caso(cd["tipo"], cd["antecedentes"], False)
        _ya_cargada = cd.get("numero","") in _numeros_en_db

        with st.expander(
            f"{clf['icono']} {cd['numero']} — {cd['imputado']}  |  {inf.get('label','')}"
            + (" ✅" if _ya_cargada else ""),
            expanded=(i==0)
        ):
            col1, col2 = st.columns([3,1])
            with col1:
                st.markdown(f"**Descripción:** {cd['descripcion']}")
                st.markdown(f"**Antecedentes previos:** {cd['antecedentes']}")
                st.markdown(f"**Unidad:** {UNIDADES[cd['unidad']]}")
                if _ya_cargada:
                    st.success("✅ Ya cargada en el sistema")
            with col2:
                st.markdown(f"""<div class="carril-{clf['carril']}">
<strong>{clf['icono']} {clf['accion']}</strong></div>""", unsafe_allow_html=True)

            col_b1, col_b2, col_b3 = st.columns(3)

            if _ya_cargada:
                col_b1.button("✅ Ya en el sistema", key=f"carga_{i}",
                              use_container_width=True, disabled=True)
            elif col_b1.button("📥 Cargar al sistema", key=f"carga_{i}", use_container_width=True):
                causa_id = guardar_causa(
                    {**cd, "victima": False, "lesiones": False, "resistencia": False, "domicilio": ""},
                    clf, fiscal_nombre
                )
                st.cache_data.clear()
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
    seg_s = _c_stats_seguimiento()
    aud_s = _c_stats_audiencias()

    # Quick system health bar
    if total > 0:
        _health_issues = []
        if seg_s.get("vencidos", 0) > 0:
            _health_issues.append(f"🔴 {seg_s['vencidos']} seguimiento(s) vencido(s)")
        if seg_s.get("incumplidos", 0) > 0:
            _health_issues.append(f"🔴 {seg_s['incumplidos']} incumplido(s)")
        if aud_s.get("hoy", 0) > 0:
            _health_issues.append(f"🟡 {aud_s['hoy']} audiencia(s) HOY")
        _sin_aud_h = _c_sin_audiencia()
        if _sin_aud_h:
            _health_issues.append(f"🟡 {len(_sin_aud_h)} sin audiencia")
        if not _health_issues:
            st.success("✅ Sistema en estado normal — sin alertas críticas")
        elif any("🔴" in h for h in _health_issues):
            st.error("🚨 **Alertas críticas:** " + " | ".join(_health_issues))
        else:
            st.warning("⚠️ **Atención:** " + " | ".join(_health_issues))

    if total == 0:
        st.info("Aún no hay causas en el sistema. Ingresá casos nuevos o cargá los demos desde la pestaña 🗂️.")
    else:
        # Weekly pulse
        try:
            from datetime import date as _dpanel
            _lunes_panel = (_dpanel.today() - timedelta(days=_dpanel.today().weekday())).isoformat()
            _nuevas_sem_p = len(listar_causas(fecha_desde=_lunes_panel, limit=200))
            _auds_sem_p   = len(listar_audiencias(desde=_lunes_panel))
            _cerradas_sem_p = len([c for c in listar_causas(fecha_desde=_lunes_panel, limit=200)
                                   if c.get("estado") in ("resuelta","archivada")])
            if _nuevas_sem_p > 0 or _auds_sem_p > 0:
                _pwk1, _pwk2, _pwk3 = st.columns(3)
                _pwk1.metric("📥 Nuevas esta semana", _nuevas_sem_p)
                _pwk2.metric("📅 Audiencias esta semana", _auds_sem_p)
                _pwk3.metric("✅ Cerradas esta semana", _cerradas_sem_p)
        except Exception:
            pass

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

        # Mes actual vs. anterior
        _mom = causas_mes_actual_vs_anterior()
        _delta_lbl = (f"+{_mom['delta']}" if _mom["delta"] >= 0 else str(_mom["delta"]))
        _pct_lbl   = (f" ({_mom['pct_cambio']:+d}% vs. mes anterior)" if _mom["pct_cambio"] is not None else "")
        _col_mom_txt = (
            f"📅 **Este mes:** {_mom['actual']} causas &nbsp;|&nbsp; "
            f"Mes anterior: {_mom['anterior']} &nbsp;|&nbsp; "
            f"Diferencia: **{_delta_lbl}{_pct_lbl}**"
        )
        if _mom["delta"] > 0:
            st.warning(_col_mom_txt)
        elif _mom["delta"] < 0:
            st.success(_col_mom_txt)
        else:
            st.info(_col_mom_txt)

        # Resumen ejecutivo en lenguaje natural
        with st.expander("📝 Resumen ejecutivo automático", expanded=False):
            _activas_n = (stats["por_estado"].get("clasificada",0)
                          + stats["por_estado"].get("notificada",0)
                          + stats["por_estado"].get("en_mediacion",0))
            _resueltas_n = (stats["por_estado"].get("resuelta",0)
                            + stats["por_estado"].get("archivada",0))
            _pct_no_pun = round((verde_n + amarillo_n)*100/total) if total else 0
            _seg_s = stats_seguimiento()
            _aud_s = stats_audiencias()
            _sin_a = causas_sin_audiencia_programada()

            _partes = [
                f"El sistema SIATC registra **{total} causas contravencionales** en total, "
                f"de las cuales **{_activas_n} se encuentran activas** (clasificadas, notificadas o en mediación) "
                f"y **{_resueltas_n} han sido resueltas o archivadas**.",

                f"El triaje automático derivó el **{_pct_no_pun}%** de las causas a vías no punitivas "
                f"({verde_n} a mediación 🟢, {amarillo_n} a suspensión a prueba 🟡, {rojo_n} a proceso pleno 🔴).",
            ]

            if _aud_s["hoy"] > 0:
                _partes.append(f"⚡ **{_aud_s['hoy']} audiencia(s) HOY** requieren gestión inmediata.")
            if _seg_s["vencidos"] > 0:
                _partes.append(f"⚠️ **{_seg_s['vencidos']} seguimiento(s) vencido(s)** sin cierre formal.")
            if _seg_s["incumplidos"] > 0:
                _partes.append(f"❌ **{_seg_s['incumplidos']} seguimiento(s) incumplido(s)** — evaluar revocación.")
            if _sin_a:
                _partes.append(f"📋 **{len(_sin_a)} causa(s) activa(s)** sin audiencia programada.")
            if stats["reincidentes"] > 0:
                _partes.append(f"🔄 **{stats['reincidentes']} persona(s) reincidente(s)** en el padrón.")
            _sin_seg_exec = _c_sin_seguimiento()
            if _sin_seg_exec:
                _partes.append(f"🔍 **{len(_sin_seg_exec)} causa(s) resuelta(s)** sin seguimiento registrado — revisión recomendada.")
            if _seg_s["activos"] > 0:
                _partes.append(f"📋 **{_seg_s['activos']} seguimiento(s) activo(s)** en curso ({_seg_s['cumplidos']} ya cumplidos).")
            if _mom["pct_cambio"] is not None:
                _tend = "en aumento" if _mom["delta"] > 0 else ("en baja" if _mom["delta"] < 0 else "estable")
                _partes.append(
                    f"La actividad mensual está **{_tend}** "
                    f"({_mom['actual']} causas este mes vs. {_mom['anterior']} el mes anterior, "
                    f"{'+'if _mom['delta']>=0 else ''}{_mom['delta']})."
                )

            for _p in _partes:
                st.markdown(f"• {_p}")

            # Automated recommendations
            _recomendaciones = []
            if _seg_s["vencidos"] > 0:
                _recomendaciones.append("Cerrar los seguimientos vencidos o registrar la prórroga si corresponde.")
            if _sin_a and len(_sin_a) > 2:
                _recomendaciones.append(f"Programar audiencias para las {len(_sin_a)} causas sin audiencia pendiente.")
            if _seg_s["incumplidos"] > 0:
                _recomendaciones.append("Evaluar revocación de la suspensión para los seguimientos incumplidos.")
            if _mom.get("delta", 0) > 0 and _mom["delta"] > 2:
                _recomendaciones.append("El ingreso de causas supera al mes anterior — considerar redistribución de carga entre fiscales.")
            if _sin_seg_exec and len(_sin_seg_exec) > 3:
                _recomendaciones.append(f"Registrar el seguimiento de condiciones para las {len(_sin_seg_exec)} causas resueltas sin registro.")
            if _recomendaciones:
                st.markdown("**💡 Recomendaciones automáticas:**")
                for _r in _recomendaciones:
                    st.markdown(f"→ {_r}")

            _ts_res = f"_{datetime.now().strftime('%d/%m/%Y %H:%M')} — generado automáticamente por SIATC_"
            st.caption(_ts_res)

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

        # ── Eficiencia por carril ─────────────────────────────────────────
        _ef_carril = stats_eficiencia_carriles()
        if _ef_carril:
            _ef_cols = st.columns(3)
            _ef_labels = {"verde": ("🟢 Mediación", "#28a745"), "amarillo": ("🟡 Suspensión", "#ffc107"),
                          "rojo": ("🔴 Proceso pleno", "#dc3545")}
            for _ec, (_ef_lbl, _ef_color) in _ef_labels.items():
                _ef_d = _ef_carril.get(_ec, {})
                if _ef_d:
                    with _ef_cols[list(_ef_labels.keys()).index(_ec)]:
                        st.markdown(f"**{_ef_lbl}**")
                        st.markdown(
                            f"<div style='background:linear-gradient(90deg,{_ef_color}22,white);border-left:4px solid {_ef_color};border-radius:4px;padding:8px'>"
                            f"<strong style='font-size:1.5rem'>{_ef_d.get('pct_resolucion',0)}%</strong> resueltas<br>"
                            f"<small>{_ef_d.get('activas',0)} activas · {(_ef_d.get('resueltas',0)+_ef_d.get('archivadas',0))} cerradas / {_ef_d.get('total',0)}</small>"
                            f"</div>",
                            unsafe_allow_html=True
                        )
            st.markdown("")

        # Causas por categoría (derivado de tipos)
        _tipos_all = causas_por_tipo()
        _cat_counts: dict[str, int] = {}
        for _t in _tipos_all:
            _cat = TIPOS_INFRACCION.get(_t.get("tipo_infraccion",""), {}).get("categoria", "Otro")
            _cat_counts[_cat] = _cat_counts.get(_cat, 0) + _t["n"]
        if _cat_counts:
            _cat_colors = {
                "Tránsito":      "#2e5090",
                "Convivencia":   "#28a745",
                "Comercio":      "#ffc107",
                "Integridad":    "#dc3545",
                "Espacio Público": "#6f42c1",
                "Otro":          "#6c757d",
            }
            _cat_labels = list(_cat_counts.keys())
            _cat_vals   = list(_cat_counts.values())
            _cat_clrs   = [_cat_colors.get(l, "#6c757d") for l in _cat_labels]
            col_cat1, col_cat2 = st.columns(2)
            with col_cat1:
                fig_cat = go.Figure(go.Pie(
                    labels=_cat_labels, values=_cat_vals,
                    marker_colors=_cat_clrs,
                    hole=0.4, textinfo="label+value",
                ))
                fig_cat.update_layout(title="Causas por categoría", showlegend=False, height=280)
                st.plotly_chart(fig_cat, use_container_width=True)
            with col_cat2:
                _rows_cat = [{"Categoría": k, "Causas": v,
                               "% del total": f"{v*100//total}%"} for k,v in sorted(_cat_counts.items(), key=lambda x:-x[1])]
                st.dataframe(pd.DataFrame(_rows_cat), use_container_width=True, hide_index=True)
        # Stacked bar: categoría × estado (pipeline view)
        _cat_est = stats_categoria_por_estado()
        if _cat_est:
            _categorias_ord = sorted(_cat_est.keys())
            _estados_plot = ["ingresada","clasificada","notificada","en_mediacion","resuelta","archivada"]
            _estado_colors = {"ingresada":"#adb5bd","clasificada":"#5a8de4","notificada":"#f39c12",
                              "en_mediacion":"#2ecc71","resuelta":"#28a745","archivada":"#6c757d"}
            _fig_stack = go.Figure()
            for _est in _estados_plot:
                _vals_est = [_cat_est.get(cat, {}).get(_est, 0) for cat in _categorias_ord]
                if any(_v > 0 for _v in _vals_est):
                    _fig_stack.add_trace(go.Bar(
                        name=ESTADOS_LABEL.get(_est, _est),
                        x=_categorias_ord,
                        y=_vals_est,
                        marker_color=_estado_colors.get(_est, "#999"),
                    ))
            _fig_stack.update_layout(
                barmode="stack", height=300,
                title="Pipeline por categoría de infracción",
                xaxis_title="", yaxis_title="Causas",
                legend=dict(orientation="h", y=1.1),
            )
            st.plotly_chart(_fig_stack, use_container_width=True)

        st.markdown("---")

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

        # ── Distribución por día de semana ────────────────────────────────
        _dow_data = stats_por_dia_semana()
        if _dow_data:
            st.markdown("---")
            _col_dow, _col_blank = st.columns([2, 1])
            with _col_dow:
                _df_dow = pd.DataFrame(_dow_data)
                _colors_dow = ["#2e5090" if d not in ("Sáb","Dom") else "#adb5bd"
                               for d in _df_dow["dia"]]
                _fig_dow = go.Figure(go.Bar(
                    x=_df_dow["dia"], y=_df_dow["n"],
                    marker_color=_colors_dow,
                    text=_df_dow["n"], textposition="outside",
                ))
                _fig_dow.update_layout(
                    title="Causas ingresadas por día de semana",
                    height=260, yaxis_title="Causas", xaxis_title="",
                    margin=dict(t=40, b=10),
                )
                st.plotly_chart(_fig_dow, use_container_width=True)
            with _col_blank:
                if len(_dow_data) >= 5:
                    _max_dow = max(_dow_data, key=lambda x: x["n"])
                    _min_dow = min(_dow_data, key=lambda x: x["n"])
                    st.metric("Día más activo", _max_dow["dia"], delta=f"{_max_dow['n']} causas")
                    st.metric("Día menos activo", _min_dow["dia"], delta=f"{_min_dow['n']} causas")

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

        # ── Tendencia: ingresadas vs. cerradas ────────────────────────────
        _tend_data = stats_tendencia_mensual(12)
        if len(_tend_data) >= 2:
            st.markdown("---")
            st.subheader("📈 Tendencia: ingresadas vs. cerradas por mes")
            _df_tend = pd.DataFrame(_tend_data)
            _fig_tend = go.Figure()
            _fig_tend.add_trace(go.Scatter(
                x=_df_tend["mes"], y=_df_tend["ingresadas"],
                mode="lines+markers", name="Ingresadas",
                line=dict(color="#2e5090", width=2), marker=dict(size=7),
                fill="tozeroy", fillcolor="rgba(46,80,144,0.07)"
            ))
            _fig_tend.add_trace(go.Scatter(
                x=_df_tend["mes"], y=_df_tend["cerradas"],
                mode="lines+markers", name="Cerradas (resueltas+archivadas)",
                line=dict(color="#28a745", width=2, dash="dash"), marker=dict(size=7),
            ))
            _fig_tend.update_layout(
                height=280, legend=dict(orientation="h", y=1.1),
                xaxis_title="", yaxis_title="Causas",
                hovermode="x unified",
            )
            st.plotly_chart(_fig_tend, use_container_width=True)
            # Show whether backlog is growing or shrinking
            _tot_ing = sum(r["ingresadas"] for r in _tend_data)
            _tot_cer = sum(r["cerradas"] for r in _tend_data)
            if _tot_cer >= _tot_ing:
                st.success(f"✅ En los últimos {len(_tend_data)} meses: {_tot_ing} ingresadas, {_tot_cer} cerradas — el pendiente se está **reduciendo**.")
            else:
                st.warning(f"⚠️ En los últimos {len(_tend_data)} meses: {_tot_ing} ingresadas, {_tot_cer} cerradas — el pendiente está **creciendo** (+{_tot_ing - _tot_cer}).")

        # ── Estadísticas detalladas por fiscal ────────────────────────────
        _sfiscal = _c_stats_por_fiscal()
        if _sfiscal:
            st.markdown("---")
            st.subheader("👨‍⚖️ Rendimiento por fiscal")
            _sfis_rows = []
            for sf in _sfiscal:
                _sfis_rows.append({
                    "Fiscal":              sf["fiscal_asignado"],
                    "Total":               sf["total"],
                    "Resueltas":           sf["resueltas"],
                    "% Resolución":        sf["pct_resolucion"],
                    "% No punitivas":      sf["pct_no_punitivo"],
                    "Prom. días":          sf["dias_promedio"] if sf["dias_promedio"] else "—",
                })
            _df_sfis = pd.DataFrame(_sfis_rows)
            st.dataframe(
                _df_sfis,
                use_container_width=True,
                hide_index=True,
                column_config={
                    "Total":          st.column_config.NumberColumn("Total", format="%d"),
                    "Resueltas":      st.column_config.NumberColumn("Resueltas", format="%d"),
                    "% Resolución":   st.column_config.ProgressColumn("% Resueltas", min_value=0, max_value=100, format="%d%%"),
                    "% No punitivas": st.column_config.ProgressColumn("% No punitivas", min_value=0, max_value=100, format="%d%%"),
                },
            )

        # ── Rendimiento por unidad contravencional ────────────────────────
        _sunidad = stats_por_unidad()
        if _sunidad:
            st.markdown("---")
            st.subheader("🏛️ Rendimiento por unidad")
            _ulab = {"norte": "Norte", "sur": "Sur", "genero": "Género"}
            _su_rows = []
            for su in _sunidad:
                _su_rows.append({
                    "Unidad":        _ulab.get(su.get("unidad",""), su.get("unidad","")),
                    "Total":         su["total"],
                    "Cerradas":      su["cerradas"] or 0,
                    "% Resolución":  su["pct_resolucion"],
                    "🟢 Verde":      su.get("verde", 0),
                    "🟡 Amarillo":   su.get("amarillo", 0),
                    "🔴 Rojo":       su.get("rojo", 0),
                    "Prom. días":    su["dias_promedio"] if su.get("dias_promedio") else "—",
                })
            _df_sunidad = pd.DataFrame(_su_rows)
            st.dataframe(
                _df_sunidad,
                use_container_width=True,
                hide_index=True,
                column_config={
                    "Total":       st.column_config.NumberColumn("Total", format="%d"),
                    "Cerradas":    st.column_config.NumberColumn("Cerradas", format="%d"),
                    "% Resolución":st.column_config.ProgressColumn("% Resolución", min_value=0, max_value=100, format="%d%%"),
                },
            )

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

        # ── Tiempo de resolución por tipo de infracción ───────────────────
        _ttipo = stats_tiempo_por_tipo()
        if _ttipo:
            st.markdown("---")
            st.subheader("📊 Tiempo de resolución por tipo de infracción")
            _ttipo_rows = []
            for t in _ttipo:
                _ttipo_rows.append({
                    "Categoría":   t.get("categoria", ""),
                    "Infracción":  t.get("label", t["tipo_infraccion"])[:45],
                    "N causas":    t["n"],
                    "Días prom.":  t["dias_promedio"] if t["dias_promedio"] else "—",
                })
            _df_ttipo = pd.DataFrame(_ttipo_rows)
            st.dataframe(
                _df_ttipo,
                use_container_width=True,
                hide_index=True,
                column_config={
                    "N causas":   st.column_config.NumberColumn("N causas", format="%d"),
                    "Días prom.": st.column_config.NumberColumn("Días promedio", format="%.1f"),
                },
            )
            # Horizontal bar chart of top 10
            _top10 = _ttipo[:10]
            if _top10:
                _fig_ttp = go.Figure(go.Bar(
                    x=[t["dias_promedio"] or 0 for t in reversed(_top10)],
                    y=[t.get("label","")[:30] for t in reversed(_top10)],
                    orientation="h",
                    marker_color="#2e5090",
                    text=[f"{t['dias_promedio']:.0f}d ({t['n']})" for t in reversed(_top10)],
                    textposition="outside",
                ))
                _fig_ttp.update_layout(
                    height=max(200, len(_top10) * 28),
                    margin=dict(l=0, r=60, t=10, b=10),
                    xaxis_title="Días promedio hasta resolución",
                )
                st.plotly_chart(_fig_ttp, use_container_width=True)

        if stats["personas"]:
            st.markdown("---")
            st.subheader("🔄 Reincidencia")
            col_r1, col_r2, col_r3 = st.columns(3)
            with col_r1:
                st.metric("Personas registradas", stats["personas"])
            with col_r2:
                if stats["reincidentes"]:
                    pct_r = round(stats["reincidentes"] * 100 / stats["personas"], 1)
                    st.metric("Reincidentes",
                              f"{stats['reincidentes']}",
                              delta=f"{pct_r}% del padrón",
                              delta_color="inverse",
                              help="Personas con 2 o más causas registradas")
                else:
                    st.metric("Reincidentes", "0")
            with col_r3:
                _multicarril = sum(1 for c in listar_causas(limit=500)
                                   if c.get("carril") == "rojo")
                st.metric("Causas Rojo (proceso pleno)", _multicarril)

            reincidentes_list = personas_reincidentes(min_causas=2)
            if reincidentes_list:
                st.markdown(f"**{len(reincidentes_list)} persona(s) con múltiples causas:**")
                _rows_reic = []
                for r in reincidentes_list:
                    # Parse carriles and estados strings
                    _carriles_str = r.get("carriles") or ""
                    _carr_icons = "".join(
                        {"verde":"🟢","amarillo":"🟡","rojo":"🔴"}.get(car.strip(),"⚪")
                        for car in _carriles_str.split(",") if car.strip()
                    )
                    _rows_reic.append({
                        "DNI":           r["dni"],
                        "Imputado/a":    r["apellido_nombre"],
                        "Edad":          r.get("edad",""),
                        "Causas":        r["n_causas"],
                        "Carriles":      _carr_icons,
                        "Última causa":  r.get("ultima_causa","")[:10] if r.get("ultima_causa") else "",
                    })
                _df_reic = pd.DataFrame(_rows_reic).sort_values("Causas", ascending=False)
                st.dataframe(_df_reic, use_container_width=True, hide_index=True,
                             column_config={"Causas": st.column_config.NumberColumn("Causas", format="%d")})
                # Quick profile links for top 3 reincidentes
                _top_reic = reincidentes_list[:3]
                if _top_reic:
                    _reic_btns = st.columns(len(_top_reic))
                    for _i_r, _r_top in enumerate(_top_reic):
                        _r_nom = (_r_top["apellido_nombre"] or "").split(",")[0]
                        if _reic_btns[_i_r].button(f"👤 {_r_nom}", key=f"pref_reic_{_r_top['dni']}",
                                                     help=f"Ver perfil de {_r_top['apellido_nombre']}",
                                                     use_container_width=True):
                            st.session_state["perfil_busqueda"] = _r_top["dni"]
                            st.session_state["goto_perfil"] = True
            else:
                st.success("✅ No hay reincidentes en el padrón actual.")

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

        # ── Causas resueltas/en mediación sin seguimiento ──────────────────
        _sin_seg_panel = _c_sin_seguimiento()
        if _sin_seg_panel:
            st.markdown("---")
            st.subheader("🔍 Causas sin seguimiento registrado")
            st.warning(
                f"**{len(_sin_seg_panel)} causa(s)** en estado 'Resuelta' o 'En mediación' "
                "que aún no tienen un período de seguimiento post-resolución registrado."
            )
            _rows_ss = []
            for _c in _sin_seg_panel:
                _rows_ss.append({
                    "Expediente": _c["numero"],
                    "Imputado/a": (_c.get("apellido_nombre","") or "").split(",")[0],
                    "Estado":     ESTADOS_LABEL.get(_c.get("estado",""), _c.get("estado","")),
                    "Carril":     {"verde":"🟢","amarillo":"🟡","rojo":"🔴"}.get(_c.get("carril",""),"⚪"),
                    "Fiscal":     _c.get("fiscal_asignado",""),
                    "Actualizada": _c.get("updated_at","")[:10],
                })
            st.dataframe(pd.DataFrame(_rows_ss), use_container_width=True, hide_index=True)

        # ── Mediaciones estancadas ────────────────────────────────────────
        _med_est_panel = mediaciones_estancadas(dias=30)
        if _med_est_panel:
            st.markdown("---")
            st.subheader("🤝 Mediaciones estancadas (>30 días sin actualización)")
            st.warning(
                f"**{len(_med_est_panel)} causa(s) en mediación** sin actualización en más de 30 días. "
                "Revisá el estado y considerá avanzar o reprogramar."
            )
            _rows_me = []
            for _cm in _med_est_panel:
                try:
                    _dias_me = (datetime.now() - datetime.strptime(_cm.get("updated_at","")[:16], "%Y-%m-%d %H:%M")).days
                except Exception:
                    _dias_me = "?"
                _rows_me.append({
                    "Expediente":  _cm["numero"],
                    "Imputado/a":  (_cm.get("apellido_nombre","") or "").split(",")[0],
                    "Días estancada": _dias_me,
                    "Fiscal":      _cm.get("fiscal_asignado",""),
                    "Ingresada":   _cm.get("created_at","")[:10],
                })
            st.dataframe(
                pd.DataFrame(_rows_me).sort_values("Días estancada", ascending=False),
                use_container_width=True, hide_index=True,
                column_config={"Días estancada": st.column_config.NumberColumn("Días sin mov.", format="%d días")},
            )

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

            # Row 2 — additional KPIs
            kc5, kc6, kc7, kc8 = st.columns(4)
            _tiempos_res = stats_tiempos_resolucion()
            if _tiempos_res:
                _dias_tot = sum(
                    (t["dias_promedio"] or 0) * t["n"]
                    for t in _tiempos_res.values() if t.get("n", 0) > 0
                )
                _n_res_total = sum(t.get("n", 0) for t in _tiempos_res.values())
                _dias_prom_global = round(_dias_tot / _n_res_total) if _n_res_total else None
                kc5.metric(
                    "Días prom. resolución",
                    f"~{_dias_prom_global}d" if _dias_prom_global else "—",
                    help="Promedio ponderado entre todos los carriles"
                )
            else:
                kc5.metric("Días prom. resolución", "—")

            # Seguimiento coverage
            _resueltas_total = stats["por_estado"].get("resuelta", 0)
            _segs_total = seg_s.get("total", 0) if isinstance(seg_s, dict) else 0
            if _resueltas_total > 0:
                _pct_seg_cov = round(_segs_total * 100 / _resueltas_total)
                kc6.metric(
                    "Cobertura seguimiento",
                    f"{_pct_seg_cov}%",
                    delta=f"{_segs_total} seguimientos / {_resueltas_total} resueltas",
                    help="Seguimientos registrados vs. causas resueltas",
                )
            else:
                kc6.metric("Cobertura seguimiento", "—")

            # Audiencias per resolved causa ratio
            if _resueltas_total > 0 and aud_s["total"] > 0:
                _auds_per_causa = round(aud_s["total"] / max(total, 1), 1)
                kc7.metric(
                    "Audiencias / causa",
                    f"{_auds_per_causa}",
                    help="Audiencias totales dividido total de causas"
                )
            else:
                kc7.metric("Audiencias / causa", "—")

            # Backlog vs capacity
            _activas_kpi = sum(stats["por_estado"].get(e, 0) for e in
                               ("ingresada","clasificada","notificada","en_mediacion"))
            kc8.metric(
                "Causas activas",
                _activas_kpi,
                delta=f"{round(_activas_kpi * 100 / total)}% del total" if total else None,
                help="Causas en estados activos (ingresada, clasificada, notificada, en mediación)",
            )

        # ── Análisis demográfico ───────────────────────────────────────────
        st.markdown("---")
        st.subheader("👥 Perfil demográfico de imputados/as")
        _edad_dist   = stats_edad()
        _edad_carril = stats_edad_por_carril()
        _grupos_edad = ["16-25", "26-35", "36-45", "46-55", "56+"]

        col_demo1, col_demo2 = st.columns(2)
        with col_demo1:
            _vals_edad = [_edad_dist.get(g, 0) for g in _grupos_edad]
            if sum(_vals_edad) > 0:
                fig_edad = go.Figure(go.Bar(
                    x=_grupos_edad,
                    y=_vals_edad,
                    marker_color=["#1a2f5e","#2e5090","#3a6bc4","#5a8de4","#7aabf0"],
                    text=_vals_edad,
                    textposition="outside",
                ))
                fig_edad.update_layout(
                    title="Personas por grupo etario",
                    xaxis_title="Grupo de edad",
                    yaxis_title="Personas",
                    height=280,
                    margin=dict(t=40, b=20),
                )
                st.plotly_chart(fig_edad, use_container_width=True)
                # Edad promedio
                _personas_all = [p for p in listar_personas()
                                 if p.get("edad") and p["edad"] > 0]
                if _personas_all:
                    _prom_edad = round(sum(p["edad"] for p in _personas_all) / len(_personas_all), 1)
                    _menor = min(p["edad"] for p in _personas_all)
                    _mayor = max(p["edad"] for p in _personas_all)
                    st.caption(f"Edad promedio: **{_prom_edad} años** · Rango: {_menor}–{_mayor} años")
            else:
                st.info("No hay datos de edad disponibles.")

        with col_demo2:
            _verde_v = [_edad_carril.get(g, {}).get("verde", 0)    for g in _grupos_edad]
            _amar_v  = [_edad_carril.get(g, {}).get("amarillo", 0) for g in _grupos_edad]
            _rojo_v  = [_edad_carril.get(g, {}).get("rojo", 0)     for g in _grupos_edad]
            if any(_verde_v + _amar_v + _rojo_v):
                fig_democ = go.Figure()
                fig_democ.add_trace(go.Bar(name="🟢 Mediación",  x=_grupos_edad, y=_verde_v,
                                           marker_color="#2ECC71"))
                fig_democ.add_trace(go.Bar(name="🟡 Suspensión", x=_grupos_edad, y=_amar_v,
                                           marker_color="#F39C12"))
                fig_democ.add_trace(go.Bar(name="🔴 Proceso",    x=_grupos_edad, y=_rojo_v,
                                           marker_color="#E74C3C"))
                fig_democ.update_layout(
                    barmode="stack",
                    title="Carriles por grupo etario",
                    xaxis_title="Grupo de edad",
                    yaxis_title="Causas",
                    height=280,
                    margin=dict(t=40, b=20),
                    legend=dict(orientation="h", y=1.18),
                )
                st.plotly_chart(fig_democ, use_container_width=True)
            else:
                st.info("Sin datos suficientes para el gráfico de carriles por edad.")

        # ── Exportación a Excel ────────────────────────────────────────────
        st.markdown("---")
        st.subheader("📥 Exportar datos")
        col_ex1, col_ex2, col_ex3, col_ex4, col_ex5 = st.columns(5)
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
                rpt_bytes  = pdf_reporte_diario(
                    stats, _auds_hoy, _pend, fiscal_nombre, unidad_key,
                    seg_stats=stats_seguimiento(),
                    causas_sin_aud=causas_sin_audiencia_programada(),
                )
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
        with col_ex5:
            try:
                from pdf_gen import pdf_lista_causas_activas as _plca
                _activas_exp = listar_causas(limit=500)
                _activas_exp = [c for c in _activas_exp
                                if c.get("estado") in ("ingresada","clasificada","notificada","en_mediacion")]
                _pdf_lista = _plca(_activas_exp, fiscal_nombre, unidad_key)
                st.download_button(
                    "⬇️ Lista causas activas (.pdf)",
                    data=_pdf_lista,
                    file_name=f"SIATC_activas_{datetime.now().strftime('%Y%m%d')}.pdf",
                    mime="application/pdf",
                    use_container_width=True,
                )
            except Exception as _e_lista:
                st.error(f"Error lista: {_e_lista}")

        # Second export row — monthly report
        _col_men, _col_men2 = st.columns([1, 4])
        with _col_men:
            try:
                from pdf_gen import pdf_informe_mensual as _pim
                _hoy_ym = datetime.now().strftime("%Y-%m")
                _mes_data = causas_por_mes(12)
                _mes_ing = next((r["n"] for r in _mes_data if r["mes"] == _hoy_ym), 0)
                _aud_s_m  = stats_audiencias()
                _tipos_m  = causas_por_tipo()[:5]
                _sfis_m   = stats_por_fiscal()
                _res_m    = stats["por_estado"].get("resuelta",0)
                _arc_m    = stats["por_estado"].get("archivada",0)
                _pdf_men  = _pim(
                    _hoy_ym, stats, _mes_ing, _res_m, _arc_m,
                    _aud_s_m["total"], _aud_s_m["realizadas"], _aud_s_m["ausentes"],
                    _tipos_m, _sfis_m, fiscal_nombre, unidad_key,
                )
                st.download_button(
                    "⬇️ Informe mensual (.pdf)",
                    data=_pdf_men,
                    file_name=f"SIATC_mensual_{datetime.now().strftime('%Y%m')}.pdf",
                    mime="application/pdf",
                    use_container_width=True,
                )
            except Exception as _e_men:
                st.error(f"Error informe mensual: {_e_men}")

        # ── Causas sin audiencia programada ───────────────────────────────
        st.markdown("---")
        st.subheader("📋 Causas sin audiencia programada")
        _sin_aud_panel = causas_sin_audiencia_programada()
        if not _sin_aud_panel:
            st.success("✅ Todas las causas notificadas y clasificadas tienen audiencia programada.")
        else:
            st.warning(f"⚠️ **{len(_sin_aud_panel)} causa(s)** notificadas o clasificadas sin audiencia programada:")
            _rows_sa = []
            for c in _sin_aud_panel:
                _rows_sa.append({
                    "Expediente":  c["numero"],
                    "Imputado/a":  (c.get("apellido_nombre","") or "").split(",")[0],
                    "Estado":      ESTADOS_LABEL.get(c["estado"], c["estado"]),
                    "Carril":      {"verde":"🟢","amarillo":"🟡","rojo":"🔴"}.get(c.get("carril",""),"⚪"),
                    "Unidad":      {"norte":"Norte","sur":"Sur","genero":"Género"}.get(c.get("unidad",""),""),
                    "Fiscal":      c.get("fiscal_asignado",""),
                    "Última act.": c.get("updated_at","")[:10] if c.get("updated_at") else "",
                })
            _df_sa = pd.DataFrame(_rows_sa)
            st.dataframe(_df_sa, use_container_width=True, hide_index=True)
            st.caption("💡 Agendá las audiencias desde **📂 Gestión de Causas** o desde **📅 Agenda**.")

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

        # ── Top causas más antiguas activas ──────────────────────────────
        _top_antigas = causas_mas_antiguas_activas(limit=5)
        if _top_antigas:
            st.markdown("---")
            st.subheader("⏳ Causas activas más antiguas")
            st.caption("Las 5 causas aún activas que llevan más tiempo abiertas desde su ingreso.")
            _rows_ant = []
            for c in _top_antigas:
                try:
                    _ant_dias = (datetime.now() - datetime.strptime(c["created_at"][:10], "%Y-%m-%d")).days
                except Exception:
                    _ant_dias = 0
                _rows_ant.append({
                    "Expediente":  c["numero"],
                    "Imputado/a":  (c.get("apellido_nombre","") or "").split(",")[0],
                    "Estado":      ESTADOS_LABEL.get(c["estado"], c["estado"]),
                    "Carril":      {"verde":"🟢","amarillo":"🟡","rojo":"🔴"}.get(c.get("carril",""),"⚪"),
                    "Días abierta": _ant_dias,
                    "Fiscal":      c.get("fiscal_asignado",""),
                    "Ingresada":   c.get("created_at","")[:10],
                })
            st.dataframe(
                pd.DataFrame(_rows_ant),
                use_container_width=True, hide_index=True,
                column_config={"Días abierta": st.column_config.NumberColumn("Días abierta", format="%d días")},
            )

        # ── Actividad reciente ────────────────────────────────────────────
        st.markdown("---")
        st.subheader("🕐 Actividad reciente")
        _actividad = actividad_reciente(limit=12)
        if not _actividad:
            st.info("No hay actividad registrada aún.")
        else:
            for _i_act, _act in enumerate(_actividad):
                _es_nota = _act.get("estado_anterior") == _act.get("estado_nuevo") and _act.get("estado_anterior")
                _nombre_a = (_act.get("apellido_nombre","") or "").split(",")[0]
                _num_a    = _act.get("numero","")
                _ts       = _act.get("created_at","")[:16]
                _usr      = _act.get("usuario","")
                _obs      = _act.get("observaciones","")
                _col_feed, _col_nav = st.columns([10, 1])
                with _col_feed:
                    if _es_nota:
                        st.markdown(
                            f"<div style='border-left:3px solid #6c757d;padding:3px 10px;"
                            f"margin:2px 0;background:#f8f9fa;border-radius:0 4px 4px 0;font-size:0.82rem'>"
                            f"📝 <strong>{_ts}</strong> — {_num_a} ({_nombre_a}): "
                            f"<em>{_obs[:80]}{'…' if len(_obs)>80 else ''}</em>"
                            f"</div>",
                            unsafe_allow_html=True
                        )
                    else:
                        _ant = ESTADOS_LABEL.get(_act.get("estado_anterior",""),"—") if _act.get("estado_anterior") else "Ingreso"
                        _nvo = ESTADOS_LABEL.get(_act.get("estado_nuevo",""), _act.get("estado_nuevo",""))
                        _obs_txt = f" — {_obs[:50]}" if _obs else ""
                        st.markdown(
                            f"<div style='border-left:3px solid #2e5090;padding:3px 10px;"
                            f"margin:2px 0;background:#f8f9fa;border-radius:0 4px 4px 0;font-size:0.82rem'>"
                            f"🔄 <strong>{_ts}</strong> — {_num_a} ({_nombre_a}): "
                            f"{_ant} ➜ <strong>{_nvo}</strong>{_obs_txt}"
                            f"</div>",
                            unsafe_allow_html=True
                        )
                with _col_nav:
                    if st.button("↗", key=f"feed_nav_{_i_act}", help=f"Ir a {_num_a} en Gestión",
                                 use_container_width=True):
                        st.session_state["gc_busqueda"] = _num_a
                        st.session_state["causa_sel_id"] = _act.get("causa_id")

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
                    try:
                        reset_db()   # trunca tablas (más confiable que borrar el archivo)
                    except Exception as _re:
                        st.warning(f"Reset parcial: {_re}")
                    init_db()
                    poblar()
                    st.cache_data.clear()
                    st.session_state.intro_vista = True   # no mostrar bienvenida de nuevo
                    st.success("Datos restablecidos correctamente.")
                    st.rerun()
            with col_r2:
                st.info("💡 **Guía de demostración (v1.3)**\n\n"
                        "1. **📋 Nuevo Caso** → DNI `38.421.667` → auto-completa nombre + muestra causas previas\n"
                        "   → triaje → pasos a seguir → fiscal sugerido → PDF + guardá con obs. inicial.\n"
                        "2. **📂 Gestión** → filtrá por '🚨 Urgencia' → badge ⚠️ Rein. → siguiente paso\n"
                        "   → nota rápida → ⭐ marcá prioritaria → agendá audiencia desde el expander\n"
                        "   → 'Ver perfil' → descargá **Expediente completo PDF**.\n"
                        "3. **📅 Agenda** → programá audiencia (detección de conflictos + slots libres)\n"
                        "   → exportá semana como PDF + .ics para Google Calendar.\n"
                        "4. **🔍 Seguimiento** → expandí activo → registrá avance → agendá próximo control\n"
                        "   → si todas condiciones ✅ → cerrá (Acta de Compromiso se genera automáticamente).\n"
                        "5. **👤 Perfil** → buscá `García` → nivel de riesgo → Gantt + audiencias en header\n"
                        "   → editá contacto → expandí 'Causas similares'.\n"
                        "6. **📊 Panel** → semáforo de salud → tendencia ingresadas vs. cerradas\n"
                        "   → pipeline por categoría → 8 KPIs → exportá 6 formatos + informe mensual.")
