# 组员 B Baseline 完整运行汇总

## 运行环境

- Conda 环境：`type3`
- 模型平台：Qwen/百炼 API
- 模型：`qwen3.5-122b-a10b`
- 配置文件：`configs/model_config.example.yaml`
- 输入数据目录：`samples/`
- 输出目录：`outputs/midterm/`

## 已完成输出

| 数据集 | 方法 | 输入样本数 | 输出文件 | 错误数 | 状态 |
|---|---|---:|---|---:|---|
| RGB | Zero-shot | 30 | `outputs/midterm/rgb_zero_shot_output.json` | 0 | 完成 |
| RGB | Naive RAG | 30 | `outputs/midterm/rgb_naive_rag_output.json` | 0 | 完成 |
| RGB | Rerank RAG | 30 | `outputs/midterm/rgb_rerank_rag_output.json` | 0 | 完成 |
| RAMDocs | Zero-shot | 20 | `outputs/midterm/ramdocs_zero_shot_output.json` | 0 | 完成 |
| RAMDocs | Naive RAG | 20 | `outputs/midterm/ramdocs_naive_rag_output.json` | 0 | 完成 |
| RAMDocs | Rerank RAG | 20 | `outputs/midterm/ramdocs_rerank_rag_output.json` | 0 | 完成 |
| CONFLICTS | Zero-shot | 20 | `outputs/midterm/conflicts_zero_shot_output.json` | 0 | 完成 |
| CONFLICTS | Naive RAG | 20 | `outputs/midterm/conflicts_naive_rag_output.json` | 0 | 完成 |
| CONFLICTS | Rerank RAG | 20 | `outputs/midterm/conflicts_rerank_rag_output.json` | 1 | 完成，保留错误分析 |

共生成 210 条 baseline 记录，其中 209 条成功返回模型答案，1 条因平台内容安全检查被拦截。

## 残留错误分析

失败样本：

- 数据集：CONFLICTS
- 方法：Rerank RAG
- 样本 ID：`conflicts_0019`
- 问题：`who has been the longest serving chief minister`
- Rerank 选中文档：`doc_2`, `doc_4`, `doc_6`, `doc_1`, `doc_5`
- 错误类型：`InternalError.Algo.DataInspectionFailed`
- 平台返回：`Input text data may contain inappropriate content.`

判断：

- 该失败不是代码错误，也不是输入 JSON 字段错误。
- 该失败不是网络超时。此前超时样本已经通过 `--resume` 补跑成功。
- 这是 Qwen/百炼平台对某条 prompt 或上下文内容触发的数据安全检查，属于 API 平台侧拦截。
- 该样本已经失败超过一次，按运行规则不再重复调用，保留错误记录用于报告说明。

对实验的影响：

- RGB 和 RAMDocs 三组 baseline 全部成功，可作为中期核心实验结果。
- CONFLICTS 主要用于冲突案例分析；其中 1 条 Rerank RAG 失败不影响其他 19 条案例输出。
- 成员 A 在计算指标时应跳过或单独统计 `error != null` 的样本。

建议处理：

- 中期报告中将该条记为“平台内容安全拦截导致的无效输出”。
- 若最终阶段必须覆盖该样本，可以尝试只使用更少上下文、改写 prompt、或人工清洗触发拦截的上下文；但中期不建议继续重复调用。

## 已完成的组员 B 计划项

- 已搭建基础 Python 项目结构。
- 已实现 Qwen/百炼 API 调用封装。
- 已实现 Zero-shot、Naive RAG、Rerank RAG。
- 已实现本地轻量 rerank，不依赖 embedding 下载。
- 已统一输出格式，便于成员 A 按 `id` 对齐评估。
- 已使用 `samples/` 中 RGB、RAMDocs、CONFLICTS 实际数据完整运行并保存输出。
- 已增加逐条保存和 `--resume`，避免长任务中断导致结果丢失。
