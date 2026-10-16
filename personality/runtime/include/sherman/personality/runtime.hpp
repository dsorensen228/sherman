#pragma once

#include <cstdint>

#include "sherman/personality/emotion.hpp"

namespace sherman::personality {

inline constexpr std::uint32_t kPersonalityApiVersion = 0x00010000U;

// The small, reviewed personality tuning surface. Values are normalized and
// affect presentation cadence only; none of them grant actuator authority.
struct PersonalityConfig {
  std::uint64_t seed{0x534845524d414eULL};
  float curiosity{0.68F};
  float sociability{0.58F};
  float calmness{0.64F};
  float expressiveness{0.78F};
  float day_activity{0.72F};
};

enum class PersonalityEvent : std::int32_t {
  Discovery = 0,
  TaskStarted,
  TaskSucceeded,
  TaskFailed,
  Blocked,
  SocialContact,
  SocialMissed,
  PickedUp,
  Rested,
  EnergyDepleted,
  UrgentRequest,
  Calmed,
  InteractionStarted,
  InteractionEnded,
  Count,
};

enum class MicroBehavior : std::int32_t {
  Settled = 0,
  Orienting,
  Observing,
  Engaged,
  Reflecting,
  Drowsy,
  Count,
};

const char* to_string(MicroBehavior behavior) noexcept;

enum PersonalityInputFlag : std::uint32_t {
  kInputResting = 1U << 0U,
  kInputQuiet = 1U << 1U,
  kInputUserPresent = 1U << 2U,
  kInputTaskActive = 1U << 3U,
  kInputPaused = 1U << 4U,
  kInputAttentionValid = 1U << 5U,
  kInputCircadianValid = 1U << 6U,
};

inline constexpr std::uint32_t kAllPersonalityInputFlags =
    kInputResting | kInputQuiet | kInputUserPresent | kInputTaskActive |
    kInputPaused | kInputAttentionValid | kInputCircadianValid;

enum PersonalityReason : std::uint32_t {
  kReasonStartup = 1U << 0U,
  kReasonCircadianQuiet = 1U << 1U,
  kReasonExplicitQuiet = 1U << 2U,
  kReasonPaused = 1U << 3U,
  kReasonExternalAttention = 1U << 4U,
  kReasonRecentInteraction = 1U << 5U,
  kReasonTaskEngaged = 1U << 6U,
  kReasonSpontaneousIdle = 1U << 7U,
  kReasonLowEnergy = 1U << 8U,
  kReasonRecentOutcome = 1U << 9U,
  kReasonFallback = 1U << 10U,
};

// Semantic observations supplied by platform/core adapters. A missing sensor
// is represented by clearing its validity flag, never by invented values.
struct PersonalityInput {
  std::uint64_t monotonic_time_ns{0};
  std::uint32_t local_second_of_day{0};
  std::uint32_t flags{0};
  float activity_load{0.0F};
  float task_engagement{0.0F};
  float social_engagement{0.0F};
  float novelty{0.0F};
  float external_urgency{0.0F};
  float attention_target_x{0.0F};
  float attention_target_y{0.0F};
  float attention_salience{0.0F};
};

// Renderer-independent presentation intent. Gaze is normalized to [-1, 1],
// while all other scalar presentation channels are normalized to [0, 1].
struct PersonalityOutput {
  std::uint64_t monotonic_time_ns{0};
  std::uint64_t sequence{0};
  Mood expression{Mood::Calm};
  MicroBehavior micro_behavior{MicroBehavior::Settled};
  std::uint32_t reason_flags{kReasonStartup};
  float valence{0.0F};
  float arousal{0.0F};
  float confidence{0.5F};
  float attention{0.0F};
  float gaze_x{0.0F};
  float gaze_y{0.0F};
  float eyelid_open{1.0F};
  float blink_rate_hz{0.18F};
};

struct PersistedPersonalityState {
  static constexpr std::uint16_t kCurrentVersion = 1;

  std::uint16_t version{kCurrentVersion};
  std::uint64_t rng_state{0};
  std::uint64_t sequence{0};
  float total_awake_s{0.0F};
  float since_interaction_s{86400.0F};
  float since_engagement_s{86400.0F};
  float idle_delay_remaining_s{0.0F};
  PersistedEmotionState emotion{};
};

enum class PersonalityStepResult : std::int32_t {
  Ok = 0,
  InvalidInput = -1,
  TimeRegression = -2,
};

enum class PersonalityEventResult : std::int32_t {
  Accepted = 0,
  CooledDown = 1,
  InvalidInput = -1,
};

class PersonalityController {
 public:
  explicit PersonalityController(PersonalityConfig config = {});

  PersonalityStepResult step(const PersonalityInput& input) noexcept;
  PersonalityEventResult apply(PersonalityEvent event,
                               float strength = 1.0F) noexcept;

  const PersonalityOutput& output() const noexcept { return output_; }
  const EmotionModel& emotion() const noexcept { return emotion_; }

  PersistedPersonalityState snapshot() const noexcept;
  bool restore(const PersistedPersonalityState& state) noexcept;
  void reset(std::uint64_t seed) noexcept;

  static PersonalityOutput safe_output(
      std::uint64_t monotonic_time_ns = 0) noexcept;
  static bool valid_config(const PersonalityConfig& config) noexcept;

 private:
  static constexpr float kMaxRememberedAgeS = 86400.0F;

  std::uint64_t next_random() noexcept;
  float random_unit() noexcept;
  float random_range(float minimum, float maximum) noexcept;
  void schedule_settled_delay(bool quiet) noexcept;
  void begin_idle_orientation() noexcept;
  void update_idle(float elapsed_s, bool quiet, bool paused,
                   bool externally_engaged) noexcept;
  void update_gaze(float elapsed_s, float target_x, float target_y,
                   float response_time_s) noexcept;
  void compose_output(const PersonalityInput& input, bool circadian_quiet,
                      bool explicit_quiet, bool paused,
                      bool external_attention) noexcept;
  void clear_transients() noexcept;

  PersonalityConfig config_;
  EmotionModel emotion_;
  PersonalityOutput output_{};
  std::uint64_t rng_state_{0};
  std::uint64_t last_monotonic_time_ns_{0};
  std::uint64_t sequence_{0};
  float total_awake_s_{0.0F};
  float since_interaction_s_{kMaxRememberedAgeS};
  float since_engagement_s_{kMaxRememberedAgeS};
  float idle_delay_remaining_s_{0.0F};
  float phase_remaining_s_{0.0F};
  float gaze_x_{0.0F};
  float gaze_y_{0.0F};
  float gaze_target_x_{0.0F};
  float gaze_target_y_{0.0F};
  MicroBehavior micro_behavior_{MicroBehavior::Settled};
  bool initialized_{false};
  bool interaction_active_{false};
  bool recent_outcome_{false};
  int last_idle_side_{0};
};

}  // namespace sherman::personality
