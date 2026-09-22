# Tìm kiếm điều luật tiếng Việt cho câu hỏi gõ thiếu dấu

Đồ án môn Xử lý ngôn ngữ tự nhiên, nhóm 09. GVHD: Đặng Văn Thìn.
Thành viên: Lê Hoàng Lộc (25210293), Lê Thị Tuấn Anh (25210250), Đoàn Mậu Thiên Thư (25210341).

Hệ tìm điều luật ghép BM25 với bi-encoder, chạy trên 61.425 điều luật của bộ Zalo AI
2021. Nhóm đo hệ khi câu hỏi bị gõ không dấu hoặc gõ dấu một nửa, sửa bằng một mô
hình bigram phục hồi dấu học từ chính kho luật, và kiểm toán lại bộ dữ liệu.

## Kết quả

Recall@10 trên 788 câu hỏi test, tham số chốt trên val:

| Câu hỏi | Hệ | Recall@10 |
|---|---|---|
| Có dấu | BM25 | 0,8522 |
| Có dấu | Ngữ nghĩa (AITeamVN) | 0,9721 |
| Có dấu | Hợp nhất có trọng số | 0,9772 |
| Không dấu, để nguyên | Hợp nhất | 0,1447 |
| Không dấu, phục hồi dấu trước | Hợp nhất | 0,9670 |
| Gõ dấu một nửa, để nguyên | Hợp nhất | 0,7481 |
| Gõ dấu một nửa, phục hồi dấu trước | Hợp nhất | 0,9721 |

Phục hồi dấu đúng 98,45% âm tiết, mất khoảng 0,9 ms mỗi câu, học xong trong 15 giây
trên CPU. Bảng đầy đủ ở `reports/eval/model_comparison.csv` và `reports/eval/khong_dau.csv`.

Kiểm toán dữ liệu tìm ra 24 câu hỏi nằm ở cả train lẫn test mà cả 24 đều mang nhãn
khác nhau, và mô hình `bkai-foundation-models/vietnamese-bi-encoder` đã được huấn
luyện trên 80% tập train Zalo 2021 (theo model card của họ). Vì vậy số chính thức
dùng `AITeamVN/Vietnamese_Embedding`, mô hình ghi rõ không học bộ này.

## Dữ liệu

Zalo AI Challenge 2021, Legal Text Retrieval, bản BEIR trên HuggingFace:
`GreenNode/zalo-ai-legal-text-retrieval-vn`, giấy phép MIT. Script bước 1 tự tải về
`data/raw/`, dữ liệu không nằm trong repo.

Bộ gốc không có tập val nên nhóm cắt val ra từ train theo câu hỏi (seed 42):

| Tập | Câu hỏi | Cặp nhãn |
|---|---|---|
| train | 1.925 | 1.986 |
| val | 481 | 492 |
| test | 788 | 793 |

## Cài đặt

Cài torch theo GPU của máy (xem đầu `requirements.txt`), rồi:

```bash
pip install -r requirements.txt
```

## Chạy

Chạy từ thư mục gốc, đúng thứ tự:

```bash
python scripts/01_prepare_data.py
python scripts/02_build_index.py --model all
python scripts/03_finetune.py
python scripts/02_build_index.py --model bkai_ft
python scripts/04_tune.py
python scripts/05_evaluate.py
python scripts/06_error_analysis.py
python scripts/07_khong_dau.py
python -m pytest
```

Trên RTX 5060 Ti 16 GB: bước 1 mất 5,5 phút, chủ yếu là tách từ bằng pyvi. Bước 2
mã hóa 154.176 đoạn, mất 11,1 phút với AITeamVN, 5,0 phút với bkai và 4,0 phút với
bkai đã fine-tune. Các bước 3 tới 7 mỗi bước dưới 3 phút.

Demo ở `notebooks/demo.ipynb`, cần chạy xong bảy bước trên trước.

## Thư mục

| Đường dẫn | Nội dung |
|---|---|
| `src/vlr/` | Thư viện: chuẩn hóa, kiểm toán, chia đoạn, BM25, bi-encoder, hợp nhất, phục hồi dấu, trợ lý tra cứu |
| `scripts/` | Bảy bước chạy tuần tự |
| `tests/` | 130 test |
| `reports/audit/` | Kết quả kiểm toán dữ liệu |
| `reports/eval/` | Kết quả đánh giá, quét tham số |
| `notebooks/` | Notebook demo |
| `docs/slides/` | Mã dựng slide và tệp pptx |
| `docs/NGHIEN_CUU_LIEN_QUAN.md` | Nghiên cứu liên quan và tài liệu tham khảo |

## Giới hạn

- Câu không dấu và câu gõ dấu một nửa đều do máy bỏ dấu từ câu gốc, chưa có câu người thật gõ.
- Nhãn không đầy đủ (24 câu có hai nhãn khác nhau), nên Recall ở đây là cận dưới.
- Mỗi cấu hình chạy một lần với một seed.
- Phục hồi dấu hay sai ở từ nói thường mà văn bản luật không dùng, như "tài xế" thành "tải xe".
