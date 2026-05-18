import psycopg2

DB_CONFIG = {
    "host": "localhost",
    "database": "granja_db",
    "user": "postgres",
    "password": "password"
}

COMMANDS = [
    """CREATE TABLE IF NOT EXISTS tabla_lotes (
        lote_id      SERIAL PRIMARY KEY,
        nombre_lote  VARCHAR(50) UNIQUE NOT NULL,
        capacidad_max INTEGER,
        descripcion  TEXT
    )""",
    """CREATE TABLE IF NOT EXISTS tabla_dieta (
        dieta_id        SERIAL PRIMARY KEY,
        nombre_dieta    VARCHAR(100) UNIQUE NOT NULL,
        descripcion_dieta TEXT,
        costo_por_kilo  NUMERIC(10,2)
    )""",
    """CREATE TABLE IF NOT EXISTS tabla_insumos (
        insumo_id      SERIAL PRIMARY KEY,
        nombre_insumo  VARCHAR(100) UNIQUE NOT NULL,
        unidad         VARCHAR(20) DEFAULT 'kg',
        stock_actual_kg NUMERIC(10,2) DEFAULT 0,
        costo_por_kg   NUMERIC(10,2)
    )""",
    """CREATE TABLE IF NOT EXISTS tabla_vacas (
        vaca_id         SERIAL PRIMARY KEY,
        rfid_code       VARCHAR(50) UNIQUE,
        nombre          VARCHAR(100) NOT NULL,
        raza            VARCHAR(50),
        fecha_nacimiento DATE,
        lote_id         INTEGER REFERENCES tabla_lotes(lote_id),
        dieta_id        INTEGER REFERENCES tabla_dieta(dieta_id),
        estado          VARCHAR(20) DEFAULT 'activa'
    )""",
    """CREATE TABLE IF NOT EXISTS tabla_leche (
        registro_id SERIAL PRIMARY KEY,
        vaca_id     INTEGER REFERENCES tabla_vacas(vaca_id),
        litros      NUMERIC(5,2) NOT NULL,
        fecha_hora  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )""",
    """CREATE TABLE IF NOT EXISTS tabla_salud (
        registro_id SERIAL PRIMARY KEY,
        vaca_id     INTEGER REFERENCES tabla_vacas(vaca_id),
        fecha       TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        tipo_evento VARCHAR(50),
        descripcion TEXT,
        veterinario VARCHAR(100),
        costo       NUMERIC(10,2) DEFAULT 0
    )""",
    """CREATE TABLE IF NOT EXISTS tabla_usuarios (
        user_id SERIAL PRIMARY KEY,
        nombre  VARCHAR(100) NOT NULL,
        rol     VARCHAR(50)
    )""",
    """CREATE TABLE IF NOT EXISTS tabla_maquinaria (
        maquina_id SERIAL PRIMARY KEY,
        nombre     VARCHAR(100) NOT NULL,
        tipo       VARCHAR(50),
        marca      VARCHAR(50),
        modelo     VARCHAR(50),
        anio       INTEGER,
        estado     VARCHAR(20) DEFAULT 'operativa'
    )""",
    """CREATE TABLE IF NOT EXISTS tabla_mantenimiento (
        manten_id            SERIAL PRIMARY KEY,
        maquina_id           INTEGER REFERENCES tabla_maquinaria(maquina_id),
        fecha                TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        tipo_mantencion      VARCHAR(50),
        descripcion          TEXT,
        costo                NUMERIC(10,2) DEFAULT 0,
        tecnico              VARCHAR(100),
        proximo_mantenimiento DATE,
        horas_uso            NUMERIC(8,1)
    )""",
]


DROP_ORDER = [
    "tabla_mantenimiento",
    "tabla_maquinaria",
    "tabla_salud",
    "tabla_leche",
    "tabla_vacas",
    "tabla_insumos",
    "tabla_dieta",
    "tabla_lotes",
    "tabla_usuarios",
]


def crear_tablas(reset: bool = False):
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        if reset:
            for t in DROP_ORDER:
                cur.execute(f"DROP TABLE IF EXISTS {t} CASCADE")
            print("Tablas eliminadas.")
        for cmd in COMMANDS:
            cur.execute(cmd)
        conn.commit()
        cur.close()
        conn.close()
        print("EXITO: Tablas creadas correctamente")
    except Exception as e:
        print(f"ERROR: {e}")


if __name__ == "__main__":
    import sys
    crear_tablas(reset="--reset" in sys.argv)
