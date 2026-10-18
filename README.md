# nudat3-decay-stability

Análisis de datos nucleares de [NuDat 3](https://www.nndc.bnl.gov/nudat3/) (NNDC).

**Pregunta científica:** ¿cómo se relaciona la razón $N/Z$ con el modo de desintegración dominante ($\beta^-$ vs $\beta^+$/EC) en los estados base?

## Documentación

- [docs/fundamentacion_fisica.md](docs/fundamentacion_fisica.md) — fenómeno y pregunta  
- [docs/origen_datos.md](docs/origen_datos.md) — origen CSV  
- [docs/cleaning_log.md](docs/cleaning_log.md) — log de limpieza  
- [docs/modelo_relacional.md](docs/modelo_relacional.md) — ER de **4 tablas**  
- [sql/schema.sql](sql/schema.sql) — schema MySQL  

## Docker: MySQL + JupyterLab + Streamlit

| Servicio | Puerto | Credenciales |
|----------|--------|--------------|
| **mysql** | 3306 | `nudat` / `nudat` / db `nudat` |
| **jupyter** | 8888 | token `nudat` → http://localhost:8888 |
| **streamlit** | 8501 | http://localhost:8501 |

### Inicio rápido

```bash
./run_app.sh
```

Comprueba Docker, **baja las imágenes de Docker Hub**, levanta los contenedores, carga `data/processed/` en MySQL si la base está vacía y abre la app en http://localhost:8501.

| Opción | Efecto |
|--------|--------|
| `--build` | Reconstruye las imágenes localmente (en vez de solo pull) |
| `--reload-data` | Fuerza la recarga de los CSV en MySQL |
| `--reset` | Borra el volumen de MySQL y reconstruye desde cero |
| `--no-browser` | No abre el navegador |
| `--stop` | Detiene los contenedores (los datos se conservan) |

### En otro PC

1. Instalar [Docker Desktop](https://docs.docker.com/get-docker/).
2. Clonar el repo (hace falta el código y `data/processed/`):

```bash
git clone https://github.com/isabelnieto900/nudat3-decay-stability.git
cd nudat3-decay-stability
./run_app.sh
```

Las imágenes de Jupyter y Streamlit se descargan de Docker Hub:

| Imagen | Hub |
|--------|-----|
| Jupyter | [isabeln9/nudat3-jupyter](https://hub.docker.com/r/isabeln9/nudat3-jupyter) |
| Streamlit | [isabeln9/nudat3-streamlit](https://hub.docker.com/r/isabeln9/nudat3-streamlit) |
| MySQL | `mysql:8.0` (oficial) |

### Paso a paso (equivalente manual)

```bash
docker compose pull
docker compose up -d
docker compose exec jupyter python -m src.load_db
```

Reconstruir localmente: `docker compose up -d --build`.  
Schema limpio desde cero: `docker compose down -v` y volver a `up` (init con `sql/schema.sql`).

## Notebooks

1. [`notebooks/01_eda.ipynb`](notebooks/01_eda.ipynb) — exploración  
2. [`notebooks/02_clean_etl.ipynb`](notebooks/02_clean_etl.ipynb) — limpieza → `data/processed/`  
3. [`notebooks/02b_load_mysql.ipynb`](notebooks/02b_load_mysql.ipynb) — carga MySQL  
4. [`notebooks/03_analysis.ipynb`](notebooks/03_analysis.ipynb) — SQL + figuras N/Z–modo  

Consultas: [`sql/queries.sql`](sql/queries.sql)

## App Streamlit

Versión interactiva del análisis, consultando MySQL en vivo ([`app/`](app/)). Con los contenedores arriba y los datos cargados: http://localhost:8501

1. **Inicio** — pregunta, KPIs y nº de estados base por modo  
2. **Carta de nuclidos** — N–Z coloreado por modo o por $\log_{10} t_{1/2}$, con filtros  
3. **N/Z por modo** — ⟨N/Z⟩ ± σ, min/max, histograma y caja/violín  
4. **Frontera y valle** — ⟨N/Z⟩ por bins de Z (ancho ajustable), valle de estables, modo mayoritario y conclusiones  
5. **Coulomb** — factor LDM $Z(Z-1)/A^{1/3}$ frente a ⟨N/Z⟩  
6. **Explorador** — nuclido individual (estados y canales), canales más frecuentes y tabla filtrable con descarga CSV  

Ejecución local (sin el contenedor): `pip install -r requirements.txt` y `streamlit run app/Inicio.py` (usa `MYSQL_HOST=127.0.0.1` por defecto).

## Datos

- `data/raw/` — Wallet Cards + Chart half-life (sin modificar)  
- `data/processed/` — limpios listos para MySQL  
