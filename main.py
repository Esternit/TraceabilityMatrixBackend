import os
import json
import hashlib
import uuid
from datetime import datetime

from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import RootModel
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase, Mapped, mapped_column
from sqlalchemy import String, select
import random

from configuration import  DB_USER, DB_PASSWORD, DB_NAME, DB_HOST, DB_PORT, WORDS



DATABASE_URL = f"postgresql+asyncpg://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

app = FastAPI()


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

SAVE_DIR = "saved_data"
os.makedirs(SAVE_DIR, exist_ok=True)

engine = create_async_engine(DATABASE_URL, echo=True)
async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

class Base(DeclarativeBase):
    pass

class JSONFile(Base):
    __tablename__ = "json_files"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    readable_name: Mapped[str] = mapped_column(String, nullable=False)
    hash: Mapped[str] = mapped_column(String, unique=True, nullable=False)


class AnyJson(RootModel[dict]):
    pass

def compute_hash(data: dict) -> str:
    json_str = json.dumps(data, sort_keys=True, separators=(',', ':'))
    return hashlib.sha256(json_str.encode('utf-8')).hexdigest()

def generate_readable_name() -> str:
    return f"{random.choice(WORDS)}-{random.choice(WORDS)}-{random.randint(100, 999)}.json"

@app.post("/save-json")
async def save_json(payload: AnyJson):
    data = payload.root
    
    if "title" not in data:
        raise HTTPException(status_code=400, detail="Поле 'title' обязательно в JSON")
        
    content_hash = compute_hash(data)

    async with async_session() as session:
        result = await session.execute(select(JSONFile).where(JSONFile.hash == content_hash))
        existing = result.scalar_one_or_none()

        if existing:
            return JSONResponse(
                content={"message": "Ой, кажется у вас дубликат :(", "file_name": existing.readable_name, "id": str(existing.id)}
            )

        file_path = os.path.join(SAVE_DIR, data["title"] + ".json")

        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)

        new_record = JSONFile(readable_name=data["title"], hash=content_hash)
        session.add(new_record)
        await session.commit()

        return JSONResponse(content={"message": "JSON сохранён", "file_name": data["title"], "id": str(new_record.id)})

@app.get("/json-files")
async def list_json_files():
    async with async_session() as session:
        result = await session.execute(select(JSONFile))
        files = result.scalars().all()
        return [{"id": str(f.id), "readable_name": f.readable_name} for f in files]

@app.get("/json-files/{file_id}")
async def get_json_file(file_id: str):
    try:
        file_uuid = uuid.UUID(file_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Неправильный формат UUID")
    async with async_session() as session:
        result = await session.execute(select(JSONFile).where(JSONFile.id == file_uuid))
        file = result.scalar_one_or_none()
        if not file:
            raise HTTPException(status_code=404, detail="Файл не найден")
        file_path = os.path.join(SAVE_DIR, file.readable_name + ".json")
        if not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail="Файл не найден на диске")
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data

@app.put("/json-files/{file_id}")
async def update_json_file(file_id: str, payload: AnyJson):
    try:
        file_uuid = uuid.UUID(file_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Неправильный формат UUID")

    data = payload.root
    
    if "title" not in data:
        raise HTTPException(status_code=400, detail="Поле 'title' обязательно в JSON")
        
    content_hash = compute_hash(data)

    async with async_session() as session:
        result = await session.execute(select(JSONFile).where(JSONFile.id == file_uuid))
        file = result.scalar_one_or_none()
        
        if not file:
            raise HTTPException(status_code=404, detail="Файл не найден")

        old_file_path = os.path.join(SAVE_DIR, file.readable_name)
        if os.path.exists(old_file_path) and file.readable_name != data["title"]:
            os.remove(old_file_path)

        file_path = os.path.join(SAVE_DIR, data["title"] + ".json")
        
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)

        file.readable_name = data["title"]
        file.hash = content_hash
        await session.commit()

        return JSONResponse(content={"message": "JSON обновлён", "file_name": data["title"], "id": str(file.id)})
