"""
Tipos de infracciones del Código de Convivencia Ciudadana de Córdoba
Ley Provincial N° 10.326 (28/03/2016) y modificatorias.

Estructura: cada infracción tiene
  - label          : descripción corta
  - categoria      : agrupación funcional para el sistema
  - articulo       : artículo del CCC
  - gravedad_base  : 1=Baja, 2=Media, 3=Alta, 4=Muy alta
  - es_conflicto_vecinal : True si es apto para derivación a mediación vecinal
  - frecuencia     : "muy_alta" | "alta" | "media" | "baja" (estadístico real MPF)
  - favorito       : True si aparece destacada por defecto en Nuevo Caso
"""

TIPOS_INFRACCION = {

    # ═══════════════════════════════════════════════════════
    # TRÁNSITO Y SEGURIDAD VIAL  (Arts. 104–114)
    # ═══════════════════════════════════════════════════════
    "transito_sin_documentacion": {
        "label": "Circular sin documentación (licencia/cédula)",
        "categoria": "Tránsito",
        "articulo": "Art. 111 CCC",
        "gravedad_base": 1,
        "es_conflicto_vecinal": False,
        "frecuencia": "muy_alta",
        "favorito": True,
    },
    "transito_sin_casco": {
        "label": "Circular sin casco o sin placa identificatoria (moto)",
        "categoria": "Tránsito",
        "articulo": "Art. 111 CCC",
        "gravedad_base": 1,
        "es_conflicto_vecinal": False,
        "frecuencia": "muy_alta",
        "favorito": True,
    },
    "transito_alcoholemia": {
        "label": "Conducción bajo efecto de alcohol / estupefacientes",
        "categoria": "Tránsito",
        "articulo": "Art. 109 CCC",
        "gravedad_base": 3,
        "es_conflicto_vecinal": False,
        "frecuencia": "alta",
        "favorito": True,
    },
    "transito_conduccion_peligrosa": {
        "label": "Conducción peligrosa (imprudente, negligente)",
        "categoria": "Tránsito",
        "articulo": "Art. 105 CCC",
        "gravedad_base": 2,
        "es_conflicto_vecinal": False,
        "frecuencia": "alta",
        "favorito": True,
    },
    "transito_carreras_via_publica": {
        "label": "Carreras / competencias no autorizadas en vía pública",
        "categoria": "Tránsito",
        "articulo": "Art. 106 CCC",
        "gravedad_base": 3,
        "es_conflicto_vecinal": False,
        "frecuencia": "baja",
        "favorito": False,
    },
    "transito_conductor_menor_edad": {
        "label": "Conductor menor de edad sin habilitación",
        "categoria": "Tránsito",
        "articulo": "Art. 104 CCC",
        "gravedad_base": 2,
        "es_conflicto_vecinal": False,
        "frecuencia": "media",
        "favorito": True,
    },
    "transito_obstruccion_senales": {
        "label": "Obstrucción de señales viales o de interés público",
        "categoria": "Tránsito",
        "articulo": "Art. 107 CCC",
        "gravedad_base": 2,
        "es_conflicto_vecinal": False,
        "frecuencia": "baja",
        "favorito": False,
    },
    "transito_omision_senalamiento": {
        "label": "Omisión de señalamiento de peligro en vía pública",
        "categoria": "Tránsito",
        "articulo": "Art. 108 CCC",
        "gravedad_base": 2,
        "es_conflicto_vecinal": False,
        "frecuencia": "baja",
        "favorito": False,
    },
    "transito_omision_documentos_carga": {
        "label": "Omisión de llevar documentación para transporte de carga",
        "categoria": "Tránsito",
        "articulo": "Art. 114 CCC",
        "gravedad_base": 1,
        "es_conflicto_vecinal": False,
        "frecuencia": "baja",
        "favorito": False,
    },

    # ═══════════════════════════════════════════════════════
    # CONVIVENCIA VECINAL  (Arts. 51–67, 80–84)
    # ═══════════════════════════════════════════════════════
    "ruidos_molestos_nocturnos": {
        "label": "Ruidos molestos en horario nocturno",
        "categoria": "Convivencia",
        "articulo": "Art. 81 CCC",
        "gravedad_base": 1,
        "es_conflicto_vecinal": True,
        "frecuencia": "muy_alta",
        "favorito": True,
    },
    "ruidos_molestos_diurnos": {
        "label": "Ruidos molestos / escándalo en horario diurno",
        "categoria": "Convivencia",
        "articulo": "Art. 81 CCC",
        "gravedad_base": 1,
        "es_conflicto_vecinal": True,
        "frecuencia": "alta",
        "favorito": True,
    },
    "riña_verbal_vecinal": {
        "label": "Escándalo / altercado verbal entre vecinos",
        "categoria": "Convivencia",
        "articulo": "Art. 80 CCC",
        "gravedad_base": 2,
        "es_conflicto_vecinal": True,
        "frecuencia": "alta",
        "favorito": True,
    },
    "molestias_personas_sitios_publicos": {
        "label": "Molestias a personas en sitios públicos (gestos, palabras ofensivas)",
        "categoria": "Convivencia",
        "articulo": "Art. 51 CCC",
        "gravedad_base": 1,
        "es_conflicto_vecinal": True,
        "frecuencia": "media",
        "favorito": False,
    },
    "hostigamiento_maltrato_intimidacion": {
        "label": "Hostigamiento, maltrato o intimidación",
        "categoria": "Convivencia",
        "articulo": "Art. 65 CCC",
        "gravedad_base": 2,
        "es_conflicto_vecinal": True,
        "frecuencia": "media",
        "favorito": True,
    },
    "agravio_personal_educacion_salud": {
        "label": "Agravio o intimidación al personal de educación o salud",
        "categoria": "Convivencia",
        "articulo": "Art. 67 CCC",
        "gravedad_base": 2,
        "es_conflicto_vecinal": False,
        "frecuencia": "baja",
        "favorito": False,
    },
    "actos_discriminatorios": {
        "label": "Actos discriminatorios (por raza, género, religión, etc.)",
        "categoria": "Convivencia",
        "articulo": "Art. 62 CCC",
        "gravedad_base": 2,
        "es_conflicto_vecinal": False,
        "frecuencia": "baja",
        "favorito": False,
    },
    "expresiones_discriminatorias": {
        "label": "Expresiones discriminatorias en vía pública",
        "categoria": "Convivencia",
        "articulo": "Art. 63 CCC",
        "gravedad_base": 2,
        "es_conflicto_vecinal": False,
        "frecuencia": "baja",
        "favorito": False,
    },
    "actos_indecencia_publica": {
        "label": "Actos contrarios a la decencia pública en vía pública",
        "categoria": "Convivencia",
        "articulo": "Art. 52 CCC",
        "gravedad_base": 1,
        "es_conflicto_vecinal": False,
        "frecuencia": "media",
        "favorito": False,
    },
    "tocamientos_indecorosos": {
        "label": "Tocamientos indecorosos en transporte o espacio público",
        "categoria": "Convivencia",
        "articulo": "Art. 53 CCC",
        "gravedad_base": 3,
        "es_conflicto_vecinal": False,
        "frecuencia": "media",
        "favorito": True,
    },
    "ebriedad_escandalosa": {
        "label": "Ebriedad o intoxicación escandalosa en vía pública",
        "categoria": "Convivencia",
        "articulo": "Art. 82 CCC",
        "gravedad_base": 1,
        "es_conflicto_vecinal": False,
        "frecuencia": "alta",
        "favorito": True,
    },
    "expendio_prohibido_bebidas": {
        "label": "Expendio de bebidas alcohólicas fuera de horario o sin habilitación",
        "categoria": "Convivencia",
        "articulo": "Art. 83 CCC",
        "gravedad_base": 2,
        "es_conflicto_vecinal": False,
        "frecuencia": "media",
        "favorito": False,
    },

    # ═══════════════════════════════════════════════════════
    # ANIMALES  (Arts. 89, 92, 93, 115–116)
    # ═══════════════════════════════════════════════════════
    "animales_sueltos": {
        "label": "Animal suelto / sin correa en espacio público",
        "categoria": "Animales",
        "articulo": "Art. 93 CCC",
        "gravedad_base": 1,
        "es_conflicto_vecinal": True,
        "frecuencia": "alta",
        "favorito": True,
    },
    "tenencia_animales_peligrosos": {
        "label": "Tenencia o circulación de animales potencialmente peligrosos",
        "categoria": "Animales",
        "articulo": "Art. 89 CCC",
        "gravedad_base": 2,
        "es_conflicto_vecinal": False,
        "frecuencia": "media",
        "favorito": True,
    },
    "animales_en_predios_ajenos": {
        "label": "Presencia de animales en predios ajenos causando daño",
        "categoria": "Animales",
        "articulo": "Art. 92 CCC",
        "gravedad_base": 1,
        "es_conflicto_vecinal": True,
        "frecuencia": "media",
        "favorito": False,
    },
    "abandono_animales": {
        "label": "Abandono de animales domésticos",
        "categoria": "Animales",
        "articulo": "Art. 93 CCC",
        "gravedad_base": 2,
        "es_conflicto_vecinal": False,
        "frecuencia": "baja",
        "favorito": False,
    },
    "faenamiento_ilegal": {
        "label": "Faenamiento y transporte ilegal de animales",
        "categoria": "Animales",
        "articulo": "Art. 115 CCC",
        "gravedad_base": 3,
        "es_conflicto_vecinal": False,
        "frecuencia": "baja",
        "favorito": False,
    },

    # ═══════════════════════════════════════════════════════
    # PROPIEDAD Y SEGURIDAD  (Arts. 68–79, 87–88, 91, 94, 99)
    # ═══════════════════════════════════════════════════════
    "daño_propiedad_publica": {
        "label": "Daño / perjuicio a la propiedad pública (grafitis, roturas)",
        "categoria": "Propiedad",
        "articulo": "Art. 68 CCC",
        "gravedad_base": 2,
        "es_conflicto_vecinal": False,
        "frecuencia": "media",
        "favorito": True,
    },
    "daño_propiedad_privada": {
        "label": "Daño / perjuicio a la propiedad privada",
        "categoria": "Propiedad",
        "articulo": "Art. 68 CCC",
        "gravedad_base": 2,
        "es_conflicto_vecinal": True,
        "frecuencia": "media",
        "favorito": True,
    },
    "interrupcion_servicios_publicos": {
        "label": "Interrupción dolosa de servicios públicos",
        "categoria": "Propiedad",
        "articulo": "Art. 68 bis CCC",
        "gravedad_base": 3,
        "es_conflicto_vecinal": False,
        "frecuencia": "baja",
        "favorito": False,
    },
    "posesion_ganzuas": {
        "label": "Posesión injustificada de llaves alteradas o ganzúas",
        "categoria": "Propiedad",
        "articulo": "Art. 69 CCC",
        "gravedad_base": 2,
        "es_conflicto_vecinal": False,
        "frecuencia": "baja",
        "favorito": False,
    },
    "conducta_sospechosa": {
        "label": "Conducta sospechosa (merodeo, manipulación de cerraduras, etc.)",
        "categoria": "Propiedad",
        "articulo": "Art. 70 CCC",
        "gravedad_base": 1,
        "es_conflicto_vecinal": False,
        "frecuencia": "media",
        "favorito": False,
    },
    "falsos_avisos_alarmas": {
        "label": "Falsos avisos, alarmas o denuncias (bomberos, policía, etc.)",
        "categoria": "Propiedad",
        "articulo": "Art. 77 CCC",
        "gravedad_base": 2,
        "es_conflicto_vecinal": False,
        "frecuencia": "baja",
        "favorito": False,
    },
    "inobservancia_seguridad": {
        "label": "Inobservancia de medidas de seguridad reglamentarias",
        "categoria": "Propiedad",
        "articulo": "Art. 87 CCC",
        "gravedad_base": 2,
        "es_conflicto_vecinal": False,
        "frecuencia": "media",
        "favorito": False,
    },
    "negativa_identificarse": {
        "label": "Negativa u omisión a identificarse / informe falso a la autoridad",
        "categoria": "Propiedad",
        "articulo": "Art. 88 CCC",
        "gravedad_base": 2,
        "es_conflicto_vecinal": False,
        "frecuencia": "media",
        "favorito": False,
    },
    "peligro_incendio": {
        "label": "Provocar peligro de incendio por imprudencia o negligencia",
        "categoria": "Propiedad",
        "articulo": "Art. 91 CCC",
        "gravedad_base": 3,
        "es_conflicto_vecinal": False,
        "frecuencia": "baja",
        "favorito": False,
    },
    "construcciones_ruinosas": {
        "label": "Construcciones o instalaciones ruinosas o peligrosas",
        "categoria": "Propiedad",
        "articulo": "Art. 94 CCC",
        "gravedad_base": 2,
        "es_conflicto_vecinal": False,
        "frecuencia": "baja",
        "favorito": False,
    },
    "incumplimiento_normas_seguridad": {
        "label": "Incumplimiento de normas de seguridad en establecimientos",
        "categoria": "Propiedad",
        "articulo": "Art. 99 CCC",
        "gravedad_base": 2,
        "es_conflicto_vecinal": False,
        "frecuencia": "media",
        "favorito": False,
    },

    # ═══════════════════════════════════════════════════════
    # COMERCIO Y ESTABLECIMIENTOS  (Arts. 58–61, 76, 79, 83)
    # ═══════════════════════════════════════════════════════
    "establecimiento_ruidos": {
        "label": "Establecimiento comercial con ruidos excesivos",
        "categoria": "Comercio",
        "articulo": "Art. 81 CCC",
        "gravedad_base": 2,
        "es_conflicto_vecinal": False,
        "frecuencia": "media",
        "favorito": True,
    },
    "establecimiento_horario": {
        "label": "Establecimiento comercial fuera de horario habilitado",
        "categoria": "Comercio",
        "articulo": "Art. 83 CCC",
        "gravedad_base": 2,
        "es_conflicto_vecinal": False,
        "frecuencia": "media",
        "favorito": True,
    },
    "venta_ambulante_sin_habilitacion": {
        "label": "Venta ambulante sin habilitación municipal",
        "categoria": "Comercio",
        "articulo": "Art. 60 CCC",
        "gravedad_base": 1,
        "es_conflicto_vecinal": False,
        "frecuencia": "media",
        "favorito": True,
    },
    "cuidado_vehiculos_sin_autorizacion": {
        "label": "Cuidado de vehículos sin autorización legal (\"trapitos\")",
        "categoria": "Comercio",
        "articulo": "Art. 60 CCC",
        "gravedad_base": 1,
        "es_conflicto_vecinal": False,
        "frecuencia": "alta",
        "favorito": True,
    },
    "ejercicio_abusivo_admision": {
        "label": "Ejercicio abusivo del derecho de admisión (discriminación en locales)",
        "categoria": "Comercio",
        "articulo": "Art. 59 CCC",
        "gravedad_base": 2,
        "es_conflicto_vecinal": False,
        "frecuencia": "baja",
        "favorito": False,
    },
    "reventa_entradas": {
        "label": "Reventa prohibida de entradas a espectáculos públicos",
        "categoria": "Comercio",
        "articulo": "Art. 79 CCC",
        "gravedad_base": 1,
        "es_conflicto_vecinal": False,
        "frecuencia": "baja",
        "favorito": False,
    },

    # ═══════════════════════════════════════════════════════
    # ESPACIO PÚBLICO  (Arts. 58–60, 72–73, 80–82, 90)
    # ═══════════════════════════════════════════════════════
    "consumo_alcohol_via_publica": {
        "label": "Consumo de alcohol en vía pública",
        "categoria": "Espacio Público",
        "articulo": "Art. 82 CCC",
        "gravedad_base": 1,
        "es_conflicto_vecinal": False,
        "frecuencia": "alta",
        "favorito": True,
    },
    "deterioro_bienes_publicos": {
        "label": "Deterioro de bienes públicos (grafitis, vandalismo)",
        "categoria": "Espacio Público",
        "articulo": "Art. 68 CCC",
        "gravedad_base": 2,
        "es_conflicto_vecinal": False,
        "frecuencia": "media",
        "favorito": True,
    },
    "quema_residuos": {
        "label": "Quema de residuos o materiales en espacio público",
        "categoria": "Espacio Público",
        "articulo": "Art. 91 CCC",
        "gravedad_base": 2,
        "es_conflicto_vecinal": False,
        "frecuencia": "media",
        "favorito": True,
    },
    "obstruccion_espacio_publico": {
        "label": "Obstrucción de espacio público (vereda, accesos)",
        "categoria": "Espacio Público",
        "articulo": "Art. 51 CCC",
        "gravedad_base": 1,
        "es_conflicto_vecinal": True,
        "frecuencia": "media",
        "favorito": False,
    },
    "daño_obras_arte_monumentos": {
        "label": "Daño a obras de arte, monumentos o patrimonio histórico",
        "categoria": "Espacio Público",
        "articulo": "Art. 72 CCC",
        "gravedad_base": 3,
        "es_conflicto_vecinal": False,
        "frecuencia": "baja",
        "favorito": False,
    },
    "organizacion_consumo_alcohol": {
        "label": "Organizar o promover competencias de consumo de alcohol",
        "categoria": "Espacio Público",
        "articulo": "Art. 84 CCC",
        "gravedad_base": 2,
        "es_conflicto_vecinal": False,
        "frecuencia": "baja",
        "favorito": False,
    },

    # ═══════════════════════════════════════════════════════
    # PIROTECNIA  (Arts. 95–100)
    # ═══════════════════════════════════════════════════════
    "pirotecnia_uso_prohibido": {
        "label": "Uso de pirotecnia prohibida en espacios públicos",
        "categoria": "Pirotecnia",
        "articulo": "Art. 96 CCC",
        "gravedad_base": 2,
        "es_conflicto_vecinal": False,
        "frecuencia": "media",
        "favorito": True,
    },
    "pirotecnia_venta_menores": {
        "label": "Venta de artículos pirotécnicos a menores de edad",
        "categoria": "Pirotecnia",
        "articulo": "Art. 97 CCC",
        "gravedad_base": 2,
        "es_conflicto_vecinal": False,
        "frecuencia": "baja",
        "favorito": False,
    },
    "pirotecnia_fabricacion_ilegal": {
        "label": "Fabricación ilegal de artículos pirotécnicos",
        "categoria": "Pirotecnia",
        "articulo": "Art. 95 CCC",
        "gravedad_base": 3,
        "es_conflicto_vecinal": False,
        "frecuencia": "baja",
        "favorito": False,
    },

    # ═══════════════════════════════════════════════════════
    # INTEGRIDAD PERSONAL  (Arts. 53, 65–67, 102–103)
    # ═══════════════════════════════════════════════════════
    "amenazas_leves": {
        "label": "Amenazas leves (sin arma)",
        "categoria": "Integridad",
        "articulo": "Art. 65 CCC",
        "gravedad_base": 3,
        "es_conflicto_vecinal": True,
        "frecuencia": "media",
        "favorito": True,
    },
    "agresion_fisica_leve": {
        "label": "Agresión física leve (sin lesiones graves)",
        "categoria": "Integridad",
        "articulo": "Art. 65 CCC",
        "gravedad_base": 4,
        "es_conflicto_vecinal": True,
        "frecuencia": "media",
        "favorito": True,
    },
    "acoso_callejero": {
        "label": "Acoso callejero / hostigamiento en espacio público",
        "categoria": "Integridad",
        "articulo": "Art. 65 CCC",
        "gravedad_base": 3,
        "es_conflicto_vecinal": False,
        "frecuencia": "media",
        "favorito": True,
    },
    "portacion_ilegal_armas": {
        "label": "Portación ilegal de armas blancas o de fuego",
        "categoria": "Integridad",
        "articulo": "Art. 102 CCC",
        "gravedad_base": 4,
        "es_conflicto_vecinal": False,
        "frecuencia": "media",
        "favorito": True,
    },
    "disparo_armas_publico": {
        "label": "Disparo de armas o encendido de fuego en sitios públicos",
        "categoria": "Integridad",
        "articulo": "Art. 103 CCC",
        "gravedad_base": 4,
        "es_conflicto_vecinal": False,
        "frecuencia": "baja",
        "favorito": False,
    },

    # ═══════════════════════════════════════════════════════
    # PROTECCIÓN DE MENORES  (Arts. 54–57, 75, 85)
    # ═══════════════════════════════════════════════════════
    "expendio_alcohol_menores": {
        "label": "Expendio o suministro de alcohol a menores de edad",
        "categoria": "Protección Menores",
        "articulo": "Art. 55 CCC",
        "gravedad_base": 2,
        "es_conflicto_vecinal": False,
        "frecuencia": "media",
        "favorito": True,
    },
    "suministro_objetos_peligrosos_menores": {
        "label": "Suministro de objetos peligrosos a menores",
        "categoria": "Protección Menores",
        "articulo": "Art. 57 CCC",
        "gravedad_base": 2,
        "es_conflicto_vecinal": False,
        "frecuencia": "baja",
        "favorito": False,
    },
    "admision_menores_espectaculos": {
        "label": "Admisión indebida de menores en espectáculos no aptos",
        "categoria": "Protección Menores",
        "articulo": "Art. 54 CCC",
        "gravedad_base": 2,
        "es_conflicto_vecinal": False,
        "frecuencia": "baja",
        "favorito": False,
    },
}

