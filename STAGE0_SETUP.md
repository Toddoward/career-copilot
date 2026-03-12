# Stage 0 셋업 가이드

## 전제 조건

- Docker Desktop (또는 Docker Engine + Compose v2)
- Python 3.11+
- llama.cpp 빌드 완료 (`llama-server` 바이너리 존재)
- GGUF 모델 파일 다운로드 완료

---

## 디렉토리 구조 (Stage 0 기준)

```
career_copilot/
├── docker-compose.yml       ← ES + MinIO + Redis (컨테이너 3개)
├── .env.example             ← 환경변수 템플릿
├── verify_stage0.py         ← 검증 스크립트
│
├── infra/
│   ├── elasticsearch/
│   │   ├── mappings/works_index.json  ← dense_vector 1024dim, sparse_vector
│   │   └── init_index.py
│   ├── minio/
│   │   └── init_buckets.py
│   └── sqlite/
│       └── schema.sql                 ← 13개 테이블
│
└── backend/
    ├── __init__.py
    ├── config.py
    ├── main.py              ← FastAPI 앱 + /health
    └── storage/
        ├── __init__.py
        ├── es_client.py
        ├── minio_client.py
        └── sqlite_client.py
```

---

## 실행 순서

### 1. 환경 파일 설정

```bash
cp .env.example .env
# .env에서 모델 절대 경로 수정
```

### 2. Docker 인프라 기동

```bash
docker-compose up -d
docker-compose ps   # 3개 서비스 모두 "healthy" 확인
```

### 3. Python 의존성 설치 (초기화 스크립트용)

```bash
pip install elasticsearch minio redis httpx
```

### 4. ES 인덱스 초기화

```bash
python infra/elasticsearch/init_index.py
```

### 5. MinIO 버킷 초기화

```bash
python infra/minio/init_buckets.py
```

### 6. SQLite 스키마 초기화

```bash
mkdir -p data
sqlite3 data/career_copilot.db < infra/sqlite/schema.sql
```

### 7. llama-server 기동 (Docker 외부, CUDA 직접 접근)

```bash
./llama-server \
  --model ./models/qwen2.5-7b-instruct-q4_k_m.gguf \
  --host 0.0.0.0 \
  --port 8080 \
  --n-gpu-layers 35 \
  --flash-attn \
  --ctx-size 8192

# 확인: curl http://localhost:8080/health
```

> `--n-gpu-layers 35` : RTX 3060 6GB 기준. OOM 시 줄여서 조정.

### 8. Stage 0 검증

```bash
python verify_stage0.py
```

**기대 출력:**

```
==================================================
CAREER_COPILOT Stage 0 검증
==================================================
  ✅ Elasticsearch 연결: status=yellow
  ✅ Elasticsearch 인덱스 존재: schema_version=1
  ✅ MinIO 연결: healthy
  ✅ MinIO 버킷 존재: cc-works, cc-outputs
  ✅ Redis 연결: PONG
  ✅ SQLite 스키마: 13개 테이블, 7개 인덱스
  ✅ llama.cpp 서버: healthy
==================================================
결과: 7개 통과 / 0개 실패
Stage 0 검증 완료. Stage 1 진행 가능.
```

---

## SQLite 테이블 목록 (schema_version=1)

| 테이블 | 설명 |
|--------|------|
| schema_meta | 스키마 버전 관리 |
| user_profile | 개인정보 |
| education | 학력 |
| career_entry | 경력 (회사명, 재직기간) |
| military_service | 군복무 |
| project | 프로젝트 그룹 |
| work_asset | 파일 상태 머신 + 로컬 경로 |
| design_cue | 디자인 큐 CSS 토큰 |
| coverletter_template | 자소서 양식 |
| generation | 생성 이력 |
| application_history | 지원 기록 + 합불 |
| user_preferences | Global Context |
| chat_message | Channel Context 대화 이력 |

---

## 트러블슈팅

| 증상 | 원인 | 해결 |
|------|------|------|
| ES `yellow` 상태 | 단일 노드 replica 미할당 | 정상 (단일 노드에서 yellow는 문제 없음) |
| ES 인덱스 생성 실패 | works_index.json 매핑 오류 | `dense_vector` / `sparse_vector` 타입 확인 |
| MinIO 연결 실패 | 컨테이너 미기동 | `docker-compose up -d minio` |
| llama-server OOM | GPU 레이어 수 과다 | `--n-gpu-layers` 줄이기 |
| SQLite `no such table` | schema.sql 미실행 | 6번 단계 재실행 |