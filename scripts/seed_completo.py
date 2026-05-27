"""
Seed completo: rellena todas las pestañas que tienen datos insuficientes.

  1. Vacas   → asigna grupo a las 170 vacas sin grupo (proporcional a n de cada dieta)
  2. Salud   → agrega ~200 registros variados en los últimos 12 meses
  3. Insumos → actualiza los 10 insumos con stock = 0
  4. Maquinaria → agrega registros de mantenimiento faltantes
"""

import psycopg2, random
from datetime import date, timedelta

DB_CONFIG = dict(host="localhost", database="granja_db", user="postgres", password="password")
random.seed(99)

today = date.today()

def dia_random(desde_dias_atras: int, hasta_dias_atras: int) -> date:
    return today - timedelta(days=random.randint(hasta_dias_atras, desde_dias_atras))

# ─────────────────────────────────────────────────────────────────────────────
# 1. VACAS SIN GRUPO
# ─────────────────────────────────────────────────────────────────────────────
def seed_grupos(cur):
    cur.execute("SELECT vaca_id FROM tabla_vacas WHERE grupo IS NULL ORDER BY vaca_id")
    vacas_sin_grupo = [r[0] for r in cur.fetchall()]
    if not vacas_sin_grupo:
        print("  [grupos] Todas las vacas ya tienen grupo.")
        return

    # Distribución proporcional según n de cada dieta
    dietas_n = {
        "novilhas": 33, "alta": 46, "baixa": 19, "seco": 26,
        "corte": 55, "bezerro +250": 32, "bezerro -250": 74, "castrado": 28,
    }
    total_n = sum(dietas_n.values())
    total_v = len(vacas_sin_grupo)

    asignaciones = {}
    asignadas    = 0
    grupos_lista = list(dietas_n.keys())
    for i, grupo in enumerate(grupos_lista):
        if i == len(grupos_lista) - 1:
            cant = total_v - asignadas
        else:
            cant = round(dietas_n[grupo] / total_n * total_v)
        asignaciones[grupo] = cant
        asignadas += cant

    random.shuffle(vacas_sin_grupo)
    idx = 0
    for grupo, cant in asignaciones.items():
        batch = vacas_sin_grupo[idx: idx + cant]
        for vid in batch:
            cur.execute("UPDATE tabla_vacas SET grupo=%s WHERE vaca_id=%s", (grupo, vid))
        idx += cant

    print(f"  [grupos] {total_v} vacas asignadas a grupos: {asignaciones}")

# ─────────────────────────────────────────────────────────────────────────────
# 2. SALUD
# ─────────────────────────────────────────────────────────────────────────────
VETS = [
    "Dr. Ramírez", "Dra. Flores", "Dr. Aguirre",
    "Dra. Méndez", "Dr. Soto", "Consultora Agrovital",
]

EVENTOS_SALUD = {
    "Vacunación": [
        ("Vacunación antiaftosa — dosis anual obligatoria", 45, 90),
        ("Vacunación IBR/DVB — refuerzo semestral", 60, 120),
        ("Vacunación Brucelosis — hembras jóvenes", 30, 80),
        ("Vacunación Leptospirosis + Clostridiales", 50, 100),
        ("Vacunación Carbunclo sintomático", 35, 70),
    ],
    "Control rutinario": [
        ("Revisión general — peso, estado corporal y mucosas normales", 0, 20),
        ("Control podal — sin alteraciones", 15, 30),
        ("Revisión reproductiva — ciclo normal detectado", 20, 50),
        ("Control de producción individual — dentro del rango esperado", 0, 15),
        ("Chequeo ecográfico — sin hallazgos relevantes", 30, 70),
        ("Control de ubres — sin mastitis detectada", 10, 25),
    ],
    "Tratamiento": [
        ("Tratamiento mastitis clínica — aplicación intramamaria antibiótico", 80, 180),
        ("Tratamiento antiparasitario — ivermectina + fasciolicida", 40, 90),
        ("Tratamiento podal — dermatitis interdigital, curación y vendaje", 60, 120),
        ("Tratamiento metritis aguda — antibiótico sistémico 5 días", 150, 280),
        ("Tratamiento cetosis — propilénglicol oral + vitaminas", 50, 100),
        ("Tratamiento hipocalcemia — calcio EV + oral", 90, 160),
    ],
    "Enfermedad": [
        ("Diarrea aguda — rehidratación oral, recuperación favorable", 40, 100),
        ("Neumonía leve — antibiótico + antiinflamatorio, evolución positiva", 120, 250),
        ("Retención de placenta — extracción manual + antibiótico", 100, 200),
        ("Timpanismo — trocarización de emergencia, sin secuelas", 80, 180),
        ("Claudicación — úlcera de suela grado 2, tratamiento podal", 70, 140),
        ("Mastitis subclínica — CMT positivo, tratamiento localizado", 60, 120),
    ],
    "Parto asistido": [
        ("Distocia leve — extracción manual del ternero, madre sin complicaciones", 120, 200),
        ("Parto gemelar — asistencia en segundo ternero, ambos viables", 100, 180),
        ("Parto gemelar — segundo feto en presentación anormal, se resolvió", 150, 250),
        ("Distocia por exceso de tamaño — feto extraído con cadenas, madre recuperada", 200, 350),
    ],
    "Cirugía": [
        ("Cesárea de emergencia — madre y cría recuperadas sin complicaciones", 800, 1500),
        ("Cirugía de desplazamiento de abomaso — exitosa, animal dado de alta a 72hs", 600, 1200),
        ("Amputación de dígito — claudicación severa grado 4 sin respuesta a tratamiento", 400, 800),
        ("Corrección quirúrgica de prolapso uterino — pronóstico reservado", 500, 1000),
    ],
}

