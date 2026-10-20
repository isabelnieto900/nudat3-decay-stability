# nudat3-decay-stability

Análisis de datos nucleares de [NuDat 3](https://www.nndc.bnl.gov/nudat3/) (NNDC).

**Pregunta científica:** ¿cómo se relaciona la razón $N/Z$ con el modo de desintegración dominante ($\beta^-$ vs $\beta^+$/EC) en los estados base?

## Documentación

- [docs/fundamentacion_fisica.md](docs/fundamentacion_fisica.md) — fenómeno y pregunta  
- [docs/origen_datos.md](docs/origen_datos.md) — origen CSV  
- [docs/cleaning_log.md](docs/cleaning_log.md) — log de limpieza  
- [docs/modelo_relacional.md](docs/modelo_relacional.md) — ER de **4 tablas**  
- [docs/docker.md](docs/docker.md) — arquitectura Docker  
- [sql/schema.sql](sql/schema.sql) — schema MySQL  

## En otro PC (un solo comando)

Requisitos: [Docker Desktop](https://docs.docker.com/get-docker/) (Windows / macOS) o Docker Engine + Compose (Linux), con el motor en marcha.

```bash
git clone https://github.com/isabelnieto900/nudat3-decay-stability.git
cd nudat3-decay-stability
```

| Sistema | Arranque |
|---------|----------|
| **Linux / macOS / WSL / Git Bash** | `./run_app.sh` |
| **Windows PowerShell** | `.\run_app.ps1` |

El script crea `.env` desde `.env.example` si falta, descarga las imágenes de Docker Hub, levanta MySQL + Jupyter + Streamlit, carga `data/processed/` si la base está vacía y abre http://localhost:8501.

### Opciones

| Linux / macOS / WSL | Windows PowerShell | Efecto |
|---------------------|--------------------|--------|
| `--build` | `-Build` | Reconstruye las imágenes en local |
| `--reload-data` | `-ReloadData` | Fuerza la recarga de los CSV en MySQL |
| `--reset` | `-Reset` | Borra el volumen de MySQL y reconstruye |
| `--no-browser` | `-NoBrowser` | No abre el navegador |
| `--stop` | `-Stop` | Detiene los contenedores (conserva datos) |

### Solo con Docker Compose (cualquier SO)

Si prefieres no usar el script:

```bash
cp .env.example .env          # Windows CMD: copy .env.example .env
docker compose pull
docker compose up -d
docker compose exec jupyter python -m src.load_db
```

Luego abre http://localhost:8501

### Credenciales y puertos

Todo se configura en `.env` (plantilla: `.env.example`). Por defecto:

| Servicio | URL / puerto host | Acceso |
|----------|-------------------|--------|
| **streamlit** | http://localhost:8501 | — |
| **jupyter** | http://localhost:8888 | token `nudat` |
| **mysql** | localhost:**3307** | user/pass/db: `nudat` / `nudat` / `nudat` |

Dentro de la red Docker, las apps usan el hostname `mysql` (puerto 3306 interno).

### Imágenes en Docker Hub

| Imagen | Hub |
|--------|-----|
| Jupyter | [isabeln9/nudat3-jupyter](https://hub.docker.com/r/isabeln9/nudat3-jupyter) |
| Streamlit | [isabeln9/nudat3-streamlit](https://hub.docker.com/r/isabeln9/nudat3-streamlit) |
| MySQL | `mysql:8.0` (oficial) |

Reconstruir y publicar:

```bash
docker compose build
docker tag isabeln9/nudat3-streamlit:latest isabeln9/nudat3-streamlit:1.0.0
docker tag isabeln9/nudat3-jupyter:latest isabeln9/nudat3-jupyter:1.0.0
docker push isabeln9/nudat3-streamlit:1.0.0
docker push isabeln9/nudat3-streamlit:latest
docker push isabeln9/nudat3-jupyter:1.0.0
docker push isabeln9/nudat3-jupyter:latest
```

## Notebooks

1. [`notebooks/01_eda.ipynb`](notebooks/01_eda.ipynb) — exploración  
2. [`notebooks/02_clean_etl.ipynb`](notebooks/02_clean_etl.ipynb) — limpieza → `data/processed/`  
3. [`notebooks/02b_load_mysql.ipynb`](notebooks/02b_load_mysql.ipynb) — carga MySQL  
4. [`notebooks/03_analysis.ipynb`](notebooks/03_analysis.ipynb) — SQL + figuras N/Z–modo  

Consultas: [`sql/queries.sql`](sql/queries.sql)

## App Streamlit

Versión interactiva del análisis, consultando MySQL en vivo ([`app/`](app/)).

1. **Inicio** — pregunta, KPIs y nº de estados base por modo  
2. **Carta de nuclidos** — N–Z coloreado por modo o por $\log_{10} t_{1/2}$  
3. **N/Z por modo** — ⟨N/Z⟩ ± σ, histograma y caja/violín  
4. **Frontera y valle** — ⟨N/Z⟩ por bins de Z, valle de estables  
5. **Coulomb** — factor LDM $Z(Z-1)/A^{1/3}$ frente a ⟨N/Z⟩  
6. **Explorador** — nuclido, canales y tabla descargable  

Ejecución local (sin contenedor Streamlit): `pip install -r requirements.txt` y `streamlit run app/Inicio.py` (usa `MYSQL_HOST=127.0.0.1` y MySQL en el puerto host de `.env`).

## Datos

- `data/raw/` — Wallet Cards + Chart half-life (sin modificar)  
- `data/processed/` — limpios listos para MySQL  
