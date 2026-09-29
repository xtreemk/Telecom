from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any, Iterator

from app.config import settings


def get_db_path() -> Path:
    path = Path(settings.DB_PATH)
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def get_db() -> sqlite3.Connection:
    conn = sqlite3.connect(str(get_db_path()))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def _ensure_migrations() -> None:
    with get_db() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS customers (
                phone TEXT PRIMARY KEY,
                profile_json TEXT NOT NULL
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS conversations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                phone TEXT NOT NULL,
                created TEXT NOT NULL,
                updated TEXT NOT NULL,
                channel TEXT NOT NULL DEFAULT 'chat',
                language TEXT NOT NULL DEFAULT 'en',
                customer_name TEXT NOT NULL DEFAULT '',
                interrupted INTEGER NOT NULL DEFAULT 0
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                conversation_id INTEGER NOT NULL,
                role TEXT NOT NULL,
                message TEXT NOT NULL,
                created TEXT NOT NULL,
                language TEXT NOT NULL DEFAULT 'en',
                intent TEXT,
                tool_called TEXT,
                tool_result_json TEXT,
                FOREIGN KEY(conversation_id) REFERENCES conversations(id)
            )
            """
        )

        conversation_columns = {row[1] for row in conn.execute("PRAGMA table_info(conversations)").fetchall()}
        if "channel" not in conversation_columns:
            conn.execute("ALTER TABLE conversations ADD COLUMN channel TEXT NOT NULL DEFAULT 'chat'")
        if "language" not in conversation_columns:
            conn.execute("ALTER TABLE conversations ADD COLUMN language TEXT NOT NULL DEFAULT 'en'")
        if "customer_name" not in conversation_columns:
            conn.execute("ALTER TABLE conversations ADD COLUMN customer_name TEXT NOT NULL DEFAULT ''")
        if "interrupted" not in conversation_columns:
            conn.execute("ALTER TABLE conversations ADD COLUMN interrupted INTEGER NOT NULL DEFAULT 0")
        message_columns = {row[1] for row in conn.execute("PRAGMA table_info(messages)").fetchall()}
        if "language" not in message_columns:
            conn.execute("ALTER TABLE messages ADD COLUMN language TEXT NOT NULL DEFAULT 'en'")
        if "intent" not in message_columns:
            conn.execute("ALTER TABLE messages ADD COLUMN intent TEXT")
        if "tool_called" not in message_columns:
            conn.execute("ALTER TABLE messages ADD COLUMN tool_called TEXT")
        if "tool_result_json" not in message_columns:
            conn.execute("ALTER TABLE messages ADD COLUMN tool_result_json TEXT")
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS transactions (
                id TEXT PRIMARY KEY,
                phone TEXT NOT NULL,
                amount INTEGER NOT NULL,
                kind TEXT NOT NULL,
                status TEXT NOT NULL,
                created TEXT NOT NULL,
                metadata_json TEXT NOT NULL
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS tickets (
                id TEXT PRIMARY KEY,
                phone TEXT NOT NULL,
                message TEXT NOT NULL,
                status TEXT NOT NULL,
                created TEXT NOT NULL
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS audit_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                actor TEXT NOT NULL,
                agent TEXT NOT NULL,
                tool TEXT NOT NULL,
                action TEXT NOT NULL,
                customer_phone TEXT NOT NULL,
                status TEXT NOT NULL,
                created TEXT NOT NULL,
                metadata_json TEXT NOT NULL
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL UNIQUE,
                role TEXT NOT NULL,
                is_active INTEGER NOT NULL DEFAULT 1,
                created TEXT NOT NULL
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS roles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                description TEXT NOT NULL
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS permissions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                role TEXT NOT NULL,
                tool_name TEXT NOT NULL,
                UNIQUE(role, tool_name)
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS knowledge_entries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                category TEXT NOT NULL,
                title TEXT NOT NULL,
                content TEXT NOT NULL,
                created TEXT NOT NULL
            )
            """
        )

        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS escalations (
                id TEXT PRIMARY KEY,
                customer_phone TEXT NOT NULL,
                conversation_ref TEXT NOT NULL,
                reason TEXT NOT NULL,
                priority TEXT NOT NULL,
                status TEXT NOT NULL,
                ai_actions_attempted TEXT NOT NULL,
                recommended_next_action TEXT NOT NULL,
                created TEXT NOT NULL,
                updated TEXT NOT NULL,
                attempted_tool TEXT NOT NULL
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS proactive_offer_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                phone TEXT NOT NULL,
                conversation_id INTEGER NOT NULL,
                offer_id TEXT NOT NULL,
                offered_at TEXT NOT NULL
            )
            """
        )
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_offer_events_phone_time "
            "ON proactive_offer_events(phone, offered_at)"
        )


def init_db() -> None:
    _ensure_migrations()
    with get_db() as conn:
        customer_count = conn.execute("SELECT COUNT(*) FROM customers").fetchone()[0]
        if customer_count == 0:
            from app.seed_data import seed_customers

            for phone, profile in seed_customers().items():
                conn.execute(
                    "INSERT INTO customers(phone, profile_json) VALUES (?, ?)",
                    (phone, json.dumps(profile)),
                )

        knowledge_count = conn.execute("SELECT COUNT(*) FROM knowledge_entries").fetchone()[0]
        if knowledge_count == 0:
            from app.seed_data import seed_knowledge

            for entry in seed_knowledge():
                conn.execute(
                    "INSERT INTO knowledge_entries(category, title, content, created) VALUES (?, ?, ?, ?)",
                    (entry["category"], entry["title"], entry["content"], entry["created"]),
                )

        role_count = conn.execute("SELECT COUNT(*) FROM roles").fetchone()[0]
        if role_count == 0:
            default_roles = [
                ("admin", "Full system access"),
                ("agent", "Customer support workflows"),
                ("network_specialist", "Network troubleshooting"),
                ("billing_specialist", "Billing and transaction workflows"),
            ]
            conn.executemany(
                "INSERT INTO roles(name, description) VALUES (?, ?)",
                default_roles,
            )

        permission_count = conn.execute("SELECT COUNT(*) FROM permissions").fetchone()[0]
        if permission_count == 0:
            default_permissions = [
                ("admin", "customer_lookup"),
                ("admin", "data_balance_lookup"),
                ("admin", "transaction_lookup"),
                ("admin", "network_diagnostic"),
                ("admin", "complaint_create"),
                ("admin", "bundle_remediation"),
                ("agent", "customer_lookup"),
                ("agent", "data_balance_lookup"),
                ("agent", "transaction_lookup"),
                ("network_specialist", "customer_lookup"),
                ("network_specialist", "network_diagnostic"),
                ("billing_specialist", "customer_lookup"),
                ("billing_specialist", "transaction_lookup"),
                ("billing_specialist", "bundle_remediation"),
                ("billing_specialist", "data_balance_lookup"),
            ]
            conn.executemany(
                "INSERT INTO permissions(role, tool_name) VALUES (?, ?)",
                default_permissions,
            )


init_db()


def row_to_dict(row: sqlite3.Row | None) -> dict[str, Any] | None:
    if row is None:
        return None
    return dict(row)
