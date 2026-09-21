param([switch]$RemoveCache,[switch]$RemoveVenv)
$ErrorActionPreference = "Stop"
if (-not (Get-Command "wsl.exe" -ErrorAction SilentlyContinue)) { throw "WSL is required by the supported Windows installation path." }
$args = @("aips","uninstall")
if ($RemoveCache) { $args += "--remove-cache" }
if ($RemoveVenv) { $args += "--remove-venv" }
wsl.exe bash -lc ($args -join " ")
if ($LASTEXITCODE -ne 0) { throw "AIPS uninstall inside WSL failed." }
