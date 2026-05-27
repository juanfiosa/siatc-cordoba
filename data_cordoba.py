"""
Tipos de infracciones del Código de Convivencia Ciudadana de Córdoba
Ley Provincial N° 10.326 y sus modificatorias
"""

TIPOS_INFRACCION = {
    # === TRÁNSITO Y SEGURIDAD VIAL ===
    "transito_sin_documentacion": {
        "label": "Circular sin documentación (licencia/cédula)",
        "categoria": "Tránsito",
        "articulo": "Art. 75 CCC",
        "gravedad_base": 1,
        "es_conflicto_vecinal": False,
        "frecuencia": "muy_alta",
    },
    "transito_sin_casco": {
        "label": "Circular sin casco (motocicleta)",
        "categoria": "Tránsito",
        "articulo": "Art. 76 CCC",
        "gravedad_base": 1,
        "es_conflicto_vecinal": False,
        "frecuencia": "muy_alta",
    },
    "transito_alcoholemia": {
        "label": "Conducción bajo efecto de alcohol",
        "categoria": "Tránsito",
        "articulo": "Art. 80 CCC",
        "gravedad_base": 3,
        "es_conflicto_vecinal": False,
        "frecuencia": "alta",
    },
    "transito_exceso_velocidad": {
        "label": "Exceso de velocidad",
        "categoria": "Tránsito",
        "articulo": "Art. 78 CCC",
        "gravedad_base": 2,
        "es_conflicto_vecinal": False,
        "frecuencia": "alta",
    },
    "transito_semaforo": {
        "label": "Violación de semáforo en rojo",
        "categoria": "Tránsito",
        "articulo": "Art. 77 CCC",
        "gravedad_base": 2,
        "es_conflicto_vecinal": False,
        "frecuencia": "media",
    },
    # === CONVIVENCIA VECINAL ===
    "ruidos_molestos_nocturnos": {
        "label": "Ruidos molestos en horario nocturno",
        "categoria": "Convivencia",
        "articulo": "Art. 49 CCC",
        "gravedad_base": 1,
        "es_conflicto_vecinal": True,
        "frecuencia": "alta",
    },
    "ruidos_molestos_diurnos": {
        "label": "Ruidos molestos en horario diurno",
        "categoria": "Convivencia",
        "articulo": "Art. 49 CCC",
        "gravedad_base": 1,
        "es_conflicto_vecinal": True,
        "frecuencia": "media",
    },
    "animales_sueltos": {
        "label": "Animal suelto / sin correa en espacio público",
        "categoria": "Convivencia",
        "articulo": "Art. 55 CCC",
        "gravedad_base": 1,
        "es_conflicto_vecinal": True,
        "frecuencia": "alta",
    },
    "obstruccion_espacio_publico": {
        "label": "Obstrucción de espacio público (vereda, acceso)",
        "categoria": "Convivencia",
        "articulo": "Art. 51 CCC",
        "gravedad_base": 1,
        "es_conflicto_vecinal": True,
        "frecuencia": "media",
    },
    "riña_verbal_vecinal": {
        "label": "Escándalo / altercado verbal entre vecinos",
        "categoria": "Convivencia",
        "articulo": "Art. 48 CCC",
        "gravedad_base": 2,
        "es_conflicto_vecinal": True,
        "frecuencia": "media",
    },
    # === ESTABLECIMIENTOS Y COMERCIOS ===
    "establecimiento_ruidos": {
        "label": "Establecimiento comercial con ruidos excesivos",
        "categoria": "Comercio",
        "articulo": "Art. 49 inc. b CCC",
        "gravedad_base": 2,
        "es_conflicto_vecinal": False,
        "frecuencia": "media",
    },
    "establecimiento_horario": {
        "label": "Establecimiento fuera de horario habilitado",
        "categoria": "Comercio",
        "articulo": "Art. 62 CCC",
        "gravedad_base": 2,
        "es_conflicto_vecinal": False,
        "frecuencia": "media",
    },
    # === ESPACIO PÚBLICO ===
    "consumo_alcohol_via_publica": {
        "label": "Consumo de alcohol en vía pública",
        "categoria": "Espacio Público",
        "articulo": "Art. 58 CCC",
        "gravedad_base": 1,
        "es_conflicto_vecinal": False,
        "frecuencia": "media",
    },
    "deterioro_bienes_publicos": {
        "label": "Deterioro de bienes públicos (grafitis, etc.)",
        "categoria": "Espacio Público",
        "articulo": "Art. 57 CCC",
        "gravedad_base": 2,
        "es_conflicto_vecinal": False,
        "frecuencia": "baja",
    },
    # === VIOLENCIA E INTEGRIDAD ===
    "amenazas_leves": {
        "label": "Amenazas leves (sin arma)",
        "categoria": "Integridad",
        "articulo": "Art. 44 CCC",
        "gravedad_base": 3,
        "es_conflicto_vecinal": True,
        "frecuencia": "media",
    },
    "agresion_fisica_leve": {
        "label": "Agresión física leve (sin lesiones graves)",
        "categoria": "Integridad",
        "articulo": "Art. 43 CCC",
        "gravedad_base": 4,
        "es_conflicto_vecinal": True,
        "frecuencia": "baja",
    },
}

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
}

UNIDADES = {
    "norte": "Unidad Contravencional Norte — Antonio del Viso 756, Barrio Alta Córdoba",
    "sur": "Unidad Contravencional Sur — Guzmán 1075, Centro",
    "genero": "Unidad Contravencional de Violencia de Género — Entre Ríos 680",
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
