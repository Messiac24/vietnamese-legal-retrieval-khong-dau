"""Bước 1: tải, kiểm toán, chia lại tập.

Chạy:
    C:/Python314/python.exe scripts/01_prepare_data.py

Sinh ra:
    data/articles.parquet   điều luật kèm token đã tách và nhóm trùng
    data/queries.parquet    câu hỏi đã khử trùng dòng
    data/qrels.parquet      nhãn đúng kèm cột split (train / val / test)
    reports/audit/*.csv     sáu tệp bằng chứng kiểm toán

Nguyên tắc: mỗi phép dọn dữ liệu đều để lại bằng chứng kiểm tra được. Không âm
thầm sửa dữ liệu rồi báo cáo con số đẹp.
"""
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import pandas as pd

from vlr import audit, config, corpus, splitting, textnorm


def _ghi(df: pd.DataFrame, ten: str) -> None:
    duong_dan = config.AUDIT_DIR / ten
    df.to_csv(duong_dan, **config.CSV_KW)
    print(f"    -> {duong_dan.relative_to(config.ROOT)}  ({len(df)} dòng)")


def main() -> None:
    t0 = time.perf_counter()
    config.ensure_dirs()

    print("=" * 70)
    print("BƯỚC 1: CHUẨN BỊ VÀ KIỂM TOÁN DỮ LIỆU")
    print("=" * 70)

    corpus.download()
    arts = corpus.load_articles()
    qs_raw = corpus.load_queries()
    qr_tr = corpus.load_qrels("train")
    qr_te = corpus.load_qrels("test")
    print(f"\nĐã nạp: {len(arts)} điều luật, {len(qs_raw)} dòng câu hỏi, "
          f"{len(qr_tr)} qrel train, {len(qr_te)} qrel test")

    # ---------- 1. Thống kê corpus ----------
    print("\n[1/6] Thống kê kho điều luật")
    so_tu = arts["text"].str.split().str.len().fillna(0).astype(int)
    stats = pd.DataFrame(
        [
            ("so_dieu_luat", len(arts)),
            ("so_van_ban", arts["doc_id"].nunique()),
            ("do_dai_trung_vi_tu", int(so_tu.median())),
            ("do_dai_trung_binh_tu", round(float(so_tu.mean()), 1)),
            ("do_dai_p90_tu", int(so_tu.quantile(0.9))),
            ("do_dai_lon_nhat_tu", int(so_tu.max())),
            ("ty_le_dai_hon_200_tu_pct", round(100 * float((so_tu > 200).mean()), 2)),
            ("ty_le_dai_hon_400_tu_pct", round(100 * float((so_tu > 400).mean()), 2)),
            ("so_cau_hoi_dong", len(qs_raw)),
            ("so_cau_hoi_id_duy_nhat", qs_raw["query_id"].nunique()),
        ],
        columns=["chi_tieu", "gia_tri"],
    )
    _ghi(stats, "corpus_stats.csv")

    # ---------- 2. Điều luật rỗng ----------
    print("\n[2/6] Điều luật có nội dung rỗng")
    rong = arts[arts["text"].str.strip() == ""][["article_id", "doc_id", "title"]]
    print(f"    {len(rong)} điều chỉ còn tiêu đề, không có thân điều "
          f"({100 * len(rong) / len(arts):.2f}%)")
    _ghi(rong, "empty_articles.csv")

    # ---------- 3. Tách từ toàn corpus ----------
    print("\n[3/6] Tách từ 61k điều luật bằng pyvi")
    cu = None
    if config.ARTICLES_PATH.exists():
        thu = pd.read_parquet(config.ARTICLES_PATH)
        if "tokens" in thu.columns and len(thu) == len(arts):
            cu = dict(zip(thu["article_id"], thu["tokens"]))
    if cu is not None and set(cu) == set(arts["article_id"]):
        arts["tokens"] = [list(cu[a]) for a in arts["article_id"]]
        print("    dùng lại token đã tách trong data/articles.parquet, bỏ qua pyvi")
    else:
        print("    chưa có bản đã tách, chạy pyvi (khoảng 3 tới 4 phút)")
        toks: list[list[str]] = []
        for i, (tieu_de, noi_dung) in enumerate(zip(arts["title"], arts["text"]), 1):
            toks.append(textnorm.tokens(f"{tieu_de} {noi_dung}"))
            if i % 5000 == 0:
                print(f"    {i}/{len(arts)}  ({time.perf_counter() - t0:.0f}s)",
                      flush=True)
        arts["tokens"] = toks

    # ---------- 4. Trùng lặp điều luật ----------
    print("\n[4/6] Trùng lặp điều luật")
    nhom = audit.exact_duplicate_groups(arts)
    arts["dup_group"] = arts["article_id"].map(nhom)
    co_nhieu = arts.groupby("dup_group")["article_id"].transform("size") > 1
    trung = (arts[co_nhieu][["dup_group", "article_id", "doc_id", "title"]]
             .sort_values(["dup_group", "article_id"]))
    so_nhom = trung["dup_group"].nunique()
    print(f"    trùng nguyên văn: {so_nhom} nhóm, {len(trung)} điều "
          f"({100 * len(trung) / len(arts):.2f}%)")
    if so_nhom:
        van_ban_moi_nhom = trung.groupby("dup_group")["doc_id"].nunique()
        print(f"    nhóm nằm gọn trong MỘT văn bản: {int((van_ban_moi_nhom == 1).sum())}"
              f"  |  vắt qua nhiều văn bản: {int((van_ban_moi_nhom > 1).sum())}")
    _ghi(trung, "duplicate_articles.csv")

    doc_trung = audit.duplicate_docs_by_diacritics(arts)
    print(f"    văn bản bị tách đôi vì khác dấu tiếng Việt: "
          f"{doc_trung['khoa_bo_dau'].nunique() if len(doc_trung) else 0} nhóm, "
          f"{len(doc_trung)} mã văn bản, {int(doc_trung['so_dieu'].sum()) if len(doc_trung) else 0} điều")
    _ghi(doc_trung, "duplicate_docs_diacritics.csv")

    ngram_df = pd.DataFrame({
        "article_id": arts["article_id"],
        "tokens": [sorted(textnorm.ngrams(t, config.SIMHASH_NGRAM))
                   for t in arts["tokens"]],
    })
    cap = audit.near_duplicate_pairs(ngram_df, threshold=config.NEAR_DUP_HAMMING)
    tieu_de = dict(zip(arts["article_id"], arts["title"]))
    gan_trung = pd.DataFrame(
        [(a, b, d, tieu_de[a], tieu_de[b]) for a, b, d in cap],
        columns=["article_a", "article_b", "hamming", "title_a", "title_b"],
    )
    print(f"    gần trùng (Hamming <= {config.NEAR_DUP_HAMMING}): {len(gan_trung)} cặp"
          f"  |  băng bỏ qua vì quá lớn: {audit.near_duplicate_pairs.bo_qua}")
    _ghi(gan_trung, "near_duplicate_articles.csv")

    # ---------- 5. Kiểm toán câu hỏi ----------
    print("\n[5/6] Kiểm toán câu hỏi")
    lap = audit.duplicate_queries(qs_raw)
    xung_dot = int((lap["so_noi_dung_khac_nhau"] > 1).sum()) if len(lap) else 0
    print(f"    query_id lặp dòng: {len(lap)} id"
          f"  |  id mang hai nội dung khác nhau: {xung_dot}")
    if xung_dot:
        raise SystemExit(
            "DỪNG: có query_id mang hai nội dung khác nhau. Không được tự đoán "
            "dòng nào đúng, phải xem lại nguồn dữ liệu."
        )
    _ghi(lap, "duplicate_queries.csv")
    qs = qs_raw.drop_duplicates("query_id").reset_index(drop=True)
    print(f"    sau khử trùng: {len(qs)} câu hỏi")

    chong_lan = audit.split_overlap(qr_tr, qr_te)
    print(f"    câu hỏi có CÙNG id ở cả train và test: {len(chong_lan)}")
    ids_tr = set(qr_tr["query_id"])
    ids_te = set(qr_te["query_id"])
    gan = audit.near_duplicate_queries(
        qs, ids_tr - ids_te, ids_te, config.QUESTION_NGRAM, config.QUESTION_JACCARD
    )
    print(f"    câu hỏi train GẦN TRÙNG câu hỏi test "
          f"(Jaccard >= {config.QUESTION_JACCARD}): {len(gan)}")
    if len(gan):
        gan = gan.assign(loai="gan_trung")
        chong_lan = pd.concat(
            [chong_lan, gan[["query_id", "loai", "query_id_doi_chieu", "jaccard"]]],
            ignore_index=True,
        )
    chong_lan["text"] = chong_lan["query_id"].map(dict(zip(qs["query_id"], qs["text"])))
    _ghi(chong_lan, "query_overlap.csv")

    # ---------- 6. Mở rộng gold và chia lại tập ----------
    print("\n[6/6] Mở rộng gold và chia lại tập")
    nhom_to_ids: dict[str, list[str]] = {}
    for aid, g in zip(arts["article_id"], arts["dup_group"]):
        nhom_to_ids.setdefault(g, []).append(aid)

    qr_all = pd.concat(
        [qr_tr.assign(split_goc="train"), qr_te.assign(split_goc="test")],
        ignore_index=True,
    )
    them = []
    for qid, aid in zip(qr_all["query_id"], qr_all["article_id"]):
        anh_em = [x for x in nhom_to_ids.get(nhom.get(aid, ""), []) if x != aid]
        if anh_em:
            them.append((qid, aid, len(anh_em), " ".join(sorted(anh_em))))
    mo_rong = pd.DataFrame(
        them, columns=["query_id", "gold_goc", "so_dieu_them", "danh_sach_them"]
    )
    print(f"    điều gold nằm trong nhóm trùng: {len(mo_rong)} / {len(qr_all)} cặp qrel")
    _ghi(mo_rong, "gold_expansion.csv")

    # Nhãn mâu thuẫn: cùng một câu hỏi nhưng train và test chỉ sang điều khác
    xung = []
    for qid in sorted(ids_tr & ids_te):
        g_tr = sorted(qr_tr[qr_tr["query_id"] == qid]["article_id"])
        g_te = sorted(qr_te[qr_te["query_id"] == qid]["article_id"])
        xung.append((qid, " ".join(g_tr), " ".join(g_te), g_tr == g_te))
    mau_thuan = pd.DataFrame(
        xung, columns=["query_id", "gold_train", "gold_test", "giong_nhau"]
    )
    mau_thuan["text"] = mau_thuan["query_id"].map(dict(zip(qs["query_id"], qs["text"])))
    so_khac = int((~mau_thuan["giong_nhau"]).sum()) if len(mau_thuan) else 0
    print(f"    trong đó gold train KHÁC gold test: {so_khac} / {len(mau_thuan)}")
    _ghi(mau_thuan, "conflicting_gold.csv")

    loai = set(chong_lan["query_id"])
    train_con_lai = sorted(ids_tr - loai)
    print(f"    loại khỏi train {len(ids_tr) - len(train_con_lai)} câu hỏi chồng lấn")
    tr_ids, va_ids = splitting.split_queries(
        train_con_lai, config.VAL_RATIO, config.SEED
    )

    assert not (tr_ids & va_ids), "train và val giao nhau"
    assert not (tr_ids & ids_te), "train và test giao nhau"
    assert not (va_ids & ids_te), "val và test giao nhau"

    # Tập test giữ NGUYÊN VẸN đúng 793 cặp của ban tổ chức. Các dòng qrel mà
    # tệp train gán cho 24 câu hỏi chồng lấn bị bỏ hẳn, không nhập vào test:
    # gộp vào là tự sửa nhãn của tập test bằng phỏng đoán của mình.
    phan_test = qr_te.assign(split="test")
    phan_train = qr_tr[qr_tr["query_id"].isin(tr_ids)].assign(split="train")
    phan_val = qr_tr[qr_tr["query_id"].isin(va_ids)].assign(split="val")
    qrels = pd.concat([phan_train, phan_val, phan_test], ignore_index=True)
    assert len(phan_test) == len(qr_te), "tập test đã bị thay đổi"

    phan_bo = (
        qrels.groupby("split")
        .agg(so_cau_hoi=("query_id", "nunique"), so_cap_qrel=("query_id", "size"))
        .reset_index()
    )
    phan_bo["gold_trung_binh"] = (
        phan_bo["so_cap_qrel"] / phan_bo["so_cau_hoi"]
    ).round(3)
    print(phan_bo.to_string(index=False))
    _ghi(phan_bo, "split_distribution.csv")

    # ---------- Ghi dữ liệu ----------
    arts.to_parquet(config.ARTICLES_PATH, index=False)
    qs.to_parquet(config.QUERIES_PATH, index=False)
    qrels.to_parquet(config.QRELS_PATH, index=False)
    print(f"\nĐã ghi {config.ARTICLES_PATH.relative_to(config.ROOT)}, "
          f"{config.QUERIES_PATH.relative_to(config.ROOT)}, "
          f"{config.QRELS_PATH.relative_to(config.ROOT)}")
    print(f"Tổng thời gian: {(time.perf_counter() - t0) / 60:.1f} phút")


if __name__ == "__main__":
    main()
