# -*- coding: utf-8 -*-
"""
Generador de PDF institucional - SIATC
Ministerio Publico Fiscal - Cordoba
"""

from fpdf import FPDF
from datetime import datetime, timedelta
from io import BytesIO
import os
from data_cordoba import TIPOS_INFRACCION, UNIDADES, CONDICIONES_SUSPENSION

# Fuente TTF desactivada: fonttools crash en Python 3.14
_USE_TTF = False

def _s(text):
    # Sanitiza caracteres fuera de latin-1 para fuentes core de PDF.
    return (str(text)
            .replace("—", "-").replace("–", "-")
            .replace("‘", "'").replace("’", "'")
            .replace("“", '"').replace("”", '"')
            .replace("…", "...").replace("·", ".")
            .replace("•", "*"))

# -- Colores institucionales ---------------------------------------------------
AZUL_MPF   = (30,  47,  94)
AZUL_CLARO = (46,  80, 144)
GRIS_LINEA = (180, 180, 180)
NEGRO      = (0,   0,   0)
BLANCO     = (255, 255, 255)
GRIS_TEXTO = (60,  60,  60)

MESES = ["enero","febrero","marzo","abril","mayo","junio",
         "julio","agosto","septiembre","octubre","noviembre","diciembre"]

def _fecha_formal(fecha=None):
    f = fecha or datetime.now()
    return f"{f.day} de {MESES[f.month-1]} de {f.year}"

def _get_condiciones(tipo, categoria):
    if tipo == "transito_alcoholemia":
        return CONDICIONES_SUSPENSION["transito_alcoholemia"]
    elif categoria == "Tránsito":
        return CONDICIONES_SUSPENSION["transito"]
    elif categoria == "Convivencia":
        return CONDICIONES_SUSPENSION["convivencia"]
    elif categoria == "Comercio":
        return CONDICIONES_SUSPENSION["comercio"]
    elif categoria == "Integridad":
        return CONDICIONES_SUSPENSION["integridad"]
    return CONDICIONES_SUSPENSION["convivencia"]


# -- Clase base para documentos MPF -------------------------------------------

class PDFMPFBase(FPDF):
    def __init__(self, unidad_key="norte"):
        super().__init__(orientation="P", unit="mm", format="A4")
        self.unidad_key = unidad_key
        self.unidad_str = UNIDADES.get(unidad_key, UNIDADES["norte"])
        self.set_margins(20, 15, 20)
        self.set_auto_page_break(auto=True, margin=25)
        self._fn = "Helvetica"   # latin-1 core font (TTF disabled)

    def _sf(self, style="", size=9):
        self.set_font(self._fn, style, size)

    # -- Encabezado de pagina --------------------------------------------------
    def header(self):
        self.set_fill_color(*AZUL_MPF)
        self.rect(0, 0, 210, 22, style="F")

        self.set_fill_color(*AZUL_CLARO)
        self.rect(8, 3, 13, 16, style="F")
        self.set_xy(8, 6)
        self._sf("B", 7)
        self.set_text_color(*BLANCO)
        self.cell(13, 5, "MPF", align="C", ln=True)
        self.set_x(8)
        self._sf("", 5)
        self.cell(13, 4, "CORDOBA", align="C")

        self.set_xy(24, 4)
        self._sf("B", 9)
        self.cell(0, 5, "MINISTERIO PUBLICO FISCAL DE LA PROVINCIA DE CORDOBA", ln=True)
        self.set_x(24)
        self._sf("", 8)
        self.cell(0, 4, _s(self.unidad_str), ln=True)

        self.set_draw_color(*AZUL_CLARO)
        self.set_line_width(0.6)
        self.line(0, 22, 210, 22)
        self.set_text_color(*NEGRO)
        self.ln(8)

    # -- Pie de pagina ---------------------------------------------------------
    def footer(self):
        self.set_y(-18)
        self.set_draw_color(*GRIS_LINEA)
        self.set_line_width(0.3)
        self.line(20, self.get_y(), 190, self.get_y())
        self.ln(1)
        self._sf("I", 7)
        self.set_text_color(*GRIS_TEXTO)
        self.cell(0, 4, "Sistema Inteligente de Apoyo al Trabajo Contravencional - SIATC | MPF Cordoba",
                  align="C", ln=True)
        self.cell(0, 4, f"Pagina {self.page_no()} / {{nb}}", align="C")

    # -- Helpers de contenido --------------------------------------------------
    def titulo_documento(self, texto):
        self._sf("B", 12)
        self.set_text_color(*AZUL_MPF)
        self.set_fill_color(235, 240, 250)
        self.cell(0, 9, _s(texto).upper(), align="C", fill=True, ln=True)
        self.set_draw_color(*AZUL_CLARO)
        self.set_line_width(0.5)
        self.line(20, self.get_y(), 190, self.get_y())
        self.ln(5)
        self.set_text_color(*NEGRO)

    def metadatos(self, numero, fecha):
        self._sf("B", 9)
        self.set_fill_color(245, 246, 250)
        self.set_draw_color(*GRIS_LINEA)
        y0 = self.get_y()
        self.rect(20, y0, 170, 10, style="FD")
        self.set_xy(22, y0 + 2)
        self.cell(85, 6, _s(f"Expediente N.: {numero}"))
        self.set_x(107)
        self._sf("", 9)
        self.cell(83, 6, _s(f"Cordoba, {fecha}"), align="R")
        self.ln(14)

    def seccion(self, titulo, cuerpo, justified=True):
        self._sf("B", 9)
        self.set_text_color(*AZUL_MPF)
        self.cell(0, 6, _s(titulo) + ":", ln=True)
        self.set_text_color(*NEGRO)
        self._sf("", 9)
        align = "J" if justified else "L"
        self.multi_cell(0, 5, _s(cuerpo), align=align)
        self.ln(3)

    def item_lista(self, numero, texto):
        self._sf("B", 9)
        self.set_x(25)
        self.cell(8, 5, f"{numero}.")
        self._sf("", 9)
        self.multi_cell(0, 5, _s(texto), align="J")
        self.ln(1)

    def linea_firma(self, nombre, cargo, unidad):
        self.ln(10)
        self.set_draw_color(*GRIS_LINEA)
        self.set_line_width(0.3)
        x_firma = 110
        self.line(x_firma, self.get_y(), 190, self.get_y())
        self.ln(2)
        self._sf("B", 9)
        self.set_x(x_firma)
        self.cell(80, 5, _s(nombre).upper(), align="C", ln=True)
        self._sf("", 8)
        self.set_x(x_firma)
        self.cell(80, 4, _s(cargo), align="C", ln=True)
        self.set_x(x_firma)
        self.cell(80, 4, _s(unidad), align="C", ln=True)


