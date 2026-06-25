# 题目八：面向噪声文档的鲁棒 RAG 推理

本仓库是合并后的项目版本，包含默认分支已有的数据处理、控制噪声实验、基础/神经 RAG 方法，以及 `member-c-egi-rag` 分支新增的 EGI-RAG（Evidence-Gated Iterative RAG）实现。

## 分工与模块

- 组员 A：RGB、RAMDocs、Conflicts 数据转换、抽样、schema 校验、可控噪声数据构造。
- 组员 B：Qwen/百炼 API 封装；Zero-shot、Naive RAG、Rerank RAG、CRAG-lite、Self-RAG-lite 等基线。
- 组员 C：EGI-RAG 流程、消融变体、Naive RAG 与 EGI-RAG 案例对比。

## 目录

```text
configs/model_config.example.yaml   # Qwen/百炼模型配置示例
data/                               # 输入 schema 与备用样例
samples/                            # 已转换的小样本、全量样本和可控噪声样本
outputs/                            # 已生成的实验输出
reports/                            # 数据、实验、方法报告
scripts/                            # 数据处理和一键实验脚本
src/run_baseline.py                 # 基线方法运行入口
src/run_egi_rag.py                  # EGI-RAG 运行入口
src/analyze_cases.py                # Naive RAG 与 EGI-RAG 案例对比
src/evaluation/                     # 数据统计、控制集构造、输出评估
src/llm/                            # Qwen/百炼 API 客户端
src/rag_baselines/                  # 检索、重排、基线流程和 prompts
src/egi_rag/                        # EGI-RAG 流程和 prompts
```

## 环境与配置

推荐使用已有 conda 环境：

```powershell
conda activate type3
pip install -r requirements.txt
```

API Key 建议通过环境变量提供：

```powershell
$env:DASHSCOPE_API_KEY="你的百炼 API Key"
```

默认配置位于 `configs/model_config.example.yaml`。如需临时替换模型：

```powershell
$env:DASHSCOPE_MODEL="qwen3.5-122b-a10b"
```

若本地没有 bge-m3、FAISS 或 bge-reranker-v2-m3，代码会自动回退到轻量词面检索/重排，便于小规模验证。

## 输入格式

实际可跑数据主要位于：

```text
samples/rgb_input.json
samples/ramdocs_input.json
samples/conflicts_input.json
samples/rgb_all_input.json
samples/ramdocs_all_input.json
samples/conflicts_all_input.json
samples/controlled/rgb/*_input.json
samples/controlled/ramdocs/*_input.json
```

样本格式：

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

## 运行基线

```powershell
python -m src.run_baseline --method zero_shot --input samples/rgb_input.json --output outputs/midterm/rgb_zero_shot_output.json --limit 30

python -m src.run_baseline --method naive_rag --input samples/rgb_input.json --output outputs/midterm/rgb_naive_rag_output.json --limit 30 --top_k 5

python -m src.run_baseline --method rerank_rag --input samples/rgb_input.json --output outputs/midterm/rgb_rerank_rag_output.json --limit 30 --top_k 20 --top_n 5

python -m src.run_baseline --method crag_lite --input samples/rgb_input.json --output outputs/rgb_results/rgb_crag_lite_output.json --limit 30 --top_k 20 --top_n 5

python -m src.run_baseline --method self_rag_lite --input samples/rgb_input.json --output outputs/rgb_results/rgb_self_rag_lite_output.json --limit 30 --top_k 20 --top_n 5
```

无 API Key 时可用 `--dry_run` 生成 prompt 和流程记录。

## 运行 EGI-RAG

```powershell
python -m src.run_egi_rag --input samples/rgb_input.json --output outputs/midterm/rgb_egi_rag_output.json --limit 10

python -m src.run_egi_rag --input samples/rgb_input.json --output outputs/midterm/rgb_egi_rag_dryrun.json --limit 3 --dry_run

python -m src.run_egi_rag --input samples/rgb_input.json --output outputs/midterm/rgb_egi_wo_verifier.json --variant wo_verifier --limit 10

.\scripts\run_member_c_midterm.ps1 -Limit 10
.\scripts\run_member_c_midterm.ps1 -DryRun -Limit 3
```

EGI-RAG 输出会额外包含 `doc_scores`、`evidence_spans`、`verification_result`、`iteration_log` 等字段。

## 进一步阅读

- `PROJECT_SUMMARY.md`：本次合并整理说明，含数据、方法和现有结果概览。
- `reports/dataset_statistics.md`：样本统计。
- `reports/baseline_run_summary.md`：基线运行摘要。
- `reports/egi_rag_framework.md`：EGI-RAG 框架说明。
- `reports/member_c_midterm.md`：组员 C 中期方案。
