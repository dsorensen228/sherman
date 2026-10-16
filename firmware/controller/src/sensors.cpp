#include "sherman/sensors.hpp"
#include <algorithm>
namespace sherman {
namespace {
#include "cliff_defaults.inc"
uint16_t be16(const uint8_t *p) { return uint16_t(uint16_t(p[0]) << 8 | p[1]); }
int32_t le_signed(const uint8_t *p) {
  const uint32_t value = uint32_t(p[1]) << 8 | p[0];
  return value < 32768 ? int32_t(value) : int32_t(value) - 65536;
}
} // namespace
bool SensorDriver::write8(uint8_t a, uint16_t r, unsigned w, uint8_t v) {
  return bus_.write(a, r, w, &v, 1);
}
bool SensorDriver::wait_register(uint8_t a, uint16_t r, uint8_t mask,
                                 uint8_t expected) {
  for (unsigned i = 0; i < 100; ++i) {
    uint8_t value = 0;
    if (!bus_.read(a, r, 2, &value, 1))
      return false;
    if ((value & mask) == expected)
      return true;
    bus_.wait_ms(1);
  }
  return false;
}
bool SensorDriver::cliff_init(uint8_t a) {
  uint8_t id[2];
  if (!bus_.read(a, 0x010f, 2, id, 2) || be16(id) != 0xebaa ||
      !wait_register(a, 0x00e5, 0xff, 3))
    return false;
  const uint8_t io[] = {0, 1, 1};
  if (!bus_.write(a, 0x2d, 2, io, sizeof(io)))
    return false;
  for (size_t offset = 0; offset < sizeof(kCliffDefaults); offset += 16) {
    if (!bus_.write(a, uint16_t(0x30 + offset), 2, kCliffDefaults + offset,
                    std::min(size_t(16), sizeof(kCliffDefaults) - offset)))
      return false;
  }
  if (!write8(a, 0x87, 2, 0x40) || !wait_register(a, 0x31, 1, 0) ||
      !write8(a, 0x86, 2, 1) || !write8(a, 0x87, 2, 0x80) ||
      !write8(a, 8, 2, 9) || !write8(a, 0x0b, 2, 0))
    return false;
  const uint8_t vhv[] = {5, 0};
  if (!bus_.write(a, 0x24, 2, vhv, 2))
    return false;
  uint8_t frequency[2];
  if (!bus_.read(a, 6, 2, frequency, 2) || !be16(frequency))
    return false;
  // 20 ms continuous timing budget, ULD integer timing calculation.
  const uint32_t macro =
      uint32_t((uint64_t(2304) * (0x40000000U / be16(frequency))) >> 6);
  const uint8_t zero[4]{};
  if (!bus_.write(a, 0x6c, 2, zero, 4))
    return false;
  for (unsigned i = 0; i < 2; ++i) {
    const uint32_t divisor =
        uint32_t((uint64_t(macro) * (i == 0 ? 16U : 12U)) >> 6);
    if (!divisor)
      return false;
    uint32_t timeout = ((17500U << 12) + (divisor >> 1)) / divisor;
    if (!timeout)
      return false;
    --timeout;
    uint8_t exponent = 0;
    while (timeout > 255 && exponent < 31) {
      timeout >>= 1;
      ++exponent;
    }
    const uint8_t data[] = {exponent, uint8_t(timeout)};
    if (!bus_.write(a, i == 0 ? 0x5e : 0x61, 2, data, 2))
      return false;
  }
  return write8(a, 0x86, 2, 1) && write8(a, 0x87, 2, 0x21);
}
void SensorDriver::initialize() {
  cliff_ok_[0] = cliff_ok_[1] = imu_ok_ = power_ok_ = false;
  bus_.xshut(0, false);
  bus_.xshut(1, false);
  bus_.wait_ms(2);
  for (unsigned i = 0; i < 2; ++i) {
    bus_.xshut(i, true);
    bus_.wait_ms(5);
    const uint8_t a = uint8_t(0x2a + i);
    if (!write8(0x29, 1, 2, a) || !cliff_init(a)) {
      // Do not leave a failed device alive at a conflicting default address.
      bus_.xshut(i, false);
    } else
      cliff_ok_[i] = true;
  }
  uint8_t id = 0;
  imu_ok_ = bus_.read(0x6b, 0x0f, 1, &id, 1) && id == 0x6c &&
            write8(0x6b, 0x12, 1, 0x44) && // BDU and register auto-increment
            write8(0x6b, 0x10, 1, 0x40) && // 104 Hz, +/-2 g
            write8(0x6b, 0x11, 1, 0x40);   // 104 Hz, +/-250 dps
  uint8_t version[2];
  power_ok_ =
      bus_.read(0x36, 8, 1, version, 2) && (be16(version) & 0xfff0) == 0x0010;
}
void SensorDriver::poll(Sensors &out) {
  for (unsigned i = 0; i < 2; ++i) {
    if (!cliff_ok_[i]) {
      out.cliff_valid[i] = false;
      continue;
    }
    const uint8_t a = uint8_t(0x2a + i);
    uint8_t ready = 1;
    if (!bus_.read(a, 0x31, 2, &ready, 1)) {
      out.cliff_valid[i] = false;
      continue;
    }
    if (ready & 1)
      continue; // no fresh sample, retain the old timestamp
    uint8_t data[15]{};
    const bool read = bus_.read(a, 0x89, 2, data, sizeof(data));
    const bool cleared = write8(a, 0x86, 2, 1);
    out.cliff_valid[i] =
        read && cleared && (data[0] & 0x1f) == 9 && data[3] != 0;
    if (out.cliff_valid[i]) {
      out.cliff_mm[i] = be16(data + 13);
      out.cliff_ms[i] = bus_.now_ms();
    }
  }
  if (!imu_ok_)
    out.imu_valid = false;
  else {
    uint8_t status = 0;
    if (!bus_.read(0x6b, 0x1e, 1, &status, 1))
      out.imu_valid = false;
    else if ((status & 3) == 3) {
      uint8_t data[12];
      out.imu_valid = bus_.read(0x6b, 0x22, 1, data, sizeof(data));
      if (out.imu_valid) {
        for (unsigned i = 0; i < 3; ++i) {
          out.accel_mg[i] = int16_t(le_signed(data + 6 + 2 * i) * 61 / 1000);
          const auto gyro = le_signed(data + 2 * i) * 875 / 100;
          // Saturation is explicitly invalid, never wrap a large angular rate.
          if (gyro < -32768 || gyro > 32767)
            out.imu_valid = false;
          out.gyro_mdeg_s[i] =
              int16_t(std::clamp<int32_t>(gyro, -32768, 32767));
        }
        if (out.imu_valid)
          out.imu_ms = bus_.now_ms();
      }
    }
  }
  if (!power_ok_)
    out.power_valid = false;
  else if (bus_.now_ms() - power_poll_ms_ >= 100) {
    power_poll_ms_ = bus_.now_ms();
    uint8_t data[4];
    out.power_valid = bus_.read(0x36, 2, 1, data, sizeof(data));
    if (out.power_valid) {
      out.battery_mv = uint16_t(uint32_t(be16(data)) * 5 / 64);
      out.soc_centi_percent = uint16_t(uint32_t(be16(data + 2)) * 100 / 256);
      out.power_valid = out.soc_centi_percent <= 10000 &&
                        out.battery_mv >= 2500 && out.battery_mv <= 4500;
      if (out.power_valid)
        out.power_ms = bus_.now_ms();
    }
  }
}
} // namespace sherman
