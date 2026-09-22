"""Cắt val ra từ train. Chia theo câu hỏi, không theo cặp nhãn."""
import random


def split_queries(
    query_ids, val_ratio: float, seed: int
) -> tuple[set[str], set[str]]:
    """Sắp xếp trước khi xáo để kết quả không phụ thuộc thứ tự đầu vào."""
    ids = sorted(set(query_ids))
    rng = random.Random(seed)
    rng.shuffle(ids)
    n_val = int(round(len(ids) * val_ratio))
    return set(ids[n_val:]), set(ids[:n_val])
