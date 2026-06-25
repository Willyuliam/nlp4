# nlp4 合并整理说明

本文档说明本次把 `Willyuliam/nlp4` 默认分支与 `member-c-egi-rag` 分支合并后的项目结构、数据、方法、现有结果和复现实验方式。

## 1. 本次合并做了什么

- 克隆仓库：`https://github.com/Willyuliam/nlp4.git`。
- 合并分支：`origin/member-c-egi-rag` 合入当前 `main`。
- 处理冲突：
  - 同名基线代码保留 `main` 的较完整版本，因为它已包含 `zero_shot`、`naive_rag`、`rerank_rag`、`crag_lite`、`self_rag_lite`。
  - 保留并接入 C 分支新增的 `src/egi_rag/`、`src/run_egi_rag.py`、`src/analyze_cases.py`、`scripts/run_member_c_midterm.ps1` 和相关 EGI-RAG 输出/报告。
  - 重写 `README.md`，作为合并后项目总入口。
  - 修复 `src/egi_rag/prompts.py` 中的乱码提示词，保证 EGI-RAG prompt 可读、可执行。
- 合并后位置：`D:\360Downloads\自然语言处理\nlp4_merged`。

## 2. 项目目标

项目对应“面向大模型 RAG 推理场景噪音文档的鲁棒性推理方法”。核心问题是：给定一个问题和一组候选文档，其中包含正确文档、无关噪声文档、误导文档或冲突文档，如何让大模型稳定地产生被证据支持的答案，并降低噪声文档诱导错误的概率。

## 3. 数据情况

### 3.1 样本文件

| 数据集 | 小样本输入 | 小样本数 | 全量输入 | 全量样本数 | 说明 |
|---|---|---:|---|---:|---|
| RGB | `samples/rgb_input.json` | 30 | `samples/rgb_all_input.json` | 300 | 每题包含较多噪声文档，正确文档比例低 |
| RAMDocs | `samples/ramdocs_input.json` | 20 | `samples/ramdocs_all_input.json` | 500 | 含 correct、noise、misinfo 等标签 |
| Conflicts | `samples/conflicts_input.json` | 20 | `samples/conflicts_all_input.json` | 458 | 更侧重冲突/不一致信息场景 |

每个数据集通常有三类文件：

- `*_input.json`：模型运行输入，包含问题和候选文档。
- `*_reference.json`：评估参考答案。
- `*_full.json`：保留更完整字段的中间/完整样本。

### 3.2 可控噪声数据

`samples/controlled/` 下有可控噪声实验集：

- `samples/controlled/rgb/`：24 个输入文件。
- `samples/controlled/ramdocs/`：24 个输入文件。

命名中包含噪声比例和正确文档位置，例如：

- `noise000`、`noise020`、`noise040`、`noise060`、`noise080`、`noise100`
- `front`、`middle`、`back`、`random`

这些文件用于测试“噪声比例变化”和“正确证据位置变化”对不同 RAG 方法的影响。

## 4. 输入与输出格式

### 4.1 输入格式

```json
[
  {
    "id": "rgb_0000",
    "question": "问题文本",
    "contexts": [
      {
        "doc_id": "doc_1",
        "title": "文档标题",
        "text": "文档正文",
        "label": "correct/noise/misinfo/unknown"
      }
    ],
    "gold_answers": ["参考答案"],
    "wrong_answers": ["错误答案，可选"]
  }
]
```

### 4.2 基线输出格式

```json
{
  "id": "rgb_0000",
  "method": "rerank_rag",
  "answer": "模型答案",
  "retrieved_doc_ids": ["doc_3", "doc_8"],
  "selected_doc_ids": ["doc_3"],
  "contexts_used": [],
  "prompt_version": "formal_v1",
  "raw_response": "模型原始响应",
  "error": null
}
```

### 4.3 EGI-RAG 输出额外字段

```json
{
  "method": "EGI-RAG",
  "doc_scores": [],
  "evidence_spans": [],
  "verification_result": "supported",
  "iteration_count": 1,
  "iteration_log": []
}
```

这些字段用于说明模型为什么选择某些文档、抽取了哪些证据、答案是否被证据支持，以及是否触发迭代修正。

## 5. 已有方法

### 5.1 Zero-shot

只输入问题，不输入候选文档。用于观察大模型自身知识能否回答问题。优点是简单；缺点是容易凭记忆回答，无法保证答案来自给定文档。

入口：

```powershell
python -m src.run_baseline --method zero_shot --input samples/rgb_input.json --output outputs/midterm/rgb_zero_shot_output.json --limit 30
```

### 5.2 Naive RAG

直接取候选文档中的前 `top_k` 篇拼进 prompt，让模型基于文档回答。优点是成本低；缺点是如果正确文档排在后面，或者前几篇噪声强，就容易拒答或被误导。

入口：

```powershell
python -m src.run_baseline --method naive_rag --input samples/rgb_input.json --output outputs/midterm/rgb_naive_rag_output.json --limit 30 --top_k 5
```

### 5.3 Rerank RAG

先进行检索/重排，再把排名最高的 `top_n` 篇文档交给模型回答。当前实现优先使用 bge-m3 + FAISS 检索、bge-reranker-v2-m3 重排；如果环境缺依赖或模型不可用，会回退到轻量词面打分。

入口：

```powershell
python -m src.run_baseline --method rerank_rag --input samples/rgb_input.json --output outputs/midterm/rgb_rerank_rag_output.json --limit 30 --top_k 20 --top_n 5
```

### 5.4 CRAG-lite

