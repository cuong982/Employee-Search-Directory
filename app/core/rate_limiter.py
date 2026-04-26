import threading
import time
from dataclasses import dataclass


@dataclass
class WindowState:
    count: int
    window_start: float


class FixedWindowRateLimiter:
    def __init__(
        self,
        limit: int,
        window_seconds: int,
        max_tracked_keys: int = 200_000,
        cleanup_interval_seconds: int = 30,
    ):
        self.limit = limit
        self.window_seconds = window_seconds
        self.max_tracked_keys = max_tracked_keys
        self.cleanup_interval_seconds = cleanup_interval_seconds
        self._windows: dict[str, WindowState] = {}
        self._last_cleanup_at = 0.0
        self._lock = threading.Lock()

    def allow(self, key: str, current_time: float | None = None) -> tuple[bool, int, int]:
        """Return (allowed, retry_after_seconds, remaining_requests)."""
        now = current_time if current_time is not None else time.time()

        with self._lock:
            self._cleanup_if_needed(now)
            state = self._windows.get(key)
            if state is None:
                if len(self._windows) >= self.max_tracked_keys:
                    return False, 1, 0
                self._windows[key] = WindowState(count=1, window_start=now)
                return True, 0, self.limit - 1

            elapsed = now - state.window_start
            if elapsed >= self.window_seconds:
                self._windows[key] = WindowState(count=1, window_start=now)
                return True, 0, self.limit - 1

            if state.count < self.limit:
                state.count += 1
                return True, 0, self.limit - state.count

            retry_after = max(1, int(self.window_seconds - elapsed))
            return False, retry_after, 0

    def _cleanup_if_needed(self, now: float) -> None:
        if now - self._last_cleanup_at < self.cleanup_interval_seconds:
            return

        expired_keys = [
            key
            for key, state in self._windows.items()
            if now - state.window_start >= self.window_seconds
        ]
        for key in expired_keys:
            del self._windows[key]
        self._last_cleanup_at = now
