"""
Motor de clasificación de casos contravencionales.
Asigna carril Verde / Amarillo / Rojo y genera justificación.
"""

from data_cordoba import TIPOS_INFRACCION


def clasificar_caso(tipo_infraccion: str, antecedentes: int, victima_identificada: bool,
                    hay_lesiones: bool = False, resistencia_autoridad: bool = False) -> dict:
    """
    Retorna un dict con:
      - carril: "verde" | "amarillo" | "rojo"
      - color: código hex para UI
      - icono: emoji
      - accion: texto de acción recomendada
      - fundamento: lista de razones
      - score: puntaje interno (debug)
    """
    infraccion = TIPOS_INFRACCION.get(tipo_infraccion, {})
    gravedad_base = infraccion.get("gravedad_base", 2)
    es_conflicto_vecinal = infraccion.get("es_conflicto_vecinal", False)
    categoria = infraccion.get("categoria", "")

    score = gravedad_base
    fundamento = []

    # Modificadores por antecedentes
    if antecedentes == 0:
        fundamento.append("Sin antecedentes contravencionales previos")
        score -= 1
    elif antecedentes == 1:
        fundamento.append("Un antecedente contravencional previo")
    elif antecedentes >= 2:
        fundamento.append(f"{antecedentes} antecedentes contravencionales — reincidencia comprobada")
        score += 2

    # Modificadores por víctima
    if victima_identificada and not es_conflicto_vecinal:
        fundamento.append("Víctima directa identificada")
        score += 1
    elif es_conflicto_vecinal:
        fundamento.append("Conflicto de convivencia vecinal — apto para mediación")
        score -= 0.5

    # Modificadores por circunstancias agravantes
    if hay_lesiones:
        fundamento.append("Se registraron lesiones físicas")
        score += 2

    if resistencia_autoridad:
        fundamento.append("Resistencia o desobediencia a la autoridad policial")
        score += 2

    # Caso especial: alcoholemia
    if tipo_infraccion == "transito_alcoholemia" and antecedentes == 0:
        fundamento.append("Primera infracción por alcoholemia — elegible para suspensión con condiciones")

    # Clasificación final
    if score <= 1.5:
        carril = "verde"
        accion = "Derivar a Centro Judicial de Mediación"
        descripcion = "El caso reúne condiciones para resolución no punitiva. Se generará citación a mediación."
        color = "#2ECC71"
        icono = "🟢"
    elif score <= 3:
        carril = "amarillo"
        accion = "Suspensión del Proceso a Prueba"
        descripcion = "Procede el dictamen de suspensión del juicio a prueba con condiciones. Revisión fiscal requerida."
        color = "#F39C12"
        icono = "🟡"
    else:
        carril = "rojo"
        accion = "Proceso Contravencional Completo"
        descripcion = "El caso requiere intervención fiscal directa. No aplica vía abreviada."
        color = "#E74C3C"
        icono = "🔴"

    return {
        "carril": carril,
        "color": color,
        "icono": icono,
        "accion": accion,
        "descripcion": descripcion,
        "fundamento": fundamento,
        "score": score,
        "categoria": categoria,
    }


def tiempo_estimado_resolucion(carril: str) -> dict:
    """Estimación de tiempos según carril, basada en datos de Prometea CABA."""
    tiempos = {
        "verde": {
            "actual_dias": 45,
            "con_sistema_dias": 5,
            "descripcion": "Citación a mediación en 48hs. Resultado en ~5 días.",
        },
        "amarillo": {
            "actual_dias": 60,
            "con_sistema_dias": 3,
            "descripcion": "Dictamen generado al momento. Firma fiscal = resolución.",
        },
        "rojo": {
            "actual_dias": 90,
            "con_sistema_dias": 7,
            "descripcion": "Requiere investigación. Sistema acelera preparación del expediente.",
        },
    }
    return tiempos.get(carril, tiempos["rojo"])
