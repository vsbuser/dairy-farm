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
    "Vacinação", "Controle rotineiro", "Tratamento",
    "Doença", "Parto assistido", "Cirurgia",
]
TIPOS_MAQUINARIA = [
    "Trator", "Ordenhadeira", "Compressor", "Gerador",
    "Mixer", "Carregadeira", "Bomba", "Cisterna", "Outro",
]
TIPOS_MANTENCION = [
    "Preventivo", "Corretivo", "Troca de óleo",
    "Revisão geral", "Reparo", "Calibração",
]
ESTADOS_MAQUINA     = ["Operacional", "Em manutenção", "Fora de serviço"]
TIPOS_FERTILIZACION = ["Inseminação Artificial", "Monta Natural"]
RESULTADOS_PARTO    = ["Bem-sucedido", "Gemelar", "Aborto", "Cria morta"]
GESTACION_DIAS      = 283
STOCK_ALERTA        = 100
STOCK_MEDIO         = 300

CARGOS_EMPLEADO = [
    "Capataz", "Ordenhador/a", "Tratorista", "Resp. por alimentação",
    "Resp. por sanidade", "Veterinário/a de campo", "Administrador/a",
    "Trabalhador rural", "Outro",
]
TIPOS_PAGO_EMP = ["Salário", "Adiantamento", "Bônus", "Rescisão"]

CATEGORIAS_INGRESO = [
    "Venda de leite",
    "Venda de animais",
    "Subsídio ou apoio estatal",
    "Outra receita",
]
CATEGORIAS_EGRESO = [
    "Alimentação e insumos",
    "Veterinário e saúde animal",
    "Manutenção de maquinário",
    "Mão de obra",
    "Combustível",
    "Serviços (luz, água, gás)",
    "Outros gastos",
]

