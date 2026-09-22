"""Gom mã và dữ liệu đã dựng thành một thư mục để tải lên Kaggle Datasets.

    python kaggle/dong_goi.py        -> kaggle/vlr-demo/ và kaggle/vlr-demo.zip

Cần chạy xong bảy bước ở README trước. Mô hình AITeamVN không gói vào, notebook tự
tải từ HuggingFace nên phải bật Internet.
"""
import json
import shutil
from pathlib import Path

import pyarrow.parquet as pq

GOC = Path(__file__).resolve().parents[1]
DICH = GOC / "kaggle" / "vlr-demo"
TEP = [
    "data/articles.parquet",
    "data/queries.parquet",
    "data/qrels.parquet",
    "data/chunks.parquet",
    "data/index/aiteam/embeddings.npy",
    "data/index/aiteam/meta.json",
    "data/index/phuc_hoi_dau.pkl",
]

if DICH.exists():
    shutil.rmtree(DICH)
for t in TEP:
    nguon = GOC / t
    if not nguon.exists():
        raise SystemExit(f"Thiếu {t}. Chạy các bước trong README trước.")
    (DICH / t).parent.mkdir(parents=True, exist_ok=True)
    if t.endswith(".parquet"):
        # bỏ siêu dữ liệu của pandas 3 (kiểu "str"), Kaggle còn dùng pandas 2
        pq.write_table(pq.read_table(nguon).replace_schema_metadata(None), DICH / t)
    else:
        shutil.copy2(nguon, DICH / t)
shutil.copytree(GOC / "src" / "vlr", DICH / "src" / "vlr", ignore=shutil.ignore_patterns("__pycache__"))
shutil.copytree(GOC / "reports", DICH / "reports")
(DICH / "dataset-metadata.json").write_text(json.dumps(
    {"title": "vlr-demo", "id": "USERNAME/vlr-demo", "licenses": [{"name": "MIT"}]}, indent=2), encoding="utf-8")

zip_tep = shutil.make_archive(str(DICH), "zip", DICH)
mb = sum(f.stat().st_size for f in DICH.rglob("*") if f.is_file()) / 1e6
print(f"{DICH}  ({mb:.0f} MB)")
print(f"{zip_tep}  ({Path(zip_tep).stat().st_size / 1e6:.0f} MB)")
