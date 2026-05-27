import json
import psycopg2
import pandas as pd
from datetime import date, timedelta
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
ESTADOS_MAQUINA     = ["Operativa", "En mantenimiento", "Fuera de servicio"]
TIPOS_FERTILIZACION = ["Inseminación Artificial", "Monta Natural"]
RESULTADOS_PARTO    = ["Exitoso", "Gemelar", "Aborto", "Cría muerta"]
GESTACION_DIAS      = 283
STOCK_ALERTA        = 100
STOCK_MEDIO         = 300

CATEGORIAS_INGRESO = [
    "Venta de leche",
    "Venta de animales",
    "Subsidio o ayuda estatal",
    "Otro ingreso",
]
CATEGORIAS_EGRESO = [
    "Alimentación e insumos",
    "Veterinario y salud animal",
    "Mantenimiento de maquinaria",
    "Mano de obra",
    "Combustible",
    "Servicios (luz, agua, gas)",
    "Otros gastos",
]

ELEGIR = "— Elegí una opción —"


# ── helpers DB ────────────────────────────────────────────────────────────────

def read_sql(query: str, params=None) -> pd.DataFrame:
    with _engine.connect() as conn:
        return pd.read_sql(query, conn, params=params)


def conectar():
    return psycopg2.connect(**DB_CONFIG)


# ── helpers UI ────────────────────────────────────────────────────────────────

CSS = """
<style>
  body { font-size: 15px; line-height: 1.55; }
  .q-table td  { padding: 10px 14px !important; font-size: 14px; }
  .q-table th  { font-size: 13px !important; font-weight: 700 !important;
                 background: #f1f5f9 !important; }
  .q-field__label  { font-size: 14px !important; }
  .q-field__native { font-size: 15px !important; }
  .q-select__dropdown-icon { font-size: 20px !important; }
  .q-notification { font-size: 15px !important; min-width: 280px; }
  a.nav-link { text-decoration: none !important; }
  .nav-active { background: rgba(255,255,255,0.22) !important;
                border-radius: 6px; }
  .help-text  { font-size: 12px; color: #6b7280; margin-top: 2px; }
  .req        { color: #ef4444; font-weight: bold; margin-left: 2px; }
  .section-title { font-size: 1.15rem; font-weight: 700;
                   color: #1e3a5f; margin-bottom: 4px; }
</style>
"""


def _css() -> None:
    ui.add_head_html(CSS)


def campo(label: str, ayuda: str = "", required: bool = False):
    """Renders a field label + optional help text above a widget."""
    with ui.column().classes("gap-0 w-full"):
        lbl = label
        if required:
            lbl += " *"
        ui.label(lbl).classes("text-sm font-semibold text-grey-8")
        if ayuda:
            ui.label(ayuda).classes("help-text mb-1")


def aviso_requeridos() -> None:
    ui.label("Los campos marcados con * son obligatorios.").classes(
        "text-xs text-grey-5 italic mt-1"
    )


def estado_vacio(mensaje: str, accion: str = "") -> None:
    with ui.column().classes("items-center py-10 gap-2"):
        ui.label("📭").style("font-size:2.5rem")
        ui.label(mensaje).classes("text-grey-6 text-base text-center")
        if accion:
            ui.label(accion).classes("text-blue-600 text-sm text-center font-medium")


def df_to_table(df: pd.DataFrame, pagination: int = 15) -> None:
    if df.empty:
        estado_vacio("Todavía no hay registros aquí.")
        return
    cols = [{"name": c, "label": c, "field": c, "sortable": True} for c in df.columns]
    rows = json.loads(df.to_json(orient="records", date_format="iso", default_handler=str))
    ui.table(columns=cols, rows=rows, pagination=pagination).classes("w-full")


def notificar_ok(msg: str) -> None:
    ui.notify(msg, type="positive", timeout=6000, position="top")


def notificar_error(exc: Exception) -> None:
    ui.notify(
        f"No se pudo guardar. Revisá los datos e intentá de nuevo.\n(Detalle: {exc})",
        type="negative", timeout=8000, position="top",
    )


def notificar_aviso(msg: str) -> None:
    ui.notify(msg, type="warning", timeout=5000, position="top")


# ── navegación ────────────────────────────────────────────────────────────────

def nav(current: str = "/") -> None:
    _css()
    links = [
        ("🏠 Inicio",      "/"),
        ("🐄 Vacas",       "/vacas"),
        ("💊 Salud",       "/salud"),
        ("🥛 Leche",       "/leche"),
        ("🥗 Dietas",      "/dietas"),
        ("📦 Bodega",      "/bodega"),
        ("🚜 Maquinaria",  "/maquinaria"),
        ("🐣 Reproducción", "/reproduccion"),
        ("💰 Finanzas",     "/finanzas"),
    ]
    with ui.header().classes("bg-blue-800 text-white flex items-center gap-2 px-6 py-3"):
        ui.label("🐄 Dairy Farm Pro").classes("text-xl font-bold mr-4")
        for label, href in links:
            extra = " nav-active" if current == href else ""
            ui.link(label, href).classes(
                f"nav-link text-white hover:text-yellow-200 text-sm font-medium px-3 py-1{extra}"
            )


# ── DASHBOARD ────────────────────────────────────────────────────────────────

@ui.page("/")
def dashboard() -> None:
    nav("/")
    with ui.column().classes("px-4 pt-4 pb-1"):
        ui.label("Resumen General").classes("text-2xl font-bold")
        ui.label("Así está tu granja hoy.").classes("text-sm text-grey-6")

    try:
        total_vacas  = int(read_sql("SELECT COUNT(*) FROM tabla_vacas WHERE estado='activa'").iloc[0, 0])
        total_dietas = int(read_sql("SELECT COUNT(*) FROM tabla_dieta").iloc[0, 0])
        litros_hoy   = float(read_sql(
            "SELECT COALESCE(SUM(litros),0) FROM tabla_leche WHERE DATE(fecha_hora)=CURRENT_DATE"
        ).iloc[0, 0])
        df_stock = read_sql(
            "SELECT nombre_insumo, stock_actual_kg FROM tabla_insumos ORDER BY stock_actual_kg DESC"
        )
        df_prod = read_sql("""
            SELECT TO_CHAR(DATE(fecha_hora), 'DD/MM') AS fecha,
                   ROUND(SUM(litros)::numeric, 1)::float AS total_litros
            FROM tabla_leche
            WHERE fecha_hora >= CURRENT_DATE - INTERVAL '7 days'
            GROUP BY DATE(fecha_hora)
            ORDER BY DATE(fecha_hora)
        """)
        df_categorias = read_sql("""
            SELECT COALESCE(grupo,'(sin grupo)') AS grupo, COUNT(*)::int AS total
            FROM tabla_vacas WHERE estado='activa'
            GROUP BY COALESCE(grupo,'(sin grupo)') ORDER BY total DESC
        """)
        stock_critico = read_sql(
            "SELECT nombre_insumo, stock_actual_kg FROM tabla_insumos WHERE stock_actual_kg < %s ORDER BY stock_actual_kg",
            params=(STOCK_ALERTA,)
        )
        partos_inminentes = read_sql("""
            SELECT v.nombre, r.fecha_parto_esperado,
                   (r.fecha_parto_esperado - CURRENT_DATE)::int AS dias
            FROM tabla_reproduccion r
            JOIN tabla_vacas v ON r.vaca_id = v.vaca_id
            WHERE r.tipo_evento = 'Fertilización'
              AND r.fecha_parto_esperado BETWEEN CURRENT_DATE AND CURRENT_DATE + 14
            ORDER BY r.fecha_parto_esperado
        """)
        error_msg = None
    except Exception as exc:
        total_vacas = total_dietas = 0
        litros_hoy  = 0.0
        df_stock = df_prod = df_categorias = pd.DataFrame()
        stock_critico = partos_inminentes = pd.DataFrame()
        error_msg = str(exc)

    # ── Alertas ──
    if not stock_critico.empty or not partos_inminentes.empty:
        with ui.card().classes("mx-4 mt-4 mb-2 bg-amber-50 border-l-4 border-amber-400 p-4"):
            ui.label("⚠  Alertas que necesitan tu atención").classes("font-bold text-amber-800 mb-2")
            for _, row in stock_critico.iterrows():
                ui.label(
                    f"📦  Stock crítico: {row['nombre_insumo']} — quedan {row['stock_actual_kg']:.0f} kg"
                ).classes("text-sm text-amber-900 mb-1")
            for _, row in partos_inminentes.iterrows():
                dias = int(row["dias"])
                txt = "¡Hoy!" if dias == 0 else f"en {dias} día{'s' if dias != 1 else ''}"
                ui.label(
                    f"🐣  Parto esperado de {row['nombre']} — {txt} ({row['fecha_parto_esperado']})"
                ).classes("text-sm text-amber-900 mb-1")

    # ── Métricas ──
    with ui.row().classes("w-full gap-4 px-4 mt-4"):
        for titulo, valor, subtitulo, href in [
            ("🐄 Vacas Activas", str(total_vacas),    "en producción",        "/vacas"),
            ("🥗 Dietas",        str(total_dietas),   "planes alimenticios",  "/dietas"),
            ("🥛 Litros Hoy",    f"{litros_hoy:.1f}", "producidos hoy",       "/leche"),
        ]:
            with ui.card().classes("flex-1 p-6 text-center cursor-pointer hover:shadow-md").on(
                "click", lambda h=href: ui.navigate.to(h)
            ):
                ui.label(titulo).classes("text-xs text-grey-5 uppercase tracking-widest")
                ui.label(valor).classes("text-5xl font-bold text-blue-800 mt-1")
                ui.label(subtitulo).classes("text-xs text-grey-5 mt-1")
                ui.label("Ver →").classes("text-xs text-blue-500 mt-2")

    if error_msg:
        ui.label(f"No se pudo conectar a la base de datos. Avisá al administrador.").classes("text-red m-4 font-semibold")
        return

    # ── Accesos rápidos ──
    with ui.card().classes("mx-4 mt-4 mb-2 p-4"):
        ui.label("Acciones frecuentes").classes("font-bold mb-3 text-grey-7")
        with ui.row().classes("gap-3 flex-wrap"):
            for icono, texto, href in [
                ("🥛", "Registrar ordeñe",       "/leche"),
                ("💊", "Anotar evento de salud", "/salud"),
                ("📦", "Reponer stock",           "/bodega"),
                ("🚜", "Registrar mantenimiento","/maquinaria"),
                ("🐣", "Registrar fertilización","/reproduccion"),
            ]:
                ui.button(f"{icono}  {texto}", on_click=lambda h=href: ui.navigate.to(h)).classes(
                    "bg-blue-50 text-blue-800 font-semibold border border-blue-200 px-4 py-2 text-sm"
                )

    # ── Gráficos ──
    with ui.row().classes("w-full gap-4 px-4 pb-4 mt-4"):
        with ui.card().classes("flex-1"):
            ui.label("Stock de insumos (kg)").classes("font-bold mb-1")
            ui.label("Cuánto hay en bodega de cada alimento o producto.").classes("help-text mb-2")
            if not df_stock.empty:
                ui.echart({
                    "tooltip": {"trigger": "axis"},
                    "xAxis": {
                        "type": "category",
                        "data": list(df_stock["nombre_insumo"]),
                        "axisLabel": {"rotate": 30, "fontSize": 11},
                    },
                    "yAxis": {"type": "value"},
                    "series": [{"type": "bar", "data": [float(v) for v in df_stock["stock_actual_kg"]],
                                "itemStyle": {"color": "#1d4ed8"}}],
                }).classes("w-full h-64")
            else:
                estado_vacio("Sin datos de stock aún.", "Andá a Bodega para cargar insumos.")

        with ui.card().classes("flex-1"):
            ui.label("Producción de leche — últimos 7 días").classes("font-bold mb-1")
            ui.label("Litros totales por día en la última semana.").classes("help-text mb-2")
            if not df_prod.empty:
                ui.echart({
                    "tooltip": {"trigger": "axis"},
                    "xAxis": {"type": "category", "data": list(df_prod["fecha"])},
                    "yAxis": {"type": "value"},
                    "series": [{"type": "line", "data": list(df_prod["total_litros"]),
                                "smooth": True, "areaStyle": {}, "itemStyle": {"color": "#16a34a"}}],
                }).classes("w-full h-64")
            else:
                estado_vacio("Sin registros de leche aún.", "Andá a Leche para registrar ordeñes.")

        with ui.card().classes("flex-1"):
            ui.label("Vacas por grupo").classes("font-bold mb-1")
            ui.label("Distribución de animales según su grupo de alimentación.").classes("help-text mb-2")
            if not df_categorias.empty:
                pie_data = [
                    {"value": int(r["total"]), "name": str(r["grupo"]).capitalize()}
                    for _, r in df_categorias.iterrows()
                ]
                ui.echart({
                    "tooltip": {"trigger": "item", "formatter": "{b}: {c} vacas ({d}%)"},
                    "legend": {"bottom": "2%", "left": "center", "type": "scroll"},
                    "series": [{
                        "type": "pie", "radius": ["45%", "72%"], "avoidLabelOverlap": True,
                        "itemStyle": {"borderRadius": 8, "borderColor": "#fff", "borderWidth": 2},
                        "label": {"show": True, "formatter": "{b}\n{c}"},
                        "emphasis": {"label": {"show": True, "fontSize": 14, "fontWeight": "bold"}},
                        "data": pie_data,
                    }],
                }).classes("w-full h-64")
            else:
                estado_vacio("Sin grupos cargados aún.", "Andá a Vacas para agregar animales.")


