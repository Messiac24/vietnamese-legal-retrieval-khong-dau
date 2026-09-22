"""Tầng ngữ nghĩa: mã hóa đoạn bằng bi-encoder, tìm bằng tích vô hướng.

bkai (PhoBERT) cần văn bản đã tách từ, AITeamVN (XLM-R) thì không. Không dùng
FAISS vì 788 truy vấn nhân 150k vector chạy thẳng bằng torch trên GPU vẫn nhanh.
"""
import json
from pathlib import Path

import numpy as np

from vlr import textnorm


def article_of(chunk_id: str) -> str:
    if "#" not in chunk_id:
        raise ValueError(f"chunk_id sai định dạng, thiếu dấu thăng: {chunk_id!r}")
    return chunk_id.rsplit("#", 1)[0]


def l2_normalize(x: np.ndarray) -> np.ndarray:
    do_dai = np.linalg.norm(x, axis=1, keepdims=True)
    do_dai[do_dai == 0] = 1.0
    return x / do_dai


def pool_chunk_scores(
    chunk_ids, scores, article_of_map: dict[str, str], how: str
) -> dict[str, float]:
    """Gộp điểm đoạn về điều bằng max hoặc mean."""
    if how not in ("max", "mean"):
        raise ValueError(f"how phải là 'max' hoặc 'mean', nhận được {how!r}")
    gom: dict[str, list[float]] = {}
    for cid, s in zip(chunk_ids, scores):
        gom.setdefault(article_of_map[cid], []).append(float(s))
    if how == "max":
        return {a: max(v) for a, v in gom.items()}
    return {a: sum(v) / len(v) for a, v in gom.items()}


def top_articles(diem: dict[str, float], top_k: int) -> list[tuple[str, float]]:
    """Hòa điểm thì xếp theo id cho kết quả ổn định."""
    return sorted(diem.items(), key=lambda x: (-x[1], x[0]))[:top_k]


