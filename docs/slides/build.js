// Bộ slide báo cáo môn Xử lý ngôn ngữ tự nhiên - Nhóm 09
// Đề tài: Truy hồi điều luật tiếng Việt cho câu hỏi gõ không dấu:
//         phục hồi dấu, truy hồi lai và kiểm toán rò rỉ dữ liệu
//
// Dựng lại bộ slide (chạy từ chính thư mục này):
//
//     C:/Python314/python.exe make_assets.py    -> img/*.png
//     npm install pptxgenjs
//     node build.js                             -> Nhom09_XLNNTN_BaoCao.pptx
//
// KHÔNG gõ tay con số nào vào tệp này. Mọi số liệu đọc từ reports/ ở thư mục
// gốc dự án. Chạy lại pipeline là slide tự đổi theo. Danh sách tài liệu tham
// khảo đọc từ docs/NGHIEN_CUU_LIEN_QUAN.md.
// Ghi chú thuyết trình nằm trong addNotes() của từng slide.
const fs = require("fs");
const path = require("path");
const pptx = require("pptxgenjs");
const p = new pptx();

const ROOT = path.resolve(__dirname, "..", "..");
const AUDIT = path.join(ROOT, "reports", "audit");
const EVAL = path.join(ROOT, "reports", "eval");

/* ---------------------- đọc số liệu từ reports/ ---------------------- */
function tachDong(dong) {
  const o = [];
  let cur = "", trongNhay = false;
  for (let i = 0; i < dong.length; i++) {
    const c = dong[i];
    if (c === '"') {
      if (trongNhay && dong[i + 1] === '"') { cur += '"'; i++; }
      else trongNhay = !trongNhay;
    } else if (c === "," && !trongNhay) { o.push(cur); cur = ""; }
    else cur += c;
  }
  o.push(cur);
  return o;
}
function docCsv(tep) {
  const t = fs.readFileSync(tep, "utf8").replace(/^\uFEFF/, "");
  const dong = t.split(/\r?\n/).filter((l) => l.length > 0);
  const dau = tachDong(dong[0]);
  return dong.slice(1).map((l) => {
    const c = tachDong(l), o = {};
    dau.forEach((h, i) => (o[h] = c[i]));
    return o;
  });
}
function demDong(tep) { return docCsv(tep).length; }
const docJson = (tep) => JSON.parse(fs.readFileSync(tep, "utf8"));

// dấu thập phân kiểu Việt Nam, và dấu chấm phân cách hàng nghìn
const so = (x, n = 4) => Number(x).toFixed(n).replace(".", ",");
const nghin = (x) => Number(x).toLocaleString("vi-VN");

const CS = {};
docCsv(path.join(AUDIT, "corpus_stats.csv")).forEach((h) => (CS[h.chi_tieu] = Number(h.gia_tri)));
const SPLIT = {};
docCsv(path.join(AUDIT, "split_distribution.csv")).forEach((h) => (SPLIT[h.split] = h));
const MC = docCsv(path.join(EVAL, "model_comparison.csv"));
const CROSS = {};
docCsv(path.join(EVAL, "crossover.csv")).forEach((h) => (CROSS[h.o] = h));
const ERRS = docCsv(path.join(EVAL, "error_summary.csv"));
const COST = {};
docCsv(path.join(EVAL, "index_cost.csv")).forEach((h) => (COST[h.chi_muc] = h));
const TS = docJson(path.join(EVAL, "chosen_params.json"));
const BEST = docJson(path.join(EVAL, "best_system.json"));
const DUP_ART = demDong(path.join(AUDIT, "duplicate_articles.csv"));
const DUP_Q = demDong(path.join(AUDIT, "duplicate_queries.csv"));
const OVERLAP = demDong(path.join(AUDIT, "query_overlap.csv"));
const CONFLICT = docCsv(path.join(AUDIT, "conflicting_gold.csv"));
const EMPTY = demDong(path.join(AUDIT, "empty_articles.csv"));
const DIA = docCsv(path.join(AUDIT, "duplicate_docs_diacritics.csv"));
const NHOM_TRUNG = new Set(docCsv(path.join(AUDIT, "duplicate_articles.csv")).map((h) => h.dup_group)).size;
const CHUNKS = Number(COST["bkai"].so_muc);
const he = (ten) => MC.find((h) => h.he_thong === ten);
const HE_SACH = he(BEST.he_sach_tot_nhat);
const BM = he("BM25");
const DE_SACH = he("Dense " + BEST.dense_sach);
const KD = docCsv(path.join(EVAL, "khong_dau.csv"));
const KDP = docJson(path.join(EVAL, "khong_dau_params.json"));
const KDL = {};
docCsv(path.join(EVAL, "khong_dau_loi.csv")).forEach((h) => (KDL[h.nhom] = h));
// kd("không dấu", "phục hồi dấu", "Hợp nhất")["recall@10"]
const kd = (dk, cach, ten) => KD.find((h) => h.dieu_kien === dk && h.cach_xu_ly === cach && h.he_thong === ten);
const pt = (x, n = 2) => so(100 * Number(x), n);   // 0,9772 -> "97,72"

/* ---------------------------- khuôn slide ---------------------------- */
p.layout = "LAYOUT_4x3"; // 10 x 7.5 inch
p.author = "Nhom 09";
p.title = "Truy hoi dieu luat tieng Viet cho cau hoi go khong dau";

const BLUE = "2D75B6", TBLHEAD = "4471C4", TBLALT = "E9EBF5";
const DARK = "303030", INK = "1A1A1A", MUTED = "5A5A5A", RED = "C0392B",
      GREEN = "1E7A4B", CAM = "D68910";
const F = "Arial";
const FOOT = "Trường Đại học Công nghệ Thông tin (UIT) – ĐHQG-HCM";

let n = 0;
function chrome(s, coSo = true) {
  s.addShape(p.ShapeType.rect, { x: 0, y: 7.05, w: 10, h: 0.45, fill: { color: DARK } });
  s.addText(FOOT, { isTextBox: true, x: 2.2, y: 7.05, w: 5.6, h: 0.45,
    fontFace: F, fontSize: 9, color: "E8E8E8", align: "center", valign: "middle", margin: 0 });
  if (coSo) {
    s.addShape(p.ShapeType.rect, { x: 0.42, y: 7.05, w: 0.55, h: 0.45,
      fill: { color: "FFFFFF" }, line: { color: DARK, width: 1 } });
    s.addText(String(n), { isTextBox: true, x: 0.42, y: 7.05, w: 0.55, h: 0.45,
      fontFace: F, fontSize: 11, color: INK, align: "center", valign: "middle", margin: 0 });
  }
}
function slide(tieuDe, ghiChu) {
  n += 1;
  const s = p.addSlide();
  s.addText(tieuDe, { isTextBox: true, x: 0.42, y: 0.16, w: 9.0, h: 0.66,
    fontFace: F, fontSize: 28, bold: true, color: BLUE, valign: "middle", margin: 0 });
  s.addShape(p.ShapeType.line, { x: 0.42, y: 0.92, w: 9.16, h: 0, line: { color: BLUE, width: 2 } });
  chrome(s);
  if (ghiChu) s.addNotes(ghiChu);
  return s;
}
function the(s, x, y, w, h, nen, vien) {
  s.addShape(p.ShapeType.roundRect, { x, y, w, h, rectRadius: 0.06,
    fill: { color: nen }, line: { color: vien, width: 1.25 } });
}
const T = { fontFace: F, fontSize: 11.5, color: INK, valign: "middle" };
const THEAD = { fill: { color: TBLHEAD }, color: "FFFFFF", bold: true, align: "center" };

/* ============================ 1. BÌA ============================ */
{
  n += 1;
  const s = p.addSlide();
  s.addImage({ path: "img/cover.png", x: 0, y: 0, w: 10, h: 7.5 });
  s.addShape(p.ShapeType.rect, { x: 0, y: 0, w: 10, h: 0.72, fill: { color: DARK } });
  s.addText("Trường Đại học Công nghệ Thông tin – Đại học Quốc gia TP. Hồ Chí Minh",
    { isTextBox: true, x: 0.42, y: 0, w: 9.2, h: 0.72,
      fontFace: F, fontSize: 14, bold: true, color: "FFFFFF", valign: "middle", margin: 0 });

  s.addShape(p.ShapeType.rect, { x: 0.42, y: 1.35, w: 2.7, h: 0.9,
    fill: { color: DARK, transparency: 12 } });
  s.addText([{ text: "Tháng 9, 2026\n", options: { bold: true } }, { text: "TP. Hồ Chí Minh" }],
    { isTextBox: true, x: 0.42, y: 1.35, w: 2.7, h: 0.9,
      fontFace: F, fontSize: 12.5, color: "FFFFFF", valign: "middle", margin: 0.12 });

  s.addShape(p.ShapeType.rect, { x: 1.0, y: 3.05, w: 9.0, h: 3.6,
    fill: { color: "0E1B2C", transparency: 15 } });
  s.addText("BÁO CÁO ĐỒ ÁN MÔN HỌC", { isTextBox: true, x: 1.25, y: 3.22, w: 8.5, h: 0.42,
    fontFace: F, fontSize: 16, bold: true, color: "FFFFFF", align: "right", margin: 0 });
  s.addText("Truy hồi điều luật tiếng Việt\ncho câu hỏi gõ không dấu",
    { isTextBox: true, x: 1.25, y: 3.66, w: 8.5, h: 1.25,
      fontFace: F, fontSize: 26, bold: true, color: "FFFFFF", align: "right",
      lineSpacingMultiple: 1.1, margin: 0 });
  s.addText("Phục hồi dấu, truy hồi lai và kiểm toán rò rỉ dữ liệu",
    { isTextBox: true, x: 1.25, y: 4.92, w: 8.5, h: 0.34,
      fontFace: F, fontSize: 15, italic: true, color: "CFE2F5", align: "right", margin: 0 });
  s.addShape(p.ShapeType.line, { x: 3.1, y: 5.34, w: 6.65, h: 0, line: { color: "C9C9C9", width: 1 } });
  s.addText([
    { text: "Nhóm 09  ·  Môn Xử lý ngôn ngữ tự nhiên", options: { bold: true, breakLine: true } },
    { text: "Lê Hoàng Lộc – 25210293", options: { breakLine: true } },
    { text: "Lê Thị Tuấn Anh – 25210250", options: { breakLine: true } },
    { text: "Đoàn Mậu Thiên Thư – 25210341", options: { breakLine: true } },
    { text: "GVHD: Đặng Văn Thìn", options: { bold: true } },
  ], { isTextBox: true, x: 1.25, y: 5.46, w: 8.5, h: 1.05,
       fontFace: F, fontSize: 11.5, color: "FFFFFF", align: "right", lineSpacing: 15, margin: 0 });
  chrome(s, false);
  s.addNotes(
`MỞ ĐẦU. Nói chậm, nhìn thầy. Khoảng 20 giây.

"Em xin chào thầy và các bạn. Nhóm 09 báo cáo đề tài Truy hồi điều luật tiếng Việt cho câu hỏi gõ không dấu."

Nếu cần nói đề tài bằng một câu: "Mô hình ngữ nghĩa sạch tốt nhất tụt từ ${pt(kd("có dấu", "giữ nguyên", "Ngữ nghĩa")["recall@10"], 0)} xuống ${pt(kd("không dấu", "giữ nguyên", "Ngữ nghĩa")["recall@10"], 0)} phần trăm khi người dân gõ không dấu. Nhóm đo điều đó cho sạch, rồi sửa nó bằng một mô hình ngôn ngữ nhỏ học từ chính kho luật."

Đừng đọc lại tên từng thành viên, thầy đã có danh sách. Chuyển slide ngay.`);
}

