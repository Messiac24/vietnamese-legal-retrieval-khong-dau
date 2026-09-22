"""Sinh notebook demo, chạy được trên Kaggle lẫn trên máy.

    python notebooks/make_notebooks.py      -> notebooks/demo.ipynb
"""
import json
from pathlib import Path

O = []


def md(s):
    O.append({"cell_type": "markdown", "metadata": {}, "source": s.strip("\n")})


def ma(s):
    O.append({"cell_type": "code", "metadata": {}, "execution_count": None, "outputs": [],
              "source": s.strip("\n")})


md("""
# Demo: tìm kiếm điều luật cho câu hỏi gõ thiếu dấu

Nhóm 09, môn Xử lý ngôn ngữ tự nhiên.

Trên Kaggle: thêm dataset `vlr-demo`, bật Internet, chọn GPU T4. Chạy ô 1 và ô 2 trước
giờ trình bày (khoảng 2 phút, lần đầu phải tải mô hình AITeamVN), các ô sau chạy trực tiếp.
""")

md("## 1. Môi trường")
ma("""
import glob, os, subprocess, sys, time
from pathlib import Path

TREN_KAGGLE = Path("/kaggle/input").exists()
if TREN_KAGGLE:
    subprocess.run([sys.executable, "-m", "pip", "install", "-q", "bm25s", "pyvi"], check=True)
    tim = glob.glob("/kaggle/input/**/src/vlr/config.py", recursive=True)
    assert tim, "Chưa thêm dataset vlr-demo vào notebook"
    GOC = Path(tim[0]).parents[2]
else:
    GOC = Path.cwd().parent if Path.cwd().name == "notebooks" else Path.cwd()
    os.environ["HF_HUB_OFFLINE"] = "1"   # máy nhóm đã có mô hình trong cache
sys.path.insert(0, str(GOC / "src"))

import pandas as pd
import torch
pd.set_option("display.max_colwidth", 80)
print("Thư mục dữ liệu:", GOC)
print("GPU:", torch.cuda.get_device_name(0) if torch.cuda.is_available() else "không có, chạy trên CPU")
""")

md("## 2. Nạp chỉ mục và mô hình")
ma("""
from vlr import config, fusion, textnorm, tra_cuu

t0 = time.time()
tro_ly = tra_cuu.TroLyTraCuu()
tro_ly.de.encode_queries(["khởi động"])   # nạp mô hình ngữ nghĩa ngay, lúc demo khỏi chờ
K = config.TOPK_FUSION
qs = pd.read_parquet(config.QUERIES_PATH).set_index("query_id")["text"]
qr = pd.read_parquet(config.QRELS_PATH)
gold = qr.groupby("query_id")["article_id"].apply(set).to_dict()
DOC = {"encoding": "utf-8-sig"}
nghin = lambda x: f"{x:,}".replace(",", ".")
print(f"Xong sau {time.time() - t0:.0f} giây: {nghin(len(tro_ly.tieu_de))} điều luật, "
      f"{nghin(len(tro_ly.de.chunk_ids))} đoạn")
""")

md("""
## 3. Dữ liệu: câu hỏi trùng giữa train và test

Bộ gốc không có val nên nhóm cắt val ra từ train. 24 câu nằm ở cả train và test đều
mang nhãn khác nhau ở hai tệp.
""")
ma("""
display(pd.read_csv(config.AUDIT_DIR / "split_distribution.csv", **DOC))
xung = pd.read_csv(config.AUDIT_DIR / "conflicting_gold.csv", **DOC)
print(f"Câu trùng mã giữa train và test: {len(xung)}, "
      f"nhãn khác nhau: {(xung['giong_nhau'].astype(str).str.lower() == 'false').sum()}")
display(xung[["text", "gold_train", "gold_test"]].head(3))

ids = {s: set(g["query_id"]) for s, g in qr.groupby("split")}
print("Sau khi chia lại, số câu chung giữa các tập:",
      len(ids["train"] & ids["val"]), len(ids["train"] & ids["test"]), len(ids["val"] & ids["test"]))
""")

