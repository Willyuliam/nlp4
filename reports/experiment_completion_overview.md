# 题目八噪音文档鲁棒 RAG 实验完成总览

本文件是当前实验产物的总入口，用于说明已经完成的实验、结果文件位置、核心指标、典型案例和后续改进方向。项目根目录为：

`D:\大学资料\自然语言处理\实验四`

研究目标对应题目八：**面向大模型 RAG 推理场景噪音文档的鲁棒性推理方法**。核心问题是：在 RAG 中检索到的文档可能与问题高度相关，但缺少关键逻辑依赖、包含误导答案或只有表面关键词重叠，从而影响大模型问答准确率。当前实验围绕“好文档位置、噪音文档影响、自定义噪音、矫正机制和方法对比”展开。

## 1. 当前完成状态

| 模块 | 状态 | 说明 |
|---|---|---|
| Prompt 标签泄露修复 | 已完成 | 模型输入只展示 `doc_id/title/text`，不展示 `label=correct/noise/misinfo`。 |
| 旧正式神经 baseline | 已保留 | RGB/RAMDocs 上已有 Naive/Rerank/CRAG/Self-RAG 结果，作为历史主 baseline。 |
| no-label 公平子集 | 已完成 | 用修复后的 prompt 跑 RGB/RAMDocs 关键子集，验证趋势不依赖标签泄露。 |
| EGI-RAG | 已完成 | 实现并跑完 RGB 全量 300、RAMDocs 全量 500、controlled 子集和 custom noise。 |
| 自定义噪音 | 已完成 | 构造 60 条 logic-gap/value-swap/high-overlap-irrelevant 噪音样本。 |
| 案例分析 | 已完成 | 已抽取好文档在后、误导文档、100% 噪音、自定义逻辑缺失噪音案例。 |
| 最终报告 | 已完成 | `reports/final_experiment_analysis.md` 给出完整结果表、结论和改进建议。 |

剩余异常：新增实验共 3440 条输出，只有 2 条 CRAG-lite 服务端错误，均已重试后保留；EGI-RAG 输出 parse error 为 0。

## 2. 主要产物路径

### 2.1 总结与报告

| 文件 | 用途 |
|---|---|
| `PLAN.md` | 早期/旧版计划骨架，仅用于了解最初分工和目标背景；当前有效实验口径以本文件和 `reports/final_experiment_analysis.md` 为准。 |
| `reports/final_experiment_analysis.md` | 最终补全实验分析，包含核心表格、案例、完成情况和改进建议。 |
| `reports/experiment_completion_overview.md` | 本文件，作为当前所有实验结果和输出路径的总览说明。 |
| `reports/fair_subset_summary.md` | 去标签 prompt 公平子集结果汇总。 |
| `reports/egi_rag_summary.md` | EGI-RAG 全量与 controlled 子集结果汇总。 |
| `reports/custom_noise_summary.md` | 自定义噪音实验结果汇总。 |
| `reports/member_b_local_analysis.md` | 旧 controlled 诊断实验分析，重点说明噪音比例和好文档位置影响。 |
| `reports/member_b_controlled_summary.md` | 旧 controlled 矩阵结果汇总。 |

### 2.2 数据与输出

| 路径 | 内容 |
|---|---|
| `samples/rgb_all_input.json` | RGB 全量输入样本。 |
| `samples/ramdocs_all_input.json` | RAMDocs 全量输入样本。 |
| `samples/controlled/rgb/` | RGB controlled 噪音比例和位置控制数据。 |
| `samples/controlled/ramdocs/` | RAMDocs controlled 噪音和 misinformation 控制数据。 |
| `samples/custom_noise/` | 新增自定义噪音数据，含 RGB 30 条、RAMDocs 30 条。 |
| `outputs/rgb_results/` | 旧 RGB 正式神经 baseline 输出。 |
| `outputs/ramdocs_results/` | 旧 RAMDocs 正式神经 baseline 输出。 |
| `outputs/controlled/` | 旧 controlled 诊断实验输出，含位置和噪音比例矩阵。 |
| `outputs/fair_subset/` | 去标签 prompt 后的小规模公平验证输出。 |
| `outputs/egi_rag/` | EGI-RAG 全量和 controlled 子集输出。 |
| `outputs/custom_noise/` | 自定义噪音实验输出。 |

