from beanie import init_beanie, Document, Indexed
from beanie.odm.operators.find.comparison import In
from hug.types import comma_separated_list, multiple
from motor.motor_asyncio import AsyncIOMotorClient
import hug


api = hug.API(__name__)
api.http.add_middleware(hug.middleware.CORSMiddleware(api, max_age=10))

mongo = AsyncIOMotorClient('mongodb://localhost:27017/watch_tracker')


class Entry(Document):
    service: Indexed(str)
    entry_id: Indexed(str)


@hug.startup()
async def before_start(app):
    await init_beanie(database=mongo.db_name, document_models=[Entry])


@hug.get('/services')
async def list_services():
    return {
        'items': [entry.service for entry in await Entry.distinct('service')]
    }


@hug.post('/add_entry')
async def add_entry(service: str, entry_id: str, **params):
    entry = await Entry.find_one(Entry.service == service, Entry.entry_id == entry_id)
    added = False
    if not entry:
        entry = Entry(service=service, entry_id=entry_id, **params)
        await Entry.insert_one(entry)
        added = True
    return {
        'added': added,
        'entry': entry.model_dump(),
    }


@hug.get('/get_entries')
async def get_entries(service: str, entry_ids: comma_separated_list):
    entries = Entry.find(Entry.service == service, In(Entry.entry_id, entry_ids))
    return [entry.model_dump() async for entry in entries]


@hug.post('/get_entries')
async def get_entries(service: str, entry_ids: multiple):
    entries = Entry.find(Entry.service == service, In(Entry.entry_id, entry_ids))
    return [entry.model_dump() async for entry in entries]


if __name__ == '__main__':
    hug.development_runner.hug(file=__file__, host='0.0.0.0', port=1234, no_404_documentation=False)
