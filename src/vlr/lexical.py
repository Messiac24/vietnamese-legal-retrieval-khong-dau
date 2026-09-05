"""Tầng từ khóa: chỉ mục BM25 trên điều luật đã tách từ.

Lập chỉ mục ở mức ĐIỀU LUẬT chứ không chia đoạn, khác với tầng ngữ nghĩa. Lý do:
BM25 đã có sẵn cơ chế chuẩn hóa theo độ dài văn bản qua tham số `b`, nên điều
dài không tự động được điểm cao hơn. Bi-encoder thì không có cơ chế đó, lại còn
bị chặn cứng ở 256 token, nên bắt buộc phải chia đoạn.
"""
import json
from pathlib import Path

import bm25s
import pandas as pd

from vlr import textnorm


class BM25Index:
    """Bọc `bm25s.BM25` để làm việc theo article_id thay vì chỉ số hàng."""

    def __init__(self, articles: pd.DataFrame, k1: float, b: float):
        self.k1 = k1
        self.b = b
        self.article_ids = list(articles["article_id"])
        if "tokens" in articles.columns:
            # Tách từ 61k điều mất 3 tới 4 phút, nên luôn dùng lại bản đã có
            kho = [list(t) for t in articles["tokens"]]
        else:
            kho = [
                textnorm.tokens(f"{tt} {nd}")
                for tt, nd in zip(articles["title"], articles["text"])
            ]
        self._model = bm25s.BM25(k1=k1, b=b)
        self._model.index(kho, show_progress=False)

    def search(self, query: str, top_k: int) -> list[tuple[str, float]]:
        """Trả về [(article_id, điểm)] xếp giảm dần."""
        return self.search_tokens(textnorm.tokens(query), top_k)

    def search_tokens(self, toks: list[str], top_k: int) -> list[tuple[str, float]]:
        """Như `search` nhưng nhận sẵn token, tránh tách từ lại nhiều lần."""
        if not toks:
            return []
        k = min(top_k, len(self.article_ids))
        chi_so, diem = self._model.retrieve([toks], k=k, show_progress=False)
        return [
            (self.article_ids[int(i)], float(s))
            for i, s in zip(chi_so[0], diem[0])
        ]

    def save(self, path) -> None:
        path = Path(path)
        path.mkdir(parents=True, exist_ok=True)
        self._model.save(str(path), allow_pickle=True)
        (path / "meta.json").write_text(
            json.dumps(
                {"article_ids": self.article_ids, "k1": self.k1, "b": self.b},
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )

    @classmethod
    def load(cls, path) -> "BM25Index":
        path = Path(path)
        meta_path = path / "meta.json"
        if not meta_path.exists():
            raise FileNotFoundError(
                f"Chưa có chỉ mục BM25 ở {path}. Chạy trước:\n"
                f"    C:/Python314/python.exe scripts/02_build_index.py --model bm25"
            )
        meta = json.loads(meta_path.read_text(encoding="utf-8"))
        obj = cls.__new__(cls)
        obj.article_ids = meta["article_ids"]
        obj.k1 = meta["k1"]
        obj.b = meta["b"]
        obj._model = bm25s.BM25.load(str(path), allow_pickle=True)
        return obj
