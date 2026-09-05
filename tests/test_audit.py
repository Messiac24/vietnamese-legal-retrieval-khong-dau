"""Kiểm thử các phép kiểm toán trùng lặp và chồng lấn."""
import pandas as pd

from vlr import audit


def test_content_hash_bo_qua_khac_biet_khoang_trang_va_hoa_thuong():
    assert audit.content_hash("Điều 1.  Phạm vi") == audit.content_hash("điều 1 phạm vi")


def test_content_hash_khac_nhau_khi_noi_dung_khac():
    assert audit.content_hash("Điều 1") != audit.content_hash("Điều 2")


def test_simhash_gan_nhau_khi_van_ban_gan_giong():
    a = audit.simhash64(["xu_phat", "vi_pham", "giao_thong", "duong_bo", "muc_phat"])
    b = audit.simhash64(["xu_phat", "vi_pham", "giao_thong", "duong_bo", "muc_tien"])
    c = audit.simhash64(["thu_tuc", "pha_san", "doanh_nghiep", "toa_an", "chu_no"])
    assert audit.hamming(a, b) < audit.hamming(a, c)


def test_hamming_voi_chinh_no_bang_khong():
    h = audit.simhash64(["a", "b", "c"])
    assert audit.hamming(h, h) == 0


def test_simhash_danh_sach_rong_tra_ve_khong():
    assert audit.simhash64([]) == 0


def test_jaccard_hai_tap_roi_nhau():
    assert audit.jaccard({"a", "b"}, {"c", "d"}) == 0.0


def test_jaccard_hai_tap_trung_hoan_toan():
    assert audit.jaccard({"a", "b"}, {"a", "b"}) == 1.0


def test_jaccard_hai_tap_rong_khong_chia_cho_khong():
    assert audit.jaccard(set(), set()) == 0.0


def test_split_overlap_bat_dung_query_chong_lan():
    tr = pd.DataFrame({"query_id": ["q1", "q2"], "article_id": ["a1", "a2"], "score": [1, 1]})
    te = pd.DataFrame({"query_id": ["q2", "q3"], "article_id": ["a2", "a3"], "score": [1, 1]})
    ov = audit.split_overlap(tr, te)
    assert list(ov["query_id"]) == ["q2"]


def test_split_overlap_khong_giao_thi_bang_rong():
    tr = pd.DataFrame({"query_id": ["q1"], "article_id": ["a1"], "score": [1]})
    te = pd.DataFrame({"query_id": ["q2"], "article_id": ["a2"], "score": [1]})
    assert len(audit.split_overlap(tr, te)) == 0


def test_exact_duplicate_groups_gom_dung_dieu_trung():
    # Chỉ khác dấu câu và hoa thường thì vẫn là một điều
    df = pd.DataFrame({
        "article_id": ["a1", "a2", "a3"],
        "title": ["Điều 5. Hiệu lực", "Điều 5. Hiệu lực", "Điều 9. Khác"],
        "text": ["Thông tư này có hiệu lực.", "Thông tư này CÓ hiệu lực!", "Nội dung khác hẳn."],
    })
    nhom = audit.exact_duplicate_groups(df)
    assert nhom["a1"] == nhom["a2"]
    assert nhom["a3"] != nhom["a1"]


def test_exact_duplicate_groups_cung_noi_dung_khac_tieu_de_la_hai_dieu():
    # Quyết định của đồ án: băm cả tiêu đề. "Điều 5. Hiệu lực" và
    # "Điều 12. Hiệu lực" cùng nội dung vẫn là hai điều khác nhau, vì số điều
    # là một phần của trích dẫn pháp lý.
    df = pd.DataFrame({
        "article_id": ["a1", "a2"],
        "title": ["Điều 5. Hiệu lực", "Điều 12. Hiệu lực"],
        "text": ["Thông tư này có hiệu lực.", "Thông tư này có hiệu lực."],
    })
    nhom = audit.exact_duplicate_groups(df)
    assert nhom["a1"] != nhom["a2"]


def test_exact_duplicate_groups_dieu_rong_khong_bi_gom_thanh_mot_cum():
    # 357 điều trong corpus thật có text rỗng. Nếu chỉ băm nội dung thì cả 357
    # điều gom thành một nhóm, sai hoàn toàn.
    df = pd.DataFrame({
        "article_id": ["a1", "a2"],
        "title": ["Điều 12. Chương trình đào tạo", "Điều 3. Giải thích từ ngữ"],
        "text": ["", ""],
    })
    nhom = audit.exact_duplicate_groups(df)
    assert nhom["a1"] != nhom["a2"]


def test_exact_duplicate_groups_moi_dieu_deu_co_nhom():
    df = pd.DataFrame({"article_id": ["a1"], "title": ["T"], "text": ["x"]})
    assert set(audit.exact_duplicate_groups(df)) == {"a1"}


def test_near_duplicate_pairs_tim_ra_cap_gan_giong():
    chung = ["dieu", "khoan", "thi", "hanh", "quy", "dinh", "chi", "tiet", "thong", "tu"]
    df = pd.DataFrame({
        "article_id": ["a1", "a2", "a3"],
        "tokens": [chung, chung[:-1] + ["nghi_dinh"],
                   ["pha", "san", "doanh", "nghiep", "toa", "an", "chu", "no", "tai", "san"]],
    })
    cap = audit.near_duplicate_pairs(df, threshold=8)
    cap_id = {tuple(sorted((a, b))) for a, b, _ in cap}
    assert ("a1", "a2") in cap_id
    assert ("a1", "a3") not in cap_id


def test_near_duplicate_pairs_bo_qua_bang_qua_lon():
    # 30 điều giống hệt nhau rơi cùng mọi băng. Với max_bucket=5 thì mọi băng
    # đều bị bỏ qua, không cặp nào được trả về, và bộ đếm phải lớn hơn 0.
    chung = ["dieu", "khoan", "thi", "hanh", "quy", "dinh"]
    df = pd.DataFrame({
        "article_id": [f"a{i}" for i in range(30)],
        "tokens": [chung] * 30,
    })
    cap = audit.near_duplicate_pairs(df, threshold=3, max_bucket=5)
    assert cap == []
    assert audit.near_duplicate_pairs.bo_qua > 0
