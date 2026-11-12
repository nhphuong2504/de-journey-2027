import argparse

import pandas as pd
from sqlalchemy import create_engine

# Ép kiểu ngay khi đọc để tránh pandas đoán sai (ví dụ ID thành float)
DTYPES = {
    "VendorID": "Int64",
    "passenger_count": "Int64",
    "trip_distance": "float64",
    "RatecodeID": "Int64",
    "store_and_fwd_flag": "string",
    "PULocationID": "Int64",
    "DOLocationID": "Int64",
    "payment_type": "Int64",
    "fare_amount": "float64",
    "extra": "float64",
    "mta_tax": "float64",
    "tip_amount": "float64",
    "tolls_amount": "float64",
    "improvement_surcharge": "float64",
    "total_amount": "float64",
    "congestion_surcharge": "float64",
}

PARSE_DATES = ["tpep_pickup_datetime", "tpep_dropoff_datetime"]
CHUNK_SIZE = 100_000


def parse_args():
    parser = argparse.ArgumentParser(description="Ingest NY Taxi CSV vào Postgres")
    parser.add_argument("--user", required=True)
    parser.add_argument("--password", required=True)
    parser.add_argument("--host", default="localhost")
    parser.add_argument("--port", default="5432")
    parser.add_argument("--db", required=True)
    parser.add_argument("--table", required=True)
    parser.add_argument("--url", required=True, help="link file .csv.gz")
    return parser.parse_args()


def main():
    args = parse_args()
    # Ghi rõ +psycopg2 vì SQLAlchemy 2.1 mặc định gọi psycopg (v3)
    engine = create_engine(
        f"postgresql+psycopg2://{args.user}:{args.password}"
        f"@{args.host}:{args.port}/{args.db}"
    )
    # test kết nối trước khi làm gì khác
    with engine.connect() as conn:
        print("Kết nối OK")

    total = 0
    first_chunk = True

    # Tải + đọc theo chunk, mỗi chunk đẩy thẳng xuống Postgres
    for chunk in pd.read_csv(
        args.url,
        dtype=DTYPES,
        parse_dates=PARSE_DATES,
        chunksize=CHUNK_SIZE,
    ):
        # chunk đầu: replace (tạo mới bảng), các chunk sau: append
        chunk.to_sql(
            name=args.table,
            con=engine,
            if_exists="replace" if first_chunk else "append",
            index=False,
        )
        total += len(chunk)
        first_chunk = False
        print(f"Đã ghi {total:,} dòng")

    print(f"Xong: {total:,} dòng -> bảng {args.table}")


if __name__ == "__main__":
    main()
