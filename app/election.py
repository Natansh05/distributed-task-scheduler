import redis.asyncio as redis
from app.config import REDIS_URL, NODE_ID, LEASE_TTL_SECONDS


r = redis.from_url(REDIS_URL, decode_responses=True)

LEADER_KEY = "leader:lock"

class LeaderElector:
    def __init__(self):
        self.r = r

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