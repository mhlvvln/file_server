from fastapi import FastAPI, HTTPException
from starlette.requests import Request
from starlette.responses import JSONResponse

from router import router as files_router

app = FastAPI()
app.include_router(files_router, tags=["Files"])


@app.exception_handler(HTTPException)
async def unicorn_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"status": False, "error": exc.detail},
    )