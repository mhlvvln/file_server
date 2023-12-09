import asyncio

from fastapi import FastAPI, HTTPException
from sqlalchemy.orm import Session
from starlette.middleware.cors import CORSMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

from database.database import get_db
from models import File
from router import router as files_router

app = FastAPI(title="FileServer e-notGPT", description="Файловый сервер для фотографий[2МБ], видео[100МБ], документов[50МБ]")
app.include_router(files_router, tags=["Files"])


async def background_task(db: Session):
    while True:
        await asyncio.sleep(300)
        files = db.query(File).all()
        for file in files:
            print(file.original_name)


origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup_event():
    db = next(get_db())
    asyncio.create_task(background_task(db))


@app.exception_handler(HTTPException)
async def unicorn_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"status": False, "error": exc.detail},
    )
