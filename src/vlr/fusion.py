"""Hợp nhất kết quả của tầng từ khóa và tầng ngữ nghĩa.

Hai tầng cho ra hai thang điểm hoàn toàn khác nhau: BM25 là số dương không chặn
trên, còn cosine của bi-encoder nằm trong khoảng [-1, 1]. Cộng thẳng là vô
nghĩa. Có hai lối thoát, đồ án đo cả hai rồi chọn theo tập val.
"""


def minmax(run: list[tuple[str, float]]) -> dict[str, float]:
    """Đưa điểm của một hệ về khoảng [0, 1] trong phạm vi danh sách trả về.

    Khi mọi điểm bằng nhau thì trả 0 cho tất cả, không chia cho không.
    """
    if not run:
        return {}
    diem = [s for _, s in run]
    lo, hi = min(diem), max(diem)
    if hi == lo:
        return {d: 0.0 for d, _ in run}
    return {d: (s - lo) / (hi - lo) for d, s in run}


def weighted_sum(
    bm25_run: list[tuple[str, float]],
    dense_run: list[tuple[str, float]],
    alpha: float,
    top_k: int | None = None,
) -> list[tuple[str, float]]:
    """Chuẩn hóa min-max rồi cộng có trọng số.

    `alpha = 0` là BM25 thuần, `alpha = 1` là ngữ nghĩa thuần. Tài liệu chỉ xuất
    hiện ở một hệ được coi là 0 điểm ở hệ kia, chứ không bị loại: một điều luật
    mà chỉ BM25 tìm ra vẫn có thể là đáp án đúng.

    Nhược điểm phải biết: min-max phụ thuộc vào chính danh sách top-k trả về,
    nên điểm không so được giữa hai truy vấn khác nhau. Với việc xếp hạng trong
    cùng một truy vấn thì không sao.
    """
    a = minmax(bm25_run)
    b = minmax(dense_run)
    ket = {
        d: (1 - alpha) * a.get(d, 0.0) + alpha * b.get(d, 0.0)
        for d in set(a) | set(b)
    }
    xep = sorted(ket.items(), key=lambda x: (-x[1], x[0]))
    return xep[:top_k] if top_k else xep


def rrf(
    runs: list[list[tuple[str, float]]],
    k: int,
    top_k: int | None = None,
) -> list[tuple[str, float]]:
    """Reciprocal Rank Fusion: cộng 1 / (k + thứ hạng).

    Chỉ dùng THỨ HẠNG, bỏ qua điểm số, nên miễn nhiễm với việc hai hệ có thang
    điểm khác nhau và không cần chuẩn hóa. Đổi lại, nó vứt đi thông tin về
    khoảng cách điểm: hạng 1 hơn hạng 2 rất xa hay sát nút đều như nhau.

    Hằng số `k` làm phẳng đóng góp của các hạng đầu. `k` lớn thì các hạng đầu
    gần bằng nhau, `k` nhỏ thì hạng 1 áp đảo.
    """
    diem: dict[str, float] = {}
    for run in runs:
        for hang, (d, _) in enumerate(run, start=1):
            diem[d] = diem.get(d, 0.0) + 1.0 / (k + hang)
    xep = sorted(diem.items(), key=lambda x: (-x[1], x[0]))
    return xep[:top_k] if top_k else xep