# ── VACAS ─────────────────────────────────────────────────────────────────────

@ui.page("/vacas")
def vacas_page() -> None:
    nav("/vacas")
    with ui.column().classes("px-4 pt-4 pb-1"):
        ui.label("🐄 Registro de Animales").classes("text-2xl font-bold")
        ui.label("Acá podés ver todos tus animales y agregar nuevos al plantel.").classes("text-sm text-grey-6")

    try:
        grupos_opts = [ELEGIR] + list(
            read_sql("SELECT nombre_dieta FROM tabla_dieta ORDER BY dieta_id")["nombre_dieta"]
        )
    except Exception as exc:
        ui.label("No se pudo cargar la lista de grupos. Avisá al administrador.").classes("text-red m-4 font-semibold")
        return

    @ui.refreshable
    def resumen_grupos() -> None:
        try:
            df = read_sql("""
                SELECT COALESCE(grupo,'(sin grupo)') AS "Grupo",
                       COUNT(*)::int AS "Animales"
                FROM tabla_vacas WHERE estado='activa'
                GROUP BY grupo ORDER BY "Animales" DESC
            """)
            if not df.empty:
                with ui.row().classes("gap-3 flex-wrap"):
                    for _, row in df.iterrows():
                        with ui.card().classes("p-3 text-center min-w-28"):
                            ui.label(str(row["Grupo"]).capitalize()).classes("text-xs text-grey-6 font-medium")
                            ui.label(str(row["Animales"])).classes("text-3xl font-bold text-blue-700")
            else:
                estado_vacio("Todavía no hay animales en el sistema.", "Usá el formulario de abajo para agregar el primero.")
        except Exception as exc:
            ui.label("Error al cargar grupos.").classes("text-red")

    @ui.refreshable
    def tabla_vacas() -> None:
        try:
            df = read_sql("""
                SELECT COALESCE(nombre,'—') AS "Nombre / Etiqueta",
                       COALESCE(grupo,'—')  AS "Grupo",
                       estado               AS "Estado"
                FROM tabla_vacas ORDER BY grupo, nombre
            """)
            df_to_table(df)
        except Exception as exc:
            ui.label("Error al cargar el listado.").classes("text-red")

    with ui.card().classes("mx-4 mb-4"):
        ui.label("Animales por Grupo").classes("text-lg font-bold mb-3")
        resumen_grupos()

    with ui.card().classes("mx-4 mb-4"):
        ui.label("Agregar un Animal").classes("text-lg font-bold mb-1")
        ui.label("Solo el Grupo es obligatorio. El nombre es un apodo o número para identificarlo fácilmente.").classes("help-text mb-4")
        aviso_requeridos()
        with ui.row().classes("gap-6 items-end flex-wrap mt-3"):
            with ui.column().classes("gap-1"):
                campo("Grupo", "¿En qué grupo de alimentación va este animal?", required=True)
                grupo = ui.select(grupos_opts, value=grupos_opts[0]).classes("w-56")
            with ui.column().classes("gap-1"):
                campo("Nombre o Etiqueta", "Podés escribir un apodo, número o código. Si lo dejás vacío se asigna uno automático.")
                nombre = ui.input(placeholder="Ej: Manchita, #42, Oreja-Amarilla…").classes("w-56")

            def guardar_vaca() -> None:
                if grupo.value == ELEGIR:
                    notificar_aviso("Primero elegí el grupo al que pertenece el animal.")
                    return
                try:
                    conn = conectar(); cur = conn.cursor()
                    nombre_val = nombre.value.strip() or None
                    if not nombre_val:
                        cur.execute("SELECT COUNT(*) FROM tabla_vacas")
                        n = cur.fetchone()[0] + 1
                        nombre_val = f"Animal {n}"
                    cur.execute(
                        "INSERT INTO tabla_vacas (nombre, grupo, estado) VALUES (%s, %s, 'activa')",
                        (nombre_val, grupo.value),
                    )
                    conn.commit(); cur.close(); conn.close()
                    notificar_ok(f"✓ {nombre_val} fue agregado al grupo '{grupo.value}'.")
                    nombre.value = ""
                    tabla_vacas.refresh()
                    resumen_grupos.refresh()
                except Exception as exc:
                    notificar_error(exc)

            ui.button("➕  Agregar Animal", on_click=guardar_vaca).classes(
                "bg-blue-700 text-white font-bold px-8 py-3 text-base"
            )

    with ui.card().classes("mx-4 mb-4"):
        ui.label("Todos los Animales").classes("text-lg font-bold mb-2")
        tabla_vacas()


# ── SALUD ─────────────────────────────────────────────────────────────────────

@ui.page("/salud")
def salud_page() -> None:
    nav("/salud")
    with ui.column().classes("px-4 pt-4 pb-1"):
        ui.label("💊 Control Sanitario").classes("text-2xl font-bold")
        ui.label("Registrá cualquier atención veterinaria: vacunas, tratamientos o revisiones.").classes("text-sm text-grey-6")

    try:
        vacas_opts = [ELEGIR] + list(
            read_sql("SELECT nombre FROM tabla_vacas WHERE estado='activa' ORDER BY nombre")["nombre"]
        )
    except Exception as exc:
        ui.label("No se pudo cargar la lista de animales. Avisá al administrador.").classes("text-red m-4 font-semibold")
        return

    @ui.refreshable
    def tabla_hist() -> None:
        try:
            df = read_sql("""
                SELECT v.nombre      AS "Animal",
                       TO_CHAR(s.fecha,'DD/MM/YYYY') AS "Fecha",
                       s.tipo_evento AS "Tipo de Atención",
                       s.descripcion AS "Descripción",
                       COALESCE(s.veterinario,'—') AS "Veterinario",
                       s.costo       AS "Costo $"
                FROM tabla_salud s
                JOIN tabla_vacas v ON s.vaca_id = v.vaca_id
                ORDER BY s.fecha DESC LIMIT 100
            """)
            df_to_table(df)
        except Exception as exc:
            ui.label("Error al cargar el historial.").classes("text-red")

    with ui.card().classes("mx-4 mb-4"):
        ui.label("Registrar una Atención").classes("text-lg font-bold mb-1")
        ui.label("Completá los datos de la atención que recibió el animal.").classes("help-text mb-3")
        aviso_requeridos()
        with ui.row().classes("w-full gap-4 mt-3"):
            with ui.column().classes("flex-1 gap-3"):
                campo("¿A qué animal?", "", required=True)
                vaca = ui.select(vacas_opts, value=vacas_opts[0]).classes("w-full")

                campo("Tipo de atención", "¿Qué tipo de intervención fue?", required=True)
                tipo = ui.select(TIPOS_EVENTO, value=TIPOS_EVENTO[0]).classes("w-full")

                campo("Veterinario", "Nombre del veterinario o técnico que atendió (opcional).")
                vet = ui.input(placeholder="Ej: Dr. Rodríguez").classes("w-full")

                campo("Costo en pesos ($)", "Cuánto costó la atención. Podés dejarlo en 0 si no sabés.")
                costo = ui.number(value=0.0, min=0, step=0.5).classes("w-full")
            with ui.column().classes("flex-1"):
                campo("Descripción", "Anotá los detalles más importantes de la atención.")
                descr = ui.textarea(placeholder="Ej: Se aplicó vacuna antiaftosa lote 2025. Sin reacciones.").classes("w-full h-52")

        def guardar_salud() -> None:
            if vaca.value == ELEGIR:
                notificar_aviso("Primero elegí el animal que fue atendido.")
                return
            try:
                conn = conectar(); cur = conn.cursor()
                cur.execute("SELECT vaca_id FROM tabla_vacas WHERE nombre=%s", (vaca.value,))
                row = cur.fetchone(); vaca_id = row[0] if row else None
                cur.execute(
                    "INSERT INTO tabla_salud (vaca_id, tipo_evento, descripcion, veterinario, costo) VALUES (%s,%s,%s,%s,%s)",
                    (vaca_id, tipo.value, descr.value, vet.value or None, costo.value or 0),
                )
                conn.commit(); cur.close(); conn.close()
                notificar_ok(f"✓ Atención de {tipo.value.lower()} registrada para {vaca.value}.")
                vet.value = ""; descr.value = ""; costo.value = 0.0
                tabla_hist.refresh()
            except Exception as exc:
                notificar_error(exc)

        ui.button("💾  Guardar Atención", on_click=guardar_salud).classes(
            "mt-4 bg-blue-700 text-white font-bold px-8 py-3 text-base"
        )

    with ui.card().classes("mx-4 mb-4"):
        ui.label("Historial de Atenciones").classes("text-lg font-bold mb-2")
        tabla_hist()


