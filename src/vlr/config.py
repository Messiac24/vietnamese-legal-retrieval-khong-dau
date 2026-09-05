"""Nơi duy nhất chứa hằng số của đồ án.

Muốn đổi tham số thì sửa ở đây, không rải số ma thuật khắp mã.
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

DATA_DIR = ROOT / "data"
RAW_DIR = DATA_DIR / "raw"
INDEX_DIR = DATA_DIR / "index"
REPORTS_DIR = ROOT / "reports"
AUDIT_DIR = REPORTS_DIR / "audit"
EVAL_DIR = REPORTS_DIR / "eval"
RUNS_DIR = ROOT / "runs"

ARTICLES_PATH = DATA_DIR / "articles.parquet"
QUERIES_PATH = DATA_DIR / "queries.parquet"
QRELS_PATH = DATA_DIR / "qrels.parquet"
CHUNKS_PATH = DATA_DIR / "chunks.parquet"

# Nguồn dữ liệu: Zalo AI Challenge 2021, bản BEIR trên HuggingFace, giấy phép MIT
HF_BASE = ("https://huggingface.co/datasets/GreenNode/"
           "zalo-ai-legal-text-retrieval-vn/resolve/main/")
RAW_FILES = {
    "corpus.jsonl": "corpus.jsonl",
    "queries.jsonl": "queries.jsonl",
    "qrels_train.jsonl": "qrels/train.jsonl",
    "qrels_test.jsonl": "qrels/test.jsonl",
}

# Tái lập
SEED = 42
VAL_RATIO = 0.2

# Chia đoạn cho tầng ngữ nghĩa
CHUNK_WORDS = 180
CHUNK_OVERLAP = 40

# Kiểm toán trùng lặp
NEAR_DUP_HAMMING = 3        # trên 64 bit SimHash
SIMHASH_NGRAM = 5           # n-gram từ dùng để băm điều luật
QUESTION_NGRAM = 3          # n-gram từ dùng để so câu hỏi
QUESTION_JACCARD = 0.8      # ngưỡng coi hai câu hỏi là gần trùng

# Truy hồi
TOPK_FUSION = 100           # số ứng viên mỗi tầng đưa vào bước hợp nhất
EVAL_KS = (1, 5, 10, 20)
TUNE_METRIC_K = 10          # chọn tham số theo Recall@10

# Lưới quét tham số, tất cả quét trên val
BM25_K1_GRID = (0.6, 0.9, 1.2, 1.5, 1.8)
BM25_B_GRID = (0.3, 0.5, 0.75, 0.9)
RRF_K_GRID = (10, 20, 60, 100)
ALPHA_GRID = tuple(round(0.05 * i, 2) for i in range(21))
POOLING_GRID = ("max", "mean")

# Mô hình
BKAI_MODEL = "bkai-foundation-models/vietnamese-bi-encoder"
BKAI_MAX_LEN = 256
BKAI_NEEDS_SEGMENT = True   # PhobertTokenizer đòi văn bản đã tách từ

AITEAM_MODEL = "AITeamVN/Vietnamese_Embedding"
AITEAM_MAX_LEN = 512        # trần thật là 8192, cắt xuống cho cân chi phí
AITEAM_NEEDS_SEGMENT = False

BKAI_FT_DIR = RUNS_DIR / "bkai_ft"

# Fine-tune
FT_EPOCHS = 2
FT_BATCH = 32
FT_LR = 2e-5
FT_WARMUP_RATIO = 0.1
FT_HARD_NEGATIVES = 4

# Mọi CSV ghi kèm BOM để mở bằng Excel không vỡ chữ tiếng Việt
CSV_KW = {"index": False, "encoding": "utf-8-sig"}


def ensure_dirs() -> None:
    """Tạo các thư mục đầu ra nếu chưa có."""
    for d in (DATA_DIR, RAW_DIR, INDEX_DIR, AUDIT_DIR, EVAL_DIR, RUNS_DIR):
        d.mkdir(parents=True, exist_ok=True)
