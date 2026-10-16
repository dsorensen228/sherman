#include "sherman/personality/runtime_c.h"

#include <array>
#include <cstddef>
#include <cstdint>
#include <new>

#include "sherman/personality/policy.hpp"
#include "sherman/personality/routine.hpp"
#include "sherman/personality/runtime.hpp"

namespace {

using sherman::personality::BehaviorCandidate;
using sherman::personality::BehaviorDecision;
using sherman::personality::BehaviorKind;
using sherman::personality::BehaviorPolicy;
using sherman::personality::BehaviorPolicyContext;
using sherman::personality::BehaviorPolicyResult;
using sherman::personality::MicroBehavior;
using sherman::personality::Mood;
using sherman::personality::Needs;
using sherman::personality::PersistedBehaviorPolicyState;
using sherman::personality::PersistedEmotionState;
using sherman::personality::PersistedPersonalityState;
using sherman::personality::PersonalityConfig;
using sherman::personality::PersonalityController;
using sherman::personality::PersonalityEvent;
using sherman::personality::PersonalityEventResult;
using sherman::personality::PersonalityInput;
using sherman::personality::PersonalityOutput;
using sherman::personality::PersonalityStepResult;
using sherman::personality::PersistedRoutineState;
using sherman::personality::RoutineCandidate;
using sherman::personality::RoutineClock;
using sherman::personality::RoutineDefinition;
using sherman::personality::RoutineResult;
using sherman::personality::RoutineScheduler;
using sherman::personality::kMaximumBehaviorCandidates;
using sherman::personality::kMaximumRoutineCheckpoints;
using sherman::personality::kMaximumRoutines;

struct RuntimeHandle {
  explicit RuntimeHandle(PersonalityConfig config)
      : controller(config), policy(config) {}
  PersonalityController controller;
  BehaviorPolicy policy;
  RoutineScheduler routines;
};

RuntimeHandle* from_handle(sherman_personality_handle handle) noexcept {
  return static_cast<RuntimeHandle*>(handle);
}

bool output_size_valid(const sherman_personality_output* output) noexcept {
  return output != nullptr && output->struct_size == sizeof(*output);
}

void copy_output(const PersonalityOutput& source,
                 sherman_personality_output& destination) noexcept {
  destination.struct_size = sizeof(destination);
  destination.api_version = SHERMAN_PERSONALITY_API_VERSION;
  destination.monotonic_time_ns = source.monotonic_time_ns;
  destination.sequence = source.sequence;
  destination.expression = static_cast<std::int32_t>(source.expression);
  destination.micro_behavior =
      static_cast<std::int32_t>(source.micro_behavior);
  destination.reason_flags = source.reason_flags;
  destination.reserved = 0U;
  destination.valence = source.valence;
  destination.arousal = source.arousal;
  destination.confidence = source.confidence;
  destination.attention = source.attention;
  destination.gaze_x = source.gaze_x;
  destination.gaze_y = source.gaze_y;
  destination.eyelid_open = source.eyelid_open;
  destination.blink_rate_hz = source.blink_rate_hz;
}

PersonalityConfig copy_config(
    const sherman_personality_config& source) noexcept {
  PersonalityConfig config;
  config.seed = source.seed;
  config.curiosity = source.curiosity;
  config.sociability = source.sociability;
  config.calmness = source.calmness;
  config.expressiveness = source.expressiveness;
  config.day_activity = source.day_activity;
  return config;
}

int32_t policy_result(BehaviorPolicyResult result) noexcept {
  switch (result) {
    case BehaviorPolicyResult::Ok:
      return SHERMAN_PERSONALITY_OK;
    case BehaviorPolicyResult::InvalidInput:
    case BehaviorPolicyResult::TooManyCandidates:
      return SHERMAN_PERSONALITY_INVALID_ARGUMENT;
    case BehaviorPolicyResult::TimeRegression:
      return SHERMAN_PERSONALITY_TIME_REGRESSION;
  }
  return SHERMAN_PERSONALITY_INVALID_ARGUMENT;
}

void copy_score(const sherman::personality::BehaviorScore& source,
                sherman_personality_behavior_score& destination) noexcept {
  destination.task_value = source.task_value;
  destination.curiosity_value = source.curiosity_value;
  destination.social_value = source.social_value;
  destination.routine_value = source.routine_value;
  destination.urgency_value = source.urgency_value;
  destination.time_cost = source.time_cost;
  destination.energy_cost = source.energy_cost;
  destination.motion_cost = source.motion_cost;
  destination.risk_cost = source.risk_cost;
  destination.repetition_cost = source.repetition_cost;
  destination.failure_cost = source.failure_cost;
  destination.deterministic_variation = source.deterministic_variation;
  destination.total = source.total;
}

void copy_behavior_candidate(
    const BehaviorCandidate& source,
    sherman_personality_behavior_candidate& destination) noexcept {
  destination.struct_size = sizeof(destination);
  destination.flags = source.flags;
  destination.candidate_id = source.candidate_id;
  destination.deadline_monotonic_time_ns =
      source.deadline_monotonic_time_ns;
  destination.kind = static_cast<std::int32_t>(source.kind);
  destination.origin_flags = source.origin_flags;
  destination.task_value = source.task_value;
  destination.information_value = source.information_value;
  destination.social_value = source.social_value;
  destination.routine_pressure = source.routine_pressure;
  destination.urgency = source.urgency;
  destination.time_cost = source.time_cost;
  destination.energy_cost = source.energy_cost;
  destination.motion_cost = source.motion_cost;
  destination.risk_cost = source.risk_cost;
  destination.repetition_cost = source.repetition_cost;
  destination.recent_failure_cost = source.recent_failure_cost;
}

int32_t routine_result(RoutineResult result) noexcept {
  switch (result) {
    case RoutineResult::Ok:
      return SHERMAN_PERSONALITY_OK;
    case RoutineResult::InvalidInput:
    case RoutineResult::TooManyRoutines:
      return SHERMAN_PERSONALITY_INVALID_ARGUMENT;
    case RoutineResult::TimeRegression:
      return SHERMAN_PERSONALITY_TIME_REGRESSION;
    case RoutineResult::UnknownRoutine:
      return SHERMAN_PERSONALITY_NOT_FOUND;
    case RoutineResult::StaleOccurrence:
      return SHERMAN_PERSONALITY_STALE;
  }
  return SHERMAN_PERSONALITY_INVALID_ARGUMENT;
}

}  // namespace

