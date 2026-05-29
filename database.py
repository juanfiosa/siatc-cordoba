"""
Capa de persistencia — SQLite
SIATC · Ministerio Público Fiscal de Córdoba
"""

import sqlite3
import os
from datetime import datetime
from contextlib import contextmanager

DB_PATH = os.path.join(os.path.dirname(__file__), "siatc.db")

ESTADOS = ["ingresada", "clasificada", "notificada", "en_mediacion", "resuelta", "archivada"]

ESTADOS_LABEL = {
    "ingresada":     "📥 Ingresada",
    "clasificada":   "🔍 Clasificada",
    "notificada":    "📬 Notificada",
    "en_mediacion":  "🤝 En mediación",
    "resuelta":      "✅ Resuelta",
    "archivada":     "🗄️ Archivada",
}

# ── Conexión ───────────────────────────────────────────────────────────────────

@contextmanager
def get_conn():
    conn = sqlite3.connect(DB_PATH, detect_types=sqlite3.PARSE_DECLTYPES)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


# ── Inicialización del esquema ─────────────────────────────────────────────────

def init_db():
    with get_conn() as conn:
        conn.executescript("""
        CREATE TABLE IF NOT EXISTS personas (
            id               INTEGER PRIMARY KEY AUTOINCREMENT,
            dni              TEXT    UNIQUE NOT NULL,
            apellido_nombre  TEXT    NOT NULL,
            edad             INTEGER,
            domicilio        TEXT,
            telefono         TEXT,
            created_at       TEXT    DEFAULT (datetime('now','localtime')),
            updated_at       TEXT    DEFAULT (datetime('now','localtime'))
        );

        CREATE TABLE IF NOT EXISTS causas (
            id                    INTEGER PRIMARY KEY AUTOINCREMENT,
            numero                TEXT    UNIQUE NOT NULL,
            persona_id            INTEGER REFERENCES personas(id),
            tipo_infraccion       TEXT    NOT NULL,
            descripcion           TEXT,
            carril                TEXT,
            accion                TEXT,
            unidad                TEXT,
            fiscal_asignado       TEXT,
            estado                TEXT    DEFAULT 'ingresada',
            victima_identificada  INTEGER DEFAULT 0,
            hay_lesiones          INTEGER DEFAULT 0,
            resistencia_autoridad INTEGER DEFAULT 0,
            score_clasificacion   REAL,
            fecha_hecho           TEXT,
            created_at            TEXT    DEFAULT (datetime('now','localtime')),
            updated_at            TEXT    DEFAULT (datetime('now','localtime'))
        );

        CREATE TABLE IF NOT EXISTS estados_causa (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            causa_id        INTEGER NOT NULL REFERENCES causas(id),
            estado_anterior TEXT,
            estado_nuevo    TEXT    NOT NULL,
            usuario         TEXT,
            observaciones   TEXT,
            created_at      TEXT    DEFAULT (datetime('now','localtime'))
        );

        CREATE TABLE IF NOT EXISTS documentos (
            id             INTEGER PRIMARY KEY AUTOINCREMENT,
            causa_id       INTEGER NOT NULL REFERENCES causas(id),
            tipo_documento TEXT    NOT NULL,
            contenido      TEXT,
            generado_por   TEXT,
            created_at     TEXT    DEFAULT (datetime('now','localtime'))
        );

        CREATE INDEX IF NOT EXISTS idx_causas_persona   ON causas(persona_id);
        CREATE INDEX IF NOT EXISTS idx_causas_estado    ON causas(estado);
        CREATE INDEX IF NOT EXISTS idx_causas_carril    ON causas(carril);
        CREATE INDEX IF NOT EXISTS idx_estados_causa_id ON estados_causa(causa_id);
        CREATE INDEX IF NOT EXISTS idx_docs_causa_id    ON documentos(causa_id);

        CREATE TABLE IF NOT EXISTS seguimientos (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            causa_id        INTEGER NOT NULL REFERENCES causas(id),
            tipo_resolucion TEXT    NOT NULL,
            fecha_inicio    TEXT    NOT NULL,
            fecha_fin       TEXT    NOT NULL,
            estado          TEXT    DEFAULT 'activo',
            fiscal          TEXT,
            observaciones   TEXT,
            created_at      TEXT    DEFAULT (datetime('now','localtime'))
        );

        CREATE TABLE IF NOT EXISTS condiciones (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            seguimiento_id  INTEGER NOT NULL REFERENCES seguimientos(id),
            tipo            TEXT    NOT NULL,
            descripcion     TEXT    NOT NULL,
            valor_objetivo  REAL    DEFAULT 0,
            unidad          TEXT    DEFAULT '',
            estado          TEXT    DEFAULT 'pendiente',
            fecha_limite    TEXT    DEFAULT '',
            created_at      TEXT    DEFAULT (datetime('now','localtime'))
        );

        CREATE TABLE IF NOT EXISTS registros_cumplimiento (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            condicion_id    INTEGER NOT NULL REFERENCES condiciones(id),
            fecha           TEXT    NOT NULL,
            valor_parcial   REAL    DEFAULT 0,
            observaciones   TEXT    DEFAULT '',
            usuario         TEXT    DEFAULT '',
            created_at      TEXT    DEFAULT (datetime('now','localtime'))
        );

        CREATE INDEX IF NOT EXISTS idx_seg_causa    ON seguimientos(causa_id);
        CREATE INDEX IF NOT EXISTS idx_cond_seg     ON condiciones(seguimiento_id);
        CREATE INDEX IF NOT EXISTS idx_reg_cond     ON registros_cumplimiento(condicion_id);

        CREATE TABLE IF NOT EXISTS audiencias (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            causa_id      INTEGER NOT NULL REFERENCES causas(id),
            tipo          TEXT    NOT NULL DEFAULT 'audiencia',
            fecha         TEXT    NOT NULL,
            hora          TEXT    DEFAULT '09:00',
            lugar         TEXT    DEFAULT '',
            estado        TEXT    DEFAULT 'programada',
            observaciones TEXT    DEFAULT '',
            created_at    TEXT    DEFAULT (datetime('now','localtime'))
        );

        CREATE INDEX IF NOT EXISTS idx_aud_causa ON audiencias(causa_id);
        CREATE INDEX IF NOT EXISTS idx_aud_fecha ON audiencias(fecha);
        """)
        # Safe migrations — ALTER TABLE is idempotent via try/except
        try:
            conn.execute("ALTER TABLE seguimientos ADD COLUMN proximo_control TEXT")
        except Exception:
            pass  # column already exists


