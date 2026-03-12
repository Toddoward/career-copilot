"""
Elasticsearch 인덱스 초기화 및 스키마 버전 검증
Stage 0 실행 시 1회 실행, 이후 앱 시작마다 버전 체크
"""
import json
import os
import sys
from pathlib import Path
from elasticsearch import Elasticsearch

ES_URL          = os.getenv("ES_URL", "http://localhost:9200")
ES_INDEX        = os.getenv("ES_INDEX_WORKS", "cc_works")
SCHEMA_VERSION  = int(os.getenv("ES_SCHEMA_VERSION", "1"))
MAPPING_PATH    = Path(__file__).parent.parent / "elasticsearch" / "mappings" / "works_index.json"


def get_client() -> Elasticsearch:
    return Elasticsearch(ES_URL)


def check_schema_version(es: Elasticsearch) -> bool:
    """현재 인덱스 스키마 버전과 코드 버전 일치 확인"""
    if not es.indices.exists(index=ES_INDEX):
        return True  # 인덱스 없음 = 신규 생성 필요

    mapping = es.indices.get_mapping(index=ES_INDEX)
    current = mapping[ES_INDEX]["mappings"].get("_meta", {}).get("schema_version")

    if current != SCHEMA_VERSION:
        print(f"[ERROR] 스키마 버전 불일치: 현재={current}, 필요={SCHEMA_VERSION}")
        print("       infra/elasticsearch/migrate.py 실행 후 앱을 재시작하세요.")
        return False

    print(f"[OK] 스키마 버전 확인: v{SCHEMA_VERSION}")
    return True


def init_index(es: Elasticsearch):
    """인덱스 없으면 생성"""
    if es.indices.exists(index=ES_INDEX):
        print(f"[SKIP] 인덱스 이미 존재: {ES_INDEX}")
        return

    with open(MAPPING_PATH) as f:
        mapping = json.load(f)

    es.indices.create(index=ES_INDEX, body=mapping)
    print(f"[OK] 인덱스 생성: {ES_INDEX}")


def verify(es: Elasticsearch) -> bool:
    """스키마 버전 검증 (앱 시작마다 호출)"""
    return check_schema_version(es)


if __name__ == "__main__":
    es = get_client()

    # 연결 확인
    if not es.ping():
        print("[ERROR] Elasticsearch 연결 실패")
        sys.exit(1)

    print(f"[OK] Elasticsearch 연결 성공: {ES_URL}")

    # 인덱스 초기화
    init_index(es)

    # 버전 체크
    if not verify(es):
        sys.exit(1)

    print("\nElasticsearch 초기화 완료")