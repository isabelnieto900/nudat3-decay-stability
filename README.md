# nudat3-decay-stability

Análisis de datos nucleares de [NuDat 3](https://www.nndc.bnl.gov/nudat3/) (NNDC): razón $N/Z$, modos de decaimiento, $Q_\beta$ y valle de estabilidad.

## Documentación

- [docs/fundamentacion_fisica.md](docs/fundamentacion_fisica.md) — fenómeno y pregunta científica  
- [docs/origen_datos.md](docs/origen_datos.md) — origen CSV  
- [docs/cleaning_log.md](docs/cleaning_log.md) — log de limpieza  
- [docs/modelo_relacional.md](docs/modelo_relacional.md) — diseño ER  
- [sql/schema.sql](sql/schema.sql) — schema MySQL  

## Docker: MySQL + JupyterLab

Dos contenedores en la red `nudat_net`:

| Servicio | Puerto host | Credenciales |
|----------|-------------|--------------|
| **mysql** | 3306 | user/pass/db: `nudat` / `nudat` / `nudat` (root: `nudatroot`) |
| **jupyter** | 8888 | token: `nudat` - http://localhost:8888 |

Volumen persistente: `mysql_data` (los datos no se pierden al parar el contenedor).

### Levantar

```bash
cd nudat3-decay-stability
docker compose up -d --build
docker compose ps
```

Si en WSL el comando `docker` no existe, use `docker.exe` (Docker Desktop) o habilite la integración WSL.

### Cargar datos limpios en MySQL

Desde una terminal del contenedor Jupyter, o abriendo el notebook:

```bash
docker compose exec jupyter python -m src.load_db
```

O en JupyterLab: [`notebooks/02b_load_mysql.ipynb`](notebooks/02b_load_mysql.ipynb).

La carga lee `data/processed/` (salida de `02_clean_etl.ipynb`) y llena las 6 tablas.

### Conexión Jupyter - MySQL

Dentro de Docker, el host es el **nombre del servicio**: `mysql` (variable `MYSQL_HOST`).  
Desde DBeaver en Windows: `localhost:3306`.

### Parar

```bash
docker compose down          # conserva volumen
docker compose down -v       # borra también mysql_data (re-init schema)
```

## Notebooks (orden)

1. [`notebooks/01_eda.ipynb`](notebooks/01_eda.ipynb) — exploración  
2. [`notebooks/02_clean_etl.ipynb`](notebooks/02_clean_etl.ipynb) — limpieza - `data/processed/`  
3. [`notebooks/02b_load_mysql.ipynb`](notebooks/02b_load_mysql.ipynb) — conexión y carga MySQL  
4. [`notebooks/03_analysis.ipynb`](notebooks/03_analysis.ipynb) — consultas SQL + análisis de la pregunta  

Consultas: [`sql/queries.sql`](sql/queries.sql)

## Datos

- `data/raw/` — CSV NuDat **sin modificar**  
- `data/processed/` — datasets limpios  