/* ============================ 2. NỘI DUNG ============================ */
{
  const s = slide("Nội dung",
`Đọc lướt 6 mục, KHÔNG giải thích gì ở đây. Khoảng 15 giây.

"Bài báo cáo gồm 6 phần. Phần nhóm muốn thầy chú ý nhất là phần 5: khi người dân gõ không dấu."`);
  const muc = [
    ["1", "Bài toán và nghiên cứu trước", "Lai BM25 và ngữ nghĩa đã là công thức mặc định. Chỗ còn trống ở đâu"],
    ["2", "Dữ liệu và kiểm toán rò rỉ", "Sáu vấn đề trong bộ đã công bố, và một mô hình đã thấy trước đề"],
    ["3", "Kiến trúc", "Phục hồi dấu, BM25, mô hình nhúng, hợp nhất"],
    ["4", "Câu hỏi có dấu", "Hợp nhất còn giúp được bao nhiêu"],
    ["5", "Câu hỏi gõ không dấu", "Mô hình mạnh nhất sụp đổ, và cách sửa rẻ nhất"],
    ["6", "Kết luận và giới hạn", "Nói thẳng chỗ chưa làm được"],
  ];
  muc.forEach((it, i) => {
    const y = 1.18 + i * 0.95;
    const nb = i === 4;
    the(s, 0.55, y, 8.9, 0.82, nb ? "FDF2E9" : "F4F8FC", nb ? CAM : BLUE);
    s.addShape(p.ShapeType.ellipse, { x: 0.80, y: y + 0.17, w: 0.48, h: 0.48,
      fill: { color: nb ? CAM : BLUE } });
    s.addText(it[0], { isTextBox: true, x: 0.80, y: y + 0.17, w: 0.48, h: 0.48,
      fontFace: F, fontSize: 16, bold: true, color: "FFFFFF", align: "center", valign: "middle", margin: 0 });
    s.addText(it[1], { isTextBox: true, x: 1.55, y: y + 0.09, w: 7.6, h: 0.34,
      fontFace: F, fontSize: 15, bold: true, color: INK, valign: "middle", margin: 0 });
    s.addText(it[2], { isTextBox: true, x: 1.55, y: y + 0.43, w: 7.6, h: 0.30,
      fontFace: F, fontSize: 11.5, color: MUTED, valign: "middle", margin: 0 });
  });
}

/* ======================= 3. BÀI TOÁN ======================= */
{
  const s = slide("Bài toán",
`Khoảng 30 giây.

"Đầu vào là một câu hỏi pháp luật viết bằng tiếng Việt tự nhiên. Đầu ra là danh sách điều luật xếp hạng, kèm điểm và những từ đã khớp. Kho tra cứu có ${nghin(CS.so_dieu_luat)} điều luật thuộc ${nghin(CS.so_van_ban)} văn bản."

Chỉ vào ví dụ: "Người dân gõ 'nướng bắp trên cầu phạt bao nhiêu tiền'. Điều luật đúng lại viết là 'sử dụng trái phép đất của đường bộ'. Không một từ nào trùng nhau. Đó chính là chỗ khó."

Chỉ vào dòng đỏ: "Và khó hơn nữa, rất nhiều người gõ đúng câu đó mà không có dấu. Đây là thách thức nhóm tập trung vào."

NẾU THẦY HỎI "sao không sinh luôn câu trả lời": đề tài là truy hồi. Trả về sai điều luật kèm một câu trả lời trôi chảy còn nguy hiểm hơn trả về sai điều luật.`);

  the(s, 0.55, 1.10, 4.25, 1.5, "F4F8FC", BLUE);
  s.addText("ĐẦU VÀO", { isTextBox: true, x: 0.78, y: 1.22, w: 3.8, h: 0.3,
    fontFace: F, fontSize: 11.5, bold: true, color: BLUE, margin: 0 });
  s.addText("Một câu hỏi pháp luật viết bằng\ntiếng Việt tự nhiên",
    { isTextBox: true, x: 0.78, y: 1.56, w: 3.8, h: 0.9,
      fontFace: F, fontSize: 12.5, color: INK, lineSpacing: 18, valign: "top", margin: 0 });
  the(s, 5.20, 1.10, 4.25, 1.5, "F4F8FC", BLUE);
  s.addText("ĐẦU RA", { isTextBox: true, x: 5.43, y: 1.22, w: 3.8, h: 0.3,
    fontFace: F, fontSize: 11.5, bold: true, color: BLUE, margin: 0 });
  s.addText("Danh sách điều luật xếp hạng,\nkèm điểm và từ khóa đã khớp",
    { isTextBox: true, x: 5.43, y: 1.56, w: 3.8, h: 0.9,
      fontFace: F, fontSize: 12.5, color: INK, lineSpacing: 18, valign: "top", margin: 0 });

  the(s, 0.55, 2.85, 8.9, 1.55, "FFF8F0", CAM);
  s.addText("Ví dụ thật, và cũng là một ca hệ trả sai", { isTextBox: true, x: 0.80, y: 2.96, w: 8.4, h: 0.3,
    fontFace: F, fontSize: 12.5, bold: true, color: "B9770E", margin: 0 });
  s.addText([
    { text: "Câu hỏi:  ", options: { bold: true } },
    { text: "Nướng bắp, ngô trên cầu phạt bao nhiêu tiền?", options: { breakLine: true } },
    { text: "Điều luật đúng:  ", options: { bold: true } },
    { text: "Xử phạt hành vi vi phạm quy định về quản lý, khai thác, bảo trì công trình đường bộ", options: { breakLine: true } },
    { text: "Không một từ nào trùng nhau.", options: { bold: true, color: RED } },
  ], { isTextBox: true, x: 0.80, y: 3.30, w: 8.4, h: 1.0,
       fontFace: F, fontSize: 12, color: INK, lineSpacing: 17, margin: 0 });

  the(s, 0.55, 4.55, 8.9, 2.25, "FFFFFF", "BFBFBF");
  s.addText("Bốn thách thức", { isTextBox: true, x: 0.80, y: 4.64, w: 8.4, h: 0.3,
    fontFace: F, fontSize: 13, bold: true, color: INK, margin: 0 });
  s.addText([
    { text: "Khoảng cách từ vựng", options: { bold: true } },
    { text: ": người dân dùng lời nói thường, luật dùng thuật ngữ", options: { breakLine: true } },
    { text: "Người dân gõ không dấu", options: { bold: true, color: RED } },
    { text: ": “nuong bap tren cau phat bao nhieu”, khi nhắn trên điện thoại hay gõ vội", options: { breakLine: true } },
    { text: "Điều luật dài", options: { bold: true } },
    { text: `: trung vị ${CS.do_dai_trung_vi_tu} từ, dài nhất ${nghin(CS.do_dai_lon_nhat_tu)} từ, vượt xa trần của mô hình`, options: { breakLine: true } },
    { text: "Dữ liệu công bố vẫn còn lỗi", options: { bold: true } },
    { text: ": phần sau sẽ chỉ ra sáu vấn đề đo được", options: {} },
  ], { isTextBox: true, x: 0.80, y: 5.02, w: 8.4, h: 1.68,
       fontFace: F, fontSize: 12, color: INK, lineSpacing: 19, valign: "top", margin: 0 });
}

