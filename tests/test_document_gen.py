import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import pytest
from datetime import datetime
from document_gen import (
    generar_dictamen_mediacion,
    generar_dictamen_suspension,
    generar_citacion,
    generar_resumen_ejecutivo,
)
from classifier import clasificar_caso

CASO_VECINAL = {
    "numero": "2024-UCN-00001",
    "tipo": "ruidos_molestos_nocturnos",
    "imputado": "Pérez, Juan Carlos",
    "dni": "30.111.222",
    "edad": 35,
    "antecedentes": 0,
    "descripcion": "Música a alto volumen en horario nocturno.",
    "unidad": "norte",
}
CLF_VERDE = clasificar_caso(CASO_VECINAL["tipo"], 0, False)

CASO_ALCOHOL = {**CASO_VECINAL,
    "numero": "2024-UCN-00002",
    "tipo": "transito_alcoholemia",
    "antecedentes": 0,
}
CLF_AMARILLO = clasificar_caso(CASO_ALCOHOL["tipo"], 0, False)

CASO_VIOLENTO = {**CASO_VECINAL,
    "numero": "2024-UCN-00003",
    "tipo": "agresion_fisica_leve",
    "antecedentes": 2,
}
CLF_ROJO = clasificar_caso(CASO_VIOLENTO["tipo"], 2, True)


class TestDictamenMediacion:
    def test_retorna_string_no_vacio(self):
        doc = generar_dictamen_mediacion(CASO_VECINAL, CLF_VERDE, "Dra. Test", "norte")
        assert isinstance(doc, str) and len(doc) > 200

    def test_contiene_nombre_imputado(self):
        doc = generar_dictamen_mediacion(CASO_VECINAL, CLF_VERDE, "Dra. Test", "norte")
        assert "Pérez" in doc or "PÉREZ" in doc.upper()

    def test_contiene_dni(self):
        doc = generar_dictamen_mediacion(CASO_VECINAL, CLF_VERDE, "Dra. Test", "norte")
        assert "30.111.222" in doc

    def test_menciona_ley_mediacion(self):
        doc = generar_dictamen_mediacion(CASO_VECINAL, CLF_VERDE, "Dra. Test", "norte")
        assert "10.543" in doc

    def test_contiene_numero_expediente(self):
        doc = generar_dictamen_mediacion(CASO_VECINAL, CLF_VERDE, "Dra. Test", "norte")
        assert "2024" in doc

    def test_fecha_audiencia_personalizada_mes(self):
        fecha = datetime(2026, 12, 25)
        doc = generar_dictamen_mediacion(CASO_VECINAL, CLF_VERDE, "Dra. Test", "norte",
                                         fecha_audiencia_dt=fecha)
        assert "diciembre" in doc and "2026" in doc

    def test_hora_audiencia_personalizada(self):
        fecha = datetime(2026, 3, 10)
        doc = generar_dictamen_mediacion(CASO_VECINAL, CLF_VERDE, "Dra. Test", "norte",
                                         fecha_audiencia_dt=fecha, hora_audiencia="14:30")
        assert "14:30" in doc

    def test_unidad_norte_aparece(self):
        doc = generar_dictamen_mediacion(CASO_VECINAL, CLF_VERDE, "Dra. Test", "norte")
        assert "Norte" in doc or "NORTE" in doc.upper() or "Alta Córdoba" in doc


class TestDictamenSuspension:
    def test_retorna_string_no_vacio(self):
        doc = generar_dictamen_suspension(CASO_ALCOHOL, CLF_AMARILLO, "Dra. Test", "norte")
        assert isinstance(doc, str) and len(doc) > 200

    def test_contiene_nombre_imputado(self):
        doc = generar_dictamen_suspension(CASO_ALCOHOL, CLF_AMARILLO, "Dra. Test", "norte")
        assert "Pérez" in doc or "PÉREZ" in doc.upper()

    def test_contiene_condiciones(self):
        doc = generar_dictamen_suspension(CASO_ALCOHOL, CLF_AMARILLO, "Dra. Test", "norte")
        assert "condicion" in doc.lower() or "prueba" in doc.lower()

    def test_alcoholemia_incluye_condicion_especifica(self):
        doc = generar_dictamen_suspension(CASO_ALCOHOL, CLF_AMARILLO, "Dra. Test", "norte")
        assert "alcohol" in doc.lower()

    def test_contiene_meses_prueba(self):
        doc = generar_dictamen_suspension(CASO_ALCOHOL, CLF_AMARILLO, "Dra. Test", "norte")
        assert "meses" in doc.lower()


class TestCitacion:
    def test_retorna_string_no_vacio(self):
        doc = generar_citacion(CASO_VECINAL, "Dra. Test", "norte")
        assert isinstance(doc, str) and len(doc) > 100

    def test_contiene_nombre_imputado(self):
        doc = generar_citacion(CASO_VECINAL, "Dra. Test", "norte")
        assert "Pérez" in doc or "PÉREZ" in doc.upper()

    def test_contiene_dni(self):
        doc = generar_citacion(CASO_VECINAL, "Dra. Test", "norte")
        assert "30.111.222" in doc

    def test_motivo_mediacion(self):
        doc = generar_citacion(CASO_VECINAL, "Dra. Test", "norte", motivo="mediacion")
        assert "mediaci" in doc.lower()

    def test_motivo_audiencia_default(self):
        doc = generar_citacion(CASO_VECINAL, "Dra. Test", "norte")
        assert "audiencia" in doc.lower()

    def test_fecha_personalizada(self):
        fecha = datetime(2026, 7, 4)
        doc = generar_citacion(CASO_VECINAL, "Dra. Test", "norte", fecha_citacion_dt=fecha)
        assert "julio" in doc and "2026" in doc

    def test_hora_personalizada(self):
        fecha = datetime(2026, 7, 4)
        doc = generar_citacion(CASO_VECINAL, "Dra. Test", "norte",
                                fecha_citacion_dt=fecha, hora_citacion="11:00")
        assert "11:00" in doc


class TestResumenEjecutivo:
    def test_retorna_string_no_vacio(self):
        doc = generar_resumen_ejecutivo(CASO_VECINAL, CLF_VERDE)
        assert isinstance(doc, str) and len(doc) > 50

    def test_contiene_numero_caso(self):
        doc = generar_resumen_ejecutivo(CASO_VECINAL, CLF_VERDE)
        assert "2024-UCN-00001" in doc

    def test_contiene_clasificacion_carril(self):
        doc = generar_resumen_ejecutivo(CASO_VECINAL, CLF_VERDE)
        assert "VERDE" in doc.upper()

    def test_contiene_nombre_imputado(self):
        doc = generar_resumen_ejecutivo(CASO_VECINAL, CLF_VERDE)
        assert "Pérez" in doc

    def test_contiene_dni(self):
        doc = generar_resumen_ejecutivo(CASO_VECINAL, CLF_VERDE)
        assert "30.111.222" in doc
