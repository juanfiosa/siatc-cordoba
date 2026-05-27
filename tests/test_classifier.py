import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import pytest
from classifier import clasificar_caso, tiempo_estimado_resolucion


class TestClasificarCaso:
    def test_carril_verde_primer_infractor_vecinal(self):
        clf = clasificar_caso("ruidos_molestos_nocturnos", 0, False)
        assert clf["carril"] == "verde"

    def test_carril_verde_sin_documentacion_primer_infractor(self):
        clf = clasificar_caso("transito_sin_documentacion", 0, False)
        assert clf["carril"] == "verde"

    def test_carril_amarillo_alcoholemia_sin_antecedentes(self):
        clf = clasificar_caso("transito_alcoholemia", 0, False)
        assert clf["carril"] == "amarillo"

    def test_carril_rojo_reincidente_con_lesiones(self):
        clf = clasificar_caso("riña_verbal_vecinal", 2, True, hay_lesiones=True)
        assert clf["carril"] == "rojo"

    def test_carril_rojo_agresion_fisica_reincidente(self):
        clf = clasificar_caso("agresion_fisica_leve", 2, True)
        assert clf["carril"] == "rojo"

    def test_carril_rojo_amenazas_resistencia(self):
        clf = clasificar_caso("amenazas_leves", 1, True, resistencia_autoridad=True)
        assert clf["carril"] == "rojo"

    def test_lesiones_sube_score(self):
        sin = clasificar_caso("ruidos_molestos_nocturnos", 0, False, hay_lesiones=False)
        con = clasificar_caso("ruidos_molestos_nocturnos", 0, False, hay_lesiones=True)
        assert con["score"] > sin["score"]

    def test_resistencia_sube_score(self):
        sin = clasificar_caso("transito_semaforo", 0, False, resistencia_autoridad=False)
        con = clasificar_caso("transito_semaforo", 0, False, resistencia_autoridad=True)
        assert con["score"] > sin["score"]

    def test_reincidencia_sube_score(self):
        cero = clasificar_caso("ruidos_molestos_nocturnos", 0, False)
        dos  = clasificar_caso("ruidos_molestos_nocturnos", 2, False)
        assert dos["score"] > cero["score"]

    def test_tipo_desconocido_no_falla(self):
        clf = clasificar_caso("tipo_inexistente_xyz", 0, False)
        assert clf["carril"] in ("verde", "amarillo", "rojo")

    def test_tiene_todos_los_campos(self):
        clf = clasificar_caso("consumo_alcohol_via_publica", 0, False)
        for campo in ["carril", "color", "icono", "accion", "descripcion",
                      "fundamento", "score", "categoria"]:
            assert campo in clf, f"Falta campo: {campo}"

    def test_carril_siempre_valido(self):
        for tipo in ["transito_sin_documentacion", "riña_verbal_vecinal",
                     "agresion_fisica_leve", "establecimiento_ruidos"]:
            clf = clasificar_caso(tipo, 0, False)
            assert clf["carril"] in ("verde", "amarillo", "rojo")

    def test_icono_corresponde_a_carril(self):
        mapeo = {"verde": "🟢", "amarillo": "🟡", "rojo": "🔴"}
        for tipo in ["ruidos_molestos_nocturnos", "transito_alcoholemia", "agresion_fisica_leve"]:
            clf = clasificar_caso(tipo, 2, True, hay_lesiones=True)
            assert clf["icono"] == mapeo[clf["carril"]]

    def test_fundamento_no_vacio(self):
        clf = clasificar_caso("animales_sueltos", 0, False)
        assert isinstance(clf["fundamento"], list) and len(clf["fundamento"]) > 0


class TestTiempoEstimado:
    def test_verde_mas_rapido_que_actual(self):
        t = tiempo_estimado_resolucion("verde")
        assert t["con_sistema_dias"] < t["actual_dias"]

    def test_amarillo_mas_rapido_que_actual(self):
        t = tiempo_estimado_resolucion("amarillo")
        assert t["con_sistema_dias"] < t["actual_dias"]

    def test_rojo_mas_rapido_que_actual(self):
        t = tiempo_estimado_resolucion("rojo")
        assert t["con_sistema_dias"] < t["actual_dias"]

    def test_campos_presentes(self):
        t = tiempo_estimado_resolucion("verde")
        for campo in ["actual_dias", "con_sistema_dias", "descripcion"]:
            assert campo in t

    def test_carril_invalido_no_falla(self):
        t = tiempo_estimado_resolucion("invalido")
        assert "con_sistema_dias" in t
