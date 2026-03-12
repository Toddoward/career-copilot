-- CAREER_COPILOT SQLite Schema
-- schema_version: 1

PRAGMA journal_mode=WAL;
PRAGMA foreign_keys=ON;

-- 스키마 버전 관리
CREATE TABLE IF NOT EXISTS schema_meta (
    key     TEXT PRIMARY KEY,
    value   TEXT NOT NULL
);
INSERT OR IGNORE INTO schema_meta VALUES ('schema_version', '1');

-- 사용자 프로필
CREATE TABLE IF NOT EXISTS user_profile (
    profile_id      TEXT PRIMARY KEY,
    name            TEXT NOT NULL,
    email           TEXT,
    phone           TEXT,
    address         TEXT,
    github_url      TEXT,
    portfolio_url   TEXT,
    is_default      INTEGER DEFAULT 0,
    created_at      TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at      TEXT NOT NULL DEFAULT (datetime('now'))
);

-- 학력
CREATE TABLE IF NOT EXISTS education (
    edu_id          TEXT PRIMARY KEY,
    profile_id      TEXT NOT NULL,
    institution     TEXT NOT NULL,
    major           TEXT,
    degree          TEXT,
    start_date      TEXT,
    end_date        TEXT,
    is_included     INTEGER DEFAULT 1,
    FOREIGN KEY (profile_id) REFERENCES user_profile(profile_id) ON DELETE CASCADE
);

-- 경력 (재직기간/회사명만, 상세는 ES)
CREATE TABLE IF NOT EXISTS career_entry (
    career_id       TEXT PRIMARY KEY,
    profile_id      TEXT NOT NULL,
    company         TEXT NOT NULL,
    role            TEXT,
    start_date      TEXT NOT NULL,
    end_date        TEXT,
    is_current      INTEGER DEFAULT 0,
    is_included     INTEGER DEFAULT 1,
    FOREIGN KEY (profile_id) REFERENCES user_profile(profile_id) ON DELETE CASCADE
);

-- 군복무
CREATE TABLE IF NOT EXISTS military_service (
    military_id     TEXT PRIMARY KEY,
    profile_id      TEXT NOT NULL,
    branch          TEXT,
    start_date      TEXT,
    end_date        TEXT,
    discharge_type  TEXT,
    is_included     INTEGER DEFAULT 1,
    FOREIGN KEY (profile_id) REFERENCES user_profile(profile_id) ON DELETE CASCADE
);

-- 작업물 (파일 업로드 상태 추적)
CREATE TABLE IF NOT EXISTS work_asset (
    asset_id        TEXT PRIMARY KEY,
    project_id      TEXT,
    intent          TEXT,
    status          TEXT NOT NULL DEFAULT 'QUEUED',
    -- QUEUED / PROCESSING / SF_DONE / INDEXED / INDEXED_PARTIAL / FAILED
    path_status     TEXT NOT NULL DEFAULT 'valid',
    -- valid / missing / moved
    local_path      TEXT NOT NULL,
    file_hash       TEXT NOT NULL UNIQUE,
    file_name       TEXT NOT NULL,
    file_type       TEXT,
    minio_rendered  TEXT,
    slot_data       TEXT,  -- SF 결과 JSON (ES 저장 전 임시)
    created_at      TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at      TEXT NOT NULL DEFAULT (datetime('now'))
);

-- 프로젝트 그룹
CREATE TABLE IF NOT EXISTS project (
    project_id      TEXT PRIMARY KEY,
    name            TEXT NOT NULL,
    intent          TEXT,
    description     TEXT,
    created_at      TEXT NOT NULL DEFAULT (datetime('now'))
);

-- 디자인 큐 (포트폴리오 CSS 토큰)
CREATE TABLE IF NOT EXISTS design_cue (
    cue_id          TEXT PRIMARY KEY,
    name            TEXT NOT NULL,
    tokens          TEXT NOT NULL,  -- JSON: CSS 변수 토큰
    layout_slots    TEXT,           -- JSON: hero_type, content_flow 등
    is_default      INTEGER DEFAULT 0,
    created_at      TEXT NOT NULL DEFAULT (datetime('now'))
);

