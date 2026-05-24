# 三人合作完成题目八的完整执行计划

## Summary

项目题目定为：**面向噪声文档的鲁棒 RAG 推理方法研究**

核心目标：在公开 RAG 数据集上系统分析不同噪声文档对大模型问答结果的影响，并提出一个可实现、可评估、可解释的矫正机制 **EGI-RAG**。

EGI-RAG 全称：**Evidence-Gated Iterative RAG**，即“证据门控迭代式 RAG”。

核心流程：

```text
问题输入
-> 检索或读取候选文档
-> 文档相关性/可信度评分
-> 证据句抽取
-> 基于证据生成答案
-> 答案-证据一致性校验
-> 如发现无证据、冲突或误导，则重新筛选/重写
-> 输出答案、证据、评分和迭代记录
```

主数据集：

- **RGB**：主实验数据集，用于噪声比例、拒答、反事实、信息整合实验。
  - https://github.com/chen700564/RGB
- **RAMDocs**：扩展实验数据集，用于 misinformation、noise、ambiguity 场景。
  - https://huggingface.co/datasets/HanNight/RAMDocs
- **CONFLICTS**：少量案例分析，用于冲突文档解释。
  - https://github.com/google-research-datasets/rag_conflicts

对比方法：

1. Zero-shot LLM
2. Naive RAG
3. Rerank RAG
4. CRAG-lite
5. Self-RAG-lite
6. EGI-RAG，即本项目方法

最终交付：

- 中期方案文档：系统设计、框架图、数据集、方法、指标、分工、初步预实验。
- 最终代码项目：数据处理、RAG baseline、EGI-RAG、评估脚本、结果复现实验。
- 最终技术报告：实验结果、案例分析、消融实验、结论与局限。
- 系统演示材料：PPT、运行示例、典型案例前后对比。

## 三人分工

### 成员 A：数据与评估负责人

职责：保证实验数据可用、指标可算、结果可信。

具体任务：

- 下载并整理 RGB、RAMDocs、CONFLICTS。
- 将不同数据集统一转换为项目格式。
- 设计并实现 `input.json`、`reference.json`。
- 实现自动评估指标。
- 统计不同噪声比例、不同噪声类型下的性能结果。
- 负责最终报告中的“数据集介绍”“评估指标”“实验结果表格”。

输入输出规范：

```json
{
  "id": "rgb_001",
  "dataset": "RGB",
  "question": "问题文本",
  "contexts": [
    {
      "doc_id": "doc_1",
      "title": "文档标题",
      "text": "文档内容",
      "label": "correct/noise/misinfo/unknown"
    }
  ],
  "gold_answers": ["参考答案"],
  "wrong_answers": ["错误答案，如果数据集提供"]
}
```

成员 A 负责的指标：

- Accuracy / EM / F1
- Misinformation Adoption Rate：是否采纳错误答案
- Evidence Selection Accuracy：是否选中正确证据
- Refusal Accuracy：无足够证据时是否正确拒答
- Noise Sensitivity Drop：噪声导致的性能下降
- Faithfulness：答案是否被证据支持

### 成员 B：RAG 系统与 baseline 负责人

职责：实现所有可比较的基础方法，保证本项目方法有合理 baseline。

具体任务：

- 实现统一 LLM 调用接口。
- 实现 embedding、FAISS 检索、top-k 文档召回。
- 实现 Naive RAG。
- 实现 Rerank RAG。
- 实现 CRAG-lite。
- 实现 Self-RAG-lite。
- 记录每个方法的完整输出，方便成员 A 评估。

默认技术选择：

- LLM：API 调用 Qwen / DeepSeek 系模型为主。
- 本地模型：如资源允许，补充 Qwen3-14B/32B 或 DeepSeek-R1-Distill-Qwen。
- Embedding：`bge-m3`。
- Reranker：`bge-reranker-v2-m3`。
- 向量库：FAISS。
- 运行语言：Python。

baseline 设计：

```text
Zero-shot:
只输入 question，不输入 contexts。

Naive RAG:
输入 question + top-k contexts，直接生成答案。

Rerank RAG:
先召回 top-k，再重排取 top-n，生成答案。

CRAG-lite:
先判断检索文档是否可靠，再过滤低质量文档或触发拒答。

Self-RAG-lite:
先生成答案，再要求模型自检是否有证据支持，必要时修正。
```

成员 B 负责的报告内容：

- 系统实现细节
- baseline 方法说明
- 检索与重排序模块
- 模型调用与实验配置

### 成员 C：EGI-RAG 方法与报告整合负责人

职责：实现项目创新点，完成案例分析和最终报告组织。

具体任务：

- 设计 EGI-RAG prompt。
- 实现文档评分模块。
- 实现证据句抽取模块。
- 实现答案-证据一致性校验模块。
- 实现迭代式修正流程。
- 做典型案例分析。
- 绘制系统框架图和流程图。
- 统筹中期方案、最终报告和答辩 PPT。

EGI-RAG 具体模块：

