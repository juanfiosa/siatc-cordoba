# -*- coding: utf-8 -*-
"""
Pantalla de ingreso al sistema SIATC.
Flujo: Login → Perfil → Home → Modulo
"""
from __future__ import annotations
import streamlit as st
from config_nodos import USUARIOS_DEMO, NODOS, get_oficinas_nodo

ETAPAS = [
    ("Ingreso",      "Registro del hecho contravencional"),
    ("Triaje",       "Clasificacion automatica Verde/Amarillo/Rojo"),
    ("Notificacion", "Cedula de citacion al imputado/a"),
    ("Audiencia",    "Mediacion, suspension o proceso pleno"),
    ("Resolucion",   "Dictamen, acuerdo o requerimiento"),
    ("Seguimiento",  "Monitoreo de condiciones impuestas"),
    ("Cierre",       "Archivo de la causa"),
]

SECCIONES = [
    ("nueva_causa",  "📋", "Nueva Causa",   "Registrar e ingresar un hecho contravencional al sistema"),
    ("mis_causas",   "📂", "Mis Causas",    "Gestionar expedientes en tramite, notas y pases"),
    ("agenda",       "📅", "Agenda",        "Audiencias programadas, proximas y control de asistencia"),
    ("seguimiento",  "🔍", "Seguimiento",   "Condiciones post-resolucion y control de cumplimiento"),
    ("mensajeria",   "📨", "Mensajeria",    "Notificaciones e instrucciones entre oficinas del MPF"),
    ("estadisticas", "📊", "Estadisticas",  "Panel de control, KPIs y exportacion de informes"),
]

CARGOS = ["Fiscal", "Fiscal Adjunto/a", "Ayudante Fiscal", "Fiscal Interino/a",
          "Secretario/a", "Of. Mayor", "Otro"]


# ── PASO 1: Login ─────────────────────────────────────────────────────────────

