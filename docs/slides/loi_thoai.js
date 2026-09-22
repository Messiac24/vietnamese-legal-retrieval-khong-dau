// Lời thoại từng slide. Sửa lời nói ở đây, build.js tự đưa vào ghi chú của pptx.
// Số liệu lấy từ D (build.js đọc từ reports/), không gõ tay.
const LOC = "Lê Hoàng Lộc", ANH = "Lê Thị Tuấn Anh", THU = "Đoàn Mậu Thiên Thư";

module.exports = (D) => {
  const { so, pt, nghin, kd } = D;
  const r10 = (dk, cach, he) => pt(kd(dk, cach, he)["recall@10"]);
  const lan = Math.round(D.tocDo / 100) * 100;
  const chenh = so(100 * (kd("có dấu", "giữ nguyên", "Hợp nhất")["recall@10"] - kd("không dấu", "phục hồi dấu", "Hợp nhất")["recall@10"]), 2);

  return {
    1: { giay: 15, nguoi: LOC, noi: [
      "Em chào thầy và các bạn. Nhóm 09 gồm Lộc, Tuấn Anh và Thư. Đề tài của nhóm là tìm kiếm điều luật tiếng Việt cho câu hỏi gõ thiếu dấu.",
    ] },

    2: { giay: 40, nguoi: LOC, noi: [
      `Bài toán là: người dân gõ một câu hỏi pháp luật, hệ thống trả về điều luật liên quan trong ${nghin(D.CS.so_dieu_luat)} điều của ${nghin(D.CS.so_van_ban)} văn bản.`,
      "Khó ở hai chỗ. Một là người hỏi dùng lời thường còn luật dùng thuật ngữ, như câu nướng bắp trên cầu này, điều luật đúng không trùng với câu hỏi chữ nào.",
      "Hai, cũng là chỗ nhóm tập trung, là nhiều người gõ không dấu, nhất là khi nhắn trên điện thoại. Với máy thì chữ phạt có dấu và chữ phat không dấu là hai chữ khác hẳn nhau.",
    ] },

    3: { giay: 40, nguoi: LOC, noi: [
      "Nhóm có đọc lại các nghiên cứu trước. Ghép tìm theo từ khóa với tìm theo ngữ nghĩa thì từ các đội thi Zalo 2021 đến bài ở hội nghị EACL năm nay đều làm rồi, và đều thấy ghép tốt hơn dùng riêng. Nhóm chỉ lặp lại phép so đó thì không có gì mới.",
      "Dòng màu đỏ mới là chỗ nhóm để ý: phục hồi dấu tiếng Việt đã đạt khoảng 97 phần trăm, nhưng người ta đo nó như một bài toán riêng, chưa ai đo xem nó giúp tìm luật được bao nhiêu.",
    ], hoi: [
      ["Nhóm đọc hết các bài đó chưa?", "Nhóm đọc phần tóm tắt, mã nguồn và model card, không đọc hết toàn văn. Danh sách 27 nguồn ở slide 16."],
    ] },

    4: { giay: 40, nguoi: LOC, noi: [
      "Xếp lại thì ra cái bảng này. Tìm luật trên câu có dấu thì làm nhiều rồi, phục hồi dấu cũng làm rồi. Còn ô đỏ, tìm luật khi câu hỏi mất dấu, thì trong các nguồn nhóm đọc chưa ai đo. Đó là câu hỏi thứ hai.",
      "Câu hỏi thứ nhất là để có một mốc sạch: trên câu có dấu, với dữ liệu đã kiểm tra và mô hình chưa thấy dữ liệu, ghép thêm BM25 được bao nhiêu. Có mốc đó rồi mới đo được mất dấu làm hỏng bao nhiêu.",
    ], hoi: [
      ["Chắc chắn chưa ai làm?", "Nhóm chỉ nói trong phạm vi các nguồn đã đối chiếu, không dám khẳng định cho mọi công trình."],
    ] },

    5: { giay: 40, nguoi: LOC, noi: [
      "Dữ liệu là bộ Zalo AI Challenge 2021, bản trên HuggingFace, đã được đưa vào bộ đánh giá MTEB. Bộ gốc chỉ có train và test, không có tập val, nên nhóm tự cắt val ra từ train.",
      `Bộ này đã công bố nhưng nhóm vẫn kiểm tra lại, ra sáu vấn đề như biểu đồ. Có ${nghin(D.nhanDoi)} điều bị nhân đôi chỉ vì mã văn bản viết nd hay nđ, tức là chuyện dấu đã gây lỗi ngay trong dữ liệu. Nặng nhất là thanh cuối: ${D.chongLan} câu hỏi nằm ở cả train lẫn test. Phần này bạn Tuấn Anh nói tiếp.`,
    ], hoi: [
      ["Sao không xóa các điều trùng?", "Kho luật thật có điều trùng thật, và các nhóm trùng đều nằm ở những văn bản khác nhau. Xóa đi thì bài toán dễ đi một cách giả tạo, nên nhóm chỉ báo cáo."],
    ] },

    6: { giay: 45, nguoi: ANH, noi: [
      `Dạ, trong ${D.chongLan} câu đó có ${D.trungId} câu trùng đúng mã câu hỏi. Tưởng là dòng bị lặp, nhưng đọc kỹ thì cả ${D.xungDot} câu đều mang nhãn khác nhau: tệp train chỉ sang một điều luật, tệp test chỉ sang điều khác.`,
      "Như câu đầu, bị thương tật 25 phần trăm có bị khởi tố không, train ghi luật sửa đổi Bộ luật Hình sự, test ghi Bộ luật Tố tụng Hình sự. Điều nào cũng liên quan. Tức là một câu hỏi có thể đúng với nhiều điều mà nhãn chỉ ghi một, nên mọi con số Recall nhóm báo cáo đều là cận dưới.",
      "Nhóm bỏ nhãn train của các câu này và giữ nguyên tập test của ban tổ chức.",
    ], hoi: [
      ["Sao không gộp nhãn train vào test cho đủ?", `Gộp vào là tự sửa nhãn của tập test bằng phỏng đoán của nhóm. Bản chạy đầu có gộp nhầm, test phình từ ${nghin(D.SPLIT.test.so_cap_qrel)} lên 818 cặp, nhóm phát hiện khi đối chiếu số dòng với tệp gốc và đã sửa.`],
    ] },

    7: { giay: 45, nguoi: ANH, noi: [
      "Rò rỉ còn nằm ở chỗ khó thấy hơn, là trong mô hình. Nhóm định dùng bkai, mô hình nhúng tiếng Việt được dùng nhiều nhất. Nhưng model card của họ ghi đã huấn luyện trên 80 phần trăm tập train của Zalo 2021, mà tập test của nhóm lại cắt ra từ đúng tập đó. Tức là mô hình đã xem đề và đáp án trước khi thi.",
      `Nên nhóm chuyển sang AITeamVN, model card ghi rõ không học bộ này, và dùng nó cho mọi con số chính thức. bkai vẫn chạy để so nhưng gắn nhãn nhiễm bẩn. Chia lại xong, nhóm có ${nghin(D.SPLIT.train.so_cau_hoi)} câu train, ${D.SPLIT.val.so_cau_hoi} câu val để chỉnh tham số, và ${D.TONG_TEST} câu test chỉ chạy đúng một lần.`,
    ], hoi: [
      ["Sao tin model card của AITeamVN?", "Nhóm không kiểm chứng trực tiếp được, nên ghi rõ đó là lời của tác giả mô hình, không phải kết quả nhóm tự đo."],
    ] },

    8: { giay: 45, nguoi: ANH, noi: [
      "Đây là kiến trúc. Câu hỏi nào cũng đi qua khâu phục hồi dấu trước, không cần biết nó có dấu hay chưa, vì chữ đã có dấu thì giữ nguyên.",
      `Sau đó chia hai nhánh. Nhánh trên là BM25, tách từ bằng pyvi rồi tìm trên nguyên điều luật, mạnh ở số hiệu và thuật ngữ. Nhánh dưới là mô hình ngữ nghĩa, tìm trên các đoạn nhỏ rồi lấy điểm cao nhất của mỗi điều. Mỗi nhánh lấy ${D.TS.top_k_hop_nhat} kết quả rồi cộng điểm theo trọng số, alpha ${so(D.TS.weighted.alpha, 2)} chọn trên val.`,
      "Đầu ra trích nguyên văn khoản luật chứ không sinh câu trả lời, nên không bịa ra được.",
    ], hoi: [
      ["Sao lấy điểm cao nhất mà không lấy trung bình các đoạn?", `Câu trả lời thường nằm gọn trong một khoản, lấy trung bình thì các khoản khác kéo điểm xuống. Đo trên val: max ${so(D.gop("max"))}, trung bình ${so(D.gop("mean"))}.`],
    ] },

    9: { giay: 35, nguoi: ANH, noi: [
      `Vì sao phải chia đoạn? Mô hình chỉ đọc được 256 token, khoảng ${D.DODAI.tran_tu_tuong_duong} chữ. Phần màu đỏ là các điều dài hơn thế, chiếm ${so(D.DODAI.ty_le_vuot_tran_pct, 1)} phần trăm. Cắt cụt thì mất phần đuôi, mà đuôi điều luật hay là mức phạt và các ngoại lệ.`,
      `Nhóm cắt theo từng khoản, khoản nào quá dài mới cắt tiếp, đoạn nào cũng gắn tiêu đề điều ở đầu. ${nghin(D.CS.so_dieu_luat)} điều thành ${nghin(D.CHUNKS)} đoạn.`,
    ] },

    10: { giay: 45, nguoi: ANH, noi: [
      `Đến câu hỏi thứ nhất. Trên ${D.TONG_TEST} câu test có dấu, Recall@10 của BM25 là ${pt(D.BM["recall@10"])}, ngữ nghĩa ${pt(D.DE_SACH["recall@10"])}, hợp nhất ${pt(D.HE_SACH["recall@10"])} phần trăm.`,
      `Hợp nhất hơn ngữ nghĩa ${so(D.loiHopR, 2)} điểm, đếm ra chỉ ${D.soCauHop} câu. Có cải thiện nhưng rất nhỏ, và mỗi cấu hình nhóm chỉ chạy một lần nên không dám nói là đáng kể. Cách RRF chỉ dựa vào thứ hạng còn kém ngữ nghĩa ở Recall@1. Em xin chuyển cho bạn Thư.`,
    ], hoi: [
      ["bkai điểm cao hơn, sao không dùng?", `bkai đạt ${pt(D.bkai["recall@10"])} nhưng đã học tập test, như slide 7, nên không so với các hệ sạch.`],
      ["F2 sao thấp?", "Nhóm cố định lấy 10 kết quả nên precision cao nhất chỉ 0,1. Zalo cho trả về số kết quả tùy ý, nên không so với bảng xếp hạng được."],
    ] },

    11: { giay: 40, nguoi: THU, noi: [
      `Dạ. Vì sao hợp nhất giúp ít như vậy? Đối chiếu từng câu thì ${D.CROSS["cả hai đúng"]} câu cả hai nhánh đều tìm đúng, ${D.CROSS["chỉ ngữ nghĩa đúng"]} câu chỉ ngữ nghĩa đúng, còn BM25 đúng mà ngữ nghĩa sai thì chỉ có ${D.CROSS["chỉ BM25 đúng"]} câu.`,
      `Vậy có bỏ BM25 không? Nhóm vẫn giữ, vì nó nhanh hơn khoảng ${lan} lần, chỉ mục nhỏ hơn gần mười lần, và chỉ ra được từ nào đã khớp để người dùng kiểm lại. Ở phần sau BM25 còn có vai trò khác.`,
    ], hoi: [
      ["Hệ vẫn sai ở những câu nào?", `Hệ hợp nhất sai ${D.soSai} câu, nhóm đọc tay cả ${D.soSai}: ${D.ERRS[0].so_ca} ca thiếu ngữ cảnh pháp lý như câu nướng bắp, ${D.ERRS[1].so_ca} ca nhiều điều cùng đúng mà nhãn ghi một, ${D.ERRS[2].so_ca} ca nhãn đáng ngờ.`],
    ] },

    12: { giay: 45, nguoi: THU, noi: [
      `Câu hỏi thứ hai. Nhóm lấy đúng ${D.TONG_TEST} câu test đó, bỏ hết dấu bằng máy, giữ nguyên nhãn rồi chạy lại. Mô hình ngữ nghĩa từ ${r10("có dấu", "giữ nguyên", "Ngữ nghĩa")} rơi xuống ${r10("không dấu", "giữ nguyên", "Ngữ nghĩa")}. BM25 còn ${r10("không dấu", "giữ nguyên", "BM25")}, hợp nhất cũng chỉ ${r10("không dấu", "giữ nguyên", "Hợp nhất")}. Gần như không dùng được.`,
      `BM25 hỏng vì phat và phạt không khớp nhau. Còn mô hình ngữ nghĩa, nhóm đoán là do nó học chủ yếu văn bản có dấu, cái này chưa kiểm chứng. Lập chỉ mục BM25 trên văn bản bỏ dấu thì lên lại ${r10("không dấu", "chỉ mục bỏ dấu", "BM25 bỏ dấu")}, nhưng vẫn còn xa.`,
    ], hoi: [
      ["Câu không dấu do máy tạo, có giống người gõ thật không?", "Chưa giống hẳn: người thật còn gõ tắt, sai chính tả. Nhóm chọn cách này vì giữ nguyên được nhãn nên đo sạch. Đây là giới hạn lớn nhất."],
      ["BM25 bỏ dấu giảm là do bỏ dấu hay do đổi cách tách từ?", `Cả hai. Đo riêng trên val: đổi cách tách từ mất ${so(D.TACH["pyvi tách từ, còn dấu"] - D.TACH["âm tiết, còn dấu"], 3)}, bỏ dấu mất thêm ${so(D.TACH["âm tiết, còn dấu"] - D.TACH["âm tiết, bỏ dấu"], 3)}.`],
    ] },

    13: { giay: 45, nguoi: THU, noi: [
      `Cách nhóm sửa là phục hồi dấu trước khi tìm. Nhóm đếm các cặp âm tiết đi liền nhau trong ${so(D.KDP.so_am_tiet / 1e6, 1)} triệu âm tiết của chính kho luật. Mỗi âm tiết không dấu có vài ứng viên, như nghi có thể là nghỉ, nghị, nghĩ, rồi thuật toán Viterbi chọn chuỗi có xác suất cao nhất.`,
      `Kết quả đúng ${pt(D.KDP.do_chinh_xac_am_tiet_test)} phần trăm âm tiết, mỗi câu chưa tới một mili giây, học xong trong ${D.KDP.giay_hoc_mo_hinh} giây trên CPU. Hệ từ ${r10("không dấu", "giữ nguyên", "Hợp nhất")} lên ${r10("không dấu", "phục hồi dấu", "Hợp nhất")}, chỉ kém câu có dấu ${chenh} điểm.`,
    ], hoi: [
      ["Sao không dùng mô hình phục hồi dấu có sẵn hoặc LLM?", "Nhóm chưa so trên cùng bộ dữ liệu nên không nói hơn kém. Bigram có lợi là không phải tải thêm mô hình, chạy trên CPU, và học đúng từ vựng luật."],
    ] },

    14: { giay: 35, nguoi: THU, noi: [
      `Phục hồi vẫn sai, chủ yếu ở từ nói thường mà luật không dùng, như tài xế thành tải xe, máu thành mẫu. Có ${D.KDL["sai ít nhất một âm tiết"].so_cau} câu sai ít nhất một âm tiết, trong đó mất ${D.KDL["mất do phục hồi sai"].so_cau} câu tìm đúng và được lại ${D.KDL["được nhờ phục hồi"].so_cau} câu.`,
      `Bên phải là câu gõ dấu một nửa, chữ có dấu chữ không. Vì chữ đã có dấu được giữ nguyên nên câu nửa dấu từ ${r10("nửa dấu", "giữ nguyên", "Hợp nhất")} lên ${r10("nửa dấu", "phục hồi dấu", "Hợp nhất")}, còn câu đủ dấu cho qua vẫn giữ ${r10("có dấu", "phục hồi dấu", "Hợp nhất")}.`,
    ] },

    15: { giay: 35, nguoi: THU, noi: [
      `Nhóm rút ra ba điều. Một, với câu có dấu, hợp nhất chỉ hơn ngữ nghĩa ${D.soCauHop} câu, BM25 đáng giữ vì nhanh và giải thích được. Hai, khi mất dấu thì hệ sụp, và một mô hình bigram nhỏ học từ kho luật kéo lại gần hết. Ba, chống rò rỉ phải kiểm cả mô hình tải về, không dừng ở chia lại tập.`,
      "Giới hạn lớn nhất là câu không dấu do máy tạo, chưa có câu người thật gõ. Em xin hết phần trình bày, nhóm xin chuyển sang demo.",
    ] },
  };
};
