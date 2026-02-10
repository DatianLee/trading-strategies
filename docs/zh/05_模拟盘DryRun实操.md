# 05 模拟盘（Dry-run）实操

## 场景说明（我在做什么）
你要在不动真金白银的情况下，验证策略真实运行行为。

## 复制即用命令（Windows PowerShell）
```powershell
freqtrade trade --config user_data/configs/S5_config_stub.json --strategy S5_LFT_Conservative_MTF_TrendReversal --dry-run
```

```powershell
freqtrade trade --config user_data/configs/S3_config_stub.json --strategy S3_MFT_Conservative_TrendPullback --dry-run
```

## 参数解释（大白话）
- `trade`：启动交易引擎。
- `--dry-run`：模拟下单，不会上交易所。

## 结果怎么看（成功/失败判断）
- 成功：日志持续运行，有开仓/平仓记录。
- 失败：如果 API 权限不完整，会出现交易所连接报错。

## 下一步做什么
连续运行至少 7 天，再对照 `06_实盘前检查清单.md` 决定是否前进。
