# -*- coding: utf-8 -*-
"""
documentos_ccc.py — Fuente única de TEXTO editable de los documentos
contravencionales CCC (Ley 10.326), para el flujo "generar → editar → archivar".

Cada generador devuelve (titulo, cuerpo). El cuerpo NO incluye el membrete
institucional ni el N° de expediente/fecha: eso lo agrega pdf_desde_texto()
al renderizar (header MPF + metadatos + sello). Así el actuante edita solo
el contenido legal y la firma, y el PDF refleja exactamente lo editado.

Los lugares que requieren completar a mano van con marcadores [ASÍ].
"""
from __future__ import annotations
from datetime import datetime, timedelta

from data_cordoba import TIPOS_INFRACCION, UNIDADES, get_condiciones_para

MESES = ["enero", "febrero", "marzo", "abril", "mayo", "junio",
         "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre"]

# Orden lógico del workflow CCC: ingreso → citación → audiencia → resolución → seguimiento
TIPOS_DOCUMENTO = [
    ("citacion_audiencia",   "Cédula de citación — audiencia"),
    ("citacion_mediacion",   "Cédula de citación — mediación"),
    ("citacion_acta",        "Cédula de citación — acta de compromiso"),
    ("notificacion_imputacion", "Notificación de la imputación (art. 133)"),
    ("citacion_testigo",     "Citación a testigo (lenguaje claro)"),
    ("citacion_imputado",    "Citación a persona imputada (lenguaje claro)"),
    ("acta_audiencia",       "Acta de audiencia contravencional"),
    ("dictamen_mediacion",   "Dictamen de derivación a mediación"),
    ("dictamen_suspension",  "Dictamen de suspensión del proceso a prueba"),
    ("acta_compromiso",      "Acta de compromiso (suspensión a prueba)"),
    ("decreto_suspension",   "Decreto de suspensión del proceso a prueba"),
    ("acta_restriccion",     "Acta de medidas restrictivas / acercamiento"),
    ("requerimiento",        "Requerimiento fiscal de apertura del proceso"),
    ("perdon_judicial",      "Resolución de perdón judicial"),
    ("decreto_archivo",      "Decreto de archivo"),
    ("resolucion_sobreseimiento", "Resolución de sobreseimiento"),
    ("certificado_cumplimiento", "Certificado de cumplimiento de condiciones"),
    ("informe_incumplimiento",   "Informe de incumplimiento de condiciones"),
    ("comunicacion_victima", "Comunicación a la víctima (lenguaje claro)"),
    ("oficio_polo",          "Oficio al Polo Integral de la Mujer"),
    ("oficio_socioambiental", "Oficio — informe socioambiental"),
    ("oficio_valoracion",    "Oficio — valoración psicológica"),
]
LABELS_DOC = dict(TIPOS_DOCUMENTO)

# Causas de archivo del Decreto de archivo. Citas verificadas contra el Compendio de
# Normativa v6.0 (Feb 2026), que incluye las modificaciones de la Ley 11.097 (BO 05/01/2026),
# y contra el Reglamento del procedimiento contravencional (salidas tempranas, arts. 5-11).
# Estructura de cada tupla: (causa_txt, base_legal, circ).
MOTIVOS_ARCHIVO_TEXTO = {
    "prescripcion": (
        "prescripción de la acción contravencional",
        "Arts. 47 inc. b) y 49 de la Ley 10.326 (Código de Convivencia Ciudadana, texto "
        "según Ley 11.097): la acción contravencional se extingue por prescripción. La "
        "acción prescribe al año (1) cuando no se hubiere iniciado procedimiento y a los "
        "dos (2) años cuando éste se encontrare iniciado.",
        "habiendo transcurrido el plazo legal de prescripción sin que se hubiera dictado "
        "resolución definitiva.",
    ),
    "muerte_imputado": (
        "muerte del imputado/a",
        "Art. 47 inc. a) de la Ley 10.326: la acción contravencional se extingue por la "
        "muerte del infractor.",
        "habiéndose acreditado el fallecimiento del/la imputado/a.",
    ),
    "reparacion_danio": (
        "perdón judicial por reparación del daño",
        "Art. 25 inc. b) de la Ley 10.326: corresponde el perdón judicial —que extingue la "
        "acción contravencional (art. 47 inc. c)— cuando el/la imputado/a, sin condena "
        "contravencional en el año anterior, ofreciere reparar el daño causado. No debe "
        "confundirse con la reparación del daño como pena sustitutiva del art. 45.",
        "habiendo el/la imputado/a ofrecido reparar el daño causado y no registrando "
        "condena contravencional en el año anterior al hecho.",
    ),
    "conciliacion": (
        "perdón judicial por conciliación",
        "Art. 25 inc. c) de la Ley 10.326: corresponde el perdón judicial —que extingue la "
        "acción contravencional (art. 47 inc. c)— cuando el particular ofendido pusiere de "
        "manifiesto su voluntad de perdonar al/la infractor/a.",
        "habiendo el/la damnificado/a manifestado su voluntad de perdonar al/la infractor/a.",
    ),
    "oportunidad": (
        "perdón judicial por levedad del hecho",
        "Art. 25 inc. a) de la Ley 10.326: corresponde el perdón judicial —que extingue la "
        "acción contravencional— cuando por circunstancias especiales resulte evidente la "
        "levedad del hecho y lo excusable de los motivos determinantes revelaren la falta de "
        "toda peligrosidad en el/la imputado/a.",
        "por resultar evidente la levedad del hecho y la falta de peligrosidad del/la "
        "imputado/a, sin registrar condena contravencional en el año anterior.",
    ),
    "falta_merito": (
        "imposibilidad de acreditar el hecho o individualizar al autor",
        "Art. 6 del Reglamento del procedimiento contravencional (con remisión al art. 135 "
        "del CCC; aplicación supletoria del Código Procesal Penal, Ley 8123): el Ayudante "
        "Fiscal dispone el archivo cuando no se hubiere podido individualizar al autor o "
        "partícipe del hecho, o fuere manifiesta la imposibilidad de reunir elementos de "
        "convicción que permitan acreditarlo.",
        "por no haberse reunido elementos de convicción suficientes para acreditar el hecho "
        "investigado o individualizar a su autor.",
    ),
    "atipicidad": (
        "atipicidad — el hecho no encuadra en figura contravencional",
        "Art. 6 inc. 2 del Reglamento del procedimiento contravencional (remisión al art. 135 "
        "del CCC): el Ayudante Fiscal dispone el archivo cuando el hecho contenido en las "
        "actuaciones no encuadra en una figura contravencional.",
        "por no encuadrar el hecho investigado en ninguna figura contravencional prevista "
        "en la Ley 10.326.",
    ),
    "inimputabilidad": (
        "inimputabilidad o causa de justificación",
        "Art. 6 inc. 1 del Reglamento del procedimiento contravencional, con remisión al "
        "art. 9 de la Ley 10.326: el Ayudante Fiscal dispone el archivo cuando no se pudiere "
        "proceder por concurrir alguno de los supuestos de inimputabilidad o causas de "
        "justificación.",
        "por concurrir en el caso un supuesto de inimputabilidad o causa de justificación "
        "que impide proseguir con la acción contravencional.",
    ),
    "pena_natural": (
        "pena natural",
        "Art. 26 de la Ley 10.326 (y art. 8 del Reglamento del procedimiento contravencional): "
        "queda exento de pena quien, como consecuencia de su conducta al cometer la "
        "contravención, se infligiere graves daños en su persona o bienes, o los produjere en "
        "la persona o bienes de quien conviva o lo unan lazos de parentesco.",
        "habiéndose acreditado que el/la imputado/a sufrió, a raíz del hecho, un daño de "
        "entidad tal que torna la sanción contravencional innecesaria y desproporcionada.",
    ),
}

