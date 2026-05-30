# -*- coding: utf-8 -*-
"""
Pantalla de ingreso al sistema SIATC.
Login + dashboard con flujo del expediente + causas activas.
"""
from __future__ import annotations

import streamlit as st
from config_nodos import USUARIOS_DEMO, NODOS, get_oficinas_nodo

ETAPAS = [
    ("📥", "Ingreso",      "El agente registra el hecho contravencional."),
    ("🔍", "Triaje",       "Clasificación automática: Verde / Amarillo / Rojo."),
    ("📬", "Notificación", "Se genera y envía la cédula de citación."),
    ("📅", "Audiencia",    "Audiencia de mediación, suspensión o proceso pleno."),
    ("✍️", "Resolución",   "Dictamen, acuerdo o requerimiento de apertura."),
    ("🔍", "Seguimiento",  "Monitoreo del cumplimiento de condiciones."),
    ("✅", "Cierre",       "Verificado el cumplimiento, se archiva la causa."),
]


def _render_login():
    """Pantalla de ingreso al sistema."""
    st.markdown(
        "<div style='background:linear-gradient(135deg,#1a2f5e,#2e5090,#3a6bc4);"
        "border-radius:12px;padding:2rem 2.5rem 1.5rem;color:white;"
        "margin-bottom:1.5rem;text-align:center'>"
        "<h2 style='margin:0 0 0.3rem 0'>⚖️ SIATC</h2>"
        "<p style='margin:0;opacity:0.85;font-size:1.05rem'>"
        "Sistema Inteligente de Apoyo al Trabajo Contravencional</p>"
        "<p style='margin:0.4rem 0 0;opacity:0.65;font-size:0.85rem'>"
        "Ministerio Publico Fiscal · Provincia de Cordoba · Ley N 10.326</p>"
        "</div>",
        unsafe_allow_html=True,
    )

    col_form, col_info = st.columns(2)

    with col_form:
        st.markdown("#### Ingresa al sistema")
        usuario  = st.text_input("Usuario", placeholder="Ej: aperez", key="login_user")
        password = st.text_input("Contrasena", key="login_pass", type="password")

        if st.button("Ingresar", type="primary", use_container_width=True):
            u = USUARIOS_DEMO.get(usuario.strip().lower())
            if u and u["pass"] == password:
                nodo_cfg      = NODOS.get(u["nodo"], {})
                oficinas_nodo = get_oficinas_nodo(u["nodo"])
                oficina_cfg   = oficinas_nodo.get(u["oficina"], {})
                st.session_state["usuario_logueado"] = True
                st.session_state["fiscal_nombre"]    = u["nombre"]
                st.session_state["nodo_key"]         = u["nodo"]
                st.session_state["oficina_key"]      = u["oficina"]
                st.session_state["oficina_label"]    = oficina_cfg.get("label", u["oficina"])
                st.session_state["circunscripcion"]  = nodo_cfg.get("circunscripcion", "")
                st.session_state["unidad_key"] = (
                    "norte"  if "norte"  in u["oficina"] else
                    "sur"    if "sur"    in u["oficina"] else
                    "genero" if "genero" in u["oficina"] else
                    "norte"
                )
                st.rerun()
            else:
                st.error("Usuario o contrasena incorrectos.")

        st.caption(
            "Modo demo | "
            "Cordoba: aperez · cmedina · lsuarez · pjudicial  "
            "Rio Cuarto: mrodriguez · sgomez · policiarc  "
            "Demo: demo  |  "
            "Contrasena: mpf2024 (o demo)"
        )

    with col_info:
        st.markdown("#### Flujo del expediente")
        for i, (icon, etapa, desc) in enumerate(ETAPAS):
            st.markdown(f"**{icon} {etapa}** — {desc}")


