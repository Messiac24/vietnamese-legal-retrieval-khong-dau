"""Kiểm thử nạp dữ liệu và tách id điều luật."""
import pytest
from vlr import corpus


def test_parse_article_id_tach_dung():
    assert corpus.parse_article_id("01/2009/tt-bnn+1") == ("01/2009/tt-bnn", 1)


def test_parse_article_id_so_hieu_co_dau_gach_va_chu_tieng_viet():
    assert corpus.parse_article_id("100/2019/nđ-cp+5") == ("100/2019/nđ-cp", 5)


def test_parse_article_id_tach_o_dau_cong_cuoi_cung():
    assert corpus.parse_article_id("a+b+7") == ("a+b", 7)


def test_parse_article_id_thieu_dau_cong_thi_bao_loi():
    with pytest.raises(ValueError):
        corpus.parse_article_id("khong-co-dau-cong")


def test_parse_article_id_phan_sau_khong_phai_so_thi_bao_loi():
    with pytest.raises(ValueError):
        corpus.parse_article_id("01/2009/tt-bnn+abc")


def test_bao_loi_tieng_viet_khi_chua_tai_du_lieu(tmp_path, monkeypatch):
    monkeypatch.setattr(corpus.config, "RAW_DIR", tmp_path / "khong-ton-tai")
    with pytest.raises(FileNotFoundError) as e:
        corpus.load_articles()
    assert "01_prepare_data.py" in str(e.value)
