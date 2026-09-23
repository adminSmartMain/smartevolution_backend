import logging
import uuid

import redis
from django.conf import settings


logger = logging.getLogger(__name__)


class BillyPollingState:
    """Estado efímero que no merece columnas nuevas en ``bills``.

    Si Redis se reinicia, los streaks vuelven a cero y la cadencia vuelve al
    comportamiento histórico (más conservador funcionalmente, nunca más
    restrictivo). No es fuente de verdad de negocio.
    """

    UNCHANGED_PREFIX = "billy:unchanged"
    QUEUED_PREFIX = "billy:queued"
    DEFAULT_QUEUE_TTL = 30 * 60
    STREAK_TTL = 7 * 24 * 60 * 60

    def __init__(self, redis_client=None):
        self.redis = redis_client or redis.Redis.from_url(
            settings.CELERY_BROKER_URL,
            decode_responses=True,
        )

    def register_unchanged(self, bill_id):
        key = f"{self.UNCHANGED_PREFIX}:{bill_id}"
        try:
            pipe = self.redis.pipeline()
            pipe.incr(key)
            pipe.expire(key, self.STREAK_TTL)
            streak, _ = pipe.execute()
            return int(streak)
        except redis.RedisError:
            logger.exception("Could not register Billy unchanged streak bill_id=%s", bill_id)
            return 0

    def reset_unchanged(self, bill_id):
        try:
            self.redis.delete(f"{self.UNCHANGED_PREFIX}:{bill_id}")
        except redis.RedisError:
            logger.exception("Could not reset Billy unchanged streak bill_id=%s", bill_id)

    def acquire_queue_slot(self, bill_id, ttl=None):
        key = f"{self.QUEUED_PREFIX}:{bill_id}"
        token = str(uuid.uuid4())
        try:
            acquired = self.redis.set(
                key,
                token,
                nx=True,
                ex=ttl or self.DEFAULT_QUEUE_TTL,
            )
        except redis.RedisError:
            # Deduplicación es una barrera de seguridad. Si no se puede
            # garantizar, el scheduler no debe aumentar el tráfico.
            logger.exception("Billy queue dedupe Redis unavailable bill_id=%s", bill_id)
            return None
        return token if acquired else None

    def release_queue_slot(self, bill_id, token):
        if not token:
            return False

        key = f"{self.QUEUED_PREFIX}:{bill_id}"
        script = """
        if redis.call("get", KEYS[1]) == ARGV[1] then
            return redis.call("del", KEYS[1])
        end
        return 0
        """
        try:
            return bool(self.redis.eval(script, 1, key, token))
        except redis.RedisError:
            logger.exception("Could not release Billy queue slot bill_id=%s", bill_id)
            return False
