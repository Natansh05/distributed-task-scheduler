import asyncio
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.config import NODE_ID
from app.db import init_db
from app.jobs import job_loop
from app.election import LeaderElector, election_loop
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(message)s")

leader_elector = LeaderElector()


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    task = asyncio.create_task(job_loop(leader_elector))
    election_task = asyncio.create_task(election_loop(leader_elector))
    try:
        yield
    finally:
        task.cancel()
        election_task.cancel()
        for t in (task, election_task):
            try:
                await t
            except asyncio.CancelledError:
                pass

app = FastAPI(lifespan=lifespan)

@app.get("/")
def root():
    return {"ok": True}
