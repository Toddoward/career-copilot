"""
CAREER_COPILOT 전역 설정
환경변수 기반, .env 파일 로드
"""
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # Elasticsearch
    es_url:             str = "http://localhost:9200"
    es_index_works:     str = "cc_works"
    es_schema_version:  int = 1

    # MinIO
    minio_endpoint:     str = "localhost:9000"
    minio_access_key:   str = "minioadmin"
    minio_secret_key:   str = "minioadmin"
    minio_bucket_works: str = "cc-works"
    minio_bucket_out:   str = "cc-outputs"

    # Redis / Celery
    redis_url:          str = "redis://localhost:6379/0"

    # SQLite
    sqlite_path:        str = "./data/career_copilot.db"

    # llama.cpp 서버
    llama_cpp_url:      str = "http://localhost:8080"

    # 모델 경로
    model_group_a:      str = "./models/qwen2.5-7b-instruct-q4_k_m.gguf"
    model_group_c:      str = "./models/qwen2.5-vl-7b-q4_k_m.gguf"
    model_bge_m3:       str = "./models/bge-m3"
    model_reranker:     str = "./models/bge-reranker-v2-m3"

    # VRAM
    gpu_layers:         int  = 35
    flash_attn:         bool = True
    vram_safety_margin: float = 0.5  # GB

    # 생성 설정
    max_retry_judge:    int = 3

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache()
def get_settings() -> Settings:
    return Settings()