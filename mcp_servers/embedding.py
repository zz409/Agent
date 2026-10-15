import os
import dotenv
from llama_index.embeddings.dashscope import DashScopeEmbedding

dotenv.load_dotenv()

embed_model=DashScopeEmbedding(
    model_name="text-embedding-v4",
    api_key=os.getenv("DASHSCOPE_API_KEY")
)

def get_embedding(text):
    return embed_model.get_text_embedding(text)