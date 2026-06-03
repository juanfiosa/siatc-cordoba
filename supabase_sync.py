"""
supabase_sync.py — Puente entre SIATC (SQLite) y sumarios-rc (Supabase/PostgreSQL)
MPF Córdoba · Ley N° 10.326

Provee dos flujos:
  A) PULL — El fiscal ve en SIATC las causas que la policía elevó en sumarios-rc
             (estado 'remitido', tipo_causa 'contravencional')
  B) PUSH — Cuando SIATC clasifica o resuelve, actualiza los campos CCC en Supabase

Modo degradado: si las variables de entorno no están configuradas, todas las
funciones retornan vacío/False sin lanzar excepciones. SIATC sigue funcionando
con SQLite puro hasta que el administrador agregue las credenciales.

Configuración (Streamlit Cloud → Settings → Secrets):
  SUPABASE_URL = "https://xxxxx.supabase.co"
  SUPABASE_KEY = "eyJhbGciOiJIUzI1..."   # anon o service_role key

Uso desde app.py:
  from supabase_sync import is_configured, pull_causas_pendientes, push_clasificacion
"""
from __future__ import annotations

import os
import logging
from datetime import datetime, date
from typing import Any

logger = logging.getLogger(__name__)

# ── Configuración ──────────────────────────────────────────────────────────────

_SUPABASE_URL: str = ""
_SUPABASE_KEY: str = ""
_client: Any = None  # supabase.Client, typed as Any to avoid import at module level


def _load_env() -> tuple[str, str]:
    """Lee las credenciales desde env vars o st.secrets."""
    url = os.environ.get("SUPABASE_URL", "")
    key = os.environ.get("SUPABASE_KEY", "")
    if not (url and key):
        # Try Streamlit secrets as fallback
        try:
            import streamlit as st
            url = st.secrets.get("SUPABASE_URL", "")
            key = st.secrets.get("SUPABASE_KEY", "")
        except Exception:
            pass
    return url.strip(), key.strip()


def is_configured() -> bool:
    """True si las credenciales Supabase están disponibles."""
    url, key = _load_env()
    return bool(url and key)


def get_client():
    """Retorna el cliente Supabase. None si no está configurado."""
    global _client, _SUPABASE_URL, _SUPABASE_KEY
    url, key = _load_env()
    if not (url and key):
        return None
    # Re-use client if credentials unchanged
    if _client and url == _SUPABASE_URL and key == _SUPABASE_KEY:
        return _client
    try:
        from supabase import create_client
        _client = create_client(url, key)
        _SUPABASE_URL = url
        _SUPABASE_KEY = key
        return _client
    except Exception as e:
        logger.warning("No se pudo conectar a Supabase: %s", e)
        return None


# ── PULL: causas de sumarios-rc → SIATC ───────────────────────────────────────

def pull_causas_pendientes(dependencia_id: str | None = None,
                           limit: int = 50) -> list[dict]:
    """
    Devuelve causas contravencionales remitidas por la policía a la fiscalía,
    que aún no tienen triaje CCC (carril IS NULL).

    Retorna lista de dicts compatibles con el formato de SIATC:
      numero, caratula, apellido_nombre_imputado, dni_imputado,
      edad_imputado, domicilio_imputado, telefono_imputado,
      descripcion_hecho, fecha_hecho, lugar_hecho,
      tipo_infraccion_ccc, id (UUID de Supabase), remitido_en

    Si Supabase no está configurado retorna lista vacía.
    """
    client = get_client()
    if not client:
        return []
    try:
        q = (
            client.table("v_causas_contravencionales")
            .select("*")
            .eq("estado_policial", "remitido")
            .is_("carril", "null")   # sin triaje aún
            .order("remitido_en", desc=False)
            .limit(limit)
        )
        if dependencia_id:
            q = q.eq("dependencia_id", dependencia_id)
        resp = q.execute()
        return resp.data or []
    except Exception as e:
        logger.error("pull_causas_pendientes: %s", e)
        return []


