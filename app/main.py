import json
import psycopg2
import pandas as pd
from sqlalchemy import create_engine
from nicegui import ui

_DB_URL = "postgresql+psycopg2://postgres:password@localhost/granja_db"
_engine  = create_engine(_DB_URL)

DB_CONFIG = {
    "host": "localhost",
    "database": "granja_db",
    "user": "postgres",
    "password": "password",
}

TIPOS_EVENTO = [
    "Vacunación", "Control rutinario", "Tratamiento",
    "Enfermedad", "Parto asistido", "Cirugía",
]

TIPOS_MAQUINARIA = [
    "Tractor", "Ordeñadora", "Compresor", "Generador",
    "Mixer", "Cargadora", "Bomba", "Cisterna", "Otro",
]

TIPOS_MANTENCION = [
    "Preventivo", "Correctivo", "Cambio de aceite",
    "Revisión general", "Reparación", "Calibración",
]

ESTADOS_MAQUINA = ["operativa", "en mantenimiento", "fuera de servicio"]


def read_sql(query: str, params=None) -> pd.DataFrame:
    """pd.read_sql via SQLAlchemy engine (sin warnings)."""
    with _engine.connect() as conn:
        return pd.read_sql(query, conn, params=params)


def conectar():
    """Conexión psycopg2 para INSERT/UPDATE/DELETE."""
    return psycopg2.connect(**DB_CONFIG)


def df_to_table(df: pd.DataFrame, pagination: int = 15) -> None:
    if df.empty:
        ui.label("Sin datos disponibles.").classes("text-grey-6 italic")
        return
    cols = [{"name": c, "label": c, "field": c, "sortable": True} for c in df.columns]
    rows = json.loads(df.to_json(orient="records", date_format="iso", default_handler=str))
    ui.table(columns=cols, rows=rows, pagination=pagination).classes("w-full")


def nav() -> None:
    links = [
        ("Dashboard", "/"),
        ("Vacas",     "/vacas"),
        ("Salud",     "/salud"),
        ("Leche",     "/leche"),
        ("Bodega",      "/bodega"),
        ("Maquinaria",  "/maquinaria"),
    ]
    with ui.header().classes("bg-blue-800 text-white flex items-center gap-6 px-6 py-3"):
        ui.label("Dairy Farm Pro").classes("text-xl font-bold mr-6")
        for label, href in links:
            ui.link(label, href).classes(
                "text-white hover:text-blue-200 text-sm font-medium no-underline"
            )


# ── DASHBOARD ────────────────────────────────────────────────────────────────

