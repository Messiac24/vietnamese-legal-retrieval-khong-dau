"""Sinh hai notebook demo từ MỘT nguồn duy nhất.

Chạy:
    C:/Python314/python.exe notebooks/make_notebooks.py

Ghi ra:
    notebooks/demo.ipynb            bản chiếu khi bảo vệ, markdown gọn
    notebooks/demo_giai_thich.ipynb bản chú giải để đọc hiểu, markdown dày

Hai notebook chạy **cùng một mã**, chỉ khác phần giải thích. Viết tay hai tệp
riêng thì sớm muộn chúng lệch nhau, và bản chiếu sẽ chạy khác bản người đọc học.
"""
import json
from pathlib import Path

GOC = Path(__file__).resolve().parent

# Mỗi khối: (markdown bản chiếu, markdown bản chú giải, mã)
KHOI: list[tuple[str, str, str]] = []


def them(ngan: str, dai: str, ma: str = "") -> None:
    KHOI.append((ngan.strip(), dai.strip(), ma.strip("\n")))


them(
    """
# Demo: Tìm kiếm điều luật cho câu hỏi pháp luật tiếng Việt

Nhóm 09, môn Xử lý ngôn ngữ tự nhiên. GVHD: Đặng Văn Thìn.

### Nội dung

1. Môi trường
2. Dữ liệu sau kiểm toán
3. Bằng chứng rò rỉ
4. Vì sao phải chia đoạn
5. Ba tầng trên một câu hỏi thật
6. Giải thích: từ nào đã khớp
7. Bảng kết quả trên tập test
8. Hệ sai ở đâu
9. Thử một câu hỏi bất kỳ
""",
    """
# Bản chú giải: Tìm kiếm điều luật cho câu hỏi pháp luật tiếng Việt

Nhóm 09, môn Xử lý ngôn ngữ tự nhiên. GVHD: Đặng Văn Thìn.

Notebook này chạy **cùng một mã** với `demo.ipynb`, chỉ dày thêm phần giải thích.
Bản kia để chiếu khi bảo vệ, bản này để đọc hiểu.

Mỗi mục dưới đây trả lời ba câu: *đang làm gì*, *vì sao làm thế*, và *nếu làm khác
thì hỏng ở đâu*.

### Nội dung

1. Môi trường
2. Dữ liệu sau kiểm toán
3. Bằng chứng rò rỉ
4. Vì sao phải chia đoạn
5. Ba tầng trên một câu hỏi thật
6. Giải thích: từ nào đã khớp
7. Bảng kết quả trên tập test
8. Hệ sai ở đâu
9. Thử một câu hỏi bất kỳ
""",
)

them(
    "## 1. Môi trường",
    """
## 1. Môi trường

Máy có nhiều bản Python cùng đánh số 3.14.4 nhưng chỉ một bản đủ thư viện, nên
notebook phải chạy bằng kernel trỏ đúng vào `C:\\Python314\\python.exe`. Ô dưới in
ra đường dẫn thật để kiểm.

Card RTX 5060 Ti là kiến trúc Blackwell, cần wheel `cu130`. Nếu thấy hậu tố `+cpu`
thì mọi phần mã hóa sẽ chạy trên CPU và chậm hàng chục lần.
""",
    """
import sys, warnings
from pathlib import Path

ROOT = Path.cwd().parent if Path.cwd().name == "notebooks" else Path.cwd()
sys.path.insert(0, str(ROOT / "src"))
warnings.filterwarnings("ignore")

import pandas as pd
import torch

from vlr import (chunking, config, dense, explain, fusion, lexical, metrics,
                 pipeline, textnorm)

pd.set_option("display.max_colwidth", 68)
pd.set_option("display.width", 150)
DOC = {"encoding": "utf-8-sig"}   # CSV ghi kèm BOM để mở bằng Excel không vỡ chữ

print("Python     :", sys.version.split()[0], "|", sys.executable)
print("torch      :", torch.__version__, "| CUDA:", torch.cuda.is_available())
if torch.cuda.is_available():
    print("GPU        :", torch.cuda.get_device_name(0),
          f"| VRAM {torch.cuda.get_device_properties(0).total_memory / 1e9:.1f} GB")
print("Thư mục gốc:", ROOT)
""",
)

