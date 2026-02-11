# S5/S7 Validation Playbook（验证手册）中文执行版

> 对应英文原文：[`docs/S5_S7_validation_playbook.md`](../S5_S7_validation_playbook.md)  
> 上一篇：[`docs/zh/Operations_Runbook_CN.md`](./Operations_Runbook_CN.md) ｜ 下一篇：[`docs/zh/Research_Contract_v1_CN.md`](./Research_Contract_v1_CN.md)

## 1) 滚动前推验证（Walk-forward）模板
建议窗口：A/B/C/D（与英文一致），所有窗口必须使用相同交易所、币对、费率假设。

```bash
freqtrade backtesting \
  -c user_data/configs/S5_config_stub.json \
  --strategy S5_LFT_Conservative_MTF_TrendReversal \
  --timerange 20230101-20230630 \
  --export trades
```
参数说明：
- `-c`：配置文件路径。
- `--strategy`：策略类名。
- `--timerange`：回测区间。
- `--export trades`：导出交易记录供后续统计。

S6/S7 只需替换策略类名和配置文件。

验收条件：
- 盈利窗口占比 >= 60%
- 测试集中位 Sharpe >= 0.8
- 最差窗口最大回撤 <= 18%
- 至少 70% 测试窗口 PF >= 1.15

## 2) 蒙特卡洛（Monte Carlo）交易序列压力测试
步骤：导出每窗口交易收益 -> 每策略每窗口做 `N=2000` 重采样/置换 -> 重建权益曲线 -> 对比分位数分布。

验收条件：
- 基准终值 > MC 35 分位
- MC 95 分位最大回撤 <= 25%
- 终值低于初始资金概率 <= 20%

## 3) 参数稳定性热力图
- S5：`adx_min` × `volatility_ceiling`，指标为 OOS PF 中位数。
- S6：`momentum_window` × `rs_threshold`，指标为 OOS Sharpe 中位数。
- S7：波动爆发分位 × 成交量脉冲倍数，指标为 OOS Calmar。

验收条件：
- 至少 25% 网格点满足 PF>=1.1 且 MDD<=20%
- 最优点不高于“上四分位中位数”的 135%
- 邻格退化平滑（±1 格下跌不超过 20%）

## 4) 客观拒绝标准（硬失败）
任一命中即拒绝：
1. >=40% 测试窗口净利润 <=0
2. 任一窗口 MDD >20%
3. >=50% 测试窗口 PF <1.05
4. MC 的 P(终值<初值) >25%
5. 交易时长中位：S5/S6 >96h 或 S7 >24h
6. 单币对贡献 >55% 总PnL
7. 模拟前推阶段连续 >3 周触发 kill-switch

## 5) Notebook 实现骨架
```python
trades = load_trades_csv("results/s5_windowA_trades.csv")
metrics = compute_metrics(trades)
sim_curves = monte_carlo_shuffle(trades["return"], n=2000, mode="bootstrap")
mc_stats = summarize_mc(sim_curves)
heatmap = aggregate_hyperopt_grid("results/s5_grid.json")
plot_heatmap(heatmap, x="adx_min", y="volatility_ceiling", value="oos_pf")
status = evaluate_rejection_rules(metrics, mc_stats)
print(status)
```
参数说明：
- `n=2000`：模拟次数。
- `mode="bootstrap"`：有放回采样。
- `aggregate_hyperopt_grid(...)`：汇总网格实验结果。

## 修正记录
- 标题原文写 S5/S6/S7，本文件名按任务要求保持 `S5_S7`，正文保留 S5/S6/S7 全覆盖，无内容删减。

### 成功判定
- 你能产出每个窗口的回测结果、MC 分布图、热力图，并通过/拒绝规则给出明确结论。

### 失败排查（最常见3项）
1. 各窗口费率/滑点不一致，导致结果不可比。
2. 只看最优窗口，忽略全窗口一致性。
3. MC 只做少量样本（如100次）导致统计不稳定。

### 下一步动作
- 转到《Research Contract v1.0》确认研究约束，再进入实现文档。
