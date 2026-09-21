param([switch]$DryRun)
$ErrorActionPreference = "Stop"
$InstallerUrl = if ($env:AIPS_INSTALL_URL) { $env:AIPS_INSTALL_URL } else { "https://raw.githubusercontent.com/LucasLu3918/ai-product-system/main/scripts/install.sh" }
if (-not (Get-Command "wsl.exe" -ErrorAction SilentlyContinue)) { throw "WSL is required by the supported Windows installation path." }
if ($DryRun) {
  Write-Output "AIPS Windows installation mode: WSL"
  Write-Output "installer=$InstallerUrl"
  Write-Output "AIPS is installed inside the selected WSL distribution."
  exit 0
}
$escaped = $InstallerUrl.Replace("'","'\\''")
wsl.exe bash -lc "command -v curl >/dev/null && curl -fsSL '$escaped' | bash"
if ($LASTEXITCODE -ne 0) { throw "AIPS installation inside WSL failed." }
Write-Output "AIPS installed inside WSL. Open your WSL terminal and run: aips doctor"
