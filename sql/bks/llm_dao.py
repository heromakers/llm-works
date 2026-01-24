# FAISS, 임베딩, Ollama 연동 샘플

from sentence_transformers import SentenceTransformer
import requests
from chromadb import Client
from chromadb.config import Settings

# 1. 테이블 명세 예시
table_specs = [
    """
t_user (
  `user_id` int(11) unsigned NOT NULL AUTO_INCREMENT COMMENT 'user key',
  `user_name` varchar(30)  NOT NULL COMMENT '구매자 이름',
  `phone` varchar(15)  NOT NULL COMMENT '전화번호',
  `email` varchar(120)  NOT NULL COMMENT '이메일',
  PRIMARY KEY (`user_id`) USING BTREE
) COMMENT '구매자 정보';
    """,
    """
t_seller (
  `seller_id` int(11) unsigned NOT NULL AUTO_INCREMENT COMMENT 'seller key',
  `seller_name` varchar(90)  NOT NULL COMMENT '판매자 이름',
  `phone` varchar(15)  NOT NULL COMMENT '전화번호',
  `email` varchar(120)  NOT NULL COMMENT '이메일',
  PRIMARY KEY (`seller_id`) USING BTREE
) COMMENT '판매자 정보';
    """,
    """
t_item (
  `item_id` int(11) unsigned NOT NULL AUTO_INCREMENT COMMENT 'item key',
  `item_kind` varchar(30) DEFAULT NULL,
  `item_name` varchar(90)  NOT NULL COMMENT '상품 이름',
  `seller_id` int(11) unsigned NOT NULL COMMENT '판매자 key',
  `price` int(11) unsigned NOT NULL DEFAULT 0 COMMENT '가격',
  PRIMARY KEY (`item_id`) USING BTREE,
  KEY `t_item_t_seller_FK` (`seller_id`),
  CONSTRAINT `t_item_t_seller_FK` FOREIGN KEY (`seller_id`) REFERENCES `t_seller` (`seller_id`)
) COMMENT '상품 정보';
    """,
    """
t_sales (
  `sales_id` int(11) unsigned NOT NULL AUTO_INCREMENT COMMENT 'sales key',
  `item_id` int(11) unsigned NOT NULL COMMENT 'item key',
  `buyer_id` int(11) unsigned NOT NULL COMMENT 'user key',
  `quantity` int(11) unsigned NOT NULL DEFAULT 0 COMMENT '수량',
  `discount` int(11) unsigned NOT NULL DEFAULT 0 COMMENT '할인액',
  `total_amount` int(11) unsigned NOT NULL DEFAULT 0 COMMENT '총 금액',
  `sales_at` datetime DEFAULT NULL COMMENT '판매 일시',
  PRIMARY KEY (`sales_id`) USING BTREE,
  KEY `t_sales_t_item_FK` (`item_id`),
  KEY `t_sales_t_buyer_FK` (`buyer_id`),
  CONSTRAINT `t_sales_t_buyer_FK` FOREIGN KEY (`buyer_id`) REFERENCES `t_user` (`user_id`),
  CONSTRAINT `t_sales_t_item_FK` FOREIGN KEY (`item_id`) REFERENCES `t_item` (`item_id`)
) COMMENT '판매 정보';
    """
]

def build_vector_store():
    model = SentenceTransformer('all-MiniLM-L6-v2')

    table_embeddings = model.encode(table_specs)

    chroma_client = Client(Settings(persist_directory="/home/dev-llm/works/chroma_store"))

    # 3. Chroma 벡터스토어에 저장
    table_collection = chroma_client.create_collection(name="table_specs")
    for i, spec in enumerate(table_specs):
        table_collection.add(
            documents=[spec],
            embeddings=[table_embeddings[i].tolist()],
            ids=[str(i)]
        )

# 5. Ollama(CodeLlama)로 자연어→SQL 변환 예시
def generate_sql_with_ollama(nl_query, table_specs):
    prompt = f"""
    테이블 명세:
    {table_specs}
    자연어 질의: {nl_query}
    SQL로 변환:
    """
    # Ollama API 예시 (로컬에서 ollama serve 중이어야 함)
    response = requests.post(
        "http://localhost:11434/api/generate",
        json={
            "model": "gpt-oss", # "codellama:34b",
            "prompt": prompt,
            "stream": False
        }
    )
    print("Ollama response : ", response)
    result = response.json()
    return result.get("response", "")

# 사용 예시
if __name__ == "__main__":
    nl_query = "판매자별 일간 판매 집계를 보여줘."
    sql = generate_sql_with_ollama(nl_query, table_specs)
    print("생성된 SQL:", sql)

# def build_vector_store():
#     """벡터 스토어 생성"""
#     embeddings = OpenAIEmbeddings(openai_api