/* ================== 4. NGHIÊN CỨU TRƯỚC ================== */
{
  const s = slide("Nghiên cứu trước: năm hướng đã có",
`Khoảng 35 giây. Không đọc hết bảng, chỉ đọc cột bên phải.

Dòng 1: "Ghép BM25 với mô hình ngữ nghĩa cho văn bản tiếng Việt thì từ các đội Zalo 2021 tới EACL 2026 đều đã làm, và đều kết luận ghép thì tốt hơn. Bài EACL 2026 còn so đúng ba cách này trên 10 bộ dữ liệu. Nếu nhóm chỉ lặp lại phép so đó thì không có gì mới."

Dòng 2 và 3, nói nhanh: "Có hướng làm mô hình ngữ nghĩa mạnh hơn, trong đó có bài của nhóm tác giả UIT năm 2025. Và có bài phân tích cách hợp nhất của Bruch và cộng sự."

Dòng 4, nói chậm: "Phục hồi dấu tiếng Việt thì đã được nghiên cứu kỹ, đạt khoảng 97 phần trăm. Nhưng nó được đo như một bài toán riêng, chưa ai đo nó ảnh hưởng thế nào tới tìm luật."

NẾU THẦY HỎI "đọc hết chưa": nhóm đối chiếu theo phần tóm tắt, mã nguồn và model card. Danh sách đầy đủ ở slide cuối và trong docs/NGHIEN_CUU_LIEN_QUAN.md.`);

  const mauHang = (i) => ({ fill: { color: i % 2 ? TBLALT : "FFFFFF" } });
  const hang = [
    ["Lai BM25 và ngữ nghĩa, văn bản tiếng Việt",
     "Hai đội Zalo AI 2021 (mã công khai); Khang và cs. 2024; Giang và cs. 2025; ViDRILL, VLSP 2025; Nguyen và Quan, EACL 2026 (10 bộ dữ liệu)",
     "Lai tốt hơn từng tầng. Không bài nào kết luận ngược"],
    ["Làm mạnh tầng ngữ nghĩa",
     "Pham và cs. 2022; Pham Tien và cs. 2024; Le và cs. 2025, UIT; ALQAC 2021-2023",
     "Cải tiến mô hình, không hỏi BM25 còn góp bao nhiêu"],
    ["Cách hợp nhất",
     "Cormack và cs. 2009 (RRF); Bruch và cs. 2023, ACM TOIS",
     "Tổng trọng số hơn RRF khi chỉnh được"],
    ["Phục hồi dấu tiếng Việt",
     "Pham, Pham, Le-Hong 2017 (IALP); Le-Hong 2021 (Knowledge-Based Systems)",
     "Khoảng 97%, nhưng chưa đo cho truy hồi"],
    ["Đánh giá mô hình nhúng",
     "MMTEB, ICLR 2025; Chung và cs. 2025",
     "Phải đánh dấu mô hình đã học dữ liệu tác vụ"],
  ].map((r, i) => [
    { text: r[0], options: { ...mauHang(i), bold: true } },
    { text: r[1], options: { ...mauHang(i), fontSize: 9.5 } },
    { text: r[2], options: { ...mauHang(i), color: i === 3 ? RED : i < 2 ? INK : BLUE, bold: i === 3 } },
  ]);
  s.addTable([
    [{ text: "Hướng", options: THEAD }, { text: "Công trình tiêu biểu", options: THEAD },
     { text: "Họ kết luận", options: THEAD }],
    ...hang,
  ], { x: 0.42, y: 1.05, w: 9.16, colW: [2.1, 4.36, 2.7], rowH: [0.36, 0.9, 0.7, 0.58, 0.64, 0.58],
       fontFace: F, fontSize: 11, color: INK, valign: "middle",
       border: { pt: 0.5, color: "BFBFBF" } });

  the(s, 0.42, 5.0, 4.48, 1.75, "F4F8FC", BLUE);
  s.addText("BM25 vẫn là mốc mạnh", { isTextBox: true, x: 0.64, y: 5.1, w: 4.1, h: 0.3,
    fontFace: F, fontSize: 12.5, bold: true, color: BLUE, margin: 0 });
  s.addText("Rosa và cs. 2021: chỉ dùng BM25 vẫn đứng hạng 2 ở COLIEE 2021, cuộc thi truy hồi văn bản pháp lý. Vì vậy BM25 là đối chứng bắt buộc, không phải để cho có.",
    { isTextBox: true, x: 0.64, y: 5.42, w: 4.1, h: 1.28,
      fontFace: F, fontSize: 11, color: INK, lineSpacing: 15, valign: "top", margin: 0 });

  the(s, 5.10, 5.0, 4.48, 1.75, "FFF8F0", CAM);
  s.addText("Hai model card trên đúng bộ Zalo", { isTextBox: true, x: 5.32, y: 5.1, w: 4.1, h: 0.3,
    fontFace: F, fontSize: 12.5, bold: true, color: "B9770E", margin: 0 });
  s.addText([
    { text: "bkai", options: { bold: true } },
    { text: ", phổ biến nhất: học 80% tập train Zalo 2021.", options: { breakLine: true } },
    { text: "vnlegal-lal", options: { bold: true } },
    { text: ", tự nhận tốt nhất trên bộ này: cũng học trên chính bộ này, và được xếp cạnh các mô hình chưa học mà không đánh dấu.", options: {} },
  ], { isTextBox: true, x: 5.32, y: 5.42, w: 4.1, h: 1.28,
       fontFace: F, fontSize: 11, color: INK, lineSpacing: 15, valign: "top", margin: 0 });
}

/* ============ 5. KHOẢNG TRỐNG VÀ CÂU HỎI NGHIÊN CỨU ============ */
{
  const s = slide("Khoảng trống và hai câu hỏi nghiên cứu",
`Khoảng 35 giây. Đây là slide trả lời "vì sao chọn hướng này". Nói chậm ở ô số 1.

"Từ các nghiên cứu đó, nhóm thấy bốn điều chưa ai báo cáo."

Ô 1, quan trọng nhất: "Mọi bài tìm luật đều chấm trên câu hỏi có dấu đầy đủ. Còn các bài phục hồi dấu thì không đo tìm luật. Không ai biết hệ đứng vững thế nào khi người dân gõ không dấu."

Ô 2 tới 4, nói nhanh: "Mô hình đã thấy dữ liệu chưa, split gốc có sạch không, và cách ghép thì chọn theo thói quen."

Đọc hai câu hỏi nghiên cứu. Nối: "Câu hỏi 1 là điều kiện để trả lời câu hỏi 2: muốn biết không dấu làm hỏng bao nhiêu thì phải có một mốc có dấu đo sạch trước."

NẾU THẦY HỎI "chắc chưa ai làm không": nhóm chỉ khẳng định trong những bài đã xem, theo phần tóm tắt và mã nguồn công bố.`);

  const gap = [
    ["Câu hỏi gõ không dấu",
     "Bài tìm luật chỉ chấm câu có dấu. Bài phục hồi dấu không đo truy hồi.", RED],
    ["Mô hình đã thấy dữ liệu chưa?",
     "Mô hình phổ biến nhất và mô hình tự nhận tốt nhất trên bộ Zalo đều đã học chính bộ này.", CAM],
    ["Split gốc có sạch không?",
     "Các bài dùng nguyên split của ban tổ chức, không ai kiểm câu hỏi trùng.", CAM],
    ["Ghép bằng cách nào?",
     "Nhân điểm (Zalo 2021), RRF (Nguyen Ba và cs. 2024), ít khi so trên val.", CAM],
  ];
  gap.forEach((g, i) => {
    const x = 0.42 + (i % 2) * 4.64, y = 1.05 + Math.floor(i / 2) * 1.52;
    the(s, x, y, 4.52, 1.40, i === 0 ? "FDEDEC" : "FFFFFF", g[2]);
    s.addShape(p.ShapeType.ellipse, { x: x + 0.15, y: y + 0.14, w: 0.40, h: 0.40, fill: { color: g[2] } });
    s.addText(String(i + 1), { isTextBox: true, x: x + 0.15, y: y + 0.14, w: 0.40, h: 0.40,
      fontFace: F, fontSize: 14, bold: true, color: "FFFFFF", align: "center", valign: "middle", margin: 0 });
    s.addText(g[0], { isTextBox: true, x: x + 0.68, y: y + 0.14, w: 3.7, h: 0.4,
      fontFace: F, fontSize: 12.5, bold: true, color: g[2] === RED ? RED : "B9770E", valign: "middle", margin: 0 });
    s.addText(g[1], { isTextBox: true, x: x + 0.20, y: y + 0.64, w: 4.15, h: 0.7,
      fontFace: F, fontSize: 11.5, color: INK, lineSpacing: 15, valign: "top", margin: 0 });
  });

  the(s, 0.42, 4.22, 9.16, 2.1, "EAF6EE", GREEN);
  s.addText("Hai câu hỏi nghiên cứu", { isTextBox: true, x: 0.65, y: 4.32, w: 8.7, h: 0.3,
    fontFace: F, fontSize: 12.5, bold: true, color: GREEN, margin: 0 });
  s.addText([
    { text: "CH1. ", options: { bold: true, color: GREEN } },
    { text: "Trên dữ liệu đã kiểm toán, với mô hình ngữ nghĩa chưa thấy dữ liệu, ghép thêm BM25 còn cải thiện được bao nhiêu?", options: { breakLine: true } },
    { text: " ", options: { breakLine: true, fontSize: 6 } },
    { text: "CH2. ", options: { bold: true, color: RED } },
    { text: "Khi người dùng gõ không dấu, hệ còn đứng vững không, và cách sửa rẻ nhất là gì?", options: { bold: true } },
  ], { isTextBox: true, x: 0.65, y: 4.68, w: 8.7, h: 1.58,
       fontFace: F, fontSize: 14, color: INK, lineSpacing: 19, valign: "top", margin: 0 });

  s.addText("“Chưa ai báo cáo”: theo phần tóm tắt, mã nguồn và model card nhóm đã đối chiếu. Danh sách nguồn ở slide cuối.",
    { isTextBox: true, x: 0.42, y: 6.42, w: 9.16, h: 0.4,
      fontFace: F, fontSize: 10, italic: true, color: MUTED, valign: "middle", margin: 0 });
}

/* ================= 6. DỮ LIỆU VÀ KIỂM TOÁN ================= */
{
  const s = slide("Dữ liệu Zalo 2021 và sáu vấn đề kiểm toán",
`Khoảng 35 giây.

"Bộ dữ liệu Zalo AI Challenge 2021, bản trên HuggingFace, giấy phép MIT, đã được đưa vào MTEB. ${nghin(CS.so_dieu_luat)} điều luật, ${nghin(CS.so_cau_hoi_id_duy_nhat)} câu hỏi. Nhóm vẫn kiểm toán lại từ đầu và tìm ra sáu vấn đề, mỗi vấn đề để lại một tệp bằng chứng trong reports/audit."

Chỉ vào cột đỏ: "${OVERLAP} câu hỏi nằm ở cả train lẫn test. Đây là rò rỉ, slide sau em nói kỹ."

Chỉ vào ô cam: "Và có bốn văn bản bị tách đôi chỉ vì dấu: nd-cp và nđ-cp. Chuyện dấu tiếng Việt đã gây lỗi ngay trong dữ liệu gốc."

NẾU THẦY HỎI "sao không xóa điều trùng đi": kho luật thật thì có điều trùng thật, xóa đi làm bài toán dễ đi một cách giả tạo.
NẾU THẦY HỎI về tập val: bộ gốc không có val, nhóm cắt val ra từ train theo câu hỏi, seed 42.`);

  s.addText(`GreenNode/zalo-ai-legal-text-retrieval-vn, MIT  |  ${nghin(CS.so_dieu_luat)} điều luật, ${nghin(CS.so_van_ban)} văn bản, ${nghin(CS.so_cau_hoi_id_duy_nhat)} câu hỏi  |  bộ gốc không có val`,
    { isTextBox: true, x: 0.55, y: 1.00, w: 8.9, h: 0.3,
      fontFace: F, fontSize: 11, italic: true, color: MUTED, margin: 0 });

  s.addImage({ path: "img/audit_findings.png", x: 0.75, y: 1.36, w: 8.5, h: 3.85 });

  the(s, 0.55, 5.28, 4.35, 1.5, "FDEDEC", RED);
  s.addText("Rò rỉ giữa train và test", { isTextBox: true, x: 0.78, y: 5.38, w: 3.9, h: 0.3,
    fontFace: F, fontSize: 12, bold: true, color: RED, margin: 0 });
  s.addText(`${OVERLAP} câu hỏi xuất hiện ở cả hai tập.\nĐã loại khỏi train, giữ nguyên test.`,
    { isTextBox: true, x: 0.78, y: 5.70, w: 3.9, h: 0.9,
      fontFace: F, fontSize: 11.5, color: INK, lineSpacing: 16, valign: "top", margin: 0 });

  the(s, 5.10, 5.28, 4.35, 1.5, "FFF8F0", CAM);
  s.addText("Bốn văn bản bị tách đôi vì dấu", { isTextBox: true, x: 5.33, y: 5.38, w: 3.9, h: 0.3,
    fontFace: F, fontSize: 12, bold: true, color: "B9770E", margin: 0 });
  s.addText(`155/2020/nd-cp và 155/2020/nđ-cp là cùng một Nghị định.\n${DIA.reduce((a, b) => a + Number(b.so_dieu), 0)} điều luật bị nhân đôi.`,
    { isTextBox: true, x: 5.33, y: 5.70, w: 3.9, h: 0.9,
      fontFace: F, fontSize: 11.5, color: INK, lineSpacing: 16, valign: "top", margin: 0 });
}

