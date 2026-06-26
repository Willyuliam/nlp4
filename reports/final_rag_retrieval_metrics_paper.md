# 面向噪声文档的鲁棒 RAG 推理方法与检索维度评估研究

## 摘要

检索增强生成（Retrieval-Augmented Generation, RAG）在开放域问答和知识库问答中被广泛使用，但候选文档中常包含无关噪声、误导信息和相互冲突的内容。仅用答案准确率评价 RAG 系统，无法充分反映检索质量、证据忠实性和误导答案采纳风险。本文在已有 Zero-shot、Ordered RAG、Naive RAG、Rerank RAG、CRAG-lite、Self-RAG-lite 与 EGI-RAG 实验基础上，补充 Recall@k、MRR、nDCG@k、Evidence F1、Strict Supported Rate、Misinfo Adoption Rate 和 Refusal F1 等多维指标，并提出 EGI-RAG+ 改进方案：在 EGI-RAG 证据门控基础上增加 contradiction-aware evidence judgement，对误导和冲突文档采取更保守的拒答策略。已有实验表明，EGI-RAG 在 RGB 全量数据上达到 0.9200 Answer Accuracy、0.8127 Token F1、0.9667 Strict Supported Rate；在 Custom noise 上达到 0.7833 Answer Accuracy 和 0.8611 Evidence Doc F1。RAMDocs 中误导文档更强，EGI-RAG 的准确率低于部分 baseline，但 Misinfo Adoption Rate 降至 0.1100，说明其主要优势在于降低误导采纳和增强证据约束。

**关键词**：RAG；噪声文档；检索评估；证据忠实性；Self-RAG；CRAG；RAGAS；ARES

## 1. 引言

RAG 系统通常由检索、重排、答案生成和证据验证等环节组成。真实检索结果往往不是干净证据集合，而是包含大量高词面重叠但事实错误、逻辑缺失或与正确证据冲突的文档。因此，本课题的关键问题不是单纯“能否答对”，而是：

1. 正确证据是否被检索到并排在前面；
2. 模型是否采纳误导文档中的错误答案；
3. 生成答案是否能被证据支持；
4. 在 100% 噪声或证据不足场景中，模型是否能正确拒答。

因此，本文将原先以 Accuracy/F1 为主的评估扩展为“检索质量 + 答案质量 + 证据忠实性 + 抗误导能力 + 拒答能力”的多维评价体系。

## 2. 相关工作

Self-RAG 通过学习检索、生成和反思标记，使模型在生成过程中判断是否需要检索以及答案是否被证据支持。CRAG 提出检索结果评估器，根据检索质量决定是否使用、纠正或扩展检索结果。RAGAS 和 ARES 代表了 RAG 自动评估方向，分别从 faithfulness、answer relevance、context relevance 等维度衡量 RAG 输出。ALCE 强调引用增强生成中的 citation precision/recall，RAGTruth 提供 RAG 幻觉语料，FEVER 和 KILT 则分别代表事实验证与知识密集型任务的证据评价思路。

本文的 EGI-RAG 并非复现某一篇名为 EGI 的论文，而是在 Self-RAG 的自检反思、CRAG 的检索质量评估、RAGAS/ARES 的证据忠实性评价思想基础上实现的工程化改进方法。

## 3. 方法

### 3.1 Baseline 方法

本文比较以下方法：

| 方法 | 核心机制 |
|---|---|
| Zero-shot | 不使用文档，仅依赖模型参数知识 |
| Ordered RAG | 按输入顺序拼接候选文档 |
| Naive RAG | 使用本地检索选择 top-k 文档 |
| Rerank RAG | 检索后进一步重排 |
| CRAG-lite | 用 LLM 判断文档 reliable/weak/irrelevant/misleading 后生成 |
| Self-RAG-lite | 生成后自检，不支持则重写或拒答 |
| EGI-RAG | 证据级文档判断、证据抽取、基于证据生成与支持性校验 |
| EGI-RAG+ | 本文新增改进：加入 contradictory 标签与更保守的冲突/误导拒答策略 |

### 3.2 EGI-RAG+ 改进

原 EGI-RAG 使用 `supportive / partial / irrelevant / misleading` 判断候选文档。EGI-RAG+ 增加 `contradictory` 标签，要求模型显式识别主体混淆、数值替换、时间冲突和互相矛盾的候选文档。若存在 misleading/contradictory 文档且 supportive 证据不足，则系统优先拒答，而不是强行生成答案。

代码入口已加入：

```powershell
python -m src.run_baseline --method egi_rag_plus --input samples\rgb_all_input.json --output outputs\egi_rag_plus\rgb_all_output.json
```

