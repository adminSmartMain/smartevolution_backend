import logging
import uuid

import environ
import redis


logger = logging.getLogger(__name__)

env = environ.Env()


class BillyRateLimiter:
    KEY = "billy:rate:requests"
    DEFAULT_LIMIT = 400
    WINDOW_MS = 60_000

    def __init__(self, redis_client=None, limit=None):
        redis_url = env(
            "CELERY_BROKER_URL",
            default="redis://redis:6379/0",
        )

        self.redis = redis_client or redis.Redis.from_url(
            redis_url,
            decode_responses=True,
        )

        self.limit = limit or env.int(
            "BILLY_RATE_LIMIT_PER_MINUTE",
            default=self.DEFAULT_LIMIT,
        )

    def acquire(self):
        member = str(uuid.uuid4())

        script = """
        local key = KEYS[1]
        local limit = tonumber(ARGV[1])
        local window = tonumber(ARGV[2])
        local member = ARGV[3]

        local time = redis.call("TIME")
        local now =
            tonumber(time[1]) * 1000
            + math.floor(tonumber(time[2]) / 1000)

        local window_start = now - window

        redis.call(
            "ZREMRANGEBYSCORE",
            key,
            0,
            window_start
        )

        local count = redis.call(
            "ZCARD",
            key
        )

        if count >= limit then
            local oldest = redis.call(
                "ZRANGE",
                key,
                0,
                0,
                "WITHSCORES"
            )

            local retry_after = 1

            if oldest[2] then
                retry_after = math.ceil(
                    (
                        tonumber(oldest[2])
                        + window
                        - now
                    ) / 1000
                )

                if retry_after < 1 then
                    retry_after = 1
                end
            end

            return {
                0,
                count,
                retry_after
            }
        end

        redis.call(
            "ZADD",
            key,
            now,
            member
        )

        redis.call(
            "PEXPIRE",
            key,
            window + 1000
        )

        return {
            1,
            count + 1,
            0
        }
        """

        allowed, count, retry_after = self.redis.eval(
            script,
            1,
            self.KEY,
            self.limit,
            self.WINDOW_MS,
            member,
        )

        return {
            "allowed": bool(allowed),
            "count": int(count),
            "limit": self.limit,
            "retry_after": int(retry_after),
        }