class DenseIndex:

    def __init__(
        self,
        model_name: str,
        max_seq_length: int,
        need_segment: bool,
        chunk_ids: list[str] | None = None,
        embeddings: np.ndarray | None = None,
        fp16: bool = True,
    ):
        self.model_name = model_name
        self.max_seq_length = max_seq_length
        self.need_segment = need_segment
        self.chunk_ids = chunk_ids or []
        self.embeddings = embeddings
        self.fp16 = fp16
        self._model = None
        self._article_of = {c: article_of(c) for c in self.chunk_ids}
        self._doan_cua: dict[str, list[int]] | None = None

    def doan_khop_nhat(self, query_vec: np.ndarray, article_id: str) -> tuple[str, float] | None:
        """Đoạn khớp câu hỏi nhất trong một điều. Chỉ là khoản quyết định điểm khi gộp bằng max."""
        if self._doan_cua is None:
            self._doan_cua = {}
            for i, c in enumerate(self.chunk_ids):
                self._doan_cua.setdefault(self._article_of[c], []).append(i)
        vt = self._doan_cua.get(article_id)
        if not vt:
            return None
        s = self.embeddings[vt].astype(np.float32) @ np.asarray(query_vec, dtype=np.float32)
        j = int(np.argmax(s))
        return self.chunk_ids[vt[j]], float(s[j])

    def _load_model(self):
        """Nạp mô hình một lần. fp16 nhanh gấp khoảng 2,5 lần fp32, cosine lệch cỡ 1e-3."""
        if self._model is None:
            import torch
            from sentence_transformers import SentenceTransformer

            co_gpu = torch.cuda.is_available()
            self._model = SentenceTransformer(
                self.model_name, device="cuda" if co_gpu else "cpu"
            )
            self._model.max_seq_length = self.max_seq_length
            if co_gpu and self.fp16:
                self._model.half()
        return self._model

    def _prepare(self, texts: list[str]) -> list[str]:
        """PhoBERT học trên văn bản đã tách từ nên phải tách trước khi mã hóa."""
        return [textnorm.segment(t) for t in texts] if self.need_segment else texts

    def encode_corpus(self, chunk_ids: list[str], texts: list[str],
                      batch_size: int = 256,
                      already_segmented: bool = False) -> None:
        """`already_segmented` để dùng lại bản đã tách từ, khỏi tách lại 150k đoạn."""
        model = self._load_model()
        vec = model.encode(
            texts if already_segmented else self._prepare(texts),
            batch_size=batch_size,
            convert_to_numpy=True,
            normalize_embeddings=True,
            show_progress_bar=True,
        )
        self.chunk_ids = list(chunk_ids)
        self.embeddings = vec.astype(np.float16)
        self._article_of = {c: article_of(c) for c in self.chunk_ids}
        self._doan_cua = None   # đệm cũ trỏ theo chỉ số của bộ đoạn trước

    def encode_queries(self, texts: list[str], batch_size: int = 256) -> np.ndarray:
        model = self._load_model()
        return model.encode(
            self._prepare(texts),
            batch_size=batch_size,
            convert_to_numpy=True,
            normalize_embeddings=True,
            show_progress_bar=False,
        ).astype(np.float32)

    def search(
        self, query_vecs: np.ndarray, top_k: int, pooling: str = "max",
        chunk_top: int = 500, block: int = 50_000,
    ) -> list[list[tuple[str, float]]]:
        """Lấy `chunk_top` đoạn tốt nhất rồi mới gộp về điều. Nhân theo lô `block` để không
        đưa cả ma trận lên GPU một lần.
        """
        import torch

        if self.embeddings is None:
            raise RuntimeError("Chỉ mục rỗng. Chạy encode_corpus hoặc load trước.")
        thiet_bi = "cuda" if torch.cuda.is_available() else "cpu"
        q = torch.from_numpy(np.ascontiguousarray(query_vecs)).to(thiet_bi).float()

        diem_tot = torch.full((len(q), 0), 0.0, device=thiet_bi)
        vi_tri_tot = torch.zeros((len(q), 0), dtype=torch.long, device=thiet_bi)
        for dau in range(0, len(self.chunk_ids), block):
            lo = torch.from_numpy(
                self.embeddings[dau:dau + block].astype(np.float32)
            ).to(thiet_bi)
            sim = q @ lo.T
            k = min(chunk_top, sim.shape[1])
            d, i = torch.topk(sim, k, dim=1)
            diem_tot = torch.cat([diem_tot, d], dim=1)
            vi_tri_tot = torch.cat([vi_tri_tot, i + dau], dim=1)
            del lo, sim
            k2 = min(chunk_top, diem_tot.shape[1])
            diem_tot, chon = torch.topk(diem_tot, k2, dim=1)
            vi_tri_tot = torch.gather(vi_tri_tot, 1, chon)

        diem_tot = diem_tot.cpu().numpy()
        vi_tri_tot = vi_tri_tot.cpu().numpy()
        ket = []
        for hang in range(len(q)):
            cids = [self.chunk_ids[int(j)] for j in vi_tri_tot[hang]]
            gom = pool_chunk_scores(cids, diem_tot[hang], self._article_of, pooling)
            ket.append(top_articles(gom, top_k))
        return ket

    def save(self, path) -> None:
        path = Path(path)
        path.mkdir(parents=True, exist_ok=True)
        np.save(path / "embeddings.npy", self.embeddings)
        (path / "meta.json").write_text(
            json.dumps(
                {
                    "model_name": self.model_name,
                    "max_seq_length": self.max_seq_length,
                    "need_segment": self.need_segment,
                    "chunk_ids": self.chunk_ids,
                },
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )

    @classmethod
    def load(cls, path) -> "DenseIndex":
        path = Path(path)
        meta_path = path / "meta.json"
        if not meta_path.exists():
            raise FileNotFoundError(
                f"Chưa có chỉ mục vector ở {path}. Chạy trước:\n"
                f"    C:/Python314/python.exe scripts/02_build_index.py"
            )
        meta = json.loads(meta_path.read_text(encoding="utf-8"))
        return cls(
            model_name=meta["model_name"],
            max_seq_length=meta["max_seq_length"],
            need_segment=meta["need_segment"],
            chunk_ids=meta["chunk_ids"],
            embeddings=np.load(path / "embeddings.npy"),
        )
