# CEB → PDF Batch Converter

把 `.ceb` 文件批量转成 PDF。基于 `ceb2pdf` + `c2pfree`（c2pfree 用户自备），**不**需要安装 CEB 阅读器。

## 特性

- ✅ 纯命令行，**不**依赖 CEB 阅读器
- ✅ 支持单文件 / 文件夹递归批量转换
- ✅ Python 3.11+ 标准库，**无第三方依赖**
- ✅ Windows 7/10/11（需 .NET Framework 4.0+）
- ✅ ceb2pdf 内部用 WinForms GUI 自动化，已用 `CreateProcess + STARTF_USESHOWWINDOW` 隐藏主窗口

## 快速开始

### 1. 准备文件

把这个 repo 克隆到本地（假设到 `D:\CEB Reader\`），然后：

```bash
cd D:\CEB Reader
```

### 2. 下载 c2pfree.exe（必需）

⚠️ **c2pfree.exe 是第三方软件，本项目不提供下载**。请自行从合法渠道获取（CEB Reader 工具包等），放到本目录（`D:\CEB Reader\`），跟 `ceb2pdf.exe` 同目录。

> 详见文末「License」节

### 3. 安装 Python（如果还没有）

下载 Python 3.11+：https://www.python.org/downloads/

### 4. 转换

**方式 A：双击 run.bat**

```bat
run.bat file.ceb D:\output
run.bat D:\books\ D:\output
```

**方式 B：命令行**

```bash
# 转一个 CEB 文件
python tool.py file.ceb --output-dir D:\output

# 转整个目录（递归）
python tool.py D:\books\ --output-dir D:\output

# JSON 输出（便于被其他程序解析）
python tool.py file.ceb --output-dir D:\output --json
```

**方式 C：作为 Python 模块 import**

```python
from tool import convert, find_ceb2pdf

print("ceb2pdf 路径:", find_ceb2pdf())
result = convert("D:\\books\\example.ceb", "D:\\output")
print(result)
# {"input": ..., "output": ..., "status": "success", ...}
```

## 输出

每文件生成同名 PDF（`<stem>.pdf`）。

**JSON 输出格式**：
```json
[
  {
    "input": "D:\\test\\example.ceb",
    "output": "D:\\output\\example.pdf",
    "status": "success",
    "message": "转换成功（1841.0 KB）",
    "duration": 7.04
  }
]
```

`status` 取值：
- `success` — 转换成功
- `failed` — 转换失败（看 `message` 字段诊断）

## ⚠️ 转换期间请勿操作电脑

ceb2pdf 内部通过 c2pfree 调起转换面板并模拟点击"同目录"+"转换"按钮，期间会临时占用鼠标和键盘焦点。

**转换过程中请勿**：
- 点击、切换窗口
- 按快捷键
- 移动/最小化窗口

否则可能影响转换结果甚至中断。批量转换每个文件都会重复一次。

## 环境检查

跑一遍 verify.py 确认环境完整：

```bash
python verify.py
```

输出示例：
```
✓ Python 3.12 (需要 3.11+)
✓ ceb2pdf.exe (D:\CEB Reader\ceb2pdf.exe)
✓ c2pfree.exe (D:\CEB Reader\c2pfree.exe)
```

## 重新编译 ceb2pdf.exe

ceb2pdf 是 C# WinForms 程序，用 .NET Framework 4.0+ 编译：

```bat
%WINDIR%\Microsoft.NET\Framework64\v4.0.30319\csc.exe /nologo /target:winexe /out:ceb2pdf.exe ceb2pdf.cs
```

或者用 .NET SDK：

```bash
dotnet build -c Release
```

## 不支持

- ❌ `.cebx`（ceb2pdf 内部限制，按其 README 说明）
- ❌ 加密的 CEB 文件（需先解密）
- ❌ Linux / macOS（ceb2pdf 是 Windows-only）

## 常见问题

### "No window" 错误

c2pfree 启动后 6 秒内未出现主窗口。**最常见原因**：
1. **缺 VC++ Runtime** → 装 [VC++ 2015-2022 Redist](https://aka.ms/vs/17/release/vc_redist.x64.exe)
2. **缺 .NET Framework 4.x**（ceb2pdf 是 C#）→ Win 10/11 默认装，Win 7/8 需手动装
3. **c2pfree 残留进程冲突**（之前没杀干净）→ 任务管理器杀 c2pfree.exe 再试

### "Not enough buttons" 错误

c2pfree 版本/界面变了，找不到 ≥4 个按钮。重新下载原版 c2pfree.exe。

### 转换成功但 PDF 是 0 字节

c2pfree 把"完成"消息当成"开始"了。重新跑一次（通常第二次能成功）。

## License

MIT（ceb2pdf.cs / tool.py / run.bat / verify.py）

⚠️ `c2pfree.exe` 是第三方软件，不在本项目内。
