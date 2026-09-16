"""Câu hỏi gõ không dấu: bỏ dấu, nhận diện, và phục hồi dấu.

Phục hồi dấu dùng mô hình ngôn ngữ bigram trên âm tiết, học từ chính kho điều
luật cộng câu hỏi train, rồi giải bằng Viterbi. Không cần tải mô hình nào thêm,
và từ vựng pháp lý có sẵn trong kho nên phục hồi đúng những từ cần để tìm luật.
"""
import math
import pickle
import re
import unicodedata
from collections import Counter
from pathlib import Path

_TU = re.compile(r"\w+", re.UNICODE)
_TACH = re.compile(r"(\w+)", re.UNICODE)


def bo_dau(s: str) -> str:
    """Bỏ mọi dấu thanh và dấu mũ, đổi đ thành d. Giữ hoa thường."""
    s = unicodedata.normalize("NFD", s)
    s = "".join(c for c in s if unicodedata.category(c) != "Mn")
    return unicodedata.normalize("NFC", s.replace("đ", "d").replace("Đ", "D"))


def co_dau(s: str) -> bool:
    """True nếu chuỗi có ít nhất một chữ mang dấu tiếng Việt."""
    s = unicodedata.normalize("NFC", s)
    return bo_dau(s) != s


def am_tiet(s: str) -> list[str]:
    """Tách thành âm tiết chữ thường, bỏ dấu câu. Không tách từ ghép."""
    return _TU.findall(unicodedata.normalize("NFC", s).lower())


class PhucHoiDau:
    """Mô hình bigram âm tiết, nội suy với unigram, giải bằng Viterbi."""

    def __init__(self, van_ban, lam: float = 0.9):
        self.lam = lam
        self.uni: Counter = Counter()
        self.bi: Counter = Counter()
        for s in van_ban:
            toks = am_tiet(s)
            self.uni.update(toks)
            self.bi.update(zip(toks, toks[1:]))
        self.N = sum(self.uni.values())
        self.V = len(self.uni)
        self.ung_vien: dict[str, list[str]] = {}
        for w in self.uni:
            self.ung_vien.setdefault(bo_dau(w), []).append(w)

    def _logp(self, truoc: str | None, w: str) -> float:
        p_uni = (self.uni[w] + 1) / (self.N + self.V)
        if truoc is None or self.uni[truoc] == 0:
            return math.log(p_uni)
        p_bi = self.bi.get((truoc, w), 0) / self.uni[truoc]
        p = self.lam * p_bi + (1 - self.lam) * p_uni
        # lam = 1 biến thành bigram thuần, gặp bigram chưa thấy là p = 0
        return math.log(p) if p > 0 else -math.inf

    def _ung_vien(self, w: str) -> list[str]:
        # Âm tiết người dùng đã gõ có dấu thì giữ nguyên, chỉ phục hồi phần thiếu
        if co_dau(w):
            return [w]
        return self.ung_vien.get(w, [w])

    def phuc_hoi_am_tiet(self, toks: list[str]) -> list[str]:
        if not toks:
            return []
        cot = [{w: (self._logp(None, w), None) for w in self._ung_vien(toks[0])}]
        for t in toks[1:]:
            moi = {}
            for w in self._ung_vien(t):
                moi[w] = max(
                    ((d + self._logp(u, w), u) for u, (d, _) in cot[-1].items()),
                    key=lambda x: x[0],
                )
            cot.append(moi)
        w = max(cot[-1], key=lambda x: cot[-1][x][0])
        kq = [w]
        for i in range(len(cot) - 1, 0, -1):
            w = cot[i][w][1]
            kq.append(w)
        return kq[::-1]

    def phuc_hoi(self, s: str) -> str:
        """Phục hồi dấu cho cả câu, giữ nguyên dấu câu và chữ hoa đầu âm tiết."""
        phan = _TACH.split(unicodedata.normalize("NFC", s))
        vi_tri = [i for i in range(1, len(phan), 2)]
        moi = self.phuc_hoi_am_tiet([phan[i].lower() for i in vi_tri])
        for i, w in zip(vi_tri, moi):
            goc = phan[i]
            if goc[:1].isupper():
                w = w.upper() if goc.isupper() and len(goc) > 1 else w[:1].upper() + w[1:]
            phan[i] = w
        return "".join(phan)

    def save(self, path) -> None:
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        with open(path, "wb") as f:
            pickle.dump(self, f, protocol=pickle.HIGHEST_PROTOCOL)

    @staticmethod
    def load(path) -> "PhucHoiDau":
        path = Path(path)
        if not path.exists():
            raise FileNotFoundError(
                f"Chưa có mô hình phục hồi dấu ở {path}. Chạy trước:\n"
                "    C:/Python314/python.exe scripts/07_khong_dau.py"
            )
        with open(path, "rb") as f:
            return pickle.load(f)


def do_chinh_xac(goc: str, phuc_hoi: str) -> tuple[int, int]:
    """(số âm tiết khớp, tổng số âm tiết), so không phân biệt hoa thường."""
    a, b = am_tiet(goc), am_tiet(phuc_hoi)
    if len(a) != len(b):
        raise ValueError(f"lệch số âm tiết: {len(a)} so với {len(b)}")
    return sum(x == y for x, y in zip(a, b)), len(a)
