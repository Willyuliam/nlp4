"""
步骤3（修正版）：将各数据集转换为统一 JSON schema 并抽取样本

实际字段（经过数据验证）：
  RGB:      id / query / answer / positive / negative  （JSONL 格式）
  RAMDocs:  待确认（下载后运行 inspect_raw 查看）
  CONFLICTS:待确认（下载后运行 inspect_raw 查看）

运行方式：
    python step3_convert_and_sample.py
"""

import json
import random
from pathlib import Path

RAW_DIR   = Path("data/raw")
SAMPLE_DIR = Path("data/samples")
SAMPLE_DIR.mkdir(parents=True, exist_ok=True)
random.seed(42)   # 固定种子，结果可复现


Full = True  # 是否使用全部数据（True）还是抽样（False）

# ──────────────────────────────────────────
# 通用工具
# ──────────────────────────────────────────

def load_file(path: Path) -> list[dict]:
    """自动判断 JSON / JSONL 格式"""
    with open(path, encoding="utf-8") as f:
        first = f.read(1)
    with open(path, encoding="utf-8") as f:
        if first == "[":          # 标准 JSON 数组
            return json.load(f)
        else:                     # JSONL，每行一个对象
            return [json.loads(l) for l in f if l.strip()]


def inspect_raw(path: Path):
    """打印原始字段，帮助核对转换器"""
    data = load_file(path)
    print(f"\n=== {path.name}（共 {len(data)} 条）===")
    print(f"字段: {list(data[0].keys())}")
    print(json.dumps(data[0], ensure_ascii=False, indent=2)[:800])
    return data


def save_samples(converted: list[dict], tag: str):
    """保存 input / reference / full 三份文件"""
    inputs = [{"id": r["id"], "dataset": r["dataset"],
               "question": r["question"], "contexts": r["contexts"]}
              for r in converted]
    refs   = [{"id": r["id"], "gold_answers": r["gold_answers"],
               "wrong_answers": r["wrong_answers"], "_meta": r.get("_meta", {})}
              for r in converted]

    (SAMPLE_DIR / f"{tag}_input.json").write_text(
        json.dumps(inputs, ensure_ascii=False, indent=2), encoding="utf-8")
    (SAMPLE_DIR / f"{tag}_reference.json").write_text(
        json.dumps(refs, ensure_ascii=False, indent=2), encoding="utf-8")
    (SAMPLE_DIR / f"{tag}_full.json").write_text(
        json.dumps(converted, ensure_ascii=False, indent=2), encoding="utf-8")

    label_cnt: dict[str, int] = {}
    for r in converted:
        for c in r["contexts"]:
            label_cnt[c["label"]] = label_cnt.get(c["label"], 0) + 1

    print(f"[{tag.upper()}] 已保存 {len(converted)} 条样本")
    print(f"  文档标签分布: {label_cnt}")
    print(f"  -> data/samples/{tag}_input.json")
    print(f"  -> data/samples/{tag}_reference.json")


# ──────────────────────────────────────────
# RGB 转换器（字段经过数据验证）
#   格式: JSONL，每行一个对象
#   字段: id / query / answer / positive / negative
#   positive/negative: list[str]（纯文本，无 title）
#   answer: list[list[str]]（多个等效答案组）
# ──────────────────────────────────────────

def convert_rgb(item: dict, idx: int) -> dict:
    contexts, dc = [], 1
    for text in item.get("positive", []):
        contexts.append({"doc_id": f"doc_{dc}", "title": "", "text": text, "label": "correct"})
        dc += 1
    for text in item.get("negative", []):
        contexts.append({"doc_id": f"doc_{dc}", "title": "", "text": text, "label": "noise"})
        dc += 1
    random.shuffle(contexts)   # 打乱，避免位置泄露标签

    # answer 是 list[list[str]]，展开并去重
    raw_ans = item.get("answer", item.get("ans", []))
    gold = []
    for sub in raw_ans:
        if isinstance(sub, list):
            gold.extend(sub)
        else:
            gold.append(sub)
    gold = list(dict.fromkeys(gold))   # 去重保序

    return {
        "id": f"rgb_{idx:04d}",
        "dataset": "RGB",
        "question": item.get("query", item.get("question", "")),
        "contexts": contexts,
        "gold_answers": gold,
        "wrong_answers": item.get("wrong_answer", []),
        "_meta": {
            "n_positive": len(item.get("positive", [])),
            "n_negative": len(item.get("negative", [])),
        }
    }


# ──────────────────────────────────────────
# RAMDocs 转换器（字段待实际数据确认）
# ──────────────────────────────────────────

