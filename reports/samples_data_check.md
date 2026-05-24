# samples 数据检查报告

## 检查依据

根据 A 组员文档 `A：实验内容1.1.docx`，数据转换目标是为 RGB、RAMDocs、CONFLICTS 分别生成三类文件：

- `{dataset}_input.json`：模型输入，包含 `id`、`question`、`contexts`。
- `{dataset}_reference.json`：评估参考，包含 `id`、`gold_answers`、`wrong_answers`。
- `{dataset}_full.json`：完整数据，包含输入、参考答案和 `_meta`。

每个 `contexts` 元素应包含 `doc_id`、`title`、`text`、`label`。

## 实际文件

当前 `samples/` 中包含：

- `rgb_input.json`、`rgb_reference.json`、`rgb_full.json`
- `ramdocs_input.json`、`ramdocs_reference.json`、`ramdocs_full.json`
- `conflicts_input.json`、`conflicts_reference.json`、`conflicts_full.json`

文件命名与 A 组员文档中的设计一致。

## 字段符合性

| 数据集 | input 条数 | reference 条数 | full 条数 | input 字段 | context 字段 | 结论 |
|---|---:|---:|---:|---|---|---|
| RGB | 30 | 30 | 30 | `id,dataset,question,contexts` | `doc_id,title,text,label` | 符合 |
| RAMDocs | 20 | 20 | 20 | `id,dataset,question,contexts` | `doc_id,title,text,label` | 符合 |
| CONFLICTS | 20 | 20 | 20 | `id,dataset,question,contexts` | `doc_id,title,text,label` | 字段符合，标签需注意 |

## 注意点

- `rgb_input.json`、`ramdocs_input.json`、`conflicts_input.json` 都可以直接作为组员 B baseline 的 `--input`。
- `*_reference.json` 可以交给成员 A 的评估脚本按 `id` 对齐。
- CONFLICTS 的实际 context 标签为 `unknown: 181`，不是 A 文档中设想的 `contradictory`。baseline 运行不受影响，但如果后续要按冲突文档类型统计，需要成员 A 重新映射标签。
- CONFLICTS 的 20 条 reference 中有 11 条 `gold_answers` 为空白，这是数据源或转换逻辑导致的评估风险；baseline 运行不受影响，但成员 A 计算 Accuracy 前应清洗空白答案。
- RGB 的每条样本文档数不是固定 20，当前代码按实际 `contexts` 列表运行，不依赖固定文档数量，因此可兼容。

## 可运行结论

当前 `samples` 数据满足组员 B 中期原型的输入要求。推荐中期优先跑 `samples/rgb_input.json` 生成三类 baseline 输出，再按时间补跑 RAMDocs。CONFLICTS 可以用于流程展示和案例分析，但在正式评估前需要处理 `unknown` 标签和空白参考答案。