# -- Dictamen de derivacion a mediacion ---------------------------------------

def pdf_dictamen_mediacion(caso, clasificacion, fiscal_nombre, unidad_key):
    inf = TIPOS_INFRACCION.get(caso["tipo"], {})
    fecha = _fecha_formal()
    fecha_audiencia = _fecha_formal(datetime.now() + timedelta(days=7))

    pdf = PDFMPFBase(unidad_key)
    pdf.alias_nb_pages()
    pdf.add_page()

    pdf.titulo_documento("Dictamen de Derivacion a Instancia de Mediacion")
    pdf.metadatos(caso.get("numero", "S/N"), fecha)

    pdf.seccion("VISTOS",
        f"Las presentes actuaciones caratuladas: \"{caso['imputado'].upper()} - "
        f"infraccion al {inf.get('articulo', 'Codigo de Convivencia Ciudadana')}\", "
        f"iniciadas con motivo del hecho descripto en el sumario de actuaciones.")

    pdf.seccion("RESULTANDO",
        f"Que de las actuaciones labradas surge que el/la imputado/a "
        f"{caso['imputado']}, D.N.I. N. {caso['dni']}, de {caso.get('edad','')} "
        f"anios de edad, habria incurrido en la conducta descripta en el parte policial "
        f"adjunto, encuadrable en los terminos del "
        f"{inf.get('articulo', 'articulo pertinente')} "
        f"de la Ley Provincial N. 10.326 - Codigo de Convivencia Ciudadana.")

    pdf._sf("B", 9)
    pdf.set_text_color(*AZUL_MPF)
    pdf.cell(0, 6, "CONSIDERANDO:", ln=True)
    pdf.set_text_color(*NEGRO)
    pdf._sf("", 9)
    pdf.ln(1)

    considerandos = [
        ("I.",
         "Que el hecho imputado reviste el caracter de contravencion de minima gravedad, "
         "sin que se registren antecedentes contravencionales previos en los registros consultados."),
        ("II.",
         "Que el conflicto subyacente presenta las caracteristicas propias de una disputa de "
         "convivencia comunitaria, siendo susceptible de abordaje mediante instancias de dialogo "
         "y acuerdo entre las partes."),
        ("III.",
         "Que la Ley Provincial N. 10.543 establece la mediacion como instancia prejudicial "
         "obligatoria en causas de esta naturaleza, constituyendo una herramienta eficaz para "
         "la resolucion del conflicto sin necesidad de avanzar en el proceso contravencional pleno."),
        ("IV.",
         "Que esta Fiscalia propicia una politica de gestion de conflictos que prioriza "
         "soluciones restaurativas y no punitivas en los casos en que la gravedad del hecho "
         "asi lo permite."),
    ]
    for num, texto in considerandos:
        pdf.set_x(22)
        pdf._sf("B", 9)
        pdf.cell(10, 5, num)
        pdf._sf("", 9)
        pdf.multi_cell(0, 5, texto, align="J")
        pdf.ln(2)

    pdf.ln(2)
    pdf._sf("B", 9)
    pdf.set_text_color(*AZUL_MPF)
    pdf.cell(0, 6, "DICTAMINO:", ln=True)
    pdf.set_text_color(*NEGRO)
    pdf._sf("", 9)
    pdf.multi_cell(0, 5,
        f"Derivar las presentes actuaciones al Centro Judicial de Mediacion dependiente "
        f"del Tribunal Superior de Justicia de la Provincia de Cordoba, fijandose audiencia "
        f"de mediacion para el dia {fecha_audiencia} a las 10:00 hs.\n\n"
        f"Notifiquese fehacientemente al/la imputado/a {caso['imputado']} en el domicilio "
        f"que surge de las actuaciones, haciendole saber que su incomparecencia injustificada "
        f"a la audiencia de mediacion habilitara la continuacion del proceso contravencional.",
        align="J")

    pdf.linea_firma(fiscal_nombre, "Ayudante Fiscal", pdf.unidad_str.split(" - ")[0].strip())

    buf = BytesIO()
    pdf.output(buf)
    return buf.getvalue()