@ui.page("/")
def dashboard() -> None:
    nav()
    ui.label("Resumen General").classes("text-2xl font-bold m-4")

    try:
        total_vacas  = int(read_sql(
            "SELECT COUNT(*) FROM tabla_vacas WHERE estado='activa'"
        ).iloc[0, 0])
        total_dietas = int(read_sql(
            "SELECT COUNT(*) FROM tabla_dieta"
        ).iloc[0, 0])
        litros_hoy   = float(read_sql(
            "SELECT COALESCE(SUM(litros),0) FROM tabla_leche WHERE DATE(fecha_hora)=CURRENT_DATE"
        ).iloc[0, 0])
        df_stock = read_sql(
            "SELECT nombre_insumo, stock_actual_kg FROM tabla_insumos ORDER BY stock_actual_kg DESC"
        )
        df_prod  = read_sql("""
            SELECT DATE(fecha_hora)::text          AS fecha,
                   ROUND(SUM(litros), 1)::float    AS total_litros
            FROM tabla_leche
            WHERE fecha_hora >= CURRENT_DATE - INTERVAL '7 days'
            GROUP BY DATE(fecha_hora)
            ORDER BY fecha
        """)
        df_categorias = read_sql("""
            SELECT COALESCE(categoria, 'lactancia') AS categoria,
                   COUNT(*)::int                    AS total
            FROM tabla_vacas
            WHERE estado = 'activa'
            GROUP BY COALESCE(categoria, 'lactancia')
            ORDER BY categoria DESC
        """)
        error_msg = None
    except Exception as exc:
        total_vacas = total_dietas = 0
        litros_hoy  = 0.0
        df_stock = df_prod = df_categorias = pd.DataFrame()
        error_msg = str(exc)

    # ── Métricas ──
    with ui.row().classes("w-full gap-4 px-4"):
        for titulo, valor in [
            ("Vacas Activas",     str(total_vacas)),
            ("Dietas",            str(total_dietas)),
            ("Litros Hoy",        f"{litros_hoy:.1f}"),
        ]:
            with ui.card().classes("flex-1 p-6 text-center"):
                ui.label(titulo).classes("text-xs text-grey-6 uppercase tracking-widest")
                ui.label(valor).classes("text-5xl font-bold text-blue-800 mt-1")

    if error_msg:
        ui.label(f"Error de conexión: {error_msg}").classes("text-red m-4")
        return

    # ── Gráficos ──
    with ui.row().classes("w-full gap-4 px-4 pb-4 mt-4"):
        with ui.card().classes("flex-1"):
            ui.label("Stock de Insumos (kg)").classes("font-bold mb-2")
            if not df_stock.empty:
                ui.echart({
                    "tooltip": {"trigger": "axis"},
                    "xAxis":   {
                        "type": "category",
                        "data": list(df_stock["nombre_insumo"]),
                        "axisLabel": {"rotate": 30, "fontSize": 11},
                    },
                    "yAxis":  {"type": "value"},
                    "series": [{
                        "type": "bar",
                        "data": [float(v) for v in df_stock["stock_actual_kg"]],
                        "itemStyle": {"color": "#1d4ed8"},
                    }],
                }).classes("w-full h-64")

        with ui.card().classes("flex-1"):
            ui.label("Producción Últimos 7 Días (lts)").classes("font-bold mb-2")
            if not df_prod.empty:
                ui.echart({
                    "tooltip": {"trigger": "axis"},
                    "xAxis":   {"type": "category", "data": list(df_prod["fecha"])},
                    "yAxis":   {"type": "value"},
                    "series":  [{
                        "type":      "line",
                        "data":      list(df_prod["total_litros"]),
                        "smooth":    True,
                        "areaStyle": {},
                        "itemStyle": {"color": "#16a34a"},
                    }],
                }).classes("w-full h-64")

        with ui.card().classes("flex-1"):
            ui.label("Vacas en Lactancia vs Secas").classes("font-bold mb-2")
            if not df_categorias.empty:
                pie_data = [
                    {"value": int(row["total"]), "name": row["categoria"].capitalize()}
                    for _, row in df_categorias.iterrows()
                ]
                colores = {"Lactancia": "#1d4ed8", "Seca": "#f59e0b"}
                for d in pie_data:
                    d["itemStyle"] = {"color": colores.get(d["name"], "#6b7280")}
                ui.echart({
                    "tooltip": {"trigger": "item", "formatter": "{b}: {c} ({d}%)"},
                    "legend":  {"bottom": "2%", "left": "center"},
                    "series":  [{
                        "type":       "pie",
                        "radius":     ["45%", "72%"],
                        "avoidLabelOverlap": True,
                        "itemStyle":  {"borderRadius": 8, "borderColor": "#fff", "borderWidth": 2},
                        "label":      {"show": True, "formatter": "{b}\n{c} vacas"},
                        "emphasis":   {"label": {"show": True, "fontSize": 14, "fontWeight": "bold"}},
                        "data":       pie_data,
                    }],
                }).classes("w-full h-64")


# ── VACAS ─────────────────────────────────────────────────────────────────────

