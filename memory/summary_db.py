from db.db import get_connection

def save_summary(
        conversation_id,
        summary,
        last_event_id
    ):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO conversation_summaries(
                    conversation_id,
                    summary,
                    last_event_id
                )
                VALUES(%s,%s,%s)
                RETURNING id
                """,
                (
                    conversation_id,
                    summary,
                    last_event_id
                )
            )

            return cur.fetchone()[0]

def load_latest_summary(conversation_id):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT
                    summary,
                    last_event_id
                FROM conversation_summaries
                WHERE conversation_id=%s
                ORDER BY id DESC
                LIMIT 1
                """,
                (conversation_id,)
            )

            row=cur.fetchone()

    if row is None:
        return {
            "summary":"",
            "last_event_id":0
        }

    return {
        "summary":row[0],
        "last_event_id":row[1]
    }

def load_recent_events(conversation_id,last_event_id=0):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT
                    id,
                    role,
                    content,
                    tool_calls,
                    tool_call_id,
                    tool_name
                FROM conversation_events
                WHERE conversation_id=%s
                  AND id>%s
                ORDER BY id ASC
                """,
                (conversation_id,last_event_id)
            )

            rows=cur.fetchall()

    return [
        {
            "id":row[0],
            "role":row[1],
            "content":row[2],
            "tool_calls":row[3],
            "tool_call_id":row[4],
            "tool_name":row[5]
        }
        for row in rows
    ]