# -- Dictamen de suspension del proceso a prueba ------------------------------

def pdf_dictamen_suspension(caso, clasificacion, fiscal_nombre, unidad_key):
    inf = TIPOS_INFRACCION.get(caso["tipo"], {})
    categoria = clasificacion.get("categoria", "Transito")
    condiciones = _get_condiciones(caso["tipo"], categoria)
    fecha = _fecha_formal()
    meses = 6 if clasificacion.get("score", 2) <= 2.5 else 12
    meses_str = "SEIS" if meses == 6 else "DOCE"
    antec = caso.get("antecedentes", 0)

    pdf = PDFMPFBase(unidad_key)
    pdf.alias_nb_pages()
    pdf.add_page()

    pdf.titulo_documento("Dictamen de Suspension del Proceso a Prueba")
    pdf.metadatos(caso.get("numero", "S/N"), fecha)

    pdf.seccion("VISTOS",
        f"Las presentes actuaciones caratuladas: \"{caso['imputado'].upper()} - "
        f"infraccion al {inf.get('articulo', 'Codigo de Convivencia Ciudadana')}\".")

    pdf.seccion("RESULTANDO",
        f"Que el/la imputado/a {caso['imputado']}, D.N.I. N. {caso['dni']}, "
        f"de {caso.get('edad','')} anios, se encuentra imputado/a de haber incurrido en la "
        f"conducta prevista por el {inf.get('articulo', 'articulo pertinente')} de la Ley "
        f"Provincial N. 10.326. Del analisis de las actuaciones surge que el hecho imputado "
        f"reune los requisitos de procedencia para la suspension del proceso a prueba "
        f"conforme a los arts. 101 y ss. del Codigo de Convivencia Ciudadana.")

    pdf._sf("B", 9)
    pdf.set_text_color(*AZUL_MPF)
    pdf.cell(0, 6, "CONSIDERANDO:", ln=True)
    pdf.set_text_color(*NEGRO)
    pdf._sf("", 9)
    pdf.ln(1)

    cons = [
        ("I.",
         f"Que el/la imputado/a cuenta con {antec} antecedente/s contravencional/es "
         f"previo/s, lo que no obsta, en el caso concreto, a la procedencia del instituto."),
        ("II.",
         "Que la infraccion imputada tiene una pena prevista que habilita el otorgamiento "
         "de la suspension del proceso a prueba conforme al ordenamiento contravencional vigente."),
        ("III.",
         "Que la aplicacion de este instituto resulta proporcional a la entidad del hecho y "
         "contribuye a los fines de prevencion especial, evitando los efectos estigmatizantes "
         "de una condena formal."),
        ("IV.",
         "Que las condiciones que se impondran al/la imputado/a resultan adecuadas para "
         "reparar el dano producido y prevenir la reiteracion de conductas similares."),
    ]
    for num, texto in cons:
        pdf.set_x(22)
        pdf._sf("B", 9)
        pdf.cell(10, 5, num)
        pdf._sf("", 9)
        pdf.multi_cell(0, 5, texto, align="J")
        pdf.ln(2)

    pdf.ln(2)
    pdf._sf("B", 9)
    pdf.set_text_color(*AZUL_MPF)
    pdf.cell(0, 6, "DICTAMINO:", ln=True)
    pdf.set_text_color(*NEGRO)
    pdf._sf("", 9)
    pdf.multi_cell(0, 5,
        f"Hacer lugar a la suspension del proceso a prueba respecto de "
        f"{caso['imputado']}, D.N.I. N. {caso['dni']}, por el termino de {meses} "
        f"({meses_str}) meses, bajo las siguientes condiciones:",
        align="J")
    pdf.ln(3)

    for i, cond in enumerate(condiciones, 1):
        pdf.item_lista(i, cond)
    pdf.ln(3)

    pdf._sf("", 9)
    pdf.multi_cell(0, 5,
        "Transcurrido el periodo de prueba sin incumplimiento de las condiciones impuestas "
        "y sin haber incurrido en nueva contravencion, se extinguira la accion contravencional "
        "y se archivaran las presentes actuaciones.\n\n"
        f"El/la imputado/a debera presentarse ante esta Unidad dentro de los DIEZ (10) dias "
        "habiles de notificado/a para suscribir el acta de compromiso correspondiente.",
        align="J")

    pdf.linea_firma(fiscal_nombre, "Ayudante Fiscal", pdf.unidad_str.split(" - ")[0].strip())

    buf = BytesIO()
    pdf.output(buf)
    return buf.getvalue()