md("""
## 4. Một câu hỏi qua ba tầng

BM25, tầng ngữ nghĩa và hợp nhất, mỗi tầng lấy 3 điều đầu.
""")
ma("""
def ba_tang(cau, k=3):
    bm = tro_ly.bm.search_tokens(textnorm.tokens(cau), K)
    de = tro_ly.de.search(tro_ly.de.encode_queries([cau]), top_k=K,
                          pooling=tro_ly.ts["dense"]["gop_doan"], chunk_top=config.CHUNK_TOP)[0]
    hop = fusion.weighted_sum(bm, de, tro_ly.ts["weighted"]["alpha"], K)
    dong = []
    for ten, ds in (("BM25", bm), ("Ngữ nghĩa", de), ("Hợp nhất", hop)):
        for i, (aid, diem) in enumerate(ds[:k], 1):
            dong.append((ten, i, aid, tro_ly.tieu_de[aid][:70], round(diem, 3)))
    return pd.DataFrame(dong, columns=["tầng", "hạng", "điều luật", "tiêu đề", "điểm"])

cau = "Người lao động nghỉ việc có được trả lương những ngày chưa nghỉ phép không?"
display(ba_tang(cau))
""")

md("""
## 5. Câu hỏi gõ không dấu

Bốn câu thật trong tập test. Cột số là hạng của điều luật đúng trong kết quả hợp nhất,
trống nghĩa là không có trong top-100.
""")
ma("""
from vlr import diacritics

def hang_dung(cau, dung):
    bm = tro_ly.bm.search_tokens(textnorm.tokens(cau), K)
    de = tro_ly.de.search(tro_ly.de.encode_queries([cau]), top_k=K,
                          pooling=tro_ly.ts["dense"]["gop_doan"], chunk_top=config.CHUNK_TOP)[0]
    hop = fusion.weighted_sum(bm, de, tro_ly.ts["weighted"]["alpha"], K)
    return next((i for i, (a, _) in enumerate(hop, 1) if a in dung), None)

vi_du = ["01191d25556225e3961e0b4a76567c07", "03d587dd91c8f4c57fc862e413e3b461",
         "07aea7f0de54d5a441e6bf38a8e20039", "0825a491aab92827292a50ea01cfe61a"]
dong = []
for q in vi_du:
    goc = qs[q]
    khong = diacritics.bo_dau(goc)
    ph = tro_ly.ph.phuc_hoi(khong)
    dong.append((khong, ph, hang_dung(goc, gold[q]), hang_dung(khong, gold[q]), hang_dung(ph, gold[q])))
bang = pd.DataFrame(dong, columns=["gõ không dấu", "sau phục hồi", "câu gốc", "không dấu", "phục hồi"])
display(bang.astype({c: "Int64" for c in ["câu gốc", "không dấu", "phục hồi"]}))
""")

md("Phục hồi dấu cho vài kiểu gõ: không dấu, dấu một nửa, viết hoa, và một câu có từ nói thường mà luật không dùng.")
ma("""
for s in ["di xe may khong doi mu bao hiem bi phat bao nhieu tien",
          "đi xe may không đội mu bao hiem",
          "NGHI VIEC KHONG BAO TRUOC CO DUOC TRO CAP KHONG",
          "tai xe uong ruou bi phat the nao"]:
    t0 = time.perf_counter()
    kq = tro_ly.ph.phuc_hoi(s)
    print(f"{s}\\n  -> {kq}   ({1000 * (time.perf_counter() - t0):.1f} ms)\\n")
""")

md("Kết quả trên cả 788 câu test, đọc từ `reports/eval/khong_dau.csv`:")
ma("""
kq = pd.read_csv(config.EVAL_DIR / "khong_dau.csv", **DOC)
kq = kq[kq["he_thong"] == "Hợp nhất"][["dieu_kien", "cach_xu_ly", "recall@1", "recall@10"]]
display(kq.reset_index(drop=True))
""")

md("""
## 6. Trợ lý tra cứu

Phục hồi dấu, tìm bằng hệ hợp nhất, rồi trích nguyên văn khoản luật. Không sinh chữ.
""")
ma("""
print(tro_ly.tra_loi("Nguoi lao dong nghi viec co duoc tra luong nhung ngay chua nghi phep khong?"))
""")
md("Câu nằm ngoài kho luật: trợ lý vẫn trả về một điều, nhưng in kèm cảnh báo.")
ma("""
print(tro_ly.tra_loi("hom nay troi dep khong"))
""")
md("Gõ câu hỏi khác vào đây rồi chạy lại ô:")
ma("""
cau_hoi = "do tuoi toi thieu duoc ket hon la bao nhieu"
print(tro_ly.tra_loi(cau_hoi))
""")

nb = {"cells": O, "metadata": {
    "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
    "language_info": {"name": "python"}}, "nbformat": 4, "nbformat_minor": 5}
ra = Path(__file__).resolve().parent / "demo.ipynb"
ra.write_text(json.dumps(nb, ensure_ascii=False, indent=1), encoding="utf-8")
print(ra)
