#!/usr/bin/env bash

set -euo pipefail
export LC_ALL=C
export LANG=C

component_dir=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
vendor_dir="$component_dir/vendor"
archive_dir="$vendor_dir/.archives"

mkdir -p \
  "$archive_dir" \
  "$vendor_dir/adafruit" \
  "$vendor_dir/luckfox" \
  "$vendor_dir/pololu" \
  "$vendor_dir/raspberry-pi" \
  "$vendor_dir/waveshare"

verify_sha256() {
  expected=$1
  path=$2
  actual=$(shasum -a 256 "$path" | awk '{print $1}')
  if [ "$actual" != "$expected" ]; then
    printf 'SHA-256 mismatch for %s\nexpected: %s\nactual:   %s\n' "$path" "$expected" "$actual" >&2
    return 1
  fi
}

download() {
  url=$1
  output=$2
  expected=$3
  if [ ! -f "$output" ]; then
    curl --fail --location --retry 3 --output "$output" "$url"
  fi
  verify_sha256 "$expected" "$output"
}

extract_zip_member() {
  archive=$1
  member=$2
  output=$3
  expected=$4
  if [ ! -f "$output" ]; then
    temporary=$(mktemp "${output}.tmp.XXXXXX")
    trap 'rm -f "$temporary"' EXIT HUP INT TERM
    unzip -p "$archive" "$member" > "$temporary"
    verify_sha256 "$expected" "$temporary"
    mv "$temporary" "$output"
    trap - EXIT HUP INT TERM
  fi
  verify_sha256 "$expected" "$output"
}

luckfox_dwg="$vendor_dir/luckfox/luckfox-pico-ultra-w.dwg"
if [ ! -f "$luckfox_dwg" ]; then
  download \
    'https://forums.luckfox.com/download/file.php?id=764' \
    "$archive_dir/luckfox-pico-ultra-w.zip" \
    '50fcaa48833ad16c2177df2d27e50042492d8b6a8e0f9fdd76d3c7edc502eb08'
  extract_zip_member \
    "$archive_dir/luckfox-pico-ultra-w.zip" \
    'Luckfox Pico Ultra W.DWG' \
    "$luckfox_dwg" \
    '5de9e6aeb3681b8c5b468619881f3438c1c07932f778f32dbeee8269f0bce6c9'
else
  verify_sha256 \
    '5de9e6aeb3681b8c5b468619881f3438c1c07932f778f32dbeee8269f0bce6c9' \
    "$luckfox_dwg"
fi
download \
  'https://wiki.luckfox.com/assets/files/SC3336-3MP-Camera-B-c02809bc24b8ac9e6b7a4c0b935c9d9e.pdf' \
  "$vendor_dir/luckfox/sc3336-camera-b-mechanical.pdf" \
  'cba499a8324fa2ca97a8641cbb1e570587dfe82cd65642cd0155c4c5cf1aabb7'

download \
  'https://files.waveshare.com/upload/9/98/1.9inch_LCD_Module_3D.zip' \
  "$archive_dir/waveshare-23822-1.9inch-lcd.zip" \
  '5f7e8b080c631df0259cabee3d6a325192b1877f79707c66eb55e9205ec598e7'
extract_zip_member \
  "$archive_dir/waveshare-23822-1.9inch-lcd.zip" \
  '1.9inch LCD Module/1_9inch-lcd-module.stp' \
  "$vendor_dir/waveshare/waveshare-23822-1.9inch-lcd.stp" \
  'b0f1c0cf83221b95561fa0bdede212159476f65140dc4795f81c9ce45b7e6ca5'

download \
  'https://pip-assets.raspberrypi.com/categories/1005-raspberry-pi-pico-2/documents/RP-009061-CA-2-Pico%202%20-%203D%20STEP.zip' \
  "$archive_dir/raspberry-pi-pico-2.zip" \
  '74974c52ee695a1d2c638d8288c798b42236c60d7de7af5345b9a5017f993f82'
