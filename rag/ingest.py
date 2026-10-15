from rag.pdf_parser import process_pdf
from mcp_servers import embedding
from db import document_db

def ingest_pdf(
        file_path,
        filename,
        file_hash,
        file_size
):
    chunks=process_pdf(file_path)

    embeddings=[]
    for chunk in chunks:
        vector=embedding.get_embedding(chunk)

        embeddings.append(vector)

    document_id=document_id.save_document(
        filename=filename,
        file_path=str(file_path),
        file_hash=file_hash,
        file_size=file_size,
        chunks=chunks,
        embeddings=embeddings
    )

    return {
        "document_id":document_id,
        "filename":filename,
        "chunk_count":len(chunks)
    }