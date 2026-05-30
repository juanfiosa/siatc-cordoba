"""
Tipos de infracciones del Código de Convivencia Ciudadana de Córdoba
Ley Provincial N° 10.326 (28/03/2016) y modificatorias.

ESTRUCTURA DEL LIBRO II (Infracciones):
  Título I   — Convivencia Ciudadana, Menores, Discriminación y Hostigamiento (Arts 51-66)
  Título II  — Protección del Personal de Educación y Salud (Art 67)
  Título III — Propiedad Pública y Privada / Seguridad (Arts 68-73)
  Título IV  — Orden Económico, Alarmas y Comunicaciones (Arts 74-79)
  Título V   — Desórdenes Públicos, Alcohol y Protección de Niñez (Arts 80-85)
  Título VI  — Seguridad Pública, Animales y Pirotecnia (Arts 86-103)
  Título VII — Tránsito y Seguridad Vial (Arts 104-111)
  Título VIII— Registros, Transporte y Comercio de Animales (Arts 112-118)

Cada infracción contiene:
  - label          : descripción breve
  - titulo_ccc     : Título del Libro II al que pertenece (para el acordeón)
  - capitulo_ccc   : Capítulo dentro del Título
  - articulo       : artículo(s) del CCC
  - gravedad_base  : 1=Baja, 2=Media, 3=Alta, 4=Muy alta
  - es_conflicto_vecinal: apto para mediación vecinal
  - frecuencia     : "muy_alta" | "alta" | "media" | "baja"
  - favorito       : True = destacada por defecto en Nuevo Caso
"""

# ── Etiquetas de los Títulos (acordeón) ──────────────────────────────────────
TITULOS_CCC = {
    "I":   "Título I — Convivencia Ciudadana, Menores, Discriminación y Hostigamiento",
    "II":  "Título II — Protección del Personal de Educación y Salud",
    "III": "Título III — Propiedad Pública y Privada",
    "IV":  "Título IV — Orden Económico, Alarmas y Comunicaciones",
    "V":   "Título V — Desórdenes Públicos, Alcohol y Protección de la Niñez",
    "VI":  "Título VI — Seguridad Pública, Animales y Pirotecnia",
    "VII": "Título VII — Tránsito y Seguridad Vial",
    "VIII":"Título VIII — Registros, Transporte y Comercio de Animales",
}

