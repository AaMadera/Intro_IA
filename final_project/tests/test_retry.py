import pytest

from app.retry import RetryExhaustedError, call_with_retries


class BusyError(RuntimeError):
    status_code = 429


class RetryAfterBusyError(BusyError):
    response = type("Response", (), {"headers": {"Retry-After": "9"}})()


def test_retry_succeeds_after_transient_busy_error() -> None:
    calls = 0
    delays: list[float] = []

    def operation() -> str:
        nonlocal calls
        calls += 1
        if calls < 3:
            raise BusyError("rate limit")
        return "ok"

    assert (
        call_with_retries("modelo", operation, backoff_seconds=2, sleep=delays.append)
        == "ok"
    )
    assert calls == 3
    assert delays == [2, 4]


def test_retry_reports_exhaustion_after_three_attempts() -> None:
    calls = 0

    def operation() -> None:
        nonlocal calls
        calls += 1
        raise BusyError("busy")

    with pytest.raises(RetryExhaustedError, match="3 intentos"):
        call_with_retries("modelo", operation, backoff_seconds=0, sleep=lambda _: None)
    assert calls == 3


def test_non_retryable_error_is_not_retried() -> None:
    calls = 0

    def operation() -> None:
        nonlocal calls
        calls += 1
        raise ValueError("invalid request")

    with pytest.raises(ValueError):
        call_with_retries("modelo", operation, sleep=lambda _: None)
    assert calls == 1


def test_retry_uses_retry_after_when_it_is_longer_than_backoff() -> None:
    delays: list[float] = []

    def operation() -> None:
        raise RetryAfterBusyError("rate limit")

    with pytest.raises(RetryExhaustedError):
        call_with_retries(
            "modelo", operation, attempts=2, backoff_seconds=1, sleep=delays.append
        )

    assert delays == [9]
