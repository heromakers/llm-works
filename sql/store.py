import json, os, requests
import chromadb
from chromadb.api.types import Documents, Embeddings
from chromadb.config import Settings # , embedding_function


# ==== 0) 설정 ====
OLLAMA_HOST = "http://localhost:11434"
GEN_MODEL = "gpt-oss"     # 또는 "llama3.1:8b-instruct"
EMB_MODEL = "nomic-embed-text"

# ==== 1) 임베딩 함수: Ollama로 호출 ====
def ollama_embed(texts):
    # texts: list[str]
    response = requests.post(f"{OLLAMA_HOST}/api/embeddings", json={"model": EMB_MODEL, "input": texts})
    response.raise_for_status()
    data = response.json()

    # Ollama는 단건/복수 모두 "embedding" 또는 "embeddings" 형태로 반환
    if isinstance(data, dict) and "embedding" in data:
        return [data["embedding"]]
    elif isinstance(data, dict) and "embeddings" in data:
        return [e["embedding"] for e in data["embeddings"]]
    else:
        # 일부 버전은 {"data":[{"embedding":[...]}]} 형태
        if "data" in data and len(data["data"])>0 and "embedding" in data["data"][0]:
            return [d["embedding"] for d in data["data"]]
        raise RuntimeError("Unexpected embedding response")

class OllamaEmbeddingFunction:
    """Chroma가 요구하는 규격: __call__ + name()"""
    def __init__(self, host: str, model: str):
        self.host = host
        self.model = model
    def __call__(self, texts: Documents) -> Embeddings:
        return ollama_embed(texts)       # 위 함수 호출
    def name(self) -> str:
        # 동일 컬렉션에 같은 EF인지 비교할 때 쓰임 → 모델명 포함 권장
        return f"ollama::{self.model}"

ef = OllamaEmbeddingFunction(OLLAMA_HOST, EMB_MODEL)

# ==== 2) Chroma 초기화 ====
chroma_client = chromadb.Client(Settings(persist_directory="/home/dev-llm/works/chroma_store", is_persistent=True))
schema_collection = chroma_client.get_or_create_collection(
    name="schema_docs",
    embedding_function=ef
)

def index_schema_into_chroma():
    schema_collection.delete(where={})  # 전체 리셋(초기화 용)
    docs = [
        {
            "table": "t_user",
            "name": "구매자 정보",
            "schema": """
user_id int(11) unsigned NOT NULL AUTO_INCREMENT COMMENT 'user key',
user_name varchar(30)  NOT NULL COMMENT '구매자 이름',
phone varchar(15)  NOT NULL COMMENT '전화번호',
email varchar(120)  NOT NULL COMMENT '이메일',
PRIMARY KEY (user_id)
            """
        },
        {
            "table": "t_seller",
            "name": "판매자` 정보",
            "schema": """
seller_id int(11) unsigned NOT NULL AUTO_INCREMENT COMMENT 'seller key',
seller_name varchar(90)  NOT NULL COMMENT '판매자 이름',
phone varchar(15)  NOT NULL COMMENT '전화번호',
email varchar(120)  NOT NULL COMMENT '이메일',
PRIMARY KEY (seller_id)
            """
        },
        {
            "table": "t_item",
            "name": "상품 정보",
            "schema": """
item_id int(11) unsigned NOT NULL AUTO_INCREMENT COMMENT 'item key',
item_kind varchar(30) DEFAULT NULL,
item_name varchar(90)  NOT NULL COMMENT '상품 이름',
seller_id int(11) unsigned NOT NULL COMMENT '판매자 key',
price int(11) unsigned NOT NULL DEFAULT 0 COMMENT '가격',
PRIMARY KEY (item_id),
CONSTRAINT t_item_t_seller_FK FOREIGN KEY (seller_id) REFERENCES t_seller (seller_id)
            """
        },
        {
            "table": "t_sales",
            "name": "판매 정보",
            "schema": """
sales_id int(11) unsigned NOT NULL AUTO_INCREMENT COMMENT 'sales key',
item_id int(11) unsigned NOT NULL COMMENT 'item key',
buyer_id int(11) unsigned NOT NULL COMMENT 'user key',
quantity int(11) unsigned NOT NULL DEFAULT 0 COMMENT '수량',
discount int(11) unsigned NOT NULL DEFAULT 0 COMMENT '할인액',
total_amount int(11) unsigned NOT NULL DEFAULT 0 COMMENT '총 금액',
sales_at datetime DEFAULT NULL COMMENT '판매 일시',
PRIMARY KEY (sales_id),
CONSTRAINT t_sales_t_buyer_FK FOREIGN KEY (buyer_id) REFERENCES t_user (user_id),
CONSTRAINT t_sales_t_item_FK FOREIGN KEY (item_id) REFERENCES t_item (item_id)
            """
        }
    ]

    ids = [f"tbl:{d['table']}" for d in docs]
    metadatas = [{"table": d["table"], "name": d["name"]} for d in docs]
    texts = [d["schema"] for d in docs]
    schema_collection.add(ids=ids, documents=texts, metadatas=metadatas)

if __name__ == "__main__":
    index_schema_into_chroma()
