"""Kiểm thử các chỉ số truy hồi."""
import math

from vlr import metrics

R = ["a", "b", "c", "d", "e"]


def test_recall_tim_thay_het_gold():
    assert metrics.recall_at_k(R, {"a", "c"}, 5) == 1.0


def test_recall_chi_tim_thay_mot_nua():
    assert metrics.recall_at_k(R, {"a", "z"}, 5) == 0.5


def test_recall_khong_tim_thay_gi():
    assert metrics.recall_at_k(R, {"z"}, 5) == 0.0


def test_recall_cat_dung_o_k():
    assert metrics.recall_at_k(R, {"e"}, 3) == 0.0
    assert metrics.recall_at_k(R, {"e"}, 5) == 1.0


def test_mrr_gold_o_vi_tri_ba():
    assert metrics.mrr_at_k(R, {"c"}, 10) == 1 / 3


def test_mrr_lay_gold_dau_tien_gap_duoc():
    assert metrics.mrr_at_k(R, {"c", "b"}, 10) == 1 / 2


def test_mrr_gold_ngoai_top_k_bang_khong():
    assert metrics.mrr_at_k(R, {"e"}, 3) == 0.0


def test_ndcg_gold_dau_bang_mot():
    assert metrics.ndcg_at_k(R, {"a"}, 5) == 1.0


def test_ndcg_giam_khi_gold_xuong_thap():
    assert metrics.ndcg_at_k(R, {"a"}, 5) > metrics.ndcg_at_k(R, {"c"}, 5)


def test_ndcg_hai_gold_dau_bang_mot():
    assert math.isclose(metrics.ndcg_at_k(R, {"a", "b"}, 5), 1.0, rel_tol=1e-9)


def test_f2_uu_tien_recall_hon_precision():
    # 1 gold, k=5: P = 1/5 = 0,2 và R = 1,0 -> F2 = 5PR / (4P + R)
    mong_doi = 5 * 0.2 * 1.0 / (4 * 0.2 + 1.0)
    assert math.isclose(metrics.f2_at_k(R, {"a"}, 5), mong_doi, rel_tol=1e-9)


def test_f2_bang_khong_khi_khong_trung_gi():
    assert metrics.f2_at_k(R, {"z"}, 5) == 0.0


def test_moi_chi_so_bang_khong_khi_gold_rong():
    assert metrics.recall_at_k(R, set(), 5) == 0.0
    assert metrics.mrr_at_k(R, set(), 5) == 0.0
    assert metrics.ndcg_at_k(R, set(), 5) == 0.0
    assert metrics.f2_at_k(R, set(), 5) == 0.0


def test_moi_chi_so_bang_khong_khi_ket_qua_rong():
    assert metrics.recall_at_k([], {"a"}, 5) == 0.0
    assert metrics.mrr_at_k([], {"a"}, 5) == 0.0


def test_evaluate_gop_trung_binh_tren_moi_cau_hoi():
    runs = {"q1": ["a", "b"], "q2": ["z", "a"]}
    gold = {"q1": {"a"}, "q2": {"a"}}
    bang = metrics.evaluate(runs, gold, ks=(1, 2))
    d = dict(zip(bang["chi_so"], bang["gia_tri"]))
    assert d["recall@1"] == 0.5      # q1 trúng ở hạng 1, q2 không
    assert d["recall@2"] == 1.0
    assert math.isclose(d["mrr@2"], (1.0 + 0.5) / 2, rel_tol=1e-9)


def test_evaluate_bao_loi_khi_thieu_gold():
    try:
        metrics.evaluate({"q1": ["a"]}, {}, ks=(1,))
    except ValueError:
        return
    raise AssertionError("phải ném ValueError khi câu hỏi không có gold")
