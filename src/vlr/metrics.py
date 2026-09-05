"""Chỉ số đánh giá truy hồi.

Mọi hàm nhận `ranked` là danh sách article_id đã xếp hạng giảm dần, và `gold` là
tập article_id đúng. Không hàm nào tự đoán gold; phía gọi quyết định dùng gold
gốc hay gold mở rộng.
"""
import math

import pandas as pd


def _trung(ranked, gold, k: int) -> list[int]:
    """Vị trí (bắt đầu từ 0) của các mục trúng trong top-k."""
    return [i for i, d in enumerate(ranked[:k]) if d in gold]


def recall_at_k(ranked, gold, k: int) -> float:
    """Tỷ lệ điều luật gold lọt vào top-k.

    Đây là chỉ số quan trọng nhất với bài toán này: gần như mỗi câu hỏi chỉ có
    một điều gold, nên Recall@k trả lời đúng câu người dùng quan tâm là "nhìn k
    kết quả đầu có thấy điều mình cần không".
    """
    if not gold:
        return 0.0
    return len(_trung(ranked, gold, k)) / len(gold)


def mrr_at_k(ranked, gold, k: int) -> float:
    """Nghịch đảo thứ hạng của mục trúng ĐẦU TIÊN.

    Phạt việc đẩy đáp án đúng xuống dưới: hạng 1 được 1,0 còn hạng 5 chỉ 0,2.
    Recall@10 không phân biệt được hai trường hợp đó.
    """
    if not gold:
        return 0.0
    vi_tri = _trung(ranked, gold, k)
    return 1.0 / (vi_tri[0] + 1) if vi_tri else 0.0


def ndcg_at_k(ranked, gold, k: int) -> float:
    """nDCG với nhãn nhị phân. Chuẩn của ngành truy hồi, so được với công bố ngoài."""
    if not gold:
        return 0.0
    dcg = sum(1.0 / math.log2(i + 2) for i in _trung(ranked, gold, k))
    idcg = sum(1.0 / math.log2(i + 2) for i in range(min(len(gold), k)))
    return dcg / idcg if idcg else 0.0


def f2_at_k(ranked, gold, k: int) -> float:
    """F2 theo đúng định nghĩa của Zalo AI Challenge 2021: 5PR / (4P + R).

    F2 nặng recall gấp bốn lần precision. Hợp với tra cứu luật: bỏ sót điều
    đúng tệ hơn nhiều so với trả kèm vài điều thừa mà người dùng tự loại được.
    """
    if not gold or k <= 0:
        return 0.0
    so_trung = len(_trung(ranked, gold, k))
    if so_trung == 0:
        return 0.0
    p = so_trung / k
    r = so_trung / len(gold)
    mau = 4 * p + r
    return 5 * p * r / mau if mau else 0.0


def evaluate(runs: dict, gold_map: dict, ks=(1, 5, 10, 20)) -> pd.DataFrame:
    """Gộp mọi chỉ số, lấy trung bình trên các câu hỏi.

    `runs`: query_id -> danh sách article_id đã xếp hạng.
    `gold_map`: query_id -> tập article_id đúng.
    Trả về bảng hai cột `chi_so`, `gia_tri`.
    """
    thieu = [q for q in runs if q not in gold_map]
    if thieu:
        raise ValueError(
            f"{len(thieu)} câu hỏi không có gold, ví dụ {thieu[:3]}. "
            "Không được lặng lẽ coi là sai."
        )
    if not runs:
        return pd.DataFrame({"chi_so": [], "gia_tri": []})

    hang = []
    for k in ks:
        for ten, ham in (
            ("recall", recall_at_k), ("mrr", mrr_at_k),
            ("ndcg", ndcg_at_k), ("f2", f2_at_k),
        ):
            gia_tri = sum(ham(r, gold_map[q], k) for q, r in runs.items()) / len(runs)
            hang.append((f"{ten}@{k}", round(gia_tri, 4)))
    return pd.DataFrame(hang, columns=["chi_so", "gia_tri"])
