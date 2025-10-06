from fastapi import FastAPI
from sql.view import router as ml2sql_router

# FastAPI 인스턴스 생성
app = FastAPI()

@app.get("/")
def read_root():
    return {"Hello": "World"}

app.include_router(ml2sql_router)