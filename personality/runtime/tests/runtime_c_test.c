#include "sherman/personality/runtime_c.h"

#include <math.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

static int failures = 0;

static void expect(int condition, const char* message) {
  if (!condition) {
    fprintf(stderr, "FAIL: %s\n", message);
    ++failures;
  }
}

int main(void) {
  expect(sherman_personality_api_version() == SHERMAN_PERSONALITY_API_VERSION,
         "C ABI version matches header");
  expect(sherman_personality_config_size() ==
             sizeof(sherman_personality_config),
         "config size matches");
  expect(sherman_personality_input_size() ==
             sizeof(sherman_personality_input),
         "input size matches");
  expect(sherman_personality_output_size() ==
             sizeof(sherman_personality_output),
         "output size matches");
  expect(sherman_personality_routine_snapshot_size() ==
             sizeof(sherman_personality_routine_snapshot),
         "routine snapshot size matches");

  sherman_personality_config config;
  memset(&config, 0, sizeof(config));
  config.struct_size = sizeof(config);
  expect(sherman_personality_default_config(&config) ==
             SHERMAN_PERSONALITY_OK,
         "default config is available");
  config.seed = UINT64_C(123);
  sherman_personality_handle handle = sherman_personality_create(&config);
  expect(handle != NULL, "C ABI creates a controller");

  sherman_personality_input input;
  memset(&input, 0, sizeof(input));
  input.struct_size = sizeof(input);
  input.flags = SHERMAN_PERSONALITY_INPUT_CIRCADIAN_VALID |
                SHERMAN_PERSONALITY_INPUT_ATTENTION_VALID;
  input.local_second_of_day = 12U * 3600U;
  input.attention_target_x = 0.7F;
  input.attention_target_y = -0.2F;
  input.attention_salience = 1.0F;
  sherman_personality_output output;
  memset(&output, 0, sizeof(output));
  output.struct_size = sizeof(output);
  expect(sherman_personality_step(handle, &input, &output) ==
             SHERMAN_PERSONALITY_OK,
         "C ABI step succeeds");
  input.monotonic_time_ns = UINT64_C(500000000);
  expect(sherman_personality_step(handle, &input, &output) ==
             SHERMAN_PERSONALITY_OK,
         "C ABI attention step succeeds");
  expect(output.api_version == SHERMAN_PERSONALITY_API_VERSION &&
             output.micro_behavior == SHERMAN_PERSONALITY_MICRO_ENGAGED &&
             output.gaze_x > 0.5F,
         "C ABI exposes semantic attention output");

  input.monotonic_time_ns = UINT64_C(100000000);
  expect(sherman_personality_step(handle, &input, &output) ==
             SHERMAN_PERSONALITY_TIME_REGRESSION,
         "C ABI rejects regressing clock");
  expect((output.reason_flags & SHERMAN_PERSONALITY_REASON_FALLBACK) != 0U,
         "C ABI emits a safe fallback on invalid time");

  sherman_personality_snapshot snapshot;
  memset(&snapshot, 0, sizeof(snapshot));
  snapshot.struct_size = sizeof(snapshot);
  expect(sherman_personality_snapshot_state(handle, &snapshot) ==
             SHERMAN_PERSONALITY_OK,
         "C ABI snapshots runtime state");
  expect(sherman_personality_reset(handle, 456) == SHERMAN_PERSONALITY_OK,
         "C ABI resets runtime and policy");
  expect(sherman_personality_restore(handle, &snapshot) ==
             SHERMAN_PERSONALITY_OK,
         "C ABI restores runtime state");

  sherman_personality_behavior_candidate choices[2];
  memset(choices, 0, sizeof(choices));
  for (size_t index = 0; index < 2; ++index) {
    choices[index].struct_size = sizeof(choices[index]);
    choices[index].candidate_id = (uint64_t)index + UINT64_C(1);
    choices[index].flags = SHERMAN_PERSONALITY_CANDIDATE_AVAILABLE |
                           SHERMAN_PERSONALITY_CANDIDATE_QUIET_ALLOWED |
                           SHERMAN_PERSONALITY_CANDIDATE_PAUSED_ALLOWED |
                           SHERMAN_PERSONALITY_CANDIDATE_LOW_ENERGY_ALLOWED |
                           SHERMAN_PERSONALITY_CANDIDATE_INTERRUPTIBLE;
    choices[index].origin_flags = SHERMAN_PERSONALITY_ORIGIN_LOCAL_IDLE;
  }
  choices[0].kind = SHERMAN_PERSONALITY_BEHAVIOR_WAIT;
  choices[0].task_value = 0.1F;
  choices[1].kind = SHERMAN_PERSONALITY_BEHAVIOR_ACKNOWLEDGE;
  choices[1].origin_flags = SHERMAN_PERSONALITY_ORIGIN_JARVIS;
  choices[1].task_value = 0.9F;
  choices[1].social_value = 0.5F;

  sherman_personality_behavior_context context;
  memset(&context, 0, sizeof(context));
  context.struct_size = sizeof(context);
  context.monotonic_time_ns = UINT64_C(1000000000);
  sherman_personality_behavior_decision decision;
  memset(&decision, 0, sizeof(decision));
  decision.struct_size = sizeof(decision);
  expect(sherman_personality_select_behavior(handle, &context, choices, 2,
                                             &decision) ==
             SHERMAN_PERSONALITY_OK,
         "C ABI behavior selection succeeds");
  expect(decision.selected_candidate_id == 2 &&
             (decision.reason_flags &
              SHERMAN_PERSONALITY_BEHAVIOR_JARVIS_REQUEST) != 0U,
         "C ABI behavior selection is inspectable");
  expect(isfinite(decision.selected_score.total),
         "C ABI score is finite");

  input.flags = SHERMAN_PERSONALITY_INPUT_CIRCADIAN_VALID;
  input.local_second_of_day = 3U * 3600U;
  input.monotonic_time_ns = context.monotonic_time_ns;
  expect(sherman_personality_step(handle, &input, &output) == SHERMAN_PERSONALITY_OK,
         "C ABI enters quiet hours");
  expect(sherman_personality_select_behavior(handle, &context, choices, 2,
                                             &decision) == SHERMAN_PERSONALITY_OK &&
             decision.selected_candidate_id == 1,
         "controller quiet overrides missing policy quiet flag");
  input.local_second_of_day = 8U * 3600U;
  input.monotonic_time_ns += UINT64_C(1000000000);
  context.monotonic_time_ns = input.monotonic_time_ns;
  sherman_personality_step(handle, &input, &output);
  expect(sherman_personality_select_behavior(handle, &context, choices, 2,
                                             &decision) == SHERMAN_PERSONALITY_OK &&
             decision.selected_candidate_id == 2,
         "fresh morning selection can admit awake work again");

  sherman_personality_policy_snapshot policy_snapshot;
  memset(&policy_snapshot, 0, sizeof(policy_snapshot));
  policy_snapshot.struct_size = sizeof(policy_snapshot);
  expect(sherman_personality_snapshot_policy(handle, &policy_snapshot) ==
             SHERMAN_PERSONALITY_OK,
         "C ABI snapshots policy history");
  expect(sherman_personality_restore_policy(handle, &policy_snapshot) ==
             SHERMAN_PERSONALITY_OK,
         "C ABI restores policy history");

  sherman_personality_routine_definition routine;
  memset(&routine, 0, sizeof(routine));
  routine.struct_size = sizeof(routine);
  routine.routine_id = UINT64_C(77);
  routine.local_start_second = 8U * 3600U;
  routine.window_duration_s = 3600U;
  routine.checkpoint_count = 1U;
  routine.checkpoint_kinds[0] = SHERMAN_PERSONALITY_BEHAVIOR_OBSERVE;
  routine.base_priority = 0.8F;
  routine.task_value = 0.4F;
  routine.information_value = 0.6F;
  routine.urgency = 0.2F;
  expect(sherman_personality_set_routines(handle, &routine, 1) ==
             SHERMAN_PERSONALITY_OK,
         "C ABI configures data-driven routine");
  sherman_personality_routine_clock routine_clock;
  memset(&routine_clock, 0, sizeof(routine_clock));
  routine_clock.struct_size = sizeof(routine_clock);
  routine_clock.flags = SHERMAN_PERSONALITY_ROUTINE_CIVIL_VALID;
  routine_clock.monotonic_time_ns = UINT64_C(2000000000);
  routine_clock.civil_day_id = 42;
  routine_clock.local_second_of_day = 8U * 3600U + 60U;
  sherman_personality_routine_candidate routine_candidates[1];
  memset(routine_candidates, 0, sizeof(routine_candidates));
  routine_candidates[0].struct_size = sizeof(routine_candidates[0]);
  uint32_t routine_candidate_count = 0;
  expect(sherman_personality_collect_routine_candidates(
             handle, &routine_clock, routine_candidates, 1,
             &routine_candidate_count) == SHERMAN_PERSONALITY_OK &&
             routine_candidate_count == 1,
         "C ABI collects routine candidate");
  expect(routine_candidates[0].routine_id == 77 &&
             routine_candidates[0].occurrence_day_id == 42 &&
             routine_candidates[0].behavior.origin_flags ==
                 SHERMAN_PERSONALITY_ORIGIN_ROUTINE,
         "C ABI routine candidate carries semantic metadata");
  expect(sherman_personality_mark_routine_result(handle, 77, 42, 0, 1) ==
             SHERMAN_PERSONALITY_OK,
         "C ABI marks routine checkpoint complete");
  routine_clock.monotonic_time_ns = UINT64_C(3000000000);
  expect(sherman_personality_collect_routine_candidates(
             handle, &routine_clock, routine_candidates, 1,
             &routine_candidate_count) == SHERMAN_PERSONALITY_OK &&
             routine_candidate_count == 0,
         "completed C ABI routine does not replay");

  sherman_personality_routine_snapshot routine_snapshot;
  memset(&routine_snapshot, 0, sizeof(routine_snapshot));
  routine_snapshot.struct_size = sizeof(routine_snapshot);
  expect(sherman_personality_snapshot_routines(handle, &routine_snapshot) ==
             SHERMAN_PERSONALITY_OK,
         "C ABI snapshots routine progress");
  expect(sherman_personality_reset(handle, UINT64_C(456)) ==
             SHERMAN_PERSONALITY_OK,
         "combined reset clears routine progress");
  expect(sherman_personality_restore_routines(handle, &routine_snapshot) ==
             SHERMAN_PERSONALITY_OK,
         "C ABI restores routine progress after definitions exist");

  expect(sherman_personality_apply_event(
             handle, SHERMAN_PERSONALITY_EVENT_TASK_SUCCEEDED, 1.0F) ==
             SHERMAN_PERSONALITY_OK,
         "C ABI applies semantic outcome event");
  expect(sherman_personality_apply_event(handle, INT32_MAX, 1.0F) ==
             SHERMAN_PERSONALITY_INVALID_ARGUMENT,
         "C ABI rejects unknown event");

  sherman_personality_destroy(handle);
  sherman_personality_destroy(NULL);
  if (failures != 0) {
    fprintf(stderr, "%d C ABI test(s) failed\n", failures);
    return EXIT_FAILURE;
  }
  puts("All personality C ABI tests passed");
  return EXIT_SUCCESS;
}
