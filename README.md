
# Jablotron Futura – custom integration (Modbus)

**Version:** 0.1.0 — 2025-08-22

This custom integration exposes the same functionality as your YAML package,
but in a tidy UI-based integration with entities and services.

## Install

1. Unzip the archive into your Home Assistant `config/custom_components/jablotron_futura/` folder.
2. Restart Home Assistant.
3. Go to *Settings → Devices & Services → Add Integration* and search for **Jablotron Futura**.
4. Enter the IP (`192.168.23.10`), port (`502`), and unit ID (`1`).

## Entities

- Sensors for temperatures, humidity, power, airflow, setpoints, timers, ALFA values.
- Binary sensors for error bits (0–12) and warning bits (0–31), plus antiradon active.
- Switches: time program, bypass, heating, cooling, comfort.
- Selects: vent mode (Vypnuto/1–5/Auto), humidity mode (Suché/Komfortní/Vlhké).
- Numbers: temperature setpoint, Boost minutes (0–120, step 15), Circulation minutes (0–120), Night hours (0–10), Party hours (0–8).
- Buttons: *Boost 60 min*, *Circulation 30 min*.

## Services

- `jablotron_futura.set_away` — fields: `begin` (datetime, UTC), `end` (datetime, UTC). Defaults to "now" and "+7 days".
- `jablotron_futura.clear_away` — clears both timestamps.

## Notes

- Polling interval is 5 seconds and reads registers in 3 blocks to be efficient.
- All timestamps are treated in **UTC** (matches your original YAML `timestamp_custom(..., true)` behavior).
- If you need additional helpers (e.g., CO₂ threshold logic), keep your existing HA helpers/automations or we can add more entities/services.

## Troubleshooting

- If entities don't update, make sure Modbus is enabled in your Futura and port 502 is reachable.
- Check HA logs for entries tagged `jablotron_futura`.
