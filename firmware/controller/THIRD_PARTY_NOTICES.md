# Third-party notices

The VL53L4CD default configuration and timing/init sequence in
`src/cliff_defaults.inc` / `src/sensors.cpp` derive from Pololu's VL53L4CD library,
revision `bc865905fc97085f40ca9edab478210c01195fde`, based on ST's ULD.
The complete BSD-3-Clause-Clear terms are in `THIRD_PARTY_LICENSE.txt`; distribute
that file with binary releases. Adaptations replace Arduino/Wire with a bounded
bus interface, explicit errors, isolated addressing and nonblocking runtime reads.
Source: https://github.com/pololu/vl53l4cd-arduino/tree/bc865905fc97085f40ca9edab478210c01195fde

Pico SDK 2.2.0 (`a1438dff1d38bd9c65dbd693f0e5db4b9ae91779`) and its pinned TinyUSB
submodule retain their upstream licenses in the fetched SDK. Distribute SDK
`LICENSE.TXT` and TinyUSB `LICENSE` with firmware packages.

Register references:
- https://www.st.com/resource/en/datasheet/lsm6dso.pdf
- https://www.st.com/resource/en/user_manual/um2931-a-guide-to-using-the-vl53l4cd-ultra-lite-driver-uld-stmicroelectronics.pdf
- https://www.analog.com/media/en/technical-documentation/data-sheets/MAX17048-MAX17049.pdf
