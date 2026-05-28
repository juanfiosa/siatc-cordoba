"""
Generador de documentos legales contravencionales.
Produce documentos en formato de la fiscalía cordobesa.
"""

from datetime import datetime, timedelta
import random
from data_cordoba import TIPOS_INFRACCION, CONDICIONES_SUSPENSION, UNIDADES


def _fecha_formal(fecha: datetime = None) -> str:
    meses = ["enero", "febrero", "marzo", "abril", "mayo", "junio",
             "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre"]
    f = fecha or datetime.now()
    return f"{f.day} de {meses[f.month - 1]} de {f.year}"


def _numero_expediente(numero_caso: str) -> str:
    return numero_caso.replace("UC", "EXP-UC").replace("-", "/")


def _get_condiciones(tipo_infraccion: str, categoria: str) -> list:
    if tipo_infraccion == "transito_alcoholemia":
        return CONDICIONES_SUSPENSION["transito_alcoholemia"]
    elif categoria == "Tránsito":
        return CONDICIONES_SUSPENSION["transito"]
    elif categoria == "Convivencia":
        return CONDICIONES_SUSPENSION["convivencia"]
    elif categoria == "Comercio":
        return CONDICIONES_SUSPENSION["comercio"]
    elif categoria == "Integridad":
        return CONDICIONES_SUSPENSION["integridad"]
    elif categoria == "Espacio Público":
        return CONDICIONES_SUSPENSION["espacio_publico"]
    return CONDICIONES_SUSPENSION["convivencia"]


def generar_dictamen_mediacion(caso: dict, clasificacion: dict, fiscal_nombre: str, unidad_key: str) -> str:
    infraccion = TIPOS_INFRACCION.get(caso["tipo"], {})
    unidad = UNIDADES.get(unidad_key, UNIDADES["norte"])
    fecha = _fecha_formal()
    fecha_audiencia = _fecha_formal(datetime.now() + timedelta(days=7))
    hora_audiencia = "10:00"

    return f"""
MINISTERIO PÚBLICO FISCAL DE LA PROVINCIA DE CÓRDOBA
{unidad.upper()}

─────────────────────────────────────────────────────────────────
DICTAMEN DE DERIVACIÓN A INSTANCIA DE MEDIACIÓN
─────────────────────────────────────────────────────────────────

Expediente N°: {_numero_expediente(caso['numero'])}
Córdoba, {fecha}

VISTOS: Las presentes actuaciones caratuladas: "{caso['imputado'].upper()} —
infracción al {infraccion.get('articulo', 'Código de Convivencia Ciudadana')}",
iniciadas con motivo del hecho descripto en el sumario de actuaciones.

RESULTANDO: Que de las actuaciones labradas surge que el/la imputado/a
{caso['imputado']}, D.N.I. N° {caso['dni']}, de {caso['edad']} años de edad,
habría incurrido en la conducta descripta en el parte policial adjunto,
encuadrable en los términos del {infraccion.get('articulo', 'artículo pertinente')}
de la Ley Provincial N° 10.326 — Código de Convivencia Ciudadana.

CONSIDERANDO:

I. Que el hecho que se le imputa al/la encausado/a reviste el carácter de
contravención de mínima gravedad, sin que se registren antecedentes
contravencionales previos en los registros consultados.

II. Que el conflicto subyacente presenta las características propias de
una disputa de convivencia comunitaria, siendo susceptible de abordaje
mediante instancias de diálogo y acuerdo entre las partes.

III. Que la Ley Provincial N° 10.543 establece la mediación como instancia
prejudicial obligatoria en causas de esta naturaleza, constituyendo una
herramienta eficaz para la resolución del conflicto primario sin necesidad
de avanzar en el proceso contravencional pleno.

IV. Que esta Fiscalía propicia una política de gestión de conflictos que
priorice soluciones restaurativas y no punitivas en los casos en que la
gravedad del hecho así lo permita.

DICTAMINO:

Derivar las presentes actuaciones al Centro Judicial de Mediación dependiente
del Tribunal Superior de Justicia de la Provincia de Córdoba, fijándose
audiencia de mediación para el día {fecha_audiencia} a las {hora_audiencia} hs.

Notifíquese fehacientemente al/la imputado/a {caso['imputado']} en el domicilio
que surge de las actuaciones, haciéndole saber que su incomparecencia injustificada
a la audiencia de mediación habilitará la continuación del proceso contravencional.

{"—" * 64}
{fiscal_nombre.upper()}
AYUDANTE FISCAL
{unidad}
""".strip()


