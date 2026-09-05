"""Ghép các tầng lại thành một lượt truy hồi hoàn chỉnh.

Mô-đun này tồn tại để hai script `04_tune.py` và `05_evaluate.py` dùng chung
đúng một đường chạy. Nếu để mỗi script tự ghép lấy, chỉ cần một chỗ lệch nhau
là tham số chọn trên val không còn là tham số dùng khi chấm test, và toàn bộ
phần đối chứng mất giá trị.
"""
import json

import pandas as pd

from vlr import config, dense, fusion, lexical, metrics, textnorm


def load_split(split: str) -> tuple[dict[str, set], dict[str, str]]:
    """Trả về (gold theo câu hỏi, nội dung câu hỏi) cho một tập.

    Chỉ đọc đúng tập được yêu cầu. `04_tune.py` gọi với 'val' và có assert
    riêng để bảo đảm không chạm vào 'test'.
    """
    if split not in ("train", "val", "test"):
        raise ValueError(f"split phải là train, val hoặc test, nhận {split!r}")
    qr = pd.read_parquet(config.QRELS_PATH)
    qs = pd.read_parquet(config.QUERIES_PATH)
    phan = qr[qr["split"] == split]
    if phan.empty:
        raise ValueError(f"Tập {split!r} rỗng. Chạy lại scripts/01_prepare_data.py")
    gold = phan.groupby("query_id")["article_id"].apply(set).to_dict()
    text = dict(zip(qs["query_id"], qs["text"]))
    return gold, {q: text[q] for q in gold}


def gold_mo_rong(gold: dict[str, set]) -> dict[str, set]:
    """Mở rộng mỗi gold thành cả nhóm điều luật trùng nguyên văn.

    Chỉ dùng cho phân tích độ nhạy, KHÔNG dùng cho con số chính thức: 719 trên
    719 nhóm trùng đều vắt qua nhiều văn bản khác nhau, nên trả về một điều
    cùng chữ ở Thông tư khác vẫn là trích dẫn sai.
    """
    arts = pd.read_parquet(config.ARTICLES_PATH, columns=["article_id", "dup_group"])
    theo_nhom: dict[str, list[str]] = {}
    for aid, g in zip(arts["article_id"], arts["dup_group"]):
        theo_nhom.setdefault(g, []).append(aid)
    cua_dieu = dict(zip(arts["article_id"], arts["dup_group"]))
    return {
        q: {x for a in g for x in theo_nhom.get(cua_dieu.get(a, ""), [a])}
        for q, g in gold.items()
    }


def bm25_runs(idx: lexical.BM25Index, text: dict[str, str], top_k: int) -> dict:
    """Chạy BM25 cho mọi câu hỏi. Tách từ một lần rồi dùng lại."""
    return {
        q: idx.search_tokens(textnorm.tokens(t), top_k) for q, t in text.items()
    }


def dense_runs(idx: dense.DenseIndex, text: dict[str, str], top_k: int,
               pooling: str) -> dict:
    """Chạy tầng ngữ nghĩa cho mọi câu hỏi, theo lô để dùng hết GPU."""
    ids = list(text)
    vecs = idx.encode_queries([text[q] for q in ids])
    kq = idx.search(vecs, top_k=top_k, pooling=pooling,
                    chunk_top=config.CHUNK_TOP)
    return dict(zip(ids, kq))


def chi_diem(runs: dict) -> dict[str, list[str]]:
    """Bỏ điểm, chỉ giữ thứ tự article_id, để đưa vào hàm chỉ số."""
    return {q: [a for a, _ in r] for q, r in runs.items()}


def recall_at(runs: dict, gold: dict, k: int) -> float:
    xep = chi_diem(runs)
    return sum(metrics.recall_at_k(xep[q], gold[q], k) for q in xep) / len(xep)


def hop_nhat_rrf(bm: dict, de: dict, k: int, top_k: int) -> dict:
    return {q: fusion.rrf([bm.get(q, []), de.get(q, [])], k, top_k)
            for q in set(bm) | set(de)}


def hop_nhat_alpha(bm: dict, de: dict, alpha: float, top_k: int) -> dict:
    return {q: fusion.weighted_sum(bm.get(q, []), de.get(q, []), alpha, top_k)
            for q in set(bm) | set(de)}


def luu_tham_so(d: dict) -> None:
    duong_dan = config.EVAL_DIR / "chosen_params.json"
    duong_dan.write_text(json.dumps(d, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"    -> {duong_dan.relative_to(config.ROOT)}")


def doc_tham_so() -> dict:
    duong_dan = config.EVAL_DIR / "chosen_params.json"
    if not duong_dan.exists():
        raise FileNotFoundError(
            "Chưa có reports/eval/chosen_params.json. Chạy trước:\n"
            "    C:/Python314/python.exe scripts/04_tune.py"
        )
    return json.loads(duong_dan.read_text(encoding="utf-8"))
