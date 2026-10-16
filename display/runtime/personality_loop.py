"""Bounded production scheduling for the semantic personality source."""

from __future__ import annotations

from collections.abc import Callable
import time

from runtime.personality_adapter import (
    FallbackPersonalitySource,
    PersonalityInput,
    PersonalityIntent,
    PersonalitySource,
    PersonalityStateStore,
    safe_fallback_intent,
)


InputProvider = Callable[[int, int, bool], PersonalityInput]


def idle_input_provider(
    monotonic_time_ns: int,
    local_second_of_day: int,
    circadian_valid: bool,
) -> PersonalityInput:
    """Current stationary-hardware input until core/sensor producers connect."""

    return PersonalityInput(
        monotonic_time_ns=monotonic_time_ns,
        local_second_of_day=local_second_of_day,
        circadian_valid=circadian_valid,
    )


class AutonomousPersonalityController:
    """Drive personality at a bounded rate and expose the latest face intent."""

    def __init__(
        self,
        source: PersonalitySource,
        *,
        started_s: float,
        tick_hz: float = 10.0,
        state_store: PersonalityStateStore | None = None,
        persistence_interval_s: float = 300.0,
        circadian_enabled: bool = True,
        source_required: bool = False,
        input_provider: InputProvider = idle_input_provider,
        localtime: Callable[[], time.struct_time] = time.localtime,
        initial_error: str = "",
    ) -> None:
        if not 1.0 <= tick_hz <= 30.0:
            raise ValueError("personality tick_hz must be in [1, 30]")
        if not 10.0 <= persistence_interval_s <= 3600.0:
            raise ValueError("persistence interval must be in [10, 3600]")
        self._source = source
        self._source_required = source_required
        self._tick_period_s = 1.0 / tick_hz
        self._next_tick_s = started_s
        self._store = state_store
        self._persistence_interval_s = persistence_interval_s
        self._next_persist_s = started_s + persistence_interval_s
        self._circadian_enabled = circadian_enabled
        self._input_provider = input_provider
        self._localtime = localtime
        self.intent = safe_fallback_intent(round(started_s * 1_000_000_000))
        self.degraded = isinstance(source, FallbackPersonalitySource)
        self.restore_status = "disabled" if state_store is None else "missing"
        self.tick_drops = 0
        self.step_errors = 0
        self.persistence_errors = 0
        self.last_error = initial_error[:512]
        self._closed = False
        self._load_state()

    @property
    def backend_name(self) -> str:
        return self._source.backend_name

    def _load_state(self) -> None:
        if self._store is None or self.degraded:
            return
        try:
            payload = self._store.load()
            if payload is None:
                return
            if self._source.restore(payload):
                self.restore_status = "restored"
            else:
                self.restore_status = "rejected"
                self.persistence_errors += 1
                self.last_error = "native personality rejected persisted state"
        except (OSError, ValueError, RuntimeError) as error:
            self.restore_status = "rejected"
            self.persistence_errors += 1
            self.last_error = str(error)[:512]

    def _local_second(self) -> int:
        if not self._circadian_enabled:
            return 0
        local = self._localtime()
        return local.tm_hour * 3600 + local.tm_min * 60 + local.tm_sec

    def _degrade(self, error: Exception, monotonic_time_ns: int) -> None:
        self.step_errors += 1
        self.last_error = str(error)[:512]
        if self._source_required:
            raise error
        self._source.close()
        self._source = FallbackPersonalitySource()
        self.degraded = True
        self.intent = safe_fallback_intent(monotonic_time_ns, self.intent.sequence + 1)

    def update(self, now_s: float) -> PersonalityIntent:
        if self._closed:
            raise RuntimeError("personality controller is closed")
        if now_s < self._next_tick_s:
            return self.intent

        elapsed_periods = int((now_s - self._next_tick_s) / self._tick_period_s)
        if elapsed_periods > 0:
            self.tick_drops += elapsed_periods
        self._next_tick_s += (elapsed_periods + 1) * self._tick_period_s
        monotonic_time_ns = max(0, round(now_s * 1_000_000_000))
        local_second = self._local_second()
        inputs = self._input_provider(
            monotonic_time_ns, local_second, self._circadian_enabled
        )
        try:
            self.intent = self._source.step(inputs)
        except (OSError, RuntimeError, ValueError) as error:
            self._degrade(error, monotonic_time_ns)
            self.intent = self._source.step(inputs)

        if now_s >= self._next_persist_s:
            self.persist()
            missed = int((now_s - self._next_persist_s) / self._persistence_interval_s)
            self._next_persist_s += (missed + 1) * self._persistence_interval_s
        return self.intent

    def persist(self) -> bool:
        if self._store is None or self.degraded:
            return False
        try:
            payload = self._source.snapshot()
            self._store.save(payload)
            return bool(payload)
        except (OSError, RuntimeError, ValueError) as error:
            self.persistence_errors += 1
            self.last_error = str(error)[:512]
            return False

    def apply_event(self, event: int, strength: float = 1.0) -> bool:
        """Apply a validated semantic outcome from a future core adapter."""

        if self._closed:
            raise RuntimeError("personality controller is closed")
        return self._source.apply_event(event, strength)

    def health(self) -> dict[str, object]:
        return {
            "personality_backend": self.backend_name,
            "personality_degraded": self.degraded,
            "personality_restore": self.restore_status,
            "personality_sequence": self.intent.sequence,
            "micro_behavior": self.intent.micro_behavior,
            "reason_flags": self.intent.reason_flags,
            "personality_tick_drops": self.tick_drops,
            "personality_step_errors": self.step_errors,
            "personality_persistence_errors": self.persistence_errors,
            "personality_last_error": self.last_error[:192],
        }

    def close(self) -> None:
        if self._closed:
            return
        self.persist()
        self._source.close()
        self._closed = True
