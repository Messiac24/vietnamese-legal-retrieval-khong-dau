"""Bước 4: quét tham số trên val.

    C:/Python314/python.exe scripts/04_tune.py

Sinh ra:
    reports/eval/tuning_bm25.csv      lưới k1 x b
    reports/eval/tuning_pooling.csv   cách gộp đoạn cho từng mô hình
    reports/eval/tuning_rrf.csv       hằng số k của RRF
    reports/eval/tuning_alpha.csv     trọng số alpha
    reports/eval/chosen_params.json   cấu hình chốt lại

Chỉ đọc split == "val", có assert chặn test.
"""
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import pandas as pd

from vlr import config, dense, lexical, metrics, pipeline, textnorm

K = config.TUNE_METRIC_K


def _ghi(df: pd.DataFrame, ten: str) -> pd.DataFrame:
    duong_dan = config.EVAL_DIR / ten
    df.to_csv(duong_dan, **config.CSV_KW)
    print(f"    -> {duong_dan.relative_to(config.ROOT)}")
    return df


def quet_bm25(arts, gold, text) -> tuple[dict, pd.DataFrame]:
    print(f"\n[1/4] Quét BM25 trên lưới {len(config.BM25_K1_GRID)} x "
          f"{len(config.BM25_B_GRID)} = "
          f"{len(config.BM25_K1_GRID) * len(config.BM25_B_GRID)} cấu hình")
    toks = {q: textnorm.tokens(t) for q, t in text.items()}
    hang = []
    for k1 in config.BM25_K1_GRID:
        for b in config.BM25_B_GRID:
            idx = lexical.BM25Index(arts, k1=k1, b=b)
            runs = {q: idx.search_tokens(tk, K) for q, tk in toks.items()}
            r = sum(metrics.recall_at_k([a for a, _ in runs[q]], gold[q], K)
                    for q in runs) / len(runs)
            hang.append({"k1": k1, "b": b, f"recall@{K}": round(r, 4)})
            print(f"    k1={k1:<4} b={b:<5} recall@{K}={r:.4f}", flush=True)
    df = _ghi(pd.DataFrame(hang).sort_values(f"recall@{K}", ascending=False),
              "tuning_bm25.csv")
    tot = df.iloc[0]
    print(f"    chọn k1={tot['k1']}, b={tot['b']}")
    return {"k1": float(tot["k1"]), "b": float(tot["b"])}, df


def quet_pooling(gold, text) -> tuple[dict, pd.DataFrame, dict]:
    print("\n[2/4] Quét cách gộp đoạn cho từng mô hình")
    hang = []
    runs_theo_mo_hinh = {}
    for ten in ("bkai", "aiteam", "bkai_ft"):
        thu_muc = config.INDEX_DIR / ten
        if not (thu_muc / "meta.json").exists():
            print(f"    bỏ qua {ten}: chưa có chỉ mục")
            continue
        idx = dense.DenseIndex.load(thu_muc)
        ids = list(text)
        vecs = idx.encode_queries([text[q] for q in ids])
        for pooling in config.POOLING_GRID:
            t0 = time.perf_counter()
            kq = idx.search(vecs, top_k=config.TOPK_FUSION, pooling=pooling,
                            chunk_top=config.CHUNK_TOP)
            runs = dict(zip(ids, kq))
            r = sum(metrics.recall_at_k([a for a, _ in runs[q]], gold[q], K)
                    for q in runs) / len(runs)
            hang.append({"mo_hinh": ten, "gop_doan": pooling,
                         f"recall@{K}": round(r, 4),
                         "giay": round(time.perf_counter() - t0, 1)})
            runs_theo_mo_hinh[(ten, pooling)] = runs
            print(f"    {ten:<8} {pooling:<5} recall@{K}={r:.4f}", flush=True)
        del idx
    if not hang:
        raise SystemExit(
            "Chưa có chỉ mục vector nào. Chạy trước:\n"
            "    C:/Python314/python.exe scripts/02_build_index.py --model all"
        )
    df = pd.DataFrame(hang)
    df["nhiem_ban"] = df["mo_hinh"].map(lambda m: config.NHIEM_BAN.get(m, ""))
    df = _ghi(df.sort_values(f"recall@{K}", ascending=False), "tuning_pooling.csv")

    # cấu hình chính thức chỉ chọn trong mô hình sạch, bkai đã học tập train Zalo
    sach = df[df["mo_hinh"].isin(config.MO_HINH_SACH)]
    if sach.empty:
        raise SystemExit(
            "Không có mô hình sạch nào. Chạy trước:\n"
            "    C:/Python314/python.exe scripts/02_build_index.py --model aiteam"
        )
    tot = sach.iloc[0]
    ban = df.iloc[0]
    print(f"    chọn cho cấu hình CHÍNH THỨC: {tot['mo_hinh']} + gộp "
          f"{tot['gop_doan']} (recall@{K}={tot[f'recall@{K}']:.4f})")
    if ban["mo_hinh"] != tot["mo_hinh"]:
        print(f"    điểm cao nhất là {ban['mo_hinh']} {ban[f'recall@{K}']:.4f}, "
              f"nhưng nhiễm bẩn: {config.NHIEM_BAN[ban['mo_hinh']]}")
    return ({"mo_hinh": tot["mo_hinh"], "gop_doan": tot["gop_doan"]},
            {"mo_hinh": ban["mo_hinh"], "gop_doan": ban["gop_doan"]},
            df, runs_theo_mo_hinh)