def pull_causa_por_numero(numero: str) -> dict | None:
    """Busca una causa específica en Supabase por número de expediente."""
    client = get_client()
    if not client:
        return None
    try:
        resp = (
            client.table("v_causas_contravencionales")
            .select("*")
            .eq("numero", numero)
            .limit(1)
            .execute()
        )
        data = resp.data
        return data[0] if data else None
    except Exception as e:
        logger.error("pull_causa_por_numero(%s): %s", numero, e)
        return None


def pull_estadisticas_nodo(dependencia_id: str) -> dict:
    """
    Devuelve estadísticas del nodo desde la vista v_siatc_dashboard.
    Retorna dict vacío si Supabase no está configurado.
    """
    client = get_client()
    if not client:
        return {}
    try:
        resp = (
            client.table("v_siatc_dashboard")
            .select("*")
            .execute()
        )
        data = resp.data or []
        # Aggregate all fiscales (or filter by one)
        total = sum(r.get("total", 0) for r in data)
        return {
            "total": total,
            "verde": sum(r.get("verde", 0) for r in data),
            "amarillo": sum(r.get("amarillo", 0) for r in data),
            "rojo": sum(r.get("rojo", 0) for r in data),
            "activas": sum(r.get("activas", 0) for r in data),
            "pendientes_triaje": sum(r.get("pendientes_triaje", 0) for r in data),
        }
    except Exception as e:
        logger.error("pull_estadisticas_nodo: %s", e)
        return {}


# ── PUSH: SIATC → Supabase ────────────────────────────────────────────────────

def push_clasificacion(
    causa_supabase_id: str,
    carril: str,
    accion: str,
    score: float,
    fiscal_nombre: str,
    tipo_infraccion: str = "",
    fundamento: list[str] | None = None,
    victima: bool = False,
    lesiones: bool = False,
    resistencia: bool = False,
) -> bool:
    """
    Actualiza los campos CCC en Supabase después del triaje de SIATC.

    Args:
        causa_supabase_id: UUID de la causa en Supabase
        carril: 'verde' | 'amarillo' | 'rojo'
        accion: Texto de la acción recomendada
        score: Score numérico del clasificador (0.0-4.0)
        fiscal_nombre: Nombre del fiscal que clasificó
        tipo_infraccion: Clave del catálogo CCC
        fundamento: Lista de strings con el fundamento de la clasificación
        victima/lesiones/resistencia: Factores agravantes

    Returns:
        True si la actualización fue exitosa
    """
    client = get_client()
    if not client:
        return False
    try:
        payload = {
            "carril": carril,
            "accion_ccc": accion,
            "score_ccc": round(score, 2),
            "fiscal_nombre_ccc": fiscal_nombre,
            "updated_at": datetime.utcnow().isoformat(),
        }
        if tipo_infraccion:
            payload["tipo_infraccion_ccc"] = tipo_infraccion
        if fundamento:
            payload["fundamento_ccc"] = fundamento[:5]  # PostgreSQL text[]
        if victima:
            payload["victima_ccc"] = True
        if lesiones:
            payload["lesiones_ccc"] = True
        if resistencia:
            payload["resistencia_ccc"] = True

        client.table("causas").update(payload).eq("id", causa_supabase_id).execute()
        return True
    except Exception as e:
        logger.error("push_clasificacion(%s): %s", causa_supabase_id, e)
        return False


