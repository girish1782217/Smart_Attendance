from datetime import timedelta

from app.core.time_utils import utc_now

MAX_FAILED_ATTEMPTS = 5
WINDOW = timedelta(minutes=15)

# Process-local in-memory state. Correct for a single-process deployment
# (this project's scope); a multi-worker production deployment would need
# a shared store (e.g. Redis) for the same guarantee across workers — see
# docs/sdd/16-security-spec.md.
_failed_attempts: dict[str, list] = {}


def _prune(key: str) -> list:
    now = utc_now()
    attempts = [t for t in _failed_attempts.get(key, []) if now - t < WINDOW]
    _failed_attempts[key] = attempts
    return attempts


def is_rate_limited(key: str) -> bool:
    return len(_prune(key)) >= MAX_FAILED_ATTEMPTS


def register_failed_attempt(key: str) -> None:
    attempts = _prune(key)
    attempts.append(utc_now())
    _failed_attempts[key] = attempts


def clear_attempts(key: str) -> None:
    _failed_attempts.pop(key, None)


def reset_all() -> None:
    """Test-only: clears all tracked state so the process-global limiter
    doesn't leak between test cases."""
    _failed_attempts.clear()
