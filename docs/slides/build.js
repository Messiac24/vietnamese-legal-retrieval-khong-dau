// Dựng bộ slide báo cáo, nhóm 09 môn Xử lý ngôn ngữ tự nhiên.
//
//     C:/Python314/python.exe make_assets.py
//     node build.js          -> Nhom09_XLNNTN_BaoCao.pptx
//
// Số liệu đọc từ reports/, tài liệu tham khảo đọc từ docs/NGHIEN_CUU_LIEN_QUAN.md.
const fs = require("fs");
const path = require("path");
const pptx = require("pptxgenjs");
const p = new pptx();

const ROOT = path.resolve(__dirname, "..", "..");
const AUDIT = path.join(ROOT, "reports", "audit");
const EVAL = path.join(ROOT, "reports", "eval");

// đọc số liệu từ reports/
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
const demDong = (tep) => docCsv(tep).length;
const docJson = (tep) => JSON.parse(fs.readFileSync(tep, "utf8"));

// dấu thập phân kiểu Việt Nam, và dấu chấm phân cách hàng nghìn
const so = (x, n = 4) => Number(x).toFixed(n).replace(".", ",");
const nghin = (x) => Number(x).toLocaleString("vi-VN");
const pt = (x, n = 2) => so(100 * Number(x), n);   // 0,9772 -> "97,72"

const CS = {};
docCsv(path.join(AUDIT, "corpus_stats.csv")).forEach((h) => (CS[h.chi_tieu] = Number(h.gia_tri)));
const SPLIT = {};
docCsv(path.join(AUDIT, "split_distribution.csv")).forEach((h) => (SPLIT[h.split] = h));
const MC = docCsv(path.join(EVAL, "model_comparison.csv"));
const CROSS = {};
docCsv(path.join(EVAL, "crossover.csv")).forEach((h) => (CROSS[h.o] = Number(h.so_cau_hoi)));
const COST = {};
docCsv(path.join(EVAL, "index_cost.csv")).forEach((h) => (COST[h.chi_muc] = h));
const TS = docJson(path.join(EVAL, "chosen_params.json"));
const BEST = docJson(path.join(EVAL, "best_system.json"));
const CHONG_LAN = docCsv(path.join(AUDIT, "query_overlap.csv"));
const TRUNG_ID = CHONG_LAN.filter((h) => h.loai === "trung_id").length;
const CONFLICT = docCsv(path.join(AUDIT, "conflicting_gold.csv"));
const DIA = docCsv(path.join(AUDIT, "duplicate_docs_diacritics.csv"));
const DODAI = docJson(path.join(AUDIT, "do_dai_dieu.json"));
const CHUNKS = Number(COST["bkai"].so_muc);
const he = (ten) => MC.find((h) => h.he_thong === ten);
const HE_SACH = he(BEST.he_sach_tot_nhat);
const DE_SACH = he("Dense " + BEST.dense_sach);
const RRF_SACH = he("RRF (BM25 + " + BEST.dense_sach + ")");
const BM = he("BM25");
const loiHopR = 100 * (Number(HE_SACH["recall@10"]) - Number(DE_SACH["recall@10"]));
const CEIL = {};
docCsv(path.join(EVAL, "fusion_ceiling.csv")).forEach((h) => (CEIL[h.he_thong] = Number(h.ty_le_dung_top10_pct)));
const TONG_TEST = Number(SPLIT.test.so_cau_hoi);
// số câu hợp nhất cứu thêm, đo bằng tỷ lệ câu có gold trong top-10 (không phải Recall@10)
const soCauHop = Math.round((CEIL[BEST.he_sach_tot_nhat] - CEIL["Dense " + BEST.dense_sach]) * TONG_TEST / 100);
const POOL = docCsv(path.join(EVAL, "tuning_pooling.csv"));
const gop = (cach) => POOL.find((h) => h.mo_hinh === BEST.dense_sach && h.gop_doan === cach)["recall@10"];
const TACH = {};
docCsv(path.join(EVAL, "khong_dau_tach_tu.csv")).forEach((h) => (TACH[h.cach_tach_tu] = Number(h["recall@10_val"])));
const KD = docCsv(path.join(EVAL, "khong_dau.csv"));
const KDP = docJson(path.join(EVAL, "khong_dau_params.json"));
const KDL = {};
docCsv(path.join(EVAL, "khong_dau_loi.csv")).forEach((h) => (KDL[h.nhom] = h));
const kd = (dk, cach, ten) => {
  const h = KD.find((r) => r.dieu_kien === dk && r.cach_xu_ly === cach && r.he_thong === ten);
  if (!h) throw new Error(`khong_dau.csv thiếu dòng: ${dk} / ${cach} / ${ten}`);
  return h;
};
const ERRS = docCsv(path.join(EVAL, "error_summary.csv"));
const tocDo = Number(DE_SACH["latency_p50_ms"]) / Number(BM["latency_p50_ms"]);

// lời thoại ở loi_thoai.js
const LOI = require("./loi_thoai")({
  so, pt, nghin, kd, gop, CS, SPLIT, BM, DE_SACH, HE_SACH, CROSS, TS, KDP, KDL, TACH, DODAI, CHUNKS,
  ERRS, soSai: ERRS.reduce((a, b) => a + Number(b.so_ca), 0), loiHopR, soCauHop, tocDo, TONG_TEST, bkai: he("Dense bkai"),
  nhanDoi: DIA.reduce((a, b) => a + Number(b.so_dieu), 0), chongLan: CHONG_LAN.length,
  trungId: TRUNG_ID, xungDot: CONFLICT.length,
});
const AM_TIET_MOI_GIAY = 3.0;   // tốc độ nói thuyết trình, ước lượng
const NGHI_MOI_SLIDE = 3;       // giây chuyển slide và chỉ vào hình
// số đọc thành nhiều âm tiết: "85,22" là tám lăm phẩy hai hai
const amTietCuaTu = (w) => { const cs = (w.match(/\d/g) || []).length;
  return cs ? Math.round(1.5 * cs) + (w.match(/\d,\d/g) || []).length : 1; };
const demAmTiet = (l) => l.noi.join(" ").split(/\s+/).filter(Boolean).reduce((a, w) => a + amTietCuaTu(w), 0);
function ghiChu(so) {
  const l = LOI[so];
  if (!l) return "Không trình bày.";
  const phan = [`${l.nguoi}  ·  khoảng ${l.giay} giây`, ...l.noi];
  (l.hoi || []).forEach(([h, d]) => phan.push(`Nếu thầy hỏi: ${h}\n${d}`));
  return phan.join("\n\n");
}

// khuôn slide
p.layout = "LAYOUT_WIDE"; // 13,333 x 7,5 inch
p.author = "Nhom 09";
p.title = "Tim kiem dieu luat tieng Viet cho cau hoi go thieu dau";

const W = 13.333, H = 7.5, MX = 0.65, CW = W - 2 * MX;
const INK = "16222C", INK2 = "46545F", MUTED = "77858E", RULE = "D9DDD7", PAPER = "F3F5F2";
const SEAL = "A8202B", SEAL_S = "F8E9E9", OK = "1B6E5A", OK_S = "E4F0EB";
const ACC = "2C5F8A", ACC_S = "E5EEF5", ACC_L = "9FC2DB", WARN = "B7791F";
const HF = "Cambria", BF = "Calibri", MF = "Consolas";
const TONG = 16;   // kiểm lại ở cuối tệp, lệch là dừng
const DE_TAI = "Nhóm 09  ·  Tìm kiếm điều luật tiếng Việt cho câu hỏi gõ thiếu dấu";

