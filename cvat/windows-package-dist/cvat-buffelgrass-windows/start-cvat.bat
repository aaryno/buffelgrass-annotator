@echo off
REM ============================================================================
REM CVAT Annotation Tool - Windows Launcher
REM Double-click this file to start CVAT
REM ============================================================================

echo.
echo ============================================================
echo    CVAT Buffelgrass Annotation Tool
echo ============================================================
echo.

REM Check if Docker Desktop is running
echo [1/4] Checking Docker Desktop...
docker info >nul 2>&1
if %errorlevel% neq 0 (
    echo.
    echo ERROR: Docker Desktop is not running!
    echo.
    echo Please start Docker Desktop first:
    echo   1. Open Docker Desktop from Start Menu
    echo   2. Wait for it to fully start (whale icon in system tray)
    echo   3. Run this script again
    echo.
    pause
    exit /b 1
)
echo      Docker is running!

REM Check if project directory exists
if not exist "%~dp0\data\training_chips" (
    echo.
    echo [2/4] Creating data directories...
    mkdir "%~dp0\data\training_chips"
    echo      Created: data\training_chips\
) else (
    echo.
    echo [2/4] Data directories found
)

REM Check for existing CVAT instance
echo.
echo [3/4] Checking for existing CVAT instance...
docker ps -a --format "{{.Names}}" | findstr "cvat_server" >nul 2>&1
if %errorlevel% equ 0 (
    echo      CVAT containers found, starting...
    docker-compose up -d
) else (
    echo      First time setup - pulling images (this may take 5-10 minutes)...
    docker-compose up -d
)

REM Wait for CVAT to be ready
echo.
echo [4/4] Waiting for CVAT to start...
timeout /t 10 /nobreak >nul

REM Test if CVAT is accessible
:WAIT_LOOP
timeout /t 5 /nobreak >nul
curl -s http://localhost:8080/api/server/about >nul 2>&1
if %errorlevel% neq 0 (
    echo      Still starting...
    goto WAIT_LOOP
)

echo      CVAT is ready!

REM Create default user if needed
echo.
echo Checking for default user...
docker exec cvat_server python manage.py shell -c "from django.contrib.auth import get_user_model; User = get_user_model(); print('exists' if User.objects.filter(username='annotator').exists() else 'create')" 2>nul | findstr "exists" >nul
if %errorlevel% neq 0 (
    echo Creating default user 'annotator'...
    docker exec cvat_server python manage.py shell -c "from django.contrib.auth import get_user_model; User = get_user_model(); User.objects.create_superuser('annotator', 'annotator@localhost', 'buffelgrass2024')" 2>nul
)

echo.
echo ============================================================
echo    CVAT is Running!
echo ============================================================
echo.
echo Open your browser to: http://localhost:8080
echo.
echo Login Credentials:
echo   Username: annotator
echo   Password: buffelgrass2024
echo.
echo Your training chips directory:
echo   %~dp0data\training_chips\
echo.
echo To STOP CVAT:
echo   Double-click: STOP-CVAT.bat
echo.
echo Press any key to open browser...
pause >nul

REM Open browser
start http://localhost:8080

echo.
echo CVAT is running in the background.
echo Close this window or press Ctrl+C to continue.
echo (CVAT will keep running)
echo.
pause
