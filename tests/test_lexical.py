"""Kiểm thử chỉ mục BM25."""
import pandas as pd

from vlr import lexical

DF = pd.DataFrame({
    "article_id": ["a1", "a2", "a3"],
    "title": ["Điều 1. Thủ tục phá sản",
              "Điều 2. Xử phạt vi phạm giao thông",
              "Điều 3. Giấy phép lái xe"],
    "text": ["Doanh nghiệp mất khả năng thanh toán thì mở thủ tục phá sản.",
             "Người điều khiển xe mô tô vi phạm bị xử phạt tiền.",
             "Giấy phép lái xe phải mang theo khi điều khiển phương tiện."],
})


def _index(**kw):
    return lexical.BM25Index(DF, k1=1.2, b=0.75, **kw)


def test_tra_ve_dung_so_luong():
    assert len(_index().search("thủ tục phá sản", top_k=2)) == 2


def test_xep_dung_dieu_lien_quan_len_dau():
    assert _index().search("thủ tục phá sản doanh nghiệp", top_k=1)[0][0] == "a1"


def test_tim_duoc_qua_tu_ghep():
    # "giấy phép lái xe" phải khớp a3 chứ không phải a2
    assert _index().search("giấy phép lái xe", top_k=1)[0][0] == "a3"


def test_diem_giam_dan():
    diem = [s for _, s in _index().search("xe", top_k=3)]
    assert diem == sorted(diem, reverse=True)


def test_top_k_lon_hon_kho_khong_no():
    assert len(_index().search("xe", top_k=100)) <= len(DF)


def test_truy_van_khong_khop_gi_khong_no():
    _index().search("zzzz qqqq wwww", top_k=3)


def test_truy_van_rong_khong_no():
    _index().search("", top_k=3)


def test_luu_va_nap_lai_cho_cung_ket_qua(tmp_path):
    idx = _index()
    truoc = idx.search("bằng lái xe", top_k=3)
    idx.save(tmp_path / "bm25")
    sau = lexical.BM25Index.load(tmp_path / "bm25").search("bằng lái xe", top_k=3)
    assert truoc == sau


def test_doi_tham_so_thi_doi_diem():
    a = _index().search("xử phạt", top_k=1)[0][1]
    b = lexical.BM25Index(DF, k1=1.8, b=0.3).search("xử phạt", top_k=1)[0][1]
    assert a != b


def test_dung_lai_token_da_tach_neu_duoc_cung_cap():
    # Tách từ 61k điều mất vài phút, nên chỉ mục phải nhận token có sẵn
    df = DF.assign(tokens=[["thu_tuc", "pha_san"], ["xu_phat"], ["lai_xe"]])
    idx = lexical.BM25Index(df, k1=1.2, b=0.75)
    assert idx.search("thu_tuc pha_san", top_k=1)[0][0] == "a1"
