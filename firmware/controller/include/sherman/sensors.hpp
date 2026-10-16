#pragma once
#include "controller.hpp"
#include <cstddef>
namespace sherman {
class SensorBus {
public:
  virtual ~SensorBus() = default;
  virtual bool read(uint8_t address, uint16_t reg, unsigned reg_bytes,
                    uint8_t *data, size_t size) = 0;
  virtual bool write(uint8_t address, uint16_t reg, unsigned reg_bytes,
                     const uint8_t *data, size_t size) = 0;
  virtual void xshut(unsigned index, bool released) = 0;
  virtual void wait_ms(uint32_t ms) = 0;
  virtual uint32_t now_ms() = 0;
};
class SensorDriver {
public:
  explicit SensorDriver(SensorBus &bus) : bus_(bus) {}
  void initialize();       // called only with motor requests held low
  void poll(Sensors &out); // non-waiting acquisition; bounded I2C transaction
                           // timeouts
private:
  bool cliff_init(uint8_t address);
  bool write8(uint8_t address, uint16_t reg, unsigned width, uint8_t value);
  bool wait_register(uint8_t address, uint16_t reg, uint8_t mask,
                     uint8_t expected);
  SensorBus &bus_;
  bool cliff_ok_[2]{}, imu_ok_ = false, power_ok_ = false;
  uint32_t power_poll_ms_ = 0;
};
} // namespace sherman
