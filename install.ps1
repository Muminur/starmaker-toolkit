# StarMaker Toolkit — One-Click Installer (Windows PowerShell)
# Usage: irm https://raw.githubusercontent.com/Muminur/starmaker-toolkit/main/install.ps1 | iex
$ErrorActionPreference = "Stop"

$Repo = "https://github.com/Muminur/starmaker-toolkit.git"
$InstallDir = "$env:USERPROFILE\.starmaker-toolkit"

Write-Host "============================================" -ForegroundColor Cyan
Write-Host "  StarMaker Toolkit - One-Click Installer" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""

# Check Python
try {
    $pyVersion = python --version 2>&1
    $pyMatch = [regex]::Match($pyVersion, "(\d+)\.(\d+)")
    $pyMajor = [int]$pyMatch.Groups[1].Value
    $pyMinor = [int]$pyMatch.Groups[2].Value

    if ($pyMajor -lt 3 -or ($pyMajor -eq 3 -and $pyMinor -lt 9)) {
        Write-Host "ERROR: Python 3.9+ required, found $pyVersion" -ForegroundColor Red
        exit 1
    }
    Write-Host "[1/5] $pyVersion detected" -ForegroundColor Green
} catch {
    Write-Host "ERROR: Python 3.9+ is required but not found." -ForegroundColor Red
    Write-Host "Install Python: https://www.python.org/downloads/" -ForegroundColor Yellow
    exit 1
}

# Check pip
try {
    python -m pip --version | Out-Null
    Write-Host "[2/5] pip available" -ForegroundColor Green
} catch {
    Write-Host "ERROR: pip is required. Run: python -m ensurepip --upgrade" -ForegroundColor Red
    exit 1
}

# Check git
try {
    git --version | Out-Null
    Write-Host "[3/5] git available" -ForegroundColor Green
} catch {
    Write-Host "ERROR: git is required. Install from https://git-scm.com/downloads" -ForegroundColor Red
    exit 1
}

# Clone or update
if (Test-Path $InstallDir) {
    Write-Host "[4/5] Updating existing installation..." -ForegroundColor Green
    Push-Location $InstallDir
    git pull --quiet origin main
    Pop-Location
} else {
    Write-Host "[4/5] Cloning StarMaker Toolkit..." -ForegroundColor Green
    git clone --quiet $Repo $InstallDir
}

# Install with browser extras
Write-Host "[5/5] Installing dependencies..." -ForegroundColor Green
Push-Location $InstallDir
python -m pip install -e ".[browser]" --quiet
Pop-Location

# Create .env from example if not exists
$envFile = Join-Path $InstallDir ".env"
$envExample = Join-Path $InstallDir ".env.example"
if (-not (Test-Path $envFile) -and (Test-Path $envExample)) {
    Copy-Item $envExample $envFile
    Write-Host ""
    Write-Host "Created .env file - edit it to add your API credentials:" -ForegroundColor Yellow
    Write-Host "  $envFile" -ForegroundColor Yellow
}

# Install Playwright browsers for Camoufox
Write-Host ""
Write-Host "Installing Camoufox browser (for automated publishing)..." -ForegroundColor Green
try {
    python -m playwright install firefox 2>$null
} catch {
    # Non-fatal
}

Write-Host ""
Write-Host "============================================" -ForegroundColor Cyan
Write-Host "  Installation complete!" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Get started:" -ForegroundColor Green
Write-Host "  starmaker              # Interactive mode"
Write-Host "  starmaker init         # Setup wizard"
Write-Host "  starmaker auto-post --readme path\to\README.md --dry-run"
Write-Host ""
Write-Host "Set up credentials:" -ForegroundColor Green
Write-Host "  Edit $envFile"
Write-Host "  Or run: starmaker setup"
Write-Host ""
Write-Host "Full docs: https://github.com/Muminur/starmaker-toolkit" -ForegroundColor Blue
