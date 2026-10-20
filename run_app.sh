#!/usr/bin/env bash
# Arranca NuDat 3 (MySQL + JupyterLab + Streamlit) en Docker.
# Compatible: Linux, macOS, WSL, Git Bash en Windows.
#
# Uso:
#   ./run_app.sh                 pull + up + carga datos + abre la app
#   ./run_app.sh --build         reconstruye imágenes localmente
#   ./run_app.sh --reload-data   fuerza recarga de data/processed/ en MySQL
#   ./run_app.sh --reset         borra volumen MySQL y reconstruye desde cero
#   ./run_app.sh --no-browser    no abre el navegador
#   ./run_app.sh --stop          detiene contenedores (conserva datos)

set -euo pipefail

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
    -h|--help) sed -n '2,12p' "$0" | sed 's/^# \{0,1\}//'; exit 0 ;;
    *) echo "Opción desconocida: $arg (usa --help)"; exit 1 ;;
  esac
done

info() { printf '\n\033[1;34m==>\033[0m %s\n' "$*"; }
ok()   { printf '\033[1;32m✔\033[0m %s\n' "$*"; }
fail() { printf '\033[1;31m✘ %s\033[0m\n' "$*" >&2; exit 1; }

is_wsl() { grep -qi microsoft /proc/version 2>/dev/null; }
is_macos() { [ "$(uname -s 2>/dev/null)" = "Darwin" ]; }

# Cliente docker usable: CLI de WSL o docker.exe de Docker Desktop (Windows).
resolve_docker_cli() {
  if command -v docker >/dev/null 2>&1; then
    DOCKER_CLI=(docker)
    return 0
  fi
  local exe
  for exe in \
    /mnt/c/Users/*/AppData/Local/Programs/DockerDesktop/resources/bin/docker.exe \
    "/mnt/c/Program Files/Docker/Docker/resources/bin/docker.exe"
  do
    if [ -f "$exe" ]; then
      DOCKER_CLI=("$exe")
      return 0
    fi
  done
  DOCKER_CLI=()
  return 1
}

docker_engine_up() {
  resolve_docker_cli || return 1
  "${DOCKER_CLI[@]}" info >/dev/null 2>&1
}

# Convierte /mnt/c/Users/... → C:\Users\...
wsl_path_to_win() {
  local p="$1"
  if [[ "$p" =~ ^/mnt/([a-zA-Z])/(.*)$ ]]; then
    local drive rest
    drive="$(printf '%s' "${BASH_REMATCH[1]}" | tr '[:lower:]' '[:upper:]')"
    rest="${BASH_REMATCH[2]//\//\\}"
    printf '%s:\\%s' "$drive" "$rest"
    return 0
  fi
  return 1
}

# Lanza Docker Desktop en la sesión de Windows (Start-Process / cmd start).
# Llamar el .exe desde bash a menudo no abre la GUI en WSL.
start_docker_desktop_windows() {
  local desktop="" win_path=""

  # 1) Instalación por usuario (AppData) — caso típico actual
  for candidate in /mnt/c/Users/*/AppData/Local/Programs/DockerDesktop/"Docker Desktop.exe"; do
    if [ -f "$candidate" ]; then
      desktop="$candidate"
      break
    fi
  done

  # 2) Instalación clásica en Program Files
  if [ -z "$desktop" ]; then
    for candidate in \
      "/mnt/c/Program Files/Docker/Docker/Docker Desktop.exe" \
      "/mnt/c/Program Files (x86)/Docker/Docker/Docker Desktop.exe"
    do
      if [ -f "$candidate" ]; then
        desktop="$candidate"
        break
      fi
    done
  fi

  # 3) Preguntar a Windows (LOCALAPPDATA / ProgramFiles)
  if [ -z "$desktop" ] && command -v powershell.exe >/dev/null 2>&1; then
    win_path="$(
      powershell.exe -NoProfile -Command '
        $cands = @(
          (Join-Path $env:LOCALAPPDATA "Programs\DockerDesktop\Docker Desktop.exe"),
          (Join-Path $env:ProgramFiles "Docker\Docker\Docker Desktop.exe")
        )
        foreach ($p in $cands) { if (Test-Path -LiteralPath $p) { Write-Output $p; break } }
      ' 2>/dev/null | tr -d '\r' | head -n1
    )"
    if [ -n "$win_path" ]; then
      # Preferir Start-Process con esa ruta Windows
      if powershell.exe -NoProfile -Command "Start-Process -FilePath '$win_path'" >/dev/null 2>&1; then
        ok "Docker Desktop lanzado ($win_path)"
        return 0
      fi
    fi
  fi

  if [ -z "$desktop" ]; then
    return 1
  fi

  win_path="$(wsl_path_to_win "$desktop")" || win_path=""

  # Preferir Start-Process en la sesión de usuario de Windows
  if [ -n "$win_path" ] && command -v powershell.exe >/dev/null 2>&1; then
    if powershell.exe -NoProfile -Command "Start-Process -FilePath '$win_path'" >/dev/null 2>&1; then
      ok "Docker Desktop lanzado ($win_path)"
      return 0
    fi
  fi

  # Fallback: cmd start (también crea proceso en Windows, no en WSL)
  if [ -n "$win_path" ] && command -v cmd.exe >/dev/null 2>&1; then
    if cmd.exe /c start "" "$win_path" >/dev/null 2>&1; then
      ok "Docker Desktop lanzado vía cmd ($win_path)"
      return 0
    fi
  fi

  return 1
}

