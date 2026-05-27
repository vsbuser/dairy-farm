"""
Seed: 50 vacas con historial reproductivo variado.

Escenarios cubiertos:
  - Fertilización reciente → parto esperado en los próximos 30 días
  - Fertilización → parto exitoso registrado
  - Fertilización → parto gemelar
  - Fertilización → aborto
  - Fertilización → cría muerta
  - Ciclo completo: parto pasado + nueva fertilización (prenada de nuevo)
  - Sólo fertilización sin parto aún (en curso)
  - Fertilizaciones con IA y con Monta Natural
"""

import psycopg2
import random
from datetime import date, timedelta

GESTACION = 283

DB_CONFIG = dict(host="localhost", database="granja_db", user="postgres", password="password")

TIPOS_FERT   = ["Inseminación Artificial", "Monta Natural"]
RESULTADOS   = ["Exitoso", "Gemelar", "Aborto", "Cría muerta"]
SEXOS        = ["hembra", "macho"]
OBS_FERT     = [
    "Semen importado lote A", "Toro 'Relampago' del campo vecino",
    "Dosis n.º 3 de catálogo", "Segunda inseminación del ciclo",
    "Sincronización hormonal previa", None, None, None,
]
OBS_PARTO    = [
    "Parto sin complicaciones", "Se requirió asistencia veterinaria",
    "Cría vigorosa, mamadera al nacer", "Gemelar — ambas crías vivas",
    "Gemelar — solo una cría sobrevivió", None, None,
]

random.seed(42)


