# 🔎CAREER_COPILOT

> **채용공고 하나로 포트폴리오, 이력서, 자소서를 자동 생성하는 로컬 AI 커리어 문서 생성기**

---

## 왜 CAREER_COPILOT인가?

취업 준비에서 가장 고통스러운 과정 중 하나는 **같은 경험을 회사마다 다르게 포장하는 반복 작업**입니다.

- 지원하는 회사마다 자소서 항목이 다르고
- 이력서의 강조 포인트를 JD에 맞게 매번 수정해야 하며
- 포트폴리오는 어떤 프로젝트를 얼마나 강조할지 매번 고민해야 합니다

CAREER_COPILOT은 당신이 쌓아온 **작업물을 한 번 등록**해두면, 이후에는 **채용공고(JD)만 입력**하면 세 가지 문서를 자동으로 생성합니다.

모든 처리는 **로컬에서 실행**됩니다. 개인 정보와 작업물이 외부 서버로 전송되지 않습니다.

---

## 핵심 특징

### 🎯 JD 기반 완전 맞춤 생성
단순한 템플릿 채우기가 아닙니다. JD를 분석해 자소서용/이력서용/포트폴리오용으로 각각 재가공한 뒤, 용도에 맞는 작업물을 선별해 문서를 생성합니다.

### 🔒 완전 로컬 실행
LLM, Embedding, Reranking, 파일 저장, 검색 모두 로컬에서 동작합니다. 인터넷 연결 없이도 사용 가능하며 개인 데이터가 외부로 나가지 않습니다.

### 📂 Fire-and-Forget 업로드
파일을 올리면 AI가 자동으로 분류하고 분석합니다. 업로드 후 기다릴 필요 없이 다른 작업을 계속할 수 있으며, 결과는 백그라운드에서 처리됩니다.

### 🧠 구조화된 지식 베이스
단순 텍스트 검색이 아닙니다. 업로드된 파일은 Intent Classification과 Slot Filling을 거쳐 정형화된 지식으로 변환됩니다. 기술스택, 성과 수치, 트러블슈팅 등이 구조화된 슬롯으로 추출되어 정확한 Retrieval이 가능합니다.

### 🌏 다국어 동시 생성
한국어, English, 中文, 日本語를 동시에 선택하면 언어별로 별도 파일이 생성됩니다. 각 언어의 표기 관행(기술용어 병렬 표기 등)을 반영한 자연스러운 문서가 출력됩니다.

### ✅ 다단계 품질 검증
생성 파이프라인 전 단계에 Judge Agent가 배치되어 사실 오류, 서사 불일치, JD 미반영 등을 자동 감지하고 재생성합니다.

---

## 생성 문서 유형

| 문서 | 형식 | 특징 |
|------|------|------|
| 포트폴리오 | PDF (16:9) | Planner → HTML 슬라이드 → Playwright 렌더링, 두괄식 구조 |
| 이력서 | DOCX | Structured Output 강제, STAR 형식, 사실 기반 |
| 자소서 | DOCX | 항목별 글자수 제한 지원, 4단계 품질 검증 |

---

## 지원 입력 파일

| 유형 | 파일 형식 |
|------|-----------|
| 개발/설계 작업물 | ZIP, PDF, PPT, PPTX, 이미지 |
| 수상 / 자격증 / 어학 | PDF, JPG, PNG |
| 대외활동 / 경력증명 | PDF, JPG, PNG |

---

## 기술 스택

### AI / ML
| 구성 요소 | 기술 |
|-----------|------|
| LLM (IC/SF/Judge/JD분석) | Qwen2.5-7B-Instruct Q4 (Group A) |
| LLM (Planner/Writer) | Qwen2.5-7B-Instruct Q4 (Group B) |
| VLM (이미지/슬라이드 분석) | Qwen2.5-VL-7B Q4 (Group C) |
| Embedding | BAAI/bge-m3 |
| Reranking | BAAI/bge-reranker-v2-m3 |
| 구동 엔진 | llama.cpp (Flash Attention) |

### 저장소 / 검색
| 구성 요소 | 기술 |
|-----------|------|
| 파일 저장소 | MinIO (로컬 S3) |
| 벡터/키워드 인덱스 | Elasticsearch (Dense + Sparse + Slot Filter) |
| 상태 / 프로필 DB | SQLite |
| Task Queue | Celery + Redis |

### 렌더링 / 백엔드 / 프론트엔드
| 구성 요소 | 기술 |
|-----------|------|
| PDF 렌더링 | Playwright (HTML → PDF) |
| DOCX 생성 | python-docx |
| API 서버 | FastAPI + SSE |
| 프론트엔드 | Svelte |

---

## 시스템 아키텍처