TIPOS_INFRACCION = {

    # ═══════════════════════════════════════════════════════════════════════
    # TÍTULO I — Arts 51-66
    # Capítulo I: Molestias en la vía pública (Arts 51-53)
    # ═══════════════════════════════════════════════════════════════════════
    "molestias_sitios_publicos": {
        "label": "Molestias a personas en sitios públicos (gestos, palabras, gratificaciones)",
        "titulo_ccc": "I", "categoria": "Integridad", "categoria": "Convivencia", "categoria": "Convivencia", "categoria": "Comercio", "categoria": "Comercio", "categoria": "Comercio", "categoria": "Comercio", "categoria": "Convivencia", "categoria": "Convivencia", "categoria": "Convivencia", "categoria": "Convivencia", "categoria": "Integridad", "categoria": "Convivencia", "categoria": "Convivencia", "capitulo_ccc": "I",
        "articulo": "Art. 51 CCC",
        "gravedad_base": 1, "es_conflicto_vecinal": True,
        "frecuencia": "media", "favorito": False,
    },
    "actos_indecencia_publica": {
        "label": "Actos contrarios a la decencia pública en vía pública",
        "titulo_ccc": "I", "capitulo_ccc": "I",
        "articulo": "Art. 52 CCC",
        "gravedad_base": 1, "es_conflicto_vecinal": False,
        "frecuencia": "media", "favorito": False,
    },
    "tocamientos_indecorosos": {
        "label": "Tocamientos indecorosos en transporte o espacio público",
        "titulo_ccc": "I", "capitulo_ccc": "I",
        "articulo": "Art. 53 CCC",
        "gravedad_base": 3, "es_conflicto_vecinal": False,
        "frecuencia": "media", "favorito": True,
    },

    # Capítulo II: Menores (Arts 54-57)
    "admision_menores_espectaculos": {
        "label": "Admisión indebida de menores en espectáculos no aptos",
        "titulo_ccc": "I", "capitulo_ccc": "II",
        "articulo": "Art. 54 CCC",
        "gravedad_base": 2, "es_conflicto_vecinal": False,
        "frecuencia": "baja", "favorito": False,
    },
    "expendio_alcohol_menores": {
        "label": "Expendio o consumo de alcohol a menores de edad",
        "titulo_ccc": "I", "capitulo_ccc": "II",
        "articulo": "Art. 55 CCC",
        "gravedad_base": 2, "es_conflicto_vecinal": False,
        "frecuencia": "media", "favorito": True,
    },
    "vehiculo_ninos_interior": {
        "label": "Vehículo con niños en su interior sin adulto responsable",
        "titulo_ccc": "I", "capitulo_ccc": "II",
        "articulo": "Art. 56 CCC",
        "gravedad_base": 2, "es_conflicto_vecinal": False,
        "frecuencia": "baja", "favorito": False,
    },
    "suministro_objetos_peligrosos_menores": {
        "label": "Suministro de objetos peligrosos a menores",
        "titulo_ccc": "I", "capitulo_ccc": "II",
        "articulo": "Art. 57 CCC",
        "gravedad_base": 2, "es_conflicto_vecinal": False,
        "frecuencia": "baja", "favorito": False,
    },

    # Capítulo III: Derecho de admisión (Arts 58-60)
    "derecho_admision": {
        "label": "Discriminación en el derecho de admisión a locales",
        "titulo_ccc": "I", "capitulo_ccc": "III",
        "articulo": "Art. 58 CCC",
        "gravedad_base": 2, "es_conflicto_vecinal": False,
        "frecuencia": "baja", "favorito": False,
    },
    "ejercicio_abusivo_admision": {
        "label": "Ejercicio abusivo del derecho de admisión (discriminación en locales)",
        "titulo_ccc": "I", "capitulo_ccc": "III",
        "articulo": "Art. 59 CCC",
        "gravedad_base": 2, "es_conflicto_vecinal": False,
        "frecuencia": "baja", "favorito": False,
    },
    "cuidado_vehiculos_sin_autorizacion": {
        "label": "Cuidado de vehículos sin autorización legal (\"trapitos\")",
        "titulo_ccc": "I", "capitulo_ccc": "III",
        "articulo": "Art. 60 CCC",
        "gravedad_base": 1, "es_conflicto_vecinal": False,
        "frecuencia": "alta", "favorito": True,
    },

    # Capítulo IV: Wiskerías (Art 61)
    "whiskerias_cabarets": {
        "label": "Violación a la prohibición de whiskerías, cabarets, clubes nocturnos",
        "titulo_ccc": "I", "capitulo_ccc": "IV",
        "articulo": "Art. 61 CCC",
        "gravedad_base": 2, "es_conflicto_vecinal": False,
        "frecuencia": "baja", "favorito": False,
    },

    # Capítulo V: Discriminación (Arts 62-64)
    "actos_discriminatorios": {
        "label": "Actos discriminatorios (por raza, género, religión, etc.)",
        "titulo_ccc": "I", "capitulo_ccc": "V",
        "articulo": "Art. 62 CCC",
        "gravedad_base": 2, "es_conflicto_vecinal": False,
        "frecuencia": "baja", "favorito": False,
    },
    "expresiones_discriminatorias": {
        "label": "Expresiones discriminatorias en vía pública",
        "titulo_ccc": "I", "capitulo_ccc": "V",
        "articulo": "Art. 63 CCC",
        "gravedad_base": 2, "es_conflicto_vecinal": False,
        "frecuencia": "baja", "favorito": False,
    },

    # Capítulo VI: Hostigamiento (Arts 65-66)
    "hostigamiento_maltrato_intimidacion": {
        "label": "Hostigamiento, maltrato o intimidación",
        "titulo_ccc": "I", "capitulo_ccc": "VI",
        "articulo": "Art. 65 CCC",
        "gravedad_base": 2, "es_conflicto_vecinal": True,
        "frecuencia": "media", "favorito": True,
    },

    # ═══════════════════════════════════════════════════════════════════════
    # TÍTULO II — Art 67
    # ═══════════════════════════════════════════════════════════════════════
    "agravio_personal_educacion_salud": {
        "label": "Agravio o intimidación al personal de centros educativos o de salud",
        "titulo_ccc": "II", "categoria": "Convivencia", "capitulo_ccc": "Único",
        "articulo": "Art. 67 CCC",
        "gravedad_base": 2, "es_conflicto_vecinal": False,
        "frecuencia": "baja", "favorito": False,
    },

    # ═══════════════════════════════════════════════════════════════════════
    # TÍTULO III — Arts 68-73
    # Capítulo I: Propiedad (Arts 68-71)
    # ═══════════════════════════════════════════════════════════════════════
    "daño_propiedad_publica": {
        "label": "Daño a la propiedad pública (grafitis, roturas, vandalismo)",
        "titulo_ccc": "III", "categoria": "Espacio Publico", "categoria": "Espacio Publico", "categoria": "Propiedad", "categoria": "Propiedad", "categoria": "Propiedad", "categoria": "Propiedad", "categoria": "Propiedad", "categoria": "Propiedad", "capitulo_ccc": "I",
        "articulo": "Art. 68 CCC",
        "gravedad_base": 2, "es_conflicto_vecinal": False,
        "frecuencia": "media", "favorito": True,
    },
    "daño_propiedad_privada": {
        "label": "Daño a la propiedad privada",
        "titulo_ccc": "III", "capitulo_ccc": "I",
        "articulo": "Art. 68 CCC",
        "gravedad_base": 2, "es_conflicto_vecinal": True,
        "frecuencia": "media", "favorito": True,
    },
    "interrupcion_servicios_publicos": {
        "label": "Interrupción dolosa de servicios públicos",
        "titulo_ccc": "III", "capitulo_ccc": "I",
        "articulo": "Art. 68 bis CCC",
        "gravedad_base": 3, "es_conflicto_vecinal": False,
        "frecuencia": "baja", "favorito": False,
    },
    "posesion_ganzuas": {
        "label": "Posesión injustificada de llaves alteradas o ganzúas",
        "titulo_ccc": "III", "capitulo_ccc": "I",
        "articulo": "Art. 69 CCC",
        "gravedad_base": 2, "es_conflicto_vecinal": False,
        "frecuencia": "baja", "favorito": False,
    },
    "conducta_sospechosa": {
        "label": "Conducta sospechosa (merodeo, manipulación de cerraduras)",
        "titulo_ccc": "III", "capitulo_ccc": "I",
        "articulo": "Art. 70 CCC",
        "gravedad_base": 1, "es_conflicto_vecinal": False,
        "frecuencia": "media", "favorito": False,
    },
    "merodeo_zona_rural": {
        "label": "Merodeo en zona rural sin justificación",
        "titulo_ccc": "III", "capitulo_ccc": "I",
        "articulo": "Art. 71 CCC",
        "gravedad_base": 1, "es_conflicto_vecinal": False,
        "frecuencia": "baja", "favorito": False,
    },

    # Capítulo II: Monumentos y arqueología (Arts 72-73)
    "daño_monumentos_historicos": {
        "label": "Daño a obras de arte, monumentos o patrimonio histórico",
        "titulo_ccc": "III", "capitulo_ccc": "II",
        "articulo": "Art. 72 CCC",
        "gravedad_base": 3, "es_conflicto_vecinal": False,
        "frecuencia": "baja", "favorito": False,
    },
    "daño_bienes_arqueologicos": {
        "label": "Daño a bienes con valor arqueológico",
        "titulo_ccc": "III", "capitulo_ccc": "II",
        "articulo": "Art. 73 CCC",
        "gravedad_base": 3, "es_conflicto_vecinal": False,
        "frecuencia": "baja", "favorito": False,
    },

    # ═══════════════════════════════════════════════════════════════════════
    # TÍTULO IV — Arts 74-79
    # ═══════════════════════════════════════════════════════════════════════
    "falsa_apariencia": {
        "label": "Falsa apariencia para obtener beneficios indebidos",
        "titulo_ccc": "IV", "categoria": "Comercio", "categoria": "Propiedad", "categoria": "Propiedad", "categoria": "Comercio", "categoria": "Convivencia", "categoria": "Propiedad", "capitulo_ccc": "I",
        "articulo": "Art. 74 CCC",
        "gravedad_base": 2, "es_conflicto_vecinal": False,
        "frecuencia": "baja", "favorito": False,
    },
    "exposicion_menores_incapaces": {
        "label": "Exposición de menores o incapaces a situación de riesgo",
        "titulo_ccc": "IV", "capitulo_ccc": "II",
        "articulo": "Art. 75 CCC",
        "gravedad_base": 3, "es_conflicto_vecinal": False,
        "frecuencia": "baja", "favorito": False,
    },
    "irregularidades_subasta": {
        "label": "Irregularidades en subasta pública",
        "titulo_ccc": "IV", "capitulo_ccc": "III",
        "articulo": "Art. 76 CCC",
        "gravedad_base": 2, "es_conflicto_vecinal": False,
        "frecuencia": "baja", "favorito": False,
    },
    "falsos_avisos_alarmas": {
        "label": "Falsos avisos, alarmas o denuncias (bomberos, policía, emergencias)",
        "titulo_ccc": "IV", "capitulo_ccc": "IV",
        "articulo": "Art. 77 CCC",
        "gravedad_base": 2, "es_conflicto_vecinal": False,
        "frecuencia": "baja", "favorito": False,
    },
    "uso_indebido_telefonos": {
        "label": "Uso indebido de teléfonos (llamadas falsas o molestas)",
        "titulo_ccc": "IV", "capitulo_ccc": "IV",
        "articulo": "Art. 78 CCC",
        "gravedad_base": 1, "es_conflicto_vecinal": False,
        "frecuencia": "baja", "favorito": False,
    },
    "reventa_entradas": {
        "label": "Reventa prohibida de entradas a espectáculos públicos",
        "titulo_ccc": "IV", "capitulo_ccc": "V",
        "articulo": "Art. 79 CCC",
        "gravedad_base": 1, "es_conflicto_vecinal": False,
        "frecuencia": "baja", "favorito": False,
    },

    # ═══════════════════════════════════════════════════════════════════════
    # TÍTULO V — Arts 80-85
    # Capítulo I: Desórdenes (Arts 80-81)
    # ═══════════════════════════════════════════════════════════════════════
    "riña_desordenes_publicos": {
        "label": "Desórdenes públicos — riña o pelea en vía pública",
        "titulo_ccc": "V", "categoria": "Convivencia", "categoria": "Convivencia", "categoria": "Comercio", "categoria": "Convivencia", "categoria": "Convivencia", "categoria": "Convivencia", "categoria": "Convivencia", "capitulo_ccc": "I",
        "articulo": "Art. 80 CCC",
        "gravedad_base": 2, "es_conflicto_vecinal": True,
        "frecuencia": "alta", "favorito": True,
    },
    "ruidos_molestos_nocturnos": {
        "label": "Escándalos o ruidos molestos en horario nocturno",
        "titulo_ccc": "V", "capitulo_ccc": "I",
        "articulo": "Art. 81 CCC",
        "gravedad_base": 1, "es_conflicto_vecinal": True,
        "frecuencia": "muy_alta", "favorito": True,
    },
    "ruidos_molestos_diurnos": {
        "label": "Escándalos o ruidos molestos en horario diurno",
        "titulo_ccc": "V", "capitulo_ccc": "I",
        "articulo": "Art. 81 CCC",
        "gravedad_base": 1, "es_conflicto_vecinal": True,
        "frecuencia": "alta", "favorito": True,
    },

    # Capítulo II: Alcohol y protección NNyA (Arts 82-85)
    "ebriedad_escandalosa": {
        "label": "Ebriedad o intoxicación escandalosa en vía pública",
        "titulo_ccc": "V", "capitulo_ccc": "II",
        "articulo": "Art. 82 CCC",
        "gravedad_base": 1, "es_conflicto_vecinal": False,
        "frecuencia": "alta", "favorito": True,
    },
    "expendio_prohibido_bebidas": {
        "label": "Expendio de bebidas alcohólicas fuera de horario o sin habilitación",
        "titulo_ccc": "V", "capitulo_ccc": "II",
        "articulo": "Art. 83 CCC",
        "gravedad_base": 2, "es_conflicto_vecinal": False,
        "frecuencia": "media", "favorito": True,
    },
    "competencias_consumo_alcohol": {
        "label": "Organizar o promover competencias de consumo de alcohol",
        "titulo_ccc": "V", "capitulo_ccc": "II",
        "articulo": "Art. 84 CCC",
        "gravedad_base": 2, "es_conflicto_vecinal": False,
        "frecuencia": "baja", "favorito": False,
    },
    "proteccion_nnya_alcohol": {
        "label": "Permisión o tolerancia de consumo de alcohol en menores",
        "titulo_ccc": "V", "capitulo_ccc": "II",
        "articulo": "Art. 85 CCC",
        "gravedad_base": 2, "es_conflicto_vecinal": False,
        "frecuencia": "baja", "favorito": False,
    },

    # ═══════════════════════════════════════════════════════════════════════
    # TÍTULO VI — Arts 86-103
    # Capítulo I: Seguridad pública y animales (Arts 86-94)
    # ═══════════════════════════════════════════════════════════════════════
    "falsa_denuncia_contravencion": {
        "label": "Falsa denuncia contravencional",
        "titulo_ccc": "VI", "categoria": "Integridad", "categoria": "Integridad", "categoria": "Propiedad", "categoria": "Pirotecnia", "categoria": "Pirotecnia", "categoria": "Pirotecnia", "categoria": "Pirotecnia", "categoria": "Propiedad", "categoria": "Animales", "categoria": "Animales", "categoria": "Propiedad", "categoria": "Espacio Publico", "categoria": "Animales", "categoria": "Propiedad", "categoria": "Propiedad", "categoria": "Propiedad", "capitulo_ccc": "I",
        "articulo": "Art. 86 CCC",
        "gravedad_base": 2, "es_conflicto_vecinal": False,
        "frecuencia": "baja", "favorito": False,
    },
    "inobservancia_seguridad": {
        "label": "Inobservancia de medidas de seguridad reglamentarias",
        "titulo_ccc": "VI", "capitulo_ccc": "I",
        "articulo": "Art. 87 CCC",
        "gravedad_base": 2, "es_conflicto_vecinal": False,
        "frecuencia": "media", "favorito": False,
    },
    "negativa_identificarse": {
        "label": "Negativa u omisión a identificarse / informe falso a la autoridad",
        "titulo_ccc": "VI", "capitulo_ccc": "I",
        "articulo": "Art. 88 CCC",
        "gravedad_base": 2, "es_conflicto_vecinal": False,
        "frecuencia": "media", "favorito": False,
    },
    "tenencia_animales_peligrosos": {
        "label": "Tenencia o circulación de animales potencialmente peligrosos",
        "titulo_ccc": "VI", "capitulo_ccc": "I",
        "articulo": "Art. 89 CCC",
        "gravedad_base": 2, "es_conflicto_vecinal": False,
        "frecuencia": "media", "favorito": True,
    },
    "juegos_fiestas_populares": {
        "label": "Juegos peligrosos en ocasión de fiestas populares o religiosas",
        "titulo_ccc": "VI", "capitulo_ccc": "I",
        "articulo": "Art. 90 CCC",
        "gravedad_base": 1, "es_conflicto_vecinal": False,
        "frecuencia": "baja", "favorito": False,
    },
    "peligro_incendio": {
        "label": "Provocar peligro de incendio por imprudencia o negligencia",
        "titulo_ccc": "VI", "capitulo_ccc": "I",
        "articulo": "Art. 91 CCC",
        "gravedad_base": 3, "es_conflicto_vecinal": False,
        "frecuencia": "baja", "favorito": False,
    },
    "animales_en_predios_ajenos": {
        "label": "Presencia de animales en predios ajenos causando daño",
        "titulo_ccc": "VI", "capitulo_ccc": "I",
        "articulo": "Art. 92 CCC",
        "gravedad_base": 1, "es_conflicto_vecinal": True,
        "frecuencia": "media", "favorito": False,
    },
    "animales_sueltos": {
        "label": "Deambulación de animales sueltos / sin correa en espacio público",
        "titulo_ccc": "VI", "capitulo_ccc": "I",
        "articulo": "Art. 93 CCC",
        "gravedad_base": 1, "es_conflicto_vecinal": True,
        "frecuencia": "alta", "favorito": True,
    },
    "construcciones_ruinosas": {
        "label": "Construcciones o instalaciones ruinosas o peligrosas",
        "titulo_ccc": "VI", "capitulo_ccc": "I",
        "articulo": "Art. 94 CCC",
        "gravedad_base": 2, "es_conflicto_vecinal": False,
        "frecuencia": "baja", "favorito": False,
    },

    # Capítulo II: Pirotecnia (Arts 95-101)
    "pirotecnia_fabricacion": {
        "label": "Fabricación ilegal de artículos pirotécnicos",
        "titulo_ccc": "VI", "capitulo_ccc": "II",
        "articulo": "Art. 95 CCC",
        "gravedad_base": 3, "es_conflicto_vecinal": False,
        "frecuencia": "baja", "favorito": False,
    },
    "pirotecnia_uso_prohibido": {
        "label": "Uso de pirotecnia prohibida en espacios públicos",
        "titulo_ccc": "VI", "capitulo_ccc": "II",
        "articulo": "Art. 96 CCC",
        "gravedad_base": 2, "es_conflicto_vecinal": False,
        "frecuencia": "media", "favorito": True,
    },
    "pirotecnia_venta_menores": {
        "label": "Venta de artículos pirotécnicos a menores de edad",
        "titulo_ccc": "VI", "capitulo_ccc": "II",
        "articulo": "Art. 97 CCC",
        "gravedad_base": 2, "es_conflicto_vecinal": False,
        "frecuencia": "baja", "favorito": False,
    },
    "pirotecnia_espectaculos": {
        "label": "Uso de pirotecnia en espectáculos públicos (prohibición)",
        "titulo_ccc": "VI", "capitulo_ccc": "II",
        "articulo": "Art. 98 CCC",
        "gravedad_base": 2, "es_conflicto_vecinal": False,
        "frecuencia": "baja", "favorito": False,
    },
    "incumplimiento_normas_seguridad": {
        "label": "Incumplimiento de normas de seguridad en establecimientos",
        "titulo_ccc": "VI", "capitulo_ccc": "II",
        "articulo": "Art. 99 CCC",
        "gravedad_base": 2, "es_conflicto_vecinal": False,
        "frecuencia": "media", "favorito": False,
    },

    # Capítulo III: Armas (Arts 102-103)
    "portacion_ilegal_armas": {
        "label": "Portación ilegal de armas blancas o de fuego",
        "titulo_ccc": "VI", "capitulo_ccc": "III",
        "articulo": "Art. 102 CCC",
        "gravedad_base": 4, "es_conflicto_vecinal": False,
        "frecuencia": "media", "favorito": True,
    },
    "disparo_armas_publico": {
        "label": "Disparo de armas o encendido de fuego en sitios públicos",
        "titulo_ccc": "VI", "capitulo_ccc": "III",
        "articulo": "Art. 103 CCC",
        "gravedad_base": 4, "es_conflicto_vecinal": False,
        "frecuencia": "baja", "favorito": False,
    },

    # ═══════════════════════════════════════════════════════════════════════
    # TÍTULO VII — Arts 104-111 (Tránsito)
    # Capítulo Único
    # ═══════════════════════════════════════════════════════════════════════
    "transito_conductor_menor_edad": {
        "label": "Conductor menor de edad sin habilitación",
        "titulo_ccc": "VII", "categoria": "Transito", "categoria": "Transito", "categoria": "Transito", "categoria": "Transito", "categoria": "Transito", "categoria": "Transito", "categoria": "Transito", "capitulo_ccc": "Único",
        "articulo": "Art. 104 CCC",
        "gravedad_base": 2, "es_conflicto_vecinal": False,
        "frecuencia": "media", "favorito": True,
    },
    "transito_conduccion_peligrosa": {
        "label": "Conducción peligrosa (imprudente, negligente o antirreglamentaria)",
        "titulo_ccc": "VII", "capitulo_ccc": "Único",
        "articulo": "Art. 105 CCC",
        "gravedad_base": 2, "es_conflicto_vecinal": False,
        "frecuencia": "alta", "favorito": True,
    },
    "transito_carreras_via_publica": {
        "label": "Carreras o competencias no autorizadas en vía pública",
        "titulo_ccc": "VII", "capitulo_ccc": "Único",
        "articulo": "Art. 106 CCC",
        "gravedad_base": 3, "es_conflicto_vecinal": False,
        "frecuencia": "baja", "favorito": False,
    },
    "transito_obstruccion_senales": {
        "label": "Obstrucción de señales viales o de interés público",
        "titulo_ccc": "VII", "capitulo_ccc": "Único",
        "articulo": "Art. 107 CCC",
        "gravedad_base": 2, "es_conflicto_vecinal": False,
        "frecuencia": "baja", "favorito": False,
    },
    "transito_omision_senalamiento": {
        "label": "Omisión de señalamiento de peligro en vía pública",
        "titulo_ccc": "VII", "capitulo_ccc": "Único",
        "articulo": "Art. 108 CCC",
        "gravedad_base": 2, "es_conflicto_vecinal": False,
        "frecuencia": "baja", "favorito": False,
    },
    "transito_alcoholemia": {
        "label": "Conducción en estado de ebriedad o bajo efecto de estupefacientes",
        "titulo_ccc": "VII", "capitulo_ccc": "Único",
        "articulo": "Art. 109 CCC",
        "gravedad_base": 3, "es_conflicto_vecinal": False,
        "frecuencia": "alta", "favorito": True,
    },
    "transito_sin_documentacion": {
        "label": "Transitar sin documentación, sin casco o sin placa identificatoria",
        "titulo_ccc": "VII", "capitulo_ccc": "Único",
        "articulo": "Art. 111 CCC",
        "gravedad_base": 1, "es_conflicto_vecinal": False,
        "frecuencia": "muy_alta", "favorito": True,
    },

    # ═══════════════════════════════════════════════════════════════════════
    # TÍTULO VIII — Arts 112-118
    # Capítulo I: Registros y documentación (Arts 112-114)
    # ═══════════════════════════════════════════════════════════════════════
    "omision_listas_registros": {
        "label": "Omisión de enviar listas o llevar registros reglamentarios",
        "titulo_ccc": "VIII", "categoria": "Animales", "categoria": "Animales", "categoria": "Transito", "categoria": "Transito", "categoria": "Transito", "capitulo_ccc": "I",
        "articulo": "Art. 112 CCC",
        "gravedad_base": 1, "es_conflicto_vecinal": False,
        "frecuencia": "baja", "favorito": False,
    },
    "omision_registro_pasajeros": {
        "label": "Omisión de llevar registro de pasajeros (transporte público)",
        "titulo_ccc": "VIII", "capitulo_ccc": "I",
        "articulo": "Art. 113 CCC",
        "gravedad_base": 1, "es_conflicto_vecinal": False,
        "frecuencia": "baja", "favorito": False,
    },
    "omision_documentacion_carga": {
        "label": "Omisión de llevar documentación para el transporte de carga",
        "titulo_ccc": "VIII", "capitulo_ccc": "I",
        "articulo": "Art. 114 CCC",
        "gravedad_base": 1, "es_conflicto_vecinal": False,
        "frecuencia": "baja", "favorito": False,
    },

    # Capítulo II: Faenamiento y comercio de animales (Arts 115-118)
    "faenamiento_ilegal": {
        "label": "Faenamiento y transporte ilegal de animales",
        "titulo_ccc": "VIII", "capitulo_ccc": "II",
        "articulo": "Art. 115 CCC",
        "gravedad_base": 3, "es_conflicto_vecinal": False,
        "frecuencia": "baja", "favorito": False,
    },
    "comercializacion_animales_ilegal": {
        "label": "Comercialización de animales faenados ilegalmente",
        "titulo_ccc": "VIII", "capitulo_ccc": "II",
        "articulo": "Art. 116 CCC",
        "gravedad_base": 3, "es_conflicto_vecinal": False,
        "frecuencia": "baja", "favorito": False,
    },
}