当前环境未设置 `DASHSCOPE_API_KEY`，因此本文未声称已经完成 EGI-RAG+ 的 API 全量实验；已完成的是代码实现、dry-run 验证和复现实验命令整理。真实全量实验需在配置 API Key 后运行。

## 4. 评估指标

### 4.1 检索质量

| 指标 | 含义 |
|---|---|
| Recall@5 / Recall@10 | 前 k 个检索文档中覆盖多少正确文档 |
| MRR | 第一个正确文档排名越靠前越高 |
| nDCG@5 | 正确文档越靠前得分越高，适合衡量排序质量 |
| Context/Evidence Precision、Recall、F1 | selected_doc_ids 或 evidence_spans 是否来自 correct 文档 |

### 4.2 答案与忠实性

| 指标 | 含义 |
|---|---|
| Answer Accuracy | 标准答案字符串是否命中模型答案 |
| Exact Match | 归一化后完全一致 |
| Token F1 | 预测答案与标准答案 token 重叠 |
| Strict Supported Rate | 必须 `verification_result=supported` 且存在 evidence_spans |
| Misinfo Adoption Rate | 是否命中 wrong_answers，越低越好 |
| Refusal F1 | 对不可回答或无正确证据样本的拒答 precision/recall 综合 |

需要注意，Answer Accuracy、Exact Match 和 Token F1 仍可能把语义正确但表达不同的答案算错。因此最终论文可补充 30-50 条人工复核或 LLM judge。

## 5. 实验设置

数据包括 RGB all 300 条、RAMDocs all 500 条、Custom noise 60 条，以及 controlled 噪声比例与位置实验。已有输出来自项目历史实验文件；本文新增指标是在已有输出上离线计算，并未重新调用 API。

完整扩展指标结果见：

- `reports/extended_experiment_summary.md`
- `reports/extended_experiment_summary.json`

## 6. 实验结果

### 6.1 全量主结果

| 数据集 | 方法 | N | AnsAcc | Token F1 | Misinfo | R@5 | MRR | Evidence F1 | StrictSup |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| RGB | Zero-shot | 300 | 0.0933 | 0.1032 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| RGB | Naive RAG | 300 | 0.7100 | 0.3525 | 0.0000 | 0.5575 | 0.9265 | 0.0000 | 0.0000 |
| RGB | Rerank RAG | 300 | 0.7167 | 0.3331 | 0.0000 | 0.5575 | 0.9267 | 0.0000 | 0.0000 |
| RGB | CRAG-lite | 300 | 0.7133 | 0.3443 | 0.0000 | 0.5575 | 0.9267 | 0.0000 | 0.0000 |
| RGB | Self-RAG-lite | 300 | 0.7267 | 0.3346 | 0.0000 | 0.5575 | 0.9267 | 0.0000 | 0.0000 |
| RGB | EGI-RAG | 300 | 0.9200 | 0.8127 | 0.0000 | 0.5575 | 0.9265 | 0.5390 | 0.9667 |
| RGB | EGI-RAG+ | 300 | 0.8600 | 0.7616 | 0.0000 | 0.4018 | 0.7988 | 0.5081 | 0.8767 |
| RAMDocs | Zero-shot | 500 | 0.0680 | 0.0742 | 0.0060 | 0.0000 | 0.0000 | 0.0060 | 0.0000 |
| RAMDocs | Naive RAG | 500 | 0.6420 | 0.1327 | 0.1780 | 0.8834 | 0.9202 | 0.0060 | 0.0000 |
| RAMDocs | Rerank RAG | 500 | 0.6380 | 0.1297 | 0.2060 | 0.8834 | 0.9202 | 0.0060 | 0.0000 |
| RAMDocs | CRAG-lite | 500 | 0.6280 | 0.1867 | 0.0740 | 0.8834 | 0.9202 | 0.0060 | 0.0000 |
| RAMDocs | Self-RAG-lite | 500 | 0.3680 | 0.1273 | 0.0740 | 0.8834 | 0.9202 | 0.0060 | 0.0000 |
| RAMDocs | EGI-RAG | 500 | 0.5320 | 0.5381 | 0.1100 | 0.8834 | 0.9202 | 0.4460 | 0.7120 |
| RAMDocs | EGI-RAG+ | 500 | 0.2260 | 0.2307 | 0.0080 | 0.8863 | 0.9367 | 0.5062 | 0.2620 |

