#include "sherman/controller.hpp"
#include <cassert>
#include <cmath>
#include <iostream>
#include <random>
using namespace sherman;
namespace {
Sensors healthy(uint32_t now) {
  Sensors s{};
  s.charge_absent = s.driver_ok = s.imu_valid = s.power_valid = true;
  s.cliff_valid[0] = s.cliff_valid[1] = true;
  s.cliff_mm[0] = s.cliff_mm[1] = 20;
  s.cliff_ms[0] = s.cliff_ms[1] = s.imu_ms = s.power_ms = now;
  s.accel_mg[2] = 1000;
  s.battery_mv = 3800;
  return s;
}
struct Rig {
  Calibration cal{true};
  Controller c{123, cal};
  uint32_t seq = 0;
  bool send(uint8_t type, uint32_t now, uint32_t value = 0,
            Sensors s = healthy(0)) {
    Frame f{};
    f.type = type;
    f.size = uint16_t(payload_size(type));
    f.session = 123;
    f.sequence = ++seq;
    put_le(f.payload.data(), value, 4);
    return c.receive(f, now, s);
  }
  void arm(uint32_t now = 0) {
    auto s = healthy(now);
    assert(send(HELLO, now, kProfile, s));
    assert(send(HEARTBEAT, now, now + 100, s));
    assert(send(ARM, now, now + 100, s));
    assert(c.armed());
  }
  bool twist(uint32_t now, int16_t linear = 20, int16_t angular = 0,
             uint32_t deadline = 100) {
    Frame f{};
    f.type = TWIST;
    f.size = uint16_t(payload_size(TWIST));
    f.session = 123;
    f.sequence = ++seq;
    put_le(f.payload.data(), deadline, 4);
    put_le(f.payload.data() + 4, uint16_t(linear), 2);
    put_le(f.payload.data() + 6, uint16_t(angular), 2);
    put_le(f.payload.data() + 8, 100, 2);
    put_le(f.payload.data() + 10, 42, 4);
    return c.receive(f, now, healthy(now));
  }
};
void expect_stop(Rig &r, uint32_t reason) {
  assert(!r.c.armed());
  assert(!r.c.output().enabled);
  assert(r.c.output().left == 0 && r.c.output().right == 0);
  assert(r.c.faults() & reason);
}
void authority() {
  Controller c(123);
  auto s = healthy(0);
  c.tick(0, s);
  assert(!c.output().enabled);
  Frame f{};
  f.session = 123;
  f.sequence = 1;
  f.type = HELLO;
  f.size = 4;
  put_le(f.payload.data(), kProfile, 4);
  assert(c.receive(f, 0, s));
  f.type = HEARTBEAT;
  ++f.sequence;
  put_le(f.payload.data(), 100, 4);
  assert(c.receive(f, 0, s));
  f.type = ARM;
  ++f.sequence;
  assert(!c.receive(f, 0, s));
  assert(c.faults() & UNQUALIFIED);
  Rig r;
  r.arm();
  assert(r.twist(0));
  r.c.tick(10, healthy(10));
  assert(r.c.output().enabled && r.c.output().left > 0 &&
         r.c.output().left <= 0.25f);
  assert(r.c.output().left == r.c.output().right);
  f = {};
  f.type = STOP;
  assert(r.c.receive(f, 11, healthy(11)));
  assert(!r.c.armed());
  assert(r.c.receive(f, 11,
                     healthy(11))); // stale/no-session STOP stays idempotent
  assert(!r.twist(12));
  expect_stop(r, COMMAND);
  assert(r.send(CLEAR_FAULT, 12, 0, healthy(12)));
  assert(!r.c.faults());
  assert(!r.send(ARM, 12, 100, healthy(12))); // clear requires new heartbeat
  Rig mismatch;
  assert(!mismatch.send(HELLO, 0, kProfile + 1));
  expect_stop(mismatch, PROTOCOL);
  Rig replay;
  replay.arm();
  replay.seq = 2;
  assert(!replay.send(ARM, 0, 100));
  expect_stop(replay, PROTOCOL);
  Rig late;
  late.arm();
  assert(late.twist(0, 20, 0, 25));
  late.c.tick(25, healthy(25));
  expect_stop(late, COMMAND);
  assert(!late.twist(25, 20, 0, 100)); // expired authority cannot revive
  Rig hb;
  hb.arm();
  hb.c.tick(100, healthy(100));
  expect_stop(hb, LINK);
  Rig window;
  window.arm();
  assert(!window.twist(0, 20, 0, 101));
  expect_stop(window, COMMAND);
  Rig reverse;
  reverse.arm();
  assert(!reverse.twist(0, -1));
  expect_stop(reverse, COMMAND);
  Rig pivot;
  pivot.arm();
  assert(!pivot.twist(0, 0, 100));
  expect_stop(pivot, COMMAND);
  Rig speed;
  speed.arm();
  assert(!speed.twist(0, 41));
  expect_stop(speed, COMMAND);
  Rig stall;
  stall.arm();
  assert(stall.twist(0));
  for (uint32_t t = 10; t < 400 && stall.c.armed(); t += 10) {
    if (t % 50 == 0) {
      assert(stall.send(HEARTBEAT, t, t + 100, healthy(t)));
      if (!stall.c.armed())
        break;
      assert(stall.twist(t, 20, 0, t + 100));
    }
    stall.c.tick(t, healthy(t));
  }
  expect_stop(stall, ENCODER);
  Rig wrap;
  wrap.arm(0xfffffff0U);
  assert(wrap.twist(0xfffffff0U, 20, 0, 84));
  wrap.c.tick(4, healthy(4));
  assert(wrap.c.output().enabled);
  wrap.c.tick(84, healthy(84));
  expect_stop(wrap, LINK);
}
void faults() {
  for (unsigned fault = 0; fault < 10; ++fault) {
    Rig r;
    r.arm();
    assert(r.twist(0));
    auto s = healthy(10);
    uint32_t reason = 0;
    switch (fault) {
    case 0:
      s.charge_absent = false;
      reason = CHARGING;
      break;
    case 1:
      s.driver_ok = false;
      reason = DRIVER;
      break;
    case 2:
      s.cliff_valid[0] = false;
      reason = SENSOR;
      break;
    case 3:
      s.cliff_mm[1] = 200;
      reason = CLIFF;
      break;
    case 4:
      s.imu_valid = false;
      reason = SENSOR;
      break;
    case 5:
      s.battery_mv = 2900;
      reason = POWER;
      break;
    case 6:
      s.accel_mg[2] = -1000;
      reason = TILT;
      break;
    case 7:
      s.ticks[0] = 10000;
      reason = ENCODER;
      break;
    case 8:
      s.invalid_transitions = 1;
      reason = ENCODER;
      break;
    case 9:
      s.cliff_ms[0] = 10 - 50U;
      reason = SENSOR;
      break;
    }
    r.c.tick(10, s);
    expect_stop(r, reason);
    r.c.tick(11, healthy(11));
    expect_stop(r, reason); // latch persists
  }
  Rig jitter;
  jitter.arm();
  assert(jitter.twist(0));
  jitter.c.tick(31, healthy(31));
  expect_stop(jitter, LOOP);
  Rig bad;
  bad.arm();
  bad.c.transport_error(1);
  expect_stop(bad, PROTOCOL);
  Rig unknown;
  unknown.arm();
  Frame f{};
  f.type = 250;
  assert(!unknown.c.receive(f, 0, healthy(0)));
  expect_stop(unknown, PROTOCOL);
  Calibration nan{true};
  nan.kp = NAN;
  Controller unqualified(123, nan);
  assert(unqualified.status(0, false, 0).payload[33] == 0);
  Rig limits;
  assert(limits.send(HELLO, 0, kProfile));
  f = {};
  f.type = CONFIGURE_LIMITS;
  f.session = 123;
  f.sequence = 2;
  f.size = 6;
  put_le(f.payload.data(), 41, 2);
  assert(!limits.c.receive(f, 0, healthy(0)));
}
void protocol() {
  const char *known = "123456789";
  assert(crc16(reinterpret_cast<const uint8_t *>(known), 9) == 0x29b1);
  Frame f{}, out{};
  f.type = TWIST;
  f.size = 14;
  f.sequence = 7;
  f.session = 0x123456789abcULL;
  for (unsigned i = 0; i < f.size; ++i)
    f.payload[i] = uint8_t(i);
  uint8_t bytes[kFrameMax];
  const auto size = encode(f, bytes);
  Parser parser;
  for (size_t i = 0; i < size; ++i)
    assert(parser.feed(bytes[i], 0, out) == (i + 1 == size));
  assert(out.payload == f.payload && out.session == f.session &&
         out.sequence == 7);
  bytes[size - 1] ^= 1;
  for (size_t i = 0; i < size; ++i)
    assert(!parser.feed(bytes[i], 0, out));
  assert(parser.errors() == 1);
  encode(f, bytes);
  for (size_t i = 0; i < 8; ++i)
    parser.feed(bytes[i], 0, out);
  for (size_t i = 0; i < size; ++i)
    assert(parser.feed(bytes[i], 21, out) == (i + 1 == size));
  assert(parser.errors() == 2);
  std::mt19937 random(531);
  for (unsigned i = 0; i < 1000000; ++i)
    parser.feed(uint8_t(random()), i / 50, out);
  // Recover at a frame gap after arbitrary corrupt/truncated stream.
  for (size_t i = 0; i < size; ++i)
    assert(parser.feed(bytes[i], 30000, out) == (i + 1 == size));
  assert(quadrature_delta(0, 1) + quadrature_delta(1, 3) +
             quadrature_delta(3, 2) + quadrature_delta(2, 0) ==
         -4);
}
} // namespace
int main() {
  authority();
  faults();
  protocol();
  std::cout << "authority, faults, wrap, control, CRC, 1000000 fuzz bytes "
               "(seed 531): PASS\n";
}
