from sentence_transformers import SentenceTransformer
# import requests
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
) 
    """,
    """
t_seller (
  `seller_id` int(11) unsigned NOT NULL AUTO_INCREMENT COMMENT 'seller key',
  `seller_name` varchar(90)  NOT NULL COMMENT '판매자 이름',
  `phone` varchar(15)  NOT NULL COMMENT '전화번호',
  `email` varchar(120)  NOT NULL COMMENT '이메일',
  PRIMARY KEY (`seller_id`) USING BTREE
) 
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
)
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
)
    """
]

example_queries = [
    {
        "indeed": "모든 판매 내역을 조회하는 SQL 쿼리",
        "query": """
        SELECT sls.*
            ,usr.user_name
            ,itm.item_name
            ,itm.price
            ,slr.seller_name
        FROM t_sales sls
        JOIN t_user usr ON usr.user_id = sls.buyer_id
        JOIN t_item itm ON itm.item_id = sls.item_id
        JOIN t_seller slr ON slr.seller_id = itm.seller_id
        ORDER BY sls.sales_id DESC
        """
    }, 
    {
        "indeed": "일자별로 판매 상품 개수, 할인 금액, 총 금액을 집계하는 SQL 쿼리",
        "query": """
        SELECT mt.sales_date
            ,SUM(mt.quantity) as quantity
            ,SUM(mt.discount) as discount
            ,SUM(mt.total_amount) as total_amount
        FROM (
            SELECT sls.*
                ,DATE(sls.sales_at) as sales_date
                ,usr.user_name
                ,itm.item_name
                ,itm.price
                ,slr.seller_name
            FROM t_sales sls
            JOIN t_user usr ON usr.user_id = sls.buyer_id
            JOIN t_item itm ON itm.item_id = sls.item_id
            JOIN t_seller slr ON slr.seller_id = itm.seller_id
            {where_sql}
        ) mt
        GROUP BY mt.sales_date
        ORDER BY mt.sales_date
        """
    }
]

model = SentenceTransformer('all-MiniLM-L6-v2')

chroma_client = Client(Settings(persist_directory="/home/dev-llm/works/chroma_store"))

def build_vector_store(table_specs, example_queries=None):
    # 3. 테이블 명세 임베딩
    table_embeddings = model.encode(table_specs)

    # query_embeddings = model.encode([q["query"] for q in example_queries])

    table_collection = chroma_client.create_collection(name="table_specs")
    for i, spec in enumerate(table_specs):
        table_collection.add(
            documents=[spec],
            embeddings=[table_embeddings[i].tolist()],
            ids=[str(i)]
        )

    # # 예제 쿼리 임베딩 및 저장
    # if example_queries:
    #     query_embeddings = model.encode(example_queries)
    #     for i, query in enumerate(example_queries):
    #         collection.add(
    #             documents=[query],
    #             embeddings=[query_embeddings[i].tolist()],
    #             ids=[f"query_{i}"]
    #         )
    # return collection


if __name__ == "__main__":
    build_vector_store(table_specs)