let n = 0;
function tx(s, text, o) {
  s.addText(text, { isTextBox: true, margin: 0, fontFace: BF, color: INK, ...o });
}
function hop(s, x, y, w, h, nen, vien, dut) {
  s.addShape(p.ShapeType.rect, { x, y, w, h, fill: { color: nen },
    line: vien ? { color: vien, width: 1.25, dashType: dut ? "dash" : "solid" } : { type: "none" } });
}
function slide(nhan, tieuDe) {
  n += 1;
  const s = p.addSlide();
  s.background = { color: "FFFFFF" };
  tx(s, `${nhan}  ·  ${String(n).padStart(2, "0")}`, { x: MX, y: 0.36, w: 6, h: 0.26,
    fontFace: MF, fontSize: 11, color: ACC, charSpacing: 1 });
  tx(s, tieuDe, { x: MX, y: 0.64, w: CW, h: 0.95, fontFace: HF, fontSize: 28, bold: true,
    valign: "top", lineSpacingMultiple: 0.95 });
  tx(s, DE_TAI, { x: MX, y: H - 0.42, w: 8, h: 0.24, fontSize: 10, color: MUTED });
  tx(s, `${String(n).padStart(2, "0")} / ${TONG}`, { x: W - MX - 1.5, y: H - 0.42, w: 1.5, h: 0.24,
    fontFace: MF, fontSize: 10, color: MUTED, align: "right" });
  s.addNotes(ghiChu(n));
  return s;
}
// số lớn kèm chú thích bên dưới
function soLon(s, x, y, w, giaTri, chuThich, mau, co = 44) {
  tx(s, giaTri, { x, y, w, h: co / 60, fontFace: HF, fontSize: co, bold: true, color: mau });
  tx(s, chuThich, { x, y: y + co / 60 + 0.06, w, h: 0.62, fontSize: 13, color: INK2, valign: "top" });
}

// giá trị nhân 10000 (97,72% -> 9772) để mã 0","00 luôn in dấu phẩy, máy chiếu cài vùng nào cũng vậy
const VAN = (x) => Math.round(10000 * Number(x));
const NHAN_PT = '[=0]"";0","00';
function bieuDo(s, series, o) {
  s.addChart(p.ChartType.bar, series, {
    barDir: "col", barGrouping: "clustered", barGapWidthPct: 55,
    showValue: true, dataLabelFormatCode: NHAN_PT, dataLabelFontFace: BF, dataLabelFontSize: 13,
    dataLabelColor: INK, dataLabelPosition: "outEnd",
    valAxisHidden: true, valAxisMinVal: 0, valAxisMaxVal: 11000, valGridLine: { style: "none" },
    catGridLine: { style: "none" }, catAxisLabelFontFace: BF, catAxisLabelFontSize: 13,
    catAxisLabelColor: INK2, catAxisLineShow: true, catAxisLineColor: RULE,
    showLegend: series.length > 1, legendPos: "t", legendFontFace: BF, legendFontSize: 12,
    legendColor: INK2,
    ...o,
  });
}
// mỗi cột một màu: mỗi cột là một chuỗi riêng, xếp chồng lên các chuỗi bằng 0
function cotMau(s, nhan, giaTri, mau, o) {
  const series = nhan.map((ten, i) => ({ name: ten, labels: nhan,
    values: nhan.map((_, j) => (j === i ? VAN(giaTri[i]) : 0)) }));
  bieuDo(s, series, { barGrouping: "stacked", chartColors: mau, showLegend: false,
    dataLabelPosition: "inEnd", dataLabelColor: "FFFFFF", dataLabelFontSize: 15, barGapWidthPct: 45, ...o });
}
function muiTen(s, x1, y1, x2, y2, mau = MUTED) {
  s.addShape(p.ShapeType.line, { x: Math.min(x1, x2), y: Math.min(y1, y2),
    w: Math.abs(x2 - x1) || 0.001, h: Math.abs(y2 - y1) || 0.001, flipV: y2 < y1,
    line: { color: mau, width: 1.75, endArrowType: "triangle" } });
}

// slide 1: bìa
{
  n += 1;
  const s = p.addSlide();
  s.background = { path: path.join(__dirname, "img", "cover.png") };
  tx(s, "Trường Đại học Công nghệ Thông tin, ĐHQG-HCM", { x: MX, y: 0.55, w: 8, h: 0.35,
    fontSize: 14, bold: true, color: "FFFFFF" });
  tx(s, "BÁO CÁO ĐỒ ÁN  ·  XỬ LÝ NGÔN NGỮ TỰ NHIÊN", { x: MX, y: 2.05, w: 8, h: 0.3,
    fontFace: MF, fontSize: 12, color: ACC_L, charSpacing: 2 });
  tx(s, "Tìm kiếm điều luật tiếng Việt\ncho câu hỏi gõ thiếu dấu", { x: MX, y: 2.45, w: 7.4, h: 1.75,
    fontFace: HF, fontSize: 40, bold: true, color: "FFFFFF", valign: "top", lineSpacingMultiple: 0.95 });
  tx(s, "Kết hợp từ khóa và ngữ nghĩa, phục hồi dấu, kiểm toán rò rỉ dữ liệu",
    { x: MX, y: 3.9, w: 7.4, h: 0.4, fontSize: 18, italic: true, color: "C9D6DF" });
  tx(s, [
    { text: "Nhóm 09", options: { bold: true, breakLine: true } },
    { text: "Lê Hoàng Lộc  25210293", options: { breakLine: true } },
    { text: "Lê Thị Tuấn Anh  25210250", options: { breakLine: true } },
    { text: "Đoàn Mậu Thiên Thư  25210341", options: { breakLine: true } },
    { text: "GVHD: Đặng Văn Thìn", options: { bold: true } },
  ], { x: MX, y: 4.75, w: 6, h: 1.45, fontSize: 13, color: "FFFFFF", lineSpacingMultiple: 1.15, valign: "top" });
  tx(s, "TP. Hồ Chí Minh, tháng 9 năm 2026", { x: MX, y: H - 0.55, w: 6, h: 0.3, fontSize: 11, color: "9AA8B2" });
  s.addNotes(ghiChu(n));
}

