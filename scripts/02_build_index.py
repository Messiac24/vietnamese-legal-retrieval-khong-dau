"""Bước 2: chia đoạn và dựng chỉ mục.

    C:/Python314/python.exe scripts/02_build_index.py --model all
    C:/Python314/python.exe scripts/02_build_index.py --model bkai

Sinh ra:
    data/chunks.parquet            bộ đoạn dùng chung cho mọi bộ mã hóa
    data/chunks_segmented.parquet  bản đã tách từ, cho PhoBERT
    data/index/bm25/               chỉ mục từ khóa
    data/index/<ten>/              chỉ mục vector
    reports/eval/index_cost.csv    thời gian và dung lượng từng chỉ mục
"""
import argparse
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import pandas as pd

from vlr import chunking, config, dense, lexical, textnorm

MO_HINH = {
    "bkai": (config.BKAI_MODEL, config.BKAI_MAX_LEN, config.BKAI_NEEDS_SEGMENT),
    "aiteam": (config.AITEAM_MODEL, config.AITEAM_MAX_LEN, config.AITEAM_NEEDS_SEGMENT),
    "bkai_ft": (str(config.BKAI_FT_DIR), config.BKAI_MAX_LEN, config.BKAI_NEEDS_SEGMENT),
}


def _dung_luong_mb(thu_muc: Path) -> float:
    return sum(f.stat().st_size for f in thu_muc.rglob("*") if f.is_file()) / 1e6


def _ghi_chi_phi(ten: str, so_muc: int, giay: float, mb: float) -> None:
    duong_dan = config.EVAL_DIR / "index_cost.csv"
    hang = {
        "chi_muc": ten,
        "so_muc": so_muc,
        "thoi_gian_giay": round(giay, 1),
        "dung_luong_mb": round(mb, 1),
    }
    if duong_dan.exists():
        df = pd.read_csv(duong_dan, encoding="utf-8-sig")
        df = df[df["chi_muc"] != ten]
        df = pd.concat([df, pd.DataFrame([hang])], ignore_index=True)
    else:
        df = pd.DataFrame([hang])
    df = df.sort_values("chi_muc")
    df.to_csv(duong_dan, **config.CSV_KW)
    print(f"    chi phí -> {duong_dan.relative_to(config.ROOT)}")


def lay_chunks(arts: pd.DataFrame) -> pd.DataFrame:
    if config.CHUNKS_PATH.exists():
        ch = pd.read_parquet(config.CHUNKS_PATH)
        print(f"  dùng lại {len(ch)} đoạn trong {config.CHUNKS_PATH.name}")
        return ch
    t0 = time.perf_counter()
    ch = chunking.build_chunks(arts, config.CHUNK_WORDS, config.CHUNK_OVERLAP)
    ch.to_parquet(config.CHUNKS_PATH, index=False)
    tb = len(ch) / len(arts)
    print(f"  cắt {len(arts)} điều thành {len(ch)} đoạn "
          f"({tb:.2f} đoạn mỗi điều, {time.perf_counter() - t0:.0f}s)")
    return ch


def lay_chunks_da_tach(ch: pd.DataFrame) -> list[str]:
    duong_dan = config.DATA_DIR / "chunks_segmented.parquet"
    if duong_dan.exists():
        df = pd.read_parquet(duong_dan)
        if len(df) == len(ch):
            print("  dùng lại bản đoạn đã tách từ")
            return list(df["text"])
    t0 = time.perf_counter()
    print(f"  tách từ {len(ch)} đoạn (khoảng 3 tới 4 phút)", flush=True)
    seg = [textnorm.segment(t) for t in ch["text"]]
    pd.DataFrame({"chunk_id": ch["chunk_id"], "text": seg}).to_parquet(
        duong_dan, index=False
    )
    print(f"  tách từ xong ({time.perf_counter() - t0:.0f}s)")
    return seg


def dung_bm25(arts: pd.DataFrame) -> None:
    print("\n[BM25] dựng chỉ mục từ khóa trên điều luật")
    t0 = time.perf_counter()
    idx = lexical.BM25Index(arts, k1=config.BM25_K1_GRID[2], b=config.BM25_B_GRID[2])
    thu_muc = config.INDEX_DIR / "bm25"
    idx.save(thu_muc)
    giay = time.perf_counter() - t0
    print(f"    {len(arts)} điều, {giay:.0f}s, {_dung_luong_mb(thu_muc):.1f} MB")
    _ghi_chi_phi("bm25", len(arts), giay, _dung_luong_mb(thu_muc))


def dung_dense(ten: str, ch: pd.DataFrame) -> None:
    model_name, max_len, need_seg = MO_HINH[ten]
    if ten == "bkai_ft" and not Path(model_name).exists():
        raise SystemExit(
            f"Chưa có mô hình đã fine-tune ở {model_name}. Chạy trước:\n"
            f"    C:/Python314/python.exe scripts/03_finetune.py"
        )
    print(f"\n[{ten}] mã hóa {len(ch)} đoạn bằng {model_name}")
    texts = list(ch["text"])
    da_tach = False
    if need_seg:
        texts = lay_chunks_da_tach(ch)
        da_tach = True

    t0 = time.perf_counter()
    idx = dense.DenseIndex(model_name, max_len, need_seg, fp16=config.ENCODE_FP16)
    idx.encode_corpus(
        list(ch["chunk_id"]), texts,
        batch_size=config.ENCODE_BATCH, already_segmented=da_tach,
    )
    giay = time.perf_counter() - t0
    thu_muc = config.INDEX_DIR / ten
    idx.save(thu_muc)
    mb = _dung_luong_mb(thu_muc)
    print(f"    xong: {idx.embeddings.shape} {idx.embeddings.dtype}, "
          f"{giay / 60:.1f} phút, {mb:.0f} MB")
    _ghi_chi_phi(ten, len(ch), giay, mb)


def main() -> None:
    ap = argparse.ArgumentParser(description="Dựng chỉ mục cho hệ tìm kiếm điều luật")
    ap.add_argument("--model", default="all",
                    choices=["all", "bm25", "bkai", "aiteam", "bkai_ft"])
    args = ap.parse_args()

    config.ensure_dirs()
    if not config.ARTICLES_PATH.exists():
        raise SystemExit(
            "Chưa có data/articles.parquet. Chạy trước:\n"
            "    C:/Python314/python.exe scripts/01_prepare_data.py"
        )
    arts = pd.read_parquet(config.ARTICLES_PATH)
    print("=" * 70)
    print(f"BƯỚC 2: DỰNG CHỈ MỤC  (--model {args.model})")
    print("=" * 70)
    ch = lay_chunks(arts)

    can = ["bm25", "bkai", "aiteam"] if args.model == "all" else [args.model]
    for ten in can:
        if ten == "bm25":
            dung_bm25(arts)
        else:
            dung_dense(ten, ch)
    print("\nXong.")


if __name__ == "__main__":
    main()
