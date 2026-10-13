import json
import uuid
from pathlib import Path


DATA_DIR=Path("data/conversations")
DATA_DIR.mkdir(parents=True,exist_ok=True)


def create_conversation():
    conversation_id=str(uuid.uuid4())

    conversation={
        "conversation_id":conversation_id,
        "messages":[]
    }

    save_conversation(conversation)
    return conversation

def save_conversation(conversation):
    path=DATA_DIR/f"{conversation["conversation_id"]}.json"

    with open(path,"w",encoding="utf-8") as f:
        json.dump(
            conversation,
            f,
            ensure_ascii=False,
            indent=2
        )

def load_conversation(conversation):
    path=DATA_DIR/f"{conversation["conversation_id"]}.json"

    with open(path,"r",encoding="utf-8") as f:
        return json.load(f)

def add_message(conversation,message):
    conversation["messages"].append(message)
    save_conversation(conversation)

def list_conversations():
    return[
        path.stem
        for path in DATA_DIR.glob("*.json")
    ]

def select_conversation():
    conversations=list_conversations()
    print("0.创建新对话")
    for i,conversation_id in enumerate(conversations,1):
        print(f"{i}.{conversation_id}")

    choice=int(input("请选择对话:"))

    if choice==0:
        return create_conversation()

    else:
        conversation={"conversation_id":conversations[choice-1]}
        return load_conversation(conversation)