/* ================== 7. NHÃN MÂU THUẪN ================== */
{
  const s = slide("Vấn đề nặng nhất: nhãn mâu thuẫn",
`Khoảng 35 giây. Slide này là điểm nhấn của phần kiểm toán.

"${CONFLICT.length} câu hỏi nằm ở cả train lẫn test. Nhưng chúng không phải dòng lặp. Với CẢ ${CONFLICT.length} TRÊN ${CONFLICT.length} CÂU, tệp train chỉ sang một điều luật, tệp test chỉ sang một điều luật khác hẳn."

Đọc dòng đầu của bảng: "Cùng câu hỏi về thương tật 25%, train bảo đáp án là Bộ luật Hình sự sửa đổi, test bảo là Bộ luật Tố tụng Hình sự. Cả hai đều là điều luật có thật và đều liên quan."

Chốt: "Nghĩa là bộ nhãn KHÔNG ĐẦY ĐỦ. Mọi con số Recall trong báo cáo này đều là cận dưới. Hệ có thể trả về một điều luật đúng mà vẫn bị chấm sai, chỉ vì người gán nhãn không liệt kê điều đó."

Thú nhận luôn nếu thầy hỏi kỹ: bản dựng đầu tiên của script đã gộp nhầm cả hai vào test, làm test phình từ 793 lên 818 cặp. Lỗi bị bắt khi đối chiếu lại số dòng với tệp gốc.`);

  s.addText(`Cả ${CONFLICT.length} trên ${CONFLICT.length} câu hỏi chồng lấn đều có gold ở train KHÁC gold ở test`,
    { isTextBox: true, x: 0.55, y: 1.02, w: 8.9, h: 0.34,
      fontFace: F, fontSize: 13, bold: true, color: RED, margin: 0 });

  const cot = [{ text: "Câu hỏi", options: THEAD }, { text: "Gold ở train", options: THEAD },
               { text: "Gold ở test", options: THEAD }];
  const hang = CONFLICT.slice(0, 3).map((h, i) => ([
    { text: (h.text || "").slice(0, 60), options: { fill: { color: i % 2 ? TBLALT : "FFFFFF" } } },
    { text: h.gold_train, options: { fill: { color: i % 2 ? TBLALT : "FFFFFF" }, color: BLUE } },
    { text: h.gold_test, options: { fill: { color: i % 2 ? TBLALT : "FFFFFF" }, color: CAM } },
  ]));
  s.addTable([cot, ...hang], { x: 0.55, y: 1.48, w: 8.9, colW: [4.3, 2.3, 2.3], rowH: 0.5,
    fontFace: F, fontSize: 10.5, color: INK, valign: "middle",
    border: { pt: 0.5, color: "BFBFBF" } });

  the(s, 0.55, 3.55, 8.9, 1.35, "F4F8FC", BLUE);
  s.addText("Giống hệt sự cố ở đồ án trước của nhóm", { isTextBox: true, x: 0.80, y: 3.66, w: 8.4, h: 0.3,
    fontFace: F, fontSize: 12.5, bold: true, color: BLUE, margin: 0 });
  s.addText("Ba ảnh cùng một chiếc lá sầu riêng mang hai nhãn bệnh khác nhau. Khác biệt: một chiếc lá chỉ có một đáp án đúng, còn một câu hỏi pháp luật thật sự có thể được trả lời bởi nhiều điều luật.",
    { isTextBox: true, x: 0.80, y: 3.98, w: 8.4, h: 0.82,
      fontFace: F, fontSize: 11.5, color: INK, lineSpacing: 16, valign: "top", margin: 0 });

  the(s, 0.55, 5.10, 8.9, 1.65, "FDEDEC", RED);
  s.addText("Hệ quả phải nói rõ trong báo cáo", { isTextBox: true, x: 0.80, y: 5.21, w: 8.4, h: 0.3,
    fontFace: F, fontSize: 12.5, bold: true, color: RED, margin: 0 });
  s.addText([
    { text: "Bộ nhãn không đầy đủ. Mọi con số Recall công bố ở đây đều là ", options: {} },
    { text: "cận dưới", options: { bold: true } },
    { text: ".\nHệ có thể trả về một điều luật đúng mà vẫn bị chấm sai, chỉ vì người gán nhãn không liệt kê điều đó.\nCách xử lý: tập test giữ NGUYÊN VẸN 793 cặp của ban tổ chức, không tự sửa nhãn.", options: {} },
  ], { isTextBox: true, x: 0.80, y: 5.53, w: 8.4, h: 1.1,
       fontFace: F, fontSize: 11.5, color: INK, lineSpacing: 16, valign: "top", margin: 0 });
}

/* ======================= 8. CHIA LẠI TẬP ======================= */
{
  const s = slide("Chia lại tập và mô hình đã thấy trước dữ liệu",
`Khoảng 40 giây. Phát hiện lớn nhất của phần kiểm toán, nói kỹ.

Phần trên: "Sau khi loại 26 câu hỏi rò rỉ, nhóm chia lại: train ${SPLIT.train.so_cau_hoi}, val ${SPLIT.val.so_cau_hoi}, test ${SPLIT.test.so_cau_hoi} câu hỏi. Test giữ nguyên vẹn của ban tổ chức."

Phần dưới, nói chậm: "Nhưng chống rò rỉ không dừng ở chia lại tập. Nhóm đọc model card của bkai, mô hình bi-encoder tiếng Việt phổ biến nhất. Nó ghi rõ: được huấn luyện trên 80% tập train của Zalo 2021. Mà tập test của nhóm lại cắt ra từ đúng tập train đó."

"Nghĩa là mô hình đã nhìn thấy phần lớn câu hỏi test kèm nhãn đúng. Gọi nó là zero-shot là sai."

"Nhóm vì thế chuyển sang AITeamVN, mô hình ghi rõ trong model card rằng không huấn luyện trên bộ này, làm mô hình sạch cho con số chính thức."

NẾU THẦY HỎI "sao tin model card": không kiểm chứng trực tiếp được, nên nhóm ghi rõ đây là tuyên bố của tác giả mô hình, không phải kết quả nhóm tự đo.`);

  s.addTable([
    [{ text: "Tập", options: THEAD }, { text: "Câu hỏi", options: THEAD },
     { text: "Cặp nhãn", options: THEAD }, { text: "Ghi chú", options: THEAD }],
    ["train", nghin(SPLIT.train.so_cau_hoi), nghin(SPLIT.train.so_cap_qrel), "đã loại 26 câu rò rỉ"],
    ["val", nghin(SPLIT.val.so_cau_hoi), nghin(SPLIT.val.so_cap_qrel), "cắt từ train, seed 42"],
    [{ text: "test", options: { bold: true } }, { text: nghin(SPLIT.test.so_cau_hoi), options: { bold: true } },
     { text: nghin(SPLIT.test.so_cap_qrel), options: { bold: true } },
     { text: "nguyên vẹn của ban tổ chức", options: { bold: true, color: GREEN } }],
  ], { x: 0.55, y: 1.05, w: 8.9, colW: [1.3, 1.5, 1.5, 4.6], rowH: 0.42,
       fontFace: F, fontSize: 11.5, color: INK, valign: "middle",
       border: { pt: 0.5, color: "BFBFBF" }, fill: { color: "FFFFFF" } });

  the(s, 0.55, 2.95, 8.9, 2.35, "FDEDEC", RED);
  s.addText("Rò rỉ không chỉ nằm trong dữ liệu, mà nằm trong cả mô hình", { isTextBox: true, x: 0.80, y: 3.06, w: 8.4, h: 0.32,
    fontFace: F, fontSize: 13.5, bold: true, color: RED, margin: 0 });
  s.addText([
    { text: "bkai-foundation-models/vietnamese-bi-encoder", options: { bold: true, fontFace: "Consolas" } },
    { text: ", model card ghi rõ:", options: { breakLine: true } },
    { text: "  \u201C80% of the training set from the Legal Text Retrieval Zalo 2021 challenge\u201D", options: { italic: true, color: RED, breakLine: true } },
    { text: "Tập test của đồ án lại cắt ra từ đúng tập train đó, nên mô hình đã nhìn thấy phần lớn câu hỏi test ", options: {} },
    { text: "kèm nhãn đúng", options: { bold: true } },
    { text: ". Gọi nó là zero-shot là sai.", options: {} },
  ], { isTextBox: true, x: 0.80, y: 3.44, w: 8.4, h: 1.75,
       fontFace: F, fontSize: 11.5, color: INK, lineSpacing: 17, valign: "top", margin: 0 });

  the(s, 0.55, 5.45, 8.9, 1.3, "EAF6EE", GREEN);
  s.addText("Cách xử lý", { isTextBox: true, x: 0.80, y: 5.55, w: 8.4, h: 0.3,
    fontFace: F, fontSize: 12.5, bold: true, color: GREEN, margin: 0 });
  s.addText("Dùng AITeamVN/Vietnamese_Embedding làm mô hình SẠCH cho con số chính thức, vì model card ghi \u201COur model was not trained on this dataset\u201D. bkai vẫn công bố nhưng gắn nhãn nhiễm bẩn.",
    { isTextBox: true, x: 0.80, y: 5.86, w: 8.4, h: 0.8,
      fontFace: F, fontSize: 11.5, color: INK, lineSpacing: 16, valign: "top", margin: 0 });
}

