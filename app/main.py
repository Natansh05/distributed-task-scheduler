import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.db import init_db
from app.jobs import job_loop

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(message)s")


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    task = asyncio.create_task(job_loop())
    print("Job loop started")
    try:
        yield
    finally:
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass


app = FastAPI(lifespan=lifespan)


@app.get("/")
def root():
    return {"ok": True}
