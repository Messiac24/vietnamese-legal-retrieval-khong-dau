"""Chuẩn hóa và tách từ tiếng Việt. pyvi nối âm tiết của từ ghép bằng dấu gạch dưới."""
import re
import unicodedata
import warnings

with warnings.catch_warnings():
    # pyvi nạp mô hình bằng pickle và bật cảnh báo dtype của NumPy 2.4
    warnings.simplefilter("ignore")
    from pyvi import ViTokenizer

# không bỏ "bị", "phải", "cấm", "được phép": trong luật mấy từ này đổi nghĩa cả câu
STOPWORDS = frozenset("""
và với của cho về từ tại theo trong ngoài trên dưới ra vào lên xuống
là làm có không chưa đã đang sẽ vẫn còn rồi
này kia đó ấy nào đâu gì ai sao
một hai các những mọi từng mỗi cả tất_cả
thì mà nên nếu tuy nhưng hoặc hay cùng
khi lúc sau trước nay giờ
ta tôi bạn họ nó mình chúng_ta chúng_tôi
rất khá hơi lắm quá
việc điều_kiện_này cái con chiếc
để do bởi vì nhằm
ạ à ơi nhé nhỉ
""".split())

_PUNCT = re.compile(r"[^\w\s]", flags=re.UNICODE)
_SPACES = re.compile(r"\s+")


def normalize(s: str) -> str:
    """NFC, chữ thường, bỏ dấu câu. Giữ chữ số và dấu gạch dưới."""
    s = unicodedata.normalize("NFC", s).lower()
    s = _PUNCT.sub(" ", s)
    return _SPACES.sub(" ", s).strip()


def segment(s: str) -> str:
    """Tách từ trên văn bản gốc, vì pyvi dựa vào dấu câu và chữ hoa để đoán ranh giới."""
    if not s or not s.strip():
        return ""
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        return ViTokenizer.tokenize(s)


def tokens(s: str) -> list[str]:
    """Đầu vào của BM25: tách từ, chuẩn hóa, bỏ stopword."""
    return [t for t in normalize(segment(s)).split() if t not in STOPWORDS]


def ngrams(toks: list[str], n: int) -> set[str]:
    if len(toks) < n:
        return {" ".join(toks)} if toks else set()
    return {" ".join(toks[i:i + n]) for i in range(len(toks) - n + 1)}