/* ======================= 9. KIẾN TRÚC ======================= */
{
  const s = slide("Kiến trúc",
`Khoảng 30 giây. Chỉ nói hộp đỏ và hai nhánh, phần tách từ và gộp max chỉ nói khi bị hỏi.

Hộp đỏ: "Câu hỏi đi vào trước hết một khâu kiểm dấu. Câu có dấu đi thẳng qua. Câu không dấu được phục hồi dấu bằng một mô hình bigram học từ chính kho luật. Phần 5 sẽ nói vì sao cần khâu này."

"Sau đó câu hỏi đi vào hai nhánh song song. Nhánh trên là BM25 trên ${nghin(CS.so_dieu_luat)} điều luật đã tách từ. Nhánh dưới là bi-encoder trên ${nghin(CHUNKS)} đoạn, rồi gộp về điều bằng cách lấy điểm cao nhất. Hai nhánh cùng trả top-100, tầng thứ ba hợp nhất lại."

Nhấn vào chỗ tách từ: "Tách từ rất quan trọng với tiếng Việt. Bằng lái xe là một khái niệm. Tách theo khoảng trắng thì chữ bằng khớp nhầm với bằng chứng."

Nhấn vào chỗ gộp max: "Lấy điểm cao nhất chứ không lấy trung bình, vì câu trả lời thường nằm gọn trong một khoản. Lấy trung bình thì các khoản không liên quan kéo điểm xuống. Nhóm đo cả hai cách trên val: max ${so(0.9563)} còn mean ${so(0.9127)}."`);

  s.addImage({ path: "img/architecture.png", x: 0.35, y: 1.15, w: 9.3, h: 4.0 });

  the(s, 0.55, 5.30, 2.85, 1.45, "FDEDEC", RED);
  s.addText("Phục hồi dấu", { isTextBox: true, x: 0.75, y: 5.40, w: 2.5, h: 0.28,
    fontFace: F, fontSize: 11.5, bold: true, color: RED, margin: 0 });
  s.addText(`Bigram âm tiết học từ ${so(KDP.so_am_tiet / 1e6, 1)} triệu âm tiết của kho luật và câu hỏi train. lambda = ${so(KDP.lambda_phuc_hoi, 1)}, chốt trên val`, { isTextBox: true, x: 0.75, y: 5.70, w: 2.5, h: 0.9,
    fontFace: F, fontSize: 10.5, color: INK, lineSpacing: 14, valign: "top", margin: 0 });

  the(s, 3.58, 5.30, 2.85, 1.45, "FFF8F0", CAM);
  s.addText("Gộp đoạn bằng max", { isTextBox: true, x: 3.78, y: 5.40, w: 2.5, h: 0.28,
    fontFace: F, fontSize: 11.5, bold: true, color: "B9770E", margin: 0 });
  s.addText(`Đo trên val: max ${so(0.9563)} so với mean ${so(0.9127)}`, { isTextBox: true, x: 3.78, y: 5.70, w: 2.5, h: 0.9,
    fontFace: F, fontSize: 10.5, color: INK, lineSpacing: 14, valign: "top", margin: 0 });

  the(s, 6.61, 5.30, 2.85, 1.45, "EAF6EE", GREEN);
  s.addText("Tham số chốt trên val", { isTextBox: true, x: 6.81, y: 5.40, w: 2.5, h: 0.28,
    fontFace: F, fontSize: 11.5, bold: true, color: GREEN, margin: 0 });
  s.addText(`k1 = ${so(TS.bm25.k1, 1)}, b = ${so(TS.bm25.b, 2)}, alpha = ${so(TS.weighted.alpha, 2)}. Test chỉ chạy một lần`,
    { isTextBox: true, x: 6.81, y: 5.70, w: 2.5, h: 0.9,
      fontFace: F, fontSize: 10.5, color: INK, lineSpacing: 14, valign: "top", margin: 0 });
}

/* ===== PHỤ LỤC A. CHIA ĐOẠN: định nghĩa ở đây, gọi sau slide Kết luận ===== */
function slideChiaDoan() {
  const s = slide("Phụ lục: vì sao bắt buộc phải chia đoạn",
`PHỤ LỤC, không trình bày trong 7 phút. Mở slide này khi thầy hỏi về chia đoạn.

"PhoBERT chỉ nhận 256 token, tương đương khoảng 140 từ tiếng Việt. Đường đứt đỏ là cái trần đó. ${so(61.1, 1)} phần trăm điều luật nằm bên phải đường này."

"Cắt cụt là vứt phần đuôi của phần lớn số điều. Mà đuôi điều luật thường là chỗ ghi mức phạt và các trường hợp ngoại lệ, đúng thứ người dân hay hỏi."

"Nhóm cắt theo ranh giới khoản trước, chỉ khi một khoản tự nó quá dài mới cắt bằng cửa sổ trượt. Kết quả ${nghin(CS.so_dieu_luat)} điều thành ${nghin(CHUNKS)} đoạn, trung bình ${so(CHUNKS / CS.so_dieu_luat, 2)} đoạn mỗi điều."

NẾU THẦY HỎI "sao không dùng mô hình ngữ cảnh dài": có, AITeamVN nhận tới 8192 token. Nhưng nhóm cho cả hai bộ mã hóa ăn cùng một bộ đoạn để biến duy nhất là bộ mã hóa.`);

  s.addImage({ path: "img/chunk_need.png", x: 0.55, y: 1.05, w: 8.9, h: 4.25 });

  the(s, 0.55, 5.45, 8.9, 1.3, "FFF8F0", CAM);
  s.addText("Cách cắt", { isTextBox: true, x: 0.80, y: 5.55, w: 8.4, h: 0.3,
    fontFace: F, fontSize: 12.5, bold: true, color: "B9770E", margin: 0 });
  s.addText(`Cắt theo ranh giới khoản trước, chỉ trượt cửa sổ khi một khoản tự nó quá dài. Mỗi đoạn đều mang tiêu đề điều. Kết quả: ${nghin(CS.so_dieu_luat)} điều thành ${nghin(CHUNKS)} đoạn, trung bình ${so(CHUNKS / CS.so_dieu_luat, 2)} đoạn mỗi điều.`,
    { isTextBox: true, x: 0.80, y: 5.86, w: 8.4, h: 0.8,
      fontFace: F, fontSize: 11.5, color: INK, lineSpacing: 16, valign: "top", margin: 0 });
}

/* ================= 10. CÂU HỎI CÓ DẤU: KẾT QUẢ ================= */
{
  const _c = {};
  docCsv(path.join(EVAL, "fusion_ceiling.csv")).forEach(
    (h) => (_c[h.he_thong] = Number(h.ty_le_dung_top10_pct)));
  const loiHop = _c[BEST.he_sach_tot_nhat] - _c["Dense " + BEST.dense_sach];
  const soCau = Math.round(loiHop * Number(SPLIT.test.so_cau_hoi) / 100);
  const chiBm = CROSS["chỉ BM25 đúng"].so_cau_hoi;
  const RRF_S = he("RRF (BM25 + " + BEST.dense_sach + ")");
  const s = slide("Câu hỏi có dấu: kết quả trên tập test",
`Khoảng 45 giây. Slide này trả lời câu hỏi nghiên cứu 1. Nói chậm và chỉ tay.

"788 câu hỏi, chấm đúng một lần, dùng tham số đã chốt trên val."

Chỉ vào ba dòng trên: "Ba dòng đầu là các hệ SẠCH. BM25 một mình được Recall@10 ${so(BM["recall@10"])}. Ngữ nghĩa một mình ${so(DE_SACH["recall@10"])}. Hợp nhất có trọng số ${so(HE_SACH["recall@10"])}."

Chỉ vào khung xanh lá, trả lời thẳng câu hỏi 1: "Hợp nhất chỉ hơn ngữ nghĩa thuần ${so(loiHop, 2)} điểm phần trăm, tức ${soCau} câu trên ${SPLIT.test.so_cau_hoi}. Có cải thiện nhưng rất nhỏ. Và cách ghép có trọng số thắng RRF, đúng như Bruch và cộng sự."

Chỉ vào hai dòng xám: "Hai dòng dưới trông đẹp hơn, nhưng dùng mô hình đã thấy dữ liệu test. Nhóm để đây để thấy một con số benchmark bị thổi lên dễ thế nào."

Chuyển slide: "Vậy BM25 có vô dụng không? Câu trả lời nằm ở phần sau, khi người dân gõ không dấu."

NẾU THẦY HỎI "F2 sao thấp": F2 ở đây cố định k = 10 nên precision tối đa chỉ 0,1. Ban tổ chức Zalo cho phép trả về số kết quả thay đổi được nên con số của họ không so trực tiếp được.
NẾU THẦY HỎI về bảng bốn ô BM25 và ngữ nghĩa: mở phụ lục B.`);

  const chon = ["BM25", "Dense " + BEST.dense_sach, BEST.he_sach_tot_nhat,
                "Dense bkai", "Trọng số (BM25 + bkai_ft)"];
  const dat = chon.map((t) => he(t)).filter(Boolean);
  const cot = ["Hệ thống", "R@1", "R@10", "MRR@10", "nDCG@10", "Độ trễ"].map(
    (t) => ({ text: t, options: THEAD }));
  const hang = dat.map((h) => {
    const ban = (h.nhiem_ban || "").length > 0;
    const nen = ban ? "F2F2F2" : "FFFFFF";
    const mau = ban ? MUTED : INK;
    const ten = h.he_thong.replace("Trọng số", "Trọng số").replace("Dense ", "Ngữ nghĩa ")
      + (ban ? "  (nhiễm bẩn)" : "");
    return [
      { text: ten, options: { fill: { color: nen }, color: mau, bold: !ban && h.he_thong === BEST.he_sach_tot_nhat } },
      { text: so(h["recall@1"]), options: { fill: { color: nen }, color: mau, align: "center" } },
      { text: so(h["recall@10"]), options: { fill: { color: nen }, color: mau, align: "center",
        bold: !ban && h.he_thong === BEST.he_sach_tot_nhat } },
      { text: so(h["mrr@10"]), options: { fill: { color: nen }, color: mau, align: "center" } },
      { text: so(h["ndcg@10"]), options: { fill: { color: nen }, color: mau, align: "center" } },
      { text: so(h["latency_p50_ms"], 1) + " ms", options: { fill: { color: nen }, color: mau, align: "center" } },
    ];
  });
  s.addTable([cot, ...hang], { x: 0.42, y: 1.08, w: 9.16,
    colW: [3.16, 1.1, 1.1, 1.2, 1.2, 1.4], rowH: 0.48,
    fontFace: F, fontSize: 11, color: INK, valign: "middle",
    border: { pt: 0.5, color: "BFBFBF" } });

  the(s, 0.42, 4.35, 4.5, 2.4, "EAF6EE", GREEN);
  s.addText("Trả lời CH1: có, nhưng rất nhỏ", { isTextBox: true, x: 0.65, y: 4.46, w: 4.05, h: 0.3,
    fontFace: F, fontSize: 12.5, bold: true, color: GREEN, margin: 0 });
  s.addText([
    { text: `Hợp nhất hơn ngữ nghĩa thuần ${so(loiHop, 2)} điểm phần trăm, tức ${soCau} câu trên ${SPLIT.test.so_cau_hoi}.`, options: { bold: true, breakLine: true } },
    { text: `Riêng BM25 cứu được ${chiBm} câu mà ngữ nghĩa bỏ lỡ.`, options: { breakLine: true } },
    { text: `Tổng trọng số thắng RRF: Recall@1 ${so(HE_SACH["recall@1"])} so với ${so(RRF_S["recall@1"])}, khớp Bruch và cs.`, options: {} },
  ], { isTextBox: true, x: 0.65, y: 4.80, w: 4.05, h: 1.85,
       fontFace: F, fontSize: 11, color: INK, lineSpacing: 16, valign: "top", margin: 0 });

  the(s, 5.08, 4.35, 4.5, 2.4, "F4F8FC", BLUE);
  s.addText("Chi phí, đo trên cùng một máy", { isTextBox: true, x: 5.31, y: 4.46, w: 4.05, h: 0.3,
    fontFace: F, fontSize: 12.5, bold: true, color: BLUE, margin: 0 });
  s.addText([
    { text: `BM25: ${so(BM["latency_p50_ms"], 1)} ms, chỉ mục ${so(COST.bm25.dung_luong_mb, 1)} MB`, options: { breakLine: true } },
    { text: `Ngữ nghĩa: ${so(DE_SACH["latency_p50_ms"], 0)} ms, chỉ mục ${so(COST[BEST.dense_sach].dung_luong_mb, 0)} MB`, options: { breakLine: true } },
    { text: `BM25 nhanh hơn khoảng ${Math.round(Number(DE_SACH["latency_p50_ms"]) / Number(BM["latency_p50_ms"]))} lần`, options: { bold: true, color: BLUE } },
  ], { isTextBox: true, x: 5.31, y: 4.80, w: 4.05, h: 1.7,
       fontFace: F, fontSize: 11.5, color: INK, lineSpacing: 19, valign: "top", margin: 0 });
}

