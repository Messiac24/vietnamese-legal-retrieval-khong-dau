"""Kiểm thử tầng ngữ nghĩa.

Các test ở đây cố ý KHÔNG nạp mô hình thật: nạp PhoBERT mất vài giây và cần
mạng, làm bộ test chậm và giòn. Phần cần kiểm là logic gộp đoạn về điều và phép
chuẩn hóa vector, chứ không phải chất lượng của mô hình.
"""
import numpy as np
import pytest

from vlr import dense

ART = {"a1#0": "a1", "a1#1": "a1", "a2#0": "a2"}


def test_gop_max_lay_diem_cao_nhat():
    r = dense.pool_chunk_scores(["a1#0", "a1#1", "a2#0"], [0.2, 0.9, 0.5], ART, "max")
    assert r == {"a1": 0.9, "a2": 0.5}


def test_gop_mean_lay_trung_binh():
    r = dense.pool_chunk_scores(["a1#0", "a1#1", "a2#0"], [0.2, 0.8, 0.5], ART, "mean")
    assert abs(r["a1"] - 0.5) < 1e-9
    assert abs(r["a2"] - 0.5) < 1e-9


def test_gop_bao_loi_khi_how_khong_hop_le():
    with pytest.raises(ValueError):
        dense.pool_chunk_scores(["a1#0"], [0.1], ART, "linh tinh")


def test_gop_bao_loi_khi_chunk_khong_thuoc_dieu_nao():
    with pytest.raises(KeyError):
        dense.pool_chunk_scores(["la#0"], [0.1], ART, "max")


def test_gop_danh_sach_rong():
    assert dense.pool_chunk_scores([], [], ART, "max") == {}


def test_chuan_hoa_vector_ve_do_dai_mot():
    v = dense.l2_normalize(np.array([[3.0, 4.0]], dtype=np.float32))
    assert abs(float(np.linalg.norm(v)) - 1.0) < 1e-6


def test_chuan_hoa_vector_khong_khong_chia_cho_khong():
    v = dense.l2_normalize(np.zeros((1, 4), dtype=np.float32))
    assert np.all(np.isfinite(v))


def test_article_of_suy_ra_dieu_tu_chunk_id():
    assert dense.article_of("100/2019/nđ-cp+5#3") == "100/2019/nđ-cp+5"


def test_article_of_bao_loi_khi_thieu_dau_thang():
    with pytest.raises(ValueError):
        dense.article_of("khong-co-dau-thang")


def test_top_k_theo_dieu_xep_giam_dan():
    diem = {"a1": 0.3, "a2": 0.9, "a3": 0.5}
    assert dense.top_articles(diem, 2) == [("a2", 0.9), ("a3", 0.5)]


def test_top_k_lon_hon_so_dieu_khong_no():
    assert len(dense.top_articles({"a1": 0.1}, 10)) == 1


def _chi_muc_gia():
    vec = np.array([[1, 0], [0, 1], [0.6, 0.8]], dtype=np.float16)
    return dense.DenseIndex("gia", 16, False, ["a1#0", "a1#1", "a2#0"], vec)


def test_doan_khop_nhat_chon_doan_diem_cao_nhat_trong_dieu():
    idx = _chi_muc_gia()
    cid, s = idx.doan_khop_nhat(np.array([0.0, 1.0]), "a1")
    assert cid == "a1#1" and s == pytest.approx(1.0)


def test_doan_khop_nhat_chi_xet_doan_cua_dung_dieu():
    # a2#0 khớp hơn a1#0 nhưng không thuộc a1, nên không được chọn
    idx = _chi_muc_gia()
    assert idx.doan_khop_nhat(np.array([1.0, 0.0]), "a1")[0] == "a1#0"


def test_doan_khop_nhat_dieu_khong_co_doan():
    assert _chi_muc_gia().doan_khop_nhat(np.array([1.0, 0.0]), "khong_co") is None
