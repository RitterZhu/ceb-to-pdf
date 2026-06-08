@echo off
REM CEB → PDF 一键转换
REM 用法: run.bat <file.ceb 或 目录> <输出目录>
REM 示例: run.bat file.ceb D:\output
REM       run.bat D:\books\ D:\output

if "%~2"=="" (
    echo 用法: %~nx0 ^<input^> ^<output-dir^>
    echo   input:        .ceb 文件 或 包含 .ceb 的目录
    echo   output-dir:   PDF 输出目录
    echo.
    echo 示例:
    echo   %~nx0 file.ceb D:\output
    echo   %~nx0 D:\books\ D:\output
    exit /b 1
)

set "INPUT=%~1"
set "OUTPUT=%~2"

REM 找 Python
where python >nul 2>&1
if errorlevel 1 (
    echo [错误] 未找到 Python，请先安装 Python 3.11+
    echo 下载: https://www.python.org/downloads/
    pause
    exit /b 1
)

REM 检查依赖
if not exist "%~dp0ceb2pdf.exe" (
    echo [错误] 未找到 ceb2pdf.exe
    echo 应该在: %~dp0ceb2pdf.exe
    pause
    exit /b 1
)
if not exist "%~dp0c2pfree.exe" (
    echo [错误] 未找到 c2pfree.exe
    echo 应该在: %~dp0c2pfree.exe
    pause
    exit /b 1
)

REM 创建输出目录
if not exist "%OUTPUT%" mkdir "%OUTPUT%"

echo.
echo ════════════════════════════════════════
echo   CEB → PDF 转换
echo   输入: %INPUT%
echo   输出: %OUTPUT%
echo ════════════════════════════════════════
echo.

python "%~dp0tool.py" "%INPUT%" --output-dir "%OUTPUT%"

set EXITCODE=%ERRORLEVEL%
echo.
if %EXITCODE%==0 (
    echo ✓ 全部完成
) else (
    echo ✗ 部分失败，看上面的错误信息
)
pause
exit /b %EXITCODE%
