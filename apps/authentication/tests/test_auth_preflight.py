from unittest.mock import patch

import pytest
import redis
from django.test import override_settings

from scripts.check_auth_preflight import check


@override_settings(DEBUG=False, AUTH_IS_PRODUCTION=True, AUTH_JWT_ALGORITHM='RS256')
@patch('scripts.check_auth_preflight.redis.Redis.from_url')
def test_preflight_checks_redis_without_printing_url(factory, capsys):
    factory.return_value.ping.return_value = True
    check()
    assert factory.return_value.ping.called
    assert 'redis://' not in capsys.readouterr().out


@override_settings(DEBUG=False, AUTH_IS_PRODUCTION=True, AUTH_JWT_ALGORITHM='RS256')
@patch('scripts.check_auth_preflight.redis.Redis.from_url')
def test_preflight_hides_redis_error_details(factory):
    factory.side_effect = redis.RedisError('sensitive-connection-details')
    with pytest.raises(SystemExit) as error:
        check()
    assert 'sensitive-connection-details' not in str(error.value)


@override_settings(DEBUG=True, AUTH_IS_PRODUCTION=True, AUTH_JWT_ALGORITHM='RS256')
def test_preflight_rejects_debug():
    with pytest.raises(SystemExit, match='DEBUG=False'):
        check()
