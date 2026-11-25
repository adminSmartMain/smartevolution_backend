import hashlib
import hmac
import ipaddress
import json
import logging
import time
from datetime import datetime, timezone

import redis
import requests
from django.apps import apps
from django.conf import settings

# Do not import apps.base.utils.index here: that convenience module imports
# decodeJWT, which loads the configured JWT authentication class and creates a
# cycle while Django is building REST_FRAMEWORK settings.
from apps.base.utils.genUUID import gen_uuid
from apps.base.utils.sendEmail import sendEmail

logger = logging.getLogger(__name__)
_captcha_alerted_reasons = set()


class LoginRejected(Exception):
    def __init__(self, retry_after=None, captcha_required=False):
        self.retry_after = retry_after
        self.captcha_required = captcha_required
        super().__init__("Login rejected")


class SecurityStoreUnavailable(Exception):
    pass


def _redis():
    try:
        client = redis.Redis.from_url(settings.AUTH_REDIS_URL, decode_responses=True)
        client.ping()
        return client
    except redis.RedisError as exc:
        logger.error("Authentication security store unavailable", exc_info=exc)
        raise SecurityStoreUnavailable() from exc


def _identifier(email):
    normalized = (email or "").strip().lower().encode("utf-8")
    return hmac.new(settings.AUTH_LOGIN_IDENTIFIER_SECRET.encode("utf-8"), normalized, hashlib.sha256).hexdigest()


