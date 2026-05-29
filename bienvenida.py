# -*- coding: utf-8 -*-
"""
Pantalla de ingreso al sistema SIATC.
Muestra login (demo), luego el flujo del expediente + dashboard de causas activas.
"""

import streamlit as st

# ── Usuarios demo ──────────────────────────────────────────────────────────────
USUARIOS_DEMO = {
    "aperez":    {"nombre": "Dra. Ana Pérez",    "unidad": "norte",  "pass": "mpf2024"},
    "cmedina":   {"nombre": "Dr. Carlos Medina", "unidad": "sur",    "pass": "mpf2024"},
    "lsuarez":   {"nombre": "Dra. Laura Suárez", "unidad": "genero", "pass": "mpf2024"},
    "demo":      {"nombre": "Usuario Demo",      "unidad": "norte",  "pass": "demo"},
}

# ── Etapas del expediente contravencional ─────────────────────────────────────
ETAPAS = [
    ("📥", "Ingreso",      "El agente registra el hecho contravencional con los datos del parte policial."),
    ("🔍", "Triaje",       "El sistema clasifica automáticamente la causa en Carril Verde, Amarillo o Rojo."),
    ("📬", "Notificación", "Se genera y envía la cédula de citación al imputado/a."),
    ("📅", "Audiencia",    "Se programa y realiza la audiencia de mediación, suspensión o proceso pleno."),
    ("✍️", "Resolución",   "El fiscal suscribe el acuerdo, dictamen o requerimiento de apertura."),
    ("🔍", "Seguimiento",  "Se monitorea el cumplimiento de condiciones durante el período acordado."),
    ("✅", "Cierre",       "Verificado el cumplimiento, la causa se archiva. Fin del expediente."),
]


def _render_login():
    """Pantalla de ingreso al sistema."""
    st.markdown("""
<div style='background:linear-gradient(135deg,#1a2f5e 0%,#2e5090 60%,#3a6bc4 100%);
            border-radius:12px;padding:2rem 2.5rem 1.5rem;color:white;
            margin-bottom:1.5rem;text-align:center'>
  <h2 style='margin:0 0 0.3rem 0'>⚖️ SIATC</h2>
  <p style='margin:0;opacity:0.85;font-size:1.05rem'>
    Sistema Inteligente de Apoyo al Trabajo Contravencional
  </p>
  <p style='margin:0.4rem 0 0 0;opacity:0.65;font-size:0.85rem'>
    Ministerio Público Fiscal · Provincia de Córdoba · Ley N° 10.326
  </p>
</div>
""", unsafe_allow_html=True)

    col_form, col_info = st.columns([1, 1], gap="large")

    with col_form:
        st.markdown("#### Ingresá al sistema")
        usuario  = st.text_input("Usuario", placeholder="Ej: aperez", key="login_user")
        password = st.password_input("Contraseña", key="login_pass")

        if st.button("→ Ingresar", type="primary", use_container_width=True):
            u = USUARIOS_DEMO.get(usuario.strip().lower())
            if u and u["pass"] == password:
                st.session_state["usuario_logueado"]  = True
                st.session_state["fiscal_nombre"]     = u["nombre"]
                st.session_state["unidad_key"]        = u["unidad"]
                st.rerun()
            else:
                st.error("Usuario o contraseña incorrectos.")

        st.caption(
            "**Modo demo** — usuarios disponibles:  \n"
            "``aperez`` · ``cmedina`` · ``lsuarez`` · ``demo``  \n"
            "Contraseña: ``mpf2024`` (o ``demo`` para el usuario demo)"
        )

    with col_info:
        st.markdown("#### Flujo del expediente")
        for i, (icon, etapa, desc) in enumerate(ETAPAS):
            st.markdown(
                f"<div style='display:flex;gap:10px;margin-bottom:6px;align-items:flex-start'>"
                f"<span style='font-size:1.1rem;min-width:28px;text-align:center'>{icon}</span>"
                f"<div><strong>{etapa}</strong><br>"
                f"<span style='font-size:0.78rem;color:#555'>{desc}</span></div></div>",
                unsafe_allow_html=True
            )
            if i < len(ETAPAS) - 1:
                st.markdown(
                    "<div style='margin-left:14px;color:#2e5090;font-size:0.8rem'>│</div>",
                    unsafe_allow_html=True
                )


