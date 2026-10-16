#pragma once

#include <array>
#include <cstddef>
#include <cstdint>
#include <vector>

namespace sherman::display {

constexpr std::size_t kProceduralFaceParameterCount = 43;
constexpr std::uint16_t kShermanPurpleRgb565 = 0xB33F;

using ProceduralFacePose = std::array<float, kProceduralFaceParameterCount>;

enum class EyeExpression {
  kCalm,
  kCurious,
  kFocused,
  kPleased,
  kUncertain,
  kFrustrated,
  kTired,
  kSurprised,
};

struct EyeAnimationInputs {
  EyeExpression expression = EyeExpression::kCalm;
  float gaze_x = 0.0F;
  float gaze_y = 0.0F;
  float blink = 0.0F;
  float attention = 0.5F;
  float arousal = 0.5F;
};

ProceduralFacePose default_procedural_face_pose() noexcept;
ProceduralFacePose expression_pose(EyeExpression expression) noexcept;
ProceduralFacePose compose_pose(const EyeAnimationInputs& inputs,
                                std::size_t width = 320,
                                std::size_t height = 170) noexcept;
ProceduralFacePose interpolate_pose(const ProceduralFacePose& from,
                                    const ProceduralFacePose& to,
                                    float amount) noexcept;

class FastProceduralEyeRenderer {
 public:
  FastProceduralEyeRenderer(std::size_t width = 320,
                            std::size_t height = 170,
                            std::uint16_t eye_color = kShermanPurpleRgb565,
                            std::uint16_t background_color = 0x0000);

  std::size_t width() const noexcept { return width_; }
  std::size_t height() const noexcept { return height_; }
  std::size_t byte_size() const noexcept { return byte_size_; }

  // Writes row-major, big-endian RGB565 ready for an ST7789 RAM write.
  void render_rgb565_be(const ProceduralFacePose& pose,
                        std::uint8_t* output,
                        std::size_t output_capacity) const;
  std::vector<std::uint8_t> render_rgb565_be(
      const ProceduralFacePose& pose) const;

 private:
  std::size_t width_;
  std::size_t height_;
  std::size_t byte_size_;
  std::uint16_t eye_color_;
  std::uint16_t background_color_;
};

}  // namespace sherman::display