-- 자소서 양식 템플릿
CREATE TABLE IF NOT EXISTS coverletter_template (
    template_id     TEXT PRIMARY KEY,
    name            TEXT NOT NULL,
    sections        TEXT NOT NULL,  -- JSON: [{question, char_limit}]
    created_at      TEXT NOT NULL DEFAULT (datetime('now'))
);

-- 생성 이력
CREATE TABLE IF NOT EXISTS generation (
    gen_id          TEXT PRIMARY KEY,
    profile_id      TEXT,
    cue_id          TEXT,
    template_id     TEXT,
    company         TEXT,
    job_title       TEXT,
    jd_raw          TEXT,
    targets         TEXT NOT NULL,  -- JSON: ["resume","coverletter","portfolio"]
    languages       TEXT NOT NULL,  -- JSON: ["ko","en"]
    status          TEXT NOT NULL DEFAULT 'QUEUED',
    -- QUEUED / PROCESSING / DONE / PARTIAL / FAILED
    output_paths    TEXT,           -- JSON: {ko: {resume: path, ...}, en: {...}}
    created_at      TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at      TEXT NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY (profile_id) REFERENCES user_profile(profile_id),
    FOREIGN KEY (cue_id) REFERENCES design_cue(cue_id)
);

-- 지원 기록 + 합불 관리
CREATE TABLE IF NOT EXISTS application_history (
    history_id  TEXT PRIMARY KEY,
    gen_id      TEXT NOT NULL,
    company     TEXT,
    job_title   TEXT,
    result      TEXT NOT NULL DEFAULT 'pending',
    -- pending / pass / fail / doc_pass / final_pass
    applied_at  TEXT,
    note        TEXT,
    created_at  TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at  TEXT NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY (gen_id) REFERENCES generation(gen_id) ON DELETE CASCADE
);
-- gen_id → generation.output_paths → MinIO Intermediate 파일 역추적 가능
-- 추후 Feedback 루프 연결 시 이 구조 그대로 활용

-- 사용자 전역 생성 방향성 (Global Context, Depth 1)
CREATE TABLE IF NOT EXISTS user_preferences (
    pref_id     TEXT PRIMARY KEY,
    profile_id  TEXT,
    content     TEXT NOT NULL,  -- 자유 텍스트 ("항상 짧게", "수치 포함" 등)
    updated_at  TEXT NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY (profile_id) REFERENCES user_profile(profile_id) ON DELETE CASCADE
);

-- 채팅 메시지 이력 (Channel Context 원본, Depth 2)
CREATE TABLE IF NOT EXISTS chat_message (
    msg_id      TEXT PRIMARY KEY,
    gen_id      TEXT NOT NULL,
    role        TEXT NOT NULL,     -- "user" | "assistant"
    msg_type    TEXT NOT NULL,     -- "jd_input" | "setup" | "generation_result"
                                   -- | "edit_request" | "edit_result" | "system"
    content     TEXT NOT NULL,     -- 메시지 본문 (텍스트 또는 JSON)
    version     INTEGER,           -- 연관 문서 버전 (수정 결과 메시지일 경우)
    created_at  TEXT NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY (gen_id) REFERENCES generation(gen_id) ON DELETE CASCADE
);
-- version + 경로 규칙으로 MinIO 수정본 역추적:
--   cc-outputs/{gen_id}/{doc_type}/{doc_type}_{lang}_v{version}.{ext}

-- 인덱스
CREATE INDEX IF NOT EXISTS idx_work_asset_hash      ON work_asset(file_hash);
CREATE INDEX IF NOT EXISTS idx_work_asset_status    ON work_asset(status);
CREATE INDEX IF NOT EXISTS idx_work_asset_project   ON work_asset(project_id);
CREATE INDEX IF NOT EXISTS idx_generation_status    ON generation(status);
CREATE INDEX IF NOT EXISTS idx_history_gen          ON application_history(gen_id);
CREATE INDEX IF NOT EXISTS idx_chat_message_gen     ON chat_message(gen_id);
CREATE INDEX IF NOT EXISTS idx_preferences_profile  ON user_preferences(profile_id);