@echo off
setlocal DisableDelayedExpansion
chcp 65001 >nul
set "PYTHONUTF8=1"
set "PYTHONIOENCODING=utf-8"
cd /d "%~dp0"
py -3 -c "import sys; sys.exit(0 if sys.version_info >= (3,10) else 1)" >nul 2>&1
if not errorlevel 1 (
  py -3 tools\library_menu.py
  pause
  exit /b
)
python -c "import sys; sys.exit(0 if sys.version_info >= (3,10) else 1)" >nul 2>&1
if not errorlevel 1 (
  python tools\library_menu.py
  pause
  exit /b
)
echo Python 3.10 or newer is required. Install Python, then run this file again.
echo No library files have been changed.
pause
exit /b 1
