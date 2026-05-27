"""
Generador de PDFs para SIATC — usa ReportLab
Ministerio Público Fiscal · Córdoba
"""
from datetime import datetime, timedelta
from io import BytesIO

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, HRFlowable,
    Table, TableStyle, ListFlowable, ListItem,
)
from reportlab.platypus.flowables import KeepTogether

from data_cordoba import TIPOS_INFRACCION, UNIDADES, CONDICIONES_SUSPENSION

# ── Colores institucionales ────────────────────────────────────────────────────
AZUL = colors.HexColor("#1a2f5e")
AZUL_CLARO = colors.HexColor("#2e5090")
AZUL_BG = colors.HexColor("#e8f0ff")

W, H = A4
MARGEN = 2.2 * cm


def _mes(n: int) -> str:
    return ["enero","febrero","marzo","abril","mayo","junio",
            "julio","agosto","septiembre","octubre","noviembre","diciembre"][n - 1]


def _fecha(dt: datetime = None) -> str:
    f = dt or datetime.now()
    return f"{f.day} de {_mes(f.month)} de {f.year}"


def _num_exp(numero: str) -> str:
    return numero.replace("UC", "EXP-UC").replace("-", "/")


def _estilos():
    base = getSampleStyleSheet()
    estilos = {
        "titulo": ParagraphStyle(
            "titulo", parent=base["Normal"],
            fontSize=11, fontName="Helvetica-Bold",
            textColor=colors.white, alignment=TA_CENTER,
            spaceAfter=6, spaceBefore=4,
        ),
        "header": ParagraphStyle(
            "header", parent=base["Normal"],
            fontSize=10, fontName="Helvetica-Bold",
            textColor=AZUL, alignment=TA_CENTER, spaceAfter=2,
        ),
        "subheader": ParagraphStyle(
            "subheader", parent=base["Normal"],
            fontSize=8, fontName="Helvetica",
            textColor=colors.HexColor("#444444"), alignment=TA_CENTER, spaceAfter=4,
        ),
        "seccion": ParagraphStyle(
            "seccion", parent=base["Normal"],
            fontSize=9, fontName="Helvetica-Bold",
            textColor=AZUL, spaceAfter=3, spaceBefore=6,
        ),
        "label": ParagraphStyle(
            "label", parent=base["Normal"],
            fontSize=9, fontName="Helvetica-Bold",
            textColor=colors.black,
        ),
        "body": ParagraphStyle(
            "body", parent=base["Normal"],
            fontSize=9, fontName="Helvetica",
            leading=14, alignment=TA_JUSTIFY,
            spaceAfter=4,
        ),
        "firma": ParagraphStyle(
            "firma", parent=base["Normal"],
            fontSize=9, fontName="Helvetica-Bold",
            alignment=TA_CENTER,
        ),
        "firma_sub": ParagraphStyle(
            "firma_sub", parent=base["Normal"],
            fontSize=8, fontName="Helvetica",
            alignment=TA_CENTER, textColor=colors.HexColor("#555555"),
        ),
    }
    return estilos


def _encabezado(estilos, unidad_label: str) -> list:
    return [
        Paragraph("MINISTERIO PÚBLICO FISCAL DE LA PROVINCIA DE CÓRDOBA", estilos["header"]),
        Paragraph(unidad_label, estilos["subheader"]),
        HRFlowable(width="100%", thickness=1.5, color=AZUL_CLARO),
        Spacer(1, 6),
    ]


def _bloque_titulo(estilos, texto: str) -> list:
    tabla = Table(
        [[Paragraph(texto.upper(), estilos["titulo"])]],
        colWidths=[W - 2 * MARGEN],
    )
    tabla.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), AZUL_CLARO),
        ("ROWPADDING", (0, 0), (-1, -1), 6),
    ]))
    return [tabla, Spacer(1, 10)]


