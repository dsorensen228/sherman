#include "sherman/personality/policy.hpp"
#include "sherman/personality/routine.hpp"
#include "sherman/personality/runtime.hpp"

#include <cmath>
#include <cstdint>
#include <cstdlib>
#include <iostream>
#include <limits>
#include <set>
#include <string_view>

namespace {

using namespace sherman::personality;

int failures = 0;

void expect(bool condition, std::string_view message) {
  if (!condition) {
    std::cerr << "FAIL: " << message << '\n';
    ++failures;
  }
}

bool near(float left, float right, float tolerance = 0.0001F) {
  return std::fabs(left - right) <= tolerance;
}

bool bounded(const PersonalityOutput& output) {
  const float unit_values[] = {output.arousal, output.confidence,
                               output.attention, output.eyelid_open};
  for (float value : unit_values) {
    if (!std::isfinite(value) || value < 0.0F || value > 1.0F) {
      return false;
    }
  }
  const auto mood = static_cast<std::int32_t>(output.expression);
  const auto micro = static_cast<std::int32_t>(output.micro_behavior);
  return std::isfinite(output.valence) && output.valence >= -1.0F &&
         output.valence <= 1.0F && std::isfinite(output.gaze_x) &&
         output.gaze_x >= -1.0F && output.gaze_x <= 1.0F &&
         std::isfinite(output.gaze_y) && output.gaze_y >= -1.0F &&
         output.gaze_y <= 1.0F && std::isfinite(output.blink_rate_hz) &&
         output.blink_rate_hz >= 0.0F && output.blink_rate_hz <= 0.40F &&
         mood >= 0 && mood < static_cast<std::int32_t>(Mood::Count) &&
         micro >= 0 && micro < static_cast<std::int32_t>(MicroBehavior::Count);
}

PersonalityInput input_at(std::uint64_t time_ns) {
  PersonalityInput input;
  input.monotonic_time_ns = time_ns;
  input.flags = kInputCircadianValid;
  input.local_second_of_day = 12U * 3600U;
  return input;
}

BehaviorCandidate candidate(std::uint64_t id, BehaviorKind kind) {
  BehaviorCandidate result;
  result.candidate_id = id;
  result.kind = kind;
  return result;
}

void test_idle_is_deterministic_bounded_and_varied() {
  PersonalityConfig config;
  config.seed = 42;
  PersonalityController left(config);
  PersonalityController right(config);
  std::set<MicroBehavior> behaviors;
  bool saw_non_center_gaze = false;
  for (std::uint64_t tick = 0; tick < 6000; ++tick) {
    PersonalityInput input = input_at(tick * UINT64_C(100000000));
    expect(left.step(input) == PersonalityStepResult::Ok,
           "left deterministic idle step succeeds");
    expect(right.step(input) == PersonalityStepResult::Ok,
           "right deterministic idle step succeeds");
    const auto& a = left.output();
    const auto& b = right.output();
    expect(a.sequence == b.sequence && a.expression == b.expression &&
               a.micro_behavior == b.micro_behavior &&
               near(a.gaze_x, b.gaze_x) && near(a.gaze_y, b.gaze_y),
           "same seed and inputs produce identical intent");
    expect(bounded(a), "idle output stays bounded");
    behaviors.insert(a.micro_behavior);
    saw_non_center_gaze = saw_non_center_gaze || std::fabs(a.gaze_x) > 0.2F;
  }
  expect(behaviors.count(MicroBehavior::Settled) != 0U,
         "idle includes settled presence");
  expect(behaviors.count(MicroBehavior::Orienting) != 0U,
         "idle includes orientation beats");
  expect(behaviors.count(MicroBehavior::Observing) != 0U,
         "idle includes observation beats");
  expect(saw_non_center_gaze, "idle gaze explores away from center");

  config.seed = 43;
  PersonalityController different(config);
  config.seed = 42;
  PersonalityController reference(config);
  bool differed = false;
  for (std::uint64_t tick = 0; tick < 300; ++tick) {
    const PersonalityInput input = input_at(tick * UINT64_C(100000000));
    different.step(input);
    reference.step(input);
    if (!near(different.output().gaze_x, reference.output().gaze_x) ||
        different.output().micro_behavior !=
            reference.output().micro_behavior) {
      differed = true;
      break;
    }
  }
  expect(differed, "different seed changes allowed idle choices");
}

void test_attention_task_interaction_and_outcomes() {
  PersonalityController controller;
  controller.step(input_at(0));
  PersonalityInput attention = input_at(UINT64_C(100000000));
  attention.flags |= kInputAttentionValid | kInputUserPresent;
  attention.attention_target_x = 0.8F;
  attention.attention_target_y = -0.3F;
  attention.attention_salience = 1.0F;
  for (int tick = 1; tick <= 8; ++tick) {
    attention.monotonic_time_ns =
        static_cast<std::uint64_t>(tick) * UINT64_C(100000000);
    controller.step(attention);
  }
  expect(controller.output().micro_behavior == MicroBehavior::Engaged,
         "salient user attention engages");
  expect(controller.output().gaze_x > 0.65F &&
             controller.output().gaze_y < -0.20F,
         "semantic attention target drives gaze");
  expect((controller.output().reason_flags & kReasonExternalAttention) != 0U,
         "attention has an inspectable reason");

  expect(controller.apply(PersonalityEvent::InteractionStarted) ==
             PersonalityEventResult::Accepted,
         "interaction start is accepted");
  PersonalityInput neutral = input_at(UINT64_C(900000000));
  controller.step(neutral);
  expect(controller.output().micro_behavior == MicroBehavior::Engaged,
         "active interaction remains engaged without fake target");
  expect((controller.output().reason_flags & kReasonRecentInteraction) != 0U,
         "recent interaction is explained");
  expect(controller.apply(PersonalityEvent::InteractionEnded) ==
             PersonalityEventResult::Accepted,
         "interaction end is accepted");
  neutral.monotonic_time_ns = UINT64_C(2500000000);
  controller.step(neutral);
  expect(controller.output().micro_behavior == MicroBehavior::Reflecting,
         "ended interaction has a bounded reflective beat");

  PersonalityInput task = input_at(UINT64_C(2600000000));
  task.flags |= kInputTaskActive;
  for (int tick = 27; tick <= 31; ++tick) {
    task.monotonic_time_ns =
        static_cast<std::uint64_t>(tick) * UINT64_C(100000000);
    controller.step(task);
  }
  expect(controller.output().expression == Mood::Focused,
         "semantic active task becomes focused");
  expect((controller.output().reason_flags & kReasonTaskEngaged) != 0U,
         "task focus is explained");

  controller.step(input_at(UINT64_C(3400000000)));
  expect(controller.apply(PersonalityEvent::TaskSucceeded) ==
             PersonalityEventResult::Accepted,
         "task success is accepted");
  for (int tick = 35; tick <= 39; ++tick) {
    controller.step(input_at(static_cast<std::uint64_t>(tick) *
                             UINT64_C(100000000)));
  }
  expect(controller.output().expression == Mood::Pleased,
         "real outcome produces pleased intent");
  expect((controller.output().reason_flags & kReasonRecentOutcome) != 0U,
         "outcome expression is explained");
}

void test_sleep_boundaries_attention_restart_and_policy() {
  PersonalityController controller;
  const std::uint32_t seconds[] = {0U, 7199U, 7200U, 10800U, 28799U, 28800U, 71100U, 86399U};
  for (std::size_t index = 0; index < 8; ++index) {
    auto input = input_at(index * UINT64_C(1000000000));
    input.local_second_of_day = seconds[index];
    input.flags |= kInputAttentionValid | kInputTaskActive | kInputPaused;
    input.attention_salience = 1.0F;
    input.attention_target_x = 1.0F;
    controller.apply(PersonalityEvent::InteractionStarted);
    expect(controller.step(input) == PersonalityStepResult::Ok, "boundary tick succeeds");
    const auto& output = controller.output();
    if (index >= 2 && index < 5) {
      expect(output.micro_behavior == MicroBehavior::Drowsy &&
                 output.eyelid_open == 0.0F && output.blink_rate_hz == 0.0F &&
                 output.gaze_x == 0.0F && output.gaze_y == 0.0F,
             "quiet sleep wins over task, interaction, attention and pause");
    } else {
      expect((output.reason_flags & kReasonCircadianQuiet) == 0U &&
                 output.eyelid_open > 0.0F, "quiet boundaries are start-inclusive/end-exclusive");
    }
  }
  PersonalityController restarted;
  expect(restarted.restore(controller.snapshot()), "sleep-compatible snapshot restores");
  auto input = input_at(0);
  input.local_second_of_day = 3U * 3600U;
  restarted.step(input);
  expect(restarted.output().eyelid_open == 0.0F, "night restart requests sleep immediately");
  input.flags = kInputQuiet;
  input.monotonic_time_ns += UINT64_C(1000000000);
  restarted.step(input);
  expect(restarted.output().eyelid_open == 0.0F, "explicit quiet works without civil time");
  input.flags = 0U;
  input.monotonic_time_ns += UINT64_C(1000000000);
  restarted.step(input);
  expect(restarted.output().eyelid_open > 0.0F, "invalid civil clock alone cannot schedule sleep");

  BehaviorPolicy policy;
  BehaviorPolicyContext context;
  context.flags = kPolicyQuiet | kPolicyCurrentActionActive;
  context.current_candidate_id = 1;
  // Every kind, even urgent non-interruptible Jarvis work labeled quiet-safe.
  for (int kind = 0; kind < static_cast<int>(BehaviorKind::Count); ++kind) {
    auto choice = candidate(1, static_cast<BehaviorKind>(kind));
    choice.flags &= ~kCandidateInterruptible;
    choice.origin_flags = kOriginJarvis;
    choice.task_value = choice.urgency = 1.0F;
    BehaviorDecision decision;
    policy.select(context, Needs{}, &choice, 1, decision);
    const bool resting = choice.kind == BehaviorKind::Wait || choice.kind == BehaviorKind::Rest;
    expect(decision.eligible_count == (resting ? 1U : 0U),
           "sleep permits only stationary wait/rest regardless of commitment");
    choice.motion_cost = 0.01F;
    policy.select(context, Needs{}, &choice, 1, decision);
    expect(decision.eligible_count == 0U, "no declared motion cost is accepted in sleep");
  }
}

void test_quiet_pause_circadian_and_invalid_input() {
  PersonalityController controller;
  controller.step(input_at(0));
  PersonalityInput quiet = input_at(UINT64_C(1000000000));
  quiet.local_second_of_day = 3U * 3600U;
  controller.step(quiet);
  expect(controller.output().micro_behavior == MicroBehavior::Drowsy,
         "nighttime circadian input becomes drowsy");
  expect(controller.output().eyelid_open <= 0.72F,
         "nighttime lowers eyelids");
  expect((controller.output().reason_flags & kReasonCircadianQuiet) != 0U,
         "circadian quiet is explained");

  PersonalityInput paused = input_at(UINT64_C(2000000000));
  paused.flags |= kInputPaused;
  for (int tick = 2; tick <= 80; ++tick) {
    paused.monotonic_time_ns =
        static_cast<std::uint64_t>(tick) * UINT64_C(1000000000);
    controller.step(paused);
    expect(controller.output().micro_behavior == MicroBehavior::Settled,
           "pause suppresses spontaneous behaviors");
    expect((controller.output().reason_flags & kReasonPaused) != 0U,
           "pause is explicit in output");
  }
  expect(std::fabs(controller.output().gaze_x) < 0.01F,
         "paused gaze returns to center");

  const auto before = controller.snapshot();
  PersonalityInput invalid = paused;
  invalid.monotonic_time_ns += UINT64_C(1000000000);
  invalid.novelty = std::numeric_limits<float>::quiet_NaN();
  expect(controller.step(invalid) == PersonalityStepResult::InvalidInput,
         "non-finite input is rejected");
  expect(controller.snapshot().sequence == before.sequence,
         "rejected input does not advance state");
  invalid = paused;
  invalid.monotonic_time_ns = 0;
  expect(controller.step(invalid) == PersonalityStepResult::TimeRegression,
         "monotonic regression is rejected");
  expect((PersonalityController::safe_output(123).reason_flags &
          kReasonFallback) != 0U,
         "explicit fallback output is safe and diagnosable");

  invalid = paused;
  invalid.monotonic_time_ns = UINT64_C(82000000000);
  invalid.novelty = 1.01F;
  expect(controller.step(invalid) == PersonalityStepResult::InvalidInput,
         "out-of-range unit semantic input is rejected");
  invalid = paused;
  invalid.monotonic_time_ns = UINT64_C(82000000000);
  invalid.flags |= kInputAttentionValid;
  invalid.attention_target_x = -1.01F;
  expect(controller.step(invalid) == PersonalityStepResult::InvalidInput,
         "out-of-range valid attention target is rejected");
}

void test_restart_policy_and_accelerated_week() {
  PersonalityController original;
  original.step(input_at(0));
  original.apply(PersonalityEvent::TaskSucceeded);
  for (std::uint64_t tick = 1; tick < 30; ++tick) {
    original.step(input_at(tick * UINT64_C(100000000)));
  }
  const auto state = original.snapshot();
  PersonalityController restored;
  expect(restored.restore(state), "valid runtime snapshot restores");
  expect(restored.snapshot().sequence == state.sequence,
         "sequence survives restart");
  expect(near(restored.snapshot().emotion.needs.confidence,
              state.emotion.needs.confidence),
         "durable needs survive restart");
  expect(restored.output().micro_behavior == MicroBehavior::Settled &&
             near(restored.output().gaze_x, 0.0F),
         "restart never resumes a transient physical presentation");

  auto corrupt = state;
  corrupt.since_interaction_s =
      std::numeric_limits<float>::quiet_NaN();
  expect(!restored.restore(corrupt), "corrupt runtime snapshot is rejected");
  expect(bounded(restored.output()), "corrupt restore leaves safe output");

  PersonalityController week;
  std::set<MicroBehavior> observed;
  constexpr std::uint64_t kMinuteNs = UINT64_C(60000000000);
  for (std::uint64_t minute = 0; minute <= 7U * 24U * 60U; ++minute) {
    PersonalityInput input = input_at(minute * kMinuteNs);
    input.local_second_of_day =
        static_cast<std::uint32_t>((minute % (24U * 60U)) * 60U);
    expect(week.step(input) == PersonalityStepResult::Ok,
           "accelerated week step succeeds");
    expect(bounded(week.output()), "accelerated week stays bounded");
    observed.insert(week.output().micro_behavior);
  }
  expect(observed.count(MicroBehavior::Drowsy) != 0U,
         "week includes circadian rest behavior");
  expect(observed.count(MicroBehavior::Observing) != 0U,
         "week includes awake observation behavior");
}

void test_policy_sources_costs_and_explanations() {
  PersonalityConfig config;
  config.seed = 99;
  BehaviorPolicy policy(config);
  Needs needs;
  BehaviorPolicyContext context;
  context.monotonic_time_ns = UINT64_C(1000000000);

  BehaviorCandidate choices[4] = {
      candidate(1, BehaviorKind::Wait),
      candidate(2, BehaviorKind::Observe),
      candidate(3, BehaviorKind::InspectChange),
      candidate(4, BehaviorKind::Acknowledge),
  };
  choices[0].task_value = 0.10F;
  choices[1].origin_flags = kOriginRoutine;
  choices[1].routine_pressure = 0.82F;
  choices[2].origin_flags = kOriginWorldChange;
  choices[2].information_value = 0.72F;
  choices[2].risk_cost = 0.15F;
  choices[3].origin_flags = kOriginJarvis;
  choices[3].task_value = 0.92F;
  choices[3].social_value = 0.45F;

  BehaviorDecision decision;
  expect(policy.select(context, needs, choices, 4, decision) ==
             BehaviorPolicyResult::Ok,
         "multi-source policy selection succeeds");
  expect(decision.selected_candidate_id == 4,
         "high-value Jarvis acknowledgement wins");
  expect((decision.reason_flags & kBehaviorJarvisRequest) != 0U,
         "Jarvis origin is explained");
  expect(decision.eligible_count == 4 && decision.runner_up_candidate_id != 0,
         "selection reports bounded alternatives");

  choices[3].risk_cost = 1.0F;
  choices[3].recent_failure_cost = 1.0F;
  context.monotonic_time_ns += UINT64_C(5000000000);
  expect(policy.select(context, needs, choices, 4, decision) ==
             BehaviorPolicyResult::Ok,
         "cost counterfactual selection succeeds");
  expect(decision.selected_candidate_id != 4,
         "risk and recent failure reduce retry utility");
  expect((decision.reason_flags &
          (kBehaviorRoutineDue | kBehaviorWorldChange)) != 0U,
         "selected local work retains its origin explanation");
}

void test_policy_admission_commitment_repetition_and_persistence() {
  BehaviorPolicy policy;
  Needs needs;
  BehaviorCandidate motion = candidate(1, BehaviorKind::Patrol);
  motion.flags = kCandidateAvailable | kCandidateInterruptible;
  motion.task_value = 0.8F;
  motion.motion_cost = 0.2F;
  BehaviorCandidate rest = candidate(2, BehaviorKind::Rest);
  rest.task_value = 0.25F;

  BehaviorPolicyContext context;
  context.flags = kPolicyQuiet | kPolicyPaused;
  BehaviorCandidate choices[] = {motion, rest};
  BehaviorDecision decision;
  expect(policy.select(context, needs, choices, 2, decision) ==
             BehaviorPolicyResult::Ok,
         "quiet paused policy selection succeeds");
  expect(decision.selected_candidate_id == 2 && decision.eligible_count == 1,
         "quiet and pause suppress disallowed motion");

  needs.energy = 0.10F;
  context.flags = 0;
  context.monotonic_time_ns = UINT64_C(1000000000);
  expect(policy.select(context, needs, choices, 2, decision) ==
             BehaviorPolicyResult::Ok,
         "low-energy policy selection succeeds");
  expect(decision.selected_candidate_id == 2,
         "low energy suppresses incompatible curiosity motion");

  BehaviorPolicy commitment;
  needs = {};
  BehaviorCandidate current = candidate(10, BehaviorKind::Observe);
  current.task_value = 0.70F;
  BehaviorCandidate challenger = candidate(11, BehaviorKind::Report);
  challenger.task_value = 0.80F;
  BehaviorCandidate pair[] = {current, challenger};
  context = {};
  context.current_candidate_id = 10;
  context.current_action_age_s = 0.3F;
  context.flags =
      kPolicyCurrentActionActive | kPolicyCurrentActionInterruptible;
  expect(commitment.select(context, needs, pair, 2, decision) ==
             BehaviorPolicyResult::Ok,
         "commitment decision succeeds");
  expect(decision.selected_candidate_id == 10 &&
             (decision.reason_flags & kBehaviorRetainedCommitment) != 0U,
         "near challenger cannot cause early twitching");

  BehaviorPolicy repetition;
  BehaviorCandidate repeated = candidate(20, BehaviorKind::Observe);
  repeated.task_value = 0.70F;
  BehaviorCandidate alternate = candidate(21, BehaviorKind::LookToward);
  alternate.task_value = 0.55F;
  BehaviorCandidate repeat_pair[] = {repeated, alternate};
  context = {};
  repetition.select(context, needs, repeat_pair, 2, decision);
  expect(decision.selected_candidate_id == 20,
         "initial strongest idle candidate wins");
  repeat_pair[0].candidate_id = 22;
  context.monotonic_time_ns = UINT64_C(1000000000);
  repetition.select(context, needs, repeat_pair, 2, decision);
  expect(decision.selected_candidate_id == 21,
         "recent kind repetition makes a close alternative win");
  const auto state = repetition.snapshot();
  BehaviorPolicy restored;
  expect(restored.restore(state), "policy repetition state restores");
  expect(restored.snapshot().seen_kind_mask == state.seen_kind_mask,
         "policy history survives restart");
  auto corrupt = state;
  corrupt.seconds_since_kind_selected[0] =
      std::numeric_limits<float>::infinity();
  expect(!restored.restore(corrupt), "corrupt policy state is rejected");
}

void test_policy_rejects_untrusted_or_unbounded_inputs() {
  BehaviorPolicy policy;
  Needs needs;
  BehaviorPolicyContext context;
  BehaviorDecision decision;
  BehaviorCandidate invalid = candidate(1, BehaviorKind::Observe);
  invalid.task_value = std::numeric_limits<float>::quiet_NaN();
  expect(policy.select(context, needs, &invalid, 1, decision) ==
             BehaviorPolicyResult::InvalidInput,
         "non-finite candidate is rejected");
  expect(policy.select(context, needs, nullptr,
                       kMaximumBehaviorCandidates + 1, decision) ==
             BehaviorPolicyResult::TooManyCandidates,
         "candidate count is bounded");
  context.flags = UINT32_C(0x80000000);
  expect(policy.select(context, needs, nullptr, 0, decision) ==
             BehaviorPolicyResult::InvalidInput,
         "unknown context flags are rejected");
  context = {};
  expect(policy.select(context, needs, nullptr, 0, decision) ==
             BehaviorPolicyResult::Ok &&
             (decision.reason_flags & kBehaviorFallbackWait) != 0U,
         "empty candidate set yields explicit safe wait");

  BehaviorCandidate duplicates[2] = {
      candidate(7, BehaviorKind::Wait), candidate(7, BehaviorKind::Rest)};
  expect(policy.select(context, needs, duplicates, 2, decision) ==
             BehaviorPolicyResult::InvalidInput,
         "duplicate candidate IDs are rejected as ambiguous");

  BehaviorCandidate expiring = candidate(8, BehaviorKind::Observe);
  context.monotonic_time_ns = UINT64_C(5000000000);
  expiring.deadline_monotonic_time_ns = context.monotonic_time_ns;
  expect(policy.select(context, needs, &expiring, 1, decision) ==
             BehaviorPolicyResult::Ok && decision.eligible_count == 0 &&
             (decision.reason_flags & kBehaviorRejectedExpired) != 0U,
         "deadline equality is expired and explained");
}

RoutineDefinition morning_routine(std::uint64_t id = 100) {
  RoutineDefinition routine;
  routine.routine_id = id;
  routine.local_start_second = 8U * 3600U;
  routine.window_duration_s = 3600U;
  routine.checkpoint_count = 2U;
  routine.checkpoint_kinds[0] = BehaviorKind::Observe;
  routine.checkpoint_kinds[1] = BehaviorKind::Report;
  routine.base_priority = 0.8F;
  routine.task_value = 0.5F;
  routine.information_value = 0.6F;
  return routine;
}

RoutineClock routine_clock(std::uint64_t monotonic_ns, std::int64_t day,
                           std::uint32_t second) {
  RoutineClock clock;
  clock.monotonic_time_ns = monotonic_ns;
  clock.civil_day_id = day;
  clock.local_second_of_day = second;
  clock.flags = kRoutineClockCivilValid;
  return clock;
}

void test_routines_checkpoints_midnight_and_clock_discontinuities() {
  RoutineScheduler scheduler;
  RoutineDefinition routine = morning_routine();
  expect(scheduler.configure(&routine, 1) == RoutineResult::Ok,
         "data-driven routine config succeeds");

  RoutineCandidate due[kMaximumRoutines];
  std::size_t count = 0;
  RoutineClock clock =
      routine_clock(0, 100, 8U * 3600U + 15U * 60U);
  expect(scheduler.collect(clock, due, kMaximumRoutines, count) ==
             RoutineResult::Ok &&
             count == 1,
         "routine is due inside its local window");
  const std::uint64_t first_id = due[0].behavior.candidate_id;
  expect(due[0].occurrence_day_id == 100 &&
             due[0].checkpoint_index == 0 &&
             due[0].behavior.kind == BehaviorKind::Observe &&
             (due[0].behavior.origin_flags & kOriginRoutine) != 0U &&
             due[0].behavior.routine_pressure > 0.0F,
         "routine candidate carries occurrence, checkpoint and pressure");

  clock.monotonic_time_ns = UINT64_C(1000000000);
  clock.local_second_of_day = 8U * 3600U + 20U * 60U;
  scheduler.collect(clock, due, kMaximumRoutines, count);
  expect(count == 1 && due[0].behavior.candidate_id == first_id,
         "polling the same occurrence preserves candidate identity");
  expect(scheduler.mark_result(100, 100, 0, true) == RoutineResult::Ok,
         "first checkpoint succeeds");
  expect(scheduler.mark_result(100, 100, 0, true) ==
             RoutineResult::StaleOccurrence,
         "duplicate checkpoint result cannot skip the next checkpoint");
  scheduler.collect(clock, due, kMaximumRoutines, count);
  expect(count == 1 && due[0].checkpoint_index == 1 &&
             due[0].behavior.kind == BehaviorKind::Report &&
             due[0].behavior.candidate_id != first_id,
         "success advances to the next semantic checkpoint");
  expect(scheduler.mark_result(100, 100, 1, true) == RoutineResult::Ok,
         "final checkpoint succeeds");

  // A repeated civil hour and a backward correction must not replay a
  // completed occurrence as monotonic time continues forward.
  clock.monotonic_time_ns = UINT64_C(2000000000);
  clock.local_second_of_day = 8U * 3600U + 10U * 60U;
  scheduler.collect(clock, due, kMaximumRoutines, count);
  expect(count == 0, "repeated civil time does not duplicate completion");
  clock.monotonic_time_ns = UINT64_C(3000000000);
  clock.local_second_of_day = 7U * 3600U + 50U * 60U;
  scheduler.collect(clock, due, kMaximumRoutines, count);
  expect(count == 0, "backward civil correction is safely inactive");

  clock.monotonic_time_ns = UINT64_C(4000000000);
  clock.civil_day_id = 101;
  clock.local_second_of_day = 8U * 3600U + 5U * 60U;
  scheduler.collect(clock, due, kMaximumRoutines, count);
  expect(count == 1 && due[0].occurrence_day_id == 101 &&
             due[0].behavior.candidate_id != first_id,
         "next civil day creates a distinct occurrence");

  RoutineDefinition midnight = morning_routine(200);
  midnight.local_start_second = 23U * 3600U + 30U * 60U;
  midnight.window_duration_s = 2U * 3600U;
  midnight.checkpoint_count = 1U;
  expect(scheduler.configure(&midnight, 1) == RoutineResult::Ok,
         "wrap-midnight routine config succeeds");
  clock.monotonic_time_ns = UINT64_C(5000000000);
  clock.civil_day_id = 201;
  clock.local_second_of_day = 30U * 60U;
  scheduler.collect(clock, due, kMaximumRoutines, count);
  expect(count == 1 && due[0].occurrence_day_id == 200,
         "window spanning midnight retains its start-day occurrence");
}

void test_routine_pause_quiet_catchup_retry_and_persistence() {
  RoutineDefinition routine = morning_routine(300);
  routine.checkpoint_count = 1U;
  routine.missed_policy = MissedRoutinePolicy::CatchUp;
  routine.catch_up_duration_s = 2U * 3600U;
  RoutineScheduler scheduler;
  expect(scheduler.configure(&routine, 1) == RoutineResult::Ok,
         "catch-up routine config succeeds");
  RoutineCandidate due[kMaximumRoutines];
  std::size_t count = 0;
  RoutineClock clock =
      routine_clock(0, 300, 8U * 3600U + 10U * 60U);
  clock.flags |= kRoutineClockPaused;
  scheduler.collect(clock, due, kMaximumRoutines, count);
  expect(count == 0, "pause suppresses all routine proposals");
  clock.flags = kRoutineClockCivilValid | kRoutineClockQuiet;
  clock.monotonic_time_ns = UINT64_C(1000000000);
  scheduler.collect(clock, due, kMaximumRoutines, count);
  expect(count == 0, "quiet suppresses incompatible routine proposals");

  clock.flags = kRoutineClockCivilValid;
  clock.monotonic_time_ns = UINT64_C(2000000000);
  clock.local_second_of_day = 10U * 3600U;
  scheduler.collect(clock, due, kMaximumRoutines, count);
  expect(count == 1 && due[0].catch_up &&
             due[0].behavior.routine_pressure >= 0.90F,
         "forward civil jump within catch-up yields urgent due work");
  expect(scheduler.mark_result(300, 300, 0, false) == RoutineResult::Ok,
         "failed routine checkpoint enters retry cooldown");
  expect(scheduler.mark_result(300, 300, 0, false) ==
             RoutineResult::StaleOccurrence,
         "duplicate failure cannot extend retry cooldown");
  clock.monotonic_time_ns = UINT64_C(3000000000);
  scheduler.collect(clock, due, kMaximumRoutines, count);
  expect(count == 0, "failure cooldown prevents a retry loop");
  clock.monotonic_time_ns = UINT64_C(33000000000);
  scheduler.collect(clock, due, kMaximumRoutines, count);
  expect(count == 1, "routine returns after bounded failure cooldown");

  const auto state = scheduler.snapshot();
  RoutineScheduler restored;
  restored.configure(&routine, 1);
  expect(restored.restore(state), "routine progress snapshot restores");
  expect(restored.snapshot().entries[0].cooldown_remaining_s ==
             state.entries[0].cooldown_remaining_s,
         "routine retry state survives restart");
  auto corrupt = state;
  corrupt.entries[0].next_checkpoint_index = 99;
  expect(!restored.restore(corrupt), "corrupt routine state is rejected");

  RoutineDefinition pair_defs[2] = {morning_routine(300),
                                    morning_routine(303)};
  RoutineScheduler duplicate_restore;
  duplicate_restore.configure(pair_defs, 2);
  auto duplicate_state = duplicate_restore.snapshot();
  duplicate_state.entries[1].routine_id = duplicate_state.entries[0].routine_id;
  expect(!duplicate_restore.restore(duplicate_state),
         "duplicate persisted routine identities are rejected");

  RoutineDefinition skip = morning_routine(301);
  skip.checkpoint_count = 1U;
  RoutineScheduler skipping;
  skipping.configure(&skip, 1);
  clock = routine_clock(0, 300, 10U * 3600U);
  skipping.collect(clock, due, kMaximumRoutines, count);
  expect(count == 0, "skip policy does not invent missed routine work");

  RoutineDefinition quiet_ok = morning_routine(302);
  quiet_ok.checkpoint_count = 1U;
  quiet_ok.flags = kRoutineQuietCompatible;
  RoutineScheduler quiet_scheduler;
  quiet_scheduler.configure(&quiet_ok, 1);
  clock = routine_clock(0, 300, 8U * 3600U + 1U);
  clock.flags |= kRoutineClockQuiet;
  quiet_scheduler.collect(clock, due, kMaximumRoutines, count);
  expect(count == 1 &&
             (due[0].behavior.flags & kCandidateQuietAllowed) != 0U,
         "explicitly quiet-compatible routine remains eligible");
}

void test_routine_validation_and_monotonic_time() {
  RoutineScheduler scheduler;
  RoutineDefinition definitions[2] = {morning_routine(1),
                                      morning_routine(1)};
  expect(scheduler.configure(definitions, 2) == RoutineResult::InvalidInput,
         "duplicate routine IDs are rejected");
  definitions[1].routine_id = 2;
  definitions[1].base_priority =
      std::numeric_limits<float>::quiet_NaN();
  expect(scheduler.configure(definitions, 2) == RoutineResult::InvalidInput,
         "non-finite routine values are rejected");
  RoutineDefinition valid = morning_routine(1);
  scheduler.configure(&valid, 1);
  RoutineCandidate due[kMaximumRoutines];
  std::size_t count = 0;
  RoutineClock clock = routine_clock(UINT64_C(1000000000), 1, 8U * 3600U);
  scheduler.collect(clock, due, kMaximumRoutines, count);
  const auto before = scheduler.snapshot();
  clock.monotonic_time_ns = 0;
  expect(scheduler.collect(clock, due, kMaximumRoutines, count) ==
             RoutineResult::TimeRegression,
         "routine monotonic regression is rejected");
  expect(scheduler.snapshot().entries[0].cooldown_remaining_s ==
             before.entries[0].cooldown_remaining_s,
         "rejected routine clock leaves progress unchanged");
  expect(scheduler.mark_result(999, 1, 0, true) == RoutineResult::UnknownRoutine,
         "unknown routine result is rejected");
  expect(scheduler.mark_result(1, 2, 0, true) == RoutineResult::StaleOccurrence,
         "stale occurrence result is rejected");
}

}  // namespace

int main() {
  test_sleep_boundaries_attention_restart_and_policy();
  test_idle_is_deterministic_bounded_and_varied();
  test_attention_task_interaction_and_outcomes();
  test_quiet_pause_circadian_and_invalid_input();
  test_restart_policy_and_accelerated_week();
  test_policy_sources_costs_and_explanations();
  test_policy_admission_commitment_repetition_and_persistence();
  test_policy_rejects_untrusted_or_unbounded_inputs();
  test_routines_checkpoints_midnight_and_clock_discontinuities();
  test_routine_pause_quiet_catchup_retry_and_persistence();
  test_routine_validation_and_monotonic_time();
  expect(std::string_view(to_string(MicroBehavior::Observing)) == "observing",
         "micro behavior names are stable");
  expect(std::string_view(to_string(static_cast<MicroBehavior>(255))) ==
             "unknown",
         "invalid micro behavior name is safe");

  if (failures != 0) {
    std::cerr << failures << " personality runtime test(s) failed\n";
    return EXIT_FAILURE;
  }
  std::cout << "All personality runtime tests passed\n";
  return EXIT_SUCCESS;
}
