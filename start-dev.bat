@echo off
REM Duplicate Photos Finder - Development Server Startup Script (Windows)
REM Runs both backend (Flask) and frontend (React) servers simultaneously
REM Usage: start-dev.bat [backend|frontend|both]
REM Default: both

setlocal enabledelayedexpansion

REM Configuration
set BACKEND_PORT=5000
set FRONTEND_PORT=3000
set BACKEND_DIR=backend
set FRONTEND_DIR=frontend

REM Parse command line argument
set TARGET=%1
if "%TARGET%"=="" set TARGET=both

REM Validate target
if not "%TARGET%"=="backend" if not "%TARGET%"=="frontend" if not "%TARGET%"=="both" (
    echo Invalid target: %TARGET%
    echo Usage: %0 [backend^|frontend^|both]
    exit /b 1
)

REM Check Python and Node are installed
if "%TARGET%"=="backend" goto skip_python_check
if "%TARGET%"=="both" (
    python --version >nul 2>&1
    if errorlevel 1 (
        echo Error: Python is not installed
        exit /b 1
    )
)
:skip_python_check

if "%TARGET%"=="frontend" goto skip_node_check
if "%TARGET%"=="both" (
    npm --version >nul 2>&1
    if errorlevel 1 (
        echo Error: npm is not installed
        exit /b 1
    )
)
:skip_node_check

REM Start backend
if "%TARGET%"=="backend" goto start_backend
if "%TARGET%"=="both" (
    :start_backend
    echo.
    echo ================================================
    echo Starting Backend (Flask) on port %BACKEND_PORT%
    echo ================================================
    echo.
    
    if not exist "%BACKEND_DIR%" (
        echo Error: Backend directory not found at %BACKEND_DIR%
        exit /b 1
    )
    
    REM Check if venv exists, if not create it
    if not exist "%BACKEND_DIR%\venv" (
        echo Virtual environment not found. Creating...
        cd %BACKEND_DIR%
        python -m venv venv
        call venv\Scripts\activate.bat
        pip install -e ".[dev]"
        cd ..
    )
    
    REM Start backend in new window
    start "Duplicate Photos - Backend (Flask)" cmd /k "cd %BACKEND_DIR% && call venv\Scripts\activate.bat && python -m app.main"
    echo ✓ Backend started on port %BACKEND_PORT%
    timeout /t 2 /nobreak
)

REM Start frontend
if "%TARGET%"=="frontend" goto start_frontend
if "%TARGET%"=="both" (
    :start_frontend
    echo.
    echo ================================================
    echo Starting Frontend (React) on port %FRONTEND_PORT%
    echo ================================================
    echo.
    
    if not exist "%FRONTEND_DIR%" (
        echo Error: Frontend directory not found at %FRONTEND_DIR%
        exit /b 1
    )
    
    REM Check if node_modules exists
    if not exist "%FRONTEND_DIR%\node_modules" (
        echo Dependencies not found. Running npm install...
        cd %FRONTEND_DIR%
        call npm install
        cd ..
    )
    
    REM Start frontend in new window
    start "Duplicate Photos - Frontend (React)" cmd /k "cd %FRONTEND_DIR% && npm start"
    echo ✓ Frontend started on port %FRONTEND_PORT%
    timeout /t 2 /nobreak
)

REM Display status
echo.
echo ================================================
echo ✓ Development Servers Starting
echo ================================================
echo.
echo Backend:
echo   URL: http://localhost:%BACKEND_PORT%
echo   API Health: http://localhost:%BACKEND_PORT%/api/health
echo.
echo Frontend:
echo   URL: http://localhost:%FRONTEND_PORT%
echo.
echo Both servers will open in new windows.
echo Close the windows or press Ctrl+C in each to stop.
echo.

endlocal
pause