def generar_dictamen_suspension(caso: dict, clasificacion: dict, fiscal_nombre: str, unidad_key: str) -> str:
    infraccion = TIPOS_INFRACCION.get(caso["tipo"], {})
    categoria = clasificacion.get("categoria", "Tránsito")
    condiciones = _get_condiciones(caso["tipo"], categoria)
    unidad = UNIDADES.get(unidad_key, UNIDADES["norte"])
    fecha = _fecha_formal()
    meses_prueba = 6 if clasificacion["score"] <= 2.5 else 12

    condiciones_str = "\n".join([f"   {i+1}. {c}" for i, c in enumerate(condiciones)])

    return f"""
MINISTERIO PÚBLICO FISCAL DE LA PROVINCIA DE CÓRDOBA
{unidad.upper()}

─────────────────────────────────────────────────────────────────
DICTAMEN DE SUSPENSIÓN DEL PROCESO A PRUEBA
─────────────────────────────────────────────────────────────────

Expediente N°: {_numero_expediente(caso['numero'])}
Córdoba, {fecha}

VISTOS: Las presentes actuaciones caratuladas: "{caso['imputado'].upper()} —
infracción al {infraccion.get('articulo', 'Código de Convivencia Ciudadana')}".

RESULTANDO: Que el/la imputado/a {caso['imputado']}, D.N.I. N° {caso['dni']},
de {caso['edad']} años, se encuentra imputado/a de haber incurrido en la conducta
prevista por el {infraccion.get('articulo', 'artículo pertinente')} de la Ley
Provincial N° 10.326. Del análisis de las actuaciones y de los antecedentes del
encausado/a surge que el hecho imputado reúne los requisitos de procedencia
establecidos en los arts. 101 y ss. del Código de Convivencia Ciudadana para
la suspensión del proceso a prueba.

CONSIDERANDO:

I. Que el imputado/a cuenta con {caso['antecedentes']} antecedente/s
contravencional/es previo/s, lo que no obsta, en el caso concreto, a la
procedencia del instituto peticionado.

II. Que la infracción imputada tiene una pena prevista que habilita el otorgamiento
de la suspensión del proceso a prueba conforme al ordenamiento contravencional vigente.

III. Que la aplicación de este instituto resulta proporcional a la entidad
del hecho y contribuye a los fines de prevención especial, evitando
los efectos estigmatizantes de una condena formal.

IV. Que las condiciones que se impondrán al/la imputado/a resultan adecuadas
para reparar el daño producido y prevenir la reiteración de conductas similares.

DICTAMINO:

Hacer lugar a la suspensión del proceso a prueba respecto de {caso['imputado']},
D.N.I. N° {caso['dni']}, por el término de {meses_prueba} ({"SEIS" if meses_prueba == 6 else "DOCE"})
meses, bajo las siguientes condiciones:

{condiciones_str}

Transcurrido el período de prueba sin incumplimiento de las condiciones impuestas
y sin haber incurrido en nueva contravención, se extinguirá la acción contravencional
y se archivarán las presentes actuaciones.

El/la imputado/a deberá presentarse ante esta Unidad dentro de los DIEZ (10) días
hábiles de notificado/a para suscribir el acta de compromiso correspondiente.

{"—" * 64}
{fiscal_nombre.upper()}
AYUDANTE FISCAL
{unidad}
""".strip()


def generar_citacion(caso: dict, fiscal_nombre: str, unidad_key: str, motivo: str = "audiencia") -> str:
    infraccion = TIPOS_INFRACCION.get(caso["tipo"], {})
    unidad = UNIDADES.get(unidad_key, UNIDADES["norte"])
    fecha = _fecha_formal()
    fecha_citacion = _fecha_formal(datetime.now() + timedelta(days=5))
    hora = "09:00"

    motivo_texto = {
        "audiencia": "comparecer a audiencia contravencional",
        "mediacion": "participar en instancia de mediación",
        "acta": "suscribir acta de compromiso de suspensión del proceso a prueba",
    }.get(motivo, "comparecer ante esta Unidad")

    return f"""
MINISTERIO PÚBLICO FISCAL DE LA PROVINCIA DE CÓRDOBA
{unidad.upper()}

─────────────────────────────────────────────────────────────────
CÉDULA DE NOTIFICACIÓN / CITACIÓN
─────────────────────────────────────────────────────────────────

Expediente N°: {_numero_expediente(caso['numero'])}
Córdoba, {fecha}

Sr./Sra.: {caso['imputado']}
D.N.I.: {caso['dni']}

Por la presente se le notifica que en los autos caratulados
"{caso['imputado'].upper()} — infracción al {infraccion.get('articulo', 'Código de Convivencia Ciudadana')}",
Expte. N° {_numero_expediente(caso['numero'])}, tramitados ante esta Unidad,
se lo/la CITA a {motivo_texto} a celebrarse el día {fecha_citacion} a
las {hora} hs. en la sede de este organismo sita en:

   {unidad}

Se le hace saber que deberá concurrir munido/a de D.N.I. y que la
incomparecencia injustificada podrá motivar la continuación del proceso
en su rebeldía.

Ante cualquier consulta comunicarse al: (0351) 4335361 (Unidad Norte) /
4466707 (Unidad Sur).

{"—" * 64}
{fiscal_nombre.upper()}
AYUDANTE FISCAL
{unidad}
""".strip()


