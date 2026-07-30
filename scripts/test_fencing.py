"""
Manual test for the fencing token rejection path.

Run this AFTER the app has run at least once normally (so leader_state
has a real highest_fencing_token_seen > 0).

Usage (from project root):
    uv run python -m scripts.test_fencing
"""

from datetime import UTC, datetime
from app.db import get_connection, get_or_create_job, record_job_run

JOB_NAME = "heartbeat_log"


def main():
    conn = get_connection()
    row = conn.execute(
        "SELECT highest_fencing_token_seen FROM leader_state WHERE id = 1"
    ).fetchone()
    highest = row[0]
    conn.close()

    print(f"Current highest_fencing_token_seen in DB: {highest}")

    job_id = get_or_create_job(JOB_NAME, 10)
    stale_token = max(highest - 1, 0)  # deliberately old/low token
    ran_at = datetime.now(UTC).isoformat()

    print(f"Attempting a write with a STALE token: {stale_token} (should be rejected)")
    try:
        record_job_run(job_id, ran_at, "fake-stale-node", fencing_token=stale_token)
        print("FAIL: stale write was NOT rejected — this is a bug.")
    except ValueError as e:
        print(f"PASS: stale write correctly rejected -> {e}")

    print()
    fresh_token = highest + 1
    print(f"Attempting a write with a FRESH token: {fresh_token} (should succeed)")
    try:
        record_job_run(job_id, ran_at, "fake-fresh-node", fencing_token=fresh_token)
        print("PASS: fresh write accepted.")
    except ValueError as e:
        print(f"FAIL: fresh write was rejected unexpectedly -> {e}")


if __name__ == "__main__":
    main()