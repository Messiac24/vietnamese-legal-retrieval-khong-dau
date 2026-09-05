"""Kiểm thử hai cách hợp nhất kết quả."""
from vlr import fusion

BM = [("a", 10.0), ("b", 8.0), ("c", 2.0)]
DE = [("c", 0.9), ("a", 0.7), ("d", 0.6)]


def test_minmax_dua_ve_khoang_0_1():
    m = fusion.minmax(BM)
    assert m["a"] == 1.0
    assert m["c"] == 0.0


def test_minmax_khong_chia_cho_khong_khi_moi_diem_bang_nhau():
    m = fusion.minmax([("a", 5.0), ("b", 5.0)])
    assert m["a"] == m["b"] == 0.0


def test_minmax_danh_sach_rong():
    assert fusion.minmax([]) == {}


def test_alpha_bang_khong_thi_giong_het_bm25():
    r = fusion.weighted_sum(BM, DE, alpha=0.0)
    assert [x for x, _ in r][:2] == ["a", "b"]


def test_alpha_bang_mot_thi_giong_het_dense():
    r = fusion.weighted_sum(BM, DE, alpha=1.0)
    assert r[0][0] == "c"


def test_weighted_sum_gop_ca_tai_lieu_chi_co_o_mot_he():
    ids = {x for x, _ in fusion.weighted_sum(BM, DE, alpha=0.5)}
    assert ids == {"a", "b", "c", "d"}


def test_rrf_gop_duoc_tai_lieu_chi_co_o_mot_he():
    assert "d" in [x for x, _ in fusion.rrf([BM, DE], k=60)]


def test_rrf_uu_tien_tai_lieu_dung_cao_o_ca_hai_he():
    # a đứng hạng 1 ở BM25 và hạng 2 ở dense, tổng nghịch đảo lớn nhất
    assert fusion.rrf([BM, DE], k=60)[0][0] == "a"


def test_rrf_chi_dung_thu_hang_khong_dung_diem():
    # nhân đôi mọi điểm BM25 không được làm đổi kết quả RRF
    bm_gap_doi = [(x, s * 2) for x, s in BM]
    assert fusion.rrf([BM, DE], 60) == fusion.rrf([bm_gap_doi, DE], 60)


def test_ket_qua_luon_xep_giam_dan():
    for r in (fusion.rrf([BM, DE], 60), fusion.weighted_sum(BM, DE, 0.5)):
        diem = [s for _, s in r]
        assert diem == sorted(diem, reverse=True)


def test_top_k_cat_dung_so_luong():
    assert len(fusion.weighted_sum(BM, DE, 0.5, top_k=2)) == 2
    assert len(fusion.rrf([BM, DE], 60, top_k=2)) == 2


def test_hai_he_rong_tra_ve_rong():
    assert fusion.rrf([[], []], 60) == []
    assert fusion.weighted_sum([], [], 0.5) == []
