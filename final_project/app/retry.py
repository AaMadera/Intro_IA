import time
from collections.abc import Callable
from typing import Any, TypeVar


Result = TypeVar("Result")


class RetryExhaustedError(RuntimeError):
    def __init__(self, operation: str, attempts: int, last_error: Exception) -> None:
        super().__init__(
            f"{operation} no estuvo disponible después de {attempts} intentos. "
            f"Último error: {type(last_error).__name__}: {last_error}"
        )
        self.operation = operation
        self.attempts = attempts
        self.last_error = last_error


def is_retryable_model_error(error: Exception) -> bool:
    status_code = getattr(error, "status_code", None) or getattr(error, "code", None)
    if status_code in {408, 425, 429, 500, 502, 503, 504}:
        return True
    message = str(error).lower()
    return any(
        marker in message
        for marker in (
            "busy",
            "rate limit",
            "rate_limit",
            "too many requests",
            "429",
            "503",
        )
    )


def _retry_after_seconds(error: Exception) -> float | None:
    response = getattr(error, "response", None)
    headers = getattr(response, "headers", None) or getattr(error, "headers", None)
    if not headers:
        return None
    value = headers.get("retry-after") or headers.get("Retry-After")
    if value is None:
        return None
    try:
        delay = float(value)
    except (TypeError, ValueError):
        return None
    return delay if delay >= 0 else None


def call_with_retries(
    operation: str,
    callback: Callable[[], Result],
    attempts: int = 3,
    backoff_seconds: float = 1.0,
    sleep: Callable[[float], Any] = time.sleep,
) -> Result:
    if attempts < 1:
        raise ValueError("attempts must be at least one")
    for attempt in range(1, attempts + 1):
        try:
            return callback()
        except Exception as error:
            retryable = is_retryable_model_error(error)
            if not retryable or attempt == attempts:
                if retryable and attempt == attempts:
                    raise RetryExhaustedError(operation, attempts, error) from error
                raise
            delay = backoff_seconds * (2 ** (attempt - 1))
            retry_after = _retry_after_seconds(error)
            sleep(max(delay, retry_after or 0))
    raise AssertionError("retry loop must return or raise")
