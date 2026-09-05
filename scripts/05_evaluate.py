"""Bước 5: chấm điểm trên tập test, ĐÚNG MỘT LẦN.

Chạy:
    C:/Python314/python.exe scripts/05_evaluate.py

Sinh ra:
    reports/eval/model_comparison.csv   bảng số chính của đồ án
    reports/eval/gold_sensitivity.csv   gold gốc so với gold mở rộng
    reports/eval/cost_comparison.csv    độ trễ và dung lượng chỉ mục
    reports/eval/per_query_test.csv     kết quả từng câu hỏi, cho bước 6
    reports/eval/recall_curve.png       biểu đồ Recall@k
    reports/eval/alpha_curve.png        đường alpha quét trên val

Mọi tham số lấy từ reports/eval/chosen_params.json, tức là đã chốt trên val
trước khi script này chạy. Không có vòng lặp nào ở đây chỉnh tham số theo test.
"""
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from vlr import config, dense, fusion, lexical, metrics, pipeline, textnorm


def _pooling_tot_nhat(ten: str, mac_dinh: str = "max") -> str:
    duong_dan = config.EVAL_DIR / "tuning_pooling.csv"
    if not duong_dan.exists():
        return mac_dinh
    df = pd.read_csv(duong_dan, encoding="utf-8-sig")
    phan = df[df["mo_hinh"] == ten]
    if phan.empty:
        return mac_dinh
    cot = [c for c in df.columns if c.startswith("recall@")][0]
    return phan.sort_values(cot, ascending=False).iloc[0]["gop_doan"]


def do_do_tre(ham, cau_hoi: list[str], so_lan: int = 60) -> tuple[float, float]:
    """Đo độ trễ một truy vấn một, đúng cảnh người dùng thật gõ một câu hỏi.

    Không đo theo lô: chạy theo lô cho ra con số đẹp nhưng không phải thứ người
    dùng cảm nhận được.
    """
    ham(cau_hoi[0])  # làm nóng
    t = []
    for c in cau_hoi[:so_lan]:
        t0 = time.perf_counter()
        ham(c)
        t.append((time.perf_counter() - t0) * 1000)
    return float(np.median(t)), float(np.percentile(t, 95))


