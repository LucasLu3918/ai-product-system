$ErrorActionPreference = "Stop"
$root = (Resolve-Path (Join-Path $PSScriptRoot "../..")).Path
$files = @(
  (Join-Path $root "README.md"),
  (Join-Path $root "docs/human/INSTALLATION.md"),
  (Join-Path $root "docs/human/GETTING_STARTED.md")
)
$snippets = foreach ($file in $files) {
  $text = [IO.File]::ReadAllText($file).Replace("`r`n", "`n")
  $match = [regex]::Match($text, '(?s)~~~powershell\n(.*?)\n~~~')
  if (-not $match.Success) { throw "Missing PowerShell install snippet: $file" }
  $match.Groups[1].Value
}
if (@($snippets | Select-Object -Unique).Count -ne 1) { throw "PowerShell install snippets differ" }

function Invoke-WebRequest {
  [CmdletBinding()]
  param([string]$Uri, [string]$OutFile)
  $script:lastOutFile = $OutFile
  switch ($script:mode) {
    "fail" { throw "fixture download failed" }
    "empty" { [IO.File]::WriteAllText($OutFile, "") }
    "child_fail" { [IO.File]::WriteAllText($OutFile, 'throw "fixture child failed"') }
    "success" { [IO.File]::WriteAllText($OutFile, '$script:childRan = $true') }
    default { throw "Unknown fixture mode" }
  }
}

foreach ($test in @(
  @{ Mode = "fail"; Success = $false },
  @{ Mode = "empty"; Success = $false },
  @{ Mode = "child_fail"; Success = $false },
  @{ Mode = "success"; Success = $true }
)) {
  $script:mode = $test.Mode
  $script:childRan = $false
  $script:lastOutFile = $null
  $succeeded = $true
  try { Invoke-Expression $snippets[0] } catch { $succeeded = $false }
  if ($succeeded -ne $test.Success) { throw "Unexpected install result for $($test.Mode)" }
  if ($test.Success -and -not $script:childRan) { throw "Installer did not run" }
  if ($script:lastOutFile -and (Test-Path -LiteralPath $script:lastOutFile)) {
    throw "Temporary installer was not removed after $($test.Mode)"
  }
}

Write-Output "install_download_contract evidence: PASS"
