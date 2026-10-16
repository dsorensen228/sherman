#include "sherman/personality/emotion.hpp"

#include <cmath>
#include <cstdlib>
#include <iostream>
#include <limits>
#include <string_view>

namespace {

using sherman::personality::EmotionConfig;
using sherman::personality::EmotionEvent;
using sherman::personality::EmotionModel;
using sherman::personality::Mood;
using sherman::personality::PersistedEmotionState;
using sherman::personality::Stimulus;

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

bool bounded(const EmotionModel& model) {
  const auto& needs = model.needs();
  const auto& expression = model.expression();
  const float values[] = {needs.energy,
                          needs.curiosity,
                          needs.social_engagement,
                          needs.confidence,
                          needs.frustration,
                          needs.urgency,
                          expression.arousal,
                          expression.confidence,
                          expression.attention};
  for (float value : values) {
    if (!std::isfinite(value) || value < 0.0F || value > 1.0F) {
      return false;
    }
  }
  return std::isfinite(expression.valence) && expression.valence >= -1.0F &&
         expression.valence <= 1.0F;
}

void settle(EmotionModel& model, Stimulus stimulus = {},
            float duration_s = 0.5F) {
  constexpr float kStepS = 0.05F;
  for (float time_s = 0.0F; time_s < duration_s; time_s += kStepS) {
    expect(model.advance(kStepS, stimulus), "settle advance succeeds");
  }
}

void test_defaults_and_names() {
  EmotionModel model;
  expect(bounded(model), "default state is bounded");
  expect(model.expression().mood == Mood::Calm, "default mood is calm");
  expect(std::string_view(sherman::personality::to_string(Mood::Frustrated)) ==
             "frustrated",
         "mood names are stable");
  expect(std::string_view(sherman::personality::to_string(Mood::Count)) ==
             "unknown",
         "invalid mood name is safe");
  expect(std::string_view(sherman::personality::to_string(
             static_cast<Mood>(255))) == "unknown",
         "out-of-range mood name is safe");
}

void test_events_are_bounded_and_cooled_down() {
  EmotionModel model;
  expect(model.apply(EmotionEvent::Blocked), "first event is accepted");
  expect(!model.apply(EmotionEvent::Blocked), "duplicate event is cooled down");
  expect(model.advance(0.25F), "cooldown clock advances");
  expect(model.apply(EmotionEvent::Blocked),
         "event is accepted after cooldown");

  for (int event = 0; event < static_cast<int>(EmotionEvent::Count); ++event) {
    for (int repetition = 0; repetition < 20; ++repetition) {
      model.advance(0.25F);
      model.apply(static_cast<EmotionEvent>(event), 4.0F);
      expect(bounded(model), "state remains bounded under repeated events");
    }
  }

  expect(!model.apply(EmotionEvent::Count), "sentinel event is rejected");
  expect(!model.apply(static_cast<EmotionEvent>(255)),
         "out-of-range event is rejected");
  expect(!model.apply(EmotionEvent::Discovery, 0.0F),
         "zero event strength is rejected");
  expect(!model.apply(EmotionEvent::Discovery,
                      std::numeric_limits<float>::quiet_NaN()),
         "non-finite event strength is rejected");
}

void test_mood_transition_is_not_backdated_across_a_threshold() {
  EmotionConfig config;
  config.relaxation_time_s.fill(1.0F);
  config.mood_transition_s = 0.25F;

  PersistedEmotionState state;
  state.needs.frustration = 0.90F;
  state.mood = Mood::Frustrated;

  EmotionModel coarse(config);
  EmotionModel fine(config);
  expect(coarse.restore(state), "coarse transition fixture restores");
  expect(fine.restore(state), "fine transition fixture restores");

  expect(coarse.advance(0.50F), "coarse threshold-crossing tick succeeds");
  for (int tick = 0; tick < 5; ++tick) {
    expect(fine.advance(0.10F), "fine threshold-crossing tick succeeds");
  }
  expect(coarse.expression().mood == Mood::Frustrated,
         "coarse tick does not backdate a newly observed mood candidate");
  expect(fine.expression().mood == Mood::Frustrated,
         "fine ticks retain the old mood until candidate dwell completes");

  expect(coarse.advance(0.25F), "coarse candidate dwell succeeds");
  expect(fine.advance(0.25F), "fine candidate dwell succeeds");
  expect(coarse.expression().mood == Mood::Calm,
         "coarse tick transitions after full candidate dwell");
  expect(fine.expression().mood == Mood::Calm,
         "fine ticks transition after full candidate dwell");
}

void test_direct_stimulus_can_occupy_a_whole_interval() {
  EmotionConfig config;
  config.mood_transition_s = 0.25F;
  EmotionModel model(config);
  Stimulus task;
  task.task_engagement = 1.0F;

  expect(model.advance(0.25F, task), "focused dwell interval succeeds");
  expect(model.expression().mood == Mood::Focused,
         "stimulus held for a full interval completes mood dwell");
}

void test_candidate_dwell_restarts_after_a_boundary_crossing() {
  EmotionConfig config;
  config.relaxation_time_s[1] = 1.0F;
  config.mood_transition_s = 0.25F;
  PersistedEmotionState state;
  state.needs.curiosity = 0.65F;

  EmotionModel model(config);
  expect(model.restore(state), "candidate reset fixture restores");

  Stimulus direct_novelty;
  direct_novelty.novelty = 0.90F;
  expect(model.advance(0.20F, direct_novelty),
         "initial curious candidate dwell succeeds");
  expect(model.expression().mood == Mood::Calm,
         "partial candidate dwell does not transition");

  Stimulus indirect_novelty;
  indirect_novelty.novelty = 0.40F;
  expect(model.advance(0.50F, indirect_novelty),
         "curiosity threshold-crossing interval succeeds");
  expect(model.expression().mood == Mood::Calm,
         "candidate interrupted at interval start loses prior dwell");

  expect(model.advance(0.05F, indirect_novelty),
         "new candidate dwell interval succeeds");
  expect(model.expression().mood == Mood::Calm,
         "new candidate has not inherited interrupted dwell time");
  expect(model.advance(0.20F, indirect_novelty),
         "remaining candidate dwell succeeds");
  expect(model.expression().mood == Mood::Curious,
         "continuous replacement candidate eventually transitions");
}

void test_tick_rate_independence() {
  EmotionModel one_tick;
  EmotionModel many_ticks;
  Stimulus stimulus;
  stimulus.activity_load = 0.65F;
  stimulus.task_engagement = 0.55F;
  stimulus.social_engagement = 0.2F;
  stimulus.novelty = 0.7F;
  stimulus.external_urgency = 0.35F;

  expect(one_tick.advance(10.0F, stimulus), "single long tick succeeds");
  for (int i = 0; i < 100; ++i) {
    expect(many_ticks.advance(0.1F, stimulus), "short tick succeeds");
  }

  const auto& one = one_tick.needs();
  const auto& many = many_ticks.needs();
  expect(near(one.energy, many.energy), "energy is tick-rate independent");
  expect(near(one.curiosity, many.curiosity),
         "curiosity is tick-rate independent");
  expect(near(one.social_engagement, many.social_engagement),
         "social engagement is tick-rate independent");
  expect(near(one.confidence, many.confidence),
         "confidence is tick-rate independent");
  expect(near(one.frustration, many.frustration),
         "frustration is tick-rate independent");
  expect(near(one.urgency, many.urgency),
         "urgency is tick-rate independent");

  const auto& one_expression = one_tick.expression();
  const auto& many_expression = many_ticks.expression();
  constexpr float kPresentationTolerance = 0.002F;
  expect(one_expression.mood == many_expression.mood,
         "mood is stable across tick rates");
  expect(near(one_expression.valence, many_expression.valence,
              kPresentationTolerance),
         "valence is stable across tick rates");
  expect(near(one_expression.arousal, many_expression.arousal,
              kPresentationTolerance),
         "arousal is stable across tick rates");
  expect(near(one_expression.confidence, many_expression.confidence,
              kPresentationTolerance),
         "presented confidence is stable across tick rates");
  expect(near(one_expression.attention, many_expression.attention,
              kPresentationTolerance),
         "attention is stable across tick rates");
}

void expect_restored_mood(PersistedEmotionState state, Mood expected,
                          std::string_view message) {
  EmotionModel model;
  expect(model.restore(state), "test state restores");
  settle(model);
  expect(model.expression().mood == expected, message);
}

void test_mood_vocabulary() {
  EmotionModel pleased;
  expect(pleased.apply(EmotionEvent::TaskSucceeded), "success is accepted");
  settle(pleased);
  expect(pleased.expression().mood == Mood::Pleased,
         "success presents as pleased");

  EmotionModel focused;
  Stimulus task;
  task.task_engagement = 0.9F;
  settle(focused, task);
  expect(focused.expression().mood == Mood::Focused,
         "engaged task presents as focused");

  EmotionModel curious;
  Stimulus novelty;
  novelty.novelty = 0.9F;
  settle(curious, novelty);
  expect(curious.expression().mood == Mood::Curious,
         "novelty presents as curious");

  PersistedEmotionState state;
  state.needs.energy = 0.12F;
  expect_restored_mood(state, Mood::Tired, "low energy presents as tired");

  state = {};
  state.needs.frustration = 0.82F;
  expect_restored_mood(state, Mood::Frustrated,
                       "high frustration presents as frustrated");

  state = {};
  state.needs.confidence = 0.18F;
  expect_restored_mood(state, Mood::Uncertain,
                       "low confidence presents as uncertain");
}

void test_persistence_and_restart_policy() {
  EmotionModel original;
  original.apply(EmotionEvent::TaskSucceeded);
  settle(original);
  const auto state = original.snapshot();

  EmotionModel restored;
  expect(restored.restore(state), "valid snapshot restores");
  expect(near(restored.needs().confidence, state.needs.confidence),
         "durable needs survive restart");
  expect(restored.expression().mood == state.mood,
         "presented mood survives restart");
  expect(near(restored.expression().attention, 0.0F),
         "transient attention clears on restart");
  expect(restored.apply(EmotionEvent::TaskSucceeded),
         "event cooldown clears on restart");

  auto corrupt = state;
  corrupt.version = 999;
  expect(!restored.restore(corrupt), "unknown snapshot version is rejected");
  expect(restored.expression().mood == Mood::Calm,
         "rejected snapshot resets to safe defaults");

  corrupt = state;
  corrupt.needs.energy = std::numeric_limits<float>::quiet_NaN();
  expect(!restored.restore(corrupt), "non-finite snapshot is rejected");
  expect(bounded(restored), "corrupt restore leaves bounded defaults");

  corrupt = state;
  corrupt.mood = static_cast<Mood>(255);
  expect(!restored.restore(corrupt), "out-of-range persisted mood is rejected");

  corrupt = state;
  corrupt.valence = std::numeric_limits<float>::infinity();
  expect(!restored.restore(corrupt),
         "non-finite persisted presentation is rejected");

  corrupt = state;
  corrupt.arousal = 1.01F;
  expect(!restored.restore(corrupt),
         "out-of-range persisted arousal is rejected");
}

void test_untrusted_inputs() {
  EmotionModel model;
  const auto before = model.snapshot();
  expect(!model.advance(-0.1F), "negative elapsed time is rejected");
  expect(!model.advance(std::numeric_limits<float>::infinity()),
         "non-finite elapsed time is rejected");
  Stimulus invalid;
  invalid.novelty = std::numeric_limits<float>::quiet_NaN();
  expect(!model.advance(0.1F, invalid), "non-finite stimulus is rejected");
  expect(near(model.needs().energy, before.needs.energy),
         "rejected input leaves state unchanged");

  expect(model.apply(EmotionEvent::Blocked),
         "cooldown rejection fixture event is accepted");
  expect(!model.advance(std::numeric_limits<float>::quiet_NaN()),
         "invalid elapsed time does not advance cooldowns");
  expect(!model.apply(EmotionEvent::Blocked),
         "event remains cooled down after invalid advance");
  expect(model.advance(0.25F), "valid elapsed time advances cooldowns");
  expect(model.apply(EmotionEvent::Blocked),
         "event is accepted after valid cooldown interval");

  Stimulus out_of_range;
  out_of_range.activity_load = 5.0F;
  out_of_range.task_engagement = -4.0F;
  out_of_range.novelty = 2.0F;
  expect(model.advance(1.0F, out_of_range),
         "finite stimulus is clamped and accepted");
  expect(bounded(model), "clamped stimulus leaves bounded state");
}

void test_invalid_config_is_sanitized() {
  EmotionConfig config;
  config.baseline.energy = std::numeric_limits<float>::quiet_NaN();
  config.relaxation_time_s[0] = 0.0F;
  config.relaxation_time_s[1] = -1.0F;
  config.relaxation_time_s[2] = std::numeric_limits<float>::infinity();
  config.presentation_filter_time_s =
      std::numeric_limits<float>::quiet_NaN();
  config.mood_transition_s = -1.0F;
  config.event_cooldown_s = 0.0F;
  config.positive_affect_decay_s = std::numeric_limits<float>::infinity();
  config.negative_affect_decay_s = -1.0F;

  EmotionModel model(config);
  expect(bounded(model), "sanitized config produces bounded defaults");
  expect(near(model.needs().energy, 0.82F),
         "invalid baseline is replaced with the default baseline");

  Stimulus extreme;
  extreme.activity_load = std::numeric_limits<float>::max();
  extreme.task_engagement = -std::numeric_limits<float>::max();
  extreme.social_engagement = std::numeric_limits<float>::max();
  extreme.novelty = std::numeric_limits<float>::max();
  extreme.external_urgency = std::numeric_limits<float>::max();
  expect(model.advance(std::numeric_limits<float>::max(), extreme),
         "maximum finite elapsed time and stimulus are accepted");
  expect(bounded(model), "extreme finite update remains bounded and finite");
}

}  // namespace

int main() {
  test_defaults_and_names();
  test_events_are_bounded_and_cooled_down();
  test_tick_rate_independence();
  test_mood_transition_is_not_backdated_across_a_threshold();
  test_direct_stimulus_can_occupy_a_whole_interval();
  test_candidate_dwell_restarts_after_a_boundary_crossing();
  test_mood_vocabulary();
  test_persistence_and_restart_policy();
  test_untrusted_inputs();
  test_invalid_config_is_sanitized();

  if (failures != 0) {
    std::cerr << failures << " emotion test(s) failed\n";
    return EXIT_FAILURE;
  }
  std::cout << "All emotion tests passed\n";
  return EXIT_SUCCESS;
}
