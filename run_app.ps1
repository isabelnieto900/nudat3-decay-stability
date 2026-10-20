# Arranca NuDat 3 (MySQL + JupyterLab + Streamlit) en Docker.
# Compatible: Windows PowerShell 5+ / PowerShell 7 (Docker Desktop).
#
# Uso:
#   .\run_app.ps1
#   .\run_app.ps1 -Build
#   .\run_app.ps1 -ReloadData
#   .\run_app.ps1 -Reset
#   .\run_app.ps1 -NoBrowser
#   .\run_app.ps1 -Stop

[CmdletBinding()]
param(
    [switch]$Build,
    [switch]$ReloadData,
    [switch]$Reset,
    [switch]$NoBrowser,
    [switch]$Stop
)

$ErrorActionPreference = "Stop"
$TimeoutS = 180

Set-Location -Path $PSScriptRoot

function Write-Info([string]$Message) { Write-Host "`n==> $Message" -ForegroundColor Cyan }
function Write-Ok([string]$Message)   { Write-Host "OK  $Message" -ForegroundColor Green }
function Write-Fail([string]$Message) {
    Write-Host "ERR $Message" -ForegroundColor Red
    exit 1
}

function Get-DotEnv {
    param([string]$Path)
    $map = @{}
    if (-not (Test-Path $Path)) { return $map }
    Get-Content -Path $Path -Encoding UTF8 | ForEach-Object {
        $line = $_.Trim()
        if ($line -eq "" -or $line.StartsWith("#")) { return }
        $idx = $line.IndexOf("=")
        if ($idx -lt 1) { return }
        $key = $line.Substring(0, $idx).Trim()
        $val = $line.Substring($idx + 1).Trim()
        if (($val.StartsWith('"') -and $val.EndsWith('"')) -or ($val.StartsWith("'") -and $val.EndsWith("'"))) {
            $val = $val.Substring(1, $val.Length - 2)
        }
        $map[$key] = $val
    }
    return $map
}

function Invoke-Compose {
    param([Parameter(ValueFromRemainingArguments = $true)][string[]]$ComposeArgs)
    & docker @("compose") @ComposeArgs
    if ($LASTEXITCODE -ne 0) {
        throw "docker compose $($ComposeArgs -join ' ') falló (código $LASTEXITCODE)"
    }
}

# --- 0. .env ------------------------------------------------------------------
if (-not (Test-Path ".env")) {
    if (Test-Path ".env.example") {
        Write-Info "Creando .env desde .env.example"
        Copy-Item ".env.example" ".env"
        Write-Ok ".env creado (puedes editar contraseñas y puertos)"
    }
    else {
        Write-Fail "Falta .env y .env.example. Restaura .env.example desde el repo."
    }
}

$envMap = Get-DotEnv ".env"
function EnvOr([string]$Key, [string]$Default) {
    if ($envMap.ContainsKey($Key) -and $envMap[$Key]) { return $envMap[$Key] }
    return $Default
}

$MysqlUser = EnvOr "MYSQL_USER" "nudat"
$MysqlPassword = EnvOr "MYSQL_PASSWORD" "nudat"
$MysqlDatabase = EnvOr "MYSQL_DATABASE" "nudat"
$MysqlHostPort = EnvOr "MYSQL_HOST_PORT" "3307"
$JupyterToken = EnvOr "JUPYTER_TOKEN" "nudat"
$JupyterHostPort = EnvOr "JUPYTER_HOST_PORT" "8888"
$StreamlitHostPort = EnvOr "STREAMLIT_HOST_PORT" "8501"

$AppUrl = "http://localhost:$StreamlitHostPort"
$JupyterUrl = "http://localhost:$JupyterHostPort/?token=$JupyterToken"

# --- 1. Docker ----------------------------------------------------------------
Write-Info "Comprobando Docker"
if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
    Write-Fail "No se encuentra 'docker'. Instala Docker Desktop: https://docs.docker.com/get-docker/"
}

docker info 1>$null 2>$null
if ($LASTEXITCODE -ne 0) {
    Write-Fail "El motor de Docker no está en ejecución. Abre Docker Desktop y reintenta."
}

