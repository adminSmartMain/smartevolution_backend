"""Wait for ephemeral QA dependencies before starting the requested command."""

import os
import sys
import time

import MySQLdb
import redis


def dependencies_are_ready():
    connection = MySQLdb.connect(
        host=os.environ["DB_HOST"],
        user=os.environ["DB_USER"],
        passwd=os.environ["DB_PASSWORD"],
        db=os.environ["DB_NAME"],
        port=int(os.environ["DB_PORT"]),
        connect_timeout=2,
    )
    connection.close()
    redis.Redis.from_url(os.environ["CELERY_BROKER_URL"]).ping()


for attempt in range(1, 61):
    try:
        dependencies_are_ready()
        break
    except Exception as error:
        if attempt == 60:
            raise RuntimeError("MySQL or Redis did not become ready for QA") from error
        print(f"Waiting for MySQL and Redis ({attempt}/60)...", flush=True)
        time.sleep(1)

os.execvp(sys.argv[1], sys.argv[1:])
