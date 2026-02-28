import threading
import time
from dataclasses import dataclass


@dataclass
class WindowState:
    count: int
    window_start: float


class FixedWindowRateLimiter:
    def __init__(self, limit: int, window_seconds: int):
        self.limit = limit
        self.window_seconds = window_seconds
        self._windows: dict[str, WindowState] = {}
        self._lock = threading.Lock()

    def allow(self, key: str, current_time: float | None = None) -> tuple[bool, int]:
        now = current_time if current_time is not None else time.time()

        with self._lock:
            state = self._windows.get(key)
            if state is None:
                self._windows[key] = WindowState(count=1, window_start=now)
                return True, 0

            elapsed = now - state.window_start
            if elapsed >= self.window_seconds:
                self._windows[key] = WindowState(count=1, window_start=now)
                return True, 0

            if state.count < self.limit:
                state.count += 1
                return True, 0

            retry_after = max(1, int(self.window_seconds - elapsed))
            return False, retry_after
