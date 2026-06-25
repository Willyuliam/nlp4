# 成员 B 阶段工作总结与实验结果报告

日期：2026-05-27  
项目：面向噪声文档的鲁棒 RAG 推理方法研究  
负责范围：RAG 系统与 baseline 实现、模型调用、检索与重排、RGB/RAMDocs baseline 实验输出

## 1. 对照 PLAN 的任务完成情况

根据 `PLAN.md` 中“成员 B：RAG 系统与 baseline 负责人”的分工，本阶段成员 B 的核心目标是实现可比较的 baseline，并为成员 A 的自动评估提供完整输出。

| PLAN 中成员 B 任务 | 当前完成情况 | 说明 |
|---|---|---|
| 实现统一 LLM 调用接口 | 已完成 | `src/llm/qwen_client.py` 封装 DashScope/Qwen compatible API，支持 `model`、`max_tokens`、`enable_thinking`、环境变量覆盖。 |
| 实现 embedding、FAISS 检索、top-k 文档召回 | 已完成 | `src/rag_baselines/retriever.py` 使用 `bge-m3` 编码 question/context，并用 FAISS `IndexFlatIP` 做每样本临时索引检索。 |
| 实现 Naive RAG | 已完成 | 当前正式版 Naive RAG 已改为 `question -> bge-m3/FAISS top_k -> prompt -> LLM`，不再直接取前 `top_k`。 |
| 实现 Rerank RAG | 已完成 | 流程为 `question -> bge-m3/FAISS top_k=20 -> bge-reranker-v2-m3 top_n=5 -> prompt -> LLM`。 |
| 实现 CRAG-lite | 已完成 | 生成前判断候选文档为 `reliable / weak / irrelevant / misleading`，保留可靠或必要 weak 文档；无可靠证据时拒答。 |
| 实现 Self-RAG-lite | 已完成 | 先生成初答，再自检答案是否被上下文支持；必要时重写或拒答。 |
| 记录完整输出方便 A 评估 | 已完成 | 输出包含 `retrieved_doc_ids`、`selected_doc_ids`、`contexts_used`，CRAG 额外包含 `doc_judgements`，Self-RAG 额外包含 `initial_answer`、`self_check_result`、`final_answer`。 |
| RGB 主实验 | 已完成 | 正式神经版 RGB 4 个 RAG 方法均完成 300 条；zero-shot 使用原全量输出。 |
| RAMDocs 扩展实验 | 已完成 | 正式神经版 RAMDocs 4 个 RAG 方法均完成 500 条；zero-shot 使用原全量输出。 |

结论：成员 B 在 `PLAN.md` 中对应的 baseline 系统实现和 RGB/RAMDocs 实验输出已经完成。后续如果进入消融阶段，成员 B 还需要在成员 C 给出 EGI-RAG 变体后负责批量运行消融版本。

## 2. 环境与模型配置

本阶段继续使用已有 conda 环境：

```powershell
D:\conda_envs\type3\python.exe
```

关键依赖已在 `type3` 环境中安装并验证：

| 组件 | 当前状态 |
|---|---|
| `faiss-cpu` | 可用 |
| `sentence-transformers` | 可用 |
| `FlagEmbedding` | 可用 |
| `transformers` | `4.57.6` |
| `huggingface_hub` | `0.36.2` |

模型缓存放在项目目录下：

```text
D:\大学资料\自然语言处理\实验四\.hf_cache\models\bge-m3
D:\大学资料\自然语言处理\实验四\.hf_cache\models\bge-reranker-v2-m3
```

缓存大小约：

| 模型 | 大小 | 用途 |
|---|---:|---|
| `bge-m3` | 约 2.16GB | query/context embedding |
| `bge-reranker-v2-m3` | 约 2.14GB | 检索结果重排 |

`.gitignore` 已加入：

```text
.hf_cache/
.pip_cache/
```

因此模型权重和 pip 缓存不会进入最终提交包，符合 `PLAN.md` 中“不提交模型权重，压缩包控制在 500M 以内”的要求。

LLM 使用：

```yaml
model: qwen3.5-flash
max_tokens: 256
enable_thinking: false
```

注意：`configs/model_config.example.yaml` 当前曾用于本地实验，提交前必须清空真实 API key，改为占位符或改用环境变量 `DASHSCOPE_API_KEY`。

## 3. 代码实现内容

本阶段成员 B 主要实现和修改了以下模块：