def _render_dashboard():
    """Dashboard post-login: ingreso de caso + causas activas."""
    import database as db
    from data_cordoba import UNIDADES

    nombre   = st.session_state.get("fiscal_nombre", "")
    unidad_k = st.session_state.get("unidad_key", "norte")
    unidad_s = {"norte": "Norte", "sur": "Sur", "genero": "Género"}.get(unidad_k, unidad_k)

    # ── Header compacto ────────────────────────────────────────────────────────
    col_hdr, col_sal = st.columns([4, 1])
    col_hdr.markdown(
        f"<div style='background:linear-gradient(90deg,#1a2f5e,#2e5090);border-radius:8px;"
        f"padding:0.8rem 1.2rem;color:white'>"
        f"<strong>⚖️ SIATC</strong> · Unidad {unidad_s} &nbsp;|&nbsp; {nombre}"
        f"</div>", unsafe_allow_html=True
    )
    if col_sal.button("🚪 Salir", use_container_width=True):
        for k in ("usuario_logueado", "fiscal_nombre", "unidad_key", "intro_vista"):
            st.session_state.pop(k, None)
        st.rerun()

    st.markdown("")

    # ── Línea de tiempo del expediente ────────────────────────────────────────
    st.markdown("### Flujo del expediente contravencional — Ley N° 10.326")
    _cols_et = st.columns(len(ETAPAS))
    for col, (icon, etapa, _) in zip(_cols_et, ETAPAS):
        col.markdown(
            f"<div style='text-align:center;background:#f0f4ff;border-radius:8px;"
            f"padding:10px 4px;border-top:3px solid #2e5090'>"
            f"<span style='font-size:1.4rem'>{icon}</span><br>"
            f"<span style='font-size:0.8rem;font-weight:bold;color:#1a2f5e'>{etapa}</span>"
            f"</div>",
            unsafe_allow_html=True
        )

    st.markdown("")

    # ── Acción principal: Nuevo Caso ──────────────────────────────────────────
    col_nc, col_stats = st.columns([2, 3], gap="large")

    with col_nc:
        st.markdown("### ➕ Registrar nueva causa")
        st.info(
            "Ingresá el DNI del imputado/a para autocompletar sus datos. "
            "El sistema clasifica la causa automáticamente y genera los documentos correspondientes."
        )
        if st.button("📋 Ir a Nuevo Caso", type="primary", use_container_width=True):
            st.session_state["intro_vista"] = True
            st.rerun()

        # Stats rápidas
        try:
            s = db.stats_generales()
            s_seg = db.stats_seguimiento()
            s_aud = db.stats_audiencias()
            st.markdown("---")
            st.markdown("**Estado del sistema:**")
            _sc1, _sc2, _sc3 = st.columns(3)
            _sc1.metric("Causas", s.get("total", 0))
            _sc2.metric("Seguimientos activos", s_seg.get("activos", 0))
            _sc3.metric("Audiencias hoy", s_aud.get("hoy", 0))
        except Exception:
            pass

    # ── Causas activas ─────────────────────────────────────────────────────────
    with col_stats:
        st.markdown("### 📂 Causas en trámite")
        try:
            from database import listar_causas, ESTADOS_LABEL
            from data_cordoba import TIPOS_INFRACCION as _TI
            from datetime import datetime

            causas_activas = listar_causas(
                unidad=unidad_k, limit=200
            )
            causas_activas = [c for c in causas_activas
                              if c.get("estado") in
                              ("ingresada", "clasificada", "notificada", "en_mediacion")]

            if not causas_activas:
                st.info("No hay causas activas para esta unidad.")
            else:
                # Organizar por estado (columnas Kanban compacto)
                _est_order = [
                    ("ingresada",   "📥 Ingresadas"),
                    ("clasificada", "🔍 Clasificadas"),
                    ("notificada",  "📬 Notificadas"),
                    ("en_mediacion","✍️ En mediación"),
                ]
                _kk_cols = st.columns(4)
                _carril_color = {"verde":"#2ECC71", "amarillo":"#F39C12", "rojo":"#E74C3C"}
                for _kcol, (_est, _lbl) in zip(_kk_cols, _est_order):
                    _c_est = [c for c in causas_activas if c.get("estado") == _est]
                    _kcol.markdown(
                        f"<div style='text-align:center;background:#f0f4ff;"
                        f"border-radius:6px;padding:4px;margin-bottom:6px'>"
                        f"<strong style='font-size:0.85rem'>{_lbl}</strong><br>"
                        f"<span style='font-size:1.4rem;font-weight:bold;color:#2e5090'>"
                        f"{len(_c_est)}</span></div>",
                        unsafe_allow_html=True
                    )
                    for _c in _c_est[:5]:
                        _clr = _carril_color.get(_c.get("carril",""), "#aaa")
                        _nom = (_c.get("apellido_nombre","") or "").split(",")[0][:16]
                        try:
                            _dias = (datetime.now() - datetime.strptime(
                                _c["updated_at"][:10], "%Y-%m-%d")).days
                            _dias_str = f"{_dias}d" if _dias > 0 else "hoy"
                        except Exception:
                            _dias_str = ""
                        _kcol.markdown(
                            f"<div style='border-left:3px solid {_clr};padding:3px 6px;"
                            f"margin:2px 0;background:white;border-radius:0 4px 4px 0;"
                            f"font-size:0.75rem'>"
                            f"<strong>{_c['numero'][-6:]}</strong> {_nom}<br>"
                            f"<span style='color:#888'>{_dias_str}</span>"
                            f"</div>",
                            unsafe_allow_html=True
                        )
                    if len(_c_est) > 5:
                        _kcol.caption(f"+ {len(_c_est)-5} más")
        except Exception as _e:
            st.info(f"Sin causas disponibles: {_e}")


def mostrar_si_primera_vez():
    """
    Controla el flujo de ingreso:
    - Si no logueado → pantalla de login
    - Si logueado pero no pasó el home → dashboard
    - Si intro_vista == True → ir a la app
    """
    if not st.session_state.get("usuario_logueado"):
        _render_login()
        return False   # detener app

    if not st.session_state.get("intro_vista"):
        _render_dashboard()
        return False   # detener app

    return True   # usuario autenticado y listo para usar la app
