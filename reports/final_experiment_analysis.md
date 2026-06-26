# 最终补全实验分析

## 1. 执行进度与数据状态

- 已完成 prompt 标签泄露修复：模型输入只包含 `doc_id`、`title`、`text`，不再包含 `label=correct/noise/misinfo`；评估仍保留 `contexts_used[*].label`。
- 已新增并跑完 EGI-RAG：全量 RGB 300 条、RAMDocs 500 条；controlled 子集 4 组；custom noise 60 条。
- 已新增自定义逻辑缺失噪音：RGB 30 条、RAMDocs 30 条，每条包含 `logic_gap`、`value_swap`、`high_overlap_irrelevant` 三类噪音。
- EGI-RAG 截断/解析问题已修复：短 JSON 输出、512 token 上限、恢复式解析；最终 EGI 输出 parse error 为 0。
- 剩余服务端错误仅 2 条，均为 CRAG-lite 样本，已按计划重试后保留。

### 剩余错误
| File | Rows | Errors |
|---|---|---|
| outputs\fair_subset\rgb\crag_lite_rgb_noise060_front_output.json | 50 | 1 |
| outputs\egi_rag\controlled\rgb\crag_lite_rgb_noise100_front_output.json | 100 | 1 |

### EGI-RAG 输出健康度
| File | Rows | Parse Errors | Evidence Rows | Refusals |
|---|---|---|---|---|
| outputs\custom_noise\egi_rag_custom_noise_all_output.json | 60 | 0 | 59 | 8 |
| outputs\egi_rag\controlled\ramdocs\egi_rag_ramdocs_noise060_front_output.json | 100 | 0 | 89 | 22 |
| outputs\egi_rag\controlled\ramdocs\egi_rag_ramdocs_noise100_front_output.json | 100 | 0 | 50 | 59 |
| outputs\egi_rag\controlled\rgb\egi_rag_rgb_noise060_back_output.json | 100 | 0 | 100 | 4 |
| outputs\egi_rag\controlled\rgb\egi_rag_rgb_noise100_front_output.json | 100 | 0 | 28 | 81 |
| outputs\egi_rag\ramdocs\egi_rag_ramdocs_all_output.json | 500 | 0 | 446 | 144 |
| outputs\egi_rag\rgb\egi_rag_rgb_all_output.json | 300 | 0 | 300 | 10 |

## 2. 噪音添加方式分析

已有 controlled 数据通过固定噪音比例和正确文档位置构造：把文档按 `correct` 与 `noise/misinfo/contradictory/unknown` 分组，再按 0%-100% 噪音比例和 front/middle/back/random 位置重排。它能回答“好文档位置”和“噪音比例”两个变量的影响。

新增 custom noise 更贴近题目中的“相关但是缺少逻辑依赖”：`logic_gap` 保留实体和问题背景但删除关键关系，`value_swap` 保留实体但替换答案细节，`high_overlap_irrelevant` 保留高重叠关键词但不给事实依据。标签只用于评估，不进入 prompt。

## 3. 主结果对比

