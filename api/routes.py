import fastapi
import memory.conversation_db
import db.user_db
import api.schemas
import agent.agent
from fastapi import UploadFile,File
from fastapi.responses import FileResponse

from pathlib import Path
from uuid import uuid4

import hashlib
import logging

import db.document_db
import rag.ingest

app=fastapi.FastAPI()


UPLOAD_DIR=Path("uploads/pdf").resolve()
UPLOAD_DIR.mkdir(parents=True,exist_ok=True)
MAX_FILE_SIZE=20*1024*1024

#注册
@app.post("/auth/register")
def register(request:api.schemas.UserRequest):
    try:
        user_id=db.user_db.register_user(
            request.username,
            request.password
        )
        return {"user_id":user_id}

    except ValueError as e:
        raise fastapi.HTTPException(
            status_code=400,
            detail=str(e)
        )

#登录
@app.post("/auth/login")
def login(request:api.schemas.UserRequest):
    user_id=db.user_db.login_user(
        request.username,
        request.password
    )

    if user_id is None:
        raise fastapi.HTTPException(
            status_code=401,
            detail="账号或密码错误"
        )

    return {"user_id":user_id}

#新建对话
@app.post("/conversations",status_code=201)
def create_conversation(
    request:api.schemas.CreateConversationRequest
):
    return {
        "id":memory.conversation_db.create_conversation(request.user_id)
    }

#新增对话内容
@app.post("/conversations/{conversation_id}/messages")
async def add_message(
    conversation_id,
    request:api.schemas.MessageRequest):
    return fastapi.responses.StreamingResponse(
        agent.agent.main(
            request.message,
            conversation_id
        ),
        media_type="text/event-stream",
        headers={
            "Cache-Control":"no-cache",
            "X-Accel-Buffering":"no"
        }
    )

#获取所有对话内容
@app.get("/conversations/{conversation_id}/getmessage")
def get_message(conversation_id):
    return memory.conversation_db.load_events(conversation_id)

#获取所有对话
@app.get("/conversationlist")
def get_conversation_list(user_id:int):
    return memory.conversation_db.get_conversation_list(user_id)

#删除对话
@app.delete(
    "/conversations/{conversation_id}",
    status_code=204
)
def delete_conversation(conversation_id:int):
    if not memory.conversation_db.delete_conversation(conversation_id):
        raise fastapi.HTTPException(
            status_code=404,
            detail="Conversation not found"
        )

@app.post("/documents",status_code=201)
def upload_document(file:UploadFile=File(...)):
    filename=Path(file.filename or "").name

    if not filename.lower().endswith(".pdf"):
        raise fastapi.HTTPException(
            status_code=400,
            detail="只支持PDF文件"
        )

    file_path=UPLOAD_DIR/f"{uuid4().hex}.pdf"
    sabed=False

    try:
        data=file.file.read(MAX_FILE_SIZE+1)

        if len(data)>MAX_FILE_SIZE:
            raise fastapi.HTTPException(
                status_code=413,
                detail="文件不能超过20MB"
            )

        if not data.startswith(b"%PDF-"):
            raise fastapi.HTTPException(
                status_code=400,
                detail="无效的PDF文件"
            )

        file_hash=hashlib.sha256(data).hexdigest()

        existing=db.document_db.get_document_by_hash(
            file_hash
        )

        if existing:
            raise fastapi.HTTPException(
                status_code=409,
                detail="该文档已存在"
            )

        file_path.write_bytes(data)

        result=rag.ingest.ingest_pdf(
            file_path=file_path,
            filename=filename,
            file_hash=file_hash,
            file_size=len(data)
        )

        saved=True

        return result

    except fastapi.HTTPException:
        raise

    except Exception:
        logging.exception("文档上传失败")

        raise fastapi.HTTPException(
            status_code=500,
            detail="文档处理失败"
        )

    finally:
        file.file.close()

        if not saved:
            file_path.unlink(missing_ok=True)

# 获取文档列表
@app.get("/documents")
def get_documents():

    rows = db.document_db.list_documents()

    return [
        {
            "id": row[0],
            "filename": row[1],
            "file_size": row[2],
            "chunk_count": row[3],
            "created_at": row[4]
        }
        for row in rows
    ]

# 获取文档详情
@app.get("/documents/{document_id}")
def get_document(document_id: int):

    row = db.document_db.get_document(document_id)

    if row is None:
        raise fastapi.HTTPException(
            status_code=404,
            detail="文档不存在"
        )

    chunks = db.document_db.get_document_chunks(
        document_id
    )

    return {
        "id": row[0],
        "filename": row[1],
        "file_size": row[3],
        "chunk_count": row[4],
        "created_at": row[5],
        "chunks": [
            {
                "id": chunk[0],
                "chunk_index": chunk[1],
                "content": chunk[2]
            }
            for chunk in chunks
        ]
    }

# 查看原始PDF
@app.get("/documents/{document_id}/file")
def get_document_file(document_id: int):

    row = db.document_db.get_document(document_id)

    if row is None:
        raise fastapi.HTTPException(
            status_code=404,
            detail="文档不存在"
        )

    file_path = Path(row[2]).resolve()

    if not file_path.is_relative_to(UPLOAD_DIR):
        raise fastapi.HTTPException(
            status_code=400,
            detail="文件路径无效"
        )

    if not file_path.is_file():
        raise fastapi.HTTPException(
            status_code=404,
            detail="PDF文件不存在"
        )

    return FileResponse(
        path=file_path,
        media_type="application/pdf",
        filename=row[1],
        content_disposition_type="inline"
    )

# 删除文档
@app.delete("/documents/{document_id}")
def delete_document(document_id: int):

    row = db.document_db.get_document(document_id)

    if row is None:
        raise fastapi.HTTPException(
            status_code=404,
            detail="文档不存在"
        )

    file_path = Path(row[2]).resolve()

    if not file_path.is_relative_to(UPLOAD_DIR):
        raise fastapi.HTTPException(
            status_code=400,
            detail="文件路径无效"
        )

    success = db.document_db.delete_document(
        document_id
    )

    if not success:
        raise fastapi.HTTPException(
            status_code=404,
            detail="文档不存在"
        )

    try:
        file_path.unlink(missing_ok=True)
    except OSError:
        logging.exception(
            "数据库记录已删除，但PDF文件清理失败"
        )

    return {
        "success": True,
        "document_id": document_id
    }