def reset_db():
    """Trunca todas las tablas y reinicia las secuencias de autoincrement.
    Más confiable que eliminar el archivo cuando Streamlit mantiene conexiones abiertas."""
    with get_conn() as conn:
        conn.executescript("""
        DELETE FROM registros_cumplimiento;
        DELETE FROM condiciones;
        DELETE FROM seguimientos;
        DELETE FROM audiencias;
        DELETE FROM documentos;
        DELETE FROM estados_causa;
        DELETE FROM causas;
        DELETE FROM personas;
        DELETE FROM sqlite_sequence WHERE name IN (
            'registros_cumplimiento','condiciones','seguimientos','audiencias',
            'documentos','estados_causa','causas','personas'
        );
        """)


# ── Personas ───────────────────────────────────────────────────────────────────

def buscar_persona_por_dni(dni: str) -> dict | None:
    dni_clean = dni.replace(".", "").replace("-", "").strip()
    with get_conn() as conn:
        row = conn.execute(
            "SELECT * FROM personas WHERE replace(replace(dni,'.',''),'-','') = ?",
            (dni_clean,)
        ).fetchone()
    return dict(row) if row else None


def contar_antecedentes(persona_id: int) -> int:
    """Causas resueltas o archivadas = antecedentes."""
    with get_conn() as conn:
        row = conn.execute(
            "SELECT COUNT(*) as n FROM causas WHERE persona_id=? AND estado IN ('resuelta','archivada')",
            (persona_id,)
        ).fetchone()
    return row["n"] if row else 0


def upsert_persona(dni: str, apellido_nombre: str, edad: int,
                   domicilio: str = "", telefono: str = "") -> int:
    with get_conn() as conn:
        existing = conn.execute(
            "SELECT id FROM personas WHERE replace(replace(dni,'.',''),'-','') = ?",
            (dni.replace(".", "").replace("-", "").strip(),)
        ).fetchone()
        if existing:
            conn.execute(
                """UPDATE personas SET apellido_nombre=?, edad=?, domicilio=?, telefono=?,
                   updated_at=datetime('now','localtime') WHERE id=?""",
                (apellido_nombre, edad, domicilio, telefono, existing["id"])
            )
            return existing["id"]
        else:
            cur = conn.execute(
                "INSERT INTO personas (dni,apellido_nombre,edad,domicilio,telefono) VALUES (?,?,?,?,?)",
                (dni, apellido_nombre, edad, domicilio, telefono)
            )
            return cur.lastrowid


def listar_personas(busqueda: str = "") -> list[dict]:
    with get_conn() as conn:
        if busqueda:
            rows = conn.execute(
                "SELECT * FROM personas WHERE apellido_nombre LIKE ? OR dni LIKE ? ORDER BY apellido_nombre",
                (f"%{busqueda}%", f"%{busqueda}%")
            ).fetchall()
        else:
            rows = conn.execute("SELECT * FROM personas ORDER BY apellido_nombre").fetchall()
    return [dict(r) for r in rows]


# ── Causas ─────────────────────────────────────────────────────────────────────

def _next_numero(unidad: str) -> str:
    prefijos = {"norte": "UCN", "sur": "UCS", "genero": "UCG"}
    pref = prefijos.get(unidad, "UCX")
    year = datetime.now().year
    with get_conn() as conn:
        row = conn.execute(
            "SELECT COUNT(*) as n FROM causas WHERE numero LIKE ?",
            (f"{year}-{pref}-%",)
        ).fetchone()
    seq = (row["n"] if row else 0) + 1
    return f"{year}-{pref}-{seq:05d}"


def guardar_causa(caso: dict, clasificacion: dict, fiscal: str) -> int:
    """Guarda o actualiza una causa. Retorna el id."""
    numero = caso.get("numero") or _next_numero(caso.get("unidad", "norte"))
    persona_id = upsert_persona(
        caso["dni"], caso["imputado"], caso.get("edad", 0),
        caso.get("domicilio", ""), caso.get("telefono", "")
    )
    with get_conn() as conn:
        existing = conn.execute("SELECT id, estado FROM causas WHERE numero=?", (numero,)).fetchone()
        if existing:
            conn.execute(
                """UPDATE causas SET tipo_infraccion=?, descripcion=?, carril=?, accion=?,
                   unidad=?, fiscal_asignado=?, victima_identificada=?, hay_lesiones=?,
                   resistencia_autoridad=?, score_clasificacion=?,
                   updated_at=datetime('now','localtime') WHERE id=?""",
                (
                    caso["tipo"], caso.get("descripcion", ""),
                    clasificacion["carril"], clasificacion["accion"],
                    caso.get("unidad", "norte"), fiscal,
                    int(caso.get("victima", False)), int(caso.get("lesiones", False)),
                    int(caso.get("resistencia", False)), clasificacion.get("score", 0),
                    existing["id"]
                )
            )
            causa_id = existing["id"]
            # Si el estado era ingresada, pasa a clasificada
            if existing["estado"] == "ingresada":
                _registrar_estado(conn, causa_id, "ingresada", "clasificada", fiscal, "Clasificación automática")
        else:
            fecha_hecho_val = caso.get("fecha_hecho") or datetime.now().strftime("%Y-%m-%d")
            cur = conn.execute(
                """INSERT INTO causas (numero,persona_id,tipo_infraccion,descripcion,carril,accion,
                   unidad,fiscal_asignado,estado,victima_identificada,hay_lesiones,
                   resistencia_autoridad,score_clasificacion,fecha_hecho)
                   VALUES (?,?,?,?,?,?,?,?,'clasificada',?,?,?,?,?)""",
                (
                    numero, persona_id, caso["tipo"], caso.get("descripcion", ""),
                    clasificacion["carril"], clasificacion["accion"],
                    caso.get("unidad", "norte"), fiscal,
                    int(caso.get("victima", False)), int(caso.get("lesiones", False)),
                    int(caso.get("resistencia", False)), clasificacion.get("score", 0),
                    fecha_hecho_val,
                )
            )
            causa_id = cur.lastrowid
            _registrar_estado(conn, causa_id, None, "clasificada", fiscal, "Caso ingresado y clasificado")
    return causa_id