| 文件 | 作用 |
|---|---|
| `src/llm/qwen_client.py` | 统一 Qwen/DashScope API 调用接口，支持配置文件和环境变量。 |
| `src/rag_baselines/retriever.py` | `bge-m3 + FAISS` 检索模块；保留 lexical fallback 作为环境异常兜底。 |
| `src/rag_baselines/reranker.py` | `bge-reranker-v2-m3` 重排模块；保留 lexical fallback 作为环境异常兜底。 |
| `src/rag_baselines/prompts.py` | Zero-shot、RAG、CRAG 判断、自检和重写 prompt。 |
| `src/rag_baselines/baselines.py` | 统一实现 `zero_shot / naive_rag / rerank_rag / crag_lite / self_rag_lite`。 |
| `src/run_baseline.py` | baseline 运行入口，支持 `--workers`、`--resume`、`--top_k`、`--top_n`。 |
| `src/benchmark_concurrency.py` | API 并发测试工具。 |
| `scripts/run_neural_full.ps1` | 正式神经版全量实验脚本。 |
| `scripts/run_neural_supplement.ps1` | 前期 50 条神经补充实验脚本，已作为正式全量实验的种子结果来源。 |

正式神经实验脚本固定设置：

```powershell
$env:RAG_DISABLE_NEURAL_RETRIEVER = "0"
$env:RAG_DISABLE_NEURAL_RERANKER = "0"
$env:RAG_EMBEDDING_MODEL = ".hf_cache\models\bge-m3"
$env:RAG_RERANKER_MODEL = ".hf_cache\models\bge-reranker-v2-m3"
```

正式运行时使用 `workers=1`。原因是本地 `bge-m3` 与 reranker 模型较大，并发会重复占用内存，反而可能导致不稳定。全量脚本支持 `--resume`，中断后可以继续跑。

## 4. 正式输出文件

Zero-shot 不涉及检索，因此沿用之前的全量输出：

| 数据集 | 方法 | 输出文件 |
|---|---|---|
| RGB | Zero-shot | `outputs/rgb_results/rgb_zero_shot_output.json` |
| RAMDocs | Zero-shot | `outputs/ramdocs_results/ramdocs_zero_shot_output.json` |

正式神经版 RAG 输出如下：

| 数据集 | 方法 | 输出文件 | 条数 | 错误数 | fallback |
|---|---|---|---:|---:|---:|
| RGB | Naive RAG | `outputs/rgb_results/rgb_neural_naive_rag_output.json` | 300 | 0 | 0 |
| RGB | Rerank RAG | `outputs/rgb_results/rgb_neural_rerank_rag_output.json` | 300 | 0 | 0 |
| RGB | CRAG-lite | `outputs/rgb_results/rgb_neural_crag_lite_output.json` | 300 | 0 | 0 |
| RGB | Self-RAG-lite | `outputs/rgb_results/rgb_neural_self_rag_lite_output.json` | 300 | 0 | 0 |
| RAMDocs | Naive RAG | `outputs/ramdocs_results/ramdocs_neural_naive_rag_output.json` | 500 | 0 | 0 |
| RAMDocs | Rerank RAG | `outputs/ramdocs_results/ramdocs_neural_rerank_rag_output.json` | 500 | 0 | 0 |
| RAMDocs | CRAG-lite | `outputs/ramdocs_results/ramdocs_neural_crag_lite_output.json` | 500 | 0 | 0 |
| RAMDocs | Self-RAG-lite | `outputs/ramdocs_results/ramdocs_neural_self_rag_lite_output.json` | 500 | 0 | 0 |

所有正式神经版输出均已验证：

- 检索后端为 `bge-m3+faiss`
- 重排后端为 `bge-reranker-v2-m3`
- 没有 `lexical_fallback`
- 没有最终错误样本

运行过程中 `ramdocs_0269` 在 RAMDocs CRAG-lite 中曾触发一次 DashScope 内容检查错误：

```text
InternalError.Algo.DataInspectionFailed
```

处理方式：删除该错误行后用 `--resume` 单独重试，最终成功补齐，当前正式结果为 500/500 且 0 errors。

## 5. 指标说明

本报告中的指标为成员 B 阶段性快速统计，用于观察趋势。最终报告中应以成员 A 的正式评估脚本为准。

| 指标 | 含义 |
|---|---|
| Accuracy | 模型答案字符串是否包含任一 gold answer。该统计可能低估语义等价答案。 |
| Refusal | 模型输出“无法根据给定信息确定”“无法确定”“没有足够信息”等拒答表达的次数。 |
| Wrong adoption | 仅用于 RAMDocs，表示模型答案是否采纳了 `wrong_answers` 中的错误答案。 |
| selected label | `contexts_used` 中不同文档标签的数量，用于粗略分析证据选择。 |
| contains correct | 每条样本的 `contexts_used` 中是否至少包含一个 `correct` 文档。 |
| contains misinfo | 每条样本的 `contexts_used` 中是否至少包含一个 `misinfo` 文档。 |

