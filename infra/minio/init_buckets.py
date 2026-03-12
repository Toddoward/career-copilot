"""
MinIO 버킷 및 기본 디렉토리 구조 초기화
Stage 0 실행 시 1회 실행
"""
import os
from minio import Minio
from minio.error import S3Error

MINIO_ENDPOINT  = os.getenv("MINIO_ENDPOINT", "localhost:9000")
MINIO_ACCESS    = os.getenv("MINIO_ACCESS_KEY", "minioadmin")
MINIO_SECRET    = os.getenv("MINIO_SECRET_KEY", "minioadmin")

BUCKETS = ["cc-works", "cc-outputs"]

def init_buckets():
    client = Minio(
        MINIO_ENDPOINT,
        access_key=MINIO_ACCESS,
        secret_key=MINIO_SECRET,
        secure=False,
    )

    for bucket in BUCKETS:
        if not client.bucket_exists(bucket):
            client.make_bucket(bucket)
            print(f"[OK] 버킷 생성: {bucket}")
        else:
            print(f"[SKIP] 이미 존재: {bucket}")

    # 더미 오브젝트로 디렉토리 구조 초기화
    import io
    placeholder = io.BytesIO(b"")
    dirs = [
        ("cc-works",   "tmp/.keep"),
        ("cc-outputs", "tmp/.keep"),
    ]
    for bucket, path in dirs:
        try:
            client.put_object(bucket, path, io.BytesIO(b""), 0)
            print(f"[OK] 디렉토리 초기화: {bucket}/{path}")
        except S3Error as e:
            print(f"[WARN] {e}")

    print("\nMinIO 초기화 완료")

if __name__ == "__main__":
    init_buckets()