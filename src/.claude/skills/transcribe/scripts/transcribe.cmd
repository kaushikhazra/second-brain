@echo off
rem Windows entry point. Finds the brain's own standalone Python at run time
rem (nothing is baked in), then hands over to launch.py.
setlocal
for %%I in ("%~dp0..\..\..") do set "CLAUDE=%%~fI"
set "PY="
for /d %%D in ("%CLAUDE%\.python\cpython-*") do if exist "%%D\python.exe" if not defined PY set "PY=%%D\python.exe"
if not defined PY (
  echo [transcribe] ERROR: no Python under "%CLAUDE%\.python". Run /init-brain first. 1>&2
  exit /b 2
)
"%PY%" "%~dp0launch.py" %*
exit /b %ERRORLEVEL%
