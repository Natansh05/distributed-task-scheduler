import os

NODE_ID = os.environ.get("NODE_ID", "node-1")
DB_PATH = os.environ.get("DB_PATH", "scheduler.db")
JOB_INTERVAL_SECONDS = float(os.environ.get("JOB_INTERVAL_SECONDS", "10"))
