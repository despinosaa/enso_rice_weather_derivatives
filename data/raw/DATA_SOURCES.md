# Fuentes de datos — links de descarga

Cada subcarpeta de `data/raw/` recibe los archivos de la fuente que le corresponde. Bajar todo a `raw/` sin tocar; los notebooks `00_` y `01_` se encargan de limpiar y volcar resultados a `data/processed/`.

---

## `data/raw/ideam/` — Series climáticas diarias (Colombia)

**Portal principal (recomendado):**
- **DHIME — Sistema de Información para gestión de datos Hidrológicos y Meteorológicos:**
  http://dhime.ideam.gov.co/atencionciudadano/
  Permite consulta y descarga de series temporales de temperatura, precipitación, humedad, viento, etc., por estación. Selección por mapa o por código de estación.
- **Manual de usuario DHIME (PDF):** http://dhime.ideam.gov.co/atencionciudadano/manual.pdf

**Alternativa vía Datos Abiertos Colombia (más cómodo para descarga masiva):**
- Temperatura: https://www.datos.gov.co/Ambiente-y-Desarrollo-Sostenible/Datos-Hidrometeorol-gicos-Crudos-Red-de-Estaciones/sbwg-7ju4
- Precipitación: buscar en https://www.datos.gov.co/ con el filtro "IDEAM" → datasets de Red de Estaciones

**Pronósticos diarios (complemento para validación):**
- http://www.pronosticosyalertas.gov.co/datos-abiertos-ideam

**Estaciones sugeridas (zonas arroceras):**
- Tolima: Perales-Ibagué, Nataima, Espinal
- Casanare: Yopal, Aguazul
- Meta: Villavicencio (Vanguardia), Puerto López
- Huila: Neiva, Aeropuerto Benito Salas

**Período objetivo:** 1990-01-01 a 2025-12-31, **frecuencia diaria**.
**Variables:** temperatura mínima, máxima, media; precipitación acumulada diaria.

---

## `data/raw/noaa/` — Índice ENSO (RONI)

**Aviso (feb 2026):** NOAA reemplazó ONI por **RONI (Relative Oceanic Niño Index)** como métrica oficial de ENSO. Usamos solo RONI para alinear con la práctica vigente.

**RONI — Relative Oceanic Niño Index:**
- Tabla CPC (1950-presente): https://www.cpc.ncep.noaa.gov/products/analysis_monitoring/enso/roni/

**Formato del archivo y conversión a mensual.** El RONI viene tabulado como **media móvil trimestral solapada centrada en cada mes**, con 12 columnas por año (DJF, JFM, FMA, MAM, AMJ, MJJ, JJA, JAS, ASO, SON, OND, NDJ). La convención NOAA asigna cada trimestre al **mes central**, lo que produce directamente una serie mensual:

| Columna | Trimestre | Mes central |
|---|---|---|
| DJF | Dic(t-1) – Ene(t) – Feb(t) | Enero |
| JFM | Ene – Feb – Mar | Febrero |
| FMA | Feb – Mar – Abr | Marzo |
| ... | ... | ... |
| NDJ | Nov – Dic – Ene(t+1) | Diciembre |

Snippet de transformación de la tabla cruda a serie mensual:

```python
import pandas as pd

# Asumiendo que descargas la tabla con columnas: Year, DJF, JFM, ..., NDJ
df_raw = pd.read_csv("data/raw/noaa/roni_quarterly.csv")  # ejemplo
months = ["DJF","JFM","FMA","MAM","AMJ","MJJ","JJA","JAS","ASO","SON","OND","NDJ"]

roni_monthly = (df_raw.melt(id_vars="Year", value_vars=months,
                            var_name="quarter", value_name="roni")
                       .assign(month=lambda d: d["quarter"].map(
                           {q: i+1 for i, q in enumerate(months)}))
                       .assign(date=lambda d: pd.to_datetime(
                           dict(year=d["Year"], month=d["month"], day=1)))
                       .sort_values("date")[["date","roni"]]
                       .reset_index(drop=True))

# Clasificación ENSO
def fase_enso(x):
    if pd.isna(x): return "NA"
    if x >= 0.5: return "Niño"
    if x <= -0.5: return "Niña"
    return "Neutro"

roni_monthly["fase"] = roni_monthly["roni"].apply(fase_enso)
```

Resultado: una tabla mensual `(date, roni, fase)` lista para hacer `merge` con el clima diario por año-mes.

---

## `data/raw/fedearroz/` — Estadísticas arroceras