# ── Categoria funcional (compatibilidad con el resto de la app) ───────────────
# Derivada del Título CCC + overrides específicos por clave.
# Preserva las categorías que usa el clasificador, filtros y PDFs.
_CAT_POR_TITULO = {
    "I":    "Convivencia",
    "II":   "Convivencia",
    "III":  "Propiedad",
    "IV":   "Propiedad",
    "V":    "Convivencia",
    "VI":   "Seguridad Publica",
    "VII":  "Transito",
    "VIII": "Transito",
}
_CAT_OVERRIDES = {
    "tocamientos_indecorosos":          "Integridad",
    "hostigamiento_maltrato_intimidacion":"Integridad",
    "actos_discriminatorios":           "Convivencia",
    "expresiones_discriminatorias":     "Convivencia",
    "derecho_admision":                 "Comercio",
    "ejercicio_abusivo_admision":       "Comercio",
    "cuidado_vehiculos_sin_autorizacion":"Comercio",
    "whiskerias_cabarets":              "Comercio",
    "expendio_prohibido_bebidas":       "Comercio",
    "reventa_entradas":                 "Comercio",
    "irregularidades_subasta":          "Comercio",
    "daño_monumentos_historicos":       "Espacio Publico",
    "daño_bienes_arqueologicos":        "Espacio Publico",
    "animales_sueltos":                 "Animales",
    "animales_en_predios_ajenos":       "Animales",
    "tenencia_animales_peligrosos":     "Animales",
    "faenamiento_ilegal":               "Animales",
    "comercializacion_animales_ilegal": "Animales",
    "pirotecnia_fabricacion":           "Pirotecnia",
    "pirotecnia_uso_prohibido":         "Pirotecnia",
    "pirotecnia_venta_menores":         "Pirotecnia",
    "pirotecnia_espectaculos":          "Pirotecnia",
    "portacion_ilegal_armas":           "Integridad",
    "disparo_armas_publico":            "Integridad",
    "expendio_alcohol_menores":         "Convivencia",
    "admision_menores_espectaculos":    "Convivencia",
    "vehiculo_ninos_interior":          "Convivencia",
    "suministro_objetos_peligrosos_menores": "Convivencia",
    "exposicion_menores_incapaces":     "Convivencia",
    "proteccion_nnya_alcohol":          "Convivencia",
    "juegos_fiestas_populares":         "Espacio Publico",
    "falsos_avisos_alarmas":            "Propiedad",
    "uso_indebido_telefonos":           "Propiedad",
    "negativa_identificarse":           "Propiedad",
    "falsa_denuncia_contravencion":     "Propiedad",
    "inobservancia_seguridad":          "Propiedad",
    "construcciones_ruinosas":          "Propiedad",
    "incumplimiento_normas_seguridad":  "Propiedad",
    "peligro_incendio":                 "Propiedad",
    "posesion_ganzuas":                 "Propiedad",
    "conducta_sospechosa":              "Propiedad",
    "merodeo_zona_rural":               "Propiedad",
    "interrupcion_servicios_publicos":  "Propiedad",
    "falsa_apariencia":                 "Propiedad",
    "omision_listas_registros":         "Transito",
    "omision_registro_pasajeros":       "Transito",
    "omision_documentacion_carga":      "Transito",
}
# Apply to all entries (overrides duplicate keys from the script)
for _k, _v in TIPOS_INFRACCION.items():
    _v["categoria"] = _CAT_OVERRIDES.get(
        _k, _CAT_POR_TITULO.get(_v.get("titulo_ccc", ""), "Convivencia")
    )