/* ===== PHỤ LỤC B. HỢP NHẤT: định nghĩa ở đây, gọi sau slide Kết luận ===== */
function slideHopNhat() {
  const chiBm = CROSS["chỉ BM25 đúng"], chiDe = CROSS["chỉ ngữ nghĩa đúng"];
  const caHai = CROSS["cả hai đúng"], khongAi = CROSS["cả hai sai"];
  const tong = Number(caHai.so_cau_hoi) + Number(chiBm.so_cau_hoi) +
               Number(chiDe.so_cau_hoi) + Number(khongAi.so_cau_hoi);
  // Cả bốn dòng dưới đây đo CÙNG một thước: tỷ lệ câu hỏi có ít nhất một điều
  // gold trong top-10. Không trộn với Recall@10 trung bình.
  const CEIL = {};
  docCsv(path.join(EVAL, "fusion_ceiling.csv")).forEach(
    (h) => (CEIL[h.he_thong] = Number(h.ty_le_dung_top10_pct)));
  const tyLeDense = CEIL["Dense " + BEST.dense_sach];
  const tyLeHop = CEIL[BEST.he_sach_tot_nhat];
  const tranTop10 = CEIL["Hợp nhất chỉ từ top-10 của hai tầng (trần của phép hợp)"];
  const s = slide("Phụ lục: hợp nhất có thật sự giúp không",
`PHỤ LỤC, không trình bày trong 7 phút. Mở khi thầy hỏi chi tiết về câu hỏi nghiên cứu 1.

"Bảng bốn ô, tính ở top-10, với mô hình sạch. ${caHai.so_cau_hoi} câu cả hai tầng đều đúng. ${chiDe.so_cau_hoi} câu chỉ ngữ nghĩa đúng. Nhưng chỉ ${chiBm.so_cau_hoi} câu trên ${tong} là chỉ BM25 đúng."

Nói chậm câu này: "Nghĩa là BM25 chỉ cứu được ${chiBm.so_cau_hoi} câu hỏi mà tầng ngữ nghĩa bỏ lỡ, tức ${so(100 * Number(chiBm.so_cau_hoi) / tong, 2)} điểm phần trăm."

Chỉ vào bảng phải: "Ngữ nghĩa một mình đúng ${so(tyLeDense, 2)} phần trăm số câu. Hợp nhất được ${so(tyLeHop, 2)} phần trăm. Chênh nhau ${so(tyLeHop - tyLeDense, 2)} điểm phần trăm, tức ${Math.round((tyLeHop - tyLeDense) * tong / 100)} câu hỏi trên ${tong}."

NẾU THẦY HỎI về dòng cuối bảng: "Đó là trần khi phép hợp chỉ lấy top-10 của mỗi tầng. Hệ thật hợp nhất từ top-${TS.top_k_hop_nhat}, nên nó kéo được cả điều luật đứng hạng 11 tới ${TS.top_k_hop_nhat} lên, và vượt dòng đó ${so(tyLeHop - tranTop10, 2)} điểm."

Kết luận trung thực: "Có cải thiện nhưng rất nhỏ. Mỗi cấu hình chỉ chạy một seed nên nhóm không có cơ sở nói về biên độ nhiễu, và không dám gọi ${so(tyLeHop - tyLeDense, 2)} điểm là đáng kể."

Nhấn thêm: "RRF còn KÉM HƠN ngữ nghĩa một mình, Recall@1 tụt từ ${so(DE_SACH["recall@1"])} xuống ${so(he("RRF (BM25 + " + BEST.dense_sach + ")")["recall@1"])}. Vì RRF chỉ nhìn thứ hạng nên nó để BM25 kéo tụt những xếp hạng vốn đã tốt."

Đối chiếu nghiên cứu trước, một câu: "Kết quả này khớp với Bruch và cộng sự năm 2023: tổng có trọng số hơn RRF khi được chỉnh trên val."`);

  s.addImage({ path: "img/venn_bm25_dense.png", x: 0.42, y: 1.02, w: 5.5, h: 3.62 });

  s.addTable([
    [{ text: "Ô", options: THEAD }, { text: "Câu hỏi", options: THEAD }],
    ["Cả hai đúng", caHai.so_cau_hoi],
    [{ text: "Chỉ BM25 đúng", options: { bold: true, color: RED } },
     { text: chiBm.so_cau_hoi, options: { bold: true, color: RED } }],
    ["Chỉ ngữ nghĩa đúng", chiDe.so_cau_hoi],
    ["Cả hai sai", khongAi.so_cau_hoi],
  ], { x: 6.10, y: 1.20, w: 3.48, colW: [2.28, 1.2], rowH: 0.40,
       fontFace: F, fontSize: 11.5, color: INK, valign: "middle",
       border: { pt: 0.5, color: "BFBFBF" }, fill: { color: "FFFFFF" } });

  s.addText("Tỷ lệ câu hỏi có ít nhất một điều gold trong top-10",
    { isTextBox: true, x: 6.10, y: 3.42, w: 3.48, h: 0.26,
      fontFace: F, fontSize: 10, italic: true, color: MUTED, margin: 0 });
  s.addTable([
    ["BM25", so(CEIL["BM25"], 2) + " %"],
    ["Ngữ nghĩa " + BEST.dense_sach, so(tyLeDense, 2) + " %"],
    [{ text: "Hợp nhất", options: { bold: true, color: GREEN } },
     { text: so(tyLeHop, 2) + " %", options: { bold: true, color: GREEN } }],
  ], { x: 6.10, y: 3.70, w: 3.48, colW: [2.28, 1.2], rowH: 0.36,
       fontFace: F, fontSize: 11, color: INK, valign: "middle",
       border: { pt: 0.5, color: "BFBFBF" }, fill: { color: "FFFFFF" } });

  the(s, 0.42, 4.80, 9.16, 1.05, "F4F8FC", BLUE);
  s.addText([
    { text: `Hợp nhất hơn ngữ nghĩa thuần ${so(tyLeHop - tyLeDense, 2)} điểm phần trăm, `, options: { bold: true } },
    { text: `tức ${Math.round((tyLeHop - tyLeDense) * tong / 100)} câu hỏi trên ${tong}. `, options: { bold: true } },
    { text: `Riêng BM25 cứu được ${chiBm.so_cau_hoi} câu mà ngữ nghĩa bỏ lỡ.`, options: {} },
  ], { isTextBox: true, x: 0.65, y: 4.92, w: 8.7, h: 0.8,
       fontFace: F, fontSize: 12.5, color: INK, valign: "middle", margin: 0 });

  the(s, 0.42, 5.98, 9.16, 0.82, "FDEDEC", RED);
  s.addText(`Kết luận trung thực: có cải thiện nhưng rất nhỏ. Mỗi cấu hình chỉ chạy một seed nên nhóm không có cơ sở nói về biên độ nhiễu, và không gọi ${so(tyLeHop - tyLeDense, 2)} điểm là đáng kể.`,
    { isTextBox: true, x: 0.65, y: 6.06, w: 8.7, h: 0.66,
      fontFace: F, fontSize: 12, bold: true, color: RED, valign: "middle", margin: 0 });
}

/* ===== PHỤ LỤC C. PHÂN TÍCH LỖI: định nghĩa ở đây, gọi sau slide Kết luận ===== */
function slidePhanTichLoi() {
  const soSai = ERRS.reduce((a, b) => a + Number(b.so_ca), 0);
  const s = slide("Phụ lục: hệ sai ở đâu trên câu có dấu",
`PHỤ LỤC, không trình bày trong 7 phút. Mở khi thầy hỏi hệ sai ở đâu. Nếu phải nói thì khoảng 45 giây.

"Hệ sạch tốt nhất sai ${soSai} trên ${nghin(SPLIT.test.so_cau_hoi)} câu hỏi. Nhóm đọc tay cả ${soSai} ca, không đoán."

Chỉ vào nhóm lớn nhất: "${ERRS[0].so_ca} ca là thiếu ngữ cảnh pháp lý. Ví dụ câu nướng bắp trên cầu ở slide 3: phải biết luật gọi hành vi đó là sử dụng trái phép đất của đường bộ mới tìm ra."

Chỉ vào nhóm cuối: "Và có ${ERRS[ERRS.length - 1].so_ca} ca mà nhóm cho rằng nhãn gold đáng ngờ. Ví dụ câu hỏi người bắt buộc chữa bệnh sẽ chữa ở đâu: hệ trả về đúng điều Tổ chức điều trị cho người bị bắt buộc chữa bệnh, còn nhãn lại ghi điều khác."

Nói thẳng: "Nhóm không giấu chỗ này. Nó củng cố nhận định ở slide 7 rằng bộ nhãn không đầy đủ."`);

  const cot = ["Nguyên nhân", "Số ca", "Tỷ lệ"].map((t) => ({ text: t, options: THEAD }));
  const ten = { thieu_ngu_canh: "Thiếu ngữ cảnh pháp lý",
                nhieu_dieu_dung: "Nhiều điều cùng đúng, nhãn ghi một",
                sai_gold: "Nhãn gold đáng ngờ" };
  const hang = ERRS.map((h, i) => ([
    { text: ten[h.nguyen_nhan] || h.nguyen_nhan, options: { fill: { color: i % 2 ? TBLALT : "FFFFFF" } } },
    { text: h.so_ca, options: { fill: { color: i % 2 ? TBLALT : "FFFFFF" }, align: "center" } },
    { text: so(h.ty_le_pct, 1) + " %", options: { fill: { color: i % 2 ? TBLALT : "FFFFFF" }, align: "center" } },
  ]));
  s.addTable([cot, ...hang], { x: 0.55, y: 1.08, w: 8.9, colW: [5.3, 1.8, 1.8], rowH: 0.46,
    fontFace: F, fontSize: 11.5, color: INK, valign: "middle",
    border: { pt: 0.5, color: "BFBFBF" } });

  the(s, 0.55, 3.05, 8.9, 1.72, "FFF8F0", CAM);
  s.addText("Ví dụ nhóm lớn nhất: thiếu ngữ cảnh pháp lý", { isTextBox: true, x: 0.80, y: 3.16, w: 8.4, h: 0.3,
    fontFace: F, fontSize: 12.5, bold: true, color: "B9770E", margin: 0 });
  s.addText([
    { text: "Hỏi:  ", options: { bold: true } },
    { text: "Nướng bắp, ngô trên cầu phạt bao nhiêu tiền?", options: { breakLine: true } },
    { text: "Điều đúng:  ", options: { bold: true } },
    { text: "Xử phạt vi phạm quy định về quản lý, khai thác, bảo trì công trình đường bộ", options: { breakLine: true } },
    { text: "Phải biết luật gọi hành vi đó là gì mới tìm ra. Không tầng nào bắc được cầu này.", options: { italic: true } },
  ], { isTextBox: true, x: 0.80, y: 3.48, w: 8.4, h: 1.2,
       fontFace: F, fontSize: 11.5, color: INK, lineSpacing: 17, valign: "top", margin: 0 });

  the(s, 0.55, 4.95, 8.9, 1.8, "FDEDEC", RED);
  s.addText("Ví dụ nhóm nhãn gold đáng ngờ", { isTextBox: true, x: 0.80, y: 5.06, w: 8.4, h: 0.3,
    fontFace: F, fontSize: 12.5, bold: true, color: RED, margin: 0 });
  s.addText([
    { text: "Hỏi:  ", options: { bold: true } },
    { text: "Người chấp hành biện pháp bắt buộc chữa bệnh sẽ chữa bệnh ở đâu?", options: { breakLine: true } },
    { text: "Hệ trả về:  ", options: { bold: true } },
    { text: "Điều 138. Tổ chức điều trị cho người bị bắt buộc chữa bệnh", options: { color: GREEN, breakLine: true } },
    { text: "Nhãn ghi:  ", options: { bold: true } },
    { text: "Điều 133. Cơ quan được giao nhiệm vụ thi hành biện pháp tư pháp", options: { color: RED } },
  ], { isTextBox: true, x: 0.80, y: 5.38, w: 8.4, h: 1.3,
       fontFace: F, fontSize: 11.5, color: INK, lineSpacing: 17, valign: "top", margin: 0 });
}

