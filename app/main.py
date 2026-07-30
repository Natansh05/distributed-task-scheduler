import asyncio
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.config import NODE_ID
from app.db import init_db
from app.jobs import job_loop
from app.election import LeaderElector, election_loop, LEADER_KEY
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(message)s")
from app.schemas import StatusResponse

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


@app.get("/status", response_model=StatusResponse)
async def status():
    current_leader = await leader_elector.get_current_leader()
    is_leader = await leader_elector.am_i_leader()
    current_token = leader_elector.current_token if is_leader else None
    lease_ttl_remaining = await leader_elector.get_ttl_left()

    response = StatusResponse(
        node_id=NODE_ID,
        role="leader" if is_leader else "follower",
        current_token=current_token,
        current_leader=current_leader,
        lease_ttl_remaining=lease_ttl_remaining,
    )
    return response
