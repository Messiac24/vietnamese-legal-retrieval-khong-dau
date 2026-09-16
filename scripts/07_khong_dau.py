"""Bước 7: câu hỏi gõ không dấu.

Chạy:
    C:/Python314/python.exe scripts/07_khong_dau.py

Sinh ra:
    data/index/bm25_khong_dau/            chỉ mục BM25 trên văn bản đã bỏ dấu
    data/index/phuc_hoi_dau.pkl           mô hình phục hồi dấu
    reports/eval/khong_dau_tuning.csv     lambda và alpha quét trên val
    reports/eval/khong_dau_tach_tu.csv    tách ảnh hưởng của cách tách từ, trên val
    reports/eval/khong_dau_params.json    tham số đã chốt trên val
    reports/eval/khong_dau.csv            bảng kết quả trên test, ba kiểu gõ
    reports/eval/khong_dau_vi_du.csv      câu hỏi, bản bỏ dấu, bản phục hồi
    reports/eval/khong_dau_loi.csv        phục hồi sai có làm hỏng truy hồi không

Câu không dấu và câu gõ dấu một nửa đều tạo bằng cách bỏ dấu câu hỏi gốc, nên
gold giữ nguyên. Mô hình phục hồi dấu học từ kho điều luật và câu hỏi TRAIN;
lambda và alpha chốt trên val; test chạy một lần.
"""
import json
import random
import re
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import numpy as np
import pandas as pd

from vlr import config, dense, diacritics, lexical, metrics, pipeline, textnorm


_TACH = re.compile(r"(\w+)", re.UNICODE)


def am_tiet_bo_dau(s: str) -> list[str]:
    return diacritics.am_tiet(diacritics.bo_dau(s))


def bo_dau_mot_nua(s: str, rng: random.Random, p: float = 0.5) -> str:
    """Mô phỏng người gõ dấu một nửa: mỗi âm tiết bị bỏ dấu với xác suất p."""
    phan = _TACH.split(s)
    for i in range(1, len(phan), 2):
        if rng.random() < p:
            phan[i] = diacritics.bo_dau(phan[i])
    return "".join(phan)


def chi_so(runs: dict, gold: dict) -> dict:
    xep = pipeline.chi_diem(runs)
    thieu = set(gold) - set(xep)
    if thieu:
        raise ValueError(f"lượt chạy thiếu {len(thieu)} câu hỏi so với gold")
    n = len(xep)
    return {
        "recall@1": round(sum(metrics.recall_at_k(xep[q], gold[q], 1) for q in xep) / n, 4),
        "recall@5": round(sum(metrics.recall_at_k(xep[q], gold[q], 5) for q in xep) / n, 4),
        "recall@10": round(sum(metrics.recall_at_k(xep[q], gold[q], 10) for q in xep) / n, 4),
        "mrr@10": round(sum(metrics.mrr_at_k(xep[q], gold[q], 10) for q in xep) / n, 4),
    }


def chay_he(text, bm, bm_kd, de, ts, alpha_kd):
    """Mọi hệ cho một bộ câu hỏi. Trả về dict tên hệ -> runs."""
    K = config.TOPK_FUSION
    a = ts["weighted"]["alpha"]
    r = {}
    r["BM25"] = {q: bm.search_tokens(textnorm.tokens(t), K) for q, t in text.items()}
    r["BM25 bỏ dấu"] = {q: bm_kd.search_tokens(am_tiet_bo_dau(t), K) for q, t in text.items()}
    r["Ngữ nghĩa"] = pipeline.dense_runs(de, text, K, ts["dense"]["gop_doan"])
    r["Hợp nhất"] = pipeline.hop_nhat_alpha(r["BM25"], r["Ngữ nghĩa"], a, K)
    if alpha_kd is not None:
        r["Hợp nhất BM25 bỏ dấu"] = pipeline.hop_nhat_alpha(
            r["BM25 bỏ dấu"], r["Ngữ nghĩa"], alpha_kd, K)
    return r


