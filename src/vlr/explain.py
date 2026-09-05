"""Giải thích vì sao một điều luật được trả về.

Một hệ tra cứu luật mà chỉ đưa ra danh sách không kèm lý do thì người dùng không
có cách nào kiểm tra. Tầng từ khóa có lợi thế lớn ở đây: giải thích được bằng
đúng những từ đã khớp, còn tầng ngữ nghĩa chỉ đưa ra một con số cosine.

Đây cũng là lý do thực dụng để giữ BM25 trong hệ lai, ngoài chuyện điểm số.
"""
import math
from collections import Counter

from vlr import textnorm


def build_idf(kho_tokens) -> dict[str, float]:
    """IDF theo công thức của BM25: log(1 + (N - n + 0,5) / (n + 0,5)).

    Từ xuất hiện ở mọi điều luật ("quy_định", "thực_hiện") gần như không mang
    thông tin phân biệt, nên IDF của chúng thấp. Từ hiếm như "phá_sản" mới là
    thứ quyết định.
    """
    n_tai_lieu = 0
    dem = Counter()
    for toks in kho_tokens:
        n_tai_lieu += 1
        dem.update(set(toks))
    return {
        t: math.log(1 + (n_tai_lieu - n + 0.5) / (n + 0.5)) for t, n in dem.items()
    }


def matched_terms(
    query: str, article_text: str, idf: dict[str, float]
) -> list[tuple[str, float]]:
    """Những từ vừa có trong câu hỏi vừa có trong điều luật, kèm đóng góp.

    Đóng góp xấp xỉ bằng IDF nhân số lần xuất hiện trong điều luật, có hãm theo
    kiểu BM25 để một từ lặp mười lần không ăn điểm gấp mười.
    """
    q = set(textnorm.tokens(query))
    if not q:
        return []
    a = textnorm.tokens(article_text)
    if not a:
        return []
    dem = Counter(a)
    ket = []
    for t in q & set(dem):
        tf = dem[t]
        ket.append((t, round(idf.get(t, 0.0) * (tf * 2.2) / (tf + 1.2), 4)))
    return sorted(ket, key=lambda x: (-x[1], x[0]))


def to_chuoi(cap: list[tuple[str, float]], toi_da: int = 6) -> str:
    """Rút gọn thành một dòng để in ra bảng hoặc slide."""
    return ", ".join(f"{t} ({s:g})" for t, s in cap[:toi_da]) or "(không từ nào khớp)"
