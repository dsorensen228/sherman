#include "sherman/controller.hpp"
#include <iomanip>
#include <iostream>
#include <string>
using namespace sherman;
int main(int argc, char **) {
  if (argc > 1) {
    Controller c(123);
    Sensors s{};
    s.cliff_valid[0] = s.cliff_valid[1] = s.imu_valid = s.power_valid = true;
    s.cliff_ms[0] = 90;
    s.cliff_ms[1] = 91;
    s.imu_ms = 92;
    s.power_ms = 93;
    s.cliff_mm[0] = 20;
    s.cliff_mm[1] = 21;
    s.battery_mv = 3800;
    s.accel_mg[2] = 1000;
    s.gyro_mdeg_s[0] = -120;
    s.soc_centi_percent = 5000;
    s.charge_absent = true;
    s.driver_ok = true;
    s.ticks[0] = 0xffffffffU;
    s.ticks[1] = 1234;
    for (const auto &f :
         {c.status(100, true, 7), c.sensor_frame(100, s), c.odometry(100, s)}) {
      uint8_t data[kFrameMax];
      const size_t size = encode(f, data);
      for (size_t i = 0; i < size; ++i)
        std::cout << std::hex << std::setw(2) << std::setfill('0')
                  << unsigned(data[i]);
      std::cout << '\n';
    }
    return 0;
  }
  std::string text;
  Parser parser;
  Frame frame{};
  while (std::cin >> text) {
    bool received = false;
    if (text.size() > 2 * kFrameMax || text.size() % 2)
      return 2;
    for (size_t i = 0; i < text.size(); i += 2) {
      const auto byte = std::stoul(text.substr(i, 2), nullptr, 16);
      received = parser.feed(uint8_t(byte), 0, frame) || received;
    }
    if (!received || frame.size != payload_size(frame.type))
      return 3;
    uint8_t data[kFrameMax];
    const size_t size = encode(frame, data);
    for (size_t i = 0; i < size; ++i)
      std::cout << std::hex << std::setw(2) << std::setfill('0')
                << unsigned(data[i]);
    std::cout << '\n';
  }
}