// slide 2: bài toán
{
  const s = slide("BÀI TOÁN", "Người dân hỏi luật bằng lời thường, và thường gõ không dấu");

  const y0 = 1.85, hT = 3.85, wT = (CW - 0.4) / 2;
  // thẻ trái: khác từ vựng
  hop(s, MX, y0, wT, hT, PAPER);
  tx(s, "KHÁC TỪ VỰNG", { x: MX + 0.35, y: y0 + 0.3, w: 4, h: 0.3, fontFace: MF, fontSize: 12, color: ACC, bold: true });
  tx(s, "Người hỏi", { x: MX + 0.35, y: y0 + 0.8, w: 4, h: 0.28, fontSize: 13, color: MUTED });
  tx(s, "Nướng bắp, ngô trên cầu phạt bao nhiêu tiền?", { x: MX + 0.35, y: y0 + 1.1, w: wT - 0.7, h: 0.8,
    fontFace: HF, fontSize: 21, valign: "top" });
  tx(s, "Điều luật đúng", { x: MX + 0.35, y: y0 + 2.05, w: 4, h: 0.28, fontSize: 13, color: MUTED });
  tx(s, "Xử phạt vi phạm quy định về quản lý, khai thác, bảo trì công trình đường bộ",
    { x: MX + 0.35, y: y0 + 2.35, w: wT - 0.7, h: 0.8, fontFace: HF, fontSize: 17, color: INK2, valign: "top" });
  tx(s, "Không trùng một từ nào", { x: MX + 0.35, y: y0 + 3.3, w: wT - 0.7, h: 0.34,
    fontSize: 15, bold: true, color: SEAL });

  // thẻ phải: mất dấu
  const x2 = MX + wT + 0.4;
  hop(s, x2, y0, wT, hT, PAPER);
  tx(s, "MẤT DẤU", { x: x2 + 0.35, y: y0 + 0.3, w: 4, h: 0.3, fontFace: MF, fontSize: 12, color: SEAL, bold: true });
  tx(s, "Gõ đủ dấu", { x: x2 + 0.35, y: y0 + 0.8, w: 4, h: 0.28, fontSize: 13, color: MUTED });
  tx(s, "Đi xe máy không đội mũ bảo hiểm bị phạt bao nhiêu tiền?", { x: x2 + 0.35, y: y0 + 1.1, w: wT - 0.7, h: 0.8,
    fontFace: HF, fontSize: 21, valign: "top" });
  tx(s, "Gõ vội trên điện thoại", { x: x2 + 0.35, y: y0 + 2.05, w: 4, h: 0.28, fontSize: 13, color: MUTED });
  tx(s, "di xe may khong doi mu bao hiem bi phat bao nhieu tien", { x: x2 + 0.35, y: y0 + 2.35, w: wT - 0.7, h: 0.8,
    fontFace: MF, fontSize: 17, color: SEAL, valign: "top" });
  tx(s, "Với máy, “phạt” và “phat” là hai chữ khác nhau", { x: x2 + 0.35, y: y0 + 3.3, w: wT - 0.7, h: 0.34,
    fontSize: 15, bold: true, color: SEAL });

  tx(s, `Đầu vào: một câu hỏi tự nhiên.   Đầu ra: điều luật xếp hạng trong ${nghin(CS.so_dieu_luat)} điều của ${nghin(CS.so_van_ban)} văn bản, kèm từ đã khớp.`,
    { x: MX, y: 6.05, w: CW, h: 0.4, fontSize: 15, color: INK2 });
}

// slide 3: nghiên cứu trước
{
  const s = slide("NGHIÊN CỨU TRƯỚC", "Kết hợp từ khóa và ngữ nghĩa đã là công thức quen thuộc");

  const nen = (i) => (i === 3 ? SEAL_S : i % 2 ? "FFFFFF" : PAPER);
  const TH = { bold: true, color: MUTED, fontFace: MF, fontSize: 11, fill: { color: "FFFFFF" } };
  const hang = [
    ["Ghép BM25 với ngữ nghĩa", "Zalo AI 2021; Khang 2024; ViDRILL, VLSP 2025; Nguyen và Quan, EACL 2026", "Ghép tốt hơn từng tầng"],
    ["Làm mạnh tầng ngữ nghĩa", "Pham 2022; Pham Tien 2024; Le 2025, UIT; ALQAC 2021-2023", "Không hỏi BM25 còn góp bao nhiêu"],
    ["Cách hợp nhất", "Cormack 2009 (RRF); Bruch 2023, ACM TOIS", "Tổng trọng số hơn RRF khi chỉnh được"],
    ["Phục hồi dấu tiếng Việt", "Pham, Pham, Le-Hong 2017; Le-Hong 2021", "Khoảng 97%, chưa đo cho tìm luật"],
    ["Đánh giá mô hình nhúng", "MMTEB, ICLR 2025; Chung 2025", "Phải đánh dấu mô hình đã học dữ liệu"],
  ].map((r, i) => [
    { text: r[0], options: { bold: true, fill: { color: nen(i) } } },
    { text: r[1], options: { color: INK2, fontSize: 13, fill: { color: nen(i) } } },
    { text: r[2], options: { bold: i === 3, color: i === 3 ? SEAL : INK, fill: { color: nen(i) } } },
  ]);
  s.addTable([[
    { text: "HƯỚNG", options: TH }, { text: "CÔNG TRÌNH TIÊU BIỂU", options: TH }, { text: "HỌ KẾT LUẬN", options: TH },
  ], ...hang], { x: MX, y: 1.9, w: CW, colW: [3.0, 5.53, 3.5], rowH: [0.42, 0.72, 0.72, 0.72, 0.72, 0.72],
    fontFace: BF, fontSize: 15, color: INK, valign: "middle", margin: [0, 0.12, 0, 0.12],
    border: { type: "solid", pt: 0.75, color: RULE } });
  tx(s, "Nhóm đối chiếu 27 nguồn theo tóm tắt, mã nguồn và model card. Danh sách ở slide 16.",
    { x: MX, y: 6.05, w: CW, h: 0.35, fontSize: 13, italic: true, color: MUTED });
}

// slide 4: khoảng trống và câu hỏi nghiên cứu
{
  const s = slide("CÂU HỎI NGHIÊN CỨU", "Chưa ai đo hệ tìm luật chịu được câu mất dấu tới đâu");

  const gx = MX + 1.85, gy = 2.35, cw = 2.85, ch = 1.6, g = 0.12;
  ["Câu hỏi có dấu", "Câu hỏi không dấu"].forEach((t, j) =>
    tx(s, t, { x: gx + j * (cw + g), y: gy - 0.42, w: cw, h: 0.32, fontSize: 14, bold: true, color: INK2, align: "center" }));
  ["Đo tìm luật", "Đo phục hồi dấu"].forEach((t, i) =>
    tx(s, t, { x: MX, y: gy + i * (ch + g), w: 1.7, h: ch, fontSize: 14, bold: true, color: INK2, valign: "middle" }));
  const o = [
    [ACC_S, null, "Đã làm nhiều", "Zalo 2021, ALQAC, EACL 2026", ACC],
    ["FFFFFF", SEAL, "Chưa ai đo", "câu hỏi nghiên cứu 2", SEAL],
    [PAPER, null, "Không áp dụng", "", MUTED],
    [ACC_S, null, "Đã làm, khoảng 97%", "Pham 2017, Le-Hong 2021", ACC],
  ];
  o.forEach((c, k) => {
    const x = gx + (k % 2) * (cw + g), y = gy + Math.floor(k / 2) * (ch + g);
    hop(s, x, y, cw, ch, c[0], c[1], true);
    tx(s, c[2], { x: x + 0.2, y: y + 0.38, w: cw - 0.4, h: 0.45, fontFace: HF, fontSize: k === 1 ? 24 : 18,
      bold: true, color: c[4], align: "center" });
    tx(s, c[3], { x: x + 0.2, y: y + 0.92, w: cw - 0.4, h: 0.35, fontSize: 13, color: INK2, align: "center" });
  });

  const rx = 8.55, rw = W - MX - rx;
  hop(s, rx, 1.95, rw, 1.75, PAPER);
  tx(s, "CH1", { x: rx + 0.3, y: 2.12, w: 1, h: 0.3, fontFace: MF, fontSize: 13, bold: true, color: ACC });
  tx(s, "Trên dữ liệu đã kiểm toán, với mô hình chưa thấy dữ liệu, ghép thêm BM25 còn giúp bao nhiêu?",
    { x: rx + 0.3, y: 2.48, w: rw - 0.6, h: 1.1, fontSize: 16, valign: "top" });
  hop(s, rx, 3.9, rw, 1.95, SEAL_S);
  tx(s, "CH2", { x: rx + 0.3, y: 4.07, w: 1, h: 0.3, fontFace: MF, fontSize: 13, bold: true, color: SEAL });
  tx(s, "Khi người dùng gõ không dấu, hệ còn đứng vững không, và cách sửa rẻ nhất là gì?",
    { x: rx + 0.3, y: 4.43, w: rw - 0.6, h: 1.3, fontSize: 16, bold: true, valign: "top" });
}

