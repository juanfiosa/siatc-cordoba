# -*- coding: utf-8 -*-
"""
Módulo de mensajería inter-oficina — SIATC MPF Córdoba
Gestiona pases de expediente y notificaciones entre oficinas del MPF.
"""
from __future__ import annotations  # Python 3.9 compat: defer type annotation evaluation

import streamlit as st
from datetime import datetime
import database as db
from config_nodos import get_oficinas_nodo, get_flujos_nodo, NODOS

# ── OFICINAS: obtenidas dinámicamente desde el nodo activo ───────────────────
# Las funciones a continuación reciben nodo_key y construyen la vista apropiada

def get_oficinas(nodo_key: str) -> dict[str, dict]:
    """
    Retorna el catálogo de oficinas del nodo.
    Prioridad: DB (dinámica) → config_nodos.py (fallback estático).
    """
    # Try DB first (populated by seed_nodos_desde_config)
    try:
        db_oficinas = db.get_oficinas_db(nodo_key)
        if db_oficinas:
            result = {}
            for o in db_oficinas:
                result[o["oficina_key"]] = {
                    "label":       o["label"],
                    "label_corto": o["label"][:25],
                    "icon":        o.get("icon", "⚖️"),
                    "tipo":        o.get("tipo", "activa"),
                    "descripcion": "",
                }
            return result
    except Exception:
        pass
    # Fallback to static config
    raw = get_oficinas_nodo(nodo_key)
    result = {}
    for key, o in raw.items():
        result[key] = {
            "label":       o["label"],
            "label_corto": o["label"][:25],
            "icon":        o["icon"],
            "tipo":        o["tipo"],
            "descripcion": o.get("descripcion", ""),
        }
    return result


# Para compatibilidad con código existente que usa OFICINAS directamente
# se define como proxy del nodo por defecto
OFICINAS = get_oficinas("cba_norte")

# Tipos de mensaje con descripción
TIPOS_MENSAJE = {
    "notificacion": {
        "label": "Notificación",
        "icon": "📢",
        "descripcion": "Comunica un hecho o providencia (no requiere respuesta obligatoria)",
        "color": "#cce5ff",
    },
    "instruccion": {
        "label": "Instrucción",
        "icon": "📋",
        "descripcion": "Orden del fiscal que requiere acuse de recibo y respuesta",
        "color": "#fff3cd",
    },
    "consulta": {
        "label": "Consulta",
        "icon": "❓",
        "descripcion": "Solicita orientación o decisión al receptor",
        "color": "#d4edda",
    },
    "respuesta": {
        "label": "Respuesta",
        "icon": "↩️",
        "descripcion": "Responde a una instrucción o consulta previa",
        "color": "#e2e3e5",
    },
    "resolucion": {
        "label": "Resolución",
        "icon": "📜",
        "descripcion": "Comunicación de una resolución formal",
        "color": "#f8d7da",
    },
}

# Flujos permitidos: ahora son dinámicos por nodo
# FLUJOS_PERMITIDOS se usa como fallback estático; preferir get_flujos_nodo(nodo_key)
FLUJOS_PERMITIDOS = get_flujos_nodo("cba_norte")

