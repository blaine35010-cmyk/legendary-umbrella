from fastapi import FastAPI, Request, BackgroundTasks
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import Optional
from agent.ask import ask
import subprocess
import os

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
    result = ask(q.question, collection=q.collection or "court-files", top_k=q.top_k or 5, format=q.format or "compact", path_contains=q.path_contains)
    return result


@app.post("/update")
def update_data(background_tasks: BackgroundTasks):
    background_tasks.add_task(run_update)
    return {"message": "Update started in background"}


def run_update():
    try:
        # Run ingest
        result1 = subprocess.run([os.sys.executable, "-m", "ingest.run_ingest"], capture_output=True, text=True)
        if result1.returncode != 0:
            print(f"Ingest failed: {result1.stderr}")
            return
        # Run index
        result2 = subprocess.run([os.sys.executable, "-m", "index.chunk_and_embed"], capture_output=True, text=True)
        if result2.returncode != 0:
            print(f"Index failed: {result2.stderr}")
            return
        print("Update completed successfully")
    except Exception as e:
        print(f"Update error: {e}")


@app.get("/", response_class=HTMLResponse)
def ui_index(request: Request):
    with open("web/static/index.html", "r", encoding="utf-8") as f:
        return HTMLResponse(f.read())
