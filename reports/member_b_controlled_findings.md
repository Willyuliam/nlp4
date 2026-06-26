# 组员 B Controlled 实验结论与后续计划

## 已完成内容

- 已跑完 `zero_shot`、`ordered_rag`、`naive_rag`、`rerank_rag`、`crag_lite`、`self_rag_lite` 六种方法。
- 已覆盖 RGB 噪音比例实验、RGB 正确文档位置实验、RAMDocs 扩展噪音实验。
- 正式输出位于 `outputs/controlled/`，指标表位于 `reports/member_b_controlled_summary.md`。
- 本轮为快速完成计划，使用 `--disable-neural`，即检索和重排采用词法 fallback；后续如时间允许，可补跑 neural embedding/reranker 版本作为更强 baseline。

## 正确文档位置影响

`ordered_rag` 是本轮新增的位置诊断 baseline，它只按输入顺序取前 `top_k=5` 篇文档，因此最能暴露正确文档位置对 RAG 的影响。

在 RGB 60% 噪音下：

| 方法 | front | middle | random | back |
|---|---:|---:|---:|---:|
| ordered_rag Accuracy | 0.7367 | 0.7233 | 0.7133 | 0.0633 |
| ordered_rag Evidence Acc | 1.0000 | 1.0000 | 0.9667 | 0.0000 |

结论：

- 当正确文档在 `front/middle/random` 且仍能进入前 `top_k` 时，回答性能保持在 0.71-0.74。
- 当正确文档在 `back` 时，`ordered_rag` 几乎完全取不到正确证据，Accuracy 从 0.7367 跌到 0.0633。
- `naive_rag`、`rerank_rag`、`self_rag_lite` 在 60% 噪音的不同位置下整体更稳定，说明检索模块能缓解单纯输入顺序偏置。

建议：

- 报告中应把 `ordered_rag` 定位为“位置敏感性诊断方法”，不要把它当成强 baseline。
- EGI-RAG 需要强调“先筛证据再生成”，避免模型只因为文档排列靠前就采纳噪声。
- 案例分析优先挑选 `ordered_rag_rgb_noise060_back_output.json` 中出错样本，能直观看出正确文档被排除后的影响。

## 噪音比例影响

RGB 中，正确文档位于 front 时，各 RAG 方法在 0%-80% 噪音下整体较稳，但到 100% 噪音时集体崩溃。

代表性结果：

| 方法 | 0% | 20% | 40% | 60% | 80% | 100% |
|---|---:|---:|---:|---:|---:|---:|
| naive_rag Accuracy | 0.7033 | 0.7200 | 0.7333 | 0.7467 | 0.6833 | 0.0533 |
| rerank_rag Accuracy | 0.7267 | 0.7167 | 0.7300 | 0.7367 | 0.6967 | 0.0567 |
| self_rag_lite Accuracy | 0.7067 | 0.7333 | 0.7267 | 0.7467 | 0.6767 | 0.0533 |
| zero_shot Accuracy | 0.1100 | 0.1033 | 0.1067 | 0.1067 | 0.1033 | 0.1033 |

RAMDocs 中，20%-60% 噪音已经能造成明显下降，100% 噪音下几乎无法回答，并且 misinformation adoption 明显升高。

代表性结果：

| 方法 | 20% Acc | 60% Acc | 100% Acc | 100% Misinfo Adopt |
|---|---:|---:|---:|---:|
| naive_rag | 0.6626 | 0.6137 | 0.0146 | 0.2743 |
| rerank_rag | 0.6528 | 0.6064 | 0.0097 | 0.2743 |
| crag_lite | 0.6235 | 0.5746 | 0.0073 | 0.2184 |
| self_rag_lite | 0.3790 | 0.3985 | 0.0073 | 0.2233 |

结论：

- 普通无关噪音比例升高时，RAG baseline 在正确证据仍可检索到的情况下不一定线性下降。
- 当输入变成 100% 噪音或 misinformation 主导时，所有 RAG 方法都缺少有效拒答机制。
- `self_rag_lite` 更保守，misinfo adoption 相对较低，但 Accuracy 也明显偏低，说明单纯生成后自检容易牺牲可回答样本。

## 方法结果建议

- `rerank_rag` 和 `naive_rag` 是当前最强常规 baseline，应作为 EGI-RAG 的主要对比对象。
- `crag_lite` 在本轮结果中没有稳定超过 rerank，说明粗粒度检索质量判断不足以处理“相关但错误”的文档。
- `self_rag_lite` 有一定拒答倾向，但对可回答样本损伤较大，后续需要把自检从“整答案判断”推进到“证据句级判断”。
- EGI-RAG 应重点解决两个问题：正确证据被位置或检索漏掉时的重新筛选，以及 100% 噪音或误导文档场景下的可靠拒答。

## 可补充的自定义噪音设置

后续可在 RGB 上自行构造以下噪音类型，增强报告说服力：

- 高词面重叠无关噪音：包含问题关键词，但不包含答案。
- 近似误导噪音：包含错误实体、错误日期或错误数值。
- 冲突噪音：与正确文档给出相反事实。
- 摘要式噪音：用简短但看似权威的句子诱导模型采纳错误答案。

建议优先使用 `20% / 60% / 100%` 三档比例，并在 `front / middle / back / random` 四种位置上做小规模补充即可，不必再完整扩展所有组合。

## 三位组员下一步计划

成员 A：

- 使用 `reports/member_b_controlled_summary.md` 生成噪音比例折线图、位置影响柱状图和 RAMDocs misinformation 表。
- 明确 `DataInspectionFailed` 的 13 条样本处理规则：保留为模型服务拒绝错误，并在表格脚注中说明。
- 从 `outputs/controlled/` 中抽取 3-5 个典型错误样本，交给成员 C 做案例分析。

成员 B：

- 保留本轮 `--disable-neural` 结果作为快速可复现 baseline。
- 如时间允许，补跑 neural embedding/reranker 版本，缓存路径继续放在项目 `.hf_cache/` 或 D 盘目录。
- 将 EGI-RAG 输出接入同一套评估脚本，确保输出字段包含 `answer`、`selected_doc_ids`、`evidence_spans`。
- 针对 100% 噪音新增更强拒答 prompt 或证据为空时的硬性拒答规则。

成员 C：

- 优先实现 EGI-RAG 的文档评分、证据句抽取和一致性校验三部分。
- 用 `ordered_rag` 的 back 位置失败案例说明“只按顺序拼上下文”的风险。
- 用 RAMDocs 100% 噪音案例说明 misinformation adoption 的危害。
- 消融实验优先做 `w/o doc scorer`、`w/o evidence extraction`、`w/o verifier` 三项，直接对应当前 baseline 暴露出的弱点。
