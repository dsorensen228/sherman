#pragma once
#include "wire_generated.hpp"
#include <array>
#include <cstddef>
#include <cstdint>
namespace sherman {
constexpr size_t kFrameMax = 20 + kMaxPayload;
struct Frame {
  uint8_t type = 0;
  uint16_t size = 0;
  uint32_t sequence = 0;
  uint64_t session = 0;
  std::array<uint8_t, kMaxPayload> payload{};
};
uint16_t crc16(const uint8_t *data, size_t size);
uint64_t get_le(const uint8_t *p, unsigned bytes);
void put_le(uint8_t *p, uint64_t value, unsigned bytes);
size_t encode(const Frame &frame, uint8_t *out);
class Parser {
public:
  bool feed(uint8_t byte, uint32_t now_ms, Frame &out);
  uint32_t errors() const { return errors_; }

private:
  std::array<uint8_t, kFrameMax> data_{};
  size_t used_ = 0;
  uint32_t last_ms_ = 0, errors_ = 0;
};
} // namespace sherman
