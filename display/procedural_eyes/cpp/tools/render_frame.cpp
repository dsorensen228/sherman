#include "sherman/display/procedural_eyes.hpp"

#include <array>
#include <cerrno>
#include <cstdlib>
#include <cstdint>
#include <fstream>
#include <iostream>
#include <memory>
#include <string>

namespace {

void usage(std::ostream& output) {
  output << "usage: procedural_eyes_render_frame [options]\n"
         << "  --expression NAME   calm|curious|focused|pleased|uncertain|"
            "frustrated|tired|surprised\n"
         << "  --gaze-x VALUE      -1 (left) to +1 (right)\n"
         << "  --gaze-y VALUE      -1 (up) to +1 (down)\n"
         << "  --blink VALUE       0 (open) to 1 (closed)\n"
         << "  --attention VALUE   0 to 1\n"
         << "  --arousal VALUE     0 to 1\n"
         << "  --output PATH       raw big-endian RGB565; '-' means stdout (default)\n";
}

bool parse_float(const char* text, float& value) {
  errno = 0;
  char* end = nullptr;
  const float parsed = std::strtof(text, &end);
  if (errno != 0 || end == text || *end != '\0') {
    return false;
  }
  value = parsed;
  return true;
}

bool parse_expression(const std::string& name,
                      sherman::display::EyeExpression& expression) {
  const std::array<std::pair<const char*, sherman::display::EyeExpression>, 8> expressions = {{
      {"calm", sherman::display::EyeExpression::kCalm},
      {"curious", sherman::display::EyeExpression::kCurious},
      {"focused", sherman::display::EyeExpression::kFocused},
      {"pleased", sherman::display::EyeExpression::kPleased},
      {"uncertain", sherman::display::EyeExpression::kUncertain},
      {"frustrated", sherman::display::EyeExpression::kFrustrated},
      {"tired", sherman::display::EyeExpression::kTired},
      {"surprised", sherman::display::EyeExpression::kSurprised},
  }};
  for (const auto& candidate : expressions) {
    if (candidate.first == name) {
      expression = candidate.second;
      return true;
    }
  }
  return false;
}

}  // namespace

int main(int argc, char** argv) {
  sherman::display::EyeAnimationInputs inputs;
  std::string output_path = "-";
  for (int index = 1; index < argc; ++index) {
    const std::string option = argv[index];
    if (option == "--help" || option == "-h") {
      usage(std::cout);
      return 0;
    }
    if (index + 1 >= argc) {
      std::cerr << "missing value for " << option << '\n';
      usage(std::cerr);
      return 2;
    }
    const char* value = argv[++index];
    if (option == "--expression") {
      if (!parse_expression(value, inputs.expression)) {
        std::cerr << "unknown expression: " << value << '\n';
        return 2;
      }
    } else if (option == "--gaze-x") {
      if (!parse_float(value, inputs.gaze_x)) return 2;
    } else if (option == "--gaze-y") {
      if (!parse_float(value, inputs.gaze_y)) return 2;
    } else if (option == "--blink") {
      if (!parse_float(value, inputs.blink)) return 2;
    } else if (option == "--attention") {
      if (!parse_float(value, inputs.attention)) return 2;
    } else if (option == "--arousal") {
      if (!parse_float(value, inputs.arousal)) return 2;
    } else if (option == "--output") {
      output_path = value;
    } else {
      std::cerr << "unknown option: " << option << '\n';
      usage(std::cerr);
      return 2;
    }
  }

  sherman::display::FastProceduralEyeRenderer renderer;
  const auto frame = renderer.render_rgb565_be(
      sherman::display::compose_pose(inputs));
  if (output_path == "-") {
    std::cout.write(reinterpret_cast<const char*>(frame.data()),
                    static_cast<std::streamsize>(frame.size()));
    return std::cout ? 0 : 1;
  }
  std::ofstream output(output_path, std::ios::binary);
  output.write(reinterpret_cast<const char*>(frame.data()),
               static_cast<std::streamsize>(frame.size()));
  return output ? 0 : 1;
}