def main() -> None:
    t_bat_dau = time.perf_counter()
    config.ensure_dirs()
    print("=" * 70)
    print("BƯỚC 7: CÂU HỎI GÕ KHÔNG DẤU")
    print("=" * 70)

    ts = pipeline.doc_tham_so()
    _, text_tr = pipeline.load_split("train")
    gold_va, text_va = pipeline.load_split("val")
    gold_te, text_te = pipeline.load_split("test")
    kd_va = {q: diacritics.bo_dau(t) for q, t in text_va.items()}
    kd_te = {q: diacritics.bo_dau(t) for q, t in text_te.items()}

    # Câu hỏi gốc nào không có lấy một chữ mang dấu? Số này cho biết tập gốc
    # hoàn toàn là câu đủ dấu, nên phần không dấu bên dưới đều do máy tạo ra.
    nham = [q for q, t in {**text_va, **text_te}.items() if not diacritics.co_dau(t)]
    print(f"\nCâu hỏi gốc không có chữ nào mang dấu: {len(nham)} trên "
          f"{len(text_va) + len(text_te)}")

    arts = pd.read_parquet(config.ARTICLES_PATH)

    print("\n[1] Chỉ mục BM25 trên văn bản bỏ dấu")
    t0 = time.perf_counter()
    kd = arts[["article_id", "title", "text"]].copy()
    kd["tokens"] = [am_tiet_bo_dau(f"{a} {b}") for a, b in zip(kd["title"], kd["text"])]
    bm_kd = lexical.BM25Index(kd, **ts["bm25"])
    bm_kd.save(config.BM25_KHONG_DAU_DIR)
    print(f"    xong {time.perf_counter() - t0:.0f} s, dùng lại k1 và b đã chốt")

    print("\n[2] Mô hình phục hồi dấu: bigram âm tiết trên kho luật + câu hỏi train")
    t0 = time.perf_counter()
    nguon = [f"{a}. {b}" for a, b in zip(arts["title"], arts["text"])] + list(text_tr.values())
    ph = diacritics.PhucHoiDau(nguon)
    giay_hoc = round(time.perf_counter() - t0)
    print(f"    {ph.N:,} âm tiết, {ph.V:,} âm tiết khác nhau, {len(ph.bi):,} bigram, "
          f"{giay_hoc} s")

    hang_tune = []
    for lam in config.PHUC_HOI_LAMBDA_GRID:
        ph.lam = lam
        dung = tong = 0
        for q, t in text_va.items():
            d, n = diacritics.do_chinh_xac(t, ph.phuc_hoi(kd_va[q]))
            dung, tong = dung + d, tong + n
        hang_tune.append({"tham_so": "lambda", "gia_tri": lam,
                          "chi_so": "do_chinh_xac_am_tiet_val", "ket_qua": round(dung / tong, 4)})
        print(f"    lambda {lam:<5} độ chính xác âm tiết trên val {dung / tong:.4f}")
    lam_tot = max((h for h in hang_tune), key=lambda h: h["ket_qua"])["gia_tri"]
    ph.lam = lam_tot
    ph.save(config.PHUC_HOI_DAU_PATH)
    print(f"    chốt lambda = {lam_tot}")

    print("\n[3] Nạp BM25 và tầng ngữ nghĩa sạch")
    bm = lexical.BM25Index(arts, **ts["bm25"])
    de = dense.DenseIndex.load(config.INDEX_DIR / ts["dense"]["mo_hinh"])

    print("\n[4] Quét alpha trên val KHÔNG DẤU cho hợp nhất BM25 bỏ dấu + ngữ nghĩa")
    r_va = chay_he(kd_va, bm, bm_kd, de, ts, None)
    for a in config.ALPHA_GRID:
        hop = pipeline.hop_nhat_alpha(r_va["BM25 bỏ dấu"], r_va["Ngữ nghĩa"], a, config.TOPK_FUSION)
        hang_tune.append({"tham_so": "alpha_khong_dau", "gia_tri": a,
                          "chi_so": "recall@10_val", "ket_qua": round(pipeline.recall_at(hop, gold_va, 10), 4)})
    alpha_kd = max((h for h in hang_tune if h["tham_so"] == "alpha_khong_dau"),
                   key=lambda h: (h["ket_qua"], -abs(h["gia_tri"] - 0.5)))["gia_tri"]
    print(f"    chốt alpha = {alpha_kd}")
    pd.DataFrame(hang_tune).to_csv(config.EVAL_DIR / "khong_dau_tuning.csv", **config.CSV_KW)

    # Chỉ mục bỏ dấu đổi hai thứ cùng lúc: bỏ dấu, và tách theo âm tiết thay vì
    # tách từ bằng pyvi. Đo thêm một chỉ mục âm tiết còn dấu để tách hai phần ra.
    print("\n[5] Cách tách từ đóng góp bao nhiêu trong mức giảm, đo trên val")
    am = arts[["article_id", "title", "text"]].copy()
    am["tokens"] = [diacritics.am_tiet(f"{a} {b}") for a, b in zip(am["title"], am["text"])]
    bm_am = lexical.BM25Index(am, **ts["bm25"])
    hang_tach = []
    for ten, chi_muc, cau, tach in (
        ("pyvi tách từ, còn dấu", bm, text_va, textnorm.tokens),
        ("âm tiết, còn dấu", bm_am, text_va, diacritics.am_tiet),
        ("âm tiết, bỏ dấu", bm_kd, kd_va, am_tiet_bo_dau),
    ):
        run = {q: chi_muc.search_tokens(tach(t), config.TOPK_FUSION) for q, t in cau.items()}
        hang_tach.append({"cach_tach_tu": ten,
                          "cau_hoi": "có dấu" if cau is text_va else "không dấu",
                          "recall@10_val": round(pipeline.recall_at(run, gold_va, 10), 4)})
        print(f"    {ten:<22} recall@10 val {hang_tach[-1]['recall@10_val']:.4f}")
    pd.DataFrame(hang_tach).to_csv(config.EVAL_DIR / "khong_dau_tach_tu.csv", **config.CSV_KW)
    del bm_am, am

    print("\n[6] Chấm test, một lần")
    t0 = time.perf_counter()
    ph_te = {q: ph.phuc_hoi(t) for q, t in kd_te.items()}
    tre_ph = (time.perf_counter() - t0) * 1000 / len(kd_te)

    # Người gõ dấu một nửa: âm tiết đã có dấu được giữ nguyên, phần thiếu mới sửa
    rng = random.Random(config.SEED)
    nua_te = {q: bo_dau_mot_nua(t, rng) for q, t in text_te.items()}
    ph_nua = {q: ph.phuc_hoi(t) for q, t in nua_te.items()}
    # Phục hồi dấu cho cả câu vốn đã đủ dấu: giá phải trả khi bỏ cổng định tuyến
    ph_co = {q: ph.phuc_hoi(t) for q, t in text_te.items()}

    def do_dung(ban: dict) -> tuple[float, int]:
        dung = tong = cau = 0
        for q in text_te:
            d, n = diacritics.do_chinh_xac(text_te[q], ban[q])
            dung, tong, cau = dung + d, tong + n, cau + (d == n)
        return dung / tong, cau

    tl_kd, cau_dung = do_dung(ph_te)
    tl_nua_goc, _ = do_dung(nua_te)
    tl_nua, cau_nua = do_dung(ph_nua)
    tl_co, cau_co = do_dung(ph_co)
    print(f"    câu không dấu:    {tl_kd:.4f} âm tiết đúng, {cau_dung} trên "
          f"{len(text_te)} câu đúng hoàn toàn, {tre_ph:.1f} ms mỗi câu")
    print(f"    câu nửa dấu:      {tl_nua_goc:.4f} trước khi phục hồi, "
          f"{tl_nua:.4f} sau, {cau_nua} câu đúng hoàn toàn")
    print(f"    câu vốn đủ dấu:   {tl_co:.4f} sau khi vẫn cho phục hồi, "
          f"{cau_co} câu giữ nguyên hoàn toàn")

    r_co = chay_he(text_te, bm, bm_kd, de, ts, None)
    r_kd = chay_he(kd_te, bm, bm_kd, de, ts, alpha_kd)
    r_ph = chay_he(ph_te, bm, bm_kd, de, ts, None)
    r_nua = chay_he(nua_te, bm, bm_kd, de, ts, None)
    r_nua_ph = chay_he(ph_nua, bm, bm_kd, de, ts, None)
    r_co_ph = chay_he(ph_co, bm, bm_kd, de, ts, None)

    hang = []
    def ghi(dieu_kien, cach, ten, runs):
        hang.append({"dieu_kien": dieu_kien, "cach_xu_ly": cach, "he_thong": ten,
                     **chi_so(runs, gold_te)})

    for ten in ("BM25", "Ngữ nghĩa", "Hợp nhất"):
        ghi("có dấu", "giữ nguyên", ten, r_co[ten])
    for ten in ("BM25", "Ngữ nghĩa", "Hợp nhất"):
        ghi("không dấu", "giữ nguyên", ten, r_kd[ten])
    ghi("không dấu", "chỉ mục bỏ dấu", "BM25 bỏ dấu", r_kd["BM25 bỏ dấu"])
    ghi("không dấu", "chỉ mục bỏ dấu", "Hợp nhất BM25 bỏ dấu", r_kd["Hợp nhất BM25 bỏ dấu"])
    for ten in ("BM25", "Ngữ nghĩa", "Hợp nhất"):
        ghi("không dấu", "phục hồi dấu", ten, r_ph[ten])
    for ten in ("BM25", "Ngữ nghĩa", "Hợp nhất"):
        ghi("nửa dấu", "giữ nguyên", ten, r_nua[ten])
    for ten in ("BM25", "Ngữ nghĩa", "Hợp nhất"):
        ghi("nửa dấu", "phục hồi dấu", ten, r_nua_ph[ten])
    ghi("có dấu", "phục hồi dấu", "Hợp nhất", r_co_ph["Hợp nhất"])
    bang = pd.DataFrame(hang)
    bang.to_csv(config.EVAL_DIR / "khong_dau.csv", **config.CSV_KW)
    print()
    print(bang.to_string(index=False))

    # dung_top10 ở đây là "có ít nhất một gold trong top-10", cùng quy ước với
    # dung@10 của script 06, khác recall@10 ở bảng trên với 5 câu có hai gold.
    xep_goc = pipeline.chi_diem(r_co["Hợp nhất"])
    xep_ph = pipeline.chi_diem(r_ph["Hợp nhất"])
    vi_du = []
    for q in text_te:
        d, n = diacritics.do_chinh_xac(text_te[q], ph_te[q])
        vi_du.append({
            "query_id": q, "goc": text_te[q], "khong_dau": kd_te[q], "phuc_hoi": ph_te[q],
            "am_tiet_dung": d, "am_tiet": n,
            "goc_dung_top10": int(bool(set(xep_goc[q][:10]) & gold_te[q])),
            "phuc_hoi_dung_top10": int(bool(set(xep_ph[q][:10]) & gold_te[q])),
        })
    vd = pd.DataFrame(vi_du)
    vd.to_csv(config.EVAL_DIR / "khong_dau_vi_du.csv", **config.CSV_KW)

    # Phục hồi sai một âm tiết có làm hỏng truy hồi không? Đo trên top-10.
    dung_het = vd["am_tiet_dung"] == vd["am_tiet"]
    loi = []
    for nhom, m in (("phục hồi đúng hoàn toàn", dung_het), ("sai ít nhất một âm tiết", ~dung_het)):
        loi.append({"nhom": nhom, "so_cau": int(m.sum()),
                    "ty_le_dung_top10_cau_goc_pct": round(100 * vd.loc[m, "goc_dung_top10"].mean(), 2),
                    "ty_le_dung_top10_phuc_hoi_pct": round(100 * vd.loc[m, "phuc_hoi_dung_top10"].mean(), 2)})
    loi.append({"nhom": "mất do phục hồi sai", "so_cau": int(((vd.goc_dung_top10 == 1) & (vd.phuc_hoi_dung_top10 == 0)).sum())})
    loi.append({"nhom": "được nhờ phục hồi", "so_cau": int(((vd.goc_dung_top10 == 0) & (vd.phuc_hoi_dung_top10 == 1)).sum())})
    pd.DataFrame(loi).to_csv(config.EVAL_DIR / "khong_dau_loi.csv", **config.CSV_KW)
    print()
    print(pd.DataFrame(loi).to_string(index=False))

    (config.EVAL_DIR / "khong_dau_params.json").write_text(json.dumps({
        "do_tren": "val",
        "lambda_phuc_hoi": lam_tot,
        "alpha_bm25_bo_dau": alpha_kd,
        "alpha_duong_chinh": ts["weighted"]["alpha"],
        "nguon_mo_hinh_ngon_ngu": "kho điều luật + câu hỏi train",
        "so_am_tiet": ph.N, "so_bigram": len(ph.bi), "giay_hoc_mo_hinh": giay_hoc,
        "do_chinh_xac_am_tiet_test": round(tl_kd, 4),
        "so_cau_phuc_hoi_dung_hoan_toan_test": cau_dung,
        "do_chinh_xac_am_tiet_nua_dau_truoc": round(tl_nua_goc, 4),
        "do_chinh_xac_am_tiet_nua_dau_sau": round(tl_nua, 4),
        "do_chinh_xac_am_tiet_cau_du_dau": round(tl_co, 4),
        "so_cau_du_dau_giu_nguyen_hoan_toan": cau_co,
        "so_cau_test": len(text_te),
        "do_tre_phuc_hoi_ms": round(tre_ph, 2),
        "cau_goc_khong_co_chu_nao_mang_dau": len(nham),
    }, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"\nXong trong {(time.perf_counter() - t_bat_dau) / 60:.1f} phút.")


if __name__ == "__main__":
    main()