def convert_ramdocs(item: dict, idx: int) -> dict:
    LABEL_MAP = {
        "correct": "correct", "misinfo": "misinfo", "noise": "noise",
        "ambiguous": "noise", "irrelevant": "noise", "unknown": "unknown",
    }
    contexts, dc = [], 1
    for doc in item.get("documents", item.get("passages", item.get("docs", []))):
        raw_label = str(doc.get("type", doc.get("label", "unknown"))).lower()
        contexts.append({
            "doc_id": f"doc_{dc}",
            "title": doc.get("title", ""),
            "text": doc.get("text", doc.get("content", doc.get("passage", ""))),
            "label": LABEL_MAP.get(raw_label, "unknown"),
        })
        dc += 1

    # raw_ans = item.get("answer", item.get("answers", ""))
    raw_ans = item.get("gold_answers", item.get("answer", item.get("answers", "")))
    gold = raw_ans if isinstance(raw_ans, list) else [raw_ans]

    return {
        "id": f"ramdocs_{idx:04d}",
        "dataset": "RAMDocs",
        "question": item.get("question", item.get("query", "")),
        "contexts": contexts,
        "gold_answers": [a for a in gold if a],
        "wrong_answers": item.get("wrong_answers", []),
        "_meta": {"original_id": str(item.get("id", "")), "noise_type": item.get("noise_type", "")},
    }


# ──────────────────────────────────────────
# CONFLICTS 转换器
# ──────────────────────────────────────────

def convert_conflicts(item: dict, idx: int) -> dict:
    contexts = []
    for i, result in enumerate(item.get("search_results", [])):
        text = result.get("response_str", result.get("snippet", result.get("text", "")))
        contexts.append({
            "doc_id": f"doc_{i+1}",
            "title": result.get("title", ""),
            "text": text,
            "label": "unknown",   # 不强行指定立场，避免把冲突方向写死
        })

    # 尝试多个可能的答案字段名，过滤空值
    gold_raw = (item.get("correct_answer")
                or item.get("answer")
                or item.get("gold_answer")
                or "")
    gold_answers = [gold_raw.strip()] if gold_raw.strip() else []

    return {
        "id": f"conflicts_{idx:04d}",
        "dataset": "CONFLICTS",
        "question": item.get("question", ""),
        "contexts": contexts,
        "gold_answers": gold_answers,
        "wrong_answers": [],
        "_meta": {
            "conflict_type": item.get("conflict_type", ""),
            "has_correct_answer": bool(gold_answers),   # 方便后续统计
        }
    }


# ──────────────────────────────────────────
# 主流程
# ──────────────────────────────────────────

def process(raw_candidates: list[Path], converter, tag: str, n: int,full=False):
    path = next((p for p in raw_candidates if p.exists()), None)
    if path is None:
        print(f"\n[{tag.upper()}] ⚠️  未找到文件，跳过。请先下载数据集。")
        print(f"  候选路径: {[str(p) for p in raw_candidates]}")
        return
    data = inspect_raw(path)
    # sample = random.sample(data, min(n, len(data)))
    sample = data if full else random.sample(data, min(n, len(data)))
    converted = [converter(item, i) for i, item in enumerate(sample)]
    save_samples(converted, tag)


def main():
    print("=" * 55)
    print("步骤3（修正版）：数据转换 & 样本抽取")
    print("=" * 55)

    # RGB：JSONL 文件在 git repo 的 data/ 目录下
    process(
        [RAW_DIR / "rgb_repo" / "data" / "en_refine.json",
         RAW_DIR / "rgb_repo" / "data" / "en.json",
         RAW_DIR / "rgb" / "en_refine.json",
         RAW_DIR / "rgb" / "en.json"],
        convert_rgb, "rgb_all", n=30,full=Full
    )

    # RAMDocs：HuggingFace 下载
    process(
        [RAW_DIR / "ramdocs" / "train.json",
         RAW_DIR / "ramdocs" / "test.json",
         RAW_DIR / "ramdocs" / "validation.json"],
        convert_ramdocs, "ramdocs_all", n=20,full=Full
    )

    # CONFLICTS：GitHub clone
    conflicts_files = (
        list((RAW_DIR / "conflicts" / "repo").rglob("*.json")) +
        list((RAW_DIR / "conflicts" / "repo").rglob("*.jsonl"))
    )
    process(conflicts_files[:1] if conflicts_files else [], convert_conflicts, "conflicts_all", n=20,full=Full)

    print("\n[OK] 完成！文件在 data/samples/ 目录")


if __name__ == "__main__":
    main()
