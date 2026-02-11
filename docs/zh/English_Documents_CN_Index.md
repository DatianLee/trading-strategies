# English Documents（英文文档）中文索引导航

> 对应英文原文：[`docs/README.md`](../README.md)  
> 上一篇：[`docs/zh/Research_Contract_Implementation_CN.md`](./Research_Contract_Implementation_CN.md) ｜ 下一篇：[`docs/zh/Final_Production_Candidate_Package_CN.md`](./Final_Production_Candidate_Package_CN.md)

本页是英文文档总入口的“完整中文对照导航页”，用于中英双向跳转。

## 一、总入口
- 英文总入口（English Docs Home）：[`docs/README.md`](../README.md)
- 中文总入口（本页）：[`docs/zh/English_Documents_CN_Index.md`](./English_Documents_CN_Index.md)

## 二、逐篇对照
1. Final Production Candidate Package  
   - EN: [`docs/final_production_candidate_package.md`](../final_production_candidate_package.md)  
   - CN: [`docs/zh/Final_Production_Candidate_Package_CN.md`](./Final_Production_Candidate_Package_CN.md)

2. Portfolio Playbook  
   - EN: [`docs/Portfolio Playbook.md`](../Portfolio%20Playbook.md)  
   - CN: [`docs/zh/Portfolio_Playbook_CN.md`](./Portfolio_Playbook_CN.md)

3. Operations Runbook  
   - EN: [`docs/operations_runbook.md`](../operations_runbook.md)  
   - CN: [`docs/zh/Operations_Runbook_CN.md`](./Operations_Runbook_CN.md)

4. S5/S7 Validation Playbook  
   - EN: [`docs/S5_S7_validation_playbook.md`](../S5_S7_validation_playbook.md)  
   - CN: [`docs/zh/S5_S7_Validation_Playbook_CN.md`](./S5_S7_Validation_Playbook_CN.md)

5. Research Contract v1.0  
   - EN: [`docs/Research_Contract_v1.0.md`](../Research_Contract_v1.0.md)  
   - CN: [`docs/zh/Research_Contract_v1_CN.md`](./Research_Contract_v1_CN.md)

6. Research Contract Implementation  
   - EN: [`docs/Research_Contract_v1_Implementation.md`](../Research_Contract_v1_Implementation.md)  
   - CN: [`docs/zh/Research_Contract_Implementation_CN.md`](./Research_Contract_Implementation_CN.md)

7. English documents（总入口/导航页）  
   - EN: [`docs/README.md`](../README.md)  
   - CN: [`docs/zh/English_Documents_CN_Index.md`](./English_Documents_CN_Index.md)

## 三、维护规则（给执行人员）
- 新增英文文档时：必须同步新增 `docs/zh/*_CN.md`。
- 修改英文命令时：中文文档保留原命令，并在命令下更新“参数说明”。
- 任一中英文文件改动后：更新 `TRANSLATION_COVERAGE_REPORT.md`。

## 修正记录
- 索引中的路径均已按当前仓库实际文件名核对。

### 成功判定
- 你能从任意一篇英文文档跳到对应中文文档，也能从中文文档跳回英文原文。

### 失败排查（最常见3项）
1. 文件名含空格未做 URL 编码（如 `Portfolio%20Playbook.md`）。
2. 新增文档后索引未更新。
3. 只做单向链接（没有双向互链）。

### 下一步动作
- 打开覆盖率报告，核对“覆盖率=100%”和命令检查结果。
