@echo off
setlocal
set "BASE=%~dp0"
start "" "%BASE%validar_fronts.html"
start "" "%BASE%frontend_cliente\index.html"
start "" "%BASE%frontend_admin\index.html"
endlocal
