@echo off
rem Double-click to open the desktop UI. pythonw keeps the console window away.
cd /d "%~dp0"
where pythonw >nul 2>nul
if %errorlevel% equ 0 (
    start "" pythonw "%~dp0gui.py"
) else (
    python "%~dp0gui.py"
    if errorlevel 1 pause
)
