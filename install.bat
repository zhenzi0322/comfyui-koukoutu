@echo off
echo Installing Koukoutu ComfyUI Node dependencies...
echo.

REM Check if we're in a Python environment
python --version >nul 2>&1
if errorlevel 1 (
    echo Python is not available. Please ensure Python is installed and in PATH.
    pause
    exit /b 1
)

echo Installing required packages...
pip install requests>=2.28.0
if errorlevel 1 (
    echo Failed to install requests
    pause
    exit /b 1
)

pip install Pillow>=9.0.0
if errorlevel 1 (
    echo Failed to install Pillow
    pause
    exit /b 1
)

pip install numpy>=1.21.0
if errorlevel 1 (
    echo Failed to install numpy
    pause
    exit /b 1
)

echo.
echo All dependencies installed successfully!
echo You can now restart ComfyUI to use the Koukoutu nodes.
echo.
pause
