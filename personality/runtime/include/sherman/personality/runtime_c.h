#ifndef SHERMAN_PERSONALITY_RUNTIME_C_H
#define SHERMAN_PERSONALITY_RUNTIME_C_H

#include <stdint.h>

#ifdef __cplusplus
extern "C" {
#endif

#define SHERMAN_PERSONALITY_API_VERSION UINT32_C(0x00010000)
#define SHERMAN_PERSONALITY_SNAPSHOT_VERSION UINT32_C(1)
#define SHERMAN_PERSONALITY_POLICY_SNAPSHOT_VERSION UINT32_C(1)
#define SHERMAN_PERSONALITY_ROUTINE_SNAPSHOT_VERSION UINT32_C(1)
#define SHERMAN_PERSONALITY_MAX_CANDIDATES UINT32_C(16)
#define SHERMAN_PERSONALITY_BEHAVIOR_KIND_COUNT UINT32_C(10)
#define SHERMAN_PERSONALITY_MAX_ROUTINES UINT32_C(8)
#define SHERMAN_PERSONALITY_MAX_ROUTINE_CHECKPOINTS UINT32_C(8)

typedef void* sherman_personality_handle;

enum sherman_personality_status {
  SHERMAN_PERSONALITY_OK = 0,
  SHERMAN_PERSONALITY_COOLDOWN = 1,
  SHERMAN_PERSONALITY_INVALID_ARGUMENT = -1,
  SHERMAN_PERSONALITY_TIME_REGRESSION = -2,
  SHERMAN_PERSONALITY_INCOMPATIBLE = -3,
  SHERMAN_PERSONALITY_ALLOCATION_FAILED = -4,
  SHERMAN_PERSONALITY_NOT_FOUND = -5,
  SHERMAN_PERSONALITY_STALE = -6
};

enum sherman_personality_event {
  SHERMAN_PERSONALITY_EVENT_DISCOVERY = 0,
  SHERMAN_PERSONALITY_EVENT_TASK_STARTED = 1,
  SHERMAN_PERSONALITY_EVENT_TASK_SUCCEEDED = 2,
  SHERMAN_PERSONALITY_EVENT_TASK_FAILED = 3,
  SHERMAN_PERSONALITY_EVENT_BLOCKED = 4,
  SHERMAN_PERSONALITY_EVENT_SOCIAL_CONTACT = 5,
  SHERMAN_PERSONALITY_EVENT_SOCIAL_MISSED = 6,
  SHERMAN_PERSONALITY_EVENT_PICKED_UP = 7,
  SHERMAN_PERSONALITY_EVENT_RESTED = 8,
  SHERMAN_PERSONALITY_EVENT_ENERGY_DEPLETED = 9,
  SHERMAN_PERSONALITY_EVENT_URGENT_REQUEST = 10,
  SHERMAN_PERSONALITY_EVENT_CALMED = 11,
  SHERMAN_PERSONALITY_EVENT_INTERACTION_STARTED = 12,
  SHERMAN_PERSONALITY_EVENT_INTERACTION_ENDED = 13
};

enum sherman_personality_expression {
  SHERMAN_PERSONALITY_EXPRESSION_CALM = 0,
  SHERMAN_PERSONALITY_EXPRESSION_CURIOUS = 1,
  SHERMAN_PERSONALITY_EXPRESSION_FOCUSED = 2,
  SHERMAN_PERSONALITY_EXPRESSION_PLEASED = 3,
  SHERMAN_PERSONALITY_EXPRESSION_UNCERTAIN = 4,
  SHERMAN_PERSONALITY_EXPRESSION_FRUSTRATED = 5,
  SHERMAN_PERSONALITY_EXPRESSION_TIRED = 6
};

enum sherman_personality_micro_behavior {
  SHERMAN_PERSONALITY_MICRO_SETTLED = 0,
  SHERMAN_PERSONALITY_MICRO_ORIENTING = 1,
  SHERMAN_PERSONALITY_MICRO_OBSERVING = 2,
  SHERMAN_PERSONALITY_MICRO_ENGAGED = 3,
  SHERMAN_PERSONALITY_MICRO_REFLECTING = 4,
  SHERMAN_PERSONALITY_MICRO_DROWSY = 5
};

enum sherman_personality_input_flag {
  SHERMAN_PERSONALITY_INPUT_RESTING = UINT32_C(1) << 0,
  SHERMAN_PERSONALITY_INPUT_QUIET = UINT32_C(1) << 1,
  SHERMAN_PERSONALITY_INPUT_USER_PRESENT = UINT32_C(1) << 2,
  SHERMAN_PERSONALITY_INPUT_TASK_ACTIVE = UINT32_C(1) << 3,
  SHERMAN_PERSONALITY_INPUT_PAUSED = UINT32_C(1) << 4,
  SHERMAN_PERSONALITY_INPUT_ATTENTION_VALID = UINT32_C(1) << 5,
  SHERMAN_PERSONALITY_INPUT_CIRCADIAN_VALID = UINT32_C(1) << 6
};

enum sherman_personality_reason {
  SHERMAN_PERSONALITY_REASON_STARTUP = UINT32_C(1) << 0,
  SHERMAN_PERSONALITY_REASON_CIRCADIAN_QUIET = UINT32_C(1) << 1,
  SHERMAN_PERSONALITY_REASON_EXPLICIT_QUIET = UINT32_C(1) << 2,
  SHERMAN_PERSONALITY_REASON_PAUSED = UINT32_C(1) << 3,
  SHERMAN_PERSONALITY_REASON_EXTERNAL_ATTENTION = UINT32_C(1) << 4,
  SHERMAN_PERSONALITY_REASON_RECENT_INTERACTION = UINT32_C(1) << 5,
  SHERMAN_PERSONALITY_REASON_TASK_ENGAGED = UINT32_C(1) << 6,
  SHERMAN_PERSONALITY_REASON_SPONTANEOUS_IDLE = UINT32_C(1) << 7,
  SHERMAN_PERSONALITY_REASON_LOW_ENERGY = UINT32_C(1) << 8,
  SHERMAN_PERSONALITY_REASON_RECENT_OUTCOME = UINT32_C(1) << 9,
  SHERMAN_PERSONALITY_REASON_FALLBACK = UINT32_C(1) << 10
};

typedef struct sherman_personality_config {
  uint32_t struct_size;
  uint32_t api_version;
  uint64_t seed;
  float curiosity;
  float sociability;
  float calmness;
  float expressiveness;
  float day_activity;
} sherman_personality_config;

typedef struct sherman_personality_input {
  uint32_t struct_size;
  uint32_t flags;
  uint64_t monotonic_time_ns;
  uint32_t local_second_of_day;
  uint32_t reserved;
  float activity_load;
  float task_engagement;
  float social_engagement;
  float novelty;
  float external_urgency;
  float attention_target_x;
  float attention_target_y;
  float attention_salience;
} sherman_personality_input;

typedef struct sherman_personality_output {
  uint32_t struct_size;
  uint32_t api_version;
  uint64_t monotonic_time_ns;
  uint64_t sequence;
  int32_t expression;
  int32_t micro_behavior;
  uint32_t reason_flags;
  uint32_t reserved;
  float valence;
  float arousal;
  float confidence;
  float attention;
  float gaze_x;
  float gaze_y;
  float eyelid_open;
  float blink_rate_hz;
} sherman_personality_output;

typedef struct sherman_personality_snapshot {
  uint32_t struct_size;
  uint32_t snapshot_version;
  uint64_t rng_state;
  uint64_t sequence;
  float total_awake_s;
  float since_interaction_s;
  float since_engagement_s;
  float idle_delay_remaining_s;
  float energy;
  float curiosity;
  float social_engagement;
  float confidence;
  float frustration;
  float urgency;
  float valence;
  float arousal;
  int32_t mood;
  uint32_t reserved;
} sherman_personality_snapshot;

enum sherman_personality_behavior_kind {
  SHERMAN_PERSONALITY_BEHAVIOR_WAIT = 0,
  SHERMAN_PERSONALITY_BEHAVIOR_OBSERVE = 1,
  SHERMAN_PERSONALITY_BEHAVIOR_LOOK_TOWARD = 2,
  SHERMAN_PERSONALITY_BEHAVIOR_INSPECT_CHANGE = 3,
  SHERMAN_PERSONALITY_BEHAVIOR_PATROL = 4,
  SHERMAN_PERSONALITY_BEHAVIOR_REVISIT = 5,
  SHERMAN_PERSONALITY_BEHAVIOR_REPORT = 6,
  SHERMAN_PERSONALITY_BEHAVIOR_REST = 7,
  SHERMAN_PERSONALITY_BEHAVIOR_ASK_FOR_HELP = 8,
  SHERMAN_PERSONALITY_BEHAVIOR_ACKNOWLEDGE = 9
};

enum sherman_personality_candidate_flag {
  SHERMAN_PERSONALITY_CANDIDATE_AVAILABLE = UINT32_C(1) << 0,
  SHERMAN_PERSONALITY_CANDIDATE_QUIET_ALLOWED = UINT32_C(1) << 1,
  SHERMAN_PERSONALITY_CANDIDATE_PAUSED_ALLOWED = UINT32_C(1) << 2,
  SHERMAN_PERSONALITY_CANDIDATE_LOW_ENERGY_ALLOWED = UINT32_C(1) << 3,
  SHERMAN_PERSONALITY_CANDIDATE_INTERRUPTIBLE = UINT32_C(1) << 4
};

enum sherman_personality_behavior_origin {
  SHERMAN_PERSONALITY_ORIGIN_LOCAL_IDLE = UINT32_C(1) << 0,
  SHERMAN_PERSONALITY_ORIGIN_ROUTINE = UINT32_C(1) << 1,
  SHERMAN_PERSONALITY_ORIGIN_JARVIS = UINT32_C(1) << 2,
  SHERMAN_PERSONALITY_ORIGIN_WORLD_CHANGE = UINT32_C(1) << 3,
  SHERMAN_PERSONALITY_ORIGIN_RECOVERY = UINT32_C(1) << 4
};

enum sherman_personality_policy_flag {
  SHERMAN_PERSONALITY_POLICY_QUIET = UINT32_C(1) << 0,
  SHERMAN_PERSONALITY_POLICY_PAUSED = UINT32_C(1) << 1,
  SHERMAN_PERSONALITY_POLICY_CURRENT_ACTION_ACTIVE = UINT32_C(1) << 2,
  SHERMAN_PERSONALITY_POLICY_CURRENT_ACTION_INTERRUPTIBLE = UINT32_C(1) << 3
};

enum sherman_personality_behavior_reason {
  SHERMAN_PERSONALITY_BEHAVIOR_ELIGIBLE = UINT32_C(1) << 0,
  SHERMAN_PERSONALITY_BEHAVIOR_ROUTINE_DUE = UINT32_C(1) << 1,
  SHERMAN_PERSONALITY_BEHAVIOR_JARVIS_REQUEST = UINT32_C(1) << 2,
  SHERMAN_PERSONALITY_BEHAVIOR_WORLD_CHANGE = UINT32_C(1) << 3,
  SHERMAN_PERSONALITY_BEHAVIOR_RECOVERY = UINT32_C(1) << 4,
  SHERMAN_PERSONALITY_BEHAVIOR_NOVELTY_VALUE = UINT32_C(1) << 5,
  SHERMAN_PERSONALITY_BEHAVIOR_REPETITION_PENALTY = UINT32_C(1) << 6,
  SHERMAN_PERSONALITY_BEHAVIOR_RECENT_FAILURE = UINT32_C(1) << 7,
  SHERMAN_PERSONALITY_BEHAVIOR_RISK_PENALTY = UINT32_C(1) << 8,
  SHERMAN_PERSONALITY_BEHAVIOR_RETAINED_COMMITMENT = UINT32_C(1) << 9,
  SHERMAN_PERSONALITY_BEHAVIOR_RETAINED_HYSTERESIS = UINT32_C(1) << 10,
  SHERMAN_PERSONALITY_BEHAVIOR_FALLBACK_WAIT = UINT32_C(1) << 11,
  SHERMAN_PERSONALITY_BEHAVIOR_REJECTED_UNAVAILABLE = UINT32_C(1) << 12,
  SHERMAN_PERSONALITY_BEHAVIOR_REJECTED_EXPIRED = UINT32_C(1) << 13,
  SHERMAN_PERSONALITY_BEHAVIOR_REJECTED_QUIET = UINT32_C(1) << 14,
  SHERMAN_PERSONALITY_BEHAVIOR_REJECTED_PAUSED = UINT32_C(1) << 15,
  SHERMAN_PERSONALITY_BEHAVIOR_REJECTED_LOW_ENERGY = UINT32_C(1) << 16
};

typedef struct sherman_personality_behavior_context {
  uint32_t struct_size;
  uint32_t flags;
  uint64_t monotonic_time_ns;
  uint64_t current_candidate_id;
  float current_action_age_s;
  uint32_t reserved;
} sherman_personality_behavior_context;

typedef struct sherman_personality_behavior_candidate {
  uint32_t struct_size;
  uint32_t flags;
  uint64_t candidate_id;
  uint64_t deadline_monotonic_time_ns;
  int32_t kind;
  uint32_t origin_flags;
  float task_value;
  float information_value;
  float social_value;
  float routine_pressure;
  float urgency;
  float time_cost;
  float energy_cost;
  float motion_cost;
  float risk_cost;
  float repetition_cost;
  float recent_failure_cost;
} sherman_personality_behavior_candidate;

typedef struct sherman_personality_behavior_score {
  float task_value;
  float curiosity_value;
  float social_value;
  float routine_value;
  float urgency_value;
  float time_cost;
  float energy_cost;
  float motion_cost;
  float risk_cost;
  float repetition_cost;
  float failure_cost;
  float deterministic_variation;
  float total;
} sherman_personality_behavior_score;

typedef struct sherman_personality_behavior_decision {
  uint32_t struct_size;
  uint32_t api_version;
  uint64_t selected_candidate_id;
  uint64_t runner_up_candidate_id;
  int32_t selected_kind;
  uint32_t reason_flags;
  uint32_t candidate_count;
  uint32_t eligible_count;
  sherman_personality_behavior_score selected_score;
  float runner_up_score;
  uint32_t reserved;
} sherman_personality_behavior_decision;

typedef struct sherman_personality_policy_snapshot {
  uint32_t struct_size;
  uint32_t snapshot_version;
  uint64_t last_selected_candidate_id;
  int32_t last_selected_kind;
  uint32_t seen_kind_mask;
  float seconds_since_kind_selected[SHERMAN_PERSONALITY_BEHAVIOR_KIND_COUNT];
} sherman_personality_policy_snapshot;

enum sherman_personality_missed_routine_policy {
  SHERMAN_PERSONALITY_ROUTINE_SKIP = 0,
  SHERMAN_PERSONALITY_ROUTINE_CATCH_UP = 1
};

enum sherman_personality_routine_flag {
  SHERMAN_PERSONALITY_ROUTINE_QUIET_COMPATIBLE = UINT32_C(1) << 0,
  SHERMAN_PERSONALITY_ROUTINE_LOW_ENERGY_COMPATIBLE = UINT32_C(1) << 1
};

enum sherman_personality_routine_clock_flag {
  SHERMAN_PERSONALITY_ROUTINE_CIVIL_VALID = UINT32_C(1) << 0,
  SHERMAN_PERSONALITY_ROUTINE_QUIET = UINT32_C(1) << 1,
  SHERMAN_PERSONALITY_ROUTINE_PAUSED = UINT32_C(1) << 2
};

typedef struct sherman_personality_routine_definition {
  uint32_t struct_size;
  uint32_t flags;
  uint64_t routine_id;
  uint32_t local_start_second;
  uint32_t window_duration_s;
  uint32_t catch_up_duration_s;
  uint32_t completion_cooldown_s;
  int32_t missed_policy;
  uint32_t checkpoint_count;
  int32_t checkpoint_kinds[SHERMAN_PERSONALITY_MAX_ROUTINE_CHECKPOINTS];
  float base_priority;
  float task_value;
  float information_value;
  float social_value;
  float urgency;
} sherman_personality_routine_definition;

typedef struct sherman_personality_routine_clock {
  uint32_t struct_size;
  uint32_t flags;
  uint64_t monotonic_time_ns;
  int64_t civil_day_id;
  uint32_t local_second_of_day;
  uint32_t reserved;
} sherman_personality_routine_clock;

typedef struct sherman_personality_routine_candidate {
  uint32_t struct_size;
  uint32_t checkpoint_index;
  uint64_t routine_id;
  int64_t occurrence_day_id;
  uint32_t catch_up;
  uint32_t reserved;
  sherman_personality_behavior_candidate behavior;
} sherman_personality_routine_candidate;

typedef struct sherman_personality_routine_progress {
  uint64_t routine_id;
  int64_t last_completed_day_id;
  int64_t active_occurrence_day_id;
  float cooldown_remaining_s;
  uint32_t next_checkpoint_index;
  uint32_t has_completed;
  uint32_t has_active_occurrence;
} sherman_personality_routine_progress;

typedef struct sherman_personality_routine_snapshot {
  uint32_t struct_size;
  uint32_t snapshot_version;
  uint32_t routine_count;
  uint32_t reserved;
  sherman_personality_routine_progress
      entries[SHERMAN_PERSONALITY_MAX_ROUTINES];
} sherman_personality_routine_snapshot;

uint32_t sherman_personality_api_version(void);
uint32_t sherman_personality_config_size(void);
uint32_t sherman_personality_input_size(void);
uint32_t sherman_personality_output_size(void);
uint32_t sherman_personality_snapshot_size(void);
uint32_t sherman_personality_behavior_context_size(void);
uint32_t sherman_personality_behavior_candidate_size(void);
uint32_t sherman_personality_behavior_decision_size(void);
uint32_t sherman_personality_policy_snapshot_size(void);
uint32_t sherman_personality_routine_definition_size(void);
uint32_t sherman_personality_routine_clock_size(void);
uint32_t sherman_personality_routine_candidate_size(void);
uint32_t sherman_personality_routine_snapshot_size(void);

int32_t sherman_personality_default_config(
    sherman_personality_config* output);
sherman_personality_handle sherman_personality_create(
    const sherman_personality_config* config);
void sherman_personality_destroy(sherman_personality_handle handle);
int32_t sherman_personality_reset(sherman_personality_handle handle,
                                  uint64_t seed);
int32_t sherman_personality_apply_event(sherman_personality_handle handle,
                                        int32_t event, float strength);
int32_t sherman_personality_step(sherman_personality_handle handle,
                                 const sherman_personality_input* input,
                                 sherman_personality_output* output);
int32_t sherman_personality_get_output(sherman_personality_handle handle,
                                       sherman_personality_output* output);
int32_t sherman_personality_snapshot_state(
    sherman_personality_handle handle,
    sherman_personality_snapshot* output);
int32_t sherman_personality_restore(
    sherman_personality_handle handle,
    const sherman_personality_snapshot* snapshot);
int32_t sherman_personality_safe_output(uint64_t monotonic_time_ns,
                                        sherman_personality_output* output);
int32_t sherman_personality_select_behavior(
    sherman_personality_handle handle,
    const sherman_personality_behavior_context* context,
    const sherman_personality_behavior_candidate* candidates,
    uint32_t candidate_count,
    sherman_personality_behavior_decision* decision);
int32_t sherman_personality_snapshot_policy(
    sherman_personality_handle handle,
    sherman_personality_policy_snapshot* output);
int32_t sherman_personality_restore_policy(
    sherman_personality_handle handle,
    const sherman_personality_policy_snapshot* snapshot);
int32_t sherman_personality_set_routines(
    sherman_personality_handle handle,
    const sherman_personality_routine_definition* definitions,
    uint32_t routine_count);
int32_t sherman_personality_collect_routine_candidates(
    sherman_personality_handle handle,
    const sherman_personality_routine_clock* clock,
    sherman_personality_routine_candidate* output,
    uint32_t output_capacity,
    uint32_t* output_count);
int32_t sherman_personality_mark_routine_result(
    sherman_personality_handle handle,
    uint64_t routine_id,
    int64_t occurrence_day_id,
    uint32_t checkpoint_index,
    uint32_t success);
int32_t sherman_personality_snapshot_routines(
    sherman_personality_handle handle,
    sherman_personality_routine_snapshot* output);
int32_t sherman_personality_restore_routines(
    sherman_personality_handle handle,
    const sherman_personality_routine_snapshot* snapshot);

#ifdef __cplusplus
}
#endif

#endif