// slide 5: dữ liệu và kiểm toán
{
  const sn = (f) => demDong(path.join(AUDIT, f));
  const nhanDoi = DIA.reduce((a, b) => a + Number(b.so_dieu), 0);
  const muc = [
    ["Điều luật trùng nguyên văn", sn("duplicate_articles.csv")],
    ["Cặp điều luật gần trùng", sn("near_duplicate_articles.csv")],
    ["Điều bị nhân đôi vì nd và nđ", nhanDoi],
    ["Điều luật rỗng nội dung", sn("empty_articles.csv")],
    ["Câu hỏi bị lặp dòng", sn("duplicate_queries.csv")],
    ["Câu hỏi nằm ở cả train và test", CHONG_LAN.length],
  ];
  const s = slide("DỮ LIỆU", `Bộ Zalo 2021 đã công bố vẫn còn ${muc.length} vấn đề khi kiểm toán lại`);

  const lx = MX, ly = 1.95;
  [[nghin(CS.so_dieu_luat), "điều luật"], [nghin(CS.so_van_ban), "văn bản"],
   [nghin(CS.so_cau_hoi_id_duy_nhat), "câu hỏi"], ["0", "tập val trong bộ gốc"]].forEach((m, i) => {
    tx(s, m[0], { x: lx, y: ly + i * 1.02, w: 2.6, h: 0.6, fontFace: HF, fontSize: 32, bold: true, color: i === 3 ? SEAL : INK });
    tx(s, m[1], { x: lx, y: ly + i * 1.02 + 0.58, w: 2.9, h: 0.3, fontSize: 13, color: INK2 });
  });

  const dao = muc.slice().reverse();   // biểu đồ ngang vẽ từ dưới lên
  s.addChart(p.ChartType.bar, [{ name: "Số bản ghi", labels: dao.map((m) => m[0]), values: dao.map((m) => m[1]) }], {
    x: 3.7, y: 1.8, w: W - MX - 3.7, h: 4.7, barDir: "bar", barGapWidthPct: 45, chartColors: [ACC],
    valAxisLogScaleBase: 10, valAxisHidden: true, valAxisMinVal: 10, valGridLine: { style: "none" },
    catGridLine: { style: "none" }, catAxisLabelFontFace: BF, catAxisLabelFontSize: 14, catAxisLabelColor: INK,
    catAxisLineShow: false, showValue: true, dataLabelPosition: "outEnd", dataLabelFontFace: BF,
    dataLabelFontSize: 14, dataLabelColor: INK, dataLabelFormatCode: '[>=1000]#"."##0;0', showLegend: false,
  });
  tx(s, "Trục ngang thang log", { x: W - MX - 3, y: 6.5, w: 3, h: 0.25, fontSize: 11, italic: true, color: MUTED, align: "right" });
}

// slide 6: nhãn mâu thuẫn
{
  const s = slide("RÒ RỈ DỮ LIỆU", `${CONFLICT.length} trên ${TRUNG_ID} câu hỏi trùng giữa train và test mang nhãn khác nhau`);

  tx(s, `${CONFLICT.length}/${TRUNG_ID}`, { x: MX, y: 1.95, w: 3.6, h: 1.5, fontFace: HF, fontSize: 88, bold: true, color: SEAL });
  tx(s, "câu hỏi trùng mã giữa train và test mang hai điều luật gold khác nhau",
    { x: MX, y: 3.5, w: 3.4, h: 1.0, fontSize: 16, color: INK, valign: "top" });
  tx(s, `${CHONG_LAN.length} câu chồng lấn gồm ${TRUNG_ID} câu trùng mã và ${CHONG_LAN.length - TRUNG_ID} câu gần giống`,
    { x: MX, y: 4.6, w: 3.4, h: 0.7, fontSize: 13, color: MUTED, valign: "top" });

  const TH = { bold: true, color: MUTED, fontFace: MF, fontSize: 11 };
  const hang = CONFLICT.slice(0, 3).map((h) => [
    { text: h.text.length > 70 ? h.text.slice(0, 68) + "…" : h.text, options: {} },
    { text: h.gold_train, options: { fontFace: MF, fontSize: 12, color: ACC } },
    { text: h.gold_test, options: { fontFace: MF, fontSize: 12, color: SEAL } },
  ]);
  const tx0 = 4.45;
  s.addTable([[{ text: "CÂU HỎI", options: TH }, { text: "GOLD Ở TRAIN", options: TH }, { text: "GOLD Ở TEST", options: TH }],
    ...hang], { x: tx0, y: 1.95, w: W - MX - tx0, colW: [3.9, 2.12, 2.21], rowH: [0.4, 0.85, 0.85, 0.85],
    fontFace: BF, fontSize: 14, color: INK, valign: "middle", margin: [0, 0.1, 0, 0.1],
    border: { type: "solid", pt: 0.75, color: RULE } });

  hop(s, tx0, 5.25, W - MX - tx0, 0.95, OK_S);
  tx(s, `Bỏ dòng train của các câu này, test giữ nguyên ${nghin(SPLIT.test.so_cap_qrel)} cặp của ban tổ chức. Mọi Recall là cận dưới.`,
    { x: tx0 + 0.25, y: 5.25, w: W - MX - tx0 - 0.5, h: 0.95, fontSize: 15, color: OK, bold: true, valign: "middle" });
}

