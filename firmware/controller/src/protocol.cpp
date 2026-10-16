#include "sherman/protocol.hpp"
#include <algorithm>
namespace sherman {
uint64_t get_le(const uint8_t *p, unsigned bytes) {
  uint64_t value = 0;
  for (unsigned i = 0; i < bytes; ++i)
    value |= uint64_t(p[i]) << (8 * i);
  return value;
}
void put_le(uint8_t *p, uint64_t value, unsigned bytes) {
  for (unsigned i = 0; i < bytes; ++i)
    p[i] = uint8_t(value >> (8 * i));
}
uint16_t crc16(const uint8_t *data, size_t size) {
  uint16_t crc = 0xffff;
  for (size_t i = 0; i < size; ++i) {
    crc ^= uint16_t(data[i]) << 8;
    for (unsigned bit = 0; bit < 8; ++bit)
      crc = uint16_t((crc << 1) ^ ((crc & 0x8000) ? 0x1021 : 0));
  }
  return crc;
}
size_t encode(const Frame &frame, uint8_t *out) {
  if (frame.size > kMaxPayload)
    return 0;
  out[0] = 0xa5;
  out[1] = 0x5a;
  out[2] = kVersion;
  out[3] = frame.type;
  put_le(out + 4, frame.size, 2);
  put_le(out + 6, frame.sequence, 4);
  put_le(out + 10, frame.session, 8);
  std::copy_n(frame.payload.begin(), frame.size, out + 18);
  put_le(out + 18 + frame.size, crc16(out + 2, 16 + frame.size), 2);
  return 20 + frame.size;
}
bool Parser::feed(uint8_t byte, uint32_t now, Frame &out) {
  if (used_ && now - last_ms_ > 20) {
    used_ = 0;
    ++errors_;
  }
  last_ms_ = now;
  if (!used_) {
    if (byte == 0xa5)
      data_[used_++] = byte;
    return false;
  }
  if (used_ == 1 && byte != 0x5a) {
    used_ = byte == 0xa5 ? 1 : 0;
    return false;
  }
  data_[used_++] = byte;
  if (used_ == 6 &&
      (data_[2] != kVersion || get_le(data_.data() + 4, 2) > kMaxPayload)) {
    used_ = 0;
    ++errors_;
    return false;
  }
  if (used_ < 6)
    return false;
  const size_t size = size_t(get_le(data_.data() + 4, 2));
  if (used_ != size + 20)
    return false;
  used_ = 0;
  if (crc16(data_.data() + 2, size + 16) !=
      get_le(data_.data() + 18 + size, 2)) {
    ++errors_;
    return false;
  }
  out.type = data_[3];
  out.size = uint16_t(size);
  out.sequence = uint32_t(get_le(data_.data() + 6, 4));
  out.session = get_le(data_.data() + 10, 8);
  std::copy_n(data_.begin() + 18, size, out.payload.begin());
  return true;
}
} // namespace sherman
