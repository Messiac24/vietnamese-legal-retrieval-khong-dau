"""Chia tập câu hỏi.

Bộ dữ liệu gốc chỉ có train và test, không có validation. Không có val thì mọi
tham số phải quét trên test, và con số công bố chính là con số đã chỉnh cho vừa
test. Mô-đun này cắt val ra từ train.

Đơn vị chia là **câu hỏi**, không phải cặp qrel. Một câu hỏi có hai điều luật
gold mà bị tách qua hai tập thì cùng một câu được chấm ở cả hai nơi.
"""
import random


def split_queries(
    query_ids, val_ratio: float, seed: int
) -> tuple[set[str], set[str]]:
    """Chia danh sách câu hỏi thành (train, val).

    `sorted` trước khi xáo để kết quả không phụ thuộc thứ tự đầu vào: cùng một
    tập câu hỏi, dù nạp theo thứ tự nào, cũng phải ra cùng một cách chia.

    Dùng `random.Random(seed)` cục bộ chứ không `random.seed`, để không đụng bộ
    sinh số ngẫu nhiên toàn cục mà phần khác của chương trình đang dùng.
    """
    ids = sorted(set(query_ids))
    rng = random.Random(seed)
    rng.shuffle(ids)
    n_val = int(round(len(ids) * val_ratio))
    return set(ids[n_val:]), set(ids[:n_val])
