"""
Asistente de IA para SIATC — analiza partes policiales con Claude.
"""
import os
import json
from typing import Optional

from data_cordoba import TIPOS_INFRACCION

try:
    from anthropic import Anthropic
    _AVAILABLE = True
except ImportError:
    _AVAILABLE = False

_PROMPT = """Sos un asistente del Ministerio Público Fiscal de la Provincia de Córdoba, Argentina.
Tu tarea es extraer información estructurada de un parte policial para el sistema SIATC de causas contravencionales.

Tipos de infracción disponibles (elegí EXACTAMENTE uno de estos códigos, o null si no aplica):
{tipos}

Parte policial a analizar:
---
{texto}
---

Respondé ÚNICAMENTE con un objeto JSON válido (sin markdown, sin explicaciones):
{{
  "imputado": "APELLIDO, Nombre (en ese formato, o vacío si no se identifica)",
  "dni": "número de DNI sin puntos ni guiones, o vacío si no se menciona",
  "edad": número entero o null,
  "tipo_infraccion": "código exacto de la lista o null",
  "descripcion": "descripción concisa del hecho en 2-3 oraciones en tercera persona",
  "victima": true o false,
  "lesiones": true o false,
  "resistencia": true o false,
  "antecedentes_mencionados": número entero si se mencionan explícitamente, o 0
}}"""


def disponible() -> bool:
    return _AVAILABLE


def analizar_parte(texto: str, api_key: Optional[str] = None) -> dict:
    """
    Usa Claude para extraer datos estructurados de un parte policial.
    Lanza RuntimeError si anthropic no está instalado, ValueError si falta la API key.
    """
    if not _AVAILABLE:
        raise RuntimeError("Instalá el paquete 'anthropic': pip install anthropic")

    key = api_key or os.environ.get("ANTHROPIC_API_KEY", "")
    if not key:
        raise ValueError("Se requiere ANTHROPIC_API_KEY")

    tipos_str = "\n".join(
        f"  - {k}: {v['label']} ({v['categoria']})"
        for k, v in TIPOS_INFRACCION.items()
    )

    client = Anthropic(api_key=key)
    resp = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=600,
        messages=[{"role": "user", "content": _PROMPT.format(tipos=tipos_str, texto=texto)}],
    )

    raw = resp.content[0].text.strip()
    # Eliminar fences de markdown si los hay
    if raw.startswith("```"):
        parts = raw.split("```")
        raw = parts[1]
        if raw.startswith("json"):
            raw = raw[4:]

    data = json.loads(raw)

    # Validar que tipo_infraccion sea un código conocido
    if data.get("tipo_infraccion") and data["tipo_infraccion"] not in TIPOS_INFRACCION:
        data["tipo_infraccion"] = None

    return data
