# Tìm kiếm điều luật cho câu hỏi pháp luật tiếng Việt

Kết hợp tìm theo từ khóa và tìm theo ngữ nghĩa, trên 61.425 điều luật Việt Nam.

Môn: Xử lý ngôn ngữ tự nhiên. GVHD: Đặng Văn Thìn.
Nhóm 09: Lê Hoàng Lộc (25210293), Lê Thị Tuấn Anh (25210250), Đoàn Mậu Thiên Thư (25210341).

Thiết kế chi tiết: [`docs/specs/2026-09-05-vietnamese-legal-retrieval-design.md`](docs/specs/2026-09-05-vietnamese-legal-retrieval-design.md)

## Kết quả một dòng

Trên 788 câu hỏi test, hệ lai tốt nhất **không dùng mô hình nhiễm bẩn** đạt
Recall@10 = 0,9772 và MRR@10 = 0,8619. Nhưng nó chỉ hơn tầng ngữ nghĩa dùng một
mình **0,50 điểm phần trăm, tức 4 câu hỏi trên 788**, và riêng BM25 chỉ cứu được
**3 câu**. Có cải thiện, nhưng rất nhỏ. Đó là kết luận thật của đồ án, không phải
kết luận mong muốn.

Phát hiện đáng giá hơn nằm ở chỗ khác: mô hình bi-encoder tiếng Việt phổ biến
nhất đã được huấn luyện trên chính bộ dữ liệu này, nên mọi con số "zero-shot" của
nó trên benchmark này đều bị thổi lên.

## 1. Cài đặt

Python 3.14.4 tại `C:\Python314\python.exe`. GPU NVIDIA RTX 5060 Ti 16 GB.

```bash
C:/Python314/python.exe -m pip install -r requirements.txt
```

Card 50-series là kiến trúc Blackwell, bắt buộc wheel `cu130`. Kiểm tra:

```bash
C:/Python314/python.exe -c "import torch; print(torch.__version__, torch.cuda.is_available())"
```

Phải thấy `2.12.0+cu130 True`.

## 2. Dữ liệu

Bộ dữ liệu **không** nằm trong kho, script tự tải:

> Zalo AI Challenge 2021, hạng mục Legal Text Retrieval, bản BEIR trên HuggingFace
> `GreenNode/zalo-ai-legal-text-retrieval-vn`, giấy phép MIT.

| Thành phần | Số lượng |
|---|---|
| Điều luật | 61.425 |
| Văn bản quy phạm pháp luật | 3.271 |
| Câu hỏi | 3.196 id duy nhất (tệp gốc có 3.298 dòng) |
| Độ dài điều luật | trung vị 183 từ, p90 592 từ, dài nhất 55.368 từ |

## 3. Chạy lại toàn bộ

Chạy từ thư mục gốc, theo đúng thứ tự:

```bash
C:/Python314/python.exe scripts/01_prepare_data.py
C:/Python314/python.exe scripts/02_build_index.py --model all
C:/Python314/python.exe scripts/03_finetune.py
C:/Python314/python.exe scripts/02_build_index.py --model bkai_ft
C:/Python314/python.exe scripts/04_tune.py
C:/Python314/python.exe scripts/05_evaluate.py
C:/Python314/python.exe scripts/06_error_analysis.py
```

Thời gian thật đã đo trên RTX 5060 Ti:

| Bước | Thời gian |
|---|---|
| Chuẩn bị và kiểm toán, gồm tách từ 61k điều bằng pyvi | 5,5 phút |
| Chỉ mục BM25 | 2,8 giây |
| Mã hóa 154.176 đoạn bằng bkai (PhoBERT base) | 5,0 phút |
| Mã hóa 154.176 đoạn bằng AITeamVN (XLM-R large) | 11,1 phút |
| Fine-tune bkai | 2,9 phút |
| Quét tham số trên val | 1,7 phút |
| Chấm điểm trên test | 1,3 phút |

Kiểm thử:

```bash
C:/Python314/python.exe -m pytest -q
```

## 4. Vì sao phải kiểm toán lại bộ dữ liệu

Đây là phần cốt lõi, không phải bước phụ. Bộ dữ liệu đã công bố, đã được đưa vào
MTEB, nhưng vẫn có sáu vấn đề đo được. Mỗi vấn đề để lại một tệp bằng chứng
trong `reports/audit/`.

