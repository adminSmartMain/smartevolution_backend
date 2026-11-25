from types import SimpleNamespace

from apps.authentication.jwt import _token_was_revoked


def test_accepts_token_with_current_security_version():
    user = SimpleNamespace(token_version=3)

    assert _token_was_revoked({"token_version": 3}, user) is False


def test_rejects_token_issued_before_a_security_change():
    user = SimpleNamespace(token_version=4)

    assert _token_was_revoked({"token_version": 3}, user) is True


def test_treats_missing_token_version_as_the_initial_version():
    user = SimpleNamespace(token_version=1)

    assert _token_was_revoked({}, user) is True