### 2.3 新增或更新脚本

| 文件 | 用途 |
|---|---|
| `scripts/build_custom_noise_sets.py` | 构造 logic-gap、value-swap、high-overlap-irrelevant 自定义噪音数据。 |
| `scripts/run_minimal_completion_experiments.py` | 最小 API 调用补全实验运行器，支持 fair subset、EGI-RAG、custom noise。 |
| `scripts/summarize_new_experiments.py` | 汇总新增实验输出，按实际 output id 过滤 reference，避免子集分母错误。 |
| `scripts/build_final_experiment_analysis.py` | 从现有 JSON 输出自动生成 `final_experiment_analysis.md`。 |
| `src/rag_baselines/prompts.py` | 更新 prompt，移除 label 泄露并加入 EGI-RAG prompt。 |
| `src/rag_baselines/baselines.py` | 实现 `egi_rag`，支持证据评分、证据句抽取、答案校验和拒答。 |
| `src/evaluation/evaluate_outputs.py` | 更新拒答识别，加入“无法根据给定信息确定”。 |

## 3. 实验矩阵与结果位置

### 3.1 旧正式神经 baseline

保留已有结果，不重跑，作为历史主 baseline。注意这些结果的 `prompt_version` 为 `formal_v1`，新实验为 `formal_v2_no_label`，报告中已区分。

| 数据集 | 方法 | 输出路径 |
|---|---|---|
| RGB | Naive/Rerank/CRAG/Self-RAG | `outputs/rgb_results/rgb_neural_*_output.json` |
| RAMDocs | Naive/Rerank/CRAG/Self-RAG | `outputs/ramdocs_results/ramdocs_neural_*_output.json` |

### 3.2 去标签 prompt 公平子集

目的：验证去掉 prompt 中的 label 后，主要趋势仍可观察。

| 设置 | 方法 | 输出路径 |
|---|---|---|
| RGB noise060 front/back/random，每组 50 条 | Naive/Rerank/CRAG/Self-RAG | `outputs/fair_subset/rgb/` |
| RAMDocs noise060 front，50 条 | Naive/Rerank/CRAG/Self-RAG | `outputs/fair_subset/ramdocs/` |
| 汇总 | 全部 | `reports/fair_subset_summary.md` |

核心发现：RGB 60% 噪音下，去标签后 Naive/Rerank/Self-RAG 仍保持约 0.64-0.72 的 Accuracy；RAMDocs 中 misinfo 会显著提高错误答案风险，Self-RAG 更保守但 Accuracy 较低。

### 3.3 EGI-RAG 全量与 controlled 子集

| 设置 | 输出路径 | 核心指标 |
|---|---|---|
| RGB 全量 300 | `outputs/egi_rag/rgb/egi_rag_rgb_all_output.json` | Accuracy 0.9200，F1 0.8127，Evidence Acc 0.9933 |
| RAMDocs 全量 500 | `outputs/egi_rag/ramdocs/egi_rag_ramdocs_all_output.json` | Accuracy 0.5320，Misinfo Adoption 0.1100，Refusal Acc 0.7100 |
| RGB noise060 back 100 条 | `outputs/egi_rag/controlled/rgb/egi_rag_rgb_noise060_back_output.json` | Accuracy 0.9200，说明好文档在后时仍能恢复证据 |
| RGB noise100 front 100 条 | `outputs/egi_rag/controlled/rgb/egi_rag_rgb_noise100_front_output.json` | Refusal Acc 0.8100，100% 噪音下能更多拒答 |
| RAMDocs noise060 front 100 条 | `outputs/egi_rag/controlled/ramdocs/egi_rag_ramdocs_noise060_front_output.json` | Accuracy 0.5700，Misinfo Adoption 0.1100 |
| RAMDocs noise100 front 100 条 | `outputs/egi_rag/controlled/ramdocs/egi_rag_ramdocs_noise100_front_output.json` | Refusal Acc 0.5900，但 Misinfo Adoption 仍有 0.3200 |
| 汇总 | `reports/egi_rag_summary.md` | 全部 EGI-RAG 与 controlled 对比 |

