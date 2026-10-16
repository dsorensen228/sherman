#pragma once

#include <array>
#include <cstddef>
#include <cstdint>

namespace sherman::personality {

// Stable semantic moods. Display code owns the visual treatment for each mood.
enum class Mood : std::uint8_t {
  Calm = 0,
  Curious,
  Focused,
  Pleased,
  Uncertain,
  Frustrated,
  Tired,
  Count,
};

const char* to_string(Mood mood) noexcept;

// Explicit observations/outcomes that may change the internal state. These are
// semantic events, not commands to display a particular animation.
enum class EmotionEvent : std::uint8_t {
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
  Count,
};

// All needs are normalized to [0, 1]. They describe presentation/policy state
// only and do not grant motion or other safety authority.
struct Needs {
  float energy{0.82F};
  float curiosity{0.58F};
  float social_engagement{0.42F};
  float confidence{0.64F};
  float frustration{0.06F};
  float urgency{0.0F};
};

// Continuous, validated input held for one advance() interval.
struct Stimulus {
  float activity_load{0.0F};
  float task_engagement{0.0F};
  float social_engagement{0.0F};
  float novelty{0.0F};
  float external_urgency{0.0F};
  bool resting{false};
};

// Renderer-facing semantics. No raw pixels and no authoritative fault/privacy
// overlays are supplied by personality.
struct ExpressionIntent {
  Mood mood{Mood::Calm};
  float valence{0.0F};       // [-1, 1]
  float arousal{0.0F};       // [0, 1]
  float confidence{0.5F};    // [0, 1]
  float attention{0.0F};     // [0, 1]
};

struct EmotionConfig {
  Needs baseline{};
  // energy, curiosity, social engagement, confidence, frustration, urgency
  std::array<float, 6> relaxation_time_s{{300.0F, 25.0F, 60.0F, 90.0F,
                                           18.0F, 4.0F}};
  float presentation_filter_time_s{0.18F};
  float mood_transition_s{0.25F};
  float event_cooldown_s{0.25F};
  float positive_affect_decay_s{6.0F};
  float negative_affect_decay_s{4.0F};
};

// Small, storage-format-independent restart snapshot. Callers may encode this
// in their versioned store; restore() rejects unknown versions and corrupt data.
struct PersistedEmotionState {
  static constexpr std::uint16_t kCurrentVersion = 1;

  std::uint16_t version{kCurrentVersion};
  Needs needs{};
  Mood mood{Mood::Calm};
  float valence{0.0F};
  float arousal{0.0F};
};

class EmotionModel {
 public:
  explicit EmotionModel(EmotionConfig config = {});

  // Returns false for an invalid enum, non-finite/non-positive strength, or an
  // event still inside its repetition cooldown. Strengths above 1 are clamped.
  bool apply(EmotionEvent event, float strength = 1.0F) noexcept;

  // Advances using an injected elapsed time. Invalid elapsed time/stimulus is
  // rejected without changing state. Stimulus fields outside [0,1] are clamped.
  bool advance(float elapsed_s, Stimulus stimulus = {}) noexcept;

  const Needs& needs() const noexcept { return needs_; }
  const ExpressionIntent& expression() const noexcept { return expression_; }

  PersistedEmotionState snapshot() const noexcept;

  // Restart policy: durable needs and presentation are restored; transient
  // affects, stimulus, transition progress and event cooldowns are cleared.
  // On rejection the model is reset to configured defaults.
  bool restore(const PersistedEmotionState& state) noexcept;
  void reset() noexcept;

 private:
  static constexpr std::size_t kNeedCount = 6;
  static constexpr std::size_t kEventCount =
      static_cast<std::size_t>(EmotionEvent::Count);

  Mood derive_mood() const noexcept;
  void update_expression(float elapsed_s, Mood mood_at_interval_start) noexcept;

  EmotionConfig config_;
  Needs needs_;
  Stimulus stimulus_{};
  ExpressionIntent expression_{};
  float positive_affect_{0.0F};
  float negative_affect_{0.0F};
  Mood mood_candidate_{Mood::Calm};
  float mood_candidate_elapsed_s_{0.0F};
  std::array<float, kEventCount> cooldown_remaining_s_{};
};

}  // namespace sherman::personality