_NUM_LETRA = {1: "UNO", 2: "DOS", 3: "TRES", 4: "CUATRO", 5: "CINCO", 6: "SEIS",
              7: "SIETE", 8: "OCHO", 9: "NUEVE", 10: "DIEZ", 11: "ONCE", 12: "DOCE"}


def _fecha(f: datetime = None) -> str:
    f = f or datetime.now()
    return f"{f.day} de {MESES[f.month - 1]} de {f.year}"


def _norm(caso: dict) -> dict:
    """Normaliza claves del row de DB a las claves usadas aquí."""
    c = dict(caso)
    c.setdefault("tipo", c.get("tipo_infraccion", ""))
    c.setdefault("imputado", c.get("apellido_nombre", ""))
    c.setdefault("dni", c.get("persona_dni", ""))
    c.setdefault("edad", c.get("persona_edad", ""))
    c.setdefault("domicilio", c.get("persona_domicilio", "") or "")
    c.setdefault("antecedentes", c.get("antecedentes", 0))
    return c


def _firma(fiscal: str, cargo: str, unidad_label: str) -> str:
    linea = "_" * 40
    return f"\n\n                                   {linea}\n" \
           f"                                   {fiscal.upper()}\n" \
           f"                                   {cargo}\n" \
           f"                                   {unidad_label}"


def _doble_firma(imp: str, dni: str, fiscal: str) -> str:
    return ("\n\n_______________________            _______________________\n"
            f"{imp.upper()}\n"
            f"Imputado/a — D.N.I. {dni}                 {fiscal.upper()} — Fiscal Contravencional")


def _condiciones(caso: dict, extra: dict) -> list[str]:
    conds = (extra or {}).get("condiciones")
    if conds:
        return [c if isinstance(c, str) else c.get("descripcion", str(c)) for c in conds]
    return get_condiciones_para(caso.get("tipo", ""), incluir_articulo=True)


# ── Generadores de texto por tipo ─────────────────────────────────────────────