ELEGIR = "— Escolha uma opção —"


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
    ui.label("Os campos marcados com * são obrigatórios.").classes(
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
        estado_vacio("Ainda não há registros aqui.")
        return
    cols = [{"name": c, "label": c, "field": c, "sortable": True} for c in df.columns]
    rows = json.loads(df.to_json(orient="records", date_format="iso", default_handler=str))
    ui.table(columns=cols, rows=rows, pagination=pagination).classes("w-full")


def notificar_ok(msg: str) -> None:
    ui.notify(msg, type="positive", timeout=6000, position="top")


def notificar_error(exc: Exception) -> None:
    ui.notify(
        f"Não foi possível salvar. Verifique os dados e tente novamente.\n(Detalhe: {exc})",
        type="negative", timeout=8000, position="top",
    )


def notificar_aviso(msg: str) -> None:
    ui.notify(msg, type="warning", timeout=5000, position="top")


# ── navegación ────────────────────────────────────────────────────────────────

def nav(current: str = "/") -> None:
    _css()
    links = [
        ("🏠 Início",      "/"),
        ("🐄 Vacas",       "/vacas"),
        ("💊 Saúde",       "/salud"),
        ("🥛 Leite",       "/leche"),
        ("🥗 Dietas",      "/dietas"),
        ("📦 Estoque",      "/bodega"),
        ("🚜 Maquinário",  "/maquinaria"),
        ("🐣 Reprodução", "/reproduccion"),
        ("💰 Finanças",     "/finanzas"),
        ("👷 Funcionários",    "/empleados"),
        ("📊 Relatórios",     "/reportes"),
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
        ui.label("Resumo Geral").classes("text-2xl font-bold")
        ui.label("Veja como está sua fazenda hoje.").classes("text-sm text-grey-6")

    try:
        total_vacas  = int(read_sql("SELECT COUNT(*) FROM tabla_vacas WHERE estado='ativa'").iloc[0, 0])
        total_dietas = int(read_sql("SELECT COUNT(*) FROM tabla_dieta").iloc[0, 0])
        litros_hoy   = float(read_sql(
            "SELECT COALESCE(SUM(litros),0) FROM tabla_leche WHERE DATE(fecha_hora)=CURRENT_DATE"
        ).iloc[0, 0])
        litros_ayer  = float(read_sql(
            "SELECT COALESCE(SUM(litros),0) FROM tabla_leche WHERE DATE(fecha_hora)=CURRENT_DATE-1"
        ).iloc[0, 0])
        vacas_tratamiento = int(read_sql("""
            SELECT COUNT(DISTINCT vaca_id) FROM tabla_salud
            WHERE tipo_evento IN ('Tratamento','Doença')
              AND fecha >= CURRENT_DATE - 7
        """).iloc[0, 0])
        balance_mes = float(read_sql("""
            SELECT COALESCE(SUM(CASE WHEN tipo='Receita' THEN monto ELSE -monto END),0)
            FROM tabla_finanzas
            WHERE DATE_TRUNC('month',fecha)=DATE_TRUNC('month',CURRENT_DATE)
        """).iloc[0, 0])
        litros_por_vaca = round(litros_hoy / total_vacas, 1) if total_vacas else 0.0
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
            FROM tabla_vacas WHERE estado='ativa'
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
            WHERE r.tipo_evento = 'Fertilização'
              AND r.fecha_parto_esperado BETWEEN CURRENT_DATE AND CURRENT_DATE + 30
            ORDER BY r.fecha_parto_esperado
        """)
        maquinaria_vencida = read_sql("""
            SELECT DISTINCT m.nombre, mn.proximo_mantenimiento
            FROM tabla_mantenimiento mn
            JOIN tabla_maquinaria m ON mn.maquina_id = m.maquina_id
            WHERE mn.proximo_mantenimiento < CURRENT_DATE
              AND mn.maquinaria_id = (
                SELECT MAX(mn2.maquinaria_id) FROM tabla_mantenimiento mn2
                WHERE mn2.maquina_id = mn.maquina_id
              )
            ORDER BY mn.proximo_mantenimiento
        """) if False else read_sql("""
            SELECT m.nombre,
                   MAX(mn.proximo_mantenimiento) AS proximo_mantenimiento
            FROM tabla_mantenimiento mn
            JOIN tabla_maquinaria m ON mn.maquina_id = m.maquina_id
            GROUP BY m.maquina_id, m.nombre
            HAVING MAX(mn.proximo_mantenimiento) < CURRENT_DATE
            ORDER BY MAX(mn.proximo_mantenimiento)
        """)
        error_msg = None
    except Exception as exc:
        total_vacas = total_dietas = vacas_tratamiento = 0
        litros_hoy = litros_ayer = litros_por_vaca = balance_mes = 0.0
        df_stock = df_prod = df_categorias = df_hist_dash = pd.DataFrame()
        stock_critico = partos_inminentes = maquinaria_vencida = pd.DataFrame()
        error_msg = str(exc)

    # ── Alertas ──
    _hay_alertas = (
        not stock_critico.empty or not partos_inminentes.empty
        or not maquinaria_vencida.empty or vacas_tratamiento > 0
    )
    if _hay_alertas:
        with ui.card().classes("mx-4 mt-4 mb-2 bg-amber-50 border-l-4 border-amber-400 p-4"):
            ui.label("⚠  Alertas que precisam de atenção").classes("font-bold text-amber-800 mb-2")
            if vacas_tratamiento > 0:
                ui.label(
                    f"💊  {vacas_tratamiento} animal{'is' if vacas_tratamiento != 1 else ''} em tratamento esta semana — veja Saúde."
                ).classes("text-sm text-amber-900 mb-1")
            for _, row in stock_critico.iterrows():
                ui.label(
                    f"📦  Estoque crítico: {row['nombre_insumo']} — restam {row['stock_actual_kg']:.0f} kg"
                ).classes("text-sm text-amber-900 mb-1")
            for _, row in partos_inminentes.iterrows():
                dias = int(row["dias"])
                if dias <= 7:
                    txt = "Hoje!" if dias == 0 else f"Em {dias} dia{'s' if dias != 1 else ''}!"
                    style = "text-sm text-red-700 font-semibold mb-1"
                else:
                    txt = f"Em {dias} dias"
                    style = "text-sm text-amber-900 mb-1"
                ui.label(
                    f"🐣  Parto de {row['nombre']} — {txt} ({row['fecha_parto_esperado']})"
                ).classes(style)
            for _, row in maquinaria_vencida.iterrows():
                ui.label(
                    f"🚜  Manutenção vencida: {row['nombre']} (venceu em {row['proximo_mantenimiento']})"
                ).classes("text-sm text-amber-900 mb-1")

    # ── Métricas ──
    _dif_litros = litros_hoy - litros_ayer
    _dif_txt    = (f"↑ {_dif_litros:+.0f} L vs ontem" if _dif_litros >= 0
                   else f"↓ {_dif_litros:.0f} L vs ontem")
    _dif_color  = "text-green-600" if _dif_litros >= 0 else "text-red-500"
    _bal_color  = "text-green-700 font-bold" if balance_mes >= 0 else "text-red-600 font-bold"
    _trat_color = "text-orange-600 font-bold" if vacas_tratamiento > 0 else "text-blue-800"

    with ui.row().classes("w-full gap-3 px-4 mt-4 flex-wrap"):
        # Vacas activas
        with ui.card().classes("flex-1 min-w-36 p-5 text-center cursor-pointer hover:shadow-md").on(
            "click", lambda: ui.navigate.to("/vacas")
        ):
            ui.label("🐄 Vacas Ativas").classes("text-xs text-grey-5 uppercase tracking-widest")
            ui.label(str(total_vacas)).classes("text-5xl font-bold text-blue-800 mt-1")
            ui.label("em produção").classes("text-xs text-grey-5 mt-1")
            ui.label("Ver →").classes("text-xs text-blue-500 mt-2")

        # Litros hoy
        with ui.card().classes("flex-1 min-w-36 p-5 text-center cursor-pointer hover:shadow-md").on(
            "click", lambda: ui.navigate.to("/leche")
        ):
            ui.label("🥛 Litros Hoje").classes("text-xs text-grey-5 uppercase tracking-widest")
            ui.label(f"{litros_hoy:.0f}").classes("text-5xl font-bold text-blue-800 mt-1")
            ui.label(_dif_txt).classes(f"text-xs {_dif_color} mt-1 font-medium")
            ui.label("Ver →").classes("text-xs text-blue-500 mt-2")

        # L/vaca/día
        with ui.card().classes("flex-1 min-w-36 p-5 text-center cursor-pointer hover:shadow-md").on(
            "click", lambda: ui.navigate.to("/reportes")
        ):
            ui.label("📈 L/Vaca/Dia").classes("text-xs text-grey-5 uppercase tracking-widest")
            ui.label(f"{litros_por_vaca:.1f}").classes("text-5xl font-bold text-blue-800 mt-1")
            ui.label("eficiência hoje").classes("text-xs text-grey-5 mt-1")
            ui.label("Ver relatórios →").classes("text-xs text-blue-500 mt-2")

        # Vacas en tratamiento
        with ui.card().classes("flex-1 min-w-36 p-5 text-center cursor-pointer hover:shadow-md").on(
            "click", lambda: ui.navigate.to("/salud")
        ):
            ui.label("💊 Em Tratamento").classes("text-xs text-grey-5 uppercase tracking-widest")
            ui.label(str(vacas_tratamiento)).classes(f"text-5xl {_trat_color} mt-1")
            ui.label("últimos 7 dias").classes("text-xs text-grey-5 mt-1")
            ui.label("Ver saúde →").classes("text-xs text-blue-500 mt-2")

        # Balance del mes
        with ui.card().classes("flex-1 min-w-36 p-5 text-center cursor-pointer hover:shadow-md").on(
            "click", lambda: ui.navigate.to("/finanzas")
        ):
            ui.label("💰 Balanço do Mês").classes("text-xs text-grey-5 uppercase tracking-widest")
            ui.label(f"${balance_mes:,.0f}").classes(f"text-3xl {_bal_color} mt-2")
            ui.label("receitas – despesas").classes("text-xs text-grey-5 mt-1")
            ui.label("Ver finanças →").classes("text-xs text-blue-500 mt-2")

    if error_msg:
        ui.label(f"Não foi possível conectar ao banco de dados. Avise o administrador.").classes("text-red m-4 font-semibold")
        return

    # ── Accesos rápidos ──
    with ui.card().classes("mx-4 mt-4 mb-2 p-4"):
        ui.label("Ações frequentes").classes("font-bold mb-3 text-grey-7")
        with ui.row().classes("gap-3 flex-wrap"):
            for icono, texto, href in [
                ("🥛", "Registrar ordenha",       "/leche"),
                ("💊", "Registrar evento de saúde", "/salud"),
                ("📦", "Repor estoque",           "/bodega"),
                ("🚜", "Registrar manutenção","/maquinaria"),
                ("🐣", "Registrar fertilização","/reproduccion"),
            ]:
                ui.button(f"{icono}  {texto}", on_click=lambda h=href: ui.navigate.to(h)).classes(
                    "bg-blue-50 text-blue-800 font-semibold border border-blue-200 px-4 py-2 text-sm"
                )

    # ── Gráficos ──
    with ui.row().classes("w-full gap-4 px-4 pb-4 mt-4"):
        with ui.card().classes("flex-1"):
            ui.label("Estoque de insumos (kg)").classes("font-bold mb-1")
            ui.label("Quanto há em estoque de cada alimento ou produto.").classes("help-text mb-2")
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
                estado_vacio("Sem dados de estoque ainda.", "Vá a Estoque para cadastrar insumos.")

        with ui.card().classes("flex-1"):
            ui.label("Produção de leite — últimos 7 dias").classes("font-bold mb-1")
            ui.label("Litros totais por dia na última semana.").classes("help-text mb-2")
            if not df_prod.empty:
                ui.echart({
                    "tooltip": {"trigger": "axis"},
                    "xAxis": {"type": "category", "data": list(df_prod["fecha"])},
                    "yAxis": {"type": "value"},
                    "series": [{"type": "line", "data": list(df_prod["total_litros"]),
                                "smooth": True, "areaStyle": {}, "itemStyle": {"color": "#16a34a"}}],
                }).classes("w-full h-64")
            else:
                estado_vacio("Sem registros de leite ainda.", "Vá a Leite para registrar ordenhas.")

        with ui.card().classes("flex-1"):
            ui.label("Vacas por grupo").classes("font-bold mb-1")
            ui.label("Distribuição de animais por grupo de alimentação.").classes("help-text mb-2")
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
                estado_vacio("Sem grupos cadastrados ainda.", "Vá a Vacas para adicionar animais.")



# ── VACAS ─────────────────────────────────────────────────────────────────────

@ui.page("/vacas")
def vacas_page() -> None:
    nav("/vacas")
    with ui.column().classes("px-4 pt-4 pb-1"):
        ui.label("🐄 Registro de Animais").classes("text-2xl font-bold")
        ui.label("Aqui você pode ver todos os seus animais e adicionar novos ao rebanho.").classes("text-sm text-grey-6")

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
                FROM tabla_vacas WHERE estado='ativa'
                GROUP BY grupo ORDER BY "Animales" DESC
            """)
            if not df.empty:
                with ui.row().classes("gap-3 flex-wrap"):
                    for _, row in df.iterrows():
                        with ui.card().classes("p-3 text-center min-w-28"):
                            ui.label(str(row["Grupo"]).capitalize()).classes("text-xs text-grey-6 font-medium")
                            ui.label(str(row["Animales"])).classes("text-3xl font-bold text-blue-700")
            else:
                estado_vacio("Ainda não há animais no sistema.", "Use o formulário abaixo para adicionar o primeiro.")
        except Exception as exc:
            ui.label("Erro ao carregar grupos.").classes("text-red")

    @ui.refreshable
    def tabla_vacas() -> None:
        try:
            df = read_sql("""
                SELECT vaca_id                         AS id,
                       COALESCE(nombre,'—')            AS "Nome / Etiqueta",
                       COALESCE(grupo,'—')             AS "Grupo",
                       estado                          AS "Estado"
                FROM tabla_vacas ORDER BY grupo, nombre
            """)
            if df.empty:
                estado_vacio("Ainda não há animais no sistema.")
                return
            cols = [
                {"name": "id",     "label": "",                  "field": "id",     "sortable": False},
                {"name": "nombre", "label": "Nombre / Etiqueta", "field": "Nombre / Etiqueta", "sortable": True},
                {"name": "grupo",  "label": "Grupo",             "field": "Grupo",  "sortable": True},
                {"name": "estado", "label": "Estado",            "field": "Estado", "sortable": True},
            ]
            rows = json.loads(df.to_json(orient="records", default_handler=str))
            tbl = ui.table(columns=cols, rows=rows, pagination=20).classes("w-full")
            tbl.add_slot("body-cell-id", """
                <q-td :props="props">
                  <q-btn flat dense size="sm" color="primary" label="Ver ficha →"
                    @click="$parent.$emit('ver', props.row)" />
                </q-td>
            """)
            tbl.on("ver", lambda e: ui.navigate.to(f"/vaca/{e.args['id']}"))
        except Exception as exc:
            ui.label("Erro ao carregar a lista.").classes("text-red")

    with ui.card().classes("mx-4 mb-4"):
        ui.label("Animais por Grupo").classes("text-lg font-bold mb-3")
        resumen_grupos()

    with ui.card().classes("mx-4 mb-4"):
        ui.label("Adicionar um Animal").classes("text-lg font-bold mb-1")
        ui.label("Somente o Grupo é obrigatório. O nome é um apelido ou número para identificar o animal com facilidade.").classes("help-text mb-4")
        aviso_requeridos()
        with ui.row().classes("gap-6 items-end flex-wrap mt-3"):
            with ui.column().classes("gap-1"):
                campo("Grupo", "Em qual grupo de alimentação vai este animal?", required=True)
                grupo = ui.select(grupos_opts, value=grupos_opts[0]).classes("w-56")
            with ui.column().classes("gap-1"):
                campo("Nome ou Etiqueta", "Você pode escrever um apelido, número ou código. Se deixar em branco, será atribuído automaticamente.")
                nombre = ui.input(placeholder="Ex: Manchinha, #42, Orelha-Amarela…").classes("w-56")

            def guardar_vaca() -> None:
                if grupo.value == ELEGIR:
                    notificar_aviso("Primeiro escolha o grupo ao qual pertence o animal.")
                    return
                try:
                    conn = conectar(); cur = conn.cursor()
                    nombre_val = nombre.value.strip() or None
                    if not nombre_val:
                        cur.execute("SELECT COUNT(*) FROM tabla_vacas")
                        n = cur.fetchone()[0] + 1
                        nombre_val = f"Animal {n}"
                    cur.execute(
                        "INSERT INTO tabla_vacas (nombre, grupo, estado) VALUES (%s, %s, 'ativa')",
                        (nombre_val, grupo.value),
                    )
                    conn.commit(); cur.close(); conn.close()
                    notificar_ok(f"✓ {nombre_val} foi adicionado ao grupo '{grupo.value}'.")
                    nombre.value = ""
                    tabla_vacas.refresh()
                    resumen_grupos.refresh()
                except Exception as exc:
                    notificar_error(exc)

            ui.button("➕  Adicionar Animal", on_click=guardar_vaca).classes(
                "bg-blue-700 text-white font-bold px-8 py-3 text-base"
            )

    with ui.card().classes("mx-4 mb-4"):
        ui.label("Todos os Animais").classes("text-lg font-bold mb-2")
        tabla_vacas()


# ── SALUD ─────────────────────────────────────────────────────────────────────

@ui.page("/salud")
def salud_page() -> None:
    nav("/salud")
    with ui.column().classes("px-4 pt-4 pb-1"):
        ui.label("💊 Controle Sanitário").classes("text-2xl font-bold")
        ui.label("Registre qualquer atendimento veterinário: vacinas, tratamentos ou revisões.").classes("text-sm text-grey-6")

    try:
        vacas_opts = [ELEGIR] + list(
            read_sql("SELECT nombre FROM tabla_vacas WHERE estado='ativa' ORDER BY nombre")["nombre"]
        )
    except Exception as exc:
        ui.label("Não foi possível carregar a lista de animais. Avise o administrador.").classes("text-red m-4 font-semibold")
        return

    @ui.refreshable
    def tabla_hist() -> None:
        try:
            df = read_sql("""
                SELECT v.nombre      AS "Animal",
                       TO_CHAR(s.fecha,'DD/MM/YYYY') AS "Data",
                       s.tipo_evento AS "Tipo de Atención",
                       s.descripcion AS "Descrição",
                       COALESCE(s.veterinario,'—') AS "Veterinário",
                       s.costo       AS "Custo R$"
                FROM tabla_salud s
                JOIN tabla_vacas v ON s.vaca_id = v.vaca_id
                ORDER BY s.fecha DESC LIMIT 100
            """)
            df_to_table(df)
        except Exception as exc:
            ui.label("Error al cargar el historial.").classes("text-red")

    with ui.card().classes("mx-4 mb-4"):
        ui.label("Registrar una Atención").classes("text-lg font-bold mb-1")
        ui.label("Preencha os dados do atendimento que o animal recebeu.").classes("help-text mb-3")
        aviso_requeridos()
        with ui.row().classes("w-full gap-4 mt-3"):
            with ui.column().classes("flex-1 gap-3"):
                campo("Qual animal?", "", required=True)
                vaca = ui.select(vacas_opts, value=vacas_opts[0]).classes("w-full")

                campo("Tipo de atendimento", "Que tipo de intervenção foi?", required=True)
                tipo = ui.select(TIPOS_EVENTO, value=TIPOS_EVENTO[0]).classes("w-full")

                campo("Veterinário", "Nombre del veterinario o técnico que atendió (opcional).")
                vet = ui.input(placeholder="Ej: Dr. Rodríguez").classes("w-full")

                campo("Custo (R$)", "Quanto custou o atendimento. Pode deixar 0 se não souber.")
                costo = ui.number(value=0.0, min=0, step=0.5).classes("w-full")
            with ui.column().classes("flex-1"):
                campo("Descrição", "Anote os detalhes mais importantes do atendimento.")
                descr = ui.textarea(placeholder="Ej: Se aplicó vacuna antiaftosa lote 2025. Sin reacciones.").classes("w-full h-52")

        def guardar_salud() -> None:
            if vaca.value == ELEGIR:
                notificar_aviso("Primeiro escolha o animal que foi atendido.")
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

        ui.button("💾  Salvar Atendimento", on_click=guardar_salud).classes(
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
        ui.label("Busque o animal, informe quantos litros produziu e salve.").classes("text-sm text-grey-6")

    try:
        vacas_data = read_sql("""
            SELECT vaca_id, COALESCE(nombre,'—') AS nombre, COALESCE(grupo,'') AS grupo
            FROM tabla_vacas WHERE estado='ativa' ORDER BY grupo, nombre
        """).to_dict("records")
    except Exception as exc:
        ui.label("Não foi possível carregar a lista de animais. Avise o administrador.").classes("text-red m-4 font-semibold")
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
        ui.label("Passo 1 — Busque o animal").classes("text-lg font-bold mb-1")
        ui.label("Digite as primeiras letras do nome ou grupo para encontrá-lo rapidamente.").classes("help-text mb-3")

        search    = ui.input(placeholder="Digite aqui o nome do animal…").classes("w-full text-base")
        resultados = ui.column().classes("w-full gap-1 mt-1")
        sel_label  = ui.label("").classes("text-blue-700 font-semibold mt-2 min-h-6")

        ui.label("Passo 2 — Informe os litros e salve").classes("text-lg font-bold mb-1 mt-4")
        ui.label("Solo disponible después de seleccionar un animal.").classes("help-text mb-3")

        with ui.row().classes("gap-4 items-end mt-2") as form_row:
            with ui.column().classes("gap-0"):
                campo("Quantos litros produziu?", "Pode usar decimais. Ex: 12.5", required=True)
                litros = ui.number(value=0.0, min=0, step=0.5).classes("w-52")

            def guardar_leche() -> None:
                if not estado["vaca_id"]:
                    notificar_aviso("Primeiro busque e selecione o animal no passo 1.")
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

    # ── Registro de produção diária ───────────────────────────────────────────
    ui.separator().classes("mx-4 my-2")
    with ui.column().classes("px-4 pt-2 pb-1"):
        ui.label("📋 Produção Diária do Rebanho").classes("text-xl font-bold")
        ui.label("Registre o total de litros por sessão de ordenha de todo o rebanho.").classes("text-sm text-grey-6")

    @ui.refreshable
    def tabla_produccion_diaria() -> None:
        try:
            df = read_sql("""
                SELECT TO_CHAR(fecha,'DD/MM/YYYY')                    AS "Data",
                       COALESCE(ordenha_1::text, '—')                 AS "Ordenha 1 (L)",
                       COALESCE(ordenha_2::text, '—')                 AS "Ordenha 2 (L)",
                       COALESCE(ordenha_3::text, '—')                 AS "Ordenha 3 (L)",
                       total_litros                                   AS "Total (L)",
                       COALESCE(num_vacas::text, '—')                 AS "Vacas",
                       COALESCE(ROUND(media_litros_vaca,2)::text,'—') AS "L/Vaca"
                FROM tabla_produccion_historica
                ORDER BY fecha DESC LIMIT 60
            """)
            df_to_table(df, pagination=15)
        except Exception as exc:
            ui.label("Error ao carregar registros.").classes("text-red")

    with ui.card().classes("mx-4 mb-4"):
        ui.label("➕ Registrar Ordenha do Dia").classes("text-lg font-bold mb-1")
        ui.label(
            "Se já existe um registro para a data escolhida, ele será atualizado."
        ).classes("help-text mb-3")
        aviso_requeridos()

        with ui.row().classes("gap-5 items-end flex-wrap mt-3"):
            with ui.column().classes("gap-1"):
                campo("Data", "Dia da ordenha.", required=True)
                p_fecha = ui.date().classes("w-44")

            with ui.column().classes("gap-1"):
                campo("Ordenha 1 (L)", "Ex: manha.")
                p_ord1 = ui.number(label="", value=None, min=0, step=0.5,
                                   placeholder="0").classes("w-36")

            with ui.column().classes("gap-1"):
                campo("Ordenha 2 (L)", "Ex: tarde.")
                p_ord2 = ui.number(label="", value=None, min=0, step=0.5,
                                   placeholder="0").classes("w-36")

            with ui.column().classes("gap-1"):
                campo("Ordenha 3 (L)", "Ex: noite.")
                p_ord3 = ui.number(label="", value=None, min=0, step=0.5,
                                   placeholder="0").classes("w-36")

            with ui.column().classes("gap-1"):
                campo("Total (L)", "Deixe 0 para calcular automaticamente.", required=True)
                p_total = ui.number(label="", value=0.0, min=0, step=0.5).classes("w-36")

            with ui.column().classes("gap-1"):
                campo("N° Vacas", "Opcional.")
                p_vacas = ui.number(label="", value=None, min=0, step=1,
                                    placeholder="—").classes("w-28")

        def _val(field):
            v = field.value
            try:
                return float(v) if v is not None and float(v) > 0 else None
            except (TypeError, ValueError):
                return None

        def _auto_total() -> None:
            parts = [_val(p_ord1), _val(p_ord2), _val(p_ord3)]
            filled = [v for v in parts if v is not None]
            if filled:
                p_total.value = round(sum(filled), 2)

        p_ord1.on("update:model-value", lambda _: _auto_total())
        p_ord2.on("update:model-value", lambda _: _auto_total())
        p_ord3.on("update:model-value", lambda _: _auto_total())

        def guardar_produccion() -> None:
            if not p_fecha.value:
                notificar_aviso("Selecione a data da ordenha.")
                return
            total = _val(p_total) or (
                sum(v for v in [_val(p_ord1), _val(p_ord2), _val(p_ord3)] if v) or None
            )
            if not total:
                notificar_aviso("Informe pelo menos o total de litros ou uma das sessions.")
                return
            num_vacas = _val(p_vacas)
            media = round(total / num_vacas, 2) if num_vacas else None
            try:
                conn = conectar(); cur = conn.cursor()
                cur.execute("""
                    INSERT INTO tabla_produccion_historica
                        (fecha, ordenha_1, ordenha_2, ordenha_3,
                         total_litros, num_vacas, media_litros_vaca)
                    VALUES (%s,%s,%s,%s,%s,%s,%s)
                    ON CONFLICT (fecha) DO UPDATE SET
                        ordenha_1         = EXCLUDED.ordenha_1,
                        ordenha_2         = EXCLUDED.ordenha_2,
                        ordenha_3         = EXCLUDED.ordenha_3,
                        total_litros      = EXCLUDED.total_litros,
                        num_vacas         = EXCLUDED.num_vacas,
                        media_litros_vaca = EXCLUDED.media_litros_vaca
                """, (
                    p_fecha.value,
                    _val(p_ord1), _val(p_ord2), _val(p_ord3),
                    total, num_vacas, media,
                ))
                conn.commit(); cur.close(); conn.close()
                notificar_ok(f"Produção de {total:.1f} L registrada para {p_fecha.value}.")
                p_ord1.value = p_ord2.value = p_ord3.value = None
                p_total.value = 0.0; p_vacas.value = None
                tabla_produccion_diaria.refresh()
            except Exception as exc:
                notificar_error(exc)

        ui.button("💾  Salvar Produção", on_click=guardar_produccion).classes(
            "mt-3 bg-blue-700 text-white font-bold px-8 py-3 text-base"
        )

    with ui.card().classes("mx-4 mb-4"):
        ui.label("Registros Recentes de Produção Diária").classes("text-lg font-bold mb-2")
        tabla_produccion_diaria()


# ── DIETAS ───────────────────────────────────────────────────────────────────

@ui.page("/dietas")
def dietas_page() -> None:
    nav("/dietas")
    with ui.column().classes("px-4 pt-4 pb-1"):
        ui.label("🥗 Dietas e Rações").classes("text-2xl font-bold")
        ui.label("Quanto come por dia cada grupo de animais e quais ingredientes compõem a ração.").classes("text-sm text-grey-6")

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
        ui.label("Passe o mouse sobre cada barra de cor para ver qual ingrediente ela representa.").classes("help-text mb-2")
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
        ui.label("Controle o estoque de alimentos e produtos da sua fazenda.").classes("text-sm text-grey-6")

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
                "Use o formulário abaixo para adicionar o primeiro."
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
                ui.label("Qual parte do orçamento representa cada produto.").classes("help-text mb-2")
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
                campo("Qual insumo?", "Digite o nome exato. Se já existir, será somado ao estoque.", required=True)
                nombre_ins = ui.input(placeholder="Ej: Alfalfa, Maíz, Minerales…").classes("w-56")
            with ui.column().classes("gap-1"):
                campo("Quantidade em kg", "Quantos quilos você vai cadastrar.", required=True)
                stock_kg = ui.number(value=0.0, min=0, step=10).classes("w-44")
            with ui.column().classes("gap-1"):
                campo("Preço por kg (R$)", "Quanto você pagou por quilo. Opcional.")
                costo_kg = ui.number(value=0.0, min=0, step=0.01).classes("w-44")

            def guardar_insumo() -> None:
                if not nombre_ins.value.strip():
                    notificar_aviso("Digite o nome do insumo antes de salvar.")
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

    # ── Sección Diesel ────────────────────────────────────────────────────────
    ui.separator().classes("mx-4 my-4")
    with ui.row().classes("w-full px-4 mb-2 items-center"):
        ui.label("⛽ Combustível — Diesel").classes("text-xl font-bold")

    @ui.refreshable
    def contenido_diesel() -> None:
        try:
            df_d = read_sql("""
                SELECT fecha, consumo_litros, estoque_litros,
                       compra_litros, precio_rl, total_rs
                FROM tabla_diesel ORDER BY fecha
            """)
            df_mes = read_sql("""
                SELECT TO_CHAR(DATE_TRUNC('month',fecha),'MM/YYYY') AS mes,
                       DATE_TRUNC('month',fecha)                    AS mes_ord,
                       SUM(consumo_litros)::float                   AS consumo,
                       SUM(compra_litros)::float                    AS compra,
                       ROUND(SUM(total_rs)::numeric,2)::float       AS gasto
                FROM tabla_diesel
                GROUP BY DATE_TRUNC('month',fecha)
                ORDER BY mes_ord
            """)
        except Exception as exc:
            ui.label(f"Error cargando diesel: {exc}").classes("text-red m-4")
            return

        # KPI cards
        estoque_actual = float(df_d["estoque_litros"].dropna().iloc[-1]) if not df_d.empty else 0
        consumo_total  = float(df_d["consumo_litros"].sum()) if not df_d.empty else 0
        gasto_total    = float(df_d["total_rs"].dropna().sum()) if not df_d.empty else 0
        preco_medio    = float(df_d["precio_rl"].dropna().mean()) if not df_d.empty else 0
        ultimo_preco   = float(df_d["precio_rl"].dropna().iloc[-1]) if not df_d.empty else 0

        with ui.row().classes("w-full gap-3 px-4 mb-4"):
            for titulo, valor, sub in [
                ("⛽ Estoque Atual",   f"{estoque_actual:,.0f} L",  "litros disponíveis"),
                ("🔥 Consumo Total",  f"{consumo_total:,.0f} L",   f"{len(df_d)} abastecimentos"),
                ("💰 Gasto Total",    f"R$ {gasto_total:,.2f}",    "histórico completo"),
                ("💲 Último Preço",   f"R$ {ultimo_preco:.2f}/L",  f"média R$ {preco_medio:.2f}/L"),
            ]:
                with ui.card().classes("flex-1 p-5 text-center"):
                    ui.label(titulo).classes("text-xs text-grey-5 uppercase tracking-widest")
                    ui.label(valor).classes("text-2xl font-bold text-blue-800 mt-1")
                    ui.label(sub).classes("text-xs text-grey-5 mt-1")

        # Gráficos
        with ui.row().classes("w-full gap-4 px-4 mb-4"):
            with ui.card().classes("flex-1"):
                ui.label("Consumo e compra por mês (L)").classes("font-bold mb-1")
                ui.label("Quanto foi consumido e comprado a cada mês.").classes("help-text mb-2")
                if not df_mes.empty:
                    consumo_vals = [v if v else 0 for v in df_mes["consumo"].tolist()]
                    compra_vals  = [v if v else 0 for v in df_mes["compra"].tolist()]
                    ui.echart({
                        "tooltip": {"trigger": "axis"},
                        "legend": {"bottom": 0},
                        "xAxis": {"type": "category", "data": list(df_mes["mes"]),
                                  "axisLabel": {"rotate": 35, "fontSize": 10}},
                        "yAxis": {"type": "value", "name": "Litros"},
                        "series": [
                            {"name": "Consumo (L)", "type": "bar", "data": consumo_vals,
                             "itemStyle": {"color": "#ef4444"}, "barMaxWidth": 30},
                            {"name": "Compra (L)",  "type": "bar", "data": compra_vals,
                             "itemStyle": {"color": "#3b82f6"}, "barMaxWidth": 30},
                        ],
                    }).classes("w-full h-56")

            with ui.card().classes("flex-1"):
                ui.label("Evolução do preço R$/L").classes("font-bold mb-1")
                ui.label("Como o preço do diesel variou ao longo do tempo.").classes("help-text mb-2")
                df_preco = df_d[df_d["precio_rl"].notna()].copy()
                if not df_preco.empty:
                    ui.echart({
                        "tooltip": {"trigger": "axis", "formatter": "{b}: R$ {c}/L"},
                        "xAxis": {"type": "category",
                                  "data": [str(d) for d in df_preco["fecha"]],
                                  "axisLabel": {"rotate": 35, "fontSize": 9}},
                        "yAxis": {"type": "value", "name": "R$/L",
                                  "axisLabel": {"formatter": "R${value}"}},
                        "series": [{
                            "type": "line", "data": list(df_preco["precio_rl"].astype(float)),
                            "smooth": True, "symbol": "circle", "symbolSize": 5,
                            "itemStyle": {"color": "#f59e0b"},
                            "areaStyle": {"opacity": 0.15},
                        }],
                    }).classes("w-full h-56")

        # Tabla histórica
        with ui.card().classes("mx-4 mb-4"):
            ui.label("📋 Histórico de Abastecimentos").classes("font-bold mb-2")
            df_tabla = df_d.copy()
            df_tabla["fecha"] = df_tabla["fecha"].astype(str)
            df_tabla.columns = ["Data", "Consumo (L)", "Estoque (L)",
                                 "Compra (L)", "Preço R$/L", "Total R$"]
            df_to_table(df_tabla, pagination=20)

    contenido_diesel()

    # Formulario para registrar nuevo abastecimiento
    with ui.card().classes("mx-4 mb-6"):
        ui.label("⛽ Registrar Abastecimento").classes("text-lg font-bold mb-1")
        ui.label("Registre cada vez que consumiu ou comprou diesel.").classes("help-text mb-4")
        aviso_requeridos()
        with ui.row().classes("gap-4 items-end flex-wrap mt-3"):
            with ui.column().classes("gap-1"):
                campo("Data", "", required=True)
                d_fecha = ui.date().classes("w-40")
            with ui.column().classes("gap-1"):
                campo("Consumo (L)", "Litros utilizados.", required=True)
                d_consumo = ui.number(value=0, min=0, step=50).classes("w-36")
            with ui.column().classes("gap-1"):
                campo("Estoque restante (L)", "Litros que ficaram no tanque.")
                d_estoque = ui.number(value=0, min=0, step=50).classes("w-36")
            with ui.column().classes("gap-1"):
                campo("Compra (L)", "Litros comprados nesta data.")
                d_compra = ui.number(value=0, min=0, step=50).classes("w-36")
            with ui.column().classes("gap-1"):
                campo("Preço R$/L", "Valor pago por litro.")
                d_precio = ui.number(value=0.0, min=0, step=0.01).classes("w-36")

            def guardar_diesel() -> None:
                if not d_fecha.value:
                    notificar_aviso("Selecione a data do abastecimento.")
                    return
                if (d_consumo.value or 0) <= 0:
                    notificar_aviso("O consumo deve ser maior que 0.")
                    return
                try:
                    conn = conectar(); cur = conn.cursor()
                    total = round((d_compra.value or 0) * (d_precio.value or 0), 2) or None
                    cur.execute("""
                        INSERT INTO tabla_diesel
                            (fecha, consumo_litros, estoque_litros, compra_litros, precio_rl, total_rs)
                        VALUES (%s,%s,%s,%s,%s,%s)
                    """, (
                        d_fecha.value,
                        d_consumo.value,
                        d_estoque.value or None,
                        d_compra.value or None,
                        d_precio.value or None,
                        total,
                    ))
                    conn.commit(); cur.close(); conn.close()
                    notificar_ok(f"Abastecimento registrado: {d_consumo.value} L consumidos.")
                    d_consumo.value = 0; d_estoque.value = 0
                    d_compra.value = 0; d_precio.value = 0.0
                    contenido_diesel.refresh()
                except Exception as exc:
                    notificar_error(exc)

            ui.button("💾  Guardar", on_click=guardar_diesel).classes(
                "bg-orange-600 text-white font-bold px-8 py-3 text-base"
            )


# ── MAQUINARIA ───────────────────────────────────────────────────────────────

@ui.page("/maquinaria")
def maquinaria_page() -> None:
    nav("/maquinaria")
    with ui.column().classes("px-4 pt-4 pb-1"):
        ui.label("🚜 Control de Maquinaria").classes("text-2xl font-bold")
        ui.label("Cadastre suas máquinas e mantenha um histórico de cada manutenção realizada.").classes("text-sm text-grey-6")

    @ui.refreshable
    def tabla_maquinas() -> None:
        try:
            df = read_sql("""
                SELECT nombre AS "Nome", tipo AS "Tipo", marca AS "Marca",
                       modelo AS "Modelo", anio AS "Ano", estado AS "Estado"
                FROM tabla_maquinaria ORDER BY nombre
            """)
            if df.empty:
                estado_vacio("Todavía no hay máquinas registradas.", "Usá el formulario de arriba para agregar la primera.")
            else:
                df_to_table(df)
        except Exception as exc:
            ui.label("Erro ao carregar a lista.").classes("text-red")

    @ui.refreshable
    def tabla_mantenimiento() -> None:
        try:
            df = read_sql("""
                SELECT m.nombre AS "Máquina",
                       TO_CHAR(t.fecha,'DD/MM/YYYY') AS "Data",
                       t.tipo_mantencion             AS "Tipo",
                       t.descripcion                 AS "Descrição",
                       COALESCE(t.tecnico,'—')       AS "Técnico",
                       t.horas_uso                   AS "Horas uso",
                       t.costo                       AS "Custo R$",
                       TO_CHAR(t.proximo_mantenimiento,'DD/MM/YYYY') AS "Próximo mant."
                FROM tabla_mantenimiento t
                JOIN tabla_maquinaria m ON t.maquina_id = m.maquina_id
                ORDER BY t.fecha DESC LIMIT 100
            """)
            if df.empty:
                estado_vacio("Ainda não há manutenções registradas.")
            else:
                df_to_table(df)
        except Exception as exc:
            ui.label("Error al cargar el historial.").classes("text-red")

    with ui.card().classes("mx-4 mb-4"):
        ui.label("Registrar una Máquina").classes("text-lg font-bold mb-1")
        ui.label("Preencha os dados principais. Somente o Nome é obrigatório.").classes("help-text mb-3")
        aviso_requeridos()
        with ui.row().classes("w-full gap-4 mt-3"):
            with ui.column().classes("flex-1 gap-3"):
                campo("Nome da máquina", "Usá un nombre que la identifique claramente en tu campo.", required=True)
                nombre_maq = ui.input(placeholder="Ej: Tractor Principal, Ordeñadora N°1").classes("w-full")
                campo("Tipo de máquina", "Para que é usada principalmente?")
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
                notificar_aviso("O nome da máquina é obrigatório.")
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
        ui.label("Máquinas Cadastradas").classes("text-lg font-bold mb-2")
        tabla_maquinas()

    with ui.card().classes("mx-4 mb-4"):
        ui.label("Registrar un Mantenimiento").classes("text-lg font-bold mb-1")
        ui.label("Registre cada revisão ou reparo para manter o histórico atualizado.").classes("help-text mb-3")
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

        campo("Qual máquina recebeu a manutenção?", "", required=True)
        maquina_sel = ui.select([ELEGIR], value=ELEGIR).classes("w-full mb-3")
        selector_maquina()

        with ui.row().classes("w-full gap-4"):
            with ui.column().classes("flex-1 gap-3"):
                campo("Tipo de manutenção", "Que tipo de trabalho foi realizado?")
                tipo_mant = ui.select(TIPOS_MANTENCION, value=TIPOS_MANTENCION[0]).classes("w-full")
                campo("Técnico o taller", "Quién hizo el trabajo.")
                tecnico = ui.input(placeholder="Ej: Taller Los Pinos, Juan Méndez").classes("w-full")
                campo("Horas de uso al momento", "Cuántas horas tenía la máquina cuando se hizo el mantenimiento.")
                horas_uso = ui.number(value=0.0, min=0, step=0.5).classes("w-full")
                campo("Custo (R$)")
                costo_mant = ui.number(value=0.0, min=0, step=10).classes("w-full")
            with ui.column().classes("flex-1 gap-3"):
                campo("Descrição do trabalho", "Detalhe o que foi feito, quais peças foram trocadas, etc.")
                descr_mant = ui.textarea(placeholder="Ej: Cambio de aceite y filtros. Se revisaron frenos.").classes("w-full h-32")
                campo("Próxima manutenção", "Quando será necessário fazer a próxima revisão.")
                prox_mant = ui.date().classes("w-full")

        def guardar_mantenimiento() -> None:
            if maquina_sel.value == ELEGIR:
                notificar_aviso("Primeiro escolha a máquina que recebeu a manutenção.")
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
        ui.label("Histórico de Manutenções").classes("text-lg font-bold mb-2")
        tabla_mantenimiento()


# ── REPRODUCCIÓN ─────────────────────────────────────────────────────────────

@ui.page("/reproduccion")
def reproduccion_page() -> None:
    nav("/reproduccion")
    with ui.column().classes("px-4 pt-4 pb-1"):
        ui.label("🐣 Reprodução").classes("text-2xl font-bold")
        ui.label("Controle as datas de fertilização e acompanhe os partos esperados.").classes("text-sm text-grey-6")

    try:
        vacas_opts = [ELEGIR] + list(
            read_sql("SELECT nombre FROM tabla_vacas WHERE estado='ativa' ORDER BY nombre")["nombre"]
        )
    except Exception as exc:
        ui.label("Não foi possível carregar a lista de animais. Avise o administrador.").classes("text-red m-4 font-semibold")
        return

    @ui.refreshable
    def metricas() -> None:
        try:
            fertil_mes  = int(read_sql("""
                SELECT COUNT(*) FROM tabla_reproduccion
                WHERE tipo_evento='Fertilização'
                  AND DATE_TRUNC('month',fecha_evento)=DATE_TRUNC('month',CURRENT_DATE)
            """).iloc[0, 0])
            partos_mes  = int(read_sql("""
                SELECT COUNT(*) FROM tabla_reproduccion
                WHERE tipo_evento='Parto'
                  AND DATE_TRUNC('month',fecha_evento)=DATE_TRUNC('month',CURRENT_DATE)
            """).iloc[0, 0])
            prox_partos = int(read_sql("""
                SELECT COUNT(*) FROM tabla_reproduccion
                WHERE tipo_evento='Fertilização'
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
                WHERE r.tipo_evento='Fertilização'
                  AND r.fecha_parto_esperado >= CURRENT_DATE
                ORDER BY r.fecha_parto_esperado ASC LIMIT 30
            """)
        except Exception as exc:
            ui.label("Error al cargar próximos partos.").classes("text-red")
            return

        if df.empty:
            estado_vacio(
                "No hay partos esperados próximamente.",
                "Registre uma fertilização para que apareça aqui a data estimada do parto."
            )
            return

        with ui.column().classes("gap-2 w-full"):
            for _, r in df.iterrows():
                dias = int(r["dias"])
                if dias <= 7:
                    bg, badge_color, urgencia = "bg-red-50 border-red-300", "red", f"Em {dias} dia{'s' if dias != 1 else ''}!"
                elif dias <= 30:
                    bg, badge_color, urgencia = "bg-amber-50 border-amber-300", "amber", f"Em {dias} dias"
                else:
                    bg, badge_color, urgencia = "bg-green-50 border-green-300", "green", f"Em {dias} dias"

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
                campo("Qual vaca?", "", required=True)
                vaca_f = ui.select(vacas_opts, value=vacas_opts[0]).classes("w-full")
                campo("Tipo de fertilização", "¿Cómo se realizó?", required=True)
                tipo_f = ui.select(TIPOS_FERTILIZACION, value=TIPOS_FERTILIZACION[0]).classes("w-full")
                campo("Fecha de la fertilización", "El día en que se realizó.", required=True)
                fecha_f = ui.date().classes("w-full")
            with ui.column().classes("flex-1"):
                campo("Observações", "Anote o touro utilizado, a dose, o fornecedor ou qualquer dado útil.")
                obs_f = ui.textarea(placeholder="Ej: Semen toro 'Relampago', dosis n.º 3, sin complicaciones.").classes("w-full h-44")

        def guardar_fertilizacion() -> None:
            if vaca_f.value == ELEGIR:
                notificar_aviso("Primeiro escolha o animal que foi fertilizado.")
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
                    VALUES (%s,'Fertilização',%s,%s,%s,%s)
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
        ui.label("Anote o resultado e os dados da cria. O sexo e o peso são opcionais.").classes("help-text mb-3")
        aviso_requeridos()
        with ui.row().classes("w-full gap-4 mt-3"):
            with ui.column().classes("flex-1 gap-3"):
                campo("Qual vaca pariu?", "", required=True)
                vaca_p = ui.select(vacas_opts, value=vacas_opts[0]).classes("w-full")
                campo("Fecha del parto", "", required=True)
                fecha_p = ui.date().classes("w-full")
                campo("Resultado do parto", "¿Cómo salió el parto?", required=True)
                resultado_p = ui.select(RESULTADOS_PARTO, value=RESULTADOS_PARTO[0]).classes("w-full")
            with ui.column().classes("flex-1 gap-3"):
                campo("Sexo da cria", "Si nació una cría viva, ¿es macho o hembra?")
                sexo_p = ui.select(["No aplica", "Fêmea", "Macho"], value="No aplica").classes("w-full")
                campo("Peso da cria (kg)", "Quanto pesou ao nascer. Pode deixar 0 se não foi pesado.")
                peso_p = ui.number(value=0.0, min=0, step=0.5).classes("w-full")
                campo("Observações", "Cualquier detalle relevante del parto.")
                obs_p = ui.textarea(placeholder="Ej: Se requirió asistencia veterinaria. Cría vigorosa.").classes("w-full h-24")

        def guardar_parto() -> None:
            if vaca_p.value == ELEGIR:
                notificar_aviso("Primeiro escolha a vaca que pariu.")
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
                       TO_CHAR(r.fecha_evento,'DD/MM/YYYY')               AS "Data",
                       COALESCE(r.tipo_fertilizacion, r.resultado_parto)  AS "Detalle",
                       COALESCE(TO_CHAR(r.fecha_parto_esperado,'DD/MM/YYYY'),'—') AS "Parto Esperado",
                       COALESCE(r.sexo_cria,'—')                          AS "Sexo Cría",
                       COALESCE(r.peso_cria_kg::text,'—')                 AS "Peso Cría (kg)",
                       COALESCE(r.observaciones,'—')                      AS "Observações"
                FROM tabla_reproduccion r
                JOIN tabla_vacas v ON r.vaca_id=v.vaca_id
                ORDER BY r.fecha_evento DESC, r.registro_id DESC LIMIT 100
            """)
            if df.empty:
                estado_vacio("Todavía no hay eventos reproductivos registrados.",
                             "Registre a primeira fertilização usando o formulário acima.")
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
        ui.label("💰 Finanças").classes("text-2xl font-bold")
        ui.label("Registre suas receitas e despesas para saber como está o dinheiro da sua fazenda.").classes("text-sm text-grey-6")

    # ── KPIs del mes actual ───────────────────────────────────────────────────
    @ui.refreshable
    def kpis() -> None:
        try:
            ingresos_mes = float(read_sql("""
                SELECT COALESCE(SUM(monto),0) FROM tabla_finanzas
                WHERE tipo='Receita'
                  AND DATE_TRUNC('month',fecha)=DATE_TRUNC('month',CURRENT_DATE)
            """).iloc[0, 0])
            egresos_mes = float(read_sql("""
                SELECT COALESCE(SUM(monto),0) FROM tabla_finanzas
                WHERE tipo='Despesa'
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
                WHERE tipo='Receita' AND EXTRACT(year FROM fecha)=EXTRACT(year FROM CURRENT_DATE)
            """).iloc[0, 0])
            egresos_anio = float(read_sql("""
                SELECT COALESCE(SUM(monto),0) FROM tabla_finanzas
                WHERE tipo='Despesa' AND EXTRACT(year FROM fecha)=EXTRACT(year FROM CURRENT_DATE)
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
                    "que não estão incluídos acima. Pode cadastrá-los manualmente para vê-los no balanço."
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
                WHERE tipo='Despesa'
                  AND fecha >= CURRENT_DATE - INTERVAL '6 months'
                GROUP BY categoria ORDER BY total DESC
            """)
        except Exception as exc:
            ui.label("Error al cargar gráficos.").classes("text-red")
            return

        if df_mensual.empty:
            estado_vacio("Ainda não há movimentos registrados.", "Usá el formulario de abajo para cargar el primero.")
            return

        meses = sorted(df_mensual["mes"].unique(), key=lambda m: df_mensual.loc[df_mensual["mes"] == m, "mes_ord"].iloc[0])
        ing_vals = []
        egr_vals = []
        for m in meses:
            sub = df_mensual[df_mensual["mes"] == m]
            ing_row = sub[sub["tipo"] == "Receita"]
            egr_row = sub[sub["tipo"] == "Despesa"]
            ing_vals.append(float(ing_row["total"].iloc[0]) if not ing_row.empty else 0)
            egr_vals.append(float(egr_row["total"].iloc[0]) if not egr_row.empty else 0)

        with ui.row().classes("w-full gap-4 px-4 mb-4 mt-4"):
            with ui.card().classes("flex-1"):
                ui.label("📊 Ingresos vs Egresos — últimos 6 meses").classes("font-bold mb-1")
                ui.label("Verde = dinero que entró · Rojo = dinero que salió").classes("help-text mb-2")
                ui.echart({
                    "tooltip": {"trigger": "axis"},
                    "legend": {"data": ["Receitas", "Despesas"], "bottom": 0},
                    "grid": {"left": "8%", "right": "4%", "top": "6%", "bottom": "14%"},
                    "xAxis": {"type": "category", "data": list(meses)},
                    "yAxis": {"type": "value", "axisLabel": {"formatter": "${value}"}},
                    "series": [
                        {"name": "Receitas", "type": "bar", "data": ing_vals,
                         "itemStyle": {"color": "#16a34a"}, "barMaxWidth": 40},
                        {"name": "Despesas",  "type": "bar", "data": egr_vals,
                         "itemStyle": {"color": "#ef4444"}, "barMaxWidth": 40},
                    ],
                }).classes("w-full h-64")

            if not df_categ.empty:
                with ui.card().classes("flex-1"):
                    ui.label("🍩 Em que foi o dinheiro?").classes("font-bold mb-1")
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
                       SUM(CASE WHEN tipo='Receita' THEN monto ELSE -monto END)::float AS balance
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
        ui.label("Informe uma receita (dinheiro que entra) ou uma despesa (dinheiro que sai).").classes("help-text mb-3")
        aviso_requeridos()

        with ui.row().classes("w-full gap-4 mt-3 flex-wrap"):
            with ui.column().classes("gap-3 flex-1"):
                campo("¿Es un ingreso o un gasto?", "", required=True)
                tipo_mov = ui.select(["Receita", "Despesa"], value="Receita").classes("w-full")

                cat_label_el = ui.label("Categoría *").classes("text-sm font-semibold text-grey-8 mt-1")
                cat_help_el  = ui.label("Que tipo é este movimento?").classes("help-text")
                categoria    = ui.select(CATEGORIAS_INGRESO, value=CATEGORIAS_INGRESO[0]).classes("w-full")

                def actualizar_categorias() -> None:
                    if tipo_mov.value == "Receita":
                        categoria.options = CATEGORIAS_INGRESO
                        categoria.value   = CATEGORIAS_INGRESO[0]
                    else:
                        categoria.options = CATEGORIAS_EGRESO
                        categoria.value   = CATEGORIAS_EGRESO[0]
                    categoria.update()

                tipo_mov.on("update:model-value", lambda _: actualizar_categorias())

                campo("Valor (R$)", "Qual o valor? Somente o número, sem o sinal R$.", required=True)
                monto = ui.number(value=0.0, min=0, step=100, prefix="$").classes("w-full")

                campo("Data", "Quando ocorreu?", required=True)
                fecha_mov = ui.date(value=date.today().isoformat()).classes("w-full")

            with ui.column().classes("flex-1"):
                campo("Descrição", "Anote os detalhes para lembrar do que se tratou.")
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
                signo = "+" if tipo_mov.value == "Receita" else "-"
                notificar_ok(f"✓ {tipo_mov.value} de ${monto.value:,.0f} registrado correctamente ({signo}).")
                monto.value = 0.0; descripcion.value = ""
                kpis.refresh()
                graficos.refresh()
                tabla_hist.refresh()
            except Exception as exc:
                notificar_error(exc)

        ui.button("💾  Salvar Movimento", on_click=guardar_movimiento).classes(
            "mt-4 bg-blue-700 text-white font-bold px-8 py-3 text-base"
        )

    # ── Costos automáticos de otras secciones ────────────────────────────────
    with ui.card().classes("mx-4 mb-4"):
        ui.label("🔗 Costos registrados en otras secciones").classes("text-lg font-bold mb-1")
        ui.label(
            "Estos costos se generaron al registrar atenciones veterinarias y mantenimientos. "
            "Estão aqui como referência — se quiser incluí-los no balanço, cadastre-os manualmente acima."
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
                SELECT TO_CHAR(fecha,'DD/MM/YYYY') AS "Data",
                       tipo                         AS "Tipo",
                       categoria                    AS "Categoria",
                       descripcion                  AS "Descrição",
                       monto                        AS "Valor R$"
                FROM tabla_finanzas
                ORDER BY fecha DESC, finanza_id DESC
                LIMIT 100
            """)
            if df.empty:
                estado_vacio("Ainda não há movimentos registrados.", "Usá el formulario de arriba para agregar el primero.")
            else:
                df_to_table(df)
        except Exception as exc:
            ui.label("Error al cargar el historial.").classes("text-red")

    with ui.card().classes("mx-4 mb-4"):
        ui.label("📋 Historial de Movimientos").classes("text-lg font-bold mb-2")
        tabla_hist()


# ── EMPLEADOS ────────────────────────────────────────────────────────────────

@ui.page("/empleados")
def empleados_page() -> None:
    nav("/empleados")
    with ui.column().classes("px-4 pt-4 pb-1"):
        ui.label("👷 Funcionários").classes("text-2xl font-bold")
        ui.label("Cadastre seu pessoal, seus cargos e mantenha o histórico de pagamentos.").classes("text-sm text-grey-6")

    # ── KPIs ─────────────────────────────────────────────────────────────────
    @ui.refreshable
    def kpis_emp() -> None:
        try:
            activos = int(read_sql(
                "SELECT COUNT(*) FROM tabla_empleados WHERE estado='ativo'"
            ).iloc[0, 0])
            nomina = float(read_sql(
                "SELECT COALESCE(SUM(sueldo_base),0) FROM tabla_empleados WHERE estado='ativo'"
            ).iloc[0, 0])
            pagos_mes = float(read_sql("""
                SELECT COALESCE(SUM(monto),0) FROM tabla_pagos
                WHERE DATE_TRUNC('month',fecha)=DATE_TRUNC('month',CURRENT_DATE)
            """).iloc[0, 0])
        except Exception as exc:
            ui.label("Error al cargar métricas.").classes("text-red")
            return
        with ui.row().classes("w-full gap-4 px-4 mt-4 mb-2"):
            for titulo, valor, sub, color in [
                ("👷 Empleados activos", str(activos),            "en el establecimiento", "blue-800"),
                ("💵 Nómina mensual",    f"${nomina:,.0f}",       "sueldos base totales",  "green-700"),
                ("💸 Pagado este mes",   f"${pagos_mes:,.0f}",    "entre sueldos y bonos", "purple-700"),
            ]:
                with ui.card().classes("flex-1 p-6 text-center"):
                    ui.label(titulo).classes("text-xs text-grey-5 uppercase tracking-widest")
                    ui.label(valor).classes(f"text-4xl font-bold text-{color} mt-1")
                    ui.label(sub).classes("text-xs text-grey-5 mt-1")

    kpis_emp()

    # ── Tarjetas de empleados ─────────────────────────────────────────────────
    @ui.refreshable
    def tarjetas_empleados() -> None:
        try:
            df = read_sql("""
                SELECT empleado_id, nombre, cargo, sueldo_base,
                       COALESCE(telefono,'—') AS telefono,
                       TO_CHAR(fecha_ingreso,'DD/MM/YYYY') AS fecha_ingreso,
                       estado
                FROM tabla_empleados
                ORDER BY estado DESC, cargo, nombre
            """)
        except Exception as exc:
            ui.label("Erro ao carregar funcionários.").classes("text-red")
            return

        if df.empty:
            estado_vacio("Ainda não há funcionários cadastrados.",
                         "Use o formulário abaixo para adicionar o primeiro.")
            return

        with ui.grid(columns=3).classes("w-full gap-3 px-4 mb-2"):
            for _, r in df.iterrows():
                activo = r["estado"] == "activo"
                bg     = "bg-white" if activo else "bg-grey-2 opacity-70"
                with ui.card().classes(f"p-4 {bg}"):
                    with ui.row().classes("items-center justify-between w-full mb-2"):
                        ui.label("👷").style("font-size:1.6rem")
                        ui.badge("Activo" if activo else "Inactivo").props(
                            f"color={'green' if activo else 'grey'} rounded"
                        )
                    ui.label(r["nombre"]).classes("font-bold text-base text-blue-900")
                    ui.label(r["cargo"]).classes("text-sm text-grey-6 mb-2")
                    ui.separator()
                    with ui.column().classes("gap-1 mt-2"):
                        ui.label(f"💵  Sueldo base: ${float(r['sueldo_base']):,.0f}").classes("text-sm")
                        ui.label(f"📱  {r['telefono']}").classes("text-sm text-grey-7")
                        ui.label(f"📅  Ingresó: {r['fecha_ingreso']}").classes("text-xs text-grey-5")

    with ui.card().classes("mx-4 mb-4"):
        ui.label("Personal del Establecimiento").classes("text-lg font-bold mb-3")
        tarjetas_empleados()

    # ── Formulario nuevo empleado ─────────────────────────────────────────────
    with ui.card().classes("mx-4 mb-4"):
        ui.label("➕ Registrar un Empleado").classes("text-lg font-bold mb-1")
        ui.label("Preencha os dados do novo integrante da equipe.").classes("help-text mb-3")
        aviso_requeridos()

        with ui.row().classes("w-full gap-4 mt-3"):
            with ui.column().classes("flex-1 gap-3"):
                campo("Nome completo", "", required=True)
                nombre_emp = ui.input(placeholder="Ej: Juan Pérez").classes("w-full")

                campo("Cargo", "Qual função exerce na fazenda?", required=True)
                cargo_emp = ui.select(CARGOS_EMPLEADO, value=CARGOS_EMPLEADO[0]).classes("w-full")

                campo("Sueldo base mensual ($)", "Monto acordado por mes.")
                sueldo_emp = ui.number(value=0.0, min=0, step=1000, prefix="$").classes("w-full")

            with ui.column().classes("flex-1 gap-3"):
                campo("Teléfono de contacto", "Celular o teléfono fijo.")
                tel_emp = ui.input(placeholder="Ej: +54 9 11 1234-5678").classes("w-full")

                campo("Data de admissão", "¿Desde cuándo trabaja aquí?")
                fecha_ing_emp = ui.date(value=date.today().isoformat()).classes("w-full")

                campo("Estado", "")
                estado_emp = ui.select(["activo", "inactivo"], value="activo").classes("w-full")

        def guardar_empleado() -> None:
            if not nombre_emp.value.strip():
                notificar_aviso("O nome do funcionário é obrigatório.")
                return
            try:
                conn = conectar(); cur = conn.cursor()
                cur.execute("""
                    INSERT INTO tabla_empleados
                        (nombre, cargo, sueldo_base, telefono, fecha_ingreso, estado)
                    VALUES (%s,%s,%s,%s,%s,%s)
                """, (nombre_emp.value.strip(), cargo_emp.value,
                      sueldo_emp.value or 0, tel_emp.value or None,
                      fecha_ing_emp.value or date.today(), estado_emp.value))
                conn.commit(); cur.close(); conn.close()
                notificar_ok(f"✓ {nombre_emp.value} registrado como {cargo_emp.value}.")
                nombre_emp.value = ""; tel_emp.value = ""; sueldo_emp.value = 0.0
                kpis_emp.refresh()
                tarjetas_empleados.refresh()
                selector_empleado.refresh()
            except Exception as exc:
                notificar_error(exc)

        ui.button("💾  Guardar Empleado", on_click=guardar_empleado).classes(
            "mt-4 bg-blue-700 text-white font-bold px-8 py-3 text-base"
        )

    # ── Formulario pago ───────────────────────────────────────────────────────
    with ui.card().classes("mx-4 mb-4"):
        ui.label("💸 Registrar um Pagamento").classes("text-lg font-bold mb-1")
        ui.label("Registre salários, adiantamentos, bônus ou rescisões.").classes("help-text mb-3")
        aviso_requeridos()

        @ui.refreshable
        def selector_empleado() -> None:
            try:
                df_e = read_sql(
                    "SELECT nombre, sueldo_base FROM tabla_empleados WHERE estado='ativo' ORDER BY nombre"
                )
                opts = [ELEGIR] + list(df_e["nombre"])
            except Exception:
                opts = [ELEGIR]
            emp_sel.options = opts
            if emp_sel.value not in opts:
                emp_sel.value = opts[0]

        with ui.row().classes("w-full gap-4 mt-3"):
            with ui.column().classes("flex-1 gap-3"):
                campo("Qual funcionário?", "", required=True)
                emp_sel = ui.select([ELEGIR], value=ELEGIR).classes("w-full")
                selector_empleado()

                campo("Tipo de pagamento", "", required=True)
                tipo_pago = ui.select(TIPOS_PAGO_EMP, value=TIPOS_PAGO_EMP[0]).classes("w-full")

                campo("Valor (R$)", "", required=True)
                monto_pago = ui.number(value=0.0, min=0, step=500, prefix="$").classes("w-full")

                campo("Data do pagamento", "", required=True)
                fecha_pago = ui.date(value=date.today().isoformat()).classes("w-full")

            with ui.column().classes("flex-1"):
                campo("Descrição", "Ex: Salário maio 2026, Adiantamento quinzena, Prêmio produtividade…")
                desc_pago = ui.textarea(placeholder="Detalhe do pagamento…").classes("w-full h-44")

        def guardar_pago() -> None:
            if emp_sel.value == ELEGIR:
                notificar_aviso("Primeiro escolha o funcionário.")
                return
            if (monto_pago.value or 0) <= 0:
                notificar_aviso("O valor deve ser maior que 0.")
                return
            try:
                conn = conectar(); cur = conn.cursor()
                cur.execute("SELECT empleado_id FROM tabla_empleados WHERE nombre=%s", (emp_sel.value,))
                row = cur.fetchone(); emp_id = row[0] if row else None
                cur.execute(
                    "INSERT INTO tabla_pagos (empleado_id, fecha, tipo, monto, descripcion) VALUES (%s,%s,%s,%s,%s)",
                    (emp_id, fecha_pago.value, tipo_pago.value,
                     monto_pago.value, desc_pago.value or None),
                )
                conn.commit(); cur.close(); conn.close()
                notificar_ok(f"✓ {tipo_pago.value} de R${monto_pago.value:,.0f} registrado para {emp_sel.value}.")
                monto_pago.value = 0.0; desc_pago.value = ""
                kpis_emp.refresh()
                tabla_pagos.refresh()
            except Exception as exc:
                notificar_error(exc)

        ui.button("💾  Registrar Pagamento", on_click=guardar_pago).classes(
            "mt-4 bg-green-700 text-white font-bold px-8 py-3 text-base"
        )

    # ── Historial de pagos ────────────────────────────────────────────────────
    @ui.refreshable
    def tabla_pagos() -> None:
        try:
            df = read_sql("""
                SELECT e.nombre                          AS "Funcionário",
                       e.cargo                           AS "Cargo",
                       TO_CHAR(p.fecha,'DD/MM/YYYY')    AS "Data",
                       p.tipo                            AS "Tipo",
                       p.monto                          AS "Valor R$",
                       COALESCE(p.descripcion,'—')      AS "Descrição"
                FROM tabla_pagos p
                JOIN tabla_empleados e ON p.empleado_id=e.empleado_id
                ORDER BY p.fecha DESC, p.pago_id DESC
                LIMIT 100
            """)
            if df.empty:
                estado_vacio("Ainda não há pagamentos registrados.",
                             "Use o formulário acima para registrar o primeiro.")
            else:
                df_to_table(df)
        except Exception as exc:
            ui.label("Erro ao carregar pagamentos.").classes("text-red")

    with ui.card().classes("mx-4 mb-4"):
        ui.label("Histórico de Pagamentos").classes("text-lg font-bold mb-2")
        tabla_pagos()


# ── REPORTES ─────────────────────────────────────────────────────────────────

@ui.page("/reportes")
def reportes_page() -> None:
    nav("/reportes")
    with ui.column().classes("px-4 pt-4 pb-2"):
        ui.label("📊 Relatórios").classes("text-2xl font-bold")
        ui.label("Resumos e análises de todas as áreas da sua fazenda.").classes("text-sm text-grey-6")

    with ui.tabs().classes("w-full px-4 mt-2").props("dense") as tabs:
        t_leche  = ui.tab("🥛 Leite")
        t_salud  = ui.tab("💊 Saúde")
        t_reprod = ui.tab("🐣 Reprodução")
        t_fin    = ui.tab("💰 Finanças")
        t_emp    = ui.tab("👷 Funcionários")
        t_maq    = ui.tab("🚜 Maquinário")
        t_hist   = ui.tab("📈 Histórico")

    with ui.tab_panels(tabs, value=t_leche).classes("w-full"):

        # ── LECHE ─────────────────────────────────────────────────────────────
        with ui.tab_panel(t_leche):
            try:
                # Top 10 vacas
                df_top = read_sql("""
                    SELECT v.nombre,
                           ROUND(SUM(l.litros)::numeric,1)::float AS total,
                           ROUND(AVG(l.litros)::numeric,2)::float AS promedio
                    FROM tabla_leche l
                    JOIN tabla_vacas v ON l.vaca_id=v.vaca_id
                    GROUP BY v.nombre ORDER BY total DESC LIMIT 10
                """)
                # Producción por grupo
                df_grupo = read_sql("""
                    SELECT COALESCE(v.grupo,'(sin grupo)') AS grupo,
                           ROUND(SUM(l.litros)::numeric,0)::float AS total,
                           COUNT(DISTINCT l.vaca_id)::int AS vacas
                    FROM tabla_leche l
                    JOIN tabla_vacas v ON l.vaca_id=v.vaca_id
                    GROUP BY v.grupo ORDER BY total DESC
                """)
                # Resumen mensual
                df_mensual = read_sql("""
                    SELECT TO_CHAR(DATE_TRUNC('month',fecha_hora),'MM/YYYY') AS mes,
                           DATE_TRUNC('month',fecha_hora) AS mes_ord,
                           ROUND(SUM(litros)::numeric,0)::float AS litros,
                           COUNT(DISTINCT vaca_id)::int AS vacas
                    FROM tabla_leche
                    GROUP BY DATE_TRUNC('month',fecha_hora)
                    ORDER BY mes_ord
                """)
                err_leche = None
            except Exception as exc:
                err_leche = str(exc)

            if err_leche:
                ui.label(f"Error: {err_leche}").classes("text-red m-4")
            else:
                with ui.row().classes("w-full gap-4 px-2 mt-3"):
                    with ui.card().classes("flex-1"):
                        ui.label("Produção por grupo").classes("font-bold mb-1")
                        ui.label("Litros totais acumulados por grupo de alimentação.").classes("help-text mb-2")
                        if not df_grupo.empty:
                            ui.echart({
                                "tooltip": {"trigger": "axis"},
                                "xAxis": {"type": "category", "data": list(df_grupo["grupo"]),
                                          "axisLabel": {"rotate": 20, "fontSize": 11}},
                                "yAxis": {"type": "value"},
                                "series": [{"type": "bar", "data": list(df_grupo["total"]),
                                            "itemStyle": {"color": "#16a34a"}, "barMaxWidth": 50}],
                            }).classes("w-full h-56")
                    with ui.card().classes("flex-none w-64 flex flex-col justify-center items-center p-6 bg-blue-50"):
                        ui.icon("show_chart", size="xl").classes("text-blue-400 mb-2")
                        ui.label("Histórico diário completo").classes("font-bold text-blue-700 text-center")
                        ui.label("Gráfico com zoom e slider de datas disponível no tab Histórico.").classes("text-xs text-grey-6 text-center mt-1")
                        ui.link("Ver Histórico →", "#").on("click", lambda: None).classes("text-sm text-blue-500 mt-3 font-medium")

                with ui.row().classes("w-full gap-4 px-2 mt-2"):
                    with ui.card().classes("flex-1"):
                        ui.label("🏆 Top 10 vacas mais produtivas").classes("font-bold mb-2")
                        if not df_top.empty:
                            df_top.columns = ["Vaca", "Total Litros", "Promedio por ordeñe"]
                            df_to_table(df_top, pagination=10)

                    with ui.card().classes("flex-1"):
                        ui.label("📅 Resumo mensal").classes("font-bold mb-2")
                        if not df_mensual.empty:
                            df_mensual_tabla = df_mensual[["mes","litros","vacas"]].copy()
                            df_mensual_tabla.columns = ["Mes", "Litros totales", "Vacas registradas"]
                            df_to_table(df_mensual_tabla, pagination=12)

        # ── SALUD ─────────────────────────────────────────────────────────────
        with ui.tab_panel(t_salud):
            try:
                df_tipos = read_sql("""
                    SELECT tipo_evento, COUNT(*)::int AS cantidad,
                           ROUND(SUM(costo)::numeric,0)::float AS costo_total
                    FROM tabla_salud GROUP BY tipo_evento ORDER BY cantidad DESC
                """)
                df_mensual_s = read_sql("""
                    SELECT TO_CHAR(DATE_TRUNC('month',fecha),'MM/YYYY') AS mes,
                           DATE_TRUNC('month',fecha) AS mes_ord,
                           COUNT(*)::int AS atenciones,
                           ROUND(SUM(costo)::numeric,0)::float AS costo
                    FROM tabla_salud
                    GROUP BY DATE_TRUNC('month',fecha) ORDER BY mes_ord
                """)
                df_vacas_s = read_sql("""
                    SELECT v.nombre, COUNT(*)::int AS atenciones,
                           ROUND(SUM(s.costo)::numeric,0)::float AS costo_total,
                           STRING_AGG(DISTINCT s.tipo_evento, ', ' ORDER BY s.tipo_evento) AS tipos
                    FROM tabla_salud s
                    JOIN tabla_vacas v ON s.vaca_id=v.vaca_id
                    GROUP BY v.nombre ORDER BY atenciones DESC LIMIT 10
                """)
                err_salud = None
            except Exception as exc:
                err_salud = str(exc)

            if err_salud:
                ui.label(f"Error: {err_salud}").classes("text-red m-4")
            else:
                with ui.row().classes("w-full gap-4 px-2 mt-3"):
                    with ui.card().classes("flex-1"):
                        ui.label("Atenciones por tipo").classes("font-bold mb-1")
                        ui.label("Cuántas veces ocurrió cada tipo de atención.").classes("help-text mb-2")
                        if not df_tipos.empty:
                            ui.echart({
                                "tooltip": {"trigger": "item", "formatter": "{b}: {c} ({d}%)"},
                                "legend": {"bottom": 0, "type": "scroll"},
                                "series": [{
                                    "type": "pie", "radius": ["38%", "66%"],
                                    "center": ["50%", "42%"],
                                    "itemStyle": {"borderRadius": 6, "borderColor": "#fff", "borderWidth": 2},
                                    "label": {"show": False},
                                    "emphasis": {"label": {"show": True, "fontSize": 13, "fontWeight": "bold"}},
                                    "data": [{"value": int(r["cantidad"]), "name": r["tipo_evento"]}
                                             for _, r in df_tipos.iterrows()],
                                }],
                            }).classes("w-full h-60")

                    with ui.card().classes("flex-1"):
                        ui.label("Atenciones y costos por mes").classes("font-bold mb-1")
                        ui.label("Evolución mensual de la cantidad de intervenciones.").classes("help-text mb-2")
                        if not df_mensual_s.empty:
                            ui.echart({
                                "tooltip": {"trigger": "axis"},
                                "legend": {"data": ["Atenciones", "Costo $"], "bottom": 0},
                                "xAxis": {"type": "category", "data": list(df_mensual_s["mes"]),
                                          "axisLabel": {"rotate": 20, "fontSize": 11}},
                                "yAxis": [
                                    {"type": "value", "name": "Atenciones"},
                                    {"type": "value", "name": "Costo $", "position": "right"},
                                ],
                                "series": [
                                    {"name": "Atenciones", "type": "bar", "data": list(df_mensual_s["atenciones"]),
                                     "itemStyle": {"color": "#6366f1"}, "barMaxWidth": 40},
                                    {"name": "Costo $", "type": "line", "yAxisIndex": 1,
                                     "data": list(df_mensual_s["costo"]),
                                     "itemStyle": {"color": "#ef4444"}, "smooth": True},
                                ],
                            }).classes("w-full h-60")

                with ui.card().classes("mx-2 mt-2"):
                    ui.label("🏥 Top 10 animais com mais atendimentos").classes("font-bold mb-2")
                    if not df_vacas_s.empty:
                        df_vacas_s.columns = ["Animal", "Atenciones", "Costo Total $", "Tipos de atención"]
                        df_to_table(df_vacas_s, pagination=10)

        # ── REPRODUCCIÓN ──────────────────────────────────────────────────────
        with ui.tab_panel(t_reprod):
            try:
                df_mensual_r = read_sql("""
                    SELECT TO_CHAR(DATE_TRUNC('month',fecha_evento),'MM/YYYY') AS mes,
                           DATE_TRUNC('month',fecha_evento) AS mes_ord,
                           tipo_evento,
                           COUNT(*)::int AS cantidad
                    FROM tabla_reproduccion
                    GROUP BY DATE_TRUNC('month',fecha_evento), tipo_evento
                    ORDER BY mes_ord, tipo_evento
                """)
                df_resultados = read_sql("""
                    SELECT resultado_parto, COUNT(*)::int AS cantidad
                    FROM tabla_reproduccion
                    WHERE tipo_evento='Parto' AND resultado_parto IS NOT NULL
                    GROUP BY resultado_parto ORDER BY cantidad DESC
                """)
                df_tipo_fert = read_sql("""
                    SELECT tipo_fertilizacion, COUNT(*)::int AS cantidad
                    FROM tabla_reproduccion
                    WHERE tipo_evento='Fertilização'
                    GROUP BY tipo_fertilizacion
                """)
                df_prox = read_sql("""
                    SELECT v.nombre,
                           TO_CHAR(r.fecha_evento,'DD/MM/YYYY')       AS fertilizacion,
                           TO_CHAR(r.fecha_parto_esperado,'DD/MM/YYYY') AS parto_esperado,
                           (r.fecha_parto_esperado-CURRENT_DATE)::int  AS dias_restantes
                    FROM tabla_reproduccion r
                    JOIN tabla_vacas v ON r.vaca_id=v.vaca_id
                    WHERE r.tipo_evento='Fertilização'
                      AND r.fecha_parto_esperado >= CURRENT_DATE
                    ORDER BY r.fecha_parto_esperado LIMIT 15
                """)
                err_reprod = None
            except Exception as exc:
                err_reprod = str(exc)

            if err_reprod:
                ui.label(f"Error: {err_reprod}").classes("text-red m-4")
            else:
                # Meses únicos ordenados
                if not df_mensual_r.empty:
                    meses_r = sorted(df_mensual_r["mes"].unique(),
                                     key=lambda m: df_mensual_r.loc[df_mensual_r["mes"]==m,"mes_ord"].iloc[0])
                    fert_v = []
                    parto_v = []
                    for m in meses_r:
                        sub = df_mensual_r[df_mensual_r["mes"]==m]
                        fr = sub[sub["tipo_evento"]=="Fertilização"]
                        pr = sub[sub["tipo_evento"]=="Parto"]
                        fert_v.append(int(fr["cantidad"].iloc[0]) if not fr.empty else 0)
                        parto_v.append(int(pr["cantidad"].iloc[0]) if not pr.empty else 0)

                with ui.row().classes("w-full gap-4 px-2 mt-3"):
                    with ui.card().classes("flex-1"):
                        ui.label("Fertilizações e partos por mês").classes("font-bold mb-1")
                        ui.label("Comparativa mensual de los dos eventos reproductivos principales.").classes("help-text mb-2")
                        if not df_mensual_r.empty:
                            ui.echart({
                                "tooltip": {"trigger": "axis"},
                                "legend": {"data": ["Fertilizaciones","Partos"], "bottom": 0},
                                "xAxis": {"type": "category", "data": meses_r,
                                          "axisLabel": {"rotate": 20, "fontSize": 11}},
                                "yAxis": {"type": "value"},
                                "series": [
                                    {"name": "Fertilizaciones", "type": "bar", "data": fert_v,
                                     "itemStyle": {"color": "#3b82f6"}, "barMaxWidth": 35},
                                    {"name": "Partos",          "type": "bar", "data": parto_v,
                                     "itemStyle": {"color": "#16a34a"}, "barMaxWidth": 35},
                                ],
                            }).classes("w-full h-56")

                    with ui.row().classes("flex-1 gap-4"):
                        with ui.card().classes("flex-1"):
                            ui.label("Resultados de partos").classes("font-bold mb-1")
                            ui.label("Distribución de los tipos de resultado.").classes("help-text mb-2")
                            if not df_resultados.empty:
                                colores = {"Bem-sucedido": "#16a34a","Gemelar": "#3b82f6",
                                           "Aborto": "#f59e0b","Cria morta": "#ef4444"}
                                ui.echart({
                                    "tooltip": {"trigger": "item", "formatter": "{b}: {c} ({d}%)"},
                                    "series": [{
                                        "type": "pie", "radius": "68%",
                                        "label": {"formatter": "{b}\n{c}"},
                                        "data": [{"value": int(r["cantidad"]), "name": r["resultado_parto"],
                                                  "itemStyle": {"color": colores.get(r["resultado_parto"],"#94a3b8")}}
                                                 for _, r in df_resultados.iterrows()],
                                    }],
                                }).classes("w-full h-56")

                        with ui.card().classes("flex-1"):
                            ui.label("Tipo de fertilização").classes("font-bold mb-2")
                            if not df_tipo_fert.empty:
                                ui.echart({
                                    "tooltip": {"trigger": "item", "formatter": "{b}: {c} ({d}%)"},
                                    "series": [{
                                        "type": "pie", "radius": "68%",
                                        "label": {"formatter": "{b}\n{c}"},
                                        "data": [{"value": int(r["cantidad"]), "name": r["tipo_fertilizacion"]}
                                                 for _, r in df_tipo_fert.iterrows()],
                                    }],
                                }).classes("w-full h-56")

                with ui.card().classes("mx-2 mt-2"):
                    ui.label("📅 Próximos partos esperados").classes("font-bold mb-2")
                    if not df_prox.empty:
                        df_prox.columns = ["Animal","Fertilização","Parto Esperado","Días restantes"]
                        df_to_table(df_prox, pagination=15)
                    else:
                        estado_vacio("No hay partos esperados próximamente.")

        # ── FINANZAS ──────────────────────────────────────────────────────────
        with ui.tab_panel(t_fin):
            try:
                df_ing_categ = read_sql("""
                    SELECT categoria, SUM(monto)::float AS total
                    FROM tabla_finanzas WHERE tipo='Receita'
                    GROUP BY categoria ORDER BY total DESC
                """)
                df_resumen_f = read_sql("""
                    SELECT TO_CHAR(DATE_TRUNC('month',fecha),'MM/YYYY') AS mes,
                           DATE_TRUNC('month',fecha) AS mes_ord,
                           SUM(CASE WHEN tipo='Receita' THEN monto ELSE 0 END)::float AS ingresos,
                           SUM(CASE WHEN tipo='Despesa'  THEN monto ELSE 0 END)::float AS egresos,
                           SUM(CASE WHEN tipo='Receita' THEN monto ELSE -monto END)::float AS balance
                    FROM tabla_finanzas
                    GROUP BY DATE_TRUNC('month',fecha) ORDER BY mes_ord
                """)
                err_fin = None
            except Exception as exc:
                err_fin = str(exc)

            if err_fin:
                ui.label(f"Error: {err_fin}").classes("text-red m-4")
            else:
                with ui.row().classes("w-full px-2 mt-3 mb-1"):
                    with ui.card().classes("w-full flex flex-row items-center gap-4 p-4 bg-amber-50"):
                        ui.icon("bar_chart", size="md").classes("text-amber-500")
                        with ui.column().classes("gap-0"):
                            ui.label("Gráficos de receitas e despesas disponíveis em Finanças").classes("font-medium text-amber-800")
                            ui.label("Barras mensais e distribuição por categoria estão na página principal de Finanças para evitar duplicação.").classes("text-xs text-grey-6")
                        ui.space()
                        ui.link("Ir para Finanças →", "/finanzas").classes("text-sm text-blue-500 font-medium whitespace-nowrap")

                with ui.row().classes("w-full gap-4 px-2 mt-2"):
                    with ui.card().classes("flex-1"):
                        ui.label("De dónde vino el dinero").classes("font-bold mb-2")
                        if not df_ing_categ.empty:
                            df_ing_categ.columns = ["Categoria", "Total $"]
                            df_to_table(df_ing_categ, pagination=10)

                    with ui.card().classes("flex-1"):
                        ui.label("Resumen financiero mensual").classes("font-bold mb-2")
                        if not df_resumen_f.empty:
                            df_r = df_resumen_f[["mes","ingresos","egresos","balance"]].copy()
                            df_r.columns = ["Mes","Ingresos $","Egresos $","Balance $"]
                            df_to_table(df_r, pagination=12)

        # ── EMPLEADOS ─────────────────────────────────────────────────────────
        with ui.tab_panel(t_emp):
            try:
                df_pagos_emp = read_sql("""
                    SELECT e.nombre,
                           e.cargo,
                           e.sueldo_base::float AS sueldo_base,
                           SUM(p.monto)::float  AS total_pagado,
                           COUNT(p.pago_id)::int AS cantidad_pagos
                    FROM tabla_empleados e
                    LEFT JOIN tabla_pagos p ON e.empleado_id=p.empleado_id
                    GROUP BY e.empleado_id, e.nombre, e.cargo, e.sueldo_base
                    ORDER BY total_pagado DESC NULLS LAST
                """)
                df_tipo_pago = read_sql("""
                    SELECT tipo, COUNT(*)::int AS cantidad,
                           SUM(monto)::float AS total
                    FROM tabla_pagos GROUP BY tipo ORDER BY total DESC
                """)
                df_nomina_mes = read_sql("""
                    SELECT TO_CHAR(DATE_TRUNC('month',fecha),'MM/YYYY') AS mes,
                           DATE_TRUNC('month',fecha) AS mes_ord,
                           SUM(monto)::float AS total,
                           COUNT(DISTINCT empleado_id)::int AS empleados
                    FROM tabla_pagos
                    GROUP BY DATE_TRUNC('month',fecha) ORDER BY mes_ord
                """)
                err_emp = None
            except Exception as exc:
                err_emp = str(exc)

            if err_emp:
                ui.label(f"Error: {err_emp}").classes("text-red m-4")
            else:
                with ui.row().classes("w-full gap-4 px-2 mt-3"):
                    with ui.card().classes("flex-1"):
                        ui.label("Nómina pagada por mes").classes("font-bold mb-1")
                        ui.label("Total abonado al personal cada mes.").classes("help-text mb-2")
                        if not df_nomina_mes.empty:
                            ui.echart({
                                "tooltip": {"trigger": "axis", "formatter": "{b}: ${c}"},
                                "xAxis": {"type": "category", "data": list(df_nomina_mes["mes"]),
                                          "axisLabel": {"rotate": 20}},
                                "yAxis": {"type": "value", "axisLabel": {"formatter": "${value}"}},
                                "series": [{"type": "bar", "data": list(df_nomina_mes["total"]),
                                            "itemStyle": {"color": "#8b5cf6"}, "barMaxWidth": 50}],
                            }).classes("w-full h-56")

                    with ui.card().classes("flex-1"):
                        ui.label("Pagos por tipo").classes("font-bold mb-1")
                        ui.label("Distribución entre sueldos, adelantos y bonos.").classes("help-text mb-2")
                        if not df_tipo_pago.empty:
                            colores_p = {"Salário": "#8b5cf6","Adiantamento": "#f59e0b",
                                         "Bônus": "#16a34a","Rescisão": "#ef4444"}
                            ui.echart({
                                "tooltip": {"trigger": "item", "formatter": "{b}: ${c} ({d}%)"},
                                "legend": {"bottom": 0},
                                "series": [{
                                    "type": "pie", "radius": ["38%","66%"],
                                    "center": ["50%","42%"],
                                    "itemStyle": {"borderRadius": 6, "borderColor": "#fff", "borderWidth": 2},
                                    "label": {"show": False},
                                    "emphasis": {"label": {"show": True, "fontSize": 12}},
                                    "data": [{"value": float(r["total"]), "name": r["tipo"],
                                              "itemStyle": {"color": colores_p.get(r["tipo"],"#94a3b8")}}
                                             for _, r in df_tipo_pago.iterrows()],
                                }],
                            }).classes("w-full h-56")

                with ui.card().classes("mx-2 mt-2"):
                    ui.label("Total pagado por empleado").classes("font-bold mb-2")
                    if not df_pagos_emp.empty:
                        df_pagos_emp.columns = ["Empleado","Cargo","Sueldo Base $","Total Pagado $","Pagos"]
                        df_to_table(df_pagos_emp)

        # ── MAQUINARIA ────────────────────────────────────────────────────────
        with ui.tab_panel(t_maq):
            try:
                df_costo_maq = read_sql("""
                    SELECT m.nombre,
                           m.tipo,
                           COUNT(t.manten_id)::int AS mantenimientos,
                           ROUND(SUM(t.costo)::numeric,0)::float AS costo_total,
                           TO_CHAR(MAX(t.fecha),'DD/MM/YYYY') AS ultimo_mant,
                           TO_CHAR(MAX(t.proximo_mantenimiento),'DD/MM/YYYY') AS proximo_mant
                    FROM tabla_maquinaria m
                    LEFT JOIN tabla_mantenimiento t ON m.maquina_id=t.maquina_id
                    GROUP BY m.maquina_id, m.nombre, m.tipo
                    ORDER BY costo_total DESC NULLS LAST
                """)
                df_tipo_mant = read_sql("""
                    SELECT tipo_mantencion, COUNT(*)::int AS cantidad,
                           ROUND(SUM(costo)::numeric,0)::float AS costo_total
                    FROM tabla_mantenimiento
                    GROUP BY tipo_mantencion ORDER BY costo_total DESC
                """)
                df_mant_mes = read_sql("""
                    SELECT TO_CHAR(DATE_TRUNC('month',fecha),'MM/YYYY') AS mes,
                           DATE_TRUNC('month',fecha) AS mes_ord,
                           COUNT(*)::int AS cantidad,
                           ROUND(SUM(costo)::numeric,0)::float AS costo
                    FROM tabla_mantenimiento
                    GROUP BY DATE_TRUNC('month',fecha) ORDER BY mes_ord
                """)
                err_maq = None
            except Exception as exc:
                err_maq = str(exc)

            if err_maq:
                ui.label(f"Error: {err_maq}").classes("text-red m-4")
            else:
                with ui.row().classes("w-full gap-4 px-2 mt-3"):
                    with ui.card().classes("flex-1"):
                        ui.label("Custo de manutenção por máquina").classes("font-bold mb-1")
                        ui.label("Total gasto em manutenções para cada equipamento.").classes("help-text mb-2")
                        if not df_costo_maq.empty:
                            df_c = df_costo_maq.dropna(subset=["costo_total"])
                            df_c = df_c[df_c["costo_total"] > 0].sort_values("costo_total")
                            if not df_c.empty:
                                h = max(220, len(df_c) * 44)
                                ui.echart({
                                    "tooltip": {"trigger": "axis", "formatter": "{b}: ${c}"},
                                    "grid": {"left": "24%","right": "12%","top": "3%","bottom": "3%"},
                                    "xAxis": {"type": "value", "axisLabel": {"formatter": "${value}"}},
                                    "yAxis": {"type": "category", "data": list(df_c["nombre"]),
                                              "axisLabel": {"fontSize": 12}},
                                    "series": [{"type": "bar", "barMaxWidth": 32,
                                                "data": list(df_c["costo_total"]),
                                                "itemStyle": {"color": "#f59e0b"},
                                                "label": {"show": True, "position": "right",
                                                          "formatter": "${c}", "fontSize": 11}}],
                                }).classes("w-full").style(f"height:{h}px;min-height:220px")

                    with ui.card().classes("flex-1"):
                        ui.label("Mantenimientos por tipo").classes("font-bold mb-1")
                        ui.label("Qual tipo de manutenção é realizado com mais frequência.").classes("help-text mb-2")
                        if not df_tipo_mant.empty:
                            ui.echart({
                                "tooltip": {"trigger": "item", "formatter": "{b}: {c} ({d}%)"},
                                "legend": {"bottom": 0, "type": "scroll"},
                                "series": [{
                                    "type": "pie", "radius": ["38%","66%"],
                                    "center": ["50%","42%"],
                                    "itemStyle": {"borderRadius": 6, "borderColor": "#fff", "borderWidth": 2},
                                    "label": {"show": False},
                                    "emphasis": {"label": {"show": True, "fontSize": 12}},
                                    "data": [{"value": int(r["cantidad"]), "name": r["tipo_mantencion"]}
                                             for _, r in df_tipo_mant.iterrows()],
                                }],
                            }).classes("w-full h-56")

                with ui.row().classes("w-full gap-4 px-2 mt-2"):
                    with ui.card().classes("flex-1"):
                        ui.label("Histórico por máquina").classes("font-bold mb-2")
                        if not df_costo_maq.empty:
                            df_costo_maq.columns = ["Máquina","Tipo","Mantenimientos",
                                                    "Costo Total $","Último Mant.","Próximo Mant."]
                            df_to_table(df_costo_maq)

                    with ui.card().classes("flex-1"):
                        ui.label("Manutenções por mês").classes("font-bold mb-2")
                        if not df_mant_mes.empty:
                            df_mant_mes_t = df_mant_mes[["mes","cantidad","costo"]].copy()
                            df_mant_mes_t.columns = ["Mes","Cantidad","Costo Total $"]
                            df_to_table(df_mant_mes_t, pagination=12)

        # ── HISTÓRICO DE PRODUCCIÓN ───────────────────────────────────────────
        with ui.tab_panel(t_hist):
            try:
                df_hist_mes = read_sql("""
                    SELECT TO_CHAR(DATE_TRUNC('month',fecha),'MM/YYYY')     AS mes,
                           DATE_TRUNC('month',fecha)                        AS mes_ord,
                           ROUND(SUM(total_litros)::numeric,0)::float       AS total,
                           ROUND(AVG(total_litros)::numeric,1)::float       AS media_diaria,
                           ROUND(AVG(media_litros_vaca)::numeric,2)::float  AS media_vaca,
                           ROUND(SUM(ordenha_1)::numeric,0)::float          AS ord1,
                           ROUND(SUM(ordenha_2)::numeric,0)::float          AS ord2,
                           ROUND(SUM(ordenha_3)::numeric,0)::float          AS ord3,
                           COUNT(*)::int                                     AS dias
                    FROM tabla_produccion_historica
                    GROUP BY DATE_TRUNC('month',fecha)
                    ORDER BY mes_ord
                """)
                df_hist_diaria = read_sql("""
                    SELECT TO_CHAR(fecha,'DD/MM/YY')           AS dia,
                           fecha                               AS dia_ord,
                           total_litros::float                 AS total,
                           COALESCE(media_litros_vaca,0)::float AS media_vaca
                    FROM tabla_produccion_historica
                    ORDER BY dia_ord
                """)
                df_yoy_leite = read_sql("""
                    SELECT
                        EXTRACT(month FROM fecha)::int AS mes_num,
                        TO_CHAR(TO_DATE(EXTRACT(month FROM fecha)::text,'MM'),'Mon') AS mes_nome,
                        ROUND(SUM(CASE WHEN EXTRACT(year FROM fecha) = EXTRACT(year FROM CURRENT_DATE)
                                       THEN total_litros ELSE 0 END)::numeric,0)::float AS atual,
                        ROUND(SUM(CASE WHEN EXTRACT(year FROM fecha) = EXTRACT(year FROM CURRENT_DATE)-1
                                       THEN total_litros ELSE 0 END)::numeric,0)::float AS anterior
                    FROM tabla_produccion_historica
                    WHERE EXTRACT(year FROM fecha) IN (
                        EXTRACT(year FROM CURRENT_DATE), EXTRACT(year FROM CURRENT_DATE)-1)
                    GROUP BY mes_num, mes_nome
                    ORDER BY mes_num
                """)
                df_yoy_fin = read_sql("""
                    SELECT
                        EXTRACT(month FROM fecha)::int AS mes_num,
                        TO_CHAR(TO_DATE(EXTRACT(month FROM fecha)::text,'MM'),'Mon') AS mes_nome,
                        ROUND(SUM(CASE WHEN tipo='Receita' AND EXTRACT(year FROM fecha)=EXTRACT(year FROM CURRENT_DATE)
                                       THEN monto ELSE 0 END)::numeric,0)::float AS rec_atual,
                        ROUND(SUM(CASE WHEN tipo='Receita' AND EXTRACT(year FROM fecha)=EXTRACT(year FROM CURRENT_DATE)-1
                                       THEN monto ELSE 0 END)::numeric,0)::float AS rec_anterior,
                        ROUND(SUM(CASE WHEN tipo='Despesa' AND EXTRACT(year FROM fecha)=EXTRACT(year FROM CURRENT_DATE)
                                       THEN monto ELSE 0 END)::numeric,0)::float AS desp_atual,
                        ROUND(SUM(CASE WHEN tipo='Despesa' AND EXTRACT(year FROM fecha)=EXTRACT(year FROM CURRENT_DATE)-1
                                       THEN monto ELSE 0 END)::numeric,0)::float AS desp_anterior
                    FROM tabla_finanzas
                    WHERE EXTRACT(year FROM fecha) IN (
                        EXTRACT(year FROM CURRENT_DATE), EXTRACT(year FROM CURRENT_DATE)-1)
                    GROUP BY mes_num, mes_nome
                    ORDER BY mes_num
                """)
                df_yoy_diesel = read_sql("""
                    SELECT
                        EXTRACT(month FROM fecha)::int AS mes_num,
                        TO_CHAR(TO_DATE(EXTRACT(month FROM fecha)::text,'MM'),'Mon') AS mes_nome,
                        ROUND(SUM(CASE WHEN EXTRACT(year FROM fecha) = EXTRACT(year FROM CURRENT_DATE)
                                       THEN consumo_litros ELSE 0 END)::numeric,1)::float AS consumo_atual,
                        ROUND(SUM(CASE WHEN EXTRACT(year FROM fecha) = EXTRACT(year FROM CURRENT_DATE)-1
                                       THEN consumo_litros ELSE 0 END)::numeric,1)::float AS consumo_anterior,
                        ROUND(SUM(CASE WHEN EXTRACT(year FROM fecha) = EXTRACT(year FROM CURRENT_DATE)
                                       THEN COALESCE(total_rs,0) ELSE 0 END)::numeric,0)::float AS custo_atual,
                        ROUND(SUM(CASE WHEN EXTRACT(year FROM fecha) = EXTRACT(year FROM CURRENT_DATE)-1
                                       THEN COALESCE(total_rs,0) ELSE 0 END)::numeric,0)::float AS custo_anterior
                    FROM tabla_diesel
                    WHERE EXTRACT(year FROM fecha) IN (
                        EXTRACT(year FROM CURRENT_DATE), EXTRACT(year FROM CURRENT_DATE)-1)
                    GROUP BY mes_num, mes_nome
                    ORDER BY mes_num
                """)
                err_hist = None
            except Exception as exc:
                err_hist = str(exc)

            if err_hist:
                ui.label(f"Error: {err_hist}").classes("text-red m-4")
            else:
                # ── KPIs ──────────────────────────────────────────────────────
                total_periodo = int(df_hist_mes["total"].sum()) if not df_hist_mes.empty else 0
                media_dia     = round(float(df_hist_diaria["total"].mean()), 1) if not df_hist_diaria.empty else 0
                mejor_mes_row = df_hist_mes.loc[df_hist_mes["total"].idxmax()] if not df_hist_mes.empty else None
                mejor_mes_txt = f"{mejor_mes_row['mes']} ({int(mejor_mes_row['total']):,} L)" if mejor_mes_row is not None else "—"
                n_meses = len(df_hist_mes)

                with ui.row().classes("gap-4 px-2 mt-3 flex-wrap"):
                    for titulo, valor, icono in [
                        ("Total do período",   f"{total_periodo:,} L",  "🥛"),
                        ("Média diária",        f"{media_dia:,} L/dia",  "📅"),
                        ("Melhor mês",          mejor_mes_txt,           "🏆"),
                        ("Meses registrados",  str(n_meses),             "📆"),
                    ]:
                        with ui.card().classes("flex-1 min-w-36 p-4 text-center"):
                            ui.label(f"{icono} {titulo}").classes("text-xs text-grey-5 uppercase tracking-widest mb-1")
                            ui.label(valor).classes("text-xl font-bold text-blue-700")

                # ── Gráfico 1: producción total por mes ───────────────────────
                with ui.row().classes("w-full gap-4 px-2 mt-3"):
                    with ui.card().classes("flex-1"):
                        ui.label("Produção total por mês").classes("font-bold mb-1")
                        ui.label("Litros totais ordenhados em cada mês do histórico.").classes("help-text mb-2")
                        if not df_hist_mes.empty:
                            ui.echart({
                                "tooltip": {"trigger": "axis", "formatter": "{b}: {c} L"},
                                "xAxis": {"type": "category", "data": list(df_hist_mes["mes"]),
                                          "axisLabel": {"rotate": 35, "fontSize": 10}},
                                "yAxis": {"type": "value", "name": "Litros"},
                                "series": [{
                                    "type": "bar", "data": list(df_hist_mes["total"]),
                                    "itemStyle": {"color": "#0ea5e9"},
                                    "barMaxWidth": 40,
                                    "label": {"show": True, "position": "top",
                                              "formatter": "{c}", "fontSize": 9},
                                }],
                            }).classes("w-full h-64")

                    with ui.card().classes("flex-1"):
                        ui.label("Sessões de ordenha por mês (O1 + O2 + O3)").classes("font-bold mb-1")
                        ui.label("Composição da produção por cada turno de ordenha.").classes("help-text mb-2")
                        if not df_hist_mes.empty:
                            colors = ["#3b82f6", "#22c55e", "#f59e0b"]
                            series = []
                            for col, name, color in [("ord1","Ordenha 1",colors[0]),
                                                      ("ord2","Ordenha 2",colors[1]),
                                                      ("ord3","Ordenha 3",colors[2])]:
                                vals = df_hist_mes[col].fillna(0).tolist()
                                series.append({"type": "bar", "name": name, "stack": "total",
                                               "data": vals, "itemStyle": {"color": color}})
                            ui.echart({
                                "tooltip": {"trigger": "axis", "axisPointer": {"type": "shadow"}},
                                "legend": {"bottom": 0},
                                "xAxis": {"type": "category", "data": list(df_hist_mes["mes"]),
                                          "axisLabel": {"rotate": 35, "fontSize": 10}},
                                "yAxis": {"type": "value", "name": "Litros"},
                                "series": series,
                            }).classes("w-full h-64")

                # ── Gráfico 2: media diaria + L/vaca ──────────────────────────
                with ui.row().classes("w-full gap-4 px-2 mt-2"):
                    with ui.card().classes("flex-1"):
                        ui.label("Média diária e L/Vaca por mês").classes("font-bold mb-1")
                        ui.label("Evolução da eficiência produtiva ao longo do tempo.").classes("help-text mb-2")
                        if not df_hist_mes.empty:
                            media_vaca_vals = [v if v and v > 0 else None
                                               for v in df_hist_mes["media_vaca"].tolist()]
                            ui.echart({
                                "tooltip": {"trigger": "axis"},
                                "legend": {"bottom": 0},
                                "xAxis": {"type": "category", "data": list(df_hist_mes["mes"]),
                                          "axisLabel": {"rotate": 35, "fontSize": 10}},
                                "yAxis": [
                                    {"type": "value", "name": "L/dia", "position": "left"},
                                    {"type": "value", "name": "L/vaca", "position": "right"},
                                ],
                                "series": [
                                    {"type": "line", "name": "Media diária (L)",
                                     "data": list(df_hist_mes["media_diaria"]),
                                     "smooth": True, "yAxisIndex": 0,
                                     "itemStyle": {"color": "#0ea5e9"}},
                                    {"type": "line", "name": "L/Vaca",
                                     "data": media_vaca_vals,
                                     "smooth": True, "yAxisIndex": 1,
                                     "itemStyle": {"color": "#f59e0b"},
                                     "lineStyle": {"type": "dashed"}},
                                ],
                            }).classes("w-full h-64")

                    with ui.card().classes("flex-1"):
                        ui.label("Produção diária — histórico completo").classes("font-bold mb-1")
                        ui.label("Cada ponto representa o total de litros de um dia.").classes("help-text mb-2")
                        if not df_hist_diaria.empty:
                            step = max(1, len(df_hist_diaria) // 30)
                            ui.echart({
                                "tooltip": {"trigger": "axis"},
                                "xAxis": {"type": "category", "data": list(df_hist_diaria["dia"]),
                                          "axisLabel": {"interval": step - 1, "rotate": 35, "fontSize": 9}},
                                "yAxis": {"type": "value", "name": "Litros"},
                                "dataZoom": [{"type": "slider", "bottom": 30, "height": 18}],
                                "series": [{
                                    "type": "line", "data": list(df_hist_diaria["total"]),
                                    "smooth": True, "symbol": "none",
                                    "areaStyle": {"opacity": 0.25},
                                    "itemStyle": {"color": "#8b5cf6"},
                                }],
                            }).classes("w-full h-64")

                # ── Tabla resumen mensual ──────────────────────────────────────
                with ui.card().classes("mx-2 mt-2"):
                    ui.label("Resumo mensal detalhado").classes("font-bold mb-2")
                    if not df_hist_mes.empty:
                        df_tabla = df_hist_mes[["mes","total","media_diaria","media_vaca","dias"]].copy()
                        df_tabla.columns = ["Mês","Total Litros","Média Diária","L/Vaca","Dias"]
                        df_to_table(df_tabla, pagination=20)

                # ── Comparação Ano a Ano ───────────────────────────────────────
                ano_a = date.today().year
                ano_b = ano_a - 1
                ui.separator().classes("mx-2 mt-6")
                with ui.row().classes("w-full px-2 mt-3 mb-1 items-center"):
                    ui.label("Comparação Ano a Ano").classes("text-lg font-bold text-grey-7")
                    ui.label(f"— {ano_b} vs {ano_a}").classes("text-sm text-grey-5 ml-1")
                    ui.space()
                    ui.label("Totais calculados apenas nos meses com dados em ambos os anos.").classes("text-xs text-grey-5 italic")

                yoy_ok = not df_yoy_leite.empty and not df_yoy_fin.empty
                if yoy_ok:
                    ov_l = df_yoy_leite[(df_yoy_leite["atual"] > 0) & (df_yoy_leite["anterior"] > 0)]
                    ov_f = df_yoy_fin[
                        ((df_yoy_fin["rec_anterior"] + df_yoy_fin["desp_anterior"]) > 0) &
                        ((df_yoy_fin["rec_atual"]    + df_yoy_fin["desp_atual"])    > 0)
                    ]
                    n_ov_l, n_ov_f = len(ov_l), len(ov_f)

                    tot_l_a = float(ov_l["atual"].sum())
                    tot_l_b = float(ov_l["anterior"].sum())

                    def _pct(a, b): return round((a - b) / b * 100, 1) if b else None
                    def _fmt(d, lower_is_better=False):
                        if d is None: return "—", "text-grey-5"
                        good  = (d <= 0) if lower_is_better else (d >= 0)
                        arrow = "▲" if d >= 0 else "▼"
                        return f"{arrow} {abs(d):.1f}%", "text-green-600" if good else "text-red-500"

                    d_l, c_l = _fmt(_pct(tot_l_a, tot_l_b))

                    # diesel overlap
                    ov_d  = df_yoy_diesel[(df_yoy_diesel["consumo_atual"] > 0) & (df_yoy_diesel["consumo_anterior"] > 0)]
                    n_ov_d = len(ov_d)
                    if n_ov_d > 0:
                        cons_a = float(ov_d["consumo_atual"].sum())
                        cons_b = float(ov_d["consumo_anterior"].sum())
                        cust_a = float(ov_d["custo_atual"].sum())
                        cust_b = float(ov_d["custo_anterior"].sum())
                        d_cons, c_cons = _fmt(_pct(cons_a, cons_b), lower_is_better=True)

                    with ui.row().classes("w-full gap-3 px-2 flex-wrap"):
                        with ui.card().classes("flex-1 min-w-52 p-4 text-center"):
                            ui.label("Produção de leite").classes("text-xs text-grey-5 uppercase tracking-widest mb-1")
                            ui.label(d_l).classes(f"text-2xl font-bold {c_l}")
                            ui.label(f"{int(tot_l_a):,} L  vs  {int(tot_l_b):,} L").classes("text-xs text-grey-5 mt-1")
                            ui.label(f"{n_ov_l} meses comparáveis").classes("text-xs text-grey-4 mt-1")

                        if n_ov_d > 0:
                            with ui.card().classes("flex-1 min-w-52 p-4 text-center"):
                                ui.label("Diesel — consumo").classes("text-xs text-grey-5 uppercase tracking-widest mb-1")
                                ui.label(d_cons).classes(f"text-2xl font-bold {c_cons}")
                                ui.label(f"{cons_a:,.0f} L  vs  {cons_b:,.0f} L").classes("text-xs text-grey-5 mt-1")
                                custo_delta = f"R$ {int(cust_a):,}  vs  R$ {int(cust_b):,}" if cust_b else ""
                                if custo_delta:
                                    ui.label(custo_delta).classes("text-xs text-grey-4")
                                ui.label(f"{n_ov_d} meses comparáveis").classes("text-xs text-grey-4 mt-1")

                        if n_ov_f > 0:
                            rec_a  = float(ov_f["rec_atual"].sum())
                            rec_b  = float(ov_f["rec_anterior"].sum())
                            desp_a = float(ov_f["desp_atual"].sum())
                            desp_b = float(ov_f["desp_anterior"].sum())
                            d_rec,  c_rec  = _fmt(_pct(rec_a,  rec_b))
                            d_desp, c_desp = _fmt(_pct(desp_a, desp_b), lower_is_better=True)
                            for titulo, txt, color, sub in [
                                ("Receitas",  d_rec,  c_rec,
                                 f"R$ {int(rec_a):,}  vs  R$ {int(rec_b):,}"),
                                ("Despesas",  d_desp, c_desp,
                                 f"R$ {int(desp_a):,}  vs  R$ {int(desp_b):,}"),
                            ]:
                                with ui.card().classes("flex-1 min-w-52 p-4 text-center"):
                                    ui.label(titulo).classes("text-xs text-grey-5 uppercase tracking-widest mb-1")
                                    ui.label(txt).classes(f"text-2xl font-bold {color}")
                                    ui.label(sub).classes("text-xs text-grey-5 mt-1")
                                    ui.label(f"{n_ov_f} meses comparáveis").classes("text-xs text-grey-4 mt-1")
                        else:
                            with ui.card().classes("flex-2 min-w-64 p-4 text-center bg-grey-1"):
                                ui.label("Receitas e Despesas").classes("text-xs text-grey-5 uppercase tracking-widest mb-1")
                                ui.label("Sem meses comparáveis ainda").classes("text-base text-grey-5 font-medium")
                                ui.label(f"Dados financeiros de {ano_b} e {ano_a} não se sobrepõem em nenhum mês.").classes("text-xs text-grey-4 mt-1")

                    meses_l = list(df_yoy_leite["mes_nome"])
                    meses_f = list(df_yoy_fin["mes_nome"])
                    meses_d = list(df_yoy_diesel["mes_nome"]) if not df_yoy_diesel.empty else []

                    # linha 1: leite + diesel
                    with ui.row().classes("w-full gap-4 px-2 mt-3"):
                        with ui.card().classes("flex-1"):
                            ui.label(f"Produção de leite — {ano_b} vs {ano_a}").classes("font-bold mb-1")
                            ui.label("Litros totais por mês em cada ano.").classes("help-text mb-2")
                            ui.echart({
                                "tooltip": {"trigger": "axis"},
                                "legend": {"data": [str(ano_b), str(ano_a)], "bottom": 0},
                                "xAxis": {"type": "category", "data": meses_l},
                                "yAxis": {"type": "value", "name": "Litros"},
                                "series": [
                                    {"name": str(ano_b), "type": "bar",
                                     "data": list(df_yoy_leite["anterior"]),
                                     "itemStyle": {"color": "#94a3b8"}, "barMaxWidth": 35},
                                    {"name": str(ano_a), "type": "bar",
                                     "data": list(df_yoy_leite["atual"]),
                                     "itemStyle": {"color": "#0ea5e9"}, "barMaxWidth": 35},
                                ],
                            }).classes("w-full h-64")

                        if meses_d:
                            with ui.card().classes("flex-1"):
                                ui.label(f"Consumo de diesel — {ano_b} vs {ano_a}").classes("font-bold mb-1")
                                ui.label("Litros consumidos por mês em cada ano.").classes("help-text mb-2")
                                ui.echart({
                                    "tooltip": {"trigger": "axis"},
                                    "legend": {"data": [str(ano_b), str(ano_a)], "bottom": 0},
                                    "xAxis": {"type": "category", "data": meses_d},
                                    "yAxis": {"type": "value", "name": "Litros"},
                                    "series": [
                                        {"name": str(ano_b), "type": "bar",
                                         "data": list(df_yoy_diesel["consumo_anterior"]),
                                         "itemStyle": {"color": "#94a3b8"}, "barMaxWidth": 35},
                                        {"name": str(ano_a), "type": "bar",
                                         "data": list(df_yoy_diesel["consumo_atual"]),
                                         "itemStyle": {"color": "#f59e0b"}, "barMaxWidth": 35},
                                    ],
                                }).classes("w-full h-64")

                    # linha 2: finanças
                    with ui.row().classes("w-full gap-4 px-2 mt-2 pb-6"):
                        with ui.card().classes("w-full"):
                            ui.label(f"Receitas e despesas — {ano_b} vs {ano_a}").classes("font-bold mb-1")
                            ui.label(f"Linha sólida = {ano_a} · Tracejada = {ano_b}.").classes("help-text mb-2")
                            ui.echart({
                                "tooltip": {"trigger": "axis"},
                                "legend": {"data": [f"Receita {ano_b}", f"Receita {ano_a}",
                                                    f"Despesa {ano_b}", f"Despesa {ano_a}"],
                                           "bottom": 0, "type": "scroll"},
                                "xAxis": {"type": "category", "data": meses_f},
                                "yAxis": {"type": "value", "name": "R$"},
                                "series": [
                                    {"name": f"Receita {ano_b}", "type": "line",
                                     "data": list(df_yoy_fin["rec_anterior"]),
                                     "smooth": True, "symbolSize": 6,
                                     "itemStyle": {"color": "#86efac"},
                                     "lineStyle": {"type": "dashed", "width": 2}},
                                    {"name": f"Receita {ano_a}", "type": "line",
                                     "data": list(df_yoy_fin["rec_atual"]),
                                     "smooth": True, "symbolSize": 6,
                                     "itemStyle": {"color": "#16a34a"},
                                     "lineStyle": {"width": 2}},
                                    {"name": f"Despesa {ano_b}", "type": "line",
                                     "data": list(df_yoy_fin["desp_anterior"]),
                                     "smooth": True, "symbolSize": 6,
                                     "itemStyle": {"color": "#fca5a5"},
                                     "lineStyle": {"type": "dashed", "width": 2}},
                                    {"name": f"Despesa {ano_a}", "type": "line",
                                     "data": list(df_yoy_fin["desp_atual"]),
                                     "smooth": True, "symbolSize": 6,
                                     "itemStyle": {"color": "#ef4444"},
                                     "lineStyle": {"width": 2}},
                                ],
                            }).classes("w-full h-56")
                else:
                    estado_vacio("Dados insuficientes para comparação ano a ano.",
                                 "Necessário ter registros em ambos os anos.")


# ── FICHA INDIVIDUAL DE VACA ─────────────────────────────────────────────────

@ui.page("/vaca/{vaca_id}")
def ficha_vaca(vaca_id: int) -> None:
    nav("/vacas")
    try:
        df_info = read_sql("""
            SELECT nombre, COALESCE(grupo,'—') AS grupo, estado,
                   TO_CHAR(CURRENT_DATE - fecha_ingreso,'FM999') AS dias_en_granja
            FROM tabla_vacas WHERE vaca_id = %s
        """, params=(vaca_id,))
        if df_info.empty:
            ui.label("Animal não encontrado.").classes("m-8 text-red font-semibold")
            return
        info = df_info.iloc[0]

        df_prod = read_sql("""
            SELECT TO_CHAR(DATE(fecha_hora),'DD/MM') AS dia,
                   DATE(fecha_hora) AS dia_ord,
                   ROUND(SUM(litros)::numeric,1)::float AS litros
            FROM tabla_leche
            WHERE vaca_id = %s AND fecha_hora >= CURRENT_DATE - 30
            GROUP BY DATE(fecha_hora) ORDER BY dia_ord
        """, params=(vaca_id,))

        df_salud = read_sql("""
            SELECT TO_CHAR(fecha,'DD/MM/YYYY') AS "Data",
                   tipo_evento                 AS "Tipo",
                   descripcion                 AS "Descrição",
                   COALESCE(veterinario,'—')   AS "Veterinário",
                   costo                       AS "Custo R$"
            FROM tabla_salud WHERE vaca_id = %s
            ORDER BY fecha DESC LIMIT 15
        """, params=(vaca_id,))

        df_reprod = read_sql("""
            SELECT TO_CHAR(fecha_evento,'DD/MM/YYYY')       AS "Data",
                   tipo_evento                               AS "Evento",
                   COALESCE(tipo_fertilizacion,'—')         AS "Fertilização",
                   TO_CHAR(fecha_parto_esperado,'DD/MM/YYYY') AS "Parto esperado",
                   COALESCE(resultado_parto,'—')            AS "Resultado",
                   COALESCE(observaciones,'—')              AS "Observações"
            FROM tabla_reproduccion WHERE vaca_id = %s
            ORDER BY fecha_evento DESC
        """, params=(vaca_id,))

        total_litros = float(read_sql(
            "SELECT COALESCE(SUM(litros),0) FROM tabla_leche WHERE vaca_id=%s", params=(vaca_id,)
        ).iloc[0, 0])
        prom_litros = float(read_sql(
            "SELECT COALESCE(AVG(litros),0) FROM tabla_leche WHERE vaca_id=%s", params=(vaca_id,)
        ).iloc[0, 0])

        error_msg = None
    except Exception as exc:
        error_msg = str(exc)

    if error_msg:
        ui.label(f"Error al cargar la ficha: {error_msg}").classes("m-8 text-red")
        return

    # Header
    with ui.row().classes("px-4 pt-4 items-center gap-4"):
        ui.button("← Voltar", on_click=lambda: ui.navigate.to("/vacas")).classes(
            "bg-grey-2 text-grey-8 font-medium px-4 py-2"
        )
        with ui.column().classes("gap-0"):
            ui.label(f"🐄 {info['nombre']}").classes("text-2xl font-bold")
            ui.label(
                f"Grupo: {info['grupo']}  •  Estado: {info['estado']}  •  {info['dias_en_granja']} dias na fazenda"
            ).classes("text-sm text-grey-6")

    # KPIs de la vaca
    with ui.row().classes("w-full gap-4 px-4 mt-4"):
        for titulo, valor, sub in [
            ("🥛 Total produzido", f"{total_litros:,.0f} L", "acumulado histórico"),
            ("📊 Média/ordenha", f"{prom_litros:.1f} L",   "por sessão de ordenha"),
            ("💊 Eventos de saúde", str(len(df_salud)),       "registros encontrados"),
            ("🐣 Eventos reprodutivos", str(len(df_reprod)), "fertilizações/partos"),
        ]:
            with ui.card().classes("flex-1 p-5 text-center"):
                ui.label(titulo).classes("text-xs text-grey-5 uppercase tracking-widest")
                ui.label(valor).classes("text-3xl font-bold text-blue-800 mt-1")
                ui.label(sub).classes("text-xs text-grey-5 mt-1")

    # Producción últimos 30 días
    with ui.card().classes("mx-4 mt-4"):
        ui.label("📈 Produção — últimos 30 dias").classes("font-bold mb-1")
        ui.label("Litros por dia de ordenha.").classes("help-text mb-2")
        if not df_prod.empty:
            ui.echart({
                "tooltip": {"trigger": "axis"},
                "xAxis": {"type": "category", "data": list(df_prod["dia"]),
                          "axisLabel": {"rotate": 30, "fontSize": 11}},
                "yAxis": {"type": "value", "name": "lts"},
                "series": [{"type": "line", "data": list(df_prod["litros"]),
                            "smooth": True, "areaStyle": {}, "itemStyle": {"color": "#0ea5e9"}}],
            }).classes("w-full h-56")
        else:
            estado_vacio("Sem registros de produção nos últimos 30 dias.")

    # Salud y reproducción lado a lado
    with ui.row().classes("w-full gap-4 px-4 mt-4 pb-6"):
        with ui.card().classes("flex-1"):
            ui.label("💊 Histórico Sanitário").classes("font-bold mb-2")
            if df_salud.empty:
                estado_vacio("Sem eventos de saúde registrados.")
            else:
                df_to_table(df_salud, pagination=10)

        with ui.card().classes("flex-1"):
            ui.label("🐣 Histórico Reprodutivo").classes("font-bold mb-2")
            if df_reprod.empty:
                estado_vacio("Sem eventos reprodutivos registrados.")
            else:
                df_to_table(df_reprod, pagination=10)


ui.run(title="Dairy Farm Pro", port=8080, reload=False)
