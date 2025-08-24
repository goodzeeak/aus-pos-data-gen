# Setup script for Australian POS Data Generator
# Run this script to set up the development environment

Write-Host "Setting up Australian POS Data Generator Environment" -ForegroundColor Green

# Step 1: Activate conda environment
Write-Host "`nStep 1: Activating conda environment..." -ForegroundColor Yellow
try {
    & conda activate aus-pos-data-gen
    if ($LASTEXITCODE -ne 0) {
        throw "Failed to activate conda environment"
    }
} catch {
    Write-Host "Error: Failed to activate conda environment" -ForegroundColor Red
    Write-Host "Please run: conda env create -f environment.yml" -ForegroundColor Yellow
    Read-Host "Press Enter to exit"
    exit 1
}

# Step 2: Install package in development mode
Write-Host "`nStep 2: Installing package in development mode..." -ForegroundColor Yellow
try {
    & python -m pip install -e .
    if ($LASTEXITCODE -ne 0) {
        throw "Failed to install package"
    }
} catch {
    Write-Host "Error: Failed to install package" -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

# Step 3: Run tests to verify installation
Write-Host "`nStep 3: Running tests to verify installation..." -ForegroundColor Yellow
try {
    & python -m pytest tests/ -v
    if ($LASTEXITCODE -ne 0) {
        Write-Host "Warning: Some tests failed, but installation may still work" -ForegroundColor Yellow
    }
} catch {
    Write-Host "Warning: Could not run tests, but installation may still work" -ForegroundColor Yellow
}

Write-Host "`nSetup complete! You can now use the Australian POS Data Generator." -ForegroundColor Green
Write-Host "`nTry these commands:" -ForegroundColor Cyan
Write-Host "  aus-pos-gen info" -ForegroundColor White
Write-Host "  aus-pos-gen generate --days 30 --businesses 3" -ForegroundColor White
Write-Host "  python scripts/generate_sample_data.py" -ForegroundColor White

Read-Host "`nPress Enter to continue"
