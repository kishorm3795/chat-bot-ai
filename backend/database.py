"""
Database module for AI Student Chatbot
Stores auto-replies, conversation history, feedback, platform config, and user settings
"""

import sqlite3
import json
from datetime import datetime
from typing import List, Dict, Optional
import os


class Database:
    """SQLite database handler for AI Student Chatbot"""

    def __init__(self, db_path: str = "chatbot.db"):
        self.db_path = db_path
        self._init_database()

    def _init_database(self):
        """Initialize all database tables"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Settings table (single row - user's persona/tone config)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS settings (
                id INTEGER PRIMARY KEY,
                user_name TEXT DEFAULT 'Me',
                tone TEXT DEFAULT 'casual',
                is_busy INTEGER DEFAULT 0,
                custom_away_message TEXT DEFAULT '',
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Insert default settings row if empty
        cursor.execute("SELECT COUNT(*) FROM settings")
        if cursor.fetchone()[0] == 0:
            cursor.execute("""
                INSERT INTO settings (user_name, tone, is_busy, custom_away_message)
                VALUES ('Me', 'casual', 0, "I'm busy right now, will reply soon!")
            """)

        # Platform status table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS platforms (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                label TEXT NOT NULL,
                icon TEXT DEFAULT '💬',
                is_active INTEGER DEFAULT 1,
                color TEXT DEFAULT '#25D366',
                reply_count INTEGER DEFAULT 0
            )
        """)

        # Insert default platforms
        cursor.execute("SELECT COUNT(*) FROM platforms")
        if cursor.fetchone()[0] == 0:
            platforms = [
                ("whatsapp", "WhatsApp", "💬", 1, "#25D366"),
                ("instagram", "Instagram", "📸", 1, "#E1306C"),
                ("telegram", "Telegram", "✈️", 1, "#0088cc"),
                ("sms", "SMS", "📱", 1, "#34C759"),
                ("discord", "Discord", "🎮", 0, "#5865F2"),
                ("facebook", "Facebook", "👥", 0, "#1877F2"),
            ]
            cursor.executemany("""
                INSERT OR IGNORE INTO platforms (name, label, icon, is_active, color)
                VALUES (?, ?, ?, ?, ?)
            """, platforms)

        # Auto-replies log table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS auto_replies (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                platform TEXT NOT NULL,
                sender_name TEXT DEFAULT 'Friend',
                incoming_message TEXT NOT NULL,
                ai_reply TEXT NOT NULL,
                reply_mode TEXT DEFAULT 'ai',
                was_sent INTEGER DEFAULT 0,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Conversation history table (for RAG pipeline)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS conversations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Create index for faster session lookups
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_conversations_session 
            ON conversations(session_id, timestamp)
        """)

        # Feedback table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS feedback (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                message TEXT,
                rating INTEGER NOT NULL,
                session_id TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)

        conn.commit()
        conn.close()

    # ─── Settings ────────────────────────────────────────────────────────────

    def get_settings(self) -> Dict:
        """Get user personality/tone settings"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM settings WHERE id = 1")
        row = cursor.fetchone()
        conn.close()
        if row:
            return dict(row)
        return {
            "user_name": "Me",
            "tone": "casual",
            "is_busy": 0,
            "custom_away_message": "I'm busy right now, will reply soon!"
        }

    def update_settings(self, **kwargs) -> Dict:
        """Update user settings"""
        allowed = {"user_name", "tone", "is_busy", "custom_away_message"}
        updates = {k: v for k, v in kwargs.items() if k in allowed}
        if not updates:
            return self.get_settings()

        set_clause = ", ".join(f"{k} = ?" for k in updates)
        values = list(updates.values())

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(
            f"UPDATE settings SET {set_clause}, updated_at = CURRENT_TIMESTAMP WHERE id = 1",
            values
        )
        conn.commit()
        conn.close()
        return self.get_settings()

    def toggle_busy(self) -> bool:
        """Toggle busy mode on/off. Returns new state."""
        settings = self.get_settings()
        new_state = 0 if settings.get("is_busy", 0) else 1
        self.update_settings(is_busy=new_state)
        return bool(new_state)

    # ─── Platforms ───────────────────────────────────────────────────────────

    def get_platforms(self) -> List[Dict]:
        """Get all platforms with reply counts"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # Get platforms with live reply counts
        cursor.execute("""
            SELECT p.name, p.label, p.icon, p.is_active, p.color,
                   COUNT(ar.id) as reply_count
            FROM platforms p
            LEFT JOIN auto_replies ar ON ar.platform = p.name
            GROUP BY p.name
            ORDER BY p.id
        """)
        rows = cursor.fetchall()
        conn.close()
        return [dict(row) for row in rows]

    def toggle_platform(self, name: str) -> bool:
        """Toggle a platform active/inactive"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE platforms SET is_active = NOT is_active WHERE name = ?",
            (name,)
        )
        conn.commit()
        cursor.execute("SELECT is_active FROM platforms WHERE name = ?", (name,))
        result = cursor.fetchone()
        conn.close()
        return bool(result[0]) if result else False

    # ─── Auto Replies ─────────────────────────────────────────────────────────

    def save_reply(
        self,
        platform: str,
        incoming_message: str,
        ai_reply: str,
        sender_name: str = "Friend",
        reply_mode: str = "ai"
    ) -> int:
        """Save a generated auto-reply to the log"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO auto_replies (platform, sender_name, incoming_message, ai_reply, reply_mode)
            VALUES (?, ?, ?, ?, ?)
        """, (platform, sender_name, incoming_message, ai_reply, reply_mode))
        reply_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return reply_id

    def mark_sent(self, reply_id: int):
        """Mark a reply as sent"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("UPDATE auto_replies SET was_sent = 1 WHERE id = ?", (reply_id,))
        conn.commit()
        conn.close()

    def get_reply_history(self, limit: int = 50, platform: str = None) -> List[Dict]:
        """Get history of all auto-generated replies"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        if platform:
            cursor.execute("""
                SELECT * FROM auto_replies WHERE platform = ?
                ORDER BY timestamp DESC LIMIT ?
            """, (platform, limit))
        else:
            cursor.execute("""
                SELECT * FROM auto_replies
                ORDER BY timestamp DESC LIMIT ?
            """, (limit,))

        rows = cursor.fetchall()
        conn.close()
        return [dict(row) for row in rows]

    def delete_reply(self, reply_id: int):
        """Delete a specific reply from history"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM auto_replies WHERE id = ?", (reply_id,))
        conn.commit()
        conn.close()

    def clear_history(self):
        """Clear all reply history"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM auto_replies")
        conn.commit()
        conn.close()

    # ─── Conversation History (for RAG) ──────────────────────────────────────

    def save_conversation_message(
        self,
        session_id: str,
        role: str,
        content: str
    ) -> int:
        """Save a message to conversation history"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO conversations (session_id, role, content)
            VALUES (?, ?, ?)
        """, (session_id, role, content))
        message_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return message_id

    def get_conversation_history(
        self,
        session_id: str,
        limit: int = 20
    ) -> List[Dict]:
        """Get conversation history for a session"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT role, content, timestamp
            FROM conversations
            WHERE session_id = ?
            ORDER BY timestamp DESC
            LIMIT ?
        """, (session_id, limit))
        
        rows = cursor.fetchall()
        conn.close()
        
        # Reverse to get chronological order
        history = [dict(row) for row in rows]
        return list(reversed(history))

    def clear_conversation(self, session_id: str):
        """Clear conversation history for a session"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM conversations WHERE session_id = ?", (session_id,))
        conn.commit()
        conn.close()

    # ─── Feedback ────────────────────────────────────────────────────────────

    def save_feedback(
        self,
        message: str,
        rating: int,
        session_id: str = None
    ) -> int:
        """Save user feedback"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO feedback (message, rating, session_id)
            VALUES (?, ?, ?)
        """, (message, rating, session_id))
        feedback_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return feedback_id

    def get_feedback_stats(self) -> Dict:
        """Get feedback statistics"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("SELECT COUNT(*) FROM feedback")
        total = cursor.fetchone()[0]

        cursor.execute("SELECT AVG(rating) FROM feedback")
        avg_rating = cursor.fetchone()[0] or 0

        cursor.execute("""
            SELECT rating, COUNT(*) as count
            FROM feedback
            GROUP BY rating
            ORDER BY rating
        """)
        by_rating = {row[0]: row[1] for row in cursor.fetchall()}

        conn.close()
        
        return {
            "total": total,
            "average_rating": round(avg_rating, 2),
            "by_rating": by_rating
        }

    # ─── Stats ────────────────────────────────────────────────────────────

    def get_stats(self) -> Dict:
        """Get usage statistics"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("SELECT COUNT(*) FROM auto_replies")
        total = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM auto_replies WHERE was_sent = 1")
        sent = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM auto_replies WHERE DATE(timestamp) = DATE('now')")
        today = cursor.fetchone()[0]

        cursor.execute("""
            SELECT platform, COUNT(*) as count
            FROM auto_replies
            GROUP BY platform
            ORDER BY count DESC
        """)
        by_platform = {row[0]: row[1] for row in cursor.fetchall()}

        # Get conversation stats
        cursor.execute("SELECT COUNT(DISTINCT session_id) FROM conversations")
        total_sessions = cursor.fetchone()[0]

        conn.close()
        return {
            "total_replies": total,
            "sent_replies": sent,
            "today_replies": today,
            "total_sessions": total_sessions,
            "by_platform": by_platform
        }