@ui.page("/vacas")
def vacas_page() -> None:
    nav()
    ui.label("Registro de Animales").classes("text-2xl font-bold m-4")

    try:
        dietas_opts = ["(sin dieta)"] + list(
            read_sql("SELECT nombre_dieta FROM tabla_dieta ORDER BY nombre_dieta")["nombre_dieta"]
        )
        lotes_opts  = ["(sin lote)"] + list(
            read_sql("SELECT nombre_lote FROM tabla_lotes ORDER BY nombre_lote")["nombre_lote"]
        )
    except Exception as exc:
        ui.label(f"Error de conexión: {exc}").classes("text-red m-4")
        return

    @ui.refreshable
    def tabla_vacas() -> None:
        try:
            df = read_sql("""
                SELECT v.rfid_code    AS "RFID",
                       v.nombre       AS "Nombre",
                       v.raza         AS "Raza",
                       v.estado       AS "Estado",
                       l.nombre_lote  AS "Lote",
                       d.nombre_dieta AS "Dieta"
                FROM tabla_vacas v
                LEFT JOIN tabla_lotes l ON v.lote_id  = l.lote_id
                LEFT JOIN tabla_dieta d ON v.dieta_id = d.dieta_id
                ORDER BY v.nombre
            """)
            df_to_table(df)
        except Exception as exc:
            ui.label(f"Error: {exc}").classes("text-red")

    with ui.card().classes("mx-4 mb-4"):
        ui.label("Nuevo Animal").classes("text-lg font-bold mb-3")
        with ui.row().classes("w-full gap-4"):
            with ui.column().classes("flex-1 gap-3"):
                rfid   = ui.input("Código RFID").classes("w-full")
                nombre = ui.input("Nombre / Caravana").classes("w-full")
                raza   = ui.input("Raza").classes("w-full")
            with ui.column().classes("flex-1 gap-3"):
                lote   = ui.select(lotes_opts,  value=lotes_opts[0],  label="Lote").classes("w-full")
                dieta  = ui.select(dietas_opts, value=dietas_opts[0], label="Dieta").classes("w-full")

        def guardar_vaca() -> None:
            if not nombre.value.strip():
                ui.notify("El nombre del animal es obligatorio.", type="warning")
                return
            try:
                conn = conectar()
                cur  = conn.cursor()
                cur.execute("SELECT dieta_id FROM tabla_dieta WHERE nombre_dieta=%s", (dieta.value,))
                row = cur.fetchone(); dieta_id = row[0] if row else None
                cur.execute("SELECT lote_id FROM tabla_lotes WHERE nombre_lote=%s", (lote.value,))
                row = cur.fetchone(); lote_id = row[0] if row else None
                cur.execute(
                    "INSERT INTO tabla_vacas (rfid_code, nombre, raza, lote_id, dieta_id) VALUES (%s,%s,%s,%s,%s)",
                    (rfid.value or None, nombre.value.strip(), raza.value or None, lote_id, dieta_id),
                )
                conn.commit(); cur.close(); conn.close()
                ui.notify(f"Animal '{nombre.value}' registrado.", type="positive")
                rfid.value = ""; nombre.value = ""; raza.value = ""
                tabla_vacas.refresh()
            except Exception as exc:
                ui.notify(f"Error: {exc}", type="negative")

        ui.button("GUARDAR ANIMAL", on_click=guardar_vaca).classes("mt-3 bg-blue-700 text-white")

    with ui.card().classes("mx-4 mb-4"):
        ui.label("Plantel Actual").classes("text-lg font-bold mb-2")
        tabla_vacas()


# ── SALUD ─────────────────────────────────────────────────────────────────────