extract_zip_member \
  "$archive_dir/raspberry-pi-pico-2.zip" \
  'rpi_pico2.step' \
  "$vendor_dir/raspberry-pi/raspberry-pi-pico-2.step" \
  'd49ada10d893cfcb07cb4abced0a0a0cadca4c4150f153d874268ca06171a24f'
extract_zip_member \
  "$archive_dir/raspberry-pi-pico-2.zip" \
  'LICENSE.txt' \
  "$vendor_dir/raspberry-pi/LICENSE-Pico-2.txt" \
  '719e1649001e3564fdcbb609c5fdfcce695153dcb6c135c9f737cc30a548bd20'

download \
  'https://pip-assets.raspberrypi.com/categories/1264-raspberry-pi-pico-2-with-headers/documents/RP-009062-CA-2-Pico%202%20H%20-%203D%20STEP.zip' \
  "$archive_dir/raspberry-pi-pico-2-h.zip" \
  '024de65032d37f0ef55e0f11611ae67f85fd0cb5a3f79d2841440a7740f967e7'
extract_zip_member \
  "$archive_dir/raspberry-pi-pico-2-h.zip" \
  'rpi_pico2h.step' \
  "$vendor_dir/raspberry-pi/raspberry-pi-pico-2-h.step" \
  'e1d6614bd8e5bb94aae2eef9452be244da56d48f4f1c363e71f19eff1fe69d4f'

download \
  'https://www.pololu.com/file/0J1874/vl53l5cx-carrier-model.step' \
  "$vendor_dir/pololu/pololu-3417-vl53l5cx.step" \
  '1cb6ed4c1e94aaade7337a5fcfc2e263b14cceeac0295d1ce1ff2bb8b43b1bcc'
download \
  'https://www.pololu.com/file/0J1195/vl53l0x-vl53l1x-vl53l3cx-vl53l4cd-carrier-model.step' \
  "$vendor_dir/pololu/pololu-3692-vl53l4cd.step" \
  'e7a0bf09f1fb4fb442448e7beae76aed2d67526c93b80a3f8a3320059b9e5c6f'
download \
  'https://www.pololu.com/file/0J1904/lsm6dso-3d-accelerometer-and-gyro-carrier-with-voltage-regulator.step' \
  "$vendor_dir/pololu/pololu-2798-lsm6dso.step" \
  '1881e0d2323766373243d5dbecda8c16a96127181c1d09ff401c0e9eda5e69c3'

download \
  'https://www.pololu.com/file/0J2042/Pololu%20Micro%20Metal%20Gearmotor%203D%20(STEP)%20Models.zip' \
  "$archive_dir/pololu-5146-micro-metal-gearmotors.zip" \
  'eeafd5682d7a2c7deed7c7c7e24719eeb36761706aca4a1c5c815c07c36cbb55'
extract_zip_member \
  "$archive_dir/pololu-5146-micro-metal-gearmotors.zip" \
  'With Encoder, Back Connector/mmgm-pm-enc-back-con.step' \
  "$vendor_dir/pololu/pololu-5146-mmgm-pm-enc-back-con.step" \
  'a010728f958a5e4d67dd6c7a8ac9892e4c47f0d0583b9a318f128276c7794cc1'
extract_zip_member \
  "$archive_dir/pololu-5146-micro-metal-gearmotors.zip" \
  'README.txt' \
  "$vendor_dir/pololu/pololu-5146-model-key.txt" \
  '66b272aed818fdc4c076578ab6d488d3ce868e3d8c1a59b894acc4e4de99e4b1'

download \
  'https://www.pololu.com/file/0J1296/pololu-wheel-32%C3%977mm.zip' \
  "$archive_dir/pololu-1087-wheel-32x7.zip" \
  '745274ce04ad44220d2152e1350cdeb43128870aa00df6536b2564edad89a350'
extract_zip_member \
  "$archive_dir/pololu-1087-wheel-32x7.zip" \
  'pololu-wheel-32x7mm-black.step' \
  "$vendor_dir/pololu/pololu-1087-wheel-32x7-black.step" \
  '0254a1d6ed3ed3117a882b34c8bea86c26f7bd9ad9f3d43a1d44faf9de44309a'

