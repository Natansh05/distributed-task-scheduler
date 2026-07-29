import asyncio
import logging
from datetime import UTC, datetime

from app.config import JOB_INTERVAL_SECONDS, NODE_ID
from app.db import get_or_create_job, record_job_run
from app.election import LeaderElector

logger = logging.getLogger("scheduler.jobs")

JOB_NAME = "heartbeat_log"


async def job_loop(leader_elector: LeaderElector) -> None:
    job_id = get_or_create_job(JOB_NAME, JOB_INTERVAL_SECONDS)
    while True:
        await asyncio.sleep(JOB_INTERVAL_SECONDS)
        ran_at = datetime.now(UTC).isoformat()
        if await leader_elector.am_i_leader():
            record_job_run(job_id, ran_at, NODE_ID, fencing_token=None)
            logger.info("job_run job=%s node=%s at=%s", JOB_NAME, NODE_ID, ran_at)
        else:
            logger.info("Node %s is not the leader, skipping job run at %s", NODE_ID, ran_at)
