"""Kiểm toán dữ liệu: điều trùng nguyên văn (SHA1), gần trùng (SimHash), câu hỏi
chồng lấn giữa các tập (Jaccard n-gram).
"""
import hashlib
import unicodedata
from collections import defaultdict

import pandas as pd

from vlr import textnorm

_MASK64 = (1 << 64) - 1


def content_hash(text: str) -> str:
    """Băm nội dung đã chuẩn hóa. Bỏ qua khác biệt hoa thường và dấu câu."""
    return hashlib.sha1(textnorm.normalize(text).encode("utf-8")).hexdigest()


def _token_hash(token: str) -> int:
    return int.from_bytes(
        hashlib.blake2b(token.encode("utf-8"), digest_size=8).digest(), "big"
    )


def simhash64(tokens) -> int:
    """SimHash 64 bit trên danh sách token."""
    tokens = list(tokens)
    if not tokens:
        return 0
    dem = [0] * 64
    for t in tokens:
        h = _token_hash(t)
        for i in range(64):
            dem[i] += 1 if (h >> i) & 1 else -1
    ket = 0
    for i in range(64):
        if dem[i] > 0:
            ket |= 1 << i
    return ket


def hamming(a: int, b: int) -> int:
    return ((a ^ b) & _MASK64).bit_count()


def jaccard(a: set, b: set) -> float:
    """Trả 0 khi cả hai tập rỗng."""
    if not a and not b:
        return 0.0
    hop = len(a | b)
    return len(a & b) / hop if hop else 0.0


def exact_duplicate_groups(df: pd.DataFrame) -> dict[str, str]:
    """article_id -> group_id. Điều không trùng ai vẫn có nhóm riêng một phần tử."""
    return {
        aid: content_hash(f"{tieu_de} {noi_dung}")
        for aid, tieu_de, noi_dung in zip(df["article_id"], df["title"], df["text"])
    }


def near_duplicate_pairs(
    df: pd.DataFrame, threshold: int, bands: int = 8, max_bucket: int = 2000
) -> list[tuple[str, str, int]]:
    """Cặp điều gần trùng. Chia mã SimHash thành băng (LSH) để khỏi so 1,9 tỷ cặp.

    Băng nào gom quá `max_bucket` điều thì bỏ qua, số băng bỏ qua ghi vào
    `near_duplicate_pairs.bo_qua`.
    """
    ma = {
        aid: simhash64(toks) for aid, toks in zip(df["article_id"], df["tokens"])
    }
    rong = 64 // bands
    thung: dict[tuple[int, int], list[str]] = defaultdict(list)
    for aid, h in ma.items():
        for i in range(bands):
            thung[(i, (h >> (i * rong)) & ((1 << rong) - 1))].append(aid)

    da_xet: set[tuple[str, str]] = set()
    ket: list[tuple[str, str, int]] = []
    bo_qua = 0
    for nhom in thung.values():
        if len(nhom) < 2:
            continue
        if len(nhom) > max_bucket:
            bo_qua += 1
            continue
        for i in range(len(nhom)):
            for j in range(i + 1, len(nhom)):
                cap = (nhom[i], nhom[j]) if nhom[i] < nhom[j] else (nhom[j], nhom[i])
                if cap in da_xet:
                    continue
                da_xet.add(cap)
                d = hamming(ma[cap[0]], ma[cap[1]])
                if d <= threshold:
                    ket.append((cap[0], cap[1], d))
    near_duplicate_pairs.bo_qua = bo_qua
    return sorted(ket, key=lambda x: x[2])


def split_overlap(qrels_train: pd.DataFrame, qrels_test: pd.DataFrame) -> pd.DataFrame:
    """Các câu hỏi có mặt ở cả train và test."""
    giao = sorted(set(qrels_train["query_id"]) & set(qrels_test["query_id"]))
    return pd.DataFrame({"query_id": giao, "loai": ["trung_id"] * len(giao)})


def duplicate_queries(queries: pd.DataFrame) -> pd.DataFrame:
    """query_id lặp dòng. `so_noi_dung_khac_nhau` > 1 là cùng id nhưng khác câu hỏi."""
    dem = queries.groupby("query_id").agg(
        so_dong=("text", "size"), so_noi_dung_khac_nhau=("text", "nunique")
    )
    lap = dem[dem["so_dong"] > 1].reset_index()
    dau = queries.drop_duplicates("query_id").set_index("query_id")["text"]
    lap["text"] = lap["query_id"].map(dau)
    return lap.sort_values("query_id").reset_index(drop=True)


def near_duplicate_queries(
    queries: pd.DataFrame, ids_a: set, ids_b: set, n: int, nguong: float
) -> pd.DataFrame:
    """Câu ở nhóm A gần trùng câu ở nhóm B theo Jaccard n-gram, lọc trước bằng chỉ mục ngược."""
    grams = {
        qid: textnorm.ngrams(textnorm.tokens(txt), n)
        for qid, txt in zip(queries["query_id"], queries["text"])
        if qid in ids_a or qid in ids_b
    }
    nghich_dao: dict[str, list[str]] = defaultdict(list)
    for qid in ids_b:
        for g in grams.get(qid, ()):
            nghich_dao[g].append(qid)

    ket = []
    for qid in sorted(ids_a):
        ung_vien = {q for g in grams.get(qid, ()) for q in nghich_dao.get(g, ())}
        for khac in ung_vien:
            j = jaccard(grams[qid], grams[khac])
            if j >= nguong:
                ket.append((qid, khac, round(j, 4)))
    return pd.DataFrame(ket, columns=["query_id", "query_id_doi_chieu", "jaccard"])


def _bo_dau(s: str) -> str:
    s = unicodedata.normalize("NFD", s)
    s = "".join(c for c in s if unicodedata.category(c) != "Mn")
    return s.replace("đ", "d").replace("Đ", "D")


def duplicate_docs_by_diacritics(df: pd.DataFrame) -> pd.DataFrame:
    """Văn bản bị tách đôi chỉ vì khác dấu trong số hiệu, như 155/2020/nd-cp và nđ-cp."""
    nhom: dict[str, list[str]] = defaultdict(list)
    for d in sorted(df["doc_id"].unique()):
        nhom[_bo_dau(d)].append(d)
    dem = df.groupby("doc_id").size().to_dict()
    hang = []
    for khoa, ds in nhom.items():
        if len(ds) < 2:
            continue
        for d in ds:
            hang.append({"khoa_bo_dau": khoa, "doc_id": d, "so_dieu": dem.get(d, 0)})
    return pd.DataFrame(hang, columns=["khoa_bo_dau", "doc_id", "so_dieu"])