# -- Cedula de citacion -------------------------------------------------------

def pdf_citacion(caso, fiscal_nombre, unidad_key, motivo="audiencia"):
    inf = TIPOS_INFRACCION.get(caso["tipo"], {})
    fecha = _fecha_formal()
    fecha_cit = _fecha_formal(datetime.now() + timedelta(days=5))
    motivo_txt = {
        "audiencia": "comparecer a audiencia contravencional",
        "mediacion": "participar en instancia de mediacion",
        "acta":      "suscribir acta de compromiso de suspension del proceso a prueba",
    }.get(motivo, "comparecer ante esta Unidad")

    pdf = PDFMPFBase(unidad_key)
    pdf.alias_nb_pages()
    pdf.add_page()

    pdf.titulo_documento("Cedula de Notificacion / Citacion")
    pdf.metadatos(caso.get("numero", "S/N"), fecha)

    # Destinatario en caja destacada
    pdf.set_fill_color(240, 244, 252)
    pdf.set_draw_color(*AZUL_CLARO)
    y0 = pdf.get_y()
    pdf.rect(20, y0, 170, 22, style="FD")
    pdf.set_xy(24, y0 + 3)
    pdf._sf("B", 9)
    pdf.cell(30, 5, "Sr./Sra.:")
    pdf._sf("", 9)
    pdf.cell(0, 5, _s(caso["imputado"]), ln=True)
    pdf.set_x(24)
    pdf._sf("B", 9)
    pdf.cell(30, 5, "D.N.I.:")
    pdf._sf("", 9)
    pdf.cell(0, 5, _s(caso["dni"]), ln=True)
    pdf.set_x(24)
    pdf._sf("B", 9)
    pdf.cell(30, 5, "Domicilio:")
    pdf._sf("", 9)
    pdf.cell(0, 5, _s(caso.get("domicilio") or "-"), ln=True)
    pdf.ln(10)

    pdf._sf("", 9)
    pdf.multi_cell(0, 5,
        f"Por la presente se le notifica que en los autos caratulados "
        f"\"{caso['imputado'].upper()} - infraccion al "
        f"{inf.get('articulo', 'Codigo de Convivencia Ciudadana')}\", "
        f"tramitados ante esta Unidad, se lo/la CITA a {motivo_txt} a celebrarse el dia "
        f"{fecha_cit} a las 09:00 hs., en la sede de este organismo sita en:",
        align="J")
    pdf.ln(3)

    pdf.set_fill_color(245, 246, 250)
    pdf._sf("B", 10)
    pdf.set_x(40)
    pdf.cell(130, 8, _s(pdf.unidad_str), align="C", fill=True, ln=True)
    pdf.ln(5)

    pdf._sf("", 9)
    pdf.multi_cell(0, 5,
        "Se le hace saber que debera concurrir munido/a de D.N.I. y que la "
        "incomparecencia injustificada podra motivar la continuacion del proceso en su rebeldia.\n\n"
        "Ante cualquier consulta comunicarse al: (0351) 4335361 - Unidad Norte / "
        "(0351) 4466707 - Unidad Sur.",
        align="J")

    pdf.linea_firma(fiscal_nombre, "Ayudante Fiscal", pdf.unidad_str.split(" - ")[0].strip())

    buf = BytesIO()
    pdf.output(buf)
    return buf.getvalue()


# -- Acta de compromiso -------------------------------------------------------

