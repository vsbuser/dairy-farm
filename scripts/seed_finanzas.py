"""Seed: 6 meses de movimientos financieros realistas para una granja lechera."""
import psycopg2, random
from datetime import date, timedelta

DB_CONFIG = dict(host="localhost", database="granja_db", user="postgres", password="password")
random.seed(7)

def run():
    conn = psycopg2.connect(**DB_CONFIG)
    cur  = conn.cursor()
    cur.execute("DELETE FROM tabla_finanzas")

    today = date.today()
    rows  = []

    for mes_atras in range(5, -1, -1):
        # Primer día del mes
        primer_dia = (today.replace(day=1) - timedelta(days=mes_atras * 30)).replace(day=1)

        def dia(n): return primer_dia + timedelta(days=n - 1)

        # ── INGRESOS ──────────────────────────────────────────────────────────
        # Venta de leche (2 liquidaciones por mes)
        litros1 = random.randint(3800, 5200)
        precio  = round(random.uniform(0.38, 0.45), 3)
        rows.append((dia(5),  "Ingreso", "Venta de leche",
                     f"Liquidación 1ª quincena — {litros1:,} litros a ${precio}/lt",
                     round(litros1 * precio, 2)))

        litros2 = random.randint(3600, 5000)
        rows.append((dia(20), "Ingreso", "Venta de leche",
                     f"Liquidación 2ª quincena — {litros2:,} litros a ${precio}/lt",
                     round(litros2 * precio, 2)))

        # Venta de terneros (eventual, ~2 meses de cada 6)
        if mes_atras in (4, 1):
            cant = random.randint(3, 7)
            precio_t = random.randint(280, 420)
            rows.append((dia(12), "Ingreso", "Venta de animales",
                         f"Venta de {cant} terneros a ${precio_t} c/u",
                         cant * precio_t))

        # Subsidio estatal (trimestral)
        if mes_atras in (5, 2):
            rows.append((dia(15), "Ingreso", "Subsidio o ayuda estatal",
                         "Subsidio trimestral producción lechera",
                         random.randint(1800, 3200)))

        # ── EGRESOS ───────────────────────────────────────────────────────────
        # Alimentación e insumos (compras quincenales)
        rows.append((dia(3),  "Egreso", "Alimentación e insumos",
                     f"Compra alfalfa y maíz — {random.randint(2000,3500)} kg",
                     random.randint(900, 1800)))
        rows.append((dia(17), "Egreso", "Alimentación e insumos",
                     f"Compra minerales y heno — {random.randint(800,1500)} kg",
                     random.randint(400, 900)))

        # Mano de obra (mensual)
        rows.append((dia(1),  "Egreso", "Mano de obra",
                     "Sueldos personal del mes",
                     random.randint(3200, 4500)))

        # Veterinario y salud (variable)
        if random.random() > 0.3:
            rows.append((dia(random.randint(5, 25)), "Egreso", "Veterinario y salud animal",
                         random.choice([
                             "Vacunación general del rodeo",
                             "Revisión reproductiva — honorarios Dr. Méndez",
                             "Tratamiento antiparasitario",
                             "Medicamentos y descornado",
                         ]),
                         random.randint(150, 600)))

        # Combustible (mensual)
        rows.append((dia(random.randint(8, 22)), "Egreso", "Combustible",
                     "Gasoil tractores y camioneta",
                     random.randint(280, 550)))

        # Mantenimiento maquinaria (eventual)
        if random.random() > 0.4:
            rows.append((dia(random.randint(6, 28)), "Egreso", "Mantenimiento de maquinaria",
                         random.choice([
                             "Servicio preventivo tractor",
                             "Reparación ordeñadora — taller Agrotécnica",
                             "Cambio correas y filtros compresor",
                             "Repuestos varios — ferretería agropecuaria",
                         ]),
                         random.randint(200, 1200)))

        # Servicios (mensual)
        rows.append((dia(10), "Egreso", "Servicios (luz, agua, gas)",
                     "Facturas de servicios del establecimiento",
                     random.randint(180, 420)))

        # Otros gastos (eventual)
        if random.random() > 0.5:
            rows.append((dia(random.randint(3, 28)), "Egreso", "Otros gastos",
                         random.choice([
                             "Materiales de limpieza e higiene",
                             "Herramientas menores",
                             "Papelería y análisis de laboratorio",
                             "Asesoramiento técnico",
                         ]),
                         random.randint(60, 320)))

    cur.executemany(
        "INSERT INTO tabla_finanzas (fecha, tipo, categoria, descripcion, monto) VALUES (%s,%s,%s,%s,%s)",
        rows,
    )
    conn.commit(); cur.close(); conn.close()
    print(f"OK: {len(rows)} movimientos insertados ({sum(1 for r in rows if r[1]=='Ingreso')} ingresos, {sum(1 for r in rows if r[1]=='Egreso')} egresos).")

if __name__ == "__main__":
    run()