download \
  'https://www.pololu.com/file/0J1723/micro-metal-gearmotor-bracket.step' \
  "$vendor_dir/pololu/pololu-989-bracket.step" \
  '87f0be95abde4d475c5a435a4b388f43000ad0a6ed518e31cdf7379b4d255881'
download \
  'https://www.pololu.com/file/0J1616/drv8833-dual-motor-driver-carrier-step.step' \
  "$vendor_dir/pololu/pololu-2130-drv8833.step" \
  '90960797d0f972d87bd07ec43d6adeec8bd4145686464896cd7f93a45d6bd70a'
download \
  'https://www.pololu.com/file/0J1561/step-up-voltage-regulator-u3v70x.step' \
  "$vendor_dir/pololu/pololu-2891-u3v70x.step" \
  '0407ad51b9083b7e6f0e6d02d9d6311db355d28cf553f6c322a61f9e6924682d'
download \
  'https://www.pololu.com/file/0J1308/mini-pushbutton-power-switch-with-reverse-voltage-protection.step' \
  "$vendor_dir/pololu/pololu-2808-power-switch.step" \
  '9e3718142701cf853fd2b2be9e70452a1d4ef040858a043e921c965aeca33707'

download \
  'https://raw.githubusercontent.com/adafruit/Adafruit_CAD_Parts/main/LICENSE' \
  "$vendor_dir/adafruit/LICENSE.txt" \
  'f60436644e066301d4c2e8f1f0674a157b1f60e4fd5586717b99dde255cc18cd'
download \
  'https://raw.githubusercontent.com/adafruit/Adafruit_CAD_Parts/main/258%201200mAh%20lipo/258%201200mAh%20lipo.step' \
  "$vendor_dir/adafruit/adafruit-258-lipo.step" \
  'c81bcfef27a54a671cec259164a23666fbad6d8b4320c10dc6b5ae0567002001'
download \
  'https://raw.githubusercontent.com/adafruit/Adafruit_CAD_Parts/main/258%201200mAh%20lipo/258%201200mAh%20lipo.stl' \
  "$vendor_dir/adafruit/adafruit-258-lipo.stl" \
  'abe4ffb89a83d1ee48780c04e4dbb38808b326f491f312eef56e2552ad5d2103'
download \
  'https://raw.githubusercontent.com/adafruit/Adafruit_CAD_Parts/main/4410%20Micro%20Lipo%20USBC/4410%20Micro%20Lipo%20USBC.step' \
  "$vendor_dir/adafruit/adafruit-4410-micro-lipo-usbc.step" \
  'e715d1f1d9ecf3fde18da2671f4c0021002265cd2a651f427927914a93e77f56'
download \
  'https://raw.githubusercontent.com/adafruit/Adafruit_CAD_Parts/main/4410%20Micro%20Lipo%20USBC/4410%20Micro%20Lipo%20USBC.stl' \
  "$vendor_dir/adafruit/adafruit-4410-micro-lipo-usbc.stl" \
  'e9cd7e222569e2beae2b84e97a760a1e334a57b7845c806957244c34ea5efbd6'
download \
  'https://raw.githubusercontent.com/adafruit/Adafruit_CAD_Parts/main/5580%20MAX17048/5580%20MAX17048.step' \
  "$vendor_dir/adafruit/adafruit-5580-max17048.step" \
  'acc003d40a01eeeb7e5f63c9f6da4e4e87a5113dcc4a02990f2f26b7df2e7971'
download \
  'https://raw.githubusercontent.com/adafruit/Adafruit_CAD_Parts/main/5580%20MAX17048/5580%20MAX17048.stl' \
  "$vendor_dir/adafruit/adafruit-5580-max17048.stl" \
  '9a108e19b44fe9adf703faf37458c78f4d4675104ce046ccceb83bbb15c0e45f'

printf 'Verified component files in %s\n' "$vendor_dir"
find "$vendor_dir" -type f ! -path "$archive_dir/*" -print | sort