def pdf_acta_compromiso(caso, condiciones_lista, fiscal_nombre, unidad_key, meses=6):
    inf = TIPOS_INFRACCION.get(caso["tipo"], {})
    fecha = _fecha_formal()
    meses_str = {3:"TRES", 6:"SEIS", 9:"NUEVE", 12:"DOCE"}.get(meses, str(meses))

    pdf = PDFMPFBase(unidad_key)
    pdf.alias_nb_pages()
    pdf.add_page()

    pdf.titulo_documento("Acta de Compromiso — Suspension del Proceso a Prueba")
    pdf.metadatos(caso.get("numero", "S/N"), fecha)

    pdf.seccion("COMPARECIENTE",
        f"En la ciudad de Cordoba, a los {fecha}, comparece ante esta Unidad "
        f"el/la Sr./Sra. {caso['imputado']}, D.N.I. N. {caso['dni']}, de {caso.get('edad','')} "
        f"anios de edad, con domicilio en {_s(caso.get('domicilio') or 'el declarado en autos')}, "
        f"en los autos caratulados \"{caso['imputado'].upper()} - infraccion al "
        f"{inf.get('articulo','Codigo de Convivencia Ciudadana')}\".")

    pdf.seccion("OBJETO",
        f"Por la presente, el/la compareciente presta su conformidad con la suspension "
        f"del proceso a prueba otorgada por esta Fiscalia por el termino de {meses} ({meses_str}) "
        f"meses a partir de la fecha, comprometiendose al cumplimiento de las siguientes condiciones:")

    pdf.ln(2)
    pdf._sf("B", 9)
    pdf.set_text_color(*AZUL_MPF)
    pdf.cell(0, 6, "CONDICIONES IMPUESTAS:", ln=True)
    pdf.set_text_color(*NEGRO)
    pdf.ln(2)
    for i, cond in enumerate(condiciones_lista, 1):
        pdf.item_lista(i, _s(cond))
    pdf.ln(3)

    pdf._sf("", 9)
    pdf.multi_cell(0, 5,
        "El/la compareciente declara conocer y aceptar las condiciones precedentes, "
        "siendo debidamente informado/a de que el incumplimiento de cualquiera de ellas "
        "habilitara la revocacion de la suspension y la continuacion del proceso "
        "contravencional en los terminos del Codigo de Convivencia Ciudadana.\n\n"
        "En prueba de conformidad, se firma la presente en dos ejemplares de un mismo "
        "tenor y a un solo efecto, quedando uno en poder del/la imputado/a y otro "
        "en las actuaciones.", align="J")
    pdf.ln(8)

    # Dos firmas
    pdf.set_draw_color(*GRIS_LINEA)
    pdf.set_line_width(0.3)
    pdf.line(20,  pdf.get_y(), 90,  pdf.get_y())
    pdf.line(120, pdf.get_y(), 190, pdf.get_y())
    pdf.ln(2)
    pdf._sf("B", 9)
    pdf.cell(90, 5, _s(caso["imputado"]).upper(), align="C")
    pdf.cell(70, 5, _s(fiscal_nombre).upper(), align="C", ln=True)
    pdf._sf("", 8)
    pdf.cell(90, 4, "Imputado/a", align="C")
    pdf.cell(70, 4, "Ayudante Fiscal", align="C", ln=True)
    pdf.cell(90, 4, f"D.N.I. {caso['dni']}", align="C")
    pdf.cell(70, 4, _s(pdf.unidad_str.split(" - ")[0].strip()), align="C", ln=True)

    buf = BytesIO()
    pdf.output(buf)
    return buf.getvalue()


# -- Informe de incumplimiento ------------------------------------------------

def pdf_informe_incumplimiento(caso, seguimiento, condiciones_inc, fiscal_nombre, unidad_key):
    inf = TIPOS_INFRACCION.get(caso["tipo"], {})
    fecha = _fecha_formal()

    pdf = PDFMPFBase(unidad_key)
    pdf.alias_nb_pages()
    pdf.add_page()

    pdf.titulo_documento("Informe de Incumplimiento de Condiciones")
    pdf.metadatos(caso.get("numero", "S/N"), fecha)

    pdf.seccion("OBJETO",
        f"La presente tiene por objeto informar el incumplimiento de las condiciones "
        f"oportunamente impuestas en el marco de la suspension del proceso a prueba "
        f"otorgada a {caso['imputado']}, D.N.I. N. {caso['dni']}, "
        f"en los autos \"{caso['imputado'].upper()} - infraccion al "
        f"{inf.get('articulo', 'Codigo de Convivencia Ciudadana')}\".")

    pdf.seccion("ANTECEDENTES",
        f"Que con fecha {_s(seguimiento.get('fecha_inicio',''))} se otorgo la suspension "
        f"del proceso a prueba por el termino correspondiente, venciendo el periodo el "
        f"{_s(seguimiento.get('fecha_fin',''))}. El/la imputado/a suscribio el acta de "
        f"compromiso respectiva comprometiendose al cumplimiento de las condiciones establecidas.")

    pdf._sf("B", 9)
    pdf.set_text_color(*AZUL_MPF)
    pdf.cell(0, 6, "CONDICIONES INCUMPLIDAS:", ln=True)
    pdf.set_text_color(*NEGRO)
    pdf.ln(2)
    for i, cond in enumerate(condiciones_inc, 1):
        desc = cond.get("descripcion", str(cond))
        pdf.item_lista(i, _s(desc))
    pdf.ln(3)

    pdf._sf("B", 9)
    pdf.set_text_color(*AZUL_MPF)
    pdf.cell(0, 6, "CONCLUSION:", ln=True)
    pdf.set_text_color(*NEGRO)
    pdf._sf("", 9)
    pdf.multi_cell(0, 5,
        "En virtud del incumplimiento acreditado, esta Fiscalia concluye que el/la "
        "imputado/a no ha dado cumplimiento a las condiciones impuestas, lo que habilita "
        "la revocacion de la suspension del proceso a prueba y la continuacion del "
        "proceso contravencional conforme las prescripciones del Codigo de Convivencia "
        "Ciudadana de la Provincia de Cordoba.\n\n"
        "Por lo expuesto, se eleva el presente informe a efectos de que se adopten "
        "las medidas procesales que correspondan.", align="J")

    pdf.linea_firma(fiscal_nombre, "Ayudante Fiscal", pdf.unidad_str.split(" - ")[0].strip())

    buf = BytesIO()
    pdf.output(buf)
    return buf.getvalue()


