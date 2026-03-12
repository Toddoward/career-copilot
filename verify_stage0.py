"""
Stage 0 검증 스크립트
전체 인프라 기동 확인 및 연결 테스트

실행: python verify_stage0.py
"""
import sys
import os
import json
import httpx
from pathlib import Path

ROOT = Path(__file__).parent

CHECKS = []


def check(name: str):
    def decorator(fn):
        CHECKS.append((name, fn))
        return fn
    return decorator


@check("Elasticsearch 연결")
def check_es():
    res = httpx.get("http://localhost:9200/_cluster/health", timeout=5)
    assert res.status_code == 200
    data = res.json()
    assert data["status"] in ("green", "yellow"), f"클러스터 상태: {data['status']}"
    return f"status={data['status']}"


@check("Elasticsearch 인덱스 존재")
def check_es_index():
    res = httpx.get("http://localhost:9200/cc_works", timeout=5)
    assert res.status_code == 200
    mapping = res.json()
    version = mapping["cc_works"]["mappings"].get("_meta", {}).get("schema_version")
    assert version == 1, f"스키마 버전 불일치: {version}"
    return f"schema_version={version}"


@check("MinIO 연결")
def check_minio():
    res = httpx.get("http://localhost:9000/minio/health/live", timeout=5)
    assert res.status_code == 200
    return "healthy"


@check("MinIO 버킷 존재")
def check_minio_buckets():
    from minio import Minio
    client = Minio("localhost:9000", access_key="minioadmin", secret_key="minioadmin", secure=False)
    for bucket in ["cc-works", "cc-outputs"]:
        assert client.bucket_exists(bucket), f"버킷 없음: {bucket}"
    return "cc-works, cc-outputs"


@check("Redis 연결")
def check_redis():
    import redis
    r = redis.Redis(host="localhost", port=6379, db=0)
    assert r.ping()
    return "PONG"


@check("SQLite 스키마")
def check_sqlite():
    import sqlite3
    db_path = "./data/career_copilot.db"
    assert Path(db_path).exists(), f"DB 파일 없음: {db_path}"
    conn = sqlite3.connect(db_path)
    tables = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table'"
    ).fetchall()
    table_names = [t[0] for t in tables]
    required = [
        "schema_meta", "user_profile", "education", "career_entry",
        "military_service", "project", "work_asset", "design_cue",
        "coverletter_template", "generation",
        "application_history", "user_preferences", "chat_message",
    ]
    for t in required:
        assert t in table_names, f"테이블 없음: {t}"
    # 인덱스 확인
    indexes = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='index'"
    ).fetchall()
    idx_names = [i[0] for i in indexes]
    required_idx = [
        "idx_work_asset_hash", "idx_work_asset_status",
        "idx_history_gen", "idx_chat_message_gen", "idx_preferences_profile",
    ]
    for i in required_idx:
        assert i in idx_names, f"인덱스 없음: {i}"
    conn.close()
    return f"{len(table_names)}개 테이블, {len(idx_names)}개 인덱스"


@check("llama.cpp 서버")
def check_llamacpp():
    res = httpx.get("http://localhost:8080/health", timeout=10)
    assert res.status_code == 200
    return "healthy"


def run():
    print("=" * 50)
    print("CAREER_COPILOT Stage 0 검증")
    print("=" * 50)

    passed = 0
    failed = 0

    for name, fn in CHECKS:
        try:
            result = fn()
            print(f"  ✅ {name}: {result}")
            passed += 1
        except Exception as e:
            print(f"  ❌ {name}: {e}")
            failed += 1

    print("=" * 50)
    print(f"결과: {passed}개 통과 / {failed}개 실패")

    if failed > 0:
        sys.exit(1)
    else:
        print("Stage 0 검증 완료. Stage 1 진행 가능.")


if __name__ == "__main__":
    run()