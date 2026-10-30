"""One shared global deadline with a nonrenewable aggregate origins ceiling."""

from __future__ import annotations

import math
import time
from collections.abc import Iterator
from contextlib import contextmanager

from ..watchlist_journal.storage import Budget as JournalBudget
from .errors import DeliveryError


class Budget(JournalBudget):
    """Remain compatible with accepted source hooks without resetting allowances."""

    def __init__(
        self, timeout: float = 2.0, maximum: float = 5.0, *, started: float | None = None
    ) -> None:
        if (
            type(timeout) not in (int, float)
            or not math.isfinite(timeout)
            or not 0 < timeout <= maximum
        ):
            raise DeliveryError("invalid_field")
        self._global_deadline = (time.monotonic() if started is None else started) + timeout
        self.reserve = min(0.5, timeout / 5)
        self._origin_start: float | None = None
        self._origin_deadline: float | None = None
        self._origin_active = False
        self._origin_completed = False
        self._reserved = False

    @property
    def global_deadline(self) -> float:
        return self._global_deadline

    @property
    def deadline(self) -> float:
        ceiling = self.global_deadline - (self.reserve if self._reserved else 0)
        if self._origin_active and self._origin_deadline is not None:
            ceiling = min(ceiling, self._origin_deadline)
        return ceiling

    @deadline.setter
    def deadline(self, value: float) -> None:
        raise AttributeError("immutable deadline")

    def remaining(self) -> float:
        remaining = self.deadline - time.monotonic()
        if remaining <= 0:
            raise DeliveryError("storage_timeout")
        return remaining

    def progress(self) -> int:
        return int(time.monotonic() >= self.deadline)

    def preclaim(self) -> float:
        remaining = self.global_deadline - time.monotonic() - self.reserve
        if self._origin_active and self._origin_deadline is not None:
            remaining = min(remaining, self._origin_deadline - time.monotonic())
        if remaining <= 0:
            raise DeliveryError("deadline_exceeded")
        return remaining

    @contextmanager
    def reserved(self) -> Iterator[None]:
        previous = self._reserved
        self._reserved = True
        try:
            self.remaining()
            yield
        finally:
            self._reserved = previous

    @contextmanager
    def origins(self) -> Iterator[None]:
        if self._origin_start is not None:
            raise DeliveryError("unsupported_evidence")
        self._origin_start = time.monotonic()
        self._origin_deadline = min(self.global_deadline - self.reserve, self._origin_start + 5.0)
        self._origin_active = True
        try:
            self.remaining()
            yield
            self.remaining()
            self._origin_completed = True
        finally:
            self._origin_active = False

    @property
    def origin_seal(self) -> tuple[float | None, float | None, bool]:
        return self._origin_start, self._origin_deadline, self._origin_completed
