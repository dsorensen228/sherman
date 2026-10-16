#include "sherman/personality/routine.hpp"

#include <algorithm>
#include <cmath>
#include <limits>

namespace sherman::personality {
namespace {

constexpr std::int64_t kSecondsPerDay = 86400;
constexpr std::int64_t kMaximumCivilDayMagnitude = 3000000;
constexpr float kMaximumCooldownS = 86400.0F;
constexpr float kFailureRetryS = 30.0F;

bool unit(float value) noexcept {
  return std::isfinite(value) && value >= 0.0F && value <= 1.0F;
}

bool valid_kind(BehaviorKind kind) noexcept {
  const auto value = static_cast<std::int32_t>(kind);
  return value >= 0 && value < static_cast<std::int32_t>(BehaviorKind::Count);
}

std::uint64_t mix(std::uint64_t value) noexcept {
  value ^= value >> 30U;
  value *= UINT64_C(0xbf58476d1ce4e5b9);
  value ^= value >> 27U;
  value *= UINT64_C(0x94d049bb133111eb);
  return value ^ (value >> 31U);
}

}  // namespace

bool RoutineScheduler::valid_definition(
    const RoutineDefinition& definition) noexcept {
  const auto missed = static_cast<std::int32_t>(definition.missed_policy);
  if (definition.routine_id == 0 || definition.local_start_second >= 86400U ||
      definition.window_duration_s == 0U ||
      definition.window_duration_s > 86400U ||
      definition.catch_up_duration_s > 21600U ||
      definition.completion_cooldown_s > 86400U ||
      (definition.flags & ~kAllRoutineFlags) != 0U || missed < 0 ||
      missed >= static_cast<std::int32_t>(MissedRoutinePolicy::Count) ||
      definition.checkpoint_count == 0U ||
      definition.checkpoint_count > kMaximumRoutineCheckpoints ||
      !unit(definition.base_priority) || !unit(definition.task_value) ||
      !unit(definition.information_value) ||
      !unit(definition.social_value) || !unit(definition.urgency)) {
    return false;
  }
  if (definition.missed_policy == MissedRoutinePolicy::Skip &&
      definition.catch_up_duration_s != 0U) {
    return false;
  }
  for (std::size_t index = 0; index < definition.checkpoint_count; ++index) {
    if (!valid_kind(definition.checkpoint_kinds[index])) {
      return false;
    }
  }
  return true;
}

RoutineResult RoutineScheduler::configure(
    const RoutineDefinition* definitions, std::size_t count) noexcept {
  if (count > kMaximumRoutines) {
    return RoutineResult::TooManyRoutines;
  }
  if (count > 0U && definitions == nullptr) {
    return RoutineResult::InvalidInput;
  }
  for (std::size_t index = 0; index < count; ++index) {
    if (!valid_definition(definitions[index])) {
      return RoutineResult::InvalidInput;
    }
    for (std::size_t other = 0; other < index; ++other) {
      if (definitions[index].routine_id == definitions[other].routine_id) {
        return RoutineResult::InvalidInput;
      }
    }
  }

  std::array<RuntimeEntry, kMaximumRoutines> replacement{};
  for (std::size_t index = 0; index < count; ++index) {
    replacement[index].definition = definitions[index];
    replacement[index].progress.routine_id = definitions[index].routine_id;
    if (RuntimeEntry* existing = find(definitions[index].routine_id)) {
      replacement[index].progress = existing->progress;
      if (replacement[index].progress.next_checkpoint_index >=
          definitions[index].checkpoint_count) {
        replacement[index].progress = {};
        replacement[index].progress.routine_id = definitions[index].routine_id;
      }
    }
  }
  entries_ = replacement;
  routine_count_ = count;
  return RoutineResult::Ok;
}

std::int64_t RoutineScheduler::floor_div(std::int64_t numerator,
                                         std::int64_t denominator) noexcept {
  std::int64_t quotient = numerator / denominator;
  const std::int64_t remainder = numerator % denominator;
  if (remainder != 0 && ((remainder < 0) != (denominator < 0))) {
    --quotient;
  }
  return quotient;
}

std::uint64_t RoutineScheduler::candidate_id(
    std::uint64_t routine_id, std::int64_t occurrence_day_id,
    std::uint32_t checkpoint_index) noexcept {
  std::uint64_t result =
      mix(routine_id ^ mix(static_cast<std::uint64_t>(occurrence_day_id)) ^
          mix(static_cast<std::uint64_t>(checkpoint_index) + 1U));
  return result == 0U ? UINT64_C(1) : result;
}

RoutineScheduler::RuntimeEntry* RoutineScheduler::find(
    std::uint64_t routine_id) noexcept {
  for (std::size_t index = 0; index < routine_count_; ++index) {
    if (entries_[index].definition.routine_id == routine_id) {
      return &entries_[index];
    }
  }
  return nullptr;
}

RoutineResult RoutineScheduler::collect(const RoutineClock& clock,
                                        RoutineCandidate* output,
                                        std::size_t capacity,
                                        std::size_t& output_count) noexcept {
  output_count = 0U;
  if ((capacity > 0U && output == nullptr) ||
      capacity < routine_count_ ||
      (clock.flags & ~kAllRoutineClockFlags) != 0U ||
      clock.local_second_of_day >= 86400U ||
      clock.civil_day_id < -kMaximumCivilDayMagnitude ||
      clock.civil_day_id > kMaximumCivilDayMagnitude) {
    return RoutineResult::InvalidInput;
  }
  if (initialized_ && clock.monotonic_time_ns < last_monotonic_time_ns_) {
    return RoutineResult::TimeRegression;
  }

  float elapsed_s = 0.0F;
  if (!initialized_) {
    initialized_ = true;
  } else {
    elapsed_s = static_cast<float>(clock.monotonic_time_ns -
                                   last_monotonic_time_ns_) /
                1.0e9F;
  }
  last_monotonic_time_ns_ = clock.monotonic_time_ns;
  for (std::size_t index = 0; index < routine_count_; ++index) {
    entries_[index].progress.cooldown_remaining_s =
        std::max(0.0F,
                 entries_[index].progress.cooldown_remaining_s - elapsed_s);
  }

  if ((clock.flags & kRoutineClockCivilValid) == 0U ||
      (clock.flags & kRoutineClockPaused) != 0U) {
    return RoutineResult::Ok;
  }

  const std::int64_t now_s =
      clock.civil_day_id * kSecondsPerDay + clock.local_second_of_day;
  for (std::size_t index = 0; index < routine_count_; ++index) {
    RuntimeEntry& entry = entries_[index];
    const RoutineDefinition& definition = entry.definition;
    PersistedRoutineEntry& progress = entry.progress;
    if ((clock.flags & kRoutineClockQuiet) != 0U &&
        (definition.flags & kRoutineQuietCompatible) == 0U) {
      continue;
    }

    const std::int64_t occurrence_day = floor_div(
        now_s - static_cast<std::int64_t>(definition.local_start_second),
        kSecondsPerDay);
    const std::int64_t start_s =
        occurrence_day * kSecondsPerDay + definition.local_start_second;
    const std::int64_t end_s = start_s + definition.window_duration_s;
    const bool in_window = now_s >= start_s && now_s < end_s;
    const bool in_catch_up =
        definition.missed_policy == MissedRoutinePolicy::CatchUp &&
        now_s >= end_s &&
        now_s < end_s + definition.catch_up_duration_s;
    if (!in_window && !in_catch_up) {
      continue;
    }
    if (progress.has_completed &&
        occurrence_day <= progress.last_completed_day_id) {
      continue;
    }
    if (progress.cooldown_remaining_s > 0.0F) {
      continue;
    }
    if (!progress.has_active_occurrence ||
        progress.active_occurrence_day_id != occurrence_day) {
      progress.has_active_occurrence = true;
      progress.active_occurrence_day_id = occurrence_day;
      progress.next_checkpoint_index = 0U;
    }

    const std::uint32_t checkpoint = progress.next_checkpoint_index;
    RoutineCandidate candidate;
    candidate.routine_id = definition.routine_id;
    candidate.occurrence_day_id = occurrence_day;
    candidate.checkpoint_index = checkpoint;
    candidate.catch_up = in_catch_up;
    candidate.behavior.candidate_id =
        candidate_id(definition.routine_id, occurrence_day, checkpoint);
    candidate.behavior.kind = definition.checkpoint_kinds[checkpoint];
    candidate.behavior.origin_flags = kOriginRoutine;
    candidate.behavior.flags = kCandidateAvailable | kCandidateInterruptible;
    if ((definition.flags & kRoutineQuietCompatible) != 0U) {
      candidate.behavior.flags |= kCandidateQuietAllowed;
    }
    if ((definition.flags & kRoutineLowEnergyCompatible) != 0U) {
      candidate.behavior.flags |= kCandidateLowEnergyAllowed;
    }
    const float progress_through_window = in_catch_up
                                              ? 1.0F
                                              : static_cast<float>(now_s - start_s) /
                                                    definition.window_duration_s;
    candidate.behavior.routine_pressure = std::clamp(
        definition.base_priority *
            (0.35F + 0.65F * progress_through_window),
        0.0F, 1.0F);
    if (in_catch_up) {
      candidate.behavior.routine_pressure =
          std::max(candidate.behavior.routine_pressure, 0.90F);
    }
    candidate.behavior.task_value = definition.task_value;
    candidate.behavior.information_value = definition.information_value;
    candidate.behavior.social_value = definition.social_value;
    candidate.behavior.urgency = definition.urgency;
    const std::int64_t proposal_end_s =
        in_catch_up ? end_s + definition.catch_up_duration_s : end_s;
    const std::int64_t remaining_s = proposal_end_s - now_s;
    const std::uint64_t remaining_ns =
        static_cast<std::uint64_t>(remaining_s) * UINT64_C(1000000000);
    candidate.behavior.deadline_monotonic_time_ns =
        remaining_ns >
                std::numeric_limits<std::uint64_t>::max() -
                    clock.monotonic_time_ns
            ? std::numeric_limits<std::uint64_t>::max()
            : clock.monotonic_time_ns + remaining_ns;
    output[output_count++] = candidate;
  }
  return RoutineResult::Ok;
}

RoutineResult RoutineScheduler::mark_result(std::uint64_t routine_id,
                                            std::int64_t occurrence_day_id,
                                            std::uint32_t checkpoint_index,
                                            bool success) noexcept {
  RuntimeEntry* entry = find(routine_id);
  if (entry == nullptr) {
    return RoutineResult::UnknownRoutine;
  }
  PersistedRoutineEntry& progress = entry->progress;
  if (!progress.has_active_occurrence ||
      progress.active_occurrence_day_id != occurrence_day_id ||
      progress.next_checkpoint_index != checkpoint_index ||
      progress.cooldown_remaining_s > 0.0F) {
    return RoutineResult::StaleOccurrence;
  }
  if (!success) {
    progress.cooldown_remaining_s = kFailureRetryS;
    return RoutineResult::Ok;
  }

  ++progress.next_checkpoint_index;
  if (progress.next_checkpoint_index >= entry->definition.checkpoint_count) {
    progress.has_completed = true;
    progress.last_completed_day_id = occurrence_day_id;
    progress.has_active_occurrence = false;
    progress.next_checkpoint_index = 0U;
    progress.cooldown_remaining_s = static_cast<float>(
        entry->definition.completion_cooldown_s);
  }
  return RoutineResult::Ok;
}

PersistedRoutineState RoutineScheduler::snapshot() const noexcept {
  PersistedRoutineState state;
  state.routine_count = static_cast<std::uint16_t>(routine_count_);
  for (std::size_t index = 0; index < routine_count_; ++index) {
    state.entries[index] = entries_[index].progress;
  }
  return state;
}

bool RoutineScheduler::restore(const PersistedRoutineState& state) noexcept {
  if (state.version != PersistedRoutineState::kCurrentVersion ||
      state.routine_count != routine_count_) {
    reset_progress();
    return false;
  }
  std::array<PersistedRoutineEntry, kMaximumRoutines> replacement{};
  for (std::size_t index = 0; index < routine_count_; ++index) {
    const PersistedRoutineEntry& persisted = state.entries[index];
    RuntimeEntry* target = find(persisted.routine_id);
    bool duplicate = false;
    for (std::size_t other = 0; other < index; ++other) {
      duplicate = duplicate ||
                  state.entries[other].routine_id == persisted.routine_id;
    }
    if (target == nullptr || !std::isfinite(persisted.cooldown_remaining_s) ||
        duplicate ||
        persisted.cooldown_remaining_s < 0.0F ||
        persisted.cooldown_remaining_s > kMaximumCooldownS ||
        persisted.next_checkpoint_index >= target->definition.checkpoint_count ||
        persisted.last_completed_day_id < -kMaximumCivilDayMagnitude ||
        persisted.last_completed_day_id > kMaximumCivilDayMagnitude ||
        persisted.active_occurrence_day_id < -kMaximumCivilDayMagnitude ||
        persisted.active_occurrence_day_id > kMaximumCivilDayMagnitude) {
      reset_progress();
      return false;
    }
    for (std::size_t slot = 0; slot < routine_count_; ++slot) {
      if (entries_[slot].definition.routine_id == persisted.routine_id) {
        replacement[slot] = persisted;
        break;
      }
    }
  }
  for (std::size_t index = 0; index < routine_count_; ++index) {
    entries_[index].progress = replacement[index];
  }
  last_monotonic_time_ns_ = 0;
  initialized_ = false;
  return true;
}

void RoutineScheduler::reset_progress() noexcept {
  for (std::size_t index = 0; index < routine_count_; ++index) {
    entries_[index].progress = {};
    entries_[index].progress.routine_id = entries_[index].definition.routine_id;
  }
  last_monotonic_time_ns_ = 0;
  initialized_ = false;
}

}  // namespace sherman::personality