# ── LECHE ─────────────────────────────────────────────────────────────────────

@ui.page("/leche")
def leche_page() -> None:
    nav("/leche")
    with ui.column().classes("px-4 pt-4 pb-1"):
        ui.label("🥛 Registro de Ordeñe").classes("text-2xl font-bold")
        ui.label("Buscá el animal, indicá cuántos litros produjo y guardá.").classes("text-sm text-grey-6")

    try:
        vacas_data = read_sql("""
            SELECT vaca_id, COALESCE(nombre,'—') AS nombre, COALESCE(grupo,'') AS grupo
            FROM tabla_vacas WHERE estado='activa' ORDER BY grupo, nombre
        """).to_dict("records")
    except Exception as exc:
        ui.label("No se pudo cargar la lista de animales. Avisá al administrador.").classes("text-red m-4 font-semibold")
        return

    estado = {"vaca_id": None, "nombre": ""}

    @ui.refreshable
    def tabla_leche() -> None:
        try:
            df = read_sql("""
                SELECT v.nombre AS "Animal",
                       l.litros AS "Litros",
                       TO_CHAR(l.fecha_hora,'DD/MM/YYYY HH24:MI') AS "Fecha y Hora"
                FROM tabla_leche l
                JOIN tabla_vacas v ON l.vaca_id = v.vaca_id
                ORDER BY l.fecha_hora DESC LIMIT 100
            """)
            df_to_table(df)
        except Exception as exc:
            ui.label("Error al cargar registros.").classes("text-red")

    with ui.card().classes("mx-4 mb-4"):
        ui.label("Paso 1 — Buscá el animal").classes("text-lg font-bold mb-1")
        ui.label("Escribí las primeras letras del nombre o grupo para encontrarlo rápido.").classes("help-text mb-3")

        search    = ui.input(placeholder="Escribí aquí el nombre del animal…").classes("w-full text-base")
        resultados = ui.column().classes("w-full gap-1 mt-1")
        sel_label  = ui.label("").classes("text-blue-700 font-semibold mt-2 min-h-6")

        ui.label("Paso 2 — Ingresá los litros y guardá").classes("text-lg font-bold mb-1 mt-4")
        ui.label("Solo disponible después de seleccionar un animal.").classes("help-text mb-3")

        with ui.row().classes("gap-4 items-end mt-2") as form_row:
            with ui.column().classes("gap-0"):
                campo("¿Cuántos litros produjo?", "Podés usar decimales. Ej: 12.5", required=True)
                litros = ui.number(value=0.0, min=0, step=0.5).classes("w-52")

            def guardar_leche() -> None:
                if not estado["vaca_id"]:
                    notificar_aviso("Primero buscá y seleccioná el animal en el paso 1.")
                    return
                if not litros.value or litros.value <= 0:
                    notificar_aviso("Los litros deben ser un número mayor a 0.")
                    return
                try:
                    conn = conectar(); cur = conn.cursor()
                    cur.execute("INSERT INTO tabla_leche (vaca_id, litros) VALUES (%s,%s)",
                                (estado["vaca_id"], litros.value))
                    conn.commit(); cur.close(); conn.close()
                    notificar_ok(f"✓ {litros.value} litros registrados para {estado['nombre']}.")
                    litros.value = 0.0
                    tabla_leche.refresh()
                except Exception as exc:
                    notificar_error(exc)

            ui.button("💾  Registrar Ordeñe", on_click=guardar_leche).classes(
                "bg-blue-700 text-white font-bold px-8 py-3 text-base"
            )

        form_row.set_visibility(False)

        def seleccionar(vid: int, nombre: str) -> None:
            estado["vaca_id"] = vid
            estado["nombre"]  = nombre
            sel_label.set_text(f"✓  Seleccionaste a: {nombre}")
            search.value = nombre
            resultados.clear()
            form_row.set_visibility(True)
            litros.run_method("focus")

        def buscar() -> None:
            term = search.value.strip().lower()
            resultados.clear()
            if estado["nombre"] and term != estado["nombre"].lower():
                estado["vaca_id"] = None
                estado["nombre"]  = ""
                sel_label.set_text("")
                form_row.set_visibility(False)
            if len(term) < 2:
                return
            matches = [v for v in vacas_data if term in v["nombre"].lower() or term in v["grupo"].lower()]
            if not matches:
                with resultados:
                    ui.label("No encontré ningún animal con ese nombre. Probá con menos letras.").classes("text-grey-6 italic text-sm px-2")
                return
            with resultados:
                for v in matches[:15]:
                    with ui.card().classes("w-full p-3 cursor-pointer hover:bg-blue-50").style("border:1px solid #e5e7eb") as card:
                        with ui.row().classes("items-center gap-3"):
                            ui.label(v["nombre"]).classes("font-medium flex-1 text-base")
                            ui.badge(v["grupo"] or "—").props("color=blue").classes("text-xs")
                        card.on("click", lambda vid=v["vaca_id"], nom=v["nombre"]: seleccionar(vid, nom))

        search.on("input", lambda: buscar())

    with ui.card().classes("mx-4 mb-4"):
        ui.label("Últimos Registros de Ordeñe").classes("text-lg font-bold mb-2")
        tabla_leche()


# ── DIETAS ───────────────────────────────────────────────────────────────────

@ui.page("/dietas")
def dietas_page() -> None:
    nav("/dietas")
    with ui.column().classes("px-4 pt-4 pb-1"):
        ui.label("🥗 Dietas y Raciones").classes("text-2xl font-bold")
        ui.label("Cuánto come por día cada grupo de animales y qué ingredientes lleva su ración.").classes("text-sm text-grey-6")

    try:
        df_dietas = read_sql("SELECT dieta_id, nombre_dieta, descripcion_dieta FROM tabla_dieta ORDER BY dieta_id")
    except Exception as exc:
        ui.label("No se pudieron cargar las dietas. Avisá al administrador.").classes("text-red m-4 font-semibold")
        return

    if df_dietas.empty:
        with ui.card().classes("mx-4 mt-4"):
            estado_vacio("Todavía no hay dietas cargadas en el sistema.", "Contactá al administrador para configurar los grupos de alimentación.")
        return

    dietas = []
    for _, row in df_dietas.iterrows():
        try:
            data = json.loads(row["descripcion_dieta"])
            n    = data.get("n", 0)
            comp = data.get("comp", {})
        except Exception:
            n = 0; comp = {}
        dietas.append({"nombre": row["nombre_dieta"], "n": n, "comp": comp, "total": round(sum(comp.values()), 3)})

    total_animales = sum(d["n"] for d in dietas)
    with ui.row().classes("w-full gap-3 px-4 mb-4 mt-2"):
        for titulo, valor, sub, color in [
            ("🥗 Grupos", str(len(dietas)),    "planes de alimentación", "blue-700"),
            ("🐄 Animales", str(total_animales), "en todos los grupos",    "green-700"),
        ]:
            with ui.card().classes("w-48 p-5 text-center"):
                ui.label(titulo).classes("text-xs text-grey-5 uppercase tracking-widest")
                ui.label(valor).classes(f"text-4xl font-bold text-{color} mt-1")
                ui.label(sub).classes("text-xs text-grey-5 mt-1")

    ingr_count: dict = {}
    for d in dietas:
        for k, v in d["comp"].items():
            if v > 0:
                ingr_count[k] = ingr_count.get(k, 0) + 1
    all_ingrs  = sorted(ingr_count, key=lambda k: -ingr_count[k])
    diet_names = [d["nombre"] for d in dietas]

    COLORS = ["#3b82f6","#16a34a","#f59e0b","#ef4444","#8b5cf6",
              "#06b6d4","#f97316","#10b981","#e11d48","#6366f1"]
    series = []
    for idx, ing in enumerate(all_ingrs):
        vals = [round(d["comp"].get(ing, 0), 4) for d in dietas]
        if any(v > 0 for v in vals):
            series.append({
                "name": ing, "type": "bar", "stack": "total", "data": vals,
                "itemStyle": {"color": COLORS[idx % len(COLORS)]},
                "label": {"show": False}, "emphasis": {"focus": "series"},
            })

    with ui.card().classes("mx-4 mb-4"):
        ui.label("📊 Comparativa de Raciones — kg por animal por día").classes("font-bold mb-1")
        ui.label("Pasá el mouse sobre cada barra de color para ver qué ingrediente representa.").classes("help-text mb-2")
        h = max(300, len(dietas) * 52)
        ui.echart({
            "tooltip": {"trigger": "axis", "axisPointer": {"type": "shadow"}},
            "legend": {"bottom": "0%", "type": "scroll", "textStyle": {"fontSize": 11}},
            "grid": {"left": "14%", "right": "6%", "top": "3%", "bottom": "14%"},
            "xAxis": {"type": "value", "name": "kg / animal / día"},
            "yAxis": {"type": "category", "data": diet_names, "axisLabel": {"fontSize": 12}},
            "series": series,
        }).classes("w-full").style(f"height:{h}px;min-height:300px")

    with ui.column().classes("px-4 mb-4 w-full"):
        ui.label("Detalle por Grupo").classes("text-lg font-bold mb-3")
        with ui.grid(columns=4).classes("w-full gap-3"):
            for d in dietas:
                total_kg = d["total"]
                with ui.card().classes("p-4"):
                    ui.label(d["nombre"].capitalize()).classes("text-lg font-bold text-blue-800")
                    with ui.row().classes("gap-2 mt-1 mb-3 flex-wrap"):
                        ui.badge(f"{d['n']} animales").props("color=blue rounded")
                        ui.badge(f"{total_kg:.2f} kg/día").props("color=green rounded")
                    ui.separator()
                    for ing, kg in sorted(d["comp"].items(), key=lambda x: -x[1]):
                        if kg > 0:
                            pct = round(kg / total_kg * 100, 1) if total_kg > 0 else 0
                            with ui.row().classes("justify-between items-center py-0.5"):
                                ui.label(ing).classes("text-sm text-grey-7 flex-1")
                                ui.label(f"{kg:.3f} kg").classes("text-sm font-semibold text-grey-8 mr-2")
                                ui.label(f"{pct}%").classes("text-xs text-grey-5 w-10 text-right")

    with ui.card().classes("mx-4 mb-4"):
        ui.label("📋 Tabla Resumen por Grupo").classes("text-lg font-bold mb-2")
        rows_tabla = []
        for d in dietas:
            row_d = {"Grupo": d["nombre"], "Animales": d["n"], "Total kg/día": d["total"]}
            for ing in all_ingrs:
                row_d[ing] = d["comp"].get(ing, 0)
            rows_tabla.append(row_d)
        df_to_table(pd.DataFrame(rows_tabla))