```
┌─────────────────────────────────────────────────────────┐
│                      Svelte Frontend                    │
│   Upload │ Assets │ Generate │ Profile │ Design Cue     │
└───────────────────────┬─────────────────────────────────┘
                        │ SSE / REST
┌───────────────────────▼────────────────────────────────┐
│                   FastAPI Backend                      │
│                                                        │
│  ┌─────────────────────────────────────────────────┐   │
│  │              Orchestrator Agent                 │   │
│  │                                                 │   │
│  │  ┌──────────────┐  ┌──────────────┐             │   │
│  │  │  Ingestion   │  │  Generation  │             │   │
│  │  │    Agent     │  │    Agent     │             │   │
│  │  │              │  │              │             │   │
│  │  │ IC → SF      │  │ JD Analyzer  │             │   │
│  │  │ VLM (opt.)   │  │ Planner      │             │   │
│  │  │ Judge-I1     │  │ Writer × 3   │             │   │
│  │  └──────┬───────┘  │ Judge G1~G4  │             │   │
│  │         │          └──────┬───────┘             │   │
│  │         │    ┌────────────▼──────┐              │   │
│  │         │    │  Retrieval Agent  │              │   │
│  │         │    │  bge-m3 + ES RAG  │              │   │
│  │         │    │  + Reranker       │              │   │
│  │         │    └───────────────────┘              │   │
│  └─────────┼───────────────────────────────────────┘   │
│            │                                           │
│  ┌─────────▼──────────────────────────────────────┐    │
│  │         VRAM Scheduler (Mutex Lock)            │    │
│  │  Group A ←→ Group B ←→ Group C (순차 스위칭)     │    │
│  └────────────────────────────────────────────────┘    │
│                                                        │
│  Celery + Redis (비동기 태스크)                          │
└───────────────────────┬────────────────────────────────┘
                        │
        ┌───────────────┼───────────────┐
        ▼               ▼               ▼
   MinIO (파생파일)   ES (인덱스)    SQLite (상태)
   rendered/         Dense+Sparse   WorkAsset
   thumb/            +Slot Filter   Profile
   outputs/                         Generation
```

---

## 워크플로우

### 1단계: 작업물 업로드 (1회성 사전 작업)

```
파일 선택
  └─ 유형 힌트 선택 (선택사항)
       🗂️ 작업물 / 🏆 수상·자격 / 📋 활동·경력 / 🤷 AI 분류
  └─ 프로젝트 연결 선택 (선택사항, 드롭다운)

↓ 백그라운드 자동 처리

SHA-256 중복 체크 → 파일 완전성 검증 (Soft Padding)
→ VLM 이미지 분석 (이미지/슬라이드 포함 시)
→ Intent Classification (Engineering/Design/Research/Achievement/Activity/Career)
→ Slot Filling (기술스택, 성과 수치, 트러블슈팅 등)
→ Judge 품질 검토 → ES 인덱싱 완료 확인 (Soft Padding)
```

### 2단계: 문서 생성 (JD 입력마다)

```
[Step 1] 생성 대상 + 언어 + 프로필 + 디자인 큐 선택
[Step 2] JD 입력 (회사명, 직무명, JD 전문)
[Step 3] 자소서 질문 입력 (자소서 선택 시)
[Step 4] 생성 시작

↓ 자동 생성 파이프라인

JD 분석 → 용도별 재가공 (자소서용/이력서용/포트폴리오용)
→ Judge G1/G2 (JD 품질 검토)
→ RAG (Hybrid Search + Reranking)
→ Judge G3a/G3b (RAG 품질 검토)
→ Planner + Writer (포트폴리오: 설계도 → HTML 슬라이드)
   Writer (이력서: Structured Output)
   Writer (자소서: 항목별 Temperature 조절)
→ Judge G4 (생성물 품질 검토)
→ 렌더링 (Playwright PDF / python-docx DOCX)
→ 출력 파일 완전성 확인 (Soft Padding)
→ 완료
```

---

## Judge 품질 검증 체계

```
Judge-I1  : SF 슬롯 추출 품질 (정확성, 완성도)
Judge-G1  : JD 재가공 3종 개별 품질
Judge-G2  : JD 재가공 3종 맥락 일관성
Judge-G3a : RAG 결과 적합성 + Hard Negative 감지
Judge-G3b : RAG 결과 통합 서사 일관성
Judge-G4r : 이력서 사실 검증 + STAR 형식
Judge-G4c : 자소서 4단계 (사실/서사/차별성/JD정합성)
Judge-G4p : 포트폴리오 설계도 구조/비중/완결성
Judge-G4ph: 포트폴리오 HTML 설계도 충실도 + CSS 변수
```

각 Judge는 `PASS / RETRY (최대 3회) / ESCALATE` 판정을 내리며,
ESCALATE는 파이프라인을 중단하지 않고 품질 경고와 함께 진행합니다.

---

## 최소 권장 사양

| 항목 | 최소 | 권장 |
|------|------|------|
| GPU VRAM | 6GB | 8GB+ |
| RAM | 16GB | 32GB |
| Storage | 50GB | 100GB+ |
| OS | Ubuntu 22.04 / Windows WSL2 / macOS | Ubuntu 22.04 |

> RTX 3060 6GB + 16GB RAM 환경에서 개발 및 검증 중입니다.

---

## 구현 로드맵

| Stage | 내용 | 상태 |
|-------|------|------|
| 0 | 인프라 기반 (Docker, ES, MinIO, SQLite, llama.cpp) | 📋 예정 |
| 1 | 파일 수집 파이프라인 (업로드 → IC/SF → ES 인덱싱) | 📋 예정 |
| 2 | Embedding + Hybrid RAG | 📋 예정 |
| 3 | 이력서 생성 End-to-End | 📋 예정 |
| 4 | 자소서 생성 | 📋 예정 |
| 5 | 포트폴리오 생성 | 📋 예정 |
| 6 | 전체 통합 + Svelte UI | 📋 예정 |

---

## 라이선스

본 프로젝트는 개인 사용 목적으로 개발 중입니다.