from fastapi import FastAPI
from fastapi.templating import Jinja2Templates
from sql.view import router as ml2sql_router

# FastAPI 인스턴스 생성
app = FastAPI()

templates = Jinja2Templates(directory="templates")

@app.get("/")
def home():
    return templates.TemplateResponse("index.html", {"request": {}})

@app.get("/sql")
def home():
    return templates.TemplateResponse("sql.html", {"request": {}})

app.include_router(ml2sql_router)