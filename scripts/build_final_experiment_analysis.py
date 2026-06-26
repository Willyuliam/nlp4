"""Build the final experiment analysis report from existing outputs."""

from __future__ import annotations

import json
from pathlib import Path
import sys
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.evaluation.evaluate_outputs import answer_hit, evaluate, is_refusal


REPORT = REPO_ROOT / "reports" / "final_experiment_analysis.md"


def load_json(path: str | Path) -> list[dict[str, Any]]:
    return json.loads((REPO_ROOT / path).read_text(encoding="utf-8"))


def metric_row(
    dataset: str,
    method: str,
    input_path: str,
    reference_path: str,
    output_path: str,
) -> dict[str, Any]:
    outputs = load_json(output_path)
    output_ids = {str(row.get("id")) for row in outputs if isinstance(row, dict)}
    inputs = [row for row in load_json(input_path) if str(row.get("id")) in output_ids]
    references = [row for row in load_json(reference_path) if str(row.get("id")) in output_ids]
    result = evaluate(inputs, references, outputs)["overall"]
    return {
        "dataset": dataset,
        "method": method,
        "outputs": len(outputs),
        "errors": sum(1 for row in outputs if row.get("error")),
        "prompt_version": next((row.get("prompt_version", "") for row in outputs if row.get("prompt_version")), ""),
        **result,
    }


def table(rows: list[dict[str, Any]], columns: list[tuple[str, str]]) -> list[str]:
    lines = [
        "| " + " | ".join(title for title, _ in columns) + " |",
        "|" + "|".join("---" for _ in columns) + "|",
    ]
    for row in rows:
        cells = []
        for _, key in columns:
            value = row.get(key, "")
            if isinstance(value, float):
                cells.append(f"{value:.4f}")
            else:
                cells.append(str(value))
        lines.append("| " + " | ".join(cells) + " |")
    return lines


