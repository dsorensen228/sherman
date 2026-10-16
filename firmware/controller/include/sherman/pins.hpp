#pragma once
namespace sherman::pins {
constexpr unsigned HOST_RX = 0, HOST_TX = 1, CTRL_READY = 2;
constexpr unsigned MOTOR_RAIL_REQUEST = 3, SAFE_SDA = 4, SAFE_SCL = 5,
                   CHARGE_ABSENT = 6;
constexpr unsigned MOTOR_L_IN1 = 8, MOTOR_L_IN2 = 9, MOTOR_R_IN1 = 10,
                   MOTOR_R_IN2 = 11;
constexpr unsigned MOTOR_SLEEP_REQUEST = 12, MOTOR_FAULT_N = 13;
constexpr unsigned ENC_L_A = 14, ENC_L_B = 15, ENC_R_A = 16, ENC_R_B = 17;
constexpr unsigned CLIFF_L_XSHUT_N = 18, CLIFF_R_XSHUT_N = 19;
constexpr unsigned CLIFF_L_INT_N = 20, CLIFF_R_INT_N = 21, IMU_INT1 = 22,
                   IMU_INT2 = 26;
} // namespace sherman::pins
