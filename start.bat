@echo off
setlocal
title JobMatch - Start
cd /d "%~dp0"

echo ================================================
echo    JobMatch - Menjalankan Server
echo ================================================
echo.

REM --- Cek prasyarat -------------------------------------------------
if not exist "backend\.venv\Scripts\python.exe" (
    echo [X] Virtualenv backend tidak ditemukan:
    echo     backend\.venv\Scripts\python.exe
    echo.
    echo     Buat dulu dengan:
    echo         cd backend
    echo         python -m venv .venv
    echo         .venv\Scripts\python -m pip install -r requirements.txt
    echo.
    pause
    exit /b 1
)

if not exist "frontend\node_modules" (
    echo [!] frontend\node_modules belum ada - menjalankan npm install...
    pushd frontend
    call npm install
    popd
    echo.
)

REM --- Cegah dobel jalan ---------------------------------------------
set ALREADY=0
for %%P in (8000 3000) do (
    for /f "tokens=5" %%A in ('netstat -ano ^| findstr ":%%P " ^| findstr "LISTENING"') do set ALREADY=1
)
if "%ALREADY%"=="1" (
    echo [!] Sebagian server sepertinya SUDAH berjalan.
    echo     Jalankan stop.bat dulu bila ingin memulai ulang.
    echo.
)

REM --- Nyalakan backend ----------------------------------------------
echo [1/2] Menyalakan BACKEND  (port 8000) ...
cd /d "%~dp0backend"
start "JobMatch Backend" cmd /k ".venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000"
cd /d "%~dp0"

REM --- Nyalakan frontend ---------------------------------------------
echo [2/2] Menyalakan FRONTEND (port 3000) ...
cd /d "%~dp0frontend"
start "JobMatch Frontend" cmd /k "npm run dev"
cd /d "%~dp0"

REM --- Tunggu lalu verifikasi ----------------------------------------
echo.
echo Menunggu server siap (model + Next.js perlu waktu ~20 detik)...
powershell -NoProfile -Command "Start-Sleep -Seconds 20"

powershell -NoProfile -Command "try { $r = Invoke-WebRequest -Uri 'http://127.0.0.1:8000/health' -UseBasicParsing -TimeoutSec 8; Write-Host '[OK] Backend  :' $r.Content } catch { Write-Host '[..] Backend  : belum merespons (masih memuat model?)' }"
powershell -NoProfile -Command "try { $r = Invoke-WebRequest -Uri 'http://localhost:3000' -UseBasicParsing -TimeoutSec 15; Write-Host '[OK] Frontend : HTTP' $r.StatusCode } catch { Write-Host '[..] Frontend : belum siap (Next.js masih compile?)' }"

echo.
echo ================================================
echo   Dashboard : http://localhost:3000
echo   API docs  : http://127.0.0.1:8000/docs
echo.
echo   Hentikan  : stop.bat
echo ================================================
echo.
pause
