from fastapi import APIRouter, UploadFile, Depends, File, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from starlette.responses import FileResponse

import models
from database.database import get_db
from service import verify_token, auth, FileUpload, get_file_info_by_hash

router = APIRouter()

security = HTTPBearer()


@router.get("/protected")
def protected_route(token: HTTPAuthorizationCredentials = Depends(security)):
    rules = auth(token, ["*"])
    return rules


@router.post("/uploadPhoto")
def upload_photo(request: Request,
                 token: HTTPAuthorizationCredentials = Depends(security),
                 file: UploadFile = File(...),
                 db: Session = Depends(get_db)):
    rules = auth(token, ["*"])
    return FileUpload(db, rules, file, request, "photo")


@router.post("/uploadVideo")
def upload_photo(request: Request,
                 token: HTTPAuthorizationCredentials = Depends(security),
                 file: UploadFile = File(...),
                 db: Session = Depends(get_db)):
    rules = auth(token, ["*"])
    return FileUpload(db, rules, file, request, "video")


@router.post("/uploadDocument")
def upload_photo(request: Request,
                 token: HTTPAuthorizationCredentials = Depends(security),
                 file: UploadFile = File(...),
                 db: Session = Depends(get_db)):
    rules = auth(token, ["*"])
    return FileUpload(db, rules, file, request, "document")


@router.get("/photos/{hash}")
def photos(hash: str, db: Session = Depends(get_db)):
    return get_file_info_by_hash(db, hash, "photo")


@router.get("/videos/{hash}")
def videos(hash: str, db: Session = Depends(get_db)):
    return get_file_info_by_hash(db, hash, "video")


@router.get("/documents/{hash}")
def documents(hash: str, db: Session = Depends(get_db)):
    return get_file_info_by_hash(db, hash, "document")