旧正式神经 baseline 的 `prompt_version` 为 `formal_v1`，新 EGI-RAG 为 `formal_v2_no_label`。因此表中 baseline 作为历史主结果保留，跨版本比较需要结合 no-label 子集一起看。
| Dataset | Method | Prompt | Outputs | Errors | Accuracy | F1 | Misinfo | Evidence | Refusal |
|---|---|---|---|---|---|---|---|---|---|
| RGB | naive_rag | formal_v1 | 300 | 0 | 0.7100 | 0.3525 | 0.0000 | 0.9967 | 0.9967 |
| RGB | rerank_rag | formal_v1 | 300 | 0 | 0.7167 | 0.3331 | 0.0000 | 0.9967 | 1.0000 |
| RGB | crag_lite | formal_v1 | 300 | 0 | 0.7133 | 0.3443 | 0.0000 | 0.9867 | 0.9900 |
| RGB | self_rag_lite | formal_v1 | 300 | 0 | 0.7267 | 0.3346 | 0.0000 | 0.9967 | 0.9933 |
| RGB | egi_rag | formal_v2_no_label | 300 | 0 | 0.9200 | 0.8127 | 0.0000 | 0.9933 | 0.9667 |
| RAMDocs | naive_rag | formal_v1 | 500 | 0 | 0.6420 | 0.1327 | 0.1780 | 0.9940 | 0.4080 |
| RAMDocs | rerank_rag | formal_v1 | 500 | 0 | 0.6380 | 0.1297 | 0.2060 | 0.9940 | 0.4000 |
| RAMDocs | crag_lite | formal_v1 | 500 | 0 | 0.6280 | 0.1867 | 0.0740 | 0.9060 | 0.6020 |
| RAMDocs | self_rag_lite | formal_v1 | 500 | 0 | 0.3680 | 0.1273 | 0.0740 | 0.9940 | 0.4280 |
| RAMDocs | egi_rag | formal_v2_no_label | 500 | 0 | 0.5320 | 0.5381 | 0.1100 | 0.7780 | 0.7100 |

结论：RGB 上 EGI-RAG 的 Accuracy 为 0.9200，高于旧 neural baseline；RAMDocs 上为 0.5320，低于 Naive/Rerank 的旧 formal_v1 主结果，但 Misinfo Adoption 为 0.1100，低于 Naive 0.1780 和 Rerank 0.2060，说明证据筛选牺牲部分覆盖率但减少误导采纳。

## 4. 关键压力测试
| Setting | Method | Accuracy | F1 | Misinfo | Evidence | Refusal | Faithfulness |
|---|---|---|---|---|---|---|---|
| RGB noise060 back | egi_rag | 0.9200 | 0.7835 | 0.0000 | 1.0000 | 0.9600 | 1.0000 |
| RGB noise100 front | egi_rag | 0.0900 | 0.1027 | 0.0000 | 0.0000 | 0.8100 | 0.2800 |
| RAMDocs noise060 front | egi_rag | 0.5700 | 0.5868 | 0.1100 | 0.7300 | 0.7800 | 0.8900 |
| RAMDocs noise100 front | egi_rag | 0.0100 | 0.0226 | 0.3200 | 0.0000 | 0.5900 | 0.5000 |

- RGB 60% 噪音且好文档在后时，EGI-RAG Accuracy 为 0.9200，说明证据抽取能缓解位置不利。
- 100% 噪音下，RGB EGI-RAG Refusal Acc 为 0.8100，与 Naive/Rerank 接近，但 Faithfulness 从 0 提升到 0.2800，说明它能输出部分带证据校验的拒答/修正结果。
- RAMDocs 100% 噪音下 EGI-RAG Refusal Acc 为 0.5900，略高于 Naive/Rerank 的 0.5000/0.5400；但 Misinfo Adoption 仍为 0.3200，说明对强误导答案的防御还不够，后续应强化矛盾检测和拒答阈值。

## 5. 自定义逻辑缺失噪音
| Dataset | Method | Accuracy | F1 | Misinfo | Evidence | Refusal | Faithfulness |
|---|---|---|---|---|---|---|---|
| Custom noise | naive_rag | 0.6500 | 0.4694 | 0.0333 | 1.0000 | 0.8000 | 1.0000 |
| Custom noise | rerank_rag | 0.6500 | 0.4703 | 0.0167 | 1.0000 | 0.8000 | 1.0000 |
| Custom noise | crag_lite | 0.6333 | 0.3511 | 0.0167 | 0.9667 | 0.7667 | 0.9667 |
| Custom noise | egi_rag | 0.7833 | 0.7755 | 0.0167 | 0.9833 | 0.8667 | 0.9833 |

结论：自定义噪音实验完成了“可以自己设置噪音”的要求。EGI-RAG Accuracy 0.7833，高于 Naive/Rerank 0.6500；Misinfo Adoption 0.0167，与 Rerank/CRAG 持平并低于 Naive 0.0333。说明把全文输入改成证据句输入，对 value-swap 和 logic-gap 噪音有帮助。

