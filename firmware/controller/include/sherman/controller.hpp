#pragma once
#include "protocol.hpp"
namespace sherman {
struct Sensors {
  bool cliff_valid[2]{}, imu_valid = false, power_valid = false;
  bool charge_absent = false, driver_ok = false;
  uint16_t cliff_mm[2]{}, battery_mv = 0, soc_centi_percent = 0;
  uint32_t cliff_ms[2]{}, imu_ms = 0, power_ms = 0;
  int16_t accel_mg[3]{}, gyro_mdeg_s[3]{};
  uint32_t ticks[2]{}, invalid_transitions = 0;
};
// Values are synthetic defaults for simulation, NOT a released physical
// profile.
struct Calibration {
  bool qualified = false;
  float mm_per_tick = 0.0281f, wheelbase_mm = 55.0f;
  float kp = 0.008f, ki = 0.015f;
  uint16_t cliff_min_mm = 5, cliff_max_mm = 45, minimum_mv = 3400;
};
struct Output {
  bool enabled = false;
  float left = 0, right = 0;
};
class Controller {
public:
  explicit Controller(uint64_t session, Calibration calibration = {});
  bool receive(const Frame &, uint32_t now_ms, const Sensors &);
  void tick(uint32_t now_ms, const Sensors &);
  void transport_error(uint32_t now_ms);
  Output output() const { return output_; }
  bool armed() const { return armed_; }
  uint32_t faults() const { return faults_; }
  Frame status(uint32_t now_ms, bool watchdog_reset, uint32_t rx_errors) const;
  Frame sensor_frame(uint32_t now_ms, const Sensors &) const;
  Frame odometry(uint32_t now_ms, const Sensors &) const;

private:
  bool future(uint32_t deadline, uint32_t now) const;
  uint32_t health(uint32_t now, const Sensors &) const;
  void stop();
  void fault(uint32_t code, uint32_t now);
  bool reject(uint32_t code, uint32_t now);
  uint64_t session_;
  Calibration cal_;
  Output output_{};
  bool negotiated_ = false, armed_ = false, have_heartbeat_ = false;
  bool have_command_ = false, have_tick_ = false, self_test_ok_ = false;
  uint32_t sequence_ = 0, faults_ = 0, first_fault_ms_ = 0, rejected_ = 0;
  uint32_t heartbeat_deadline_ = 0, command_deadline_ = 0, last_tick_ = 0;
  uint32_t action_id_ = 0, last_ticks_[2]{}, stall_ms_[2]{};
  uint16_t speed_limit_ = 40, angular_limit_ = 500, accel_limit_ = 100;
  uint16_t accel_ = 100, interval_ms_ = 0;
  float requested_[2]{}, target_[2]{}, integral_[2]{}, measured_[2]{};
};
int quadrature_delta(uint8_t previous, uint8_t current);
} // namespace sherman