def main() -> None:
    t_bat_dau = time.perf_counter()
    config.ensure_dirs()
    print("=" * 70)
    print("BƯỚC 5: CHẤM ĐIỂM TRÊN TẬP TEST")
    print("=" * 70)

    ts = pipeline.doc_tham_so()
    print(json.dumps(ts, ensure_ascii=False, indent=2))
    gold, text = pipeline.load_split("test")
    gold_rong = pipeline.gold_mo_rong(gold)
    them = sum(len(gold_rong[q]) - len(gold[q]) for q in gold)
    print(f"\ntest: {len(gold)} câu hỏi. Gold mở rộng thêm tổng cộng {them} điều luật.")

    arts = pd.read_parquet(config.ARTICLES_PATH)
    ids = list(text)
    cau_hoi = [text[q] for q in ids]

    # ---------- Tầng từ khóa ----------
    print("\n[1] BM25")
    idx_bm = lexical.BM25Index(arts, **ts["bm25"])
    toks = {q: textnorm.tokens(text[q]) for q in ids}
    bm_runs = {q: idx_bm.search_tokens(toks[q], config.TOPK_FUSION) for q in ids}
    tre_bm = do_do_tre(lambda c: idx_bm.search_tokens(textnorm.tokens(c), 10), cau_hoi)
    print(f"    độ trễ p50 {tre_bm[0]:.1f} ms, p95 {tre_bm[1]:.1f} ms")

    # ---------- Tầng ngữ nghĩa ----------
    de_runs: dict[str, dict] = {}
    tre_de: dict[str, tuple[float, float]] = {}
    pooling_dung: dict[str, str] = {}
    for ten in ("bkai", "aiteam", "bkai_ft"):
        thu_muc = config.INDEX_DIR / ten
        if not (thu_muc / "meta.json").exists():
            print(f"\n[-] bỏ qua {ten}: chưa có chỉ mục")
            continue
        pooling = _pooling_tot_nhat(ten)
        pooling_dung[ten] = pooling
        print(f"\n[2] dense {ten} (gộp {pooling})")
        idx = dense.DenseIndex.load(thu_muc)
        vecs = idx.encode_queries(cau_hoi)
        kq = idx.search(vecs, top_k=config.TOPK_FUSION, pooling=pooling,
                        chunk_top=config.CHUNK_TOP)
        de_runs[ten] = dict(zip(ids, kq))
        tre_de[ten] = do_do_tre(
            lambda c, i=idx, p=pooling: i.search(
                i.encode_queries([c]), top_k=10, pooling=p,
                chunk_top=config.CHUNK_TOP),
            cau_hoi, so_lan=40,
        )
        print(f"    độ trễ p50 {tre_de[ten][0]:.0f} ms, p95 {tre_de[ten][1]:.0f} ms")
        del idx

    # ---------- Hợp nhất ----------
    sach = ts["dense"]["mo_hinh"]
    he_thong: dict[str, dict] = {"BM25": bm_runs}
    for t, r in de_runs.items():
        he_thong[f"Dense {t}"] = r
    if sach in de_runs:
        he_thong[f"RRF (BM25 + {sach})"] = pipeline.hop_nhat_rrf(
            bm_runs, de_runs[sach], ts["rrf"]["rrf_k"], config.TOPK_FUSION)
        he_thong[f"Trọng số (BM25 + {sach})"] = pipeline.hop_nhat_alpha(
            bm_runs, de_runs[sach], ts["weighted"]["alpha"], config.TOPK_FUSION)
    ban = ts.get("dense_nhiem_ban", {}).get("mo_hinh")
    if ban and ban in de_runs:
        he_thong[f"RRF (BM25 + {ban})"] = pipeline.hop_nhat_rrf(
            bm_runs, de_runs[ban], ts["rrf_nhiem_ban"]["rrf_k"], config.TOPK_FUSION)
        he_thong[f"Trọng số (BM25 + {ban})"] = pipeline.hop_nhat_alpha(
            bm_runs, de_runs[ban], ts["weighted_nhiem_ban"]["alpha"],
            config.TOPK_FUSION)

    def _nhan_nhiem_ban(ten_he: str) -> str:
        for m, ghi_chu in config.NHIEM_BAN.items():
            if ghi_chu and (ten_he.endswith(m) or ten_he.endswith(f"{m})")):
                return ghi_chu
        return ""

    # ---------- Bảng kết quả ----------
    print("\n[3] Bảng kết quả trên test")
    chi_phi = {}
    cp_path = config.EVAL_DIR / "index_cost.csv"
    if cp_path.exists():
        d = pd.read_csv(cp_path, encoding="utf-8-sig")
        chi_phi = dict(zip(d["chi_muc"], d["dung_luong_mb"]))

    hang = []
    for ten, runs in he_thong.items():
        xep = pipeline.chi_diem(runs)
        d = {"he_thong": ten}
        for k in config.EVAL_KS:
            d[f"recall@{k}"] = round(
                sum(metrics.recall_at_k(xep[q], gold[q], k) for q in xep) / len(xep), 4)
        d["mrr@10"] = round(
            sum(metrics.mrr_at_k(xep[q], gold[q], 10) for q in xep) / len(xep), 4)
        d["ndcg@10"] = round(
            sum(metrics.ndcg_at_k(xep[q], gold[q], 10) for q in xep) / len(xep), 4)
        d["f2@10"] = round(
            sum(metrics.f2_at_k(xep[q], gold[q], 10) for q in xep) / len(xep), 4)
        if ten == "BM25":
            d["latency_p50_ms"], d["latency_p95_ms"] = round(tre_bm[0], 1), round(tre_bm[1], 1)
            d["chi_muc_mb"] = chi_phi.get("bm25")
        elif ten.startswith("Dense "):
            m = ten.split()[1]
            d["latency_p50_ms"], d["latency_p95_ms"] = (round(tre_de[m][0], 1),
                                                        round(tre_de[m][1], 1))
            d["chi_muc_mb"] = chi_phi.get(m)
        else:
            m = next((x for x in de_runs if ten.endswith(f"{x})")), sach)
            d["latency_p50_ms"] = round(tre_bm[0] + tre_de.get(m, (0, 0))[0], 1)
            d["latency_p95_ms"] = round(tre_bm[1] + tre_de.get(m, (0, 0))[1], 1)
            d["chi_muc_mb"] = round((chi_phi.get("bm25") or 0) + (chi_phi.get(m) or 0), 1)
        d["nhiem_ban"] = _nhan_nhiem_ban(ten)
        hang.append(d)
    bang = pd.DataFrame(hang)
    bang.to_csv(config.EVAL_DIR / "model_comparison.csv", **config.CSV_KW)
    print(bang.to_string(index=False))

    # ---------- Độ nhạy của gold ----------
    print("\n[4] Gold gốc so với gold mở rộng")
    hang = []
    for ten, runs in he_thong.items():
        xep = pipeline.chi_diem(runs)
        g = sum(metrics.recall_at_k(xep[q], gold[q], 10) for q in xep) / len(xep)
        r = sum(metrics.recall_at_k(xep[q], gold_rong[q], 10) for q in xep) / len(xep)
        hang.append({"he_thong": ten, "recall@10_gold_goc": round(g, 4),
                     "recall@10_gold_mo_rong": round(r, 4),
                     "chenh_lech": round(r - g, 4)})
    ds = pd.DataFrame(hang)
    ds.to_csv(config.EVAL_DIR / "gold_sensitivity.csv", **config.CSV_KW)
    print(ds.to_string(index=False))

    # ---------- Kết quả từng câu hỏi ----------
    tieu_de = dict(zip(arts["article_id"], arts["title"]))
    # Hệ tốt nhất để phân tích lỗi phải là hệ SẠCH. Chọn hệ nhiễm bẩn thì phần
    # phân tích lỗi cũng bị nhiễm theo.
    chi_sach = bang[bang["nhiem_ban"] == ""]
    tot_nhat = chi_sach.sort_values("recall@10", ascending=False).iloc[0]["he_thong"]
    cao_nhat = bang.sort_values("recall@10", ascending=False).iloc[0]["he_thong"]
    print(f"\n[5] Hệ sạch tốt nhất theo recall@10: {tot_nhat}")
    if cao_nhat != tot_nhat:
        print(f"    (điểm cao nhất bảng là {cao_nhat}, nhưng nhiễm bẩn)")
    hang = []
    for q in ids:
        d = {"query_id": q, "cau_hoi": text[q],
             "gold": " ".join(sorted(gold[q])),
             "gold_title": " | ".join(tieu_de.get(a, "") for a in sorted(gold[q]))}
        for ten, runs in he_thong.items():
            xep = [a for a, _ in runs[q]]
            d[f"dung@10::{ten}"] = int(bool(set(xep[:10]) & gold[q]))
        d["top10_tot_nhat"] = " ".join(a for a, _ in he_thong[tot_nhat][q][:10])
        hang.append(d)
    pd.DataFrame(hang).to_csv(config.EVAL_DIR / "per_query_test.csv", **config.CSV_KW)
    print(f"    -> reports/eval/per_query_test.csv")

    # Ghi lại lựa chọn để bước 6 dùng đúng hệ này, không tự chọn lại. Bản đầu
    # tiên để bước 6 tự chọn theo điểm cao nhất, nên nó lọc ca sai theo một hệ
    # còn cột top10 lại của hệ khác, ra bảng mâu thuẫn.
    (config.EVAL_DIR / "best_system.json").write_text(
        json.dumps({"he_sach_tot_nhat": tot_nhat,
                    "he_diem_cao_nhat": cao_nhat,
                    "dense_sach": sach,
                    "cot_dense_sach": f"dung@10::Dense {sach}"},
                   ensure_ascii=False, indent=2),
        encoding="utf-8")
    print("    -> reports/eval/best_system.json")

    # ---------- Biểu đồ ----------
    ve_recall(bang)
    ve_alpha()
    print(f"\nTổng thời gian: {(time.perf_counter() - t_bat_dau) / 60:.1f} phút")


