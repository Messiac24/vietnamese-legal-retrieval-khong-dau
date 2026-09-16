"""Kiểm thử bỏ dấu, nhận diện câu không dấu và phục hồi dấu."""
import pytest

from vlr import diacritics as dc

KHO = [
    "Người lao động được nghỉ việc hưởng nguyên lương",
    "Người sử dụng lao động phải trả lương cho người lao động",
    "Mức phạt tiền đối với hành vi vi phạm",
    "Mức phạt đối với người điều khiển xe mô tô",
]


def test_bo_dau_ca_dau_thanh_dau_mu_va_chu_d():
    assert dc.bo_dau("Người điều khiển xe") == "Nguoi dieu khien xe"
    assert dc.bo_dau("ĐỘNG") == "DONG"


def test_bo_dau_giu_so_va_dau_cau():
    assert dc.bo_dau("Điều 7, khoản 2.") == "Dieu 7, khoan 2."


def test_co_dau():
    assert dc.co_dau("phạt bao nhiêu")
    assert not dc.co_dau("phat bao nhieu")
    assert dc.co_dau("đi")          # chỉ có chữ đ cũng tính là có dấu
    assert not dc.co_dau("100/2019")


def test_am_tiet_bo_dau_cau_ha_chu_thuong():
    assert dc.am_tiet("Mức phạt, bao nhiêu?") == ["mức", "phạt", "bao", "nhiêu"]


def test_phuc_hoi_dung_theo_ngu_canh_bigram():
    m = dc.PhucHoiDau(KHO)
    assert m.phuc_hoi("nguoi lao dong") == "người lao động"
    assert m.phuc_hoi("muc phat tien") == "mức phạt tiền"


def test_phuc_hoi_giu_dau_cau_va_chu_hoa():
    m = dc.PhucHoiDau(KHO)
    assert m.phuc_hoi("Muc phat, bao nhieu?") == "Mức phạt, bao nhieu?"


def test_phuc_hoi_giu_nguyen_am_tiet_da_co_dau():
    m = dc.PhucHoiDau(KHO)
    # người dùng gõ dấu một nửa: phần đã có dấu không bị đổi
    assert m.phuc_hoi("người lao dong") == "người lao động"


def test_phuc_hoi_am_tiet_la_giu_nguyen():
    m = dc.PhucHoiDau(KHO)
    assert m.phuc_hoi("xyz") == "xyz"
    assert m.phuc_hoi("") == ""


def test_do_chinh_xac():
    assert dc.do_chinh_xac("mức phạt tiền", "mức phát tiền") == (2, 3)


def test_luu_va_nap(tmp_path):
    m = dc.PhucHoiDau(KHO)
    m.save(tmp_path / "m.pkl")
    m2 = dc.PhucHoiDau.load(tmp_path / "m.pkl")
    assert m2.phuc_hoi("muc phat") == m.phuc_hoi("muc phat")


def test_phuc_hoi_am_tiet_viet_hoa_toan_bo():
    # lỗi cũ: nhánh viết hoa trả lại chính chuỗi người dùng gõ, bỏ mất bản phục hồi
    m = dc.PhucHoiDau(KHO)
    assert m.phuc_hoi("MUC PHAT TIEN") == "MỨC PHẠT TIỀN"
    assert m.phuc_hoi("Muc PHAT tien") == "Mức PHẠT tiền"


def test_phuc_hoi_cau_go_dau_mot_nua():
    m = dc.PhucHoiDau(KHO)
    assert m.phuc_hoi("Người lao dong duoc nghi viec") == "Người lao động được nghỉ việc"


def test_lam_bang_mot_khong_vo_khi_gap_bigram_la():
    m = dc.PhucHoiDau(KHO, lam=1.0)
    assert m.phuc_hoi("muc phat") == "mức phạt"


def test_do_chinh_xac_bao_loi_khi_lech_so_am_tiet():
    with pytest.raises(ValueError):
        dc.do_chinh_xac("mức phạt tiền", "mức phạt")
