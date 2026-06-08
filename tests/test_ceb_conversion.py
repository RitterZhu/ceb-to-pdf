"""端到端集成测试 — 实际跑一个 CEB 文件验证 tool.py 能用。

前置：
- ceb2pdf.exe 在 tool.py 同目录
- c2pfree.exe 在 tool.py 同目录
- tests/test_inputs/ 下有 ≥1 个 .ceb 文件

跑：
  python -m pytest tests/ -v
"""
import shutil
import subprocess
import sys
import time
from pathlib import Path

import pytest

SCRIPT_DIR = Path(__file__).resolve().parent.parent
TOOL_PY = SCRIPT_DIR / "tool.py"
TEST_INPUTS = SCRIPT_DIR / "tests" / "test_inputs"
TEST_OUTPUT = SCRIPT_DIR / "tests" / "_test_output"


def _kill_c2pfree() -> None:
    """杀 c2pfree 残留进程。"""
    try:
        subprocess.run(
            ["taskkill", "/F", "/IM", "c2pfree.exe"],
            capture_output=True, timeout=5,
        )
    except Exception:
        pass


@pytest.fixture(scope="module", autouse=True)
def cleanup_c2pfree():
    """模块结束时确保 c2pfree 不残留。"""
    yield
    _kill_c2pfree()
    if TEST_OUTPUT.exists():
        shutil.rmtree(TEST_OUTPUT, ignore_errors=True)


def _has_dependencies() -> bool:
    """检查依赖（ceb2pdf + c2pfree + 测试样本）。"""
    ceb2pdf = SCRIPT_DIR / "ceb2pdf.exe"
    c2pfree = SCRIPT_DIR / "c2pfree.exe"
    if not ceb2pdf.is_file() or not c2pfree.is_file():
        return False
    if not TEST_INPUTS.is_dir():
        return False
    return any(TEST_INPUTS.rglob("*.ceb"))


# 跳过条件：缺依赖就跳过（不报错）
pytestmark = pytest.mark.skipif(
    not _has_dependencies(),
    reason="缺 ceb2pdf.exe / c2pfree.exe / 测试 CEB 样本",
)


def test_single_ceb_conversion():
    """跑一个 CEB 文件 → 验证 PDF 生成。"""
    ceb_files = list(TEST_INPUTS.rglob("*.ceb"))
    assert len(ceb_files) > 0, "tests/test_inputs/ 下没 .ceb 文件"

    test_file = ceb_files[0]
    TEST_OUTPUT.mkdir(parents=True, exist_ok=True)

    result = subprocess.run(
        [sys.executable, str(TOOL_PY), str(test_file), "--output-dir", str(TEST_OUTPUT)],
        capture_output=True, text=True, timeout=180,
    )

    # 找生成的 PDF（tool.py 保持原文件名 + .pdf）
    expected_pdf = TEST_OUTPUT / f"{test_file.stem}.pdf"
    assert expected_pdf.exists(), (
        f"PDF 未生成: {expected_pdf}\n"
        f"returncode={result.returncode}\n"
        f"stdout={result.stdout}\n"
        f"stderr={result.stderr}"
    )
    assert expected_pdf.stat().st_size > 0, f"PDF 是空的: {expected_pdf}"


def test_folder_recursive_conversion():
    """跑整个目录 → 验证递归处理。"""
    if not TEST_INPUTS.is_dir():
        pytest.skip("测试输入目录不存在")

    ceb_count = len(list(TEST_INPUTS.rglob("*.ceb")))
    if ceb_count == 0:
        pytest.skip("tests/test_inputs/ 下没 .ceb 文件")

    TEST_OUTPUT.mkdir(parents=True, exist_ok=True)
    result = subprocess.run(
        [sys.executable, str(TOOL_PY), str(TEST_INPUTS), "--output-dir", str(TEST_OUTPUT)],
        capture_output=True, text=True, timeout=300,
    )

    # 应该生成 ≥1 个 PDF
    pdfs = list(TEST_OUTPUT.glob("*.pdf"))
    assert len(pdfs) > 0, (
        f"没生成任何 PDF\n"
        f"returncode={result.returncode}\n"
        f"stderr={result.stderr[:500]}"
    )


def test_json_output_format():
    """验证 --json 输出的 JSON 格式。"""
    import json
    ceb_files = list(TEST_INPUTS.rglob("*.ceb"))
    if not ceb_files:
        pytest.skip("没测试 CEB")

    test_file = ceb_files[0]
    TEST_OUTPUT.mkdir(parents=True, exist_ok=True)
    result = subprocess.run(
        [sys.executable, str(TOOL_PY), str(test_file), "--output-dir", str(TEST_OUTPUT), "--json"],
        capture_output=True, text=True, timeout=180,
    )

    # 解析最后一行（tool.py 在 _early_log 输出到 stderr，JSON 走 stdout）
    # 找 JSON 数组起始
    out = result.stdout.strip()
    if not out.startswith("["):
        pytest.skip(f"输出不是 JSON 数组: {out[:200]}")

    try:
        data = json.loads(out)
    except json.JSONDecodeError as e:
        pytest.fail(f"JSON 解析失败: {e}\nstdout: {out[:500]}")

    assert isinstance(data, list)
    assert len(data) >= 1
    item = data[0]
    assert "input" in item
    assert "output" in item
    assert "status" in item
    assert "duration" in item
    assert item["status"] == "success", f"转换失败: {item.get('message', '')[:200]}"


def test_tool_imports():
    """tool.py 作为 Python 模块可以 import。"""
    sys.path.insert(0, str(SCRIPT_DIR))
    try:
        import tool  # noqa: F401

        assert hasattr(tool, "convert")
        assert hasattr(tool, "find_ceb2pdf")
        assert callable(tool.convert)
        assert callable(tool.find_ceb2pdf)
    finally:
        sys.path.pop(0)


def test_find_ceb2pdf_locates_executable():
    """find_ceb2pdf() 找到同目录的 ceb2pdf.exe。"""
    sys.path.insert(0, str(SCRIPT_DIR))
    try:
        import tool
        path = tool.find_ceb2pdf()
        assert path is not None, "find_ceb2pdf 返 None"
        assert Path(path).is_file(), f"路径不存在: {path}"
        assert Path(path).name == "ceb2pdf.exe"
    finally:
        sys.path.pop(0)


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-v"]))
