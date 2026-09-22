"""Chỉ số truy hồi. `ranked` là danh sách article_id đã xếp hạng, `gold` là tập đúng."""
import math

import pandas as pd


def _trung(ranked, gold, k: int) -> list[int]:
    return [i for i, d in enumerate(ranked[:k]) if d in gold]


def recall_at_k(ranked, gold, k: int) -> float:
    if not gold:
        return 0.0
    return len(_trung(ranked, gold, k)) / len(gold)


def mrr_at_k(ranked, gold, k: int) -> float:
    if not gold:
        return 0.0
    vi_tri = _trung(ranked, gold, k)
    return 1.0 / (vi_tri[0] + 1) if vi_tri else 0.0


def ndcg_at_k(ranked, gold, k: int) -> float:
    """nDCG với nhãn nhị phân."""
    if not gold:
        return 0.0
    dcg = sum(1.0 / math.log2(i + 2) for i in _trung(ranked, gold, k))
    idcg = sum(1.0 / math.log2(i + 2) for i in range(min(len(gold), k)))
    return dcg / idcg if idcg else 0.0


def f2_at_k(ranked, gold, k: int) -> float:
    """F2 theo cách chấm của Zalo AI 2021: 5PR / (4P + R)."""
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
    """Trung bình mọi chỉ số trên các câu hỏi, trả về bảng hai cột chi_so, gia_tri."""
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
