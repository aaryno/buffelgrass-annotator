@echo off
REM ============================================================================
REM CVAT Annotation Tool - Windows Shutdown Script
REM ============================================================================

echo.
echo ============================================================
echo    Stopping CVAT...
echo ============================================================
echo.

docker-compose stop

echo.
echo CVAT has been stopped.
echo Your annotations are saved and will be available when you restart.
echo.
echo To restart CVAT, double-click: START-CVAT.bat
echo.
pause