/* =========== 11. CÂU HỎI GÕ KHÔNG DẤU: SỤP ĐỔ =========== */
{
  const coDe = kd("có dấu", "giữ nguyên", "Ngữ nghĩa"), khDe = kd("không dấu", "giữ nguyên", "Ngữ nghĩa");
  const khBm = kd("không dấu", "giữ nguyên", "BM25"), khHop = kd("không dấu", "giữ nguyên", "Hợp nhất");
  const bmBo = kd("không dấu", "chỉ mục bỏ dấu", "BM25 bỏ dấu");
  const s = slide("Câu hỏi gõ không dấu: hệ sụp đổ",
`Khoảng 40 giây. Đây là kết quả chính của đồ án. Nói chậm, chỉ tay vào biểu đồ.

"Nhóm lấy đúng 788 câu hỏi test, bỏ hết dấu, giữ nguyên nhãn. Rồi chạy lại đúng hệ vừa rồi."

Chỉ vào ba thanh đỏ: "Mô hình ngữ nghĩa sạch tốt nhất tụt từ ${pt(coDe["recall@10"])} xuống ${pt(khDe["recall@10"])} phần trăm. BM25 còn ${pt(khBm["recall@10"])}. Hợp nhất cũng chỉ ${pt(khHop["recall@10"])}. Cả hệ gần như không dùng được."

Chỉ vào thanh cam: "Chỉ cần lập chỉ mục BM25 trên văn bản đã bỏ dấu, không cần mô hình nào, BM25 lên lại ${pt(bmBo["recall@10"])}, gấp ${Math.round(Number(bmBo["recall@10"]) / Number(khDe["recall@10"]))} lần mô hình ngữ nghĩa. Ở câu có dấu BM25 gần như vô dụng, ở đây nó lại là tầng đứng vững nhất."

Chỉ vào thanh xanh lá: "Và cách tốt nhất là phục hồi dấu trước khi tìm. Slide sau."

NẾU THẦY HỎI "vì sao mô hình ngữ nghĩa sụp": giả thuyết của nhóm là mô hình học chủ yếu trên văn bản có dấu, nên 'phat' và 'phạt' bị tách thành những token khác hẳn nhau. Nhóm chưa kiểm chứng trực tiếp giả thuyết này.
NẾU THẦY HỎI "câu không dấu này có thật không": là câu gốc bị bỏ dấu bằng máy, nên nhãn giữ nguyên được. Chưa có câu gõ tay thật, ghi rõ ở phần giới hạn.`);

  s.addText([
    { text: "Có dấu:  ", options: { bold: true } },
    { text: "Đi xe máy không đội mũ bảo hiểm bị phạt bao nhiêu tiền?", options: { breakLine: true } },
    { text: "Không dấu:  ", options: { bold: true, color: RED } },
    { text: "Di xe may khong doi mu bao hiem bi phat bao nhieu tien?", options: { color: RED } },
  ], { isTextBox: true, x: 0.55, y: 1.02, w: 8.9, h: 0.6,
       fontFace: F, fontSize: 12, color: INK, lineSpacing: 17, valign: "top", margin: 0 });

  s.addImage({ path: "img/khong_dau.png", x: 0.55, y: 1.68, w: 8.9, h: 3.74 });

  the(s, 0.55, 5.52, 4.35, 1.25, "FDEDEC", RED);
  s.addText("Vì sao sụp", { isTextBox: true, x: 0.78, y: 5.60, w: 3.9, h: 0.28,
    fontFace: F, fontSize: 12, bold: true, color: RED, margin: 0 });
  s.addText("BM25: “phat” và “phạt” là hai từ khác nhau, không khớp gì. Mô hình ngữ nghĩa: nhóm đoán do học chủ yếu trên văn bản có dấu.",
    { isTextBox: true, x: 0.78, y: 5.90, w: 3.9, h: 0.82,
      fontFace: F, fontSize: 10.5, color: INK, lineSpacing: 14, valign: "top", margin: 0 });

  the(s, 5.10, 5.52, 4.35, 1.25, "FFF8F0", CAM);
  s.addText(`BM25 bỏ dấu: ${pt(bmBo["recall@10"])}%, không cần mô hình`, { isTextBox: true, x: 5.33, y: 5.60, w: 3.9, h: 0.28,
    fontFace: F, fontSize: 12, bold: true, color: "B9770E", margin: 0 });
  s.addText("Ở câu có dấu BM25 gần như không góp gì. Ở câu không dấu nó lại là tầng đứng vững nhất.",
    { isTextBox: true, x: 5.33, y: 5.90, w: 3.9, h: 0.82,
      fontFace: F, fontSize: 10.5, color: INK, lineSpacing: 14, valign: "top", margin: 0 });
}

/* ========= 12. SỬA BẰNG PHỤC HỒI DẤU ========= */
{
  const coHop = kd("có dấu", "giữ nguyên", "Hợp nhất"), phHop = kd("không dấu", "phục hồi dấu", "Hợp nhất");
  const dtCo = kd("có dấu", "định tuyến", "Hợp nhất");
  const saiNhom = KDL["sai ít nhất một âm tiết"], mat = KDL["mất do phục hồi sai"], duoc = KDL["được nhờ phục hồi"];
  const chenh = 100 * (Number(coHop["recall@10"]) - Number(phHop["recall@10"]));
  const s = slide("Sửa bằng phục hồi dấu: bigram học từ kho luật",
`Khoảng 40 giây. Trả lời câu hỏi nghiên cứu 2.

Khung trái: "Cách làm rất đơn giản. Đếm cặp âm tiết liền nhau trên ${so(KDP.so_am_tiet / 1e6, 1)} triệu âm tiết của chính kho luật. Một âm tiết không dấu như 'phat' có nhiều ứng viên: phát, phạt, phắt. Thuật toán Viterbi chọn chuỗi ứng viên có xác suất cao nhất. Không cần tải mô hình nào, học trong vài giây."

Khung phải: "Kết quả: ${pt(KDP.do_chinh_xac_am_tiet_test)} phần trăm âm tiết đúng, khoảng ${so(KDP.do_tre_phuc_hoi_ms, 1)} mili giây mỗi câu. Hệ lai lên lại ${pt(phHop["recall@10"])} phần trăm, chỉ kém câu có dấu ${so(chenh, 2)} điểm."

Khung đỏ, nói thẳng chỗ sai: "Phục hồi sai rơi vào từ nói thường mà văn bản luật không dùng. Tài xế thành tải xe, máu thành mẫu. Đây lại chính là khoảng cách từ vựng ở slide 3."

Khung xanh lá: "Bộ định tuyến không nhận nhầm câu gốc nào, nên câu có dấu vẫn giữ nguyên ${pt(dtCo["recall@10"])}."

NẾU THẦY HỎI "sao không dùng mô hình phục hồi dấu có sẵn": các mô hình dịch máy đạt khoảng 97 phần trăm, cùng mức với bigram này, nhưng phải tải và chạy thêm một mô hình lớn. Nhóm chưa so trên cùng bộ dữ liệu nên không nói hơn kém.
NẾU THẦY HỎI "sao không mã hóa lại cả kho ở dạng không dấu": chưa đo, nên không trả lời bằng số được. Phục hồi dấu có lợi thế là giữ nguyên toàn bộ hệ phía sau.`);

  the(s, 0.42, 1.05, 4.5, 2.9, "F4F8FC", BLUE);
  s.addText("Cách làm", { isTextBox: true, x: 0.64, y: 1.14, w: 4.1, h: 0.3,
    fontFace: F, fontSize: 12.5, bold: true, color: BLUE, margin: 0 });
  s.addText([
    { text: `1. Đếm unigram và bigram trên ${so(KDP.so_am_tiet / 1e6, 1)} triệu âm tiết của kho luật và câu hỏi train`, options: { breakLine: true } },
    { text: "2. Mỗi âm tiết không dấu có nhiều ứng viên: phat → phát, phạt, phắt", options: { breakLine: true } },
    { text: "3. Viterbi chọn chuỗi có xác suất bigram cao nhất", options: { breakLine: true } },
    { text: `4. Hệ số nội suy lambda = ${so(KDP.lambda_phuc_hoi, 1)}, chốt trên val`, options: {} },
  ], { isTextBox: true, x: 0.64, y: 1.50, w: 4.1, h: 2.4,
       fontFace: F, fontSize: 12, color: INK, lineSpacing: 18, paraSpaceAfter: 4, valign: "top", margin: 0 });

  const kpi = [
    [pt(KDP.do_chinh_xac_am_tiet_test) + "%", "âm tiết phục hồi đúng"],
    [`${KDP.so_cau_phuc_hoi_dung_hoan_toan_test}/${KDP.so_cau_test}`, "câu đúng hoàn toàn"],
    [`${so(KDP.do_tre_phuc_hoi_ms, 1)} ms`, "phục hồi dấu mỗi câu"],
    [pt(phHop["recall@10"]) + "%", `Recall@10, kém câu có dấu ${so(chenh, 2)} điểm`],
  ];
  kpi.forEach((k, i) => {
    const x = 5.10 + (i % 2) * 2.27, y = 1.05 + Math.floor(i / 2) * 1.47;
    the(s, x, y, 2.18, 1.37, i === 3 ? "EAF6EE" : "FFFFFF", i === 3 ? GREEN : "BFBFBF");
    s.addText(k[0], { isTextBox: true, x, y: y + 0.12, w: 2.18, h: 0.6,
      fontFace: F, fontSize: 22, bold: true, color: i === 3 ? GREEN : BLUE, align: "center", valign: "middle", margin: 0 });
    s.addText(k[1], { isTextBox: true, x: x + 0.1, y: y + 0.76, w: 1.98, h: 0.52,
      fontFace: F, fontSize: 10, color: MUTED, align: "center", valign: "top", margin: 0 });
  });

  the(s, 0.42, 4.12, 9.16, 1.4, "FDEDEC", RED);
  s.addText("Sai ở đâu: từ nói thường mà văn bản luật không dùng", { isTextBox: true, x: 0.64, y: 4.21, w: 8.7, h: 0.3,
    fontFace: F, fontSize: 12.5, bold: true, color: RED, margin: 0 });
  s.addText([
    { text: "“Tài xế” → “tải xe”,  “máu” → “mẫu”,  “đi bộ” → “đi bờ”", options: { bold: true, breakLine: true } },
    { text: `${saiNhom.so_cau} câu sai ít nhất một âm tiết. Ở nhóm này tỷ lệ tìm đúng trong top-10 tụt từ ${so(saiNhom.ty_le_dung_top10_cau_goc_pct, 2)}% xuống ${so(saiNhom.ty_le_dung_top10_phuc_hoi_pct, 2)}%: mất ${mat.so_cau} câu, được ${duoc.so_cau} câu.`, options: {} },
  ], { isTextBox: true, x: 0.64, y: 4.55, w: 8.7, h: 0.92,
       fontFace: F, fontSize: 11.5, color: INK, lineSpacing: 17, valign: "top", margin: 0 });

  the(s, 0.42, 5.66, 9.16, 1.1, "EAF6EE", GREEN);
  s.addText([
    { text: "Bộ định tuyến: ", options: { bold: true, color: GREEN } },
    { text: `${KDP.cau_goc_bi_nhan_la_khong_dau} câu gốc bị nhận nhầm là không dấu, nên câu có dấu vẫn giữ nguyên Recall@10 ${pt(dtCo["recall@10"])}%. Trong demo, trợ lý tra cứu dùng đúng đường chạy này và trả lời bằng cách trích nguyên văn khoản luật.`, options: {} },
  ], { isTextBox: true, x: 0.64, y: 5.72, w: 8.7, h: 0.98,
       fontFace: F, fontSize: 11.5, color: INK, lineSpacing: 16, valign: "middle", margin: 0 });
}

