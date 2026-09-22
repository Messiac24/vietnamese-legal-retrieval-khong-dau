"""Liệt kê từ khớp giữa câu hỏi và điều luật, để biết vì sao điều đó được trả về."""
import math
from collections import Counter

from vlr import textnorm


def build_idf(kho_tokens) -> dict[str, float]:
    """IDF kiểu BM25: log(1 + (N - n + 0,5) / (n + 0,5))."""
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
    """Từ vừa có trong câu hỏi vừa có trong điều luật, kèm đóng góp xấp xỉ theo BM25."""
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
    return ", ".join(f"{t} ({s:g})" for t, s in cap[:toi_da]) or "(không từ nào khớp)"