| # | Phát hiện | Con số | Tệp bằng chứng |
|---|---|---|---|
| 1 | Câu hỏi lặp dòng trong `queries.jsonl` | 93 id, 195 dòng, 0 xung đột nội dung | `duplicate_queries.csv` |
| 2 | Câu hỏi nằm ở **cả** train và test | 24 id, cộng 2 câu gần trùng | `query_overlap.csv` |
| 3 | **Nhãn mâu thuẫn** ở 24 câu đó | 24 trên 24 câu có gold train khác gold test | `conflicting_gold.csv` |
| 4 | Điều luật trùng nguyên văn | 719 nhóm, 1.467 điều (2,39%), 0 nhóm nằm trong cùng một văn bản | `duplicate_articles.csv` |
| 5 | Văn bản bị tách đôi vì **dấu tiếng Việt** | 4 nhóm, 8 mã, 780 điều | `duplicate_docs_diacritics.csv` |
| 6 | Điều luật rỗng, chỉ còn tiêu đề | 357 điều (0,58%) | `empty_articles.csv` |

Phát hiện 3 là nặng nhất. Ví dụ câu "Bị thương tật 25%, cơ quan nhà nước có khởi
tố không?": tệp train chỉ sang `12/2017/qh14+1`, tệp test chỉ sang
`101/2015/qh13+155`. Cả hai đều là điều luật có thật và đều liên quan. Nghĩa là
bộ nhãn **không đầy đủ**, và mọi con số Recall công bố ở đây đều là **cận dưới**.

Phát hiện 5 giải thích một phần lớn phát hiện 4: `155/2020/nd-cp` và
`155/2020/nđ-cp` là cùng một Nghị định nằm dưới hai mã, mỗi mã đủ 310 điều. Phép
băm SHA1 bắt được 390 trên 390 cặp, tức 26,6% tổng số điều trùng chỉ đến từ bốn
văn bản này.

Bộ gốc **không có tập validation**. Không có val thì mọi tham số phải quét trên
test, và con số công bố chính là con số đã chỉnh cho vừa test. Pipeline vì thế
cắt val ra từ train, `seed=42`:

| Tập | Câu hỏi | Cặp qrel |
|---|---|---|
| train | 1.925 | 1.986 |
| val | 481 | 492 |
| test | 788 | 793 |

Tập test giữ **nguyên vẹn** 793 cặp của ban tổ chức. Bản dựng đầu tiên của
script từng gộp nhầm các dòng train của 24 câu chồng lấn vào test, làm test
phình lên 818 cặp; lỗi này bị bắt khi đối chiếu lại với số dòng của tệp gốc, và
script nay có `assert` chặn.

## 5. Mô hình công khai đã thấy trước dữ liệu này

Đây là phát hiện quan trọng nhất của đồ án, và nó không nằm trong dữ liệu mà nằm
trong mô hình.

Model card của `bkai-foundation-models/vietnamese-bi-encoder` ghi rõ mô hình được
huấn luyện trên *"80% of the training set from the Legal Text Retrieval Zalo 2021
challenge"*. Tập test của đồ án lại được cắt ra từ đúng tập train đó. Nghĩa là mô
hình đã nhìn thấy phần lớn câu hỏi test **kèm nhãn đúng**. Gọi nó là "zero-shot"
là sai.

Model card của `AITeamVN/Vietnamese_Embedding` ghi ngược lại: *"Our model was not
trained on this dataset"*. Đồ án vì thế lấy AITeamVN làm mô hình **sạch** cho con
số chính thức, và vẫn công bố bkai kèm nhãn nhiễm bẩn để thấy chênh lệch.

Bài học rút ra: chống rò rỉ dữ liệu không dừng ở việc chia lại tập. Phải kiểm cả
dữ liệu huấn luyện của mô hình tiền huấn luyện mà mình đem dùng.

## 6. Kiến trúc

```
câu hỏi
   |
   +--> tách từ pyvi --> BM25 trên 61.425 điều luật ------> top-100
   |                                                           |
   +--> bi-encoder --> 154.176 đoạn --> gộp max về điều ----> top-100
                                                               |
                                       hợp nhất: RRF hoặc tổng có trọng số
                                                               |
                                              xếp hạng + từ khóa đã khớp
```

Tách từ quan trọng với tiếng Việt: "bằng lái xe" là một khái niệm, tách theo
khoảng trắng thì "bằng" khớp nhầm với "bằng chứng".

