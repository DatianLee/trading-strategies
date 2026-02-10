# 04 超参优化（Hyperopt）实操

## 场景说明（我在做什么）
你想自动搜索更合适的参数组合，但仍然要避免过拟合。

## 复制即用命令（Windows PowerShell）
```powershell
freqtrade hyperopt --config user_data/configs/S1_config_stub.json --strategy S1_HFT_Conservative_MicroTrend_Scalper --spaces buy sell stoploss trailing --hyperopt-loss SharpeHyperOptLossDaily --epochs 100
```

## 参数解释（大白话）
- `--spaces`：告诉系统优化哪些参数块（买点/卖点/止损/跟踪止盈）。
- `--hyperopt-loss`：用夏普比率做优化目标。
- `--epochs 100`：尝试 100 轮，先小样本验证。

## 结果怎么看（成功/失败判断）
- 成功：输出最佳参数和评分。
- 失败：通常是数据不足或策略代码错误。

## 下一步做什么
把最优参数回填后，重新执行“训练+测试+门槛校验”。