# ── Favoritos por defecto ─────────────────────────────────────────────────────
FAVORITOS_DEFAULT = [k for k, v in TIPOS_INFRACCION.items() if v.get("favorito")]

# ── Helper: condiciones de suspensión por tipo ────────────────────────────────
# NOTA: esta función se redefine DESPUÉS de CONDICIONES_SUSPENSION (ver abajo)
def get_condiciones_para(tipo_infraccion: str) -> list:
    """Stub — la implementación real está al final del archivo."""
    return []

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
        "Adecuar el establecimiento a los niveles reglamentarios dentro de los TREINTA (30) días",
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
        "Abonar multa correspondiente por deterioro de bienes comunes según art. 94 CCC",
    ],
    "animales": [
        "No reincidir en infracciones vinculadas a la tenencia irresponsable de animales por el término de UN (1) año",
        "Acreditar inscripción y vacunación del animal en el Registro Municipal correspondiente dentro de los TREINTA (30) días",
        "Prestar VEINTE (20) horas de trabajo comunitario en organismo de protección animal a designar",
        "En caso de animal potencialmente peligroso: colocar bozal y correa reglamentaria en espacio público",
    ],
    "pirotecnia": [
        "Abstenerse de adquirir, portar o usar artículos pirotécnicos por el término de UN (1) año (art. 96 CCC)",
        "No reincidir en infracciones similares bajo pena de duplicación de sanciones (art. 101 CCC)",
        "Prestar TREINTA (30) horas de trabajo comunitario en organismo a designar",
        "Abonar multa correspondiente según escala del art. 94 CCC",
    ],
    "propiedad": [
        "No reincidir en conductas que afecten la propiedad pública o privada por el término de SEIS (6) meses",
        "Reparar o restituir el daño causado dentro de los TREINTA (30) días de la resolución",
        "Prestar VEINTE (20) horas de trabajo comunitario, preferentemente en tareas de restauración de bienes públicos",
    ],
    "proteccion_menores": [
        "Abstenerse de suministrar bebidas alcohólicas o sustancias peligrosas a menores por el término de UN (1) año",
        "No reincidir en conductas que afecten la integridad de niñas, niños o adolescentes",
        "Prestar TREINTA (30) horas de trabajo comunitario en organismo de niñez a designar",
        "Acreditar participación en taller de crianza responsable o protección de la infancia",
    ],
}

