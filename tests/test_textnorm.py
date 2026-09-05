"""Kiểm thử chuẩn hóa và tách từ tiếng Việt."""
from vlr import textnorm


def test_normalize_bo_dau_cau_va_ha_chu_thuong():
    assert textnorm.normalize("Điều 7. Xử phạt!") == "điều 7 xử phạt"


def test_normalize_gom_khoang_trang():
    assert textnorm.normalize("a   b\n\nc") == "a b c"


def test_normalize_giu_dau_gach_duoi_cua_tu_ghep():
    # pyvi nối từ ghép bằng gạch dưới, chuẩn hóa không được xóa nó
    assert textnorm.normalize("Công_an xã") == "công_an xã"


def test_segment_ghep_tu_ghep():
    assert "công_an" in textnorm.segment("Công an xã xử phạt").lower()


def test_tokens_bo_stopword():
    toks = textnorm.tokens("Công an xã xử phạt lỗi không mang bằng lái xe")
    assert "không" not in toks
    assert any(t.startswith("xử_phạt") for t in toks)


def test_tokens_giu_con_so():
    assert "25" in textnorm.tokens("Bị thương tật 25% có khởi tố không")


def test_tokens_giu_tu_mang_nghia_phap_ly():
    # 'bị', 'phải', 'cấm' là từ mang nghĩa trong văn bản luật, không phải stopword
    for tu in ("bị", "phải", "cấm"):
        assert tu not in textnorm.STOPWORDS


def test_tokens_chuoi_rong_tra_ve_danh_sach_rong():
    assert textnorm.tokens("   ") == []
