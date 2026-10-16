#include "sherman/sensors.hpp"
#include <array>
#include <cassert>
#include <cstring>
#include <iostream>
#include <map>
#include <tuple>
using namespace sherman;
struct Bus : SensorBus {
  uint32_t now = 0;
  bool live[2]{}, fail = false, wrong_id = false, ready = true;
  uint8_t address[2]{0x29, 0x29};
  bool saw_collision = false, bad_range = false, imu_ready = true;
  unsigned writes = 0;
  bool read(uint8_t a, uint16_t r, unsigned, uint8_t *data,
            size_t size) override {
    std::memset(data, 0, size);
    if (fail)
      return false;
    if (a >= 0x29 && a <= 0x2b) {
      unsigned count = 0;
      for (unsigned i = 0; i < 2; ++i)
        count += live[i] && address[i] == a;
      if (count != 1) {
        saw_collision = true;
        return false;
      }
      if (r == 0x10f) {
        data[0] = wrong_id ? 0 : 0xeb;
        data[1] = 0xaa;
      }
      if (r == 0xe5)
        data[0] = 3;
      if (r == 6) {
        data[0] = 0xb0;
        data[1] = 0x00;
      }
      if (r == 0x31)
        data[0] = ready ? 0 : 1;
      if (r == 0x89) {
        data[0] = bad_range ? 4 : 9;
        data[3] = 10;
        data[14] = 20;
      }
    } else if (a == 0x6b) {
      if (r == 0x0f)
        data[0] = 0x6c;
      if (r == 0x1e)
        data[0] = imu_ready ? 3 : 0;
      if (r == 0x22) {
        data[10] = 0x0a;
        data[11] = 0x40;
      } // ~1000 mg Z
    } else if (a == 0x36) {
      if (r == 8)
        data[1] = 0x12;
      if (r == 2) {
        data[0] = 0xbe;
        data[1] = 0x00;
        data[2] = 50;
      }
    } else
      return false;
    return true;
  }
  bool write(uint8_t a, uint16_t r, unsigned, const uint8_t *data,
             size_t) override {
    ++writes;
    if (fail)
      return false;
    if (a == 0x29 && r == 1) {
      unsigned count = 0;
      for (unsigned i = 0; i < 2; ++i)
        if (live[i] && address[i] == a) {
          ++count;
          address[i] = data[0];
        }
      if (count != 1) {
        saw_collision = true;
        return false;
      }
    }
    return true;
  }
  void xshut(unsigned i, bool released) override {
    live[i] = released;
    if (!released)
      address[i] = 0x29;
  }
  void wait_ms(uint32_t ms) override { now += ms; }
  uint32_t now_ms() override { return now; }
};
int main() {
  Bus bus;
  SensorDriver driver(bus);
  Sensors s{};
  driver.initialize();
  assert(!bus.saw_collision);
  assert(bus.address[0] == 0x2a && bus.address[1] == 0x2b);
  bus.now = 100;
  driver.poll(s);
  assert(s.cliff_valid[0] && s.cliff_valid[1] && s.cliff_mm[0] == 20 &&
         s.cliff_ms[0] == 100);
  assert(s.imu_valid && s.accel_mg[2] == 1000 && s.imu_ms == 100);
  assert(s.power_valid && s.battery_mv == 3800 && s.soc_centi_percent == 5000);
  bus.ready = bus.imu_ready = false;
  bus.now = 120;
  driver.poll(s);
  assert(s.cliff_ms[0] == 100 && s.imu_ms == 100);
  Controller c(123);
  auto frame = c.sensor_frame(151, s);
  assert((frame.payload[24] & 7) == 0);
  bus.ready = true;
  bus.bad_range = true;
  driver.poll(s);
  assert(!s.cliff_valid[0]);
  bus.fail = true;
  bus.now = 200;
  driver.poll(s);
  assert(!s.imu_valid && !s.cliff_valid[1] && !s.power_valid);
  Bus missing;
  missing.fail = true;
  SensorDriver d2(missing);
  d2.initialize();
  Sensors absent{};
  d2.poll(absent);
  assert(!missing.live[0] && !missing.live[1]);
  assert(!absent.imu_valid && !absent.cliff_valid[0]);
  Bus wrong;
  wrong.wrong_id = true;
  SensorDriver d3(wrong);
  d3.initialize();
  assert(!wrong.live[0] && !wrong.live[1]);
  Bus timeout;
  timeout.ready = false;
  SensorDriver d4(timeout);
  d4.initialize();
  assert(timeout.now <= 220);
  assert(!timeout.live[0] && !timeout.live[1]);
  std::cout << "W1 addressing, conversions, missing/wrong/stale sensors and "
               "bounded timeout: PASS\n";
}
