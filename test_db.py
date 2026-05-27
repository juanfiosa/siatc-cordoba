import sys
sys.path.insert(0, '.')
from database import init_db, guardar_causa, listar_causas, stats_generales, avanzar_estado
from classifier import clasificar_caso
from data_cordoba import CASOS_DEMO

init_db()
print("DB inicializada OK")

for cd in CASOS_DEMO:
    clf = clasificar_caso(cd["tipo"], cd["antecedentes"], False)
    cid = guardar_causa(
        {**cd, "victima": False, "lesiones": False, "resistencia": False, "domicilio": ""},
        clf, "Test fiscal"
    )
    print(f"  ID {cid}: [{clf['carril'].upper()}] {cd['imputado']}")

# Avanzar una causa
avanzar_estado(1, "notificada", "Test fiscal", "Notificación enviada por cédula")
print("Estado avanzado OK")

stats = stats_generales()
print(f"Total causas: {stats['total']}")
print(f"Por carril:   {stats['por_carril']}")
print(f"Por estado:   {stats['por_estado']}")
print(f"Personas:     {stats['personas']}")
print(f"Reincidentes: {stats['reincidentes']}")
print("Todo OK")
