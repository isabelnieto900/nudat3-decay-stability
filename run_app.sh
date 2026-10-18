#!/usr/bin/env bash
# Instala y abre la app NuDat 3 (MySQL + JupyterLab + Streamlit en Docker).
#
# Uso:
#   ./run_app.sh                 baja imágenes de Docker Hub, levanta, carga datos y abre la app
#   ./run_app.sh --build         reconstruye las imágenes localmente (en vez de solo pull)
#   ./run_app.sh --reload-data   fuerza la recarga de data/processed/ en MySQL
#   ./run_app.sh --reset         borra el volumen de MySQL y reconstruye todo desde cero
#   ./run_app.sh --no-browser    no abre el navegador
#   ./run_app.sh --stop          detiene los contenedores (los datos se conservan)

set -euo pipefail

APP_URL="http://localhost:8501"
JUPYTER_URL="http://localhost:8888/?token=nudat"
TIMEOUT_S=180

cd "$(dirname "$0")"

reload_data=false
reset=false
open_browser=true
stop=false
do_build=false

for arg in "$@"; do
  case "$arg" in
    --reload-data) reload_data=true ;;
    --reset) reset=true ;;
    --no-browser) open_browser=false ;;
    --stop) stop=true ;;
    --build) do_build=true ;;
    -h|--help) sed -n '2,10p' "$0" | sed 's/^# \{0,1\}//'; exit 0 ;;
    *) echo "Opción desconocida: $arg (usa --help)"; exit 1 ;;
  esac
done

info() { printf '\n\033[1;34m==>\033[0m %s\n' "$*"; }
ok()   { printf '\033[1;32m✔\033[0m %s\n' "$*"; }
fail() { printf '\033[1;31m✘ %s\033[0m\n' "$*" >&2; exit 1; }

is_wsl() { grep -qi microsoft /proc/version 2>/dev/null; }

# --- 1. Docker disponible ---------------------------------------------------
info "Comprobando Docker"
if ! command -v docker >/dev/null 2>&1; then
  if is_wsl; then
    fail "No se encuentra 'docker'. Abre Docker Desktop y activa la integración WSL (Settings > Resources > WSL integration)."
  fi
  fail "No se encuentra 'docker'. Instala Docker Desktop o Docker Engine: https://docs.docker.com/get-docker/"
fi

if docker compose version >/dev/null 2>&1; then
  compose=(docker compose)
elif command -v docker-compose >/dev/null 2>&1; then
  compose=(docker-compose)
else
  fail "No se encuentra Docker Compose (docker compose)."
fi

docker info >/dev/null 2>&1 || fail "El motor de Docker no está en ejecución. Abre Docker Desktop y vuelve a intentarlo."
ok "Docker listo ($("${compose[@]}" version --short 2>/dev/null || echo compose))"

if $stop; then
  info "Deteniendo contenedores"
  "${compose[@]}" down
  ok "Contenedores detenidos (los datos de MySQL se conservan en el volumen)."
  exit 0
fi

# --- 2. Imágenes y contenedores ----------------------------------------------
if $reset; then
  info "Reset: eliminando contenedores y volumen de MySQL"
  "${compose[@]}" down -v
  reload_data=true
fi

if $do_build; then
  info "Construyendo imágenes localmente y levantando contenedores"
  "${compose[@]}" up -d --build
else
  info "Descargando imágenes de Docker Hub (isabeln9/nudat3-*)"
  if ! "${compose[@]}" pull; then
    info "Pull falló; construyendo localmente como respaldo"
    "${compose[@]}" up -d --build
  else
    info "Levantando contenedores"
    "${compose[@]}" up -d
  fi
fi

# --- 3. Esperar a MySQL -------------------------------------------------------
info "Esperando a que MySQL esté listo"
elapsed=0
until [ "$(docker inspect -f '{{.State.Health.Status}}' nudat-mysql 2>/dev/null)" = "healthy" ]; do
  [ "$elapsed" -ge "$TIMEOUT_S" ] && fail "MySQL no respondió en ${TIMEOUT_S}s. Revisa: ${compose[*]} logs mysql"
  sleep 3; elapsed=$((elapsed + 3))
done
ok "MySQL healthy"

# --- 4. Cargar datos si la base está vacía -----------------------------------
n_states=$("${compose[@]}" exec -T -e MYSQL_PWD=nudat mysql \
  mysql -unudat -N -B nudat -e "SELECT COUNT(*) FROM nuclear_state" 2>/dev/null || echo 0)
n_states=${n_states//[^0-9]/}

if $reload_data || [ "${n_states:-0}" -eq 0 ]; then
  info "Cargando data/processed/ en MySQL (src/load_db.py)"
  "${compose[@]}" exec -T jupyter python -m src.load_db
  ok "Datos cargados"
else
  ok "La base ya tiene datos (${n_states} estados nucleares); no se recarga. Usa --reload-data para forzarlo."
fi

# --- 5. Esperar a Streamlit ---------------------------------------------------
info "Esperando a que la app Streamlit responda"
elapsed=0
until "${compose[@]}" exec -T streamlit python -c \
  "import urllib.request; urllib.request.urlopen('http://localhost:8501/_stcore/health', timeout=3)" \
  >/dev/null 2>&1; do
  [ "$elapsed" -ge "$TIMEOUT_S" ] && fail "Streamlit no respondió en ${TIMEOUT_S}s. Revisa: ${compose[*]} logs streamlit"
  sleep 3; elapsed=$((elapsed + 3))
done
ok "App lista"

# --- 6. Abrir el navegador ---------------------------------------------------
if $open_browser; then
  info "Abriendo $APP_URL"
  if is_wsl; then
    cmd.exe /c start "" "$APP_URL" >/dev/null 2>&1 || true
  elif command -v xdg-open >/dev/null 2>&1; then
    xdg-open "$APP_URL" >/dev/null 2>&1 || true
  elif command -v open >/dev/null 2>&1; then
    open "$APP_URL" || true
  fi
fi

cat <<EOF

  App Streamlit : $APP_URL
  JupyterLab    : $JUPYTER_URL
  MySQL         : localhost:3306  (nudat / nudat, base nudat)

  Imágenes Hub  : isabeln9/nudat3-jupyter , isabeln9/nudat3-streamlit
  Detener todo  : ./run_app.sh --stop
EOF
