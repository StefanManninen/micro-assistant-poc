import sqlite3
import os
import hashlib

class AssistantDatabase:
    def __init__(self, db_path="storage/micro_assistant.db"):
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self.db_path = db_path
        self.init_db()

    def get_connection(self):
        return sqlite3.connect(self.db_path)

    def normalize_text(self, text):
        return " ".join(text.strip().lower().split())

    def generate_hash(self, context, user_input):
        normalized = self.normalize_text(user_input)
        combined = f"{context}:{normalized}"
        return hashlib.sha256(combined.encode("utf-8")).hexdigest()

    def init_db(self):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # 1.History log
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS history_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    context TEXT,
                    user_input TEXT,
                    router_decision TEXT,
                    final_response TEXT
                )
            ''')
            
            # 2. The new, separated policy layer (v3)
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS tool_policy (
                    context_hash TEXT PRIMARY KEY,
                    context TEXT,
                    raw_input TEXT,
                    cached_answer TEXT,
                    route_weight REAL DEFAULT 1.0,
                    answer_weight REAL DEFAULT 1.0,
                    source TEXT DEFAULT 'generated',
                    hit_count INTEGER DEFAULT 0,
                    last_used_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            # 3. Statistics table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS assistant_stats (
                    metric TEXT PRIMARY KEY,
                    value REAL DEFAULT 0.0
                )
            ''')
            cursor.execute("INSERT OR IGNORE INTO assistant_stats (metric, value) VALUES ('intuition_hits', 0.0)")
            cursor.execute("INSERT OR IGNORE INTO assistant_stats (metric, value) VALUES ('saved_time_ms', 0.0)")
            cursor.execute("INSERT OR IGNORE INTO assistant_stats (metric, value) VALUES ('saved_tokens', 0.0)")
            conn.commit()

    def log_interaction(self, context, user_input, router_decision, final_response):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO history_log (context, user_input, router_decision, final_response)
                VALUES (?, ?, ?, ?)
            ''', (context, user_input, str(router_decision), final_response))
            conn.commit()

    def get_policy_state(self, context, user_input):
        """Gets the full state of a hash match."""
        context_hash = self.generate_hash(context, user_input)
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT cached_answer, route_weight, answer_weight, source FROM tool_policy 
                WHERE context_hash = ?
            ''', (context_hash,))
            row = cursor.fetchone()
            if row:
                return {
                    "cached_answer": row[0],
                    "route_weight": row[1],
                    "answer_weight": row[2],
                    "source": row[3]
                }
            return None

    def initialize_or_update_policy(self, context, user_input, answer, route_rw, answer_rw, source):
        """Creates or updates weights separately."""
        context_hash = self.generate_hash(context, user_input)
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO tool_policy (context_hash, context, raw_input, cached_answer, route_weight, answer_weight, source)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(context_hash) DO UPDATE SET
                route_weight = route_weight + ?,
                answer_weight = answer_weight + ?,
                cached_answer = CASE WHEN ? > 0 THEN ? ELSE cached_answer END,
                hit_count = hit_count + 1,
                last_used_at = CURRENT_TIMESTAMP
            ''', (context_hash, context, user_input, answer, 1.0 + route_rw, 1.0 + answer_rw, source, 
                  route_rw, answer_rw, answer_rw, answer))
            conn.commit()

    def log_intuition_hit(self, saved_time_ms, estimated_tokens):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE assistant_stats SET value = value + 1 WHERE metric = 'intuition_hits'")
            cursor.execute("UPDATE assistant_stats SET value = value + ? WHERE metric = 'saved_time_ms'", (saved_time_ms,))
            cursor.execute("UPDATE assistant_stats SET value = value + ? WHERE metric = 'saved_tokens'", (estimated_tokens,))
            conn.commit()

    def get_stats(self):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT metric, value FROM assistant_stats")
            return dict(cursor.fetchall())