# Research Contract Implementation（研究契约落地）中文执行版

> 对应英文原文：[`docs/Research_Contract_v1_Implementation.md`](../Research_Contract_v1_Implementation.md)  
> 上一篇：[`docs/zh/Research_Contract_v1_CN.md`](./Research_Contract_v1_CN.md) ｜ 下一篇：[`docs/zh/English_Documents_CN_Index.md`](./English_Documents_CN_Index.md)

## 目录结构
与英文一致：S1-S4 策略、配置模板、`scripts/validate_backtest_gates.py`。

## 保护组件及用途
- CooldownPeriod：平仓后冷却，防止连续打脸。
- StoplossGuard：连续止损后暂停。
- MaxDrawdown：组合级回撤刹车。
- LowProfitPairs：短期表现差的币对临时禁用。

## 市场状态过滤
- S1/S3/S4（趋势）通过 ADX/ATR/高周期过滤减少震荡误入。
- S2（均值回归）通过 ADX 上限和斜率上限避免单边行情硬抄底。

## 回测命令（原样保留）
### S1
```bash
freqtrade backtesting \
  --config user_data/configs/S1_config_stub.json \
  --strategy S1_HFT_Conservative_MicroTrend_Scalper \
  --timeframe 1m \
  --timerange 20240101-20240630 \
  --export trades \
  --backtest-filename user_data/backtest_results/S1_train.json

freqtrade backtesting \
  --config user_data/configs/S1_config_stub.json \
  --strategy S1_HFT_Conservative_MicroTrend_Scalper \
  --timeframe 1m \
  --timerange 20240701-20240930 \
  --export trades \
  --backtest-filename user_data/backtest_results/S1_test.json
```
参数说明：
- `--timeframe`：执行级K线周期。
- `--timerange`：训练/测试切分区间。

### S2/S3/S4
> 命令模板同英文，分别替换 `--config`、`--strategy`、`--timeframe` 与输出文件名。

## Hyperopt（超参优化）命令
```bash
freqtrade hyperopt --config user_data/configs/S1_config_stub.json --strategy S1_HFT_Conservative_MicroTrend_Scalper --spaces buy sell stoploss trailing --hyperopt-loss SharpeHyperOptLossDaily --epochs 200
freqtrade hyperopt --config user_data/configs/S2_config_stub.json --strategy S2_HFT_Aggressive_MeanReversion_Fade --spaces buy sell stoploss trailing --hyperopt-loss SharpeHyperOptLossDaily --epochs 200
freqtrade hyperopt --config user_data/configs/S3_config_stub.json --strategy S3_MFT_Conservative_TrendPullback --spaces buy sell stoploss trailing --hyperopt-loss SharpeHyperOptLossDaily --epochs 200
freqtrade hyperopt --config user_data/configs/S4_config_stub.json --strategy S4_MFT_Progressive_BreakoutRetest --spaces buy sell stoploss trailing --hyperopt-loss SharpeHyperOptLossDaily --epochs 200
```
参数说明：
- `--spaces buy sell stoploss trailing`：四类参数一起搜。
- `--hyperopt-loss SharpeHyperOptLossDaily`：按日夏普损失函数优化。

## Pass/Fail Gate 命令
```bash
python scripts/validate_backtest_gates.py \
  --strategy S1 --train user_data/backtest_results/S1_train.json --test user_data/backtest_results/S1_test.json \
  --max-dd 0.10 --max-profit-factor-delta 0.60 --max-winrate-delta 0.12
python scripts/validate_backtest_gates.py \
  --strategy S2 --train user_data/backtest_results/S2_train.json --test user_data/backtest_results/S2_test.json \
  --max-dd 0.12 --max-profit-factor-delta 0.75 --max-winrate-delta 0.15
python scripts/validate_backtest_gates.py \
  --strategy S3 --train user_data/backtest_results/S3_train.json --test user_data/backtest_results/S3_test.json \
  --max-dd 0.15 --max-profit-factor-delta 0.50 --max-winrate-delta 0.10
python scripts/validate_backtest_gates.py \
  --strategy S4 --train user_data/backtest_results/S4_train.json --test user_data/backtest_results/S4_test.json \
  --max-dd 0.14 --max-profit-factor-delta 0.55 --max-winrate-delta 0.12
```
参数说明：
- `--max-dd`：测试集可接受最大回撤。
- `--max-profit-factor-delta`：PF 训练/测试偏差容忍。
- `--max-winrate-delta`：胜率偏差容忍。

## 拒绝规则
命中任意一项即 `REJECTED`：测试回撤超限、PF 偏差超限、胜率偏差超限。

## 策略卡片（S1~S4）
- S1：短脉冲趋势延续；风险在低流动性震荡与突发反转。
- S2：短时过度偏离回归；风险在单边趋势日。
- S3：大趋势中的回调接力；风险在趋势转区间。
- S4：突破回踩确认；风险在假突破高噪音时段。

## 修正记录
- 全部命令中的配置/策略名已与仓库现有文件核对一致，无需改命令。

### 成功判定
- 每个策略都能产出 train/test JSON，并通过 gate 脚本得到 PASS/REJECT 明确结论。

### 失败排查（最常见3项）
1. `user_data/backtest_results/` 目录不存在。
2. 回测时间段无本地数据导致输出为空。
3. 超参优化 epochs 过小导致参数不稳定。

### 下一步动作
- 回到中文索引页，按总入口进行双语跳转与持续维护。
