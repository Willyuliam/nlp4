# EGI-RAG 方法来源、复现方向与评估改进说明

## 1. EGI-RAG 参考了什么论文

当前项目中的 EGI-RAG（Evidence-Gated Iterative RAG）不是严格复现某一篇论文的官方算法，而是把多篇 RAG 鲁棒性与评估论文中的核心思想组合成一个工程化方法。它更适合在论文报告中表述为“基于现有鲁棒 RAG 思想的改进方法”，而不是“复现 EGI-RAG 论文”。

与当前实现关系最紧密的论文如下：

| 论文/框架 | 可参考思想 | 与本项目 EGI-RAG 的对应关系 |
|---|---|---|
| Self-RAG: Learning to Retrieve, Generate, and Critique through Self-Reflection | 按需检索、生成后自我反思、检查答案是否被证据支持 | EGI-RAG 的 verifier、iteration/correction 与 Self-RAG 的自检思想接近，但本项目未训练 reflection tokens，而是用 prompt 调用大模型实现 |
| Corrective Retrieval Augmented Generation (CRAG) | 对检索结果质量进行评估，根据结果触发纠正动作，并过滤无关信息 | EGI-RAG 的 document scorer 和 reselect/refuse 机制与 CRAG 的 retrieval evaluator 思路接近 |
| RAGAS | 从 context relevance、faithfulness、answer quality 等维度评估 RAG | 本项目新增指标可对齐 RAGAS 的 answer faithfulness、context precision/recall 思路 |
| ARES | 使用自动 judge 分别评估 context relevance、answer faithfulness、answer relevance | 后续可引入 LLM judge 或轻量判别器，替代当前过粗的字符串匹配 |
| ALCE / 引用增强生成评估 | 关注生成内容是否有引用支撑、引用是否覆盖答案 | EGI-RAG 输出 evidence_spans，可进一步计算 citation precision/recall |
| FEVER / fact verification | 将事实判断分为 supported、refuted、not enough info | EGI-RAG verifier 的 supported / conflict / insufficient_evidence 与事实验证任务一致 |

可写入报告的准确表述：

> 本文提出的 EGI-RAG 并非对单一论文方法的直接复现，而是在 Self-RAG 的生成后反思、CRAG 的检索质量评估、RAGAS/ARES 的证据忠实性评价思想基础上，面向噪声文档场景设计的证据门控迭代推理框架。其核心改进是将“文档评分-证据抽取-答案生成-证据校验-拒答/重选”显式串联，并在输出中保存证据链与校验结果。

## 2. 可以复现哪些论文，或者做哪些改进

### 2.1 最推荐的复现路线

建议不要声称“复现 EGI-RAG 论文”，因为 EGI-RAG 是本项目自定义名称。更稳妥的路线是：

1. 复现 CRAG-lite：已有 `crag_lite`，可以完善为更接近 CRAG 的三分类检索评估器：`correct / ambiguous / incorrect`。
2. 复现 Self-RAG-lite：已有 `self_rag_lite`，可以把输出改成更明确的 reflection decisions，例如 `retrieve`、`is_supported`、`is_useful`。
3. 在二者基础上提出 EGI-RAG：加入显式 evidence extraction 与 verifier，作为本项目改进方法。
4. 做消融实验：`wo_doc_scorer`、`wo_evidence_extraction`、`wo_verifier`、`wo_iteration`。项目代码里已经支持这些 variant。

### 2.2 可写成创新点的改进

| 改进方向 | 实现方式 | 预期贡献 |
|---|---|---|
| Contradiction-aware verifier | 在 verifier 中加入“若证据之间冲突，不能直接采纳任一答案”规则 | 降低 RAMDocs 强误导场景下的 misinfo adoption |
| Evidence-only answer generation | 答案生成只读取 evidence_spans，不读取全文 | 减少高重叠噪声对模型的诱导 |
| Answerable/unanswerable split | 有标准答案和无标准答案分开评估 | 避免把不可回答样本混入普通 accuracy |
| Evidence precision/recall/F1 | 用 correct doc id 评估 selected_doc_ids/evidence_spans | 比单纯 answer accuracy 更能体现 RAG 质量 |
| Refusal precision/recall/F1 | 对无答案或无正确证据样本单独评估拒答质量 | 适合 100% 噪声和 Conflicts 场景 |
| LLM judge 评估 | 参考 RAGAS/ARES 设计 answer relevance、faithfulness judge | 弥补字符串匹配对同义表达不友好的问题 |

## 3. EGI-RAG 是否跑了全量数据集

本地文件核对结果如下：

| 数据集 | 输入样本数 | 参考答案数 | EGI 输出数 | 状态 |
|---|---:|---:|---:|---|
| RGB all | 300 | 300 | 300 | 已跑全量 |
| RAMDocs all | 500 | 500 | 500 | 已跑全量 |
| Custom noise all | 60 | 60 | 60 | 已跑完整补充集 |
| Controlled RGB/RAMDocs | 多组 100 条 | 对应 reference | 对应输出 | 已跑关键压力测试 |
| Conflicts all | 458 | 237 有标准答案，221 无标准答案 | 未作为主表全量评估 | 不建议直接用普通 accuracy 做主结论 |

结论：不能再写“EGI 没有跑全量数据集”。准确说法应该是：

> EGI-RAG 已完成 RGB 300 条和 RAMDocs 500 条全量实验，也完成 custom noise 60 条和若干 controlled 压力测试；Conflicts 因为大量样本缺少标准答案，目前更适合作为冲突/不可回答案例分析，不适合直接纳入普通 Accuracy 主表。

