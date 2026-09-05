"""Bước 6: đối chiếu chéo hai tầng và phân loại ca sai.

Chạy:
    C:/Python314/python.exe scripts/06_error_analysis.py

Sinh ra:
    reports/eval/crossover.csv        bảng bốn ô BM25 đúng/sai x dense đúng/sai
    reports/eval/crossover_examples.csv  ví dụ cho từng ô
    reports/eval/error_taxonomy.csv   30 ca sai của hệ tốt nhất, chờ đọc tay
    reports/eval/venn_bm25_dense.png  hình minh họa

Bảng bốn ô là bằng chứng trực tiếp cho luận điểm của đồ án. Nếu ô "BM25 đúng,
dense sai" và ô "BM25 sai, dense đúng" đều lớn thì hai hướng thật sự bù nhau và
việc hợp nhất có cơ sở. Nếu một ô gần bằng không thì một tầng chỉ là tập con của
tầng kia, và phải nói thẳng ra như vậy.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
from matplotlib.patches import Circle

from vlr import config, explain, pipeline

SO_CA_SAI = 30


def ve_venn(chi_bm: int, chi_de: int, ca_hai: int, khong_ai: int) -> None:
    fig, ax = plt.subplots(figsize=(7, 4.6))
    ax.add_patch(Circle((0.38, 0.5), 0.30, alpha=0.42, color="#2D75B6"))
    ax.add_patch(Circle((0.62, 0.5), 0.30, alpha=0.42, color="#D68910"))
    ax.text(0.22, 0.5, str(chi_bm), ha="center", va="center", fontsize=17, weight="bold")
    ax.text(0.50, 0.5, str(ca_hai), ha="center", va="center", fontsize=17, weight="bold")
    ax.text(0.78, 0.5, str(chi_de), ha="center", va="center", fontsize=17, weight="bold")
    ax.text(0.28, 0.86, "BM25 đúng", ha="center", fontsize=12, color="#2D75B6",
            weight="bold")
    ax.text(0.72, 0.86, "Ngữ nghĩa đúng", ha="center", fontsize=12, color="#B9770E",
            weight="bold")
    ax.text(0.5, 0.09, f"Cả hai đều sai: {khong_ai} câu hỏi", ha="center", fontsize=11)
    ax.set_title("Đối chiếu chéo trên tập test, tính ở top-10")
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")
    fig.tight_layout()
    fig.savefig(config.EVAL_DIR / "venn_bm25_dense.png", dpi=150)
    plt.close(fig)
    print("    -> reports/eval/venn_bm25_dense.png")


def main() -> None:
    config.ensure_dirs()
    duong_dan = config.EVAL_DIR / "per_query_test.csv"
    if not duong_dan.exists():
        raise SystemExit(
            "Chưa có reports/eval/per_query_test.csv. Chạy trước:\n"
            "    C:/Python314/python.exe scripts/05_evaluate.py"
        )
    print("=" * 70)
    print("BƯỚC 6: PHÂN TÍCH LỖI")
    print("=" * 70)

    pq = pd.read_csv(duong_dan, encoding="utf-8-sig")
    cot_dung = [c for c in pq.columns if c.startswith("dung@10::")]
    cot_bm = "dung@10::BM25"
    cot_de = next((c for c in cot_dung if c.startswith("dung@10::Dense")), None)
    if cot_de is None:
        raise SystemExit("Không tìm thấy cột kết quả của tầng ngữ nghĩa.")
    print(f"So sánh: {cot_bm}  và  {cot_de}")

    bm = pq[cot_bm].astype(bool)
    de = pq[cot_de].astype(bool)
    ca_hai = int((bm & de).sum())
    chi_bm = int((bm & ~de).sum())
    chi_de = int((~bm & de).sum())
    khong_ai = int((~bm & ~de).sum())

    bang = pd.DataFrame([
        {"o": "cả hai đúng", "so_cau_hoi": ca_hai},
        {"o": "chỉ BM25 đúng", "so_cau_hoi": chi_bm},
        {"o": "chỉ ngữ nghĩa đúng", "so_cau_hoi": chi_de},
        {"o": "cả hai sai", "so_cau_hoi": khong_ai},
    ])
    bang["ty_le_pct"] = (100 * bang["so_cau_hoi"] / len(pq)).round(2)
    bang.to_csv(config.EVAL_DIR / "crossover.csv", **config.CSV_KW)
    print(bang.to_string(index=False))
    print(f"\nTrần lý thuyết nếu hợp nhất hoàn hảo: "
          f"{100 * (ca_hai + chi_bm + chi_de) / len(pq):.2f}% "
          f"(hiện BM25 {100 * bm.mean():.2f}%, ngữ nghĩa {100 * de.mean():.2f}%)")
    ve_venn(chi_bm, chi_de, ca_hai, khong_ai)

    vi_du = []
    for ten, mat_na in [("chi_bm25_dung", bm & ~de), ("chi_ngu_nghia_dung", ~bm & de),
                        ("ca_hai_sai", ~bm & ~de)]:
        for _, h in pq[mat_na].head(8).iterrows():
            vi_du.append({"o": ten, "cau_hoi": h["cau_hoi"],
                          "gold_title": h["gold_title"]})
    pd.DataFrame(vi_du).to_csv(
        config.EVAL_DIR / "crossover_examples.csv", **config.CSV_KW)
    print("    -> reports/eval/crossover_examples.csv")

    # ---------- Ca sai của hệ tốt nhất ----------
    mc = pd.read_csv(config.EVAL_DIR / "model_comparison.csv", encoding="utf-8-sig")
    tot_nhat = mc.sort_values("recall@10", ascending=False).iloc[0]["he_thong"]
    cot_tot = f"dung@10::{tot_nhat}"
    sai = pq[~pq[cot_tot].astype(bool)]
    print(f"\nHệ tốt nhất: {tot_nhat}  |  sai {len(sai)} / {len(pq)} câu hỏi")

    arts = pd.read_parquet(config.ARTICLES_PATH)
    tieu_de = dict(zip(arts["article_id"], arts["title"]))
    van_ban = dict(zip(arts["article_id"], arts["text"]))
    idf = explain.build_idf(list(arts["tokens"]))

    hang = []
    for _, h in sai.head(SO_CA_SAI).iterrows():
        top = str(h["top10_tot_nhat"]).split()[:3]
        hang.append({
            "query_id": h["query_id"],
            "cau_hoi": h["cau_hoi"],
            "gold": h["gold"],
            "gold_title": h["gold_title"],
            "top1": top[0] if top else "",
            "top1_title": tieu_de.get(top[0], "") if top else "",
            "top2_title": tieu_de.get(top[1], "") if len(top) > 1 else "",
            "top3_title": tieu_de.get(top[2], "") if len(top) > 2 else "",
            "tu_khop_voi_top1": explain.to_chuoi(
                explain.matched_terms(h["cau_hoi"],
                                      f"{tieu_de.get(top[0], '')} {van_ban.get(top[0], '')}"
                                      if top else "", idf)),
            "tu_khop_voi_gold": explain.to_chuoi(
                explain.matched_terms(
                    h["cau_hoi"],
                    " ".join(f"{tieu_de.get(a, '')} {van_ban.get(a, '')}"
                             for a in str(h["gold"]).split()), idf)),
            "nguyen_nhan": "",
        })
    df_sai = pd.DataFrame(hang)
    df_sai.to_csv(config.EVAL_DIR / "error_taxonomy.csv", **config.CSV_KW)
    print(f"    -> reports/eval/error_taxonomy.csv ({len(df_sai)} ca, "
          f"cột nguyen_nhan để trống chờ đọc tay)")
    print("    Các loại nguyên nhân dùng để điền: sai_gold, thieu_ngu_canh, "
          "nhieu_dieu_dung, cau_hoi_mo_ho, dieu_qua_dai, khac")

    print("\nNăm ca sai đầu tiên:")
    for _, h in df_sai.head(5).iterrows():
        print(f"\n  HỎI : {h['cau_hoi']}")
        print(f"  GOLD: {h['gold']}  {h['gold_title'][:70]}")
        print(f"  TOP1: {h['top1']}  {h['top1_title'][:70]}")
        print(f"  khớp với top1: {h['tu_khop_voi_top1'][:100]}")
        print(f"  khớp với gold: {h['tu_khop_voi_gold'][:100]}")


if __name__ == "__main__":
    main()
