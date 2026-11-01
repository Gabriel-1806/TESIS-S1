@echo off
title PhishTrain - servidor
cd /d "%~dp0"
call venv\Scripts\activate.bat
echo ============================================
echo   PhishTrain
echo   Pagina: http://127.0.0.1:8001/
echo   No cierres esta ventana mientras lo usas.
echo   Para apagar: Ctrl + C
echo ============================================
start "" cmd /c "timeout /t 4 >nul & start http://127.0.0.1:8001/"
python manage.py runserver 8001
pause
