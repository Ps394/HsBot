# HsBot Installation Script for Windows
# This script sets up the virtual environment and installs dependencies

Write-Host "=== HsBot Installation ===" -ForegroundColor Cyan
Write-Host ""

# Check if Python is available
try {
    $pythonVersion = python --version 2>&1
    Write-Host "Found: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "Error: Python is not installed or not in PATH" -ForegroundColor Red
    Write-Host "Please install Python from https://www.python.org/downloads/" -ForegroundColor Yellow
    exit 1
}

Write-Host ""
Write-Host "Step 1: Creating virtual environment..." -ForegroundColor Yellow
if (Test-Path "venv") {
    Write-Host "Virtual environment already exists. Skipping creation." -ForegroundColor Gray
} else {
    python -m venv venv
    if ($LASTEXITCODE -eq 0) {
        Write-Host "Virtual environment created successfully." -ForegroundColor Green
    } else {
        Write-Host "Error: Failed to create virtual environment" -ForegroundColor Red
        exit 1
    }
}

Write-Host ""
Write-Host "Step 2: Verifying virtual environment..." -ForegroundColor Yellow

# Check for both Windows and MSYS2/MinGW venv structures
$venvPython = $null
$venvPip = $null
$isMSYS2 = $false

if (Test-Path "venv\Scripts\python.exe") {
    # Standard Windows Python
    $venvPython = "venv\Scripts\python.exe"
    $venvPip = "venv\Scripts\pip.exe"
    Write-Host "Detected standard Windows Python venv structure." -ForegroundColor Gray
} elseif (Test-Path "venv\bin\python.exe") {
    # MSYS2/MinGW Python
    $venvPython = "venv\bin\python.exe"
    $venvPip = "venv\bin\pip.exe"
    $isMSYS2 = $true
    Write-Host "Detected MSYS2/MinGW Python venv structure." -ForegroundColor Gray
} else {
    Write-Host "Error: Virtual environment Python not found" -ForegroundColor Red
    Write-Host "Checked locations:" -ForegroundColor Yellow
    Write-Host "  - venv\Scripts\python.exe (Windows)" -ForegroundColor Gray
    Write-Host "  - venv\bin\python.exe (MSYS2/MinGW)" -ForegroundColor Gray
    exit 1
}

Write-Host "Virtual environment Python found at: $venvPython" -ForegroundColor Green

Write-Host ""
Write-Host "Step 3: Upgrading pip in virtual environment..." -ForegroundColor Yellow
& $venvPython -m pip install --upgrade pip --quiet
if ($LASTEXITCODE -ne 0) {
    Write-Host "Error: Failed to upgrade pip" -ForegroundColor Red
    exit 1
}
Write-Host "pip upgraded successfully." -ForegroundColor Green

Write-Host ""
Write-Host "Step 4: Installing dependencies from requirements.txt..." -ForegroundColor Yellow
& $venvPip install -r requirements.txt
$installExitCode = $LASTEXITCODE

if ($installExitCode -ne 0) {
    Write-Host ""
    Write-Host "Warning: Some packages failed to install" -ForegroundColor Yellow
    
    if ($isMSYS2) {
        Write-Host ""
        Write-Host "MSYS2 detected: psutil cannot be installed via pip." -ForegroundColor Yellow
        Write-Host "To install psutil, run the following command in MSYS2 terminal:" -ForegroundColor Cyan
        Write-Host "  pacman -S mingw-w64-ucrt-x86_64-python-psutil" -ForegroundColor White
        Write-Host ""
        Write-Host "Alternatively, the bot will work without psutil (resource monitoring disabled)." -ForegroundColor Gray
        Write-Host ""
        
        # Try installing without psutil
        Write-Host "Attempting to install other dependencies without psutil..." -ForegroundColor Yellow
        & $venvPip install discord.py aiosqlite
        if ($LASTEXITCODE -eq 0) {
            Write-Host "Core dependencies installed successfully (without psutil)." -ForegroundColor Green
        } else {
            Write-Host "Error: Failed to install core dependencies" -ForegroundColor Red
            exit 1
        }
    } else {
        Write-Host "Error: Failed to install dependencies" -ForegroundColor Red
        Write-Host "Please check your requirements.txt file and internet connection." -ForegroundColor Yellow
        exit 1
    }
} else {
    Write-Host "Dependencies installed successfully." -ForegroundColor Green
}

Write-Host ""
Write-Host "=== Optional: Bot Token Configuration ===" -ForegroundColor Cyan
Write-Host ""
$response = Read-Host "Do you want to configure a bot token now? (y/N)"

if ($response -eq "y" -or $response -eq "Y") {
    Write-Host ""
    $token = Read-Host "Please enter your Discord bot token" -AsSecureString
    
    # Convert SecureString to plain text for storage
    $BSTR = [System.Runtime.InteropServices.Marshal]::SecureStringToBSTR($token)
    $plainToken = [System.Runtime.InteropServices.Marshal]::PtrToStringAuto($BSTR)
    [System.Runtime.InteropServices.Marshal]::ZeroFreeBSTR($BSTR)
    
    if ($plainToken -ne "") {
        try {
            # Create registry path if it doesn't exist
            $regPath = "HKCU:\Software\HsBot"
            if (-not (Test-Path $regPath)) {
                New-Item -Path $regPath -Force | Out-Null
            }
            
            # Store token in registry
            Set-ItemProperty -Path $regPath -Name "WZ_BOT_TOKEN" -Value $plainToken
            Write-Host ""
            Write-Host "Bot token stored successfully in Windows Registry." -ForegroundColor Green
            Write-Host "Registry location: HKEY_CURRENT_USER\Software\HsBot" -ForegroundColor Gray
        } catch {
            Write-Host ""
            Write-Host "Error: Failed to store token in registry: $_" -ForegroundColor Red
        }
    } else {
        Write-Host ""
        Write-Host "No token entered. Skipping token configuration." -ForegroundColor Yellow
    }
} else {
    Write-Host "Skipping bot token configuration." -ForegroundColor Gray
}

Write-Host ""
Write-Host "=== Installation Complete ===" -ForegroundColor Green
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Cyan
Write-Host "  1. Activate the virtual environment: .\venv\Scripts\Activate.ps1" -ForegroundColor White
Write-Host "     (or use directly: .\venv\Scripts\python.exe Bot.py)" -ForegroundColor Gray
Write-Host "  2. Run your bot: python Bot.py" -ForegroundColor White
Write-Host ""
Write-Host "To retrieve the stored bot token from registry, use:" -ForegroundColor Cyan
Write-Host '  Get-ItemProperty -Path "HKCU:\Software\HsBot" -Name "WZ_BOT_TOKEN"' -ForegroundColor White
Write-Host ""
