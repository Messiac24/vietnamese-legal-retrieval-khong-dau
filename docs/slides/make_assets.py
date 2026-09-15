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


DO, XLA = "#C0392B", "#1E7A4B"


def _hop(ax, x, y, w, h, nhan, phu, mau):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.012",
                                linewidth=1.6, edgecolor=mau, facecolor=mau + "1A"))
    ax.text(x + w / 2, y + h * 0.68, nhan, ha="center", va="center",
            fontsize=11, weight="bold", color=MUC)
    ax.text(x + w / 2, y + h * 0.28, phu, ha="center", va="center",
            fontsize=8.5, color=XAM, linespacing=1.25)


def _mui_ten(ax, xy1, xy2):
    ax.add_patch(FancyArrowPatch(xy1, xy2, arrowstyle="-|>", mutation_scale=13,
                                 linewidth=1.3, color=XAM))


def ve_kien_truc() -> None:
    arts = pd.read_parquet(config.ARTICLES_PATH, columns=["article_id"])
    so_doan = len(pd.read_parquet(config.CHUNKS_PATH, columns=["chunk_id"]))
    nghin = lambda x: f"{x:,}".replace(",", ".")
    fig, ax = plt.subplots(figsize=(10, 4.3))
    _hop(ax, 0.00, 0.38, 0.12, 0.24, "Câu hỏi", "có dấu hoặc\nkhông dấu", XAM)
    _hop(ax, 0.155, 0.36, 0.17, 0.28, "Phục hồi dấu",
         "chỉ khi câu thiếu dấu\nbigram + Viterbi", DO)
    _hop(ax, 0.37, 0.66, 0.24, 0.24, "Tầng từ khóa: BM25",
         f"tách từ pyvi, {nghin(len(arts))} điều", XANH)
    _hop(ax, 0.37, 0.10, 0.24, 0.24, "Tầng ngữ nghĩa",
         f"{nghin(so_doan)} đoạn, gộp max", CAM)
    _hop(ax, 0.655, 0.38, 0.15, 0.24, "Hợp nhất", "tổng có trọng số", XLA)
    _hop(ax, 0.845, 0.38, 0.155, 0.24, "Trả lời", "trích khoản luật\nkèm từ khớp", XAM)
    _mui_ten(ax, (0.12, 0.50), (0.155, 0.50))
    _mui_ten(ax, (0.325, 0.54), (0.37, 0.76))
    _mui_ten(ax, (0.325, 0.46), (0.37, 0.22))
    _mui_ten(ax, (0.61, 0.76), (0.655, 0.56))
    _mui_ten(ax, (0.61, 0.22), (0.655, 0.44))
    _mui_ten(ax, (0.805, 0.50), (0.845, 0.50))
    ax.text(0.49, 0.94, "bắt đúng số hiệu, thuật ngữ, con số",
            ha="center", fontsize=8.5, color=XANH, style="italic")
    ax.text(0.49, 0.03, "bắt được diễn đạt khác, không cần trùng từ",
            ha="center", fontsize=8.5, color="#B9770E", style="italic")
    ax.text(0.24, 0.27, "câu có dấu đi thẳng qua", ha="center", fontsize=8.5,
            color=DO, style="italic")
    ax.set_xlim(-0.015, 1.015)
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


def ve_khong_dau() -> None:
    """Recall@10 khi câu hỏi gõ không dấu, đọc từ reports/eval/khong_dau.csv."""
    kq = pd.read_csv(config.EVAL_DIR / "khong_dau.csv", encoding="utf-8-sig")
    lay = lambda dk, cach, he: 100 * float(kq[(kq.dieu_kien == dk) & (kq.cach_xu_ly == cach)
                                             & (kq.he_thong == he)]["recall@10"].iloc[0])
    dong = [
        ("Câu có dấu, hệ lai (mốc)", lay("có dấu", "giữ nguyên", "Hợp nhất"), XAM),
        ("Không dấu, BM25 giữ nguyên", lay("không dấu", "giữ nguyên", "BM25"), DO),
        ("Không dấu, ngữ nghĩa giữ nguyên", lay("không dấu", "giữ nguyên", "Ngữ nghĩa"), DO),
        ("Không dấu, hệ lai giữ nguyên", lay("không dấu", "giữ nguyên", "Hợp nhất"), DO),
        ("Không dấu, BM25 chỉ mục bỏ dấu", lay("không dấu", "chỉ mục bỏ dấu", "BM25 bỏ dấu"), CAM),
        ("Không dấu, phục hồi dấu rồi hệ lai", lay("không dấu", "phục hồi dấu", "Hợp nhất"), XLA),
    ][::-1]
    fig, ax = plt.subplots(figsize=(8.8, 3.7))
    thanh = ax.barh([d[0] for d in dong], [d[1] for d in dong],
                    color=[d[2] for d in dong], alpha=0.9)
    for t, d in zip(thanh, dong):
        ax.text(d[1] + 1, t.get_y() + t.get_height() / 2, f"{d[1]:.2f}".replace(".", ","),
                va="center", fontsize=10.5, weight="bold")
    ax.set_xlim(0, 108)
    ax.set_xlabel("Recall@10 (%) trên 788 câu hỏi test")
    ax.tick_params(axis="y", labelsize=10)
    ax.grid(axis="x", alpha=0.3)
    fig.tight_layout()
    fig.savefig(IMG / "khong_dau.png", dpi=170)
    plt.close(fig)
    print("  khong_dau.png")


def sao_chep_bieu_do() -> None:
    for ten in ("recall_curve.png", "alpha_curve.png", "venn_bm25_dense.png"):
        nguon = config.EVAL_DIR / ten
        if nguon.exists():
            shutil.copy2(nguon, IMG / ten)
            print(f"  {ten} (sao từ reports/eval)")
        else:
            print(f"  THIẾU {ten}: chạy scripts/05_evaluate.py và 06_error_analysis.py")


def ve_bia() -> None:
    """Nền trang bìa: các dòng văn bản mờ gợi hình một trang văn bản luật.

    Tự vẽ thay vì lấy ảnh trên mạng để khỏi vướng bản quyền.
    """
    import numpy as np

    rng = np.random.default_rng(config.SEED)
    fig, ax = plt.subplots(figsize=(10, 7.5))
    ax.set_facecolor("#12243A")
    fig.patch.set_facecolor("#12243A")
    y = 0.94
    while y > 0.04:
        if rng.random() < 0.16:
            ax.plot([0.08, 0.08 + 0.30 * rng.random()], [y, y],
                    color="#7FB3E8", lw=2.6, alpha=0.30)
            y -= 0.035
            continue
        rong = 0.55 + 0.32 * rng.random()
        ax.plot([0.08, 0.08 + rong], [y, y], color="#BBD5F0", lw=1.5, alpha=0.13)
        y -= 0.022
    for _ in range(220):
        ax.scatter(rng.random(), rng.random(), s=rng.random() * 7,
                   color="#2D75B6", alpha=0.16)
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")
    fig.subplots_adjust(0, 0, 1, 1)
    fig.savefig(IMG / "cover.png", dpi=140, facecolor="#12243A")
    plt.close(fig)
    print("  cover.png")


def main() -> None:
    IMG.mkdir(parents=True, exist_ok=True)
    print("Sinh hình cho slide:")
    ve_bia()
    ve_kien_truc()
    ve_do_dai()
    ve_kiem_toan()
    ve_khong_dau()
    sao_chep_bieu_do()


if __name__ == "__main__":
    main()
