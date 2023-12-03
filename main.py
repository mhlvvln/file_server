from fastapi import FastAPI, HTTPException
from sqlalchemy.orm import Session
from starlette.requests import Request
from starlette.responses import JSONResponse
from apscheduler.schedulers.background import BackgroundScheduler

from models import File
from router import router as files_router

app = FastAPI()
app.include_router(files_router, tags=["Files"])


def background_task(db: Session):
    files = db.query(File).all()
    for file in files:
        print(file.original_name)


scheduler = BackgroundScheduler()


def start_scheduler():
    scheduler.add_job(background_task, 'interval', minutes=30)
    scheduler.start()


app.add_event_handler("startup", start_scheduler)


@app.exception_handler(HTTPException)
async def unicorn_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"status": False, "error": exc.detail},
    )