def _render_dashboard():
    """Dashboard post-login."""
    import database as db

    nombre        = st.session_state.get("fiscal_nombre", "")
    nodo_key      = st.session_state.get("nodo_key", "cba_norte")
    nodo_cfg      = NODOS.get(nodo_key, {})
    oficina_label = st.session_state.get("oficina_label", "")
    circunsc      = st.session_state.get("circunscripcion", "")

    col_hdr, col_sal = st.columns([4, 1])
    col_hdr.markdown(
        f"<div style='background:linear-gradient(90deg,#1a2f5e,#2e5090);border-radius:8px;"
        f"padding:0.8rem 1.2rem;color:white'>"
        f"<strong>⚖️ SIATC</strong> · {nodo_cfg.get('nombre', '')} | "
        f"{oficina_label} | {nombre}"
        f"<br><span style='opacity:0.7;font-size:0.8rem'>{circunsc}</span>"
        f"</div>",
        unsafe_allow_html=True,
    )
    if col_sal.button("🚪 Salir", use_container_width=True):
        for k in ("usuario_logueado", "fiscal_nombre", "nodo_key",
                  "oficina_key", "oficina_label", "circunscripcion", "intro_vista"):
            st.session_state.pop(k, None)
        st.rerun()

    st.markdown("")

    # Flujo del expediente
    st.markdown("### Flujo del expediente contravencional — Ley N 10.326")
    _cols_et = st.columns(len(ETAPAS))
    for col, (icon, etapa, _) in zip(_cols_et, ETAPAS):
        col.markdown(
            f"<div style='text-align:center;background:#f0f4ff;border-radius:8px;"
            f"padding:10px 4px;border-top:3px solid #2e5090'>"
            f"<span style='font-size:1.4rem'>{icon}</span><br>"
            f"<span style='font-size:0.8rem;font-weight:bold;color:#1a2f5e'>{etapa}</span>"
            f"</div>",
            unsafe_allow_html=True,
        )

    st.markdown("")

    col_nc, col_stats = st.columns([2, 3])

    with col_nc:
        st.markdown("### Registrar nueva causa")
        st.info(
            "Ingresa el DNI del imputado/a para autocompletar sus datos. "
            "El sistema clasifica la causa automaticamente."
        )
        if st.button("📋 Ir a Nuevo Caso", type="primary", use_container_width=True):
            st.session_state["intro_vista"] = True
            st.rerun()

        try:
            s     = db.stats_generales()
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

    with col_stats:
        st.markdown("### Causas en tramite")
        try:
            from database import listar_causas, ESTADOS_LABEL
            from datetime import datetime

            unidad_k      = st.session_state.get("unidad_key", "norte")
            causas_activas = [
                c for c in listar_causas(unidad=unidad_k, limit=200)
                if c.get("estado") in ("ingresada", "clasificada", "notificada", "en_mediacion")
            ]

            if not causas_activas:
                st.info("No hay causas activas para esta unidad.")
            else:
                _est_order = [
                    ("ingresada",   "📥 Ingresadas"),
                    ("clasificada", "🔍 Clasificadas"),
                    ("notificada",  "📬 Notificadas"),
                    ("en_mediacion","✍️ Mediacion"),
                ]
                _kk_cols = st.columns(4)
                _carril_color = {"verde": "#2ECC71", "amarillo": "#F39C12", "rojo": "#E74C3C"}
                for _kcol, (_est, _lbl) in zip(_kk_cols, _est_order):
                    _c_est = [c for c in causas_activas if c.get("estado") == _est]
                    _kcol.markdown(
                        f"<div style='text-align:center;background:#f0f4ff;"
                        f"border-radius:6px;padding:4px;margin-bottom:6px'>"
                        f"<strong style='font-size:0.85rem'>{_lbl}</strong><br>"
                        f"<span style='font-size:1.4rem;font-weight:bold;color:#2e5090'>"
                        f"{len(_c_est)}</span></div>",
                        unsafe_allow_html=True,
                    )
                    for _c in _c_est[:5]:
                        _clr = _carril_color.get(_c.get("carril", ""), "#aaa")
                        _nom = (_c.get("apellido_nombre", "") or "").split(",")[0][:16]
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
                            unsafe_allow_html=True,
                        )
                    if len(_c_est) > 5:
                        _kcol.caption(f"+ {len(_c_est)-5} mas")
        except Exception as _e:
            st.info(f"Sin causas disponibles.")


def mostrar_si_primera_vez():
    """
    Flujo de ingreso:
    - No logueado → login
    - Logueado pero no intro_vista → dashboard
    - intro_vista == True → app
    """
    if not st.session_state.get("usuario_logueado"):
        _render_login()
        return False

    if not st.session_state.get("intro_vista"):
        _render_dashboard()
        return False

    return True