def _campos(estilos, pares: list) -> list:
    rows = []
    for label, valor in pares:
        rows.append([
            Paragraph(f"{label}:", estilos["label"]),
            Paragraph(str(valor), estilos["body"]),
        ])
    tabla = Table(rows, colWidths=[4.5 * cm, W - 2 * MARGEN - 4.5 * cm])
    tabla.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
    ]))
    return [tabla, Spacer(1, 4)]


def _seccion_titulo(estilos, texto: str) -> list:
    fila = Table(
        [[Paragraph(texto, estilos["seccion"])]],
        colWidths=[W - 2 * MARGEN],
    )
    fila.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), AZUL_BG),
        ("ROWPADDING", (0, 0), (-1, -1), 4),
    ]))
    return [fila, Spacer(1, 3)]


def _parrafo(estilos, texto: str) -> list:
    return [Paragraph(texto, estilos["body"]), Spacer(1, 3)]


def _firma_block(estilos, fiscal: str, unidad_key: str) -> list:
    unidad = UNIDADES.get(unidad_key, UNIDADES["norte"])
    linea = Table(
        [["", Paragraph(fiscal.upper(), estilos["firma"])]],
        colWidths=[(W - 2 * MARGEN) * 0.5, (W - 2 * MARGEN) * 0.5],
    )
    linea.setStyle(TableStyle([
        ("LINEABOVE", (1, 0), (1, 0), 0.8, colors.black),
        ("TOPPADDING", (1, 0), (1, 0), 4),
    ]))
    return [
        Spacer(1, 24),
        linea,
        Table(
            [["", Paragraph("AYUDANTE FISCAL", estilos["firma_sub"])]],
            colWidths=[(W - 2 * MARGEN) * 0.5, (W - 2 * MARGEN) * 0.5],
        ),
        Table(
            [["", Paragraph(unidad, estilos["firma_sub"])]],
            colWidths=[(W - 2 * MARGEN) * 0.5, (W - 2 * MARGEN) * 0.5],
        ),
    ]


def _build_pdf(story: list) -> bytes:
    buf = BytesIO()
    doc = SimpleDocTemplate(
        buf, pagesize=A4,
        leftMargin=MARGEN, rightMargin=MARGEN,
        topMargin=MARGEN, bottomMargin=MARGEN,
    )
    doc.build(story)
    return buf.getvalue()


# ── Documentos públicos ────────────────────────────────────────────────────────

def pdf_dictamen_mediacion(caso: dict, clf: dict, fiscal: str, unidad_key: str,
                            fecha_audiencia_dt: datetime = None,
                            hora_audiencia: str = "10:00") -> bytes:
    inf = TIPOS_INFRACCION.get(caso["tipo"], {})
    unidad = UNIDADES.get(unidad_key, UNIDADES["norte"])
    fecha_aud = _fecha(fecha_audiencia_dt or datetime.now() + timedelta(days=7))
    es = _estilos()

    story = []
    story += _encabezado(es, unidad)
    story += _bloque_titulo(es, "Dictamen de Derivación a Instancia de Mediación")
    story += _campos(es, [
        ("Expediente N°", _num_exp(caso["numero"])),
        ("Fecha", _fecha()),
    ])
    story.append(Spacer(1, 6))
    story += _seccion_titulo(es, "I. VISTOS")
    story += _parrafo(es,
        f'Las presentes actuaciones caratuladas: "<b>{caso["imputado"].upper()} — '
        f'infracción al {inf.get("articulo","Código de Convivencia Ciudadana")}</b>", '
        f'iniciadas con motivo del hecho descripto en el sumario de actuaciones.')

    story += _seccion_titulo(es, "II. RESULTANDO")
    story += _parrafo(es,
        f'Que de las actuaciones labradas surge que el/la imputado/a <b>{caso["imputado"]}</b>, '
        f'D.N.I. N° {caso["dni"]}, de {caso["edad"]} años de edad, habría incurrido '
        f'en la conducta encuadrable en los términos del '
        f'{inf.get("articulo","artículo pertinente")} de la Ley Provincial N° 10.326 '
        f'— Código de Convivencia Ciudadana.')

    if caso.get("descripcion"):
        story += _seccion_titulo(es, "DESCRIPCIÓN DEL HECHO")
        story += _parrafo(es, caso["descripcion"])

    story += _seccion_titulo(es, "III. CONSIDERANDO")
    story += _parrafo(es,
        "Que el hecho reviste carácter de contravención de mínima gravedad, sin que se "
        "registren antecedentes contravencionales previos en los registros consultados. "
        "Que el conflicto subyacente presenta características propias de una disputa de "
        "convivencia comunitaria, siendo susceptible de abordaje mediante instancias de "
        "diálogo y acuerdo entre las partes. "
        "Que la Ley Provincial N° 10.543 establece la mediación como instancia prejudicial "
        "obligatoria en causas de esta naturaleza.")

    story += _seccion_titulo(es, "IV. DICTAMINO")
    story += _parrafo(es,
        f'Derivar las presentes actuaciones al Centro Judicial de Mediación dependiente '
        f'del Tribunal Superior de Justicia de la Provincia de Córdoba, fijándose audiencia '
        f'de mediación para el día <b>{fecha_aud}</b> a las <b>{hora_audiencia} hs.</b>')
    story += _parrafo(es,
        f'Notifíquese fehacientemente al/la imputado/a <b>{caso["imputado"]}</b> en el '
        f'domicilio que surge de las actuaciones, haciéndole saber que su incomparecencia '
        f'injustificada a la audiencia de mediación habilitará la continuación del proceso '
        f'contravencional.')

    story += _firma_block(es, fiscal, unidad_key)
    return _build_pdf(story)