// slide 7: mô hình đã thấy tập test
{
  const s = slide("RÒ RỈ DỮ LIỆU", "Mô hình phổ biến nhất đã học chính tập test");

  const y0 = 1.95, wT = (CW - 0.4) / 2, hT = 2.75;
  const the = (x, ten, nhan, mau, nen, trich, ket) => {
    hop(s, x, y0, wT, hT, nen);
    hop(s, x + 0.35, y0 + 0.3, 1.4, 0.36, mau);
    tx(s, nhan, { x: x + 0.35, y: y0 + 0.3, w: 1.4, h: 0.36, fontFace: MF, fontSize: 12, bold: true,
      color: "FFFFFF", align: "center", valign: "middle" });
    tx(s, ten, { x: x + 0.35, y: y0 + 0.8, w: wT - 0.7, h: 0.3, fontFace: MF, fontSize: 13, color: INK2 });
    tx(s, trich, { x: x + 0.35, y: y0 + 1.2, w: wT - 0.7, h: 0.95, fontFace: HF, fontSize: 19, italic: true, valign: "top" });
    tx(s, ket, { x: x + 0.35, y: y0 + 2.2, w: wT - 0.7, h: 0.4, fontSize: 14, color: mau, bold: true, valign: "top" });
  };
  the(MX, "bkai-foundation-models/vietnamese-bi-encoder", "NHIỄM BẨN", SEAL, SEAL_S,
    "“80% of the training set from the Legal Text Retrieval Zalo 2021 challenge”",
    "Tập test của nhóm cắt ra từ đúng tập train này");
  the(MX + wT + 0.4, "AITeamVN/Vietnamese_Embedding", "SẠCH", OK, OK_S,
    "“Our model was not trained on this dataset”",
    "Dùng cho mọi con số chính thức");

  tx(s, "CHIA LẠI TẬP THEO CÂU HỎI", { x: MX, y: 5.0, w: 6, h: 0.3, fontFace: MF, fontSize: 12, color: ACC, bold: true });
  [["train", SPLIT.train.so_cau_hoi, `đã bỏ ${CHONG_LAN.length} câu rò rỉ`],
   ["val", SPLIT.val.so_cau_hoi, "cắt từ train, seed 42, để chỉnh tham số"],
   ["test", SPLIT.test.so_cau_hoi, "nguyên vẹn, chỉ chạy một lần"]].forEach((t, i) => {
    const x = MX + i * (CW / 3);
    tx(s, [{ text: nghin(t[1]), options: { fontFace: HF, fontSize: 26, bold: true } },
           { text: `  câu hỏi ${t[0]}`, options: { fontSize: 15, color: INK2 } }],
      { x, y: 5.35, w: CW / 3 - 0.2, h: 0.55 });
    tx(s, t[2], { x, y: 5.9, w: CW / 3 - 0.2, h: 0.3, fontSize: 13, color: MUTED });
  });
}

// slide 8: kiến trúc
{
  const s = slide("PHƯƠNG PHÁP", "Một khâu phục hồi dấu đứng trước ba tầng tìm kiếm");

  const cy = 3.55, bh = 1.25;
  const khoi = (x, y, w, ten, phu, mau, nen) => {
    hop(s, x, y, w, bh, nen, mau);
    tx(s, ten, { x: x + 0.15, y: y + 0.18, w: w - 0.3, h: 0.4, fontSize: 17, bold: true, color: mau === MUTED ? INK : mau, align: "center" });
    tx(s, phu, { x: x + 0.15, y: y + 0.6, w: w - 0.3, h: 0.55, fontSize: 12.5, color: INK2, align: "center", valign: "top" });
  };
  khoi(MX, cy, 1.75, "Câu hỏi", "có dấu, không dấu\nhoặc nửa dấu", MUTED, "FFFFFF");
  khoi(2.85, cy, 2.2, "Phục hồi dấu", "bigram âm tiết\nvà Viterbi", SEAL, SEAL_S);
  khoi(5.65, 2.05, 2.6, "Từ khóa: BM25", `tách từ pyvi\n${nghin(CS.so_dieu_luat)} điều`, ACC, ACC_S);
  khoi(5.65, 5.05, 2.6, "Ngữ nghĩa", `AITeamVN, ${nghin(CHUNKS)} đoạn\ngộp về điều bằng max`, WARN, "FBF1E1");
  khoi(8.85, cy, 1.9, "Hợp nhất", `trọng số\nalpha = ${so(TS.weighted.alpha, 2)}`, OK, OK_S);
  khoi(11.1, cy, W - MX - 11.1, "Điều luật", "trích nguyên văn\nkhoản luật", MUTED, "FFFFFF");
  const my = cy + bh / 2;
  muiTen(s, MX + 1.75, my, 2.85, my);
  muiTen(s, 5.05, my - 0.2, 5.65, 2.05 + bh / 2);
  muiTen(s, 5.05, my + 0.2, 5.65, 5.05 + bh / 2);
  muiTen(s, 8.25, 2.05 + bh / 2, 8.85, my - 0.2);
  muiTen(s, 8.25, 5.05 + bh / 2, 8.85, my + 0.2);
  muiTen(s, 10.75, my, 11.1, my);
  tx(s, "bắt đúng số hiệu, thuật ngữ, con số", { x: 5.4, y: 1.7, w: 3.1, h: 0.3, fontSize: 12.5, italic: true, color: ACC, align: "center" });
  tx(s, "bắt được cách diễn đạt khác", { x: 5.4, y: 6.35, w: 3.1, h: 0.3, fontSize: 12.5, italic: true, color: WARN, align: "center" });
  tx(s, `Chốt trên val: k1 = ${so(TS.bm25.k1, 1)}, b = ${so(TS.bm25.b, 1)}, lambda = ${so(KDP.lambda_phuc_hoi, 1)}.\nTập test chỉ chạy một lần.`,
    { x: 8.85, y: 5.4, w: W - MX - 8.85, h: 0.8, fontSize: 13, color: MUTED, valign: "top" });
}

// slide 9: chia đoạn
{
  const s = slide("PHƯƠNG PHÁP", `${so(DODAI.ty_le_vuot_tran_pct, 0)}% điều luật dài hơn giới hạn của mô hình, nên phải chia đoạn`);

  const pb = DODAI.phan_bo;
  const nhan = pb.map((c) => (c.den === null ? `≥${nghin(c.tu)}` : String(c.tu)));
  const duoi = pb.map((c) => (c.den !== null && c.den <= DODAI.tran_tu_tuong_duong ? c.so_dieu : 0));
  const tren = pb.map((c, i) => c.so_dieu - duoi[i]);
  s.addChart(p.ChartType.bar, [
    { name: `≤ ${DODAI.tran_tu_tuong_duong} từ, vừa mô hình`, labels: nhan, values: duoi },
    { name: `> ${DODAI.tran_tu_tuong_duong} từ, bị cắt nếu không chia`, labels: nhan, values: tren },
  ], { x: MX, y: 1.8, w: 8.2, h: 4.75, barDir: "col", barGrouping: "stacked", barGapWidthPct: 15,
    chartColors: [ACC, SEAL], showValue: false, catAxisLabelFrequency: 10, catAxisLabelFontFace: BF,
    catAxisLabelFontSize: 12, catAxisLabelColor: INK2, catAxisLineColor: RULE, valAxisLabelFontFace: BF,
    valAxisLabelFontSize: 11, valAxisLabelColor: MUTED, valAxisLabelFormatCode: '[>=1000]#"."##0;0',
    valGridLine: { color: "ECEEEB", size: 0.75 }, catGridLine: { style: "none" }, valAxisLineShow: false,
    showLegend: true, legendPos: "t", legendFontFace: BF, legendFontSize: 12, legendColor: INK2,
    showCatAxisTitle: true, catAxisTitle: "Độ dài điều luật (số từ)", catAxisTitleFontSize: 12, catAxisTitleColor: MUTED });

  const rx = 9.3, rw = W - MX - rx;
  soLon(s, rx, 2.0, rw, `${so(DODAI.ty_le_vuot_tran_pct, 1)}%`, `điều luật dài hơn 256 token (khoảng ${DODAI.tran_tu_tuong_duong} từ)`, SEAL, 48);
  tx(s, [{ text: nghin(CS.so_dieu_luat), options: { bold: true } }, { text: " điều", options: { breakLine: true } },
         { text: "↓", options: { color: MUTED, breakLine: true } },
         { text: nghin(CHUNKS), options: { bold: true } }, { text: " đoạn" }],
    { x: rx, y: 3.75, w: rw, h: 1.35, fontFace: HF, fontSize: 24, valign: "top" });
  tx(s, "Cắt theo ranh giới khoản, khoản quá dài mới trượt cửa sổ. Mỗi đoạn mang tiêu đề điều.",
    { x: rx, y: 5.2, w: rw, h: 0.9, fontSize: 13, color: INK2, valign: "top" });
}