def seed_salud(cur):
    cur.execute("SELECT vaca_id FROM tabla_vacas WHERE estado='activa' ORDER BY vaca_id")
    vaca_ids = [r[0] for r in cur.fetchall()]

    registros = []

    # Distribución: vacunaciones masivas trimestrales
    for q in range(4):         # 4 trimestres en el año
        dias_base = q * 90
        # Vacunación general ~ 60% del rodeo
        muestra = random.sample(vaca_ids, k=int(len(vaca_ids) * 0.60))
        for vid in muestra:
            desc, cmin, cmax = random.choice(EVENTOS_SALUD["Vacunación"])
            fecha = today - timedelta(days=dias_base + random.randint(5, 25))
            registros.append((vid, "Vacunación", fecha,
                              desc, random.choice(VETS), random.randint(cmin, cmax)))

    # Controles rutinarios mensuales (~15 animales/mes revisados)
    for mes in range(12):
        muestra = random.sample(vaca_ids, k=15)
        for vid in muestra:
            desc, cmin, cmax = random.choice(EVENTOS_SALUD["Control rutinario"])
            fecha = today - timedelta(days=mes * 30 + random.randint(0, 20))
            registros.append((vid, "Control rutinario", fecha,
                              desc, random.choice(VETS), random.randint(cmin, cmax)))

    # Tratamientos (~8/mes)
    for mes in range(10):
        muestra = random.sample(vaca_ids, k=8)
        for vid in muestra:
            desc, cmin, cmax = random.choice(EVENTOS_SALUD["Tratamiento"])
            fecha = today - timedelta(days=mes * 30 + random.randint(0, 25))
            registros.append((vid, "Tratamiento", fecha,
                              desc, random.choice(VETS), random.randint(cmin, cmax)))

    # Enfermedades (~4/mes)
    for mes in range(10):
        muestra = random.sample(vaca_ids, k=4)
        for vid in muestra:
            desc, cmin, cmax = random.choice(EVENTOS_SALUD["Enfermedad"])
            fecha = today - timedelta(days=mes * 30 + random.randint(0, 28))
            registros.append((vid, "Enfermedad", fecha,
                              desc, random.choice(VETS), random.randint(cmin, cmax)))

    # Partos asistidos (~3/mes)
    for mes in range(10):
        muestra = random.sample(vaca_ids, k=3)
        for vid in muestra:
            desc, cmin, cmax = random.choice(EVENTOS_SALUD["Parto asistido"])
            fecha = today - timedelta(days=mes * 30 + random.randint(0, 25))
            registros.append((vid, "Parto asistido", fecha,
                              desc, random.choice(VETS), random.randint(cmin, cmax)))

    # Cirugías (~1 por 2 meses)
    for mes in range(0, 12, 2):
        vid = random.choice(vaca_ids)
        desc, cmin, cmax = random.choice(EVENTOS_SALUD["Cirugía"])
        fecha = today - timedelta(days=mes * 30 + random.randint(5, 25))
        registros.append((vid, "Cirugía", fecha,
                          desc, random.choice(VETS), random.randint(cmin, cmax)))

    cur.executemany("""
        INSERT INTO tabla_salud (vaca_id, tipo_evento, fecha, descripcion, veterinario, costo)
        VALUES (%s, %s, %s, %s, %s, %s)
    """, registros)
    print(f"  [salud] {len(registros)} registros nuevos agregados.")

# ─────────────────────────────────────────────────────────────────────────────
# 3. INSUMOS CON STOCK = 0
# ─────────────────────────────────────────────────────────────────────────────
INSUMOS_STOCK = {
    "Adsorbente":           (120,    6.50),
    "Capim Acu":            (3500,   0.12),
    "Caroco Soja/PPA":      (2200,   0.48),
    "Cevada":               (1800,   0.39),
    "Farelo Soja/Algodao":  (2500,   0.62),
    "Nucleo Mineral":       (350,    4.20),
    "Silagem de Milho":     (18000,  0.07),
    "Sorgo":                (4000,   0.28),
    "Tifton":               (6500,   0.11),
    "Ureia":                (280,    1.35),
}

