# -*- coding: utf-8 -*-
"""
Poblar la base de datos con datos demo realistas.
SIATC - MPF Córdoba
"""

import sqlite3
from datetime import datetime, date, timedelta
import database as db

# ---------------------------------------------------------------------------
# Datos de personas e imputados ficticios
# ---------------------------------------------------------------------------

PERSONAS_DEMO = [
    # ── Córdoba Capital (índices 0-13) ────────────────────────────────────────
    {"dni": "38421667", "apellido_nombre": "Garcia, Lucas Damian",    "edad": 24, "domicilio": "Av. Colon 1200, Córdoba", "telefono": "351-4521001"},
    {"dni": "30112445", "apellido_nombre": "Perez, Marcelo Ariel",    "edad": 41, "domicilio": "Rivadavia 456, Córdoba",  "telefono": "351-4522002"},
    {"dni": "33887021", "apellido_nombre": "Rodriguez, Sebastian Omar","edad": 29, "domicilio": "Figueroa Alcorta 890",   "telefono": "351-4523003"},
    {"dni": "27334891", "apellido_nombre": "Lopez, Maria Fernanda",   "edad": 55, "domicilio": "Plaza V. Sarsfield s/n", "telefono": "351-4524004"},
    {"dni": "25661003", "apellido_nombre": "Martinez, Jorge Alberto", "edad": 48, "domicilio": "Galeria Comercial Local 12","telefono": "351-4525005"},
    {"dni": "40112233", "apellido_nombre": "Fernandez, Valentina",    "edad": 22, "domicilio": "Bv. Chacabuco 550",       "telefono": "351-4526006"},
    {"dni": "29887654", "apellido_nombre": "Gomez, Ricardo Hernan",   "edad": 37, "domicilio": "Calle Lima 320",          "telefono": "351-4527007"},
    {"dni": "35441122", "apellido_nombre": "Diaz, Carolina Beatriz",  "edad": 32, "domicilio": "Bv. Illia 1100",          "telefono": "351-4528008"},
    {"dni": "22334455", "apellido_nombre": "Torres, Hector Manuel",   "edad": 62, "domicilio": "Calle Tucuman 780",       "telefono": "351-4529009"},
    {"dni": "41556677", "apellido_nombre": "Ruiz, Agustina Paola",    "edad": 21, "domicilio": "Dean Funes 234",          "telefono": "351-4530010"},
    {"dni": "36778899", "apellido_nombre": "Sanchez, Pablo Eduardo",  "edad": 35, "domicilio": "Av. Maipú 1450",         "telefono": "351-4531011"},
    {"dni": "28990011", "apellido_nombre": "Moreno, Claudia Ines",    "edad": 44, "domicilio": "Calle Obispo Trejo 890", "telefono": "351-4532012"},
    {"dni": "43221890", "apellido_nombre": "Villareal, Natalia Belen","edad": 28, "domicilio": "Av. Cabrera 340, Villa El Libertador", "telefono": "351-4533013"},
    {"dni": "31445677", "apellido_nombre": "Acuña, Roberto Carlos",   "edad": 52, "domicilio": "Calle Belgrano 1220, Bº Los Plátanos", "telefono": "351-4534014"},
    # ── Río Cuarto (índices 14-19) ────────────────────────────────────────────
    {"dni": "37661234", "apellido_nombre": "Bustos, Marcos Ezequiel",  "edad": 26, "domicilio": "Bv. Roca 560, Rio Cuarto",             "telefono": "358-4621001"},
    {"dni": "32445566", "apellido_nombre": "Peralta, Graciela Noemi",  "edad": 49, "domicilio": "Calle Sobremonte 890, Rio Cuarto",      "telefono": "358-4621002"},
    {"dni": "41229900", "apellido_nombre": "Cabral, Ignacio Ramon",    "edad": 23, "domicilio": "Av. Laprida 1200, Rio Cuarto",          "telefono": "358-4621003"},
    {"dni": "28776655", "apellido_nombre": "Quintero, Sandra Patricia","edad": 38, "domicilio": "Calle San Martin 450, Rio Cuarto",      "telefono": "358-4621004"},
    {"dni": "39887766", "apellido_nombre": "Ferreyra, Diego Ariel",    "edad": 31, "domicilio": "Bv. Sarmiento 2100, Rio Cuarto",        "telefono": "358-4621005"},
    {"dni": "25669988", "apellido_nombre": "Molina, Ana Cecilia",      "edad": 57, "domicilio": "Calle Constitucion 780, Rio Cuarto",    "telefono": "358-4621006"},
]