```text
1. Document Scorer
判断每篇文档是否：
- directly_supportive
- partially_relevant
- irrelevant
- contradictory
- misleading
- insufficient

2. Evidence Extractor
从候选文档中抽取能直接回答问题的证据句。

3. Answer Generator
只允许基于证据句生成答案。

4. Consistency Verifier
检查答案中的每个事实是否被证据支持。

5. Iterative Corrector
如果发现无证据、冲突、误导，则重新筛文档或重写答案。
```

EGI-RAG 输出格式：

```json
{
  "id": "rgb_001",
  "method": "EGI-RAG",
  "answer": "最终答案",
  "selected_doc_ids": ["doc_1", "doc_3"],
  "evidence_spans": [
    {
      "doc_id": "doc_1",
      "text": "支持答案的证据句"
    }
  ],
  "doc_scores": [
    {
      "doc_id": "doc_1",
      "label": "directly_supportive",
      "score": 0.92,
      "reason": "该文档直接给出了问题答案"
    }
  ],
  "iteration_count": 2,
  "verification_result": "supported"
}
```

成员 C 负责的报告内容：

- EGI-RAG 方法设计
- 典型案例前后对比
- 消融实验分析
- 最终结论、局限与未来工作

## 时间计划

### 当前紧急阶段：5 月 24 日 - 5 月 26 日，中期检查冲刺

目标：完成可提交的中期方案，不追求完整实验跑完，但必须有清晰系统设计和小规模预实验。

**5 月 24 日**

- 成员 A：
  - 下载 RGB 和 RAMDocs。
  - 抽取各 20-50 条样本做小规模验证。
  - 完成统一 JSON schema 草案。
- 成员 B：
  - 搭建基础 Python 项目结构。
  - 完成 LLM API 调用测试。
  - 完成 Naive RAG prompt 初版。
- 成员 C：
  - 完成 EGI-RAG 方法说明。
  - 画系统框架图。
  - 整理近两年相关方法：CRAG、Self-RAG、RAMDocs、RARE、Magic Mushroom。

**5 月 25 日**

- 成员 A：
  - 实现 Accuracy、wrong-answer 命中率、证据选择准确率的初版评估。
  - 输出一张小规模实验结果表。
- 成员 B：
  - 跑 Zero-shot、Naive RAG、Rerank RAG 小规模结果。
  - 保存 `output.json`。
- 成员 C：
  - 跑 EGI-RAG 小规模案例。
  - 整理 2 个“矫正前后对比”案例。
  - 完成中期报告主体。

**5 月 26 日**

- 三人共同：
  - 合并中期文档。
  - 检查文件命名：`队长姓名-队长学号-题目编号.docx/pdf`。
  - 提交中期方案。
  - 中期方案必须包含：
    - 研究背景
    - 数据集说明
    - 系统框架图
    - 方法设计
    - baseline 设计
    - 评价指标
    - 三人分工
    - 初步实验计划
    - 初步案例或预实验结果

### 主实验阶段：5 月 27 日 - 6 月 10 日

目标：完成 RGB 主实验。

- 成员 A：
  - 完成 RGB 全部实验数据转换。
  - 实现噪声比例分组统计。
  - 输出不同噪声比例下的评估表。
- 成员 B：
  - 完成 Zero-shot、Naive RAG、Rerank RAG、CRAG-lite、Self-RAG-lite。
  - 每个方法至少跑完 RGB 主实验。
- 成员 C：
  - 完成 EGI-RAG 完整流程。
  - 做 EGI-RAG 消融实验准备。

主实验表：

| 方法 | 0% 噪声 | 20% 噪声 | 40% 噪声 | 60% 噪声 | 80% 噪声 | 100% 噪声 |
|---|---:|---:|---:|---:|---:|---:|
| Zero-shot | | | | | | |
| Naive RAG | | | | | | |
| Rerank RAG | | | | | | |
| CRAG-lite | | | | | | |
| Self-RAG-lite | | | | | | |
| EGI-RAG | | | | | | |

### 扩展实验阶段：6 月 11 日 - 6 月 18 日

目标：完成 RAMDocs 和冲突文档分析。

- 成员 A：
  - 按 `correct / misinfo / noise` 统计结果。
  - 实现 misinformation adoption rate。
- 成员 B：
  - 将所有 baseline 跑到 RAMDocs。
  - 检查不同模型输出稳定性。
- 成员 C：
  - 做 5-8 个典型案例分析。
  - 分析错误原因：排序错误、证据缺失、错误文档采纳、冲突处理失败。

RAMDocs 分析表：

| 方法 | Accuracy | Misinfo Adoption Rate | Evidence Selection Accuracy | Faithfulness |
|---|---:|---:|---:|---:|
| Naive RAG | | | | |
| Rerank RAG | | | | |
| CRAG-lite | | | | |
| Self-RAG-lite | | | | |
| EGI-RAG | | | | |

### 消融与总结阶段：6 月 19 日 - 6 月 24 日

目标：证明 EGI-RAG 每个模块有效。

消融设置：

