from db.db import get_connection
from psycopg.types.json import Jsonb

def create_conversation(user_id,title=None):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO conversations(user_id,title)
                VALUES(%s,%s)
                RETURNING id
                """,
                (user_id,title)
            )
            return cur.fetchone()[0]

def append_event(
        conversation_id,
        role,
        content=None,
        tool_calls=None,
        tool_call_id=None
):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO conversation_events(
                    conversation_id,
                    role,
                    content,
                    tool_calls,
                    tool_call_id
                )
                VALUES(%s,%s,%s,%s,%s)
                RETURNING id
                """,
                (
                    conversation_id,
                    role,
                    content,
                    Jsonb(tool_calls) if tool_calls is not None else None,
                    tool_call_id,
                )
            )

            return cur.fetchone()[0]

def load_events(conversation_id):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT 
                    id,
                    role,
                    content,
                    tool_calls,
                    tool_call_id
                FROM conversation_events
                WHERE conversation_id =%s
                ORDER BY id ASC
                """,
                (conversation_id,)
            )

            rows=cur.fetchall()

    return [
        {
            "id":row[0],
            "role":row[1],
            "content":row[2],
            "tool_calls":row[3],
            "tool_call_id":row[4],
        }
        for row in rows
    ]

def get_conversation_list(user_id):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT id,title
                FROM conversations
                WHERE user_id=%s
                ORDER BY created_at DESC
                """,
                (user_id,)
            )

            rows=cur.fetchall()
            return[
                {
                    "id":row[0],
                    "title":row[1]
                }
                for row in rows
            ]

def delete_conversation(conversation_id,user_id):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                DELETE FROM conversations
                WHERE id=%s AND user_id=%s
                RETURNING id
                """,
                (conversation_id,user_id)
            )

            return cur.fetchone() is not None