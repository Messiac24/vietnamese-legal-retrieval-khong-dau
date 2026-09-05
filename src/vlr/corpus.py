"""Tải và nạp bộ dữ liệu Zalo AI Challenge 2021 (bản BEIR trên HuggingFace).

Bộ dữ liệu không nằm trong kho mã: nặng 115 MB và tải lại được bằng một lệnh.
"""
import json
import urllib.request
from pathlib import Path

import pandas as pd

from vlr import config


def _fetch(url: str, dest: Path) -> None:
    """Tải một tệp, in tiến trình theo MB. Bỏ qua nếu đã có."""
    if dest.exists() and dest.stat().st_size > 0:
        print(f"  đã có {dest.name} ({dest.stat().st_size / 1e6:.1f} MB), bỏ qua")
        return
    dest.parent.mkdir(parents=True, exist_ok=True)
    tmp = dest.with_suffix(dest.suffix + ".part")
    req = urllib.request.Request(url, headers={"User-Agent": "vlr/1.0"})
    with urllib.request.urlopen(req, timeout=180) as r, open(tmp, "wb") as f:
        tong = int(r.headers.get("Content-Length") or 0)
        da = 0
        while True:
            khoi = r.read(1 << 20)
            if not khoi:
                break
            f.write(khoi)
            da += len(khoi)
            if tong:
                print(f"\r  {dest.name}: {da / 1e6:6.1f}/{tong / 1e6:.1f} MB", end="")
            else:
                print(f"\r  {dest.name}: {da / 1e6:6.1f} MB", end="")
    print()
    tmp.replace(dest)


def download() -> None:
    """Tải bốn tệp nguồn về data/raw/."""
    config.ensure_dirs()
    print("Tải bộ dữ liệu Zalo AI 2021 từ HuggingFace:")
    for ten_dich, duong_dan in config.RAW_FILES.items():
        _fetch(config.HF_BASE + duong_dan, config.RAW_DIR / ten_dich)


def _read_jsonl(ten: str) -> list[dict]:
    duong_dan = config.RAW_DIR / ten
    if not duong_dan.exists():
        raise FileNotFoundError(
            f"Chưa có {duong_dan}. Chạy trước:\n"
            f"    C:/Python314/python.exe scripts/01_prepare_data.py"
        )
    with open(duong_dan, encoding="utf-8") as f:
        return [json.loads(dong) for dong in f if dong.strip()]


def parse_article_id(article_id: str) -> tuple[str, int]:
    """Tách '01/2009/tt-bnn+1' thành ('01/2009/tt-bnn', 1).

    Tách ở dấu cộng CUỐI CÙNG, vì số hiệu văn bản về nguyên tắc có thể chứa
    dấu cộng.
    """
    if "+" not in article_id:
        raise ValueError(
            f"id điều luật sai định dạng, thiếu dấu cộng: {article_id!r}"
        )
    doc_id, so = article_id.rsplit("+", 1)
    if not so.isdigit():
        raise ValueError(
            f"id điều luật sai định dạng, phần sau dấu cộng không phải số: {article_id!r}"
        )
    return doc_id, int(so)


def load_articles() -> pd.DataFrame:
    """Bảng điều luật: article_id, doc_id, article_no, title, text."""
    ban_ghi = _read_jsonl("corpus.jsonl")
    df = pd.DataFrame(
        {
            "article_id": [b["_id"] for b in ban_ghi],
            "title": [b.get("title", "") or "" for b in ban_ghi],
            "text": [b.get("text", "") or "" for b in ban_ghi],
        }
    )
    tach = df["article_id"].map(parse_article_id)
    df["doc_id"] = [t[0] for t in tach]
    df["article_no"] = [t[1] for t in tach]
    return df[["article_id", "doc_id", "article_no", "title", "text"]]


def load_queries() -> pd.DataFrame:
    """Bảng câu hỏi: query_id, text."""
    ban_ghi = _read_jsonl("queries.jsonl")
    return pd.DataFrame(
        {
            "query_id": [b["_id"] for b in ban_ghi],
            "text": [b["text"] for b in ban_ghi],
        }
    )


def load_qrels(split: str) -> pd.DataFrame:
    """Bảng nhãn đúng: query_id, article_id, score. split là 'train' hoặc 'test'."""
    if split not in ("train", "test"):
        raise ValueError(f"split phải là 'train' hoặc 'test', nhận được {split!r}")
    ban_ghi = _read_jsonl(f"qrels_{split}.jsonl")
    return pd.DataFrame(
        {
            "query_id": [b["query-id"] for b in ban_ghi],
            "article_id": [b["corpus-id"] for b in ban_ghi],
            "score": [int(b["score"]) for b in ban_ghi],
        }
    )
