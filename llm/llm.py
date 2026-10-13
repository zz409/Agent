import openai
import os
import dotenv

dotenv.load_dotenv()
deepseek_api_key=os.getenv("DEEPSEEK_API_KEY")

def get_client():
    return openai.AsyncOpenAI(
        api_key=deepseek_api_key,
        base_url="https://api.deepseek.com"
    )

def get_response(client,prompt,model,tools):
    response=client.chat.completions.create(
        model=model,
        messages=prompt,
        tools=tools
    )

    return response