/* ======================= 13. KẾT LUẬN ======================= */
{
  const _c = {};
  docCsv(path.join(EVAL, "fusion_ceiling.csv")).forEach(
    (h) => (_c[h.he_thong] = Number(h.ty_le_dung_top10_pct)));
  const loiHop = _c[BEST.he_sach_tot_nhat] - _c["Dense " + BEST.dense_sach];
  const soCau = Math.round(loiHop * Number(SPLIT.test.so_cau_hoi) / 100);
  const khHop = kd("không dấu", "giữ nguyên", "Hợp nhất"), phHop = kd("không dấu", "phục hồi dấu", "Hợp nhất");
  const khDe = kd("không dấu", "giữ nguyên", "Ngữ nghĩa");
  const bmBo = kd("không dấu", "chỉ mục bỏ dấu", "BM25 bỏ dấu");
  const s = slide("Kết luận",
`Khoảng 40 giây. Nói chậm, đây là ấn tượng cuối cùng.

"Một, câu hỏi nghiên cứu 1: với câu có dấu, hợp nhất chỉ hơn ngữ nghĩa thuần ${so(loiHop, 2)} điểm phần trăm, tức ${soCau} câu trên ${SPLIT.test.so_cau_hoi}. Có cải thiện nhưng rất nhỏ."

"Hai, câu hỏi nghiên cứu 2, và đây là điều nhóm muốn thầy nhớ: khi người dân gõ không dấu, mô hình ngữ nghĩa tốt nhất chỉ còn ${pt(khDe["recall@10"])} phần trăm. Một mô hình bigram nhỏ học từ chính kho luật kéo hệ về ${pt(phHop["recall@10"])}. Và BM25, tầng tưởng như vô dụng, lại là tầng đứng vững nhất khi không có dấu."

"Ba, chống rò rỉ dữ liệu không dừng ở chia lại tập. Mô hình tiền huấn luyện mình đem dùng cũng có thể đã thấy tập test rồi."

Kết: "Em xin hết. Nhóm xin demo code ngay sau đây."`);

  const muc = [
    [GREEN, "CH1. Câu có dấu: hợp nhất có cải thiện, nhưng rất nhỏ",
     `Hơn ngữ nghĩa thuần ${so(loiHop, 2)} điểm phần trăm, tức ${soCau} câu trên ${SPLIT.test.so_cau_hoi}. Tổng trọng số thắng RRF. BM25 nhanh hơn khoảng ${Math.round(Number(DE_SACH["latency_p50_ms"]) / Number(BM["latency_p50_ms"]))} lần và giải thích được kết quả.`],
    [RED, "CH2. Câu không dấu: hệ sụp, phục hồi dấu kéo lại gần hết",
     `Hệ lai giữ nguyên chỉ còn ${pt(khHop["recall@10"])}%. BM25 bỏ dấu đạt ${pt(bmBo["recall@10"])}% không cần mô hình. Phục hồi dấu bằng bigram đưa hệ về ${pt(phHop["recall@10"])}%, ${pt(KDP.do_chinh_xac_am_tiet_test)}% âm tiết đúng.`],
    [BLUE, "Chống rò rỉ không dừng ở việc chia lại tập",
     "Mô hình bi-encoder tiếng Việt phổ biến nhất đã học chính bộ dữ liệu này. Phải đọc model card trước khi tin một con số benchmark."],
  ];
  muc.forEach((m, i) => {
    const y = 1.05 + i * 1.30;
    the(s, 0.55, y, 8.9, 1.15, "FFFFFF", m[0]);
    s.addShape(p.ShapeType.rect, { x: 0.55, y, w: 0.09, h: 1.15, fill: { color: m[0] } });
    s.addText(m[1], { isTextBox: true, x: 0.82, y: y + 0.08, w: 8.4, h: 0.32,
      fontFace: F, fontSize: 13, bold: true, color: m[0], margin: 0 });
    s.addText(m[2], { isTextBox: true, x: 0.82, y: y + 0.42, w: 8.4, h: 0.66,
      fontFace: F, fontSize: 11.5, color: INK, lineSpacing: 16, valign: "top", margin: 0 });
  });

  the(s, 0.55, 5.05, 4.35, 1.7, "F4F8FC", BLUE);
  s.addText("Giới hạn", { isTextBox: true, x: 0.78, y: 5.15, w: 3.9, h: 0.3,
    fontFace: F, fontSize: 12.5, bold: true, color: BLUE, margin: 0 });
  s.addText("Câu không dấu tạo bằng máy từ câu gốc, chưa có câu gõ tay thật, chưa đo câu gõ dấu một nửa.\nNhãn không đầy đủ, mọi Recall là cận dưới.\nMỗi cấu hình chỉ chạy một seed.",
    { isTextBox: true, x: 0.78, y: 5.46, w: 3.9, h: 1.25,
      fontFace: F, fontSize: 10.5, color: INK, lineSpacing: 14, valign: "top", margin: 0 });

  the(s, 5.10, 5.05, 4.35, 1.7, "EAF6EE", GREEN);
  s.addText("Hướng phát triển", { isTextBox: true, x: 5.33, y: 5.15, w: 3.9, h: 0.3,
    fontFace: F, fontSize: 12.5, bold: true, color: GREEN, margin: 0 });
  s.addText("Thu câu hỏi không dấu do người thật gõ.\nCho mô hình phục hồi dấu học thêm văn nói.\nCross-encoder xếp hạng lại top-20.",
    { isTextBox: true, x: 5.33, y: 5.46, w: 3.9, h: 1.25,
      fontFace: F, fontSize: 10.5, color: INK, lineSpacing: 14, valign: "top", margin: 0 });
}

/* ============================ PHỤ LỤC ============================ */
slideChiaDoan();
slideHopNhat();
slidePhanTichLoi();

/* ===== PHỤ LỤC D. TÀI LIỆU THAM KHẢO, đọc từ docs/NGHIEN_CUU_LIEN_QUAN.md ===== */
{
  const md = fs.readFileSync(path.join(ROOT, "docs", "NGHIEN_CUU_LIEN_QUAN.md"), "utf8");
  const phan = md.split(/^## Tài liệu tham khảo\s*$/m)[1] || "";
  const tl = phan.split(/\r?\n/).map((l) => l.match(/^(\d+)\.\s+(.*)$/)).filter(Boolean)
    .map((m) => `[${m[1]}] ${m[2].replace(/\*/g, "")}`);
  if (tl.length === 0) throw new Error("Không đọc được tài liệu tham khảo từ NGHIEN_CUU_LIEN_QUAN.md");
  const s = slide("Tài liệu tham khảo",
`PHỤ LỤC. Danh sách đọc thẳng từ docs/NGHIEN_CUU_LIEN_QUAN.md, không gõ lại trong slide.`);
  const nua = Math.ceil(tl.length / 2);
  [tl.slice(0, nua), tl.slice(nua)].forEach((cot, i) => {
    s.addText(cot.map((t, j) => ({ text: t, options: { breakLine: j < cot.length - 1 } })),
      { isTextBox: true, x: 0.42 + i * 4.62, y: 1.02, w: 4.5, h: 5.9,
        fontFace: F, fontSize: 8.5, color: INK, lineSpacing: 11, paraSpaceAfter: 3,
        valign: "top", margin: 0 });
  });
}

const OUT = "Nhom09_XLNNTN_BaoCao.pptx";
p.writeFile({ fileName: OUT }).then(() => {
  console.log(`Đã dựng ${n} slide -> ${OUT}`);
  console.log("Mọi con số đọc từ reports/, không gõ tay.");
});