them(
    "## 2. Dữ liệu sau kiểm toán",
    """
## 2. Dữ liệu sau kiểm toán

Bộ gốc chỉ có `train` và `test`, **không có validation**. Đó là một cái bẫy: không
có val thì mọi tham số phải quét trên test, và con số công bố chính là con số đã
chỉnh cho vừa test.

Nhóm cắt val ra từ train theo **câu hỏi** chứ không theo cặp nhãn, `seed = 42`.
Chia theo cặp nhãn sẽ làm một câu hỏi có hai điều gold bị tách qua hai tập, và
cùng một câu được chấm ở cả hai nơi.

Chú ý cột `so_cap_qrel` khác `so_cau_hoi`: vài câu hỏi có nhiều hơn một điều luật
đúng.
""",
    """
qr = pd.read_parquet(config.QRELS_PATH)
qs = pd.read_parquet(config.QUERIES_PATH)
arts = pd.read_parquet(config.ARTICLES_PATH, columns=["article_id", "title", "text"])

print(f"{len(arts):,} điều luật  |  {len(qs):,} câu hỏi  |  {len(qr):,} cặp nhãn"
      .replace(",", "."))
display(pd.read_csv(config.AUDIT_DIR / "split_distribution.csv", **DOC))
""",
)

them(
    "## 3. Bằng chứng rò rỉ",
    """
## 3. Bằng chứng rò rỉ

Đây là phần quan trọng nhất của cả đồ án.

24 câu hỏi xuất hiện ở **cả** tệp train lẫn tệp test. Nếu chỉ dừng ở đó thì đơn
giản: loại khỏi train là xong. Nhưng khi đọc kỹ thì thấy chúng **không phải dòng
lặp**: với cả 24 trên 24 câu, tệp train chỉ sang một điều luật, tệp test chỉ sang
điều luật khác hẳn.

Cả hai đều là điều luật có thật và đều liên quan tới câu hỏi. Nghĩa là bộ nhãn
**không đầy đủ**, và mọi con số Recall trong báo cáo này là **cận dưới**: hệ có
thể trả về một điều luật đúng mà vẫn bị chấm sai chỉ vì người gán nhãn không liệt
kê điều đó.

Ô dưới còn chạy lại phép kiểm tự động: ba tập không được giao nhau câu hỏi nào.
Phép kiểm này nằm trong `scripts/01_prepare_data.py` dưới dạng `assert`, nên nó
chạy mỗi lần chuẩn bị dữ liệu chứ không chỉ ở đây.
""",
    """
xung = pd.read_csv(config.AUDIT_DIR / "conflicting_gold.csv", **DOC)
khac = int((xung["giong_nhau"].astype(str).str.lower() == "false").sum())
print(f"Câu hỏi nằm ở cả train và test: {len(xung)}")
print(f"Trong đó gold ở train KHÁC gold ở test: {khac} / {len(xung)}")
display(xung[["text", "gold_train", "gold_test"]].head(3))

ids = {s: set(g["query_id"]) for s, g in qr.groupby("split")}
print("Kiểm tra tự động, ba tập phải rời nhau:")
print(f"   train ∩ val  = {len(ids['train'] & ids['val'])}")
print(f"   train ∩ test = {len(ids['train'] & ids['test'])}")
print(f"   val   ∩ test = {len(ids['val'] & ids['test'])}")
""",
)

them(
    "## 4. Vì sao phải chia đoạn",
    """
## 4. Vì sao phải chia đoạn

PhoBERT nhận tối đa 256 token, khoảng 140 từ tiếng Việt. **61,1% điều luật dài hơn
thế.** Cắt cụt là vứt phần đuôi, mà đuôi điều luật thường là chỗ ghi mức phạt và
các trường hợp ngoại lệ, đúng thứ người dân hay hỏi.

Cách cắt của nhóm: theo **ranh giới khoản** trước, chỉ khi một khoản tự nó dài hơn
180 từ mới cắt bằng cửa sổ trượt chồng lấn 40 từ. Cắt giữa câu làm hỏng nghĩa;
ranh giới khoản là ranh giới ngữ nghĩa có sẵn của văn bản luật.

Mỗi đoạn đều được ghép **tiêu đề điều** ở đầu. Đoạn thứ ba của một điều mà mất
tiêu đề thì gần như vô nghĩa khi đứng riêng, vì không còn biết nó thuộc điều nào.
""",
    """
so_tu = arts["text"].str.split().str.len().fillna(0)
dai = arts[(so_tu > 400) & (so_tu < 700)].iloc[0]
doan = chunking.split_article(dai["title"], dai["text"],
                              config.CHUNK_WORDS, config.CHUNK_OVERLAP)
print(f"{dai['article_id']}  |  {dai['title']}")
print(f"{int(so_tu.loc[dai.name])} từ  ->  {len(doan)} đoạn\\n")
for i, d in enumerate(doan):
    print(f"  đoạn {i}: {d[:105]} ...")
""",
)