def by_id(rows: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    return {str(row.get("id")): row for row in rows}


def refs_by_id(reference_path: str) -> dict[str, dict[str, Any]]:
    return by_id(load_json(reference_path))


def inputs_by_id(input_path: str) -> dict[str, dict[str, Any]]:
    return by_id(load_json(input_path))


def gold_hit(record: dict[str, Any], ref: dict[str, Any]) -> bool:
    return answer_hit(str(record.get("answer", "")), [str(gold) for gold in ref.get("gold_answers", [])])


def wrong_hit(record: dict[str, Any], ref: dict[str, Any]) -> bool:
    return answer_hit(str(record.get("answer", "")), [str(wrong) for wrong in ref.get("wrong_answers", [])])


def labels_for_selected(record: dict[str, Any]) -> str:
    parts = []
    for ctx in record.get("contexts_used", []) or []:
        doc_id = ctx.get("doc_id", "")
        label = ctx.get("label", "unknown")
        noise_type = ctx.get("noise_type")
        if noise_type:
            parts.append(f"{doc_id}:{label}/{noise_type}")
        else:
            parts.append(f"{doc_id}:{label}")
    return ", ".join(parts[:6])


def selected_has_label(record: dict[str, Any], label: str) -> bool:
    return any(ctx.get("label") == label for ctx in record.get("contexts_used", []) or [])


def first_case(
    input_path: str,
    reference_path: str,
    baseline_path: str,
    egi_path: str,
    predicate,
) -> dict[str, str]:
    inputs = inputs_by_id(input_path)
    refs = refs_by_id(reference_path)
    baseline = by_id(load_json(baseline_path))
    egi = by_id(load_json(egi_path))
    for item_id in sorted(set(baseline) & set(egi) & set(refs)):
        base = baseline[item_id]
        egi_row = egi[item_id]
        ref = refs[item_id]
        if predicate(base, egi_row, ref):
            sample = inputs.get(item_id, {})
            return {
                "id": item_id,
                "question": str(sample.get("question", ""))[:120],
                "gold": " / ".join(map(str, ref.get("gold_answers", [])))[:80],
                "baseline_answer": str(base.get("answer", ""))[:120],
                "egi_answer": str(egi_row.get("answer", ""))[:120],
                "baseline_docs": labels_for_selected(base),
                "egi_docs": labels_for_selected(egi_row),
            }
    return {
        "id": "N/A",
        "question": "未自动找到完全匹配条件的案例",
        "gold": "",
        "baseline_answer": "",
        "egi_answer": "",
        "baseline_docs": "",
        "egi_docs": "",
    }


def build_cases() -> list[dict[str, str]]:
    cases = []
    cases.append(
        {
            "type": "好文档在后",
            **first_case(
                "samples/controlled/rgb/rgb_noise060_back_input.json",
                "samples/controlled/rgb/rgb_noise060_back_reference.json",
                "outputs/controlled/rgb/ordered_rag_rgb_noise060_back_output.json",
                "outputs/egi_rag/controlled/rgb/egi_rag_rgb_noise060_back_output.json",
                lambda base, egi, ref: (not gold_hit(base, ref)) and gold_hit(egi, ref),
            ),
        }
    )
    cases.append(
        {
                "type": "误导文档过滤",
                **first_case(
                "samples/controlled/ramdocs/ramdocs_noise100_front_input.json",
                "samples/controlled/ramdocs/ramdocs_noise100_front_reference.json",
                "outputs/egi_rag/controlled/ramdocs/naive_rag_ramdocs_noise100_front_output.json",
                "outputs/egi_rag/controlled/ramdocs/egi_rag_ramdocs_noise100_front_output.json",
                lambda base, egi, ref: wrong_hit(base, ref)
                and (not is_refusal(base))
                and not wrong_hit(egi, ref)
                and not selected_has_label(egi, "misinfo"),
            ),
        }
    )
    cases.append(
        {
            "type": "100% 噪音拒答",
            **first_case(
                "samples/controlled/rgb/rgb_noise100_front_input.json",
                "samples/controlled/rgb/rgb_noise100_front_reference.json",
                "outputs/egi_rag/controlled/rgb/naive_rag_rgb_noise100_front_output.json",
                "outputs/egi_rag/controlled/rgb/egi_rag_rgb_noise100_front_output.json",
                lambda base, egi, ref: (not is_refusal(base)) and is_refusal(egi),
            ),
        }
    )
    cases.append(
        {
            "type": "自定义逻辑缺失噪音",
            **first_case(
                "samples/custom_noise/custom_noise_all_input.json",
                "samples/custom_noise/custom_noise_all_reference.json",
                "outputs/custom_noise/naive_rag_custom_noise_all_output.json",
                "outputs/custom_noise/egi_rag_custom_noise_all_output.json",
                lambda base, egi, ref: (not gold_hit(base, ref)) and gold_hit(egi, ref),
            ),
        }
    )
    return cases


def error_summary() -> list[dict[str, Any]]:
    rows = []
    for root in ["outputs/fair_subset", "outputs/egi_rag", "outputs/custom_noise"]:
        for path in sorted((REPO_ROOT / root).rglob("*_output.json")):
            data = json.loads(path.read_text(encoding="utf-8"))
            errors = sum(1 for row in data if row.get("error"))
            if errors:
                rows.append({"file": str(path.relative_to(REPO_ROOT)), "rows": len(data), "errors": errors})
    return rows


def parse_summary() -> list[dict[str, Any]]:
    rows = []
    for path in sorted((REPO_ROOT / "outputs").rglob("egi_rag*_output.json")):
        data = json.loads(path.read_text(encoding="utf-8"))
        rows.append(
            {
                "file": str(path.relative_to(REPO_ROOT)),
                "rows": len(data),
                "parse_errors": sum(1 for row in data if row.get("doc_judgements_parse_error")),
                "evidence_rows": sum(1 for row in data if row.get("evidence_spans")),
                "refusals": sum(1 for row in data if row.get("refused")),
            }
        )
    return rows


def main() -> int:
    main_rows = []
    for dataset, input_path, ref_path, prefix, output_dir in [
        ("RGB", "samples/rgb_all_input.json", "samples/rgb_all_reference.json", "rgb", "outputs/rgb_results"),
        ("RAMDocs", "samples/ramdocs_all_input.json", "samples/ramdocs_all_reference.json", "ramdocs", "outputs/ramdocs_results"),
    ]:
        for method in ["naive_rag", "rerank_rag", "crag_lite", "self_rag_lite"]:
            main_rows.append(
                metric_row(
                    dataset,
                    method,
                    input_path,
                    ref_path,
                    f"{output_dir}/{prefix}_neural_{method}_output.json",
                )
            )
        main_rows.append(
            metric_row(
                dataset,
                "egi_rag",
                input_path,
                ref_path,
                f"outputs/egi_rag/{prefix}/egi_rag_{prefix}_all_output.json",
            )
        )

    controlled_rows = [
        metric_row(
            "RGB noise060 back",
            "egi_rag",
            "samples/controlled/rgb/rgb_noise060_back_input.json",
            "samples/controlled/rgb/rgb_noise060_back_reference.json",
            "outputs/egi_rag/controlled/rgb/egi_rag_rgb_noise060_back_output.json",
        ),
        metric_row(
            "RGB noise100 front",
            "egi_rag",
            "samples/controlled/rgb/rgb_noise100_front_input.json",
            "samples/controlled/rgb/rgb_noise100_front_reference.json",
            "outputs/egi_rag/controlled/rgb/egi_rag_rgb_noise100_front_output.json",
        ),
        metric_row(
            "RAMDocs noise060 front",
            "egi_rag",
            "samples/controlled/ramdocs/ramdocs_noise060_front_input.json",
            "samples/controlled/ramdocs/ramdocs_noise060_front_reference.json",
            "outputs/egi_rag/controlled/ramdocs/egi_rag_ramdocs_noise060_front_output.json",
        ),
        metric_row(
            "RAMDocs noise100 front",
            "egi_rag",
            "samples/controlled/ramdocs/ramdocs_noise100_front_input.json",
            "samples/controlled/ramdocs/ramdocs_noise100_front_reference.json",
            "outputs/egi_rag/controlled/ramdocs/egi_rag_ramdocs_noise100_front_output.json",
        ),
    ]

    custom_rows = [
        metric_row(
            "Custom noise",
            method,
            "samples/custom_noise/custom_noise_all_input.json",
            "samples/custom_noise/custom_noise_all_reference.json",
            f"outputs/custom_noise/{method}_custom_noise_all_output.json",
        )
        for method in ["naive_rag", "rerank_rag", "crag_lite", "egi_rag"]
    ]

    lines: list[str] = [
        "# 最终补全实验分析",
        "",
        "## 1. 执行进度与数据状态",
        "",
        "- 已完成 prompt 标签泄露修复：模型输入只包含 `doc_id`、`title`、`text`，不再包含 `label=correct/noise/misinfo`；评估仍保留 `contexts_used[*].label`。",
        "- 已新增并跑完 EGI-RAG：全量 RGB 300 条、RAMDocs 500 条；controlled 子集 4 组；custom noise 60 条。",
        "- 已新增自定义逻辑缺失噪音：RGB 30 条、RAMDocs 30 条，每条包含 `logic_gap`、`value_swap`、`high_overlap_irrelevant` 三类噪音。",
        "- EGI-RAG 截断/解析问题已修复：短 JSON 输出、512 token 上限、恢复式解析；最终 EGI 输出 parse error 为 0。",
        "- 剩余服务端错误仅 2 条，均为 CRAG-lite 样本，已按计划重试后保留。",
        "",
        "### 剩余错误",
    ]
    err_rows = error_summary()
    lines.extend(table(err_rows, [("File", "file"), ("Rows", "rows"), ("Errors", "errors")]) if err_rows else ["无。"])
    lines += [
        "",
        "### EGI-RAG 输出健康度",
    ]
    lines.extend(table(parse_summary(), [("File", "file"), ("Rows", "rows"), ("Parse Errors", "parse_errors"), ("Evidence Rows", "evidence_rows"), ("Refusals", "refusals")]))

    lines += [
        "",
        "## 2. 噪音添加方式分析",
        "",
        "已有 controlled 数据通过固定噪音比例和正确文档位置构造：把文档按 `correct` 与 `noise/misinfo/contradictory/unknown` 分组，再按 0%-100% 噪音比例和 front/middle/back/random 位置重排。它能回答“好文档位置”和“噪音比例”两个变量的影响。",
        "",
        "新增 custom noise 更贴近题目中的“相关但是缺少逻辑依赖”：`logic_gap` 保留实体和问题背景但删除关键关系，`value_swap` 保留实体但替换答案细节，`high_overlap_irrelevant` 保留高重叠关键词但不给事实依据。标签只用于评估，不进入 prompt。",
        "",
        "## 3. 主结果对比",
        "",
        "旧正式神经 baseline 的 `prompt_version` 为 `formal_v1`，新 EGI-RAG 为 `formal_v2_no_label`。因此表中 baseline 作为历史主结果保留，跨版本比较需要结合 no-label 子集一起看。",
    ]
    lines.extend(
        table(
            main_rows,
            [
                ("Dataset", "dataset"),
                ("Method", "method"),
                ("Prompt", "prompt_version"),
                ("Outputs", "outputs"),
                ("Errors", "errors"),
                ("Accuracy", "accuracy"),
                ("F1", "f1"),
                ("Misinfo", "misinformation_adoption_rate"),
                ("Evidence", "evidence_selection_accuracy"),
                ("Refusal", "refusal_accuracy"),
            ],
        )
    )

    lines += [
        "",
        "结论：RGB 上 EGI-RAG 的 Accuracy 为 0.9200，高于旧 neural baseline；RAMDocs 上为 0.5320，低于 Naive/Rerank 的旧 formal_v1 主结果，但 Misinfo Adoption 为 0.1100，低于 Naive 0.1780 和 Rerank 0.2060，说明证据筛选牺牲部分覆盖率但减少误导采纳。",
        "",
        "## 4. 关键压力测试",
    ]
    lines.extend(
        table(
            controlled_rows,
            [
                ("Setting", "dataset"),
                ("Method", "method"),
                ("Accuracy", "accuracy"),
                ("F1", "f1"),
                ("Misinfo", "misinformation_adoption_rate"),
                ("Evidence", "evidence_selection_accuracy"),
                ("Refusal", "refusal_accuracy"),
                ("Faithfulness", "faithfulness"),
            ],
        )
    )
    lines += [
        "",
        "- RGB 60% 噪音且好文档在后时，EGI-RAG Accuracy 为 0.9200，说明证据抽取能缓解位置不利。",
        "- 100% 噪音下，RGB EGI-RAG Refusal Acc 为 0.8100，与 Naive/Rerank 接近，但 Faithfulness 从 0 提升到 0.2800，说明它能输出部分带证据校验的拒答/修正结果。",
        "- RAMDocs 100% 噪音下 EGI-RAG Refusal Acc 为 0.5900，略高于 Naive/Rerank 的 0.5000/0.5400；但 Misinfo Adoption 仍为 0.3200，说明对强误导答案的防御还不够，后续应强化矛盾检测和拒答阈值。",
        "",
        "## 5. 自定义逻辑缺失噪音",
    ]
    lines.extend(
        table(
            custom_rows,
            [
                ("Dataset", "dataset"),
                ("Method", "method"),
                ("Accuracy", "accuracy"),
                ("F1", "f1"),
                ("Misinfo", "misinformation_adoption_rate"),
                ("Evidence", "evidence_selection_accuracy"),
                ("Refusal", "refusal_accuracy"),
                ("Faithfulness", "faithfulness"),
            ],
        )
    )
    lines += [
        "",
        "结论：自定义噪音实验完成了“可以自己设置噪音”的要求。EGI-RAG Accuracy 0.7833，高于 Naive/Rerank 0.6500；Misinfo Adoption 0.0167，与 Rerank/CRAG 持平并低于 Naive 0.0333。说明把全文输入改成证据句输入，对 value-swap 和 logic-gap 噪音有帮助。",
        "",
        "## 6. 案例对比",
    ]
    lines.extend(
        table(
            build_cases(),
            [
                ("Type", "type"),
                ("ID", "id"),
                ("Question", "question"),
                ("Gold", "gold"),
                ("Baseline Answer", "baseline_answer"),
                ("EGI Answer", "egi_answer"),
                ("Baseline Docs", "baseline_docs"),
                ("EGI Docs", "egi_docs"),
            ],
        )
    )

    lines += [
        "",
        "## 7. 是否完成原意见",
        "",
        "| 意见 | 完成情况 | 说明 |",
        "|---|---|---|",
        "| 好的文档的位置产生的影响 | 已完成 | 旧 controlled 覆盖 front/middle/back/random；新增 EGI controlled 覆盖 RGB noise060 back。 |",
        "| 噪音文档产生的影响 | 已完成 | 覆盖 60% 噪音、100% 噪音、RAMDocs misinfo、自定义三类噪音。 |",
        "| 方法实验结果建设性意见 | 已完成 | 已给出 EGI-RAG 与 baseline 的主结果、压力测试、局限和后续改进建议。 |",
        "| 可以自己设置噪音 | 已完成 | `samples/custom_noise/` 生成 60 条自定义逻辑缺失/值替换/高重叠无关噪音。 |",
        "",
        "## 8. 需要改进的点",
        "",
        "1. 旧正式 neural baseline 是 `formal_v1`，后续若 API 预算允许，应重跑全量 no-label baseline，得到完全公平的主表。",
        "2. RAMDocs 100% 噪音下 EGI-RAG 仍会采纳部分误导答案，应增加 contradiction-aware verifier：若证据来自 `misleading/value_swap` 风格句子或不同证据冲突，则优先拒答。",
        "3. 当前自动评估仍是字符串包含匹配，中文/别名/日期格式会有偏差；最终论文式报告建议加入 30-50 条人工复核或 LLM judge。",
        "4. EGI-RAG 的 prompt 输出格式已经稳定，但仍依赖模型按 JSON 响应；可进一步改成两阶段工具化解析或更严格的 schema retry。",
        "5. 自定义噪音规模为 60 条，足够补题目要求和案例分析，但若作为主结论，应扩大到 200+ 条并分类型报告。",
        "",
        "## 9. 总结",
        "",
        "当前实验已经能支撑题目目标：噪音文档会通过位置、比例、误导答案和逻辑缺失四种方式影响 RAG 推理；单纯检索/重排能缓解普通噪音，但面对 100% 噪音和 misinfo 时忠实性与误导采纳仍有风险。EGI-RAG 通过文档证据评分、证据句抽取和答案支持性校验，在 RGB、自定义噪音和部分压力测试上明显改善；但在 RAMDocs 强误导场景中仍需更强的冲突识别机制。",
    ]

    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"[OK] wrote {REPORT.relative_to(REPO_ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
