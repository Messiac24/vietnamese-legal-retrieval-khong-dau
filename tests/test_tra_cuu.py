"""Kiểm thử phần trích khoản luật của trợ lý tra cứu."""
from vlr.tra_cuu import TroLyTraCuu, trich_khoan


def test_trich_khoan_bo_tieu_de_da_ghep():
    assert trich_khoan("Điều 2. Tổ chức. 1. Nội dung", "Điều 2. Tổ chức") == "1. Nội dung"


def test_trich_khoan_giu_nguyen_khi_khong_co_tieu_de():
    assert trich_khoan("1. Nội dung", "Điều 9. Khác") == "1. Nội dung"


def test_trich_khoan_cat_o_ranh_gioi_tu():
    kq = trich_khoan("một hai ba bốn năm", "", toi_da=9)
    assert kq == "một hai ..."


def _tro_ly_gia(ket_qua, da_phuc_hoi=False):
    """Chỉ dựng phần định dạng câu trả lời, không nạp chỉ mục hay mô hình."""
    t = TroLyTraCuu.__new__(TroLyTraCuu)
    t.tim = lambda cau_hoi, k=3: {
        "cau_hoi": cau_hoi, "da_phuc_hoi_dau": da_phuc_hoi,
        "cau_dung_de_tim": "đi xe máy", "ket_qua": ket_qua}
    return t


_KQ = [{"dieu_luat": "100/2019/nđ-cp+6", "tieu_de": "Điều 6", "diem": 0.9,
        "so_tu_khop": 3, "khoan": "1. Phạt tiền", "tu_khop": "xe_máy (2)"}]


def test_tra_loi_bao_khi_khong_co_ket_qua():
    assert "Không tìm được" in _tro_ly_gia([]).tra_loi("di xe may")


def test_tra_loi_canh_bao_khi_khong_tu_nao_khop():
    kq = [{**_KQ[0], "so_tu_khop": 0, "tu_khop": "(không từ nào khớp)"}]
    assert "Cảnh báo" in _tro_ly_gia(kq).tra_loi("hom nay troi dep khong")


def test_tra_loi_khong_canh_bao_khi_co_tu_khop():
    assert "Cảnh báo" not in _tro_ly_gia(_KQ).tra_loi("di xe may")


def test_tra_loi_bao_da_phuc_hoi_dau():
    assert "Đã phục hồi dấu" in _tro_ly_gia(_KQ, da_phuc_hoi=True).tra_loi("di xe may")
