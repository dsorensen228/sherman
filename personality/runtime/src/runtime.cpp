#include "sherman/personality/runtime.hpp"

#include <algorithm>
#include <cmath>
#include <limits>
#include <utility>

namespace sherman::personality {
namespace {

constexpr float kNanosecondsPerSecond = 1.0e9F;
constexpr float kMaxTotalAwakeS = 315576000.0F;  // Ten years, bounded.
constexpr float kLongDiscontinuityS = 120.0F;

bool unit(float value) noexcept {
  return std::isfinite(value) && value >= 0.0F && value <= 1.0F;
}

float clamp01(float value) noexcept {
  return std::clamp(value, 0.0F, 1.0F);
}

float clamp_age(float value) noexcept {
  return std::clamp(value, 0.0F, 86400.0F);
}

bool finite_input(const PersonalityInput& input) noexcept {
  const float values[] = {
      input.activity_load,       input.task_engagement,
      input.social_engagement,   input.novelty,
      input.external_urgency,    input.attention_target_x,
      input.attention_target_y,  input.attention_salience,
  };
  for (float value : values) {
    if (!std::isfinite(value)) {
      return false;
    }
  }
  return true;
}

bool valid_input_ranges(const PersonalityInput& input) noexcept {
  const float unit_values[] = {
      input.activity_load,      input.task_engagement,
      input.social_engagement,  input.novelty,
      input.external_urgency,   input.attention_salience,
  };
  for (float value : unit_values) {
    if (!unit(value)) {
      return false;
    }
  }
  if ((input.flags & kInputAttentionValid) != 0U) {
    return input.attention_target_x >= -1.0F &&
           input.attention_target_x <= 1.0F &&
           input.attention_target_y >= -1.0F &&
           input.attention_target_y <= 1.0F;
  }
  return true;
}

EmotionConfig emotion_config(const PersonalityConfig& personality) noexcept {
  EmotionConfig config;
  config.baseline.curiosity =
      clamp01(0.38F + 0.30F * personality.curiosity);
  config.baseline.social_engagement =
      clamp01(0.24F + 0.31F * personality.sociability);
  return config;
}

bool valid_mood(Mood mood) noexcept {
  return static_cast<std::uint8_t>(mood) <
         static_cast<std::uint8_t>(Mood::Count);
}

float saturated_add(float value, float increment, float maximum) noexcept {
  if (increment >= maximum - value) {
    return maximum;
  }
  return value + increment;
}

}  // namespace

const char* to_string(MicroBehavior behavior) noexcept {
  switch (behavior) {
    case MicroBehavior::Settled:
      return "settled";
    case MicroBehavior::Orienting:
      return "orienting";
    case MicroBehavior::Observing:
      return "observing";
    case MicroBehavior::Engaged:
      return "engaged";
    case MicroBehavior::Reflecting:
      return "reflecting";
    case MicroBehavior::Drowsy:
      return "drowsy";
    case MicroBehavior::Count:
      break;
  }
  return "unknown";
}

bool PersonalityController::valid_config(
    const PersonalityConfig& config) noexcept {
  return unit(config.curiosity) && unit(config.sociability) &&
         unit(config.calmness) && unit(config.expressiveness) &&
         unit(config.day_activity);
}

PersonalityController::PersonalityController(PersonalityConfig config)
    : config_(valid_config(config) ? std::move(config) : PersonalityConfig{}),
      emotion_(emotion_config(config_)) {
  reset(config_.seed);
}

PersonalityOutput PersonalityController::safe_output(
    std::uint64_t monotonic_time_ns) noexcept {
  PersonalityOutput safe;
  safe.monotonic_time_ns = monotonic_time_ns;
  safe.reason_flags = kReasonFallback;
  safe.confidence = 0.5F;
  safe.eyelid_open = 0.86F;
  safe.blink_rate_hz = 0.16F;
  return safe;
}

void PersonalityController::clear_transients() noexcept {
  last_monotonic_time_ns_ = 0;
  phase_remaining_s_ = 0.0F;
  gaze_x_ = 0.0F;
  gaze_y_ = 0.0F;
  gaze_target_x_ = 0.0F;
  gaze_target_y_ = 0.0F;
  micro_behavior_ = MicroBehavior::Settled;
  initialized_ = false;
  interaction_active_ = false;
  recent_outcome_ = false;
  last_idle_side_ = 0;
}

void PersonalityController::reset(std::uint64_t seed) noexcept {
  emotion_.reset();
  rng_state_ = seed;
  sequence_ = 0;
  total_awake_s_ = 0.0F;
  since_interaction_s_ = kMaxRememberedAgeS;
  since_engagement_s_ = kMaxRememberedAgeS;
  idle_delay_remaining_s_ = 0.0F;
  clear_transients();
  schedule_settled_delay(false);
  output_ = safe_output();
  output_.reason_flags = kReasonStartup;
}

std::uint64_t PersonalityController::next_random() noexcept {
  // SplitMix64 has a full-period state transition and deterministic output on
  // every C++17 target; seed zero is intentionally valid.
  rng_state_ += UINT64_C(0x9e3779b97f4a7c15);
  std::uint64_t value = rng_state_;
  value = (value ^ (value >> 30U)) * UINT64_C(0xbf58476d1ce4e5b9);
  value = (value ^ (value >> 27U)) * UINT64_C(0x94d049bb133111eb);
  return value ^ (value >> 31U);
}

float PersonalityController::random_unit() noexcept {
  constexpr float kScale = 1.0F / 16777216.0F;
  return static_cast<float>(next_random() >> 40U) * kScale;
}

float PersonalityController::random_range(float minimum,
                                          float maximum) noexcept {
  return minimum + (maximum - minimum) * random_unit();
}

void PersonalityController::schedule_settled_delay(bool quiet) noexcept {
  const float curiosity_factor = 1.0F - 0.58F * config_.curiosity;
  const float calm_factor = 0.82F + 0.65F * config_.calmness;
  const float activity_factor = 1.25F - 0.40F * config_.day_activity;
  const float quiet_factor = quiet ? 3.2F : 1.0F;
  idle_delay_remaining_s_ =
      random_range(2.4F, 6.8F) * curiosity_factor * calm_factor *
      activity_factor * quiet_factor;
  idle_delay_remaining_s_ =
      std::clamp(idle_delay_remaining_s_, 1.2F, 24.0F);
}

void PersonalityController::begin_idle_orientation() noexcept {
  micro_behavior_ = MicroBehavior::Orienting;
  phase_remaining_s_ = random_range(0.28F, 0.62F);

  int side = random_unit() < 0.5F ? -1 : 1;
  if (side == last_idle_side_ && random_unit() < 0.72F) {
    side = -side;
  }
  last_idle_side_ = side;
  const float magnitude = random_range(0.28F, 0.78F);
  gaze_target_x_ = static_cast<float>(side) * magnitude;
  gaze_target_y_ = random_range(-0.22F, 0.16F);
}

void PersonalityController::update_idle(float elapsed_s, bool quiet,
                                        bool paused,
                                        bool externally_engaged) noexcept {
  if (paused) {
    micro_behavior_ = MicroBehavior::Settled;
    gaze_target_x_ = 0.0F;
    gaze_target_y_ = 0.05F;
    phase_remaining_s_ = 0.0F;
    schedule_settled_delay(true);
    return;
  }
  if (externally_engaged) {
    micro_behavior_ = MicroBehavior::Engaged;
    phase_remaining_s_ = 0.0F;
    schedule_settled_delay(quiet);
    return;
  }
  if (recent_outcome_ && since_engagement_s_ < 2.4F) {
    micro_behavior_ = MicroBehavior::Reflecting;
    gaze_target_x_ = 0.0F;
    gaze_target_y_ = 0.10F;
    phase_remaining_s_ = 2.4F - since_engagement_s_;
    return;
  }
  if (quiet) {
    micro_behavior_ = MicroBehavior::Drowsy;
    gaze_target_x_ = 0.0F;
    gaze_target_y_ = 0.12F;
    phase_remaining_s_ = 0.0F;
    schedule_settled_delay(true);
    return;
  }

  if (elapsed_s > kLongDiscontinuityS) {
    micro_behavior_ = MicroBehavior::Settled;
    gaze_target_x_ = 0.0F;
    gaze_target_y_ = 0.0F;
    phase_remaining_s_ = 0.0F;
    schedule_settled_delay(false);
    return;
  }

  switch (micro_behavior_) {
    case MicroBehavior::Settled:
    case MicroBehavior::Drowsy:
    case MicroBehavior::Engaged:
    case MicroBehavior::Reflecting:
      micro_behavior_ = MicroBehavior::Settled;
      idle_delay_remaining_s_ -= elapsed_s;
      if (idle_delay_remaining_s_ <= 0.0F) {
        begin_idle_orientation();
      }
      break;
    case MicroBehavior::Orienting:
      phase_remaining_s_ -= elapsed_s;
      if (phase_remaining_s_ <= 0.0F) {
        micro_behavior_ = MicroBehavior::Observing;
        phase_remaining_s_ = random_range(1.1F, 3.4F);
      }
      break;
    case MicroBehavior::Observing:
      phase_remaining_s_ -= elapsed_s;
      if (phase_remaining_s_ <= 0.0F) {
        micro_behavior_ = MicroBehavior::Settled;
        gaze_target_x_ = random_range(-0.06F, 0.06F);
        gaze_target_y_ = random_range(-0.02F, 0.06F);
        schedule_settled_delay(false);
      }
      break;
    case MicroBehavior::Count:
      micro_behavior_ = MicroBehavior::Settled;
      gaze_target_x_ = 0.0F;
      gaze_target_y_ = 0.0F;
      schedule_settled_delay(false);
      break;
  }
}

void PersonalityController::update_gaze(float elapsed_s, float target_x,
                                        float target_y,
                                        float response_time_s) noexcept {
  target_x = std::clamp(target_x, -1.0F, 1.0F);
  target_y = std::clamp(target_y, -1.0F, 1.0F);
  if (elapsed_s <= 0.0F) {
    return;
  }
  const float alpha = -std::expm1(-elapsed_s / response_time_s);
  gaze_x_ = std::clamp(gaze_x_ + (target_x - gaze_x_) * alpha, -1.0F, 1.0F);
  gaze_y_ = std::clamp(gaze_y_ + (target_y - gaze_y_) * alpha, -1.0F, 1.0F);
}

PersonalityStepResult PersonalityController::step(
    const PersonalityInput& input) noexcept {
  if ((input.flags & ~kAllPersonalityInputFlags) != 0U ||
      !finite_input(input) || !valid_input_ranges(input) ||
      (((input.flags & kInputCircadianValid) != 0U) &&
       input.local_second_of_day >= 86400U)) {
    return PersonalityStepResult::InvalidInput;
  }
  if (initialized_ && input.monotonic_time_ns < last_monotonic_time_ns_) {
    return PersonalityStepResult::TimeRegression;
  }

  float elapsed_s = 0.0F;
  if (!initialized_) {
    initialized_ = true;
  } else {
    const std::uint64_t elapsed_ns =
        input.monotonic_time_ns - last_monotonic_time_ns_;
    elapsed_s = static_cast<float>(elapsed_ns) / kNanosecondsPerSecond;
  }
  last_monotonic_time_ns_ = input.monotonic_time_ns;
  total_awake_s_ = saturated_add(total_awake_s_, elapsed_s, kMaxTotalAwakeS);
  since_interaction_s_ =
      saturated_add(since_interaction_s_, elapsed_s, kMaxRememberedAgeS);
  since_engagement_s_ =
      saturated_add(since_engagement_s_, elapsed_s, kMaxRememberedAgeS);
  if (interaction_active_) {
    since_interaction_s_ = 0.0F;
    since_engagement_s_ = 0.0F;
  }
  if (recent_outcome_ && since_engagement_s_ >= 2.4F) {
    recent_outcome_ = false;
  }

  const bool explicit_quiet = (input.flags & kInputQuiet) != 0U;
  const bool paused = (input.flags & kInputPaused) != 0U;
  const bool circadian_valid =
      (input.flags & kInputCircadianValid) != 0U;
  const bool circadian_quiet =
      circadian_valid &&
      (input.local_second_of_day < 7U * 3600U ||
       input.local_second_of_day >= 22U * 3600U + 30U * 60U);
  const bool quiet = explicit_quiet || circadian_quiet;
  const bool task_active = (input.flags & kInputTaskActive) != 0U;
  const bool user_present = (input.flags & kInputUserPresent) != 0U;
  const bool attention_valid =
      (input.flags & kInputAttentionValid) != 0U;
  const float attention_salience = clamp01(input.attention_salience);
  const bool external_attention =
      attention_valid && attention_salience >= 0.05F;
  const bool recent_interaction = since_interaction_s_ < 1.4F;
  const bool externally_engaged =
      task_active || interaction_active_ || recent_interaction ||
      external_attention;

  Stimulus stimulus;
  stimulus.activity_load = clamp01(input.activity_load);
  stimulus.task_engagement = clamp01(std::max(
      input.task_engagement, task_active ? 0.72F : 0.0F));
  stimulus.social_engagement = clamp01(
      input.social_engagement +
      (user_present ? 0.18F * config_.sociability : 0.0F));
  stimulus.novelty =
      clamp01(input.novelty * (0.65F + 0.50F * config_.curiosity));
  stimulus.external_urgency = clamp01(input.external_urgency);
  stimulus.resting = (input.flags & kInputResting) != 0U || quiet || paused;
  if (!emotion_.advance(elapsed_s, stimulus)) {
    return PersonalityStepResult::InvalidInput;
  }

  update_idle(elapsed_s, quiet, paused, externally_engaged);
  if (external_attention) {
    gaze_target_x_ = std::clamp(input.attention_target_x, -1.0F, 1.0F);
    gaze_target_y_ = std::clamp(input.attention_target_y, -1.0F, 1.0F);
  } else if (task_active || recent_interaction || interaction_active_) {
    gaze_target_x_ = 0.0F;
    gaze_target_y_ = -0.04F;
  }

  float response_time_s = 0.24F;
  if (external_attention) {
    response_time_s = 0.09F + 0.16F * (1.0F - attention_salience);
  } else if (micro_behavior_ == MicroBehavior::Drowsy) {
    response_time_s = 0.55F;
  }
  update_gaze(elapsed_s, gaze_target_x_, gaze_target_y_, response_time_s);
  compose_output(input, circadian_quiet, explicit_quiet, paused,
                 external_attention);
  return PersonalityStepResult::Ok;
}

PersonalityEventResult PersonalityController::apply(PersonalityEvent event,
                                                    float strength) noexcept {
  const auto value = static_cast<std::int32_t>(event);
  if (value < 0 || value >= static_cast<std::int32_t>(PersonalityEvent::Count) ||
      !std::isfinite(strength) || strength <= 0.0F) {
    return PersonalityEventResult::InvalidInput;
  }

  EmotionEvent emotion_event = EmotionEvent::Calmed;
  bool has_emotion_event = true;
  switch (event) {
    case PersonalityEvent::Discovery:
      emotion_event = EmotionEvent::Discovery;
      break;
    case PersonalityEvent::TaskStarted:
      emotion_event = EmotionEvent::TaskStarted;
      break;
    case PersonalityEvent::TaskSucceeded:
      emotion_event = EmotionEvent::TaskSucceeded;
      break;
    case PersonalityEvent::TaskFailed:
      emotion_event = EmotionEvent::TaskFailed;
      break;
    case PersonalityEvent::Blocked:
      emotion_event = EmotionEvent::Blocked;
      break;
    case PersonalityEvent::SocialContact:
      emotion_event = EmotionEvent::SocialContact;
      break;
    case PersonalityEvent::SocialMissed:
      emotion_event = EmotionEvent::SocialMissed;
      break;
    case PersonalityEvent::PickedUp:
      emotion_event = EmotionEvent::PickedUp;
      break;
    case PersonalityEvent::Rested:
      emotion_event = EmotionEvent::Rested;
      break;
    case PersonalityEvent::EnergyDepleted:
      emotion_event = EmotionEvent::EnergyDepleted;
      break;
    case PersonalityEvent::UrgentRequest:
      emotion_event = EmotionEvent::UrgentRequest;
      break;
    case PersonalityEvent::Calmed:
      emotion_event = EmotionEvent::Calmed;
      break;
    case PersonalityEvent::InteractionStarted:
      emotion_event = EmotionEvent::SocialContact;
      break;
    case PersonalityEvent::InteractionEnded:
      has_emotion_event = false;
      break;
    case PersonalityEvent::Count:
      return PersonalityEventResult::InvalidInput;
  }

  if (has_emotion_event && !emotion_.apply(emotion_event, strength) &&
      event != PersonalityEvent::InteractionStarted) {
    return PersonalityEventResult::CooledDown;
  }
  switch (event) {
    case PersonalityEvent::Discovery:
    case PersonalityEvent::TaskSucceeded:
    case PersonalityEvent::TaskFailed:
    case PersonalityEvent::Blocked:
    case PersonalityEvent::SocialMissed:
    case PersonalityEvent::PickedUp:
      recent_outcome_ = true;
      since_engagement_s_ = 0.0F;
      break;
    case PersonalityEvent::TaskStarted:
    case PersonalityEvent::UrgentRequest:
      since_engagement_s_ = 0.0F;
      break;
    case PersonalityEvent::SocialContact:
      since_interaction_s_ = 0.0F;
      since_engagement_s_ = 0.0F;
      break;
    case PersonalityEvent::Calmed:
      recent_outcome_ = false;
      break;
    case PersonalityEvent::InteractionStarted:
      interaction_active_ = true;
      since_interaction_s_ = 0.0F;
      since_engagement_s_ = 0.0F;
      break;
    case PersonalityEvent::InteractionEnded:
      interaction_active_ = false;
      since_interaction_s_ = 0.0F;
      since_engagement_s_ = 0.0F;
      recent_outcome_ = true;
      break;
    case PersonalityEvent::Rested:
    case PersonalityEvent::EnergyDepleted:
    case PersonalityEvent::Count:
      break;
  }
  return PersonalityEventResult::Accepted;
}

void PersonalityController::compose_output(const PersonalityInput& input,
                                           bool circadian_quiet,
                                           bool explicit_quiet, bool paused,
                                           bool external_attention) noexcept {
  const ExpressionIntent& expression = emotion_.expression();
  output_.monotonic_time_ns = input.monotonic_time_ns;
  output_.sequence = ++sequence_;
  output_.expression = expression.mood;
  output_.micro_behavior = micro_behavior_;
  output_.reason_flags = 0U;
  if (total_awake_s_ < 1.0F) {
    output_.reason_flags |= kReasonStartup;
  }
  if (circadian_quiet) {
    output_.reason_flags |= kReasonCircadianQuiet;
  }
  if (explicit_quiet) {
    output_.reason_flags |= kReasonExplicitQuiet;
  }
  if (paused) {
    output_.reason_flags |= kReasonPaused;
  }
  if (external_attention) {
    output_.reason_flags |= kReasonExternalAttention;
  }
  if (since_interaction_s_ < 4.0F) {
    output_.reason_flags |= kReasonRecentInteraction;
  }
  if ((input.flags & kInputTaskActive) != 0U) {
    output_.reason_flags |= kReasonTaskEngaged;
  }
  if (micro_behavior_ == MicroBehavior::Orienting ||
      micro_behavior_ == MicroBehavior::Observing) {
    output_.reason_flags |= kReasonSpontaneousIdle;
  }
  if (emotion_.needs().energy <= 0.30F) {
    output_.reason_flags |= kReasonLowEnergy;
  }
  if (recent_outcome_) {
    output_.reason_flags |= kReasonRecentOutcome;
  }

  output_.valence = expression.valence;
  output_.arousal = expression.arousal;
  output_.confidence = expression.confidence;
  output_.attention = expression.attention;
  if (external_attention) {
    output_.attention =
        std::max(output_.attention, clamp01(input.attention_salience));
  }
  output_.gaze_x = gaze_x_;
  output_.gaze_y = gaze_y_;

  float eyelid_open = 0.96F;
  float blink_rate_hz = 0.16F;
  switch (expression.mood) {
    case Mood::Calm:
      break;
    case Mood::Curious:
      eyelid_open = 1.0F;
      blink_rate_hz = 0.18F;
      break;
    case Mood::Focused:
      eyelid_open = 0.93F;
      blink_rate_hz = 0.10F;
      break;
    case Mood::Pleased:
      eyelid_open = 0.91F;
      blink_rate_hz = 0.19F;
      break;
    case Mood::Uncertain:
      eyelid_open = 0.84F;
      blink_rate_hz = 0.22F;
      break;
    case Mood::Frustrated:
      eyelid_open = 0.79F;
      blink_rate_hz = 0.24F;
      break;
    case Mood::Tired:
      eyelid_open = 0.62F;
      blink_rate_hz = 0.28F;
      break;
    case Mood::Count:
      eyelid_open = 0.86F;
      break;
  }
  const bool quiet = circadian_quiet || explicit_quiet;
  if (quiet && !external_attention) {
    eyelid_open = std::min(eyelid_open, 0.72F);
    blink_rate_hz = std::max(blink_rate_hz, 0.24F);
  }
  if (paused) {
    eyelid_open = std::min(eyelid_open, 0.78F);
    blink_rate_hz = 0.12F;
  }
  const float expression_scale = 0.55F + 0.70F * config_.expressiveness;
  output_.eyelid_open = clamp01(1.0F - (1.0F - eyelid_open) * expression_scale);
  output_.blink_rate_hz =
      std::clamp(blink_rate_hz * expression_scale, 0.05F, 0.40F);
}

PersistedPersonalityState PersonalityController::snapshot() const noexcept {
  PersistedPersonalityState state;
  state.rng_state = rng_state_;
  state.sequence = sequence_;
  state.total_awake_s = total_awake_s_;
  state.since_interaction_s = since_interaction_s_;
  state.since_engagement_s = since_engagement_s_;
  state.idle_delay_remaining_s =
      std::clamp(idle_delay_remaining_s_, 0.0F, 24.0F);
  state.emotion = emotion_.snapshot();
  return state;
}

bool PersonalityController::restore(
    const PersistedPersonalityState& state) noexcept {
  const bool valid =
      state.version == PersistedPersonalityState::kCurrentVersion &&
      std::isfinite(state.total_awake_s) && state.total_awake_s >= 0.0F &&
      state.total_awake_s <= kMaxTotalAwakeS &&
      std::isfinite(state.since_interaction_s) &&
      state.since_interaction_s >= 0.0F &&
      state.since_interaction_s <= kMaxRememberedAgeS &&
      std::isfinite(state.since_engagement_s) &&
      state.since_engagement_s >= 0.0F &&
      state.since_engagement_s <= kMaxRememberedAgeS &&
      std::isfinite(state.idle_delay_remaining_s) &&
      state.idle_delay_remaining_s >= 0.0F &&
      state.idle_delay_remaining_s <= 24.0F && valid_mood(state.emotion.mood);
  if (!valid || !emotion_.restore(state.emotion)) {
    reset(config_.seed);
    return false;
  }

  rng_state_ = state.rng_state;
  sequence_ = state.sequence;
  total_awake_s_ = state.total_awake_s;
  since_interaction_s_ = clamp_age(state.since_interaction_s);
  since_engagement_s_ = clamp_age(state.since_engagement_s);
  idle_delay_remaining_s_ = state.idle_delay_remaining_s;
  clear_transients();
  output_ = safe_output();
  output_.expression = emotion_.expression().mood;
  output_.valence = emotion_.expression().valence;
  output_.arousal = emotion_.expression().arousal;
  output_.confidence = emotion_.expression().confidence;
  output_.reason_flags = kReasonStartup;
  return true;
}

}  // namespace sherman::personality
