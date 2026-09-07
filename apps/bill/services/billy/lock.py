import logging
import uuid

import redis
from django.conf import settings


logger = logging.getLogger(__name__)


class BillyLock:
    PREFIX = "billy:lock"
    DEFAULT_TTL = 30

    def __init__(self, redis_client=None):
        self.redis = redis_client or redis.Redis.from_url(
            settings.CELERY_BROKER_URL,
            decode_responses=True,
        )

    def acquire(self, cufe, ttl=None):
        ttl = ttl or self.DEFAULT_TTL

        key = self._build_key(cufe)
        token = str(uuid.uuid4())

        acquired = self.redis.set(
            key,
            token,
            nx=True,
            ex=ttl,
        )

        if not acquired:
            logger.info(
                "Billy lock already held cufe=%s",
                cufe,
            )
            return None

        logger.debug(
            "Billy lock acquired cufe=%s token=%s",
            cufe,
            token,
        )

        return token

    def release(self, cufe, token):
        key = self._build_key(cufe)

        script = """
        if redis.call("get", KEYS[1]) == ARGV[1] then
            return redis.call("del", KEYS[1])
        else
            return 0
        end
        """

        released = self.redis.eval(
            script,
            1,
            key,
            token,
        )

        if released:
            logger.debug(
                "Billy lock released cufe=%s",
                cufe,
            )
            return True

        logger.warning(
            "Billy lock release skipped because token does not match cufe=%s",
            cufe,
        )

        return False

    def _build_key(self, cufe):
        return f"{self.PREFIX}:{cufe}"