Chia đoạn là bắt buộc: 46,2% điều luật dài hơn 200 từ, và **61,1% vượt trần 256
token của PhoBERT** (khoảng 140 từ tiếng Việt). Cắt cụt là vứt phần đuôi, mà đuôi
điều luật thường là chỗ ghi mức phạt và ngoại lệ.

Hai bộ mã hóa ăn **cùng một bộ 154.176 đoạn**, chỉ khác khâu tiền xử lý mà kiến
trúc của chúng đòi hỏi, nên biến duy nhất giữa hai lượt chạy là bộ mã hóa.

Tham số chốt trên val, không đụng test: `k1 = 0,6`, `b = 0,9`, gộp đoạn `max`,
`alpha = 0,75`, `RRF k = 10`.

## 7. Kết quả trên tập test

788 câu hỏi, gold gốc. Đọc từ [`reports/eval/model_comparison.csv`](reports/eval/model_comparison.csv).

| Hệ thống | R@1 | R@10 | MRR@10 | nDCG@10 | Độ trễ p50 | Nhiễm bẩn |
|---|---|---|---|---|---|---|
| BM25 | 0,4740 | 0,8522 | 0,6025 | 0,6625 | **0,5 ms** | không |
| Dense AITeamVN | 0,7811 | 0,9721 | 0,8595 | 0,8869 | 351 ms | không |
| RRF (BM25 + AITeamVN) | 0,6701 | 0,9670 | 0,7894 | 0,8330 | 352 ms | không |
| **Trọng số (BM25 + AITeamVN)** | **0,7824** | **0,9772** | **0,8619** | **0,8900** | 352 ms | không |
| Dense bkai | 0,8204 | 0,9746 | 0,8865 | 0,9082 | 265 ms | có |
| Dense bkai fine-tune | 0,8141 | 0,9784 | 0,8841 | 0,9073 | 261 ms | có |
| Trọng số (BM25 + bkai fine-tune) | 0,8452 | 0,9860 | 0,9070 | 0,9264 | 261 ms | có |

Đọc bảng này cẩn thận. Bốn dòng cuối trông đẹp hơn nhưng chúng dùng mô hình đã
thấy dữ liệu test khi huấn luyện, nên không so được với bốn dòng trên.

## 8. Hợp nhất có thật sự giúp không

Câu hỏi trung tâm của đề tài. Trả lời bằng bảng bốn ô, tính ở top-10, với mô hình
sạch. Đọc từ [`reports/eval/crossover.csv`](reports/eval/crossover.csv).

| | Số câu hỏi | Tỷ lệ |
|---|---|---|
| Cả hai đúng | 669 | 84,90% |
| **Chỉ BM25 đúng** | **3** | **0,38%** |
| Chỉ ngữ nghĩa đúng | 98 | 12,44% |
| Cả hai sai | 18 | 2,28% |

BM25 chỉ cứu được **3 câu hỏi trên 788** mà tầng ngữ nghĩa bỏ lỡ.

Đo cùng một thước, là tỷ lệ câu hỏi có ít nhất một điều gold trong top-10. Đọc từ
[`reports/eval/fusion_ceiling.csv`](reports/eval/fusion_ceiling.csv).

| Hệ | Tỷ lệ đúng ở top-10 |
|---|---|
| BM25 | 85,28% |
| Ngữ nghĩa AITeamVN | 97,34% |
| **Hợp nhất có trọng số** | **97,84%** |
| Nếu chỉ hợp nhất top-10 của hai tầng | 97,72% |

Hợp nhất hơn ngữ nghĩa thuần **0,50 điểm phần trăm, tức 4 câu hỏi trên 788**.

Chú ý dòng cuối bảng. Bản đầu tiên của phân tích gọi nó là "trần lý thuyết", rồi
số đo bác bỏ ngay: hệ hợp nhất đạt 97,84% và **vượt** nó 0,13 điểm. Lý do là hệ
thật hợp nhất từ **top-100** của mỗi tầng, nên nó kéo được cả những điều luật
đứng hạng 11 tới 100 lên top-10. Dòng đó chỉ là trần khi phép hợp bị giới hạn
trong top-10, và tên gọi cũ là sai.

