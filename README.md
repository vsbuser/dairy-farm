# 🐄 Dairy Farm Pro — Guía de inicio

Panel de gestión para granjas lecheras. Permite controlar vacas, producción de leche, salud animal, dietas, bodega, maquinaria, reproducción y finanzas.

---

## Requisitos previos

Antes de empezar, necesitás tener instalado en tu computadora:

| Programa | Versión mínima | Dónde descargarlo |
|---|---|---|
| Python | 3.11 o superior | https://www.python.org/downloads/ |
| PostgreSQL | 14 o superior | https://www.postgresql.org/download/ |
| Git | cualquiera | https://git-scm.com/downloads |

> **Tip:** Durante la instalación de Python, marcá la opción **"Add Python to PATH"**.  
> Durante la instalación de PostgreSQL, anotá la contraseña que le ponés al usuario `postgres`.

---

## Paso 1 — Clonar el proyecto

Abrí una terminal (PowerShell en Windows, Terminal en Mac/Linux) y ejecutá:

```bash
git clone https://github.com/vsbuser/dairy-farm.git
cd dairy-farm
```

---

## Paso 2 — Crear el entorno virtual

Dentro de la carpeta del proyecto, ejecutá:

```bash
# Windows
python -m venv venv

# Mac / Linux
python3 -m venv venv
```

---

## Paso 3 — Instalar las dependencias

Activá el entorno virtual e instalá los paquetes:

```bash
# Windows
venv\Scripts\activate
pip install nicegui pandas psycopg2-binary sqlalchemy

# Mac / Linux
source venv/bin/activate
pip install nicegui pandas psycopg2-binary sqlalchemy
```

---

## Paso 4 — Crear la base de datos en PostgreSQL

Abrí **pgAdmin** (se instala junto con PostgreSQL) o la terminal `psql` y creá la base de datos:

```sql
CREATE DATABASE granja_db;
```

> Si la contraseña de tu usuario `postgres` es distinta de `password`,
> abrí el archivo `app/main.py` y cambiá estas líneas al inicio:
>
> ```python
> _DB_URL = "postgresql+psycopg2://postgres:TU_CONTRASEÑA@localhost/granja_db"
> DB_CONFIG = { ..., "password": "TU_CONTRASEÑA", ... }
> ```

---

## Paso 5 — Crear las tablas

Con el entorno virtual activo, ejecutá:

```bash
python scripts/setup_db.py
```

Deberías ver: `EXITO: Tablas creadas correctamente`

---

## Paso 6 — Cargar datos de ejemplo

Ejecutá los scripts de seed en este orden:

```bash
# Datos base: dietas, vacas, leche, insumos, maquinaria
python scripts/seed_data.py

# Vacas adicionales con producción
python scripts/add_vacas_produccion.py

# Datos de reproducción (fertilizaciones y partos)
python scripts/seed_reproduccion.py

# Datos financieros (ingresos y egresos)
python scripts/seed_finanzas.py

# Completa el resto: grupos, salud, insumos y mantenimiento
python scripts/seed_completo.py
```

---

## Paso 7 — Iniciar la aplicación

```bash
python app/main.py
```

Verás en la terminal:

```
NiceGUI ready to go on http://localhost:8080
```

---

## Paso 8 — Abrir en el navegador

Abrí tu navegador (Chrome, Firefox, Edge) y entrá a:

```
http://127.0.0.1:8080
```

¡Listo! El dashboard debería aparecer con todos los datos cargados.

---

## Cómo detener la aplicación

En la terminal donde está corriendo la app, presioná:

```
Ctrl + C
```

---

## Estructura del proyecto

```
dairy-farm/
├── app/
│   └── main.py              ← Aplicación principal (todas las páginas)
├── scripts/
│   ├── setup_db.py          ← Crea las tablas en la base de datos
│   ├── seed_data.py         ← Carga datos base
│   ├── add_vacas_produccion.py
│   ├── seed_reproduccion.py ← Datos de fertilizaciones y partos
│   ├── seed_finanzas.py     ← Datos de ingresos y gastos
│   └── seed_completo.py     ← Completa datos faltantes en todas las secciones
└── README.md
```

---

## Pestañas disponibles

| Pestaña | ¿Para qué sirve? |
|---|---|
| 🏠 Inicio | Resumen general con alertas y gráficos |
| 🐄 Vacas | Registro y agrupación del plantel |
| 💊 Salud | Historial de atenciones veterinarias |
| 🥛 Leche | Registro diario de producción por ordeñe |
| 🥗 Dietas | Composición y comparativa de raciones |
| 📦 Bodega | Control de stock de insumos y alimentos |
| 🚜 Maquinaria | Registro de máquinas y mantenimientos |
| 🐣 Reproducción | Fertilizaciones y partos con fechas estimadas |
| 💰 Finanzas | Ingresos, egresos y balance mensual |

---

## Problemas frecuentes

**"No se pudo conectar a la base de datos"**  
→ Verificá que PostgreSQL esté iniciado. En Windows: Panel de control → Servicios → `postgresql-x64-XX` → Iniciar.

**"Module not found"**  
→ Asegurate de haber activado el entorno virtual (Paso 3) antes de correr la app.

**Puerto 8080 ocupado**  
→ Cambiá el puerto al final de `app/main.py`:  
```python
ui.run(title="Dairy Farm Pro", port=8081, reload=False)
```
y abrí `http://127.0.0.1:8081` en el navegador.
