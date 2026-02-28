from app.core.rate_limiter import FixedWindowRateLimiter


def test_fixed_window_rate_limiter_blocks_after_limit_and_recovers() -> None:
    limiter = FixedWindowRateLimiter(limit=2, window_seconds=10)

    allowed_1, retry_after_1 = limiter.allow("org_1:user_1:127.0.0.1", current_time=100.0)
    allowed_2, retry_after_2 = limiter.allow("org_1:user_1:127.0.0.1", current_time=101.0)
    allowed_3, retry_after_3 = limiter.allow("org_1:user_1:127.0.0.1", current_time=102.0)

    assert allowed_1 is True
    assert retry_after_1 == 0
    assert allowed_2 is True
    assert retry_after_2 == 0
    assert allowed_3 is False
    assert retry_after_3 >= 1

    allowed_4, retry_after_4 = limiter.allow("org_1:user_1:127.0.0.1", current_time=111.0)
    assert allowed_4 is True
    assert retry_after_4 == 0