**Portal Fedearroz - Investigaciones Económicas:**
- Hub: https://www.fedearroz.com.co/es/fondo-nacional-del-arroz/investigaciones-economicas/estadisticas-arroceras/
- **Área, producción, rendimiento (semestral, 1980-presente, por zona):**
  https://fedearroz.com.co/es/fondo-nacional-del-arroz/investigaciones-economicas/estadisticas-arroceras/area-produccion-y-rendimiento/
- **Precios:** https://www.fedearroz.com.co/es/fondo-nacional-del-arroz/investigaciones-economicas/estadisticas-arroceras/precios-del-sector-arrocero/
- **Costos de producción:** https://www.fedearroz.com.co/es/fondo-nacional-del-arroz/investigaciones-economicas/estadisticas-arroceras/costos/

**Censo Nacional Arrocero (DANE-Fedearroz) — referencia más detallada:**
- 5° Censo 2023: https://www.dane.gov.co/files/operaciones/CNA/bol-5toCNA-2023.pdf
- Boletín semestral ENAM (Encuesta Nacional de Arroz Mecanizado): https://www.dane.gov.co/files/operaciones/ENAM/bol-ENAM-Isem2025.pdf

**Agronet (MADR) — Evaluaciones Agropecuarias Municipales (EVA):**
- Portal: https://agronet.gov.co/estadisticas/agricola
- Descargas históricas: https://agronet.gov.co/documentacion-estadisticas/agricola/reporte-evaluaciones-agropecuarias-eva-y-anuario-estadistico
- EVA 2019-2024 (datos abiertos): https://www.datos.gov.co/Agricultura-y-Desarrollo-Rural/Evaluaciones-Agropecuarias-Municipales-EVA-2019-20/uejq-wxrr
- EVA histórica completa: https://www.datos.gov.co/Agricultura-y-Desarrollo-Rural/Evaluaciones-Agropecuarias-Municipales-EVA/2pnw-mmge

**Variables a extraer:** área sembrada, área cosechada, producción, rendimiento (t/ha) — por departamento, **semestre** (I y II), sistema (riego/secano).

---

## `data/raw/era5/` — Reanálisis ECMWF (para huecos IDEAM)

ERA5 sirve como reanálisis de referencia para imputar vacíos en las series IDEAM. Grilla ~31 km, frecuencia horaria/diaria, desde 1979.

**Opción 1 (recomendada para uso técnico) — Copernicus Climate Data Store (CDS):**
- Portal: https://cds.climate.copernicus.eu/
- Dataset "ERA5 daily statistics" o "ERA5 hourly data on single levels"
- Requiere registro gratuito y uso del API `cdsapi` (Python).
- Tutorial: https://forum.ecmwf.int/t/downloading-era5-land-data-summarized-daily/2927

**Opción 2 (más fácil sin registro) — Google Earth Engine:**
- ERA5 Daily Aggregates: https://developers.google.com/earth-engine/datasets/catalog/ECMWF_ERA5_DAILY
- ERA5 Hourly: https://developers.google.com/earth-engine/datasets/catalog/ECMWF_ERA5_HOURLY

**Variables a descargar:**
- `mean_2m_air_temperature`, `minimum_2m_air_temperature`, `maximum_2m_air_temperature` (Kelvin → convertir a °C)
- `total_precipitation` (metros → convertir a mm)

**Coordenadas de las estaciones IDEAM principales:**
| Estación | Lat | Lon |
|---|---|---|
| Perales-Ibagué (Tolima) | 4.43 | -75.15 |
| Yopal (Casanare) | 5.32 | -72.40 |
| Villavicencio-Vanguardia (Meta) | 4.17 | -73.61 |
| Neiva-Benito Salas (Huila) | 2.95 | -75.29 |

*(Verificar coordenadas exactas en metadatos IDEAM al descargar.)*

---

## Notas operativas

- **Convención de naming:** `<fuente>_<variable>_<estacion-o-region>_<periodo>.<ext>`. Ej.: `ideam_temperatura_perales_1990-2025.csv`, `noaa_roni_1950-2026.csv`.
- **No editar archivos en `data/raw/`** una vez descargados. Toda transformación queda en notebooks `00_` / `01_` y los resultados se vuelcan a `data/processed/`.
- **Formatos preferidos en `processed/`:** `.parquet` para series diarias largas (más rápido que CSV con pandas), `.csv` solo para tablas chicas de resultados.

---

## Esquema de la base de datos consolidada

La base se organiza en **tres capas temporales** (diaria, mensual, semestral) que viven en `data/processed/`. Cada capa conserva su frecuencia natural; los joins entre capas se hacen en el momento del análisis, no antes. Esto evita destruir la granularidad diaria del clima, que es la que necesitamos para calcular HDD/CRI sobre la ventana fenológica del arroz.

### Capa A — Clima diario

