@echo off
set ASTRO_TELEMETRY_DISABLED=1
cd /d "%~dp0"
node node_modules\astro\astro.js dev --host 127.0.0.1 --port 4321
