import logging
from datetime import datetime, timezone as dt_timezone
from email.utils import parsedate_to_datetime

import redis
from django.conf import settings


logger = logging.getLogger(__name__)


class BillyRateLimiter:
    """Límite global distribuido para *todas* las llamadas a Billy.

    Redis es la fuente de verdad para que web + workers compartan el mismo
    presupuesto. Se aplican simultáneamente una ventana móvil de 1 minuto y
    otra de 1 hora. Si Redis no está disponible, el limitador falla cerrado:
    no se permite llamar a Billy sin poder garantizar los límites.
    """

    MINUTE_KEY = "billy:rate:minute"
    HOUR_KEY = "billy:rate:hour"
    GLOBAL_BLOCK_KEY = "billy:global:block"

    MINUTE_WINDOW_MS = 60_000
    HOUR_WINDOW_MS = 3_600_000

    DEFAULT_MINUTE_LIMIT = 400
    DEFAULT_HOUR_LIMIT = 4000

    ACQUIRE_SCRIPT = """
    local minute_key = KEYS[1]
    local hour_key = KEYS[2]
    local block_key = KEYS[3]
    local minute_limit = tonumber(ARGV[1])
    local hour_limit = tonumber(ARGV[2])
    local minute_window = tonumber(ARGV[3])
    local hour_window = tonumber(ARGV[4])
    local member = ARGV[5]

    local blocked = redis.call("GET", block_key)
    if blocked then
        local ttl = redis.call("TTL", block_key)
        if ttl < 1 then ttl = 1 end
        return {0, 0, 0, ttl, "global_block"}
    end

    local t = redis.call("TIME")
    local now = tonumber(t[1]) * 1000 + math.floor(tonumber(t[2]) / 1000)

    redis.call("ZREMRANGEBYSCORE", minute_key, 0, now - minute_window)
    redis.call("ZREMRANGEBYSCORE", hour_key, 0, now - hour_window)

    local minute_count = redis.call("ZCARD", minute_key)
    local hour_count = redis.call("ZCARD", hour_key)

    local retry_after = 0
    local scope = ""

    if minute_count >= minute_limit then
        local oldest = redis.call("ZRANGE", minute_key, 0, 0, "WITHSCORES")
        if oldest[2] then
            retry_after = math.ceil((tonumber(oldest[2]) + minute_window - now) / 1000)
        else
            retry_after = 1
        end
        if retry_after < 1 then retry_after = 1 end
        scope = "minute"
    end

    if hour_count >= hour_limit then
        local oldest = redis.call("ZRANGE", hour_key, 0, 0, "WITHSCORES")
        local hour_retry = 1
        if oldest[2] then
            hour_retry = math.ceil((tonumber(oldest[2]) + hour_window - now) / 1000)
        end
        if hour_retry < 1 then hour_retry = 1 end
        if hour_retry > retry_after then retry_after = hour_retry end
        scope = "hour"
    end

    if scope ~= "" then
        return {0, minute_count, hour_count, retry_after, scope}
    end

    redis.call("ZADD", minute_key, now, member)
    redis.call("ZADD", hour_key, now, member)
    redis.call("PEXPIRE", minute_key, minute_window + 1000)
    redis.call("PEXPIRE", hour_key, hour_window + 1000)

    return {1, minute_count + 1, hour_count + 1, 0, "allowed"}
    """

    SNAPSHOT_SCRIPT = """
    local minute_key = KEYS[1]
    local hour_key = KEYS[2]
    local block_key = KEYS[3]
    local minute_limit = tonumber(ARGV[1])
    local hour_limit = tonumber(ARGV[2])
    local minute_window = tonumber(ARGV[3])
    local hour_window = tonumber(ARGV[4])

    local blocked = redis.call("GET", block_key)
    if blocked then
        local ttl = redis.call("TTL", block_key)
        if ttl < 1 then ttl = 1 end
        return {0, 0, 0, 0, ttl, "global_block"}
    end

    local t = redis.call("TIME")
    local now = tonumber(t[1]) * 1000 + math.floor(tonumber(t[2]) / 1000)
    redis.call("ZREMRANGEBYSCORE", minute_key, 0, now - minute_window)
    redis.call("ZREMRANGEBYSCORE", hour_key, 0, now - hour_window)

    local minute_count = redis.call("ZCARD", minute_key)
    local hour_count = redis.call("ZCARD", hour_key)
    local minute_remaining = minute_limit - minute_count
    local hour_remaining = hour_limit - hour_count
    if minute_remaining < 0 then minute_remaining = 0 end
    if hour_remaining < 0 then hour_remaining = 0 end

    return {1, minute_count, hour_count, minute_remaining, hour_remaining, "available"}
    """

    def __init__(self, redis_client=None, minute_limit=None, hour_limit=None):
        self.redis = redis_client or redis.Redis.from_url(
            settings.CELERY_BROKER_URL,
            decode_responses=True,
        )
        self.minute_limit = minute_limit or getattr(
            settings,
            "BILLY_RATE_LIMIT_PER_MINUTE",
            self.DEFAULT_MINUTE_LIMIT,
        )
        self.hour_limit = hour_limit or getattr(
            settings,
            "BILLY_RATE_LIMIT_PER_HOUR",
            self.DEFAULT_HOUR_LIMIT,
        )

    def acquire(self):
        import uuid

        member = str(uuid.uuid4())
        try:
            allowed, minute_count, hour_count, retry_after, scope = self.redis.eval(
                self.ACQUIRE_SCRIPT,
                3,
                self.MINUTE_KEY,
                self.HOUR_KEY,
                self.GLOBAL_BLOCK_KEY,
                self.minute_limit,
                self.hour_limit,
                self.MINUTE_WINDOW_MS,
                self.HOUR_WINDOW_MS,
                member,
            )
        except redis.RedisError:
            logger.exception("Billy rate limiter Redis unavailable; failing closed")
            return {
                "allowed": False,
                "minute_count": 0,
                "hour_count": 0,
                "minute_limit": self.minute_limit,
                "hour_limit": self.hour_limit,
                "retry_after": 60,
                "scope": "redis_unavailable",
            }

        return {
            "allowed": bool(allowed),
            "minute_count": int(minute_count),
            "hour_count": int(hour_count),
            "minute_limit": self.minute_limit,
            "hour_limit": self.hour_limit,
            # Compatibilidad con código/tests previos.
            "count": int(minute_count),
            "limit": self.minute_limit,
            "retry_after": int(retry_after),
            "scope": str(scope),
        }

    def get_budget(self):
        """Snapshot no destructivo usado por Beat antes de encolar."""
        try:
            result = self.redis.eval(
                self.SNAPSHOT_SCRIPT,
                3,
                self.MINUTE_KEY,
                self.HOUR_KEY,
                self.GLOBAL_BLOCK_KEY,
                self.minute_limit,
                self.hour_limit,
                self.MINUTE_WINDOW_MS,
                self.HOUR_WINDOW_MS,
            )
        except redis.RedisError:
            logger.exception("Billy budget Redis unavailable; scheduler fails closed")
            return {
                "available": False,
                "minute_remaining": 0,
                "hour_remaining": 0,
                "retry_after": 60,
                "scope": "redis_unavailable",
            }

        if not bool(result[0]):
            return {
                "available": False,
                "minute_remaining": 0,
                "hour_remaining": 0,
                "retry_after": int(result[4]),
                "scope": str(result[5]),
            }

        return {
            "available": True,
            "minute_count": int(result[1]),
            "hour_count": int(result[2]),
            "minute_remaining": int(result[3]),
            "hour_remaining": int(result[4]),
            "retry_after": 0,
            "scope": str(result[5]),
        }

    def block_global(self, retry_after, reason="429"):
        seconds = max(int(retry_after or 1), 1)
        try:
            self.redis.set(
                self.GLOBAL_BLOCK_KEY,
                reason,
                ex=seconds,
            )
        except redis.RedisError:
            logger.exception("Could not persist Billy global block in Redis")
        return seconds

    @staticmethod
    def parse_retry_after(value, default=60):
        if value in (None, ""):
            return int(default)

        try:
            return max(int(value), 1)
        except (TypeError, ValueError):
            pass

        try:
            target = parsedate_to_datetime(str(value))
            if target.tzinfo is None:
                target = target.replace(tzinfo=dt_timezone.utc)
            now = datetime.now(dt_timezone.utc)
            return max(int((target - now).total_seconds()), 1)
        except (TypeError, ValueError, OverflowError):
            return int(default)