在 Rerank RAG 基础上增加文档可靠性判断。模型先判断候选文档是 reliable、weak、irrelevant 还是 misleading，再用可靠/弱相关文档生成答案。如果没有可用证据，则拒答。

入口：

```powershell
python -m src.run_baseline --method crag_lite --input samples/rgb_all_input.json --output outputs/rgb_results/rgb_crag_lite_output.json --top_k 20 --top_n 5
```

### 5.5 Self-RAG-lite

先生成答案，再让模型做一次自检。如果自检发现答案不被文档支持，就尝试重写；仍不支持则拒答。它强调“生成后校验”。

入口：

```powershell
python -m src.run_baseline --method self_rag_lite --input samples/rgb_all_input.json --output outputs/rgb_results/rgb_self_rag_lite_output.json --top_k 20 --top_n 5
```

### 5.6 EGI-RAG

EGI-RAG 是 C 分支新增方法，全称 Evidence-Gated Iterative RAG。它将“证据门控”和“迭代修正”放到核心流程中：

1. 本地重排，初步选出候选文档。
2. Document Scorer：LLM 给每篇文档打标签和可信分。
3. Evidence Extractor：只抽取能直接支持答案的证据句。
4. Answer Generator：只基于证据句生成答案。
5. Verifier：检查答案是否被证据支持。
6. Corrector：若不支持，则重选文档、重写答案或拒答。

入口：

```powershell
python -m src.run_egi_rag --input samples/rgb_input.json --output outputs/midterm/rgb_egi_rag_output.json --limit 10
```

消融变体：

```powershell
python -m src.run_egi_rag --input samples/rgb_input.json --output outputs/midterm/rgb_egi_wo_verifier.json --variant wo_verifier --limit 10
```

支持的变体：

- `full`
- `wo_doc_scorer`
- `wo_evidence_extraction`
- `wo_verifier`
- `wo_iteration`

## 6. 现有实验输出

### 6.1 中期小样本输出

`outputs/midterm/` 中已有：

| 数据集 | 方法 | 样本数 |
|---|---|---:|
| RGB | Zero-shot / Naive RAG / Rerank RAG | 各 30 |
| RAMDocs | Zero-shot / Naive RAG / Rerank RAG | 各 20 |
| Conflicts | Zero-shot / Naive RAG / Rerank RAG | 各 20 |
| RGB | EGI-RAG | 30 |
| RGB | EGI-RAG dry run | 2 |

### 6.2 全量/扩展输出

`outputs/rgb_results/`：

- RGB 全量 300 条：`zero_shot`、`naive_rag`、`rerank_rag`、`crag_lite`、`self_rag_lite`。
- 神经检索/重排版本：`rgb_neural_*_output.json`，多数为 300 条，也有 50 条快跑版本。

`outputs/ramdocs_results/`：

- RAMDocs 全量 500 条：`zero_shot`、`naive_rag`、`rerank_rag`、`crag_lite`、`self_rag_lite`。
- 神经检索/重排版本：`ramdocs_neural_*_output.json`，多数为 500 条，也有 50 条快跑版本。

## 7. 运行与复现建议

### 7.1 安装依赖

```powershell
conda activate type3
pip install -r requirements.txt
```

`requirements.txt` 包含：

- `faiss-cpu`
- `FlagEmbedding`
- `numpy`
- `sentence-transformers`

如果不安装这些依赖，项目仍可跑小规模验证，因为检索/重排会回退到词面打分。

### 7.2 配置模型

```powershell
$env:DASHSCOPE_API_KEY="你的 API Key"
$env:DASHSCOPE_MODEL="qwen3.5-122b-a10b"
```

也可以编辑：

```text
configs/model_config.example.yaml
```

### 7.3 快速 dry run

不调用 API，只检查 prompt 和流程：

```powershell
python -m src.run_baseline --method naive_rag --input samples/rgb_input.json --output outputs/midterm/rgb_naive_rag_dryrun.json --limit 2 --dry_run

python -m src.run_egi_rag --input samples/rgb_input.json --output outputs/midterm/rgb_egi_rag_dryrun.json --limit 2 --dry_run
```

### 7.4 案例对比

```powershell
python -m src.analyze_cases `
  --input samples/rgb_input.json `
  --baseline outputs/midterm/rgb_naive_rag_output.json `
  --egi outputs/midterm/rgb_egi_rag_output.json `
  --output reports/egi_case_comparison.md `
  --limit 5
```

## 8. 合并后的注意事项

- `member-c-egi-rag` 分支和 `main` 分支存在“不相关历史”合并问题，本地合并时使用了 `--allow-unrelated-histories`。
- 同名输出文件如 `outputs/midterm/rgb_naive_rag_output.json` 保留了主分支版本；C 分支新增的 EGI-RAG 输出已保留。
- C 分支新增的 EGI-RAG prompt 文件曾有乱码/断句问题，已修复为可读中文。
- 目前没有重新调用线上 API，只做了本地合并、语法检查和 dry-run 级别的可执行性准备。

## 9. 后续可做

1. 用统一评估脚本重新评估所有输出，生成准确率、拒答率、错误率表。
2. 对 RGB/RAMDocs 的可控噪声数据批量跑 `rerank_rag`、`crag_lite`、`self_rag_lite`、`EGI-RAG`。
3. 对 EGI-RAG 做消融实验，比较 `wo_doc_scorer`、`wo_evidence_extraction`、`wo_verifier`、`wo_iteration`。
4. 把旧报告中显示异常的中文重新生成一版，避免编码问题影响展示。