// slide 10: CH1, kết quả câu có dấu
{
  const s = slide("CH1  ·  CÂU CÓ DẤU", `Trên câu có dấu, hợp nhất chỉ hơn ngữ nghĩa ${so(loiHopR, 2)} điểm Recall@10`);

  const heS = [["BM25", BM], [`Ngữ nghĩa`, DE_SACH], ["RRF", RRF_SACH], ["Hợp nhất trọng số", HE_SACH]];
  bieuDo(s, [
    { name: "Recall@1", labels: heS.map((h) => h[0]), values: heS.map((h) => VAN(h[1]["recall@1"])) },
    { name: "Recall@10", labels: heS.map((h) => h[0]), values: heS.map((h) => VAN(h[1]["recall@10"])) },
  ], { x: MX, y: 1.8, w: 8.1, h: 4.75, chartColors: [ACC_L, ACC] });

  const rx = 9.25, rw = W - MX - rx;
  soLon(s, rx, 2.0, rw, `+${so(loiHopR, 2)}`, "điểm Recall@10 của hợp nhất so với ngữ nghĩa thuần", ACC, 54);
  tx(s, `tức ${soCauHop} câu trên ${TONG_TEST} có gold lọt vào top-10 nhờ hợp nhất`,
    { x: rx, y: 3.75, w: rw, h: 0.65, fontSize: 14, color: INK, valign: "top" });
  tx(s, `RRF còn kém ngữ nghĩa ở Recall@1: ${so(RRF_SACH["recall@1"])} so với ${so(DE_SACH["recall@1"])}`,
    { x: rx, y: 4.55, w: rw, h: 0.65, fontSize: 14, color: SEAL, valign: "top" });
  tx(s, "Chỉ so hệ sạch. bkai đạt cao hơn nhưng đã học tập test.",
    { x: rx, y: 5.45, w: rw, h: 0.65, fontSize: 12.5, italic: true, color: MUTED, valign: "top" });
}

// slide 11: CH1, BM25 cứu được bao nhiêu
{
  const chiBm = CROSS["chỉ BM25 đúng"], chiDe = CROSS["chỉ ngữ nghĩa đúng"];
  const caHai = CROSS["cả hai đúng"], khongAi = CROSS["cả hai sai"];
  const tong = chiBm + chiDe + caHai + khongAi;
  const lan = Math.round(tocDo / 100) * 100;
  const s = slide("CH1  ·  CÂU CÓ DẤU", `BM25 chỉ cứu thêm ${chiBm} câu, nhưng nhanh hơn khoảng ${lan} lần`);

  // hai vòng tròn chồng nhau
  const cy = 4.05, r = 1.85, xa = 1.55, xb = 3.95;
  s.addShape(p.ShapeType.ellipse, { x: xa, y: cy - r, w: 2 * r, h: 2 * r, fill: { color: ACC, transparency: 72 }, line: { color: ACC, width: 1.5 } });
  s.addShape(p.ShapeType.ellipse, { x: xb, y: cy - r, w: 2 * r, h: 2 * r, fill: { color: WARN, transparency: 72 }, line: { color: WARN, width: 1.5 } });
  tx(s, "BM25 đúng", { x: xa, y: cy - r - 0.45, w: 2.2, h: 0.35, fontSize: 15, bold: true, color: ACC });
  tx(s, "Ngữ nghĩa đúng", { x: xb + 2 * r - 2.4, y: cy - r - 0.45, w: 2.4, h: 0.35, fontSize: 15, bold: true, color: WARN, align: "right" });
  tx(s, String(chiBm), { x: xa + 0.25, y: cy - 0.4, w: 1.4, h: 0.8, fontFace: HF, fontSize: 40, bold: true, color: SEAL, align: "center" });
  tx(s, String(caHai), { x: xb, y: cy - 0.4, w: xa + 2 * r - xb, h: 0.8, fontFace: HF, fontSize: 34, bold: true, align: "center" });
  tx(s, String(chiDe), { x: xa + 2 * r + 0.05, y: cy - 0.4, w: xb + 2 * r - (xa + 2 * r) - 0.2, h: 0.8, fontFace: HF, fontSize: 34, bold: true, align: "center" });
  tx(s, `Cả hai sai: ${khongAi} câu. Tính ở top-10, ${tong} câu test.`, { x: xa, y: cy + r + 0.15, w: 6.2, h: 0.35, fontSize: 13, color: MUTED });

  const rx = 8.7, rw = W - MX - rx;
  tx(s, "MỖI TRUY VẤN", { x: rx, y: 1.95, w: rw, h: 0.3, fontFace: MF, fontSize: 12, bold: true, color: ACC });
  soLon(s, rx, 2.3, rw / 2, `${so(BM["latency_p50_ms"], 1)} ms`, "BM25", ACC, 34);
  soLon(s, rx + rw / 2, 2.3, rw / 2, `${so(DE_SACH["latency_p50_ms"], 0)} ms`, "ngữ nghĩa", WARN, 34);
  tx(s, "CHỈ MỤC", { x: rx, y: 3.75, w: rw, h: 0.3, fontFace: MF, fontSize: 12, bold: true, color: ACC });
  soLon(s, rx, 4.1, rw / 2, `${so(COST.bm25.dung_luong_mb, 0)} MB`, "BM25", ACC, 34);
  soLon(s, rx + rw / 2, 4.1, rw / 2, `${so(COST[BEST.dense_sach].dung_luong_mb, 0)} MB`, "ngữ nghĩa", WARN, 34);
  tx(s, "BM25 còn chỉ ra được từ nào đã khớp.", { x: rx, y: 5.6, w: rw, h: 0.5, fontSize: 14, bold: true });
}

