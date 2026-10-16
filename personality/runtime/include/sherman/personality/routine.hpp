#pragma once

#include <array>
#include <cstddef>
#include <cstdint>

#include "sherman/personality/policy.hpp"

namespace sherman::personality {

inline constexpr std::size_t kMaximumRoutines = 8;
inline constexpr std::size_t kMaximumRoutineCheckpoints = 8;

enum class MissedRoutinePolicy : std::int32_t {
  Skip = 0,
  CatchUp,
  Count,
};

enum RoutineFlag : std::uint32_t {
  kRoutineQuietCompatible = 1U << 0U,
  kRoutineLowEnergyCompatible = 1U << 1U,
};

inline constexpr std::uint32_t kAllRoutineFlags =
    kRoutineQuietCompatible | kRoutineLowEnergyCompatible;

enum RoutineClockFlag : std::uint32_t {
  kRoutineClockCivilValid = 1U << 0U,
  kRoutineClockQuiet = 1U << 1U,
  kRoutineClockPaused = 1U << 2U,
};

inline constexpr std::uint32_t kAllRoutineClockFlags =
    kRoutineClockCivilValid | kRoutineClockQuiet | kRoutineClockPaused;

struct RoutineDefinition {
  std::uint64_t routine_id{0};
  std::uint32_t local_start_second{0};
  std::uint32_t window_duration_s{3600};
  std::uint32_t catch_up_duration_s{0};
  std::uint32_t completion_cooldown_s{0};
  std::uint32_t flags{0};
  MissedRoutinePolicy missed_policy{MissedRoutinePolicy::Skip};
  std::uint32_t checkpoint_count{1};
  std::array<BehaviorKind, kMaximumRoutineCheckpoints> checkpoint_kinds{
      BehaviorKind::Observe};
  float base_priority{0.5F};
  float task_value{0.2F};
  float information_value{0.2F};
  float social_value{0.0F};
  float urgency{0.1F};
};

struct RoutineClock {
  std::uint64_t monotonic_time_ns{0};
  std::int64_t civil_day_id{0};
  std::uint32_t local_second_of_day{0};
  std::uint32_t flags{0};
};

struct RoutineCandidate {
  BehaviorCandidate behavior{};
  std::uint64_t routine_id{0};
  std::int64_t occurrence_day_id{0};
  std::uint32_t checkpoint_index{0};
  bool catch_up{false};
};

struct PersistedRoutineEntry {
  std::uint64_t routine_id{0};
  std::int64_t last_completed_day_id{0};
  std::int64_t active_occurrence_day_id{0};
  float cooldown_remaining_s{0.0F};
  std::uint32_t next_checkpoint_index{0};
  bool has_completed{false};
  bool has_active_occurrence{false};
};

struct PersistedRoutineState {
  static constexpr std::uint16_t kCurrentVersion = 1;
  std::uint16_t version{kCurrentVersion};
  std::uint16_t routine_count{0};
  std::array<PersistedRoutineEntry, kMaximumRoutines> entries{};
};

enum class RoutineResult : std::int32_t {
  Ok = 0,
  InvalidInput = -1,
  TimeRegression = -2,
  TooManyRoutines = -3,
  UnknownRoutine = -4,
  StaleOccurrence = -5,
};

class RoutineScheduler {
 public:
  RoutineScheduler() = default;

  RoutineResult configure(const RoutineDefinition* definitions,
                          std::size_t count) noexcept;
  RoutineResult collect(const RoutineClock& clock, RoutineCandidate* output,
                        std::size_t capacity,
                        std::size_t& output_count) noexcept;
  RoutineResult mark_result(std::uint64_t routine_id,
                            std::int64_t occurrence_day_id,
                            std::uint32_t checkpoint_index,
                            bool success) noexcept;

  PersistedRoutineState snapshot() const noexcept;
  bool restore(const PersistedRoutineState& state) noexcept;
  void reset_progress() noexcept;

  std::size_t routine_count() const noexcept { return routine_count_; }

 private:
  struct RuntimeEntry {
    RoutineDefinition definition{};
    PersistedRoutineEntry progress{};
  };

  static bool valid_definition(const RoutineDefinition& definition) noexcept;
  static std::int64_t floor_div(std::int64_t numerator,
                                std::int64_t denominator) noexcept;
  static std::uint64_t candidate_id(std::uint64_t routine_id,
                                    std::int64_t occurrence_day_id,
                                    std::uint32_t checkpoint_index) noexcept;
  RuntimeEntry* find(std::uint64_t routine_id) noexcept;

  std::array<RuntimeEntry, kMaximumRoutines> entries_{};
  std::size_t routine_count_{0};
  std::uint64_t last_monotonic_time_ns_{0};
  bool initialized_{false};
};

}  // namespace sherman::personality
