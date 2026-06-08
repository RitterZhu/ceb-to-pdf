# Changelog

所有对本项目的重要变更都会记录在此文件。

格式基于 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.1.0/)，
本项目遵循 [语义化版本](https://semver.org/lang/zh-CN/)。

## [Unreleased]

### Added
- CHANGELOG.md
- docs/c2pfree-license.md（说明 c2pfree 版权和获取方式）
- tests/test_ceb_conversion.py（端到端集成测试）
- tests/test_inputs/（测试 CEB 样本）
- verify.py（一键环境检查）
- .github/ISSUE_TEMPLATE/bug_report.md

## [0.1.0] - 2026-06-08

### Added
- 首个公开版本
- ceb2pdf.cs（C# WinForms 转换器，CreateProcess + STARTF_USESHOWWINDOW 隐藏窗口）
- tool.py（Python 3.11+ CLI 包装，支持单文件 / 文件夹 / JSON 输出）
- run.bat（Windows 一键运行）
- README.md（中文说明 + 截图占位）
- LICENSE（MIT，仅适用于 ceb2pdf.cs / tool.py / run.bat / verify.py）
- .gitignore

### Known Issues
- ⚠️ 转换过程中 c2pfree 会弹出控制台窗口（.NET ProcessStartInfo 限制，无法 100% 隐藏）。期间请勿操作电脑。
- ❌ c2pfree.exe 不在本项目内——用户需自行从 Apabi 官方渠道获取（见 `docs/c2pfree-license.md`）

[Unreleased]: https://github.com/<owner>/<repo>/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/<owner>/<repo>/releases/tag/v0.1.0
