#include "sherman/display/procedural_eyes_c.h"
#include "sherman/display/procedural_eyes.hpp"

#include <array>
#include <cassert>
#include <cstdint>
#include <iostream>
#include <vector>

int main() {
  sherman_eye_renderer* renderer = sherman_eye_renderer_create();
  assert(renderer != nullptr);
  assert(sherman_eye_renderer_width(renderer) == 320);
  assert(sherman_eye_renderer_height(renderer) == 170);
  assert(sherman_eye_renderer_byte_size(renderer) == 320U * 170U * 2U);

  std::vector<std::uint8_t> output(sherman_eye_renderer_byte_size(renderer));
  const sherman_eye_inputs inputs = {
      SHERMAN_EYE_CURIOUS, 0.5F, -0.25F, 0.2F, 0.8F, 0.7F};
  assert(sherman_eye_renderer_render_rgb565_be(
             renderer, &inputs, output.data(), output.size()) == 0);
  assert(output[0] == 0 && output[1] == 0);

  const auto pose = sherman::display::compose_pose(
      {sherman::display::EyeExpression::kCurious,
       0.5F, -0.25F, 0.2F, 0.8F, 0.7F});
  std::vector<std::uint8_t> pose_output(output.size());
  assert(sherman_eye_renderer_render_pose_rgb565_be(
             renderer, pose.data(), pose.size(), pose_output.data(),
             pose_output.size()) == 0);
  assert(output == pose_output);
  assert(sherman_eye_renderer_render_pose_rgb565_be(
             renderer, pose.data(), pose.size() - 1, pose_output.data(),
             pose_output.size()) == 1);

  sherman_eye_inputs invalid = inputs;
  invalid.expression = 99;
  assert(sherman_eye_renderer_render_rgb565_be(
             renderer, &invalid, output.data(), output.size()) == 2);
  assert(sherman_eye_renderer_render_rgb565_be(
             renderer, &inputs, output.data(), 4) == 1);
  sherman_eye_renderer_destroy(renderer);
  sherman_eye_renderer_destroy(nullptr);
  std::cout << "procedural_eyes_c_test: all checks passed\n";
  return 0;
}
