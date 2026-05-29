import psycopg2
conn = psycopg2.connect(host="localhost", database="granja_db", user="postgres", password="password")
cur = conn.cursor()
cur.execute("SELECT nombre_insumo, unidad, stock_actual_kg, costo_por_kg FROM tabla_insumos ORDER BY nombre_insumo")
rows = cur.fetchall()
print(f"Total: {len(rows)} insumos\n")
for r in rows:
    p = f"R$ {r[3]:.4f}/u" if r[3] else "sem preco"
    print(f"  {r[0]:<45}  {r[2]:>8.1f} {r[1]:<5}  {p}")
cur.close(); conn.close()
