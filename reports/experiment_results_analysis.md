# 组员 B Baseline 实验结果分析

## 1. 实验设置

本次实验用于中期答辩阶段，目标是验证组员 B 负责的 RAG baseline 能够在成员 A 转换后的实际样本上完整运行，并为后续 EGI-RAG 方法提供可比较的基础结果。

实验环境与配置：

| 项目 | 内容 |
|---|---|
| 运行环境 | conda `type3` |
| 调用模型 | `qwen3.5-122b-a10b` |
| 模型平台 | Qwen / 百炼 API |
| 输入目录 | `samples/` |
| 输出目录 | `outputs/midterm/` |
| 输出格式 | JSON，按 `id` 与 reference 文件对齐 |

实验数据：

| 数据集 | 输入文件 | 样本数 | 主要用途 |
|---|---|---:|---|
| RGB | `samples/rgb_input.json` | 30 | 主实验，分析普通噪声文档对 RAG 的影响 |
| RAMDocs | `samples/ramdocs_input.json` | 20 | 扩展实验，分析 misinformation / wrong answer 采纳 |
| CONFLICTS | `samples/conflicts_input.json` | 20 | 案例实验，分析冲突上下文下的模型表现 |

对比方法：

| 方法 | 说明 |
|---|---|
| Zero-shot | 只输入问题，不输入上下文文档 |
| Naive RAG | 输入问题和前 `top_k=5` 篇候选文档，直接生成答案 |
| Rerank RAG | 先用本地轻量重排从前 `top_k=8` 篇候选文档中选出 `top_n=5` 篇，再生成答案 |

说明：中期阶段的 Rerank RAG 使用关键词/字符重合度进行轻量重排，未使用 embedding、FAISS 或专业 reranker。

## 2. 运行完成情况

| 数据集 | 方法 | 输出文件 | 记录数 | 错误数 | 状态 |
|---|---|---|---:|---:|---|
| RGB | Zero-shot | `outputs/midterm/rgb_zero_shot_output.json` | 30 | 0 | 完成 |
| RGB | Naive RAG | `outputs/midterm/rgb_naive_rag_output.json` | 30 | 0 | 完成 |
| RGB | Rerank RAG | `outputs/midterm/rgb_rerank_rag_output.json` | 30 | 0 | 完成 |
| RAMDocs | Zero-shot | `outputs/midterm/ramdocs_zero_shot_output.json` | 20 | 0 | 完成 |
| RAMDocs | Naive RAG | `outputs/midterm/ramdocs_naive_rag_output.json` | 20 | 0 | 完成 |
| RAMDocs | Rerank RAG | `outputs/midterm/ramdocs_rerank_rag_output.json` | 20 | 0 | 完成 |
| CONFLICTS | Zero-shot | `outputs/midterm/conflicts_zero_shot_output.json` | 20 | 0 | 完成 |
| CONFLICTS | Naive RAG | `outputs/midterm/conflicts_naive_rag_output.json` | 20 | 0 | 完成 |
| CONFLICTS | Rerank RAG | `outputs/midterm/conflicts_rerank_rag_output.json` | 20 | 1 | 完成，保留错误分析 |

总计生成 210 条 baseline 输出记录，其中 209 条成功返回答案，1 条因百炼平台内容安全检查被拦截。

## 3. 自动评估结果

本节结果使用简单字符串包含匹配自动计算：若模型答案包含任一 `gold_answers`，或参考答案包含模型答案，则记为命中。该指标适合中期快速比较，但会低估语义等价、翻译答案、简称答案等情况，最终报告建议加入人工复核或 LLM judge。

### 3.1 答案命中率

| 数据集 | 方法 | 可评估样本数 | 命中数 | 自动命中率 |
|---|---|---:|---:|---:|
| RGB | Zero-shot | 30 | 3 | 10.0% |
| RGB | Naive RAG | 30 | 16 | 53.3% |
| RGB | Rerank RAG | 30 | 18 | 60.0% |
| RAMDocs | Zero-shot | 20 | 2 | 10.0% |
| RAMDocs | Naive RAG | 20 | 11 | 55.0% |
| RAMDocs | Rerank RAG | 20 | 13 | 65.0% |
| CONFLICTS | Zero-shot | 9 | 2 | 22.2% |
| CONFLICTS | Naive RAG | 9 | 2 | 22.2% |
| CONFLICTS | Rerank RAG | 9 | 5 | 55.6% |

