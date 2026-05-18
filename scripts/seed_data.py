"""Pobla la base de datos con datos de prueba realistas."""
import psycopg2
import random
from datetime import date, datetime, timedelta

DB_CONFIG = {
    "host": "localhost",
    "database": "granja_db",
    "user": "postgres",
    "password": "password"
}

LOTES = [
    ("Lote A", 30, "Vacas en alta lactancia"),
    ("Lote B", 25, "Vacas en lactancia media"),
    ("Lote C", 20, "Vacas secas y preparto"),
    ("Lote D", 15, "Vaquillonas en desarrollo"),
]

DIETAS = [
    ("Alta Producción",  "Para vacas con más de 25 lts/día. Alto en energía.", 45.50),
    ("Media Producción", "Vacas entre 15-25 lts/día. Equilibrada.",            32.00),
    ("Seca / Preparto",  "Transición 3 semanas antes del parto.",              38.75),
    ("Vaquillonas",      "Animales jóvenes en crecimiento.",                   28.00),
    ("Mantenimiento",    "Vacas fuera de producción.",                         20.00),
]

INSUMOS = [
    ("Maíz molido",       "kg", 4500.0, 0.28),
    ("Soja pellet",       "kg", 1800.0, 0.52),
    ("Heno de alfalfa",   "kg", 5000.0, 0.18),
    ("Silaje de maíz",    "kg", 12000.0, 0.12),
    ("Sal mineralizada",  "kg",  600.0, 0.65),
    ("Núcleo vitamínico", "kg",  350.0, 1.20),
    ("Melaza",            "kg",  900.0, 0.22),
    ("Expeller girasol",  "kg", 1200.0, 0.38),
    ("Urea forrajera",    "kg",  200.0, 0.55),
    ("Sorgo silaje",      "kg", 6000.0, 0.10),
]

NOMBRES_VACAS = [
    "Clavel", "Rosa", "Margarita", "Violeta", "Azucena",
    "Hortensia", "Magnolia", "Dalia", "Camelia", "Begonia",
    "Petunia", "Gardenia", "Lavanda", "Mimosa", "Orquídea",
    "Flor", "Paloma", "Luna", "Estrella", "Nube",
]

RAZAS = ["Holstein", "Jersey", "Shorthorn", "Normando", "Holando Argentino"]

VETERINARIOS = ["Dr. García", "Dra. López", "Dr. Martínez", "Dra. Sánchez"]

TIPOS_EVENTO = [
    "Vacunación", "Control rutinario", "Tratamiento antibiótico",
    "Enfermedad digestiva", "Parto asistido", "Revisión podal",
]


