#!/usr/bin/env python3
"""
CEB → PDF 批量转换器（基于 ceb2pdf + c2pfree，无 Apabi GUI 自动化）

ceb2pdf.exe 接受一个或多个 CEB 文件作为参数，**后台执行**（窗口已自动隐藏），
通过 WM_COMMAND 消息自动点"同目录"+"转换"按钮，输出 PDF 后退出，返回码 0/1。

**注意**：转换过程中 c2pfree 会弹出控制台窗口，期间会临时占用鼠标和键盘焦点，
请勿操作电脑（点击、切换窗口、按快捷键等），否则可能影响转换结果。

用法：
  # 标准模式（JSON 输出，便于被其他程序解析）
  python tool.py --input file.ceb --output-dir D:\\output --json
  python tool.py --input folder/   --output-dir D:\\output   # 递归
"""
import sys
import os
import json
import argparse
import subprocess
import time
from pathlib import Path

# 脚本所在目录（ceb-reader 工具包跟 tool.py 同目录）
SCRIPT_DIR = Path(__file__).resolve().parent
BUNDLED_CEB2PDF = SCRIPT_DIR / "ceb2pdf.exe"
USER_CONFIG = SCRIPT_DIR / ".user-config.json"


def _early_log(msg: str) -> None:
    print(f"[{time.strftime('%H:%M:%S')}] {msg}", file=sys.stderr, flush=True)


def _get_user_config_value(dep_name: str) -> str | None:
    """从 user-config.json 读用户手动配置的 ceb2pdf 路径。"""
    if not USER_CONFIG.exists():
        return None
    try:
        config = json.loads(USER_CONFIG.read_text(encoding="utf-8"))
        deps = (
            config.get("tools", {})
            .get("ceb-to-pdf", {})
            .get("dependencies", {})
        )
        v = deps.get(dep_name, "")
        if v:
            return v
    except Exception:
        pass
    return None


def find_ceb2pdf() -> str | None:
    """找 ceb2pdf.exe。优先级：
    1. `.user-config.json` 里用户手动配的
    2. 脚本同目录的 ceb2pdf.exe（独立项目用法）
    """
    configured = _get_user_config_value("ceb-reader")
    if configured and Path(configured).is_file():
        return configured

    if BUNDLED_CEB2PDF.is_file():
        return str(BUNDLED_CEB2PDF)

    return None


