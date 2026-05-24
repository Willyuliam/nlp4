"""
步骤1（修正版）：下载 RGB 数据集

RGB 数据就在 GitHub repo 里（不需要 HuggingFace），直接 git clone 即可。
数据格式：JSONL，每行一条记录。
文件清单：en_refine.json / en.json / zh_refine.json / zh.json 等

运行方式：
    python step1_download_rgb.py
"""

import subprocess
from pathlib import Path
import json

REPO_URL   = "https://github.com/chen700564/RGB.git"
TARGET_DIR = Path("data/raw/rgb_repo")


def clone_rgb():
    if TARGET_DIR.exists():
        print(f"[RGB] 目录已存在：{TARGET_DIR}，跳过克隆")
        return True

    print("[RGB] 正在 git clone（数据直接在 repo 里，无需 HuggingFace）...")
    result = subprocess.run(
        ["git", "clone", "--depth=1", REPO_URL, str(TARGET_DIR)],
        capture_output=True, text=True
    )
    if result.returncode == 0:
        print("  克隆成功！")
        return True
    else:
        print(f"  克隆失败：{result.stderr.strip()}")
        return False


def inspect():
    data_dir = TARGET_DIR / "data"
    files = list(data_dir.glob("*.json")) if data_dir.exists() else []
    print(f"\n[RGB] 数据文件（共 {len(files)} 个）：")
    for f in files:
        # 统计行数
        with open(f, encoding="utf-8") as fh:
            lines = [l for l in fh if l.strip()]
        print(f"  {f.name:<25} {len(lines):>4} 条")

    # 显示 en_refine.json 字段结构
    refine = TARGET_DIR / "data" / "en_refine.json"
    if refine.exists():
        with open(refine, encoding="utf-8") as fh:
            first = json.loads(fh.readline())
        print(f"\n  en_refine.json 字段：{list(first.keys())}")
        print(f"  positive 数量：{len(first['positive'])}")
        print(f"  negative 数量：{len(first['negative'])}")
        print(f"  answer 示例：{first['answer']}")
        print(f"\n  推荐使用：data/raw/rgb_repo/data/en_refine.json（已修正版本）")


if __name__ == "__main__":
    print("=" * 50)
    print("RGB 数据集下载（git clone 方式）")
    print("=" * 50)
    if clone_rgb():
        inspect()
    print("\n完成！下一步运行：python step3_convert_and_sample.py")