核心发现：EGI-RAG 在 RGB 和自定义噪音上效果明显；在 RAMDocs 强 misinformation 下能降低误导采纳，但会牺牲一部分 Accuracy，仍需要更强的冲突检测。

### 3.4 自定义逻辑缺失噪音实验

自定义噪音数据路径：

- `samples/custom_noise/custom_noise_all_input.json`
- `samples/custom_noise/custom_noise_all_reference.json`
- `samples/custom_noise/custom_noise_rgb_input.json`
- `samples/custom_noise/custom_noise_ramdocs_input.json`

输出路径：

- `outputs/custom_noise/naive_rag_custom_noise_all_output.json`
- `outputs/custom_noise/rerank_rag_custom_noise_all_output.json`
- `outputs/custom_noise/crag_lite_custom_noise_all_output.json`
- `outputs/custom_noise/egi_rag_custom_noise_all_output.json`

结果：

| 方法 | Accuracy | F1 | Misinfo Adoption | Evidence Acc | Refusal Acc |
|---|---:|---:|---:|---:|---:|
| Naive RAG | 0.6500 | 0.4694 | 0.0333 | 1.0000 | 0.8000 |
| Rerank RAG | 0.6500 | 0.4703 | 0.0167 | 1.0000 | 0.8000 |
| CRAG-lite | 0.6333 | 0.3511 | 0.0167 | 0.9667 | 0.7667 |
| EGI-RAG | 0.7833 | 0.7755 | 0.0167 | 0.9833 | 0.8667 |

核心发现：自定义噪音实验直接回应“相关但缺少逻辑依赖”的题目要求。EGI-RAG 通过只输入证据句生成答案，在 logic-gap 和 high-overlap irrelevant 噪音下比直接输入全文的 RAG 更稳。

## 4. 方法机制总结

EGI-RAG 当前实现路径：

`src/rag_baselines/baselines.py`

流程如下：

1. 检索或重排候选文档。
2. 对候选文档进行证据级评分，标签为 `supportive/partial/irrelevant/misleading`。
3. 只抽取 `supportive` 文档中的最短证据句。
4. 只把证据句输入答案生成阶段，不直接输入全部候选文档。
5. 对答案进行支持性校验，若 `verification_result` 不是 `supported`，输出“无法根据给定信息确定”。

这种机制的作用：

- 对普通无关噪音：通过证据句抽取降低上下文干扰。
- 对好文档在后：不依赖原始文档顺序，先评分再选择证据。
- 对 logic-gap：相关但缺少关键事实的文档会被标成 `partial`，不进入生成。
- 对 value-swap/misinfo：能过滤部分误导答案，但 RAMDocs 强误导场景仍有提升空间。

## 5. 说明性案例

| 类型 | 样本 | 现象 | 输出路径 |
|---|---|---|---|
| 好文档在后 | `rgb_0000` | Ordered RAG 只看到前部噪音而拒答；EGI-RAG 找到后部 correct 文档并答出首映日期。 | `outputs/controlled/rgb/ordered_rag_rgb_noise060_back_output.json` 与 `outputs/egi_rag/controlled/rgb/egi_rag_rgb_noise060_back_output.json` |
| 误导文档过滤 | `ramdocs_0012` | Naive RAG 在 100% 噪音中采纳错误答案 `The Beatles`；EGI-RAG 因无可靠证据拒答。 | `outputs/egi_rag/controlled/ramdocs/naive_rag_ramdocs_noise100_front_output.json` 与 `outputs/egi_rag/controlled/ramdocs/egi_rag_ramdocs_noise100_front_output.json` |
| 100% 噪音拒答 | `rgb_0016` | Naive RAG 在全噪音下回答 `Google Iris`；EGI-RAG 输出“无法根据给定信息确定”。 | `outputs/egi_rag/controlled/rgb/naive_rag_rgb_noise100_front_output.json` 与 `outputs/egi_rag/controlled/rgb/egi_rag_rgb_noise100_front_output.json` |
| 自定义逻辑缺失噪音 | `custom_ramdocs_0000` | 自定义 logic-gap/value-swap/high-overlap 噪音干扰下，Naive RAG 拒答，EGI-RAG 从 correct 文档抽取证据并回答 `1961`。 | `outputs/custom_noise/naive_rag_custom_noise_all_output.json` 与 `outputs/custom_noise/egi_rag_custom_noise_all_output.json` |

