# nudat3-decay-stability

Análisis de datos nucleares de [NuDat 3](https://www.nndc.bnl.gov/nudat3/) (NNDC).

**Pregunta científica:** ¿cómo se relaciona la razón $N/Z$ con el modo de desintegración dominante ($\beta^-$ vs $\beta^+$/EC) en los estados base?

## Documentación

- [docs/fundamentacion_fisica.md](docs/fundamentacion_fisica.md) — fenómeno y pregunta  
- [docs/origen_datos.md](docs/origen_datos.md) — origen CSV  
- [docs/cleaning_log.md](docs/cleaning_log.md) — log de limpieza  
- [docs/modelo_relacional.md](docs/modelo_relacional.md) — ER de **4 tablas**  
- [sql/schema.sql](sql/schema.sql) — schema MySQL  

## Docker: MySQL + JupyterLab

| Servicio | Puerto | Credenciales |
|----------|--------|--------------|
| **mysql** | 3306 | `nudat` / `nudat` / db `nudat` |
| **jupyter** | 8888 | token `nudat` → http://localhost:8888 |

```bash
docker compose up -d --build
docker compose exec jupyter python -m src.load_db
```

Schema limpio desde cero: `docker compose down -v` y volver a `up` (init con `sql/schema.sql`).

## Notebooks

1. [`notebooks/01_eda.ipynb`](notebooks/01_eda.ipynb) — exploración  
2. [`notebooks/02_clean_etl.ipynb`](notebooks/02_clean_etl.ipynb) — limpieza → `data/processed/`  
3. [`notebooks/02b_load_mysql.ipynb`](notebooks/02b_load_mysql.ipynb) — carga MySQL  
4. [`notebooks/03_analysis.ipynb`](notebooks/03_analysis.ipynb) — SQL + figuras N/Z–modo  

Consultas: [`sql/queries.sql`](sql/queries.sql)

## Datos

- `data/raw/` — Wallet Cards + Chart half-life (sin modificar)  
- `data/processed/` — limpios listos para MySQL  
