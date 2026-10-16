#include "hardware/i2c.h"
#include "hardware/sync.h"
#include "hardware/uart.h"
#include "hardware/watchdog.h"
#include "pico/rand.h"
#include "pico/stdlib.h"
#include "sherman/controller.hpp"
#include "sherman/pins.hpp"
#include "sherman/sensors.hpp"
#include "tusb.h"
#include <algorithm>
#include <array>
#include <cstdio>
#include <cstring>
using namespace sherman;
namespace {
uint32_t now_ms() { return uint32_t(time_us_64() / 1000); }
void low_output(unsigned pin) {
  gpio_init(pin);
  gpio_put(pin, false);
  gpio_set_dir(pin, GPIO_OUT);
}
void inhibit() {
  gpio_put(pins::MOTOR_SLEEP_REQUEST, false);
  gpio_put(pins::MOTOR_RAIL_REQUEST, false);
  for (unsigned p = 8; p <= 11; ++p)
    gpio_put(p, false);
}
class PicoBus final : public SensorBus {
public:
  bool read(uint8_t a, uint16_t r, unsigned width, uint8_t *data,
            size_t size) override {
    uint8_t reg[] = {uint8_t(r >> 8), uint8_t(r)};
    if (i2c_write_timeout_us(i2c0, a, reg + (width == 1 ? 1 : 0), width, true,
                             2000) != int(width))
      return false;
    return i2c_read_timeout_us(i2c0, a, data, size, false, 2000) == int(size);
  }
  bool write(uint8_t a, uint16_t r, unsigned width, const uint8_t *data,
             size_t size) override {
    if (size + width > 32)
      return false;
    uint8_t bytes[32];
    if (width == 2)
      bytes[0] = uint8_t(r >> 8);
    bytes[width - 1] = uint8_t(r);
    std::memcpy(bytes + width, data, size);
    return i2c_write_timeout_us(i2c0, a, bytes, size + width, false, 4000) ==
           int(size + width);
  }
  void xshut(unsigned index, bool released) override {
    const unsigned pin =
        index == 0 ? pins::CLIFF_L_XSHUT_N : pins::CLIFF_R_XSHUT_N;
    gpio_put(pin, false);
    gpio_set_dir(pin, released ? GPIO_IN : GPIO_OUT);
    gpio_disable_pulls(pin); // never drive 2.8 V carrier XSHUT high
  }
  void wait_ms(uint32_t ms) override { sleep_ms(ms); }
  uint32_t now_ms() override { return ::now_ms(); }
};
volatile uint32_t encoder_ticks[2]{}, encoder_errors = 0;
uint8_t encoder_state[2]{};
void encoder_irq(uint gpio, uint32_t) {
  const unsigned index = gpio >= pins::ENC_R_A ? 1 : 0;
  const unsigned a = index == 0 ? pins::ENC_L_A : pins::ENC_R_A;
  const auto state = uint8_t(gpio_get(a) | (gpio_get(a + 1) << 1));
  if ((state ^ encoder_state[index]) == 3)
    ++encoder_errors;
  encoder_ticks[index] +=
      uint32_t(quadrature_delta(encoder_state[index], state));
  encoder_state[index] = state;
}
void snapshot(Sensors &s) {
  const auto saved = save_and_disable_interrupts();
  s.ticks[0] = encoder_ticks[0];
  s.ticks[1] = encoder_ticks[1];
  s.invalid_transitions = encoder_errors;
  restore_interrupts(saved);
  s.charge_absent = gpio_get(pins::CHARGE_ABSENT);
  s.driver_ok = gpio_get(pins::MOTOR_FAULT_N);
}
class Transmitter {
public:
  void queue(Frame frame) {
    if (used_) {
      ++dropped;
      return;
    }
    frame.sequence = ++sequence_;
    used_ = encode(frame, data_.data());
    offset_ = 0;
  }
  void pump() {
    // Never block on a stalled host; each pass writes only available FIFO
    // slots.
    for (unsigned count = 0; count < 32 && used_ && uart_is_writable(uart0);
         ++count) {
      uart_get_hw(uart0)->dr = data_[offset_++];
      if (offset_ == used_)
        used_ = 0;
    }
  }
  uint32_t dropped = 0;

private:
  std::array<uint8_t, kFrameMax> data_{};
  size_t used_ = 0, offset_ = 0;
  uint32_t sequence_ = 0;
};
} // namespace
int main() {
  // Earliest GPIO work: both XSHUT low before any I2C, requests/PWM low.
  low_output(pins::CLIFF_L_XSHUT_N);
  low_output(pins::CLIFF_R_XSHUT_N);
  low_output(pins::MOTOR_RAIL_REQUEST);
  low_output(pins::MOTOR_SLEEP_REQUEST);
  for (unsigned p = 8; p <= 11; ++p)
    low_output(p);
  low_output(pins::CTRL_READY);
  inhibit();
  gpio_init(pins::CHARGE_ABSENT);
  gpio_pull_down(pins::CHARGE_ABSENT);
  gpio_init(pins::MOTOR_FAULT_N);
  gpio_pull_down(pins::MOTOR_FAULT_N);
  // External qualified nFAULT pull-up is required; unplug must fail closed.
  for (unsigned p = 14; p <= 17; ++p) {
    gpio_init(p);
    gpio_pull_down(p);
  }
  for (unsigned i = 0; i < 2; ++i)
    encoder_state[i] =
        uint8_t(gpio_get(14 + 2 * i) | (gpio_get(15 + 2 * i) << 1));
  for (unsigned p = 14; p <= 17; ++p)
    gpio_set_irq_enabled_with_callback(
        p, GPIO_IRQ_EDGE_RISE | GPIO_IRQ_EDGE_FALL, true, encoder_irq);
  uart_init(uart0, 115200);
  uart_set_format(uart0, 8, 1, UART_PARITY_NONE);
  uart_set_hw_flow(uart0, false, false);
  gpio_set_function(0, GPIO_FUNC_UART);
  gpio_set_function(1, GPIO_FUNC_UART);
  i2c_init(i2c0, 100000);
  gpio_set_function(4, GPIO_FUNC_I2C);
  gpio_set_function(5, GPIO_FUNC_I2C);
  stdio_init_all();
  const bool watchdog_reset = watchdog_caused_reboot();
  Controller controller(get_rand_64()); // default profile unqualified; no
                                        // motor-enabled target mode
  PicoBus bus;
  SensorDriver driver(bus);
  Sensors sensors{};
  Parser parser;
  Transmitter tx;
  watchdog_enable(3000,
                  true); // bounded sensor startup may take over 1 s on faults
  driver.initialize();
  watchdog_enable(1000, true);
  uint32_t last_poll = now_ms(), last_report = last_poll, last_usb = last_poll;
  uint32_t max_loop_us = 0, errors = 0, parser_errors_seen = 0;
  unsigned report = 0;
  gpio_put(pins::CTRL_READY, true); // runtime alive, NOT motion-ready
  while (true) {
    const auto start = time_us_64();
    snapshot(sensors);
    controller.tick(now_ms(), sensors);
    inhibit();
    // Bounded RX work prevents a UART flood from starving sensors/safety.
    for (unsigned budget = 0; budget < 64 && uart_is_readable(uart0);
         ++budget) {
      const uint32_t raw = uart_get_hw(uart0)->dr;
      if (raw & 0xf00U) {
        ++errors;
        controller.transport_error(now_ms());
        continue;
      }
      Frame frame;
      if (parser.feed(uint8_t(raw), now_ms(), frame))
        controller.receive(frame, now_ms(), sensors);
      if (parser.errors() != parser_errors_seen) {
        parser_errors_seen = parser.errors();
        controller.transport_error(now_ms());
      }
    }
    if (now_ms() - last_poll >= 10) {
      last_poll = now_ms();
      driver.poll(sensors);
    }
    snapshot(sensors);
    controller.tick(now_ms(), sensors);
    inhibit();
    if (now_ms() - last_report >= 20) {
      last_report = now_ms();
      if (report == 0)
        tx.queue(controller.status(now_ms(), watchdog_reset,
                                   errors + parser.errors()));
      else if (report == 1)
        tx.queue(controller.sensor_frame(now_ms(), sensors));
      else
        tx.queue(controller.odometry(now_ms(), sensors));
      report = (report + 1) % 3;
    }
    tx.pump();
    // Bounded read-only USB summary, no printf/USB wait in the safety loop.
    if (now_ms() - last_usb >= 1000) {
      last_usb = now_ms();
      char text[192];
      const int n = snprintf(
          text, sizeof(text),
          "Sherman Pico2 W1 draft %s uptime_ms=%lu qualified=0 armed=0 "
          "faults=%lu rx_errors=%lu loop_max_us=%lu tx_drop=%lu\n",
          SHERMAN_BUILD_ID, (unsigned long)now_ms(),
          (unsigned long)controller.faults(),
          (unsigned long)(errors + parser.errors()), (unsigned long)max_loop_us,
          (unsigned long)tx.dropped);
      // TinyUSB is also serviced by the SDK's background IRQ. This single-core
      // program masks it only for the bounded FIFO copy (never for formatting).
      const auto saved = save_and_disable_interrupts();
      if (n > 0 && size_t(n) < sizeof(text) && tud_cdc_connected() &&
          tud_cdc_write_available() >= uint32_t(n))
        tud_cdc_write(text, uint32_t(n));
      restore_interrupts(saved);
    }
    max_loop_us = std::max(max_loop_us, uint32_t(time_us_64() - start));
    watchdog_update();
    sleep_us(100);
  }
}