这些案例已写入：

`reports/final_experiment_analysis.md`

## 6. 对核心意见的回答

| 核心意见 | 当前完成情况 | 证据路径 |
|---|---|---|
| 好的文档的位置产生的影响 | 已完成。旧 controlled 覆盖 front/middle/back/random；新增 EGI-RAG 覆盖 RGB noise060 back。 | `outputs/controlled/`，`outputs/egi_rag/controlled/rgb/` |
| 噪音文档产生的影响 | 已完成。覆盖普通 noise、100% noise、RAMDocs misinfo、自定义三类噪音。 | `reports/member_b_local_analysis.md`，`reports/egi_rag_summary.md`，`reports/custom_noise_summary.md` |
| 方法实验结果建设性意见 | 已完成。报告中给出 EGI-RAG 有效性、局限和改进方案。 | `reports/final_experiment_analysis.md` |
| 可以自己设置噪音 | 已完成。已生成 custom noise 数据集并跑完实验。 | `samples/custom_noise/`，`outputs/custom_noise/` |

## 7. 结论

1. **噪音文档确实影响 RAG 推理**：影响来源包括位置、比例、误导答案和逻辑缺失。
2. **好文档位置对顺序型方法影响大**：Ordered RAG 在好文档靠后时容易只读到噪音；检索、重排和 EGI-RAG 能缓解这一问题。
3. **普通噪音和 misinfo 影响不同**：普通噪音主要稀释证据；misinfo 会让模型采纳错误答案，是更危险的噪音。
4. **100% 噪音是关键压力测试**：baseline 会出现幻答或误答；EGI-RAG 有更强的拒答倾向，但 RAMDocs 强误导场景仍不完全可靠。
5. **自定义 logic-gap 噪音验证了题目核心场景**：相关但缺少关键逻辑的文档会干扰直接生成，EGI-RAG 的证据门控机制能显著改善。

## 8. 后续改进建议

1. **重跑全量 no-label baseline**：旧正式 baseline 是 `formal_v1`，若 API 预算允许，应重跑全量 `formal_v2_no_label` baseline，获得完全公平的主表。
2. **增强冲突检测**：RAMDocs 100% 噪音下 EGI-RAG 仍有误导采纳，应加入 contradiction-aware verifier。
3. **扩大自定义噪音规模**：当前 60 条足够支撑课程实验和案例分析，若写成正式论文式报告，应扩到 200+ 条并按噪音类型分表。
4. **增加人工复核或 LLM judge**：当前 Accuracy、Misinfo Adoption 依赖字符串匹配，中文表达、日期格式和别名会带来误差。
5. **让 EGI-RAG 输出结构更强约束**：当前已修复 JSON 截断，但仍可进一步加入 schema retry 或函数式输出。

## 9. 复现实验入口

生成自定义噪音：

```powershell
D:\conda_envs\type3\python.exe scripts\build_custom_noise_sets.py
```

运行最小补全实验：

```powershell
D:\conda_envs\type3\python.exe scripts\run_minimal_completion_experiments.py --python D:\conda_envs\type3\python.exe --groups fair_subset
D:\conda_envs\type3\python.exe scripts\run_minimal_completion_experiments.py --python D:\conda_envs\type3\python.exe --groups egi_full,egi_controlled,custom_noise
```

生成汇总：

```powershell
D:\conda_envs\type3\python.exe scripts\summarize_new_experiments.py --output-root outputs\fair_subset --save reports\fair_subset_summary.md
D:\conda_envs\type3\python.exe scripts\summarize_new_experiments.py --output-root outputs\egi_rag --save reports\egi_rag_summary.md
D:\conda_envs\type3\python.exe scripts\summarize_new_experiments.py --output-root outputs\custom_noise --save reports\custom_noise_summary.md
```

生成最终分析报告：

```powershell
D:\conda_envs\type3\python.exe scripts\build_final_experiment_analysis.py
```