extern "C" {

uint32_t sherman_personality_api_version(void) {
  return SHERMAN_PERSONALITY_API_VERSION;
}

uint32_t sherman_personality_config_size(void) {
  return sizeof(sherman_personality_config);
}

uint32_t sherman_personality_input_size(void) {
  return sizeof(sherman_personality_input);
}

uint32_t sherman_personality_output_size(void) {
  return sizeof(sherman_personality_output);
}

uint32_t sherman_personality_snapshot_size(void) {
  return sizeof(sherman_personality_snapshot);
}

uint32_t sherman_personality_behavior_context_size(void) {
  return sizeof(sherman_personality_behavior_context);
}

uint32_t sherman_personality_behavior_candidate_size(void) {
  return sizeof(sherman_personality_behavior_candidate);
}

uint32_t sherman_personality_behavior_decision_size(void) {
  return sizeof(sherman_personality_behavior_decision);
}

uint32_t sherman_personality_policy_snapshot_size(void) {
  return sizeof(sherman_personality_policy_snapshot);
}

uint32_t sherman_personality_routine_definition_size(void) {
  return sizeof(sherman_personality_routine_definition);
}

uint32_t sherman_personality_routine_clock_size(void) {
  return sizeof(sherman_personality_routine_clock);
}

uint32_t sherman_personality_routine_candidate_size(void) {
  return sizeof(sherman_personality_routine_candidate);
}

uint32_t sherman_personality_routine_snapshot_size(void) {
  return sizeof(sherman_personality_routine_snapshot);
}

int32_t sherman_personality_default_config(
    sherman_personality_config* output) {
  if (output == nullptr || output->struct_size != sizeof(*output)) {
    return SHERMAN_PERSONALITY_INVALID_ARGUMENT;
  }
  const PersonalityConfig defaults;
  output->api_version = SHERMAN_PERSONALITY_API_VERSION;
  output->seed = defaults.seed;
  output->curiosity = defaults.curiosity;
  output->sociability = defaults.sociability;
  output->calmness = defaults.calmness;
  output->expressiveness = defaults.expressiveness;
  output->day_activity = defaults.day_activity;
  return SHERMAN_PERSONALITY_OK;
}

sherman_personality_handle sherman_personality_create(
    const sherman_personality_config* config) {
  PersonalityConfig native_config;
  if (config != nullptr) {
    if (config->struct_size != sizeof(*config) ||
        config->api_version != SHERMAN_PERSONALITY_API_VERSION) {
      return nullptr;
    }
    native_config = copy_config(*config);
    if (!PersonalityController::valid_config(native_config)) {
      return nullptr;
    }
  }
  return new (std::nothrow) RuntimeHandle(native_config);
}

void sherman_personality_destroy(sherman_personality_handle handle) {
  delete from_handle(handle);
}

int32_t sherman_personality_reset(sherman_personality_handle handle,
                                  uint64_t seed) {
  RuntimeHandle* runtime = from_handle(handle);
  if (runtime == nullptr) {
    return SHERMAN_PERSONALITY_INVALID_ARGUMENT;
  }
  runtime->controller.reset(seed);
  runtime->policy.reset(seed);
  runtime->routines.reset_progress();
  return SHERMAN_PERSONALITY_OK;
}

int32_t sherman_personality_apply_event(sherman_personality_handle handle,
                                        int32_t event, float strength) {
  RuntimeHandle* runtime = from_handle(handle);
  if (runtime == nullptr) {
    return SHERMAN_PERSONALITY_INVALID_ARGUMENT;
  }
  const PersonalityEventResult result = runtime->controller.apply(
      static_cast<PersonalityEvent>(event), strength);
  switch (result) {
    case PersonalityEventResult::Accepted:
      return SHERMAN_PERSONALITY_OK;
    case PersonalityEventResult::CooledDown:
      return SHERMAN_PERSONALITY_COOLDOWN;
    case PersonalityEventResult::InvalidInput:
      return SHERMAN_PERSONALITY_INVALID_ARGUMENT;
  }
  return SHERMAN_PERSONALITY_INVALID_ARGUMENT;
}

int32_t sherman_personality_step(sherman_personality_handle handle,
                                 const sherman_personality_input* input,
                                 sherman_personality_output* output) {
  RuntimeHandle* runtime = from_handle(handle);
  if (runtime == nullptr || input == nullptr ||
      input->struct_size != sizeof(*input) || input->reserved != 0U ||
      !output_size_valid(output)) {
    return SHERMAN_PERSONALITY_INVALID_ARGUMENT;
  }
  PersonalityInput native_input;
  native_input.monotonic_time_ns = input->monotonic_time_ns;
  native_input.local_second_of_day = input->local_second_of_day;
  native_input.flags = input->flags;
  native_input.activity_load = input->activity_load;
  native_input.task_engagement = input->task_engagement;
  native_input.social_engagement = input->social_engagement;
  native_input.novelty = input->novelty;
  native_input.external_urgency = input->external_urgency;
  native_input.attention_target_x = input->attention_target_x;
  native_input.attention_target_y = input->attention_target_y;
  native_input.attention_salience = input->attention_salience;

  const PersonalityStepResult result = runtime->controller.step(native_input);
  if (result == PersonalityStepResult::Ok) {
    copy_output(runtime->controller.output(), *output);
    return SHERMAN_PERSONALITY_OK;
  }
  copy_output(PersonalityController::safe_output(input->monotonic_time_ns),
              *output);
  return result == PersonalityStepResult::TimeRegression
             ? SHERMAN_PERSONALITY_TIME_REGRESSION
             : SHERMAN_PERSONALITY_INVALID_ARGUMENT;
}

int32_t sherman_personality_get_output(sherman_personality_handle handle,
                                       sherman_personality_output* output) {
  RuntimeHandle* runtime = from_handle(handle);
  if (runtime == nullptr || !output_size_valid(output)) {
    return SHERMAN_PERSONALITY_INVALID_ARGUMENT;
  }
  copy_output(runtime->controller.output(), *output);
  return SHERMAN_PERSONALITY_OK;
}

int32_t sherman_personality_snapshot_state(
    sherman_personality_handle handle,
    sherman_personality_snapshot* output) {
  RuntimeHandle* runtime = from_handle(handle);
  if (runtime == nullptr || output == nullptr ||
      output->struct_size != sizeof(*output)) {
    return SHERMAN_PERSONALITY_INVALID_ARGUMENT;
  }
  const PersistedPersonalityState state = runtime->controller.snapshot();
  output->snapshot_version = SHERMAN_PERSONALITY_SNAPSHOT_VERSION;
  output->rng_state = state.rng_state;
  output->sequence = state.sequence;
  output->total_awake_s = state.total_awake_s;
  output->since_interaction_s = state.since_interaction_s;
  output->since_engagement_s = state.since_engagement_s;
  output->idle_delay_remaining_s = state.idle_delay_remaining_s;
  output->energy = state.emotion.needs.energy;
  output->curiosity = state.emotion.needs.curiosity;
  output->social_engagement = state.emotion.needs.social_engagement;
  output->confidence = state.emotion.needs.confidence;
  output->frustration = state.emotion.needs.frustration;
  output->urgency = state.emotion.needs.urgency;
  output->valence = state.emotion.valence;
  output->arousal = state.emotion.arousal;
  output->mood = static_cast<std::int32_t>(state.emotion.mood);
  output->reserved = 0U;
  return SHERMAN_PERSONALITY_OK;
}

int32_t sherman_personality_restore(
    sherman_personality_handle handle,
    const sherman_personality_snapshot* snapshot) {
  RuntimeHandle* runtime = from_handle(handle);
  if (runtime == nullptr || snapshot == nullptr ||
      snapshot->struct_size != sizeof(*snapshot) ||
      snapshot->snapshot_version != SHERMAN_PERSONALITY_SNAPSHOT_VERSION ||
      snapshot->reserved != 0U) {
    return SHERMAN_PERSONALITY_INCOMPATIBLE;
  }
  PersistedPersonalityState state;
  state.version = PersistedPersonalityState::kCurrentVersion;
  state.rng_state = snapshot->rng_state;
  state.sequence = snapshot->sequence;
  state.total_awake_s = snapshot->total_awake_s;
  state.since_interaction_s = snapshot->since_interaction_s;
  state.since_engagement_s = snapshot->since_engagement_s;
  state.idle_delay_remaining_s = snapshot->idle_delay_remaining_s;
  state.emotion.version = PersistedEmotionState::kCurrentVersion;
  state.emotion.needs = Needs{snapshot->energy,
                              snapshot->curiosity,
                              snapshot->social_engagement,
                              snapshot->confidence,
                              snapshot->frustration,
                              snapshot->urgency};
  state.emotion.mood = static_cast<Mood>(snapshot->mood);
  state.emotion.valence = snapshot->valence;
  state.emotion.arousal = snapshot->arousal;
  return runtime->controller.restore(state) ? SHERMAN_PERSONALITY_OK
                                            : SHERMAN_PERSONALITY_INCOMPATIBLE;
}

int32_t sherman_personality_safe_output(uint64_t monotonic_time_ns,
                                        sherman_personality_output* output) {
  if (!output_size_valid(output)) {
    return SHERMAN_PERSONALITY_INVALID_ARGUMENT;
  }
  copy_output(PersonalityController::safe_output(monotonic_time_ns), *output);
  return SHERMAN_PERSONALITY_OK;
}

int32_t sherman_personality_select_behavior(
    sherman_personality_handle handle,
    const sherman_personality_behavior_context* context,
    const sherman_personality_behavior_candidate* candidates,
    uint32_t candidate_count,
    sherman_personality_behavior_decision* decision) {
  RuntimeHandle* runtime = from_handle(handle);
  if (runtime == nullptr || context == nullptr || decision == nullptr ||
      context->struct_size != sizeof(*context) ||
      context->reserved != 0U ||
      decision->struct_size != sizeof(*decision) ||
      candidate_count > kMaximumBehaviorCandidates ||
      (candidate_count > 0U && candidates == nullptr)) {
    return SHERMAN_PERSONALITY_INVALID_ARGUMENT;
  }

  BehaviorPolicyContext native_context;
  native_context.monotonic_time_ns = context->monotonic_time_ns;
  native_context.current_candidate_id = context->current_candidate_id;
  native_context.flags = context->flags;
  // The latest personality tick is authoritative for behavioral quiet even
  // when a caller forgets to copy its circadian/explicit quiet into context.
  if ((runtime->controller.output().reason_flags &
       (sherman::personality::kReasonCircadianQuiet |
        sherman::personality::kReasonExplicitQuiet)) != 0U) {
    native_context.flags |= sherman::personality::kPolicyQuiet;
  }
  native_context.current_action_age_s = context->current_action_age_s;
  std::array<BehaviorCandidate, kMaximumBehaviorCandidates> native_candidates{};
  for (std::uint32_t index = 0; index < candidate_count; ++index) {
    if (candidates[index].struct_size != sizeof(candidates[index])) {
      return SHERMAN_PERSONALITY_INVALID_ARGUMENT;
    }
    BehaviorCandidate& native = native_candidates[index];
    native.candidate_id = candidates[index].candidate_id;
    native.deadline_monotonic_time_ns =
        candidates[index].deadline_monotonic_time_ns;
    native.kind = static_cast<BehaviorKind>(candidates[index].kind);
    native.origin_flags = candidates[index].origin_flags;
    native.flags = candidates[index].flags;
    native.task_value = candidates[index].task_value;
    native.information_value = candidates[index].information_value;
    native.social_value = candidates[index].social_value;
    native.routine_pressure = candidates[index].routine_pressure;
    native.urgency = candidates[index].urgency;
    native.time_cost = candidates[index].time_cost;
    native.energy_cost = candidates[index].energy_cost;
    native.motion_cost = candidates[index].motion_cost;
    native.risk_cost = candidates[index].risk_cost;
    native.repetition_cost = candidates[index].repetition_cost;
    native.recent_failure_cost = candidates[index].recent_failure_cost;
  }

  BehaviorDecision native_decision;
  const BehaviorPolicyResult result = runtime->policy.select(
      native_context, runtime->controller.emotion().needs(),
      native_candidates.data(), candidate_count, native_decision);
  const int32_t status = policy_result(result);
  if (status != SHERMAN_PERSONALITY_OK) {
    return status;
  }
  decision->api_version = SHERMAN_PERSONALITY_API_VERSION;
  decision->selected_candidate_id = native_decision.selected_candidate_id;
  decision->runner_up_candidate_id = native_decision.runner_up_candidate_id;
  decision->selected_kind =
      static_cast<std::int32_t>(native_decision.selected_kind);
  decision->reason_flags = native_decision.reason_flags;
  decision->candidate_count = native_decision.candidate_count;
  decision->eligible_count = native_decision.eligible_count;
  copy_score(native_decision.selected_score, decision->selected_score);
  decision->runner_up_score = native_decision.runner_up_score;
  decision->reserved = 0U;
  return SHERMAN_PERSONALITY_OK;
}

int32_t sherman_personality_snapshot_policy(
    sherman_personality_handle handle,
    sherman_personality_policy_snapshot* output) {
  RuntimeHandle* runtime = from_handle(handle);
  if (runtime == nullptr || output == nullptr ||
      output->struct_size != sizeof(*output)) {
    return SHERMAN_PERSONALITY_INVALID_ARGUMENT;
  }
  const PersistedBehaviorPolicyState state = runtime->policy.snapshot();
  output->snapshot_version = SHERMAN_PERSONALITY_POLICY_SNAPSHOT_VERSION;
  output->last_selected_candidate_id = state.last_selected_candidate_id;
  output->last_selected_kind =
      static_cast<std::int32_t>(state.last_selected_kind);
  output->seen_kind_mask = state.seen_kind_mask;
  for (std::size_t index = 0;
       index < state.seconds_since_kind_selected.size(); ++index) {
    output->seconds_since_kind_selected[index] =
        state.seconds_since_kind_selected[index];
  }
  return SHERMAN_PERSONALITY_OK;
}

int32_t sherman_personality_restore_policy(
    sherman_personality_handle handle,
    const sherman_personality_policy_snapshot* snapshot) {
  RuntimeHandle* runtime = from_handle(handle);
  if (runtime == nullptr || snapshot == nullptr ||
      snapshot->struct_size != sizeof(*snapshot) ||
      snapshot->snapshot_version != SHERMAN_PERSONALITY_POLICY_SNAPSHOT_VERSION ||
      snapshot->seen_kind_mask >= (1U << SHERMAN_PERSONALITY_BEHAVIOR_KIND_COUNT)) {
    return SHERMAN_PERSONALITY_INCOMPATIBLE;
  }
  PersistedBehaviorPolicyState state;
  state.version = PersistedBehaviorPolicyState::kCurrentVersion;
  state.last_selected_candidate_id = snapshot->last_selected_candidate_id;
  state.last_selected_kind =
      static_cast<BehaviorKind>(snapshot->last_selected_kind);
  state.seen_kind_mask =
      static_cast<std::uint16_t>(snapshot->seen_kind_mask);
  for (std::size_t index = 0;
       index < state.seconds_since_kind_selected.size(); ++index) {
    state.seconds_since_kind_selected[index] =
        snapshot->seconds_since_kind_selected[index];
  }
  return runtime->policy.restore(state) ? SHERMAN_PERSONALITY_OK
                                        : SHERMAN_PERSONALITY_INCOMPATIBLE;
}

int32_t sherman_personality_set_routines(
    sherman_personality_handle handle,
    const sherman_personality_routine_definition* definitions,
    uint32_t routine_count) {
  RuntimeHandle* runtime = from_handle(handle);
  if (runtime == nullptr || routine_count > kMaximumRoutines ||
      (routine_count > 0U && definitions == nullptr)) {
    return SHERMAN_PERSONALITY_INVALID_ARGUMENT;
  }
  std::array<RoutineDefinition, kMaximumRoutines> native{};
  for (std::uint32_t index = 0; index < routine_count; ++index) {
    if (definitions[index].struct_size != sizeof(definitions[index])) {
      return SHERMAN_PERSONALITY_INVALID_ARGUMENT;
    }
    native[index].routine_id = definitions[index].routine_id;
    native[index].local_start_second = definitions[index].local_start_second;
    native[index].window_duration_s = definitions[index].window_duration_s;
    native[index].catch_up_duration_s =
        definitions[index].catch_up_duration_s;
    native[index].completion_cooldown_s =
        definitions[index].completion_cooldown_s;
    native[index].flags = definitions[index].flags;
    native[index].missed_policy =
        static_cast<sherman::personality::MissedRoutinePolicy>(
            definitions[index].missed_policy);
    native[index].checkpoint_count = definitions[index].checkpoint_count;
    for (std::size_t checkpoint = 0;
         checkpoint < kMaximumRoutineCheckpoints; ++checkpoint) {
      native[index].checkpoint_kinds[checkpoint] =
          static_cast<BehaviorKind>(
              definitions[index].checkpoint_kinds[checkpoint]);
    }
    native[index].base_priority = definitions[index].base_priority;
    native[index].task_value = definitions[index].task_value;
    native[index].information_value = definitions[index].information_value;
    native[index].social_value = definitions[index].social_value;
    native[index].urgency = definitions[index].urgency;
  }
  return routine_result(
      runtime->routines.configure(native.data(), routine_count));
}

int32_t sherman_personality_collect_routine_candidates(
    sherman_personality_handle handle,
    const sherman_personality_routine_clock* clock,
    sherman_personality_routine_candidate* output,
    uint32_t output_capacity,
    uint32_t* output_count) {
  RuntimeHandle* runtime = from_handle(handle);
  if (runtime == nullptr || clock == nullptr || output_count == nullptr ||
      clock->struct_size != sizeof(*clock) ||
      clock->reserved != 0U ||
      output_capacity > kMaximumRoutines ||
      (output_capacity > 0U && output == nullptr)) {
    return SHERMAN_PERSONALITY_INVALID_ARGUMENT;
  }
  for (std::uint32_t index = 0; index < output_capacity; ++index) {
    if (output[index].struct_size != sizeof(output[index])) {
      return SHERMAN_PERSONALITY_INVALID_ARGUMENT;
    }
  }
  RoutineClock native_clock;
  native_clock.monotonic_time_ns = clock->monotonic_time_ns;
  native_clock.civil_day_id = clock->civil_day_id;
  native_clock.local_second_of_day = clock->local_second_of_day;
  native_clock.flags = clock->flags;
  std::array<RoutineCandidate, kMaximumRoutines> native_output{};
  std::size_t native_count = 0U;
  const RoutineResult result = runtime->routines.collect(
      native_clock, native_output.data(), output_capacity, native_count);
  const int32_t status = routine_result(result);
  if (status != SHERMAN_PERSONALITY_OK) {
    *output_count = 0U;
    return status;
  }
  *output_count = static_cast<std::uint32_t>(native_count);
  for (std::size_t index = 0; index < native_count; ++index) {
    output[index].struct_size = sizeof(output[index]);
    output[index].checkpoint_index = native_output[index].checkpoint_index;
    output[index].routine_id = native_output[index].routine_id;
    output[index].occurrence_day_id =
        native_output[index].occurrence_day_id;
    output[index].catch_up = native_output[index].catch_up ? 1U : 0U;
    output[index].reserved = 0U;
    copy_behavior_candidate(native_output[index].behavior,
                            output[index].behavior);
  }
  return SHERMAN_PERSONALITY_OK;
}

int32_t sherman_personality_mark_routine_result(
    sherman_personality_handle handle, uint64_t routine_id,
    int64_t occurrence_day_id, uint32_t checkpoint_index, uint32_t success) {
  RuntimeHandle* runtime = from_handle(handle);
  if (runtime == nullptr || success > 1U) {
    return SHERMAN_PERSONALITY_INVALID_ARGUMENT;
  }
  return routine_result(runtime->routines.mark_result(
      routine_id, occurrence_day_id, checkpoint_index, success != 0U));
}

int32_t sherman_personality_snapshot_routines(
    sherman_personality_handle handle,
    sherman_personality_routine_snapshot* output) {
  RuntimeHandle* runtime = from_handle(handle);
  if (runtime == nullptr || output == nullptr ||
      output->struct_size != sizeof(*output)) {
    return SHERMAN_PERSONALITY_INVALID_ARGUMENT;
  }
  const PersistedRoutineState state = runtime->routines.snapshot();
  output->snapshot_version = state.version;
  output->routine_count = state.routine_count;
  output->reserved = 0U;
  for (std::size_t index = 0; index < kMaximumRoutines; ++index) {
    output->entries[index].routine_id = state.entries[index].routine_id;
    output->entries[index].last_completed_day_id =
        state.entries[index].last_completed_day_id;
    output->entries[index].active_occurrence_day_id =
        state.entries[index].active_occurrence_day_id;
    output->entries[index].cooldown_remaining_s =
        state.entries[index].cooldown_remaining_s;
    output->entries[index].next_checkpoint_index =
        state.entries[index].next_checkpoint_index;
    output->entries[index].has_completed =
        state.entries[index].has_completed ? 1U : 0U;
    output->entries[index].has_active_occurrence =
        state.entries[index].has_active_occurrence ? 1U : 0U;
  }
  return SHERMAN_PERSONALITY_OK;
}

int32_t sherman_personality_restore_routines(
    sherman_personality_handle handle,
    const sherman_personality_routine_snapshot* snapshot) {
  RuntimeHandle* runtime = from_handle(handle);
  if (runtime == nullptr || snapshot == nullptr ||
      snapshot->struct_size != sizeof(*snapshot) ||
      snapshot->snapshot_version !=
          PersistedRoutineState::kCurrentVersion ||
      snapshot->routine_count > kMaximumRoutines || snapshot->reserved != 0U) {
    return SHERMAN_PERSONALITY_INCOMPATIBLE;
  }
  PersistedRoutineState state;
  state.version = PersistedRoutineState::kCurrentVersion;
  state.routine_count = static_cast<std::uint16_t>(snapshot->routine_count);
  for (std::size_t index = 0; index < kMaximumRoutines; ++index) {
    if (snapshot->entries[index].has_completed > 1U ||
        snapshot->entries[index].has_active_occurrence > 1U) {
      return SHERMAN_PERSONALITY_INCOMPATIBLE;
    }
    state.entries[index].routine_id = snapshot->entries[index].routine_id;
    state.entries[index].last_completed_day_id =
        snapshot->entries[index].last_completed_day_id;
    state.entries[index].active_occurrence_day_id =
        snapshot->entries[index].active_occurrence_day_id;
    state.entries[index].cooldown_remaining_s =
        snapshot->entries[index].cooldown_remaining_s;
    state.entries[index].next_checkpoint_index =
        snapshot->entries[index].next_checkpoint_index;
    state.entries[index].has_completed =
        snapshot->entries[index].has_completed != 0U;
    state.entries[index].has_active_occurrence =
        snapshot->entries[index].has_active_occurrence != 0U;
  }
  return runtime->routines.restore(state)
             ? SHERMAN_PERSONALITY_OK
             : SHERMAN_PERSONALITY_INCOMPATIBLE;
}

}  // extern "C"
