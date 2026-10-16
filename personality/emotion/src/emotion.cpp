#include "sherman/personality/emotion.hpp"

#include <algorithm>
#include <cmath>
#include <utility>

namespace sherman::personality {
namespace {

constexpr float kMinimumTimeConstantS = 0.001F;

float clamp01(float value) noexcept {
  return std::clamp(value, 0.0F, 1.0F);
}

bool is_unit(float value) noexcept {
  return std::isfinite(value) && value >= 0.0F && value <= 1.0F;
}

bool valid_needs(const Needs& needs) noexcept {
  return is_unit(needs.energy) && is_unit(needs.curiosity) &&
         is_unit(needs.social_engagement) && is_unit(needs.confidence) &&
         is_unit(needs.frustration) && is_unit(needs.urgency);
}

bool valid_stimulus(const Stimulus& stimulus) noexcept {
  return std::isfinite(stimulus.activity_load) &&
         std::isfinite(stimulus.task_engagement) &&
         std::isfinite(stimulus.social_engagement) &&
         std::isfinite(stimulus.novelty) &&
         std::isfinite(stimulus.external_urgency);
}

Stimulus clamp_stimulus(Stimulus stimulus) noexcept {
  stimulus.activity_load = clamp01(stimulus.activity_load);
  stimulus.task_engagement = clamp01(stimulus.task_engagement);
  stimulus.social_engagement = clamp01(stimulus.social_engagement);
  stimulus.novelty = clamp01(stimulus.novelty);
  stimulus.external_urgency = clamp01(stimulus.external_urgency);
  return stimulus;
}

float relax(float current, float target, float elapsed_s,
            float time_constant_s) noexcept {
  const float alpha = -std::expm1(-elapsed_s / time_constant_s);
  return clamp01(current + (target - current) * alpha);
}

float decay(float value, float elapsed_s, float time_constant_s) noexcept {
  return clamp01(value * std::exp(-elapsed_s / time_constant_s));
}

bool valid_mood(Mood mood) noexcept {
  return static_cast<std::uint8_t>(mood) <
         static_cast<std::uint8_t>(Mood::Count);
}

EmotionConfig sanitize(EmotionConfig config) noexcept {
  const EmotionConfig defaults;
  if (!valid_needs(config.baseline)) {
    config.baseline = defaults.baseline;
  }
  for (std::size_t i = 0; i < config.relaxation_time_s.size(); ++i) {
    if (!std::isfinite(config.relaxation_time_s[i]) ||
        config.relaxation_time_s[i] < kMinimumTimeConstantS) {
      config.relaxation_time_s[i] = defaults.relaxation_time_s[i];
    }
  }
  auto sanitize_time = [](float value, float fallback) {
    return std::isfinite(value) && value >= kMinimumTimeConstantS ? value
                                                                  : fallback;
  };
  config.presentation_filter_time_s =
      sanitize_time(config.presentation_filter_time_s,
                    defaults.presentation_filter_time_s);
  config.mood_transition_s =
      sanitize_time(config.mood_transition_s, defaults.mood_transition_s);
  config.event_cooldown_s =
      sanitize_time(config.event_cooldown_s, defaults.event_cooldown_s);
  config.positive_affect_decay_s =
      sanitize_time(config.positive_affect_decay_s,
                    defaults.positive_affect_decay_s);
  config.negative_affect_decay_s =
      sanitize_time(config.negative_affect_decay_s,
                    defaults.negative_affect_decay_s);
  return config;
}

}  // namespace

const char* to_string(Mood mood) noexcept {
  switch (mood) {
    case Mood::Calm:
      return "calm";
    case Mood::Curious:
      return "curious";
    case Mood::Focused:
      return "focused";
    case Mood::Pleased:
      return "pleased";
    case Mood::Uncertain:
      return "uncertain";
    case Mood::Frustrated:
      return "frustrated";
    case Mood::Tired:
      return "tired";
    case Mood::Count:
      break;
  }
  return "unknown";
}

EmotionModel::EmotionModel(EmotionConfig config)
    : config_(sanitize(std::move(config))) {
  reset();
}

void EmotionModel::reset() noexcept {
  needs_ = config_.baseline;
  stimulus_ = {};
  positive_affect_ = 0.0F;
  negative_affect_ = 0.0F;
  expression_ = {};
  expression_.confidence = needs_.confidence;
  expression_.mood = Mood::Calm;
  mood_candidate_ = Mood::Calm;
  mood_candidate_elapsed_s_ = 0.0F;
  cooldown_remaining_s_.fill(0.0F);
}

bool EmotionModel::apply(EmotionEvent event, float strength) noexcept {
  const auto event_index = static_cast<std::size_t>(event);
  if (event_index >= kEventCount || !std::isfinite(strength) ||
      strength <= 0.0F || cooldown_remaining_s_[event_index] > 0.0F) {
    return false;
  }

  strength = clamp01(strength);
  cooldown_remaining_s_[event_index] = config_.event_cooldown_s;

  auto add = [strength](float& value, float amount) {
    value = clamp01(value + amount * strength);
  };

  switch (event) {
    case EmotionEvent::Discovery:
      add(needs_.curiosity, -0.12F);
      add(needs_.confidence, 0.06F);
      add(needs_.frustration, -0.08F);
      add(positive_affect_, 0.72F);
      break;
    case EmotionEvent::TaskStarted:
      add(needs_.urgency, 0.22F);
      add(needs_.confidence, 0.03F);
      break;
    case EmotionEvent::TaskSucceeded:
      add(needs_.confidence, 0.16F);
      add(needs_.frustration, -0.22F);
      add(needs_.urgency, -0.20F);
      add(positive_affect_, 1.0F);
      add(negative_affect_, -0.35F);
      break;
    case EmotionEvent::TaskFailed:
      add(needs_.confidence, -0.13F);
      add(needs_.frustration, 0.18F);
      add(needs_.urgency, 0.06F);
      add(negative_affect_, 0.38F);
      break;
    case EmotionEvent::Blocked:
      add(needs_.confidence, -0.05F);
      add(needs_.frustration, 0.24F);
      add(needs_.urgency, 0.07F);
      add(negative_affect_, 0.48F);
      break;
    case EmotionEvent::SocialContact:
      add(needs_.social_engagement, 0.18F);
      add(positive_affect_, 0.30F);
      break;
    case EmotionEvent::SocialMissed:
      add(needs_.social_engagement, -0.10F);
      add(needs_.confidence, -0.03F);
      add(negative_affect_, 0.15F);
      break;
    case EmotionEvent::PickedUp:
      add(needs_.frustration, 0.14F);
      add(needs_.urgency, 0.32F);
      add(negative_affect_, 0.70F);
      break;
    case EmotionEvent::Rested:
      add(needs_.energy, 0.28F);
      add(needs_.frustration, -0.18F);
      add(negative_affect_, -0.30F);
      break;
    case EmotionEvent::EnergyDepleted:
      add(needs_.energy, -0.34F);
      add(needs_.urgency, 0.12F);
      break;
    case EmotionEvent::UrgentRequest:
      add(needs_.urgency, 0.56F);
      break;
    case EmotionEvent::Calmed:
      add(needs_.frustration, -0.36F);
      add(needs_.urgency, -0.34F);
      add(negative_affect_, -0.55F);
      break;
    case EmotionEvent::Count:
      return false;
  }
  return true;
}

bool EmotionModel::advance(float elapsed_s, Stimulus stimulus) noexcept {
  if (!std::isfinite(elapsed_s) || elapsed_s < 0.0F ||
      !valid_stimulus(stimulus)) {
    return false;
  }
  stimulus_ = clamp_stimulus(stimulus);
  const Mood mood_at_interval_start = derive_mood();

  for (float& cooldown_s : cooldown_remaining_s_) {
    cooldown_s = std::max(0.0F, cooldown_s - elapsed_s);
  }

  const float energy_target =
      clamp01(config_.baseline.energy + (stimulus_.resting ? 0.18F : 0.0F) -
              0.58F * stimulus_.activity_load);
  const float curiosity_target =
      clamp01(config_.baseline.curiosity + 0.34F * stimulus_.novelty -
              0.10F * stimulus_.task_engagement);
  const float social_target =
      clamp01(config_.baseline.social_engagement +
              0.42F * stimulus_.social_engagement);
  const float confidence_target =
      clamp01(config_.baseline.confidence +
              0.08F * stimulus_.task_engagement);
  const float frustration_target = config_.baseline.frustration;
  const float urgency_target =
      std::max(config_.baseline.urgency, stimulus_.external_urgency);

  needs_.energy = relax(needs_.energy, energy_target, elapsed_s,
                        config_.relaxation_time_s[0]);
  needs_.curiosity = relax(needs_.curiosity, curiosity_target, elapsed_s,
                           config_.relaxation_time_s[1]);
  needs_.social_engagement =
      relax(needs_.social_engagement, social_target, elapsed_s,
            config_.relaxation_time_s[2]);
  needs_.confidence = relax(needs_.confidence, confidence_target, elapsed_s,
                            config_.relaxation_time_s[3]);
  needs_.frustration =
      relax(needs_.frustration, frustration_target, elapsed_s,
            config_.relaxation_time_s[4]);
  needs_.urgency = relax(needs_.urgency, urgency_target, elapsed_s,
                         config_.relaxation_time_s[5]);

  positive_affect_ = decay(positive_affect_, elapsed_s,
                           config_.positive_affect_decay_s);
  negative_affect_ = decay(negative_affect_, elapsed_s,
                           config_.negative_affect_decay_s);

  update_expression(elapsed_s, mood_at_interval_start);
  return true;
}

Mood EmotionModel::derive_mood() const noexcept {
  if (needs_.energy <= 0.30F) {
    return Mood::Tired;
  }
  if (needs_.frustration >= 0.60F) {
    return Mood::Frustrated;
  }
  if (needs_.confidence <= 0.35F) {
    return Mood::Uncertain;
  }
  if (std::max(needs_.urgency, stimulus_.task_engagement) >= 0.62F) {
    return Mood::Focused;
  }
  if (positive_affect_ >= 0.46F) {
    return Mood::Pleased;
  }
  if (needs_.curiosity >= 0.70F || stimulus_.novelty >= 0.52F) {
    return Mood::Curious;
  }
  return Mood::Calm;
}

void EmotionModel::update_expression(
    float elapsed_s, Mood mood_at_interval_start) noexcept {
  const float attention_target =
      std::max({stimulus_.task_engagement, stimulus_.external_urgency,
                stimulus_.novelty * needs_.curiosity});
  const float valence_target = std::clamp(
      0.45F * (needs_.confidence - 0.5F) +
          0.25F * (needs_.energy - 0.5F) + 0.65F * positive_affect_ -
          0.65F * negative_affect_ - 0.50F * needs_.frustration,
      -1.0F, 1.0F);
  const float arousal_target =
      std::max({needs_.urgency, 0.90F * needs_.frustration,
                0.80F * attention_target, 0.45F * positive_affect_,
                0.70F * negative_affect_});

  const float alpha =
      -std::expm1(-elapsed_s / config_.presentation_filter_time_s);
  expression_.valence = std::clamp(
      expression_.valence + (valence_target - expression_.valence) * alpha,
      -1.0F, 1.0F);
  expression_.arousal = clamp01(
      expression_.arousal + (arousal_target - expression_.arousal) * alpha);
  expression_.confidence = clamp01(
      expression_.confidence + (needs_.confidence - expression_.confidence) *
                                   alpha);
  expression_.attention = clamp01(
      expression_.attention + (attention_target - expression_.attention) *
                                  alpha);

  const Mood mood_at_interval_end = derive_mood();
  if (mood_at_interval_end == expression_.mood) {
    mood_candidate_ = mood_at_interval_end;
    mood_candidate_elapsed_s_ = 0.0F;
    return;
  }

  // A candidate that is present at both ends is known to have occupied this
  // interval. If a continuously changing need crosses a mood boundary during
  // the interval, counting the whole interval would backdate the new mood and
  // make a single coarse tick transition sooner than equivalent fine ticks.
  // Conservatively begin its dwell clock at the boundary observation.
  const float candidate_elapsed_s =
      mood_at_interval_start == mood_at_interval_end ? elapsed_s : 0.0F;
  if (mood_at_interval_start != mood_at_interval_end ||
      mood_at_interval_end != mood_candidate_) {
    mood_candidate_ = mood_at_interval_end;
    mood_candidate_elapsed_s_ = candidate_elapsed_s;
  } else {
    mood_candidate_elapsed_s_ =
        std::min(config_.mood_transition_s,
                 mood_candidate_elapsed_s_ + candidate_elapsed_s);
  }
  if (mood_candidate_elapsed_s_ >= config_.mood_transition_s) {
    expression_.mood = mood_candidate_;
    mood_candidate_elapsed_s_ = 0.0F;
  }
}

PersistedEmotionState EmotionModel::snapshot() const noexcept {
  PersistedEmotionState state;
  state.needs = needs_;
  state.mood = expression_.mood;
  state.valence = expression_.valence;
  state.arousal = expression_.arousal;
  return state;
}

bool EmotionModel::restore(const PersistedEmotionState& state) noexcept {
  if (state.version != PersistedEmotionState::kCurrentVersion ||
      !valid_needs(state.needs) || !valid_mood(state.mood) ||
      !std::isfinite(state.valence) || state.valence < -1.0F ||
      state.valence > 1.0F || !is_unit(state.arousal)) {
    reset();
    return false;
  }

  needs_ = state.needs;
  stimulus_ = {};
  positive_affect_ = 0.0F;
  negative_affect_ = 0.0F;
  expression_.mood = state.mood;
  expression_.valence = state.valence;
  expression_.arousal = state.arousal;
  expression_.confidence = needs_.confidence;
  expression_.attention = 0.0F;
  mood_candidate_ = state.mood;
  mood_candidate_elapsed_s_ = 0.0F;
  cooldown_remaining_s_.fill(0.0F);
  return true;
}

}  // namespace sherman::personality
