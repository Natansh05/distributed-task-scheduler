import redis.asyncio as redis
import asyncio
import logging
from app.config import REDIS_URL, NODE_ID, LEASE_TTL_SECONDS, RENEW_INTERVAL_SECONDS


r = redis.from_url(REDIS_URL, decode_responses=True)
logger = logging.getLogger("scheduler.election")

LEADER_KEY = "leader:lock"

RENEW_SCRIPT = """
if redis.call("GET", KEYS[1]) == ARGV[1] then
    return redis.call("EXPIRE", KEYS[1], ARGV[2])
else
    return 0
end
"""

renew_script = r.register_script(RENEW_SCRIPT)

class LeaderElector:
    def __init__(self):
        self.r = r
        self.renew_script = renew_script

    async def try_acquire(self)-> bool:
        """
        Try to acquire the leadership lock.
        Returns True if the lock was acquired, False otherwise.
        """

        result = await self.r.set(LEADER_KEY, NODE_ID, nx=True, ex=LEASE_TTL_SECONDS)
        return bool(result)

    async def am_i_leader(self) -> bool:
        """
        Check if the current node is the leader.
        Returns True if the current node is the leader, False otherwise.
        """
        current_leader = await self.r.get(LEADER_KEY)
        return current_leader == NODE_ID

    async def renew(self) -> bool:
        """
        Renew the leadership lock if the current node is the leader.
        Returns True if the lock was renewed, False otherwise.
        """
        result = await self.renew_script(keys=[LEADER_KEY], args=[NODE_ID, LEASE_TTL_SECONDS])
        return bool(result)

async def election_loop(elector: LeaderElector):
    while True:
        renewed = await elector.renew()
        if renewed:
            logger.info("Leadership lock renewed.")
        else:
            logger.info("Failed to renew leadership lock.")
            acquired = await elector.try_acquire()
            if acquired:
                logger.info("Leadership lock acquired by node %s.", NODE_ID)
            else:
                logger.info("Failed to acquire leadership lock.")
        await asyncio.sleep(RENEW_INTERVAL_SECONDS)