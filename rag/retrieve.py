import db.db as db

from mcp_servers import embedding
from sentence_transformers import CrossEncoder


rerank_model = None


def get_rerank_model():
    global rerank_model

    if rerank_model is None:
        rerank_model = CrossEncoder(
            "BAAI/bge-reranker-v2-m3"
        )

    return rerank_model


# 向量召回
def retrieve_documents(question, top_k=20):

    question_vector = embedding.get_embedding(question)

    with db.get_connection() as conn:
        with conn.cursor() as cur:

            cur.execute(
                """
                SELECT
                    c.id,
                    c.content,
                    d.filename,
                    c.chunk_index,
                    c.embedding <=> %s::vector AS distance,
                    d.id AS document_id
                FROM documents c
                JOIN knowledge_documents d
                    ON c.document_id = d.id
                ORDER BY c.embedding <=> %s::vector
                LIMIT %s
                """,
                (
                    question_vector,
                    question_vector,
                    top_k
                )
            )

            rows = cur.fetchall()

    return [
        {
            "chunk_id": row[0],
            "content": row[1],
            "source": row[2],
            "chunk_index": row[3],
            "distance": float(row[4]),
            "document_id": row[5]
        }
        for row in rows
    ]


# 重排序
def rerank_documents(question, documents, top_k=5):

    if not documents:
        return []

    model = get_rerank_model()

    pairs = [
        [question, doc["content"]]
        for doc in documents
    ]

    scores = model.predict(pairs)

    results = []

    for doc, score in zip(documents, scores):

        results.append({
            **doc,
            "rerank_score": float(score)
        })

    results.sort(
        key=lambda x: x["rerank_score"],
        reverse=True
    )

    return results[:top_k]


# RAG 检索主函数
def search_documents(
    question,
    retrieve_top_k=20,
    rerank_top_k=5
):

    documents = retrieve_documents(
        question,
        retrieve_top_k
    )

    if not documents:
        return []

    return rerank_documents(
        question,
        documents,
        rerank_top_k
    )