## 6. 正式实验主结果

### 6.1 RGB 结果

| 方法 | Accuracy | Refusal |
|---|---:|---:|
| Zero-shot | 27/300 = 9.0% | 104 |
| Naive RAG | 208/300 = 69.3% | 1 |
| Rerank RAG | 209/300 = 69.7% | 0 |
| CRAG-lite | 208/300 = 69.3% | 3 |
| Self-RAG-lite | 212/300 = 70.7% | 2 |

RGB 证据选择情况：

| 方法 | selected correct | selected noise | contains correct |
|---|---:|---:|---:|
| Naive RAG | 1227 | 273 | 299/300 = 99.7% |
| Rerank RAG | 1384 | 116 | 299/300 = 99.7% |
| CRAG-lite | 1354 | 33 | 296/300 = 98.7% |
| Self-RAG-lite | 1384 | 116 | 299/300 = 99.7% |

RGB 上可以观察到：

1. Zero-shot 只有 9.0%，说明不提供上下文时模型无法可靠回答这些问题。
2. 引入 RAG 后，Accuracy 从 9.0% 提升到约 69%-71%，说明上下文证据对任务至关重要。
3. Rerank RAG 将 selected noise 从 273 降到 116，说明 bge-reranker 能明显减少无关噪声进入最终 prompt。
4. CRAG-lite 进一步把 selected noise 降到 33，但 Accuracy 没有提升，说明它过滤噪声更强，同时也可能过滤掉少量有用证据。
5. Self-RAG-lite 最高，达到 70.7%，说明生成后自检在 RGB 上有小幅收益。

CRAG-lite 在 RGB 的文档判断分布：

| 判断 | 数量 |
|---|---:|
| reliable | 1271 |
| weak | 120 |
| irrelevant | 64 |
| misleading | 28 |

Self-RAG-lite 在 RGB 的自检分布：

| 自检状态 | 数量 |
|---|---:|
| supported | 297 |
| unsupported | 3 |

RGB 结论：`bge-m3 + FAISS` 已经能高度稳定地召回正确证据；重排和自检能带来小幅提升；CRAG 在 RGB 上主要表现为更强的噪声过滤，而不是显著提升 Accuracy。

### 6.2 RAMDocs 结果

| 方法 | Accuracy | Refusal | Wrong adoption |
|---|---:|---:|---:|
| Zero-shot | 34/500 = 6.8% | 317 | 3/306 = 1.0% |
| Naive RAG | 320/500 = 64.0% | 293 | 88/306 = 28.8% |
| Rerank RAG | 317/500 = 63.4% | 297 | 103/306 = 33.7% |
| CRAG-lite | 311/500 = 62.2% | 198 | 36/306 = 11.8% |
| Self-RAG-lite | 183/500 = 36.6% | 285 | 37/306 = 12.1% |

RAMDocs 证据选择情况：

| 方法 | selected correct | selected noise | selected misinfo | contains correct | contains misinfo |
|---|---:|---:|---:|---:|---:|
| Naive RAG | 1586 | 320 | 271 | 497/500 = 99.4% | 228/500 = 45.6% |
| Rerank RAG | 1604 | 308 | 265 | 497/500 = 99.4% | 221/500 = 44.2% |
| CRAG-lite | 1034 | 48 | 30 | 453/500 = 90.6% | 27/500 = 5.4% |
| Self-RAG-lite | 1604 | 308 | 265 | 497/500 = 99.4% | 221/500 = 44.2% |

CRAG-lite 在 RAMDocs 的文档判断分布：

| 判断 | 数量 |
|---|---:|
| reliable | 764 |
| weak | 351 |
| irrelevant | 588 |
| misleading | 357 |

Self-RAG-lite 在 RAMDocs 的自检分布：

| 自检状态 | 数量 |
|---|---:|
| supported | 246 |
| insufficient | 200 |
| unsupported | 34 |
| conflict | 20 |

Self-RAG-lite 的重写后检查分布：

| 重写后状态 | 数量 |
|---|---:|
| supported | 164 |
| insufficient | 34 |
| unsupported | 51 |
| conflict | 5 |

RAMDocs 上可以观察到：

