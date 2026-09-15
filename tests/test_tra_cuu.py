"""Kiểm thử phần trích khoản luật của trợ lý tra cứu."""
from vlr.tra_cuu import trich_khoan


def test_trich_khoan_bo_tieu_de_da_ghep():
    assert trich_khoan("Điều 2. Tổ chức. 1. Nội dung", "Điều 2. Tổ chức") == "1. Nội dung"


def test_trich_khoan_giu_nguyen_khi_khong_co_tieu_de():
    assert trich_khoan("1. Nội dung", "Điều 9. Khác") == "1. Nội dung"


def test_trich_khoan_cat_o_ranh_gioi_tu():
    kq = trich_khoan("một hai ba bốn năm", "", toi_da=9)
    assert kq == "một hai ..."
