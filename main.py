from contextlib import asynccontextmanager
from typing import Annotated

import uvicorn
from beanie import init_beanie, Document, Indexed
from beanie.odm.operators.find.comparison import In
from fastapi import FastAPI, Query
from motor.motor_asyncio import AsyncIOMotorClient
from pydantic import BaseModel, ConfigDict
from starlette.middleware.cors import CORSMiddleware

mongo = AsyncIOMotorClient('mongodb://localhost:27017/watch_tracker')


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_beanie(database=mongo.db_name, document_models=[Entry])
    yield
    mongo.close()


app = FastAPI(lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class Entry(Document):
    service: Indexed(str)
    entry_id: Indexed(str)


class AddEntryBody(BaseModel):
    service: str
    entry_id: str

    model_config = ConfigDict(
        extra='allow',
    )


class GetEntriesBody(BaseModel):
    service: str
    entry_ids: list[str]


@app.get('/services')
async def list_services():
    return {
        'items': [entry.service for entry in await Entry.distinct('service')]
    }


@app.post('/add_entry')
async def add_entry(body: AddEntryBody):
    entry = await Entry.find_one(Entry.service == body.service, Entry.entry_id == body.entry_id)
    added = False
    if not entry:
        entry = Entry(service=body.service, entry_id=body.entry_id, **body.model_extra)
        await Entry.insert_one(entry)
        added = True
    return {
        'added': added,
        'entry': entry.model_dump(),
    }


@app.get('/get_entries')
async def get_entries(service: str, entry_ids: Annotated[list[str], Query()]):
    entries = Entry.find(Entry.service == service, In(Entry.entry_id, entry_ids))
    return [entry.model_dump() async for entry in entries]


@app.post('/get_entries')
async def get_entries(body: AddEntryBody):
    entries = Entry.find(Entry.service == body.service, In(Entry.entry_id, body.entry_ids))
    return [entry.model_dump() async for entry in entries]


if __name__ == '__main__':
    uvicorn.run(app='main:app', host='0.0.0.0', port=1234, reload=True)
