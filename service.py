import datetime
import hashlib
import os
import datetime
import time

from fastapi import Depends, HTTPException, Header, UploadFile
from fastapi.security import OAuth2PasswordBearer, HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError
from sqlalchemy.orm import Session
from starlette.responses import JSONResponse, FileResponse
from models import User as UserModel
from models import File as FileModel

from database.database import get_db

SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM")


def get_current_user(token: str, db: Session = Depends(get_db)):
    # credentials_exception = HTTPException(
    #     status_code=status.HTTP_401_UNAUTHORIZED,
    #     detail={""},
    #     headers={"WWW-Authenticate": "Bearer"},
    # )
    try:
        print("hello")
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        id: str = str(payload.get("sub"))
        role: str = payload.get("role")
        if id is None:
            return JSONResponse({"status": False, "error": "не авторизован"}, status_code=401)
        token_data = payload.get("email")
    except JWTError as e:
        return JSONResponse({"status": False, "error": str(e)}, status_code=401)
    user = get_user(db, email=token_data)
    if user is None:
        return JSONResponse({"status": False, "error": "не авторизован"}, status_code=401)
    return user


def verify_token(authorization: dict = Header(..., convert_underscores=False)):
    # print(f"{authorization=}")
    try:
        scheme, token = authorization["scheme"], authorization["credentials"]
        print(scheme, token)
        if scheme.lower() != "bearer":
            raise HTTPException(status_code=401, detail="Invalid authentication scheme")
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        id: str = str(payload.get("sub"))
        if id is None:
            raise HTTPException(status_code=401, detail="Invalid token")
    except JWTError as e:
        raise HTTPException(status_code=401, detail=f"Invalid token: {str(e)}")

    return payload


def auth(token: HTTPAuthorizationCredentials, rules: list):
    token = token.model_dump()
    token = verify_token(token)
    for rule in rules:
        if rule == "*" or rule == token['role']:
            return token
    raise HTTPException(status_code=403, detail="Нет прав")


def get_user(db: Session, email: str):
    return db.query(UserModel).filter(UserModel.email == email).first()


types = {
    "photo": "photos",
    "video": "videos",
    "document": "documents"
}

sizes = {
    "photo": 2 * 1024 * 1024,
    "video": 100 * 1024 * 1024,
    "document": 10 * 1024 * 1024,
}

extensions = {
    "photo": ["jpg", "jpeg", "png"],
    "video": ["mp4", "mow", "wav"],
    "document": ["vnd.openxmlformats-officedocument.wordprocessingml.document", "pdf", "txt"]
}


def generate_hash(user_sub: str, filename: str) -> str:
    return hashlib.sha1((filename + str(round(time.time() * 1001)) + str(user_sub)).encode('utf-8')).hexdigest()


def validate_file_type_and_size(file: UploadFile, type: str, max_size: int, allowed_extensions: list):
    extension = file.content_type.split('/')[1]
    print(file.content_type)
    print(extension)
    if extension not in allowed_extensions:
        raise HTTPException(status_code=403,
                            detail=f"Неверный формат файла, допустимые значения: {', .'.join(allowed_extensions)}")

    if file.size > max_size:
        raise HTTPException(status_code=403, detail=f"Слишком большой размер файла. Не должен превышать {max_size} МБ")


def save_file(file_path: str, file: UploadFile):
    with open(file_path, "wb") as file_object:
        file_object.write(file.file.read())


def create_file_record(db: Session, user_sub: str, file: UploadFile, new_hash: str, type: str) -> FileModel:
    db_file = FileModel(
        owner_id=int(user_sub),
        original_name=file.filename,
        extension=file.content_type,
        hash_name=new_hash,
        type=type
    )
    db.add(db_file)
    db.commit()
    db.refresh(db_file)
    return db_file


def FileUpload(db: Session, user_info: dict, file: UploadFile, request, type):
    user = user_info
    return upload(db, user, file, request, type)


def upload(db: Session, user: dict, file: UploadFile, request, type):
    extension = file.content_type.split('/')[1]

    new_hash = generate_hash(user["sub"], file.filename) + "." + extension

    validate_file_type_and_size(file, type, sizes[type], extensions[type])

    file_path = f"{types[type]}/{new_hash}.{extension}"

    save_file(file_path, file)

    db_file = create_file_record(db, user["sub"], file, new_hash, type)

    return JSONResponse({
        "status": True,
        "url": f"{request.base_url}{types[type]}/{new_hash}",
        "file_id": db_file.id
    }, status_code=200)


def get_file_by_hash(db: Session, hash_name: str, type: str):
    file = db.query(FileModel).filter(
        FileModel.hash_name == hash_name,
        FileModel.type == type,
        FileModel.disabled == False
    ).first()

    if not file:
        raise HTTPException(status_code=404, detail="Файл не найден или удален")
    return file


def file_exists(file_path: str) -> bool:
    return os.path.exists(file_path)


def get_file_info_by_hash(db: Session, hash_name: str, type: str):
    file = get_file_by_hash(db, hash_name, type)
    file_path = f"{types[type]}/{file.hash_name}.{file.extension.split('/')[-1]}"
    if not file_exists(file_path):
        raise HTTPException(status_code=404, detail="Файл не найден или удален")
    if type != "document":
        return FileResponse(file_path)
    else:
        return FileResponse(file_path, filename=file.original_name)