docker compose version 1>$null 2>$null
if ($LASTEXITCODE -ne 0) {
    Write-Fail "No se encuentra Docker Compose (docker compose)."
}
Write-Ok "Docker listo"

if ($Stop) {
    Write-Info "Deteniendo contenedores"
    Invoke-Compose down
    Write-Ok "Contenedores detenidos (los datos de MySQL se conservan en el volumen)."
    exit 0
}

# --- 2. Up --------------------------------------------------------------------
if ($Reset) {
    Write-Info "Reset: eliminando contenedores y volumen de MySQL"
    Invoke-Compose down -v
    $ReloadData = $true
}

if ($Build) {
    Write-Info "Construyendo imágenes localmente y levantando contenedores"
    Invoke-Compose up -d --build
}
else {
    Write-Info "Descargando imágenes de Docker Hub (isabeln9/nudat3-*)"
    docker compose pull
    if ($LASTEXITCODE -ne 0) {
        Write-Info "Pull falló; construyendo localmente como respaldo"
        Invoke-Compose up -d --build
    }
    else {
        Write-Info "Levantando contenedores"
        Invoke-Compose up -d
    }
}

# --- 3. Esperar MySQL ---------------------------------------------------------
Write-Info "Esperando a que MySQL esté listo"
$elapsed = 0
while ($true) {
    $status = docker inspect -f "{{.State.Health.Status}}" nudat-mysql 2>$null
    if ($status -eq "healthy") { break }
    if ($elapsed -ge $TimeoutS) {
        Write-Fail "MySQL no respondió en ${TimeoutS}s. Revisa: docker compose logs mysql"
    }
    Start-Sleep -Seconds 3
    $elapsed += 3
}
Write-Ok "MySQL healthy"

# --- 4. Cargar datos ----------------------------------------------------------
$countOut = docker compose exec -T -e "MYSQL_PWD=$MysqlPassword" mysql `
    mysql -u"$MysqlUser" -N -B "$MysqlDatabase" -e "SELECT COUNT(*) FROM nuclear_state" 2>$null
if ($LASTEXITCODE -ne 0 -or [string]::IsNullOrWhiteSpace($countOut)) {
    $nStates = 0
}
else {
    $digits = ($countOut | Out-String) -replace "[^0-9]", ""
    if ([string]::IsNullOrWhiteSpace($digits)) { $nStates = 0 } else { $nStates = [int]$digits }
}

if ($ReloadData -or $nStates -eq 0) {
    Write-Info "Cargando data/processed/ en MySQL (src/load_db.py)"
    Invoke-Compose exec -T jupyter python -m src.load_db
    Write-Ok "Datos cargados"
}
else {
    Write-Ok "La base ya tiene datos ($nStates estados nucleares); no se recarga. Usa -ReloadData para forzarlo."
}

# --- 5. Esperar Streamlit -----------------------------------------------------
Write-Info "Esperando a que la app Streamlit responda"
$elapsed = 0
$healthPy = "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8501/_stcore/health', timeout=3)"
while ($true) {
    docker compose exec -T streamlit python -c $healthPy 1>$null 2>$null
    if ($LASTEXITCODE -eq 0) { break }
    if ($elapsed -ge $TimeoutS) {
        Write-Fail "Streamlit no respondió en ${TimeoutS}s. Revisa: docker compose logs streamlit"
    }
    Start-Sleep -Seconds 3
    $elapsed += 3
}
Write-Ok "App lista"

# --- 6. Navegador -------------------------------------------------------------
if (-not $NoBrowser) {
    Write-Info "Abriendo $AppUrl"
    try { Start-Process $AppUrl } catch { }
}

Write-Host ""
Write-Host "  App Streamlit : $AppUrl"
Write-Host "  JupyterLab    : $JupyterUrl"
Write-Host "  MySQL         : localhost:$MysqlHostPort  ($MysqlUser / ***, base $MysqlDatabase)"
Write-Host ""
Write-Host "  Imágenes Hub  : isabeln9/nudat3-jupyter , isabeln9/nudat3-streamlit"
Write-Host "  Detener todo  : .\run_app.ps1 -Stop"
Write-Host ""