# ── Favoritos por defecto ─────────────────────────────────────────────────────
# Selección inicial para Nuevo Caso. El fiscal puede personalizar desde el Panel.
FAVORITOS_DEFAULT = [k for k, v in TIPOS_INFRACCION.items() if v.get("favorito")]

# ── Condiciones de suspensión por categoría ───────────────────────────────────
CONDICIONES_SUSPENSION = {
    "transito": [
        "No reincidir en infracciones de tránsito por el término de SEIS (6) meses",
        "Realizar el Curso de Educación Vial dictado por la Dirección de Tránsito Municipal",
        "Abonar la multa correspondiente según escala del art. 94 CCC",
    ],
    "transito_alcoholemia": [
        "Abstenerse de conducir vehículos automotores bajo efectos del alcohol por el término de UN (1) año",
        "Realizar el Curso de Conducción Responsable y Prevención del Alcohol al Volante",
        "Someterse a dos controles de alcoholemia en los próximos 6 meses ante esta Unidad",
        "Prestar CUARENTA (40) horas de trabajo comunitario en organismo a designar",
    ],
    "convivencia": [
        "No reincidir en conductas perturbadoras de la convivencia por el término de SEIS (6) meses",
        "Prestar VEINTE (20) horas de trabajo comunitario en organismo a designar por esta Fiscalía",
        "Acreditar participación en taller de resolución pacífica de conflictos",
    ],
    "comercio": [
        "Adecuar el establecimiento a los niveles de ruido permitidos por la normativa municipal dentro de los TREINTA (30) días",
        "No reincidir en infracciones similares por el término de UN (1) año",
        "Prestar TREINTA (30) horas de trabajo comunitario en organismo a designar",
    ],
    "integridad": [
        "No acercarse a menos de DOSCIENTOS (200) metros de la presunta víctima por el término de SEIS (6) meses",
        "No reincidir en conductas similares durante el período de prueba",
        "Prestar CUARENTA (40) horas de trabajo comunitario",
        "Acreditar participación en programa de manejo de conflictos del Ministerio de Justicia Provincial",
    ],
    "espacio_publico": [
        "No reincidir en conductas perturbadoras del espacio público por el término de SEIS (6) meses",
        "Prestar VEINTE (20) horas de trabajo comunitario en tareas de limpieza y mantenimiento de espacios públicos",
        "Abonar multa correspondiente a tarifa por deterioro de bienes comunes según art. 94 CCC",
    ],
}