# Plantillas de mensajes frecuentes por tipo de comunicación
PLANTILLAS = {
    ("policia_judicial", "instruccion"): [
        ("Cítese al imputado/a", "Sírvase citar al imputado/a {imputado} (DNI {dni}) a comparecer ante esta Unidad el día ______ a las ______ hs. Adjunto cédula de notificación."),
        ("Procédase al secuestro", "Ordénese el secuestro de los elementos descriptos en las actuaciones de la causa {numero}. Procédase conforme art. 129 CCC."),
        ("Elévese acta de diligencia", "Procédase a labrar acta circunstanciada de la diligencia realizada en causa {numero} y elévese a esta Fiscalía en el plazo de 48 hs."),
        ("Deje en libertad al detenido", "Dispóngase la libertad del detenido/a {imputado} (DNI {dni}), en causa {numero}."),
    ],
    ("policia_judicial", "notificacion"): [
        ("Ingreso de nueva causa", "Se eleva actuación contravencional labrada por hecho ocurrido el {fecha}. Imputado/a: {imputado} (DNI {dni}). Infracción: {infraccion}."),
        ("Diligencia cumplida", "Se informa que se dio cumplimiento a la instrucción impartida en causa {numero}. Imputado/a notificado/a con fecha ______."),
        ("Imputado incomparece", "Se hace saber que el/la imputado/a {imputado} (DNI {dni}) no compareció a la citación dispuesta en causa {numero} para el día ______."),
        ("Secuestro efectuado", "Se informa que se efectuó el secuestro ordenado en causa {numero}. Los elementos se encuentran a disposición de esa Fiscalía."),
    ],
    ("unidad_norte", "instruccion"): [
        ("Instrucción a Policía Judicial", "Instrúyase a Policía Judicial para que proceda conforme se indica en la presente y en los plazos previstos por el Código de Convivencia Ciudadana."),
    ],
}


# ── CRUD — Mensajes ────────────────────────────────────────────────────────────

def enviar_mensaje(
    causa_id: int | None,
    tipo: str,
    asunto: str,
    cuerpo: str,
    oficina_origen: str,
    usuario_origen: str,
    oficina_destino: str,
    adjunto_tipo: str = "",
    prioridad: str = "normal",
    referencia_id: int | None = None,
) -> int:
    """Crea un mensaje inter-oficina. Retorna el id del mensaje."""
    with db.get_conn() as conn:
        cur = conn.execute(
            """INSERT INTO mensajes_interoficina
               (causa_id, tipo, asunto, cuerpo, oficina_origen, usuario_origen,
                oficina_destino, adjunto_tipo, prioridad, referencia_id)
               VALUES (?,?,?,?,?,?,?,?,?,?)""",
            (causa_id, tipo, asunto, cuerpo, oficina_origen, usuario_origen,
             oficina_destino, adjunto_tipo, prioridad, referencia_id)
        )
    return cur.lastrowid


def get_bandeja_entrada(oficina: str, solo_no_leidos: bool = False) -> list[dict]:
    """Mensajes recibidos por una oficina, ordenados por prioridad y fecha."""
    sql = """
        SELECT m.*, c.numero, c.apellido_nombre
        FROM mensajes_interoficina m
        LEFT JOIN causas c ON m.causa_id = c.id
        WHERE m.oficina_destino = ?
    """
    params = [oficina]
    if solo_no_leidos:
        sql += " AND m.leido_at IS NULL"
    sql += " ORDER BY CASE m.prioridad WHEN 'urgente' THEN 0 ELSE 1 END, m.created_at DESC"
    with db.get_conn() as conn:
        rows = conn.execute(sql, params).fetchall()
    return [dict(r) for r in rows]


def get_bandeja_salida(oficina: str) -> list[dict]:
    """Mensajes enviados por una oficina."""
    with db.get_conn() as conn:
        rows = conn.execute(
            """SELECT m.*, c.numero, c.apellido_nombre
               FROM mensajes_interoficina m
               LEFT JOIN causas c ON m.causa_id = c.id
               WHERE m.oficina_origen = ?
               ORDER BY m.created_at DESC""",
            (oficina,)
        ).fetchall()
    return [dict(r) for r in rows]


def get_mensajes_causa(causa_id: int) -> list[dict]:
    """Todos los mensajes de una causa, ordenados cronológicamente."""
    with db.get_conn() as conn:
        rows = conn.execute(
            """SELECT m.*
               FROM mensajes_interoficina m
               WHERE m.causa_id = ?
               ORDER BY m.created_at ASC""",
            (causa_id,)
        ).fetchall()
    return [dict(r) for r in rows]


def marcar_leido(mensaje_id: int) -> None:
    with db.get_conn() as conn:
        conn.execute(
            "UPDATE mensajes_interoficina SET leido_at=datetime('now','localtime'), estado='recibido' WHERE id=?",
            (mensaje_id,)
        )