CASOS_SEED = [
    # Estado: archivada (seguimiento cumplido)
    {"persona_idx": 0, "tipo": "transito_sin_documentacion", "unidad": "norte",
     "desc": "Circulaba en motocicleta Yamaha sin portar licencia de conducir. Control rutina.",
     "antec": 0, "estado": "archivada", "carril": "verde",
     "dias_atras": 120, "seg": True, "seg_estado": "cumplido", "seg_meses": 6},

    # Estado: resuelta (seguimiento activo, al 60%)
    {"persona_idx": 1, "tipo": "ruidos_molestos_nocturnos", "unidad": "sur",
     "desc": "Música a alto volumen desde departamento 4B, 00:30hs del sábado.",
     "antec": 1, "estado": "resuelta", "carril": "amarillo",
     "dias_atras": 45, "seg": True, "seg_estado": "activo", "seg_meses": 6},

    # Estado: resuelta (seguimiento activo, próximo a vencer)
    {"persona_idx": 2, "tipo": "transito_alcoholemia", "unidad": "norte",
     "desc": "Alcotest positivo 0.85 g/l en Av. Figueroa Alcorta. Sin accidente.",
     "antec": 0, "estado": "resuelta", "carril": "amarillo",
     "dias_atras": 160, "seg": True, "seg_estado": "activo", "seg_meses": 6},

    # Estado: resuelta (seguimiento activo, casi cumplido)
    {"persona_idx": 3, "tipo": "animales_sueltos", "unidad": "sur",
     "desc": "Perro mediano suelto en plaza Vélez Sársfield que mordió a otro animal.",
     "antec": 0, "estado": "resuelta", "carril": "verde",
     "dias_atras": 70, "seg": True, "seg_estado": "activo", "seg_meses": 3},

    # Estado: notificada (sin seguimiento aún, SIN ACTIVIDAD desde hace 8 días)
    {"persona_idx": 4, "tipo": "riña_verbal_vecinal", "unidad": "norte",
     "desc": "Altercado verbal con insultos en galería comercial. Testigos presentes.",
     "antec": 2, "estado": "notificada", "carril": "rojo",
     "dias_atras": 10, "seg": False, "updated_dias": 8},

    # Estado: clasificada
    {"persona_idx": 5, "tipo": "consumo_alcohol_via_publica", "unidad": "sur",
     "desc": "Consumo de bebida alcohólica en banco de plaza. Personal preventor constató.",
     "antec": 0, "estado": "clasificada", "carril": "verde",
     "dias_atras": 3, "seg": False},

    # Estado: archivada (cumplido)
    {"persona_idx": 6, "tipo": "establecimiento_horario", "unidad": "sur",
     "desc": "Local bailable con música a las 5:30hs, fuera del horario habilitado.",
     "antec": 0, "estado": "archivada", "carril": "amarillo",
     "dias_atras": 200, "seg": True, "seg_estado": "cumplido", "seg_meses": 12},

    # Estado: resuelta (seguimiento incumplido)
    {"persona_idx": 7, "tipo": "amenazas_leves", "unidad": "norte",
     "desc": "Amenazas por conflicto de medianera. Víctima identificada. Sin arma.",
     "antec": 1, "estado": "resuelta", "carril": "rojo",
     "dias_atras": 95, "seg": True, "seg_estado": "incumplido", "seg_meses": 6},

    # Estado: en_mediacion
    {"persona_idx": 8, "tipo": "obstruccion_espacio_publico", "unidad": "norte",
     "desc": "Vehículo obstruye acceso peatonal de edificio. Denuncia vecinal reiterada.",
     "antec": 0, "estado": "en_mediacion", "carril": "verde",
     "dias_atras": 15, "seg": False},

    # Estado: clasificada
    {"persona_idx": 9, "tipo": "transito_exceso_velocidad", "unidad": "norte",
     "desc": "Radar detectó 98 km/h en zona de 60 km/h. Av. Rafael Núñez al 3200.",
     "antec": 0, "estado": "clasificada", "carril": "amarillo",
     "dias_atras": 5, "seg": False},

    # Estado: resuelta (seguimiento activo, vencido sin cierre)
    {"persona_idx": 10, "tipo": "deterioro_bienes_publicos", "unidad": "sur",
     "desc": "Grafiti en fachada de edificio histórico en la peatonal. Filmado por cámaras.",
     "antec": 0, "estado": "resuelta", "carril": "amarillo",
     "dias_atras": 220, "seg": True, "seg_estado": "activo", "seg_meses": 6},

    # Estado: ingresada (reciente)
    {"persona_idx": 11, "tipo": "establecimiento_ruidos", "unidad": "sur",
     "desc": "Bar con música en vivo supera decibeles permitidos. Medición técnica realizada.",
     "antec": 0, "estado": "ingresada", "carril": "amarillo",
     "dias_atras": 1, "seg": False},

    # Unidad Género: notificada SIN audiencia, SIN actividad hace 35 días
    {"persona_idx": 12, "tipo": "agresion_fisica_leve", "unidad": "genero",
     "desc": "Agresión física hacia conviviente en domicilio particular. Constatada por personal policial. Víctima identificada. Requiere medida cautelar.",
     "antec": 1, "estado": "notificada", "carril": "rojo",
     "dias_atras": 40, "seg": False, "updated_dias": 35},

    # Unidad Género: clasificada SIN audiencia, SIN actividad hace 20 días
    {"persona_idx": 13, "tipo": "amenazas_leves", "unidad": "genero",
     "desc": "Amenazas hacia ex pareja mediante mensajes de voz reiterados. Víctima identificada. Solicita restricción de acercamiento.",
     "antec": 0, "estado": "clasificada", "carril": "rojo",
     "dias_atras": 25, "seg": False, "updated_dias": 20},

    # REINCIDENCIA: segunda causa para Garcia (persona_idx=0) - transito_exceso_velocidad
    {"persona_idx": 0, "tipo": "transito_exceso_velocidad", "unidad": "norte",
     "desc": "Control radar Av. Rafael Núñez al 3200 marcó 112 km/h en zona de 60 km/h. Reincidente en infracciones viales.",
     "antec": 1, "estado": "clasificada", "carril": "amarillo",
     "dias_atras": 4, "seg": False},

    # ── Río Cuarto (índices 16-21, usa unidad="rio_cuarto") ───────────────────
    # Fiscales manejan penal Y contravencional. Policía Provincial eleva las actas.
    {"persona_idx": 14, "tipo": "transito_alcoholemia", "unidad": "rio_cuarto",
     "desc": "Alcotest positivo 0.92 g/l en Bv. Roca al 800. Sin accidente, vehículo retenido.",
     "antec": 0, "estado": "notificada", "carril": "amarillo",
     "dias_atras": 12, "seg": False,
     "fiscal": "Dr. Moine", "nodo": "rio_cuarto"},

    {"persona_idx": 15, "tipo": "riña_desordenes_publicos", "unidad": "rio_cuarto",
     "desc": "Pelea entre dos personas en Calle Sobremonte 890 a las 23:00hs. Testigos identificados. Ambos imputados.",
     "antec": 1, "estado": "clasificada", "carril": "rojo",
     "dias_atras": 5, "seg": False,
     "fiscal": "Dra. Di Santo", "nodo": "rio_cuarto"},

    {"persona_idx": 16, "tipo": "tenencia_animales_peligrosos", "unidad": "rio_cuarto",
     "desc": "Pitbull sin bozal ni correa agredió a peatón en Av. Laprida 1200. Propietario identificado. Víctima con lesiones leves.",
     "antec": 0, "estado": "resuelta", "carril": "amarillo",
     "dias_atras": 45, "seg": True, "seg_estado": "activo", "seg_meses": 3,
     "fiscal": "Dr. Moine", "nodo": "rio_cuarto"},

    {"persona_idx": 17, "tipo": "negativa_identificarse", "unidad": "rio_cuarto",
     "desc": "Persona detenida se negó a identificarse ante personal policial en control de rutina. Finalmente identificada.",
     "antec": 0, "estado": "ingresada", "carril": "verde",
     "dias_atras": 2, "seg": False,
     "fiscal": "Dra. Di Santo", "nodo": "rio_cuarto"},

    {"persona_idx": 18, "tipo": "daño_propiedad_publica", "unidad": "rio_cuarto",
     "desc": "Grafitis en fachada del edificio municipal de Bv. Sarmiento. Daño valuado en $85.000. Imputado filmado por cámara.",
     "antec": 0, "estado": "notificada", "carril": "amarillo",
     "dias_atras": 20, "seg": False,
     "fiscal": "Dr. Moine", "nodo": "rio_cuarto"},

    {"persona_idx": 19, "tipo": "pirotecnia_uso_prohibido", "unidad": "rio_cuarto",
     "desc": "Uso de pirotecnia de alto impacto en zona urbana durante festejo deportivo. Vecinos con mascotas afectadas.",
     "antec": 1, "estado": "archivada", "carril": "verde",
     "dias_atras": 90, "seg": True, "seg_estado": "cumplido", "seg_meses": 3,
     "fiscal": "Dra. Di Santo", "nodo": "rio_cuarto"},
]

