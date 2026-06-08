# c2pfree.exe 版权说明

## c2pfree.exe 不在本项目内

**`c2pfree.exe` 是北京方正阿帕比技术有限公司（Apabi / 数方科技）开发的专有软件**，版权和使用权归 Apabi 所有。

**本项目不包含、不分发、不授权 `c2pfree.exe`**。你需要自己从合法渠道获取。

## 获取 c2pfree.exe 的合法渠道

### 1. Apabi Reader 安装包（推荐）

下载并安装 [Apabi Reader](http://www.apabi.com/)，安装后从其安装目录复制 `c2pfree.exe`：

```
C:\Program Files (x86)\Apabi Reader 4.0\c2pfree.exe
C:\Program Files\Apabi Reader 4.0\c2pfree.exe
```

### 2. CEB Reader 工具包

部分公司内部提供 "CEB Reader" 工具包，里面通常包含 c2pfree.exe。请咨询你的 IT 部门或软件供应商。

### 3. 联系 Apabi 官方

如果上面渠道都不可用，请联系 Apabi 官方获取授权：
- 官网：http://www.apabi.com/
- 客服：见官网"联系我们"页面

## ceb2pdf.exe 是开源的

与 `c2pfree.exe` 不同，`ceb2pdf.exe` 是本项目**自己编写**的开源程序（MIT 协议），源码见 `ceb2pdf.cs`。

ceb2pdf 通过 Win32 API（`CreateProcess` + `WM_COMMAND` 消息）调用 c2pfree 的 GUI 界面实现自动化转换 —— 类似按键精灵的工作方式。

## 责任声明

使用本项目转换 CEB 文件时，请确保：
- ✅ 你**有合法权利**转换这些 CEB 文件（自己创作、已获授权、或在合理使用范围内）
- ✅ 你**有合法权利**使用 c2pfree.exe（已购买 Apabi Reader 授权、或在 Apabi 授权范围内）

本项目作者不对 CEB 文件的版权问题或 c2pfree.exe 的使用授权问题负责。