# -- Reporte diario -----------------------------------------------------------

def pdf_reporte_diario(stats, audiencias_hoy, causas_pendientes, fiscal_nombre, unidad_key):
    """Genera un resumen ejecutivo del dia para la unidad."""
    fecha = _fecha_formal()
    now   = datetime.now()

    pdf = PDFMPFBase(unidad_key)
    pdf.alias_nb_pages()
    pdf.add_page()

    pdf.titulo_documento("Reporte Diario de Gestion Contravencional")
    pdf._sf("B", 9)
    pdf.set_text_color(*AZUL_CLARO)
    pdf.cell(0, 6, f"Fecha: {fecha}  -  Generado: {now.strftime('%H:%M hs')}", ln=True)
    pdf.set_text_color(*NEGRO)
    pdf.ln(4)

    # Estadisticas generales
    pdf._sf("B", 10)
    pdf.set_text_color(*AZUL_MPF)
    pdf.set_fill_color(240, 244, 255)
    pdf.cell(0, 7, "ESTADISTICAS GENERALES", fill=True, ln=True)
    pdf.set_text_color(*NEGRO)
    pdf._sf("", 9)
    pdf.ln(2)
    pdf.cell(95, 6, f"Total causas en el sistema: {stats.get('total', 0)}", ln=False)
    pdf.cell(95, 6, f"Personas registradas: {stats.get('personas', 0)}", ln=True)
    por_carril = stats.get("por_carril", {})
    pdf.cell(95, 6, f"Carril Verde (mediacion): {por_carril.get('verde', 0)}", ln=False)
    pdf.cell(95, 6, f"Carril Amarillo (suspension): {por_carril.get('amarillo', 0)}", ln=True)
    pdf.cell(95, 6, f"Carril Rojo (proceso pleno): {por_carril.get('rojo', 0)}", ln=False)
    pdf.cell(95, 6, f"Reincidentes: {stats.get('reincidentes', 0)}", ln=True)
    pdf.ln(4)

    # Audiencias del dia
    pdf._sf("B", 10)
    pdf.set_text_color(*AZUL_MPF)
    pdf.set_fill_color(240, 244, 255)
    n_aud = len(audiencias_hoy) if audiencias_hoy else 0
    pdf.cell(0, 7, f"AUDIENCIAS DEL DIA ({n_aud})", fill=True, ln=True)
    pdf.set_text_color(*NEGRO)
    pdf._sf("", 9)
    pdf.ln(2)
    if audiencias_hoy:
        for a in audiencias_hoy:
            hora  = _s(a.get("hora", ""))
            nom   = _s(a.get("apellido_nombre", "")).split(",")[0].strip()
            num   = _s(a.get("numero", ""))
            tipo  = _s(a.get("tipo","")).replace("_"," ").capitalize()
            est   = _s(a.get("estado","")).capitalize()
            pdf.cell(25, 5, hora, ln=False)
            pdf.cell(60, 5, nom, ln=False)
            pdf.cell(55, 5, num, ln=False)
            pdf.cell(50, 5, tipo, ln=True)
    else:
        pdf.cell(0, 5, "No hay audiencias programadas para el dia de hoy.", ln=True)
    pdf.ln(4)

    # Causas pendientes de accion
    pdf._sf("B", 10)
    pdf.set_text_color(*AZUL_MPF)
    pdf.set_fill_color(240, 244, 255)
    n_pend = len(causas_pendientes) if causas_pendientes else 0
    pdf.cell(0, 7, f"CAUSAS PENDIENTES DE ACCION ({n_pend})", fill=True, ln=True)
    pdf.set_text_color(*NEGRO)
    pdf._sf("", 9)
    pdf.ln(2)
    if causas_pendientes:
        for c in causas_pendientes[:15]:
            nom   = _s(c.get("apellido_nombre","")).split(",")[0].strip()
            num   = _s(c.get("numero",""))
            est   = _s(c.get("estado","")).capitalize()
            tipo  = TIPOS_INFRACCION.get(c.get("tipo_infraccion",""), {}).get("label", "")
            pdf.cell(55, 5, nom, ln=False)
            pdf.cell(50, 5, num, ln=False)
            pdf.cell(45, 5, _s(tipo)[:28], ln=False)
            pdf.cell(40, 5, est, ln=True)
        if len(causas_pendientes) > 15:
            pdf.cell(0, 5, f"... y {len(causas_pendientes)-15} causas mas.", ln=True)
    else:
        pdf.cell(0, 5, "No hay causas pendientes de accion inmediata.", ln=True)
    pdf.ln(6)

    pdf._sf("I", 8)
    pdf.set_text_color(*GRIS_TEXTO)
    pdf.cell(0, 4,
        f"Generado automaticamente por SIATC - MPF Cordoba - {now.strftime('%d/%m/%Y %H:%M')}",
        ln=True, align="C")

    buf = BytesIO()
    pdf.output(buf)
    return buf.getvalue()