them(
    "## 5. Ba tầng trên một câu hỏi thật",
    """
## 5. Ba tầng trên một câu hỏi thật

Ba tầng chạy trên cùng một câu hỏi, để thấy chúng khác nhau ở đâu.

- **BM25** khớp đúng từ. Nó bắt được số hiệu văn bản, thuật ngữ luật, con số.
- **Bi-encoder** so nghĩa. Nó bắt được cách diễn đạt khác mà không cần trùng từ.
- **Hợp nhất** chuẩn hóa min-max điểm của hai tầng rồi cộng theo trọng số
  `alpha = 0,75`. Trọng số này quét trên tập **val**, không phải test.

Chú ý: chỉ mục BM25 được dựng lại tại chỗ với tham số đã chốt (`k1 = 0,6`,
`b = 0,9`), mất khoảng ba giây. Chỉ mục vector thì nạp từ đĩa, vì mã hóa lại
154.176 đoạn mất nhiều phút.

Mô hình dùng ở đây là **AITeamVN**, mô hình sạch. Mục 7 sẽ giải thích vì sao không
dùng mô hình có điểm cao hơn.

Câu hỏi chọn làm ví dụ đúng là một trong 17 ca mà hệ bị chấm sai. Mục 8 sẽ cho
thấy vì sao nhóm cho rằng ở ca này chính **nhãn** mới đáng ngờ, chứ không phải hệ.
""",
    """
CAU_HOI = "Không đăng ký tạm trú cho khách nước ngoài phạt bao nhiêu tiền?"

ts = pipeline.doc_tham_so()
print("Tham số đã chốt trên val:", {k: ts[k] for k in ("bm25", "dense", "weighted")})

idx_bm = lexical.BM25Index(pd.read_parquet(config.ARTICLES_PATH), **ts["bm25"])
idx_de = dense.DenseIndex.load(config.INDEX_DIR / ts["dense"]["mo_hinh"])

run_bm = idx_bm.search_tokens(textnorm.tokens(CAU_HOI), config.TOPK_FUSION)
run_de = idx_de.search(idx_de.encode_queries([CAU_HOI]), top_k=config.TOPK_FUSION,
                       pooling=ts["dense"]["gop_doan"], chunk_top=config.CHUNK_TOP)[0]
run_hop = fusion.weighted_sum(run_bm, run_de, ts["weighted"]["alpha"],
                              config.TOPK_FUSION)

TIEU_DE = dict(zip(arts["article_id"], arts["title"]))

def bang_top(run, ten, k=5):
    return pd.DataFrame({
        "tầng": ten,
        "hạng": range(1, k + 1),
        "điều luật": [a for a, _ in run[:k]],
        "tiêu đề": [TIEU_DE.get(a, "")[:52] for a, _ in run[:k]],
        "điểm": [round(s, 4) for _, s in run[:k]],
    })

print("\\nHỎI:", CAU_HOI)
display(pd.concat([bang_top(run_bm, "BM25"),
                   bang_top(run_de, "Ngữ nghĩa"),
                   bang_top(run_hop, "Hợp nhất")], ignore_index=True))
""",
)

them(
    "## 6. Giải thích: từ nào đã khớp",
    """
## 6. Giải thích: từ nào đã khớp

Đây là thứ tầng ngữ nghĩa **không** làm được. Nó chỉ đưa ra một con số cosine, còn
BM25 chỉ được đúng những từ đã khớp và mức đóng góp của từng từ.

Với một hệ tra cứu luật thì đây không phải chi tiết phụ. Người dùng cần kiểm tra
được vì sao hệ trả về điều này chứ không phải điều kia, nhất là khi họ sắp viện
dẫn nó.

Đóng góp tính xấp xỉ bằng `IDF(t)` nhân với phần hãm tần suất kiểu BM25. IDF cao
nghĩa là từ hiếm, mà từ hiếm mới là thứ phân biệt. Những từ như "quy_định" hay
"thực_hiện" xuất hiện ở gần như mọi điều luật nên IDF của chúng rất thấp.
""",
    """
IDF = explain.build_idf(list(pd.read_parquet(config.ARTICLES_PATH,
                                             columns=["tokens"])["tokens"]))
VAN_BAN = dict(zip(arts["article_id"], arts["text"]))

for ten, run in (("BM25", run_bm), ("Hợp nhất", run_hop)):
    aid = run[0][0]
    khop = explain.matched_terms(
        CAU_HOI, f"{TIEU_DE.get(aid, '')} {VAN_BAN.get(aid, '')}", IDF)
    print(f"[{ten}] hạng 1: {aid}  |  {TIEU_DE.get(aid, '')[:58]}")
    print(f"        từ khớp: {explain.to_chuoi(khop)}\\n")
""",
)