def marcar_procesado(mensaje_id: int) -> None:
    with db.get_conn() as conn:
        conn.execute(
            "UPDATE mensajes_interoficina SET estado='procesado' WHERE id=?",
            (mensaje_id,)
        )


def count_no_leidos(oficina: str) -> int:
    with db.get_conn() as conn:
        r = conn.execute(
            "SELECT COUNT(*) as n FROM mensajes_interoficina WHERE oficina_destino=? AND leido_at IS NULL",
            (oficina,)
        ).fetchone()
    return r["n"] if r else 0


# ── CRUD — Pases de expediente ─────────────────────────────────────────────────

def registrar_pase(
    causa_id: int,
    oficina_origen: str,
    usuario_origen: str,
    oficina_destino: str,
    motivo: str,
    observaciones: str = "",
    nodo_key: str = "cba_norte",
) -> int:
    """
    Registra el pase formal del expediente entre oficinas.
    - Oficinas activas: actualiza oficina_actual en DB + nota de timeline.
    - Oficinas fantasma (Juzgado, Mediación): registra el pase pero indica
      que el envío es físico; genera_pdf_pase() puede generar el documento.
    """
    _ofs = get_oficinas(nodo_key)
    _es_fantasma = _ofs.get(oficina_destino, {}).get("tipo") == "fantasma"
    _destino_label = _ofs.get(oficina_destino, {}).get("label", oficina_destino)

    with db.get_conn() as conn:
        conn.execute(
            "UPDATE causas SET oficina_actual=?, updated_at=datetime('now','localtime') WHERE id=?",
            (oficina_destino, causa_id)
        )
        cur = conn.execute(
            """INSERT INTO pases_expediente
               (causa_id, oficina_origen, usuario_origen, oficina_destino, motivo, observaciones)
               VALUES (?,?,?,?,?,?)""",
            (causa_id, oficina_origen, usuario_origen, oficina_destino, motivo, observaciones)
        )
        pase_id = cur.lastrowid

    _nota = (
        f"PASE EXTERNO (físico): Expediente remitido a {_destino_label}. "
        f"Motivo: {motivo}. Pendiente acuerdo institucional — envío por mesa de entradas."
        if _es_fantasma else
        f"PASE A OFICINA: Expediente remitido a {_destino_label}. Motivo: {motivo}."
    )
    db.agregar_nota_causa(causa_id, _nota, usuario_origen)
    return pase_id


