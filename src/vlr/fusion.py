"""Hợp nhất BM25 với tầng ngữ nghĩa: tổng trọng số sau min-max, hoặc RRF."""


def minmax(run: list[tuple[str, float]]) -> dict[str, float]:
    """Mọi điểm bằng nhau thì trả 0 hết."""
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
    """alpha = 0 là BM25 thuần, 1 là ngữ nghĩa thuần. Điều chỉ có ở một hệ được 0 điểm ở hệ kia."""
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
    """Cộng 1 / (k + hạng), bỏ qua điểm số."""
    diem: dict[str, float] = {}
    for run in runs:
        for hang, (d, _) in enumerate(run, start=1):
            diem[d] = diem.get(d, 0.0) + 1.0 / (k + hang)
    xep = sorted(diem.items(), key=lambda x: (-x[1], x[0]))
    return xep[:top_k] if top_k else xep
