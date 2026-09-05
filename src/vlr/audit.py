"""Kiểm toán dữ liệu: trùng lặp, gần trùng, chồng lấn giữa các tập.

Nguyên tắc của đồ án: không tin split do người khác chia. Mỗi hàm ở đây sinh ra
bằng chứng kiểm tra được, chứ không âm thầm dọn dữ liệu.

Ba mức trùng lặp cần ba công cụ khác nhau:

    Mức                      Ví dụ                              Công cụ
    trùng từng ký tự         copy nguyên điều sang văn bản khác  SHA1
    gần trùng                sửa vài chữ, đổi số hiệu            SimHash + Hamming
    trùng ở mức câu hỏi      hai câu hỏi diễn đạt khác nhau      Jaccard n-gram
"""
import hashlib
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
    """SimHash 64 bit.

    Mỗi token góp +1 cho những bit nó bật và -1 cho những bit nó tắt. Bit kết
    quả bật khi tổng dương. Hai văn bản chia sẻ phần lớn token sẽ cho hai mã
    lệch nhau ít bit, kể cả khi khác nhau vài chỗ.
    """
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
    """Số bit khác nhau giữa hai mã 64 bit."""
    return ((a ^ b) & _MASK64).bit_count()


def jaccard(a: set, b: set) -> float:
    """Độ trùng lặp hai tập. Trả 0 khi cả hai rỗng, không chia cho không."""
    if not a and not b:
        return 0.0
    hop = len(a | b)
    return len(a & b) / hop if hop else 0.0


def exact_duplicate_groups(df: pd.DataFrame) -> dict[str, str]:
    """Gom điều luật trùng nguyên văn thành nhóm.

    Trả về ánh xạ article_id -> group_id. Điều không trùng ai vẫn có nhóm
    riêng gồm đúng một phần tử, để phía dùng không phải xử lý trường hợp thiếu.
    """
    return {
        aid: content_hash(f"{tieu_de} {noi_dung}")
        for aid, tieu_de, noi_dung in zip(df["article_id"], df["title"], df["text"])
    }


def near_duplicate_pairs(
    df: pd.DataFrame, threshold: int, bands: int = 8, max_bucket: int = 2000
) -> list[tuple[str, str, int]]:
    """Tìm các cặp điều luật gần trùng bằng SimHash chia băng.

    So mọi cặp trong 61.425 điều là 1,9 tỷ phép so, không chạy nổi. Cách làm:
    chia mã 64 bit thành `bands` băng bằng nhau, hai điều chỉ được đem ra so
    khi rơi cùng một băng. Đây là kỹ thuật LSH: đánh đổi một ít độ phủ để lấy
    tốc độ.

    `df` cần hai cột: `article_id` và `tokens` (danh sách token đã tách từ).
    Trả về danh sách (article_a, article_b, khoảng_cách_hamming).

    `max_bucket` là chốt chặn: một băng gom quá nhiều điều thì số cặp phải so
    tăng theo bình phương và bước kiểm toán treo. Băng vượt ngưỡng bị bỏ qua và
    được đếm lại trong `near_duplicate_pairs.bo_qua`, để báo cáo chứ không im
    lặng. Cùng một cặp thường rơi vào nhiều băng nên bỏ một băng hiếm khi mất
    cặp thật.
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
    """Các câu hỏi xuất hiện ở cả train và test.

    Đây là rò rỉ nặng nhất và cũng dễ bỏ sót nhất: chỉ cần một phép giao tập là
    thấy, nhưng nếu tin split có sẵn thì không ai nhìn.
    """
    giao = sorted(set(qrels_train["query_id"]) & set(qrels_test["query_id"]))
    return pd.DataFrame({"query_id": giao, "loai": ["trung_id"] * len(giao)})


def duplicate_queries(queries: pd.DataFrame) -> pd.DataFrame:
    """Các query_id xuất hiện nhiều hơn một dòng trong queries.jsonl.

    Cột `so_noi_dung_khac_nhau` là chỗ đáng lo: bằng 1 nghĩa là các dòng lặp
    giống hệt nhau, khử trùng an toàn. Lớn hơn 1 nghĩa là cùng một id mang hai
    câu hỏi khác nhau, lúc đó không được tự đoán dòng nào đúng.
    """
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
    """Câu hỏi ở nhóm A gần trùng câu hỏi ở nhóm B, đo bằng Jaccard n-gram.

    Dùng chỉ mục ngược trên n-gram để không phải so mọi cặp: hai câu không có
    n-gram nào chung thì Jaccard chắc chắn bằng 0, khỏi cần tính.
    """
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