def generar_pdf_pase(causa: dict, oficina_destino: str, motivo: str,
                     observaciones: str, fiscal_nombre: str,
                     nodo_key: str = "cba_norte") -> bytes:
    """
    Genera un PDF de remisión para pases a oficinas externas (fantasma).
    El fiscal lo imprime y lo presenta físicamente en la mesa de entradas
    del Juzgado o del Centro de Mediación.
    """
    from pdf_gen import PDFMPFBase, _s, _fecha_formal, AZUL_MPF, AZUL_CLARO, NEGRO, GRIS_TEXTO
    from io import BytesIO
    from datetime import datetime

    _ofs         = get_oficinas(nodo_key)
    _dest_label  = _ofs.get(oficina_destino, {}).get("label", oficina_destino)
    unidad_key   = "norte"  # fallback for PDF header

    pdf = PDFMPFBase(unidad_key)
    pdf.alias_nb_pages()
    pdf.add_page()
    pdf.titulo_documento("Oficio de Remision de Actuaciones")

    pdf._sf("B", 9); pdf.set_text_color(*AZUL_CLARO)
    pdf.cell(0, 6, _s(f"Fecha: {_fecha_formal()}  -  Generado: {datetime.now().strftime('%H:%M hs')}"), ln=True)
    pdf.set_text_color(*NEGRO); pdf.ln(4)

    pdf._sf("B", 10); pdf.set_text_color(*AZUL_MPF); pdf.set_fill_color(240, 244, 255)
    pdf.cell(0, 7, "DATOS DE LA REMISION", fill=True, ln=True)
    pdf.set_text_color(*NEGRO); pdf._sf("", 9); pdf.ln(2)

    pdf.cell(60, 5, "Expediente N:", ln=False)
    pdf.cell(130, 5, _s(causa.get("numero", "")), ln=True)
    pdf.cell(60, 5, "Imputado/a:", ln=False)
    pdf.cell(130, 5, _s(causa.get("apellido_nombre", "")), ln=True)
    pdf.cell(60, 5, "DNI:", ln=False)
    pdf.cell(130, 5, _s(causa.get("persona_dni", "")), ln=True)
    pdf.cell(60, 5, "Destino:", ln=False)
    pdf.cell(130, 5, _s(_dest_label), ln=True)
    pdf.cell(60, 5, "Motivo:", ln=False)
    pdf.cell(130, 5, _s(motivo), ln=True)
    pdf.ln(4)

    if observaciones:
        pdf._sf("B", 10); pdf.set_text_color(*AZUL_MPF); pdf.set_fill_color(240, 244, 255)
        pdf.cell(0, 7, "OBSERVACIONES", fill=True, ln=True)
        pdf.set_text_color(*NEGRO); pdf._sf("", 9); pdf.ln(2)
        pdf.multi_cell(0, 5, _s(observaciones))
        pdf.ln(4)

    pdf._sf("B", 9); pdf.set_text_color(*AZUL_MPF); pdf.set_fill_color(240, 244, 255)
    pdf.cell(0, 7, "NOTA ACERCA DEL ENVIO", fill=True, ln=True)
    pdf.set_text_color(*NEGRO); pdf._sf("I", 8); pdf.ln(2)
    pdf.multi_cell(0, 5, _s(
        "La oficina destinataria no se encuentra integrada al sistema SIATC. "
        "Este oficio debe presentarse fisicamente en la Mesa de Entradas correspondiente. "
        "El pase queda registrado en el historial del expediente."
    ))
    pdf.ln(4)
    pdf.linea_firma(fiscal_nombre, "Fiscal / Ayudante Fiscal", "")
    pdf._sf("I", 7); pdf.set_text_color(*GRIS_TEXTO)
    pdf.cell(0, 4, _s(f"Generado por SIATC - MPF Cordoba - {datetime.now().strftime('%d/%m/%Y %H:%M')}"),
             ln=True, align="C")

    buf = BytesIO()
    pdf.output(buf)
    return buf.getvalue()


def get_historial_pases(causa_id: int) -> list[dict]:
    """Historial de pases de un expediente."""
    with db.get_conn() as conn:
        rows = conn.execute(
            "SELECT * FROM pases_expediente WHERE causa_id=? ORDER BY created_at ASC",
            (causa_id,)
        ).fetchall()
    return [dict(r) for r in rows]


def get_oficina_actual(causa_id: int) -> str:
    """Retorna la oficina que actualmente tiene el expediente."""
    with db.get_conn() as conn:
        r = conn.execute(
            "SELECT oficina_actual FROM causas WHERE id=?", (causa_id,)
        ).fetchone()
    return (r["oficina_actual"] or "unidad") if r else "unidad"


# ── UI — Componentes reutilizables ─────────────────────────────────────────────

def render_badge_oficina(oficina_key: str, small: bool = False) -> str:
    """Retorna HTML de un badge de oficina."""
    o = OFICINAS.get(oficina_key, {"icon": "📋", "label_corto": oficina_key, "tipo": "activa"})
    color = "#cce5ff" if o["tipo"] == "activa" else "#e2e3e5"
    size = "0.7rem" if small else "0.8rem"
    return (
        f"<span style='background:{color};border-radius:10px;padding:2px 8px;"
        f"font-size:{size};white-space:nowrap'>{o['icon']} {o['label_corto']}</span>"
    )