def avanzar_estado(causa_id: int, nuevo_estado: str, usuario: str, observaciones: str = "") -> bool:
    with get_conn() as conn:
        row = conn.execute("SELECT estado FROM causas WHERE id=?", (causa_id,)).fetchone()
        if not row:
            return False
        estado_actual = row["estado"]
        if nuevo_estado not in ESTADOS:
            return False
        conn.execute(
            "UPDATE causas SET estado=?, updated_at=datetime('now','localtime') WHERE id=?",
            (nuevo_estado, causa_id)
        )
        _registrar_estado(conn, causa_id, estado_actual, nuevo_estado, usuario, observaciones)
    return True


def _registrar_estado(conn, causa_id, anterior, nuevo, usuario, obs=""):
    conn.execute(
        "INSERT INTO estados_causa (causa_id,estado_anterior,estado_nuevo,usuario,observaciones) VALUES (?,?,?,?,?)",
        (causa_id, anterior, nuevo, usuario, obs)
    )


def agregar_nota_causa(causa_id: int, nota: str, usuario: str) -> bool:
    """Registra una nota libre en la causa sin cambiar su estado.
    Aparece en el historial con estado_anterior == estado_nuevo."""
    if not nota or not nota.strip():
        return False
    with get_conn() as conn:
        row = conn.execute("SELECT estado FROM causas WHERE id=?", (causa_id,)).fetchone()
        if not row:
            return False
        estado_actual = row["estado"]
        # Touch updated_at so the causa appears as recently active
        conn.execute(
            "UPDATE causas SET updated_at=datetime('now','localtime') WHERE id=?",
            (causa_id,)
        )
        conn.execute(
            "INSERT INTO estados_causa (causa_id,estado_anterior,estado_nuevo,usuario,observaciones) VALUES (?,?,?,?,?)",
            (causa_id, estado_actual, estado_actual, usuario, nota.strip())
        )
    return True


def listar_causas(estado: str = None, carril: str = None, unidad: str = None,
                  busqueda: str = None, tipo_infraccion: str = None,
                  fecha_desde: str = None, fecha_hasta: str = None,
                  fiscal: str = None,
                  limit: int = 200) -> list[dict]:
    """
    Devuelve causas filtradas. fecha_desde / fecha_hasta filtran sobre created_at (YYYY-MM-DD).
    """
    sql = """
        SELECT c.*, p.apellido_nombre, p.dni as persona_dni,
               p.edad as persona_edad, p.domicilio as persona_domicilio,
               p.telefono as persona_telefono
        FROM causas c
        LEFT JOIN personas p ON c.persona_id = p.id
        WHERE 1=1
    """
    params = []
    if estado:
        sql += " AND c.estado = ?"
        params.append(estado)
    if carril:
        sql += " AND c.carril = ?"
        params.append(carril)
    if unidad:
        sql += " AND c.unidad = ?"
        params.append(unidad)
    if tipo_infraccion:
        sql += " AND c.tipo_infraccion = ?"
        params.append(tipo_infraccion)
    if fecha_desde:
        sql += " AND c.created_at >= ?"
        params.append(fecha_desde)
    if fecha_hasta:
        sql += " AND c.created_at <= ?"
        params.append(fecha_hasta + " 23:59:59")
    if fiscal:
        sql += " AND c.fiscal_asignado = ?"
        params.append(fiscal)
    if busqueda:
        sql += """ AND (p.apellido_nombre LIKE ? OR c.numero LIKE ? OR p.dni LIKE ?
                        OR c.tipo_infraccion LIKE ? OR c.descripcion LIKE ?)"""
        params.extend([f"%{busqueda}%"] * 5)
    sql += " ORDER BY c.created_at DESC LIMIT ?"
    params.append(limit)
    with get_conn() as conn:
        rows = conn.execute(sql, params).fetchall()
    return [dict(r) for r in rows]


def causas_similares(tipo_infraccion: str, exclude_persona_id: int = None,
                     limit: int = 6) -> list[dict]:
    """Causas del mismo tipo de infracción, excluyendo al imputado dado."""
    sql = """
        SELECT c.*, p.apellido_nombre, p.dni as persona_dni, p.edad as persona_edad
        FROM causas c
        LEFT JOIN personas p ON c.persona_id = p.id
        WHERE c.tipo_infraccion = ?
    """
    params: list = [tipo_infraccion]
    if exclude_persona_id:
        sql += " AND c.persona_id != ?"
        params.append(exclude_persona_id)
    sql += " ORDER BY c.created_at DESC LIMIT ?"
    params.append(limit)
    with get_conn() as conn:
        rows = conn.execute(sql, params).fetchall()
    return [dict(r) for r in rows]


def get_causa(causa_id: int) -> dict | None:
    with get_conn() as conn:
        row = conn.execute(
            """SELECT c.*, p.apellido_nombre, p.dni as persona_dni, p.edad as persona_edad
               FROM causas c LEFT JOIN personas p ON c.persona_id=p.id WHERE c.id=?""",
            (causa_id,)
        ).fetchone()
    return dict(row) if row else None


def get_timeline(causa_id: int) -> list[dict]:
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT * FROM estados_causa WHERE causa_id=? ORDER BY created_at ASC",
            (causa_id,)
        ).fetchall()
    return [dict(r) for r in rows]


def actividad_reciente(limit: int = 15) -> list[dict]:
    """Retorna las últimas N entradas de estados_causa de cualquier causa,
    con número de expediente y nombre del imputado."""
    sql = """
        SELECT ec.created_at, ec.causa_id, ec.estado_anterior, ec.estado_nuevo,
               ec.usuario, ec.observaciones,
               c.numero, p.apellido_nombre
        FROM estados_causa ec
        JOIN causas c ON ec.causa_id = c.id
        JOIN personas p ON c.persona_id = p.id
        ORDER BY ec.created_at DESC
        LIMIT ?
    """
    with get_conn() as conn:
        rows = conn.execute(sql, (limit,)).fetchall()
    return [dict(r) for r in rows]


# ── Documentos ─────────────────────────────────────────────────────────────────

