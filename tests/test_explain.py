"""Kiểm thử phần giải thích vì sao một điều luật được trả về."""
from vlr import explain

IDF = {"thủ_tục": 2.0, "phá_sản": 5.0, "doanh_nghiệp": 1.0}


def test_chi_ra_tu_khop():
    ket = explain.matched_terms("thủ tục phá sản", "Mở thủ tục phá sản doanh nghiệp", IDF)
    assert "phá_sản" in [t for t, _ in ket]


def test_tu_khong_xuat_hien_trong_dieu_thi_khong_liet_ke():
    ket = explain.matched_terms("phá sản", "Quy định về giấy phép lái xe", IDF)
    assert ket == []


def test_xep_theo_dong_gop_giam_dan():
    ket = explain.matched_terms("thủ tục phá sản", "thủ tục phá sản", IDF)
    assert [t for t, _ in ket][0] == "phá_sản"


def test_tu_hiem_dong_gop_nhieu_hon_tu_pho_bien():
    ket = dict(explain.matched_terms(
        "phá sản doanh nghiệp", "thủ tục phá sản doanh nghiệp", IDF))
    assert ket["phá_sản"] > ket["doanh_nghiệp"]


def test_tu_khong_co_trong_bang_idf_van_khong_no():
    explain.matched_terms("xyzzy", "xyzzy", IDF)


def test_truy_van_rong_tra_ve_rong():
    assert explain.matched_terms("", "bất kỳ", IDF) == []


def test_idf_tu_kho_cho_tu_hiem_diem_cao_hon():
    idf = explain.build_idf([["a", "b"], ["a", "c"], ["a", "d"]])
    assert idf["b"] > idf["a"]