# ── Helper: condiciones por categoría de infracción ──────────────────────────
def get_condiciones_para(tipo_infraccion: str) -> list:
    """Retorna las condiciones de suspensión apropiadas para el tipo dado."""
    v = TIPOS_INFRACCION.get(tipo_infraccion, {})
    cat = v.get("categoria", "")
    if tipo_infraccion == "transito_alcoholemia":
        return CONDICIONES_SUSPENSION["transito_alcoholemia"]
    elif cat == "Tránsito":
        return CONDICIONES_SUSPENSION["transito"]
    elif cat in ("Convivencia", "Animales", "Espacio Público", "Pirotecnia", "Comercio"):
        return CONDICIONES_SUSPENSION.get(
            {"Convivencia": "convivencia", "Comercio": "comercio",
             "Espacio Público": "espacio_publico", "Pirotecnia": "espacio_publico",
             "Animales": "convivencia"}[cat], CONDICIONES_SUSPENSION["convivencia"]
        )
    elif cat == "Integridad":
        return CONDICIONES_SUSPENSION["integridad"]
    return CONDICIONES_SUSPENSION["convivencia"]

UNIDADES = {
    "norte": "Unidad Contravencional Norte - Antonio del Viso 756, Barrio Alta Cordoba",
    "sur": "Unidad Contravencional Sur - Guzman 1075, Centro",
    "genero": "Unidad Contravencional de Violencia de Genero - Entre Rios 680",
}

