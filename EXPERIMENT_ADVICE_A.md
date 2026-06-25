# 面向噪音文档鲁棒 RAG 的补充实验建议

这份说明面向当前题目要求，重点补充三个实验问题：

1. 好文档位置会不会影响模型回答？
2. 噪音文档比例会不会影响模型回答？
3. 新方法应该如何更具体地设计和验证？

## 新的具体方法建议

建议把原来的 EGI-RAG 进一步细化为：

**Position-Aware Evidence-Gated RAG，位置感知证据门控 RAG。**

核心思想：

- 不默认排序靠前的文档更可信。
- 先对每篇文档做证据级判断，再决定是否进入答案生成。
- 对正确文档在前、中、后不同位置分别测试，验证方法是否真的不依赖“好文档靠前”。
- 对噪音比例 0%、20%、40%、60%、80%、100% 分别测试，观察方法鲁棒性。

## 成员A需要完成的部分

这些属于成员A任务，我已经补充完成：

- 构造可控噪音比例实验集。
- 构造正确文档位置实验集。
- 输出统一 input / reference / full 文件，供成员B/C直接跑模型。

新增脚本：

```bash
python src/evaluation/build_controlled_noise_sets.py
```

输出目录：

```text
samples/controlled/
  rgb/
  ramdocs/
```

每个数据集会生成：

- `noise000_front`
- `noise000_middle`
- `noise000_back`
- `noise000_random`
- `noise020_front`
- ...
- `noise100_random`

其中：

- `noise000` 表示无噪音文档。
- `noise020` 表示约 20% 噪音文档。
- `front` 表示正确文档放在上下文前部。
- `middle` 表示正确文档放在上下文中部。
- `back` 表示正确文档放在上下文后部。
- `random` 表示随机顺序。

## 成员B需要完成的部分

这部分不是成员A任务，理由是它涉及 RAG 系统和 baseline 实现。

成员B需要在上述可控输入上运行：

- Naive RAG
- Rerank RAG
- CRAG-lite
- Self-RAG-lite
- Zero-shot

建议至少先跑 RGB：

```text
samples/controlled/rgb/rgb_noise000_front_input.json
samples/controlled/rgb/rgb_noise020_front_input.json
samples/controlled/rgb/rgb_noise040_front_input.json
samples/controlled/rgb/rgb_noise060_front_input.json
samples/controlled/rgb/rgb_noise080_front_input.json
samples/controlled/rgb/rgb_noise100_front_input.json
```

如果时间充足，再补 `middle/back/random` 位置实验。

## 成员C需要完成的部分

这部分不是成员A任务，理由是它涉及新方法的 prompt、证据评分、迭代修正和案例分析。

成员C需要完成：

- Position-Aware Evidence-Gated RAG 的 prompt。
- 文档证据评分。
- 答案-证据一致性校验。
- 对错误案例进行矫正前后比较。

建议案例格式：

| 项目 | 内容 |
|---|---|
| 问题 | 原始问题 |
| 正确文档位置 | front / middle / back / random |
| 噪音比例 | 0% / 20% / 40% / 60% / 80% / 100% |
| Naive RAG 输出 | 矫正前答案 |
| 错误原因 | 被前置噪音影响 / 忽略后置正确文档 / 采纳误导文档 |
| 新方法输出 | 矫正后答案 |
| 修正原因 | 证据门控、文档评分、一致性校验 |

## 建议最终实验表

### 表1：正确文档位置影响

| 方法 | front | middle | back | random |
|---|---:|---:|---:|---:|
| Naive RAG | | | | |
| Rerank RAG | | | | |
| CRAG-lite | | | | |
| Self-RAG-lite | | | | |
| Position-Aware EGI-RAG | | | | |

### 表2：噪音比例影响

| 方法 | 0% | 20% | 40% | 60% | 80% | 100% |
|---|---:|---:|---:|---:|---:|---:|
| Naive RAG | | | | | | |
| Rerank RAG | | | | | | |
| CRAG-lite | | | | | | |
| Self-RAG-lite | | | | | | |
| Position-Aware EGI-RAG | | | | | | |

### 表3：误导文档采纳率

| 方法 | RAMDocs noise | RAMDocs misinfo | 总体 |
|---|---:|---:|---:|
| Naive RAG | | | |
| Rerank RAG | | | |
| CRAG-lite | | | |
| Self-RAG-lite | | | |
| Position-Aware EGI-RAG | | | |

## 给队友的结论

成员A已经补充完成数据层面的可控实验条件。

后续是否能得到实验结果，取决于成员B/C是否把各方法跑完并输出 `output.json`。成员A拿到这些输出后，可以继续用 `src/evaluation/evaluate_outputs.py` 计算指标并整理实验表。