# -- Perfil del imputado ------------------------------------------------------

def pdf_perfil_persona(perfil: dict, fiscal_nombre: str, unidad_key: str) -> bytes:
    """Genera una ficha institucional con el historial completo de una persona."""
    p       = perfil.get("persona", {})
    causas  = perfil.get("causas", [])
    segs    = perfil.get("seguimientos", [])
    auds    = perfil.get("audiencias", [])
    antec   = perfil.get("antecedentes", 0)
    fecha   = _fecha_formal()

    pdf = PDFMPFBase(unidad_key)
    pdf.alias_nb_pages()
    pdf.add_page()

    pdf.titulo_documento("Ficha del Imputado/a — Historial Contravencional")
    pdf.metadatos(f"DNI {_s(p.get('dni', ''))}", fecha)

    # -- Datos personales --
    pdf._sf("B", 10)
    pdf.set_text_color(*AZUL_MPF)
    pdf.set_fill_color(235, 240, 250)
    pdf.cell(0, 7, "DATOS PERSONALES", fill=True, ln=True)
    pdf.set_text_color(*NEGRO)
    pdf._sf("", 9)
    pdf.ln(2)

    pdf.cell(50, 6, "Apellido y Nombre:")
    pdf._sf("B", 9)
    pdf.cell(0, 6, _s(p.get("apellido_nombre", "")), ln=True)
    pdf._sf("", 9)
    pdf.cell(50, 6, "D.N.I.:")
    pdf.cell(60, 6, _s(str(p.get("dni", ""))))
    pdf.cell(30, 6, "Edad:")
    pdf._sf("B", 9)
    pdf.cell(0, 6, _s(str(p.get("edad", ""))), ln=True)
    pdf._sf("", 9)
    pdf.cell(50, 6, "Domicilio:")
    pdf.cell(0, 6, _s(p.get("domicilio") or "No registrado"), ln=True)
    pdf.cell(50, 6, "Telefono:")
    pdf.cell(0, 6, _s(p.get("telefono") or "No registrado"), ln=True)
    pdf.ln(2)

    # Antecedentes highlight
    if antec == 0:
        pdf.set_fill_color(212, 237, 218)
        antec_txt = "Sin antecedentes contravencionales registrados"
    elif antec == 1:
        pdf.set_fill_color(255, 243, 205)
        antec_txt = f"1 antecedente contravencional registrado"
    else:
        pdf.set_fill_color(248, 215, 218)
        antec_txt = f"{antec} antecedentes contravencionales registrados"
    pdf._sf("B", 9)
    pdf.cell(0, 7, _s(antec_txt), fill=True, align="C", ln=True)
    pdf.ln(4)

    # -- Causas --
    pdf._sf("B", 10)
    pdf.set_text_color(*AZUL_MPF)
    pdf.set_fill_color(235, 240, 250)
    pdf.cell(0, 7, f"HISTORIAL DE CAUSAS ({len(causas)})", fill=True, ln=True)
    pdf.set_text_color(*NEGRO)
    pdf.ln(2)

    CARRIL_STR = {"verde": "VERDE (Mediacion)", "amarillo": "AMARILLO (Suspension)", "rojo": "ROJO (Proceso pleno)"}
    for c in causas:
        inf = TIPOS_INFRACCION.get(c.get("tipo_infraccion", ""), {})
        pdf._sf("B", 9)
        pdf.cell(0, 5, _s(f"* {c.get('numero','')} — {inf.get('label', c.get('tipo_infraccion',''))}"), ln=True)
        pdf._sf("", 9)
        pdf.cell(10, 5, "")
        pdf.cell(40, 5, "Estado:")
        pdf.cell(60, 5, _s(c.get("estado","").capitalize()))
        pdf.cell(30, 5, "Carril:")
        pdf.cell(0, 5, _s(CARRIL_STR.get(c.get("carril",""), "")), ln=True)
        pdf.cell(10, 5, "")
        pdf.cell(40, 5, "Infraccion:")
        pdf.multi_cell(0, 5, _s(inf.get("articulo", "")))
        if c.get("descripcion"):
            pdf.cell(10, 5, "")
            pdf.cell(40, 5, "Hechos:")
            pdf.multi_cell(0, 5, _s(str(c.get("descripcion",""))[:200]))
        pdf.ln(2)

    if not causas:
        pdf._sf("", 9)
        pdf.cell(0, 5, "Sin causas registradas.", ln=True)
    pdf.ln(2)

    # -- Seguimientos --
    if segs:
        pdf._sf("B", 10)
        pdf.set_text_color(*AZUL_MPF)
        pdf.set_fill_color(235, 240, 250)
        pdf.cell(0, 7, f"SEGUIMIENTOS POST-RESOLUCION ({len(segs)})", fill=True, ln=True)
        pdf.set_text_color(*NEGRO)
        pdf.ln(2)
        for s in segs:
            pdf._sf("B", 9)
            tipo_s = {"suspension":"Suspension a Prueba","mediacion":"Acuerdo de Mediacion","acuerdo":"Acuerdo Conciliatorio"}.get(s.get("tipo_resolucion",""), s.get("tipo_resolucion",""))
            pdf.cell(0, 5, _s(f"* {tipo_s} — {s.get('estado','').capitalize()}"), ln=True)
            pdf._sf("", 9)
            pdf.cell(10, 5, "")
            pdf.cell(40, 5, "Periodo:")
            pdf.cell(0, 5, _s(f"{s.get('fecha_inicio','')} a {s.get('fecha_fin','')}"), ln=True)
            pdf.ln(2)

    # -- Audiencias --
    if auds:
        pdf._sf("B", 10)
        pdf.set_text_color(*AZUL_MPF)
        pdf.set_fill_color(235, 240, 250)
        pdf.cell(0, 7, f"AUDIENCIAS ({len(auds)})", fill=True, ln=True)
        pdf.set_text_color(*NEGRO)
        pdf.ln(2)
        TIPO_STR = {"audiencia":"Audiencia contravencional","mediacion":"Mediacion",
                    "acta_compromiso":"Acta de compromiso","control_seg":"Control seguimiento",
                    "reprogramada":"Reprogramada"}
        for a in sorted(auds, key=lambda x: x.get("fecha",""), reverse=True)[:10]:
            ESTADO_A = {"programada":"Programada","realizada":"Realizada",
                        "ausente":"AUSENTE","reprogramada":"Reprogramada","cancelada":"Cancelada"}
            pdf._sf("", 9)
            pdf.cell(30, 5, _s(f"{a.get('fecha','')} {a.get('hora','')}"))
            pdf.cell(70, 5, _s(TIPO_STR.get(a.get("tipo",""), a.get("tipo",""))))
            pdf.cell(0, 5, _s(ESTADO_A.get(a.get("estado",""), a.get("estado","").capitalize())), ln=True)

    pdf.ln(6)
    pdf._sf("I", 8)
    pdf.set_text_color(*GRIS_TEXTO)
    pdf.cell(0, 4,
        _s(f"Generado por SIATC - MPF Cordoba - {datetime.now().strftime('%d/%m/%Y %H:%M')} - {fiscal_nombre}"),
        ln=True, align="C")

    buf = BytesIO()
    pdf.output(buf)
    return buf.getvalue()