def generar_texto(tipo: str, caso: dict, fiscal_nombre: str,
                  unidad_key: str, extra: dict = None) -> tuple[str, str]:
    """Devuelve (titulo, cuerpo_editable) para el tipo de documento dado."""
    extra = extra or {}
    c = _norm(caso)
    inf = TIPOS_INFRACCION.get(c.get("tipo", ""), {})
    art = inf.get("articulo", "Código de Convivencia Ciudadana")
    art_num = art.replace(" CCC", "").strip()  # "Art. 65" sin el sufijo CCC, para no duplicarlo
    unidad = UNIDADES.get(unidad_key, UNIDADES["norte"])
    imp, dni, edad = c.get("imputado", ""), c.get("dni", ""), c.get("edad", "")
    dom = c.get("domicilio") or "el declarado en autos"
    caratula = f'"{imp.upper()} — infracción al {art}"'
    titulo = LABELS_DOC.get(tipo, "Documento contravencional")

    # ── Cédulas de citación ──────────────────────────────────────────────────
    if tipo in ("citacion_audiencia", "citacion_mediacion", "citacion_acta"):
        motivo_txt = {
            "citacion_audiencia": "comparecer a audiencia contravencional",
            "citacion_mediacion": "participar en instancia de mediación",
            "citacion_acta":      "suscribir acta de compromiso de suspensión del proceso a prueba",
        }.get(tipo, "comparecer ante esta Unidad")
        f_cit = _fecha(datetime.now() + timedelta(days=5))
        cuerpo = (
            f"Sr./Sra.: {imp}\nD.N.I.: {dni}\n\n"
            f"Por la presente se le notifica que en los autos caratulados {caratula}, "
            f"tramitados ante esta Unidad, se lo/la CITA a {motivo_txt}, a celebrarse "
            f"el día {f_cit} a las ____ hs. en la sede de este organismo sito en {unidad}.\n\n"
            "Se le hace saber que deberá concurrir munido/a de su D.N.I. y que la "
            "incomparecencia injustificada podrá motivar la continuación del proceso "
            "en su rebeldía.\n\n"
            "Ante cualquier consulta comunicarse a los teléfonos de la Unidad interviniente."
            + _firma(fiscal_nombre, "Ayudante Fiscal", unidad)
        )
        return titulo, cuerpo

    # ── Notificación de la imputación (art. 133 CCC) ──────────────────────────
    if tipo == "notificacion_imputacion":
        cuerpo = (
            f"En {unidad}, a los {_fecha()}, comparece ante esta Instancia el/la "
            f"ciudadano/a {imp}, D.N.I. N° {dni}, de {edad} años de edad, con domicilio "
            f"en {dom}.\n\n"
            f"Se le INFORMA que en las presentes actuaciones {caratula} se le atribuye un "
            f"hecho encuadrado, en principio, en el {art_num} del Código de Convivencia "
            "Ciudadana (Ley 10.326), que se investiga en esta Unidad Contravencional.\n\n"
            "Se le hace saber que tiene derecho a:\n"
            "   • Requerir copia del acta del art. 130 del CCC con la que se inició el caso;\n"
            "   • Designar un/a abogado/a de su confianza o a que se le designe uno/a de "
            "oficio en caso de carecer;\n"
            "   • Realizar una llamada telefónica y dar aviso de su situación a un familiar "
            "o persona de confianza;\n"
            "   • Permanecer en silencio, sin que ello implique presunción de culpabilidad.\n\n"
            "Oportunamente se le notificará la fecha de audiencia. A tal fin, constituye "
            "domicilio legal en [DOMICILIO LEGAL CONSTITUIDO].\n\n"
            "Previa lectura y ratificación, firma el/la compareciente. Doy fe."
            + _doble_firma(imp, dni, fiscal_nombre)
        )
        return titulo, cuerpo

    # ── Citación a testigo (lenguaje claro) ───────────────────────────────────
    if tipo == "citacion_testigo":
        cuerpo = (
            "Sr./Sra.: [NOMBRE DEL/LA TESTIGO]\nDomicilio: [DOMICILIO]\n\n"
            f"Mi nombre es {fiscal_nombre} y soy Ayudante Fiscal de la {unidad}. Lo/la "
            f"contactamos porque en las actuaciones {caratula} se lo/la menciona como "
            "testigo de un hecho contravencional (infracción a la Ley provincial N° 10.326).\n\n"
            "Por ello lo/la CITO formalmente para que se presente el día [FECHA] a las "
            f"[HORA] hs. en la sede de esta Unidad, sita en {unidad}.\n\n"
            "Le haremos preguntas sobre el hecho y usted deberá responder lo que sabe. Le "
            "recuerdo que ser testigo es una carga pública, por lo que tiene la obligación "
            "de concurrir a esta citación.\n\n"
            "Ante cualquier duda o consulta puede comunicarse con esta Unidad."
            + _firma(fiscal_nombre, "Ayudante Fiscal", unidad)
        )
        return titulo, cuerpo

    # ── Citación a persona imputada (lenguaje claro) ──────────────────────────
    if tipo == "citacion_imputado":
        cuerpo = (
            f"Sr./Sra.: {imp}\nD.N.I.: {dni}\nDomicilio: {dom}\n\n"
            f"Mi nombre es {fiscal_nombre} y soy Ayudante Fiscal de la {unidad}. Lo/la "
            f"contactamos porque en las actuaciones {caratula} existen elementos de prueba "
            "suficientes para imputarle una contravención (infracción a la Ley provincial "
            "N° 10.326).\n\n"
            "Por ello lo/la CITO formalmente para que se presente el día [FECHA] a las "
            f"[HORA] hs. en la sede de esta Unidad, sita en {unidad}.\n\n"
            "Podrá concurrir con su abogado/a de confianza. Le recuerdo que tiene la "
            "obligación de concurrir a esta citación.\n\n"
            "Ante cualquier duda o consulta puede comunicarse con esta Unidad."
            + _firma(fiscal_nombre, "Ayudante Fiscal", unidad)
        )
        return titulo, cuerpo

    # ── Resolución de perdón judicial (art. 25 CCC) ───────────────────────────
    if tipo == "perdon_judicial":
        cuerpo = (
            "RESOLUCIÓN N° [NÚMERO]\n\n"
            f"VISTOS: Las presentes actuaciones contravencionales {caratula}, siendo "
            f"imputado/a el/la Sr./Sra. {imp}, D.N.I. {dni}, por presunta infracción al "
            f"{art}.\n\n"
            "Y CONSIDERANDO:\n\n"
            f"Que el hecho atribuido a {imp} se encuadra, en principio, en el {art_num} del "
            "Código de Convivencia Ciudadana (Ley 10.326).\n\n"
            "Que conforme al art. 25 del CCC corresponde otorgar el perdón judicial cuando "
            "el/la imputado/a no registre condena contravencional en el año anterior y el "
            "hecho se evidencie como leve, sin revelar peligrosidad — circunstancias que se "
            "verifican en el presente caso.\n\n"
            "POR TODO ELLO, ESTE MINISTERIO PÚBLICO FISCAL RESUELVE:\n\n"
            f"ARTÍCULO 1°: DISPONER el perdón judicial de {imp} por la presunta infracción "
            f"al {art} y, en consecuencia, DECLARAR EXTINGUIDA la acción contravencional "
            "(arts. 25 y 47 inc. c) del CCC).\n\n"
            f"ARTÍCULO 2°: NOTIFICAR a {imp} los alcances de la presente resolución de "
            "forma clara y precisa.\n\n"
            "ARTÍCULO 3°: [En caso de secuestros, DISPONER su entrega al titular registral, "
            "remitiendo oficio a la dependencia policial correspondiente].\n\n"
            "ARTÍCULO 4°: PROTOCOLÍCESE, NOTIFÍQUESE y ARCHÍVESE."
            + _firma(fiscal_nombre, "Ayudante Fiscal", unidad)
        )
        return titulo, cuerpo

    # ── Resolución de sobreseimiento ──────────────────────────────────────────
    if tipo == "resolucion_sobreseimiento":
        cuerpo = (
            "RESOLUCIÓN N° [NÚMERO]\n\n"
            "1. IDENTIFICACIÓN DEL/LA IMPUTADO/A:\n"
            f"   {imp} — D.N.I. {dni}.\n\n"
            "2. HECHOS:\n"
            "   [DESCRIBIR el hecho atribuido: fecha, lugar y circunstancias].\n\n"
            "3. CALIFICACIÓN LEGAL:\n"
            f"   La conducta encuadra, en principio, en el {art_num} del Código de "
            "Convivencia Ciudadana (Ley 10.326).\n\n"
            "4. ELEMENTOS DE PRUEBA:\n"
            "   [DETALLAR las constancias: acta del art. 130, declaraciones, secuestros, "
            "acta de imputación del art. 133, etc.].\n\n"
            "5. FUNDAMENTOS DE LA DECISIÓN:\n"
            "   Que corresponde dictar el SOBRESEIMIENTO —y no el mero archivo— por cuanto "
            "el/la imputado/a fue formalmente imputado/a y notificado/a de sus derechos "
            "(art. 133 del CCC). Si bien el sobreseimiento no se halla específicamente "
            "regulado en el CCC, resulta aplicable por remisión supletoria al Código "
            "Procesal Penal (art. 149 del CCC).\n"
            "   [FUNDAR la causal concreta: p. ej. prescripción de la acción —art. 49 del "
            "CCC—, no habiéndose verificado causales interruptivas (art. 50 del CCC)].\n\n"
            "6. PARTE RESOLUTIVA:\n"
            f"   ARTÍCULO 1°: DECLARAR EXTINGUIDA la acción contravencional respecto de "
            f"{imp} y DICTAR EL SOBRESEIMIENTO TOTAL en la presente causa a su favor, por el "
            f"hecho calificado como {art}, conforme los arts. 348, 350 inc. 4 y 351 del "
            "C.P.P. en relación con los arts. 146, 47 inc. b) y 49 del CCC.\n"
            "   ARTÍCULO 2°: [En caso de secuestros, DISPONER su restitución al legítimo "
            "propietario].\n"
            f"   ARTÍCULO 3°: NOTIFICAR a {imp} y a las partes interesadas. PROTOCOLÍCESE."
            + _firma(fiscal_nombre, "Ayudante Fiscal", unidad)
        )
        return titulo, cuerpo

    # ── Comunicación a la víctima (lenguaje claro) ────────────────────────────
    if tipo == "comunicacion_victima":
        cuerpo = (
            "Sr./Sra.: [NOMBRE DE LA VÍCTIMA]\nDomicilio: [DOMICILIO]\n\n"
            f"Mi nombre es {fiscal_nombre} y soy Ayudante Fiscal de la {unidad}. La/lo "
            "contactamos para informarle que hemos tomado una decisión en relación con la "
            "denuncia que usted efectuó, identificada con el número [N° DE CAUSA].\n\n"
            "Le informamos, en lenguaje claro, qué se resolvió:\n"
            "   [RESUMIR la resolución: qué se decidió respecto del/la imputado/a y qué "
            "consecuencias tiene — p. ej. multa, prohibición de acercamiento por X días, "
            "curso, etc. Si corresponde, indicar qué puede hacer la víctima ante un "
            "incumplimiento].\n\n"
            "Se acompaña a la presente la resolución completa. Esta comunicación es "
            "solamente para informarle, de manera sencilla, cómo se resolvió el caso.\n\n"
            "Ante cualquier duda o consulta puede llamar a esta Unidad y consultar con el/la "
            "instructor/a interviniente.\n\n"
            "La/lo saludamos atentamente."
            + _firma(fiscal_nombre, "Ayudante Fiscal", unidad)
        )
        return titulo, cuerpo

    # ── Acta de audiencia ─────────────────────────────────────────────────────
    if tipo == "acta_audiencia":
        cuerpo = (
            f"En la sede de esta {unidad}, siendo las ____ horas del día {_fecha()}, "
            f"comparece por ante el/la Fiscal Contravencional el/la Sr./Sra. {imp}, "
            f"D.N.I. N° {dni}, en los autos caratulados {caratula}. Enterado/a del objeto "
            "del acto y de sus derechos (Art. 40 Const. Prov. Córdoba), procede a manifestar:\n\n"
            "MANIFESTACIONES DEL/LA IMPUTADO/A:\n"
            "[Transcribir aquí las manifestaciones del/la compareciente]\n\n"
            "RESOLUCIÓN DEL FISCAL:\n"
            "[Consignar aquí la resolución adoptada en la audiencia]\n\n"
            "Con lo que se da por terminado el acto, previa lectura en alta voz y "
            "ratificación, firman los intervinientes."
            + _doble_firma(imp, dni, fiscal_nombre)
        )
        return titulo, cuerpo

    # ── Dictamen de mediación ─────────────────────────────────────────────────
    if tipo == "dictamen_mediacion":
        f_aud = _fecha(datetime.now() + timedelta(days=7))
        cuerpo = (
            f"VISTOS: Las presentes actuaciones caratuladas {caratula}, iniciadas con "
            "motivo del hecho descripto en el sumario de actuaciones.\n\n"
            f"RESULTANDO: Que de las actuaciones surge que el/la imputado/a {imp}, "
            f"D.N.I. N° {dni}, de {edad} años de edad, habría incurrido en la conducta "
            f"descripta en el parte policial adjunto, encuadrable en el {art} de la Ley "
            "Provincial N° 10.326 — Código de Convivencia Ciudadana.\n\n"
            "CONSIDERANDO:\n\n"
            "I. Que el hecho imputado reviste el carácter de contravención de mínima "
            "gravedad, sin antecedentes contravencionales previos en los registros consultados.\n\n"
            "II. Que el conflicto subyacente presenta las características propias de una "
            "disputa de convivencia comunitaria, susceptible de abordaje mediante diálogo "
            "y acuerdo entre las partes.\n\n"
            "III. Que la Ley Provincial N° 10.543 establece la mediación como instancia "
            "prejudicial en causas de esta naturaleza.\n\n"
            "IV. Que esta Fiscalía propicia soluciones restaurativas y no punitivas cuando "
            "la gravedad del hecho así lo permite.\n\n"
            "DICTAMINO:\n\n"
            "Derivar las presentes actuaciones al Centro Judicial de Mediación dependiente "
            f"del Tribunal Superior de Justicia, fijándose audiencia para el día {f_aud} a "
            "las ____ hs. Notifíquese fehacientemente al/la imputado/a en el domicilio de "
            "autos, haciéndole saber que su incomparecencia injustificada habilitará la "
            "continuación del proceso contravencional."
            + _firma(fiscal_nombre, "Ayudante Fiscal", unidad)
        )
        return titulo, cuerpo

    # ── Dictamen de suspensión a prueba ───────────────────────────────────────
    if tipo == "dictamen_suspension":
        meses = (extra or {}).get("plazo_meses", 6)
        conds = _condiciones(c, extra)
        conds_str = "\n".join(f"   {i+1}. {x}" for i, x in enumerate(conds))
        cuerpo = (
            f"VISTOS: Las presentes actuaciones caratuladas {caratula}.\n\n"
            f"RESULTANDO: Que el/la imputado/a {imp}, D.N.I. N° {dni}, de {edad} años, "
            f"se encuentra imputado/a de la conducta prevista por el {art} de la Ley "
            "Provincial N° 10.326. Del análisis de las actuaciones surge que el hecho "
            "reúne los requisitos de procedencia para la suspensión del proceso a prueba "
            "(Arts. 76 a 81 CCC).\n\n"
            "CONSIDERANDO:\n\n"
            f"I. Que el/la imputado/a cuenta con {c.get('antecedentes', 0)} antecedente/s "
            "contravencional/es previo/s, lo que no obsta a la procedencia del instituto.\n\n"
            "II. Que la pena prevista habilita el otorgamiento de la suspensión a prueba.\n\n"
            "III. Que el instituto resulta proporcional a la entidad del hecho y atiende "
            "a fines de prevención especial, evitando efectos estigmatizantes.\n\n"
            "IV. Que las condiciones a imponer resultan adecuadas para reparar el daño y "
            "prevenir la reiteración.\n\n"
            "DICTAMINO:\n\n"
            f"Hacer lugar a la suspensión del proceso a prueba respecto de {imp}, "
            f"D.N.I. N° {dni}, por el término de {meses} ({_NUM_LETRA.get(meses, str(meses))}) "
            "meses, bajo las siguientes condiciones:\n\n"
            f"{conds_str}\n\n"
            "Transcurrido el período sin incumplimiento y sin nueva contravención, se "
            "extinguirá la acción y se archivarán las actuaciones. El/la imputado/a deberá "
            "presentarse dentro de los DIEZ (10) días hábiles de notificado/a para suscribir "
            "el acta de compromiso correspondiente."
            + _firma(fiscal_nombre, "Ayudante Fiscal", unidad)
        )
        return titulo, cuerpo

    # ── Acta de compromiso ────────────────────────────────────────────────────
    if tipo == "acta_compromiso":
        meses = (extra or {}).get("plazo_meses", 6)
        conds = _condiciones(c, extra)
        conds_str = "\n".join(f"   {i+1}. {x}" for i, x in enumerate(conds))
        cuerpo = (
            f"En la ciudad de Córdoba, a los {_fecha()}, comparece ante esta Unidad el/la "
            f"Sr./Sra. {imp}, D.N.I. N° {dni}, de {edad} años de edad, con domicilio en "
            f"{dom}, en los autos caratulados {caratula}.\n\n"
            "OBJETO: Por la presente, el/la compareciente presta su conformidad con la "
            f"suspensión del proceso a prueba otorgada por esta Fiscalía por el término de "
            f"{meses} ({_NUM_LETRA.get(meses, str(meses))}) meses a partir de la fecha, "
            "comprometiéndose al cumplimiento de las siguientes condiciones:\n\n"
            f"{conds_str}\n\n"
            "El/la compareciente declara conocer y aceptar las condiciones precedentes, "
            "siendo informado/a de que el incumplimiento de cualquiera de ellas habilitará "
            "la revocación de la suspensión y la continuación del proceso contravencional.\n\n"
            "En prueba de conformidad se firma la presente en dos ejemplares de un mismo "
            "tenor y a un solo efecto."
            + _doble_firma(imp, dni, fiscal_nombre)
        )
        return titulo, cuerpo

    # ── Decreto de suspensión a prueba ────────────────────────────────────────
    if tipo == "decreto_suspension":
        meses = (extra or {}).get("plazo_meses", 6)
        conds = _condiciones(c, extra)
        conds_str = "\n".join(f"   {i+1}. {x}" for i, x in enumerate(conds))
        f_ini = _fecha()
        f_fin = _fecha(datetime.now() + timedelta(days=meses * 30))
        cuerpo = (
            f"VISTOS los autos caratulados {caratula}, tramitados ante esta {unidad}, en "
            f"los que como imputado/a figura {imp}, D.N.I. N° {dni}.\n\n"
            "CONSIDERANDO: Que habiéndose celebrado audiencia con el/la imputado/a, quien "
            "prestó conformidad con la propuesta de suspensión del proceso contravencional "
            "a prueba (Arts. 76 a 81 Ley 10.326), y habiendo acordado las condiciones que "
            "se detallan, corresponde hacer lugar a la suspensión.\n\n"
            "ESTE MINISTERIO PÚBLICO FISCAL RESUELVE:\n\n"
            f"ARTÍCULO 1°: SUSPENDER el proceso contravencional a prueba seguido contra "
            f"{imp}, D.N.I. N° {dni}, por el término de {meses} "
            f"({_NUM_LETRA.get(meses, str(meses))}) meses, desde el {f_ini} hasta el {f_fin}.\n\n"
            "ARTÍCULO 2°: Imponer al/la imputado/a el cumplimiento de las siguientes "
            "condiciones durante el plazo de la suspensión:\n\n"
            f"{conds_str}\n\n"
            "ARTÍCULO 3°: Hacer saber que el incumplimiento de cualquiera de las condiciones "
            "podrá determinar la revocación de la suspensión y la continuación del proceso "
            "(Art. 80 Ley 10.326).\n\n"
            "ARTÍCULO 4°: NOTIFÍQUESE fehacientemente. Líbrense los oficios correspondientes. "
            "Agréguese al legajo fiscal. REGÍSTRESE."
            + _firma(fiscal_nombre, "Fiscal Contravencional", unidad)
        )
        return titulo, cuerpo

    # ── Acta de medidas restrictivas ──────────────────────────────────────────
    if tipo == "acta_restriccion":
        vic = (extra or {}).get("victima_nombre") or "[NOMBRE DE LA VÍCTIMA]"
        dom_vic = (extra or {}).get("victima_domicilio") or "[DOMICILIO DE LA VÍCTIMA]"
        # Art. 135 bis CCC: ninguna medida cautelar puede superar los 60 días.
        plazo = min(int((extra or {}).get("plazo_dias", 60)), 60)
        cuerpo = (
            f"En la localidad sede de esta {unidad}, a los {_fecha()}, en el marco de los "
            f"autos caratulados {caratula}.\n\n"
            "VISTOS Y CONSIDERANDO: Que de las constancias de autos surge la necesidad de "
            "adoptar medidas urgentes de protección a favor de la víctima, a fin de hacer "
            "cesar los efectos de la contravención y prevenir su reiteración.\n\n"
            "Que el Art. 135 bis de la Ley 10.326 (Código de Convivencia Ciudadana) faculta "
            "a la Autoridad de Juzgamiento a ordenar, por resolución fundada y dictada "
            "inaudita parte, medidas cautelares y de protección por el tiempo estrictamente "
            "necesario, sin que su duración pueda superar los sesenta (60) días.\n\n"
            "POR ELLO, ESTE MINISTERIO PÚBLICO FISCAL RESUELVE establecer respecto de "
            f"{imp} las siguientes medidas (suprimir las que no correspondan):\n\n"
            "   a) PROHIBICIÓN DE ACERCAMIENTO al lugar de residencia, trabajo, estudio, "
            f"esparcimiento o de habitual concurrencia de {vic}, con domicilio en {dom_vic}, "
            "a una distancia no menor a [DISTANCIA] metros.\n"
            f"   b) PROHIBICIÓN DE COMUNICACIÓN Y CONTACTO con {vic} y/o los testigos por "
            "cualquier medio, incluso telefónico, digital, telemático, a través de redes "
            "sociales o por intermedio de terceros.\n"
            "   c) PROHIBICIÓN DE CONCURRENCIA: se prohíbe asistir, ingresar o permanecer "
            "en [LUGAR DETERMINADO].\n"
            "   d) REGLAS DE CONDUCTA: [DETALLAR toda otra medida adecuada para hacer cesar "
            "los efectos de la contravención].\n\n"
            f"PLAZO: Las medidas se disponen por el término de {plazo} días corridos desde la "
            "presente notificación —que en ningún caso podrá superar los sesenta (60) días, "
            "conforme el Art. 135 bis del CCC—, hasta que tome intervención la Autoridad de "
            "Juzgamiento competente.\n\n"
            "Notifíquese al/la imputado/a, haciéndole saber que el incumplimiento de las "
            "presentes medidas podrá motivar su inmediata elevación a la Autoridad de "
            "Juzgamiento, la adopción de medidas más gravosas y la eventual configuración del "
            "delito de desobediencia a una orden judicial (art. 239 del Código Penal)."
            + _doble_firma(imp, dni, fiscal_nombre)
        )
        return titulo, cuerpo

    # ── Requerimiento de apertura ─────────────────────────────────────────────
    if tipo == "requerimiento":
        agr = []
        if c.get("antecedentes", 0) >= 2:
            agr.append(f"reincidencia comprobada ({c['antecedentes']} causas previas)")
        if extra.get("lesiones") or caso.get("hay_lesiones"):
            agr.append("lesiones físicas constatadas")
        if extra.get("resistencia") or caso.get("resistencia_autoridad"):
            agr.append("resistencia o desobediencia a la autoridad")
        agr_str = " / ".join(agr) if agr else "gravedad objetiva del hecho"
        desc = caso.get("descripcion") or caso.get("descripcion_hecho") or "—"
        cuerpo = (
            "AL SR./SRA. JUEZ/A CONTRAVENCIONAL:\n\n"
            f"El/la Ayudante Fiscal que suscribe, {fiscal_nombre}, en la causa caratulada "
            f"{caratula}, dice:\n\n"
            "I. HECHO IMPUTADO\n\n"
            f"Se le imputa a {imp}, D.N.I. N° {dni}, de {edad} años de edad, haber incurrido "
            f"en la conducta encuadrable en el {art} de la Ley Provincial N° 10.326.\n\n"
            f"Descripción del hecho: {desc}\n\n"
            "II. FUNDAMENTOS DE LA APERTURA\n\n"
            "Esta Fiscalía considera que el caso NO resulta procedente para las vías "
            "alternativas (mediación o suspensión a prueba), en atención a:\n\n"
            f"   a) {agr_str.capitalize()}.\n"
            "   b) La naturaleza del hecho requiere investigación y debate oral.\n"
            "   c) La clasificación de la causa arroja CARRIL ROJO conforme a los parámetros "
            "del triaje fiscal.\n\n"
            "III. PETITORIO\n\n"
            "Por lo expuesto, esta Fiscalía REQUIERE:\n\n"
            "   1. La apertura formal del proceso contravencional.\n"
            f"   2. Se convoque a {imp} a audiencia (Art. 56 y ss. CCC).\n"
            "   3. Se adopten las medidas cautelares que el Tribunal considere pertinentes."
            + _firma(fiscal_nombre, "Ayudante Fiscal", unidad)
        )
        return titulo, cuerpo

    # ── Decreto de archivo ────────────────────────────────────────────────────
    if tipo == "decreto_archivo":
        motivo = (extra or {}).get("motivo", "falta_merito")
        causa_txt, base_legal, circ = MOTIVOS_ARCHIVO_TEXTO.get(
            motivo, ("causa de archivo debidamente fundada",
                     (extra or {}).get("fundamento", "conforme las constancias de autos."), ""))
        cuerpo = (
            f"VISTOS: Las actuaciones contravencionales caratuladas {caratula}, tramitadas "
            f"ante esta {unidad}.\n\n"
            "CONSIDERANDO:\n\n"
            f"Que habiéndose analizado las presentes actuaciones, se advierte que corresponde "
            f"disponer su archivo por la siguiente causa: {causa_txt}.\n\n"
            f"{base_legal}\n\n"
            f"Que en el caso concreto ello se verifica {circ}\n\n"
            "POR TODO ELLO, ESTE MINISTERIO PÚBLICO FISCAL RESUELVE:\n\n"
            f"ARTÍCULO 1°: ARCHIVAR las presentes actuaciones contravencionales caratuladas "
            f'"{imp.upper()}", por {causa_txt}.\n\n'
            "ARTÍCULO 2°: NOTIFÍQUESE a las partes interesadas. Déjese constancia en el "
            "registro respectivo. REGÍSTRESE y archívese."
            + _firma(fiscal_nombre, "Fiscal Contravencional", unidad)
        )
        return titulo, cuerpo

    # ── Certificado de cumplimiento ───────────────────────────────────────────
    if tipo == "certificado_cumplimiento":
        seg = (extra or {}).get("seguimiento", {}) or {}
        conds = [x for x in ((extra or {}).get("condiciones", []))
                 if (x.get("estado") == "cumplido" if isinstance(x, dict) else True)]
        conds_str = "\n".join(
            f"   {i+1}. {x.get('descripcion','') if isinstance(x, dict) else x}"
            for i, x in enumerate(conds)) or "   (Detallar las condiciones cumplidas)"
        cuerpo = (
            f"Imputado/a: {imp}\nD.N.I.: {dni}\nInfracción: {inf.get('label', c.get('tipo',''))}\n\n"
            f"El/la Fiscal Contravencional que suscribe CERTIFICA que en los autos caratulados "
            f"{caratula}, tramitados ante esta {unidad}, el/la imputado/a ha dado cumplimiento "
            "ÍNTEGRO Y SATISFACTORIO a la totalidad de las condiciones impuestas en el marco "
            "de la suspensión del proceso contravencional a prueba (Arts. 76 a 81 Ley 10.326).\n\n"
            "CONDICIONES CUMPLIDAS:\n\n"
            f"{conds_str}\n\n"
            f"La suspensión se otorgó con fecha {seg.get('fecha_inicio','____')} y concluyó el "
            f"{seg.get('fecha_fin','____')}. Habiendo el/la imputado/a cumplido satisfactoriamente "
            "todas las condiciones, corresponde tener por EXTINGUIDA la acción contravencional "
            "(Art. 81 Ley 10.326).\n\n"
            "*** CONDICIONES CUMPLIDAS — PROCESO EXTINGUIDO ***"
            + _firma(fiscal_nombre, "Fiscal Contravencional", unidad)
        )
        return titulo, cuerpo

    # ── Informe de incumplimiento ─────────────────────────────────────────────
    if tipo == "informe_incumplimiento":
        seg = (extra or {}).get("seguimiento", {}) or {}
        conds_inc = (extra or {}).get("condiciones_inc", [])
        conds_str = "\n".join(
            f"   {i+1}. {x.get('descripcion','') if isinstance(x, dict) else x}"
            for i, x in enumerate(conds_inc)) or "   (Detallar las condiciones incumplidas)"
        cuerpo = (
            f"OBJETO: La presente tiene por objeto informar el incumplimiento de las "
            f"condiciones impuestas en el marco de la suspensión del proceso a prueba otorgada "
            f"a {imp}, D.N.I. N° {dni}, en los autos {caratula}.\n\n"
            f"ANTECEDENTES: Que con fecha {seg.get('fecha_inicio','____')} se otorgó la "
            f"suspensión del proceso a prueba, venciendo el período el {seg.get('fecha_fin','____')}. "
            "El/la imputado/a suscribió el acta de compromiso comprometiéndose al cumplimiento "
            "de las condiciones establecidas.\n\n"
            "CONDICIONES INCUMPLIDAS:\n\n"
            f"{conds_str}\n\n"
            "CONCLUSIÓN: En virtud del incumplimiento acreditado, esta Fiscalía concluye que "
            "el/la imputado/a no ha dado cumplimiento a las condiciones impuestas, lo que "
            "habilita la revocación de la suspensión del proceso a prueba y la continuación "
            "del proceso contravencional. Por lo expuesto, se eleva el presente informe a "
            "efectos de que se adopten las medidas procesales que correspondan."
            + _firma(fiscal_nombre, "Fiscal Contravencional", unidad)
        )
        return titulo, cuerpo

    # ── Oficio al Polo de la Mujer ────────────────────────────────────────────
    if tipo == "oficio_polo":
        vic = (extra or {}).get("victima_nombre") or "[NOMBRE DE LA VÍCTIMA]"
        resena = (extra or {}).get("resena") or caso.get("descripcion") or "Según constancias de autos."
        cuerpo = (
            "A la Dirección del Polo Integral de la Mujer / Centro de Asistencia a Víctimas "
            "de Violencia de Género\nS / D\n\n"
            f"En el marco de las actuaciones contravencionales caratuladas {caratula}, que se "
            f"tramitan ante esta {unidad}, se libra el presente a fin de PONER EN SU "
            f"CONOCIMIENTO que en fecha {_fecha()} se formalizaron actuaciones en las que "
            f"resulta presunta damnificada la Sra. {vic}.\n\n"
            f"Reseña de los hechos: {resena}\n\n"
            "El motivo del presente es a los fines de que ese organismo adopte las medidas de "
            f"contención y asistencia que crea pertinentes en orden a la problemática y "
            f"necesidades de {vic}, presunta víctima en autos.\n\n"
            "Asimismo, se solicita que en caso de que la persona concurra a ese Centro, se "
            "informe a esta Fiscalía a efectos de coordinar las medidas de protección que "
            "correspondan."
            + _firma(fiscal_nombre, "Fiscal Contravencional", unidad)
        )
        return titulo, cuerpo

    # ── Oficio informe socioambiental ─────────────────────────────────────────
    if tipo == "oficio_socioambiental":
        mun = (extra or {}).get("municipio") or "esta ciudad"
        cuerpo = (
            f"Sra. Asistente Social\nÁrea de Desarrollo Social — Municipalidad de {mun}\nS / D\n\n"
            f"En relación a los autos caratulados {caratula}, que se tramitan ante esta {unidad}, "
            "se dispuso librar el presente a fin de solicitarle que tenga a bien realizar un "
            f"INFORME SOCIOAMBIENTAL en el domicilio habitado por {imp}, ubicado en {dom}.\n\n"
            "Para lo cual se requiere que el informe atienda los siguientes puntos:\n\n"
            "   1. Diagnóstico social a fin de determinar la situación familiar.\n"
            "   2. Configuración vincular del grupo familiar.\n"
            "   3. Caracterización de los vínculos e interacciones entre sus miembros.\n"
            "   4. Presencia y/o ausencia de situación de vulnerabilidad y factores protectores.\n"
            "   5. Evaluación del cumplimiento de las condiciones impuestas en el marco de la "
            "suspensión contravencional a prueba.\n"
            "   6. Todo otro dato de interés que se estime útil a los fines del seguimiento.\n\n"
            "Se solicita que, de existir informes anteriores sobre el/la imputado/a o su grupo "
            "familiar, sean valorados al elaborar el informe. Tenga a bien remitir lo actuado a "
            "la sede de este organismo a la brevedad posible."
            + _firma(fiscal_nombre, "Fiscal Contravencional", unidad)
        )
        return titulo, cuerpo

    # ── Oficio valoración psicológica ─────────────────────────────────────────
    if tipo == "oficio_valoracion":
        hosp = (extra or {}).get("hospital") or "[HOSPITAL / CENTRO DE SALUD]"
        cuerpo = (
            f"Sr./Sra. Director/a — {hosp}\nS / D\n\n"
            f"En el marco de los autos caratulados {caratula}, tramitados ante esta {unidad}, "
            f"y por intermedio de quien corresponda, se solicita a ese nosocomio que otorgue "
            f"turno a/la Sr./Sra. {imp} a los fines de que personal a su cargo realice sobre "
            "dicha persona una valoración del estado de salud mental, como condición de la "
            "suspensión del proceso contravencional a prueba.\n\n"
            "En caso de no contar con personal en el área de salud mental, informe a partir de "
            "qué fecha retornaría la actividad, o indique el centro de salud más apropiado.\n\n"
            f"El resultado de la valoración deberá ser remitido a la sede de esta {unidad} a la "
            "brevedad posible, a efectos de su incorporación al expediente y control del "
            "cumplimiento de condiciones."
            + _firma(fiscal_nombre, "Fiscal Contravencional", unidad)
        )
        return titulo, cuerpo

    # Fallback
    return titulo, ("[Documento sin plantilla específica. Redacte aquí el contenido.]"
                    + _firma(fiscal_nombre, "Fiscal Contravencional", unidad))
