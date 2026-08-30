@echo off
title AuditDesk - Fieldwork OS
echo ========================================================
echo   Starting AuditDesk Internal Audit Workbench...
echo ========================================================
echo.

:: 1. Deep Python Detection
set PY_CMD=

:: Check PATH (python or py)
where python >nul 2>nul && set PY_CMD=python
if not defined PY_CMD (
    where py >nul 2>nul && set PY_CMD=py
)

:: Check common Windows installation paths
if not defined PY_CMD (
    for /d %%i in ("%LOCALAPPDATA%\Programs\Python\Python3*") do (
        if exist "%%i\python.exe" set PY_CMD="%%i\python.exe"
    )
)
if not defined PY_CMD (
    for /d %%i in ("%PROGRAMFILES%\Python3*") do (
        if exist "%%i\python.exe" set PY_CMD="%%i\python.exe"
    )
)

:: 2. Handle Case Where Python Is Truly Not Installed
if not defined PY_CMD (
    echo ========================================================
    echo   [NOTICE] Python 3 was not detected on this computer.
    echo ========================================================
    echo.
    echo AuditDesk requires Python 3.10+ to run its analytics engine.
    echo.
    
    :: Check if winget is available for 1-click install
    where winget >nul 2>nul
    if %ERRORLEVEL% equ 0 (
        echo Windows Package Manager (winget) is available.
        set /p INSTALL_CHOICE="Would you like to auto-install Python now? (Y/N): "
        if /i "%INSTALL_CHOICE%"=="Y" (
            echo.
            echo Installing Python 3.11 via Windows winget...
            winget install -e --id Python.Python.3.11 --accept-source-agreements --accept-package-agreements
            echo.
            echo Python installation complete! Restarting launcher...
            timeout /t 3 >nul
            goto :EOF
        )
    )
    
    echo.
    echo Opening Python official download page in your browser...
    start https://www.python.org/downloads/
    echo Please install Python (make sure to check "Add Python to PATH") and run AuditDesk.bat again.
    echo.
    pause
    exit /b 1
)

:: 3. Check for python-docx dependency
%PY_CMD% -c "import docx" >nul 2>nul
if %ERRORLEVEL% neq 0 (
    echo Installing required reporting engine (python-docx)...
    %PY_CMD% -m pip install python-docx --quiet
)

:: 4. Navigate to script directory and launch
cd /d "%~dp0"

echo [OK] Python detected: %PY_CMD%
echo Launching AuditDesk application...
%PY_CMD% server.py
pause
