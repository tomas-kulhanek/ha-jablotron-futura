from __future__ import annotations

from homeassistant.components.select import SelectEntity

from .entity import FuturaEntity
from .coordinator import FuturaCoordinator
from .const import VENT_MODE_MAP, VENT_MODE_INV, HUMI_MODE_MAP


class FuturaVentModeSelect(FuturaEntity, SelectEntity):
    def __init__(self, coordinator: FuturaCoordinator):
        super().__init__(coordinator, "Režim větrání", "vent_mode")
        self._attr_options = list(VENT_MODE_MAP.keys())

    @property
    def current_option(self) -> str | None:
        raw = int(self.coordinator.data.get("mode_raw", 0) or 0)
        return VENT_MODE_INV.get(raw, "Vypnuto")

    async def async_select_option(self, option: str) -> None:
        value = VENT_MODE_MAP[option]
        await self.coordinator._write_u16(0, value)
        await self.coordinator.async_request_refresh()


class FuturaHumiModeSelect(FuturaEntity, SelectEntity):
    def __init__(self, coordinator: FuturaCoordinator):
        super().__init__(coordinator, "Požadovaná vlhkost", "humi_mode")
        self._attr_options = list(HUMI_MODE_MAP.keys())

    @property
    def current_option(self) -> str | None:
        val = float(self.coordinator.data.get("humi_set_raw", 50.0) or 50.0)
        if val < 37.5:
            return "Suché"
        elif val < 62.5:
            return "Komfortní"
        return "Vlhké"

    async def async_select_option(self, option: str) -> None:
        target = int(HUMI_MODE_MAP[option] * 10)
        await self.coordinator._write_u16(11, target)
        await self.coordinator.async_request_refresh()


async def async_setup_entry(hass, entry, async_add_entities):
    coord: FuturaCoordinator = hass.data["jablotron_futura"][entry.entry_id]
    async_add_entities([FuturaVentModeSelect(coord), FuturaHumiModeSelect(coord)], True)
