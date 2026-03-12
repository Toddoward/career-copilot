"""
CAREER_COPILOT FastAPI 진입점
Stage 0: 앱 시작 시 인프라 연결 확인 + 스키마 버전 체크 + 경로 유효성 체크
"""
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.config import get_settings
from backend.storage.sqlite_client import init_db, check_all_local_paths

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # ── 앱 시작 시 실행 ──────────────────────────────────────────────
    print("[startup] CAREER_COPILOT 초기화 시작")

    # 1. SQLite 스키마 초기화 (idempotent)
    init_db()

    # 2. ES 스키마 버전 체크 (ES-5: 불일치 시 앱 시작 차단)
    from backend.storage.es_client import verify_schema
    if not verify_schema():
        raise RuntimeError(
            "[startup] ES 스키마 버전 불일치 — "
            "infra/elasticsearch/init_index.py 실행 후 재시작하세요."
        )

    # 3. 로컬 파일 경로 유효성 체크 (FILE_MISSING 감지)
    check_all_local_paths()

    print("[startup] 초기화 완료")
    yield
    # ── 앱 종료 시 실행 ──────────────────────────────────────────────
    print("[shutdown] CAREER_COPILOT 종료")


app = FastAPI(
    title="CAREER_COPILOT",
    version="0.1.0",
    description="JD 기반 로컬 AI 문서 생성 서비스",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # Vite dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── 헬스체크 ──────────────────────────────────────────────────────────────────

@app.get("/health")
def health():
    return {"status": "ok", "version": "0.1.0"}


@app.get("/health/infra")
def health_infra():
    """인프라 연결 상태 상세 확인 (개발용)"""
    results: dict[str, str] = {}

    # ES
    try:
        from backend.storage.es_client import get_client as es_client
        es_client().ping()
        results["elasticsearch"] = "ok"
    except Exception as e:
        results["elasticsearch"] = f"error: {e}"

    # MinIO
    try:
        from backend.storage.minio_client import get_client as minio_client
        minio_client().bucket_exists("cc-works")
        results["minio"] = "ok"
    except Exception as e:
        results["minio"] = f"error: {e}"

    # Redis
    try:
        import redis
        r = redis.Redis.from_url(settings.redis_url)
        r.ping()
        results["redis"] = "ok"
    except Exception as e:
        results["redis"] = f"error: {e}"

    # llama.cpp
    try:
        import httpx
        res = httpx.get(f"{settings.llama_cpp_url}/health", timeout=3)
        results["llama_cpp"] = "ok" if res.status_code == 200 else f"status={res.status_code}"
    except Exception as e:
        results["llama_cpp"] = f"error: {e}"

    all_ok = all(v == "ok" for v in results.values())
    return {"status": "ok" if all_ok else "degraded", "services": results}