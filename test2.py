import openai
import dotenv
import os

dotenv.load_dotenv()

api_key=os.getenv("API_KEY")
base_url=os.getenv("BASE_URL")
model=os.getenv("MODEL")

client = openai.OpenAI(
    api_key=api_key,
    base_url=base_url
)

messages=[]

while True:
    user_input=input("\nYou: ")

    if user_input=="quit":
        break

    messages.append({"role": "user", "content": user_input})

    stream=client.chat.completions.create(
        model=model,
        messages=messages,
    )

    for chunk in stream:
        print(chunk)