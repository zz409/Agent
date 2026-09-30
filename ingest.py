import os
import db
import embedding

def read_file(file_path):
    with open(file_path,'r',encoding='utf-8') as f:
        return f.read()

def split_text(text):
    paragraphs=text.split('\n')
    chunks=[]
    for paragraph in paragraphs:
        paragraph=paragraph.strip()
        if paragraph:
            chunks.append(paragraph)
    return chunks

def ingest_file(file_path):
    content=read_file(file_path)
    chunks=split_text(content)
    source=os.path.basename(file_path)
    conn=db.get_connection()
    try:
        with conn.cursor() as cur:  
            for index,chunk in enumerate(chunks):
                vector=embedding.get_embedding(chunk)
                cur.execute(
                    """
                    INSERT INTO documents(content,source,chunk_index,embedding)
                    VALUES(%s,%s,%s,%s)
                    """,
                    (chunk,source,index,vector)
                )
            conn.commit()
    finally:
        conn.close()

if __name__ == "__main__":
    ingest_file("agent.txt")