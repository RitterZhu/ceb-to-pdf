#!/usr/bin/env python3
"""
一键环境检查 — 跑一遍确认 CEB Reader 工具链完整。

用法：
  python verify.py
"""
import os
import platform
import subprocess
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent

CHECKS = []


def check(name: str, ok: bool, detail: str = "") -> None:
    """记录一条检查结果。"""
    status = "✓" if ok else "✗"
    line = f"  {status} {name}"
    if detail:
        line += f" — {detail}"
    CHECKS.append((ok, line))
    print(line)


def main() -> int:
    print("=" * 60)
    print("CEB Reader 环境检查")
    print("=" * 60)
    print()

    # 1. Python 版本
    py_version = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
    check("Python", sys.version_info >= (3, 11), f"v{py_version}")

    # 2. ceb2pdf.exe
    ceb2pdf = SCRIPT_DIR / "ceb2pdf.exe"
    if ceb2pdf.is_file():
        size = ceb2pdf.stat().st_size
        check("ceb2pdf.exe", True, f"{size} bytes")
    else:
        check("ceb2pdf.exe", False, f"缺失: {ceb2pdf}")

    # 3. c2pfree.exe（必需但用户自备）
    c2pfree = SCRIPT_DIR / "c2pfree.exe"
    if c2pfree.is_file():
        size = c2pfree.stat().st_size
        check("c2pfree.exe", True, f"{size} bytes")
    else:
        check(
            "c2pfree.exe",
            False,
            f"缺失: {c2pfree}（请从 Apabi Reader 安装目录复制，见 docs/c2pfree-license.md）",
        )

    # 4. .NET Framework 4.x
    if platform.system() == "Windows":
        try:
            # 查注册表
            import winreg
            with winreg.OpenKey(
                winreg.HKEY_LOCAL_MACHINE,
                r"SOFTWARE\Microsoft\NET Framework Setup\NDP\v4\Full",
            ) as key:
                release = winreg.QueryValueEx(key, "Release")[0]
                # Release ≥ 378389 = .NET 4.5+
                ok = release >= 378389
                check(".NET Framework 4.x", ok, f"Release={release}")
        except (OSError, ImportError):
            check(".NET Framework 4.x", False, "未找到（Win 10/11 默认装，Win 7/8 需手动装）")
    else:
        check(".NET Framework 4.x", False, "仅 Windows 支持")

    # 5. 测试 CEB 文件
    test_ceb_dir = SCRIPT_DIR / "tests" / "test_inputs"
    if test_ceb_dir.is_dir():
        ceb_files = list(test_ceb_dir.rglob("*.ceb"))
        check("测试 CEB 样本", len(ceb_files) > 0, f"{len(ceb_files)} 个文件")
    else:
        check("测试 CEB 样本", False, f"目录不存在: {test_ceb_dir}")

    # 6. 关键 Python 模块
    try:
        import json, subprocess, argparse, time  # noqa: F401
        check("Python 标准库", True, "json / subprocess / argparse / time")
    except ImportError as e:
        check("Python 标准库", False, str(e))

    # 7. 实际跑一个测试 CEB（如果上面都过 + 有测试样本）
    if ceb2pdf.is_file() and c2pfree.is_file() and test_ceb_dir.is_dir():
        ceb_files = list(test_ceb_dir.rglob("*.ceb"))
        if ceb_files:
            print()
            print("=" * 60)
            print("Smoke test: 跑一个 CEB")
            print("=" * 60)
            test_file = ceb_files[0]
            out_dir = SCRIPT_DIR / "tests" / "_smoke_output"
            out_dir.mkdir(parents=True, exist_ok=True)
            try:
                # 用 tool.py 调
                # encoding="utf-8" + errors="replace" 避免 ceb2pdf 输出中文到
                # console 时 Python subprocess 试图用 GBK 解码失败抛 UnicodeDecodeError。
                result = subprocess.run(
                    [sys.executable, str(SCRIPT_DIR / "tool.py"),
                     str(test_file), "--output-dir", str(out_dir)],
                    capture_output=True, text=True, encoding="utf-8",
                    errors="replace", timeout=60,
                )
                # 找生成的 PDF
                pdfs = list(out_dir.glob("*.pdf"))
                if result.returncode == 0 and pdfs:
                    check("Smoke test", True, f"{pdfs[0].name} ({pdfs[0].stat().st_size} bytes)")
                else:
                    check("Smoke test", False, f"returncode={result.returncode}, stderr={result.stderr[:200]}")
            except subprocess.TimeoutExpired:
                check("Smoke test", False, "超时（60s）")
            finally:
                # 清理
                import shutil
                shutil.rmtree(out_dir, ignore_errors=True)
                # 杀 c2pfree 残留
                if platform.system() == "Windows":
                    subprocess.run(
                        ["taskkill", "/F", "/IM", "c2pfree.exe"],
                        capture_output=True,
                    )

    # 总结
    print()
    print("=" * 60)
    failed = [line for ok, line in CHECKS if not ok]
    if not failed:
        print("✓ 全部通过 — 可以开始用 CEB Reader 了")
        return 0
    print(f"✗ {len(failed)} 项不通过：")
    for line in failed:
        print(line)
    print()
    print("修复建议：")
    if not (SCRIPT_DIR / "c2pfree.exe").is_file():
        print("  - 缺 c2pfree.exe → 见 docs/c2pfree-license.md")
    return 1


if __name__ == "__main__":
    sys.exit(main())