## 6. 案例对比
| Type | ID | Question | Gold | Baseline Answer | EGI Answer | Baseline Docs | EGI Docs |
|---|---|---|---|---|---|---|---|
| 好文档在后 | rgb_0000 | When is the premiere of 'Carole King & James Taylor: Just Call Out My Name'? | January 2 2022 / Jan 2, 2022 / Jan. 2, 2022 / January 2, 2022 / 2 January 2022 / | 无法根据给定信息确定 | January 2, 2022, at 9:00pm ET/PT on CNN | doc_17:noise, doc_16:noise, doc_8:noise, doc_9:noise, doc_13:noise | doc_5:correct, doc_4:correct, doc_1:correct, doc_2:correct |
| 误导文档过滤 | ramdocs_0012 | Who is the artist of the album "VII"? | Blitzen Trapper | The Beatles | 无法根据给定信息确定 | doc_5:misinfo, doc_4:misinfo, doc_7:noise, doc_6:noise |  |
| 100% 噪音拒答 | rgb_0016 | What is the codename for Google's AR headset project? | Project Iris | Google Iris | 无法根据给定信息确定 | doc_24:noise, doc_15:noise, doc_19:noise, doc_20:noise, doc_12:noise |  |
| 自定义逻辑缺失噪音 | custom_ramdocs_0000 | When was Rutherford High School established? | 1961 / 1922 / 1985 | 无法根据给定信息确定 | 1961 | custom_high_overlap_irrelevant:noise, custom_value_swap:misinfo, custom_logic_gap:noise, doc_1:correct, doc_3:correct | doc_1:correct |

## 7. 是否完成原意见

| 意见 | 完成情况 | 说明 |
|---|---|---|
| 好的文档的位置产生的影响 | 已完成 | 旧 controlled 覆盖 front/middle/back/random；新增 EGI controlled 覆盖 RGB noise060 back。 |
| 噪音文档产生的影响 | 已完成 | 覆盖 60% 噪音、100% 噪音、RAMDocs misinfo、自定义三类噪音。 |
| 方法实验结果建设性意见 | 已完成 | 已给出 EGI-RAG 与 baseline 的主结果、压力测试、局限和后续改进建议。 |
| 可以自己设置噪音 | 已完成 | `samples/custom_noise/` 生成 60 条自定义逻辑缺失/值替换/高重叠无关噪音。 |

## 8. 需要改进的点

1. 旧正式 neural baseline 是 `formal_v1`，后续若 API 预算允许，应重跑全量 no-label baseline，得到完全公平的主表。
2. RAMDocs 100% 噪音下 EGI-RAG 仍会采纳部分误导答案，应增加 contradiction-aware verifier：若证据来自 `misleading/value_swap` 风格句子或不同证据冲突，则优先拒答。
3. 当前自动评估仍是字符串包含匹配，中文/别名/日期格式会有偏差；最终论文式报告建议加入 30-50 条人工复核或 LLM judge。
4. EGI-RAG 的 prompt 输出格式已经稳定，但仍依赖模型按 JSON 响应；可进一步改成两阶段工具化解析或更严格的 schema retry。
5. 自定义噪音规模为 60 条，足够补题目要求和案例分析，但若作为主结论，应扩大到 200+ 条并分类型报告。

## 9. 总结

当前实验已经能支撑题目目标：噪音文档会通过位置、比例、误导答案和逻辑缺失四种方式影响 RAG 推理；单纯检索/重排能缓解普通噪音，但面对 100% 噪音和 misinfo 时忠实性与误导采纳仍有风险。EGI-RAG 通过文档证据评分、证据句抽取和答案支持性校验，在 RGB、自定义噪音和部分压力测试上明显改善；但在 RAMDocs 强误导场景中仍需更强的冲突识别机制。
