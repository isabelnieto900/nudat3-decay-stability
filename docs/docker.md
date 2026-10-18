# Docker — MySQL + JupyterLab + Streamlit

## Arquitectura

```text
┌──────────────────────────────────────────────────────────────┐
│  red Docker: nudat_net                                       │
│                                                              │
│  ┌──────────────┐      ┌─────────────────┐                   │
│  │ nudat-mysql  │◄────►│ nudat-jupyter   │                   │
│  │ :3306        │      │ :8888           │                   │
│  │ vol mysql_data│     │ mount ./ → work │                   │
│  └──────────────┘      └─────────────────┘                   │
│         ▲                                                    │
│         │              ┌─────────────────┐                   │
│         └─────────────►│ nudat-streamlit │                   │
│                        │ :8501           │                   │
│                        │ mount ./ → app  │                   │
│                        └─────────────────┘                   │
└──────────────────────────────────────────────────────────────┘
         ▲                        ▲                  ▲
         │ localhost:3306         │ localhost:8888   │ localhost:8501
      DBeaver / host           navegador          navegador
```

- Jupyter y Streamlit hablan con MySQL usando el hostname **`mysql`** (DNS interno de Compose).
- El schema se aplica en el **primer** arranque (volumen vacío) vía `sql/schema.sql`.
- Para regenerar schema desde cero: `docker compose down -v` y volver a `up`.
- El código y `data/processed/` se montan desde el clone de Git; las imágenes de Hub traen el entorno (Python + librerías).

## Imágenes en Docker Hub

| Servicio | Imagen |
|----------|--------|
| mysql | `mysql:8.0` (oficial) |
| jupyter | [`isabeln9/nudat3-jupyter`](https://hub.docker.com/r/isabeln9/nudat3-jupyter) |
| streamlit | [`isabeln9/nudat3-streamlit`](https://hub.docker.com/r/isabeln9/nudat3-streamlit) |

En `docker-compose.yml` cada servicio custom tiene `image:` (Hub) y `build:` (reconstruir en local). Por defecto se usa el pull.

Publicar de nuevo tras cambiar un Dockerfile:

```bash
docker build -f Dockerfile.streamlit -t isabeln9/nudat3-streamlit:latest .
docker build -f Dockerfile.jupyter -t isabeln9/nudat3-jupyter:latest .
docker login
docker push isabeln9/nudat3-streamlit:latest
docker push isabeln9/nudat3-jupyter:latest
```

## Arranque

1. Abrir **Docker Desktop** (el motor debe estar en ejecución).
2. En WSL, activar integración WSL2 o usar `docker.exe`.
3. En el repo:

```bash
./run_app.sh
# o manualmente:
docker compose pull
docker compose up -d
docker compose ps
```

4. Abrir http://localhost:8888/?token=nudat  
5. Cargar datos (si `./run_app.sh` no lo hizo ya):

```bash
docker compose exec jupyter python -m src.load_db
```

6. Abrir la app interactiva: http://localhost:8501 (si la BD está vacía, la app lo indica).

## Archivos

| Archivo | Rol |
|---------|-----|
| `docker-compose.yml` | Servicios, red, volumen, env + nombres de Hub |
| `Dockerfile.jupyter` | Imagen Jupyter + SQLAlchemy/PyMySQL |
| `Dockerfile.streamlit` | Imagen Python + Streamlit/Plotly para `app/` |
| `run_app.sh` | Pull/up + carga de datos + abrir navegador |
| `sql/schema.sql` | Tablas + FK (init) |
| `src/load_db.py` | ETL processed → MySQL |
| `notebooks/02b_load_mysql.ipynb` | Prueba de conexión y carga |
| `app/` | App Streamlit (consulta MySQL en vivo) |
