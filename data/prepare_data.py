"""Download UCI Online Retail II and convert the two Excel sheets to one Parquet file.

Run once locally, then upload data/online_retail_ii.parquet to the Unity Catalog volume.
    uv run --python 3.11 --with pandas --with openpyxl --with pyarrow data/prepare_data.py
"""
import io
import urllib.request
import zipfile
from pathlib import Path

import pandas as pd

URL = "https://archive.ics.uci.edu/static/public/502/online+retail+ii.zip"
OUT = Path(__file__).parent / "online_retail_ii.parquet"
XLSX = Path(__file__).parent / "raw" / "online_retail_II.xlsx"


def main() -> None:
    if not XLSX.exists():
        XLSX.parent.mkdir(parents=True, exist_ok=True)
        with urllib.request.urlopen(URL) as resp:
            zipfile.ZipFile(io.BytesIO(resp.read())).extractall(XLSX.parent)

    # Both sheets share a schema; read everything as text so bronze stays faithful to the source.
    sheets = pd.read_excel(XLSX, sheet_name=None, dtype=str)
    df = pd.concat(sheets.values(), ignore_index=True)
    df.columns = ["invoice", "stock_code", "description", "quantity", "invoice_date", "price", "customer_id", "country"]
    df.to_parquet(OUT, index=False)
    print(f"Wrote {len(df):,} rows to {OUT}")


if __name__ == "__main__":
    main()