结论：

- RGB 和 RAMDocs 上，RAG 方法明显优于 Zero-shot，说明外部上下文对知识密集型问答有明显帮助。
- Rerank RAG 在 RGB 和 RAMDocs 上均优于 Naive RAG，说明即使是轻量重排，也能改善候选文档质量。
- CONFLICTS 的准确率仅供参考，因为该数据集 reference 中有较多空白答案，且当前 context 标签均为 `unknown`，不适合直接作为严格自动评估结果。

### 3.2 RAMDocs 错误答案采纳率

RAMDocs 提供 `wrong_answers`，因此可以初步统计模型是否采纳误导答案。

| 方法 | 可评估样本数 | 命中 wrong answer 数 | 错误答案采纳率 |
|---|---:|---:|---:|
| Zero-shot | 10 | 0 | 0.0% |
| Naive RAG | 10 | 1 | 10.0% |
| Rerank RAG | 10 | 1 | 10.0% |

结论：

- Naive RAG 和 Rerank RAG 都出现了少量 wrong answer 命中，说明引入文档后模型确实可能受误导文档影响。
- Rerank RAG 的错误答案采纳率没有低于 Naive RAG，说明仅靠相关性重排不足以完全识别“相关但错误”的文档。
- 这为成员 C 的 EGI-RAG 提供了动机：需要文档可信度判断、证据抽取和答案一致性校验，而不只是检索相关性排序。

## 4. 文档选择分析

### 4.1 RGB 文档选择

| 方法 | 选中文档总数 | correct 文档数 | noise 文档数 | 含至少 1 个 correct 文档的样本比例 |
|---|---:|---:|---:|---:|
| Naive RAG | 150 | 50 | 100 | 83.3% |
| Rerank RAG | 150 | 65 | 85 | 90.0% |

分析：

- Naive RAG 固定取前 5 篇文档，其中噪声文档占比仍然较高。
- Rerank RAG 将 correct 文档数从 50 提升到 65，说明轻量重排能提高正确证据进入上下文的概率。
- 即便 Rerank 后仍有 85 篇 noise 文档被选入，说明 RAG 仍会面对大量噪声上下文，后续需要更强的证据门控机制。

### 4.2 RAMDocs 文档选择

| 方法 | 选中文档总数 | correct | misinfo | noise | 含至少 1 个 correct 文档的样本比例 |
|---|---:|---:|---:|---:|---:|
| Naive RAG | 88 | 63 | 12 | 13 | 100.0% |
| Rerank RAG | 88 | 66 | 9 | 13 | 100.0% |

分析：

- RAMDocs 中每个样本平均文档数较少，因此 Naive 和 Rerank 都能选到 correct 文档。
- Rerank RAG 将 misinfo 文档从 12 降到 9，说明重排对误导文档有一定过滤作用。
- 但 Rerank RAG 仍保留 9 篇 misinfo 文档，并且 wrong answer adoption 仍为 10.0%，说明误导文档只要进入上下文，就仍可能影响生成结果。

### 4.3 CONFLICTS 文档选择

| 方法 | 选中文档总数 | 标签分布 | 说明 |
|---|---:|---|---|
| Naive RAG | 100 | `unknown: 100` | 当前转换结果未标出 correct / contradictory |
| Rerank RAG | 100 | `unknown: 100` | 当前转换结果未标出 correct / contradictory |

分析：

- 当前 CONFLICTS 的 `contexts.label` 全部为 `unknown`，与 A 组员文档中“冲突文档标为 contradictory”的设想不一致。
- 因此 CONFLICTS 当前更适合作为案例分析数据，而不是直接做文档标签统计。
- 若最终报告要分析冲突文档影响，应先由成员 A 修正标签映射或人工标注冲突/支持文档。

## 5. 典型样例观察

### RGB 示例

问题：`Who is the runner-up in the women's singles at the 2023 French Open?`

| 方法 | 输出摘要 | 选中文档 |
|---|---|---|
| Zero-shot | `卡罗利娜·穆霍娃` | 无 |
| Naive RAG | `Muchova` | `doc_26`, `doc_19`, `doc_6`, `doc_23`, `doc_11` |
| Rerank RAG | `穆霍娃（Muchova）` | `doc_8`, `doc_7`, `doc_19`, `doc_11`, `doc_6` |

