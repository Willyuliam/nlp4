"""
步骤4：验证样本格式并输出统计报告

运行方式：
    python scripts/step4_validate_schema.py
"""

import json
from pathlib import Path
from collections import Counter

SAMPLE_DIR = Path("samples")


def validate_item(item: dict, idx: int) -> list[str]:
    """返回该条数据的校验错误列表"""
    errors = []
    required_fields = ["id", "dataset", "question", "contexts", "gold_answers"]
    for field in required_fields:
        if field not in item:
            errors.append(f"缺少字段：{field}")

    if "contexts" in item:
        for ci, ctx in enumerate(item["contexts"]):
            ctx_required = ["doc_id", "title", "text", "label"]
            for cf in ctx_required:
                if cf not in ctx:
                    errors.append(f"contexts[{ci}] 缺少字段：{cf}")
            valid_labels = {"correct", "noise", "misinfo", "contradictory", "unknown", "insufficient"}
            if ctx.get("label") not in valid_labels:
                errors.append(f"contexts[{ci}].label 非法值：{ctx.get('label')}")

    # if "gold_answers" in item and not item["gold_answers"]:
    #     errors.append("gold_answers 为空列表")
        
    if "gold_answers" in item and not item["gold_answers"]:
        # CONFLICTS 数据集允许空答案（situated QA 类问题无唯一答案）
        if item.get("dataset") != "CONFLICTS":
            errors.append("gold_answers 为空列表")

    return errors


def report(dataset_name: str):
    full_path = SAMPLE_DIR / f"{dataset_name.lower()}_full.json"
    if not full_path.exists():
        print(f"[SKIP] {dataset_name}: 未找到 {full_path}")
        return

    with open(full_path, encoding="utf-8") as f:
        data = json.load(f)

    print(f"\n{'='*50}")
    print(f"数据集：{dataset_name}  共 {len(data)} 条样本")
    print(f"{'='*50}")

    all_errors = []
    label_counter: Counter = Counter()
    ctx_per_item = []
    ans_len = []

    for i, item in enumerate(data):
        errors = validate_item(item, i)
        if errors:
            all_errors.append((item.get("id", i), errors))

        for ctx in item.get("contexts", []):
            label_counter[ctx["label"]] += 1
        ctx_per_item.append(len(item.get("contexts", [])))

        for ans in item.get("gold_answers", []):
            ans_len.append(len(ans))

    # 校验结果
    if all_errors:
        print(f"[WARN] 发现 {len(all_errors)} 条格式问题：")
        for item_id, errors in all_errors[:5]:
            print(f"   [{item_id}] {errors}")
        if len(all_errors) > 5:
            print(f"   ... 共 {len(all_errors)} 条（只显示前5条）")
    else:
        print("[OK] 格式校验通过，无问题")

    # 统计信息
    print(f"\n文档标签分布：")
    total_docs = sum(label_counter.values())
    for label, count in sorted(label_counter.items(), key=lambda x: -x[1]):
        pct = count / total_docs * 100 if total_docs else 0
        print(f"   {label:<15} {count:>5} 条  ({pct:.1f}%)")

    print(f"\n每条样本文档数：avg={sum(ctx_per_item)/len(ctx_per_item):.1f}  "
          f"min={min(ctx_per_item)}  max={max(ctx_per_item)}")

    if ans_len:
        print(f"答案长度（字符数）：avg={sum(ans_len)/len(ans_len):.0f}  "
              f"min={min(ans_len)}  max={max(ans_len)}")

    # 打印第一条样本
    print(f"\n--- 第一条样本预览 ---")
    sample = data[0]
    print(f"ID:       {sample['id']}")
    print(f"问题:     {sample['question'][:100]}")
    print(f"文档数:   {len(sample['contexts'])}")
    for ctx in sample['contexts'][:2]:
        print(f"  [{ctx['label']}] {ctx['title'][:40]} | {ctx['text'][:80]}...")
    print(f"参考答案: {sample['gold_answers']}")


if __name__ == "__main__":
    print("步骤4：格式校验 & 统计报告")
    for ds in ["RGB_all", "RAMDocs_all", "CONFLICTS_all"]:
        report(ds)
    print("\n完成！")
