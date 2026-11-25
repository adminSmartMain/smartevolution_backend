from datetime import datetime, timedelta, timezone
import os
import subprocess
import sys

import environ
import jwt
import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from django.core.exceptions import ImproperlyConfigured

from core.auth_keys import validate_jwt_key_pair


def generate_pair():
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    private = key.private_bytes(
        serialization.Encoding.PEM,
        serialization.PrivateFormat.PKCS8,
        serialization.NoEncryption(),
    ).decode()
    public = key.public_key().public_bytes(
        serialization.Encoding.PEM,
        serialization.PublicFormat.SubjectPublicKeyInfo,
    ).decode()
    return private, public


def test_file_aware_env_loads_pem_and_rs256_round_trip(tmp_path, monkeypatch):
    private, public = generate_pair()
    private_file, public_file = tmp_path / 'private.pem', tmp_path / 'public.pem'
    private_file.write_text(private)
    public_file.write_text(public)
    monkeypatch.setenv('AUTH_JWT_SIGNING_KEY', 'should-not-be-used')
    monkeypatch.setenv('AUTH_JWT_SIGNING_KEY_FILE', str(private_file))
    monkeypatch.setenv('AUTH_JWT_VERIFYING_KEY_FILE', str(public_file))
    env = environ.FileAwareEnv()
    signing, verifying = env('AUTH_JWT_SIGNING_KEY'), env('AUTH_JWT_VERIFYING_KEY')
    validate_jwt_key_pair(signing, verifying, 'RS256')
    token = jwt.encode({'sub': 'test-user'}, signing, algorithm='RS256')
    assert jwt.decode(token, verifying, algorithms=['RS256'])['sub'] == 'test-user'


def test_invalid_and_mismatched_keys_fail_without_leaking_material():
    private, _ = generate_pair()
    _, other_public = generate_pair()
    for signing, verifying in ((private, other_public), ('invalid-private', 'invalid-public')):
        with pytest.raises(ImproperlyConfigured) as error:
            validate_jwt_key_pair(signing, verifying, 'RS256')
        assert signing not in str(error.value)
        assert verifying not in str(error.value)
        assert error.value.__cause__ is None


def test_rs256_rejects_expired_access_token():
    private, public = generate_pair()
    expired = datetime.now(timezone.utc) - timedelta(seconds=30)
    token = jwt.encode({'sub': 'test-user', 'exp': expired}, private, algorithm='RS256')
    with pytest.raises(jwt.ExpiredSignatureError):
        jwt.decode(token, public, algorithms=['RS256'])


def test_strict_settings_reject_mismatched_pem_files_without_logging_keys(tmp_path):
    private, _ = generate_pair()
    _, other_public = generate_pair()
    private_file, public_file = tmp_path / 'private.pem', tmp_path / 'public.pem'
    private_file.write_text(private)
    public_file.write_text(other_public)
    process_env = os.environ.copy()
    process_env.update({
        'DEBUG': 'False',
        'AUTH_SECURITY_ENVIRONMENT': 'production',
        'AUTH_JWT_ALGORITHM': 'RS256',
        'AUTH_JWT_SIGNING_KEY_FILE': str(private_file),
        'AUTH_JWT_VERIFYING_KEY_FILE': str(public_file),
    })
    result = subprocess.run(
        [sys.executable, '-c', 'import core.settings'],
        env=process_env, capture_output=True, text=True, check=False,
    )
    assert result.returncode != 0
    assert 'keys are invalid or do not match' in result.stderr
    assert private not in result.stderr
    assert other_public not in result.stderr
