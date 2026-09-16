"""Trợ lý tra cứu kiểu truy hồi: trả lời bằng cách trích nguyên văn khoản luật.

Không có mô hình sinh chữ, nên trợ lý không bịa được câu nào: mọi câu trả lời là
một đoạn có thật trong kho, kèm số hiệu điều luật để người dùng tự kiểm.
Câu hỏi gõ không dấu được phục hồi dấu trước khi tìm.
"""
import pandas as pd

from vlr import config, dense, diacritics, explain, fusion, lexical, pipeline, textnorm


def trich_khoan(doan: str, tieu_de: str, toi_da: int = 600) -> str:
    """Bỏ tiêu đề điều mà bước chia đoạn đã ghép vào đầu, cắt gọn ở ranh giới từ."""
    tien_to = f"{tieu_de.strip()}. "
    if doan.startswith(tien_to):
        doan = doan[len(tien_to):]
    if len(doan) <= toi_da:
        return doan
    return doan[:toi_da].rsplit(" ", 1)[0] + " ..."


class TroLyTraCuu:
    def __init__(self, bm: lexical.BM25Index | None = None,
                 de: dense.DenseIndex | None = None):
        # Nhận lại chỉ mục đã nạp sẵn: nạp mô hình ngữ nghĩa lần hai mất gần một phút
        self.ts = pipeline.doc_tham_so()
        arts = pd.read_parquet(config.ARTICLES_PATH, columns=["article_id", "title", "text", "tokens"])
        self.tieu_de = dict(zip(arts["article_id"], arts["title"]))
        self.van_ban = dict(zip(arts["article_id"], arts["text"]))
        self.idf = explain.build_idf(list(arts["tokens"]))
        self.bm = bm or lexical.BM25Index(arts, **self.ts["bm25"])
        self.de = de or dense.DenseIndex.load(config.INDEX_DIR / self.ts["dense"]["mo_hinh"])
        ch = pd.read_parquet(config.CHUNKS_PATH, columns=["chunk_id", "text"])
        self.doan = dict(zip(ch["chunk_id"], ch["text"]))
        self.ph = diacritics.PhucHoiDau.load(config.PHUC_HOI_DAU_PATH)

    def tim(self, cau_hoi: str, k: int = 3) -> dict:
        # Phục hồi dấu cho mọi câu, không hỏi câu có dấu hay không. Âm tiết đã
        # có dấu được giữ nguyên, nên câu gõ dấu một nửa cũng được sửa phần
        # thiếu. Giá phải trả đo trên val: 0,9989 âm tiết đúng với câu đủ dấu.
        cau_tim = self.ph.phuc_hoi(cau_hoi)
        K = config.TOPK_FUSION
        bm = self.bm.search_tokens(textnorm.tokens(cau_tim), K)
        qv = self.de.encode_queries([cau_tim])
        de = self.de.search(qv, top_k=K, pooling=self.ts["dense"]["gop_doan"],
                            chunk_top=config.CHUNK_TOP)[0]
        hop = fusion.weighted_sum(bm, de, self.ts["weighted"]["alpha"], K)
        ket_qua = []
        for aid, diem in hop[:k]:
            khop = self.de.doan_khop_nhat(qv[0], aid)
            tu_khop = explain.matched_terms(
                cau_tim, f"{self.tieu_de.get(aid, '')} {self.van_ban.get(aid, '')}", self.idf)
            ket_qua.append({
                "dieu_luat": aid,
                "tieu_de": self.tieu_de.get(aid, ""),
                "diem": round(diem, 4),
                "so_tu_khop": len(tu_khop),
                "khoan": trich_khoan(self.doan.get(khop[0], "") if khop else "",
                                     self.tieu_de.get(aid, "")),
                "tu_khop": explain.to_chuoi(tu_khop, 4),
            })
        return {"cau_hoi": cau_hoi, "da_phuc_hoi_dau": cau_tim != cau_hoi,
                "cau_dung_de_tim": cau_tim, "ket_qua": ket_qua}

    def tra_loi(self, cau_hoi: str) -> str:
        r = self.tim(cau_hoi)
        dong = [f"Bạn hỏi: {r['cau_hoi']}"]
        if r["da_phuc_hoi_dau"]:
            dong.append(f"(Đã phục hồi dấu thành: {r['cau_dung_de_tim']})")
        if not r["ket_qua"]:
            return "\n".join(dong + ["", "Không tìm được điều luật nào."])
        dau, *con_lai = r["ket_qua"]
        if dau["so_tu_khop"] == 0:
            # Không một từ nào của câu hỏi có mặt trong điều luật: gần như chắc
            # chắn câu hỏi nằm ngoài phạm vi kho luật đang có
            dong.append("(Cảnh báo: không từ nào trong câu hỏi khớp điều luật bên dưới, "
                        "nhiều khả năng câu hỏi nằm ngoài phạm vi kho)")
        dong += [
            "",
            f"Điều luật phù hợp nhất: {dau['tieu_de']}  [{dau['dieu_luat']}]",
            f"Nội dung liên quan: “{dau['khoan']}”",
            f"Từ khớp: {dau['tu_khop']}",
            "",
            "Tham khảo thêm:",
        ]
        dong += [f"  - {x['tieu_de']}  [{x['dieu_luat']}]" for x in con_lai]
        dong += ["", "Trợ lý chỉ trích nguyên văn điều luật, không diễn giải. "
                     "Hãy đọc toàn văn điều trước khi viện dẫn."]
        return "\n".join(dong)