Kết luận trung thực: hợp nhất **có** cải thiện, nhưng 0,50 điểm phần trăm là rất
nhỏ. Mỗi cấu hình chỉ chạy một seed nên nhóm không có cơ sở để nói về biên độ
nhiễu, và không gọi mức chênh đó là đáng kể.

BM25 vẫn có hai lý do thực dụng để giữ lại: nó nhanh hơn **700 lần** (0,5 ms so
với 352 ms) và nó **giải thích được** vì sao một điều luật được trả về, bằng đúng
những từ đã khớp. Tầng ngữ nghĩa chỉ đưa ra một con số cosine.

Đáng chú ý: RRF **kém hơn** ngữ nghĩa một mình (0,9670 so với 0,9721, và Recall@1
tụt từ 0,7811 xuống 0,6701). RRF chỉ nhìn thứ hạng nên nó để BM25 kéo tụt những
xếp hạng vốn đã tốt của tầng ngữ nghĩa. Hợp nhất theo điểm số có chuẩn hóa mới
tránh được chuyện đó.

## 9. Phân tích lỗi

Hệ sạch tốt nhất sai 17 trên 788 câu hỏi. Cả 17 ca đều được đọc tay, nhãn nằm ở
tệp nguồn [`docs/nhan_loi_doc_tay.csv`](docs/nhan_loi_doc_tay.csv).

| Nguyên nhân | Số ca | Tỷ lệ |
|---|---|---|
| Thiếu ngữ cảnh pháp lý | 10 | 58,8% |
| Nhiều điều luật cùng đúng, nhãn chỉ ghi một | 5 | 29,4% |
| Nhãn gold đáng ngờ | 2 | 11,8% |

Ví dụ nhóm "thiếu ngữ cảnh": *"Nướng bắp, ngô trên cầu phạt bao nhiêu tiền?"*.
Không từ nào trong câu hỏi xuất hiện trong điều luật đúng, vốn viết là "sử dụng
trái phép đất của đường bộ". Cần biết luật gọi hành vi đó là gì mới tìm ra.

Ví dụ nhóm "nhãn gold đáng ngờ": *"Người chấp hành biện pháp bắt buộc chữa bệnh
sẽ chữa bệnh ở đâu?"*. Hệ trả về Điều 138 "Tổ chức điều trị cho người bị bắt buộc
chữa bệnh", còn nhãn ghi Điều 133 về cơ quan được giao nhiệm vụ. Điều hệ trả về
sát câu hỏi hơn.

## 10. Giới hạn

1. **Nhãn không đầy đủ.** 24 câu hỏi có hai bộ nhãn khác nhau trong chính bộ dữ
   liệu gốc. Mọi con số Recall là cận dưới.
2. **Một seed.** Mỗi cấu hình chạy đúng một lần, nên không nói được gì về biên độ
   nhiễu giữa các lần chạy.
3. **F2@10 không so được với bảng xếp hạng Zalo.** Ban tổ chức chấm trên tập test
   riêng không công khai, và cho phép trả về số lượng kết quả thay đổi được. Con
   số F2@10 ở đây cố định k = 10 nên thấp một cách máy móc.
4. **Không có cross-encoder xếp hạng lại.** Đây là hướng phát triển rõ ràng nhất.
5. **Không sinh câu trả lời.** Đề tài là truy hồi. Trả về sai điều luật kèm một
   câu trả lời trôi chảy còn nguy hiểm hơn trả về sai điều luật.

## 11. Bản đồ thư mục

| Đường dẫn | Nội dung |
|---|---|
| `src/vlr/` | Thư viện lõi, 12 mô-đun, mỗi mô-đun có test riêng |
| `scripts/01` tới `06` | Sáu bước chạy tuần tự |
| `reports/audit/` | 11 tệp bằng chứng kiểm toán |
| `reports/eval/` | Bảng kết quả, quét tham số, biểu đồ |
| `runs/bkai_ft/` | Mô hình đã fine-tune và cấu hình thật đã chạy |
| `notebooks/demo.ipynb` | Bản chiếu khi bảo vệ |
| `notebooks/demo_giai_thich.ipynb` | Bản chú giải để đọc hiểu |
| `docs/slides/` | Mã sinh slide và tệp `.pptx` |
| `docs/HUONG_DAN_THUYET_TRINH.md` | Kịch bản thuyết trình |

Mọi con số trong slide và báo cáo đều đọc từ `reports/`. Không con số nào gõ tay.
