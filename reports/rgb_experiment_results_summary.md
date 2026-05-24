# RGB 主实验结果汇总

> 自动生成于中期预实验阶段。涵盖 Zero-shot、Naive RAG、Rerank RAG 与 EGI-RAG 在 RGB 数据集 30 条样本上的对比结果。

---

## 1. 实验设置

| 项目 | 内容 |
|---|---|
| 数据集 | RGB（`samples/rgb_input.json`） |
| 参考答案 | `samples/rgb_reference.json` |
| 样本数 | 30 |
| 调用模型 | DeepSeek Chat（`deepseek-chat`） |
| API 配置 | `DASHSCOPE_BASE_URL=https://api.deepseek.com/chat/completions` |
| 噪声特点 | 每条样本含大量 noise 文档，仅少数 correct 文档含答案 |

### 方法说明

| 方法 | 配置 | 核心机制 |
|---|---|---|
| Zero-shot | 无文档 | 仅输入问题 |
| Naive RAG | top_k=5 | 直接取原始文档列表前 5 篇 |
| Rerank RAG | top_k=8, top_n=5 | 本地轻量重排后取前 5 篇 |
| EGI-RAG | top_k=8, top_n=5, max_iter=2 | rerank → 文档评分 → 证据抽取 → 答案生成 → 一致性校验 → 迭代修正 |

### 评估方式

- **Accuracy**：预测答案与 `gold_answers` 做子串匹配（忽略大小写与多余空格）
- **拒答率**：答案包含「无法根据给定信息确定」的样本比例
- 匹配规则与成员 A 评估脚本保持一致的中期简化版本

---

## 2. 总体结果

### 2.1 主指标表

| 方法 | Accuracy | 正确数 | 拒答数 | 错误数 |
|---|---:|---:|---:|---:|
| Zero-shot | 6.7% | 2/30 | 23 | 0 |
| Naive RAG | 73.3% | 22/30 | 7 | 0 |
| Rerank RAG | 83.3% | 25/30 | 3 | 0 |
| **EGI-RAG** | **90.0%** | **27/30** | **2** | **0** |

### 2.2 相对提升

| 对比 | 提升 |
|---|---:|
| Naive RAG → Rerank RAG | +10.0 pp |
| Rerank RAG → EGI-RAG | +6.7 pp |
| Naive RAG → EGI-RAG | +16.7 pp |

### 2.3 方法间 head-to-head（30 条样本）

**Naive RAG vs EGI-RAG**

| 情况 | 数量 |
|---|---:|
| 仅 EGI-RAG 答对 | 5 |
| 仅 Naive RAG 答对 | 0 |
| 两者都答对 | 22 |
| 两者都答错 | 3 |

**Rerank RAG vs EGI-RAG**

| 情况 | 数量 |
|---|---:|
| 仅 EGI-RAG 答对 | 2 |
| 仅 Rerank RAG 答对 | 0 |
| 两者都答对 | 25 |
| 两者都答错 | 3 |

---

## 3. EGI-RAG 专项统计

| 指标 | 数值 |
|---|---:|
| 校验通过（verification_result=supported） | 29/30 |
| 触发第 2 轮迭代 | 1/30 |
| 平均证据句数 | 1.93 |
| 平均选用文档数 | 3.2 |

EGI-RAG 每条输出还包含：

- `doc_scores`：文档相关性/可信度评分
- `evidence_spans`：支持答案的证据句
- `verification_result`：答案-证据一致性校验结果
- `iteration_log`：迭代修正过程记录

---

## 4. 典型案例

### 4.1 EGI-RAG 矫正成功（5 条）

#### 案例 A：rgb_0004 — 关键文档未被 Naive 召回

| 项目 | 内容 |
|---|---|
| 问题 | How much money did Texas Tech pay Marlene Stollings in the settlement? |
| 参考答案 | $740,000 |
| Naive RAG | 拒答 |
| EGI-RAG | **$740,000** |
| 原因 | Naive 只取列表前 5 篇（doc_15~doc_14），correct 文档 doc_3 排在第 8 位；EGI 经 rerank + 文档评分选中 doc_3 |

#### 案例 B：rgb_0003 — 噪声文档淹没关键证据

| 项目 | 内容 |
|---|---|
| 问题 | Which animated series won the Emmy Award for Best Animated Program? |
| 参考答案 | Arcane |
| Naive RAG | 拒答（选中 doc_7, doc_10 等规则/背景类 noise） |
| EGI-RAG | **Arcane**（证据来自 doc_4） |

#### 案例 C：rgb_0007 — 正确文档排序靠后

| 项目 | 内容 |
|---|---|
| 问题 | Which team won the 2023 Big 12 Championships in women's golf? |
| 参考答案 | Oklahoma State |
| Naive RAG | 拒答 |
| EGI-RAG | **Oklahoma State**（证据来自 doc_1） |

#### 案例 D：rgb_0013 — Naive 被噪声误导，EGI 也优于 Rerank

