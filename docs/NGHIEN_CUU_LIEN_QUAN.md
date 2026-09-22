# Nghiên cứu liên quan và lý do chọn hướng

Đề tài: **Tìm kiếm điều luật tiếng Việt cho câu hỏi gõ thiếu dấu (kết hợp từ khóa và ngữ nghĩa, phục hồi dấu bằng mô hình ngôn ngữ, kiểm toán rò rỉ dữ liệu ở cả bộ dữ liệu lẫn mô hình tiền huấn luyện).**

Các nguồn được mở và đối chiếu ngày 15/9/2026. Với bài báo, nhóm đọc phần tóm tắt
và mã nguồn công bố, không đọc hết toàn văn, nên "không báo cáo" ở dưới nghĩa là
không thấy trong những phần đó.

## 1. Năm hướng đã có

### 1.1. Lai BM25 với mô hình ngữ nghĩa cho văn bản tiếng Việt

| Công trình | Làm gì | Họ kết luận |
|---|---|---|
| Mã nguồn công khai của hai đội dự thi Zalo AI 2021 [20, 21] | Đội thứ nhất lấy trung bình có trọng số bốn mô hình PhoBERT, Condenser, coCondenser, viBERT rồi **nhân** cosine với điểm BM25. Đội thứ hai lọc top-k bằng BM25 trên Elasticsearch rồi xếp hạng lại bằng cross-encoder PhoBERT | Đội thứ hai báo F2 0,747 trên public test, so với khoảng 0,54 của BM25 một mình |
| Khang và cs., 2024 [10] | Sparse cộng dense, PhoBERT tiền huấn luyện thêm trên 3 GB văn bản luật | Kết hợp hai cách tốt hơn từng cách |
| Nguyen Ba và cs., 2024 [11] | Hệ hỏi đáp RAG, ghép tìm từ khóa với tìm vector bằng RRF cải tiến | Hợp nhất cải thiện độ tin cậy |
| Giang và cs., 2025 [14] | So nhiều chiến lược truy hồi cho RAG pháp luật | Lai sparse và dense "consistently outperform" từng cách riêng |
| ViDRILL, 2025 [15] | BM25 lấy top-200, E5 và GTE, cross-encoder BGE xếp hạng lại | Top-5 cuộc thi VLSP 2025 |
| Nguyen và Quan, 2026 [17] | So lexical, sparse học được, late-interaction, dense và lai trên 10 bộ dữ liệu tiếng Việt ở 6 lĩnh vực, có luật | Lai có lợi thế; mô hình lớn hơn không chắc tốt hơn |

Đây là công thức mặc định của cộng đồng. Không bài nào nhóm đọc đưa ra kết luận
ngược. Bài [17] đã làm đúng phép so ba cách này ở quy mô lớn hơn đồ án nhiều, nên
nếu đồ án chỉ lặp lại phép so đó thì không có gì mới.

### 1.2. Làm mạnh riêng tầng ngữ nghĩa

| Công trình | Đóng góp |
|---|---|
| Pham, Nguyen, Do, 2022 [9] | Truy hồi nhiều tầng bằng sentence-transformer, so tách âm tiết với tách từ |
| Pham Tien và cs., 2024 [12] | Dùng LLM sinh câu hỏi tổng hợp để bù thiếu dữ liệu gán nhãn |
| Le và cs., 2025 [13] | Nhóm tác giả UIT. Bi-encoder cộng cross-encoder, khai thác âm bán khó, top 3 SoICT Hackathon 2024 |
| ALQAC 2021 tới 2023 [16] | Cuộc thi truy hồi điều luật tiếng Việt, bộ dữ liệu gán nhãn tay |

### 1.3. Cách hợp nhất

| Công trình | Kết luận |
|---|---|
| Cormack và cs., 2009 [2] | Đề xuất RRF: chỉ dùng thứ hạng, không cần chuẩn hóa điểm |
| Bruch, Gai, Ingber, 2023 [7] | RRF nhạy với tham số `k`; tổng lồi có trọng số hơn RRF cả trong và ngoài miền; chỉ cần ít mẫu để chỉnh trọng số |
| Rosa và cs., 2021 [8] | Chỉ dùng BM25 vẫn đứng hạng 2 ở COLIEE 2021 task 1: BM25 là mốc mạnh trong truy hồi pháp lý |

