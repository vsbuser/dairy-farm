"""
Reemplaza todos los insumos de tabla_insumos con los datos reales
extraídos de Insumos_Fazenda_2.xlsx.

Uso:
    python scripts/importar_insumos.py [ruta_excel]
"""
import sys, math
import pandas as pd
import psycopg2

RUTA_DEFAULT = r"C:\Users\santi\Downloads\Insumos_Fazenda_2.xlsx"
DB_CONFIG = dict(host="localhost", database="granja_db", user="postgres", password="password")

def nan(v):
    try:
        f = float(v)
        return None if math.isnan(f) else f
    except (TypeError, ValueError):
        return None

def last_val(series):
    """Último valor no-NaN de una series."""
    s = series.dropna()
    return float(s.iloc[-1]) if not s.empty else None

def parse_sheet(df_raw, hdr_col_name):
    """Devuelve DataFrame limpio a partir del header real."""
    hdr_idx = None
    for i, row in df_raw.iterrows():
        if any(str(v).strip() == 'Data' for v in row.values):
            hdr_idx = i
            break
    if hdr_idx is None:
        return None
    df = pd.read_excel.__func__  # placeholder — releer desde xl
    return hdr_idx

def read_sheet(xl, sheet):
    df_raw = pd.read_excel(xl, sheet_name=sheet, header=None)
    hdr_idx = None
    for i, row in df_raw.iterrows():
        if any(str(v).strip() == 'Data' for v in row.values):
            hdr_idx = i
            break
    if hdr_idx is None:
        return None
    df = pd.read_excel(xl, sheet_name=sheet, header=hdr_idx)
    df = df[df['Data'].notna()]
    df = df[~df['Data'].astype(str).str.upper().str.contains('TOTAL')]
    return df


def extraer_insumos(ruta):
    xl = pd.ExcelFile(ruta)
    insumos = []  # lista de (nombre, unidad, stock_kg, costo_por_kg)

    # ── Sucedâneo Lácteo ──────────────────────────────────────────────────────
    df = read_sheet(xl, 'Sucedâneo 2025-26')
    if df is not None:
        stock  = last_val(df['Estoque (kg)'])
        precio = last_val(df['Valor (R$/kg)'])
        insumos.append(("Sucedâneo Lácteo",   "kg", stock or 0, precio))

    # ── Sal ───────────────────────────────────────────────────────────────────
    df = read_sheet(xl, 'Sal')
    if df is not None:
        stock  = last_val(df['Estoque (kg)'])
        precio = last_val(df['Custo (R$/kg)'])
        insumos.append(("Sal",                "kg", stock or 0, precio))

    # ── Uréia ─────────────────────────────────────────────────────────────────
    df = read_sheet(xl, 'Uréia')
    if df is not None:
        stock  = last_val(df['Estoque (kg)'])
        precio = last_val(df['Custo (R$/kg)'])
        insumos.append(("Uréia",              "kg", stock or 0, precio))

    # ── Ração Bezerras (split por Tipo) ───────────────────────────────────────
    df = read_sheet(xl, 'Ração Bezerras')
    if df is not None and 'Tipo' in df.columns:
        for tipo, nombre in [('24%', 'Ração Bezerras 24%'), ('20%', 'Ração Bezerras 20%')]:
            sub = df[df['Tipo'].astype(str).str.contains(tipo, na=False)]
            if not sub.empty:
                stock  = last_val(sub['Estoque (kg)'])
                precio = last_val(sub['Preço (R$/kg)'])
                insumos.append((nombre, "kg", stock or 0, precio))

    # ── Núcleo (split por Categoria) ──────────────────────────────────────────
    df = read_sheet(xl, 'Núcleo')
    if df is not None and 'Categoria' in df.columns:
        cat_map = {
            'Lactante':  'Núcleo Lactante (Bovigold Pró)',
            'Novilhas':  'Núcleo Novilhas (Bovigold Plus)',
            'Pré-parto': 'Núcleo Pré-parto (Bovigold Ovn)',
            'Engorda':   'Núcleo Engorda (Fosbov)',
        }
        for cat, nombre in cat_map.items():
            sub = df[df['Categoria'].astype(str).str.contains(cat, na=False)]
            if not sub.empty:
                stock  = last_val(sub['Estoque (kg)'])
                precio = last_val(sub['Custo (R$/kg)'])
                insumos.append((nombre, "kg", stock or 0, precio))

    # ── Milho / Sorgo ─────────────────────────────────────────────────────────
    df = read_sheet(xl, 'Milho-Sorgo')
    if df is not None and 'Produto' in df.columns:
        for prod, nombre in [('Sorgo', 'Sorgo moído'), ('Milho', 'Milho')]:
            sub = df[df['Produto'].astype(str).str.contains(prod, na=False)]
            if not sub.empty:
                stock = last_val(sub['Estoque (kg)'])
                # precio está en R$/t → convertir a R$/kg
                p_t = last_val(sub['Valor (R$/t)'])
                precio = round(p_t / 1000, 4) if p_t else None
                insumos.append((nombre, "kg", stock or 0, precio))

    # ── Farelo Algodão / Soja ─────────────────────────────────────────────────
    df = read_sheet(xl, 'Farelo Algodão-Soja')
    if df is not None and 'Produto' in df.columns:
        for prod, nombre in [('Algodão', 'Farelo de Algodão'), ('Soja', 'Farelo de Soja')]:
            sub = df[df['Produto'].astype(str).str.contains(prod, na=False)]
            if not sub.empty:
                stock = last_val(sub['Estoque (kg)'])
                p_t   = last_val(sub['Valor (R$/t)'])
                precio = round(p_t / 1000, 4) if p_t else None
                insumos.append((nombre, "kg", stock or 0, precio))

    # ── Testes Antibiótico ────────────────────────────────────────────────────
    df = read_sheet(xl, 'Testes Antibiótico')
    if df is not None and 'Estoque' in df.columns:
        stock = last_val(df['Estoque'])
        insumos.append(("Testes Antibiótico", "unid", stock or 0, None))

    return insumos


def importar(ruta):
    print(f"Lendo: {ruta}")
    insumos = extraer_insumos(ruta)

    print(f"\nInsumos a importar ({len(insumos)}):")
    for nome, unid, stock, preco in insumos:
        print(f"  {nome:<40} {stock:>8.1f} {unid:<5}  R$ {preco:.4f}/kg" if preco else
              f"  {nome:<40} {stock:>8.1f} {unid:<5}  (sem preco)")

    conn = psycopg2.connect(**DB_CONFIG)
    cur  = conn.cursor()

    cur.execute("DELETE FROM tabla_insumos")
    print(f"\nInsumos anteriores eliminados.")

    for nome, unid, stock, preco in insumos:
        cur.execute(
            "INSERT INTO tabla_insumos (nombre_insumo, unidad, stock_actual_kg, costo_por_kg) VALUES (%s,%s,%s,%s)",
            (nome, unid, stock, preco)
        )

    conn.commit(); cur.close(); conn.close()
    print(f"EXITO: {len(insumos)} insumos importados.")


if __name__ == "__main__":
    ruta = sys.argv[1] if len(sys.argv) > 1 else RUTA_DEFAULT
    importar(ruta)
