param(
    [switch]$OpenBrowser,
    [string]$HostAddress = '192.168.56.1'
)

$ErrorActionPreference = 'Stop'

$projectDirectory = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location -LiteralPath $projectDirectory

$pythonCandidates = [System.Collections.Generic.List[object]]::new()
$localVirtualEnvironment = Join-Path $projectDirectory '.venv\Scripts\python.exe'
if (Test-Path -LiteralPath $localVirtualEnvironment) {
    $pythonCandidates.Add([pscustomobject]@{ Path = $localVirtualEnvironment; Arguments = @(); Label = 'entorno virtual del proyecto' })
}

foreach ($commandName in @('py', 'python', 'python3')) {
    $resolvedCommand = Get-Command $commandName -ErrorAction SilentlyContinue
    if ($null -ne $resolvedCommand -and $resolvedCommand.Source -notlike '*\Microsoft\WindowsApps\*') {
        $prefixArguments = if ($commandName -eq 'py') { @('-3') } else { @() }
        $pythonCandidates.Add([pscustomobject]@{ Path = $resolvedCommand.Source; Arguments = $prefixArguments; Label = $commandName })
    }
}

$codexPython = Join-Path $env:USERPROFILE '.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe'
if (Test-Path -LiteralPath $codexPython) {
    $pythonCandidates.Add([pscustomobject]@{ Path = $codexPython; Arguments = @(); Label = 'Python incluido con Codex (respaldo)' })
}

$selectedPython = $null
foreach ($candidate in $pythonCandidates) {
    try {
        $candidateArguments = $candidate.Arguments
        & $candidate.Path @candidateArguments -c "import sys, numpy; print(sys.executable)" *> $null
        if ($LASTEXITCODE -eq 0) {
            $selectedPython = $candidate
            break
        }
    }
    catch {
        continue
    }
}

if ($null -eq $selectedPython) {
    Write-Host ''
    Write-Host 'ERROR: no se encontro una instalacion funcional de Python con NumPy.' -ForegroundColor Red
    Write-Host 'Instala Python 3 desde https://www.python.org/downloads/ y luego ejecuta:'
    Write-Host '  python -m pip install -r requirements.txt'
    exit 1
}

Write-Host "Python seleccionado: $($selectedPython.Label)" -ForegroundColor Cyan
Write-Host "Iniciando la aplicacion en http://${HostAddress}:8765 ..." -ForegroundColor Green
Write-Host 'Mantén esta terminal abierta mientras uses la aplicación.' -ForegroundColor Yellow
$launchArguments = $selectedPython.Arguments
$applicationArguments = @('-u', 'app.py', '--host', $HostAddress, '--port', '8765')
if ($OpenBrowser) {
    $applicationArguments += '--open'
}
& $selectedPython.Path @launchArguments @applicationArguments
exit $LASTEXITCODE