def guardar_documento(causa_id: int, tipo: str, contenido: str, generado_por: str) -> int:
    with get_conn() as conn:
        cur = conn.execute(
            "INSERT INTO documentos (causa_id,tipo_documento,contenido,generado_por) VALUES (?,?,?,?)",
            (causa_id, tipo, contenido, generado_por)
        )
    return cur.lastrowid


def listar_documentos(causa_id: int) -> list[dict]:
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT * FROM documentos WHERE causa_id=? ORDER BY created_at DESC",
            (causa_id,)
        ).fetchall()
    return [dict(r) for r in rows]


# ── Estadísticas ───────────────────────────────────────────────────────────────

def stats_generales() -> dict:
    with get_conn() as conn:
        total = conn.execute("SELECT COUNT(*) as n FROM causas").fetchone()["n"]
        por_carril = {
            r["carril"]: r["n"]
            for r in conn.execute("SELECT carril, COUNT(*) as n FROM causas GROUP BY carril").fetchall()
            if r["carril"]
        }
        por_estado = {
            r["estado"]: r["n"]
            for r in conn.execute("SELECT estado, COUNT(*) as n FROM causas GROUP BY estado").fetchall()
        }
        por_unidad = {
            r["unidad"]: r["n"]
            for r in conn.execute("SELECT unidad, COUNT(*) as n FROM causas GROUP BY unidad").fetchall()
            if r["unidad"]
        }
        reincidentes = conn.execute(
            """SELECT COUNT(DISTINCT persona_id) as n FROM causas
               WHERE persona_id IN (SELECT persona_id FROM causas GROUP BY persona_id HAVING COUNT(*)>1)"""
        ).fetchone()["n"]
        personas = conn.execute("SELECT COUNT(*) as n FROM personas").fetchone()["n"]

    return {
        "total": total,
        "por_carril": por_carril,
        "por_estado": por_estado,
        "por_unidad": por_unidad,
        "reincidentes": reincidentes,
        "personas": personas,
    }


def causas_por_tipo() -> list[dict]:
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT tipo_infraccion, COUNT(*) as n FROM causas GROUP BY tipo_infraccion ORDER BY n DESC"
        ).fetchall()
    return [dict(r) for r in rows]


def personas_reincidentes(min_causas: int = 2) -> list[dict]:
    """
    Retorna personas con al menos `min_causas` causas registradas,
    con detalle de sus antecedentes y último estado.
    Ordenadas por cantidad de causas descendente.
    """
    sql = """
        SELECT p.id, p.dni, p.apellido_nombre, p.edad,
               COUNT(c.id) as n_causas,
               MAX(c.created_at) as ultima_causa,
               GROUP_CONCAT(DISTINCT c.carril) as carriles,
               GROUP_CONCAT(DISTINCT c.estado) as estados
        FROM personas p
        JOIN causas c ON c.persona_id = p.id
        GROUP BY p.id
        HAVING COUNT(c.id) >= ?
        ORDER BY n_causas DESC, ultima_causa DESC
    """
    with get_conn() as conn:
        rows = conn.execute(sql, (min_causas,)).fetchall()
    return [dict(r) for r in rows]


def causas_por_mes(meses: int = 12) -> list[dict]:
    """Retorna cantidad de causas ingresadas por mes (ultimos N meses)."""
    with get_conn() as conn:
        rows = conn.execute(
            """SELECT strftime('%Y-%m', created_at) as mes, COUNT(*) as n
               FROM causas
               GROUP BY mes
               ORDER BY mes ASC
               LIMIT ?""",
            (meses,)
        ).fetchall()
    return [dict(r) for r in rows]


def stats_tendencia_mensual(meses: int = 12) -> list[dict]:
    """
    Retorna por mes: ingresadas, resueltas/archivadas, y activas acumuladas.
    Used for the management trend chart in Panel de Control.
    Returns list of {mes, ingresadas, cerradas} ordered ASC.
    """
    with get_conn() as conn:
        # Ingresadas por mes
        ing = conn.execute(
            """SELECT strftime('%Y-%m', created_at) as mes, COUNT(*) as n
               FROM causas
               GROUP BY mes ORDER BY mes ASC""",
        ).fetchall()
        # Cerradas (resuelta o archivada) por mes — use updated_at as proxy for close date
        cer = conn.execute(
            """SELECT strftime('%Y-%m', updated_at) as mes, COUNT(*) as n
               FROM causas
               WHERE estado IN ('resuelta', 'archivada')
               GROUP BY mes ORDER BY mes ASC""",
        ).fetchall()
    ing_d = {r["mes"]: r["n"] for r in ing}
    cer_d = {r["mes"]: r["n"] for r in cer}
    all_meses = sorted(set(ing_d) | set(cer_d))
    if meses:
        all_meses = all_meses[-meses:]
    return [{"mes": m, "ingresadas": ing_d.get(m, 0), "cerradas": cer_d.get(m, 0)} for m in all_meses]


def stats_tiempos_resolucion() -> dict:
    """
    Calcula tiempos promedio de resolución (días entre ingresada → resuelta)
    por carril. Compara con el proceso tradicional estimado.
    """
    TIEMPO_TRADICIONAL = {"verde": 90, "amarillo": 150, "rojo": 240}
    with get_conn() as conn:
        rows = conn.execute(
            """
            SELECT c.carril,
                   ROUND(AVG(
                       JULIANDAY(ec_res.created_at) - JULIANDAY(c.created_at)
                   )) as dias_promedio,
                   COUNT(*) as n
            FROM causas c
            JOIN estados_causa ec_res
              ON ec_res.causa_id = c.id AND ec_res.estado_nuevo = 'resuelta'
            WHERE c.carril IS NOT NULL
            GROUP BY c.carril
            """
        ).fetchall()

    por_carril = {}
    for r in rows:
        carril = r["carril"]
        dias   = int(r["dias_promedio"]) if r["dias_promedio"] else None
        trad   = TIEMPO_TRADICIONAL.get(carril, 120)
        por_carril[carril] = {
            "dias_promedio": dias,
            "tradicional":   trad,
            "reduccion_pct": round((trad - dias) / trad * 100) if dias else None,
            "n":             r["n"],
        }
    return por_carril


