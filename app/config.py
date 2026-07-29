import os

NODE_ID = os.environ.get("NODE_ID", "node-1")
DB_PATH = os.environ.get("DB_PATH", "scheduler.db")
JOB_INTERVAL_SECONDS = float(os.environ.get("JOB_INTERVAL_SECONDS", "4"))

REDIS_URL = os.environ.get("REDIS_URL", "redis://localhost:6379/0")
LEASE_TTL_SECONDS = int(os.environ.get("LEASE_TTL_SECONDS", "10"))