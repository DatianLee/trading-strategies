# Final Production Candidate Package（最终生产候选包）中文执行版

> 对应英文原文：[`docs/final_production_candidate_package.md`](../final_production_candidate_package.md)  
> 上一篇：[`docs/zh/English_Documents_CN_Index.md`](./English_Documents_CN_Index.md) ｜ 下一篇：[`docs/zh/Portfolio_Playbook_CN.md`](./Portfolio_Playbook_CN.md)

## A) 完整仓库树

```text
.
├── docs
│   ├── Portfolio Playbook.md
│   ├── Research_Contract_v1.0.md
│   ├── Research_Contract_v1_Implementation.md
│   ├── S5_S7_validation_playbook.md
│   ├── final_production_candidate_package.md
│   └── operations_runbook.md
├── scripts
│   └── validate_backtest_gates.py
└── user_data
    ├── configs
    │   ├── S10_config_stub.json
    │   ├── S1_config_stub.json
    │   ├── S2_config_stub.json
    │   ├── S3_config_stub.json
    │   ├── S4_config_stub.json
    │   ├── S5_config_stub.json
    │   ├── S6_config_stub.json
    │   ├── S7_config_stub.json
    │   ├── S8_config_stub.json
    │   ├── S9_config_stub.json
    │   └── portfolio_orchestration_profiles.yaml
    └── strategies
        ├── S10_LFT_Aggressive_RegimeSwitch_Trend.py
        ├── S1_HFT_Conservative_MicroTrend_Scalper.py
        ├── S2_HFT_Aggressive_MeanReversion_Fade.py
        ├── S3_MFT_Conservative_TrendPullback.py
        ├── S4_MFT_Progressive_BreakoutRetest.py
        ├── S5_LFT_Conservative_MTF_TrendReversal.py
        ├── S6_LFT_Progressive_Momentum_Rotation.py
        ├── S7_Event_Volatility_Shock_Strategy.py
        ├── S8_HFT_Progressive_Orderflow_Impulse.py
        └── S9_MFT_Aggressive_TrendAcceleration.py
```

## 策略集合分类（最终要求）
- 高频（High-frequency）：S1 保守、S8 进取、S2 激进。
- 中频（Medium-frequency）：S3 保守、S4 进取、S9 激进、S7 混合。
- 低频（Low-frequency）：S5 保守、S6 进取、S10 激进。

## 全局验收标准
### 1) 无未来函数（Lookahead）/数据泄漏（Leakage）
- S7 已修复 `shift(-1)`，改为仅使用已收盘K线确认。
- 静态扫描命令：
```bash
rg "shift\(-[0-9]+\)" user_data/strategies
```
参数说明：
- `rg`：全文检索工具（ripgrep）。
- `"shift\(-[0-9]+\)"`：匹配所有负位移写法。
- `user_data/strategies`：仅检查策略目录。

### 2) 样本外退化（OOS degradation）在可接受区间
- 验证脚本：`scripts/validate_backtest_gates.py`。
- 通用校验命令：
```bash
python scripts/validate_backtest_gates.py --strategy <Sx> --train <train.json> --test <test.json> --max-dd <tier_limit> --max-profit-factor-delta <tier_pf_delta> --max-winrate-delta <tier_wr_delta>
```
参数说明：
- `--strategy`：策略简称（如 `S1`）。
- `--train/--test`：训练集与测试集回测结果JSON。
- `--max-dd`：最大回撤上限（小数）。
- `--max-profit-factor-delta`：训练/测试 PF 差值上限。
- `--max-winrate-delta`：训练/测试胜率差值上限。

### 3) PF/DD 分层阈值
- 保守（Conservative）：PF >= 1.25，最大回撤 <= 10%。
- 进取/混合（Progressive/Hybrid）：PF >= 1.18，最大回撤 <= 14%。
- 激进（Aggressive）：PF >= 1.10，最大回撤 <= 16%。

### 4) 交易频次与风格一致
- HFT：1m，短ROI，低冷却。
- MFT：15m，中等ROI。
- LFT：1h + 高周期锚点，长ROI。

### 5) Binance / Hyperliquid 约束
- Binance：配置模板为 USDT 永续、市价单、受限杠杆。
- Hyperliquid：逻辑不变，只替换交易所配置和币对，先缩小交易池。

## 统一回测（Backtest）+ 滚动验证（Walk-forward）命令
```bash
freqtrade backtesting \
  --config user_data/configs/S1_config_stub.json \
  --strategy S1_HFT_Conservative_MicroTrend_Scalper \
  --timerange 20230101-20240630 \
  --export trades \
  --backtest-filename user_data/backtest_results/S1_train.json

freqtrade backtesting \
  --config user_data/configs/S1_config_stub.json \
  --strategy S1_HFT_Conservative_MicroTrend_Scalper \
  --timerange 20240701-20241231 \
  --export trades \
  --backtest-filename user_data/backtest_results/S1_test.json

python scripts/validate_backtest_gates.py \
  --strategy S1 \
  --train user_data/backtest_results/S1_train.json \
  --test user_data/backtest_results/S1_test.json \
  --max-dd 0.10 \
  --max-profit-factor-delta 0.60 \
  --max-winrate-delta 0.12
```
参数说明：
- `freqtrade backtesting`：回测。
- `--config`：策略配置文件。
- `--strategy`：策略类名（必须和 `.py` 类名一致）。
- `--timerange`：时间区间（YYYYMMDD-YYYYMMDD）。
- `--export trades`：导出交易明细。
- `--backtest-filename`：输出回测JSON路径。

## 超参优化（Hyperopt）命令模板
```bash
freqtrade hyperopt \
  --config user_data/configs/S1_config_stub.json \
  --strategy S1_HFT_Conservative_MicroTrend_Scalper \
  --spaces buy sell stoploss trailing \
  --hyperopt-loss SharpeHyperOptLossDaily \
  --epochs 200
```
参数说明：
- `--spaces`：优化买入/卖出/止损/跟踪止损参数。
- `--hyperopt-loss`：优化目标函数。
- `--epochs`：迭代轮数，越大越慢但搜索更充分。

## Go / No-Go 检查清单
- [ ] 无 `shift(-N)`。
- [ ] OOS 退化在门限内。
- [ ] PF / DD 达到对应分层标准。
- [ ] 交易频次符合 HFT > MFT > LFT。
- [ ] 交易所约束验证通过（杠杆、最小下单金额、币对格式）。
- [ ] 模拟盘（Dry-run）至少跑满 7 天无故障。

## 修正记录
- 已核对文档中的策略类名、配置路径、验证脚本路径，与仓库现状一致；本文件无需额外命令修正。

### 成功判定
- 你能跑通“训练回测 + 测试回测 + gate 脚本”，并看到 `PASS: all gates satisfied`。

### 失败排查（最常见3项）
1. 本机未安装 `freqtrade`。
2. `--strategy` 类名拼写不一致。
3. 回测输出路径不存在或无写权限。

### 下一步动作
- 进入下一篇《Portfolio Playbook》执行组合层风控与配资。