@ui.page("/salud")
def salud_page() -> None:
    nav()
    ui.label("Control Sanitario").classes("text-2xl font-bold m-4")

    try:
        vacas_opts = ["(seleccionar)"] + list(
            read_sql("SELECT nombre FROM tabla_vacas WHERE estado='activa' ORDER BY nombre")["nombre"]
        )
    except Exception as exc:
        ui.label(f"Error de conexión: {exc}").classes("text-red m-4")
        return

    @ui.refreshable
    def tabla_hist() -> None:
        try:
            df = read_sql("""
                SELECT v.nombre      AS "Vaca",
                       s.fecha       AS "Fecha",
                       s.tipo_evento AS "Tipo",
                       s.descripcion AS "Descripción",
                       s.veterinario AS "Veterinario",
                       s.costo       AS "Costo $"
                FROM tabla_salud s
                JOIN tabla_vacas v ON s.vaca_id = v.vaca_id
                ORDER BY s.fecha DESC LIMIT 100
            """)
            df_to_table(df)
        except Exception as exc:
            ui.label(f"Error: {exc}").classes("text-red")

    with ui.card().classes("mx-4 mb-4"):
        ui.label("Nuevo Evento Sanitario").classes("text-lg font-bold mb-3")
        with ui.row().classes("w-full gap-4"):
            with ui.column().classes("flex-1 gap-3"):
                vaca  = ui.select(vacas_opts, value=vacas_opts[0], label="Animal").classes("w-full")
                tipo  = ui.select(TIPOS_EVENTO, value=TIPOS_EVENTO[0], label="Tipo de Evento").classes("w-full")
                vet   = ui.input("Veterinario").classes("w-full")
                costo = ui.number("Costo ($)", value=0.0, min=0, step=0.5).classes("w-full")
            with ui.column().classes("flex-1"):
                descr = ui.textarea("Descripción del evento").classes("w-full h-40")

        def guardar_salud() -> None:
            if vaca.value == "(seleccionar)":
                ui.notify("Selecciona un animal.", type="warning")
                return
            try:
                conn = conectar(); cur = conn.cursor()
                cur.execute("SELECT vaca_id FROM tabla_vacas WHERE nombre=%s", (vaca.value,))
                row = cur.fetchone(); vaca_id = row[0] if row else None
                cur.execute("""
                    INSERT INTO tabla_salud (vaca_id, tipo_evento, descripcion, veterinario, costo)
                    VALUES (%s, %s, %s, %s, %s)
                """, (vaca_id, tipo.value, descr.value, vet.value, costo.value or 0))
                conn.commit(); cur.close(); conn.close()
                ui.notify("Evento registrado.", type="positive")
                vet.value = ""; descr.value = ""; costo.value = 0.0
                tabla_hist.refresh()
            except Exception as exc:
                ui.notify(f"Error: {exc}", type="negative")

        ui.button("REGISTRAR EVENTO", on_click=guardar_salud).classes("mt-3 bg-blue-700 text-white")

    with ui.card().classes("mx-4 mb-4"):
        ui.label("Historial Sanitario").classes("text-lg font-bold mb-2")
        tabla_hist()


# ── LECHE ─────────────────────────────────────────────────────────────────────

