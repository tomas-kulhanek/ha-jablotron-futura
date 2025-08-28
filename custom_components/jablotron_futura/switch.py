from __future__ import annotations

from homeassistant.components.switch import SwitchEntity

from .entity import FuturaEntity
from .coordinator import FuturaCoordinator


class FuturaRegSwitch(FuturaEntity, SwitchEntity):
    def __init__(
        self,
        coordinator: FuturaCoordinator,
        name: str,
        key: str,
        address: int,
        avail_key: str | None = None,
    ):
        super().__init__(coordinator, name, f"switch_{key}")
        self.key = key
        self.address = address
        self.avail_key = avail_key

    @property
    def is_on(self) -> bool:
        return int(self.coordinator.data.get(self.key, 0)) == 1

    @property
    def available(self) -> bool:
        if self.avail_key is None:
            return True
        return bool(self.coordinator.data.get(self.avail_key, False))

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
    ents.append(FuturaRegSwitch(coord, "Bypass povolen", "bypass_enable_raw", 14, "bypass_available"))
    ents.append(FuturaRegSwitch(coord, "Topení povoleno", "heating_enable_raw", 15, "heating_available"))
    ents.append(FuturaRegSwitch(coord, "Chlazení povoleno", "cooling_enable_raw", 16, "cooling_available"))
    ents.append(FuturaRegSwitch(coord, "Komfortní režim", "comfort_enable_raw", 17))

    async_add_entities(ents, True)