def render_bandeja(oficina: str, fiscal_nombre: str):
    """Renderiza la bandeja de entrada de una oficina."""
    mensajes = get_bandeja_entrada(oficina)
    no_leidos = [m for m in mensajes if not m.get("leido_at")]

    if not mensajes:
        st.info("📭 Bandeja vacía — no hay mensajes recibidos.")
        return

    for m in mensajes:
        tm = TIPOS_MENSAJE.get(m["tipo"], TIPOS_MENSAJE["notificacion"])
        leido = bool(m.get("leido_at"))
        urgente = m.get("prioridad") == "urgente"

        bg = "#fff8e1" if urgente and not leido else ("#f8f9fa" if leido else "white")
        border = "#dc3545" if urgente and not leido else (tm["color"])

        with st.container():
            st.markdown(
                f"<div style='border-left:4px solid {border};background:{bg};"
                f"padding:8px 12px;margin:4px 0;border-radius:0 6px 6px 0'>",
                unsafe_allow_html=True
            )
            col_info, col_acc = st.columns([5, 1])
            with col_info:
                _from = OFICINAS.get(m["oficina_origen"], {}).get("label_corto", m["oficina_origen"])
                _causa_ref = f"  ·  **{m['numero']}**" if m.get("numero") else ""
                st.markdown(
                    f"{'🔴 ' if urgente and not leido else ''}"
                    f"**{tm['icon']} {m['asunto']}**{_causa_ref}  \n"
                    f"*De: {_from} · {m['created_at'][:16]}*"
                    + (f"  \n{m['cuerpo'][:200]}{'…' if len(m.get('cuerpo',''))>200 else ''}" if m.get("cuerpo") else "")
                )
            with col_acc:
                if not leido:
                    if st.button("✓ Leído", key=f"msg_read_{m['id']}", use_container_width=True):
                        marcar_leido(m["id"])
                        st.rerun()
                elif m["estado"] != "procesado" and m["tipo"] in ("instruccion", "consulta"):
                    if st.button("✅ Procesado", key=f"msg_proc_{m['id']}", use_container_width=True, type="primary"):
                        marcar_procesado(m["id"])
                        st.rerun()
            st.markdown("</div>", unsafe_allow_html=True)


def render_nuevo_mensaje(causa_id: int | None, causa_numero: str,
                          oficina_origen: str, fiscal_nombre: str,
                          nodo_key: str = "cba_norte"):
    """Formulario para enviar un nuevo mensaje inter-oficina."""
    _oficinas_nodo = get_oficinas(nodo_key)
    _flujos_nodo   = get_flujos_nodo(nodo_key)
    destinos_posibles = _flujos_nodo.get(oficina_origen, [])
    if not destinos_posibles:
        st.warning("Esta oficina no tiene destinos configurados.")
        return

    col1, col2 = st.columns(2)
    with col1:
        dest_sel = st.selectbox(
            "Oficina destinataria",
            destinos_posibles,
            format_func=lambda k: f"{_oficinas_nodo.get(k,{}).get('icon','📋')} {_oficinas_nodo.get(k,{}).get('label', k)}"
                                   + (" 👻" if _oficinas_nodo.get(k,{}).get("tipo") == "fantasma" else ""),
            key=f"msg_dest_{causa_id}",
        )
        if _oficinas_nodo.get(dest_sel, {}).get("tipo") == "fantasma":
            st.warning("⚠️ Oficina externa: el mensaje generará un documento PDF para envío físico.")
    with col2:
        tipo_sel = st.selectbox(
            "Tipo",
            list(TIPOS_MENSAJE.keys()),
            format_func=lambda k: f"{TIPOS_MENSAJE[k]['icon']} {TIPOS_MENSAJE[k]['label']}",
            key=f"msg_tipo_{causa_id}",
        )

    # Template selector
    plantillas_disp = PLANTILLAS.get((oficina_origen, tipo_sel), [])
    if plantillas_disp:
        plantilla_sel = st.selectbox(
            "Plantilla",
            ["— Escribir manualmente —"] + [p[0] for p in plantillas_disp],
            key=f"msg_plantilla_{causa_id}",
        )
        _txt_plantilla = ""
        if plantilla_sel != "— Escribir manualmente —":
            _txt_plantilla = next(p[1] for p in plantillas_disp if p[0] == plantilla_sel)
    else:
        plantilla_sel = None
        _txt_plantilla = ""

    asunto = st.text_input(
        "Asunto",
        value=plantilla_sel if plantilla_sel and plantilla_sel != "— Escribir manualmente —" else "",
        key=f"msg_asunto_{causa_id}",
    )
    cuerpo = st.text_area(
        "Cuerpo del mensaje",
        value=_txt_plantilla,
        height=120,
        key=f"msg_cuerpo_{causa_id}",
    )

    col_pri, col_adj, col_btn = st.columns([1, 2, 1])
    prioridad = col_pri.radio("Prioridad", ["normal", "urgente"], horizontal=True,
                               key=f"msg_pri_{causa_id}")
    adjunto = col_adj.selectbox(
        "Adjunto",
        ["", "cedula", "acta", "requerimiento", "resolucion", "dictamen"],
        format_func=lambda k: {
            "": "Sin adjunto", "cedula": "📄 Cédula de notificación",
            "acta": "📄 Acta", "requerimiento": "📄 Requerimiento",
            "resolucion": "📄 Resolución", "dictamen": "📄 Dictamen",
        }.get(k, k),
        key=f"msg_adj_{causa_id}",
    )

    if col_btn.button("📤 Enviar", key=f"msg_enviar_{causa_id}",
                       type="primary", use_container_width=True):
        if not asunto.strip():
            st.warning("Completá el asunto.")
        else:
            enviar_mensaje(
                causa_id=causa_id,
                tipo=tipo_sel,
                asunto=asunto,
                cuerpo=cuerpo,
                oficina_origen=oficina_origen,
                usuario_origen=fiscal_nombre,
                oficina_destino=dest_sel,
                adjunto_tipo=adjunto,
                prioridad=prioridad,
            )
            st.success(f"Mensaje enviado a {OFICINAS.get(dest_sel,{}).get('label','oficina destinataria')}.")
            st.rerun()