them(
    "## 7. Bảng kết quả trên tập test",
    """
## 7. Bảng kết quả trên tập test

Bảng này đọc **thẳng** từ `reports/eval/model_comparison.csv`, không con số nào gõ
tay. Chạy lại pipeline là bảng tự đổi theo.

Cột `nhiem_ban` là phần đáng chú ý nhất. Model card của
`bkai-foundation-models/vietnamese-bi-encoder` ghi rõ nó được huấn luyện trên
*"80% of the training set from the Legal Text Retrieval Zalo 2021 challenge"*. Tập
test của đồ án lại cắt ra từ đúng tập train đó, nên mô hình đã nhìn thấy phần lớn
câu hỏi test **kèm nhãn đúng**. Gọi nó là "zero-shot" là sai.

Vì vậy con số chính thức của đồ án lấy theo `AITeamVN`, mô hình có model card ghi
*"Our model was not trained on this dataset"*. Các dòng nhiễm bẩn vẫn để lại, để
thấy một con số benchmark bị thổi lên dễ thế nào.

Bảng thứ hai đo **cùng một thước**: tỷ lệ câu hỏi có ít nhất một điều gold trong
top-10. Không trộn với Recall@10 trung bình, vì câu hỏi có nhiều gold cho ra recall
lẻ và hai con số sẽ lệch nhau vài phần trăm.
""",
    """
mc = pd.read_csv(config.EVAL_DIR / "model_comparison.csv", **DOC)
display(mc[["he_thong", "recall@1", "recall@10", "mrr@10", "ndcg@10",
            "latency_p50_ms", "nhiem_ban"]])

print("Tỷ lệ câu hỏi có ít nhất một điều gold trong top-10:")
display(pd.read_csv(config.EVAL_DIR / "fusion_ceiling.csv", **DOC))

print("Đối chiếu chéo BM25 và tầng ngữ nghĩa (mô hình sạch):")
display(pd.read_csv(config.EVAL_DIR / "crossover.csv", **DOC))
""",
)

them(
    "## 8. Hệ sai ở đâu",
    """
## 8. Hệ sai ở đâu

Hệ sạch tốt nhất sai 17 trên 788 câu hỏi. Cả 17 ca đều được **đọc tay**, không
đoán. Nhãn nguyên nhân giữ ở tệp nguồn `docs/nhan_loi_doc_tay.csv` rồi ghép vào,
chứ không gõ thẳng vào tệp kết quả: gõ thẳng thì lần chạy sau mất sạch.

Nhóm lớn nhất là **thiếu ngữ cảnh pháp lý**: câu hỏi dùng lời nói thường, điều luật
dùng thuật ngữ, và không tầng nào bắc được cầu giữa hai bên.

Nhóm cuối là **nhãn gold đáng ngờ**: có hai ca mà điều luật hệ trả về sát câu hỏi
hơn cả điều được ghi trong nhãn. Nhóm không giấu chỗ này, vì nó củng cố nhận định
ở mục 3 rằng bộ nhãn không đầy đủ.
""",
    """
display(pd.read_csv(config.EVAL_DIR / "error_summary.csv", **DOC))

sai = pd.read_csv(config.EVAL_DIR / "error_taxonomy.csv", **DOC)
for _, h in sai[sai["nguyen_nhan"] == "sai_gold"].head(2).iterrows():
    print("HỎI      :", h["cau_hoi"])
    print("Nhãn ghi :", h["gold"], "|", str(h["gold_title"])[:62])
    print("Hệ trả về:", h["top1"], "|", str(h["top1_title"])[:62])
    print("Nhận xét :", h["ghi_chu"], "\\n")
""",
)

