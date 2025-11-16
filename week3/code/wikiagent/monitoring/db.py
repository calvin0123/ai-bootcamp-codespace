import os
import sqlite3
from contextlib import contextmanager
from datetime import datetime
from typing import Iterable, Optional

from schemas import LLMLogRecord, CheckResult


class Database:
    
    
    def __init__(self, db_file: str = "data/monitoring.db"):
        import os
        os.makedirs("data", exist_ok=True)
        self.db_file = db_file
        self.ensure_schema()
    
    # ----------------------------
    # INTERNAL: create connection
    # ----------------------------
    def connect(self):
        return sqlite3.connect(self.db_file)


    # ----------------------------
    # Create tables if missing
    # ----------------------------
    def ensure_schema(self):
        conn = self.connect()
        cursor = conn.cursor()


        cursor.execute("""
        CREATE TABLE IF NOT EXISTS llm_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            filepath TEXT NOT NULL,
            agent_name TEXT,
            provider TEXT,
            model TEXT,
            user_prompt TEXT,
            instructions TEXT,
            tool_calls TEXT,
            total_input_tokens INTEGER,
            total_output_tokens INTEGER,
            assistant_answer TEXT,
            raw_json TEXT
        )
        """)

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS eval_checks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                log_id INTEGER NOT NULL,
                check_name TEXT NOT NULL,
                passed INTEGER,
                details TEXT,
                created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (log_id) REFERENCES llm_logs(id) ON DELETE CASCADE
            );
            """
                )
        conn.commit()
        conn.close()

    # ----------------------------
    # Insert a log file entry
    # ----------------------------
    def insert_log(self, rec: LLMLogRecord) -> int:
        conn = self.connect()
        cursor = conn.cursor()

        sql = ("""
        INSERT INTO llm_logs (
            filepath, 
            agent_name, 
            provider, model, 
            user_prompt, 
            instructions, 
            tool_calls,
            total_input_tokens,
            total_output_tokens, 
            assistant_answer, 
            raw_json)
        VALUES (?,?,?,?,?,?,?,?,?,?, ?)
        """)
        params = (
                rec.filepath,
                rec.agent_name,
                rec.provider,
                rec.model,
                rec.user_prompt,
                rec.instructions,
                rec.tool_calls,
                rec.total_input_tokens,
                rec.total_output_tokens,
                rec.assistant_answer,
                rec.raw_json,
                # _adapt_decimal(rec.input_cost),
                # _adapt_decimal(rec.output_cost),
                # _adapt_decimal(rec.total_cost),
            )
        cursor.execute(sql, params)
        log_id = cursor.lastrowid

        conn.commit()
        conn.close()

        return log_id
    
    # ----------------------------
    # Insert evaluation checks
    # ----------------------------
    def insert_checks(self, checks: Iterable[CheckResult]) -> None:
        conn = self.connect()
        cursor = conn.cursor()

        checks = list(checks)

        if not checks:
            return
        
        sql = (
            "INSERT INTO eval_checks (log_id, check_name, passed, details) VALUES (?,?,?,?)"
        )
        for c in checks:
            # normalize booleans for sqlite
            passed = c.passed
            if passed is not None:
                passed = 1 if passed else 0

            params = (
                    c.log_id,
                    getattr(c.check_name, "value", str(c.check_name)),
                    passed,
                    c.details,
                )
            
            cursor.execute(
                sql,
                params,
            )

        conn.commit()
        conn.close()


