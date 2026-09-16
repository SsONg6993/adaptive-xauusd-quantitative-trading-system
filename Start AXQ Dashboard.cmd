@echo off
setlocal
for %%I in ("%~dp0.") do set "PROJECT_ROOT=%%~fI"
set "AXQ_PYTHON=%PROJECT_ROOT%\.venv\Scripts\python.exe"
if exist "%AXQ_PYTHON%" (
  for %%I in ("%AXQ_PYTHON%") do if %%~zI GTR 0 (
    "%AXQ_PYTHON%" --version >nul 2>&1
    if not errorlevel 1 goto python_ready
  )
)
set "AXQ_PYTHON=%PROJECT_ROOT%\..\..\.venv\Scripts\python.exe"
if exist "%AXQ_PYTHON%" (
  for %%I in ("%AXQ_PYTHON%") do if %%~zI GTR 0 (
    "%AXQ_PYTHON%" --version >nul 2>&1
    if not errorlevel 1 goto python_ready
  )
)
(
  echo AXQ project virtual environment was not found.
  echo Expected .venv in the project root or the parent repository.
  pause
  exit /b 1
)
:python_ready
"%AXQ_PYTHON%" "%PROJECT_ROOT%\scripts\start_axq_dashboard.py" --project-root "%PROJECT_ROOT%"
if errorlevel 1 pause
endlocal
