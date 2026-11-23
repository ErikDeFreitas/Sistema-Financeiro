# Gera o SistemaFinanceiro.exe e o .sha256 que acompanham cada Release no GitHub.
# Antes: aumente __version__ em src\sistema_financeiro\__init__.py.
# Uso:  powershell -File build.ps1            (venv limpo, instala de requirements.txt)
#       powershell -File build.ps1 -Local     (venv limpo, instala ..\Tcm-ui e ..\Send_Agregados;
#                                              so ate as tags v1.1.0 e v2.0.0 existirem)
#       powershell -File build.ps1 -Python python   (CI: o workflow ja instalou tudo)
param([string]$Python, [switch]$Local)
Set-Location $PSScriptRoot

function Invoke-Nativo([scriptblock]$Comando, [string]$Falha) {
    & $Comando
    if ($LASTEXITCODE -ne 0) {
        Write-Host "`nERRO: $Falha" -ForegroundColor Red
        exit 1
    }
}

if (-not $Python) {
    $venv = Join-Path $PSScriptRoot "build\venv"
    if (Test-Path $venv) { Remove-Item $venv -Recurse -Force }
    Invoke-Nativo { python -m venv $venv } "nao foi possivel criar o venv."
    $Python = Join-Path $venv "Scripts\python.exe"
    Invoke-Nativo { & $Python -m pip install --quiet --upgrade pip } "pip."
    if ($Local) {
        Invoke-Nativo { & $Python -m pip install --quiet -r requirements-local.txt } "requirements-local.txt."
        Invoke-Nativo { & $Python -m pip install --quiet --no-deps ../Send_Agregados . } "instalar Send_Agregados e a casca."
    } else {
        Invoke-Nativo { & $Python -m pip install --quiet -r requirements.txt } "requirements.txt."
        Invoke-Nativo { & $Python -m pip install --quiet . } "instalar a casca."
    }
    Invoke-Nativo { & $Python -m pip install --quiet pytest pytest-qt pyinstaller } "pytest/pyinstaller."
    $env:QT_QPA_PLATFORM = "offscreen"
    Invoke-Nativo { & $Python -m pytest -q } "os testes falharam."
    Remove-Item Env:QT_QPA_PLATFORM
}

$nome = "SistemaFinanceiro"
$exe = "dist\$nome.exe"
$antes = if (Test-Path $exe) { (Get-Item $exe).LastWriteTime } else { [datetime]::MinValue }

$argsSistemas = @(& $Python ferramentas\args_pyinstaller.py)
if ($LASTEXITCODE -ne 0) { Write-Host "`nERRO: args_pyinstaller.py falhou." -ForegroundColor Red; exit 1 }

# Importacoes ocultas que o PyInstaller nao enxerga:
#   openpyxl, pythoncom, win32com.client -> robo_agregado (planilhas e Outlook via COM)
& $Python -m PyInstaller --noconfirm --onefile --windowed --name $nome `
    @argsSistemas `
    --hidden-import openpyxl --hidden-import pythoncom --hidden-import win32com.client `
    --exclude-module matplotlib --exclude-module scipy --exclude-module IPython --exclude-module tkinter `
    --workpath build --specpath build --distpath dist main.py
if ($LASTEXITCODE -ne 0 -or -not (Test-Path $exe) -or (Get-Item $exe).LastWriteTime -le $antes) {
    Write-Host "`nERRO: o build falhou; nenhum arquivo novo foi gerado." -ForegroundColor Red
    exit 1
}

# Verificacao do .exe: carrega todos os sistemas e abre cada pagina, sem tocar nos dados reais.
$tmp = Join-Path ([IO.Path]::GetTempPath()) ("sf-verificar-" + [guid]::NewGuid().ToString("N"))
$dadosSf = Join-Path $tmp "sf"
$dadosRobo = Join-Path $tmp "robo"
New-Item -ItemType Directory -Force $dadosSf, $dadosRobo | Out-Null
$salvas = @{}
$vars = @{
    SISTEMA_FINANCEIRO_DADOS = $dadosSf
    ROBO_AGREGADO_DADOS      = $dadosRobo
    SMTP_USUARIO             = "teste@example.com"
    SMTP_SENHA               = "senha-falsa"
    QT_QPA_PLATFORM          = "offscreen"
}
foreach ($k in $vars.Keys) {
    $salvas[$k] = [Environment]::GetEnvironmentVariable($k)
    [Environment]::SetEnvironmentVariable($k, $vars[$k])
}
$ok = $false
try {
    $p = Start-Process (Resolve-Path $exe) -ArgumentList "--verificar" -PassThru
    if ($p.WaitForExit(180000)) {
        $ok = ($p.ExitCode -eq 0)
    } else {
        & taskkill /PID $p.Id /T /F | Out-Null
        Write-Host "Tempo esgotado (180 s) na verificacao do .exe." -ForegroundColor Red
    }
} finally {
    foreach ($k in $vars.Keys) { [Environment]::SetEnvironmentVariable($k, $salvas[$k]) }
}
if (-not $ok) {
    Write-Host "`nERRO: a verificacao do .exe (--verificar) falhou." -ForegroundColor Red
    $log = Join-Path $dadosSf "logs\sistema_financeiro.log"
    if (Test-Path $log) { Get-Content $log } else { Write-Host "(sem log em $log)" }
    exit 1
}
Remove-Item $tmp -Recurse -Force -ErrorAction SilentlyContinue
Write-Host "Verificacao do .exe: OK"

$hash = (Get-FileHash $exe -Algorithm SHA256).Hash.ToLower()
[IO.File]::WriteAllText("$PSScriptRoot\dist\$nome.exe.sha256", "$hash  $nome.exe`n")
$versao = (Select-String -Path src\sistema_financeiro\__init__.py -Pattern '__version__ = "(.+)"').Matches[0].Groups[1].Value
Write-Host "`nPronto: versao $versao | SHA-256 $hash"
Write-Host "Publique em uma Release com a tag v$versao anexando os DOIS arquivos de dist\:"
Write-Host "  $nome.exe  e  $nome.exe.sha256"