1. Zero-shot Accuracy 只有 6.8%，说明该任务强依赖给定上下文。
2. Naive RAG 提升到 64.0%，但 wrong adoption 达到 28.8%，说明普通 RAG 在 misinformation 场景下容易采纳错误文档。
3. Rerank RAG Accuracy 为 63.4%，wrong adoption 反而升至 33.7%。这说明重排器主要优化“相关性”，而不是“真实性”。misinfo 文档往往与问题高度相关，因此可能被重排到前列。
4. CRAG-lite Accuracy 略低，为 62.2%，但 wrong adoption 显著降到 11.8%，同时 contains misinfo 从约 45% 降到 5.4%。这说明文档可靠性判断对抑制误导文档非常有效。
5. Self-RAG-lite wrong adoption 也降到 12.1%，但 Accuracy 只有 36.6%。这说明当前 Self-RAG prompt 在 RAMDocs 上过于保守，频繁将答案判为 insufficient/unsupported，导致正确答案损失较大。

RAMDocs 结论：只做 retrieval/rerank 不能解决 misinformation；CRAG-lite 是当前 baseline 中最能体现抗误导能力的方法；Self-RAG-lite 可降低错误采纳，但当前实现需要优化自检和重写策略。

## 7. 与项目研究问题的对应关系

### 7.1 不同噪声文档对 RAG 的影响

RGB 主要体现 ordinary noise 的干扰。实验显示：

- RAG 方法整体远强于 zero-shot。
- bge-reranker 能减少普通 noise 进入最终 prompt。
- CRAG-lite 能进一步过滤 noise，但过强过滤不一定提高 Accuracy。

RAMDocs 主要体现 misinformation 的风险。实验显示：

- misinfo 比普通 noise 更危险。
- Rerank RAG 未能降低 misinfo 风险，反而提高 wrong adoption。
- CRAG-lite 显著降低 selected misinfo 和 wrong adoption，说明“生成前证据门控”是必要的。

### 7.2 对 EGI-RAG 的支撑

本项目最终方法 EGI-RAG 的核心思想是 Evidence-Gated Iterative RAG，即生成前证据门控 + 生成后校验 + 必要时重写。

成员 B 的 baseline 结果为 EGI-RAG 提供了三点直接依据：

1. Naive RAG 能提升基础回答能力，但容易受噪声和误导文档影响。
2. Rerank RAG 只能解决相关性排序问题，不能判断文档真伪。
3. CRAG-lite 和 Self-RAG-lite 分别证明了生成前过滤和生成后自检的价值，但二者单独使用都有局限。

因此，EGI-RAG 将“文档评分、证据抽取、一致性校验、迭代修正”组合起来是合理的：它需要同时解决错误文档进入 prompt 和答案生成后不忠实的问题。

## 8. 当前阶段的限制与后续建议

1. 本报告中的 Accuracy / Wrong adoption 是字符串匹配统计，可能低估同义表达或格式不同但语义正确的答案。最终结果应由成员 A 的正式评估脚本统一计算。
2. 当前正式神经版实验固定使用 `qwen3.5-flash`，尚未系统比较不同 LLM 的输出稳定性。若时间允许，可补充少量不同模型对照。
3. Self-RAG-lite 在 RAMDocs 上过度保守，需要优化 prompt，尤其是区分“证据不足”和“证据存在但表达不同”的情况。
4. CRAG-lite 在降低 wrong adoption 方面效果明显，但会牺牲部分正确证据召回。后续 EGI-RAG 可通过证据句抽取和迭代修正减少这种损失。
5. 提交前必须清理 `configs/model_config.example.yaml` 中的真实 API key。
6. 模型权重位于 `.hf_cache/`，已加入 `.gitignore`，最终压缩包不应包含该目录。

## 9. 阶段结论

成员 B 本阶段已经完成 `PLAN.md` 要求的 RAG baseline 系统建设和 RGB/RAMDocs baseline 实验：

- 统一 LLM 调用接口已完成。
- bge-m3 + FAISS 检索已完成。
- bge-reranker-v2-m3 重排已完成。
- Naive RAG、Rerank RAG、CRAG-lite、Self-RAG-lite 已完成。
- RGB 300 条和 RAMDocs 500 条正式神经版实验已完成。
- 所有正式神经 RAG 输出均为 0 errors、0 fallback。

实验结果表明：在普通噪声场景下，检索和重排可以有效提高答案准确率；在 misinformation 场景下，单纯 rerank 不足以避免错误答案采纳，CRAG-lite 的文档可靠性判断能显著降低 wrong adoption。这一结论直接支持项目后续 EGI-RAG 方法中“证据门控 + 自检修正”的设计必要性。