them(
    "## 9. Thử một câu hỏi bất kỳ",
    """
## 9. Thử một câu hỏi bất kỳ

Hàm `hoi()` gói lại toàn bộ đường chạy: tách từ, BM25, mã hóa câu hỏi, tìm trên
154.176 đoạn, gộp về điều, hợp nhất, rồi in kèm những từ đã khớp.

Đây cũng là phần dễ gây bất ngờ nhất khi bảo vệ. Nếu hệ trả sai thì **đừng giấu**:
17 ca sai đã được phân loại ở mục 8, và một ca sai mới chỉ xác nhận đúng những gì
đã báo cáo.
""",
    """
def hoi(cau_hoi: str, k: int = 5) -> pd.DataFrame:
    \"\"\"Chạy đủ ba tầng cho một câu hỏi và trả về bảng top-k.\"\"\"
    bm = idx_bm.search_tokens(textnorm.tokens(cau_hoi), config.TOPK_FUSION)
    de = idx_de.search(idx_de.encode_queries([cau_hoi]), top_k=config.TOPK_FUSION,
                       pooling=ts["dense"]["gop_doan"],
                       chunk_top=config.CHUNK_TOP)[0]
    hop = fusion.weighted_sum(bm, de, ts["weighted"]["alpha"], config.TOPK_FUSION)
    return pd.DataFrame({
        "hạng": range(1, k + 1),
        "điều luật": [a for a, _ in hop[:k]],
        "tiêu đề": [TIEU_DE.get(a, "")[:56] for a, _ in hop[:k]],
        "điểm": [round(s, 4) for _, s in hop[:k]],
        "từ khớp": [explain.to_chuoi(explain.matched_terms(
            cau_hoi, f"{TIEU_DE.get(a, '')} {VAN_BAN.get(a, '')}", IDF), 3)
            for a, _ in hop[:k]],
    })


hoi("Đi xe máy không đội mũ bảo hiểm bị phạt bao nhiêu tiền?")
""",
)

them(
    """
## Kết luận

| | |
|---|---|
| Hệ sạch tốt nhất | Trọng số (BM25 + AITeamVN), Recall@10 = 0,9772 |
| Hơn ngữ nghĩa thuần | 0,50 điểm phần trăm, tức 4 câu hỏi trên 788 |
| BM25 đóng góp riêng | 3 câu hỏi |
| Lý do vẫn giữ BM25 | nhanh hơn khoảng 700 lần, và giải thích được kết quả |

Bài học lớn nhất: chống rò rỉ dữ liệu không dừng ở việc chia lại tập. Mô hình tiền
huấn luyện mà mình đem dùng cũng có thể đã thấy tập test rồi.
""",
    """
## Kết luận

| | |
|---|---|
| Hệ sạch tốt nhất | Trọng số (BM25 + AITeamVN), Recall@10 = 0,9772 |
| Hơn ngữ nghĩa thuần | 0,50 điểm phần trăm, tức 4 câu hỏi trên 788 |
| BM25 đóng góp riêng | 3 câu hỏi |
| Lý do vẫn giữ BM25 | nhanh hơn khoảng 700 lần, và giải thích được kết quả |

Trả lời thẳng câu hỏi của đề tài: **hợp nhất có giúp, nhưng rất ít**. Không gọi
0,50 điểm phần trăm là đáng kể, nhất là khi mỗi cấu hình chỉ chạy một seed nên
nhóm không có cơ sở nói về biên độ nhiễu.

BM25 vẫn đáng giữ, nhưng vì hai lý do khác chứ không phải điểm số: nó nhanh hơn
khoảng 700 lần, và nó giải thích được vì sao một điều luật được trả về.

Bài học lớn nhất nằm ở chỗ khác hẳn: chống rò rỉ dữ liệu không dừng ở việc chia
lại tập. Mô hình bi-encoder tiếng Việt phổ biến nhất đã được huấn luyện trên chính
bộ dữ liệu này. Phải đọc model card trước khi tin một con số benchmark.
""",
)


def dung(chi_muc: int) -> dict:
    o = []
    for k, (ngan, dai, ma) in enumerate(KHOI):
        # nbformat 5 doi moi o co id on dinh
        o.append({"cell_type": "markdown", "id": f"md{k:02d}", "metadata": {},
                  "source": (dai if chi_muc else ngan).splitlines(keepends=True)})
        if ma:
            o.append({"cell_type": "code", "id": f"code{k:02d}",
                      "execution_count": None, "metadata": {},
                      "outputs": [], "source": ma.splitlines(keepends=True)})
    return {
        "cells": o,
        "metadata": {
            "kernelspec": {"display_name": "Python 3.14 (do an XLNNTN)",
                           "language": "python", "name": "python3"},
            "language_info": {"name": "python", "version": "3.14.4"},
        },
        "nbformat": 4,
        "nbformat_minor": 5,
    }


def main() -> None:
    for ten, chi_muc in (("demo.ipynb", 0), ("demo_giai_thich.ipynb", 1)):
        d = GOC / ten
        d.write_text(json.dumps(dung(chi_muc), ensure_ascii=False, indent=1),
                     encoding="utf-8")
        print(f"  {ten}  ({len(dung(chi_muc)['cells'])} ô)")


if __name__ == "__main__":
    print("Sinh notebook:")
    main()