## 4. 当前评估指标的问题

原始 `src/evaluation/evaluate_outputs.py` 存在几个问题：

1. `answer_accuracy` 主要是字符串包含匹配，不能处理同义表达、别名、日期格式变化。
2. `faithfulness` 过宽，只要有 `evidence_spans` 或 `selected_doc_ids` 命中，就可能算 faithful，不等价于答案真的被证据支持。
3. 无标准答案样本和有标准答案样本混合计算，会让 Conflicts 或 100% 噪声场景解释困难。
4. 拒答质量只有 `refusal_accuracy`，不能区分拒答 precision 和 recall。
5. 证据质量只看是否命中任一正确文档，缺少 precision/recall/F1。

## 5. 已新增的扩展评估脚本

已新增：

```text
scripts/evaluate_rag_extended.py
```

新增指标包括：

| 指标 | 含义 |
|---|---|
| answer_accuracy_answerable | 只在有标准答案样本上计算答案命中率 |
| exact_match_answerable | 只在有标准答案样本上计算完全匹配 |
| token_f1_answerable | 只在有标准答案样本上计算 token F1 |
| misinformation_adoption_rate | 是否命中 wrong_answers |
| refusal_precision / recall / F1 | 评估该拒答时是否真的应该拒答 |
| selected_context_precision / recall / F1 | 评估选择文档是否命中 correct 文档 |
| evidence_doc_precision / recall / F1 | 评估 evidence_spans 来自哪些 correct 文档 |
| evidence_rate | 是否给出证据 |
| strict_supported_rate | 必须 verifier=supported 且存在 evidence_spans 才算支持 |

示例命令：

```powershell
python scripts\evaluate_rag_extended.py `
  --input samples\rgb_all_input.json `
  --reference samples\rgb_all_reference.json `
  --output outputs\egi_rag\rgb\egi_rag_rgb_all_output.json `
  --save outputs\egi_rag\rgb\egi_rag_rgb_all_extended_metrics.json
```

## 6. 扩展评估结果

| 数据集 | Answer Acc | Exact Match | Token F1 | Misinfo | Evidence Doc F1 | Evidence Rate | Strict Supported |
|---|---:|---:|---:|---:|---:|---:|---:|
| RGB all | 0.9200 | 0.6200 | 0.8127 | 0.0000 | 0.5390 | 1.0000 | 0.9667 |
| RAMDocs all | 0.5320 | 0.4720 | 0.5381 | 0.1100 | 0.4460 | 0.8920 | 0.7120 |
| Custom noise all | 0.7833 | 0.6833 | 0.7755 | 0.0167 | 0.8611 | 0.9833 | 0.8667 |

这组指标比旧 accuracy 更有解释力：RGB 的答案准确率高，但 evidence doc recall 不高，说明 EGI 常选中少量关键正确文档而非覆盖全部正确文档；RAMDocs 的 strict supported rate 和 evidence F1 明显下降，说明误导文档确实更难处理；custom noise 的 evidence doc F1 高，支持“证据门控对自定义噪声有效”的结论。

## 7. 为什么有些数据没有标准答案

主要是 Conflicts 数据集造成的。项目转换脚本 `scripts/step3_convert_and_sample.py` 中，`convert_conflicts` 会尝试从以下字段读取答案：

```python
gold_raw = (
    item.get("correct_answer")
    or item.get("answer")
    or item.get("gold_answer")
    or ""
)
gold_answers = [gold_raw.strip()] if gold_raw.strip() else []
```

如果原始样本没有这些字段，`gold_answers` 就会是空数组。当前统计为：

| 数据集 | 总数 | 有标准答案 | 无标准答案 |
|---|---:|---:|---:|
| RGB all | 300 | 300 | 0 |
| RAMDocs all | 500 | 500 | 0 |
| Conflicts all | 458 | 237 | 221 |
| Conflicts sample | 20 | 9 | 11 |

原因不是转换脚本漏掉所有答案，而是 Conflicts 数据本身包含不少更接近“冲突识别/不可回答/信息不足”的样本。它们适合用拒答率、冲突识别准确率、证据一致性来评估，不适合和 RGB/RAMDocs 一样直接算普通答案准确率。

## 8. 下一步建议

优先级从高到低：

1. 在报告中把 EGI-RAG 定位为“基于 Self-RAG、CRAG、RAGAS/ARES 思想的改进方法”，不要说成直接复现某篇 EGI 论文。
2. 将 `scripts/evaluate_rag_extended.py` 的结果加入论文实验部分，替换或补充旧的 faithfulness/refusal 指标。
3. 对 Conflicts 单独建表：只统计 237 条有答案样本的 answer accuracy；对 221 条无答案样本统计 refusal precision/recall/F1。
4. 补一个 contradiction-aware verifier，把 RAMDocs 的 misinfo adoption 作为主要优化目标。
5. 选择 30-50 条样本做人工复核或 LLM judge，作为字符串匹配指标的补充。

## 9. 参考文献与资料

- Self-RAG: Learning to Retrieve, Generate, and Critique through Self-Reflection. https://arxiv.org/abs/2310.11511
- Corrective Retrieval Augmented Generation. https://arxiv.org/abs/2401.15884
- RAGAS: Automated Evaluation of Retrieval Augmented Generation. https://arxiv.org/abs/2309.15217
- ARES: An Automated Evaluation Framework for Retrieval-Augmented Generation Systems. https://arxiv.org/abs/2311.09476
- RAGAS official documentation. https://docs.ragas.io/en/stable/
- ARES GitHub repository. https://github.com/stanford-futuredata/ARES
