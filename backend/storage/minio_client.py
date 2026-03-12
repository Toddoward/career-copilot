"""
MinIO 클라이언트 래퍼
원본 파일은 로컬 경로 참조만 저장
MinIO는 rendered/, thumb/, outputs/ 파생 파일만 저장
"""
import io
import os
from pathlib import Path
from minio import Minio
from minio.error import S3Error
from backend.config import get_settings

settings = get_settings()
_client: Minio | None = None


def get_client() -> Minio:
    global _client
    if _client is None:
        _client = Minio(
            settings.minio_endpoint,
            access_key=settings.minio_access_key,
            secret_key=settings.minio_secret_key,
            secure=False,
        )
    return _client


def upload_file(
    bucket: str,
    object_path: str,
    local_path: str | Path,
    content_type: str = "application/octet-stream",
) -> str:
    """
    파일을 임시 경로에 먼저 업로드 후 atomic rename
    원칙 5: 데이터 저장은 원자적으로
    """
    tmp_path = f"tmp/{object_path}"
    final_path = object_path
    client = get_client()

    # 1. 임시 경로에 업로드
    client.fput_object(
        bucket, tmp_path, str(local_path),
        content_type=content_type,
    )

    # 2. 임시 → 정식 경로 복사 후 임시 삭제 (atomic rename)
    client.copy_object(
        bucket, final_path,
        f"{bucket}/{tmp_path}",
    )
    client.remove_object(bucket, tmp_path)

    return f"minio://{bucket}/{final_path}"


def upload_bytes(
    bucket: str,
    object_path: str,
    data: bytes,
    content_type: str = "application/octet-stream",
) -> str:
    """바이트 데이터 업로드 (렌더링 결과 등)"""
    tmp_path = f"tmp/{object_path}"
    client = get_client()

    client.put_object(
        bucket, tmp_path, io.BytesIO(data), len(data),
        content_type=content_type,
    )
    client.copy_object(bucket, object_path, f"{bucket}/{tmp_path}")
    client.remove_object(bucket, tmp_path)

    return f"minio://{bucket}/{object_path}"


def download_bytes(bucket: str, object_path: str) -> bytes:
    response = get_client().get_object(bucket, object_path)
    try:
        return response.read()
    finally:
        response.close()
        response.release_conn()


def object_exists(bucket: str, object_path: str) -> bool:
    try:
        get_client().stat_object(bucket, object_path)
        return True
    except S3Error:
        return False


def delete_object(bucket: str, object_path: str):
    try:
        get_client().remove_object(bucket, object_path)
    except S3Error:
        pass