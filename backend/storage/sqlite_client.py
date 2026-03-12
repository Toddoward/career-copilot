"""
SQLite 클라이언트
상태 관리, 프로필, 생성 이력
"""
import sqlite3
import json
from contextlib import contextmanager
from pathlib import Path
from backend.config import get_settings

settings = get_settings()


def get_db_path() -> str:
    path = Path(settings.sqlite_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    return str(path)


@contextmanager
def get_conn():
    conn = sqlite3.connect(get_db_path(), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db():
    """스키마 초기화 (앱 시작 시 실행)"""
    schema_path = Path(__file__).parent.parent.parent / "infra" / "sqlite" / "schema.sql"
    with open(schema_path) as f:
        sql = f.read()
    with get_conn() as conn:
        conn.executescript(sql)
    print("[OK] SQLite 스키마 초기화 완료")


# WorkAsset CRUD
def upsert_asset(asset: dict):
    with get_conn() as conn:
        conn.execute("""
            INSERT INTO work_asset
                (asset_id, project_id, intent, status, path_status,
                 local_path, file_hash, file_name, file_type,
                 minio_rendered, slot_data, updated_at)
            VALUES
                (:asset_id, :project_id, :intent, :status, :path_status,
                 :local_path, :file_hash, :file_name, :file_type,
                 :minio_rendered, :slot_data, datetime('now'))
            ON CONFLICT(asset_id) DO UPDATE SET
                status       = excluded.status,
                path_status  = excluded.path_status,
                intent       = excluded.intent,
                project_id   = excluded.project_id,
                minio_rendered = excluded.minio_rendered,
                slot_data    = excluded.slot_data,
                updated_at   = datetime('now')
        """, asset)


def get_asset(asset_id: str) -> dict | None:
    with get_conn() as conn:
        row = conn.execute(
            "SELECT * FROM work_asset WHERE asset_id = ?", (asset_id,)
        ).fetchone()
    return dict(row) if row else None


def find_by_hash(file_hash: str) -> dict | None:
    with get_conn() as conn:
        row = conn.execute(
            "SELECT * FROM work_asset WHERE file_hash = ?", (file_hash,)
        ).fetchone()
    return dict(row) if row else None


def update_asset_status(asset_id: str, status: str):
    with get_conn() as conn:
        conn.execute(
            "UPDATE work_asset SET status = ?, updated_at = datetime('now') WHERE asset_id = ?",
            (status, asset_id)
        )


def get_pending_sf_done() -> list[dict]:
    """앱 재시작 시 SF_DONE 상태 복구용"""
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT * FROM work_asset WHERE status = 'SF_DONE'"
        ).fetchall()
    return [dict(r) for r in rows]


# 경로 유효성 체크
def check_all_local_paths():
    """앱 시작 시 또는 주기적 실행"""
    import os
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT asset_id, local_path FROM work_asset WHERE path_status = 'valid'"
        ).fetchall()
        for row in rows:
            if not os.path.exists(row["local_path"]):
                conn.execute(
                    "UPDATE work_asset SET path_status = 'missing', updated_at = datetime('now') WHERE asset_id = ?",
                    (row["asset_id"],)
                )


# ── application_history CRUD ──────────────────────────────────────────────────

def insert_history(record: dict):
    """지원 기록 생성"""
    with get_conn() as conn:
        conn.execute("""
            INSERT INTO application_history
                (history_id, gen_id, company, job_title, result,
                 applied_at, note, created_at, updated_at)
            VALUES
                (:history_id, :gen_id, :company, :job_title, :result,
                 :applied_at, :note, datetime('now'), datetime('now'))
        """, record)


def update_history_result(history_id: str, result: str, note: str | None = None):
    """합불 결과 업데이트"""
    with get_conn() as conn:
        conn.execute(
            """UPDATE application_history
               SET result = ?, note = COALESCE(?, note), updated_at = datetime('now')
               WHERE history_id = ?""",
            (result, note, history_id)
        )


def get_history_by_gen(gen_id: str) -> dict | None:
    with get_conn() as conn:
        row = conn.execute(
            "SELECT * FROM application_history WHERE gen_id = ?", (gen_id,)
        ).fetchone()
    return dict(row) if row else None


def list_history(limit: int = 50) -> list[dict]:
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT * FROM application_history ORDER BY created_at DESC LIMIT ?",
            (limit,)
        ).fetchall()
    return [dict(r) for r in rows]


# ── user_preferences CRUD ─────────────────────────────────────────────────────

def upsert_preference(pref_id: str, profile_id: str | None, content: str):
    """Global Context 저장/갱신"""
    with get_conn() as conn:
        conn.execute("""
            INSERT INTO user_preferences (pref_id, profile_id, content, updated_at)
            VALUES (?, ?, ?, datetime('now'))
            ON CONFLICT(pref_id) DO UPDATE SET
                content    = excluded.content,
                updated_at = datetime('now')
        """, (pref_id, profile_id, content))


def get_preference(profile_id: str | None) -> str | None:
    """profile_id 기준 Global Context 조회 (없으면 None)"""
    with get_conn() as conn:
        row = conn.execute(
            "SELECT content FROM user_preferences WHERE profile_id IS ? LIMIT 1",
            (profile_id,)
        ).fetchone()
    return row["content"] if row else None


# ── chat_message CRUD ─────────────────────────────────────────────────────────

def insert_chat_message(msg: dict):
    """채팅 메시지 저장"""
    with get_conn() as conn:
        conn.execute("""
            INSERT INTO chat_message
                (msg_id, gen_id, role, msg_type, content, version, created_at)
            VALUES
                (:msg_id, :gen_id, :role, :msg_type, :content, :version, datetime('now'))
        """, msg)


def get_chat_messages(gen_id: str) -> list[dict]:
    """채널 전체 이력 조회 (시간순)"""
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT * FROM chat_message WHERE gen_id = ? ORDER BY created_at ASC",
            (gen_id,)
        ).fetchall()
    return [dict(r) for r in rows]


def get_recent_chat_messages(gen_id: str, limit: int = 3) -> list[dict]:
    """롤링 요약용 최근 N개 메시지"""
    with get_conn() as conn:
        rows = conn.execute(
            """SELECT * FROM chat_message WHERE gen_id = ?
               ORDER BY created_at DESC LIMIT ?""",
            (gen_id, limit)
        ).fetchall()
    return list(reversed([dict(r) for r in rows]))