@ui.page("/leche")
def leche_page() -> None:
    nav()
    ui.label("Registro de Producción Láctea").classes("text-2xl font-bold m-4")

    try:
        vacas_data = read_sql("""
            SELECT vaca_id,
                   nombre,
                   COALESCE(rfid_code, '') AS rfid,
                   COALESCE(categoria, 'lactancia') AS categoria
            FROM tabla_vacas
            WHERE estado = 'activa'
            ORDER BY nombre
        """).to_dict("records")
    except Exception as exc:
        ui.label(f"Error de conexión: {exc}").classes("text-red m-4")
        return

    estado = {"vaca_id": None, "nombre": ""}

    @ui.refreshable
    def tabla_leche() -> None:
        try:
            df = read_sql("""
                SELECT v.nombre     AS "Vaca",
                       l.litros     AS "Litros",
                       l.fecha_hora AS "Fecha/Hora"
                FROM tabla_leche l
                JOIN tabla_vacas v ON l.vaca_id = v.vaca_id
                ORDER BY l.fecha_hora DESC LIMIT 100
            """)
            df_to_table(df)
        except Exception as exc:
            ui.label(f"Error: {exc}").classes("text-red")

    # ── Buscador ────────────────────────────────────────
    with ui.card().classes("mx-4 mb-4"):
        ui.label("Buscar Vaca").classes("text-lg font-bold mb-3")

        search      = ui.input(placeholder="Escribí nombre o RFID...").classes("w-full")
        resultados  = ui.column().classes("w-full gap-1 mt-1")
        sel_label   = ui.label("").classes("text-blue-700 font-semibold mt-2 min-h-6")

        with ui.row().classes("gap-4 items-end mt-4") as form_row:
            litros = ui.number("Litros producidos", value=0.0, min=0, step=0.5).classes("w-52")

            def guardar_leche() -> None:
                if not estado["vaca_id"]:
                    ui.notify("Buscá y seleccioná una vaca primero.", type="warning")
                    return
                if not litros.value or litros.value <= 0:
                    ui.notify("Los litros deben ser mayor a 0.", type="warning")
                    return
                try:
                    conn = conectar(); cur = conn.cursor()
                    cur.execute(
                        "INSERT INTO tabla_leche (vaca_id, litros) VALUES (%s, %s)",
                        (estado["vaca_id"], litros.value),
                    )
                    conn.commit(); cur.close(); conn.close()
                    ui.notify(
                        f"{litros.value} lts registrados para {estado['nombre']}.",
                        type="positive",
                    )
                    litros.value = 0.0
                    tabla_leche.refresh()
                except Exception as exc:
                    ui.notify(f"Error: {exc}", type="negative")

            ui.button("REGISTRAR ORDEÑE", on_click=guardar_leche).classes(
                "bg-blue-700 text-white"
            )

        form_row.set_visibility(False)

        def seleccionar(vid: int, nombre: str) -> None:
            estado["vaca_id"] = vid
            estado["nombre"]  = nombre
            sel_label.set_text(f"✓  {nombre}")
            search.value = nombre
            resultados.clear()
            form_row.set_visibility(True)
            litros.run_method("focus")

        def buscar() -> None:
            term = search.value.strip().lower()
            resultados.clear()
            # Limpiar selección si el usuario modificó el texto
            if estado["nombre"] and term != estado["nombre"].lower():
                estado["vaca_id"] = None
                estado["nombre"]  = ""
                sel_label.set_text("")
                form_row.set_visibility(False)
            if len(term) < 2:
                return
            matches = [
                v for v in vacas_data
                if term in v["nombre"].lower() or term in v["rfid"].lower()
            ]
            if not matches:
                with resultados:
                    ui.label("Sin resultados.").classes("text-grey-6 italic text-sm px-2")
                return
            with resultados:
                for v in matches[:15]:
                    cat_color = "blue" if v["categoria"] == "lactancia" else "amber"
                    with ui.card().classes(
                        "w-full p-2 cursor-pointer hover:bg-blue-50"
                    ).style("border:1px solid #e5e7eb") as card:
                        with ui.row().classes("items-center gap-3"):
                            ui.label(v["nombre"]).classes("font-medium flex-1")
                            ui.label(v["rfid"] or "—").classes("text-grey-6 text-xs w-28")
                            ui.badge(v["categoria"]).props(f"color={cat_color}").classes("text-xs")
                        card.on("click", lambda vid=v["vaca_id"], nom=v["nombre"]: seleccionar(vid, nom))

        search.on("input", lambda: buscar())

    # ── Historial ───────────────────────────────────────
    with ui.card().classes("mx-4 mb-4"):
        ui.label("Últimos Registros").classes("text-lg font-bold mb-2")
        tabla_leche()


# ── BODEGA ────────────────────────────────────────────────────────────────────

@ui.page("/bodega")
def bodega_page() -> None:
    nav()
    ui.label("Bodega e Insumos").classes("text-2xl font-bold m-4")

    @ui.refreshable
    def tabla_bodega() -> None:
        try:
            df = read_sql("""
                SELECT nombre_insumo   AS "Insumo",
                       unidad          AS "Unidad",
                       stock_actual_kg AS "Stock (kg)",
                       costo_por_kg    AS "Costo/kg $"
                FROM tabla_insumos ORDER BY nombre_insumo
            """)
            df_to_table(df)
        except Exception as exc:
            ui.label(f"Error: {exc}").classes("text-red")

    with ui.card().classes("mx-4 mb-4"):
        ui.label("Agregar / Actualizar Insumo").classes("text-lg font-bold mb-3")
        with ui.row().classes("gap-4 items-end"):
            nombre_ins = ui.input("Nombre del Insumo").classes("w-56")
            stock_kg   = ui.number("Stock a Agregar (kg)", value=0.0, min=0).classes("w-44")
            costo_kg   = ui.number("Costo/kg ($)", value=0.0, min=0, step=0.01).classes("w-44")

            def guardar_insumo() -> None:
                if not nombre_ins.value.strip():
                    ui.notify("El nombre del insumo es obligatorio.", type="warning")
                    return
                try:
                    conn = conectar(); cur = conn.cursor()
                    cur.execute("""
                        INSERT INTO tabla_insumos (nombre_insumo, stock_actual_kg, costo_por_kg)
                        VALUES (%s, %s, %s)
                        ON CONFLICT (nombre_insumo) DO UPDATE
                            SET stock_actual_kg = tabla_insumos.stock_actual_kg + EXCLUDED.stock_actual_kg,
                                costo_por_kg    = EXCLUDED.costo_por_kg
                    """, (nombre_ins.value.strip(), stock_kg.value or 0, costo_kg.value or 0))
                    conn.commit(); cur.close(); conn.close()
                    ui.notify(f"Insumo '{nombre_ins.value}' actualizado.", type="positive")
                    nombre_ins.value = ""; stock_kg.value = 0.0; costo_kg.value = 0.0
                    tabla_bodega.refresh()
                except Exception as exc:
                    ui.notify(f"Error: {exc}", type="negative")

            ui.button("AGREGAR / ACTUALIZAR STOCK", on_click=guardar_insumo).classes("bg-blue-700 text-white")

    with ui.card().classes("mx-4 mb-4"):
        ui.label("Inventario Actual").classes("text-lg font-bold mb-2")
        tabla_bodega()


