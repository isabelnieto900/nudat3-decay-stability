# Docker — MySQL + JupyterLab

## Arquitectura

```text
┌─────────────────────────────────────────────┐
│  red Docker: nudat_net                      │
│                                             │
│  ┌──────────────┐      ┌─────────────────┐  │
│  │ nudat-mysql  │◄────►│ nudat-jupyter   │  │
│  │ :3306        │      │ :8888           │  │
│  │ vol mysql_data│     │ mount ./ → work │  │
│  └──────────────┘      └─────────────────┘  │
└─────────────────────────────────────────────┘
         ▲                        ▲
         │ localhost:3306         │ localhost:8888
      DBeaver / host           navegador
```

- Jupyter habla con MySQL usando el hostname **`mysql`** (DNS interno de Compose).
- El schema se aplica en el **primer** arranque (volumen vacío) vía `sql/schema.sql`.
- Para regenerar schema desde cero: `docker compose down -v` y volver a `up`.

## Arranque

1. Abrir **Docker Desktop** (el motor debe estar en ejecución).
2. En WSL, activar integración WSL2 o usar `docker.exe`.
3. En el repo:

```bash
docker compose up -d --build
docker compose ps
docker compose logs -f mysql   # opcional
```

4. Abrir http://localhost:8888/?token=nudat  
5. Cargar datos:

```bash
docker compose exec jupyter python -m src.load_db
```

## Archivos

| Archivo | Rol |
|---------|-----|
| `docker-compose.yml` | Servicios, red, volumen, env |
| `Dockerfile.jupyter` | Imagen Jupyter + SQLAlchemy/PyMySQL |
| `sql/schema.sql` | Tablas + FK (init) |
| `src/load_db.py` | ETL processed → MySQL |
| `notebooks/02b_load_mysql.ipynb` | Prueba de conexión y carga |