| 方法变体 | 去掉内容 | 目的 |
|---|---|---|
| EGI-RAG full | 无 | 完整方法 |
| w/o doc scorer | 去掉文档评分 | 验证文档评分是否有用 |
| w/o evidence extraction | 去掉证据句抽取 | 验证证据压缩是否有用 |
| w/o verifier | 去掉生成后校验 | 验证自检是否有用 |
| w/o iteration | 去掉迭代修正 | 验证多轮修正是否有用 |

分工：

- 成员 A：整理消融实验数据。
- 成员 B：批量跑消融版本。
- 成员 C：分析消融结果并写入报告。

### 演示与最终提交阶段：6 月 25 日 - 6 月 30 日

目标：完成答辩和最终压缩包。

- 成员 A：
  - 整理所有表格、图表、数据说明。
- 成员 B：
  - 整理代码 README、运行命令、依赖说明。
- 成员 C：
  - 完成最终报告和 PPT。
  - 整合项目压缩包。

最终压缩包内容：

```text
项目根目录/
  data/
    sample_input.json
    sample_reference.json
  outputs/
    rgb_results/
    ramdocs_results/
    case_outputs/
  src/
    data_prepare/
    rag_baselines/
    egi_rag/
    evaluation/
  configs/
    model_config.example.yaml
    experiment_config.yaml
  reports/
    final_report.pdf
    slides.pptx
  README.md
  requirements.txt
```

注意：不提交模型权重，压缩包控制在 500M 以内。

## 实验如何对应题目要求

### 要求 1：针对具体数据集，给出实验结果、结论与分析

对应实现：

- 用 RGB 做主实验。
- 用 RAMDocs 做误导文档扩展实验。
- 输出不同方法、不同噪声比例、不同噪声类型下的指标表。
- 得出结论：
  - 噪声比例越高，Naive RAG 退化越明显。
  - misinfo 文档比普通 noise 文档更危险。
  - 只做 rerank 不能完全解决“相关但错误”的文档。
  - EGI-RAG 在高噪声场景下更稳定。

### 要求 2：重点关注不同文档对模型问答结果的影响

对应实现：

- 将文档分为 correct、noise、misinfo、contradictory、insufficient。
- 分析模型是否选中了正确文档。
- 分析模型是否采纳了错误文档中的 wrong answer。
- 用案例展示：
  - 无关文档如何稀释关键证据。
  - 弱相关文档如何诱导模型过度推理。
  - 错误文档如何直接导致错误答案。
  - 冲突文档如何影响模型选择。

### 要求 3：设计合理的矫正机制

对应实现：

- EGI-RAG 的文档评分、证据抽取、答案校验、迭代修正就是矫正机制。
- 同时包含提示词优化和迭代式生成。
- 可解释性强：每次输出都保留文档评分、证据句和修正原因。

### 要求 4：给出矫正前后的问答结果比较和原因分析

对应实现：

每个典型案例按以下格式写入报告：

| 项目 | 内容 |
|---|---|
| 问题 | 原始问题 |
| 正确文档 | 支持答案的文档 |
| 噪声文档 | 干扰模型的文档 |
| Naive RAG 输出 | 矫正前答案 |
| 错误原因 | 采纳错误文档 / 忽略关键证据 / 推理过度 |
| EGI-RAG 输出 | 矫正后答案 |
| 修正过程 | 文档评分、证据抽取、校验、重写 |
| 结论 | 说明矫正机制为什么有效 |

### 要求 5：与现有方法进行性能比较

对应实现：

- 与 Naive RAG 比较：证明普通 RAG 不够鲁棒。
- 与 Rerank RAG 比较：证明只靠相关性排序不足以识别误导文档。
- 与 CRAG-lite 比较：证明检索质量评估有用，但仍需要证据级校验。
- 与 Self-RAG-lite 比较：证明生成后自检有用，但生成前证据门控更稳定。
- 与 EGI-RAG full 比较：说明本方法组合了生成前控制和生成后校验。

## 验收标准

项目完成时必须满足：

- 至少跑完 RGB 主实验。
- 至少跑完 RAMDocs 扩展实验。
- 至少包含 5 种 baseline 或方法变体。
- 至少包含 5 个典型案例分析。
- 至少包含 1 组消融实验。
- 报告中有系统框架图、流程图、实验表、结果图和案例分析。
- 代码能通过 README 中的命令复现实验小样本。
- 最终结论能明确回答：
  - 哪类噪声文档最影响 RAG？
  - 哪种方法最能缓解噪声影响？
  - EGI-RAG 相比现有方法有效在哪里？
  - 当前方法还有哪些局限？

## Assumptions

- 三人分工按 A/B/C 执行，实际姓名由组内自行映射。
- 主实验优先使用 API 调用模型，保证进度；本地部署只作为加分项。
- 不进行模型微调，不提交模型权重。
- 中期检查时间紧，5 月 26 日前只需要完成方案和小规模预实验，不要求完整主实验。
- 最终报告重点放在“噪声影响分析 + 矫正机制有效性”，不要把项目写成普通 RAG 系统介绍。