def seed():
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()

    # ── Lotes ────────────────────────────────────────────
    cur.executemany("""
        INSERT INTO tabla_lotes (nombre_lote, capacidad_max, descripcion)
        VALUES (%s, %s, %s)
        ON CONFLICT (nombre_lote) DO NOTHING
    """, LOTES)

    # ── Dietas ───────────────────────────────────────────
    cur.executemany("""
        INSERT INTO tabla_dieta (nombre_dieta, descripcion_dieta, costo_por_kilo)
        VALUES (%s, %s, %s)
        ON CONFLICT (nombre_dieta) DO NOTHING
    """, DIETAS)

    # ── Insumos ──────────────────────────────────────────
    cur.executemany("""
        INSERT INTO tabla_insumos (nombre_insumo, unidad, stock_actual_kg, costo_por_kg)
        VALUES (%s, %s, %s, %s)
        ON CONFLICT (nombre_insumo) DO NOTHING
    """, INSUMOS)

    # Obtener IDs
    cur.execute("SELECT lote_id, nombre_lote FROM tabla_lotes")
    lotes_ids = {r[1]: r[0] for r in cur.fetchall()}

    cur.execute("SELECT dieta_id, nombre_dieta FROM tabla_dieta")
    dietas_ids = {r[1]: r[0] for r in cur.fetchall()}

    # ── Vacas ────────────────────────────────────────────
    vacas = []
    lote_keys  = list(lotes_ids.keys())
    dieta_keys = list(dietas_ids.keys())
    for i, nombre in enumerate(NOMBRES_VACAS):
        rfid     = f"AR{200000 + i:06d}"
        raza     = RAZAS[i % len(RAZAS)]
        nacido   = date(2019, 1, 1) + timedelta(days=random.randint(0, 1460))
        lote     = lote_keys[i % len(lote_keys)]
        dieta    = dieta_keys[i % len(dieta_keys)]
        vacas.append((rfid, nombre, raza, nacido, lotes_ids[lote], dietas_ids[dieta]))

    cur.executemany("""
        INSERT INTO tabla_vacas (rfid_code, nombre, raza, fecha_nacimiento, lote_id, dieta_id)
        VALUES (%s, %s, %s, %s, %s, %s)
        ON CONFLICT (rfid_code) DO NOTHING
    """, vacas)

    cur.execute("SELECT vaca_id FROM tabla_vacas")
    vaca_ids = [r[0] for r in cur.fetchall()]

    # ── Registros de leche (últimos 45 días, 2 ordeñes/día) ──
    leche = []
    for dias_atras in range(45, 0, -1):
        base = datetime.now() - timedelta(days=dias_atras)
        for vid in vaca_ids:
            for hora in [6, 15]:
                litros = round(random.uniform(6, 30), 2)
                ts = base.replace(hour=hora, minute=random.randint(0, 30), second=0)
                leche.append((vid, litros, ts))

    cur.executemany("""
        INSERT INTO tabla_leche (vaca_id, litros, fecha_hora) VALUES (%s, %s, %s)
    """, leche)

    # ── Eventos de salud ─────────────────────────────────
    salud = []
    for _ in range(30):
        vid   = random.choice(vaca_ids)
        dias  = random.randint(1, 120)
        fecha = datetime.now() - timedelta(days=dias)
        tipo  = random.choice(TIPOS_EVENTO)
        costo = round(random.uniform(50, 800), 2)
        vet   = random.choice(VETERINARIOS)
        salud.append((vid, fecha, tipo, f"Registro: {tipo.lower()}.", vet, costo))

    cur.executemany("""
        INSERT INTO tabla_salud (vaca_id, fecha, tipo_evento, descripcion, veterinario, costo)
        VALUES (%s, %s, %s, %s, %s, %s)
    """, salud)

    # ── Usuarios ─────────────────────────────────────────
    usuarios = [
        ("Administrador", "admin"),
        ("Juan Pérez",    "operario"),
        ("María González","veterinaria"),
    ]
    cur.executemany("""
        INSERT INTO tabla_usuarios (nombre, rol) VALUES (%s, %s)
    """, usuarios)

    # ── Maquinaria ───────────────────────────────────────
    maquinas = [
        ("Tractor 1",        "Tractor",      "John Deere",  "5075E",       2018, "operativa"),
        ("Tractor 2",        "Tractor",      "New Holland", "T5.110",      2020, "operativa"),
        ("Ordeñadora A",     "Ordeñadora",   "DeLaval",     "Classic 300", 2019, "operativa"),
        ("Ordeñadora B",     "Ordeñadora",   "Westfalia",   "M200",        2017, "en mantenimiento"),
        ("Compresor",        "Compresor",    "Atlas Copco", "GA11",        2021, "operativa"),
        ("Generador",        "Generador",    "Caterpillar", "DE22E3",      2016, "operativa"),
        ("Mixer forrajero",  "Mixer",        "Seko",        "Duplo 15",    2019, "operativa"),
        ("Cargadora frontal","Cargadora",    "Bobcat",      "S650",        2022, "operativa"),
        ("Bomba de agua",    "Bomba",        "Grundfos",    "CM5-5",       2020, "fuera de servicio"),
        ("Cisterna",         "Cisterna",     "Indutec",     "5000L",       2015, "operativa"),
    ]
    cur.executemany("""
        INSERT INTO tabla_maquinaria (nombre, tipo, marca, modelo, anio, estado)
        VALUES (%s, %s, %s, %s, %s, %s)
    """, maquinas)

    cur.execute("SELECT maquina_id FROM tabla_maquinaria ORDER BY maquina_id")
    maquina_ids = [r[0] for r in cur.fetchall()]

    tipos_manten = ["Preventivo", "Correctivo", "Cambio de aceite", "Revisión general", "Reparación"]
    tecnicos_manten = ["Carlos Ríos", "Pedro Soto", "Taller Agro SA", "Servicio oficial"]

    mantenimientos = []
    for _ in range(25):
        mid   = random.choice(maquina_ids)
        dias  = random.randint(1, 180)
        fecha = datetime.now() - timedelta(days=dias)
        tipo  = random.choice(tipos_manten)
        costo = round(random.uniform(150, 3500), 2)
        tec   = random.choice(tecnicos_manten)
        prox  = (fecha + timedelta(days=random.randint(60, 180))).date()
        horas = round(random.uniform(50, 800), 1)
        mantenimientos.append((mid, fecha, tipo, f"Trabajo: {tipo.lower()}.", costo, tec, prox, horas))

    cur.executemany("""
        INSERT INTO tabla_mantenimiento
            (maquina_id, fecha, tipo_mantencion, descripcion, costo, tecnico, proximo_mantenimiento, horas_uso)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
    """, mantenimientos)

    conn.commit()
    cur.close()
    conn.close()

    print("EXITO: Datos de prueba cargados")
    print(f"  {len(LOTES)} lotes | {len(DIETAS)} dietas | {len(INSUMOS)} insumos")
    print(f"  {len(vacas)} vacas | {len(leche)} registros leche | {len(salud)} eventos salud")
    print(f"  {len(maquinas)} máquinas | {len(mantenimientos)} eventos de mantenimiento")


if __name__ == "__main__":
    seed()