def causas_mes_actual_vs_anterior() -> dict:
    """Compara causas ingresadas este mes vs. el anterior.
    Retorna {actual, anterior, delta, pct_cambio}."""
    with get_conn() as conn:
        actual = conn.execute(
            "SELECT COUNT(*) as n FROM causas WHERE strftime('%Y-%m', created_at) = strftime('%Y-%m', 'now', 'localtime')"
        ).fetchone()["n"]
        anterior = conn.execute(
            "SELECT COUNT(*) as n FROM causas WHERE strftime('%Y-%m', created_at) = strftime('%Y-%m', 'now', '-1 month', 'localtime')"
        ).fetchone()["n"]
    delta = actual - anterior
    pct = round(delta * 100 / anterior) if anterior else None
    return {"actual": actual, "anterior": anterior, "delta": delta, "pct_cambio": pct}


def causas_por_fiscal() -> list[dict]:
    """Retorna cantidad de causas por fiscal asignado."""
    with get_conn() as conn:
        rows = conn.execute(
            """SELECT fiscal_asignado, COUNT(*) as n
               FROM causas
               WHERE fiscal_asignado IS NOT NULL AND fiscal_asignado != ''
               GROUP BY fiscal_asignado
               ORDER BY n DESC"""
        ).fetchall()
    return [dict(r) for r in rows]


def stats_por_fiscal() -> list[dict]:
    """Estadísticas detalladas por fiscal: total, resueltas, archivadas, pct_resolucion,
    dias_promedio (entre created_at y updated_at para causas resueltas/archivadas)."""
    with get_conn() as conn:
        rows = conn.execute(
            """SELECT
                 fiscal_asignado,
                 COUNT(*) AS total,
                 SUM(CASE WHEN estado IN ('resuelta','archivada') THEN 1 ELSE 0 END) AS resueltas,
                 SUM(CASE WHEN carril IN ('verde','amarillo') THEN 1 ELSE 0 END) AS no_punitivas,
                 ROUND(AVG(CASE WHEN estado IN ('resuelta','archivada')
                       THEN CAST(
                         (julianday(updated_at) - julianday(created_at)) AS REAL)
                       END), 1) AS dias_promedio
               FROM causas
               WHERE fiscal_asignado IS NOT NULL AND fiscal_asignado != ''
               GROUP BY fiscal_asignado
               ORDER BY total DESC"""
        ).fetchall()
    result = []
    for r in rows:
        d = dict(r)
        tot = d["total"] or 0
        res = d["resueltas"] or 0
        d["pct_resolucion"] = round(res * 100 / tot) if tot else 0
        d["pct_no_punitivo"] = round((d["no_punitivas"] or 0) * 100 / tot) if tot else 0
        result.append(d)
    return result


def causas_inactivas(dias: int = 30, estados: list = None) -> list[dict]:
    """
    Retorna causas en estados activos (notificada/clasificada/en_mediacion)
    cuya última actualización supera `dias` días.
    Útil para detectar causas que se están "enfriando" sin resolución.
    """
    if estados is None:
        estados = ["clasificada", "notificada", "en_mediacion"]
    placeholders = ",".join(["?" for _ in estados])
    sql = f"""
        SELECT c.*, p.apellido_nombre, p.dni as persona_dni, p.edad as persona_edad,
               CAST(JULIANDAY('now','localtime') - JULIANDAY(c.updated_at) AS INTEGER) as dias_inactivo
        FROM causas c
        LEFT JOIN personas p ON c.persona_id = p.id
        WHERE c.estado IN ({placeholders})
          AND JULIANDAY('now','localtime') - JULIANDAY(c.updated_at) > ?
        ORDER BY dias_inactivo DESC
    """
    params = estados + [dias]
    with get_conn() as conn:
        rows = conn.execute(sql, params).fetchall()
    return [dict(r) for r in rows]


def causas_sin_seguimiento(estados: list = None) -> list[dict]:
    """
    Causas en estados 'resuelta' o 'en_mediacion' sin seguimiento registrado.
    Útil para detectar resoluciones pendientes de seguimiento post-resolución.
    """
    if estados is None:
        estados = ["resuelta", "en_mediacion"]
    placeholders = ",".join(["?" for _ in estados])
    sql = f"""
        SELECT c.*, p.apellido_nombre, p.dni as persona_dni
        FROM causas c
        LEFT JOIN personas p ON c.persona_id = p.id
        WHERE c.estado IN ({placeholders})
          AND NOT EXISTS (
              SELECT 1 FROM seguimientos s WHERE s.causa_id = c.id
          )
        ORDER BY c.updated_at DESC
    """
    with get_conn() as conn:
        rows = conn.execute(sql, estados).fetchall()
    return [dict(r) for r in rows]


def causas_sin_audiencia_programada(estados: list = None) -> list[dict]:
    """
    Retorna causas en estados activos que no tienen ninguna audiencia
    programada con fecha futura (>=hoy).
    Útil para alertar sobre imputados notificados sin audiencia asignada.
    """
    if estados is None:
        estados = ["notificada", "clasificada"]
    placeholders = ",".join(["?" for _ in estados])
    sql = f"""
        SELECT c.*, p.apellido_nombre, p.dni as persona_dni, p.edad as persona_edad
        FROM causas c
        LEFT JOIN personas p ON c.persona_id = p.id
        WHERE c.estado IN ({placeholders})
          AND NOT EXISTS (
              SELECT 1 FROM audiencias a
              WHERE a.causa_id = c.id
                AND a.estado = 'programada'
                AND a.fecha >= date('now','localtime')
          )
        ORDER BY c.updated_at ASC
    """
    with get_conn() as conn:
        rows = conn.execute(sql, estados).fetchall()
    return [dict(r) for r in rows]


def historial_persona(persona_id: int) -> list[dict]:
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT * FROM causas WHERE persona_id=? ORDER BY created_at DESC",
            (persona_id,)
        ).fetchall()
    return [dict(r) for r in rows]


# ── Seguimiento post-resolución ────────────────────────────────────────────────

def crear_seguimiento(causa_id: int, tipo_resolucion: str,
                      fecha_inicio: str, fecha_fin: str,
                      fiscal: str, observaciones: str = "") -> int:
    with get_conn() as conn:
        cur = conn.execute(
            """INSERT INTO seguimientos
               (causa_id, tipo_resolucion, fecha_inicio, fecha_fin, fiscal, observaciones)
               VALUES (?,?,?,?,?,?)""",
            (causa_id, tipo_resolucion, fecha_inicio, fecha_fin, fiscal, observaciones)
        )
        return cur.lastrowid