# ── BODEGA ────────────────────────────────────────────────────────────────────

@ui.page("/bodega")
def bodega_page() -> None:
    nav("/bodega")
    with ui.column().classes("px-4 pt-4 pb-1"):
        ui.label("📦 Bodega e Insumos").classes("text-2xl font-bold")
        ui.label("Controlá el stock de alimentos y productos de tu granja.").classes("text-sm text-grey-6")

    @ui.refreshable
    def contenido_bodega() -> None:
        try:
            df = read_sql("""
                SELECT nombre_insumo,
                       COALESCE(unidad,'kg')                                                AS unidad,
                       ROUND(COALESCE(stock_actual_kg,0)::numeric,1)::float                 AS stock_actual_kg,
                       ROUND(COALESCE(costo_por_kg,0)::numeric,2)::float                    AS costo_por_kg,
                       ROUND((COALESCE(stock_actual_kg,0)*COALESCE(costo_por_kg,0))::numeric,0)::float AS valor_total
                FROM tabla_insumos ORDER BY nombre_insumo
            """)
        except Exception as exc:
            ui.label("No se pudieron cargar los insumos. Avisá al administrador.").classes("text-red-600 m-4 font-semibold")
            return

        total_tipos = len(df)
        stock_total = float(df["stock_actual_kg"].sum()) if not df.empty else 0.0
        valor_total = float(df["valor_total"].sum())     if not df.empty else 0.0
        n_alertas   = int((df["stock_actual_kg"] < STOCK_ALERTA).sum()) if not df.empty else 0

        with ui.row().classes("w-full gap-3 px-4 mb-4"):
            for titulo, valor, subtitulo, color in [
                ("📦 Tipos de insumo", str(total_tipos),         "productos distintos",    "blue-700"),
                ("⚖ Stock Total",     f"{stock_total:,.0f} kg", "en bodega ahora",        "green-700"),
                ("💰 Valor Estimado", f"${valor_total:,.0f}",   "valor del inventario",   "purple-700"),
                ("⚠ Con poco stock",  str(n_alertas),           "insumos a reponer",      "red-700" if n_alertas else "grey-6"),
            ]:
                with ui.card().classes("flex-1 p-5 text-center"):
                    ui.label(titulo).classes("text-xs text-grey-5 uppercase tracking-widest")
                    ui.label(valor).classes(f"text-4xl font-bold text-{color} mt-1")
                    ui.label(subtitulo).classes("text-xs text-grey-5 mt-1")

        if df.empty:
            estado_vacio(
                "Todavía no hay insumos cargados.",
                "Usá el formulario de abajo para agregar el primero."
            )
            return

        def _color(v: float) -> str:
            if v < STOCK_ALERTA: return "#ef4444"
            if v < STOCK_MEDIO:  return "#f59e0b"
            return "#16a34a"

        with ui.row().classes("w-full gap-4 px-4 mb-4"):
            with ui.card().classes("flex-1"):
                ui.label("📊 Stock actual por insumo").classes("font-bold mb-1")
                ui.label("🟢 Suficiente   🟡 Poco stock   🔴 Crítico — hay que reponer").classes("help-text mb-2")
                df_h = df.sort_values("stock_actual_kg")
                h    = max(220, len(df_h) * 44)
                ui.echart({
                    "tooltip": {"trigger": "axis", "formatter": "{b}: {c} kg"},
                    "grid": {"left": "24%", "right": "14%", "top": "3%", "bottom": "3%"},
                    "xAxis": {"type": "value", "name": "kg"},
                    "yAxis": {"type": "category", "data": list(df_h["nombre_insumo"]),
                              "axisLabel": {"fontSize": 12}},
                    "series": [{
                        "type": "bar", "barMaxWidth": 32,
                        "data": [{"value": float(v), "itemStyle": {"color": _color(float(v))}}
                                 for v in df_h["stock_actual_kg"]],
                        "label": {"show": True, "position": "right", "formatter": "{c} kg", "fontSize": 11},
                    }],
                }).classes("w-full").style(f"height:{h}px;min-height:220px")

            with ui.card().classes("flex-1"):
                ui.label("💰 Valor del inventario por insumo").classes("font-bold mb-1")
                ui.label("Qué porción del presupuesto representa cada producto.").classes("help-text mb-2")
                pie_data = [{"value": float(r["valor_total"]), "name": r["nombre_insumo"]}
                            for _, r in df.iterrows() if float(r["valor_total"]) > 0]
                if pie_data:
                    ui.echart({
                        "tooltip": {"trigger": "item", "formatter": "{b}<br/>Valor: ${c}<br/>Parte: {d}%"},
                        "legend": {"bottom": "0%", "left": "center", "type": "scroll",
                                   "textStyle": {"fontSize": 11}},
                        "series": [{
                            "type": "pie", "radius": ["38%", "68%"], "center": ["50%", "44%"],
                            "avoidLabelOverlap": True,
                            "itemStyle": {"borderRadius": 6, "borderColor": "#fff", "borderWidth": 2},
                            "label": {"show": False},
                            "emphasis": {"label": {"show": True, "fontSize": 13, "fontWeight": "bold"},
                                         "itemStyle": {"shadowBlur": 10, "shadowColor": "rgba(0,0,0,0.2)"}},
                            "data": pie_data,
                        }],
                    }).classes("w-full h-72")
                else:
                    estado_vacio("Agregá precios por kg para ver este gráfico.")

        df_precio = df[df["costo_por_kg"] > 0].sort_values("costo_por_kg", ascending=False)
        if not df_precio.empty:
            with ui.card().classes("mx-4 mb-4"):
                ui.label("💲 Precio de compra por kg").classes("font-bold mb-1")
                ui.label("Comparación del costo de cada insumo para tomar mejores decisiones de compra.").classes("help-text mb-2")
                ui.echart({
                    "tooltip": {"trigger": "axis", "formatter": "{b}: ${c}/kg"},
                    "xAxis": {"type": "category", "data": list(df_precio["nombre_insumo"]),
                              "axisLabel": {"rotate": 30, "fontSize": 11}},
                    "yAxis": {"type": "value", "name": "$/kg",
                              "axisLabel": {"formatter": "${value}"}},
                    "series": [{
                        "type": "bar", "data": [float(v) for v in df_precio["costo_por_kg"]],
                        "itemStyle": {"color": "#7c3aed"},
                        "label": {"show": True, "position": "top", "formatter": "${c}"},
                        "barMaxWidth": 50,
                    }],
                }).classes("w-full h-52")

        with ui.column().classes("px-4 mb-4 w-full"):
            ui.label("Estado del stock — semáforo").classes("text-lg font-bold mb-1")
            ui.label(
                f"🔴 Crítico: menos de {STOCK_ALERTA} kg  ·  "
                f"🟡 Bajo: menos de {STOCK_MEDIO} kg  ·  "
                f"🟢 Bien: {STOCK_MEDIO} kg o más"
            ).classes("help-text mb-3")
            with ui.grid(columns=3).classes("w-full gap-3"):
                for _, row in df.iterrows():
                    stock = float(row["stock_actual_kg"])
                    valor = float(row["valor_total"])
                    costo = float(row["costo_por_kg"])
                    unid  = row["unidad"]
                    if stock < STOCK_ALERTA:
                        bg, bdg, icono, etq = "bg-red-50",    "red",   "⚠",  "¡Hay que reponer!"
                    elif stock < STOCK_MEDIO:
                        bg, bdg, icono, etq = "bg-yellow-50", "amber", "⚡", "Stock bajo"
                    else:
                        bg, bdg, icono, etq = "bg-green-50",  "green", "✓",  "Suficiente"
                    with ui.card().classes(f"p-4 {bg}"):
                        with ui.row().classes("items-center justify-between w-full"):
                            ui.label(f"{icono}  {row['nombre_insumo']}").classes("font-bold text-base")
                            ui.badge(etq).props(f"color={bdg} rounded")
                        ui.label(f"{stock:,.1f} {unid}").classes("text-3xl font-bold mt-2 text-grey-8")
                        with ui.row().classes("gap-4 mt-1"):
                            if costo > 0:
                                ui.label(f"${costo:.2f} / {unid}").classes("text-xs text-grey-6")
                            if valor > 0:
                                ui.label(f"Valor total: ${valor:,.0f}").classes("text-xs text-grey-6")

        with ui.card().classes("mx-4 mb-4"):
            ui.label("📋 Inventario Completo").classes("text-lg font-bold mb-2")
            df_tabla = df.rename(columns={
                "nombre_insumo": "Insumo", "unidad": "Unidad",
                "stock_actual_kg": "Stock (kg)", "costo_por_kg": "Precio/kg $",
                "valor_total": "Valor Total $",
            })
            df_to_table(df_tabla)

    contenido_bodega()

    with ui.card().classes("mx-4 mb-4"):
        ui.label("➕ Agregar o Reponer Insumo").classes("text-lg font-bold mb-1")
        ui.label(
            "Si el insumo ya existe, la cantidad que ingresás se suma al stock que ya hay en bodega."
        ).classes("help-text mb-4")
        aviso_requeridos()
        with ui.row().classes("gap-6 items-end flex-wrap mt-3"):
            with ui.column().classes("gap-1"):
                campo("¿Qué insumo es?", "Escribí el nombre exacto. Si ya existe, se suma al stock.", required=True)
                nombre_ins = ui.input(placeholder="Ej: Alfalfa, Maíz, Minerales…").classes("w-56")
            with ui.column().classes("gap-1"):
                campo("Cantidad en kg", "Cuántos kilos vas a ingresar.", required=True)
                stock_kg = ui.number(value=0.0, min=0, step=10).classes("w-44")
            with ui.column().classes("gap-1"):
                campo("Precio por kg ($)", "Cuánto pagaste por kilo. Opcional.")
                costo_kg = ui.number(value=0.0, min=0, step=0.01).classes("w-44")

            def guardar_insumo() -> None:
                if not nombre_ins.value.strip():
                    notificar_aviso("Escribí el nombre del insumo antes de guardar.")
                    return
                if (stock_kg.value or 0) <= 0:
                    notificar_aviso("La cantidad en kg debe ser mayor a 0.")
                    return
                try:
                    conn = conectar(); cur = conn.cursor()
                    cur.execute("""
                        INSERT INTO tabla_insumos (nombre_insumo, stock_actual_kg, costo_por_kg)
                        VALUES (%s,%s,%s)
                        ON CONFLICT (nombre_insumo) DO UPDATE
                            SET stock_actual_kg = tabla_insumos.stock_actual_kg + EXCLUDED.stock_actual_kg,
                                costo_por_kg    = EXCLUDED.costo_por_kg
                    """, (nombre_ins.value.strip(), stock_kg.value or 0, costo_kg.value or 0))
                    conn.commit(); cur.close(); conn.close()
                    notificar_ok(f"✓ '{nombre_ins.value}' actualizado correctamente en bodega.")
                    nombre_ins.value = ""; stock_kg.value = 0.0; costo_kg.value = 0.0
                    contenido_bodega.refresh()
                except Exception as exc:
                    notificar_error(exc)

            ui.button("➕  Agregar Stock", on_click=guardar_insumo).classes(
                "bg-green-600 text-white font-bold px-8 py-3 text-base"
            )


