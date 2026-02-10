# 02 Windows11 从零部署 Freqtrade

## 场景说明（我在做什么）
你是零基础用户，要在 Windows11 安装并能在当前仓库执行 Freqtrade 命令。

## 复制即用命令（Windows PowerShell）
```powershell
winget install -e --id Python.Python.3.11
```

```powershell
py -3.11 -m pip install -U pip
```

```powershell
py -3.11 -m pip install freqtrade
```

```powershell
cd .\trading-strategies
```

```powershell
freqtrade --version
```

## 参数解释（大白话）
- `winget install`：安装 Python 3.11。
- `pip install freqtrade`：安装交易框架本体。
- `freqtrade --version`：检查安装是否成功。

## 结果怎么看（成功/失败判断）
- 成功：打印版本号，例如 `freqtrade X.Y.Z`。
- 失败：如果提示“不是内部命令”，重开 PowerShell 再试。

## 下一步做什么
按 `00_总览与快速开始.md` 下载数据并跑第一轮回测。
