#include "sherman/display/procedural_eyes.hpp"

#include <algorithm>
#include <cmath>
#include <limits>
#include <stdexcept>

namespace sherman::display {
namespace {

constexpr float kDesignWidth = 128.0F;
constexpr float kDesignHeight = 64.0F;
constexpr float kPi = 3.14159265358979323846F;
constexpr float kCenterXFactor = 0.55F;
constexpr float kCenterYFactor = 0.25F;

constexpr std::size_t kFaceCenterX = 0;
constexpr std::size_t kFaceCenterY = 1;
constexpr std::size_t kFaceScaleX = 2;
constexpr std::size_t kFaceScaleY = 3;
constexpr std::size_t kFaceAngle = 4;
constexpr std::size_t kLeftEye = 5;
constexpr std::size_t kRightEye = 24;

std::size_t checked_frame_byte_size(std::size_t width,
                                    std::size_t height) {
  if (width == 0 || height == 0) {
    throw std::invalid_argument("invalid procedural-eye framebuffer dimensions");
  }
  constexpr std::size_t kBytesPerPixel = 2;
  const std::size_t maximum_pixels =
      std::numeric_limits<std::size_t>::max() / kBytesPerPixel;
  if (width > maximum_pixels / height) {
    throw std::invalid_argument("procedural-eye framebuffer byte size overflows");
  }
  return width * height * kBytesPerPixel;
}

constexpr std::size_t kEyeCenterX = 0;
constexpr std::size_t kEyeCenterY = 1;
constexpr std::size_t kEyeScaleX = 2;
constexpr std::size_t kEyeScaleY = 3;
constexpr std::size_t kEyeAngle = 4;
constexpr std::size_t kLowerInnerRadiusX = 5;
constexpr std::size_t kLowerInnerRadiusY = 6;
constexpr std::size_t kLowerOuterRadiusX = 7;
constexpr std::size_t kLowerOuterRadiusY = 8;
constexpr std::size_t kUpperInnerRadiusX = 9;
constexpr std::size_t kUpperInnerRadiusY = 10;
constexpr std::size_t kUpperOuterRadiusX = 11;
constexpr std::size_t kUpperOuterRadiusY = 12;
constexpr std::size_t kUpperLidY = 13;
constexpr std::size_t kUpperLidAngle = 14;
constexpr std::size_t kUpperLidBend = 15;
constexpr std::size_t kLowerLidY = 16;
constexpr std::size_t kLowerLidAngle = 17;
constexpr std::size_t kLowerLidBend = 18;

float finite_or(float value, float fallback) noexcept {
  return std::isfinite(value) ? value : fallback;
}

float bounded(float value, float minimum, float maximum, float fallback) noexcept {
  return std::clamp(finite_or(value, fallback), minimum, maximum);
}

float positive_scale(float value) noexcept {
  return std::max(0.002F, std::abs(finite_or(value, 1.0F)));
}

float radians(float degrees) noexcept {
  return degrees * kPi / 180.0F;
}

struct AffineTransform {
  float xx;
  float xy;
  float x0;
  float yx;
  float yy;
  float y0;
};

AffineTransform inverse_transform(float center_x,
                                  float center_y,
                                  float scale_x,
                                  float scale_y,
                                  float angle_degrees) noexcept {
  const float angle = radians(finite_or(angle_degrees, 0.0F));
  const float cosine = std::cos(angle);
  const float sine = std::sin(angle);
  const float inverse_x = 1.0F / positive_scale(scale_x);
  const float inverse_y = 1.0F / positive_scale(scale_y);
  const float xx = cosine * inverse_x;
  const float xy = sine * inverse_x;
  const float yx = -sine * inverse_y;
  const float yy = cosine * inverse_y;
  return {xx, xy, -xx * center_x - xy * center_y,
          yx, yy, -yx * center_x - yy * center_y};
}

AffineTransform combine(const AffineTransform& outer,
                        const AffineTransform& inner) noexcept {
  // Result applies outer first, then inner.
  return {
      inner.xx * outer.xx + inner.xy * outer.yx,
      inner.xx * outer.xy + inner.xy * outer.yy,
      inner.xx * outer.x0 + inner.xy * outer.y0 + inner.x0,
      inner.yx * outer.xx + inner.yy * outer.yx,
      inner.yx * outer.xy + inner.yy * outer.yy,
      inner.yx * outer.x0 + inner.yy * outer.y0 + inner.y0,
  };
}

struct CornerRadii {
  float x;
  float y;
};

struct PreparedEye {
  AffineTransform screen_to_eye;
  float half_width;
  float half_height;
  float corner_radius;
  CornerRadii upper_left;
  CornerRadii upper_right;
  CornerRadii lower_left;
  CornerRadii lower_right;
  float upper_lid_base;
  float upper_lid_slope;
  float upper_lid_curve;
  float lower_lid_base;
  float lower_lid_slope;
  float lower_lid_curve;
};

CornerRadii radii(const ProceduralFacePose& pose,
                  std::size_t eye,
                  std::size_t x_index,
                  std::size_t y_index) noexcept {
  return {bounded(pose[eye + x_index], 0.0F, 1.5F, 0.5F),
          bounded(pose[eye + y_index], 0.0F, 1.5F, 0.5F)};
}

PreparedEye prepare_eye(const ProceduralFacePose& pose,
                        std::size_t eye,
                        bool is_left,
                        std::size_t width,
                        std::size_t height,
                        const AffineTransform& screen_to_face) noexcept {
  const float eye_width = static_cast<float>(width) * 28.0F / kDesignWidth;
  const float eye_height = static_cast<float>(height) * 40.0F / kDesignHeight;
  const float half_width = eye_width * 0.5F;
  const float half_height = eye_height * 0.5F;
  const float eye_offset = static_cast<float>(width / 5U) * (is_left ? -1.0F : 1.0F);
  const float center_x = eye_offset + finite_or(pose[eye + kEyeCenterX], 0.0F) *
                                          kCenterXFactor;
  const float center_y = finite_or(pose[eye + kEyeCenterY], 0.0F) * kCenterYFactor;
  const AffineTransform face_to_eye = inverse_transform(
      center_x, center_y, pose[eye + kEyeScaleX], pose[eye + kEyeScaleY],
      pose[eye + kEyeAngle]);

  const CornerRadii upper_inner =
      radii(pose, eye, kUpperInnerRadiusX, kUpperInnerRadiusY);
  const CornerRadii upper_outer =
      radii(pose, eye, kUpperOuterRadiusX, kUpperOuterRadiusY);
  const CornerRadii lower_inner =
      radii(pose, eye, kLowerInnerRadiusX, kLowerInnerRadiusY);
  const CornerRadii lower_outer =
      radii(pose, eye, kLowerOuterRadiusX, kLowerOuterRadiusY);

  const float upper_y = bounded(pose[eye + kUpperLidY], 0.0F, 0.98F, 0.0F);
  const float lower_y = bounded(pose[eye + kLowerLidY], 0.0F, 0.98F, 0.0F);
  const float upper_bend = bounded(pose[eye + kUpperLidBend], -1.0F, 1.0F, 0.0F);
  const float lower_bend = bounded(pose[eye + kLowerLidBend], -1.0F, 1.0F, 0.0F);

  return {
      combine(screen_to_face, face_to_eye),
      half_width,
      half_height,
      static_cast<float>(width) / 20.0F + static_cast<float>(height) / 10.0F,
      is_left ? upper_outer : upper_inner,
      is_left ? upper_inner : upper_outer,
      is_left ? lower_outer : lower_inner,
      is_left ? lower_inner : lower_outer,
      -half_height + upper_y * eye_height,
      -std::tan(radians(bounded(pose[eye + kUpperLidAngle], -60.0F, 60.0F, 0.0F))),
      upper_bend * (1.0F - upper_y) * eye_height,
      half_height - lower_y * eye_height,
      -std::tan(radians(bounded(pose[eye + kLowerLidAngle], -60.0F, 60.0F, 0.0F))),
      lower_bend * (1.0F - lower_y) * eye_height,
  };
}

bool inside_ellipse(float x,
                    float y,
                    float center_x,
                    float center_y,
                    float radius_x,
                    float radius_y) noexcept {
  if (radius_x <= 0.01F || radius_y <= 0.01F) {
    return true;
  }
  const float dx = (x - center_x) / radius_x;
  const float dy = (y - center_y) / radius_y;
  return dx * dx + dy * dy <= 1.0F;
}

bool inside_eye_shape(const PreparedEye& eye, float x, float y) noexcept {
  if (x < -eye.half_width || x > eye.half_width ||
      y < -eye.half_height || y > eye.half_height) {
    return false;
  }

  const auto outside_corner = [&](CornerRadii radii_value,
                                  bool right,
                                  bool lower) {
    const float radius_x = radii_value.x * eye.corner_radius;
    const float radius_y = radii_value.y * eye.corner_radius;
    const float center_x = right ? eye.half_width - radius_x
                                 : -eye.half_width + radius_x;
    const float center_y = lower ? eye.half_height - radius_y
                                 : -eye.half_height + radius_y;
    const bool in_corner_region =
        (right ? x > center_x : x < center_x) &&
        (lower ? y > center_y : y < center_y);
    return in_corner_region &&
           !inside_ellipse(x, y, center_x, center_y, radius_x, radius_y);
  };

  if (outside_corner(eye.upper_left, false, false) ||
      outside_corner(eye.upper_right, true, false) ||
      outside_corner(eye.lower_left, false, true) ||
      outside_corner(eye.lower_right, true, true)) {
    return false;
  }

  const float normalized_x = std::clamp(x / eye.half_width, -1.0F, 1.0F);
  const float curve_weight = 1.0F - normalized_x * normalized_x;
  const float upper_boundary = eye.upper_lid_base + eye.upper_lid_slope * x +
                               eye.upper_lid_curve * curve_weight;
  const float lower_boundary = eye.lower_lid_base + eye.lower_lid_slope * x -
                               eye.lower_lid_curve * curve_weight;
  return y >= upper_boundary && y <= lower_boundary;
}

void set_eye(ProceduralFacePose& pose,
             std::size_t eye,
             std::size_t field,
             float value) noexcept {
  pose[eye + field] = value;
}

}  // namespace

ProceduralFacePose default_procedural_face_pose() noexcept {
  constexpr std::array<float, 19> eye = {
      0.0F, 0.0F, 1.0F, 1.0F, 0.0F,
      0.5F, 0.5F, 0.5F, 0.5F,
      0.5F, 0.5F, 0.5F, 0.5F,
      0.0F, 0.0F, 0.0F,
      0.0F, 0.0F, 0.0F,
  };
  ProceduralFacePose pose{};
  pose[kFaceScaleX] = 1.0F;
  pose[kFaceScaleY] = 1.0F;
  std::copy(eye.begin(), eye.end(), pose.begin() + kLeftEye);
  std::copy(eye.begin(), eye.end(), pose.begin() + kRightEye);
  return pose;
}

ProceduralFacePose expression_pose(EyeExpression expression) noexcept {
  ProceduralFacePose pose = default_procedural_face_pose();
  set_eye(pose, kLeftEye, kEyeScaleX, 0.8F);
  set_eye(pose, kLeftEye, kEyeScaleY, 0.8F);
  set_eye(pose, kRightEye, kEyeScaleX, 0.8F);
  set_eye(pose, kRightEye, kEyeScaleY, 0.8F);

  switch (expression) {
    case EyeExpression::kCalm:
      break;
    case EyeExpression::kCurious:
      set_eye(pose, kLeftEye, kEyeScaleX, 0.76F);
      set_eye(pose, kLeftEye, kEyeScaleY, 0.82F);
      set_eye(pose, kRightEye, kEyeScaleX, 0.92F);
      set_eye(pose, kRightEye, kEyeScaleY, 0.98F);
      set_eye(pose, kLeftEye, kLowerLidY, 0.12F);
      set_eye(pose, kLeftEye, kLowerLidBend, 0.15F);
      set_eye(pose, kRightEye, kUpperLidAngle, -10.0F);
      set_eye(pose, kRightEye, kUpperLidY, 0.12F);
      break;
    case EyeExpression::kFocused:
      set_eye(pose, kLeftEye, kUpperLidY, 0.18F);
      set_eye(pose, kLeftEye, kUpperLidAngle, -16.0F);
      set_eye(pose, kRightEye, kUpperLidY, 0.18F);
      set_eye(pose, kRightEye, kUpperLidAngle, 16.0F);
      set_eye(pose, kLeftEye, kEyeScaleY, 0.76F);
      set_eye(pose, kRightEye, kEyeScaleY, 0.76F);
      break;
    case EyeExpression::kPleased:
      for (const std::size_t eye : {kLeftEye, kRightEye}) {
        set_eye(pose, eye, kUpperOuterRadiusX, 1.0F);
        set_eye(pose, eye, kUpperInnerRadiusX, 1.0F);
        set_eye(pose, eye, kLowerLidY, 0.36F);
        set_eye(pose, eye, kLowerLidBend, 0.36F);
      }
      break;
    case EyeExpression::kUncertain:
      set_eye(pose, kLeftEye, kUpperLidY, 0.34F);
      set_eye(pose, kLeftEye, kUpperLidAngle, -8.0F);
      set_eye(pose, kRightEye, kUpperLidY, 0.10F);
      set_eye(pose, kRightEye, kUpperLidAngle, 22.0F);
      set_eye(pose, kLeftEye, kLowerLidY, 0.18F);
      set_eye(pose, kRightEye, kLowerLidY, 0.18F);
      break;
    case EyeExpression::kFrustrated:
      set_eye(pose, kLeftEye, kUpperLidY, 0.30F);
      set_eye(pose, kLeftEye, kUpperLidAngle, -28.0F);
      set_eye(pose, kRightEye, kUpperLidY, 0.30F);
      set_eye(pose, kRightEye, kUpperLidAngle, 28.0F);
      set_eye(pose, kLeftEye, kLowerLidY, 0.12F);
      set_eye(pose, kRightEye, kLowerLidY, 0.12F);
      break;
    case EyeExpression::kTired:
      set_eye(pose, kLeftEye, kUpperLidY, 0.38F);
      set_eye(pose, kLeftEye, kUpperLidAngle, 5.0F);
      set_eye(pose, kRightEye, kUpperLidY, 0.38F);
      set_eye(pose, kRightEye, kUpperLidAngle, -5.0F);
      set_eye(pose, kLeftEye, kLowerLidY, 0.34F);
      set_eye(pose, kRightEye, kLowerLidY, 0.34F);
      set_eye(pose, kLeftEye, kEyeCenterY, 18.0F);
      set_eye(pose, kRightEye, kEyeCenterY, 18.0F);
      break;
    case EyeExpression::kSurprised:
      for (const std::size_t eye : {kLeftEye, kRightEye}) {
        set_eye(pose, eye, kEyeScaleX, 1.0F);
        set_eye(pose, eye, kEyeScaleY, 1.0F);
        for (const std::size_t field : {
                 kLowerInnerRadiusX, kLowerInnerRadiusY,
                 kLowerOuterRadiusX, kLowerOuterRadiusY,
                 kUpperInnerRadiusX, kUpperInnerRadiusY,
                 kUpperOuterRadiusX, kUpperOuterRadiusY}) {
          set_eye(pose, eye, field, 0.9F);
        }
      }
      break;
  }
  return pose;
}

ProceduralFacePose compose_pose(const EyeAnimationInputs& inputs,
                                std::size_t width,
                                std::size_t height) noexcept {
  ProceduralFacePose pose = expression_pose(inputs.expression);
  const float gaze_x = bounded(inputs.gaze_x, -1.0F, 1.0F, 0.0F);
  const float gaze_y = bounded(inputs.gaze_y, -1.0F, 1.0F, 0.0F);
  const float blink = bounded(inputs.blink, 0.0F, 1.0F, 0.0F);
  const float attention = bounded(inputs.attention, 0.0F, 1.0F, 0.5F);
  const float arousal = bounded(inputs.arousal, 0.0F, 1.0F, 0.5F);
  const float scale = std::min(static_cast<float>(width) / kDesignWidth,
                               static_cast<float>(height) / kDesignHeight);
  pose[kFaceCenterX] += gaze_x * (10.0F + 3.0F * attention) * scale;
  pose[kFaceCenterY] += gaze_y * (28.0F + 4.0F * attention) * scale;
  for (const std::size_t eye : {kLeftEye, kRightEye}) {
    pose[eye + kEyeScaleX] *= (0.94F + 0.12F * attention) * (1.0F + blink * 0.20F);
    pose[eye + kEyeScaleY] *=
        (0.94F + 0.12F * arousal) * std::max(0.035F, 1.0F - blink * 0.965F);
  }
  return pose;
}

ProceduralFacePose interpolate_pose(const ProceduralFacePose& from,
                                    const ProceduralFacePose& to,
                                    float amount) noexcept {
  const float t = bounded(amount, 0.0F, 1.0F, 0.0F);
  ProceduralFacePose result{};
  for (std::size_t index = 0; index < result.size(); ++index) {
    const float source = finite_or(from[index], 0.0F);
    result[index] = source + t * (finite_or(to[index], 0.0F) - source);
  }
  return result;
}

FastProceduralEyeRenderer::FastProceduralEyeRenderer(
    std::size_t width,
    std::size_t height,
    std::uint16_t eye_color,
    std::uint16_t background_color)
    : width_(width),
      height_(height),
      byte_size_(checked_frame_byte_size(width, height)),
      eye_color_(eye_color),
      background_color_(background_color) {}

void FastProceduralEyeRenderer::render_rgb565_be(
    const ProceduralFacePose& pose,
    std::uint8_t* output,
    std::size_t output_capacity) const {
  if (output == nullptr || output_capacity < byte_size()) {
    throw std::invalid_argument("RGB565 output buffer is null or too small");
  }

  const float face_center_x = static_cast<float>(width_) * 0.5F +
                              finite_or(pose[kFaceCenterX], 0.0F) * kCenterXFactor;
  const float face_center_y = static_cast<float>(height_) * 0.5F +
                              finite_or(pose[kFaceCenterY], 0.0F) * kCenterYFactor;
  const AffineTransform screen_to_face = inverse_transform(
      face_center_x, face_center_y, pose[kFaceScaleX], pose[kFaceScaleY],
      pose[kFaceAngle]);
  const PreparedEye left =
      prepare_eye(pose, kLeftEye, true, width_, height_, screen_to_face);
  const PreparedEye right =
      prepare_eye(pose, kRightEye, false, width_, height_, screen_to_face);

  const std::uint8_t eye_high = static_cast<std::uint8_t>(eye_color_ >> 8U);
  const std::uint8_t eye_low = static_cast<std::uint8_t>(eye_color_ & 0xFFU);
  const std::uint8_t background_high =
      static_cast<std::uint8_t>(background_color_ >> 8U);
  const std::uint8_t background_low =
      static_cast<std::uint8_t>(background_color_ & 0xFFU);

  std::size_t offset = 0;
  for (std::size_t y = 0; y < height_; ++y) {
    const float sample_y = static_cast<float>(y) + 0.5F;
    float left_x = left.screen_to_eye.xx * 0.5F +
                   left.screen_to_eye.xy * sample_y + left.screen_to_eye.x0;
    float left_y = left.screen_to_eye.yx * 0.5F +
                   left.screen_to_eye.yy * sample_y + left.screen_to_eye.y0;
    float right_x = right.screen_to_eye.xx * 0.5F +
                    right.screen_to_eye.xy * sample_y + right.screen_to_eye.x0;
    float right_y = right.screen_to_eye.yx * 0.5F +
                    right.screen_to_eye.yy * sample_y + right.screen_to_eye.y0;
    for (std::size_t x = 0; x < width_; ++x) {
      const bool lit = inside_eye_shape(left, left_x, left_y) ||
                       inside_eye_shape(right, right_x, right_y);
      output[offset++] = lit ? eye_high : background_high;
      output[offset++] = lit ? eye_low : background_low;
      left_x += left.screen_to_eye.xx;
      left_y += left.screen_to_eye.yx;
      right_x += right.screen_to_eye.xx;
      right_y += right.screen_to_eye.yx;
    }
  }
}

std::vector<std::uint8_t> FastProceduralEyeRenderer::render_rgb565_be(
    const ProceduralFacePose& pose) const {
  std::vector<std::uint8_t> output(byte_size());
  render_rgb565_be(pose, output.data(), output.size());
  return output;
}

}  // namespace sherman::display
