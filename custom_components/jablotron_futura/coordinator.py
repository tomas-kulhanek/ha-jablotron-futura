from __future__ import annotations

import datetime as dt
import logging
from typing import Any, Dict

from homeassistant.const import CONF_HOST, CONF_PORT
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from pymodbus.client import AsyncModbusTcpClient
from pymodbus.exceptions import ModbusException

from .const import (
    DOMAIN, CONF_UNIT_ID, DEFAULT_UNIT_ID, INP_START_MAIN, INP_LEN_MAIN, INP_START_ALFA, INP_LEN_ALFA,
    HOLD_START_MAIN, HOLD_LEN_MAIN, KEYS
)

_LOGGER = logging.getLogger(__name__)


def _to_int16(x: int) -> int:
    return x - 0x10000 if x & 0x8000 else x


class FuturaCoordinator(DataUpdateCoordinator[Dict[str, Any]]):
    """Coordinator that reads/writes Modbus registers."""

    def __init__(self, hass: HomeAssistant, cfg: dict) -> None:
        super().__init__(
            hass,
            _LOGGER,
            name="Jablotron Futura",
            update_interval=dt.timedelta(seconds=5),
        )
        self.host = cfg.get(CONF_HOST)
        self.port = cfg.get(CONF_PORT, 502)
        self.unit = cfg.get(CONF_UNIT_ID, DEFAULT_UNIT_ID)

        self.client: AsyncModbusTcpClient | None = None

    async def _ensure_client(self) -> AsyncModbusTcpClient:
        if self.client is None:
            self.client = AsyncModbusTcpClient(self.host, port=self.port)
            await self.client.connect()
        return self.client

    async def async_close(self) -> None:
        if self.client:
            try:
                await self.client.close()
            except Exception:  # noqa: BLE001
                pass
            self.client = None

    async def _read_block(self, start: int, count: int, *, input_regs: bool) -> list[int]:
        client = await self._ensure_client()
        try:
            if input_regs:
                rr = await client.read_input_registers(start, count, unit=self.unit)
            else:
                rr = await client.read_holding_registers(start, count, unit=self.unit)
        except ModbusException as e:
            raise UpdateFailed(f"Modbus read failed @ {start}/{count}: {e}") from e
        if rr.isError():
            raise UpdateFailed(f"Modbus error @ {start}/{count}: {rr}")
        return list(rr.registers)

    @staticmethod
    def _u32_from(block: list[int], base: int, addr: int) -> int:
        idx = addr - base
        hi = block[idx]
        lo = block[idx + 1]
        return (hi << 16) | lo

    @staticmethod
    def _i16_from(block: list[int], base: int, addr: int) -> int:
        idx = addr - base
        return _to_int16(block[idx])

    @staticmethod
    def _u16_from(block: list[int], base: int, addr: int) -> int:
        idx = addr - base
        return block[idx]

    async def _async_update_data(self) -> Dict[str, Any]:
        """Read all needed registers and parse into a dict."""
        inp_main = await self._read_block(INP_START_MAIN, INP_LEN_MAIN, input_regs=True)
        inp_alfa = await self._read_block(INP_START_ALFA, INP_LEN_ALFA, input_regs=True)
        hold_main = await self._read_block(HOLD_START_MAIN, HOLD_LEN_MAIN, input_regs=False)

        data: Dict[str, Any] = {}

        # Input area
        data["variant_raw"] = self._u16_from(inp_main, INP_START_MAIN, KEYS["variant_raw"])
        data["modes_bits_raw"] = self._u32_from(inp_main, INP_START_MAIN, KEYS["modes_bits_raw"])
        data["errors_bits_raw"] = self._u32_from(inp_main, INP_START_MAIN, KEYS["errors_bits_raw"])
        data["warnings_bits_raw"] = self._u32_from(inp_main, INP_START_MAIN, KEYS["warnings_bits_raw"])

        for k in ("temp_outdoor","temp_supply","temp_extract","temp_exhaust","temp_outdoor_ntc"):
            data[k] = self._i16_from(inp_main, INP_START_MAIN, KEYS[k]) / 10.0
        for k in ("humi_outdoor","humi_supply","humi_extract","humi_exhaust"):
            data[k] = self._i16_from(inp_main, INP_START_MAIN, KEYS[k]) / 10.0

        data["filter_wear"] = self._u16_from(inp_main, INP_START_MAIN, KEYS["filter_wear"])
        data["power"] = self._u16_from(inp_main, INP_START_MAIN, KEYS["power"])
        data["air_flow"] = self._u16_from(inp_main, INP_START_MAIN, KEYS["air_flow"])

        data["alfa_co2_1"] = self._u16_from(inp_alfa, INP_START_ALFA, KEYS["alfa_co2_1"])
        data["alfa_temp_1"] = self._i16_from(inp_alfa, INP_START_ALFA, KEYS["alfa_temp_1"]) / 10.0
        data["alfa_humi_1"] = self._u16_from(inp_alfa, INP_START_ALFA, KEYS["alfa_humi_1"]) / 10.0

        # Holding area
        for k in (
            "mode_raw","boost_remaining_s","circulation_remaining_s","overpressure_remaining_s",
            "night_remaining_s","party_remaining_s","time_program_raw","antiradon_raw",
            "bypass_enable_raw","heating_enable_raw","cooling_enable_raw","comfort_enable_raw",
        ):
            data[k] = self._u16_from(hold_main, HOLD_START_MAIN, KEYS[k])

        data["away_begin_ts"] = self._u32_from(hold_main, HOLD_START_MAIN, KEYS["away_begin_ts"])
        data["away_end_ts"] = self._u32_from(hold_main, HOLD_START_MAIN, KEYS["away_end_ts"])

        data["temp_set_raw"] = self._i16_from(hold_main, HOLD_START_MAIN, KEYS["temp_set_raw"]) / 10.0
        data["humi_set_raw"] = self._i16_from(hold_main, HOLD_START_MAIN, KEYS["humi_set_raw"]) / 10.0

        # Derived helpers
        v = data.get("mode_raw", 0)
        data["mode_text"] = ["Vypnuto","1","2","3","4","5","Auto"][v] if v in (0,1,2,3,4,5,6) else "Neznámé"

        for key in ("boost_remaining_s","circulation_remaining_s"):
            s = int(data.get(key, 0) or 0)
            data[key.replace("_s", "_min")] = (s + 59) // 60

        def _hours_from_seconds(s: int) -> int:
            return 0 if s == 0 else (s + 3599) // 3600

        data["night_remaining_h"] = _hours_from_seconds(int(data.get("night_remaining_s", 0)))
        data["party_remaining_h"] = _hours_from_seconds(int(data.get("party_remaining_s", 0)))

        for which in ("away_begin_ts","away_end_ts"):
            ts = int(data.get(which, 0) or 0)
            data[which.replace("_ts","_text")] = "Nenastaveno" if ts == 0 else dt.datetime.utcfromtimestamp(ts).strftime("%Y-%m-%d %H:%M")

        return data

    async def _write_u16(self, address: int, value: int) -> None:
        client = await self._ensure_client()
        rr = await client.write_register(address, value, unit=self.unit)
        if rr.isError():
            raise UpdateFailed(f"Write failed @ {address}: {rr}")

    async def _write_u32(self, address: int, value: int) -> None:
        """Write two consecutive holding registers starting at 'address' (hi, lo)."""
        client = await self._ensure_client()
        hi = (value >> 16) & 0xFFFF
        lo = value & 0xFFFF
        # Write multiple registers
        rr = await client.write_registers(address, [hi, lo], unit=self.unit)
        if rr.isError():
            raise UpdateFailed(f"Write failed @ {address} (u32): {rr}")

    async def async_set_away(self, begin: dt.datetime | None, end: dt.datetime | None) -> None:
        now_ts = int(dt.datetime.utcnow().timestamp())
        b_ts = int(begin.timestamp()) if isinstance(begin, dt.datetime) else now_ts
        # Default: 7 days if end not provided or invalid
        if not isinstance(end, dt.datetime) or int(end.timestamp()) <= b_ts:
            e_ts = b_ts + 7*24*3600
        else:
            e_ts = int(end.timestamp())

        await self._write_u32(6, b_ts)
        await self._write_u32(8, e_ts)
        await self.async_request_refresh()

    async def async_clear_away(self) -> None:
        await self._write_u32(6, 0)
        await self._write_u32(8, 0)
        await self.async_request_refresh()
