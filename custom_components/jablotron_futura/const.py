DOMAIN = "jablotron_futura"

CONF_HOST = "host"
CONF_PORT = "port"
CONF_UNIT_ID = "unit_id"
DEFAULT_PORT = 502
DEFAULT_UNIT_ID = 1

PLATFORMS = [
    "sensor",
    "binary_sensor",
    "switch",
    "select",
    "number",
    "button",
]

# Register map (addresses) derived from your YAML
# Input registers (read-only)
INP_START_MAIN = 14
INP_LEN_MAIN = 37   # 14..52
INP_START_ALFA = 160

# Holding registers (read/write)
HOLD_START_MAIN = 0
HOLD_LEN_MAIN = 18  # 0..17

# Keys we expose in coordinator.data
KEYS = {
    # Input area (14..44)
    "variant_raw": 14,
    "fut_config_raw": 15,       # uint16 bitfield with feature availability
    "modes_bits_raw": 16,       # uint32
    "errors_bits_raw": 18,      # uint32
    "warnings_bits_raw": 20,    # uint32

    "temp_outdoor": 30,         # int16, x0.1
    "temp_supply": 31,          # int16, x0.1
    "temp_extract": 32,         # int16, x0.1
    "temp_exhaust": 33,         # int16, x0.1
    "temp_outdoor_ntc": 38,     # int16, x0.1

    "humi_outdoor": 34,         # int16, x0.1
    "humi_supply": 35,          # int16, x0.1
    "humi_extract": 36,         # int16, x0.1
    "humi_exhaust": 37,         # int16, x0.1

    "filter_wear": 40,          # uint16 (%)
    "power": 41,                # uint16 (W)
    "heat_recovering": 42,      # uint16 (W)
    "heating_power": 43,        # uint16 (W)
    "air_flow": 44,             # uint16 (m3/h)
    "fan_power_supply": 45,     # uint16 (W)
    "fan_power_exhaust": 46,    # uint16 (W)
    "fan_rpm_supply": 47,       # uint16 (rpm)
    "fan_rpm_exhaust": 48,      # uint16 (rpm)
    "rtc_batt_voltage": 52,     # uint16 (mV)

    # ALFA controllers
    "alfa_connected_bits": 75,  # uint16 bitfield

    # Holding 0..17
    "mode_raw": 0,              # uint16 (0..6)
    "boost_remaining_s": 1,     # uint16 seconds
    "circulation_remaining_s": 2,# uint16 seconds
    "overpressure_remaining_s": 3,# uint16 seconds
    "night_remaining_s": 4,     # uint16 seconds
    "party_remaining_s": 5,     # uint16 seconds
    "away_begin_ts": 6,         # uint32 (6,7)
    "away_end_ts": 8,           # uint32 (8,9)
    "temp_set_raw": 10,         # int16 x0.1 °C
    "humi_set_raw": 11,         # int16 x0.1 %
    "time_program_raw": 12,     # 0/1
    "antiradon_raw": 13,        # 0/1
    "bypass_enable_raw": 14,    # 0/1
    "heating_enable_raw": 15,   # 0/1
    "cooling_enable_raw": 16,   # 0/1
    "comfort_enable_raw": 17,   # 0/1
}

for i in range(1, 9):
    base = 160 + (i - 1) * 10
    KEYS[f"alfa_mb_address_{i}"] = base       # uint16
    KEYS[f"alfa_options_{i}"] = base + 1      # uint16 bit flags
    KEYS[f"alfa_co2_{i}"] = base + 2          # uint16 ppm
    KEYS[f"alfa_temp_{i}"] = base + 3         # int16 x0.1 °C
    KEYS[f"alfa_humi_{i}"] = base + 4         # uint16 x0.1 %
    KEYS[f"alfa_ntc_temp_{i}"] = base + 5     # int16 x0.1 °C

VENT_MODE_MAP = {
    "Vypnuto": 0,
    "1": 1,
    "2": 2,
    "3": 3,
    "4": 4,
    "5": 5,
    "Auto": 6,
}
VENT_MODE_INV = {v: k for k, v in VENT_MODE_MAP.items()}

HUMI_MODE_MAP = {"Suché": 25.0, "Komfortní": 50.0, "Vlhké": 75.0}