# Condiciones pre-armadas por tipo de seguimiento
CONDICIONES_SEED = {
    "transito_sin_documentacion": [
        ("otro", "No reincidir en infracciones de tránsito por 6 meses", 0, "", ""),
        ("curso", "Realizar Curso de Educación Vial - Dirección de Tránsito", 0, "", ""),
    ],
    "ruidos_molestos_nocturnos": [
        ("otro", "No reincidir en conductas perturbadoras por 6 meses", 0, "", ""),
        ("trabajo_comunitario", "Trabajo comunitario", 20, "horas", ""),
        ("curso", "Taller de resolución pacífica de conflictos", 0, "", ""),
    ],
    "transito_alcoholemia": [
        ("abstencion", "Abstenerse de conducir bajo efectos del alcohol por 1 año", 0, "", ""),
        ("curso", "Curso de Conducción Responsable y Prevención Alcohol al Volante", 0, "", ""),
        ("presentacion", "Controles de alcoholemia en los próximos 6 meses", 2, "controles", ""),
        ("trabajo_comunitario", "Trabajo comunitario", 40, "horas", ""),
    ],
    "animales_sueltos": [
        ("otro", "No reincidir en conductas perturbadoras por 6 meses", 0, "", ""),
        ("trabajo_comunitario", "Trabajo comunitario en organismo a designar", 20, "horas", ""),
    ],
    "amenazas_leves": [
        ("abstencion", "No acercarse a menos de 200 metros de la víctima por 6 meses", 0, "", ""),
        ("otro", "No reincidir en conductas similares", 0, "", ""),
        ("trabajo_comunitario", "Trabajo comunitario", 40, "horas", ""),
        ("curso", "Programa de manejo de conflictos del Ministerio de Justicia", 0, "", ""),
    ],
    "establecimiento_horario": [
        ("otro", "Adecuar establecimiento a horarios habilitados en 30 días", 0, "", ""),
        ("otro", "No reincidir en infracciones similares por 1 año", 0, "", ""),
        ("trabajo_comunitario", "Trabajo comunitario", 30, "horas", ""),
    ],
    "deterioro_bienes_publicos": [
        ("otro", "No reincidir en conductas perturbadoras por 6 meses", 0, "", ""),
        ("trabajo_comunitario", "Trabajo comunitario", 20, "horas", ""),
    ],
}

