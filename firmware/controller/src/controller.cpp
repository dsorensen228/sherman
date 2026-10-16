#include "sherman/controller.hpp"
#include <algorithm>
#include <cmath>
namespace sherman {
namespace {
int16_t signed16(const uint8_t *p) {
  const auto u = uint32_t(get_le(p, 2));
  return int16_t(u < 32768 ? int32_t(u) : int32_t(u) - 65536);
}
int64_t tick_delta(uint32_t a, uint32_t b) {
  const uint32_t d = a - b;
  return d < 0x80000000U ? int64_t(d) : int64_t(d) - 0x100000000LL;
}
} // namespace
Controller::Controller(uint64_t session, Calibration cal)
    : session_(session), cal_(cal) {
  if (!std::isfinite(cal.mm_per_tick) || cal.mm_per_tick <= 0 ||
      cal.mm_per_tick > 1 || !std::isfinite(cal.wheelbase_mm) ||
      cal.wheelbase_mm < 10 || cal.wheelbase_mm > 200 ||
      !std::isfinite(cal.kp) || cal.kp < 0 || cal.kp > 1 ||
      !std::isfinite(cal.ki) || cal.ki < 0 || cal.ki > 1 ||
      cal.cliff_min_mm >= cal.cliff_max_mm || cal.cliff_max_mm > 100 ||
      cal.minimum_mv < 3000 || cal.minimum_mv > 4200)
    cal_.qualified = false;
}
bool Controller::future(uint32_t deadline, uint32_t now) const {
  const auto remaining = deadline - now;
  return remaining > 0 && remaining <= 100;
}
void Controller::stop() {
  armed_ = false;
  have_command_ = false;
  output_ = {};
  for (unsigned i = 0; i < 2; ++i) {
    requested_[i] = target_[i] = integral_[i] = 0;
    stall_ms_[i] = 0;
  }
}
void Controller::fault(uint32_t code, uint32_t now) {
  if (!faults_)
    first_fault_ms_ = now;
  faults_ |= code;
  stop();
}
bool Controller::reject(uint32_t code, uint32_t now) {
  ++rejected_;
  fault(code, now);
  return false;
}
uint32_t Controller::health(uint32_t now, const Sensors &s) const {
  uint32_t f = 0;
  if (!cal_.qualified)
    f |= UNQUALIFIED;
  if (!s.charge_absent)
    f |= CHARGING;
  if (!s.driver_ok)
    f |= DRIVER;
  for (unsigned i = 0; i < 2; ++i) {
    if (!s.cliff_valid[i] || now - s.cliff_ms[i] >= 50)
      f |= SENSOR;
    else if (s.cliff_mm[i] < cal_.cliff_min_mm ||
             s.cliff_mm[i] > cal_.cliff_max_mm)
      f |= CLIFF;
  }
  if (!s.imu_valid || now - s.imu_ms >= 50)
    f |= SENSOR;
  else if (std::abs(int(s.accel_mg[0])) > 400 ||
           std::abs(int(s.accel_mg[1])) > 400 || s.accel_mg[2] < 800 ||
           s.accel_mg[2] > 1200)
    f |= TILT;
  if (!s.power_valid || now - s.power_ms >= 500)
    f |= SENSOR;
  else if (s.battery_mv < cal_.minimum_mv || s.battery_mv > 4250)
    f |= POWER;
  return f;
}
bool Controller::receive(const Frame &f, uint32_t now, const Sensors &s) {
  tick(now, s); // expiry wins over a late refresh
  if (f.size != payload_size(f.type))
    return reject(PROTOCOL, now);
  if (f.type == STOP) {
    stop();
    have_heartbeat_ = false;
    return true;
  }
  if (f.session != session_ || !f.sequence || f.sequence <= sequence_)
    return reject(PROTOCOL, now);
  sequence_ = f.sequence; // consume even rejected commands
  const auto *p = f.payload.data();
  if (f.type == HELLO) {
    stop();
    have_heartbeat_ = false;
    negotiated_ = get_le(p, 4) == kProfile;
    if (!negotiated_)
      return reject(PROTOCOL, now);
    return true;
  }
  if (!negotiated_)
    return reject(LINK, now);
  switch (f.type) {
  case HEARTBEAT:
    if (!future(uint32_t(get_le(p, 4)), now))
      return reject(LINK, now);
    heartbeat_deadline_ = uint32_t(get_le(p, 4));
    have_heartbeat_ = true;
    return true;
  case ARM: {
    if (armed_ || faults_ || !have_heartbeat_ ||
        !future(heartbeat_deadline_, now) ||
        !future(uint32_t(get_le(p, 4)), now))
      return reject(COMMAND, now);
    const auto h = health(now, s);
    if (h)
      return reject(h, now);
    armed_ = true;
    command_deadline_ = uint32_t(get_le(p, 4));
    for (unsigned i = 0; i < 2; ++i)
      last_ticks_[i] = s.ticks[i];
    return true;
  }
  case TWIST: {
    if (!armed_ || !future(uint32_t(get_le(p, 4)), now))
      return reject(COMMAND, now);
    const int linear = signed16(p + 4), angular = signed16(p + 6);
    const auto accel = uint16_t(get_le(p + 8, 2));
    // W1 has only front cliff coverage: reject reverse/pivot trajectories.
    const float turn = float(angular) * cal_.wheelbase_mm / 2000.0f;
    const float left = float(linear) - turn, right = float(linear) + turn;
    if (linear < 0 || linear > speed_limit_ ||
        std::abs(angular) > angular_limit_ || !accel || accel > accel_limit_ ||
        left < 0 || right < 0 || left > speed_limit_ || right > speed_limit_)
      return reject(COMMAND, now);
    requested_[0] = left;
    requested_[1] = right;
    accel_ = accel;
    command_deadline_ = uint32_t(get_le(p, 4));
    action_id_ = uint32_t(get_le(p + 10, 4));
    have_command_ = true;
    return true;
  }
  case CLEAR_FAULT:
    if (armed_)
      return reject(COMMAND, now);
    if (health(now, s))
      return reject(health(now, s), now);
    faults_ = 0;
    first_fault_ms_ = 0;
    have_heartbeat_ = false;
    return true;
  case CONFIGURE_LIMITS: {
    const auto speed = get_le(p, 2), angular = get_le(p + 2, 2),
               accel = get_le(p + 4, 2);
    if (armed_ || !speed || speed > 40 || !angular || angular > 500 || !accel ||
        accel > 100)
      return reject(COMMAND, now);
    speed_limit_ = uint16_t(speed);
    angular_limit_ = uint16_t(angular);
    accel_limit_ = uint16_t(accel);
    return true;
  }
  case SELF_TEST:
    if (armed_)
      return reject(COMMAND, now);
    self_test_ok_ = health(now, s) == 0;
    return true;
  default:
    return reject(PROTOCOL, now);
  }
}
void Controller::transport_error(uint32_t now) { fault(PROTOCOL, now); }
void Controller::tick(uint32_t now, const Sensors &s) {
  if (armed_) {
    const auto h = health(now, s);
    if (h) {
      fault(h, now);
      return;
    }
    if (!have_heartbeat_ || !future(heartbeat_deadline_, now)) {
      fault(LINK, now);
      return;
    }
    if (!future(command_deadline_, now)) {
      fault(COMMAND, now);
      return;
    }
  }
  if (!have_tick_) {
    last_tick_ = now;
    have_tick_ = true;
    for (unsigned i = 0; i < 2; ++i)
      last_ticks_[i] = s.ticks[i];
    return;
  }
  const auto dt = now - last_tick_;
  if (dt < 10)
    return;
  last_tick_ = now;
  interval_ms_ = uint16_t(std::min<uint32_t>(dt, 65535U));
  if (armed_ && dt > 30) {
    fault(LOOP, now);
    return;
  }
  for (unsigned i = 0; i < 2; ++i) {
    const auto delta = tick_delta(s.ticks[i], last_ticks_[i]);
    last_ticks_[i] = s.ticks[i];
    measured_[i] = float(delta) * cal_.mm_per_tick * 1000.0f / float(dt);
    if (armed_ && (std::abs(measured_[i]) > 150 || s.invalid_transitions)) {
      fault(ENCODER, now);
      return;
    }
    if (!armed_ || !have_command_)
      continue;
    const float step = float(accel_) * float(dt) / 1000.0f;
    target_[i] += std::clamp(requested_[i] - target_[i], -step, step);
    const float error = target_[i] - measured_[i];
    const float candidate =
        std::clamp(integral_[i] + error * float(dt) / 1000.0f, -10.0f, 10.0f);
    const float raw = cal_.kp * error + cal_.ki * candidate;
    // No reverse drive to brake, and no integral windup at output saturation.
    if (raw >= 0 && raw <= 0.25f)
      integral_[i] = candidate;
    const float duty = target_[i] == 0 ? 0 : std::clamp(raw, 0.0f, 0.25f);
    if (target_[i] == 0)
      integral_[i] = 0;
    if (i == 0)
      output_.left = duty;
    else
      output_.right = duty;
    stall_ms_[i] = target_[i] > 5 && delta <= 0 ? stall_ms_[i] + dt : 0;
    if (stall_ms_[i] >= 200) {
      fault(ENCODER, now);
      return;
    }
  }
  output_.enabled = armed_ && have_command_;
}
Frame Controller::status(uint32_t now, bool watchdog, uint32_t errors) const {
  Frame f{};
  f.type = STATUS;
  f.size = uint16_t(payload_size(STATUS));
  f.session = session_;
  auto *p = f.payload.data();
  const uint32_t fields[] = {now,       kProfile,   faults_,   first_fault_ms_,
                             sequence_, action_id_, rejected_, errors};
  for (unsigned i = 0; i < 8; ++i)
    put_le(p + i * 4, fields[i], 4);
  p[32] = armed_;
  p[33] = cal_.qualified;
  p[34] = watchdog;
  p[35] = self_test_ok_;
  return f;
}
Frame Controller::sensor_frame(uint32_t now, const Sensors &s) const {
  Frame f{};
  f.type = SENSORS;
  f.size = uint16_t(payload_size(SENSORS));
  f.session = session_;
  auto *p = f.payload.data();
  put_le(p, now, 4);
  put_le(p + 4, s.cliff_mm[0], 2);
  put_le(p + 6, s.cliff_mm[1], 2);
  put_le(p + 8, s.battery_mv, 2);
  put_le(p + 10, s.soc_centi_percent, 2);
  for (unsigned i = 0; i < 3; ++i) {
    put_le(p + 12 + 2 * i, uint16_t(s.accel_mg[i]), 2);
    put_le(p + 18 + 2 * i, uint16_t(s.gyro_mdeg_s[i]), 2);
  }
  p[24] = uint8_t((s.cliff_valid[0] && now - s.cliff_ms[0] < 50) |
                  ((s.cliff_valid[1] && now - s.cliff_ms[1] < 50) << 1) |
                  ((s.imu_valid && now - s.imu_ms < 50) << 2) |
                  ((s.power_valid && now - s.power_ms < 500) << 3));
  p[25] = uint8_t(s.charge_absent | (s.driver_ok << 1));
  put_le(p + 26, now - s.cliff_ms[0], 4);
  put_le(p + 30, now - s.cliff_ms[1], 4);
  put_le(p + 34, now - s.imu_ms, 4);
  return f;
}
Frame Controller::odometry(uint32_t now, const Sensors &s) const {
  Frame f{};
  f.type = ODOMETRY;
  f.size = uint16_t(payload_size(ODOMETRY));
  f.session = session_;
  auto *p = f.payload.data();
  put_le(p, now, 4);
  for (unsigned i = 0; i < 2; ++i) {
    put_le(p + 4 + 4 * i, s.ticks[i], 4);
    put_le(p + 12 + 2 * i,
           uint16_t(int16_t(std::clamp(measured_[i], -32767.0f, 32767.0f))), 2);
  }
  put_le(p + 16, interval_ms_, 2);
  put_le(p + 18, std::min<uint32_t>(s.invalid_transitions, 65535U), 2);
  return f;
}
int quadrature_delta(uint8_t previous, uint8_t current) {
  static constexpr int8_t table[16] = {0,  -1, 1, 0, 1, 0, 0,  -1,
                                       -1, 0,  0, 1, 0, 1, -1, 0};
  return table[((previous & 3) << 2) | (current & 3)];
}
} // namespace sherman
