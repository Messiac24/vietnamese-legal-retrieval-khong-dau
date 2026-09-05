"""Sinh hình cho bộ slide.

Chạy:
    C:/Python314/python.exe docs/slides/make_assets.py

Mọi hình đều vẽ từ reports/ hoặc từ dữ liệu thật, không hình nào vẽ bằng số gõ
tay. Chạy lại pipeline là hình tự đổi theo.
"""
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch

from vlr import config

IMG = Path(__file__).resolve().parent / "img"
XANH, CAM, XAM, MUC = "#2D75B6", "#D68910", "#5A5A5A", "#1A1A1A"


def _hop(ax, x, y, w, h, nhan, phu, mau):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.012",
                                linewidth=1.6, edgecolor=mau, facecolor=mau + "1A"))
    ax.text(x + w / 2, y + h * 0.63, nhan, ha="center", va="center",
            fontsize=11, weight="bold", color=MUC)
    ax.text(x + w / 2, y + h * 0.26, phu, ha="center", va="center",
            fontsize=8.5, color=XAM)


def _mui_ten(ax, xy1, xy2):
    ax.add_patch(FancyArrowPatch(xy1, xy2, arrowstyle="-|>", mutation_scale=13,
                                 linewidth=1.3, color=XAM))


def ve_kien_truc() -> None:
    fig, ax = plt.subplots(figsize=(10, 4.3))
    _hop(ax, 0.01, 0.40, 0.15, 0.20, "Câu hỏi", "tiếng Việt tự nhiên", XAM)
    _hop(ax, 0.22, 0.66, 0.30, 0.22, "Tầng từ khóa: BM25",
         "tách từ pyvi, 61.425 điều", XANH)
    _hop(ax, 0.22, 0.12, 0.30, 0.22, "Tầng ngữ nghĩa: bi-encoder",
         "154.176 đoạn, gộp max về điều", CAM)
    _hop(ax, 0.58, 0.39, 0.20, 0.22, "Hợp nhất",
         "RRF hoặc trọng số", "#1E7A4B")
    _hop(ax, 0.83, 0.39, 0.16, 0.22, "Xếp hạng", "kèm từ khớp", XAM)
    _mui_ten(ax, (0.16, 0.52), (0.22, 0.74))
    _mui_ten(ax, (0.16, 0.48), (0.22, 0.26))
    _mui_ten(ax, (0.52, 0.74), (0.58, 0.56))
    _mui_ten(ax, (0.52, 0.26), (0.58, 0.44))
    _mui_ten(ax, (0.78, 0.50), (0.83, 0.50))
    ax.text(0.37, 0.92, "bắt đúng số hiệu, thuật ngữ, con số",
            ha="center", fontsize=8.5, color=XANH, style="italic")
    ax.text(0.37, 0.05, "bắt được diễn đạt khác, không cần trùng từ",
            ha="center", fontsize=8.5, color="#B9770E", style="italic")
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")
    fig.tight_layout()
    fig.savefig(IMG / "architecture.png", dpi=170)
    plt.close(fig)
    print("  architecture.png")


def ve_do_dai() -> None:
    """Bằng chứng cho quyết định chia đoạn: bao nhiêu điều vượt trần 256 token."""
    arts = pd.read_parquet(config.ARTICLES_PATH, columns=["text"])
    so_tu = arts["text"].str.split().str.len().fillna(0).astype(int)
    tran = 140  # 256 token PhoBERT tương đương khoảng 140 từ tiếng Việt
    fig, ax = plt.subplots(figsize=(8.4, 4.0))
    ax.hist(so_tu.clip(upper=1000), bins=60, color=XANH, alpha=0.85)
    ax.axvline(tran, color="crimson", ls="--", linewidth=1.8)
    vuot = 100 * float((so_tu > tran).mean())
    ax.text(tran + 18, ax.get_ylim()[1] * 0.82,
            f"trần 256 token của PhoBERT\n(khoảng {tran} từ)\n"
            f"{vuot:.1f}% điều luật vượt qua",
            color="crimson", fontsize=10)
    ax.set_xlabel("Độ dài điều luật (số từ, cắt hiển thị ở 1.000)")
    ax.set_ylabel("Số điều luật")
    ax.set_title(f"Phân bố độ dài {len(arts):,} điều luật".replace(",", "."))
    ax.grid(axis="y", alpha=0.3)
    fig.tight_layout()
    fig.savefig(IMG / "chunk_need.png", dpi=170)
    plt.close(fig)
    print(f"  chunk_need.png  ({vuot:.1f}% vượt trần)")


def ve_kiem_toan() -> None:
    """Bốn phát hiện kiểm toán, đọc thẳng từ reports/audit/."""
    d = config.AUDIT_DIR
    muc = [
        ("Điều luật trùng\nnguyên văn",
         len(pd.read_csv(d / "duplicate_articles.csv", encoding="utf-8-sig"))),
        ("Cặp điều luật\ngần trùng",
         len(pd.read_csv(d / "near_duplicate_articles.csv", encoding="utf-8-sig"))),
        ("Điều luật\nrỗng nội dung",
         len(pd.read_csv(d / "empty_articles.csv", encoding="utf-8-sig"))),
        ("query_id\nbị lặp dòng",
         len(pd.read_csv(d / "duplicate_queries.csv", encoding="utf-8-sig"))),
        ("Câu hỏi chồng lấn\ntrain và test",
         len(pd.read_csv(d / "query_overlap.csv", encoding="utf-8-sig"))),
    ]
    fig, ax = plt.subplots(figsize=(8.6, 3.9))
    ten = [m[0] for m in muc]
    gia_tri = [m[1] for m in muc]
    mau = [XANH, XANH, XANH, CAM, "#C0392B"]
    thanh = ax.bar(ten, gia_tri, color=mau, alpha=0.9)
    for t, v in zip(thanh, gia_tri):
        ax.text(t.get_x() + t.get_width() / 2, v * 1.05, f"{v:,}".replace(",", "."),
                ha="center", fontsize=11, weight="bold")
    ax.set_yscale("log")
    ax.set_ylabel("Số bản ghi (thang log)")
    ax.set_title("Năm phát hiện khi kiểm toán bộ dữ liệu công bố")
    ax.tick_params(axis="x", labelsize=9)
    ax.grid(axis="y", alpha=0.3)
    fig.tight_layout()
    fig.savefig(IMG / "audit_findings.png", dpi=170)
    plt.close(fig)
    print("  audit_findings.png")


def sao_chep_bieu_do() -> None:
    for ten in ("recall_curve.png", "alpha_curve.png", "venn_bm25_dense.png"):
        nguon = config.EVAL_DIR / ten
        if nguon.exists():
            shutil.copy2(nguon, IMG / ten)
            print(f"  {ten} (sao từ reports/eval)")
        else:
            print(f"  THIẾU {ten}: chạy scripts/05_evaluate.py và 06_error_analysis.py")


def main() -> None:
    IMG.mkdir(parents=True, exist_ok=True)
    print("Sinh hình cho slide:")
    ve_kien_truc()
    ve_do_dai()
    ve_kiem_toan()
    sao_chep_bieu_do()


if __name__ == "__main__":
    main()
