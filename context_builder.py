from memory.summary_db import load_latest_summary,load_recent_events

def build_message(conversation_id,system_prompt):
    messages=[
        {
            "role":"system",
            "content":system_prompt
        }
    ]

    summary=load_latest_summary(conversation_id)
    last_event_id=0
    if summary:
        messages.append({
            "role":"system",
            "content":f"历史对话摘要:\n{summary['summary']}"
        })

        last_event_id=summary["last_event_id"]

    events=load_recent_events(
        conversation_id,
        last_event_id
    )

    for event in events:
        message={
            "role":event["role"]
        }

        if event["content"] is not None:
            message["content"]=event["content"]

        if event["tool_calls"] is not None:
            message["tool_calls"]=event["tool_calls"]

        if event["tool_call_id"]:
            message["tool_call_id"]=event["tool_call_id"]

        messages.append(message)

    return messages