def render_editor_titulares(nodo_key: str, fiscal_nombre: str):
    """
    UI para editar los titulares de las oficinas del nodo.
    Se muestra en el Panel de Control bajo 'Configuración del nodo'.
    """
    oficinas_nodo = get_oficinas(nodo_key)
    titulares_actuales = db.get_titulares_nodo(nodo_key)

    st.subheader("👤 Titulares de oficinas")
    st.caption(
        "Cargá el nombre del fiscal o funcionario titular de cada oficina. "
        "Una vez guardado, aparecerá en los mensajes y el panel del nodo."
    )

    CARGOS = ["Fiscal", "Fiscal Adjunto/a", "Ayudante Fiscal", "Fiscal Interino/a",
              "Of. Mayor", "Secretario/a", "Otro"]

    for oficina_key, o in oficinas_nodo.items():
        if o.get("tipo") == "fantasma":
            continue   # no editar fantasmas
        actual = titulares_actuales.get(oficina_key, {})
        with st.expander(
            f"{o['icon']} {o['label']}"
            + (f" — {actual['titular']}" if actual.get("titular") else " — *sin titular cargado*"),
            expanded=False,
        ):
            col_n, col_c, col_btn = st.columns([4, 2, 1])
            _nombre_val = actual.get("titular", "")
            _cargo_val  = actual.get("cargo", "Fiscal")
            nuevo_nombre = col_n.text_input(
                "Nombre y apellido",
                value=_nombre_val,
                placeholder="Ej: Dr. Juan Pérez",
                key=f"tit_nombre_{nodo_key}_{oficina_key}",
            )
            nuevo_cargo = col_c.selectbox(
                "Cargo",
                CARGOS,
                index=CARGOS.index(_cargo_val) if _cargo_val in CARGOS else 0,
                key=f"tit_cargo_{nodo_key}_{oficina_key}",
            )
            if col_btn.button("💾", key=f"tit_save_{nodo_key}_{oficina_key}",
                              help="Guardar", use_container_width=True):
                db.set_titular(nodo_key, oficina_key, nuevo_nombre.strip(),
                               nuevo_cargo, fiscal_nombre)
                st.success("Titular guardado.")
                st.rerun()
