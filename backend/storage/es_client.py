"""
Elasticsearch 클라이언트 래퍼
ES 8.x Python client: body= 파라미터 deprecated → document=/query= 사용
"""
from elasticsearch import Elasticsearch, NotFoundError
from backend.config import get_settings

settings = get_settings()
_client: Elasticsearch | None = None


def get_client() -> Elasticsearch:
    global _client
    if _client is None:
        _client = Elasticsearch(settings.es_url)
    return _client


def verify_schema() -> bool:
    """
    ES 스키마 버전 검증 (앱 시작 시 호출 — ES-5 대응)
    인덱스가 없으면 True 반환 (신규 생성 필요 상태, 앱 시작은 허용)
    버전 불일치 시 False 반환 → 앱 시작 차단
    """
    es = get_client()
    if not es.indices.exists(index=settings.es_index_works):
        print(f"[warn] 인덱스 없음: {settings.es_index_works} — init_index.py를 실행하세요.")
        return True  # 인덱스 미생성은 차단 사유 아님

    mapping = es.indices.get_mapping(index=settings.es_index_works)
    current = (
        mapping[settings.es_index_works]["mappings"]
        .get("_meta", {})
        .get("schema_version")
    )
    if current != settings.es_schema_version:
        print(
            f"[error] ES 스키마 버전 불일치: "
            f"현재={current}, 필요={settings.es_schema_version}"
        )
        return False

    print(f"[ok] ES 스키마 버전: v{current}")
    return True


def index_doc(doc_id: str, document: dict) -> bool:
    """문서 색인 (신규 or 덮어쓰기)"""
    try:
        get_client().index(
            index=settings.es_index_works,
            id=doc_id,
            document=document,        # ES 8.x: body= deprecated → document=
            refresh="wait_for",
        )
        return True
    except Exception as e:
        raise RuntimeError(f"ES 인덱싱 실패: {e}") from e


def update_doc(doc_id: str, partial: dict) -> bool:
    """부분 업데이트 (related_docs 추가 등)"""
    try:
        get_client().update(
            index=settings.es_index_works,
            id=doc_id,
            doc=partial,              # ES 8.x: body= deprecated → doc=
            refresh="wait_for",
        )
        return True
    except NotFoundError:
        return False
    except Exception as e:
        raise RuntimeError(f"ES 업데이트 실패: {e}") from e


def get_doc(doc_id: str) -> dict | None:
    try:
        res = get_client().get(index=settings.es_index_works, id=doc_id)
        return res["_source"]
    except NotFoundError:
        return None


def doc_exists(doc_id: str) -> bool:
    return get_client().exists(index=settings.es_index_works, id=doc_id)


def delete_doc(doc_id: str) -> bool:
    try:
        get_client().delete(index=settings.es_index_works, id=doc_id)
        return True
    except NotFoundError:
        return False