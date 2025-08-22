from __future__ import annotations

from homeassistant.components.switch import SwitchEntity

from .entity import FuturaEntity
from .coordinator import FuturaCoordinator


class FuturaRegSwitch(FuturaEntity, SwitchEntity):
    def __init__(self, coordinator: FuturaCoordinator, name: str, key: str, address: int):
        super().__init__(coordinator, name, f"switch_{key}")
        self.key = key
        self.address = address

    @property
    def is_on(self) -> bool:
        return int(self.coordinator.data.get(self.key, 0)) == 1

    async def async_turn_on(self, **kwargs):
        await self.coordinator._write_u16(self.address, 1)
        await self.coordinator.async_request_refresh()

    async def async_turn_off(self, **kwargs):
        await self.coordinator._write_u16(self.address, 0)
        await self.coordinator.async_request_refresh()


async def async_setup_entry(hass, entry, async_add_entities):
    coord: FuturaCoordinator = hass.data["jablotron_futura"][entry.entry_id]

    ents = []
    ents.append(FuturaRegSwitch(coord, "Časový program", "time_program_raw", 12))
    ents.append(FuturaRegSwitch(coord, "Bypass povolen", "bypass_enable_raw", 14))
    ents.append(FuturaRegSwitch(coord, "Topení povoleno", "heating_enable_raw", 15))
    ents.append(FuturaRegSwitch(coord, "Chlazení povoleno", "cooling_enable_raw", 16))
    ents.append(FuturaRegSwitch(coord, "Komfortní režim", "comfort_enable_raw", 17))

    async_add_entities(ents, True)
