param(
  [Parameter(Mandatory = $true, Position = 0)]
  [string]$ScriptPath,

  [Parameter(ValueFromRemainingArguments = $true)]
  [string[]]$ScriptArgs
)

$candidates = @()

$localPython = Join-Path $env:LOCALAPPDATA "Programs\Python"
if (Test-Path $localPython) {
  $candidates += Get-ChildItem $localPython -Recurse -Filter python.exe -ErrorAction SilentlyContinue |
    Where-Object { $_.FullName -notlike "*WindowsApps*" } |
    Select-Object -ExpandProperty FullName
}

$cmd = Get-Command python -ErrorAction SilentlyContinue
if ($cmd -and $cmd.Source -notlike "*WindowsApps*") {
  $candidates += $cmd.Source
}

$pythonExe = $candidates | Select-Object -First 1
if (-not $pythonExe) {
  throw "No real python.exe found. Install Python or update scripts/run_python.ps1."
}

& $pythonExe $ScriptPath @ScriptArgs
exit $LASTEXITCODE
