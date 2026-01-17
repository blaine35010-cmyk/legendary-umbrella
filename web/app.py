from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import Optional
from agent.ask import ask

app = FastAPI()
app.mount("/static", StaticFiles(directory="web/static"), name="static")


class Query(BaseModel):
    question: str
    collection: Optional[str] = "court-files"
    top_k: Optional[int] = 5
    format: Optional[str] = "compact"
    path_contains: Optional[str] = None


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/ask")
def do_ask(q: Query):
    return {"answer": ask(q.question, collection=q.collection or "court-files", top_k=q.top_k or 5, format_mode=q.format or "compact", path_contains=q.path_contains)}


@app.get("/", response_class=HTMLResponse)
def ui_index(request: Request):
    with open("web/static/index.html", "r", encoding="utf-8") as f:
        return HTMLResponse(f.read())
