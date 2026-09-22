"""Đếm phân bố độ dài điều luật cho biểu đồ ở slide 9, và vẽ nền bìa.

    C:/Python314/python.exe docs/slides/make_assets.py
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from vlr import config

IMG = Path(__file__).resolve().parent / "img"
BUOC = 20      # độ rộng mỗi cột phân bố, tính bằng từ
TRAN_TU = 140  # 256 token PhoBERT tương đương khoảng 140 từ tiếng Việt


def do_dai() -> None:
    arts = pd.read_parquet(config.ARTICLES_PATH, columns=["text"])
    so_tu = arts["text"].str.split().str.len().fillna(0).astype(int)
    vuot = 100 * float((so_tu > TRAN_TU).mean())
    # cột cuối gom mọi điều dài từ 1.000 từ trở lên
    cot = [{"tu": a, "den": a + BUOC, "so_dieu": int(((so_tu >= a) & (so_tu < a + BUOC)).sum())}
           for a in range(0, 1000, BUOC)]
    cot.append({"tu": 1000, "den": None, "so_dieu": int((so_tu >= 1000).sum())})
    (config.AUDIT_DIR / "do_dai_dieu.json").write_text(json.dumps({
        "tran_token_phobert": 256, "tran_tu_tuong_duong": TRAN_TU,
        "so_dieu": int(len(arts)), "ty_le_vuot_tran_pct": round(vuot, 1),
        "trung_vi_tu": int(so_tu.median()), "buoc_tu": BUOC, "phan_bo": cot,
    }, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"  do_dai_dieu.json  ({vuot:.1f}% vượt trần, {len(cot)} cột)")


def ve_bia() -> None:
    rng = np.random.default_rng(config.SEED)
    nen = "#16222C"
    fig, ax = plt.subplots(figsize=(13.333, 7.5))
    ax.set_facecolor(nen)
    fig.patch.set_facecolor(nen)
    y = 0.93
    while y > 0.06:
        if rng.random() < 0.14:   # dòng tiêu đề điều
            ax.plot([0.60, 0.60 + 0.18 * rng.random()], [y, y], color="#9FC2DB", lw=2.4, alpha=0.30)
            y -= 0.04
            continue
        ax.plot([0.60, 0.60 + 0.30 + 0.14 * rng.random()], [y, y], color="#C9D6DF", lw=1.3, alpha=0.12)
        y -= 0.024
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")
    fig.subplots_adjust(0, 0, 1, 1)
    fig.savefig(IMG / "cover.png", dpi=120, facecolor=nen)
    plt.close(fig)
    print("  cover.png")


def main() -> None:
    IMG.mkdir(parents=True, exist_ok=True)
    print("Sinh dữ liệu cho slide:")
    ve_bia()
    do_dai()


if __name__ == "__main__":
    main()