def quet_hop_nhat(bm_runs, de_runs, gold, hau_to: str = "") -> tuple[dict, dict]:
    nhan = f"  [cặp {hau_to.strip('_')}]" if hau_to else ""
    print(f"\n[3/4] Quét hằng số k của RRF{nhan}")
    hang = []
    for k in config.RRF_K_GRID:
        runs = pipeline.hop_nhat_rrf(bm_runs, de_runs, k, config.TOPK_FUSION)
        r = pipeline.recall_at(runs, gold, K)
        hang.append({"rrf_k": k, f"recall@{K}": round(r, 4)})
        print(f"    k={k:<4} recall@{K}={r:.4f}")
    df_rrf = _ghi(pd.DataFrame(hang).sort_values(f"recall@{K}", ascending=False),
                  f"tuning_rrf{hau_to}.csv")

    print(f"\n[4/4] Quét trọng số alpha{nhan}")
    hang = []
    for a in config.ALPHA_GRID:
        runs = pipeline.hop_nhat_alpha(bm_runs, de_runs, a, config.TOPK_FUSION)
        r = pipeline.recall_at(runs, gold, K)
        hang.append({"alpha": a, f"recall@{K}": round(r, 4)})
    df_a = pd.DataFrame(hang)
    for _, h in df_a.iterrows():
        print(f"    alpha={h['alpha']:<5} recall@{K}={h[f'recall@{K}']:.4f}")
    _ghi(df_a, f"tuning_alpha{hau_to}.csv")

    tot_rrf = df_rrf.iloc[0]
    tot_a = df_a.sort_values(f"recall@{K}", ascending=False).iloc[0]
    print(f"\n    RRF tốt nhất  : k={int(tot_rrf['rrf_k'])} "
          f"-> {tot_rrf[f'recall@{K}']:.4f}")
    print(f"    Alpha tốt nhất: alpha={tot_a['alpha']} "
          f"-> {tot_a[f'recall@{K}']:.4f}")
    if tot_a["alpha"] in (0.0, 1.0):
        print("    CẢNH BÁO: đỉnh nằm ở biên, tức là hợp nhất không có tác dụng. "
              "Phải báo cáo đúng như vậy.")
    return ({"rrf_k": int(tot_rrf["rrf_k"]), f"recall@{K}": float(tot_rrf[f"recall@{K}"])},
            {"alpha": float(tot_a["alpha"]), f"recall@{K}": float(tot_a[f"recall@{K}"])})


def main() -> None:
    t0 = time.perf_counter()
    config.ensure_dirs()
    print("=" * 70)
    print("BƯỚC 4: QUÉT THAM SỐ TRÊN TẬP VAL")
    print("=" * 70)

    gold, text = pipeline.load_split("val")
    gold_test, _ = pipeline.load_split("test")
    assert not (set(gold) & set(gold_test)), "val và test giao nhau"
    print(f"val: {len(gold)} câu hỏi (test có {len(gold_test)} câu, KHÔNG đụng tới)")

    arts = pd.read_parquet(config.ARTICLES_PATH)
    tham_so_bm25, _ = quet_bm25(arts, gold, text)

    idx_bm = lexical.BM25Index(arts, **tham_so_bm25)
    toks = {q: textnorm.tokens(t) for q, t in text.items()}
    bm_runs = {q: idx_bm.search_tokens(tk, config.TOPK_FUSION)
               for q, tk in toks.items()}

    dense_sach, dense_ban, _, runs_theo = quet_pooling(gold, text)
    de_runs = runs_theo[(dense_sach["mo_hinh"], dense_sach["gop_doan"])]
    rrf, alpha = quet_hop_nhat(bm_runs, de_runs, gold)

    chon = {
        "do_tren": "val",
        "so_cau_hoi_val": len(gold),
        "chi_so_chon": f"recall@{K}",
        "bm25": tham_so_bm25,
        "dense": dense_sach,
        "rrf": rrf,
        "weighted": alpha,
        "top_k_hop_nhat": config.TOPK_FUSION,
        "ghi_chu_nhiem_ban": config.NHIEM_BAN,
    }
    if dense_ban["mo_hinh"] != dense_sach["mo_hinh"]:
        de_ban = runs_theo[(dense_ban["mo_hinh"], dense_ban["gop_doan"])]
        rrf_b, alpha_b = quet_hop_nhat(bm_runs, de_ban, gold, hau_to="_nhiem_ban")
        chon["dense_nhiem_ban"] = dense_ban
        chon["rrf_nhiem_ban"] = rrf_b
        chon["weighted_nhiem_ban"] = alpha_b
    print("\nCấu hình chốt lại:")
    pipeline.luu_tham_so(chon)
    print(f"Tổng thời gian: {(time.perf_counter() - t0) / 60:.1f} phút")


if __name__ == "__main__":
    main()