def _render_login():
    st.markdown(
        "<div style='background:linear-gradient(135deg,#1a2f5e,#2e5090,#3a6bc4);"
        "border-radius:12px;padding:2rem 2.5rem 1.5rem;color:white;"
        "margin-bottom:1.5rem;text-align:center'>"
        "<h2 style='margin:0 0 0.3rem 0'>⚖️ SIATC</h2>"
        "<p style='margin:0;opacity:0.85;font-size:1.05rem'>"
        "Sistema Inteligente de Apoyo al Trabajo Contravencional</p>"
        "<p style='margin:0.4rem 0 0;opacity:0.65;font-size:0.85rem'>"
        "Ministerio Publico Fiscal de Cordoba - Ley N 10.326</p>"
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
                st.session_state.update({
                    "usuario_logueado": True,
                    "fiscal_nombre":    u["nombre"],
                    "nodo_key":         u["nodo"],
                    "oficina_key":      u["oficina"],
                    "oficina_label":    oficina_cfg.get("label", u["oficina"]),
                    "circunscripcion":  nodo_cfg.get("circunscripcion", ""),
                    "unidad_key": (
                        "norte"  if "norte"  in u["oficina"] else
                        "sur"    if "sur"    in u["oficina"] else
                        "genero" if "genero" in u["oficina"] else
                        "norte"
                    ),
                })
                st.rerun()
            else:
                st.error("Usuario o contrasena incorrectos.")

        with st.expander("Ver usuarios demo"):
            st.markdown(
                "**Cordoba Capital**  \n"
                "`aperez` · `cmedina` · `lsuarez` · `pjudicial`  \n\n"
                "**Rio Cuarto**  \n"
                "`mrodriguez` · `sgomez` · `policiarc`  \n\n"
                "**Demo:** `demo`  |  **Contrasena:** `mpf2024`"
            )

    with col_info:
        st.markdown("#### Flujo del expediente")
        for i, (etapa, desc) in enumerate(ETAPAS):
            n = i + 1
            st.markdown(
                f"<div style='display:flex;gap:8px;margin:4px 0;align-items:center'>"
                f"<span style='background:#2e5090;color:white;border-radius:50%;"
                f"width:22px;height:22px;display:flex;align-items:center;"
                f"justify-content:center;font-size:0.75rem;flex-shrink:0'>{n}</span>"
                f"<div><strong>{etapa}</strong> — <span style='color:#555;font-size:0.85rem'>{desc}</span></div>"
                f"</div>",
                unsafe_allow_html=True,
            )


# ── PASO 2: Perfil ────────────────────────────────────────────────────────────

def _render_perfil():
    nombre    = st.session_state.get("fiscal_nombre", "")
    of_label  = st.session_state.get("oficina_label", "")
    circ      = st.session_state.get("circunscripcion", "")
    nodo_key  = st.session_state.get("nodo_key", "cba_norte")
    nodo_cfg  = NODOS.get(nodo_key, {})

    st.markdown(
        "<div style='background:linear-gradient(90deg,#1a2f5e,#2e5090);border-radius:10px;"
        "padding:1.2rem 1.8rem;color:white;margin-bottom:1.5rem'>"
        "<h3 style='margin:0'>Confirma tus datos de trabajo</h3>"
        "<p style='margin:0.3rem 0 0;opacity:0.8;font-size:0.9rem'>"
        "Esta informacion quedara guardada. La podras cambiar desde tu perfil.</p>"
        "</div>",
        unsafe_allow_html=True,
    )

    col_a, col_b = st.columns(2)

    with col_a:
        st.markdown("**Tu identificacion**")
        nuevo_nombre = st.text_input("Nombre completo",
                                     value=nombre,
                                     placeholder="Ej: Dr. Juan Perez",
                                     key="perfil_nombre")
        nuevo_cargo  = st.selectbox("Cargo", CARGOS, key="perfil_cargo")

    with col_b:
        st.markdown("**Tu oficina**")
        oficinas_nodo = get_oficinas_nodo(nodo_key)
        of_activas    = {k: v for k, v in oficinas_nodo.items() if v.get("activa", True)}
        of_key_actual = st.session_state.get("oficina_key", list(of_activas.keys())[0] if of_activas else "")
        of_keys       = list(of_activas.keys())
        of_idx        = of_keys.index(of_key_actual) if of_key_actual in of_keys else 0
        nueva_oficina = st.selectbox(
            "Oficina",
            of_keys,
            index=of_idx,
            format_func=lambda k: f"{of_activas[k]['icon']} {of_activas[k]['label']}",
            key="perfil_oficina",
        )
        st.caption(f"Nodo: {nodo_cfg.get('nombre','')}  \n{circ}")

    st.markdown("")
    if st.button("Confirmar y comenzar", type="primary", use_container_width=True):
        st.session_state.update({
            "fiscal_nombre":    nuevo_nombre.strip() or nombre,
            "fiscal_cargo":     nuevo_cargo,
            "oficina_key":      nueva_oficina,
            "oficina_label":    of_activas.get(nueva_oficina, {}).get("label", nueva_oficina),
            "perfil_configurado": True,
        })
        st.rerun()


# ── PASO 3: Home ──────────────────────────────────────────────────────────────

def _render_home():
    nombre    = st.session_state.get("fiscal_nombre", "")
    cargo     = st.session_state.get("fiscal_cargo", "")
    of_label  = st.session_state.get("oficina_label", "")
    circ      = st.session_state.get("circunscripcion", "")

    # Header compacto
    col_id, col_sal = st.columns([5, 1])
    col_id.markdown(
        f"<div style='background:linear-gradient(90deg,#1a2f5e,#2e5090);border-radius:8px;"
        f"padding:0.7rem 1.2rem;color:white'>"
        f"<strong>⚖️ SIATC</strong> &nbsp;·&nbsp; {of_label}"
        f"<br><span style='opacity:0.8;font-size:0.82rem'>"
        f"{cargo} {nombre} &nbsp;·&nbsp; {circ}</span>"
        f"</div>",
        unsafe_allow_html=True,
    )
    if col_sal.button("🚪 Salir", use_container_width=True):
        for k in ("usuario_logueado","fiscal_nombre","nodo_key","oficina_key",
                  "oficina_label","circunscripcion","perfil_configurado","intro_vista"):
            st.session_state.pop(k, None)
        st.rerun()

    st.markdown("<br>", unsafe_allow_html=True)

    # Stats rapidas
    try:
        import database as _db
        _s   = _db.stats_generales()
        _sa  = _db.stats_audiencias()
        _ss  = _db.stats_seguimiento()
        from mensajeria import count_no_leidos as _cnl
        _nml = _cnl(st.session_state.get("oficina_key",""))
        _c1,_c2,_c3,_c4 = st.columns(4)
        _c1.metric("Causas en el sistema",  _s.get("total",0))
        _c2.metric("Audiencias hoy",        _sa.get("hoy",0))
        _c3.metric("Seguimientos activos",  _ss.get("activos",0))
        _c4.metric("Mensajes sin leer",     _nml,
                   delta="nueva(s)" if _nml else None,
                   delta_color="inverse" if _nml else "off")
    except Exception:
        pass

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("### Que queres hacer?")

    # Grid de secciones — 3 por fila
    for row_start in range(0, len(SECCIONES), 3):
        row = SECCIONES[row_start:row_start+3]
        cols = st.columns(len(row))
        for col, (sec_key, icon, titulo, desc) in zip(cols, row):
            # Badge para mensajeria
            badge = ""
            if sec_key == "mensajeria":
                try:
                    from mensajeria import count_no_leidos as _cnl2
                    _n = _cnl2(st.session_state.get("oficina_key",""))
                    if _n:
                        badge = f" 🔴 {_n}"
                except Exception:
                    pass
            with col:
                st.markdown(
                    f"<div style='background:#f8f9fa;border:1px solid #dee2e6;"
                    f"border-radius:10px;padding:1.5rem 1rem;text-align:center;"
                    f"min-height:130px;display:flex;flex-direction:column;"
                    f"align-items:center;justify-content:center'>"
                    f"<span style='font-size:2rem'>{icon}</span>"
                    f"<strong style='font-size:1rem;color:#1a2f5e;margin-top:0.5rem'>"
                    f"{titulo}{badge}</strong>"
                    f"<span style='font-size:0.78rem;color:#666;margin-top:0.3rem'>"
                    f"{desc}</span>"
                    f"</div>",
                    unsafe_allow_html=True,
                )
                if st.button(f"Abrir {titulo}", key=f"home_btn_{sec_key}",
                             use_container_width=True):
                    st.session_state["seccion_activa"] = sec_key
                    st.session_state["intro_vista"]    = True
                    st.rerun()

    st.markdown("")
    st.caption("SIATC · MPF Cordoba · v1.3-demo · Ley N 10.326")


# ── Control de flujo ──────────────────────────────────────────────────────────

def mostrar_si_primera_vez():
    """
    Retorna True solo cuando el usuario esta autenticado, perfil configurado
    y ha elegido una seccion. Caso contrario muestra la pantalla correspondiente.
    """
    if not st.session_state.get("usuario_logueado"):
        _render_login()
        return False

    if not st.session_state.get("perfil_configurado"):
        _render_perfil()
        return False

    if not st.session_state.get("intro_vista"):
        _render_home()
        return False

    return True
