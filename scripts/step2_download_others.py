"""
步骤2（修正版）：下载 RAMDocs 和 CONFLICTS

RAMDocs：HuggingFace 数据集，使用国内镜像 hf-mirror.com
CONFLICTS：GitHub 仓库，直接 git clone

运行方式：
    python scripts/step2_download_others.py
"""

import subprocess
from pathlib import Path

RAMDOCS_DIR   = Path("data/raw/ramdocs")
CONFLICTS_DIR = Path("data/raw/conflicts/repo")


# ──────────────────── RAMDocs ────────────────────

def download_ramdocs():
    RAMDOCS_DIR.mkdir(parents=True, exist_ok=True)
    print("\n[RAMDocs] 使用 hf-mirror.com 下载...")

    try:
        from datasets import load_dataset
    except ImportError:
        print("  缺少 datasets 库，请先在当前项目环境中安装后再运行。")
        print("  示例：pip install datasets")
        return

    try:
        import datasets as ds_lib
        ds_lib.config.HF_ENDPOINT = "https://hf-mirror.com"

        ds = load_dataset("HanNight/RAMDocs")
        print(f"  下载成功！splits: {list(ds.keys())}")

        import json
        for split_name, split_data in ds.items():
            records = [dict(item) for item in split_data]
            out = RAMDOCS_DIR / f"{split_name}.json"
            out.write_text(json.dumps(records, ensure_ascii=False, indent=2), encoding="utf-8")
            print(f"  已保存：{out}（{len(records)} 条）")

        # 打印字段
        first = dict(ds[list(ds.keys())[0]][0])
        print(f"  字段：{list(first.keys())}")

    except Exception as e:
        print(f"  下载失败：{e}")
        print()
        print("  手动下载方式：")
        print("  1. 浏览器访问 https://hf-mirror.com/datasets/HanNight/RAMDocs/tree/main")
        print("  2. 下载 data/ 目录下的 .json 或 .parquet 文件")
        print("  3. 放到 data/raw/ramdocs/ 目录")
        print()
        print("  或者用 huggingface-cli（如已安装）：")
        print("  HF_ENDPOINT=https://hf-mirror.com huggingface-cli download \\")
        print("      --repo-type dataset HanNight/RAMDocs --local-dir data/raw/ramdocs")


# ──────────────────── CONFLICTS ────────────────────

def download_conflicts():
    print("\n[CONFLICTS] 正在 git clone...")

    if CONFLICTS_DIR.exists():
        print(f"  目录已存在：{CONFLICTS_DIR}，跳过")
        _list_conflicts()
        return

    CONFLICTS_DIR.parent.mkdir(parents=True, exist_ok=True)
    result = subprocess.run(
        ["git", "clone", "--depth=1",
         "https://github.com/google-research-datasets/rag_conflicts.git",
         str(CONFLICTS_DIR)],
        capture_output=True, text=True
    )
    if result.returncode == 0:
        print("  克隆成功！")
        _list_conflicts()
    else:
        print(f"  克隆失败：{result.stderr.strip()}")


def _list_conflicts():
    files = list(CONFLICTS_DIR.rglob("*.json")) + list(CONFLICTS_DIR.rglob("*.jsonl"))
    print(f"  数据文件（共 {len(files)} 个）：")
    for f in files:
        print(f"    {f.relative_to(CONFLICTS_DIR)}")
    if not files:
        all_files = [f for f in CONFLICTS_DIR.rglob("*") if f.is_file()]
        print("  未找到 .json 文件，仓库内容：")
        for f in all_files[:15]:
            print(f"    {f.relative_to(CONFLICTS_DIR)}")


if __name__ == "__main__":
    print("=" * 50)
    print("RAMDocs & CONFLICTS 下载脚本（修正版）")
    print("=" * 50)
    download_ramdocs()
    download_conflicts()
    print("\n完成！下一步运行：python scripts/step3_convert_and_sample.py")
