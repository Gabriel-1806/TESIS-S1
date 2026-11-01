@echo off
title PhishTrain - instalacion
cd /d "%~dp0"
if not exist venv (
    echo Creando el entorno virtual...
    py -3.12 -m venv venv || py -m venv venv
)
call venv\Scripts\activate.bat
python -m pip install -r requirements.txt
if errorlevel 1 goto error
python manage.py migrate
if errorlevel 1 goto error
python manage.py validar_contenido
if errorlevel 1 goto error
python manage.py test
if errorlevel 1 goto error
echo.
echo Listo. Ahora abre ABRIR_PHISHTRAIN.bat
pause
exit /b 0
:error
echo.
echo Hubo un error. Revisa el mensaje de arriba.
pause
