#include "sherman/personality/policy.hpp"

#include <algorithm>
#include <cmath>
#include <limits>

namespace sherman::personality {
namespace {

constexpr float kMaximumPolicyAgeS = 86400.0F;
constexpr float kSelectionHysteresis = 0.12F;
constexpr float kMinimumCommitmentS = 1.2F;

bool unit(float value) noexcept {
  return std::isfinite(value) && value >= 0.0F && value <= 1.0F;
}

bool valid_needs(const Needs& needs) noexcept {
  return unit(needs.energy) && unit(needs.curiosity) &&
         unit(needs.social_engagement) && unit(needs.confidence) &&
         unit(needs.frustration) && unit(needs.urgency);
}

std::uint64_t mix(std::uint64_t value) noexcept {
  value ^= value >> 30U;
  value *= UINT64_C(0xbf58476d1ce4e5b9);
  value ^= value >> 27U;
  value *= UINT64_C(0x94d049bb133111eb);
  return value ^ (value >> 31U);
}

}  // namespace

BehaviorPolicy::BehaviorPolicy(PersonalityConfig config)
    : config_(PersonalityController::valid_config(config) ? config
                                                           : PersonalityConfig{}) {
  reset();
}

void BehaviorPolicy::reset() noexcept {
  seconds_since_kind_selected_.fill(kMaximumPolicyAgeS);
  seen_kind_mask_ = 0U;
  last_selected_candidate_id_ = 0;
  last_selected_kind_ = BehaviorKind::Wait;
  last_monotonic_time_ns_ = 0;
  initialized_ = false;
}

void BehaviorPolicy::reset(std::uint64_t seed) noexcept {
  config_.seed = seed;
  reset();
}

bool BehaviorPolicy::valid_candidate(
    const BehaviorCandidate& candidate) const noexcept {
  const auto kind = static_cast<std::int32_t>(candidate.kind);
  if (candidate.candidate_id == 0 || kind < 0 ||
      kind >= static_cast<std::int32_t>(BehaviorKind::Count) ||
      (candidate.origin_flags & ~kAllBehaviorOrigins) != 0U ||
      candidate.origin_flags == 0U ||
      (candidate.flags & ~kAllBehaviorCandidateFlags) != 0U) {
    return false;
  }
  const float values[] = {
      candidate.task_value,          candidate.information_value,
      candidate.social_value,        candidate.routine_pressure,
      candidate.urgency,             candidate.time_cost,
      candidate.energy_cost,         candidate.motion_cost,
      candidate.risk_cost,           candidate.repetition_cost,
      candidate.recent_failure_cost,
  };
  for (float value : values) {
    if (!unit(value)) {
      return false;
    }
  }
  return true;
}

std::uint32_t BehaviorPolicy::eligibility(
    const BehaviorPolicyContext& context, const Needs& needs,
    const BehaviorCandidate& candidate) const noexcept {
  std::uint32_t reasons = 0U;
  if ((candidate.flags & kCandidateAvailable) == 0U) {
    reasons |= kBehaviorRejectedUnavailable;
  }
  if (candidate.deadline_monotonic_time_ns != 0U &&
      candidate.deadline_monotonic_time_ns <= context.monotonic_time_ns) {
    reasons |= kBehaviorRejectedExpired;
  }
  if ((context.flags & kPolicyQuiet) != 0U &&
      ((candidate.flags & kCandidateQuietAllowed) == 0U ||
       (candidate.kind != BehaviorKind::Wait &&
        candidate.kind != BehaviorKind::Rest) ||
       candidate.motion_cost != 0.0F)) {
    reasons |= kBehaviorRejectedQuiet;
  }
  if ((context.flags & kPolicyPaused) != 0U &&
      (candidate.flags & kCandidatePausedAllowed) == 0U) {
    reasons |= kBehaviorRejectedPaused;
  }
  if (needs.energy < 0.25F &&
      (candidate.flags & kCandidateLowEnergyAllowed) == 0U) {
    reasons |= kBehaviorRejectedLowEnergy;
  }
  return reasons == 0U ? kBehaviorEligible : reasons;
}

float BehaviorPolicy::deterministic_variation(
    std::uint64_t candidate_id, std::uint64_t time_ns) const noexcept {
  // Stable for a five-second decision epoch, so polling cannot churn a tie.
  const std::uint64_t epoch = time_ns / UINT64_C(5000000000);
  const std::uint64_t bits = mix(config_.seed ^ mix(candidate_id) ^ mix(epoch));
  constexpr float kScale = 1.0F / 16777216.0F;
  const float unit_value = static_cast<float>(bits >> 40U) * kScale;
  return (unit_value - 0.5F) * 0.04F;
}

BehaviorScore BehaviorPolicy::score(
    const BehaviorPolicyContext& context, const Needs& needs,
    const BehaviorCandidate& candidate) const noexcept {
  BehaviorScore result;
  result.task_value = candidate.task_value * 1.05F;
  result.curiosity_value = candidate.information_value *
                           (0.48F + 0.78F * config_.curiosity) *
                           (0.55F + 0.55F * needs.curiosity);
  result.social_value = candidate.social_value *
                        (0.38F + 0.70F * config_.sociability) *
                        (0.65F + 0.35F * needs.social_engagement);
  result.routine_value = candidate.routine_pressure * 0.92F;
  result.urgency_value = candidate.urgency * 1.18F + needs.urgency * 0.12F;
  result.time_cost = candidate.time_cost * 0.28F;
  result.energy_cost = candidate.energy_cost *
                       (0.42F + 1.35F * (1.0F - needs.energy));
  result.motion_cost = candidate.motion_cost *
                       (0.28F + 0.44F * config_.calmness);
  result.risk_cost = candidate.risk_cost * 1.75F;

  const auto kind_index = static_cast<std::size_t>(candidate.kind);
  const float age_s = seconds_since_kind_selected_[kind_index];
  const float automatic_repetition =
      (seen_kind_mask_ & (1U << kind_index)) != 0U
          ? std::max(0.0F, 1.0F - age_s / 18.0F)
          : 0.0F;
  result.repetition_cost =
      (candidate.repetition_cost + automatic_repetition * 0.55F) * 0.78F;
  result.failure_cost = candidate.recent_failure_cost *
                        (0.62F + 0.38F * (1.0F - config_.calmness));
  result.deterministic_variation =
      deterministic_variation(candidate.candidate_id,
                              context.monotonic_time_ns);
  result.total = result.task_value + result.curiosity_value +
                 result.social_value + result.routine_value +
                 result.urgency_value - result.time_cost -
                 result.energy_cost - result.motion_cost - result.risk_cost -
                 result.repetition_cost - result.failure_cost +
                 result.deterministic_variation;
  return result;
}

BehaviorPolicyResult BehaviorPolicy::select(
    const BehaviorPolicyContext& context, const Needs& needs,
    const BehaviorCandidate* candidates, std::size_t candidate_count,
    BehaviorDecision& decision) noexcept {
  decision = {};
  decision.candidate_count = static_cast<std::uint32_t>(candidate_count);
  if (candidate_count > kMaximumBehaviorCandidates) {
    return BehaviorPolicyResult::TooManyCandidates;
  }
  if ((candidate_count > 0U && candidates == nullptr) ||
      (context.flags & ~kAllBehaviorPolicyFlags) != 0U ||
      !std::isfinite(context.current_action_age_s) ||
      context.current_action_age_s < 0.0F || !valid_needs(needs)) {
    return BehaviorPolicyResult::InvalidInput;
  }
  if (initialized_ && context.monotonic_time_ns < last_monotonic_time_ns_) {
    return BehaviorPolicyResult::TimeRegression;
  }

  // Validate the complete batch before advancing ages. Candidate IDs are the
  // stable identity used for commitment and explanation, so aliases would be
  // ambiguous and are rejected rather than resolved by array order.
  for (std::size_t index = 0; index < candidate_count; ++index) {
    if (!valid_candidate(candidates[index])) {
      return BehaviorPolicyResult::InvalidInput;
    }
    for (std::size_t other = 0; other < index; ++other) {
      if (candidates[index].candidate_id == candidates[other].candidate_id) {
        return BehaviorPolicyResult::InvalidInput;
      }
    }
  }

  float elapsed_s = 0.0F;
  if (!initialized_) {
    initialized_ = true;
  } else {
    elapsed_s = static_cast<float>(context.monotonic_time_ns -
                                   last_monotonic_time_ns_) /
                1.0e9F;
  }
  last_monotonic_time_ns_ = context.monotonic_time_ns;
  for (float& age_s : seconds_since_kind_selected_) {
    age_s = std::min(kMaximumPolicyAgeS, age_s + elapsed_s);
  }

  std::size_t best_index = candidate_count;
  std::size_t runner_up_index = candidate_count;
  std::size_t current_index = candidate_count;
  BehaviorScore best_score;
  best_score.total = -std::numeric_limits<float>::infinity();
  BehaviorScore runner_up_score = best_score;
  BehaviorScore current_score = best_score;
  std::array<std::uint32_t, kMaximumBehaviorCandidates> reasons{};

  for (std::size_t index = 0; index < candidate_count; ++index) {
    reasons[index] = eligibility(context, needs, candidates[index]);
    if (reasons[index] != kBehaviorEligible) {
      decision.reason_flags |= reasons[index];
      continue;
    }
    ++decision.eligible_count;
    const BehaviorScore candidate_score =
        score(context, needs, candidates[index]);
    if (candidates[index].candidate_id == context.current_candidate_id) {
      current_index = index;
      current_score = candidate_score;
    }
    if (candidate_score.total > best_score.total) {
      runner_up_index = best_index;
      runner_up_score = best_score;
      best_index = index;
      best_score = candidate_score;
    } else if (candidate_score.total > runner_up_score.total) {
      runner_up_index = index;
      runner_up_score = candidate_score;
    }
  }

  if (best_index == candidate_count) {
    decision.reason_flags |= kBehaviorFallbackWait;
    return BehaviorPolicyResult::Ok;
  }

  bool retained_commitment = false;
  bool retained_hysteresis = false;
  const bool current_active =
      (context.flags & kPolicyCurrentActionActive) != 0U;
  const bool current_interruptible =
      (context.flags & kPolicyCurrentActionInterruptible) != 0U;
  if (current_active && current_index != candidate_count &&
      current_index != best_index) {
    if (!current_interruptible ||
        (context.current_action_age_s < kMinimumCommitmentS &&
         best_score.total < current_score.total + 0.36F)) {
      runner_up_index = best_index;
      runner_up_score = best_score;
      best_index = current_index;
      best_score = current_score;
      retained_commitment = true;
    } else if (best_score.total < current_score.total + kSelectionHysteresis) {
      runner_up_index = best_index;
      runner_up_score = best_score;
      best_index = current_index;
      best_score = current_score;
      retained_hysteresis = true;
    }
  }

  const BehaviorCandidate& selected = candidates[best_index];
  decision.selected_candidate_id = selected.candidate_id;
  decision.selected_kind = selected.kind;
  decision.selected_score = best_score;
  decision.reason_flags = kBehaviorEligible;
  if ((selected.origin_flags & kOriginRoutine) != 0U &&
      selected.routine_pressure > 0.0F) {
    decision.reason_flags |= kBehaviorRoutineDue;
  }
  if ((selected.origin_flags & kOriginJarvis) != 0U) {
    decision.reason_flags |= kBehaviorJarvisRequest;
  }
  if ((selected.origin_flags & kOriginWorldChange) != 0U) {
    decision.reason_flags |= kBehaviorWorldChange;
  }
  if ((selected.origin_flags & kOriginRecovery) != 0U) {
    decision.reason_flags |= kBehaviorRecovery;
  }
  if (selected.information_value > 0.0F) {
    decision.reason_flags |= kBehaviorNoveltyValue;
  }
  if (best_score.repetition_cost > 0.0F) {
    decision.reason_flags |= kBehaviorRepetitionPenalty;
  }
  if (selected.recent_failure_cost > 0.0F) {
    decision.reason_flags |= kBehaviorRecentFailure;
  }
  if (selected.risk_cost > 0.0F) {
    decision.reason_flags |= kBehaviorRiskPenalty;
  }
  if (retained_commitment) {
    decision.reason_flags |= kBehaviorRetainedCommitment;
  }
  if (retained_hysteresis) {
    decision.reason_flags |= kBehaviorRetainedHysteresis;
  }
  if (runner_up_index != candidate_count) {
    decision.runner_up_candidate_id = candidates[runner_up_index].candidate_id;
    decision.runner_up_score = runner_up_score.total;
  }

  if (selected.candidate_id != last_selected_candidate_id_) {
    const auto kind_index = static_cast<std::size_t>(selected.kind);
    seconds_since_kind_selected_[kind_index] = 0.0F;
    seen_kind_mask_ = static_cast<std::uint16_t>(
        seen_kind_mask_ | static_cast<std::uint16_t>(1U << kind_index));
    last_selected_candidate_id_ = selected.candidate_id;
    last_selected_kind_ = selected.kind;
  }
  return BehaviorPolicyResult::Ok;
}

PersistedBehaviorPolicyState BehaviorPolicy::snapshot() const noexcept {
  PersistedBehaviorPolicyState state;
  state.seen_kind_mask = seen_kind_mask_;
  state.last_selected_candidate_id = last_selected_candidate_id_;
  state.last_selected_kind = last_selected_kind_;
  state.seconds_since_kind_selected = seconds_since_kind_selected_;
  return state;
}

bool BehaviorPolicy::restore(
    const PersistedBehaviorPolicyState& state) noexcept {
  constexpr std::uint16_t kValidSeenMask =
      static_cast<std::uint16_t>((1U << static_cast<std::size_t>(
                                      BehaviorKind::Count)) -
                                 1U);
  const auto kind = static_cast<std::int32_t>(state.last_selected_kind);
  bool valid =
      state.version == PersistedBehaviorPolicyState::kCurrentVersion &&
      (state.seen_kind_mask & ~kValidSeenMask) == 0U && kind >= 0 &&
      kind < static_cast<std::int32_t>(BehaviorKind::Count) &&
      ((state.last_selected_candidate_id == 0U &&
        state.seen_kind_mask == 0U) ||
       (state.last_selected_candidate_id != 0U &&
        (state.seen_kind_mask & (1U << static_cast<std::uint32_t>(kind))) !=
            0U));
  for (float age_s : state.seconds_since_kind_selected) {
    valid = valid && std::isfinite(age_s) && age_s >= 0.0F &&
            age_s <= kMaximumPolicyAgeS;
  }
  if (!valid) {
    reset();
    return false;
  }
  seen_kind_mask_ = state.seen_kind_mask;
  last_selected_candidate_id_ = state.last_selected_candidate_id;
  last_selected_kind_ = state.last_selected_kind;
  seconds_since_kind_selected_ = state.seconds_since_kind_selected;
  last_monotonic_time_ns_ = 0;
  initialized_ = false;
  return true;
}

}  // namespace sherman::personality
