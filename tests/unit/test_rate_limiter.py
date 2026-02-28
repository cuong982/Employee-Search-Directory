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


def test_fixed_window_rate_limiter_cleans_expired_keys() -> None:
    limiter = FixedWindowRateLimiter(
        limit=2,
        window_seconds=10,
        max_tracked_keys=100,
        cleanup_interval_seconds=1,
    )

    limiter.allow("k1", current_time=0.0)
    limiter.allow("k2", current_time=0.0)
    limiter.allow("k3", current_time=0.0)
    assert len(limiter._windows) == 3

    # At t=11 all previous keys are expired and should be removed on cleanup.
    limiter.allow("fresh", current_time=11.0)
    assert len(limiter._windows) == 1
    assert "fresh" in limiter._windows


def test_fixed_window_rate_limiter_blocks_new_keys_when_saturated() -> None:
    limiter = FixedWindowRateLimiter(
        limit=5,
        window_seconds=60,
        max_tracked_keys=2,
        cleanup_interval_seconds=60,
    )

    allowed_1, _ = limiter.allow("k1", current_time=100.0)
    allowed_2, _ = limiter.allow("k2", current_time=100.0)
    allowed_3, retry_after = limiter.allow("k3", current_time=100.0)

    assert allowed_1 is True
    assert allowed_2 is True
    assert allowed_3 is False
    assert retry_after == 1
    assert len(limiter._windows) == 2
