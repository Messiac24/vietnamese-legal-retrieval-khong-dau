"""Chuẩn hóa và tách từ tiếng Việt.

Tách từ quan trọng với tiếng Việt vì ranh giới từ không trùng ranh giới khoảng
trắng. "bằng lái xe" là một khái niệm; tách theo khoảng trắng thì "bằng" khớp
nhầm với "bằng chứng", "ngang bằng". pyvi nối các âm tiết của một từ ghép bằng
dấu gạch dưới, nên `normalize` phải giữ lại dấu gạch dưới.
"""
import re
import unicodedata
import warnings

with warnings.catch_warnings():
    # pyvi nạp mô hình bằng pickle và bật cảnh báo dtype của NumPy 2.4
    warnings.simplefilter("ignore")
    from pyvi import ViTokenizer

# Từ chức năng tiếng Việt. Cố ý KHÔNG chứa các từ mang nghĩa pháp lý như
# "bị", "phải", "cấm", "được phép", vì chúng phân biệt nghĩa trong văn bản luật.
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
    """Đưa về NFC, chữ thường, bỏ dấu câu, gom khoảng trắng.

    Giữ chữ số và dấu gạch dưới. Chữ số quan trọng vì câu hỏi pháp luật hay
    xoay quanh con số: "thương tật 25%", "Điều 4", "100/2019/nđ-cp".
    """
    s = unicodedata.normalize("NFC", s).lower()
    s = _PUNCT.sub(" ", s)
    return _SPACES.sub(" ", s).strip()


def segment(s: str) -> str:
    """Tách từ bằng pyvi. Giữ nguyên hoa thường và dấu câu.

    Không chuẩn hóa trước khi gọi pyvi: bộ tách từ dùng dấu câu và chữ hoa làm
    manh mối đoán ranh giới từ, bỏ chúng đi thì tách kém đi.
    """
    if not s or not s.strip():
        return ""
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        return ViTokenizer.tokenize(s)


def tokens(s: str) -> list[str]:
    """Tách từ, chuẩn hóa, bỏ stopword. Đây là đầu vào của BM25."""
    return [t for t in normalize(segment(s)).split() if t not in STOPWORDS]


def ngrams(toks: list[str], n: int) -> set[str]:
    """Tập n-gram từ, dùng cho SimHash và Jaccard trong bước kiểm toán."""
    if len(toks) < n:
        return {" ".join(toks)} if toks else set()
    return {" ".join(toks[i:i + n]) for i in range(len(toks) - n + 1)}
