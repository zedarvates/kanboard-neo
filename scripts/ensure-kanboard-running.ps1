[CmdletBinding()]
param(
    [string]$HealthUrl = $(if ($env:KANBOARD_HEALTH_URL) { $env:KANBOARD_HEALTH_URL } else { "http://127.0.0.1/healthcheck.php" }),
    [string]$ComposeFile = $(if ($env:KANBOARD_COMPOSE_FILE) { $env:KANBOARD_COMPOSE_FILE } else { Join-Path $PSScriptRoot "..\docker-compose.sqlite.yml" })
)

$ErrorActionPreference = "Stop"

function Test-KanboardHealth {
    try {
        $response = Invoke-WebRequest -Uri $HealthUrl -UseBasicParsing -TimeoutSec 3
        return $response.StatusCode -eq 200
    }
    catch {
        return $false
    }
}

if (Test-KanboardHealth) {
    Write-Host "Kanboard Neo is already healthy."
    exit 0
}

if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
    Write-Error "Docker is unavailable; Kanboard Neo was not started."
    exit 1
}

Write-Host "Kanboard Neo is stopped; starting the existing Compose stack."
docker compose -f $ComposeFile up -d
if ($LASTEXITCODE -ne 0) {
    Write-Error "Docker Compose failed to start Kanboard Neo."
    exit $LASTEXITCODE
}

for ($attempt = 0; $attempt -lt 20; $attempt++) {
    if (Test-KanboardHealth) {
        Write-Host "Kanboard Neo is healthy."
        exit 0
    }
    Start-Sleep -Seconds 1
}

Write-Error "Kanboard Neo did not become healthy within 20 seconds."
exit 1