# Intenta arrancar el motor si no responde (Docker Desktop o systemd).
start_docker_engine() {
  info "El motor de Docker no responde; intentando iniciarlo"

  if is_wsl || { command -v powershell.exe >/dev/null 2>&1 && command -v cmd.exe >/dev/null 2>&1; }; then
    if start_docker_desktop_windows; then
      # Arrancar también el servicio de Windows si está detenido (ayuda al motor)
      if command -v powershell.exe >/dev/null 2>&1; then
        powershell.exe -NoProfile -Command \
          "try { Start-Service com.docker.service -ErrorAction SilentlyContinue } catch {}" \
          >/dev/null 2>&1 || true
      fi
      return 0
    fi
    if is_wsl; then
      fail "No se encontró Docker Desktop (Program Files ni AppData\\\\Local\\\\Programs\\\\DockerDesktop). Instálalo: https://docs.docker.com/desktop/wsl/"
    fi
  fi

  if is_macos; then
    if [ -d "/Applications/Docker.app" ]; then
      open -a Docker
      ok "Docker Desktop lanzado (macOS)"
      return 0
    fi
    fail "No se encontró Docker.app en /Applications. Instala Docker Desktop."
  fi

  # Linux nativo: servicio systemd
  if command -v systemctl >/dev/null 2>&1; then
    if systemctl is-active --quiet docker 2>/dev/null; then
      return 0
    fi
    if systemctl start docker 2>/dev/null; then
      ok "Servicio docker iniciado (systemctl)"
      return 0
    fi
    if command -v sudo >/dev/null 2>&1 && sudo -n systemctl start docker 2>/dev/null; then
      ok "Servicio docker iniciado (sudo systemctl)"
      return 0
    fi
    if command -v sudo >/dev/null 2>&1 && sudo systemctl start docker; then
      ok "Servicio docker iniciado (sudo systemctl)"
      return 0
    fi
  fi

  if command -v service >/dev/null 2>&1; then
    if service docker start 2>/dev/null || sudo service docker start 2>/dev/null; then
      ok "Servicio docker iniciado (service)"
      return 0
    fi
  fi

  fail "No se pudo iniciar Docker automáticamente. Ábrelo a mano e inténtalo de nuevo."
}

wait_for_docker_engine() {
  local timeout_s="${1:-180}"
  local elapsed=0
  info "Esperando a que el motor de Docker esté listo (hasta ${timeout_s}s)"
  until docker_engine_up; do
    if [ "$elapsed" -ge "$timeout_s" ]; then
      fail "Docker no respondió en ${timeout_s}s. Si usas WSL, activa Settings → Resources → WSL integration para esta distro."
    fi
    sleep 3
    elapsed=$((elapsed + 3))
    printf '  … %ss\n' "$elapsed"
  done
  # Preferir el CLI de Linux cuando ya esté inyectado por Desktop
  if command -v docker >/dev/null 2>&1; then
    DOCKER_CLI=(docker)
  fi
  ok "Motor de Docker listo"
}

# --- 0. .env ------------------------------------------------------------------
if [ ! -f .env ]; then
  if [ -f .env.example ]; then
    info "Creando .env desde .env.example"
    cp .env.example .env
    ok ".env creado (puedes editar contraseñas y puertos)"
  else
    fail "Falta .env y .env.example. Restaura .env.example desde el repo."
  fi
fi