# ── MAQUINARIA ───────────────────────────────────────────────────────────────

@ui.page("/maquinaria")
def maquinaria_page() -> None:
    nav("/maquinaria")
    with ui.column().classes("px-4 pt-4 pb-1"):
        ui.label("🚜 Control de Maquinaria").classes("text-2xl font-bold")
        ui.label("Registrá tus máquinas y llevá un historial de cada mantenimiento realizado.").classes("text-sm text-grey-6")

    @ui.refreshable
    def tabla_maquinas() -> None:
        try:
            df = read_sql("""
                SELECT nombre AS "Nombre", tipo AS "Tipo", marca AS "Marca",
                       modelo AS "Modelo", anio AS "Año", estado AS "Estado"
                FROM tabla_maquinaria ORDER BY nombre
            """)
            if df.empty:
                estado_vacio("Todavía no hay máquinas registradas.", "Usá el formulario de arriba para agregar la primera.")
            else:
                df_to_table(df)
        except Exception as exc:
            ui.label("Error al cargar el listado.").classes("text-red")

    @ui.refreshable
    def tabla_mantenimiento() -> None:
        try:
            df = read_sql("""
                SELECT m.nombre AS "Máquina",
                       TO_CHAR(t.fecha,'DD/MM/YYYY') AS "Fecha",
                       t.tipo_mantencion             AS "Tipo",
                       t.descripcion                 AS "Descripción",
                       COALESCE(t.tecnico,'—')       AS "Técnico",
                       t.horas_uso                   AS "Horas uso",
                       t.costo                       AS "Costo $",
                       TO_CHAR(t.proximo_mantenimiento,'DD/MM/YYYY') AS "Próximo mant."
                FROM tabla_mantenimiento t
                JOIN tabla_maquinaria m ON t.maquina_id = m.maquina_id
                ORDER BY t.fecha DESC LIMIT 100
            """)
            if df.empty:
                estado_vacio("Todavía no hay mantenimientos registrados.")
            else:
                df_to_table(df)
        except Exception as exc:
            ui.label("Error al cargar el historial.").classes("text-red")

    with ui.card().classes("mx-4 mb-4"):
        ui.label("Registrar una Máquina").classes("text-lg font-bold mb-1")
        ui.label("Completá los datos principales. Solo el Nombre es obligatorio.").classes("help-text mb-3")
        aviso_requeridos()
        with ui.row().classes("w-full gap-4 mt-3"):
            with ui.column().classes("flex-1 gap-3"):
                campo("Nombre de la máquina", "Usá un nombre que la identifique claramente en tu campo.", required=True)
                nombre_maq = ui.input(placeholder="Ej: Tractor Principal, Ordeñadora N°1").classes("w-full")
                campo("Tipo de máquina", "¿Para qué se usa principalmente?")
                tipo_maq = ui.select(TIPOS_MAQUINARIA, value=TIPOS_MAQUINARIA[0]).classes("w-full")
                campo("Estado actual", "¿Cómo se encuentra hoy la máquina?")
                estado_maq = ui.select(ESTADOS_MAQUINA, value=ESTADOS_MAQUINA[0]).classes("w-full")
            with ui.column().classes("flex-1 gap-3"):
                campo("Marca", "Ej: John Deere, Case, New Holland")
                marca_maq = ui.input(placeholder="Ej: John Deere").classes("w-full")
                campo("Modelo", "Número o nombre del modelo.")
                modelo_maq = ui.input(placeholder="Ej: 5075E").classes("w-full")
                campo("Año de fabricación")
                anio_maq = ui.number(value=2020, min=1990, max=2030, step=1).classes("w-full")

        def guardar_maquina() -> None:
            if not nombre_maq.value.strip():
                notificar_aviso("El nombre de la máquina es obligatorio.")
                return
            try:
                conn = conectar(); cur = conn.cursor()
                cur.execute("""
                    INSERT INTO tabla_maquinaria (nombre, tipo, marca, modelo, anio, estado)
                    VALUES (%s,%s,%s,%s,%s,%s)
                """, (nombre_maq.value.strip(), tipo_maq.value,
                      marca_maq.value or None, modelo_maq.value or None,
                      int(anio_maq.value) if anio_maq.value else None,
                      estado_maq.value))
                conn.commit(); cur.close(); conn.close()
                notificar_ok(f"✓ Máquina '{nombre_maq.value}' registrada correctamente.")
                nombre_maq.value = ""; marca_maq.value = ""; modelo_maq.value = ""
                tabla_maquinas.refresh()
                selector_maquina.refresh()
            except Exception as exc:
                notificar_error(exc)

        ui.button("💾  Guardar Máquina", on_click=guardar_maquina).classes(
            "mt-4 bg-blue-700 text-white font-bold px-8 py-3 text-base"
        )

    with ui.card().classes("mx-4 mb-4"):
        ui.label("Máquinas Registradas").classes("text-lg font-bold mb-2")
        tabla_maquinas()

    with ui.card().classes("mx-4 mb-4"):
        ui.label("Registrar un Mantenimiento").classes("text-lg font-bold mb-1")
        ui.label("Anotá cada revisión o reparación para llevar el historial al día.").classes("help-text mb-3")
        aviso_requeridos()

        @ui.refreshable
        def selector_maquina() -> None:
            try:
                maq_df   = read_sql("SELECT nombre FROM tabla_maquinaria ORDER BY nombre")
                maq_opts = [ELEGIR] + list(maq_df["nombre"])
            except Exception:
                maq_opts = [ELEGIR]
            maquina_sel.options = maq_opts
            if maquina_sel.value not in maq_opts:
                maquina_sel.value = maq_opts[0]

        campo("¿A qué máquina le hiciste el mantenimiento?", "", required=True)
        maquina_sel = ui.select([ELEGIR], value=ELEGIR).classes("w-full mb-3")
        selector_maquina()

        with ui.row().classes("w-full gap-4"):
            with ui.column().classes("flex-1 gap-3"):
                campo("Tipo de mantenimiento", "¿Qué clase de trabajo se realizó?")
                tipo_mant = ui.select(TIPOS_MANTENCION, value=TIPOS_MANTENCION[0]).classes("w-full")
                campo("Técnico o taller", "Quién hizo el trabajo.")
                tecnico = ui.input(placeholder="Ej: Taller Los Pinos, Juan Méndez").classes("w-full")
                campo("Horas de uso al momento", "Cuántas horas tenía la máquina cuando se hizo el mantenimiento.")
                horas_uso = ui.number(value=0.0, min=0, step=0.5).classes("w-full")
                campo("Costo en pesos ($)")
                costo_mant = ui.number(value=0.0, min=0, step=10).classes("w-full")
            with ui.column().classes("flex-1 gap-3"):
                campo("Descripción del trabajo", "Detallá qué se hizo, qué piezas se cambiaron, etc.")
                descr_mant = ui.textarea(placeholder="Ej: Cambio de aceite y filtros. Se revisaron frenos.").classes("w-full h-32")
                campo("Próximo mantenimiento", "Cuándo hay que volver a hacerle servicio.")
                prox_mant = ui.date().classes("w-full")

        def guardar_mantenimiento() -> None:
            if maquina_sel.value == ELEGIR:
                notificar_aviso("Primero elegí la máquina a la que le hiciste el mantenimiento.")
                return
            try:
                conn = conectar(); cur = conn.cursor()
                cur.execute("SELECT maquina_id FROM tabla_maquinaria WHERE nombre=%s", (maquina_sel.value,))
                row = cur.fetchone(); maquina_id = row[0] if row else None
                cur.execute("""
                    INSERT INTO tabla_mantenimiento
                        (maquina_id, tipo_mantencion, descripcion, tecnico, costo, proximo_mantenimiento, horas_uso)
                    VALUES (%s,%s,%s,%s,%s,%s,%s)
                """, (maquina_id, tipo_mant.value, descr_mant.value,
                      tecnico.value or None, costo_mant.value or 0,
                      prox_mant.value or None, horas_uso.value or None))
                conn.commit(); cur.close(); conn.close()
                notificar_ok(f"✓ Mantenimiento de '{maquina_sel.value}' registrado correctamente.")
                tecnico.value = ""; descr_mant.value = ""
                costo_mant.value = 0.0; horas_uso.value = 0.0
                tabla_mantenimiento.refresh()
            except Exception as exc:
                notificar_error(exc)

        ui.button("💾  Registrar Mantenimiento", on_click=guardar_mantenimiento).classes(
            "mt-4 bg-blue-700 text-white font-bold px-8 py-3 text-base"
        )

    with ui.card().classes("mx-4 mb-4"):
        ui.label("Historial de Mantenimientos").classes("text-lg font-bold mb-2")
        tabla_mantenimiento()


