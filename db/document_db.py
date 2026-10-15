import db.db

def get_document_by_hash(file_hash):
    with db.db.get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT id,filename
                FROM knowledge_documents
                WHERE file_hash=%s
                """,
                (file_hash,)
            )

            return cur.fetchone()

def save_document(
        filename,
        file_path,
        file_hash,
        file_size,
        chunks,
        embeddings
):
    if len(chunks)!=len(embeddings):
        raise ValueError("Chunk和Embedding数量不一致")

    with db.db.get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO knowledge_documents(
                    filename,
                    file_path,
                    file_hash,
                    file_size,
                    chunk_count
                )
                VALUES(%s,%s,%s,%s,%s)
                RETURNING id
                """,
                (
                    filename,
                    file_path,
                    file_hash,
                    file_size,
                    len(chunks)
                )
            )

            document_id=cur.fetchone()[0]

            for index,(chunk,vector) in enumerate(
                zip(chunks,embeddings)
            ):
                cur.execute(
                    """
                    INSERT INTO documents(
                        document_id,
                        content,
                        source,
                        chunk_index,
                        embedding
                    )
                    VALUES(
                        %s,%s,%s,%s,%s::vector
                    )
                    """,
                    (
                        document_id,
                        chunks,
                        filename,
                        index,
                        vector
                    )
                )

        conn.commit()

    return document_id

def list_documents():
    with db.db.get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT
                    id,
                    filename,
                    file_size,
                    chunk_count,
                    created_at
                FROM knowledge_documents
                ORDER BY created_at DESC,id DESC
                """
            )

            return cur.fetchall()

def get_document(document_id):
    with db.db.get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT
                    id,
                    filename,
                    file_path,
                    file_size,
                    chunk_count,
                    created_at
                FROM knowledge_documents
                WHERE id=%s
                """,
                (document_id,)
            )

            return cur.fetchone()

def get_document_chunks(document_id):
    with db.db.get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT
                    id,
                    chunk_index,
                    content
                FROM documents
                WHERE document_id=%s
                ORDER BY chunk_index
                """,
                (document_id,)
            )

            return cur.fetchall()

def delete_document(document_id):
    with db.db.get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                DELETE FROM knowledge_documents
                WHERE id=%s
                RETURNING id
                """,
                (document_id,)
            )

            row=cur.fetchone()

        conn.commit()

    return row is not None