**Archivo:** `data/processed/clima_diario.parquet`
**Llave primaria:** `(station_id, date)`
**Cobertura:** 1990-01-01 → 2025-12-31 (~13.140 filas por estación × 8-10 estaciones)

| Columna | Tipo | Descripción |
|---|---|---|
| `station_id` | str | Código IDEAM (ej. `21206900` para Perales) |
| `station_name` | str | Nombre legible |
| `department` | str | Departamento (Tolima, Casanare, Meta, Huila) |
| `zone` | str | Zona arrocera (Centro, Llanos) — coincide con clasificación Fedearroz |
| `date` | date | Fecha (resolución diaria) |
| `t_min` | float | Temperatura mínima (°C) |
| `t_max` | float | Temperatura máxima (°C) |
| `t_mean` | float | Temperatura media (°C) — `(t_min + t_max) / 2` si IDEAM no la reporta |
| `precip` | float | Precipitación acumulada diaria (mm) |
| `source` | str | `"ideam"` o `"era5"` (cuando se imputa un hueco) |

### Capa B — Índice ENSO mensual

**Archivo:** `data/processed/enso_mensual.parquet`
**Llave primaria:** `(year, month)`
**Cobertura:** 1990-01 → 2026-04 (~436 filas)

| Columna | Tipo | Descripción |
|---|---|---|
| `year` | int | Año |
| `month` | int | Mes (1-12) |
| `date` | date | Primer día del mes (para joins por fecha) |
| `roni` | float | RONI del trimestre centrado en este mes |
| `fase` | str | `"Niño"` si RONI ≥ 0.5, `"Niña"` si ≤ -0.5, `"Neutro"` en otro caso |

### Capa C — Rendimientos semestrales

**Archivo:** `data/processed/rendimientos.parquet`
**Llave primaria:** `(zone, year, semester)`
**Cobertura:** 1990-I → 2024-II (~70 filas por zona × 5 zonas)

| Columna | Tipo | Descripción |
|---|---|---|
| `zone` | str | Zona arrocera Fedearroz (Centro, Llanos, Costa Norte, Bajo Cauca, Santanderes) |
| `year` | int | Año |
| `semester` | int | 1 o 2 |
| `system` | str | `"riego"` o `"secano"` (cuando se reporta separado) |
| `area_sembrada` | float | Hectáreas |
| `area_cosechada` | float | Hectáreas |
| `produccion` | float | Toneladas (arroz paddy verde) |
| `rendimiento` | float | t/ha — variable dependiente principal |
| `precio_paddy` | float | COP/tonelada (opcional, viene de tabla de precios) |

### Cómo se hacen los joins entre capas

**Join A ↔ B (clima diario con ENSO mensual)** — necesario para clasificar cada día según fase ENSO y para hacer regresiones clima ~ ENSO:

```python
clima = pd.read_parquet("data/processed/clima_diario.parquet")
enso  = pd.read_parquet("data/processed/enso_mensual.parquet")

clima["year"]  = clima["date"].dt.year
clima["month"] = clima["date"].dt.month
clima_con_enso = clima.merge(enso[["year","month","roni","fase"]],
                             on=["year","month"], how="left")
```

**Join A ↔ C (clima diario con rendimientos semestrales)** — agregar índices climáticos sobre la ventana fenológica del semestre antes de unir:

```python
# 1. Definir ventana fenológica del semestre (ejemplo: días 60-100 desde inicio)
def en_ventana_fenologica(date, semester):
    """Devuelve True si la fecha está en la ventana floración-llenado del semestre."""
    # ajustar según calendario de siembra real por zona
    ...

# 2. Calcular HDD y CRI por (zone, year, semester)
indices_sem = (clima.assign(semester=lambda d: (d["date"].dt.month > 6).astype(int) + 1)
                    .query("en_ventana_fenologica(date, semester)")
                    .groupby(["zone","year","semester"])
                    .agg(hdd=("t_max", lambda s: (s.clip(lower=32) - 32).sum()),
                         cri=("precip", "sum"))
                    .reset_index())

# 3. Unir con rendimientos
df_modelo = rend.merge(indices_sem, on=["zone","year","semester"], how="left")
```

Esta tabla `df_modelo` final es la que alimenta la regresión rendimiento ~ HDD + CRI + (controles) que da el hedge ratio del notebook 10.

### Resumen visual de las llaves

```
Capa A (diaria) ─── (year, month) ───► Capa B (mensual)
       │
       └── (zone, year, semester) [tras agregación a HDD/CRI] ───► Capa C (semestral)
```

Mantener las tres capas separadas tiene una ventaja extra: cuando el grupo necesite cambiar la definición de la ventana fenológica, del umbral del HDD o de la fase ENSO, solo se re-ejecuta el cálculo de los joins; las capas crudas procesadas no cambian.