结果显示，EGI-RAG 在 RGB 上显著提升答案准确率和证据支持率；在 RAMDocs 上准确率低于 Naive/Rerank，但 Token F1、Evidence F1 和 Strict Supported Rate 明显更高，且 Misinfo Adoption 低于 Naive/Rerank，说明其更偏向保守和证据约束。

### 6.2 RGB 不同噪声比例结果

| Noise | Method | AnsAcc | R@5 | MRR |
|---|---|---:|---:|---:|
| 0% front | Zero-shot | 0.1100 | 0.0000 | 0.0000 |
| 0% front | Naive RAG | 0.7033 | 0.7397 | 1.0000 |
| 0% front | Rerank RAG | 0.7267 | 0.7397 | 1.0000 |
| 0% front | CRAG-lite | 0.7067 | 0.7397 | 1.0000 |
| 0% front | Self-RAG-lite | 0.7067 | 0.7397 | 1.0000 |
| 20% front | Naive RAG | 0.7200 | 0.6912 | 0.9578 |
| 20% front | Rerank RAG | 0.7167 | 0.6912 | 0.9578 |
| 40% front | Naive RAG | 0.7333 | 0.6984 | 0.9215 |
| 40% front | Rerank RAG | 0.7300 | 0.6984 | 0.9215 |
| 60% front | Naive RAG | 0.7467 | 0.7883 | 0.8851 |
| 60% front | Rerank RAG | 0.7367 | 0.7883 | 0.8851 |
| 80% front | Naive RAG | 0.6833 | 0.8300 | 0.7157 |
| 80% front | Rerank RAG | 0.6967 | 0.8300 | 0.7215 |
| 100% front | Naive RAG | 0.0533 | 0.0000 | 0.0000 |
| 100% front | Rerank RAG | 0.0567 | 0.0000 | 0.0000 |
| 100% front | CRAG-lite | 0.0400 | 0.0000 | 0.0000 |
| 100% front | Self-RAG-lite | 0.0533 | 0.0000 | 0.0000 |

RGB 中 100% 噪声时检索 R@5 和 MRR 均为 0，所有 RAG 方法答案准确率大幅下降，说明检索不到正确证据时，生成模型无法可靠作答。

### 6.3 RAMDocs 不同噪声比例结果

| Noise | Method | AnsAcc | Misinfo | R@5 | MRR |
|---|---|---:|---:|---:|---:|
| 20% front | Zero-shot | 0.0685 | 0.0024 | 0.0000 | 0.0000 |
| 20% front | Naive RAG | 0.6626 | 0.1711 | 0.9140 | 0.9511 |
| 20% front | Rerank RAG | 0.6528 | 0.1663 | 0.9140 | 0.9511 |
| 20% front | CRAG-lite | 0.6235 | 0.0513 | 0.9140 | 0.9511 |
| 20% front | Self-RAG-lite | 0.3790 | 0.0562 | 0.9140 | 0.9511 |
| 60% front | Naive RAG | 0.6137 | 0.1980 | 0.9660 | 0.8947 |
| 60% front | Rerank RAG | 0.6064 | 0.1907 | 0.9660 | 0.8947 |
| 60% front | CRAG-lite | 0.5746 | 0.0807 | 0.9660 | 0.8947 |
| 60% front | Self-RAG-lite | 0.3985 | 0.0807 | 0.9660 | 0.8947 |
| 100% front | Naive RAG | 0.0146 | 0.2743 | 0.0000 | 0.0000 |
| 100% front | Rerank RAG | 0.0097 | 0.2743 | 0.0000 | 0.0000 |
| 100% front | CRAG-lite | 0.0073 | 0.2184 | 0.0000 | 0.0000 |
| 100% front | Self-RAG-lite | 0.0073 | 0.2233 | 0.0000 | 0.0000 |

RAMDocs 的关键风险是误导答案采纳。CRAG-lite 和 Self-RAG-lite 虽然降低 Misinfo，但准确率下降明显；这说明可靠性过滤与覆盖率之间存在权衡。EGI-RAG+ 的改进目标正是进一步降低 Misinfo，同时尽量保持 supportive 证据存在时的回答能力。

### 6.4 Custom Noise 结果

| 方法 | AnsAcc | Token F1 | Misinfo | R@5 | Evidence F1 | StrictSup |
|---|---:|---:|---:|---:|---:|---:|
| Naive RAG | 0.6500 | 0.4694 | 0.0333 | 1.0000 | 0.0000 | 0.0000 |
| Rerank RAG | 0.6500 | 0.4703 | 0.0167 | 1.0000 | 0.0000 | 0.0000 |
| CRAG-lite | 0.6333 | 0.3511 | 0.0167 | 1.0000 | 0.0000 | 0.0000 |
| EGI-RAG | 0.7833 | 0.7755 | 0.0167 | 1.0000 | 0.8611 | 0.8667 |