### 1.4. Phục hồi dấu tiếng Việt

| Công trình | Làm gì |
|---|---|
| Pham, Pham, Le-Hong, 2017 [25] | So dịch máy theo cụm từ và dịch máy nơ-ron cho bài toán phục hồi dấu: 97,32% và 96,15% |
| Le-Hong, 2021 [26] | Phục hồi dấu rồi dùng cho phát hiện phát ngôn thù ghét trên mạng xã hội |

Phục hồi dấu là bài toán đã được nghiên cứu kỹ, nhưng được đánh giá như một bài
toán riêng hoặc cho phân loại văn bản. Nhóm không tìm thấy bài nào đo nó ảnh hưởng
thế nào tới truy hồi văn bản luật.

### 1.5. Đánh giá mô hình nhúng và nhiễm bẩn

| Công trình | Liên quan thế nào |
|---|---|
| MMTEB, 2025 [18] | Dựng lại MTEB tiếng Anh thành bản zero-shot bằng cách bỏ MS MARCO và Natural Questions, vì nhiều mô hình đã huấn luyện trên chúng |
| Chung và cs., 2025 [19] | Định nghĩa điểm zero-shot và hiển thị nó trên bảng xếp hạng MTEB. Mô hình không zero-shot nếu đã huấn luyện trên split khác của cùng bộ dữ liệu |

## 2. Model card trên đúng bộ dữ liệu của đồ án

| Mô hình | Model card ghi | Hệ quả |
|---|---|---|
| `bkai-foundation-models/vietnamese-bi-encoder` [22] | Huấn luyện trên "80% of the training set from the Legal Text Retrieval Zalo 2021 challenge" | Không zero-shot trên bộ này |
| `darklethelong/vnlegal-lal` [23] | Huấn luyện trên `GreenNode/zalo-ai-legal-text-retrieval-vn`, tự nhận state-of-the-art với nDCG@10 0,8488 trên ZacLegalTextRetrieval | Bảng so sánh trên model card đặt nó cạnh các mô hình chưa thấy bộ này, không đánh dấu |
| `AITeamVN/Vietnamese_Embedding` [24] | "Our model was not trained on this dataset", nền BGE-M3 [6] | Nhóm dùng làm mô hình sạch, ghi rõ đây là tuyên bố của tác giả |

## 3. Khoảng trống

Bốn điều các công trình ở mục 1.1, 1.2 và 1.4 không báo cáo:

1. **Câu gõ không dấu.** Mọi bài truy hồi luật nhóm đọc đều chấm trên câu hỏi
   có dấu đầy đủ. Các bài phục hồi dấu thì không đo truy hồi. Không ai biết hệ tìm
   luật đứng vững thế nào khi người dân gõ không dấu.
2. **Mô hình đã thấy dữ liệu đánh giá chưa.** Mục 2 cho thấy mô hình
   tiếng Việt phổ biến nhất và mô hình tự nhận tốt nhất trên bộ này đều đã huấn
   luyện trên nó. Chính nhóm duy trì MTEB đã phải thêm điểm zero-shot vì lý do này
   [19].
3. **Split gốc.** Các bài dùng nguyên split của ban tổ chức. Không
   bài nào báo cáo kiểm tra câu hỏi trùng giữa train và test.
4. **Hàm hợp nhất.** Chọn theo thói quen: nhân điểm [20], RRF [11], hay một trọng số
   cố định, ít khi so các cách trên một tập val riêng, trong khi [7] cho thấy lựa
   chọn này thay đổi kết quả.

## 4. Hai câu hỏi nghiên cứu và lý do chọn

> **CH1.** Trên dữ liệu đã kiểm toán và với mô hình ngữ nghĩa chưa thấy dữ liệu,
> ghép thêm BM25 còn cải thiện được bao nhiêu?
>
> **CH2.** Khi người dùng gõ không dấu, hệ còn đứng vững không, và cách sửa rẻ nhất
> là gì?

Lý do chọn:

- **Gõ không dấu là thói quen có thật.** Nhắn trên điện thoại, máy không cài bộ gõ,
  hoặc gõ vội. Hệ tra cứu luật cho người dân phải chịu được chuyện đó.
