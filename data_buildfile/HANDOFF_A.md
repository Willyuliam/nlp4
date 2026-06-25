# 成员A任务交接说明

项目题目：面向大模型 RAG 推理场景噪音文档的鲁棒性推理方法

成员A职责：数据整理、统一格式、评估指标、实验结果统计。

## 已完成内容

1. 已整理 RGB、RAMDocs、CONFLICTS 三个数据集。
2. 已将数据转换为统一 JSON 格式。
3. 已生成 input / reference / full 三类数据文件。
4. 已完成 schema 校验脚本。
5. 已补充自动评估脚本，可计算实验指标。
6. 已生成数据集统计表，可用于报告中的“数据集介绍”部分。
7. 已补充可控实验集：支持分析正确文档位置和噪音比例对 RAG 的影响。

## 主要文件

数据文件：

- `data/samples/rgb_all_input.json`
- `data/samples/rgb_all_reference.json`
- `data/samples/rgb_all_full.json`
- `data/samples/ramdocs_all_input.json`
- `data/samples/ramdocs_all_reference.json`
- `data/samples/ramdocs_all_full.json`
- `data/samples/conflicts_all_input.json`
- `data/samples/conflicts_all_reference.json`
- `data/samples/conflicts_all_full.json`

脚本文件：

- `step1_download_rgb.py`：下载 RGB 数据集。
- `step2_download_others.py`：下载 RAMDocs 和 CONFLICTS。
- `step3_convert_and_sample.py`：统一转换数据格式。
- `step4_validate_schema.py`：校验数据格式并输出统计信息。
- `src/evaluation/evaluate_outputs.py`：评估各方法输出结果。
- `src/evaluation/build_dataset_report.py`：生成数据集统计报告。
- `src/evaluation/build_controlled_noise_sets.py`：生成可控噪音比例和正确文档位置实验集。

报告辅助文件：

- `reports/dataset_statistics.md`
- `EXPERIMENT_ADVICE_A.md`

可控实验数据：

- `data/controlled/rgb/`
- `data/controlled/ramdocs/`

## 当前数据规模

| 数据集 | 样本数 | 文档总数 | 主要标签 |
|---|---:|---:|---|
| RGB | 300 | 7976 | correct / noise |
| RAMDocs | 500 | 2766 | correct / noise / misinfo |
| CONFLICTS | 458 | 4212 | unknown |

## 数据格式

每条数据统一为：

```json
{
  "id": "rgb_0001",
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
  "wrong_answers": ["错误答案"]
}
```

## 验证方式

检查数据格式：

```bash
python step4_validate_schema.py
```

生成数据集统计表：

```bash
python src/evaluation/build_dataset_report.py
```

生成可控噪音/位置实验集：

```bash
python src/evaluation/build_controlled_noise_sets.py
```

评估某个方法的输出：

```bash
python src/evaluation/evaluate_outputs.py ^
  --input data/samples/rgb_all_input.json ^
  --reference data/samples/rgb_all_reference.json ^
  --output outputs/rgb_results/naive_rag_output.json ^
  --save outputs/rgb_results/naive_rag_metrics.json
```

## 对队友输出文件的要求

成员B或成员C跑完模型后，请保存类似下面的 `output.json`：

```json
[
  {
    "id": "rgb_0001",
    "method": "Naive RAG",
    "answer": "模型最终答案",
    "selected_doc_ids": ["doc_1", "doc_3"],
    "evidence_spans": [
      {
        "doc_id": "doc_1",
        "text": "支持答案的证据句"
      }
    ],
    "verification_result": "supported"
  }
]
```

其中必须有：

- `id`
- `answer`

建议保留：

- `method`
- `selected_doc_ids`
- `evidence_spans`
- `verification_result`

这样成员A可以直接计算 Accuracy、EM、F1、误导答案采纳率、证据选择准确率、拒答准确率、Faithfulness 等指标。

## 后续还需要队友完成

成员B需要继续完成：

- Zero-shot
- Naive RAG
- Rerank RAG
- CRAG-lite
- Self-RAG-lite
- 各方法输出 `output.json`

成员C需要继续完成：

- EGI-RAG 完整流程
- 矫正前后案例
- 消融实验
- 最终报告和 PPT 整合

成员A后续在拿到各方法输出后，需要继续：

- 跑评估脚本生成各方法指标。
- 整理 RGB 主实验表。
- 整理 RAMDocs 扩展实验表。
- 整理噪声比例和噪声类型下的性能变化。
- 将 `reports/dataset_statistics.md` 内容写入最终报告。
- 根据 `data/controlled/` 下的结果整理“正确文档位置影响”和“噪音比例影响”实验表。
