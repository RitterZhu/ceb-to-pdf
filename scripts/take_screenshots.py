"""
截图脚本 — 抓 2 张图：
1. CLI 运行中的 cmd 窗口
2. 输出 PDF 在文件资源管理器中

用 PowerShell GDI+ / .NET 抓屏。
"""
import os
import subprocess
import sys
import time
from pathlib import Path

DEST = Path(r"D:\CEB Reader\docs")
DEST.mkdir(parents=True, exist_ok=True)

PS_SCRIPT = r"""
param(
    [string]$OutFile
)
Add-Type -AssemblyName System.Windows.Forms
Add-Type -AssemblyName System.Drawing

$Screen = [System.Windows.Forms.Screen]::PrimaryScreen.Bounds
$Bitmap = New-Object System.Drawing.Bitmap $Screen.Width, $Screen.Height
$Graphics = [System.Drawing.Graphics]::FromImage($Bitmap)
$Graphics.CopyFromScreen($Screen.Location, [System.Drawing.Point]::Empty, $Screen.Size)
$Bitmap.Save($OutFile, [System.Drawing.Imaging.ImageFormat]::Png)
$Graphics.Dispose()
$Bitmap.Dispose()

Write-Host "Saved: $OutFile"
"""

def grab_screen(out_file: Path) -> bool:
    """PowerShell 抓全屏。"""
    try:
        result = subprocess.run(
            ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass",
             "-Command", PS_SCRIPT, "-OutFile", str(out_file)],
            capture_output=True, text=True, timeout=10,
        )
        if out_file.is_file() and out_file.stat().st_size > 0:
            print(f"  OK: {out_file} ({out_file.stat().st_size} bytes)")
            return True
        else:
            print(f"  FAIL: {result.stderr[:200]}")
            return False
    except Exception as e:
        print(f"  ERROR: {e}")
        return False


def main():
    print("=" * 50)
    print("截 CLI 窗口（命令行工具运行中）")
    print("=" * 50)
    print("操作步骤：")
    print("  1. 打开 cmd")
    print("  2. cd D:\\CEB Reader")
    print("  3. 跑 python verify.py")
    print("  4. 30 秒内回这里按 Enter")
    print()
    input("准备好后按 Enter（30s 超时）...")
    cli_png = DEST / "screenshot-cli.png"
    if grab_screen(cli_png):
        print(f"  保存: {cli_png}")

    print()
    print("=" * 50)
    print("截 输出 PDF（文件资源管理器）")
    print("=" * 50)
    print("操作步骤：")
    print("  1. 打开文件资源管理器到 D:\\test_output")
    print("  2. 显示 .pdf 文件详情")
    print("  3. 30 秒内回这里按 Enter")
    print()
    input("准备好后按 Enter（30s 超时）...")
    pdf_png = DEST / "screenshot-result.png"
    if grab_screen(pdf_png):
        print(f"  保存: {pdf_png}")


if __name__ == "__main__":
    main()