def ve_recall(bang: pd.DataFrame) -> None:
    ks = list(config.EVAL_KS)
    fig, ax = plt.subplots(figsize=(9, 5))
    rong = 0.8 / len(bang)
    x = np.arange(len(ks))
    for i, (_, h) in enumerate(bang.iterrows()):
        ban = bool(h.get("nhiem_ban"))
        ax.bar(x + i * rong, [h[f"recall@{k}"] for k in ks], rong,
               label=h["he_thong"] + (" (nhiễm bẩn)" if ban else ""),
               hatch="//" if ban else None,
               alpha=0.55 if ban else 1.0)
    ax.set_xticks(x + 0.4 - rong / 2)
    ax.set_xticklabels([f"Recall@{k}" for k in ks])
    ax.set_ylabel("Recall")
    ax.set_title("Recall trên tập test, 788 câu hỏi, gold gốc.\n"
                 "Cột gạch chéo dùng mô hình đã thấy dữ liệu này khi huấn luyện.",
                 fontsize=11)
    ax.legend(fontsize=8)
    ax.grid(axis="y", alpha=0.3)
    fig.tight_layout()
    fig.savefig(config.EVAL_DIR / "recall_curve.png", dpi=150)
    plt.close(fig)
    print("    -> reports/eval/recall_curve.png")


def ve_alpha() -> None:
    duong_dan = config.EVAL_DIR / "tuning_alpha.csv"
    if not duong_dan.exists():
        return
    df = pd.read_csv(duong_dan, encoding="utf-8-sig")
    cot = [c for c in df.columns if c.startswith("recall@")][0]
    ts = pipeline.doc_tham_so()
    fig, ax = plt.subplots(figsize=(8, 4.5))
    ax.plot(df["alpha"], df[cot], marker="o", ms=3)
    ax.axvline(ts["weighted"]["alpha"], color="crimson", ls="--",
               label=f"alpha đã chọn = {ts['weighted']['alpha']}")
    ax.set_xlabel("alpha  (0 = BM25 thuần, 1 = ngữ nghĩa thuần)")
    ax.set_ylabel(cot)
    ax.set_title("Quét trọng số hợp nhất trên tập val")
    ax.legend()
    ax.grid(alpha=0.3)
    fig.tight_layout()
    fig.savefig(config.EVAL_DIR / "alpha_curve.png", dpi=150)
    plt.close(fig)
    print("    -> reports/eval/alpha_curve.png")


if __name__ == "__main__":
    main()