def convert(input_path: str, output_dir: str) -> dict:
    """单文件转换 / 批量转换。
    input_path 可以是文件或目录（目录会被调用方提前展开成文件列表）。
    output_dir 是输出目录，CEB 文件保持原文件名 + .pdf 后缀。
    """
    _early_log(f"convert() called: input={input_path} output_dir={output_dir}")
    start = time.time()
    input_p = Path(input_path)
    output_dir_p = Path(output_dir)
    output_dir_p.mkdir(parents=True, exist_ok=True)

    if not input_p.exists():
        return _fail(input_path, str(output_dir_p), f"输入文件不存在: {input_path}", start)

    ceb2pdf = find_ceb2pdf()
    if not ceb2pdf:
        return _fail(
            input_path, str(output_dir_p),
            "未找到 ceb2pdf.exe。\n"
            "请把 ceb2pdf.exe 放在 tool.py 同目录，"
            "或创建 .user-config.json 写明完整路径。",
            start,
        )

    # 预检：c2pfree.exe 必须跟 ceb2pdf 在同目录
    ceb2pdf_dir = Path(ceb2pdf).parent
    c2pfree_path = ceb2pdf_dir / "c2pfree.exe"
    if not c2pfree_path.is_file():
        return _fail(
            input_path, str(output_dir_p),
            f"ceb2pdf 缺少依赖 c2pfree.exe\n应在：{c2pfree_path}",
            start,
        )

    # 单文件：output_dir 下生成 <input.stem>.pdf
    output_file = output_dir_p / f"{input_p.stem}.pdf"

    # ceb2pdf 接受：ceb2pdf.exe <input.ceb> [output.pdf]
    cmd = [ceb2pdf, str(input_p.absolute()), str(output_file.absolute())]
    _early_log(f"调用: {cmd}")

    try:
        # 180s 超时（ceb2pdf 内部有 180s 限制）。
        # **不传** creationflags=CREATE_NO_WINDOW——某些杀软会拦截
        # CREATE_NO_WINDOW + subprocess.run 的组合，返 PermissionError(13)。
        # ceb2pdf 内部自己用 CreateProcess + STARTF_USESHOWWINDOW 隐藏窗口，
        # 我们不重复设。
        # encoding="utf-8" + errors="replace" 避免 ceb2pdf 中文输出触发 GBK 解码失败。
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=180,
        )
    except subprocess.TimeoutExpired:
        return _fail(input_path, str(output_file),
                     f"转换超时（180s）：{input_p.name}", start)
    except FileNotFoundError:
        return _fail(input_path, str(output_file),
                     f"ceb2pdf.exe 不存在：{ceb2pdf}", start)
    except OSError as e:
        return _fail(input_path, str(output_file),
                     f"启动 ceb2pdf 失败：{e!r}", start)

    stderr = (result.stderr or "").strip()
    stdout = (result.stdout or "").strip()

    if result.returncode == 0 and output_file.is_file() and output_file.stat().st_size > 0:
        size_kb = output_file.stat().st_size / 1024
        return {
            "input": input_path,
            "output": str(output_file),
            "status": "success",
            "message": f"转换成功（{size_kb:.1f} KB）",
            "duration": round(time.time() - start, 2),
        }

    # 失败：把 stderr / stdout **完整**带回去便于诊断
    msg_lines = [
        f"ceb2pdf 返回码 {result.returncode}",
        f"输出 PDF 不存在或大小为 0：{output_file}",
    ]
    if stderr:
        msg_lines.append(f"--- ceb2pdf stderr ---\n{stderr}")
    if stdout:
        msg_lines.append(f"--- ceb2pdf stdout ---\n{stdout}")
    return _fail(input_path, str(output_file), "\n".join(msg_lines), start)


def _fail(input_path: str, output: str, message: str, start: float) -> dict:
    return {
        "input": input_path,
        "output": output,
        "status": "failed",
        "message": message,
        "duration": round(time.time() - start, 2),
    }


def _expand_inputs(inputs: list[str]) -> list[Path]:
    """展开 inputs：文件直接收，目录递归收所有 .ceb 文件。"""
    out: list[Path] = []
    for inp in inputs:
        p = Path(inp)
        if not p.exists():
            continue
        if p.is_file():
            out.append(p)
        elif p.is_dir():
            for f in p.rglob("*.ceb"):
                if f.is_file():
                    out.append(f)
    return out


def main() -> int:
    parser = argparse.ArgumentParser(
        description="CEB → PDF 批量转换（基于 ceb2pdf + c2pfree）",
        epilog="示例: python tool.py file.ceb --output-dir D:\\output",
    )
    parser.add_argument("inputs", nargs="+", help="一个或多个 .ceb 文件 / 目录")
    parser.add_argument("--output-dir", "-o", required=True, help="PDF 输出目录")
    parser.add_argument("--json", action="store_true", help="以 JSON 输出每文件结果")
    args = parser.parse_args()

    files = _expand_inputs(args.inputs)
    if not files:
        _early_log(f"未找到任何 .ceb 文件（输入：{args.inputs}）")
        return 1

    _early_log(f"找到 {len(files)} 个 .ceb 文件，开始转换 → {args.output_dir}")

    results = []
    success = 0
    for i, f in enumerate(files, 1):
        _early_log(f"[{i}/{len(files)}] {f.name}")
        r = convert(str(f), args.output_dir)
        results.append(r)
        if r["status"] == "success":
            success += 1
        else:
            _early_log(f"  失败：{r['message'][:200]}")

    _early_log(f"完成：{success}/{len(files)} 成功")
    if args.json:
        print(json.dumps(results, ensure_ascii=False, indent=2))
    return 0 if success == len(files) else 1


if __name__ == "__main__":
    sys.exit(main())
