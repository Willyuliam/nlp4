# 题目八：面向噪声文档的鲁棒 RAG 推理

本仓库包含三人分工代码：

- **组员 B**：Qwen/百炼 API、Zero-shot、Naive RAG、Rerank RAG
- **组员 C**：EGI-RAG（Evidence-Gated Iterative RAG）及案例对比自动化

## 目录

```text
configs/model_config.example.yaml   # Qwen/百炼模型配置
data/sample_input.json              # 备用空输入模板
data/sample_input.schema.json       # 输入字段说明
samples/*_input.json                # 成员 A 已转换好的 RGB/RAMDocs/CONFLICTS 小样本
outputs/midterm/                    # 中期输出文件
src/run_baseline.py                 # baseline 运行入口
src/run_egi_rag.py                  # EGI-RAG 运行入口（组员 C）
src/analyze_cases.py                # Naive vs EGI 案例对比
src/llm/                            # Qwen/百炼 API 客户端
src/rag_baselines/                  # baseline prompt 与轻量 rerank
src/egi_rag/                        # EGI-RAG 流程（组员 C）
scripts/run_member_c_midterm.ps1    # 组员 C 中期一键脚本
reports/member_c_midterm.md         # 组员 C 中期方案
reports/egi_rag_framework.md          # 系统框架图
```

## 配置

所有命令默认在已有 conda 环境 `type3` 中运行：

```powershell
conda activate type3
```

API Key 可以通过环境变量或配置文件提供。为了避免泄露，建议运行前在 PowerShell 临时设置：

```powershell
$env:DASHSCOPE_API_KEY="你的百炼APIKey"
```

当前配置文件已指定中期模型：

```yaml
provider: qwen
model: "qwen3.5-122b-a10b"
base_url: "https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions"
```

如需临时覆盖模型，可设置：

```powershell
$env:DASHSCOPE_MODEL="qwen3.5-122b-a10b"
```

## 输入格式

`data/sample_input.json` 是备用空模板。当前实际可跑数据在 `samples/`：

```text
samples/rgb_input.json
samples/ramdocs_input.json
samples/conflicts_input.json
```

期望格式：

```json
[
  {
    "id": "sample_001",
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
    "wrong_answers": ["错误答案，可选"]
  }
]
```

## 运行命令

正式运行：

```powershell
conda activate type3

python -m src.run_baseline --method zero_shot --input data/sample_input.json --output outputs/midterm/zero_shot_output.json --limit 30

python -m src.run_baseline --method naive_rag --input data/sample_input.json --output outputs/midterm/naive_rag_output.json --limit 30 --top_k 5

python -m src.run_baseline --method rerank_rag --input data/sample_input.json --output outputs/midterm/rerank_rag_output.json --limit 30 --top_k 8 --top_n 5
```

使用成员 A 的 RGB 样本运行：

```powershell
conda activate type3

python -m src.run_baseline --method zero_shot --input samples/rgb_input.json --output outputs/midterm/rgb_zero_shot_output.json --limit 30

python -m src.run_baseline --method naive_rag --input samples/rgb_input.json --output outputs/midterm/rgb_naive_rag_output.json --limit 30 --top_k 5

python -m src.run_baseline --method rerank_rag --input samples/rgb_input.json --output outputs/midterm/rgb_rerank_rag_output.json --limit 30 --top_k 8 --top_n 5
```

无 API Key 或无正式数据时，可使用 dry run 生成 prompt 和流程记录：

```powershell
conda activate type3

python -m src.run_baseline --method naive_rag --input data/sample_input.json --output outputs/midterm/naive_rag_dryrun.json --dry_run
```

## 输出格式

每条输出包含：

```json
{
  "id": "sample_001",
  "method": "naive_rag",
  "answer": "模型答案",
  "selected_doc_ids": ["doc_1"],
  "contexts_used": [],
  "prompt_version": "midterm_v1",
  "raw_response": "模型原始响应",
  "error": null
}
```

`dry_run` 模式会额外输出 `prompt` 字段，便于中期答辩展示。

实际调用 API 时，程序默认读取 `configs/model_config.example.yaml`，也可以用 `--config` 指定其他配置文件。

## 组员 C：EGI-RAG 运行

```powershell
conda activate type3

# 小规模正式运行
python -m src.run_egi_rag --input samples/rgb_input.json --output outputs/midterm/rgb_egi_rag_output.json --limit 10

# dry run（无 API Key）
python -m src.run_egi_rag --input samples/rgb_input.json --output outputs/midterm/rgb_egi_rag_dryrun.json --limit 3 --dry_run

# 消融实验
python -m src.run_egi_rag --input samples/rgb_input.json --output outputs/midterm/rgb_egi_wo_verifier.json --variant wo_verifier --limit 10

# 一键自动化（EGI 运行 + 案例对比）
.\scripts\run_member_c_midterm.ps1 -Limit 10
.\scripts\run_member_c_midterm.ps1 -DryRun -Limit 3
```

EGI-RAG 输出额外包含 `evidence_spans`、`doc_scores`、`verification_result`、`iteration_log`。

若已有 `outputs/midterm/rgb_naive_rag_output.json`，可生成案例对比：

```powershell
python -m src.analyze_cases --input samples/rgb_input.json --baseline outputs/midterm/rgb_naive_rag_output.json --egi outputs/midterm/rgb_egi_rag_output.json --output reports/egi_case_comparison.md --limit 5
```

## 中期说明

中期 `rerank_rag` 与 EGI-RAG 前置 rerank 均使用本地轻量重排，不下载 embedding 模型：先按问题和文档的关键词/字符重合度排序，再取前 `top_n` 篇文档。最终阶段可替换为 embedding、FAISS 和专业 reranker。