def _ip_identifier(ip):
    return hmac.new(
        settings.AUTH_LOGIN_IDENTIFIER_SECRET.encode("utf-8"),
        (ip or "unknown").encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()


def _network_identifier(ip):
    """Return a privacy-preserving key for an IPv4 /24 or IPv6 /64 range."""
    try:
        address = ipaddress.ip_address(ip)
        network = ipaddress.ip_network(
            f"{address}/{'24' if address.version == 4 else '64'}", strict=False,
        )
        value = str(network)
    except ValueError:
        value = "unknown"
    return hmac.new(
        settings.AUTH_LOGIN_IDENTIFIER_SECRET.encode("utf-8"),
        value.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()


def client_ip(request):
    forwarded = request.META.get("HTTP_X_FORWARDED_FOR", "")
    values = [value.strip() for value in forwarded.split(",") if value.strip()]
    if settings.AUTH_TRUSTED_PROXY_COUNT and len(values) >= settings.AUTH_TRUSTED_PROXY_COUNT:
        return values[-(settings.AUTH_TRUSTED_PROXY_COUNT + 1)] if len(values) > settings.AUTH_TRUSTED_PROXY_COUNT else values[0]
    return request.META.get("REMOTE_ADDR", "unknown")


def audit(event, request, email, reason, user=None, extra=None):
    """Persist security events without credentials or token material."""
    details = {
        "identifier_hash": _identifier(email),
        "reason": reason,
        "user_agent": (request.META.get("HTTP_USER_AGENT", "")[:512] if request else ""),
        **(extra or {}),
    }
    # JSON is deliberately emitted as the log message so it remains structured
    # even when the hosting platform uses Django's plain-text formatter.
    logger.info(json.dumps({
        "event": event,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "ip_hash": _ip_identifier(client_ip(request)) if request else None,
        "user_id": str(user.id) if user else None,
        **details,
    }, sort_keys=True, default=str))
    try:
        # Resolve the model only after Django's app registry is ready. Importing
        # it at module load time would cycle through User -> base utils -> DRF
        # settings -> configured JWT authentication.
        access_audit = apps.get_model("authentication", "AccessAudit")
        security_audit = apps.get_model("authentication", "AuthenticationSecurityAudit")
        access_audit.objects.create(
            id=gen_uuid(), actor=user, action=event, target_type="authentication",
            target_id=str(user.id) if user else None,
            ip_address=client_ip(request) if request else None,
            details=details,
        )
        security_audit.objects.create(
            id=gen_uuid(),
            actor=user,
            event=event,
            email_attempted=(email or '').strip().lower(),
            identifier_hash=_identifier(email),
            ip_address=client_ip(request) if request else None,
            user_agent=(request.META.get("HTTP_USER_AGENT", "")[:512] if request else ""),
            reason=reason,
            metadata=extra or {},
        )
    except Exception:
        # Security audit must not ever expose authentication internals to a user.
        logger.exception("Unable to persist authentication audit event")


def emit_security_alert(event, request, email, details):
    """Emit an alert without making a monitoring outage block authentication."""
    payload = {
        "event": event,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "identifier_hash": _identifier(email),
        "ip_hash": _ip_identifier(client_ip(request)),
        "user_agent": request.META.get("HTTP_USER_AGENT", "")[:512],
        **details,
    }
    logger.warning(json.dumps(payload, sort_keys=True, default=str))
    if not settings.AUTH_SECURITY_ALERT_WEBHOOK_URL:
        return
    try:
        requests.post(settings.AUTH_SECURITY_ALERT_WEBHOOK_URL, json=payload, timeout=2)
    except requests.RequestException:
        logger.exception("Security alert webhook delivery failed")


def captcha_status():
    """Return safe operational state without exposing provider secrets."""
    enabled = bool(settings.AUTH_CAPTCHA_ENABLED)
    configured = bool(str(settings.AUTH_TURNSTILE_SECRET_KEY or "").strip())
    return {
        "enabled": enabled,
        "configured": configured,
        "ready": enabled and configured,
    }


def report_captcha_problem(reason, request=None, email="", details=None):
    """Emit a one-time actionable alert; provider outages never kill startup."""
    if reason in _captcha_alerted_reasons:
        return
    _captcha_alerted_reasons.add(reason)
    payload = {"event": "AUTH_CAPTCHA_ALERT", "reason": reason, **(details or {})}
    logger.error(json.dumps(payload, sort_keys=True, default=str))
    if request:
        audit("AUTH_CAPTCHA_ALERT", request, email, reason, extra=details)
        emit_security_alert("AUTH_CAPTCHA_ALERT", request, email, payload)


def report_captcha_configuration():
    """Called at startup to flag a configured-but-unusable CAPTCHA safely."""
    state = captcha_status()
    if settings.AUTH_IS_PRODUCTION and not state["enabled"]:
        report_captcha_problem("turnstile_disabled_in_production")
        return
    if state["enabled"] and not state["configured"]:
        report_captcha_problem("missing_turnstile_secret")


def _increment_with_ttl(client, key, ttl):
    value = client.incr(key)
    if value == 1:
        client.expire(key, ttl)
    return value


def check_login_attempt(request, email, captcha_token):
    client = _redis()
    ip = client_ip(request)
    identifier = _identifier(email)
    ip_key = f"auth:login:ip:{ip}"
    ip_count = _increment_with_ttl(client, ip_key, settings.AUTH_LOGIN_IP_WINDOW_SECONDS)
    if ip_count > settings.AUTH_LOGIN_IP_LIMIT:
        retry_after = max(1, client.ttl(ip_key))
        audit("LOGIN_RATE_LIMITED", request, email, "ip_limit", extra={"retry_after": retry_after})
        raise LoginRejected(retry_after=retry_after)

    lock_key = f"auth:login:lock:{identifier}"
    lock_ttl = client.ttl(lock_key)
    if lock_ttl > 0:
        audit("LOGIN_RATE_LIMITED", request, email, "account_locked", extra={"retry_after": lock_ttl})
        raise LoginRejected(retry_after=lock_ttl)

    failures = int(client.get(f"auth:login:failures:{identifier}") or 0)
    ip_failures = int(client.get(f"auth:login:failures:ip:{_ip_identifier(ip)}") or 0)
    if (
        settings.AUTH_CAPTCHA_ENABLED
        and max(failures, ip_failures) >= settings.AUTH_CAPTCHA_AFTER_FAILURES
    ):
        verify_captcha(captcha_token, request, email)

    backoff_ttl = client.ttl(f"auth:login:backoff:{identifier}")
    if backoff_ttl > 0:
        raise LoginRejected(retry_after=backoff_ttl, captcha_required=max(failures, ip_failures) >= settings.AUTH_CAPTCHA_AFTER_FAILURES)


def verify_captcha(captcha_token, request, email=""):
    if not settings.AUTH_CAPTCHA_ENABLED:
        return
    if not captcha_status()["configured"]:
        report_captcha_problem("missing_turnstile_secret", request, email)
        raise LoginRejected(retry_after=settings.AUTH_CAPTCHA_MISSING_RETRY_SECONDS, captcha_required=True)
    if not captcha_token:
        raise LoginRejected(captcha_required=True)
    try:
        response = requests.post(
            settings.AUTH_TURNSTILE_VERIFY_URL,
            data={
                "secret": settings.AUTH_TURNSTILE_SECRET_KEY,
                "response": captcha_token,
                "remoteip": client_ip(request),
            },
            timeout=3,
        )
        result = response.json()
    except (requests.RequestException, ValueError):
        report_captcha_problem("turnstile_unavailable", request, email)
        raise LoginRejected(retry_after=settings.AUTH_CAPTCHA_MISSING_RETRY_SECONDS, captcha_required=True)
    if not result.get("success"):
        error_codes = set(result.get("error-codes") or [])
        if error_codes.intersection({"missing-input-secret", "invalid-input-secret"}):
            report_captcha_problem(
                "invalid_turnstile_secret", request, email,
                {"provider_error_codes": sorted(error_codes)},
            )
            raise LoginRejected(retry_after=settings.AUTH_CAPTCHA_MISSING_RETRY_SECONDS, captcha_required=True)
        raise LoginRejected(captcha_required=True)
    expected_hostnames = settings.AUTH_TURNSTILE_EXPECTED_HOSTNAMES
    response_hostname = str(result.get("hostname", "")).lower()
    if expected_hostnames and response_hostname not in expected_hostnames:
        report_captcha_problem("turnstile_hostname_mismatch", request, email)
        raise LoginRejected(captcha_required=True)


def record_failed_login(request, email, user=None):
    client = _redis()
    identifier = _identifier(email)
    key = f"auth:login:failures:{identifier}"
    failures = _increment_with_ttl(client, key, settings.AUTH_LOGIN_FAILURE_WINDOW_SECONDS)
    ip = client_ip(request)
    ip_failures = _increment_with_ttl(
        client,
        f"auth:login:failures:ip:{_ip_identifier(ip)}",
        settings.AUTH_LOGIN_FAILURE_WINDOW_SECONDS,
    )
    alert_failures = _increment_with_ttl(
        client,
        f"auth:login:failures-alert:ip:{_ip_identifier(ip)}",
        5 * 60,
    )
    network_key = _network_identifier(ip)
    network_failures = _increment_with_ttl(
        client,
        f"auth:login:failures-alert:network:{network_key}",
        5 * 60,
    )
    network_accounts_key = f"auth:login:failure-identifiers:network:{network_key}"
    # The set contains HMACs, never raw emails. It detects a distributed
    # password-spraying pattern separately from a single-account brute force.
    client.sadd(network_accounts_key, identifier)
    client.expire(network_accounts_key, 5 * 60)
    network_accounts = client.scard(network_accounts_key)
    audit("LOGIN_FAILED", request, email, "invalid_credentials", user=user, extra={"attempt": failures})

    if alert_failures == 20:
        # This event is deliberately structured for the existing log pipeline
        # / SIEM. It contains no raw email, password, token or cookie value.
        emit_security_alert(
            "AUTH_IP_FAILURE_ALERT", request, email,
            {"reason": "ip_failure_threshold", "failures": alert_failures},
        )
        audit("AUTH_IP_FAILURE_ALERT", request, email, "ip_failure_threshold", extra={"ip_failures": alert_failures})

    if network_accounts == 3 or (network_failures == 20 and network_accounts > 1):
        emit_security_alert(
            "AUTH_NETWORK_FAILURE_ALERT", request, email,
            {
                "reason": "network_password_spraying",
                "network_hash": network_key,
                "failures": network_failures,
                "distinct_accounts": network_accounts,
            },
        )
        audit(
            "AUTH_NETWORK_FAILURE_ALERT",
            request,
            email,
            "network_password_spraying",
            extra={"network_failures": network_failures, "distinct_accounts": network_accounts},
        )

    if failures >= settings.AUTH_LOGIN_MAX_FAILURES:
        client.setex(f"auth:login:lock:{identifier}", settings.AUTH_LOGIN_LOCK_SECONDS, "1")
        audit("ACCOUNT_LOCKED", request, email, "max_failures", user=user)
        _notify_lock(user)
        raise LoginRejected(retry_after=settings.AUTH_LOGIN_LOCK_SECONDS)
    if failures >= settings.AUTH_LOGIN_BACKOFF_FROM_FAILURES:
        retry_after = min(2 ** (failures - settings.AUTH_LOGIN_BACKOFF_FROM_FAILURES + 1), 8)
        client.setex(f"auth:login:backoff:{identifier}", retry_after, "1")
        # The first throttled credential failure is deliberately delayed after
        # password verification. Later attempts are rejected from Redis before
        # authentication work, preventing worker exhaustion during an attack.
        time.sleep(retry_after)
        raise LoginRejected(retry_after=retry_after, captcha_required=failures >= settings.AUTH_CAPTCHA_AFTER_FAILURES)
    return failures >= settings.AUTH_CAPTCHA_AFTER_FAILURES


def reset_failed_logins(email):
    client = _redis()
    identifier = _identifier(email)
    client.delete(f"auth:login:failures:{identifier}", f"auth:login:backoff:{identifier}")


def _notify_lock(user):
    if not user or not user.email:
        return False
    try:
        delivered = sendEmail(
            subject="Actividad inusual de inicio de sesión",
            message="Detectamos varios intentos fallidos. Tu acceso fue bloqueado temporalmente por seguridad.",
            email=user.email,
        )
        if delivered != 1:
            raise RuntimeError("SMTP did not accept the account-lock notification")
        return True
    except Exception:
        logger.exception(
            json.dumps({
                "event": "ACCOUNT_LOCK_NOTIFICATION_FAILED",
                "user_id": str(user.id),
                "reason": "smtp_delivery_failed",
                "timestamp": datetime.now(timezone.utc).isoformat(),
            })
        )
        return False