def push_estado_causa(
    causa_supabase_id: str,
    nuevo_estado: str,
    usuario: str = "",
    observaciones: str = "",
) -> bool:
    """
    Actualiza el estado de una causa en Supabase.

    Estados válidos (de sumarios-rc): en_tramite | consulta | archivado | girado | remitido
    Estados SIATC mapeados:
      resuelta   → archivado (causa terminada en fiscalía)
      archivada  → archivado
      en_mediacion → en_tramite (sigue activa)

    También registra en estados_causa_ccc para audit trail.
    """
    client = get_client()
    if not client:
        return False
    # Mapeo de estados SIATC → estados Supabase
    _MAPA_ESTADOS = {
        "resuelta":     "archivado",
        "archivada":    "archivado",
        "en_mediacion": "en_tramite",
        "notificada":   "en_tramite",
        "clasificada":  "en_tramite",
        "ingresada":    "en_tramite",
    }
    estado_sb = _MAPA_ESTADOS.get(nuevo_estado, "en_tramite")
    try:
        # Update estado in causas
        client.table("causas").update({
            "estado": estado_sb,
            "updated_at": datetime.utcnow().isoformat(),
        }).eq("id", causa_supabase_id).execute()

        # Insert audit record in estados_causa_ccc
        client.table("estados_causa_ccc").insert({
            "causa_id": causa_supabase_id,
            "estado_nuevo": nuevo_estado,  # keep SIATC state for detail
            "usuario": usuario,
            "observaciones": observaciones,
        }).execute()
        return True
    except Exception as e:
        logger.error("push_estado_causa(%s → %s): %s", causa_supabase_id, nuevo_estado, e)
        return False


def push_seguimiento(
    causa_supabase_id: str,
    tipo_resolucion: str,
    fecha_inicio: str,
    fecha_fin: str,
    fiscal: str,
    condiciones: list[dict] | None = None,
    observaciones: str = "",
) -> str | None:
    """
    Crea un seguimiento en Supabase con sus condiciones.

    Args:
        causa_supabase_id: UUID de la causa
        tipo_resolucion: 'suspension' | 'mediacion' | 'acuerdo'
        fecha_inicio/fin: ISO date strings ('YYYY-MM-DD')
        fiscal: Nombre del fiscal
        condiciones: lista de {tipo, descripcion, valor_objetivo, unidad, fecha_limite}
        observaciones: texto libre

    Returns:
        UUID del seguimiento creado, None si falló
    """
    client = get_client()
    if not client:
        return None
    try:
        resp = client.table("seguimientos_ccc").insert({
            "causa_id": causa_supabase_id,
            "tipo_resolucion": tipo_resolucion,
            "fecha_inicio": fecha_inicio,
            "fecha_fin": fecha_fin,
            "fiscal": fiscal,
            "observaciones": observaciones,
            "estado": "activo",
        }).execute()
        seg_data = resp.data
        if not seg_data:
            return None
        seg_id = seg_data[0]["id"]

        # Insert condiciones
        if condiciones:
            for cond in condiciones:
                client.table("condiciones_ccc").insert({
                    "seguimiento_id": seg_id,
                    "tipo": cond.get("tipo", "otro"),
                    "descripcion": cond.get("descripcion", ""),
                    "valor_objetivo": cond.get("valor_objetivo", 0),
                    "unidad": cond.get("unidad", ""),
                    "fecha_limite": cond.get("fecha_limite") or None,
                }).execute()
        return seg_id
    except Exception as e:
        logger.error("push_seguimiento(%s): %s", causa_supabase_id, e)
        return None


def push_audiencia(
    causa_supabase_id: str,
    tipo: str,
    fecha: str,
    hora: str = "09:00",
    lugar: str = "",
    observaciones: str = "",
) -> str | None:
    """Registra una audiencia CCC en Supabase. Retorna UUID o None."""
    client = get_client()
    if not client:
        return None
    try:
        resp = client.table("audiencias_ccc").insert({
            "causa_id": causa_supabase_id,
            "tipo": tipo,
            "fecha": fecha,
            "hora": hora,
            "lugar": lugar,
            "observaciones": observaciones,
            "estado": "programada",
        }).execute()
        data = resp.data
        return data[0]["id"] if data else None
    except Exception as e:
        logger.error("push_audiencia(%s): %s", causa_supabase_id, e)
        return None


