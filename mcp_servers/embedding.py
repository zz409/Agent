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

if __name__=="__main__":
    vector=get_embedding("苹果是一种水果")
    print("向量：")
    print(vector)
    print("向量维度：")
    print(len(vector))