# Avances parciales para condiciones con meta cuantitativa
AVANCES_SEED = {
    # persona_idx: {tipo_cond: avances}
    1: {"trabajo_comunitario": [8, 8, 4]},    # Perez: 20h objetivo, 20 cargadas (cumplido)
    2: {"trabajo_comunitario": [8, 8, 8, 8],  # Rodriguez: 40h objetivo, 32 cargadas
        "controles": [1]},                     # 1 de 2 controles
    3: {"trabajo_comunitario": [16, 4]},       # Lopez: 20h objetivo, 20 cargadas (cumplido)
    10: {"trabajo_comunitario": [5]},          # Sanchez: apenas empezó
}


def _fecha(dias_atras):
    return (date.today() - timedelta(days=dias_atras)).isoformat()


def _dt(dias_atras):
    return (datetime.now() - timedelta(days=dias_atras)).strftime("%Y-%m-%d %H:%M:%S")


def ya_poblado():
    with db.get_conn() as conn:
        n = conn.execute("SELECT COUNT(*) as n FROM causas").fetchone()["n"]
    return n >= 5


def rc_poblado():
    """Verifica si hay causas del nodo Río Cuarto en la DB."""
    with db.get_conn() as conn:
        n = conn.execute(
            "SELECT COUNT(*) as n FROM causas WHERE unidad='rio_cuarto'"
        ).fetchone()["n"]
    return n >= 3


