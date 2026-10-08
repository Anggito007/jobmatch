@echo off
setlocal enabledelayedexpansion
title JobMatch - Stop
cd /d "%~dp0"

echo ================================================
echo    JobMatch - Menghentikan Server
echo ================================================
echo.

set FOUND=0

REM --- 1. Tutup jendela yang dijalankan start.bat ---------------------
for %%T in ("JobMatch Backend" "JobMatch Frontend") do (
    taskkill /FI "WINDOWTITLE eq %%~T*" /T /F >nul 2>&1
    if !errorlevel! equ 0 (
        echo [OK] Jendela %%~T dihentikan.
        set FOUND=1
    )
)

REM --- 2. Sapu bersih proses yang masih memegang port -----------------
for %%P in (8000 3000) do (
    for /f "tokens=5" %%A in ('netstat -ano ^| findstr ":%%P " ^| findstr "LISTENING"') do (
        taskkill /PID %%A /T /F >nul 2>&1
        if !errorlevel! equ 0 (
            echo [OK] PID %%A - port %%P dihentikan.
            set FOUND=1
        )
    )
)

REM --- 3. Verifikasi -------------------------------------------------
powershell -NoProfile -Command "Start-Sleep -Seconds 2"
echo.
set LEFT=0
for %%P in (8000 3000) do (
    for /f "tokens=5" %%A in ('netstat -ano ^| findstr ":%%P " ^| findstr "LISTENING"') do set LEFT=1
)

if "!LEFT!"=="1" (
    echo [!] Masih ada proses di port 8000/3000.
    echo     Coba jalankan ulang stop.bat, atau tutup manual jendelanya.
) else (
    echo [OK] Port 8000 dan 3000 sudah kosong - semua server berhenti.
)

if "!FOUND!"=="0" echo [i] Tidak ada server JobMatch yang sedang berjalan.

echo.
pause
