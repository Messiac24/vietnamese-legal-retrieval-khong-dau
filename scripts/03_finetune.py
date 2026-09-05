"""Bước 3: huấn luyện tiếp bi-encoder bkai trên tập train đã dọn.

Chạy:
    C:/Python314/python.exe scripts/03_finetune.py

Sinh ra:
    runs/bkai_ft/                        mô hình đã huấn luyện
    runs/bkai_ft/history.csv             chỉ số theo epoch
    runs/bkai_ft/train_config.json       cấu hình thật đã chạy
    reports/audit/finetune_data_check.csv  bằng chứng không rò rỉ val và test

Hàm mất mát là MultipleNegativesRankingLoss: trong mỗi lô, đoạn dương của câu
hỏi này chính là đoạn âm của câu hỏi khác. Nhờ vậy một lô 32 câu hỏi cho ra 32
bài toán phân biệt 1 đúng trên 32 lựa chọn mà không cần gán nhãn thêm. Thêm 4
đoạn âm khó lấy từ BM25 để mô hình phải phân biệt những điều luật trông giống
nhau, chứ không chỉ những điều ngẫu nhiên chẳng liên quan.

Việc chọn giữa mô hình gốc và mô hình này KHÔNG diễn ra ở đây: script chỉ huấn
luyện. So sánh nằm ở bước 4, đo trên tập val.
"""
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import pandas as pd

from vlr import config, lexical, textnorm

SO_AM = config.FT_HARD_NEGATIVES


def kiem_tra_ro_ri(qr: pd.DataFrame) -> set[str]:
    """Chặn đường val và test lọt vào dữ liệu huấn luyện, và ghi lại bằng chứng."""
    theo_tap = {t: set(g["query_id"]) for t, g in qr.groupby("split")}
    tr = theo_tap.get("train", set())
    va = theo_tap.get("val", set())
    te = theo_tap.get("test", set())
    bang = pd.DataFrame([
        {"tap": "train", "so_query": len(tr),
         "giao_voi_val": len(tr & va), "giao_voi_test": len(tr & te)},
        {"tap": "val", "so_query": len(va),
         "giao_voi_val": len(va), "giao_voi_test": len(va & te)},
        {"tap": "test", "so_query": len(te),
         "giao_voi_val": len(te & va), "giao_voi_test": len(te)},
    ])
    bang.to_csv(config.AUDIT_DIR / "finetune_data_check.csv", **config.CSV_KW)
    print(bang.to_string(index=False))
    assert not (tr & va), "train giao val"
    assert not (tr & te), "train giao test"
    return tr


def chon_doan_duong(gold_chunks: list[tuple[str, str]], q_toks: set[str]) -> str:
    """Chọn đoạn nào của điều luật gold làm mẫu dương.

    Điều luật gold có thể dài nhiều đoạn, mà chỉ một đoạn thật sự trả lời câu
    hỏi. Lấy đoạn trùng nhiều từ nhất với câu hỏi. Đây là phép xấp xỉ rẻ tiền,
    không phải nhãn thật, nên có thể chọn nhầm; nhưng dạy mô hình bằng một đoạn
    gần đúng vẫn hơn là dạy bằng đoạn đầu tiên bất kể nội dung.
    """
    tot, diem_tot = gold_chunks[0][1], -1
    for _, van_ban in gold_chunks:
        diem = len(q_toks & set(van_ban.split()))
        if diem > diem_tot:
            tot, diem_tot = van_ban, diem
    return tot