分析：该样本中三种方法都能给出正确答案，但 Rerank RAG 选择了不同的上下文组合，说明文档排序会改变输入证据来源。对于简单短答案问题，Zero-shot 可能凭模型知识答对，但整体统计上仍明显弱于 RAG。

### RAMDocs 示例

问题：`What sport is Scott Murray associated with?`

| 方法 | 输出摘要 | 选中文档 |
|---|---|---|
| Zero-shot | `橄榄球` | 无 |
| Naive RAG | `足球` | `doc_1`, `doc_2`, `doc_3`, `doc_4`, `doc_5` |
| Rerank RAG | `足球` | `doc_1`, `doc_4`, `doc_3`, `doc_7`, `doc_2` |

分析：Zero-shot 缺少上下文，容易依赖模型内部知识或猜测；RAG 引入文档后能将答案拉回到文档证据中。但如果上下文中同时存在误导信息，仍需要后续证据校验。

### CONFLICTS 示例

问题：`Who owns the majority of papa john's?`

| 方法 | 输出摘要 | 选中文档 |
|---|---|---|
| Zero-shot | `它是一家上市公司，主要由机构投资者持有。` | 无 |
| Naive RAG | `Papa John's 是一家上市公司，无单一多数股东...` | `doc_1`, `doc_2`, `doc_3`, `doc_4`, `doc_5` |
| Rerank RAG | `Papa John's 是一家上市公司，没有单一实体拥有多数股权...` | `doc_1`, `doc_2`, `doc_7`, `doc_3`, `doc_4` |

分析：在冲突文档场景下，RAG 方法会综合多个上下文给出答案，但如果文档之间存在矛盾，仅靠 Naive 或 Rerank 不能明确说明哪些证据可信。该类样本更适合展示 EGI-RAG 的证据一致性校验价值。

## 6. 错误与局限

### 6.1 API 调用错误

最终仅保留 1 条失败样本：

| 数据集 | 方法 | 样本 ID | 错误原因 |
|---|---|---|---|
| CONFLICTS | Rerank RAG | `conflicts_0019` | 百炼 API 返回 `DataInspectionFailed`，输入文本触发内容安全检查 |

该样本已经失败超过一次，不再重复调用。该错误不是代码错误，也不是 JSON 字段问题，而是平台侧内容安全拦截。后续评估时应将 `error != null` 的记录单独统计或排除。

### 6.2 自动评估局限

- 当前答案命中率基于字符串包含匹配，不能完全识别中英文翻译、同义表达、简称和复杂表述。
- CONFLICTS 有 11 条 reference 的 `gold_answers` 为空白，因此本报告只对 9 条非空 reference 做自动命中率统计。
- RAMDocs 的 wrong-answer adoption 只在 `wrong_answers` 非空的 10 条样本上统计。
- Rerank RAG 使用轻量本地重排，不能代表最终专业 reranker 效果。

## 7. 中期结论

1. 组员 B 的三种 baseline 已经在实际 samples 数据上完整跑通，输出格式稳定，可交给成员 A 继续评估。
2. RGB 和 RAMDocs 的结果表明，RAG 相比 Zero-shot 有明显提升，说明上下文文档对知识问答有效。
3. Rerank RAG 相比 Naive RAG 有进一步提升，说明文档排序会影响答案质量。
4. 噪声和误导文档仍会进入 RAG 上下文，RAMDocs 中仍出现 10.0% 的 wrong answer adoption，说明只做重排不足以解决鲁棒性问题。
5. CONFLICTS 暴露出冲突文档场景下的评估难点：当前标签不充分、参考答案存在空白，需要后续清洗或人工案例分析。
6. 上述结果支持项目提出 EGI-RAG：在检索和生成之间加入文档可信度评分、证据抽取、一致性校验和迭代修正，是有必要的。

## 8. 建议放入中期答辩的表述

可以在答辩中概括为：

> 我们已经完成了 Zero-shot、Naive RAG 和 Rerank RAG 三种 baseline，并在 RGB、RAMDocs、CONFLICTS 三个小样本数据集上完成运行。初步结果显示，RAG 能显著提升问答命中率，Rerank 能进一步提升正确文档进入上下文的比例；但在 RAMDocs 中仍出现错误答案采纳，说明仅依赖相关性排序无法完全过滤误导文档。因此，后续 EGI-RAG 将通过文档可信度评分、证据抽取和一致性校验来增强 RAG 在噪声文档场景下的鲁棒性。
