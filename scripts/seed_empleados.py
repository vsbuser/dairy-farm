"""Seed: empleados de una granja lechera con historial de pagos de 6 meses."""
import psycopg2, random
from datetime import date, timedelta

DB_CONFIG = dict(host="localhost", database="granja_db", user="postgres", password="password")
random.seed(55)

EMPLEADOS = [
    ("Carlos Mendoza",    "Capataz",                    85000, "+54 9 11 4523-8871", 730),
    ("Ana Gómez",         "Ordeñadora",                 58000, "+54 9 11 3345-2290", 540),
    ("Roberto Díaz",      "Ordeñador",                  58000, "+54 9 11 6612-4403", 480),
    ("Lucía Fernández",   "Ordeñadora",                 58000, "+54 9 11 7891-3312", 210),
    ("Miguel Torres",     "Tractorista",                62000, "+54 9 11 5523-9980", 900),
    ("Patricia Ruiz",     "Encargada de alimentación",  60000, "+54 9 11 4401-7765", 365),
    ("Diego Herrera",     "Veterinario de campo",       95000, "+54 9 11 3312-6654", 820),
    ("Silvia Castro",     "Administradora",             72000, "+54 9 11 8890-1123", 1100),
    ("Javier Morales",    "Peón rural",                 50000, "+54 9 11 2234-8897", 60),
    ("Florencia López",   "Peón rural",                 50000, "+54 9 11 9978-3345", 45),
    ("Hernán Romero",     "Tractorista",                62000, "+54 9 11 6634-5521", 730),
    ("Claudia Vargas",    "Encargada de sanidad",       68000, "+54 9 11 4456-7789", 550),
]

TIPOS_PAGO = ["Sueldo", "Adelanto", "Bono"]

def run():
    conn = psycopg2.connect(**DB_CONFIG)
    cur  = conn.cursor()
    cur.execute("DELETE FROM tabla_pagos")
    cur.execute("DELETE FROM tabla_empleados")

    today = date.today()
    emp_ids = []

    for nombre, cargo, sueldo, tel, dias_ingreso in EMPLEADOS:
        fecha_ing = today - timedelta(days=dias_ingreso)
        estado = "activo" if random.random() > 0.08 else "inactivo"
        cur.execute(
            "INSERT INTO tabla_empleados (nombre, cargo, sueldo_base, telefono, fecha_ingreso, estado) "
            "VALUES (%s,%s,%s,%s,%s,%s) RETURNING empleado_id",
            (nombre, cargo, sueldo, tel, fecha_ing, estado)
        )
        emp_ids.append((cur.fetchone()[0], sueldo, estado))

    pagos = []
    for mes_atras in range(5, -1, -1):
        primer_dia = (today.replace(day=1) - timedelta(days=mes_atras * 30)).replace(day=1)
        dia_pago   = primer_dia + timedelta(days=4)   # se paga el día 5

        for emp_id, sueldo, estado in emp_ids:
            if estado == "inactivo" and mes_atras == 0:
                continue
            # Sueldo mensual
            pagos.append((emp_id, dia_pago, "Sueldo",
                          round(sueldo * random.uniform(0.97, 1.0), 0),
                          f"Sueldo {primer_dia.strftime('%B %Y')}"))
            # Adelanto (~30% de los empleados por mes)
            if random.random() < 0.30:
                dia_adel = primer_dia + timedelta(days=random.randint(10, 20))
                monto_adel = round(sueldo * random.uniform(0.25, 0.40), 0)
                pagos.append((emp_id, dia_adel, "Adelanto",
                              monto_adel, "Adelanto de quincena"))
            # Bono (fin de año o productividad — ~20% y solo algunos meses)
            if random.random() < 0.15:
                dia_bono = primer_dia + timedelta(days=random.randint(25, 30))
                monto_bono = round(sueldo * random.uniform(0.10, 0.30), 0)
                pagos.append((emp_id, dia_bono, "Bono",
                              monto_bono, random.choice([
                                  "Bono por productividad",
                                  "Premio presentismo",
                                  "Gratificación temporada alta",
                              ])))

    cur.executemany(
        "INSERT INTO tabla_pagos (empleado_id, fecha, tipo, monto, descripcion) VALUES (%s,%s,%s,%s,%s)",
        pagos,
    )
    conn.commit(); cur.close(); conn.close()
    print(f"OK: {len(EMPLEADOS)} empleados y {len(pagos)} pagos insertados.")

if __name__ == "__main__":
    run()
