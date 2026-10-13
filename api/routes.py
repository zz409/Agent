import fastapi
import memory.conversation_db
import api.schemas
import agent.agent

app=fastapi.FastAPI()

@app.post("/conversations")
def create_conversation():
    return {
        "id":memory.conversation_db.create_conversation()
    }

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

@app.get("/conversations/{conversation_id}/getmessage")
def get_message(conversation_id):
    return memory.conversation_db.load_events(conversation_id)

@app.get("/conversationlist")
def get_conversation_list():
    return memory.conversation_db.get_conversation_list()

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