# -- Punto de entrada ---------------------------------------------------------

def generar_pdf(tipo_doc, caso, clf, fiscal, unidad):
    # Normalize DB row keys to the legacy keys used by pdf helpers.
    # get_causa() returns apellido_nombre / persona_dni / persona_edad;
    # the pdf helpers expect imputado / dni / edad / tipo / antecedentes.
    if isinstance(caso, dict):
        caso = dict(caso)
        caso.setdefault("tipo",         caso.get("tipo_infraccion", ""))
        caso.setdefault("imputado",     caso.get("apellido_nombre", ""))
        caso.setdefault("dni",          caso.get("persona_dni", ""))
        caso.setdefault("edad",         caso.get("persona_edad", ""))
        caso.setdefault("antecedentes", 0)
        caso.setdefault("domicilio",    caso.get("persona_domicilio", ""))
    t = tipo_doc.lower()
    if "mediaci" in t:
        return pdf_dictamen_mediacion(caso, clf, fiscal, unidad)
    elif "suspensi" in t or "prueba" in t:
        return pdf_dictamen_suspension(caso, clf, fiscal, unidad)
    elif "acta" in t and "compromiso" in t:
        condiciones = clf.get("condiciones", []) if clf else []
        return pdf_acta_compromiso(caso, condiciones, fiscal, unidad)
    elif "incumplimiento" in t:
        seguimiento = clf.get("seguimiento", {}) if clf else {}
        conds_inc   = clf.get("condiciones_inc", []) if clf else []
        return pdf_informe_incumplimiento(caso, seguimiento, conds_inc, fiscal, unidad)
    elif "citaci" in t:
        motivo = "mediacion" if "mediaci" in t else ("acta" if "acta" in t else "audiencia")
        return pdf_citacion(caso, fiscal, unidad, motivo)
    else:
        return pdf_citacion(caso, fiscal, unidad)
