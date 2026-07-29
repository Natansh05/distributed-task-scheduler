import asyncio
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.config import NODE_ID
from app.db import init_db
from app.jobs import job_loop
from app.election import LeaderElector

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(message)s")

leader_elector = LeaderElector()


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    elected = await leader_elector.try_acquire()
    task = None
    if elected:
        logging.info("Node %s is the leader", NODE_ID)
        task = asyncio.create_task(job_loop(leader_elector))
    try:
        yield
    finally:
        if task is not None:
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass


app = FastAPI(lifespan=lifespan)

@app.get("/")
def root():
    return {"ok": True}
