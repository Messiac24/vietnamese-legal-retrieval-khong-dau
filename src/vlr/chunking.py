"""Cắt điều luật thành đoạn cho tầng ngữ nghĩa: theo khoản trước, khoản quá dài mới
trượt cửa sổ.
"""
import re

import pandas as pd

# Đầu một khoản: "1. ", "12. " ở đầu dòng hoặc ngay sau xuống dòng
_DAU_KHOAN = re.compile(r"(?:(?<=\n)|(?<=^))\s*(?=\d{1,2}\.\s)")


def _tach_khoan(text: str) -> list[str]:
    phan = [p.strip() for p in _DAU_KHOAN.split(text) if p and p.strip()]
    return phan or ([text.strip()] if text.strip() else [])


def split_article(
    title: str,
    text: str,
    max_words: int,
    overlap: int,
    max_chunks: int | None = None,
) -> list[str]:
    """Cắt một điều thành các đoạn, đoạn nào cũng ghép tiêu đề điều ở đầu."""
    tien_to = title.strip()
    buoc = max(1, max_words - overlap)

    cua_so: list[list[str]] = []
    hien_tai: list[str] = []
    for khoan in _tach_khoan(text):
        tu = khoan.split()
        if not tu:
            continue
        if len(tu) > max_words:
            # Khoản này tự nó đã quá dài: đóng cửa sổ đang mở rồi trượt
            if hien_tai:
                cua_so.append(hien_tai)
                hien_tai = []
            for i in range(0, len(tu), buoc):
                cua_so.append(tu[i:i + max_words])
                if i + max_words >= len(tu):
                    break
        elif len(hien_tai) + len(tu) <= max_words:
            hien_tai.extend(tu)
        else:
            cua_so.append(hien_tai)
            hien_tai = list(tu)
    if hien_tai:
        cua_so.append(hien_tai)

    if not cua_so:
        return [tien_to] if tien_to else []
    if max_chunks is not None:
        cua_so = cua_so[:max_chunks]
    return [f"{tien_to}. {' '.join(w)}".strip() for w in cua_so]


def build_chunks(
    articles: pd.DataFrame,
    max_words: int,
    overlap: int,
    max_chunks: int | None = None,
) -> pd.DataFrame:
    """Bảng chunk_id, article_id, text. chunk_id có dạng `<article_id>#<n>`."""
    ids: list[str] = []
    thuoc: list[str] = []
    noi_dung: list[str] = []
    for aid, tieu_de, than in zip(
        articles["article_id"], articles["title"], articles["text"]
    ):
        doan = split_article(tieu_de, than, max_words, overlap, max_chunks)
        if not doan:
            doan = [str(aid)]
        for i, d in enumerate(doan):
            ids.append(f"{aid}#{i}")
            thuoc.append(aid)
            noi_dung.append(d)
    return pd.DataFrame({"chunk_id": ids, "article_id": thuoc, "text": noi_dung})