def seed_insumos(cur):
    actualizados = 0
    for nombre, (stock, precio) in INSUMOS_STOCK.items():
        # Variación aleatoria ±15%
        stock_v  = round(stock  * random.uniform(0.85, 1.15), 1)
        precio_v = round(precio * random.uniform(0.92, 1.08), 2)
        cur.execute("""
            UPDATE tabla_insumos
               SET stock_actual_kg = %s, costo_por_kg = %s
             WHERE nombre_insumo = %s AND stock_actual_kg = 0
        """, (stock_v, precio_v, nombre))
        if cur.rowcount:
            actualizados += 1
    print(f"  [insumos] {actualizados} insumos actualizados con stock y precio.")

# ─────────────────────────────────────────────────────────────────────────────
# 4. MANTENIMIENTO ADICIONAL
# ─────────────────────────────────────────────────────────────────────────────
MANT_EXTRAS = [
    ("Tractor 1",       "Preventivo",        "Servicio de 500 hs — aceite, filtros y revisión general",                     "Taller AgriService",  380, 90),
    ("Tractor 2",       "Cambio de aceite",  "Cambio de aceite hidráulico y diferencial",                                   "Taller Los Álamos",   290, 60),
    ("Ordeñadora A",    "Revisión general",  "Calibración de vacío y pulsadores — todo en norma",                           "Técnico DeLaval",     420, 45),
    ("Ordeñadora B",    "Correctivo",        "Reemplazo de mangueras y pezoneras dañadas",                                  "Técnico Westfalia",   510, 30),
    ("Compresor",       "Preventivo",        "Cambio de aceite compresor y revisión de válvulas",                           "Taller AgriService",  180, 70),
    ("Generador",       "Revisión general",  "Prueba de carga y revisión de alternador — sin fallas",                       "Electro Campo",       240, 60),
    ("Mixer forrajero", "Reparación",        "Reemplazo de cuchillas de corte — desgaste avanzado",                         "Herrería Agro",       650, 45),
    ("Cargadora frontal","Cambio de aceite", "Cambio de aceite hidráulico y ajuste de mangueras",                           "Taller Los Álamos",   220, 55),
    ("Bomba de agua",   "Correctivo",        "Reemplazo de rodete y sello — bomba fuera de servicio por rotura",            "Bombas del Sur",      480, 20),
    ("Cisterna",        "Preventivo",        "Limpieza y desinfección interior — revisión de válvulas y tapas",             "Personal propio",      90, 90),
    ("Tractor 1",       "Reparación",        "Reparación de sistema de frenos — cilindro maestro reemplazado",              "Taller AgriService",  720, 45),
    ("Ordeñadora A",    "Correctivo",        "Falla en unidad de lavado automático — reparada, sin pérdida de producción",  "Técnico DeLaval",     380, 20),
    ("Generador",       "Calibración",       "Calibración de regulador de tensión — tensión estabilizada a 220V",           "Electro Campo",       150, 40),
    ("Mixer forrajero", "Preventivo",        "Lubricación de cadenas y revisión de caja reductora",                         "Personal propio",      60, 60),
    ("Tractor 2",       "Revisión general",  "Revisión de sistema eléctrico y ajuste de dirección",                         "Taller Los Álamos",   310, 30),
]

def seed_mantenimiento(cur):
    cur.execute("SELECT maquina_id, nombre FROM tabla_maquinaria")
    maq_map = {r[1]: r[0] for r in cur.fetchall()}

    registros = []
    for nombre, tipo, desc, tecnico, costo, dias_atras in MANT_EXTRAS:
        maq_id = maq_map.get(nombre)
        if not maq_id:
            continue
        fecha      = today - timedelta(days=dias_atras + random.randint(0, 15))
        prox_mant  = fecha + timedelta(days=random.choice([60, 90, 120, 180]))
        horas_uso  = round(random.uniform(200, 4800), 1)
        costo_v    = costo * random.uniform(0.90, 1.10)
        registros.append((maq_id, tipo, fecha, desc, tecnico,
                          round(costo_v, 0), prox_mant, horas_uso))

    cur.executemany("""
        INSERT INTO tabla_mantenimiento
            (maquina_id, tipo_mantencion, fecha, descripcion, tecnico,
             costo, proximo_mantenimiento, horas_uso)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
    """, registros)
    print(f"  [mantenimiento] {len(registros)} registros nuevos agregados.")

# ─────────────────────────────────────────────────────────────────────────────
def run():
    conn = psycopg2.connect(**DB_CONFIG)
    cur  = conn.cursor()
    print("Iniciando seed completo…")
    seed_grupos(cur)
    seed_salud(cur)
    seed_insumos(cur)
    seed_mantenimiento(cur)
    conn.commit()
    cur.close(); conn.close()
    print("Listo.")

if __name__ == "__main__":
    run()
