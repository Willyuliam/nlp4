# 组员 C：EGI-RAG 中期方案

## 1. 方法概述

**EGI-RAG**（Evidence-Gated Iterative RAG，证据门控迭代式 RAG）面向噪声文档场景，在生成答案前先做文档评分与证据抽取，生成后再做一致性校验，必要时迭代修正。

与 Naive RAG / Rerank RAG 的区别：

| 阶段 | Naive RAG | EGI-RAG |
|---|---|---|
| 文档筛选 | 直接取 top-k | 文档评分 + 可信度过滤 |
| 答案生成 | 基于整篇文档 | 仅基于证据句 |
| 生成后校验 | 无 | 答案-证据一致性校验 |
| 失败处理 | 无 | 重新选文档或拒答 |

## 2. 系统框架

```text
问题输入
  -> 本地轻量 rerank (top_k -> top_n)
  -> Document Scorer (LLM 评分)
  -> 过滤 contradictory / misleading 文档
  -> Evidence Extractor (抽取证据句)
  -> Answer Generator (仅基于证据)
  -> Consistency Verifier (校验支持性)
  -> Iterative Corrector (重选文档 / 拒答)
  -> 输出答案 + 证据 + 评分 + 迭代记录
```

## 3. 模块设计

### 3.1 Document Scorer

对每篇候选文档输出：

- `label`: directly_supportive / partially_relevant / irrelevant / contradictory / misleading / insufficient
- `score`: 0~1
- `reason`: 简短理由

### 3.2 Evidence Extractor

从高分文档中抽取可直接支持答案的原文证据句，输出 `evidence_spans`。

### 3.3 Answer Generator

只允许基于证据句生成答案；无足够证据时回答“无法根据给定信息确定”。

### 3.4 Consistency Verifier

检查答案是否被证据支持，输出：

- `supported`
- `unsupported`
- `conflict`
- `insufficient_evidence`

### 3.5 Iterative Corrector

校验失败时，根据文档评分重新选择文档或触发拒答，默认最多 2 轮。

## 4. 代码结构

```text
src/egi_rag/
  prompts.py      # 各模块 prompt
  json_utils.py   # LLM JSON 解析
  pipeline.py     # 完整流程
src/run_egi_rag.py
src/analyze_cases.py
scripts/run_member_c_midterm.ps1
```

## 5. 运行命令

```powershell
conda activate type3
$env:DASHSCOPE_API_KEY="你的百炼APIKey"

# 小规模正式运行
python -m src.run_egi_rag --input samples/rgb_input.json --output outputs/midterm/rgb_egi_rag_output.json --limit 10

# 无 API Key 时 dry run
python -m src.run_egi_rag --input samples/rgb_input.json --output outputs/midterm/rgb_egi_rag_dryrun.json --limit 3 --dry_run

# 一键自动化
.\scripts\run_member_c_midterm.ps1 -Limit 10
.\scripts\run_member_c_midterm.ps1 -DryRun -Limit 3
```

## 6. 输出格式

```json
{
  "id": "rgb_0000",
  "method": "EGI-RAG",
  "answer": "Karolina Muchova",
  "selected_doc_ids": ["doc_5", "doc_1"],
  "evidence_spans": [{"doc_id": "doc_5", "text": "..."}],
  "doc_scores": [{"doc_id": "doc_5", "label": "directly_supportive", "score": 0.95, "reason": "..."}],
  "iteration_count": 1,
  "verification_result": "supported",
  "iteration_log": []
}
```

## 7. 消融实验变体

通过 `--variant` 切换：

- `full`
- `wo_doc_scorer`
- `wo_evidence_extraction`
- `wo_verifier`
- `wo_iteration`

## 8. 中期预实验计划

1. 在 RGB 小样本（10~30 条）上对比 Naive RAG 与 EGI-RAG。
2. 自动生成 2~5 个“矫正前后对比”案例（`reports/egi_case_comparison.md`）。
3. 统计 EGI-RAG 是否更少采纳 misinfo / noise 文档。

## 9. 相关方法（文献整理）

- **CRAG**：检索质量评估 + 外部知识补偿，强调检索可信度门控。
- **Self-RAG**：生成后反思与自我校验，可修正无证据回答。
- **RAMDocs**：系统分析 misinformation、noise、ambiguity 对 RAG 的影响。
- **RARE / Magic Mushroom**：关注检索误导与证据冲突下的鲁棒推理。

EGI-RAG 结合“生成前证据门控 + 生成后一致性校验 + 迭代修正”，针对高噪声 RAG 场景更强调可解释性。

## 10. 与组员 A/B 的接口

- 输入：沿用 `samples/*_input.json`
- baseline 对比：读取 B 的 `outputs/midterm/rgb_naive_rag_output.json`
- 评估：将 EGI 输出交给 A 的评估脚本计算 Accuracy / Evidence Selection / Faithfulness
