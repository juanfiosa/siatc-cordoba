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


# -- Punto de entrada ---------------------------------------------------------

def generar_pdf(tipo_doc, caso, clf, fiscal, unidad):
    if "mediaci" in tipo_doc or "mediacion" in tipo_doc:
        return pdf_dictamen_mediacion(caso, clf, fiscal, unidad)
    elif "suspensi" in tipo_doc or "prueba" in tipo_doc:
        return pdf_dictamen_suspension(caso, clf, fiscal, unidad)
    elif "citaci" in tipo_doc or "citacion" in tipo_doc:
        motivo = "mediacion" if "mediaci" in tipo_doc else "audiencia"
        return pdf_citacion(caso, fiscal, unidad, motivo)
    else:
        return pdf_citacion(caso, fiscal, unidad)