- **CH1 là điều kiện để trả lời CH2.** Muốn biết không dấu làm hỏng bao nhiêu thì
  phải có một mốc có dấu đo sạch trước. Ba khoảng trống 2, 3, 4 đều có thể làm con
  số mốc lệch theo chiều có lợi.
- **Vừa sức một đồ án môn học.** Một GPU 16 GB, mã hóa toàn bộ kho bằng mô hình
  sạch mất 11,1 phút (`reports/eval/index_cost.csv`). Mô hình phục hồi dấu đếm xong
  trong 15 giây, không cần tải mô hình nào thêm.
- **Kinh nghiệm từ đồ án trước.** Ở đồ án nhận diện bệnh lá sầu riêng, bộ dữ liệu
  công bố có ảnh cùng một chiếc lá nằm ở cả train và test. Nhóm muốn biết bộ văn
  bản có mắc cùng lỗi không.

## 5. Kết quả đặt cạnh nghiên cứu trước

| Nghiên cứu trước nói | Đồ án đo được | Khớp không |
|---|---|---|
| Lai tốt hơn từng tầng [10, 11, 14, 15, 17] | Câu có dấu: tổng trọng số hơn ngữ nghĩa thuần 0,51 điểm Recall@10, 4 câu trên 788 | Cùng chiều, nhưng mức nhỏ tới mức không gọi được là đáng kể |
| Tổng trọng số hơn RRF, RRF nhạy tham số [7] | Recall@10 0,9772 so với 0,9670; RRF còn kém ngữ nghĩa thuần ở Recall@1 (0,6701 so với 0,7811) | Khớp |
| BM25 là mốc mạnh trong truy hồi pháp lý [8] | Câu có dấu: BM25 kém ngữ nghĩa 12 điểm Recall@10. Câu không dấu, chỉ mục bỏ dấu: BM25 đạt 0,7430, gấp sáu lần ngữ nghĩa (0,1244) | Đúng ở tình huống không dấu |
| Phục hồi dấu đạt khoảng 97% [25] | Bigram âm tiết học từ kho luật: 98,45% âm tiết trên câu hỏi test | Cùng mức, dù mô hình đơn giản hơn nhiều; chưa so trên cùng bộ dữ liệu nên không kết luận hơn kém |
| Phải tách mô hình zero-shot khỏi mô hình đã thấy dữ liệu [18, 19] | bkai nhỏ hơn AITeamVN khoảng bốn lần nhưng Recall@1 cao hơn: 0,8204 so với 0,7811 | Cùng chiều, nhưng chỉ là dấu hiệu: không tách được bao nhiêu điểm là do đã thấy dữ liệu |

Các con số ở bảng này chép từ `reports/eval/model_comparison.csv`,
`reports/eval/khong_dau.csv` và `reports/eval/khong_dau_params.json`. Chạy lại
pipeline thì phải dò lại bảng này bằng tay.

## Tài liệu tham khảo

### Nền tảng phương pháp

1. Robertson, S., & Zaragoza, H. (2009). The Probabilistic Relevance Framework: BM25 and Beyond. *Foundations and Trends in Information Retrieval*, 3(4).
2. Cormack, G. V., Clarke, C. L. A., & Büttcher, S. (2009). Reciprocal Rank Fusion Outperforms Condorcet and Individual Rank Learning Methods. *SIGIR 2009*.
3. Karpukhin, V., et al. (2020). Dense Passage Retrieval for Open-Domain Question Answering. *EMNLP 2020*.
4. Nguyen, D. Q., & Nguyen, A. T. (2020). PhoBERT: Pre-trained Language Models for Vietnamese. *Findings of EMNLP 2020*.
5. Gao, L., Zhang, Y., Han, J., & Callan, J. (2021). Scaling Deep Contrastive Learning Batch Size under Memory Limited Setup. *RepL4NLP 2021*.
6. Chen, J., Xiao, S., Zhang, P., Luo, K., Lian, D., & Liu, Z. (2024). BGE M3-Embedding: Multi-Lingual, Multi-Functionality, Multi-Granularity Text Embeddings Through Self-Knowledge Distillation. arXiv:2402.03216.
7. Bruch, S., Gai, S., & Ingber, A. (2023). An Analysis of Fusion Functions for Hybrid Retrieval. *ACM Transactions on Information Systems*, 42(1).
8. Rosa, G. M., Rodrigues, R. C., Lotufo, R., & Nogueira, R. (2021). Yes, BM25 is a Strong Baseline for Legal Case Retrieval. arXiv:2105.05686.