def generar_requerimiento_apertura(caso: dict, clasificacion: dict, fiscal_nombre: str, unidad_key: str) -> str:
    """
    Requerimiento Fiscal de Apertura del Proceso Contravencional.
    Aplicable a causas en carril rojo (proceso pleno).
    """
    infraccion = TIPOS_INFRACCION.get(caso["tipo"], {})
    unidad = UNIDADES.get(unidad_key, UNIDADES["norte"])
    fecha = _fecha_formal()

    agravantes = []
    if caso.get("antecedentes", 0) >= 2:
        agravantes.append(f"reincidencia comprobada ({caso['antecedentes']} causas previas)")
    if caso.get("lesiones"):
        agravantes.append("lesiones físicas constatadas")
    if caso.get("resistencia"):
        agravantes.append("resistencia o desobediencia a la autoridad policial")
    agravantes_str = " / ".join(agravantes) if agravantes else "gravedad objetiva del hecho"

    return f"""
MINISTERIO PÚBLICO FISCAL DE LA PROVINCIA DE CÓRDOBA
{unidad.upper()}

─────────────────────────────────────────────────────────────────
REQUERIMIENTO FISCAL DE APERTURA DEL PROCESO CONTRAVENCIONAL
─────────────────────────────────────────────────────────────────

Expediente N°: {_numero_expediente(caso['numero'])}
Córdoba, {fecha}

AL SR./SRA. JUEZ/A CONTRAVENCIONAL:

El/la Ayudante Fiscal que suscribe, {fiscal_nombre}, a cargo de la Unidad
Contravencional {unidad_key.capitalize()}, en la causa caratulada:
"{caso['imputado'].upper()} — infracción al {infraccion.get('articulo', 'Código de Convivencia Ciudadana')}",
Expte. N° {_numero_expediente(caso['numero'])}, dice:

I. HECHO IMPUTADO

Se le imputa a {caso['imputado']}, D.N.I. N° {caso['dni']}, de {caso['edad']} años de
edad, haber incurrido en la conducta encuadrable en el {infraccion.get('articulo', 'artículo pertinente')}
de la Ley Provincial N° 10.326 (Código de Convivencia Ciudadana de Córdoba).

Descripción del hecho: {caso.get('descripcion', '—')}

II. FUNDAMENTOS DE LA APERTURA

Esta Fiscalía considera que el presente caso NO resulta procedente para las vías
alternativas (mediación o suspensión del proceso a prueba), en atención a:

  a) {agravantes_str.capitalize()}.
  b) La naturaleza del hecho imputado requiere una investigación y debate oral.
  c) El resultado del sistema de triaje automatizado SIATC arroja CARRIL ROJO
     (score: {clasificacion.get('score', '—')}) conforme a los parámetros de la
     Resolución General de este Ministerio.

III. PETITORIO

Por los fundamentos expuestos, esta Fiscalía REQUIERE:

  1. La apertura formal del proceso contravencional.
  2. Se convoque a {caso['imputado']} a audiencia en los términos del art. 56
     y ss. del Código de Convivencia Ciudadana.
  3. Se adopten las medidas cautelares que el Tribunal considere pertinentes.

{"—" * 64}
{fiscal_nombre.upper()}
AYUDANTE FISCAL
{unidad}
""".strip()


def generar_resumen_ejecutivo(caso: dict, clasificacion: dict) -> str:
    infraccion = TIPOS_INFRACCION.get(caso["tipo"], {})
    t = clasificacion

    return f"""
╔══════════════════════════════════════════════════════════════╗
║  RESUMEN EJECUTIVO — CLASIFICACIÓN AUTOMÁTICA DEL CASO      ║
╚══════════════════════════════════════════════════════════════╝

N° de Caso : {caso['numero']}
Imputado/a : {caso['imputado']} (DNI {caso['dni']}, {caso['edad']} años)
Infracción : {infraccion.get('label', caso['tipo'])}
Normativa  : {infraccion.get('articulo', '—')}
Antecedentes: {caso['antecedentes']}

──────────────────────────────────────────────────────────────
CLASIFICACIÓN: {t['icono']} CARRIL {t['carril'].upper()}
ACCIÓN:        {t['accion']}
──────────────────────────────────────────────────────────────

Fundamentación:
{chr(10).join(f"  • {f}" for f in t['fundamento'])}

{t['descripcion']}
""".strip()
