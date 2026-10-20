# Docker — MySQL + JupyterLab + Streamlit

## Arranque en otro PC

1. Instalar [Docker Desktop](https://docs.docker.com/get-docker/) (Windows/macOS) o Docker Engine + Compose (Linux).
2. Clonar el repo (hace falta el código y `data/processed/`).
3. Un comando:

| SO | Comando |
|----|---------|
| Linux / macOS / WSL / Git Bash | `./run_app.sh` |
| Windows PowerShell | `.\run_app.ps1` |

Sin script:

```bash
cp .env.example .env    # Windows: copy .env.example .env
docker compose pull
docker compose up -d
docker compose exec jupyter python -m src.load_db
```

## Variables de entorno

Plantilla: [`.env.example`](../.env.example). Copia a `.env` (no se sube a Git).

| Variable | Default | Uso |
|----------|---------|-----|
| `MYSQL_ROOT_PASSWORD` | `nudatroot` | root de MySQL |
| `MYSQL_USER` / `MYSQL_PASSWORD` / `MYSQL_DATABASE` | `nudat` | usuario de la app |
| `MYSQL_HOST` | `mysql` | DNS interno en Compose |
| `MYSQL_PORT` | `3306` | puerto **dentro** de la red |
| `MYSQL_HOST_PORT` | `3307` | puerto en tu PC (DBeaver, app local) |
| `JUPYTER_TOKEN` | `nudat` | token de JupyterLab |
| `JUPYTER_HOST_PORT` | `8888` | puerto host Jupyter |
| `STREAMLIT_HOST_PORT` | `8501` | puerto host Streamlit |

Compose sustituye `${VAR:-default}` al parsear el YAML. Los scripts leen `.env` para mensajes y la carga de datos.

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
         │ localhost:3307         │ localhost:8888   │ localhost:8501
      DBeaver / host           navegador          navegador
```

- Jupyter y Streamlit hablan con MySQL usando el hostname **`mysql`**.
- El schema se aplica en el **primer** arranque (volumen vacío) vía `sql/schema.sql`.
- Los datos (`INSERT`) se cargan con `src/load_db.py` (lo hacen `run_app.sh` / `run_app.ps1` si la BD está vacía).
- Para regenerar schema desde cero: `docker compose down -v` o `./run_app.sh --reset` / `.\run_app.ps1 -Reset`.

## Imágenes en Docker Hub

| Servicio | Imagen |
|----------|--------|
| mysql | `mysql:8.0` (oficial) |
| jupyter | [`isabeln9/nudat3-jupyter`](https://hub.docker.com/r/isabeln9/nudat3-jupyter) |
| streamlit | [`isabeln9/nudat3-streamlit`](https://hub.docker.com/r/isabeln9/nudat3-streamlit) |

En `docker-compose.yml` cada servicio custom tiene `image:` (Hub) y `build:` (reconstruir en local).

Publicar tras cambiar un Dockerfile:

```bash
docker compose build
docker tag isabeln9/nudat3-streamlit:latest isabeln9/nudat3-streamlit:1.0.0
docker tag isabeln9/nudat3-jupyter:latest isabeln9/nudat3-jupyter:1.0.0
docker login
docker push isabeln9/nudat3-streamlit:1.0.0 && docker push isabeln9/nudat3-streamlit:latest
docker push isabeln9/nudat3-jupyter:1.0.0 && docker push isabeln9/nudat3-jupyter:latest
```

## Archivos

| Archivo | Rol |
|---------|-----|
| `.env.example` | Plantilla de secretos y puertos |
| `.env` | Valores locales (gitignored) |
| `docker-compose.yml` | Servicios, red, volumen, `${VAR}` |
| `Dockerfile.jupyter` | Imagen Jupyter + SQLAlchemy/PyMySQL |
| `Dockerfile.streamlit` | App Streamlit (deps fijadas, USER, HEALTHCHECK) |
| `requirements-app.txt` | Dependencias de la imagen Streamlit |
| `run_app.sh` | Arranque Linux/macOS/WSL/Git Bash |
| `run_app.ps1` | Arranque Windows PowerShell |
| `sql/schema.sql` | Tablas + FK (init) |
| `src/load_db.py` | ETL processed → MySQL |
| `app/` | App Streamlit (consulta MySQL en vivo) |