def main() -> None:
    t0 = time.perf_counter()
    config.ensure_dirs()
    print("=" * 70)
    print("BƯỚC 3: FINE-TUNE BI-ENCODER")
    print("=" * 70)

    seg_path = config.DATA_DIR / "chunks_segmented.parquet"
    if not seg_path.exists():
        raise SystemExit(
            "Chưa có data/chunks_segmented.parquet. Chạy trước:\n"
            "    C:/Python314/python.exe scripts/02_build_index.py --model bkai"
        )

    qr = pd.read_parquet(config.QRELS_PATH)
    qs = pd.read_parquet(config.QUERIES_PATH)
    arts = pd.read_parquet(config.ARTICLES_PATH, columns=["article_id", "dup_group"])
    ch = pd.read_parquet(config.CHUNKS_PATH)
    seg = pd.read_parquet(seg_path)

    print("\n[1/4] Kiểm tra rò rỉ")
    tr_ids = kiem_tra_ro_ri(qr)

    print("\n[2/4] Dựng cặp huấn luyện")
    van_ban_doan = dict(zip(seg["chunk_id"], seg["text"]))
    doan_cua_dieu: dict[str, list[tuple[str, str]]] = {}
    for cid, aid in zip(ch["chunk_id"], ch["article_id"]):
        doan_cua_dieu.setdefault(aid, []).append((cid, van_ban_doan[cid]))

    nhom_cua_dieu = dict(zip(arts["article_id"], arts["dup_group"]))
    text_cua_query = dict(zip(qs["query_id"], qs["text"]))
    gold_cua_query = (qr[qr["split"] == "train"]
                      .groupby("query_id")["article_id"].apply(list).to_dict())

    idx_bm = lexical.BM25Index.load(config.INDEX_DIR / "bm25")
    cot = {"anchor": [], "positive": [], **{f"negative_{i}": [] for i in range(1, SO_AM + 1)}}
    bo_qua = 0
    for n, (qid, gold) in enumerate(gold_cua_query.items(), 1):
        cau_hoi = text_cua_query[qid]
        q_toks = set(textnorm.tokens(cau_hoi))
        dieu_gold = gold[0]
        if dieu_gold not in doan_cua_dieu:
            bo_qua += 1
            continue
        duong = chon_doan_duong(doan_cua_dieu[dieu_gold], q_toks)

        cam = {nhom_cua_dieu.get(g) for g in gold}
        am = []
        for aid, _ in idx_bm.search_tokens(list(q_toks), SO_AM * 5):
            if nhom_cua_dieu.get(aid) in cam or aid not in doan_cua_dieu:
                continue
            am.append(doan_cua_dieu[aid][0][1])
            if len(am) == SO_AM:
                break
        if len(am) < SO_AM:
            bo_qua += 1
            continue

        cot["anchor"].append(textnorm.segment(cau_hoi))
        cot["positive"].append(duong)
        for i, a in enumerate(am, 1):
            cot[f"negative_{i}"].append(a)
        if n % 500 == 0:
            print(f"    {n}/{len(gold_cua_query)}", flush=True)

    print(f"    dựng được {len(cot['anchor'])} cặp, bỏ qua {bo_qua} câu hỏi "
          f"(thiếu đoạn hoặc thiếu đủ {SO_AM} âm khó)")
    assert len(cot["anchor"]) > 500, "quá ít dữ liệu huấn luyện, xem lại bước dựng cặp"

    print("\n[3/4] Huấn luyện")
    import torch
    from datasets import Dataset
    from sentence_transformers import (SentenceTransformer,
                                       SentenceTransformerTrainer,
                                       SentenceTransformerTrainingArguments, losses)

    ds = Dataset.from_dict(cot)
    model = SentenceTransformer(config.BKAI_MODEL, device="cuda")
    model.max_seq_length = config.BKAI_MAX_LEN
    loss = losses.MultipleNegativesRankingLoss(model)

    dau_ra = config.BKAI_FT_DIR
    args = SentenceTransformerTrainingArguments(
        output_dir=str(dau_ra / "checkpoints"),
        num_train_epochs=config.FT_EPOCHS,
        per_device_train_batch_size=config.FT_BATCH,
        learning_rate=config.FT_LR,
        warmup_ratio=config.FT_WARMUP_RATIO,
        bf16=torch.cuda.is_available(),
        logging_steps=20,
        save_strategy="no",
        report_to=[],
        seed=config.SEED,
    )
    trainer = SentenceTransformerTrainer(
        model=model, args=args, train_dataset=ds, loss=loss
    )
    ket_qua = trainer.train()

    print("\n[4/4] Lưu mô hình")
    model.save(str(dau_ra))
    lich_su = pd.DataFrame(trainer.state.log_history)
    lich_su.to_csv(dau_ra / "history.csv", **config.CSV_KW)
    (dau_ra / "train_config.json").write_text(
        json.dumps({
            "mo_hinh_goc": config.BKAI_MODEL,
            "so_cap": len(ds),
            "so_am_kho": SO_AM,
            "epochs": config.FT_EPOCHS,
            "batch": config.FT_BATCH,
            "learning_rate": config.FT_LR,
            "warmup_ratio": config.FT_WARMUP_RATIO,
            "seed": config.SEED,
            "train_loss_cuoi": round(float(ket_qua.training_loss), 5),
            "thoi_gian_phut": round((time.perf_counter() - t0) / 60, 1),
        }, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"    -> {dau_ra.relative_to(config.ROOT)}")
    print(f"    loss cuối: {ket_qua.training_loss:.5f}")
    print(f"\nTổng thời gian: {(time.perf_counter() - t0) / 60:.1f} phút")
    print("Bước tiếp theo:\n"
          "    C:/Python314/python.exe scripts/02_build_index.py --model bkai_ft")


if __name__ == "__main__":
    main()