def run():
    conn = psycopg2.connect(**DB_CONFIG)
    cur  = conn.cursor()

    # Limpiar datos previos de prueba (opcional — comentar para acumular)
    cur.execute("DELETE FROM tabla_reproduccion")

    # Tomar 50 vacas activas al azar
    cur.execute("SELECT vaca_id, nombre FROM tabla_vacas WHERE estado='activa' ORDER BY RANDOM() LIMIT 50")
    vacas = cur.fetchall()

    today = date.today()
    registros = []

    for idx, (vaca_id, nombre) in enumerate(vacas):
        escenario = idx % 10   # 10 escenarios distintos, 5 vacas cada uno

        if escenario == 0:
            # Próximo parto en < 30 días
            dias_atras = GESTACION - random.randint(5, 29)
            f_fert = today - timedelta(days=dias_atras)
            f_parto_esp = f_fert + timedelta(days=GESTACION)
            registros.append((vaca_id, "Fertilización", f_fert,
                               random.choice(TIPOS_FERT), f_parto_esp,
                               None, None, None, random.choice(OBS_FERT)))

        elif escenario == 1:
            # Próximo parto en 30-90 días
            dias_atras = GESTACION - random.randint(30, 90)
            f_fert = today - timedelta(days=dias_atras)
            f_parto_esp = f_fert + timedelta(days=GESTACION)
            registros.append((vaca_id, "Fertilización", f_fert,
                               random.choice(TIPOS_FERT), f_parto_esp,
                               None, None, None, random.choice(OBS_FERT)))

        elif escenario == 2:
            # Parto exitoso registrado
            f_fert = today - timedelta(days=GESTACION + random.randint(10, 60))
            f_parto_esp = f_fert + timedelta(days=GESTACION)
            f_parto = f_parto_esp + timedelta(days=random.randint(-3, 3))
            sexo   = random.choice(SEXOS)
            peso   = round(random.uniform(30, 48), 1)
            registros.append((vaca_id, "Fertilización", f_fert,
                               random.choice(TIPOS_FERT), f_parto_esp,
                               None, None, None, random.choice(OBS_FERT)))
            registros.append((vaca_id, "Parto", f_parto,
                               None, None,
                               "Exitoso", sexo, peso, random.choice(OBS_PARTO)))

        elif escenario == 3:
            # Parto gemelar
            f_fert = today - timedelta(days=GESTACION + random.randint(30, 120))
            f_parto_esp = f_fert + timedelta(days=GESTACION)
            f_parto = f_parto_esp + timedelta(days=random.randint(-5, 5))
            registros.append((vaca_id, "Fertilización", f_fert,
                               "Inseminación Artificial", f_parto_esp,
                               None, None, None, "Sincronización hormonal previa"))
            registros.append((vaca_id, "Parto", f_parto,
                               None, None,
                               "Gemelar", random.choice(SEXOS),
                               round(random.uniform(24, 36), 1),
                               "Gemelar — ambas crías vivas"))

        elif escenario == 4:
            # Aborto
            f_fert = today - timedelta(days=random.randint(90, 200))
            f_parto_esp = f_fert + timedelta(days=GESTACION)
            f_aborto = f_fert + timedelta(days=random.randint(60, 180))
            registros.append((vaca_id, "Fertilización", f_fert,
                               random.choice(TIPOS_FERT), f_parto_esp,
                               None, None, None, random.choice(OBS_FERT)))
            registros.append((vaca_id, "Parto", f_aborto,
                               None, None,
                               "Aborto", None, None,
                               "Pérdida gestacional — revisión veterinaria"))

        elif escenario == 5:
            # Cría muerta
            f_fert = today - timedelta(days=GESTACION + random.randint(5, 40))
            f_parto_esp = f_fert + timedelta(days=GESTACION)
            f_parto = f_parto_esp + timedelta(days=random.randint(-2, 4))
            registros.append((vaca_id, "Fertilización", f_fert,
                               random.choice(TIPOS_FERT), f_parto_esp,
                               None, None, None, random.choice(OBS_FERT)))
            registros.append((vaca_id, "Parto", f_parto,
                               None, None,
                               "Cría muerta", random.choice(SEXOS),
                               round(random.uniform(25, 40), 1),
                               "Cría nació sin vida — autopsia solicitada"))

        elif escenario == 6:
            # Ciclo completo: parto pasado + nueva preñez
            f_fert1 = today - timedelta(days=GESTACION + random.randint(120, 300))
            f_parto1 = f_fert1 + timedelta(days=GESTACION + random.randint(-3, 3))
            f_fert2 = f_parto1 + timedelta(days=random.randint(45, 90))
            f_parto2_esp = f_fert2 + timedelta(days=GESTACION)
            registros.append((vaca_id, "Fertilización", f_fert1,
                               "Monta Natural", f_fert1 + timedelta(days=GESTACION),
                               None, None, None, None))
            registros.append((vaca_id, "Parto", f_parto1,
                               None, None,
                               "Exitoso", random.choice(SEXOS),
                               round(random.uniform(30, 46), 1),
                               "Parto anterior del ciclo"))
            registros.append((vaca_id, "Fertilización", f_fert2,
                               "Inseminación Artificial", f_parto2_esp,
                               None, None, None, "Nueva preñez post-parto"))

        elif escenario == 7:
            # Parto exitoso reciente + aún no refertilizada
            f_fert = today - timedelta(days=GESTACION + random.randint(10, 50))
            f_parto_esp = f_fert + timedelta(days=GESTACION)
            f_parto = f_parto_esp + timedelta(days=random.randint(-2, 2))
            registros.append((vaca_id, "Fertilización", f_fert,
                               random.choice(TIPOS_FERT), f_parto_esp,
                               None, None, None, random.choice(OBS_FERT)))
            registros.append((vaca_id, "Parto", f_parto,
                               None, None,
                               "Exitoso", random.choice(SEXOS),
                               round(random.uniform(33, 50), 1),
                               "Parto reciente — pendiente nueva fertilización"))

        elif escenario == 8:
            # Fertilización antigua (parto esperado ya pasó, sin registro de parto)
            f_fert = today - timedelta(days=GESTACION + random.randint(1, 15))
            f_parto_esp = f_fert + timedelta(days=GESTACION)
            registros.append((vaca_id, "Fertilización", f_fert,
                               random.choice(TIPOS_FERT), f_parto_esp,
                               None, None, None, "Parto esperado — pendiente registro"))

        else:
            # Escenario 9: sólo fertilización reciente (< 60 días), sin parto aún
            f_fert = today - timedelta(days=random.randint(5, 60))
            f_parto_esp = f_fert + timedelta(days=GESTACION)
            registros.append((vaca_id, "Fertilización", f_fert,
                               random.choice(TIPOS_FERT), f_parto_esp,
                               None, None, None, random.choice(OBS_FERT)))

    cur.executemany("""
        INSERT INTO tabla_reproduccion
            (vaca_id, tipo_evento, fecha_evento, tipo_fertilizacion,
             fecha_parto_esperado, resultado_parto, sexo_cria, peso_cria_kg, observaciones)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
    """, registros)

    conn.commit()
    cur.close(); conn.close()
    print(f"OK: {len(registros)} registros insertados para 50 vacas.")


if __name__ == "__main__":
    run()