| 项目 | 内容 |
|---|---|
| 问题 | Who won the World Cup Final in 2022? |
| 参考答案 | Argentina |
| Naive RAG | 阿根廷（中文，未匹配英文 gold） |
| Rerank RAG | 阿根廷（同上） |
| EGI-RAG | **Argentina** |

#### 案例 E：rgb_0023 — 职位信息抽取

| 项目 | 内容 |
|---|---|
| 问题 | What position did Jason Semore hold at Valdosta State before returning to Georgia Tech? |
| 参考答案 | defensive coordinator |
| Naive RAG | 拒答 |
| EGI-RAG | **defensive coordinator** |

### 4.2 EGI-RAG 优于 Rerank RAG 的额外案例

| ID | 问题 | Rerank 输出 | EGI 输出 |
|---|---|---|---|
| rgb_0027 | New Amsterdam Season 5 premiere date? | 中文长句，日期格式未匹配 | September 20, 2022 |

### 4.3 失败案例（3 条，EGI-RAG 亦未答对）

| ID | 问题 | 参考答案 | 各方法输出 | 分析 |
|---|---|---|---|---|
| rgb_0000 | 2023 法网女单亚军 | Karolina Muchova | Naive/Rerank 拒答；EGI 答 Coco Gauff | doc_8 含「runner-up to Swiatek last year」造成时间混淆，EGI 误将其标为 directly_supportive |
| rgb_0009 | Argentina's semi opponent | Croatia | 全部拒答 | 证据分散，各方法均未找到明确答案 |
| rgb_0011 | 2022 Ivan Allen Jr. Prize 获奖者 | 4 人名单 | 全部拒答 | 多实体答案，文档信息分散 |

---

## 5. 结论与分析

### 5.1 噪声文档的影响

1. **Zero-shot 几乎无法回答**（6.7%），说明 RGB 问题依赖外部文档。
2. **Naive RAG 受文档顺序影响大**：直接取前 5 篇，correct 文档若排在后面会被完全忽略（如 rgb_0004）。
3. **Rerank 显著缓解排序问题**（73.3% → 83.3%），但仍可能被「相关但错误」的文档误导。

### 5.2 EGI-RAG 的有效性

1. **准确率最高**（90.0%），在 30 条样本上未出现比 Naive/Rerank 更差的情况。
2. **5 条 Naive 失败 → EGI 成功** 的案例，典型原因是：
   - 关键 correct 文档排序靠后（文档召回问题）
   - 噪声文档虽相关但无具体答案（证据抽取 + 评分过滤）
   - 输出格式/语言与 gold 不匹配（证据约束生成）
3. **可解释性强**：每条输出保留文档评分、证据句和校验结果，便于写入报告案例分析。

### 5.3 当前局限

1. **时间/实体混淆**：rgb_0000 表明「相关但错误」文档仍可能骗过评分与校验。
2. **校验通过 ≠ 答案正确**：29/30 为 supported，但仍有 3 条最终答错或拒答。
3. **多实体答案困难**：rgb_0011 需列出 4 个获奖者，当前 pipeline 难以完整覆盖。
4. **API 成本**：EGI-RAG 每条样本约 4–6 次 LLM 调用，高于 baseline。

---

## 6. 输出文件索引

| 类型 | 路径 |
|---|---|
| 输入数据 | `samples/rgb_input.json` |
| 参考答案 | `samples/rgb_reference.json` |
| Zero-shot 输出 | `outputs/midterm/rgb_zero_shot_output.json` |
| Naive RAG 输出 | `outputs/midterm/rgb_naive_rag_output.json` |
| Rerank RAG 输出 | `outputs/midterm/rgb_rerank_rag_output.json` |
| EGI-RAG 输出 | `outputs/midterm/rgb_egi_rag_output.json` |
| 案例对比报告 | `reports/egi_case_comparison.md` |
| EGI 方法说明 | `reports/member_c_midterm.md` |

---

## 7. 复现命令

```powershell
conda activate type3
$env:DASHSCOPE_API_KEY="你的APIKey"
$env:DASHSCOPE_BASE_URL="https://api.deepseek.com/chat/completions"
$env:DASHSCOPE_MODEL="deepseek-chat"

# Baselines
python -m src.run_baseline --method zero_shot --input samples/rgb_input.json --output outputs/midterm/rgb_zero_shot_output.json --limit 30
python -m src.run_baseline --method naive_rag --input samples/rgb_input.json --output outputs/midterm/rgb_naive_rag_output.json --limit 30 --top_k 5
python -m src.run_baseline --method rerank_rag --input samples/rgb_input.json --output outputs/midterm/rgb_rerank_rag_output.json --limit 30 --top_k 8 --top_n 5

# EGI-RAG
python -m src.run_egi_rag --input samples/rgb_input.json --output outputs/midterm/rgb_egi_rag_output.json --limit 30

# 案例对比
python -m src.analyze_cases --input samples/rgb_input.json --baseline outputs/midterm/rgb_naive_rag_output.json --egi outputs/midterm/rgb_egi_rag_output.json --output reports/egi_case_comparison.md --limit 5
```