def poblar_rc():
    """Inserta los casos demo específicos de Río Cuarto. Idempotente."""
    if rc_poblado():
        return False

    rc_casos = [c for c in CASOS_SEED if c.get("unidad") == "rio_cuarto"]
    rc_personas_idx = {c["persona_idx"] for c in rc_casos}

    with db.get_conn() as conn:
        for idx in rc_personas_idx:
            p = PERSONAS_DEMO[idx]
            db.upsert_persona(p["dni"], p["apellido_nombre"], p["edad"],
                              p["domicilio"], p["telefono"])

    prefijos = {"rio_cuarto": "RC"}
    for i, caso in enumerate(rc_casos):
        p = PERSONAS_DEMO[caso["persona_idx"]]
        pref  = "RC"
        numero = f"2025-{pref}-{i+1:05d}"
        clf    = {"carril": caso["carril"], "accion": _accion(caso["carril"]),
                  "score": _score(caso["carril"])}

        with db.get_conn() as conn:
            existing = conn.execute("SELECT id FROM causas WHERE numero=?", (numero,)).fetchone()
            if existing:
                continue
            _n_est  = {"ingresada":1,"clasificada":2,"notificada":3,"en_mediacion":4,"resuelta":4,"archivada":5}.get(caso["estado"],2)
            _step   = max(1, caso["dias_atras"] // _n_est)
            cur = conn.execute("""
                INSERT INTO causas
                  (numero, persona_id, tipo_infraccion, descripcion, carril, accion,
                   unidad, fiscal_asignado, estado, score_clasificacion,
                   fecha_hecho, created_at, updated_at)
                VALUES (?,
                  (SELECT id FROM personas WHERE dni=?),
                  ?,?,?,?,?,?,?,?,?,?,?)""", (
                numero, p["dni"], caso["tipo"], caso["desc"],
                caso["carril"], clf["accion"],
                caso["unidad"],
                caso.get("fiscal", "Dr. Moine"),
                caso["estado"], clf["score"],
                _fecha(caso["dias_atras"] + 3),
                _dt(caso["dias_atras"]),
                _dt(caso.get("updated_dias", _step)),
            ))
            causa_id = cur.lastrowid
            fiscal_caso = caso.get("fiscal", "Dr. Moine")
            _insertar_timeline(conn, causa_id, caso["estado"], caso["dias_atras"], fiscal_caso)
        if caso.get("seg"):
            p_dict = PERSONAS_DEMO[caso["persona_idx"]]
            _crear_seg_demo(causa_id, caso, p_dict)

    return True


def poblar():
    """Inserta todos los datos demo en la base. Idempotente por DNI único."""
    if ya_poblado():
        return False

    prefijos = {"norte": "UCN", "sur": "UCS", "genero": "UCG",
                "rio_cuarto": "RC", "bell_ville": "BV", "villa_maria": "VM",
                "san_francisco": "SF", "villa_dolores": "VD",
                "cruz_del_eje": "CE", "laboulaye": "LB",
                "dean_funes": "DF", "rio_tercero": "RT"}
    numeros_causa = {}  # persona_idx -> causa_id

    for idx, caso in enumerate(CASOS_SEED):
        p = PERSONAS_DEMO[caso["persona_idx"]]

        # Persona
        pid = db.upsert_persona(p["dni"], p["apellido_nombre"], p["edad"],
                                p["domicilio"], p["telefono"])

        # Número de causa
        pref = prefijos.get(caso["unidad"], "UCX")
        numero = f"2025-{pref}-{idx+1:05d}"

        clf = {"carril": caso["carril"], "accion": _accion(caso["carril"]),
               "score": _score(caso["carril"])}

        with db.get_conn() as conn:
            existing = conn.execute("SELECT id FROM causas WHERE numero=?", (numero,)).fetchone()
            if existing:
                numeros_causa[caso["persona_idx"]] = existing["id"]
                continue

            # updated_at ≈ last state change time (approximate)
            _estados_count = {
                "ingresada": 1, "clasificada": 2, "notificada": 3,
                "en_mediacion": 4, "resuelta": 4, "archivada": 5,
            }
            _n_est = _estados_count.get(caso["estado"], 2)
            _step  = max(1, caso["dias_atras"] // _n_est)
            _updated_dias = max(0, _step)  # last state was ~1 step ago

            cur = conn.execute("""
                INSERT INTO causas
                  (numero, persona_id, tipo_infraccion, descripcion, carril, accion,
                   unidad, fiscal_asignado, estado, score_clasificacion, fecha_hecho, created_at, updated_at)
                VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)
            """, (
                numero, pid, caso["tipo"], caso["desc"],
                caso["carril"], clf["accion"],
                caso["unidad"],
                caso.get("fiscal") or {
                    "norte": "Dra. Ana Perez", "sur": "Dr. Carlos Medina",
                    "genero": "Dra. Laura Suarez"
                }.get(caso["unidad"], "Dra. Ana Perez"),
                caso["estado"], clf["score"],
                _fecha(caso["dias_atras"] + 3),
                _dt(caso["dias_atras"]),
                _dt(caso.get("updated_dias", _updated_dias)),
            ))
            causa_id = cur.lastrowid
            numeros_causa[caso["persona_idx"]] = causa_id

            # Timeline de estados
            fiscal_caso = caso.get("fiscal") or {
                "norte": "Dra. Ana Perez", "sur": "Dr. Carlos Medina",
                "genero": "Dra. Laura Suarez"
            }.get(caso["unidad"], "Dra. Ana Perez")
            _insertar_timeline(conn, causa_id, caso["estado"], caso["dias_atras"], fiscal_caso)

        # Seguimiento
        if caso.get("seg"):
            _crear_seg_demo(causa_id, caso, p)

    # Audiencias vinculadas a las causas
    _crear_audiencias_demo(numeros_causa)

    # Mensajes demo inter-oficina (ilustra el sistema de mensajería)
    _crear_mensajes_demo(numeros_causa)

    return True


def _crear_mensajes_demo(causa_ids_por_idx: dict):
    """Crea mensajes demo entre Policía Judicial y la Unidad para ilustrar la mensajería."""
    try:
        from database import get_conn
        causa_id_1 = causa_ids_por_idx.get(0)  # Garcia - causa archivada
        causa_id_2 = causa_ids_por_idx.get(4)  # Martinez - causa notificada
        if causa_id_1:
            with get_conn() as conn:
                conn.execute("""INSERT OR IGNORE INTO mensajes_interoficina
                    (causa_id, tipo, asunto, cuerpo, oficina_origen, usuario_origen,
                     oficina_destino, estado, prioridad, created_at)
                    VALUES (?,?,?,?,?,?,?,?,?,?)""", (
                    causa_id_1, "notificacion",
                    "Ingreso de actuacion contravencional",
                    "Se eleva actuacion labrada por infraccion al Art. 111 CCC. "
                    "Imputado identificado en control de rutina Av. Colon 1200.",
                    "policia_judicial", "Of. Roberto Sosa",
                    "fiscal_cba_norte", "recibido", "normal",
                    _dt(5)
                ))
        if causa_id_2:
            with get_conn() as conn:
                conn.execute("""INSERT OR IGNORE INTO mensajes_interoficina
                    (causa_id, tipo, asunto, cuerpo, oficina_origen, usuario_origen,
                     oficina_destino, estado, prioridad, created_at)
                    VALUES (?,?,?,?,?,?,?,?,?,?)""", (
                    causa_id_2, "instruccion",
                    "Citese al imputado",
                    "Sintese citar al imputado Martinez, Jorge Alberto (DNI 25661003) "
                    "a comparecer ante esta Unidad el dia proximo martes a las 10:00 hs. "
                    "Adjunto cedula de notificacion.",
                    "fiscal_cba_norte", "Dra. Ana Perez",
                    "policia_judicial", "enviado", "normal",
                    _dt(3)
                ))
                conn.execute("""INSERT OR IGNORE INTO mensajes_interoficina
                    (causa_id, tipo, asunto, cuerpo, oficina_origen, usuario_origen,
                     oficina_destino, estado, prioridad, created_at)
                    VALUES (?,?,?,?,?,?,?,?,?,?)""", (
                    causa_id_2, "notificacion",
                    "Diligencia cumplida - imputado notificado",
                    "Se informa que el imputado Martinez fue notificado exitosamente "
                    "en su domicilio de Galeria Comercial Local 12. Firma en el acta.",
                    "policia_judicial", "Of. Roberto Sosa",
                    "fiscal_cba_norte", "enviado", "normal",
                    _dt(1)
                ))
    except Exception:
        pass  # mensajería es opcional en el seed


def _accion(carril):
    return {"verde": "Derivar a mediación", "amarillo": "Suspensión del proceso a prueba",
            "rojo": "Proceso contravencional pleno"}.get(carril, "")


def _score(carril):
    return {"verde": 1.0, "amarillo": 2.2, "rojo": 3.8}.get(carril, 2.0)


def _insertar_timeline(conn, causa_id, estado_final, dias_atras, usuario="Dra. Ana Perez"):
    estados_map = {
        "ingresada":    ["ingresada"],
        "clasificada":  ["ingresada", "clasificada"],
        "notificada":   ["ingresada", "clasificada", "notificada"],
        "en_mediacion": ["ingresada", "clasificada", "notificada", "en_mediacion"],
        "resuelta":     ["ingresada", "clasificada", "notificada", "resuelta"],
        "archivada":    ["ingresada", "clasificada", "notificada", "resuelta", "archivada"],
    }
    estados = estados_map.get(estado_final, ["ingresada", "clasificada"])
    step = max(1, dias_atras // len(estados))
    ant = None
    for i, est in enumerate(estados):
        dias = dias_atras - i * step
        conn.execute(
            """INSERT INTO estados_causa
               (causa_id, estado_anterior, estado_nuevo, usuario, observaciones, created_at)
               VALUES (?,?,?,?,?,?)""",
            (causa_id, ant, est, usuario, _obs(est), _dt(dias))
        )
        ant = est


def _obs(estado):
    return {
        "ingresada":    "Causa ingresada por parte policial",
        "clasificada":  "Clasificación automática SIATC",
        "notificada":   "Cédula de citación emitida",
        "en_mediacion": "Derivada al Centro Judicial de Mediación",
        "resuelta":     "Dictamen de suspensión del proceso a prueba suscripto",
        "archivada":    "Seguimiento completado satisfactoriamente. Causa archivada.",
    }.get(estado, "")


def _crear_seg_demo(causa_id, caso, persona):
    tipo_res = "suspension" if caso["carril"] in ("amarillo", "rojo") else "mediacion"
    meses = caso.get("seg_meses", 6)
    dias = caso["dias_atras"]
    fiscal_seg = {"norte": "Dra. Ana Perez", "sur": "Dr. Carlos Medina",
                  "genero": "Dra. Laura Suarez"}.get(caso["unidad"], "Dra. Ana Perez")

    fecha_inicio = _fecha(dias)
    fecha_fin_dt = date.today() - timedelta(days=dias) + timedelta(days=meses * 30)
    fecha_fin = fecha_fin_dt.isoformat()

    seg_id = db.crear_seguimiento(
        causa_id=causa_id,
        tipo_resolucion=tipo_res,
        fecha_inicio=fecha_inicio,
        fecha_fin=fecha_fin,
        fiscal=fiscal_seg,
        observaciones=""
    )

    # Condiciones
    conds = CONDICIONES_SEED.get(caso["tipo"], [
        ("otro", "No reincidir en conductas similares por 6 meses", 0, "", ""),
        ("trabajo_comunitario", "Trabajo comunitario en organismo a designar", 20, "horas", ""),
    ])

    pid = caso["persona_idx"]
    avances_persona = AVANCES_SEED.get(pid, {})

    cond_ids = {}
    for tipo, desc, objetivo, unidad, flim in conds:
        cid = db.agregar_condicion(seg_id, tipo, desc, objetivo, unidad, flim)
        cond_ids[tipo] = cid

    # Registrar avances parciales
    for tipo_cond, avances in avances_persona.items():
        cid = cond_ids.get(tipo_cond)
        if not cid:
            continue
        base_dia = dias - 5
        for av in avances:
            base_dia -= 7
            db.registrar_avance(cid, _fecha(max(0, base_dia)), av, "Acreditado por certificado", "Dra. Ana Perez")

    # Marcar condiciones como cumplidas si el seguimiento fue exitoso
    if caso.get("seg_estado") == "cumplido":
        for cid in cond_ids.values():
            db.marcar_condicion(cid, "cumplido")

    # Set próximo control for active seguimientos (within next 14 days)
    if caso.get("seg_estado") not in ("cumplido", "incumplido", "revocado"):
        import random as _rand
        _ctrl_dias = _rand.randint(1, 14)
        _pc_fecha = (date.today() + timedelta(days=_ctrl_dias)).isoformat()
        db.set_proximo_control(seg_id, _pc_fecha)

    # Cerrar seguimiento si corresponde
    if caso.get("seg_estado") in ("cumplido", "incumplido", "revocado"):
        db.cerrar_seguimiento(seg_id, caso["seg_estado"])


def _crear_audiencias_demo(causa_ids_por_idx):
    """Crea audiencias demo vinculadas a las causas generadas."""
    from database import crear_audiencia
    from datetime import date, timedelta

    hoy = date.today()

    # Programadas futuras (notificadas, clasificadas, en_mediacion)
    audiencias = [
        # (persona_idx, tipo, dias_desde_hoy, hora, estado)
        (4,  "audiencia",       2,   "10:00", "programada"),   # Martinez rojo - urgente
        (8,  "mediacion",       3,   "11:30", "programada"),   # Torres en mediacion
        (9,  "audiencia",       5,   "09:00", "programada"),   # Ruiz clasificada
        (5,  "acta_compromiso", 7,   "10:30", "programada"),   # Fernandez
        (11, "audiencia",       10,  "09:00", "programada"),   # Moreno ingresada
        (12, "audiencia",       1,   "09:30", "programada"),   # Villareal genero - urgente
        # Ya realizadas
        (0,  "audiencia",      -45,  "09:00", "realizada"),    # Garcia archivada
        (1,  "mediacion",      -30,  "10:00", "realizada"),    # Perez resuelta
        (2,  "audiencia",      -60,  "09:00", "realizada"),    # Rodriguez resuelta
        (3,  "mediacion",      -50,  "11:00", "realizada"),    # Lopez resuelta
        # Ausente (esto dispara alerta)
        (7,  "audiencia",      -10,  "09:00", "ausente"),      # Diaz incumplida
        # Reprogramada
        (6,  "control_seg",    -5,   "09:30", "reprogramada"), # Gomez
    ]

    unidades_por_idx = {
        0: "norte", 1: "sur", 2: "norte", 3: "sur", 4: "norte",
        5: "sur", 6: "sur", 7: "norte", 8: "norte", 9: "norte",
        10: "sur", 11: "sur", 12: "genero", 13: "genero",
    }

    for pidx, tipo, dias, hora, estado in audiencias:
        cid = causa_ids_por_idx.get(pidx)
        if not cid:
            continue
        u = unidades_por_idx.get(pidx, "norte")
        lugar = {
            "norte":  "Unidad Contravencional Norte - Antonio del Viso 756",
            "sur":    "Unidad Contravencional Sur - Guzman 1075",
            "genero": "Unidad de Violencia de Genero - Entre Rios 680",
        }.get(u, "Sede de la Unidad")

        fecha = (hoy + timedelta(days=dias)).isoformat()
        aud_id = crear_audiencia(cid, tipo, fecha, hora, lugar, "")

        if estado != "programada":
            db.actualizar_estado_audiencia(aud_id, estado)