// slide 12: CH2, câu gõ không dấu sụp đổ
{
  const heK = [["BM25", "BM25"], ["Ngữ nghĩa", "Ngữ nghĩa"], ["Hợp nhất", "Hợp nhất"]];
  const coDe = kd("có dấu", "giữ nguyên", "Ngữ nghĩa"), khDe = kd("không dấu", "giữ nguyên", "Ngữ nghĩa");
  const bmBo = kd("không dấu", "chỉ mục bỏ dấu", "BM25 bỏ dấu");
  const s = slide("CH2  ·  CÂU MẤT DẤU", `Mất dấu, mô hình ngữ nghĩa tốt nhất tụt từ ${pt(coDe["recall@10"], 0)}% còn ${pt(khDe["recall@10"], 0)}%`);

  bieuDo(s, [
    { name: "Câu có dấu", labels: heK.map((h) => h[0]), values: heK.map((h) => VAN(kd("có dấu", "giữ nguyên", h[1])["recall@10"])) },
    { name: "Cùng câu, bỏ hết dấu", labels: heK.map((h) => h[0]), values: heK.map((h) => VAN(kd("không dấu", "giữ nguyên", h[1])["recall@10"])) },
  ], { x: MX, y: 1.8, w: 8.1, h: 4.75, chartColors: [INK2, SEAL], dataLabelFontSize: 14 });

  const rx = 9.25, rw = W - MX - rx;
  tx(s, "VÌ SAO", { x: rx, y: 2.0, w: rw, h: 0.3, fontFace: MF, fontSize: 12, bold: true, color: SEAL });
  tx(s, [{ text: "BM25: ", options: { bold: true } }, { text: "“phat” và “phạt” là hai chữ khác nhau, không khớp gì.", options: { breakLine: true } },
         { text: " ", options: { breakLine: true, fontSize: 8 } },
         { text: "Ngữ nghĩa: ", options: { bold: true } }, { text: "giả thuyết là mô hình học chủ yếu văn bản có dấu. Chưa kiểm chứng." }],
    { x: rx, y: 2.35, w: rw, h: 2.2, fontSize: 15, valign: "top" });
  hop(s, rx, 4.75, rw, 1.35, PAPER);
  tx(s, `Chỉ mục BM25 trên văn bản bỏ dấu lên lại ${pt(bmBo["recall@10"])}%, không cần mô hình.`,
    { x: rx + 0.25, y: 4.75, w: rw - 0.5, h: 1.35, fontSize: 14, color: INK, valign: "middle" });
}

// slide 13: CH2, sửa bằng phục hồi dấu
{
  const coHop = kd("có dấu", "giữ nguyên", "Hợp nhất"), khHop = kd("không dấu", "giữ nguyên", "Hợp nhất");
  const phHop = kd("không dấu", "phục hồi dấu", "Hợp nhất");
  const s = slide("CH2  ·  CÂU MẤT DẤU", `Phục hồi dấu bằng bigram kéo hệ về ${pt(phHop["recall@10"], 1)}%, không cần GPU`);

  const lx = MX, lw = 5.6;
  tx(s, "VÍ DỤ", { x: lx, y: 1.95, w: lw, h: 0.3, fontFace: MF, fontSize: 12, bold: true, color: ACC });
  tx(s, "nguoi lao dong nghi viec", { x: lx, y: 2.3, w: lw, h: 0.45, fontFace: MF, fontSize: 20, color: SEAL });
  tx(s, [{ text: "nghi  →  ", options: { fontFace: MF, color: MUTED } }, { text: "nghỉ", options: { bold: true, color: OK } },
         { text: "   nghị   nghĩ   nghi", options: { color: MUTED } }],
    { x: lx, y: 2.85, w: lw, h: 0.45, fontSize: 18 });
  tx(s, "người lao động nghỉ việc", { x: lx, y: 3.4, w: lw, h: 0.5, fontFace: HF, fontSize: 22, bold: true, color: OK });
  tx(s, [
    { text: `1.  Đếm bigram trên ${so(KDP.so_am_tiet / 1e6, 1)} triệu âm tiết của kho luật`, options: { breakLine: true } },
    { text: "2.  Sinh ứng viên có dấu cho mỗi âm tiết", options: { breakLine: true } },
    { text: `3.  Viterbi chọn chuỗi xác suất cao nhất, lambda = ${so(KDP.lambda_phuc_hoi, 1)}`, options: { breakLine: true } },
    { text: "4.  Âm tiết đã có dấu thì giữ nguyên" },
  ], { x: lx, y: 4.15, w: lw, h: 1.6, fontSize: 15, color: INK2, paraSpaceAfter: 5, valign: "top" });

  cotMau(s, ["Có dấu (mốc)", "Không dấu, giữ nguyên", "Không dấu, phục hồi dấu"],
    [coHop["recall@10"], khHop["recall@10"], phHop["recall@10"]], [INK2, SEAL, OK],
    { x: 6.55, y: 1.8, w: W - MX - 6.55, h: 3.85, catAxisLabelFontSize: 12.5 });
  tx(s, "Recall@10 của hệ hợp nhất (%)", { x: 6.7, y: 5.6, w: 4, h: 0.26, fontSize: 11, italic: true, color: MUTED });

  [[`${pt(KDP.do_chinh_xac_am_tiet_test)}%`, "âm tiết phục hồi đúng"],
   [`${so(KDP.do_tre_phuc_hoi_ms, 2)} ms`, "mỗi câu hỏi"],
   [`${KDP.giay_hoc_mo_hinh} giây`, "để học, chạy trên CPU"]].forEach((k, i) => {
    const x = 6.7 + i * 2.0;
    tx(s, k[0], { x, y: 5.95, w: 1.95, h: 0.42, fontFace: HF, fontSize: 20, bold: true, color: OK });
    tx(s, k[1], { x, y: 6.37, w: 1.95, h: 0.3, fontSize: 11.5, color: INK2 });
  });
}

// slide 14: CH2, sai ở đâu, và câu gõ nửa dấu
{
  const saiNhom = KDL["sai ít nhất một âm tiết"], mat = KDL["mất do phục hồi sai"], duoc = KDL["được nhờ phục hồi"];
  const nuaGiu = kd("nửa dấu", "giữ nguyên", "Hợp nhất"), nuaPh = kd("nửa dấu", "phục hồi dấu", "Hợp nhất");
  const coPh = kd("có dấu", "phục hồi dấu", "Hợp nhất");
  const s = slide("CH2  ·  CÂU MẤT DẤU", "Phục hồi sai ở từ nói thường, nhưng sửa được cả câu gõ nửa dấu");

  const lx = MX, lw = 5.5;
  tx(s, "PHỤC HỒI SAI", { x: lx, y: 1.95, w: lw, h: 0.3, fontFace: MF, fontSize: 12, bold: true, color: SEAL });
  [["tài xế", "tải xe"], ["máu", "mẫu"], ["đi bộ", "đi bờ"]].forEach((c, i) => {
    const y = 2.4 + i * 0.62;
    tx(s, c[0], { x: lx, y, w: 1.8, h: 0.5, fontFace: HF, fontSize: 22, color: OK, bold: true });
    tx(s, "→", { x: lx + 1.9, y, w: 0.5, h: 0.5, fontSize: 20, color: MUTED });
    tx(s, c[1], { x: lx + 2.5, y, w: 2.0, h: 0.5, fontFace: HF, fontSize: 22, color: SEAL, bold: true });
  });
  tx(s, `${saiNhom.so_cau} câu sai ít nhất một âm tiết. Trong nhóm này, tỷ lệ tìm đúng ở top-10 tụt từ ${so(saiNhom.ty_le_dung_top10_cau_goc_pct, 2)}% xuống ${so(saiNhom.ty_le_dung_top10_phuc_hoi_pct, 2)}%: mất ${mat.so_cau} câu, được ${duoc.so_cau} câu.`,
    { x: lx, y: 4.45, w: lw, h: 1.2, fontSize: 15, color: INK2, valign: "top" });

  tx(s, "CÂU GÕ NỬA DẤU", { x: 6.55, y: 1.95, w: 5, h: 0.3, fontFace: MF, fontSize: 12, bold: true, color: OK });
  cotMau(s, ["Nửa dấu, giữ nguyên", "Nửa dấu, phục hồi dấu", "Câu đủ dấu, vẫn phục hồi"],
    [nuaGiu["recall@10"], nuaPh["recall@10"], coPh["recall@10"]], [SEAL, OK, INK2],
    { x: 6.55, y: 2.3, w: W - MX - 6.55, h: 3.85, catAxisLabelFontSize: 12.5 });
  tx(s, "Recall@10 của hệ hợp nhất (%)", { x: 6.7, y: 6.15, w: 4, h: 0.26, fontSize: 11, italic: true, color: MUTED });
}

