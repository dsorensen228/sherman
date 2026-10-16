#include "sherman/display/procedural_eyes_c.h"

#include "sherman/display/procedural_eyes.hpp"

#include <algorithm>
#include <cstdint>
#include <new>
#include <stdexcept>

struct sherman_eye_renderer {
  explicit sherman_eye_renderer(
      sherman::display::FastProceduralEyeRenderer renderer_value)
      : renderer(renderer_value) {}

  sherman::display::FastProceduralEyeRenderer renderer;
};

namespace {

bool valid_expression(std::int32_t expression) noexcept {
  return expression >= SHERMAN_EYE_CALM && expression <= SHERMAN_EYE_SURPRISED;
}

sherman::display::EyeExpression to_cpp_expression(
    std::int32_t expression) noexcept {
  return static_cast<sherman::display::EyeExpression>(
      static_cast<unsigned>(expression));
}

}  // namespace

extern "C" {

sherman_eye_renderer* sherman_eye_renderer_create(void) {
  return sherman_eye_renderer_create_custom(
      320, 170, sherman::display::kShermanPurpleRgb565, 0x0000);
}

sherman_eye_renderer* sherman_eye_renderer_create_custom(
    size_t width,
    size_t height,
    uint16_t eye_rgb565,
    uint16_t background_rgb565) {
  try {
    return new sherman_eye_renderer(sherman::display::FastProceduralEyeRenderer(
        width, height, eye_rgb565, background_rgb565));
  } catch (...) {
    return nullptr;
  }
}

void sherman_eye_renderer_destroy(sherman_eye_renderer* renderer) {
  delete renderer;
}

size_t sherman_eye_renderer_width(const sherman_eye_renderer* renderer) {
  return renderer == nullptr ? 0 : renderer->renderer.width();
}

size_t sherman_eye_renderer_height(const sherman_eye_renderer* renderer) {
  return renderer == nullptr ? 0 : renderer->renderer.height();
}

size_t sherman_eye_renderer_byte_size(const sherman_eye_renderer* renderer) {
  return renderer == nullptr ? 0 : renderer->renderer.byte_size();
}

int sherman_eye_renderer_render_rgb565_be(
    const sherman_eye_renderer* renderer,
    const sherman_eye_inputs* inputs,
    uint8_t* output,
    size_t output_capacity) {
  if (renderer == nullptr || inputs == nullptr || output == nullptr) {
    return 1;
  }
  if (!valid_expression(inputs->expression)) {
    return 2;
  }
  try {
    sherman::display::EyeAnimationInputs cpp_inputs;
    cpp_inputs.expression = to_cpp_expression(inputs->expression);
    cpp_inputs.gaze_x = inputs->gaze_x;
    cpp_inputs.gaze_y = inputs->gaze_y;
    cpp_inputs.blink = inputs->blink;
    cpp_inputs.attention = inputs->attention;
    cpp_inputs.arousal = inputs->arousal;
    const auto pose = sherman::display::compose_pose(
        cpp_inputs, renderer->renderer.width(), renderer->renderer.height());
    renderer->renderer.render_rgb565_be(pose, output, output_capacity);
    return 0;
  } catch (const std::invalid_argument&) {
    return 1;
  } catch (...) {
    return 3;
  }
}

int sherman_eye_renderer_render_pose_rgb565_be(
    const sherman_eye_renderer* renderer,
    const float* pose,
    size_t pose_count,
    uint8_t* output,
    size_t output_capacity) {
  if (renderer == nullptr || pose == nullptr || output == nullptr ||
      pose_count != sherman::display::kProceduralFaceParameterCount) {
    return 1;
  }
  try {
    sherman::display::ProceduralFacePose cpp_pose;
    std::copy_n(pose, cpp_pose.size(), cpp_pose.begin());
    renderer->renderer.render_rgb565_be(
        cpp_pose, output, output_capacity);
    return 0;
  } catch (const std::invalid_argument&) {
    return 1;
  } catch (...) {
    return 3;
  }
}

}  // extern "C"
