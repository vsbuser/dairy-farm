"""
Importa el histórico de producción de leche desde el Excel
al la tabla tabla_produccion_historica en granja_db.

Uso:
    python scripts/importar_produccion.py [ruta_excel]

Si no se pasa ruta, usa la ruta por defecto del desktop.
"""
import sys
import math
import pandas as pd
import psycopg2
from datetime import date

RUTA_DEFAULT = r"C:\Users\santi\Desktop\historico_leite\Producao_Leite_2024_2026.xlsx"

DB_CONFIG = {
    "host": "localhost",
    "database": "granja_db",
    "user": "postgres",
    "password": "password",
}

INSERT_SQL = """
    INSERT INTO tabla_produccion_historica
        (fecha, ordenha_1, ordenha_2, ordenha_3, total_litros, num_vacas, media_litros_vaca)
    VALUES (%s, %s, %s, %s, %s, %s, %s)
    ON CONFLICT (fecha) DO UPDATE SET
        ordenha_1         = EXCLUDED.ordenha_1,
        ordenha_2         = EXCLUDED.ordenha_2,
        ordenha_3         = EXCLUDED.ordenha_3,
        total_litros      = EXCLUDED.total_litros,
        num_vacas         = EXCLUDED.num_vacas,
        media_litros_vaca = EXCLUDED.media_litros_vaca
"""


def _nan_to_none(val):
    if val is None:
        return None
    try:
        if math.isnan(val):
            return None
    except TypeError:
        pass
    return val


def cargar_excel(ruta: str) -> pd.DataFrame:
    xl = pd.ExcelFile(ruta)
    frames = []
    for sheet in xl.sheet_names:
        df = pd.read_excel(xl, sheet_name=sheet)
        # Renombrar columnas de forma tolerante a encoding
        df.columns = ["fecha", "ord1", "ord2", "ord3", "total", "num_vacas", "media"]
        # Descartar fila de totales (Data no es datetime)
        df = df[pd.to_datetime(df["fecha"], errors="coerce").notna()].copy()
        df["fecha"] = pd.to_datetime(df["fecha"]).dt.date
        frames.append(df)
    return pd.concat(frames, ignore_index=True)


def importar(ruta: str) -> None:
    print(f"Leyendo: {ruta}")
    df = cargar_excel(ruta)
    print(f"  -> {len(df)} registros encontrados ({df['fecha'].min()} a {df['fecha'].max()})")

    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()

    # Crear tabla si no existe
    cur.execute("""
        CREATE TABLE IF NOT EXISTS tabla_produccion_historica (
            id                SERIAL PRIMARY KEY,
            fecha             DATE UNIQUE NOT NULL,
            ordenha_1         NUMERIC(8,2),
            ordenha_2         NUMERIC(8,2),
            ordenha_3         NUMERIC(8,2),
            total_litros      NUMERIC(8,2) NOT NULL,
            num_vacas         INTEGER,
            media_litros_vaca NUMERIC(6,2)
        )
    """)

    insertados = actualizados = 0
    for _, row in df.iterrows():
        cur.execute(
            "SELECT id FROM tabla_produccion_historica WHERE fecha = %s",
            (row["fecha"],),
        )
        existe = cur.fetchone() is not None

        ord1  = _nan_to_none(row["ord1"])
        ord2  = _nan_to_none(row["ord2"])
        ord3  = _nan_to_none(row["ord3"])
        total = _nan_to_none(row["total"])
        if total is None:
            parts = [v for v in (ord1, ord2, ord3) if v is not None]
            total = sum(parts) if parts else None
        if total is None:
            continue  # fila sin datos de producción, ignorar

        cur.execute(INSERT_SQL, (
            row["fecha"],
            ord1, ord2, ord3, total,
            int(row["num_vacas"]) if _nan_to_none(row["num_vacas"]) is not None else None,
            _nan_to_none(row["media"]),
        ))
        if existe:
            actualizados += 1
        else:
            insertados += 1

    conn.commit()
    cur.close()
    conn.close()

    print(f"  -> Insertados: {insertados}  |  Actualizados: {actualizados}")
    print("ÉXITO: importación completada.")


if __name__ == "__main__":
    ruta = sys.argv[1] if len(sys.argv) > 1 else RUTA_DEFAULT
    importar(ruta)