def crear_causa_fiscal(
    numero: str,
    caratula: str,
    descripcion: str,
    fecha_hecho: str,
    lugar_hecho: str,
    tipo_infraccion: str,
    dependencia_id: str,
    fiscal_nombre: str,
    imputado_apellido: str,
    imputado_nombre: str,
    imputado_dni: str = "",
    imputado_edad: int | None = None,
    imputado_domicilio: str = "",
    imputado_telefono: str = "",
) -> str | None:
    """
    Crea una causa contravencional de inicio fiscal directamente en Supabase.
    Llama a la función SQL `crear_causa_contravencional()`.
    Art. 125 CCC: la acción pública puede ser promovida por la fiscalía directamente.

    Retorna el UUID de la causa creada, o None si falló.
    """
    client = get_client()
    if not client:
        return None
    try:
        resp = client.rpc("crear_causa_contravencional", {
            "p_numero": numero,
            "p_caratula": caratula,
            "p_descripcion": descripcion,
            "p_fecha_hecho": fecha_hecho,
            "p_lugar_hecho": lugar_hecho,
            "p_tipo_infraccion": tipo_infraccion,
            "p_dependencia_id": dependencia_id,
            "p_fiscal_nombre": fiscal_nombre,
            "p_imputado_apellido": imputado_apellido,
            "p_imputado_nombre": imputado_nombre,
            "p_imputado_dni": imputado_dni or None,
            "p_imputado_edad": imputado_edad,
            "p_imputado_domicilio": imputado_domicilio or None,
            "p_imputado_telefono": imputado_telefono or None,
        }).execute()
        # RPC returns the UUID directly
        return str(resp.data) if resp.data else None
    except Exception as e:
        logger.error("crear_causa_fiscal: %s", e)
        return None


# ── Helpers para la UI ─────────────────────────────────────────────────────────

def causa_supabase_a_siatc(raw: dict) -> dict:
    """
    Convierte un dict de v_causas_contravencionales al formato que espera app.py.
    Permite mostrar causas de sumarios-rc en la UI de SIATC sin duplicar en SQLite.
    """
    nombre = raw.get("apellido_nombre_imputado", "Imputado desconocido")
    return {
        # Identificadores
        "id": f"SB:{raw['id']}",   # prefijo para distinguir de SQLite IDs
        "supabase_id": raw["id"],
        "numero": raw.get("numero", ""),
        # Imputado
        "apellido_nombre": nombre,
        "persona_dni": raw.get("dni_imputado", ""),
        "persona_edad": raw.get("edad_imputado"),
        "persona_domicilio": raw.get("domicilio_imputado", ""),
        "persona_telefono": raw.get("telefono_imputado", ""),
        # Causa
        "tipo_infraccion": raw.get("tipo_infraccion_ccc", ""),
        "descripcion": raw.get("descripcion_hecho", ""),
        "fecha_hecho": raw.get("fecha_hecho", ""),
        "unidad": raw.get("oficina_actual_ccc", "fiscalia"),
        "carril": raw.get("carril"),
        "accion": raw.get("accion_ccc"),
        "score_clasificacion": raw.get("score_ccc"),
        "fiscal_asignado": raw.get("fiscal_nombre_ccc", ""),
        "estado": "ingresada",  # En SIATC siempre empieza en ingresada
        "created_at": raw.get("remitido_en") or raw.get("created_at", ""),
        "updated_at": raw.get("updated_at", ""),
        # Fuente
        "_fuente": "supabase",
        "_estado_policial": raw.get("estado_policial", "remitido"),
    }


def render_banner_supabase(st_module) -> None:
    """
    Muestra un banner informativo en la UI cuando Supabase está configurado.
    Llamar desde app.py al inicio de cada sección si se quiere mostrar el estado.
    """
    st = st_module
    if is_configured():
        st.success(
            "🔗 **Integración sumarios-rc activa** — "
            "Las causas remitidas por la policía aparecen en la Bandeja RC.",
            icon="✅"
        )
    else:
        st.info(
            "ℹ️ La integración con **sumarios-rc** no está configurada. "
            "SIATC funciona en modo local (SQLite). "
            "Para activar la integración, configurá `SUPABASE_URL` y `SUPABASE_KEY` "
            "en los secretos de Streamlit Cloud.",
            icon="🔗"
        )