def pdf_dictamen_suspension(caso: dict, clf: dict, fiscal: str, unidad_key: str) -> bytes:
    inf = TIPOS_INFRACCION.get(caso["tipo"], {})
    categoria = clf.get("categoria", "Tránsito")
    unidad = UNIDADES.get(unidad_key, UNIDADES["norte"])

    if caso["tipo"] == "transito_alcoholemia":
        condiciones = CONDICIONES_SUSPENSION["transito_alcoholemia"]
    elif categoria == "Tránsito":
        condiciones = CONDICIONES_SUSPENSION["transito"]
    elif categoria == "Convivencia":
        condiciones = CONDICIONES_SUSPENSION["convivencia"]
    elif categoria == "Comercio":
        condiciones = CONDICIONES_SUSPENSION["comercio"]
    else:
        condiciones = CONDICIONES_SUSPENSION["integridad"]

    meses = 6 if clf.get("score", 2) <= 2.5 else 12
    meses_texto = "SEIS" if meses == 6 else "DOCE"
    es = _estilos()

    story = []
    story += _encabezado(es, unidad)
    story += _bloque_titulo(es, "Dictamen de Suspensión del Proceso a Prueba")
    story += _campos(es, [
        ("Expediente N°", _num_exp(caso["numero"])),
        ("Fecha", _fecha()),
    ])
    story.append(Spacer(1, 6))

    story += _seccion_titulo(es, "I. VISTOS")
    story += _parrafo(es,
        f'Las presentes actuaciones caratuladas: "<b>{caso["imputado"].upper()} — '
        f'infracción al {inf.get("articulo","Código de Convivencia Ciudadana")}</b>".')

    story += _seccion_titulo(es, "II. RESULTANDO")
    story += _parrafo(es,
        f'Que el/la imputado/a <b>{caso["imputado"]}</b>, D.N.I. N° {caso["dni"]}, '
        f'de {caso["edad"]} años, se encuentra imputado/a de haber incurrido en la conducta '
        f'prevista por el {inf.get("articulo","artículo pertinente")} de la Ley N° 10.326. '
        f'Del análisis de las actuaciones surge que el hecho reúne los requisitos de '
        f'procedencia de los arts. 101 y ss. del Código de Convivencia Ciudadana para '
        f'la suspensión del proceso a prueba.')

    story += _seccion_titulo(es, "III. CONSIDERANDO")
    story += _parrafo(es,
        f'Que el/la imputado/a cuenta con {caso.get("antecedentes", 0)} antecedente/s '
        f'contravencional/es previo/s. Que la aplicación de este instituto resulta '
        f'proporcional a la entidad del hecho y contribuye a los fines de prevención '
        f'especial, evitando los efectos estigmatizantes de una condena formal.')

    story += _seccion_titulo(es, "IV. DICTAMINO")
    story += _parrafo(es,
        f'Hacer lugar a la suspensión del proceso a prueba respecto de <b>{caso["imputado"]}</b>, '
        f'D.N.I. N° {caso["dni"]}, por el término de {meses} ({meses_texto}) meses, '
        f'bajo las siguientes condiciones:')

    items = [ListItem(Paragraph(c, es["body"]), bulletColor=AZUL_CLARO) for c in condiciones]
    story.append(ListFlowable(items, bulletType="1", leftIndent=20, bulletFontSize=9))
    story.append(Spacer(1, 6))

    story += _parrafo(es,
        'Transcurrido el período de prueba sin incumplimiento de las condiciones impuestas '
        'y sin haber incurrido en nueva contravención, se extinguirá la acción contravencional '
        'y se archivarán las presentes actuaciones. El/la imputado/a deberá presentarse ante '
        'esta Unidad dentro de los DIEZ (10) días hábiles de notificado/a para suscribir el '
        'acta de compromiso correspondiente.')

    story += _firma_block(es, fiscal, unidad_key)
    return _build_pdf(story)