def agregar_condicion(seguimiento_id: int, tipo: str, descripcion: str,
                      valor_objetivo: float = 0, unidad: str = "",
                      fecha_limite: str = "") -> int:
    with get_conn() as conn:
        cur = conn.execute(
            """INSERT INTO condiciones
               (seguimiento_id, tipo, descripcion, valor_objetivo, unidad, fecha_limite)
               VALUES (?,?,?,?,?,?)""",
            (seguimiento_id, tipo, descripcion, valor_objetivo, unidad, fecha_limite)
        )
        return cur.lastrowid


def registrar_avance(condicion_id: int, fecha: str, valor_parcial: float,
                     observaciones: str, usuario: str) -> int:
    with get_conn() as conn:
        cur = conn.execute(
            """INSERT INTO registros_cumplimiento
               (condicion_id, fecha, valor_parcial, observaciones, usuario)
               VALUES (?,?,?,?,?)""",
            (condicion_id, fecha, valor_parcial, observaciones, usuario)
        )
        # Calcular acumulado y actualizar estado
        total = conn.execute(
            "SELECT COALESCE(SUM(valor_parcial),0) as t FROM registros_cumplimiento WHERE condicion_id=?",
            (condicion_id,)
        ).fetchone()["t"]
        cond = conn.execute(
            "SELECT valor_objetivo FROM condiciones WHERE id=?", (condicion_id,)
        ).fetchone()
        if cond and cond["valor_objetivo"] > 0 and total >= cond["valor_objetivo"]:
            conn.execute("UPDATE condiciones SET estado='cumplido' WHERE id=?", (condicion_id,))
        elif total > 0:
            conn.execute("UPDATE condiciones SET estado='en_curso' WHERE id=?", (condicion_id,))
        return cur.lastrowid


def marcar_condicion(condicion_id: int, estado: str) -> bool:
    if estado not in ("pendiente", "en_curso", "cumplido", "incumplido"):
        return False
    with get_conn() as conn:
        conn.execute("UPDATE condiciones SET estado=? WHERE id=?", (estado, condicion_id))
    return True


def cerrar_seguimiento(seguimiento_id: int, estado: str) -> bool:
    if estado not in ("cumplido", "incumplido", "revocado"):
        return False
    with get_conn() as conn:
        conn.execute("UPDATE seguimientos SET estado=? WHERE id=?", (estado, seguimiento_id))
    return True


def set_proximo_control(seguimiento_id: int, fecha: str) -> None:
    """Guarda o actualiza la fecha del próximo control de un seguimiento activo."""
    with get_conn() as conn:
        conn.execute("UPDATE seguimientos SET proximo_control=? WHERE id=?",
                     (fecha, seguimiento_id))


def get_seguimiento(seguimiento_id: int) -> dict | None:
    with get_conn() as conn:
        row = conn.execute(
            """SELECT s.*, c.numero, p.apellido_nombre, p.dni
               FROM seguimientos s
               JOIN causas c ON s.causa_id = c.id
               JOIN personas p ON c.persona_id = p.id
               WHERE s.id=?""",
            (seguimiento_id,)
        ).fetchone()
    return dict(row) if row else None


def get_condiciones(seguimiento_id: int) -> list[dict]:
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT * FROM condiciones WHERE seguimiento_id=? ORDER BY id",
            (seguimiento_id,)
        ).fetchall()
    return [dict(r) for r in rows]


def get_registros(condicion_id: int) -> list[dict]:
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT * FROM registros_cumplimiento WHERE condicion_id=? ORDER BY fecha DESC",
            (condicion_id,)
        ).fetchall()
    return [dict(r) for r in rows]


def listar_seguimientos(estado: str = None, unidad: str = None) -> list[dict]:
    sql = """
        SELECT s.*, c.numero, c.unidad, c.tipo_infraccion,
               p.apellido_nombre, p.dni
        FROM seguimientos s
        JOIN causas c ON s.causa_id = c.id
        JOIN personas p ON c.persona_id = p.id
        WHERE 1=1
    """
    params = []
    if estado:
        sql += " AND s.estado=?"
        params.append(estado)
    if unidad:
        sql += " AND c.unidad=?"
        params.append(unidad)
    sql += " ORDER BY s.fecha_fin ASC"
    with get_conn() as conn:
        rows = conn.execute(sql, params).fetchall()
    return [dict(r) for r in rows]


def get_seguimiento_por_causa(causa_id: int) -> dict | None:
    with get_conn() as conn:
        row = conn.execute(
            "SELECT * FROM seguimientos WHERE causa_id=? ORDER BY id DESC LIMIT 1",
            (causa_id,)
        ).fetchone()
    return dict(row) if row else None


def progress_seguimiento(seguimiento_id: int) -> dict:
    """Calcula el progreso global de un seguimiento."""
    condiciones = get_condiciones(seguimiento_id)
    total = len(condiciones)
    if total == 0:
        return {"total": 0, "cumplidas": 0, "en_curso": 0, "pendientes": 0, "incumplidas": 0, "pct": 0}
    cumplidas   = sum(1 for c in condiciones if c["estado"] == "cumplido")
    en_curso    = sum(1 for c in condiciones if c["estado"] == "en_curso")
    incumplidas = sum(1 for c in condiciones if c["estado"] == "incumplido")
    pendientes  = total - cumplidas - en_curso - incumplidas
    return {
        "total": total, "cumplidas": cumplidas, "en_curso": en_curso,
        "pendientes": pendientes, "incumplidas": incumplidas,
        "pct": round(cumplidas / total * 100)
    }


def acumulado_condicion(condicion_id: int) -> float:
    with get_conn() as conn:
        row = conn.execute(
            "SELECT COALESCE(SUM(valor_parcial),0) as t FROM registros_cumplimiento WHERE condicion_id=?",
            (condicion_id,)
        ).fetchone()
    return row["t"] if row else 0.0