# ── REPRODUCCIÓN ─────────────────────────────────────────────────────────────

@ui.page("/reproduccion")
def reproduccion_page() -> None:
    nav("/reproduccion")
    with ui.column().classes("px-4 pt-4 pb-1"):
        ui.label("🐣 Reproducción").classes("text-2xl font-bold")
        ui.label("Controlá las fechas de fertilización y hacé seguimiento de los partos esperados.").classes("text-sm text-grey-6")

    try:
        vacas_opts = [ELEGIR] + list(
            read_sql("SELECT nombre FROM tabla_vacas WHERE estado='activa' ORDER BY nombre")["nombre"]
        )
    except Exception as exc:
        ui.label("No se pudo cargar la lista de animales. Avisá al administrador.").classes("text-red m-4 font-semibold")
        return

    @ui.refreshable
    def metricas() -> None:
        try:
            fertil_mes  = int(read_sql("""
                SELECT COUNT(*) FROM tabla_reproduccion
                WHERE tipo_evento='Fertilización'
                  AND DATE_TRUNC('month',fecha_evento)=DATE_TRUNC('month',CURRENT_DATE)
            """).iloc[0, 0])
            partos_mes  = int(read_sql("""
                SELECT COUNT(*) FROM tabla_reproduccion
                WHERE tipo_evento='Parto'
                  AND DATE_TRUNC('month',fecha_evento)=DATE_TRUNC('month',CURRENT_DATE)
            """).iloc[0, 0])
            prox_partos = int(read_sql("""
                SELECT COUNT(*) FROM tabla_reproduccion
                WHERE tipo_evento='Fertilización'
                  AND fecha_parto_esperado BETWEEN CURRENT_DATE AND CURRENT_DATE+30
            """).iloc[0, 0])
        except Exception as exc:
            ui.label("Error al cargar métricas.").classes("text-red")
            return
        with ui.row().classes("w-full gap-4 px-4 mt-4 mb-2"):
            for titulo, valor, sub, color in [
                ("💉 Fertilizaciones",  str(fertil_mes),  "realizadas este mes",         "blue-800"),
                ("🐄 Partos",           str(partos_mes),  "registrados este mes",         "green-800"),
                ("📅 Próximos Partos",  str(prox_partos), "esperados en 30 días",         "amber-700" if prox_partos else "grey-6"),
            ]:
                with ui.card().classes("flex-1 p-6 text-center"):
                    ui.label(titulo).classes("text-xs text-grey-5 uppercase tracking-widest")
                    ui.label(valor).classes(f"text-5xl font-bold text-{color} mt-1")
                    ui.label(sub).classes("text-xs text-grey-5 mt-1")

    metricas()

    # ── Próximos partos con urgencia visual ──────────────────────────────────
    @ui.refreshable
    def proximos_partos_card() -> None:
        try:
            df = read_sql("""
                SELECT v.nombre                                 AS nombre,
                       r.fecha_evento::text                     AS fecha_fert,
                       r.tipo_fertilizacion                     AS tipo,
                       r.fecha_parto_esperado                   AS fecha_parto,
                       (r.fecha_parto_esperado-CURRENT_DATE)::int AS dias
                FROM tabla_reproduccion r
                JOIN tabla_vacas v ON r.vaca_id=v.vaca_id
                WHERE r.tipo_evento='Fertilización'
                  AND r.fecha_parto_esperado >= CURRENT_DATE
                ORDER BY r.fecha_parto_esperado ASC LIMIT 30
            """)
        except Exception as exc:
            ui.label("Error al cargar próximos partos.").classes("text-red")
            return

        if df.empty:
            estado_vacio(
                "No hay partos esperados próximamente.",
                "Registrá una fertilización para que aparezca aquí la fecha estimada de parto."
            )
            return

        with ui.column().classes("gap-2 w-full"):
            for _, r in df.iterrows():
                dias = int(r["dias"])
                if dias <= 7:
                    bg, badge_color, urgencia = "bg-red-50 border-red-300", "red", f"¡En {dias} día{'s' if dias != 1 else ''}!"
                elif dias <= 30:
                    bg, badge_color, urgencia = "bg-amber-50 border-amber-300", "amber", f"En {dias} días"
                else:
                    bg, badge_color, urgencia = "bg-green-50 border-green-300", "green", f"En {dias} días"

                fecha_fmt = pd.to_datetime(r["fecha_parto"]).strftime("%d/%m/%Y") if r["fecha_parto"] else "—"
                fert_fmt  = r["fecha_fert"][:10] if r["fecha_fert"] else "—"
                try:
                    fert_fmt = pd.to_datetime(fert_fmt).strftime("%d/%m/%Y")
                except Exception:
                    pass

                with ui.card().classes(f"w-full p-3 border {bg}"):
                    with ui.row().classes("items-center gap-4 w-full"):
                        ui.label("🐄").style("font-size:1.6rem")
                        with ui.column().classes("flex-1 gap-0"):
                            ui.label(r["nombre"]).classes("font-bold text-base")
                            ui.label(f"Fertilización: {fert_fmt}  ·  Tipo: {r['tipo']}").classes("text-xs text-grey-6")
                        with ui.column().classes("items-end gap-1"):
                            ui.badge(urgencia).props(f"color={badge_color} rounded")
                            ui.label(f"Parto: {fecha_fmt}").classes("text-sm font-semibold")

    with ui.card().classes("mx-4 mb-4"):
        ui.label("📅 Próximos Partos Esperados").classes("text-lg font-bold mb-1")
        ui.label(f"Calculado sumando {GESTACION_DIAS} días a la fecha de fertilización.  🔴 ≤ 7 días  ·  🟡 ≤ 30 días  ·  🟢 más de 30 días.").classes("help-text mb-3")
        proximos_partos_card()

    # ── Formulario Fertilización ──────────────────────────────────────────────
    with ui.card().classes("mx-4 mb-4"):
        ui.label("💉 Registrar una Fertilización").classes("text-lg font-bold mb-1")
        ui.label(
            f"Al guardar, el sistema calcula automáticamente la fecha estimada de parto ({GESTACION_DIAS} días de gestación)."
        ).classes("help-text mb-3")
        aviso_requeridos()
        with ui.row().classes("w-full gap-4 mt-3"):
            with ui.column().classes("flex-1 gap-3"):
                campo("¿A qué vaca?", "", required=True)
                vaca_f = ui.select(vacas_opts, value=vacas_opts[0]).classes("w-full")
                campo("Tipo de fertilización", "¿Cómo se realizó?", required=True)
                tipo_f = ui.select(TIPOS_FERTILIZACION, value=TIPOS_FERTILIZACION[0]).classes("w-full")
                campo("Fecha de la fertilización", "El día en que se realizó.", required=True)
                fecha_f = ui.date().classes("w-full")
            with ui.column().classes("flex-1"):
                campo("Observaciones", "Anotá el toro utilizado, la dosis, el proveedor o cualquier dato útil.")
                obs_f = ui.textarea(placeholder="Ej: Semen toro 'Relampago', dosis n.º 3, sin complicaciones.").classes("w-full h-44")

        def guardar_fertilizacion() -> None:
            if vaca_f.value == ELEGIR:
                notificar_aviso("Primero elegí el animal que fue fertilizado.")
                return
            if not fecha_f.value:
                notificar_aviso("Indicá la fecha en que se realizó la fertilización.")
                return
            try:
                fecha_fert      = date.fromisoformat(fecha_f.value)
                fecha_parto_esp = fecha_fert + timedelta(days=GESTACION_DIAS)
                conn = conectar(); cur = conn.cursor()
                cur.execute("SELECT vaca_id FROM tabla_vacas WHERE nombre=%s", (vaca_f.value,))
                row = cur.fetchone(); vaca_id = row[0] if row else None
                cur.execute("""
                    INSERT INTO tabla_reproduccion
                        (vaca_id, tipo_evento, fecha_evento, tipo_fertilizacion, fecha_parto_esperado, observaciones)
                    VALUES (%s,'Fertilización',%s,%s,%s,%s)
                """, (vaca_id, fecha_fert, tipo_f.value, fecha_parto_esp, obs_f.value or None))
                conn.commit(); cur.close(); conn.close()
                notificar_ok(
                    f"✓ Fertilización registrada para {vaca_f.value}. "
                    f"Parto estimado: {fecha_parto_esp.strftime('%d/%m/%Y')}."
                )
                obs_f.value = ""
                metricas.refresh()
                proximos_partos_card.refresh()
                tabla_historial.refresh()
            except Exception as exc:
                notificar_error(exc)

        ui.button("💾  Registrar Fertilización", on_click=guardar_fertilizacion).classes(
            "mt-4 bg-blue-700 text-white font-bold px-8 py-3 text-base"
        )

    # ── Formulario Parto ──────────────────────────────────────────────────────
    with ui.card().classes("mx-4 mb-4"):
        ui.label("🐄 Registrar un Parto").classes("text-lg font-bold mb-1")
        ui.label("Anotá el resultado y los datos de la cría. El sexo y el peso son opcionales.").classes("help-text mb-3")
        aviso_requeridos()
        with ui.row().classes("w-full gap-4 mt-3"):
            with ui.column().classes("flex-1 gap-3"):
                campo("¿Qué vaca parió?", "", required=True)
                vaca_p = ui.select(vacas_opts, value=vacas_opts[0]).classes("w-full")
                campo("Fecha del parto", "", required=True)
                fecha_p = ui.date().classes("w-full")
                campo("Resultado del parto", "¿Cómo salió el parto?", required=True)
                resultado_p = ui.select(RESULTADOS_PARTO, value=RESULTADOS_PARTO[0]).classes("w-full")
            with ui.column().classes("flex-1 gap-3"):
                campo("Sexo de la cría", "Si nació una cría viva, ¿es macho o hembra?")
                sexo_p = ui.select(["No aplica", "Hembra", "Macho"], value="No aplica").classes("w-full")
                campo("Peso de la cría (kg)", "Cuánto pesó al nacer. Podés dejarlo en 0 si no lo pesaron.")
                peso_p = ui.number(value=0.0, min=0, step=0.5).classes("w-full")
                campo("Observaciones", "Cualquier detalle relevante del parto.")
                obs_p = ui.textarea(placeholder="Ej: Se requirió asistencia veterinaria. Cría vigorosa.").classes("w-full h-24")

        def guardar_parto() -> None:
            if vaca_p.value == ELEGIR:
                notificar_aviso("Primero elegí la vaca que parió.")
                return
            if not fecha_p.value:
                notificar_aviso("Indicá la fecha en que ocurrió el parto.")
                return
            try:
                conn = conectar(); cur = conn.cursor()
                cur.execute("SELECT vaca_id FROM tabla_vacas WHERE nombre=%s", (vaca_p.value,))
                row = cur.fetchone(); vaca_id = row[0] if row else None
                sexo_val = None if sexo_p.value == "No aplica" else sexo_p.value.lower()
                peso_val = peso_p.value if (peso_p.value or 0) > 0 else None
                cur.execute("""
                    INSERT INTO tabla_reproduccion
                        (vaca_id, tipo_evento, fecha_evento, resultado_parto, sexo_cria, peso_cria_kg, observaciones)
                    VALUES (%s,'Parto',%s,%s,%s,%s,%s)
                """, (vaca_id, fecha_p.value, resultado_p.value, sexo_val, peso_val, obs_p.value or None))
                conn.commit(); cur.close(); conn.close()
                notificar_ok(f"✓ Parto de {vaca_p.value} registrado como '{resultado_p.value}'.")
                obs_p.value = ""; peso_p.value = 0.0
                metricas.refresh()
                tabla_historial.refresh()
            except Exception as exc:
                notificar_error(exc)

        ui.button("💾  Registrar Parto", on_click=guardar_parto).classes(
            "mt-4 bg-green-700 text-white font-bold px-8 py-3 text-base"
        )

    # ── Historial ─────────────────────────────────────────────────────────────
    @ui.refreshable
    def tabla_historial() -> None:
        try:
            df = read_sql("""
                SELECT v.nombre                                            AS "Animal",
                       r.tipo_evento                                       AS "Evento",
                       TO_CHAR(r.fecha_evento,'DD/MM/YYYY')               AS "Fecha",
                       COALESCE(r.tipo_fertilizacion, r.resultado_parto)  AS "Detalle",
                       COALESCE(TO_CHAR(r.fecha_parto_esperado,'DD/MM/YYYY'),'—') AS "Parto Esperado",
                       COALESCE(r.sexo_cria,'—')                          AS "Sexo Cría",
                       COALESCE(r.peso_cria_kg::text,'—')                 AS "Peso Cría (kg)",
                       COALESCE(r.observaciones,'—')                      AS "Observaciones"
                FROM tabla_reproduccion r
                JOIN tabla_vacas v ON r.vaca_id=v.vaca_id
                ORDER BY r.fecha_evento DESC, r.registro_id DESC LIMIT 100
            """)
            if df.empty:
                estado_vacio("Todavía no hay eventos reproductivos registrados.",
                             "Registrá la primera fertilización usando el formulario de arriba.")
            else:
                df_to_table(df)
        except Exception as exc:
            ui.label("Error al cargar el historial.").classes("text-red")

    with ui.card().classes("mx-4 mb-4"):
        ui.label("Historial Reproductivo Completo").classes("text-lg font-bold mb-2")
        tabla_historial()