# ── MAQUINARIA ───────────────────────────────────────────────────────────────

@ui.page("/maquinaria")
def maquinaria_page() -> None:
    nav()
    ui.label("Control de Maquinaria").classes("text-2xl font-bold m-4")

    # ── Tablas refrescables ──────────────────────────────
    @ui.refreshable
    def tabla_maquinas() -> None:
        try:
            df = read_sql("""
                SELECT nombre        AS "Nombre",
                       tipo          AS "Tipo",
                       marca         AS "Marca",
                       modelo        AS "Modelo",
                       anio          AS "Año",
                       estado        AS "Estado"
                FROM tabla_maquinaria
                ORDER BY nombre
            """)
            df_to_table(df)
        except Exception as exc:
            ui.label(f"Error: {exc}").classes("text-red")

    @ui.refreshable
    def tabla_mantenimiento() -> None:
        try:
            df = read_sql("""
                SELECT m.nombre               AS "Máquina",
                       t.fecha                AS "Fecha",
                       t.tipo_mantencion      AS "Tipo",
                       t.descripcion          AS "Descripción",
                       t.tecnico              AS "Técnico",
                       t.horas_uso            AS "Horas uso",
                       t.costo                AS "Costo $",
                       t.proximo_mantenimiento AS "Próximo mant."
                FROM tabla_mantenimiento t
                JOIN tabla_maquinaria m ON t.maquina_id = m.maquina_id
                ORDER BY t.fecha DESC
                LIMIT 100
            """)
            df_to_table(df)
        except Exception as exc:
            ui.label(f"Error: {exc}").classes("text-red")

    # ── Registrar nueva máquina ──────────────────────────
    with ui.card().classes("mx-4 mb-4"):
        ui.label("Registrar Máquina").classes("text-lg font-bold mb-3")
        with ui.row().classes("w-full gap-4"):
            with ui.column().classes("flex-1 gap-3"):
                nombre_maq = ui.input("Nombre / Identificación").classes("w-full")
                tipo_maq   = ui.select(TIPOS_MAQUINARIA, value=TIPOS_MAQUINARIA[0], label="Tipo").classes("w-full")
                estado_maq = ui.select(ESTADOS_MAQUINA,  value=ESTADOS_MAQUINA[0],  label="Estado").classes("w-full")
            with ui.column().classes("flex-1 gap-3"):
                marca_maq  = ui.input("Marca").classes("w-full")
                modelo_maq = ui.input("Modelo").classes("w-full")
                anio_maq   = ui.number("Año", value=2020, min=1990, max=2030, step=1).classes("w-full")

        def guardar_maquina() -> None:
            if not nombre_maq.value.strip():
                ui.notify("El nombre de la máquina es obligatorio.", type="warning")
                return
            try:
                conn = conectar(); cur = conn.cursor()
                cur.execute("""
                    INSERT INTO tabla_maquinaria (nombre, tipo, marca, modelo, anio, estado)
                    VALUES (%s, %s, %s, %s, %s, %s)
                """, (
                    nombre_maq.value.strip(), tipo_maq.value,
                    marca_maq.value or None, modelo_maq.value or None,
                    int(anio_maq.value) if anio_maq.value else None,
                    estado_maq.value,
                ))
                conn.commit(); cur.close(); conn.close()
                ui.notify(f"Máquina '{nombre_maq.value}' registrada.", type="positive")
                nombre_maq.value = ""; marca_maq.value = ""; modelo_maq.value = ""
                tabla_maquinas.refresh()
                # recargar selector de máquinas en el formulario de mantenimiento
                selector_maquina.refresh()
            except Exception as exc:
                ui.notify(f"Error: {exc}", type="negative")

        ui.button("GUARDAR MÁQUINA", on_click=guardar_maquina).classes("mt-3 bg-blue-700 text-white")

    with ui.card().classes("mx-4 mb-4"):
        ui.label("Máquinas Registradas").classes("text-lg font-bold mb-2")
        tabla_maquinas()

    # ── Registrar evento de mantenimiento ────────────────
    with ui.card().classes("mx-4 mb-4"):
        ui.label("Registrar Mantenimiento").classes("text-lg font-bold mb-3")

        @ui.refreshable
        def selector_maquina() -> None:
            try:
                maq_df   = read_sql("SELECT nombre FROM tabla_maquinaria ORDER BY nombre")
                maq_opts = ["(seleccionar)"] + list(maq_df["nombre"])
            except Exception:
                maq_opts = ["(seleccionar)"]

            maquina_sel.options = maq_opts
            if maquina_sel.value not in maq_opts:
                maquina_sel.value = maq_opts[0]

        maquina_sel = ui.select(["(seleccionar)"], value="(seleccionar)", label="Máquina").classes("w-full mb-2")
        selector_maquina()

        with ui.row().classes("w-full gap-4"):
            with ui.column().classes("flex-1 gap-3"):
                tipo_mant  = ui.select(TIPOS_MANTENCION, value=TIPOS_MANTENCION[0], label="Tipo de Mantención").classes("w-full")
                tecnico    = ui.input("Técnico / Taller").classes("w-full")
                horas_uso  = ui.number("Horas de Uso", value=0.0, min=0, step=0.5).classes("w-full")
                costo_mant = ui.number("Costo ($)", value=0.0, min=0, step=10).classes("w-full")
            with ui.column().classes("flex-1 gap-3"):
                descr_mant = ui.textarea("Descripción del trabajo").classes("w-full h-28")
                prox_mant  = ui.date("Próximo Mantenimiento").classes("w-full")

        def guardar_mantenimiento() -> None:
            if maquina_sel.value == "(seleccionar)":
                ui.notify("Selecciona una máquina.", type="warning")
                return
            try:
                conn = conectar(); cur = conn.cursor()
                cur.execute("SELECT maquina_id FROM tabla_maquinaria WHERE nombre=%s", (maquina_sel.value,))
                row = cur.fetchone(); maquina_id = row[0] if row else None
                cur.execute("""
                    INSERT INTO tabla_mantenimiento
                        (maquina_id, tipo_mantencion, descripcion, tecnico,
                         costo, proximo_mantenimiento, horas_uso)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                """, (
                    maquina_id, tipo_mant.value, descr_mant.value,
                    tecnico.value or None, costo_mant.value or 0,
                    prox_mant.value or None, horas_uso.value or None,
                ))
                conn.commit(); cur.close(); conn.close()
                ui.notify("Evento de mantenimiento registrado.", type="positive")
                tecnico.value = ""; descr_mant.value = ""
                costo_mant.value = 0.0; horas_uso.value = 0.0
                tabla_mantenimiento.refresh()
            except Exception as exc:
                ui.notify(f"Error: {exc}", type="negative")

        ui.button("REGISTRAR MANTENIMIENTO", on_click=guardar_mantenimiento).classes("mt-3 bg-blue-700 text-white")

    with ui.card().classes("mx-4 mb-4"):
        ui.label("Historial de Mantenimiento").classes("text-lg font-bold mb-2")
        tabla_mantenimiento()


ui.run(title="Dairy Farm Pro", port=8080, reload=False)