# Cargar .env (compatible con finales de línea CRLF de Windows)
while IFS= read -r line || [ -n "$line" ]; do
  line="${line%$'\r'}"
  [[ -z "$line" || "$line" == \#* ]] && continue
  key="${line%%=*}"
  val="${line#*=}"
  # trim espacios
  key="$(printf '%s' "$key" | sed 's/^[[:space:]]*//;s/[[:space:]]*$//')"
  val="$(printf '%s' "$val" | sed 's/^[[:space:]]*//;s/[[:space:]]*$//')"
  [[ -z "$key" ]] && continue
  if [[ "${val:0:1}" == '"' && "${val: -1}" == '"' ]]; then val="${val:1:-1}"; fi
  if [[ "${val:0:1}" == "'" && "${val: -1}" == "'" ]]; then val="${val:1:-1}"; fi
  export "$key=$val"
done < .env

MYSQL_USER="${MYSQL_USER:-nudat}"
MYSQL_PASSWORD="${MYSQL_PASSWORD:-nudat}"
MYSQL_DATABASE="${MYSQL_DATABASE:-nudat}"
MYSQL_HOST_PORT="${MYSQL_HOST_PORT:-3307}"
JUPYTER_TOKEN="${JUPYTER_TOKEN:-nudat}"
JUPYTER_HOST_PORT="${JUPYTER_HOST_PORT:-8888}"
STREAMLIT_HOST_PORT="${STREAMLIT_HOST_PORT:-8501}"

APP_URL="http://localhost:${STREAMLIT_HOST_PORT}"
JUPYTER_URL="http://localhost:${JUPYTER_HOST_PORT}/?token=${JUPYTER_TOKEN}"

# --- 1. Docker disponible -----------------------------------------------------
info "Comprobando Docker"
if ! docker_engine_up; then
  if ! resolve_docker_cli && ! is_wsl && ! is_macos; then
    fail "No se encuentra 'docker'. Instala Docker Engine o Docker Desktop: https://docs.docker.com/get-docker/"
  fi
  start_docker_engine
  wait_for_docker_engine 180
fi

resolve_docker_cli || fail "No se encuentra el cliente 'docker' tras iniciar el motor."

# Preferir CLI de Linux (integración WSL); si no, docker.exe de Windows
if command -v docker >/dev/null 2>&1 && docker info >/dev/null 2>&1; then
  DOCKER_CLI=(docker)
fi

if "${DOCKER_CLI[@]}" compose version >/dev/null 2>&1; then
  compose=("${DOCKER_CLI[@]}" compose)
elif command -v docker-compose >/dev/null 2>&1; then
  compose=(docker-compose)
else
  fail "No se encuentra Docker Compose (docker compose)."
fi

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
until [ "$("${DOCKER_CLI[@]}" inspect -f '{{.State.Health.Status}}' nudat-mysql 2>/dev/null)" = "healthy" ]; do
  [ "$elapsed" -ge "$TIMEOUT_S" ] && fail "MySQL no respondió en ${TIMEOUT_S}s. Revisa: ${compose[*]} logs mysql"
  sleep 3; elapsed=$((elapsed + 3))
done
ok "MySQL healthy"

# --- 4. Cargar datos si la base está vacía -----------------------------------
n_states=$("${compose[@]}" exec -T -e "MYSQL_PWD=${MYSQL_PASSWORD}" mysql \
  mysql -u"${MYSQL_USER}" -N -B "${MYSQL_DATABASE}" -e "SELECT COUNT(*) FROM nuclear_state" 2>/dev/null || echo 0)
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
  "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8501/_stcore/health', timeout=3)" \
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
  elif is_macos && command -v open >/dev/null 2>&1; then
    open "$APP_URL" || true
  elif command -v xdg-open >/dev/null 2>&1; then
    xdg-open "$APP_URL" >/dev/null 2>&1 || true
  elif command -v open >/dev/null 2>&1; then
    open "$APP_URL" || true
  elif command -v powershell.exe >/dev/null 2>&1; then
    # Git Bash en Windows nativo
    powershell.exe -NoProfile -Command "Start-Process '$APP_URL'" >/dev/null 2>&1 || true
  fi
fi

cat <<EOF

  App Streamlit : $APP_URL
  JupyterLab    : $JUPYTER_URL
  MySQL         : localhost:${MYSQL_HOST_PORT}  (${MYSQL_USER} / ***, base ${MYSQL_DATABASE})

  Imágenes Hub  : isabeln9/nudat3-jupyter , isabeln9/nudat3-streamlit
  Detener todo  : ./run_app.sh --stop
EOF
