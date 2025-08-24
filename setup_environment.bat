@echo off
echo Setting up Australian POS Data Generator Environment

echo.
echo Step 1: Activating conda environment...
call conda activate aus-pos-data-gen

if errorlevel 1 (
    echo Error: Failed to activate conda environment
    echo Please run: conda env create -f environment.yml
    pause
    exit /b 1
)

echo.
echo Step 2: Installing package in development mode...
python -m pip install -e .

if errorlevel 1 (
    echo Error: Failed to install package
    pause
    exit /b 1
)

echo.
echo Step 3: Running tests to verify installation...
python -m pytest tests/ -v

echo.
echo Setup complete! You can now use the Australian POS Data Generator.
echo.
echo Try these commands:
echo   aus-pos-gen info
echo   aus-pos-gen generate --days 30 --businesses 3
echo.

pause