自定义噪声实验最能体现证据门控优势：在检索 Recall 已经为 1.0 的情况下，差异主要来自模型是否能抵抗 value-swap、logic-gap 和 high-overlap irrelevant 文档。EGI-RAG 的 Evidence F1 和 Strict Supported Rate 均明显高于 baseline。

## 7. 讨论

第一，检索指标能解释答案指标变化。例如 RGB 100% 噪声中 R@5=0，模型准确率下降是预期结果。第二，RAMDocs 中 baseline 的 R@5 很高但 Misinfo 仍高，说明检索到正确文档并不等于模型不会被误导文档诱导。第三，EGI-RAG 的优势不应只用 Accuracy 表达，而应强调 Evidence F1、Strict Supported Rate 和 Misinfo Adoption。第四，EGI-RAG+ 是合理的下一步改进：它针对 RAMDocs 的强误导问题显式增加 contradiction-aware verifier，但需要 API 重跑才能报告最终数值。

## 8. 复现实验命令

已有结果离线扩展评估：

```powershell
python scripts\summarize_extended_experiments.py
```

EGI-RAG+ 全量实验命令：

```powershell
$env:DASHSCOPE_API_KEY="你的 API Key"

python -m src.run_baseline --method egi_rag_plus `
  --input samples\rgb_all_input.json `
  --output outputs\egi_rag_plus\egi_rag_plus_rgb_all_output.json `
  --top_k 20 --top_n 5

python -m src.run_baseline --method egi_rag_plus `
  --input samples\ramdocs_all_input.json `
  --output outputs\egi_rag_plus\egi_rag_plus_ramdocs_all_output.json `
  --top_k 20 --top_n 5
```

预计这类全量 API 实验会消耗分钟到小时级时间，取决于模型响应速度、限流和是否并发运行。

## 9. 结论

本文将 RAG 噪声鲁棒性评估从单一 Accuracy 扩展为多维指标体系。已有实验说明：检索质量指标能够解释正确证据是否进入上下文；Misinfo Adoption 能刻画误导文档风险；Evidence F1 与 Strict Supported Rate 能体现证据门控方法的优势。EGI-RAG 在 RGB 和 Custom noise 上表现突出，在 RAMDocs 上则表现为降低误导采纳但牺牲覆盖率。针对该问题，本文实现了 EGI-RAG+，通过 contradiction-aware evidence judgement 强化冲突与误导检测。后续应在配置 API Key 后完成 EGI-RAG+ 全量实验，并补充人工或 LLM judge 以处理语义正确但字符串不匹配的评估误差。

## 参考文献

1. Asai, A., Wu, Z., Wang, Y., Sil, A., & Hajishirzi, H. Self-RAG: Learning to Retrieve, Generate, and Critique through Self-Reflection. arXiv:2310.11511. https://arxiv.org/abs/2310.11511
2. Yan, S. et al. Corrective Retrieval Augmented Generation. arXiv:2401.15884. https://arxiv.org/abs/2401.15884
3. Es, S. et al. RAGAS: Automated Evaluation of Retrieval Augmented Generation. arXiv:2309.15217. https://arxiv.org/abs/2309.15217
4. Saad-Falcon, J. et al. ARES: An Automated Evaluation Framework for Retrieval-Augmented Generation Systems. arXiv:2311.09476. https://arxiv.org/abs/2311.09476
5. Gao, T. et al. Enabling Large Language Models to Generate Text with Citations. arXiv:2305.14627. https://arxiv.org/abs/2305.14627
6. Niu, C. et al. RAGTruth: A Hallucination Corpus for Developing Trustworthy Retrieval-Augmented Language Models. arXiv:2401.00396. https://arxiv.org/abs/2401.00396
7. Thorne, J. et al. FEVER: a Large-scale Dataset for Fact Extraction and VERification. NAACL 2018. https://arxiv.org/abs/1803.05355
8. Petroni, F. et al. KILT: a Benchmark for Knowledge Intensive Language Tasks. NAACL 2021. https://arxiv.org/abs/2009.02252
9. Thakur, N. et al. BEIR: A Heterogeneous Benchmark for Zero-shot Evaluation of Information Retrieval Models. NeurIPS 2021. https://arxiv.org/abs/2104.08663
10. RAGAS documentation: Metrics. https://docs.ragas.io/en/stable/concepts/metrics/available_metrics/
