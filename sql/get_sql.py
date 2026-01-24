
# ==== 4) NL → 관련 스키마 검색 ====
def retrieve_related_schema(nl_query: str, top_k=5):
    res = schema_collection.query(query_texts=[nl_query], n_results=top_k)
    docs = res.get("documents", [[]])[0]
    metas = res.get("metadatas", [[]])[0]
    return list(zip(docs, metas))

# ==== 5) 프롬프트 템플릿 ====
SYSTEM_PROMPT = """당신은 SQL 전문가입니다.
반드시 아래 규칙을 지키세요.
- 제공된 스키마와 컬럼만 사용하세요. 존재하지 않는 테이블/컬럼은 만들지 마세요.
- DML/DCL/DDL 금지(INSERT/UPDATE/DELETE/CREATE/ALTER/GRANT 등). 오직 SELECT/CTE만.
- 결과 행수는 기본적으로 200 이내로 제한하세요.
- 최종 답변은 오직 SQL만 ```sql ... ``` 코드블록 형태로 출력하세요. 자연어 설명 금지.
"""

USER_PROMPT_TMPL = """자연어 질의:
{question}

사용 가능한 스키마:
{schema_snippets}

요구사항:
- 질의 의도에 맞는 단일 SELECT 문을 생성
- 필요한 경우 CTE(with) 사용 가능
- LIMIT이 없다면 LIMIT 200 추가
- 날짜/시간 컬럼이 있으면 최신순 정렬 고려
- 한국어 컬럼명/테이블명을 그대로 사용

SQL만 ```sql ... ``` 형태로 출력:
"""

def build_prompt(nl_query: str, related_schema: list):
    snippets = "\n\n".join(d for d,_ in related_schema)
    return SYSTEM_PROMPT, USER_PROMPT_TMPL.format(question=nl_query, schema_snippets=snippets)

# ==== 6) LLM 호출 ====
def ollama_generate(model: str, system: str, user: str):
    payload = {
        "model": model,
        "messages": [
            {"role":"system","content":system},
            {"role":"user","content":user}
        ],
        "options": {
            "temperature": 0.2,
            "num_ctx": 4096
        }
    }
    r = requests.post(f"{OLLAMA_HOST}/api/chat", json=payload, timeout=120)
    r.raise_for_status()
    data = r.json()
    # Ollama chat API는 message.content에 최종 텍스트
    if "message" in data and "content" in data["message"]:
        return data["message"]["content"]
    # 스트리밍 비사용 시 위 형태. 버전에 따라 다르면 적절히 파싱
    if "content" in data:
        return data["content"]
    raise RuntimeError("Unexpected chat response")

# ==== 7) SQL 안전 검사 ====
ALLOWED = {"select","with","where","group","having","order","limit","offset","from","join","left","right","inner","outer","on","and","or","as","distinct","union","union all"}

def sanitize_sql(sql: str) -> str:
    # ```sql ... ``` 블록만 추출
    m = re.search(r"```sql\s*(.*?)\s*```", sql, flags=re.S|re.I)
    if m: sql = m.group(1).strip()
    # 멀티 스테이트먼트 금지
    if ";" in sql.strip().rstrip(";"):
        raise ValueError("Multiple statements are not allowed.")
    # 금지 키워드(간단 체크)
    lowered = re.sub(r"\s+"," ",sql.lower())
    forbidden = ["insert","update","delete","drop","alter","create","grant","revoke","truncate","attach","pragma"]
    if any(f in lowered for f in forbidden):
        raise ValueError("Only SELECT queries are allowed.")
    # 토큰 키워드 체크(관대한 편)
    # (실서비스에선 SQL 파서로 더 엄격히 제어)
    if "select" not in lowered and "with" not in lowered:
        raise ValueError("No SELECT/CTE found.")
    # LIMIT 강제
    if " limit " not in lowered:
        sql += "\nLIMIT 200"
    return sql.strip()

# ==== 8) 실행기 (SQLite 예시) ====
def run_sqlite(sql: str, db_path=DB_PATH, max_rows=1000):
    con = sqlite3.connect(db_path, timeout=5)
    cur = con.cursor()
    cur.execute(sql)
    cols = [d[0] for d in cur.description] if cur.description else []
    rows = cur.fetchall()
    con.close()
    if len(rows) > max_rows:
        rows = rows[:max_rows]
    return cols, rows

class AskBody(BaseModel):
    question: str

@app.post("/ask")
def ask_sql(body: AskBody):
    # 1) 관련 스키마 RAG
    related = retrieve_related_schema(body.question, top_k=5)
    # 2) 프롬프트 구성
    sys_p, user_p = build_prompt(body.question, related)
    # 3) LLM으로 SQL 생성
    raw = ollama_generate(GEN_MODEL, sys_p, user_p)
    try:
        sql = sanitize_sql(raw)
    except Exception as e:
        return {"error": f"생성된 SQL 거부: {e}", "raw": raw}
    # 4) 실행 (DB종류별로 분기)
    try:
        cols, rows = run_sqlite(sql)
        return {"sql": sql, "columns": cols, "rows": rows[:200]}
    except Exception as e:
        return {"error": f"SQL 실행 오류: {e}", "sql": sql, "raw": raw}