CASOS_DEMO = [
    {
        "numero": "2024-UCN-00412",
        "tipo": "transito_sin_documentacion",
        "imputado": "García, Lucas Damián",
        "dni": "38.421.667",
        "edad": 24,
        "antecedentes": 0,
        "descripcion": "Circulaba en motocicleta Yamaha dominio AB 123 CD sin portar licencia de conducir ni cédula del vehículo. Control de rutina en Av. Colón 1200.",
        "unidad": "norte",
    },
    {
        "numero": "2024-UCS-00389",
        "tipo": "ruidos_molestos_nocturnos",
        "imputado": "Pérez, Marcelo Ariel",
        "dni": "30.112.445",
        "edad": 41,
        "antecedentes": 1,
        "descripcion": "Vecinos del consorcio Edificio Rivadavia denuncian música a alto volumen en departamento 4B desde las 00:30hs del sábado 15/06. Personal policial constató el hecho.",
        "unidad": "sur",
    },
    {
        "numero": "2024-UCN-00401",
        "tipo": "transito_alcoholemia",
        "imputado": "Rodríguez, Sebastián Omar",
        "dni": "33.887.021",
        "edad": 29,
        "antecedentes": 0,
        "descripcion": "Control de alcotest en av. Figueroa Alcorta. Resultado: 0.85 g/l. Sin accidente. Vehículo Ford Focus dominio AE 456 GH.",
        "unidad": "norte",
    },
    {
        "numero": "2024-UCS-00375",
        "tipo": "animales_sueltos",
        "imputado": "López, María Fernanda",
        "dni": "27.334.891",
        "edad": 55,
        "antecedentes": 0,
        "descripcion": "Denuncia vecinal por perro de raza mediana suelto en plaza Vélez Sársfield que mordió a otro animal. Propietaria identificada en el lugar.",
        "unidad": "sur",
    },
    {
        "numero": "2024-UCN-00398",
        "tipo": "riña_verbal_vecinal",
        "imputado": "Martínez, Jorge Alberto",
        "dni": "25.661.003",
        "edad": 48,
        "antecedentes": 2,
        "descripcion": "Altercado verbal con insultos y amenazas menores en galería comercial. Testigos presentes. Denunciante: comerciante del local 12.",
        "unidad": "norte",
    },
]