def pdf_citacion(caso: dict, fiscal: str, unidad_key: str, motivo: str = "audiencia",
                 fecha_citacion_dt: datetime = None, hora_citacion: str = "09:00") -> bytes:
    inf = TIPOS_INFRACCION.get(caso["tipo"], {})
    unidad = UNIDADES.get(unidad_key, UNIDADES["norte"])
    fecha_cit = _fecha(fecha_citacion_dt or datetime.now() + timedelta(days=5))

    motivo_texto = {
        "audiencia": "comparecer a audiencia contravencional",
        "mediacion": "participar en instancia de mediación",
        "acta": "suscribir acta de compromiso de suspensión del proceso a prueba",
    }.get(motivo, "comparecer ante esta Unidad")
    es = _estilos()

    story = []
    story += _encabezado(es, unidad)
    story += _bloque_titulo(es, "Cédula de Notificación / Citación")
    story += _campos(es, [
        ("Expediente N°", _num_exp(caso["numero"])),
        ("Fecha de emisión", _fecha()),
    ])
    story.append(Spacer(1, 6))

    story += _seccion_titulo(es, "DATOS DEL CITADO/A")
    story += _campos(es, [
        ("Apellido y nombre", caso["imputado"]),
        ("D.N.I.", caso["dni"]),
    ])
    story.append(Spacer(1, 4))

    story += _seccion_titulo(es, "OBJETO DE LA CITACIÓN")
    story += _parrafo(es,
        f'Por la presente se le notifica que en los autos caratulados '
        f'"<b>{caso["imputado"].upper()} — '
        f'infracción al {inf.get("articulo","Código de Convivencia Ciudadana")}</b>", '
        f'Expte. N° {_num_exp(caso["numero"])}, tramitados ante esta Unidad, se lo/la '
        f'CITA a <b>{motivo_texto}</b> a celebrarse el día <b>{fecha_cit}</b> a las '
        f'<b>{hora_citacion} hs.</b> en la sede de este organismo sita en:')

    story.append(Paragraph(f"<b>{unidad}</b>", ParagraphStyle(
        "dir", parent=es["body"], alignment=TA_CENTER, fontSize=9, spaceAfter=6,
    )))

    story += _parrafo(es,
        'Se le hace saber que deberá concurrir munido/a de D.N.I. y que la incomparecencia '
        'injustificada podrá motivar la continuación del proceso en su rebeldía.')

    story += _parrafo(es,
        'Ante cualquier consulta comunicarse al: (0351) 4335361 (Unidad Norte) / '
        '4466707 (Unidad Sur).')

    story += _firma_block(es, fiscal, unidad_key)
    return _build_pdf(story)
