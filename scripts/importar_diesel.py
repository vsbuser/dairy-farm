"""
Importa el histórico de consumo de diesel desde el Excel a tabla_diesel.

Uso:
    python scripts/importar_diesel.py [ruta_excel]
"""
import sys, math
import pandas as pd
import psycopg2
from datetime import datetime

RUTA_DEFAULT = r"C:\Users\santi\Downloads\consumo_diesel.xlsx"

DB_CONFIG = dict(host="localhost", database="granja_db", user="postgres", password="password")

INSERT_SQL = """
    INSERT INTO tabla_diesel
        (fecha, consumo_litros, estoque_litros, compra_litros, precio_rl, total_rs)
    VALUES (%s, %s, %s, %s, %s, %s)
"""

CREATE_SQL = """
    CREATE TABLE IF NOT EXISTS tabla_diesel (
        id             SERIAL PRIMARY KEY,
        fecha          DATE NOT NULL,
        consumo_litros NUMERIC(8,1) NOT NULL,
        estoque_litros NUMERIC(8,1),
        compra_litros  NUMERIC(8,1),
        precio_rl      NUMERIC(6,2),
        total_rs       NUMERIC(10,2)
    )
"""

def _nan(v):
    try:
        return None if (v is None or math.isnan(float(v))) else float(v)
    except (TypeError, ValueError):
        return None

def _parse_date(v):
    if pd.isnull(v):
        return None
    if isinstance(v, datetime):
        return v.date()
    s = str(v).strip()
    for fmt in ("%d/%m/%y", "%d/%m/%Y", "%Y-%m-%d"):
        try:
            return datetime.strptime(s, fmt).date()
        except ValueError:
            continue
    return None

def importar(ruta: str) -> None:
    print(f"Leyendo: {ruta}")
    df = pd.read_excel(ruta)
    df.columns = ["fecha", "consumo", "estoque", "compra", "precio", "total"]

    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()
    cur.execute(CREATE_SQL)

    ok = skipped = 0
    for _, row in df.iterrows():
        fecha = _parse_date(row["fecha"])
        consumo = _nan(row["consumo"])
        if fecha is None or consumo is None:
            skipped += 1
            continue
        cur.execute(INSERT_SQL, (
            fecha, consumo,
            _nan(row["estoque"]),
            _nan(row["compra"]),
            _nan(row["precio"]),
            _nan(row["total"]),
        ))
        ok += 1

    conn.commit(); cur.close(); conn.close()
    print(f"  -> Insertados: {ok}  |  Omitidos: {skipped}")
    print("EXITO: importacion completada.")

if __name__ == "__main__":
    ruta = sys.argv[1] if len(sys.argv) > 1 else RUTA_DEFAULT
    importar(ruta)
