"""
Agrega 100 vacas en lactancia (producción 20-30 L/día) y 50 vacas secas.
Genera 45 días de registros de leche con variación diaria realista.
"""
import psycopg2
import random
from datetime import datetime, timedelta

DB_CONFIG = {
    "host": "localhost",
    "database": "granja_db",
    "user": "postgres",
    "password": "password",
}

RAZAS = ["Holstein", "Jersey", "Holando Argentino", "Shorthorn", "Normando"]


def run():
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()

    # Agregar columna categoria si no existe
    cur.execute("""
        ALTER TABLE tabla_vacas
        ADD COLUMN IF NOT EXISTS categoria VARCHAR(20) DEFAULT 'lactancia'
    """)

    # Obtener IDs de lotes y dietas
    cur.execute("SELECT lote_id, nombre_lote FROM tabla_lotes")
    lotes = {r[1]: r[0] for r in cur.fetchall()}

    cur.execute("SELECT dieta_id, nombre_dieta FROM tabla_dieta")
    dietas = {r[1]: r[0] for r in cur.fetchall()}

    lote_a    = lotes.get("Lote A")
    lote_b    = lotes.get("Lote B")
    lote_c    = lotes.get("Lote C")
    d_alta    = dietas.get("Alta Producción")
    d_media   = dietas.get("Media Producción")
    d_seca    = dietas.get("Seca / Preparto")

    # ── 100 vacas en lactancia ───────────────────────────
    vaca_ids_lact = []
    vacas_lact = []
    for i in range(1, 101):
        rfid     = f"LAC{i:04d}"
        nombre   = f"Lactancia {i:03d}"
        raza     = random.choice(RAZAS)
        lote_id  = lote_a if i <= 50 else lote_b
        dieta_id = d_alta if i <= 50 else d_media
        vacas_lact.append((rfid, nombre, raza, lote_id, dieta_id))

    for row in vacas_lact:
        cur.execute("""
            INSERT INTO tabla_vacas
                (rfid_code, nombre, raza, lote_id, dieta_id, estado, categoria)
            VALUES (%s, %s, %s, %s, %s, 'activa', 'lactancia')
            RETURNING vaca_id
        """, row)
        vaca_ids_lact.append(cur.fetchone()[0])

    # ── 50 vacas secas ───────────────────────────────────
    vacas_secas = []
    for i in range(1, 51):
        rfid     = f"SEC{i:04d}"
        nombre   = f"Seca {i:03d}"
        raza     = random.choice(RAZAS)
        vacas_secas.append((rfid, nombre, raza, lote_c, d_seca))

    cur.executemany("""
        INSERT INTO tabla_vacas
            (rfid_code, nombre, raza, lote_id, dieta_id, estado, categoria)
        VALUES (%s, %s, %s, %s, %s, 'activa', 'seca')
    """, vacas_secas)

    # ── Registros de leche: 45 días, 2 ordeñes/día ──────
    # Cada vaca tiene producción base entre 20 y 30 L/día.
    # Variación diaria ±15%.  Mañana = 55%, tarde = 45%.
    leche = []
    for vaca_id in vaca_ids_lact:
        base = random.uniform(20.0, 30.0)
        for dias_atras in range(45, 0, -1):
            dt         = datetime.now() - timedelta(days=dias_atras)
            diario     = base * random.uniform(0.85, 1.15)
            manana     = round(diario * 0.55, 2)
            tarde      = round(diario * 0.45, 2)
            ts_manana  = dt.replace(hour=6,  minute=random.randint(0, 30), second=0, microsecond=0)
            ts_tarde   = dt.replace(hour=15, minute=random.randint(0, 30), second=0, microsecond=0)
            leche.append((vaca_id, manana, ts_manana))
            leche.append((vaca_id, tarde,  ts_tarde))

    cur.executemany(
        "INSERT INTO tabla_leche (vaca_id, litros, fecha_hora) VALUES (%s, %s, %s)",
        leche,
    )

    conn.commit()
    cur.close()
    conn.close()

    print("EXITO:")
    print(f"  100 vacas en lactancia  (Lote A: 50 | Lote B: 50)")
    print(f"   50 vacas secas         (Lote C)")
    print(f"  {len(leche):,} registros de leche  (45 días × 2 ordeñes × 100 vacas)")
    print(f"  Producción: 20–30 L/día por vaca, ±15 % variación diaria")


if __name__ == "__main__":
    run()
