"""Kiểm thử cắt điều luật thành đoạn.

46,2% điều luật dài hơn 200 từ, trong khi PhoBERT chỉ nhận 256 token (khoảng 130
tới 150 từ tiếng Việt). Cắt cụt là mất phần đuôi của gần một nửa số điều, mà đuôi
điều luật thường là chỗ ghi mức phạt và ngoại lệ.
"""
import pandas as pd

from vlr import chunking


def test_dieu_ngan_thi_mot_doan():
    doan = chunking.split_article("Điều 1. Phạm vi", "Thông tư này hướng dẫn.", 180, 40)
    assert len(doan) == 1
    assert doan[0].startswith("Điều 1. Phạm vi")


def test_dieu_dai_bi_cat_nhieu_doan():
    text = " ".join(["tu"] * 500)
    assert len(chunking.split_article("Điều 9. Xử phạt", text, 180, 40)) >= 3


def test_moi_doan_deu_co_tieu_de():
    text = " ".join(["tu"] * 500)
    for d in chunking.split_article("Điều 9. Xử phạt", text, 180, 40):
        assert d.startswith("Điều 9. Xử phạt")


def test_cac_doan_chong_lan_nhau():
    text = " ".join(str(i) for i in range(400))
    doan = chunking.split_article("T", text, 180, 40)
    duoi_doan_dau = set(doan[0].split()[-30:])
    assert duoi_doan_dau & set(doan[1].split())


def test_cat_theo_ranh_gioi_khoan():
    text = ("1. Khoản một. " + " ".join(["a"] * 150)
            + "\n2. Khoản hai. " + " ".join(["b"] * 150))
    doan = chunking.split_article("T", text, 180, 40)
    assert len(doan) >= 2
    # khoản một không bị vỡ đôi giữa chừng khi nó vừa một cửa sổ
    assert doan[0].count("Khoản một") == 1


def test_khong_sinh_doan_rong():
    assert all(d.strip() for d in chunking.split_article("T", "   ", 180, 40))


def test_dieu_rong_van_giu_lai_tieu_de():
    doan = chunking.split_article("Điều 12. Chương trình đào tạo", "", 180, 40)
    assert len(doan) == 1
    assert "Chương trình đào tạo" in doan[0]


def test_chan_tren_so_doan():
    text = " ".join(["tu"] * 20000)
    doan = chunking.split_article("T", text, 180, 40, max_chunks=10)
    assert len(doan) == 10


def test_build_chunks_sinh_id_va_giu_lien_ket_ve_dieu():
    df = pd.DataFrame({
        "article_id": ["a1", "a2"],
        "title": ["Điều 1. Ngắn", "Điều 2. Dài"],
        "text": ["Một câu ngắn.", " ".join(["tu"] * 500)],
    })
    ch = chunking.build_chunks(df, 180, 40)
    assert set(ch.columns) >= {"chunk_id", "article_id", "text"}
    assert (ch[ch.article_id == "a1"]["chunk_id"] == "a1#0").all()
    assert len(ch[ch.article_id == "a2"]) >= 3
    assert ch["chunk_id"].is_unique


def test_build_chunks_moi_dieu_deu_co_it_nhat_mot_doan():
    df = pd.DataFrame({
        "article_id": ["a1", "a2"],
        "title": ["T1", "T2"],
        "text": ["", "   "],
    })
    ch = chunking.build_chunks(df, 180, 40)
    assert set(ch["article_id"]) == {"a1", "a2"}
