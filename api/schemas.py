import pydantic

class ChatRequest(pydantic.BaseModel):
    conversation_id:str
    message:str

class Chatresponse(pydantic.BaseModel):
    conversation_id:str
    response:str

class MessageRequest(pydantic.BaseModel):
    message:str

class UserRequest(pydantic.BaseModel):
    username:str
    password:str

class CreateConversationRequest(pydantic.BaseModel):
    user_id:int