### Truy hồi văn bản tiếng Việt

9. Pham, N.-M., Nguyen, H.-T., & Do, T.-H. (2022). Multi-stage Information Retrieval for Vietnamese Legal Texts. *PKAW 2022*. arXiv:2209.14494.
10. Nguyen Hoang Gia Khang, Nguyen Minh Nhat, Trung Nguyen Quoc, & Vinh Truong Hoang (2024). Vietnamese Legal Text Retrieval based on Sparse and Dense Retrieval approaches. *Procedia Computer Science*.
11. Nguyen Ba, T., Doan The, V., Pham Quang, T., & Tran Van, T. (2024). Vietnamese Legal Information Retrieval in Question-Answering System. arXiv:2409.13699.
12. Pham Tien, S., Nguyen Doan, H., Nguyen Dai, A., & Dinh Viet, S. (2024). Improving Vietnamese Legal Document Retrieval using Synthetic Data. arXiv:2412.00657.
13. Le, V.-H., Nguyen, D.-V., Nguyen, K. V., & Nguyen, N. L.-T. (2025). Optimizing Legal Document Retrieval in Vietnamese with Semi-Hard Negative Mining. *ICCCI 2025*. arXiv:2507.14619.
14. Giang, N. T., Duc, T. M., Dang, N. M., & Trang, N. T. M. (2026). Optimizing Retrieval Strategies for Vietnamese Legal RAG Systems. *CIT&DS 2025*, CCIS vol. 2803, Springer.
15. Tran, D. X., Truong, T. D., & Nguyen, K. C. (2025). ViDRILL: A Multi-Stage Retrieval Framework for Vietnamese Legal Document Search. *VLSP 2025*, tr. 120-126.
16. Nguyen, C., et al. (2023). A Summary of the ALQAC 2023 Competition. *KSE 2023*.
17. Nguyen, L. S. T., & Quan, T. T. (2026). Which Works Best for Vietnamese? A Practical Study of Information Retrieval Methods across Domains. *Findings of EACL 2026*.

### Đánh giá mô hình nhúng

18. Enevoldsen, K., et al. (2025). MMTEB: Massive Multilingual Text Embedding Benchmark. *ICLR 2025*.
19. Chung, I., Kerboua, I., Kardos, M., Solomatin, R., & Enevoldsen, K. (2025). Maintaining MTEB: Towards Long Term Usability and Reproducibility of Embedding Benchmarks. arXiv:2506.21182.

### Mã nguồn, mô hình và dữ liệu

20. CuongNN218. zalo_ltr_2021: Source code for Zalo AI 2021 submission. https://github.com/CuongNN218/zalo_ltr_2021
21. hieudx149. ZaloAI2021_LTR. https://github.com/hieudx149/ZaloAI2021_LTR
22. BKAI Foundation Models. vietnamese-bi-encoder (model card). https://huggingface.co/bkai-foundation-models/vietnamese-bi-encoder
23. darklethelong. vnlegal-lal (model card). https://huggingface.co/darklethelong/vnlegal-lal
24. AITeamVN. Vietnamese_Embedding (model card). https://huggingface.co/AITeamVN/Vietnamese_Embedding

### Phục hồi dấu tiếng Việt

25. Pham, T.-H., Pham, X.-K., & Le-Hong, P. (2017). On the Use of Machine Translation-Based Approaches for Vietnamese Diacritic Restoration. *IALP 2017*. arXiv:1709.07104.
26. Le-Hong, P. (2021). Diacritics Generation and Application in Hate Speech Detection on Vietnamese Social Networks. *Knowledge-Based Systems*, 233.

### Dữ liệu

27. GreenNode. zalo-ai-legal-text-retrieval-vn (dataset card). https://huggingface.co/datasets/GreenNode/zalo-ai-legal-text-retrieval-vn
