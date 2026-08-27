<#
.SYNOPSIS
    Enterprise Architect Strategy - setup and verification (Windows).

.DESCRIPTION
    The framework itself has no dependencies. That is a design rule, not an
    accident: it has to run behind a corporate proxy on a locked-down laptop.
    So the default run installs nothing - it proves the framework works on the
    Python you already have.

    The optional extras exist only to regenerate the setup document. You do not
    need them to run an assessment.

.EXAMPLE
    .\setup.ps1              Verify the framework runs (installs nothing)
.EXAMPLE
    .\setup.ps1 -Docs        Also install the document-generation extras
.EXAMPLE
    .\setup.ps1 -Check       Verify only, never install
#>
[CmdletBinding()]
param(
    [switch]$Docs,
    [switch]$All,
    [switch]$Check,
    [switch]$Venv
)

$ErrorActionPreference = 'Stop'
Set-Location -Path $PSScriptRoot
if ($All -or $Venv) { $Docs = $true }

function Step($t) { Write-Host ""; Write-Host $t -ForegroundColor White }
function Ok($t)   { Write-Host "  " -NoNewline; Write-Host "OK " -ForegroundColor Green -NoNewline; Write-Host $t }
function Warn($t) { Write-Host "  " -NoNewline; Write-Host "!  " -ForegroundColor Yellow -NoNewline; Write-Host $t }
function Bad($t)  { Write-Host "  " -NoNewline; Write-Host "X  " -ForegroundColor Red -NoNewline; Write-Host $t }
function Hint($t) { Write-Host "     $t" -ForegroundColor DarkGray }

Write-Host "Enterprise Architect Strategy - setup" -ForegroundColor White
Write-Host $PSScriptRoot -ForegroundColor DarkGray

# --- 1. Python -------------------------------------------------------------
Step "1. Python"
$py = $null
foreach ($c in @('python3', 'python', 'py')) {
    $exe = Get-Command $c -ErrorAction SilentlyContinue
    if (-not $exe) { continue }
    & $c -c "import sys; sys.exit(0 if sys.version_info[:2] >= (3,9) else 1)" 2>$null
    if ($LASTEXITCODE -eq 0) { $py = $c; break }
}
if (-not $py) {
    Bad "no Python 3.9 or later found on PATH"
    Hint "The framework needs only the standard library, but it needs a recent one:"
    Hint "Path.is_relative_to and PEP 585 generics both arrived in 3.9."
    exit 1
}
$ver = & $py -c "import sys; print('%d.%d.%d' % sys.version_info[:3])"
Ok "$py $ver (need 3.9+)"

# --- 2. Core dependencies --------------------------------------------------
Step "2. Core dependencies"
$missing = & $py -c @"
import importlib.util
mods = ['argparse','copy','csv','dataclasses','datetime','hashlib','html','http.server',
        'io','json','mimetypes','os','pathlib','re','shutil','sys','tempfile','time',
        'traceback','typing','unicodedata','unittest','urllib.parse']
print(' '.join(m for m in mods if importlib.util.find_spec(m) is None))
"@
if ($missing.Trim()) {
    Bad "standard library modules missing: $missing"
    Hint "This Python install is incomplete - reinstall from python.org."
    exit 1
}
Ok "all 23 required modules present - every one is standard library"
Ok "nothing to install for the framework itself"

# --- 3. Verification -------------------------------------------------------
Step "3. Verification"
& $py -m eas lint | Out-Null
if ($LASTEXITCODE -ne 0) { Bad "catalogue lint failed - run '$py -m eas lint'"; exit 1 }
Ok "catalogue is coherent"

$testOut = & $py -m unittest discover tests 2>&1 | Select-Object -Last 3
if ($testOut -match '^OK$') {
    $ran = ($testOut | Select-String -Pattern 'Ran \d+ tests? in [\d.]+s').Matches.Value
    Ok "$ran, all passing"
} else {
    Bad "test suite failed"
    $testOut | ForEach-Object { Write-Host $_ }
    exit 1
}

$counts = & $py -c @"
import sys, pathlib
sys.path.insert(0, '.')
from eas.catalogue import Catalogue
s = Catalogue().summary()
print(f\"{s['domains']} domains, {s['options']} options, {s['capabilities']} capabilities, {s['rules']} rules, {s['signals']} signals\")
print(f\"{len(list(pathlib.Path('.claude/agents').glob('*.md')))} agents, {len(list(pathlib.Path('.claude/skills').glob('*/SKILL.md')))} skills\")
"@
$counts -split "`n" | Where-Object { $_.Trim() } | ForEach-Object { Ok $_.Trim() }

# --- 4. Optional extras ----------------------------------------------------
if ($Docs -and -not $Check) {
    Step "4. Optional extras (document generation only)"
    Hint "These are needed only to rebuild docs\eas-setup-and-flow.docx."
    Hint "An assessment run needs none of them."

    if (Get-Command npm -ErrorAction SilentlyContinue) {
        node -e "require('docx')" 2>$null
        if ($LASTEXITCODE -eq 0) { Ok "npm 'docx' already available" }
        else {
            Write-Host "     installing npm docx ..."
            npm install --silent --no-audit --no-fund 2>$null | Out-Null
            if ($LASTEXITCODE -eq 0) { Ok "npm 'docx' installed" }
            else {
                Warn "npm install failed - the document generator will not run"
                Hint "behind a proxy? npm config set proxy `$env:HTTP_PROXY https-proxy `$env:HTTPS_PROXY"
            }
        }
    } else { Warn "npm not found - skipping the document generator" }

    $pyPip = $py
    if ($Venv) {
        if (-not (Test-Path .venv)) { & $py -m venv .venv; Ok "created .\.venv" }
        else { Ok "using existing .\.venv" }
        $pyPip = ".\.venv\Scripts\python.exe"
    }
    & $pyPip -c "import lxml, defusedxml" 2>$null
    if ($LASTEXITCODE -eq 0) { Ok "python validator extras already available" }
    else {
        Write-Host "     installing lxml and defusedxml ..."
        $userFlag = if ($Venv -or $env:VIRTUAL_ENV) { @() } else { @('--user') }
        & $pyPip -m pip install --quiet --disable-pip-version-check @userFlag -r requirements-dev.txt 2>$null
        if ($LASTEXITCODE -eq 0) { Ok "python validator extras installed" }
        else {
            Warn "pip install failed - docx schema validation will not run"
            Hint "behind a proxy? pip install --proxy `$env:HTTPS_PROXY -r requirements-dev.txt"
        }
    }
} elseif ($Docs) {
    Step "4. Optional extras"
    Hint "-Check given, so nothing was installed"
}

# --- Done ------------------------------------------------------------------
Step "Ready"
@"
    $py -m eas new --brief briefs\example-regulated.md    assess a direction
    $py -m eas serve                                       browser UI on :8000
    $py -m eas catalogue                                   every domain and option
    $py -m eas list                                        your projects

    Briefs to try: briefs\example-simple.md, example-regulated.md,
                   example-strategic.md, example-sase-migration.md,
                   example-agentic-sdlc.md
"@ | Write-Host
if (-not $Docs -and -not $Check) {
    Write-Host ""
    Write-Host "    Only rebuilding the setup document? .\setup.ps1 -Docs" -ForegroundColor DarkGray
}
Write-Host ""
