@echo off
set ASTRO_TELEMETRY_DISABLED=1
cd /d "%~dp0"
node node_modules\astro\astro.js check
if errorlevel 1 exit /b 1
node node_modules\astro\astro.js build
