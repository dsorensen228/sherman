#include "sherman/display/procedural_eyes.hpp"

#include <algorithm>
#include <chrono>
#include <cstdint>
#include <cstdlib>
#include <iomanip>
#include <iostream>
#include <numeric>
#include <vector>

int main(int argc, char** argv) {
  const int frame_count = argc > 1 ? std::atoi(argv[1]) : 500;
  if (frame_count <= 0) {
    std::cerr << "frame count must be positive\n";
    return 2;
  }

  sherman::display::FastProceduralEyeRenderer renderer;
  std::vector<std::uint8_t> output(renderer.byte_size());
  std::vector<double> samples_ms;
  samples_ms.reserve(static_cast<std::size_t>(frame_count));
  std::uint32_t checksum = 0;
  for (int index = -10; index < frame_count; ++index) {
    sherman::display::EyeAnimationInputs inputs;
    inputs.gaze_x = static_cast<float>((index + 10) % 31 - 15) / 15.0F;
    inputs.gaze_y = static_cast<float>((index + 10) % 17 - 8) / 8.0F;
    inputs.blink = ((index + 10) % 47 < 3) ? 1.0F : 0.0F;
    const auto pose = sherman::display::compose_pose(inputs);
    const auto started = std::chrono::steady_clock::now();
    renderer.render_rgb565_be(pose, output.data(), output.size());
    const auto stopped = std::chrono::steady_clock::now();
    checksum = checksum * 16777619U ^ output[static_cast<std::size_t>(index + 10) * 97U %
                                               output.size()];
    if (index >= 0) {
      samples_ms.push_back(
          std::chrono::duration<double, std::milli>(stopped - started).count());
    }
  }

  std::sort(samples_ms.begin(), samples_ms.end());
  const double total = std::accumulate(samples_ms.begin(), samples_ms.end(), 0.0);
  const double mean = total / static_cast<double>(samples_ms.size());
  const std::size_t p95_index = std::min(
      samples_ms.size() - 1,
      static_cast<std::size_t>(static_cast<double>(samples_ms.size()) * 0.95));
  std::cout << std::fixed << std::setprecision(3)
            << "frames=" << samples_ms.size() << '\n'
            << "mean_ms=" << mean << '\n'
            << "p95_ms=" << samples_ms[p95_index] << '\n'
            << "max_ms=" << samples_ms.back() << '\n'
            << "mean_fps=" << 1000.0 / mean << '\n'
            << "checksum=" << checksum << '\n';
  return 0;
}
