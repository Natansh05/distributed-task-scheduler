import redis.asyncio as redis
import asyncio
import logging
from app.config import REDIS_URL, NODE_ID, LEASE_TTL_SECONDS, RENEW_INTERVAL_SECONDS


r = redis.from_url(REDIS_URL, decode_responses=True)
logger = logging.getLogger("scheduler.election")

LEADER_KEY = "leader:lock"
FENCING_TOKEN_KEY = "leader:fencing_token"

RENEW_SCRIPT = """
if redis.call("GET", KEYS[1]) == ARGV[1] then
    return redis.call("EXPIRE", KEYS[1], ARGV[2])
else
    return 0
end
"""

ACQUIRE_SCRIPT = """
if redis.call("SET", KEYS[1], ARGV[1], "NX", "EX", ARGV[2]) then
    return redis.call("INCR", KEYS[2])
else
    return nil
end
"""

renew_script = r.register_script(RENEW_SCRIPT)
acquire_script = r.register_script(ACQUIRE_SCRIPT)

class LeaderElector:
    def __init__(self):
        self.r = r
        self.renew_script = renew_script
        self.acquire_script = acquire_script
        self.current_token = None

    async def try_acquire(self)-> int | None:
        """
        Try to acquire the leadership lock.
        Returns the fencing token if the lock was acquired, None otherwise.
        """

        result = await self.acquire_script(keys=[LEADER_KEY, FENCING_TOKEN_KEY], args=[NODE_ID, LEASE_TTL_SECONDS])
        self.current_token = result
        return result

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
                logger.info("Leadership lock acquired by node %s with token %d", NODE_ID, elector.current_token)
            else:
                logger.info("Failed to acquire leadership lock.")
        await asyncio.sleep(RENEW_INTERVAL_SECONDS)