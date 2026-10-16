#pragma once

#include <array>
#include <cstddef>
#include <cstdint>

#include "sherman/personality/emotion.hpp"
#include "sherman/personality/runtime.hpp"

namespace sherman::personality {

inline constexpr std::size_t kMaximumBehaviorCandidates = 16;

enum class BehaviorKind : std::int32_t {
  Wait = 0,
  Observe,
  LookToward,
  InspectChange,
  Patrol,
  Revisit,
  Report,
  Rest,
  AskForHelp,
  Acknowledge,
  Count,
};

enum BehaviorCandidateFlag : std::uint32_t {
  kCandidateAvailable = 1U << 0U,
  kCandidateQuietAllowed = 1U << 1U,
  kCandidatePausedAllowed = 1U << 2U,
  kCandidateLowEnergyAllowed = 1U << 3U,
  kCandidateInterruptible = 1U << 4U,
};

inline constexpr std::uint32_t kAllBehaviorCandidateFlags =
    kCandidateAvailable | kCandidateQuietAllowed | kCandidatePausedAllowed |
    kCandidateLowEnergyAllowed | kCandidateInterruptible;

enum BehaviorOrigin : std::uint32_t {
  kOriginLocalIdle = 1U << 0U,
  kOriginRoutine = 1U << 1U,
  kOriginJarvis = 1U << 2U,
  kOriginWorldChange = 1U << 3U,
  kOriginRecovery = 1U << 4U,
};

inline constexpr std::uint32_t kAllBehaviorOrigins =
    kOriginLocalIdle | kOriginRoutine | kOriginJarvis |
    kOriginWorldChange | kOriginRecovery;

enum BehaviorPolicyFlag : std::uint32_t {
  kPolicyQuiet = 1U << 0U,
  kPolicyPaused = 1U << 1U,
  kPolicyCurrentActionActive = 1U << 2U,
  kPolicyCurrentActionInterruptible = 1U << 3U,
};

inline constexpr std::uint32_t kAllBehaviorPolicyFlags =
    kPolicyQuiet | kPolicyPaused | kPolicyCurrentActionActive |
    kPolicyCurrentActionInterruptible;

enum BehaviorReason : std::uint32_t {
  kBehaviorEligible = 1U << 0U,
  kBehaviorRoutineDue = 1U << 1U,
  kBehaviorJarvisRequest = 1U << 2U,
  kBehaviorWorldChange = 1U << 3U,
  kBehaviorRecovery = 1U << 4U,
  kBehaviorNoveltyValue = 1U << 5U,
  kBehaviorRepetitionPenalty = 1U << 6U,
  kBehaviorRecentFailure = 1U << 7U,
  kBehaviorRiskPenalty = 1U << 8U,
  kBehaviorRetainedCommitment = 1U << 9U,
  kBehaviorRetainedHysteresis = 1U << 10U,
  kBehaviorFallbackWait = 1U << 11U,
  kBehaviorRejectedUnavailable = 1U << 12U,
  kBehaviorRejectedExpired = 1U << 13U,
  kBehaviorRejectedQuiet = 1U << 14U,
  kBehaviorRejectedPaused = 1U << 15U,
  kBehaviorRejectedLowEnergy = 1U << 16U,
};

struct BehaviorCandidate {
  std::uint64_t candidate_id{0};
  std::uint64_t deadline_monotonic_time_ns{0};
  BehaviorKind kind{BehaviorKind::Wait};
  std::uint32_t origin_flags{kOriginLocalIdle};
  std::uint32_t flags{kCandidateAvailable | kCandidateQuietAllowed |
                      kCandidatePausedAllowed | kCandidateLowEnergyAllowed |
                      kCandidateInterruptible};
  float task_value{0.0F};
  float information_value{0.0F};
  float social_value{0.0F};
  float routine_pressure{0.0F};
  float urgency{0.0F};
  float time_cost{0.0F};
  float energy_cost{0.0F};
  float motion_cost{0.0F};
  float risk_cost{0.0F};
  float repetition_cost{0.0F};
  float recent_failure_cost{0.0F};
};

struct BehaviorPolicyContext {
  std::uint64_t monotonic_time_ns{0};
  std::uint64_t current_candidate_id{0};
  std::uint32_t flags{0};
  float current_action_age_s{0.0F};
};

struct BehaviorScore {
  float task_value{0.0F};
  float curiosity_value{0.0F};
  float social_value{0.0F};
  float routine_value{0.0F};
  float urgency_value{0.0F};
  float time_cost{0.0F};
  float energy_cost{0.0F};
  float motion_cost{0.0F};
  float risk_cost{0.0F};
  float repetition_cost{0.0F};
  float failure_cost{0.0F};
  float deterministic_variation{0.0F};
  float total{0.0F};
};

struct BehaviorDecision {
  std::uint64_t selected_candidate_id{0};
  std::uint64_t runner_up_candidate_id{0};
  BehaviorKind selected_kind{BehaviorKind::Wait};
  std::uint32_t reason_flags{kBehaviorFallbackWait};
  std::uint32_t candidate_count{0};
  std::uint32_t eligible_count{0};
  BehaviorScore selected_score{};
  float runner_up_score{-1000.0F};
};

struct PersistedBehaviorPolicyState {
  static constexpr std::uint16_t kCurrentVersion = 1;
  std::uint16_t version{kCurrentVersion};
  std::uint16_t seen_kind_mask{0};
  std::uint64_t last_selected_candidate_id{0};
  BehaviorKind last_selected_kind{BehaviorKind::Wait};
  std::array<float, static_cast<std::size_t>(BehaviorKind::Count)>
      seconds_since_kind_selected{};
};

enum class BehaviorPolicyResult : std::int32_t {
  Ok = 0,
  InvalidInput = -1,
  TimeRegression = -2,
  TooManyCandidates = -3,
};

class BehaviorPolicy {
 public:
  explicit BehaviorPolicy(PersonalityConfig config = {});

  BehaviorPolicyResult select(const BehaviorPolicyContext& context,
                              const Needs& needs,
                              const BehaviorCandidate* candidates,
                              std::size_t candidate_count,
                              BehaviorDecision& decision) noexcept;

  PersistedBehaviorPolicyState snapshot() const noexcept;
  bool restore(const PersistedBehaviorPolicyState& state) noexcept;
  void reset() noexcept;
  void reset(std::uint64_t seed) noexcept;

 private:
  bool valid_candidate(const BehaviorCandidate& candidate) const noexcept;
  std::uint32_t eligibility(const BehaviorPolicyContext& context,
                            const Needs& needs,
                            const BehaviorCandidate& candidate) const noexcept;
  BehaviorScore score(const BehaviorPolicyContext& context,
                      const Needs& needs,
                      const BehaviorCandidate& candidate) const noexcept;
  float deterministic_variation(std::uint64_t candidate_id,
                                std::uint64_t time_ns) const noexcept;

  PersonalityConfig config_;
  std::array<float, static_cast<std::size_t>(BehaviorKind::Count)>
      seconds_since_kind_selected_{};
  std::uint16_t seen_kind_mask_{0};
  std::uint64_t last_selected_candidate_id_{0};
  BehaviorKind last_selected_kind_{BehaviorKind::Wait};
  std::uint64_t last_monotonic_time_ns_{0};
  bool initialized_{false};
};

}  // namespace sherman::personality
