from __future__ import annotations

import datetime as dt
import logging
from typing import Any, Dict

from homeassistant.const import CONF_HOST, CONF_PORT
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.util import dt as ha_dt

from pymodbus.client import AsyncModbusTcpClient
from pymodbus.exceptions import ModbusException

from .const import DOMAIN, CONF_UNIT_ID, DEFAULT_UNIT_ID, KEYS, INP_START_ALFA

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
            # timeout stejně jako v původním YAML (5 s)
            self.client = AsyncModbusTcpClient(self.host, port=self.port, timeout=5)

        if not getattr(self.client, "connected", False):
            try:
                await self.client.connect()
            except Exception as e:
                try:
                    await self.client.close()
                except Exception:
                    pass
                self.client = None
                raise UpdateFailed(
                    f"TCP connect failed to {self.host}:{self.port}"
                ) from e
            if not getattr(self.client, "connected", False):
                try:
                    await self.client.close()
                except Exception:
                    pass
                self.client = None
                raise UpdateFailed(f"TCP connect failed to {self.host}:{self.port}")

        return self.client

    async def async_close(self) -> None:
        if self.client:
            try:
                await self.client.close()
            except Exception:
                pass
            self.client = None

    async def _read_block(self, start: int, count: int, *, input_regs: bool) -> list[int]:
        client = await self._ensure_client()
        try:
            if input_regs:
                rr = await client.read_input_registers(start, count=count, slave=self.unit)
            else:
                rr = await client.read_holding_registers(start, count=count, slave=self.unit)
        except ModbusException as e:
            try:
                await client.close()
            except Exception:
                pass
            self.client = None
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
        """Read all needed registers and parse into a dict.

        Čteme po segmentech, protože velký rozsah 14..44 vrací ILLEGAL DATA ADDRESS.
        """
        # Input segments
        inp_14_21 = await self._read_block(14, 8, input_regs=True)   # 14..21 (variant + bity 16..21)
        inp_30_33 = await self._read_block(30, 4, input_regs=True)   # 30..33 (teploty)
        inp_34_38 = await self._read_block(34, 5, input_regs=True)   # 34..38 (vlhkosti + NTC)
        inp_40_41 = await self._read_block(40, 2, input_regs=True)   # 40..41 (filtr, příkon)
        inp_42    = await self._read_block(42, 1, input_regs=True)   # 42 (zpětně získávané teplo)
        inp_43    = await self._read_block(43, 1, input_regs=True)  # 43 (výkon topení dohřevu)
        inp_44    = await self._read_block(44, 1, input_regs=True)   # 44 (průtok)
        inp_alfa_bits = await self._read_block(KEYS["alfa_connected_bits"], 1, input_regs=True)  # 75 (bitfield)

        # Holding area (0..17 je u Futury souvislý rozsah)
        hold_main = await self._read_block(0, 18, input_regs=False)

        data: Dict[str, Any] = {}

        # Input area – bity a variant
        data["variant_raw"]      = self._u16_from(inp_14_21, 14, KEYS["variant_raw"])
        data["modes_bits_raw"]   = self._u32_from(inp_14_21, 14, KEYS["modes_bits_raw"])
        data["errors_bits_raw"]  = self._u32_from(inp_14_21, 14, KEYS["errors_bits_raw"])
        data["warnings_bits_raw"]= self._u32_from(inp_14_21, 14, KEYS["warnings_bits_raw"])

        # Teploty
        data["temp_outdoor"]     = self._i16_from(inp_30_33, 30, KEYS["temp_outdoor"]) / 10.0
        data["temp_supply"]      = self._i16_from(inp_30_33, 30, KEYS["temp_supply"]) / 10.0
        data["temp_extract"]     = self._i16_from(inp_30_33, 30, KEYS["temp_extract"]) / 10.0
        data["temp_exhaust"]     = self._i16_from(inp_30_33, 30, KEYS["temp_exhaust"]) / 10.0
        data["temp_outdoor_ntc"] = self._i16_from(inp_34_38, 34, KEYS["temp_outdoor_ntc"]) / 10.0

        # Vlhkosti
        data["humi_outdoor"]     = self._i16_from(inp_34_38, 34, KEYS["humi_outdoor"]) / 10.0
        data["humi_supply"]      = self._i16_from(inp_34_38, 34, KEYS["humi_supply"]) / 10.0
        data["humi_extract"]     = self._i16_from(inp_34_38, 34, KEYS["humi_extract"]) / 10.0
        data["humi_exhaust"]     = self._i16_from(inp_34_38, 34, KEYS["humi_exhaust"]) / 10.0

        # Výkony / průtok
        data["filter_wear"]      = self._u16_from(inp_40_41, 40, KEYS["filter_wear"])
        data["power"]            = self._u16_from(inp_40_41, 40, KEYS["power"])
        data["heat_recovering"]  = self._u16_from(inp_42, 42, KEYS["heat_recovering"])
        data["heating_power"]    = self._u16_from(inp_43, 43, KEYS["heating_power"])
        data["air_flow"]         = self._u16_from(inp_44,    44, KEYS["air_flow"])

        # ALFA
        bits = self._u16_from(inp_alfa_bits, KEYS["alfa_connected_bits"], KEYS["alfa_connected_bits"])
        data["alfa_connected_bits"] = bits
        data["alfa_count"] = bits.bit_count()
        for i in range(1, 9):
            if not (bits & (1 << (i - 1))):
                continue
            base = INP_START_ALFA + (i - 1) * 10
            # Each ALFA occupies the first six registers of its 10-register slot
            # (160..165, 170..175, ...). Reading beyond 6 registers may trigger
            # ILLEGAL DATA ADDRESS errors, so limit the range.
            block = await self._read_block(base, 6, input_regs=True)
            data[f"alfa_mb_address_{i}"] = self._u16_from(block, base, base)
            data[f"alfa_options_{i}"] = self._u16_from(block, base, base + 1)
            data[f"alfa_co2_{i}"] = self._u16_from(block, base, base + 2)
            data[f"alfa_temp_{i}"] = self._i16_from(block, base, base + 3) / 10.0
            data[f"alfa_humi_{i}"] = self._u16_from(block, base, base + 4) / 10.0
            data[f"alfa_ntc_temp_{i}"] = self._u16_from(block, base, base + 5) / 10.0

        # Holding area
        for k in (
            "mode_raw","boost_remaining_s","circulation_remaining_s","overpressure_remaining_s",
            "night_remaining_s","party_remaining_s","time_program_raw","antiradon_raw",
            "bypass_enable_raw","heating_enable_raw","cooling_enable_raw","comfort_enable_raw",
        ):
            data[k] = self._u16_from(hold_main, 0, KEYS[k])

        data["away_begin_ts"] = self._u32_from(hold_main, 0, KEYS["away_begin_ts"])
        data["away_end_ts"]   = self._u32_from(hold_main, 0, KEYS["away_end_ts"])

        data["temp_set_raw"] = self._u16_from(hold_main, 0, KEYS["temp_set_raw"]) / 10.0
        data["humi_set_raw"] = self._u16_from(hold_main, 0, KEYS["humi_set_raw"]) / 10.0

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
            data[which.replace("_ts", "_text")] = (
                "Nenastaveno" if ts == 0
                else ha_dt.as_local(ha_dt.utc_from_timestamp(ts)).strftime("%Y-%m-%d %H:%M")
            )

        return data

    async def _write_u16(self, address: int, value: int) -> None:
        client = await self._ensure_client()
        try:
            rr = await client.write_register(address, value=value, slave=self.unit)
        except ModbusException as e:
            try:
                await client.close()
            except Exception:
                pass
            self.client = None
            raise UpdateFailed(f"Write failed @ {address}: {e}") from e
        if rr.isError():
            raise UpdateFailed(f"Write failed @ {address}: {rr}")

    async def _write_u32(self, address: int, value: int) -> None:
        """Write two consecutive holding registers starting at 'address' (hi, lo)."""
        client = await self._ensure_client()
        hi = (value >> 16) & 0xFFFF
        lo = value & 0xFFFF
        try:
            rr = await client.write_registers(address, values=[hi, lo], slave=self.unit)
        except ModbusException as e:
            try:
                await client.close()
            except Exception:
                pass
            self.client = None
            raise UpdateFailed(f"Write failed @ {address} (u32): {e}") from e
        if rr.isError():
            raise UpdateFailed(f"Write failed @ {address} (u32): {rr}")

    async def async_set_away(self, begin: dt.datetime | None, end: dt.datetime | None) -> None:
        now_ts = int(dt.datetime.utcnow().timestamp())
        b_ts = int(begin.timestamp()) if isinstance(begin, dt.datetime) else now_ts
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
