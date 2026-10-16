#include "sherman/display/procedural_eyes.hpp"

#include <algorithm>
#include <array>
#include <cassert>
#include <cmath>
#include <cstdint>
#include <iostream>
#include <limits>
#include <stdexcept>
#include <vector>

namespace {

using sherman::display::EyeAnimationInputs;
using sherman::display::EyeExpression;
using sherman::display::FastProceduralEyeRenderer;
using sherman::display::ProceduralFacePose;

std::size_t lit_pixels(const std::vector<std::uint8_t>& frame) {
  std::size_t count = 0;
  for (std::size_t index = 0; index < frame.size(); index += 2) {
    if (frame[index] != 0 || frame[index + 1] != 0) {
      ++count;
    }
  }
  return count;
}

double centroid_x(const std::vector<std::uint8_t>& frame,
                  std::size_t width) {
  double total = 0.0;
  std::size_t count = 0;
  for (std::size_t index = 0; index < frame.size() / 2; ++index) {
    if (frame[index * 2] != 0 || frame[index * 2 + 1] != 0) {
      total += static_cast<double>(index % width);
      ++count;
    }
  }
  assert(count > 0);
  return total / static_cast<double>(count);
}

std::uint64_t fnv1a(const std::vector<std::uint8_t>& frame) {
  std::uint64_t hash = 1469598103934665603ULL;
  for (const std::uint8_t byte : frame) {
    hash ^= byte;
    hash *= 1099511628211ULL;
  }
  return hash;
}

bool lit_outside_region(const std::vector<std::uint8_t>& frame,
                        std::size_t width,
                        std::size_t x,
                        std::size_t y,
                        std::size_t region_width,
                        std::size_t region_height) {
  for (std::size_t pixel = 0; pixel < frame.size() / 2; ++pixel) {
    if (frame[pixel * 2] == 0 && frame[pixel * 2 + 1] == 0) {
      continue;
    }
    const std::size_t pixel_x = pixel % width;
    const std::size_t pixel_y = pixel / width;
    if (pixel_x < x || pixel_x >= x + region_width || pixel_y < y ||
        pixel_y >= y + region_height) {
      return true;
    }
  }
  return false;
}

void test_pose_contract() {
  const ProceduralFacePose pose = sherman::display::default_procedural_face_pose();
  static_assert(std::tuple_size<ProceduralFacePose>::value == 43);
  assert(pose[2] == 1.0F);
  assert(pose[3] == 1.0F);
  assert(pose[7] == 1.0F);
  assert(pose[26] == 1.0F);

  const ProceduralFacePose target =
      sherman::display::expression_pose(EyeExpression::kTired);
  assert(sherman::display::interpolate_pose(pose, target, -1.0F) == pose);
  assert(sherman::display::interpolate_pose(pose, target, 2.0F) == target);
}

void test_frame_contract_and_expressions() {
  FastProceduralEyeRenderer renderer;
  const std::array<EyeExpression, 8> expressions = {
      EyeExpression::kCalm,       EyeExpression::kCurious,
      EyeExpression::kFocused,    EyeExpression::kPleased,
      EyeExpression::kUncertain,  EyeExpression::kFrustrated,
      EyeExpression::kTired,      EyeExpression::kSurprised,
  };
  std::array<std::uint64_t, 8> hashes{};
  for (std::size_t index = 0; index < expressions.size(); ++index) {
    const auto frame = renderer.render_rgb565_be(
        sherman::display::expression_pose(expressions[index]));
    assert(frame.size() == 320U * 170U * 2U);
    assert(lit_pixels(frame) > 100);
    assert(std::find(frame.begin(), frame.end(), 0xB3U) != frame.end());
    hashes[index] = fnv1a(frame);
    for (std::size_t prior = 0; prior < index; ++prior) {
      assert(hashes[index] != hashes[prior]);
    }
  }
}

void test_animation_inputs() {
  FastProceduralEyeRenderer renderer;
  EyeAnimationInputs left_inputs;
  left_inputs.gaze_x = -1.0F;
  EyeAnimationInputs right_inputs;
  right_inputs.gaze_x = 1.0F;
  const auto left = renderer.render_rgb565_be(
      sherman::display::compose_pose(left_inputs));
  const auto right = renderer.render_rgb565_be(
      sherman::display::compose_pose(right_inputs));
  assert(centroid_x(right, 320) - centroid_x(left, 320) > 25.0);

  EyeAnimationInputs closed_inputs;
  closed_inputs.blink = 1.0F;
  const auto open = renderer.render_rgb565_be(
      sherman::display::compose_pose(EyeAnimationInputs{}));
  const auto closed = renderer.render_rgb565_be(
      sherman::display::compose_pose(closed_inputs));
  assert(lit_pixels(closed) > 100);
  assert(lit_pixels(closed) < lit_pixels(open) / 8);

  EyeAnimationInputs invalid;
  invalid.gaze_x = std::numeric_limits<float>::infinity();
  invalid.blink = std::numeric_limits<float>::quiet_NaN();
  assert(lit_pixels(renderer.render_rgb565_be(
             sherman::display::compose_pose(invalid))) > 100);
}

void test_buffer_validation() {
  FastProceduralEyeRenderer renderer;
  std::array<std::uint8_t, 16> small{};
  bool rejected = false;
  try {
    renderer.render_rgb565_be(
        sherman::display::default_procedural_face_pose(), small.data(), small.size());
  } catch (const std::invalid_argument&) {
    rejected = true;
  }
  assert(rejected);
}

void test_dimension_byte_size_validation() {
  bool rejected = false;
  try {
    FastProceduralEyeRenderer invalid(0, 170);
  } catch (const std::invalid_argument&) {
    rejected = true;
  }
  assert(rejected);

  const std::size_t maximum_pixels =
      std::numeric_limits<std::size_t>::max() / 2U;
  const FastProceduralEyeRenderer largest_representable(maximum_pixels, 1);
  assert(largest_representable.byte_size() == maximum_pixels * 2U);

  rejected = false;
  try {
    FastProceduralEyeRenderer overflow(maximum_pixels + 1U, 1);
  } catch (const std::invalid_argument&) {
    rejected = true;
  }
  assert(rejected);

  rejected = false;
  try {
    FastProceduralEyeRenderer overflow(maximum_pixels / 2U + 1U, 2);
  } catch (const std::invalid_argument&) {
    rejected = true;
  }
  assert(rejected);
}

void test_bounded_update_region() {
  FastProceduralEyeRenderer renderer;
  const std::array<EyeExpression, 8> expressions = {
      EyeExpression::kCalm,       EyeExpression::kCurious,
      EyeExpression::kFocused,    EyeExpression::kPleased,
      EyeExpression::kUncertain,  EyeExpression::kFrustrated,
      EyeExpression::kTired,      EyeExpression::kSurprised,
  };
  for (const EyeExpression expression : expressions) {
    for (const float gaze_x : {-1.0F, 0.0F, 1.0F}) {
      for (const float gaze_y : {-1.0F, 0.0F, 1.0F}) {
        for (const float attention : {0.0F, 1.0F}) {
          for (const float arousal : {0.0F, 1.0F}) {
            EyeAnimationInputs inputs;
            inputs.expression = expression;
            inputs.gaze_x = gaze_x;
            inputs.gaze_y = gaze_y;
            inputs.attention = attention;
            inputs.arousal = arousal;
            const auto frame = renderer.render_rgb565_be(
                sherman::display::compose_pose(inputs));
            assert(!lit_outside_region(frame, 320, 28, 4, 264, 162));
          }
        }
      }
    }
  }
}

}  // namespace

int main() {
  test_pose_contract();
  test_frame_contract_and_expressions();
  test_animation_inputs();
  test_buffer_validation();
  test_dimension_byte_size_validation();
  test_bounded_update_region();
  std::cout << "procedural_eyes_cpp_test: all checks passed\n";
  return 0;
}