def stats_seguimiento() -> dict:
    with get_conn() as conn:
        total   = conn.execute("SELECT COUNT(*) as n FROM seguimientos").fetchone()["n"]
        activos = conn.execute("SELECT COUNT(*) as n FROM seguimientos WHERE estado='activo'").fetchone()["n"]
        cumplidos = conn.execute("SELECT COUNT(*) as n FROM seguimientos WHERE estado='cumplido'").fetchone()["n"]
        incumplidos = conn.execute("SELECT COUNT(*) as n FROM seguimientos WHERE estado='incumplido'").fetchone()["n"]
        vencidos = conn.execute(
            "SELECT COUNT(*) as n FROM seguimientos WHERE estado='activo' AND fecha_fin < date('now')"
        ).fetchone()["n"]
    return {
        "total": total, "activos": activos, "cumplidos": cumplidos,
        "incumplidos": incumplidos, "vencidos": vencidos
    }


# ── Análisis demográfico ───────────────────────────────────────────────────────

_EDAD_GRUPOS = ["16-25", "26-35", "36-45", "46-55", "56+"]


def _edad_bucket(edad: int) -> str:
    if edad <= 25:
        return "16-25"
    if edad <= 35:
        return "26-35"
    if edad <= 45:
        return "36-45"
    if edad <= 55:
        return "46-55"
    return "56+"


def stats_edad() -> dict:
    """Distribución de personas registradas por grupo etario."""
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT edad FROM personas WHERE edad IS NOT NULL AND edad > 0"
        ).fetchall()
    buckets = {g: 0 for g in _EDAD_GRUPOS}
    for row in rows:
        buckets[_edad_bucket(row["edad"])] += 1
    return buckets


def stats_edad_por_carril() -> dict:
    """Cross-tab: número de causas por grupo etario × carril."""
    with get_conn() as conn:
        rows = conn.execute("""
            SELECT p.edad, c.carril
            FROM causas c
            JOIN personas p ON p.id = c.persona_id
            WHERE p.edad IS NOT NULL AND p.edad > 0 AND c.carril IS NOT NULL
        """).fetchall()
    result = {g: {"verde": 0, "amarillo": 0, "rojo": 0} for g in _EDAD_GRUPOS}
    for row in rows:
        bucket = _edad_bucket(row["edad"])
        carril = row["carril"]
        if carril in result[bucket]:
            result[bucket][carril] += 1
    return result


# ── Audiencias / agenda ────────────────────────────────────────────────────────

TIPOS_AUDIENCIA = {
    "audiencia":          "Audiencia contravencional",
    "mediacion":          "Audiencia de mediación",
    "acta_compromiso":    "Suscripción de acta de compromiso",
    "control_seg":        "Control de seguimiento",
    "reprogramada":       "Audiencia reprogramada",
}

ESTADOS_AUDIENCIA = ["programada", "realizada", "ausente", "reprogramada", "cancelada"]


def crear_audiencia(causa_id: int, tipo: str, fecha: str, hora: str = "09:00",
                    lugar: str = "", observaciones: str = "") -> int:
    with get_conn() as conn:
        cur = conn.execute(
            """INSERT INTO audiencias (causa_id, tipo, fecha, hora, lugar, observaciones)
               VALUES (?,?,?,?,?,?)""",
            (causa_id, tipo, fecha, hora, lugar, observaciones)
        )
        return cur.lastrowid


def actualizar_estado_audiencia(audiencia_id: int, estado: str,
                                observaciones: str = "") -> bool:
    if estado not in ESTADOS_AUDIENCIA:
        return False
    with get_conn() as conn:
        conn.execute(
            "UPDATE audiencias SET estado=?, observaciones=? WHERE id=?",
            (estado, observaciones, audiencia_id)
        )
    return True


def listar_audiencias(desde: str = None, hasta: str = None,
                      estado: str = None, causa_id: int = None) -> list[dict]:
    sql = """
        SELECT a.*, c.numero, c.unidad, c.carril,
               p.apellido_nombre, p.dni, p.telefono as persona_telefono,
               p.domicilio as persona_domicilio
        FROM audiencias a
        JOIN causas c ON a.causa_id = c.id
        JOIN personas p ON c.persona_id = p.id
        WHERE 1=1
    """
    params = []
    if desde:
        sql += " AND a.fecha >= ?"
        params.append(desde)
    if hasta:
        sql += " AND a.fecha <= ?"
        params.append(hasta)
    if estado:
        sql += " AND a.estado = ?"
        params.append(estado)
    if causa_id:
        sql += " AND a.causa_id = ?"
        params.append(causa_id)
    sql += " ORDER BY a.fecha ASC, a.hora ASC"
    with get_conn() as conn:
        rows = conn.execute(sql, params).fetchall()
    return [dict(r) for r in rows]


def audiencias_hoy() -> list[dict]:
    from datetime import date
    return listar_audiencias(desde=date.today().isoformat(),
                             hasta=date.today().isoformat(),
                             estado="programada")


def audiencias_proximos_dias(dias: int = 7) -> list[dict]:
    from datetime import date, timedelta
    hoy = date.today()
    return listar_audiencias(desde=hoy.isoformat(),
                             hasta=(hoy + timedelta(days=dias)).isoformat())


def stats_audiencias() -> dict:
    from datetime import date
    hoy = date.today().isoformat()
    with get_conn() as conn:
        total     = conn.execute("SELECT COUNT(*) as n FROM audiencias").fetchone()["n"]
        proximas  = conn.execute(
            "SELECT COUNT(*) as n FROM audiencias WHERE fecha >= ? AND estado='programada'",
            (hoy,)).fetchone()["n"]
        hoy_n     = conn.execute(
            "SELECT COUNT(*) as n FROM audiencias WHERE fecha = ? AND estado='programada'",
            (hoy,)).fetchone()["n"]
        realizadas = conn.execute(
            "SELECT COUNT(*) as n FROM audiencias WHERE estado='realizada'").fetchone()["n"]
        ausentes  = conn.execute(
            "SELECT COUNT(*) as n FROM audiencias WHERE estado='ausente'").fetchone()["n"]
    return {"total": total, "proximas": proximas, "hoy": hoy_n,
            "realizadas": realizadas, "ausentes": ausentes}


# ── Perfil del imputado ────────────────────────────────────────────────────────

