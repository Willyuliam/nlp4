# 组员 B：RAG Baseline 中期原型

本目录实现第八题“面向大模型 RAG 推理场景噪音文档的鲁棒性推理方法”中组员 B 负责的中期原型：Qwen/百炼 API 调用封装、Zero-shot、Naive RAG、Rerank RAG，以及统一输出格式。

## 目录

```text
configs/model_config.example.yaml   # Qwen/百炼模型配置
data/sample_input.json              # 备用空输入模板
data/sample_input.schema.json       # 输入字段说明
samples/*_input.json                # 成员 A 已转换好的 RGB/RAMDocs/CONFLICTS 小样本
samples/controlled/                 # 成员 A 构造的噪音比例/正确文档位置可控实验集
outputs/midterm/                    # 中期输出文件
reports/dataset_statistics.md       # 数据统计报告
scripts/step*.py                    # 数据下载、转换、校验脚本
src/run_baseline.py                 # baseline 运行入口
src/evaluation/                     # 数据统计、可控实验构造、输出评估脚本
src/llm/                            # Qwen/百炼 API 客户端
src/rag_baselines/                  # baseline prompt 与轻量 rerank
HANDOFF_A.md                        # 成员 A 数据与评估交接说明
EXPERIMENT_ADVICE_A.md              # 可控实验和后续实验表建议
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
samples/rgb_all_input.json
samples/ramdocs_all_input.json
samples/conflicts_all_input.json
samples/controlled/rgb/*_input.json
samples/controlled/ramdocs/*_input.json
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

## 成员 A 数据与评估脚本

校验统一数据格式：

```powershell
python scripts/step4_validate_schema.py
```

生成数据集统计报告：

```powershell
python src/evaluation/build_dataset_report.py
```

生成噪音比例和正确文档位置可控实验集：

```powershell
python src/evaluation/build_controlled_noise_sets.py
```

评估某个方法的输出：

```powershell
python src/evaluation/evaluate_outputs.py --input samples/rgb_all_input.json --reference samples/rgb_all_reference.json --output outputs/rgb_results/rgb_naive_rag_output.json --save outputs/rgb_results/rgb_naive_rag_metrics.json
```

成员 B/C 跑完 baseline 或 EGI-RAG 后，把输出保存为 JSON 数组，并至少保留 `id` 和 `answer` 字段；如保留 `selected_doc_ids`、`evidence_spans`、`verification_result`，评估脚本可以继续计算证据选择准确率和 Faithfulness。

## 中期说明

中期 `rerank_rag` 使用本地轻量重排，不下载 embedding 模型：先按问题和文档的关键词/字符重合度排序，再取前 `top_n` 篇文档生成答案。最终阶段可替换为 embedding、FAISS 和专业 reranker。
