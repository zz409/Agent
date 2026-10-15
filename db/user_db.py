from db.db import get_connection
from argon2 import PasswordHasher
from psycopg.errors import UniqueViolation
from argon2.exceptions import VerificationError,VerifyMismatchError

ph=PasswordHasher()

def register_user(username,password):
    password_hash=ph.hash(password)

    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO users(
                        username,
                        password_hash
                    )
                    VALUES (%s,%s)
                    RETURNING id
                    """,
                    (username,password_hash)
                )

                return cur.fetchone()[0]

    except UniqueViolation:
        raise ValueError("账号已存在")

def login_user(username,password):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT id,password_hash
                FROM users
                WHERE username=%s
                """,
                (username,)
            )

            row=cur.fetchone()

    if row is None:
        return None

    user_id,password_hash=row

    try:
        ph.verify(password_hash,password)
        return user_id

    except (VerifyMismatchError,VerificationError):
        return None