def perfil_persona(persona_id: int) -> dict:
    """Devuelve datos completos de una persona: causas, seguimientos, audiencias."""
    with get_conn() as conn:
        persona = conn.execute(
            "SELECT * FROM personas WHERE id=?", (persona_id,)
        ).fetchone()
        if not persona:
            return {}
        causas = conn.execute(
            "SELECT * FROM causas WHERE persona_id=? ORDER BY created_at DESC",
            (persona_id,)
        ).fetchall()
    causas_list = [dict(c) for c in causas]
    causa_ids = [c["id"] for c in causas_list]

    seguimientos_p = []
    audiencias_p   = []
    for cid in causa_ids:
        seg = get_seguimiento_por_causa(cid)
        if seg:
            seguimientos_p.append(seg)
        auds = listar_audiencias(causa_id=cid)
        audiencias_p.extend(auds)

    antecedentes = contar_antecedentes(persona_id)
    return {
        "persona":      dict(persona),
        "causas":       causas_list,
        "seguimientos": seguimientos_p,
        "audiencias":   audiencias_p,
        "antecedentes": antecedentes,
        "total_causas": len(causas_list),
    }


def proximas_audiencias_por_causa() -> dict[int, dict]:
    """
    Retorna la próxima audiencia programada para cada causa_id.
    Formato: {causa_id: {fecha, hora, tipo}} — sólo audiencias con fecha >= hoy.
    """
    from datetime import date
    hoy = date.today().isoformat()
    with get_conn() as conn:
        rows = conn.execute(
            """SELECT a.causa_id, a.fecha, a.hora, a.tipo
               FROM audiencias a
               WHERE a.fecha >= ? AND a.estado = 'programada'
               ORDER BY a.causa_id, a.fecha ASC, a.hora ASC""",
            (hoy,)
        ).fetchall()
    # Keep only the first (earliest) audiencia per causa
    result: dict[int, dict] = {}
    for r in rows:
        cid = r["causa_id"]
        if cid not in result:
            result[cid] = {"fecha": r["fecha"], "hora": r["hora"], "tipo": r["tipo"]}
    return result


def causas_count_por_persona(persona_ids: list) -> dict:
    """Returns {persona_id: total_causas} for the given persona IDs (bulk query)."""
    if not persona_ids:
        return {}
    placeholders = ",".join("?" * len(persona_ids))
    with get_conn() as conn:
        rows = conn.execute(
            f"SELECT persona_id, COUNT(*) as n FROM causas WHERE persona_id IN ({placeholders}) GROUP BY persona_id",
            persona_ids
        ).fetchall()
    return {r["persona_id"]: r["n"] for r in rows}


def stats_por_dia_semana() -> list[dict]:
    """
    Returns count of causas created per day of week (0=Mon … 6=Sun).
    Useful for staffing/resource planning charts.
    """
    with get_conn() as conn:
        rows = conn.execute("""
            SELECT CAST(strftime('%w', created_at) AS INTEGER) AS dow, COUNT(*) AS n
            FROM causas
            GROUP BY dow
            ORDER BY dow
        """).fetchall()
    # SQLite: %w is 0=Sunday, 1=Monday … convert to Mon=0 … Sun=6
    DIA = {0: "Dom", 1: "Lun", 2: "Mar", 3: "Mié", 4: "Jue", 5: "Vie", 6: "Sáb"}
    # remap: SQLite 0→Sun, 1→Mon … → ISO 0→Mon … 6→Sun
    iso_map = {1: 0, 2: 1, 3: 2, 4: 3, 5: 4, 6: 5, 0: 6}
    result = [{
        "dia_num": iso_map.get(r["dow"], r["dow"]),
        "dia":     ["Lun","Mar","Mié","Jue","Vie","Sáb","Dom"][iso_map.get(r["dow"], r["dow"])],
        "n":       r["n"],
    } for r in rows]
    return sorted(result, key=lambda x: x["dia_num"])


def stats_tiempo_por_tipo() -> list[dict]:
    """
    Avg resolution days and count per tipo_infraccion (only resolved/archived causas).
    Returns list of {tipo_infraccion, label, n, dias_promedio} sorted by dias_promedio DESC.
    """
    with get_conn() as conn:
        rows = conn.execute("""
            SELECT tipo_infraccion,
                   COUNT(*) as n,
                   ROUND(AVG(
                       CAST((julianday(updated_at) - julianday(created_at)) AS REAL)
                   ), 1) AS dias_promedio
            FROM causas
            WHERE estado IN ('resuelta', 'archivada')
              AND tipo_infraccion IS NOT NULL AND tipo_infraccion != ''
            GROUP BY tipo_infraccion
            HAVING n >= 1
            ORDER BY dias_promedio DESC
        """).fetchall()
    # Enrich with human-readable label from TIPOS_INFRACCION
    from data_cordoba import TIPOS_INFRACCION as _TI
    result = []
    for r in rows:
        d = dict(r)
        _inf = _TI.get(d["tipo_infraccion"], {})
        d["label"] = _inf.get("label", d["tipo_infraccion"])
        d["categoria"] = _inf.get("categoria", "")
        result.append(d)
    return result


def stats_por_unidad() -> list[dict]:
    """
    Performance metrics per unidad contravencional:
    total, resueltas, archivadas, pct_resolucion, dias_promedio,
    verde/amarillo/rojo counts.
    """
    with get_conn() as conn:
        rows = conn.execute("""
            SELECT unidad,
                   COUNT(*) AS total,
                   SUM(CASE WHEN estado IN ('resuelta','archivada') THEN 1 ELSE 0 END) AS cerradas,
                   SUM(CASE WHEN carril = 'verde'    THEN 1 ELSE 0 END) AS verde,
                   SUM(CASE WHEN carril = 'amarillo' THEN 1 ELSE 0 END) AS amarillo,
                   SUM(CASE WHEN carril = 'rojo'     THEN 1 ELSE 0 END) AS rojo,
                   ROUND(AVG(CASE WHEN estado IN ('resuelta','archivada')
                         THEN CAST((julianday(updated_at) - julianday(created_at)) AS REAL)
                         END), 1) AS dias_promedio
            FROM causas
            WHERE unidad IS NOT NULL AND unidad != ''
            GROUP BY unidad
            ORDER BY total DESC
        """).fetchall()
    result = []
    for r in rows:
        d = dict(r)
        tot = d["total"] or 0
        cer = d["cerradas"] or 0
        d["pct_resolucion"] = round(cer * 100 / tot) if tot else 0
        result.append(d)
    return result