# ── FINANZAS ─────────────────────────────────────────────────────────────────

@ui.page("/finanzas")
def finanzas_page() -> None:
    nav("/finanzas")
    with ui.column().classes("px-4 pt-4 pb-1"):
        ui.label("💰 Finanzas").classes("text-2xl font-bold")
        ui.label("Registrá tus ingresos y gastos para saber cómo está la plata de tu granja.").classes("text-sm text-grey-6")

    # ── KPIs del mes actual ───────────────────────────────────────────────────
    @ui.refreshable
    def kpis() -> None:
        try:
            ingresos_mes = float(read_sql("""
                SELECT COALESCE(SUM(monto),0) FROM tabla_finanzas
                WHERE tipo='Ingreso'
                  AND DATE_TRUNC('month',fecha)=DATE_TRUNC('month',CURRENT_DATE)
            """).iloc[0, 0])
            egresos_mes = float(read_sql("""
                SELECT COALESCE(SUM(monto),0) FROM tabla_finanzas
                WHERE tipo='Egreso'
                  AND DATE_TRUNC('month',fecha)=DATE_TRUNC('month',CURRENT_DATE)
            """).iloc[0, 0])
            # Costos automáticos del mes (salud + mantenimiento)
            costos_auto = float(read_sql("""
                SELECT COALESCE(SUM(costo),0) FROM (
                    SELECT costo FROM tabla_salud
                    WHERE DATE_TRUNC('month',fecha)=DATE_TRUNC('month',CURRENT_DATE)
                    UNION ALL
                    SELECT costo FROM tabla_mantenimiento
                    WHERE DATE_TRUNC('month',fecha)=DATE_TRUNC('month',CURRENT_DATE)
                ) t
            """).iloc[0, 0])
            balance_mes   = ingresos_mes - egresos_mes
            ingresos_anio = float(read_sql("""
                SELECT COALESCE(SUM(monto),0) FROM tabla_finanzas
                WHERE tipo='Ingreso' AND EXTRACT(year FROM fecha)=EXTRACT(year FROM CURRENT_DATE)
            """).iloc[0, 0])
            egresos_anio = float(read_sql("""
                SELECT COALESCE(SUM(monto),0) FROM tabla_finanzas
                WHERE tipo='Egreso' AND EXTRACT(year FROM fecha)=EXTRACT(year FROM CURRENT_DATE)
            """).iloc[0, 0])
            balance_anio = ingresos_anio - egresos_anio
        except Exception as exc:
            ui.label("Error al calcular métricas.").classes("text-red m-4")
            return

        bal_color_mes  = "green-700" if balance_mes  >= 0 else "red-700"
        bal_color_anio = "green-700" if balance_anio >= 0 else "red-700"
        bal_icono_mes  = "▲" if balance_mes  >= 0 else "▼"
        bal_icono_anio = "▲" if balance_anio >= 0 else "▼"

        with ui.row().classes("w-full gap-3 px-4 mt-4 flex-wrap"):
            # Mes actual
            for titulo, valor, sub, color in [
                ("📈 Ingresos del mes",  f"${ingresos_mes:,.0f}", "entradas este mes",   "green-700"),
                ("📉 Egresos del mes",   f"${egresos_mes:,.0f}",  "gastos este mes",      "red-700"),
                (f"{bal_icono_mes} Balance del mes",
                 f"${abs(balance_mes):,.0f}",
                 "ganancia" if balance_mes >= 0 else "pérdida",
                 bal_color_mes),
            ]:
                with ui.card().classes("flex-1 p-5 text-center min-w-40"):
                    ui.label(titulo).classes("text-xs text-grey-5 uppercase tracking-widest")
                    ui.label(valor).classes(f"text-4xl font-bold text-{color} mt-1")
                    ui.label(sub).classes("text-xs text-grey-5 mt-1")

            # Año
            with ui.card().classes("flex-1 p-5 text-center min-w-40 bg-blue-50"):
                ui.label("🗓 Balance del año").classes("text-xs text-grey-5 uppercase tracking-widest")
                ui.label(f"${abs(balance_anio):,.0f}").classes(f"text-4xl font-bold text-{bal_color_anio} mt-1")
                ui.label("ganancia acumulada" if balance_anio >= 0 else "pérdida acumulada").classes("text-xs text-grey-5 mt-1")

        if costos_auto > 0:
            with ui.card().classes("mx-4 mt-3 mb-1 p-3 bg-amber-50 border-l-4 border-amber-300"):
                ui.label(
                    f"ℹ  Este mes también hay ${costos_auto:,.0f} en costos registrados en Salud y Maquinaria "
                    "que no están incluidos arriba. Podés cargarlos manualmente si querés verlos en el balance."
                ).classes("text-sm text-amber-800")

    kpis()

    # ── Gráficos ──────────────────────────────────────────────────────────────
    @ui.refreshable
    def graficos() -> None:
        try:
            df_mensual = read_sql("""
                SELECT TO_CHAR(DATE_TRUNC('month',fecha),'MM/YYYY') AS mes,
                       DATE_TRUNC('month',fecha)                     AS mes_ord,
                       tipo,
                       SUM(monto)::float                             AS total
                FROM tabla_finanzas
                WHERE fecha >= CURRENT_DATE - INTERVAL '6 months'
                GROUP BY DATE_TRUNC('month',fecha), tipo
                ORDER BY mes_ord, tipo
            """)
            df_categ = read_sql("""
                SELECT categoria, SUM(monto)::float AS total
                FROM tabla_finanzas
                WHERE tipo='Egreso'
                  AND fecha >= CURRENT_DATE - INTERVAL '6 months'
                GROUP BY categoria ORDER BY total DESC
            """)
        except Exception as exc:
            ui.label("Error al cargar gráficos.").classes("text-red")
            return

        if df_mensual.empty:
            estado_vacio("Todavía no hay movimientos registrados.", "Usá el formulario de abajo para cargar el primero.")
            return

        meses = sorted(df_mensual["mes"].unique(), key=lambda m: df_mensual.loc[df_mensual["mes"] == m, "mes_ord"].iloc[0])
        ing_vals = []
        egr_vals = []
        for m in meses:
            sub = df_mensual[df_mensual["mes"] == m]
            ing_row = sub[sub["tipo"] == "Ingreso"]
            egr_row = sub[sub["tipo"] == "Egreso"]
            ing_vals.append(float(ing_row["total"].iloc[0]) if not ing_row.empty else 0)
            egr_vals.append(float(egr_row["total"].iloc[0]) if not egr_row.empty else 0)

        with ui.row().classes("w-full gap-4 px-4 mb-4 mt-4"):
            with ui.card().classes("flex-1"):
                ui.label("📊 Ingresos vs Egresos — últimos 6 meses").classes("font-bold mb-1")
                ui.label("Verde = dinero que entró · Rojo = dinero que salió").classes("help-text mb-2")
                ui.echart({
                    "tooltip": {"trigger": "axis"},
                    "legend": {"data": ["Ingresos", "Egresos"], "bottom": 0},
                    "grid": {"left": "8%", "right": "4%", "top": "6%", "bottom": "14%"},
                    "xAxis": {"type": "category", "data": list(meses)},
                    "yAxis": {"type": "value", "axisLabel": {"formatter": "${value}"}},
                    "series": [
                        {"name": "Ingresos", "type": "bar", "data": ing_vals,
                         "itemStyle": {"color": "#16a34a"}, "barMaxWidth": 40},
                        {"name": "Egresos",  "type": "bar", "data": egr_vals,
                         "itemStyle": {"color": "#ef4444"}, "barMaxWidth": 40},
                    ],
                }).classes("w-full h-64")

            if not df_categ.empty:
                with ui.card().classes("flex-1"):
                    ui.label("🍩 ¿En qué se fue el dinero?").classes("font-bold mb-1")
                    ui.label("Distribución de gastos por categoría en los últimos 6 meses.").classes("help-text mb-2")
                    pie_data = [{"value": float(r["total"]), "name": r["categoria"]}
                                for _, r in df_categ.iterrows()]
                    ui.echart({
                        "tooltip": {"trigger": "item", "formatter": "{b}<br/>${c} ({d}%)"},
                        "legend": {"bottom": 0, "left": "center", "type": "scroll",
                                   "textStyle": {"fontSize": 11}},
                        "series": [{
                            "type": "pie", "radius": ["38%", "66%"],
                            "center": ["50%", "42%"],
                            "avoidLabelOverlap": True,
                            "itemStyle": {"borderRadius": 6, "borderColor": "#fff", "borderWidth": 2},
                            "label": {"show": False},
                            "emphasis": {"label": {"show": True, "fontSize": 13, "fontWeight": "bold"}},
                            "data": pie_data,
                        }],
                    }).classes("w-full h-64")

        # Línea de balance acumulado
        try:
            df_bal = read_sql("""
                SELECT TO_CHAR(DATE_TRUNC('month',fecha),'MM/YYYY') AS mes,
                       DATE_TRUNC('month',fecha)                     AS mes_ord,
                       SUM(CASE WHEN tipo='Ingreso' THEN monto ELSE -monto END)::float AS balance
                FROM tabla_finanzas
                WHERE fecha >= CURRENT_DATE - INTERVAL '6 months'
                GROUP BY DATE_TRUNC('month',fecha)
                ORDER BY mes_ord
            """)
        except Exception:
            df_bal = pd.DataFrame()

        if not df_bal.empty:
            with ui.card().classes("mx-4 mb-4"):
                ui.label("📈 Balance mensual (ganancia o pérdida por mes)").classes("font-bold mb-1")
                ui.label("Por encima de 0 = ganancia · Por debajo = pérdida ese mes").classes("help-text mb-2")
                bal_vals = list(df_bal["balance"])
                bar_colors = ["#16a34a" if v >= 0 else "#ef4444" for v in bal_vals]
                ui.echart({
                    "tooltip": {"trigger": "axis", "formatter": "{b}: ${c}"},
                    "grid": {"left": "8%", "right": "4%", "top": "8%", "bottom": "10%"},
                    "xAxis": {"type": "category", "data": list(df_bal["mes"])},
                    "yAxis": {"type": "value", "axisLabel": {"formatter": "${value}"}},
                    "series": [{
                        "type": "bar", "barMaxWidth": 50,
                        "data": [{"value": v, "itemStyle": {"color": c}}
                                 for v, c in zip(bal_vals, bar_colors)],
                        "markLine": {
                            "silent": True,
                            "data": [{"yAxis": 0}],
                            "lineStyle": {"color": "#94a3b8", "type": "dashed"},
                        },
                    }],
                }).classes("w-full h-52")

    graficos()

    # ── Formulario de registro ─────────────────────────────────────────────────
    with ui.card().classes("mx-4 mb-4"):
        ui.label("➕ Registrar un movimiento").classes("text-lg font-bold mb-1")
        ui.label("Ingresá un ingreso (plata que entrá) o un gasto (plata que sale).").classes("help-text mb-3")
        aviso_requeridos()

        with ui.row().classes("w-full gap-4 mt-3 flex-wrap"):
            with ui.column().classes("gap-3 flex-1"):
                campo("¿Es un ingreso o un gasto?", "", required=True)
                tipo_mov = ui.select(["Ingreso", "Egreso"], value="Ingreso").classes("w-full")

                cat_label_el = ui.label("Categoría *").classes("text-sm font-semibold text-grey-8 mt-1")
                cat_help_el  = ui.label("¿De qué tipo es este movimiento?").classes("help-text")
                categoria    = ui.select(CATEGORIAS_INGRESO, value=CATEGORIAS_INGRESO[0]).classes("w-full")

                def actualizar_categorias() -> None:
                    if tipo_mov.value == "Ingreso":
                        categoria.options = CATEGORIAS_INGRESO
                        categoria.value   = CATEGORIAS_INGRESO[0]
                    else:
                        categoria.options = CATEGORIAS_EGRESO
                        categoria.value   = CATEGORIAS_EGRESO[0]
                    categoria.update()

                tipo_mov.on("update:model-value", lambda _: actualizar_categorias())

                campo("Monto en pesos ($)", "¿Cuánto dinero fue? Solo el número, sin el signo $.", required=True)
                monto = ui.number(value=0.0, min=0, step=100, prefix="$").classes("w-full")

                campo("Fecha", "¿Cuándo ocurrió?", required=True)
                fecha_mov = ui.date(value=date.today().isoformat()).classes("w-full")

            with ui.column().classes("flex-1"):
                campo("Descripción", "Anotá los detalles para recordar de qué se trató.")
                descripcion = ui.textarea(
                    placeholder="Ej: Venta de 4.200 litros de leche a $0.42/lt · Taller López — cambio de aceite tractor"
                ).classes("w-full h-44")

        def guardar_movimiento() -> None:
            if (monto.value or 0) <= 0:
                notificar_aviso("El monto debe ser un número mayor a 0.")
                return
            if not fecha_mov.value:
                notificar_aviso("Indicá la fecha del movimiento.")
                return
            try:
                conn = conectar(); cur = conn.cursor()
                cur.execute(
                    "INSERT INTO tabla_finanzas (fecha, tipo, categoria, descripcion, monto) VALUES (%s,%s,%s,%s,%s)",
                    (fecha_mov.value, tipo_mov.value, categoria.value,
                     descripcion.value or None, monto.value),
                )
                conn.commit(); cur.close(); conn.close()
                signo = "+" if tipo_mov.value == "Ingreso" else "-"
                notificar_ok(f"✓ {tipo_mov.value} de ${monto.value:,.0f} registrado correctamente ({signo}).")
                monto.value = 0.0; descripcion.value = ""
                kpis.refresh()
                graficos.refresh()
                tabla_hist.refresh()
            except Exception as exc:
                notificar_error(exc)

        ui.button("💾  Guardar Movimiento", on_click=guardar_movimiento).classes(
            "mt-4 bg-blue-700 text-white font-bold px-8 py-3 text-base"
        )

    # ── Costos automáticos de otras secciones ────────────────────────────────
    with ui.card().classes("mx-4 mb-4"):
        ui.label("🔗 Costos registrados en otras secciones").classes("text-lg font-bold mb-1")
        ui.label(
            "Estos costos se generaron al registrar atenciones veterinarias y mantenimientos. "
            "Están aquí como referencia — si querés incluirlos en el balance, cargalos manualmente arriba."
        ).classes("help-text mb-3")
        try:
            df_auto = read_sql("""
                SELECT 'Salud animal' AS origen,
                       TO_CHAR(DATE_TRUNC('month',fecha),'MM/YYYY') AS mes,
                       SUM(costo)::float AS total
                FROM tabla_salud WHERE costo > 0
                GROUP BY DATE_TRUNC('month',fecha)
                UNION ALL
                SELECT 'Mantenimiento maquinaria',
                       TO_CHAR(DATE_TRUNC('month',fecha),'MM/YYYY'),
                       SUM(costo)::float
                FROM tabla_mantenimiento WHERE costo > 0
                GROUP BY DATE_TRUNC('month',fecha)
                ORDER BY mes DESC, origen
                LIMIT 24
            """)
            if df_auto.empty:
                estado_vacio("Sin costos automáticos registrados aún.")
            else:
                df_auto.columns = ["Origen", "Mes", "Total $"]
                df_to_table(df_auto)
        except Exception as exc:
            ui.label("Error al cargar costos automáticos.").classes("text-red")

    # ── Historial ─────────────────────────────────────────────────────────────
    @ui.refreshable
    def tabla_hist() -> None:
        try:
            df = read_sql("""
                SELECT TO_CHAR(fecha,'DD/MM/YYYY') AS "Fecha",
                       tipo                         AS "Tipo",
                       categoria                    AS "Categoría",
                       descripcion                  AS "Descripción",
                       monto                        AS "Monto $"
                FROM tabla_finanzas
                ORDER BY fecha DESC, finanza_id DESC
                LIMIT 100
            """)
            if df.empty:
                estado_vacio("Todavía no hay movimientos registrados.", "Usá el formulario de arriba para agregar el primero.")
            else:
                df_to_table(df)
        except Exception as exc:
            ui.label("Error al cargar el historial.").classes("text-red")

    with ui.card().classes("mx-4 mb-4"):
        ui.label("📋 Historial de Movimientos").classes("text-lg font-bold mb-2")
        tabla_hist()


ui.run(title="Dairy Farm Pro", port=8080, reload=False)