# ── get_condiciones_para — implementación final (después de CONDICIONES_SUSPENSION)
def get_condiciones_para(tipo_infraccion: str) -> list:
    """
    Retorna las condiciones de suspensión apropiadas para el tipo de infracción dado.
    Usa el campo 'categoria' + 'titulo_ccc' para seleccionar el set correcto.
    """
    v    = TIPOS_INFRACCION.get(tipo_infraccion, {})
    cat  = v.get("categoria", "")
    tit  = v.get("titulo_ccc", "")
    grav = v.get("gravedad_base", 1)

    if tipo_infraccion == "transito_alcoholemia":
        return CONDICIONES_SUSPENSION["transito_alcoholemia"]
    if cat == "Transito" or tit == "VII":
        return CONDICIONES_SUSPENSION["transito"]
    if cat == "Animales":
        return CONDICIONES_SUSPENSION["animales"]
    if cat == "Pirotecnia":
        return CONDICIONES_SUSPENSION["pirotecnia"]
    if cat == "Propiedad":
        return CONDICIONES_SUSPENSION["propiedad"]
    if cat == "Integridad":
        return CONDICIONES_SUSPENSION["integridad"]
    if cat == "Comercio":
        return CONDICIONES_SUSPENSION["comercio"]
    if cat == "Espacio Publico":
        return CONDICIONES_SUSPENSION["espacio_publico"]
    if cat == "Proteccion Menores":
        return CONDICIONES_SUSPENSION["proteccion_menores"]
    # Convivencia y fallback
    return CONDICIONES_SUSPENSION["convivencia"]


UNIDADES = {
    "norte": "Unidad Contravencional Norte - Antonio del Viso 756, Barrio Alta Cordoba",
    "sur":   "Unidad Contravencional Sur - Guzman 1075, Centro",
    "genero":"Unidad Contravencional de Violencia de Genero - Entre Rios 680",
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
        "tipo": "riña_desordenes_publicos",
        "imputado": "Martínez, Jorge Alberto",
        "dni": "25.661.003",
        "edad": 48,
        "antecedentes": 2,
        "descripcion": "Altercado verbal con insultos y amenazas menores en galería comercial. Testigos presentes. Denunciante: comerciante del local 12.",
        "unidad": "norte",
    },
]