// slide 15: kết luận
{
  n += 1;
  const s = p.addSlide();
  s.background = { color: INK };
  const khHop = kd("không dấu", "giữ nguyên", "Hợp nhất"), phHop = kd("không dấu", "phục hồi dấu", "Hợp nhất");
  tx(s, `KẾT LUẬN  ·  ${n}`, { x: MX, y: 0.36, w: 6, h: 0.26, fontFace: MF, fontSize: 11, color: ACC_L, charSpacing: 1 });
  tx(s, "Ba điều nhóm rút ra", { x: MX, y: 0.64, w: CW, h: 0.8, fontFace: HF, fontSize: 32, bold: true, color: "FFFFFF" });
  const muc = [
    [`+${so(loiHopR, 2)}`, "CH1  ·  CÂU CÓ DẤU", `Hợp nhất chỉ hơn ngữ nghĩa ${soCauHop} câu trên ${TONG_TEST}. BM25 vẫn đáng giữ vì nhanh và giải thích được.`, ACC_L],
    [`${pt(khHop["recall@10"], 0)} → ${pt(phHop["recall@10"], 0)}`, "CH2  ·  CÂU MẤT DẤU", `Mất dấu thì hệ sụp. Bigram học từ chính kho luật kéo lại gần hết, ${so(KDP.do_tre_phuc_hoi_ms, 2)} ms mỗi câu.`, "7FD1B0"],
    ["80%", "RÒ RỈ DỮ LIỆU", "Mô hình phổ biến nhất đã học tập train Zalo. Đọc model card trước khi tin một con số benchmark.", "F0A0A6"],
  ];
  const cw = (CW - 0.8) / 3;
  muc.forEach((m, i) => {
    const x = MX + i * (cw + 0.4);
    tx(s, m[0], { x, y: 1.95, w: cw, h: 1.0, fontFace: HF, fontSize: 48, bold: true, color: m[3] });
    tx(s, m[1], { x, y: 3.05, w: cw, h: 0.3, fontFace: MF, fontSize: 12, bold: true, color: "C9D6DF" });
    tx(s, m[2], { x, y: 3.45, w: cw, h: 1.5, fontSize: 16, color: "FFFFFF", valign: "top" });
  });
  tx(s, "Giới hạn: câu không dấu và nửa dấu do máy tạo, chưa có câu người thật gõ  ·  nhãn không đầy đủ nên Recall là cận dưới  ·  mỗi cấu hình một seed",
    { x: MX, y: 5.35, w: CW, h: 0.6, fontSize: 13, color: "9AA8B2", valign: "top" });
  tx(s, "Tiếp theo: demo trên Kaggle  →", { x: MX, y: 6.25, w: CW, h: 0.45, fontSize: 18, bold: true, color: "FFFFFF", align: "right" });
  tx(s, `${String(n).padStart(2, "0")} / ${TONG}`, { x: W - MX - 1.5, y: H - 0.42, w: 1.5, h: 0.24,
    fontFace: MF, fontSize: 10, color: "9AA8B2", align: "right" });
  s.addNotes(ghiChu(n));
}

// slide 16: tài liệu tham khảo
{
  const md = fs.readFileSync(path.join(ROOT, "docs", "NGHIEN_CUU_LIEN_QUAN.md"), "utf8");
  const phan = md.split(/^## Tài liệu tham khảo\s*$/m)[1] || "";
  const tl = phan.split(/\r?\n/).map((l) => l.match(/^(\d+)\.\s+(.*)$/)).filter(Boolean)
    .map((m) => `[${m[1]}] ${m[2].replace(/\*/g, "")}`);
  if (tl.length === 0) throw new Error("Không đọc được tài liệu tham khảo từ NGHIEN_CUU_LIEN_QUAN.md");
  const s = slide("PHỤ LỤC", "Tài liệu tham khảo");
  const nua = Math.ceil(tl.length / 2);
  [tl.slice(0, nua), tl.slice(nua)].forEach((cot, i) => {
    tx(s, cot.map((t, j) => ({ text: t, options: { breakLine: j < cot.length - 1 } })),
      { x: MX + i * (CW / 2 + 0.1), y: 1.55, w: CW / 2 - 0.1, h: 5.4,
        fontSize: 9.5, color: INK2, paraSpaceAfter: 2.5, valign: "top" });
  });
}

if (n !== TONG) throw new Error(`Dựng ${n} slide nhưng TONG = ${TONG}: sửa TONG cho khớp.`);
// bấm giờ theo số âm tiết, và xuất lời thoại cho file Word kịch bản
let tongGiay = 0, tongDuKien = 0;
const bang = ["| Slide | Người nói | Dự kiến | Ước theo số chữ |", "|---|---|---|---|"];
const md = ["## Lời thoại", ""];
Object.keys(LOI).map(Number).forEach((so) => {
  const l = LOI[so], uoc = Math.round(demAmTiet(l) / AM_TIET_MOI_GIAY) + NGHI_MOI_SLIDE;
  tongGiay += uoc; tongDuKien += l.giay;
  bang.push(`| ${so} | ${l.nguoi} | ${l.giay} giây | ${uoc} giây |`);
  if (Math.abs(uoc - l.giay) > 8) console.log(`  slide ${so}: dự kiến ${l.giay} giây, lời thoại đọc mất khoảng ${uoc} giây`);
  md.push(`### Slide ${so}. ${l.nguoi}, khoảng ${l.giay} giây`, "", ...l.noi.flatMap((d) => [d, ""]));
  (l.hoi || []).forEach(([h, d]) => md.push(`Nếu thầy hỏi: ${h}`, "", d, ""));
});
const phut = (g) => `${Math.floor(g / 60)} phút ${g % 60} giây`;
bang.push(`| Tổng | | ${phut(tongDuKien)} | ${phut(tongGiay)} |`);
console.log(`  lời thoại: dự kiến ${phut(tongDuKien)}, ước theo số chữ ${phut(tongGiay)}`);
fs.writeFileSync(path.join(ROOT, "docs", "LOI_THOAI.md"),
  ["# Lời thoại từng slide", "", "## Thời lượng", "", `Ước theo ${String(AM_TIET_MOI_GIAY).replace(".", ",")} âm tiết mỗi giây, cộng ${NGHI_MOI_SLIDE} giây mỗi slide để chuyển và chỉ hình. Phải bấm giờ khi tập để chỉnh.`, "", ...bang, "", ...md].join("\n"));

const OUT = "Nhom09_XLNNTN_BaoCao.pptx";
p.writeFile({ fileName: OUT }).then(() => {
  console.log(`Đã dựng ${n} slide -> ${OUT}`);
});
