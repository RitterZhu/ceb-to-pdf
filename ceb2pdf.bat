@echo off
setlocal

REM CEB to PDF converter wrapper
REM Usage: ceb2pdf.bat <input.ceb> [output.pdf]

if "%~1"=="" (
    echo Usage: ceb2pdf ^<input.ceb^> [output.pdf]
    exit /b 1
)

set INPUT=%~1
if not exist "%INPUT%" (
    echo Error: File not found: %INPUT%
    exit /b 1
)

set OUTPUT=%~2
if "%OUTPUT%"=="" (
    set OUTPUT=%~dpn1.pdf
)

echo Converting: %INPUT%
echo Output:     %OUTPUT%

REM Launch c2pfree.exe
start "" "D:\OneDrive\Project\Others\CEB Reader\c2pfree.exe"

REM Wait for window to appear
timeout /t 3 /nobreak >nul

echo.
echo ====================================================
echo Please manually convert the file:
echo 1. Click "在原文件同目录" (Same directory)
echo 2. Click "转换" (Convert)
echo 3. Select the file: %INPUT%
echo 4. Click "打开" (Open)
echo 5. Wait for conversion to complete
echo ====================================================
echo.

REM Wait for output file
:waitloop
if exist "%OUTPUT%" (
    echo Output file created: %OUTPUT%
    exit /b 0
)
timeout /t 1 /nobreak >nul
goto waitloop
