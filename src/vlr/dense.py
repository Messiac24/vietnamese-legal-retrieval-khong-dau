"""Tầng ngữ nghĩa: mã hóa đoạn thành vector rồi tìm bằng tích vô hướng.

Hai bộ mã hóa ăn CÙNG một bộ đoạn, chỉ khác khâu tiền xử lý mà kiến trúc của
chúng đòi hỏi. Nhờ vậy biến duy nhất giữa hai lượt chạy là bộ mã hóa:

    bkai (PhoBERT base)      768 chiều, 256 token, BẮT BUỘC tách từ
    AITeamVN (XLM-R large)  1024 chiều, cắt ở 512 token, không cần tách từ

Không dùng FAISS. 788 truy vấn nhân với khoảng 150.000 vector 768 chiều là phép
nhân ma trận nhỏ với GPU, chạy thẳng bằng torch còn nhanh hơn dựng chỉ mục xấp
xỉ, lại bỏ được một phụ thuộc và không có sai số xấp xỉ.
"""
import json
from pathlib import Path

import numpy as np

from vlr import textnorm


def article_of(chunk_id: str) -> str:
    """Suy ra article_id từ chunk_id dạng `<article_id>#<n>`."""
    if "#" not in chunk_id:
        raise ValueError(f"chunk_id sai định dạng, thiếu dấu thăng: {chunk_id!r}")
    return chunk_id.rsplit("#", 1)[0]


def l2_normalize(x: np.ndarray) -> np.ndarray:
    """Chuẩn hóa từng hàng về độ dài 1, để tích vô hướng chính là cosine."""
    do_dai = np.linalg.norm(x, axis=1, keepdims=True)
    do_dai[do_dai == 0] = 1.0
    return x / do_dai


def pool_chunk_scores(
    chunk_ids, scores, article_of_map: dict[str, str], how: str
) -> dict[str, float]:
    """Gộp điểm của các đoạn về điểm của điều luật.

    `max` là mặc định của đồ án: câu trả lời cho một câu hỏi thường nằm gọn
    trong một khoản, nên đoạn khớp nhất mới là bằng chứng. Lấy trung bình sẽ để
    các khoản không liên quan kéo điểm xuống, và điều luật càng dài càng bị
    thiệt. Cả hai cách đều được đo trên val chứ không chọn bằng cảm tính.
    """
    if how not in ("max", "mean"):
        raise ValueError(f"how phải là 'max' hoặc 'mean', nhận được {how!r}")
    gom: dict[str, list[float]] = {}
    for cid, s in zip(chunk_ids, scores):
        gom.setdefault(article_of_map[cid], []).append(float(s))
    if how == "max":
        return {a: max(v) for a, v in gom.items()}
    return {a: sum(v) / len(v) for a, v in gom.items()}


def top_articles(diem: dict[str, float], top_k: int) -> list[tuple[str, float]]:
    """Xếp điều luật theo điểm giảm dần, cắt ở top_k. Hòa điểm thì xếp theo id."""
    return sorted(diem.items(), key=lambda x: (-x[1], x[0]))[:top_k]


class DenseIndex:
    """Chỉ mục vector cho một bộ mã hóa."""

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
        """Đoạn khớp câu hỏi nhất trong một điều luật.

        Với pooling max thì đây đúng là khoản đã quyết định điểm của điều; với
        pooling mean thì chỉ là khoản khớp nhất, không phải khoản quyết định điểm.
        """
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
        """Nạp mô hình một lần, chạy fp16 trên GPU.

        Đo thật trên RTX 5060 Ti với bkai: fp32 batch 128 mất 9,6 phút cho 150k
        đoạn, fp16 batch 256 chỉ 3,8 phút. Sai khác về điểm cosine ở mức 1e-3,
        không đổi thứ hạng. VRAM đỉnh 2,57 GB trên 17,1 GB.
        """
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
        """PhoBERT được huấn luyện trên văn bản đã tách từ. Đưa văn bản thô vào
        thì mỗi âm tiết thành một token lạ và chất lượng tụt hẳn."""
        return [textnorm.segment(t) for t in texts] if self.need_segment else texts

    def encode_corpus(self, chunk_ids: list[str], texts: list[str],
                      batch_size: int = 256,
                      already_segmented: bool = False) -> None:
        """Mã hóa cả kho đoạn.

        `already_segmented` cho phép phía gọi truyền vào văn bản đã tách từ sẵn.
        Tách từ 150k đoạn mất hơn 3 phút, mà cả bkai gốc lẫn bkai đã fine-tune
        đều cần đúng bộ đoạn đã tách đó, nên tách lại lần hai là phí.
        """
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
        """Tìm top_k điều luật cho từng truy vấn.

        Lấy `chunk_top` đoạn tốt nhất rồi mới gộp về điều, thay vì gộp trên toàn
        bộ 150k đoạn: một điều chỉ vào được top-k khi có ít nhất một đoạn lọt
        vào `chunk_top`, nên kết quả không đổi mà rẻ hơn nhiều.

        Nhân theo lô `block` vector để không nạp cả ma trận lên GPU cùng lúc.
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
