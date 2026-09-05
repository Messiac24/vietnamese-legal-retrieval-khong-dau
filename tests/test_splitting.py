"""Kiểm thử chia tập. Điểm quan trọng nhất: chạy lại phải ra kết quả y hệt."""
import random

from vlr import splitting

IDS = [f"q{i}" for i in range(100)]


def test_chia_dung_ty_le():
    tr, va = splitting.split_queries(IDS, val_ratio=0.2, seed=42)
    assert len(va) == 20
    assert len(tr) == 80


def test_hai_tap_khong_giao_nhau_va_phu_het():
    tr, va = splitting.split_queries(IDS, val_ratio=0.2, seed=42)
    assert tr & va == set()
    assert tr | va == set(IDS)


def test_cung_seed_cho_cung_ket_qua():
    assert splitting.split_queries(IDS, 0.2, 42) == splitting.split_queries(IDS, 0.2, 42)


def test_khac_seed_cho_ket_qua_khac():
    assert splitting.split_queries(IDS, 0.2, 42) != splitting.split_queries(IDS, 0.2, 7)


def test_khong_phu_thuoc_thu_tu_dau_vao():
    xao = list(IDS)
    random.Random(1).shuffle(xao)
    assert splitting.split_queries(IDS, 0.2, 42) == splitting.split_queries(xao, 0.2, 42)


def test_khong_dung_den_rng_toan_cuc():
    random.seed(7)
    truoc = random.random()
    splitting.split_queries(IDS, 0.2, 42)
    random.seed(7)
    assert random.random() == truoc


def test_id_lap_chi_tinh_mot_lan():
    tr, va = splitting.split_queries(["a", "a", "b", "b"], 0.5, 42)
    assert len(tr) + len(va) == 2


def test_danh_sach_rong_khong_no():
    tr, va = splitting.split_queries([], 0.2, 42)
    assert tr == set() and va == set()
